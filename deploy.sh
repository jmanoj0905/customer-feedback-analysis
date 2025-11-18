#!/bin/bash

# Customer Feedback Analysis - AWS Deployment Script
# This script automates the deployment of the entire application to AWS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration
CONFIG_FILE="config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: config.json not found${NC}"
    exit 1
fi

# Parse configuration using Python
AWS_REGION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['aws']['region'])")
FUNCTION_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['lambda']['function_name'])")
TABLE_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['dynamodb']['table_name'])")
S3_BUCKET=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['s3']['bucket_name'])")
WEBSITE_BUCKET=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['s3']['website_bucket'])")
ROLE_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['lambda']['role_name'])")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Customer Feedback Analysis Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Create IAM Role for Lambda
echo -e "${YELLOW}[1/8] Creating IAM Role for Lambda...${NC}"
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

if aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo "Role $ROLE_NAME already exists, skipping..."
else
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document "$TRUST_POLICY" \
        --region $AWS_REGION

    # Attach necessary policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/ComprehendReadOnly

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

    echo -e "${GREEN}Role created successfully${NC}"
    echo "Waiting 10 seconds for role propagation..."
    sleep 10
fi

# Step 2: Create DynamoDB Table
echo -e "${YELLOW}[2/8] Creating DynamoDB Table...${NC}"
if aws dynamodb describe-table --table-name $TABLE_NAME --region $AWS_REGION 2>/dev/null; then
    echo "Table $TABLE_NAME already exists, skipping..."
else
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions \
            AttributeName=feedback_id,AttributeType=S \
            AttributeName=timestamp,AttributeType=S \
        --key-schema \
            AttributeName=feedback_id,KeyType=HASH \
            AttributeName=timestamp,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region $AWS_REGION

    echo -e "${GREEN}DynamoDB table created successfully${NC}"
    echo "Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name $TABLE_NAME --region $AWS_REGION
fi

# Step 3: Create S3 Bucket for data storage
echo -e "${YELLOW}[3/8] Creating S3 Bucket for data...${NC}"
if aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
    echo "Bucket $S3_BUCKET already exists, skipping..."
else
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3 mb "s3://$S3_BUCKET" --region $AWS_REGION
    else
        aws s3 mb "s3://$S3_BUCKET" --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION
    fi
    echo -e "${GREEN}S3 bucket created successfully${NC}"
fi

# Step 4: Package and Deploy Lambda Function
echo -e "${YELLOW}[4/8] Packaging Lambda Function...${NC}"
cd backend
pip install boto3 -t . --quiet 2>/dev/null || true
zip -r ../lambda_deployment.zip . -q
cd ..

echo -e "${YELLOW}[5/8] Deploying Lambda Function...${NC}"
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda_deployment.zip \
        --region $AWS_REGION > /dev/null
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://lambda_deployment.zip \
        --timeout 60 \
        --memory-size 256 \
        --environment "Variables={DYNAMODB_TABLE=$TABLE_NAME,S3_BUCKET=$S3_BUCKET}" \
        --region $AWS_REGION > /dev/null
fi

echo -e "${GREEN}Lambda function deployed successfully${NC}"

# Clean up
rm lambda_deployment.zip

# Step 6: Create API Gateway
echo -e "${YELLOW}[6/8] Creating API Gateway...${NC}"
API_NAME="CustomerFeedbackAPI"

# Check if API already exists
API_ID=$(aws apigateway get-rest-apis --region $AWS_REGION --query "items[?name=='$API_NAME'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "Creating new API Gateway..."
    API_ID=$(aws apigateway create-rest-api \
        --name $API_NAME \
        --description "API for Customer Feedback Analysis" \
        --region $AWS_REGION \
        --query 'id' \
        --output text)
    echo "API Gateway ID: $API_ID"
else
    echo "API Gateway already exists with ID: $API_ID"
fi

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query 'items[?path==`/`].id' \
    --output text)

# Create /analyze resource if it doesn't exist
ANALYZE_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query "items[?pathPart=='analyze'].id" \
    --output text 2>/dev/null || true)

