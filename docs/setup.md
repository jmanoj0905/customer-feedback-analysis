# Setup Guide

This guide will walk you through setting up the Customer Feedback Analysis System from scratch.

## Prerequisites

### Required Software

- **AWS CLI** (v2.x or later)
  ```bash
  aws --version
  ```

- **Python** (3.9 or later)
  ```bash
  python3 --version
  ```

- **Git**
  ```bash
  git --version
  ```

### Optional Software

- **Terraform** (v1.0 or later) - for Infrastructure as Code
  ```bash
  terraform --version
  ```

- **Node.js** (v14 or later) - for frontend development tools
  ```bash
  node --version
  ```

### AWS Account Requirements

- AWS Account with administrative access
- AWS CLI configured with credentials
- Sufficient service limits for:
  - Lambda functions (2+)
  - DynamoDB tables (1+)
  - S3 buckets (1+)
  - API Gateway APIs (1+)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/customer-sentiment-analysis.git
cd customer-sentiment-analysis
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Enter your credentials:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (`json`)

Verify configuration:
```bash
aws sts get-caller-identity
```

### 3. Install Python Dependencies

```bash
# For Lambda functions
cd backend/lambda/analyze_feedback
pip install -r requirements.txt -t .

cd ../get_analytics
pip install -r requirements.txt -t .

cd ../../..
```

### 4. Update Configuration

Edit `config.json` to customize your deployment:

```json
{
  "aws": {
    "region": "us-east-1"
  },
  "lambda": {
    "function_name": "CustomerFeedbackAnalyzer"
  },
  "dynamodb": {
    "table_name": "CustomerFeedback"
  },
  "s3": {
    "website_bucket": "your-unique-bucket-name"
  }
}
```

## Deployment Options

### Option 1: Automated Deployment Script (Recommended)

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

This script will:
1. Create IAM roles and policies
2. Set up DynamoDB table
3. Package and deploy Lambda functions
4. Create API Gateway
5. Deploy frontend to S3
6. Output URLs and endpoints

### Option 2: CloudFormation Deployment

```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/template.yaml

# Create stack
aws cloudformation create-stack \
  --stack-name customer-feedback-analysis \
  --template-body file://infrastructure/cloudformation/template.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=customer-feedback-analysis \
               ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name customer-feedback-analysis

# Get outputs
aws cloudformation describe-stacks \
  --stack-name customer-feedback-analysis \
  --query 'Stacks[0].Outputs'
```

### Option 3: Terraform Deployment

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply configuration
terraform apply -auto-approve

# View outputs
terraform output
```

## Post-Deployment Configuration

### 1. Update Frontend API Endpoint

After deployment, update the API endpoint in the frontend:

```bash
# Get API endpoint from stack outputs
export API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name customer-feedback-analysis \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"
```

Edit `frontend/src/js/api.js`:
```javascript
const CONFIG = {
  API_ENDPOINT: "YOUR_API_ENDPOINT_HERE",  // Replace with actual endpoint
  USE_MOCK_DATA: false,  // Set to false for production
};
```

### 2. Deploy Frontend to S3

```bash
# Get bucket name
export BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name customer-feedback-analysis \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
  --output text | cut -d'.' -f1 | cut -d'/' -f3)

# Upload frontend files
aws s3 sync frontend/public s3://$BUCKET_NAME/ --exclude ".DS_Store"
aws s3 sync frontend/src s3://$BUCKET_NAME/src/ --exclude ".DS_Store"
```

### 3. Test the Deployment

```bash
# Get website URL
export WEBSITE_URL=$(aws cloudformation describe-stacks \
  --stack-name customer-feedback-analysis \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
  --output text)

echo "Website URL: $WEBSITE_URL"
```

Open the URL in your browser to access the application.

## Testing the API

### Test Analyze Endpoint

```bash
curl -X POST $API_ENDPOINT/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "analyze_feedback",
    "feedback": "This product is amazing! Best purchase ever!",
    "customer_id": "TEST001",
    "metadata": {
      "category": "product"
    }
  }'
```

### Test Analytics Endpoint

```bash
curl -X POST $API_ENDPOINT/analytics \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "get_analytics",
    "limit": 50
  }'
```

## Local Development Setup

### Running Frontend Locally

1. Update `frontend/src/js/api.js` to use mock data:
   ```javascript
   const CONFIG = {
     USE_MOCK_DATA: true,
   };
   ```

2. Open `frontend/public/index.html` in a web browser

3. Or use a local server:
   ```bash
   cd frontend/public
   python3 -m http.server 8000
   ```
   
   Visit: http://localhost:8000

### Testing Lambda Functions Locally

```bash
cd backend/lambda/analyze_feedback

# Create test event
cat > event.json << EOF
{
  "httpMethod": "POST",
  "body": "{\"feedback\":\"Great product!\",\"customer_id\":\"TEST001\"}"
}
EOF

# Invoke locally (requires sam cli)
sam local invoke AnalyzeFeedbackFunction -e event.json
```

## Troubleshooting

### Common Issues

#### 1. Lambda Deployment Package Too Large

**Error**: "Unzipped size must be smaller than 262144000 bytes"

**Solution**: Use Lambda Layers for dependencies
```bash
# Create layer
cd backend/lambda/analyze_feedback
mkdir python
pip install -r requirements.txt -t python/
zip -r layer.zip python/
aws lambda publish-layer-version \
  --layer-name comprehend-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.9
```

#### 2. CORS Errors

**Error**: "Access-Control-Allow-Origin header"

**Solution**: Verify CORS configuration in Lambda responses:
```python
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}
```

#### 3. DynamoDB Access Denied

**Error**: "User is not authorized to perform: dynamodb:PutItem"

**Solution**: Verify IAM role has correct permissions:
```bash
aws iam get-role-policy \
  --role-name customer-feedback-analysis-lambda-role \
  --policy-name DynamoDBAccess
```

#### 4. Comprehend API Errors

**Error**: "TextSizeLimitExceededException"

**Solution**: Validate text length before sending:
```python
if len(text) > 5000:
    return error_response("Text too long", 400)
```

### Checking Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/CustomerFeedbackAnalyzer --follow

# API Gateway logs (if enabled)
aws logs tail /aws/apigateway/customer-feedback-api --follow
```

### Monitoring

```bash
# Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=CustomerFeedbackAnalyzer \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Cleanup

### Remove All Resources

#### Using CloudFormation:
```bash
aws cloudformation delete-stack --stack-name customer-feedback-analysis
aws cloudformation wait stack-delete-complete --stack-name customer-feedback-analysis
```

#### Using Terraform:
```bash
cd infrastructure/terraform
terraform destroy -auto-approve
```

#### Manual Cleanup:
```bash
# Delete S3 bucket (empty it first)
aws s3 rb s3://your-bucket-name --force

# Delete Lambda functions
aws lambda delete-function --function-name CustomerFeedbackAnalyzer
aws lambda delete-function --function-name GetCustomerAnalytics

# Delete DynamoDB table
aws dynamodb delete-table --table-name CustomerFeedback

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Delete IAM role
aws iam delete-role --role-name customer-feedback-lambda-role
```

## Next Steps

- Review [Architecture Documentation](./architecture.md)
- Check [API Documentation](./api_documentation.md)
- Run tests: `python -m pytest tests/`
- Configure monitoring and alerts
- Set up CI/CD pipeline

## Support

For issues and questions:
- Check the [GitHub Issues](https://github.com/yourusername/customer-sentiment-analysis/issues)
- Review AWS service documentation
- Contact: your.email@example.com
