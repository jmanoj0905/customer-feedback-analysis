#!/bin/bash

#######################################
# Customer Feedback Analysis System
# Automated Deployment Script
#######################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="customer-feedback-analysis"
ENVIRONMENT="prod"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure'"
        exit 1
    fi
    print_success "AWS credentials configured"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install it first."
        exit 1
    fi
    print_success "Python 3 found"

    # Check jq (optional but helpful)
    if ! command -v jq &> /dev/null; then
        print_info "jq not found (optional). Install for better JSON parsing."
    else
        print_success "jq found"
    fi
}

create_deployment_packages() {
    print_header "Creating Lambda Deployment Packages"

    # Package analyze_feedback
    print_info "Packaging analyze_feedback Lambda..."
    cd backend/lambda/analyze_feedback

    # Install dependencies
    pip3 install -r requirements.txt -t . --quiet

    # Create deployment package
    zip -r lambda_deployment.zip . -x "*.pyc" -x "__pycache__/*" -x "*.git*" &> /dev/null
    print_success "analyze_feedback packaged"

    cd ../../..

    # Package get_analytics
    print_info "Packaging get_analytics Lambda..."
    cd backend/lambda/get_analytics

    pip3 install -r requirements.txt -t . --quiet
    zip -r lambda_deployment.zip . -x "*.pyc" -x "__pycache__/*" -x "*.git*" &> /dev/null
    print_success "get_analytics packaged"

    cd ../../..
}

deploy_cloudformation() {
    print_header "Deploying CloudFormation Stack"

    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION &> /dev/null; then
        print_info "Stack exists. Updating..."
        OPERATION="update"

        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure/cloudformation/template.yaml \
            --parameters \
                ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
                ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION || {
                print_info "No updates to perform"
                return 0
            }

        print_info "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
    else
        print_info "Creating new stack..."
        OPERATION="create"

        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure/cloudformation/template.yaml \
            --parameters \
                ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
                ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION

        print_info "Waiting for stack creation to complete..."
        aws cloudformation wait stack-create-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
    fi

    print_success "CloudFormation stack ${OPERATION}d successfully"
}

update_lambda_code() {
    print_header "Updating Lambda Function Code"

    # Get function names from stack
    ANALYZE_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`AnalyzeFunctionName`].OutputValue' \
        --output text)

    ANALYTICS_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`AnalyticsFunctionName`].OutputValue' \
        --output text)

    # Update analyze_feedback
    print_info "Updating $ANALYZE_FUNCTION..."
    aws lambda update-function-code \
        --function-name $ANALYZE_FUNCTION \
        --zip-file fileb://backend/lambda/analyze_feedback/lambda_deployment.zip \
        --region $AWS_REGION \
        --no-cli-pager > /dev/null
    print_success "Updated analyze_feedback Lambda"

    # Update get_analytics
    print_info "Updating $ANALYTICS_FUNCTION..."
    aws lambda update-function-code \
        --function-name $ANALYTICS_FUNCTION \
        --zip-file fileb://backend/lambda/get_analytics/lambda_deployment.zip \
        --region $AWS_REGION \
        --no-cli-pager > /dev/null
    print_success "Updated get_analytics Lambda"
}

deploy_frontend() {
    print_header "Deploying Frontend to S3"

    # Get bucket name from stack
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
        --output text | cut -d'.' -f1 | cut -d'/' -f3)

    print_info "Uploading to bucket: $BUCKET_NAME"

    # Upload frontend files
    aws s3 sync frontend/public s3://$BUCKET_NAME/ \
        --exclude ".DS_Store" \
        --region $AWS_REGION \
        --quiet

    aws s3 sync frontend/src s3://$BUCKET_NAME/src/ \
        --exclude ".DS_Store" \
        --region $AWS_REGION \
        --quiet

    print_success "Frontend deployed successfully"
}

display_outputs() {
    print_header "Deployment Complete!"

    # Get outputs
    API_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
        --output text)

    WEBSITE_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
        --output text)

    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
        --output text)

    echo -e "${GREEN}API Endpoint:${NC} $API_ENDPOINT"
    echo -e "${GREEN}Website URL:${NC} $WEBSITE_URL"
    echo -e "${GREEN}DynamoDB Table:${NC} $TABLE_NAME"

    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo "1. Update frontend/src/js/api.js with the API endpoint:"
    echo "   API_ENDPOINT: '$API_ENDPOINT'"
    echo "2. Open the website URL in your browser"
    echo "3. Test the API with sample data from data/sample_feedback.json"
    echo "4. Monitor logs: aws logs tail /aws/lambda/$ANALYZE_FUNCTION --follow"
}

cleanup_temp_files() {
    print_header "Cleaning Up Temporary Files"

    # Remove deployment packages
    rm -f backend/lambda/analyze_feedback/lambda_deployment.zip
    rm -f backend/lambda/get_analytics/lambda_deployment.zip

    print_success "Cleanup complete"
}

# Main execution
main() {
    print_header "Customer Feedback Analysis - Deployment"
    echo "Project: $PROJECT_NAME"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $AWS_REGION"

    check_prerequisites
    create_deployment_packages
    deploy_cloudformation
    update_lambda_code
    deploy_frontend
    display_outputs
    cleanup_temp_files

    print_success "Deployment completed successfully!"
}

# Run main function
main