if [ -z "$ANALYZE_RESOURCE_ID" ]; then
    ANALYZE_RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ROOT_RESOURCE_ID \
        --path-part analyze \
        --region $AWS_REGION \
        --query 'id' \
        --output text)
fi

# Create POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $ANALYZE_RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region $AWS_REGION 2>/dev/null || echo "Method already exists"

# Enable CORS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $ANALYZE_RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $AWS_REGION 2>/dev/null || echo "OPTIONS method already exists"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION --query 'Configuration.FunctionArn' --output text)

# Set up Lambda integration
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $ANALYZE_RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $AWS_REGION > /dev/null 2>&1 || echo "Integration already exists"

# Add Lambda permission for API Gateway
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id apigateway-invoke-post \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$AWS_REGION:*:$API_ID/*/*" \
    --region $AWS_REGION 2>/dev/null || echo "Permission already exists"

# Deploy API
echo -e "${YELLOW}[7/8] Deploying API Gateway...${NC}"
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $AWS_REGION > /dev/null

API_ENDPOINT="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/analyze"
echo -e "${GREEN}API Gateway deployed successfully${NC}"
echo -e "API Endpoint: ${GREEN}$API_ENDPOINT${NC}"

# Step 8: Deploy Frontend to S3
echo -e "${YELLOW}[8/8] Deploying Frontend...${NC}"

# Create website bucket if it doesn't exist
if aws s3 ls "s3://$WEBSITE_BUCKET" 2>/dev/null; then
    echo "Website bucket already exists..."
else
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3 mb "s3://$WEBSITE_BUCKET" --region $AWS_REGION
    else
        aws s3 mb "s3://$WEBSITE_BUCKET" --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION
    fi
fi

# Enable static website hosting
aws s3 website "s3://$WEBSITE_BUCKET" \
    --index-document index.html \
    --error-document index.html \
    --region $AWS_REGION

# Update API endpoint in frontend
sed -i.bak "s|YOUR_API_GATEWAY_URL_HERE|$API_ENDPOINT|g" frontend/app.js
sed -i.bak "s|USE_MOCK_DATA: true|USE_MOCK_DATA: false|g" frontend/app.js

# Upload frontend files
aws s3 sync frontend/ "s3://$WEBSITE_BUCKET" \
    --exclude "*.bak" \
    --region $AWS_REGION

# Make bucket public for website hosting
BUCKET_POLICY="{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {
      \"Sid\": \"PublicReadGetObject\",
      \"Effect\": \"Allow\",
      \"Principal\": \"*\",
      \"Action\": \"s3:GetObject\",
      \"Resource\": \"arn:aws:s3:::$WEBSITE_BUCKET/*\"
    }
  ]
}"

echo "$BUCKET_POLICY" > /tmp/bucket-policy.json
aws s3api put-bucket-policy \
    --bucket $WEBSITE_BUCKET \
    --policy file:///tmp/bucket-policy.json \
    --region $AWS_REGION
rm /tmp/bucket-policy.json

# Restore original frontend files
mv frontend/app.js.bak frontend/app.js 2>/dev/null || true

WEBSITE_URL="http://$WEBSITE_BUCKET.s3-website-$AWS_REGION.amazonaws.com"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "API Endpoint: ${GREEN}$API_ENDPOINT${NC}"
echo -e "Website URL: ${GREEN}$WEBSITE_URL${NC}"
echo ""
echo -e "DynamoDB Table: ${GREEN}$TABLE_NAME${NC}"
echo -e "Lambda Function: ${GREEN}$FUNCTION_NAME${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open the website URL in your browser"
echo "2. Submit sample feedback to test the system"
echo "3. Monitor CloudWatch Logs for Lambda execution"
echo ""
echo -e "${YELLOW}To test the API directly:${NC}"
echo "curl -X POST $API_ENDPOINT \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"operation\":\"analyze_feedback\",\"feedback\":\"This product is amazing!\"}'"
echo ""
