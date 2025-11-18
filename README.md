# Customer Feedback Analysis System

> AI-powered sentiment analysis platform using AWS Comprehend for real-time customer feedback insights

[![AWS](https://img.shields.io/badge/AWS-Comprehend-orange)](https://aws.amazon.com/comprehend/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Cost Estimation](#cost-estimation)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Customer Feedback Analysis System is a serverless application built on AWS that analyzes customer feedback using natural language processing (NLP). It provides real-time sentiment analysis, key phrase extraction, and entity recognition to help businesses understand customer opinions and improve their products and services.

## Architecture

```
┌─────────────┐      ┌──────────────┐        ┌─────────────┐
│   Frontend  │─────▶│ API Gateway  │───────▶│   Lambda    │
│  (S3/HTML)  │      │   (REST)     │        │  Functions  │
└─────────────┘      └──────────────┘        └──────┬──────┘
                                                    │
                                          ┌─────────┴────────┐
                                          │                  │
                                    ┌─────▼──────┐     ┌─────▼────────┐
                                    │ Comprehend │     │  DynamoDB    │
                                    │   (NLP)    │     │   (NoSQL)    │
                                    └────────────┘     └──────────────┘
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| AWS Comprehend | Sentiment analysis, key phrase extraction, entity recognition |
| AWS Lambda | Serverless compute for processing feedback |
| Amazon DynamoDB | NoSQL database for feedback storage |
| Amazon S3 | Static website hosting |
| API Gateway | RESTful API endpoints |
| IAM | Security and access management |
| CloudWatch | Logging and monitoring |

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/customer-sentiment-analysis.git
cd customer-sentiment-analysis
```

### Step 2: Configure AWS Credentials

```bash
aws configure
```

When prompted, enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (example: us-east-1)
- Default output format (recommended: json)

### Step 3: Deploy to AWS

Make the deployment script executable and run it:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

The deployment script will automatically:
- Create all required AWS resources
- Deploy Lambda functions with dependencies
- Configure API Gateway endpoints
- Host the frontend on S3
- Display URLs and endpoints upon completion

### Step 4: Update Frontend Configuration

After deployment completes, update the API endpoint in `frontend/src/js/api.js`:

```javascript
const CONFIG = {
  API_ENDPOINT: "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
  USE_MOCK_DATA: false,
};
```

Replace `your-api-id` with the actual API Gateway ID from the deployment output.

### Step 5: Access the Application

Open the Website URL provided in the deployment output in your web browser.

### (Alternative): Running Locally
Clone repo, then run the following command in the project root directory:

```
python3 -m http.server 8000
```

## Project Structure

```
customer-feedback-analysis/
│
├── backend/
│   ├── lambda/
│   │   ├── analyze_feedback/
│   │   │   ├── lambda_function.py          # Sentiment analysis handler
│   │   │   ├── requirements.txt            # Python dependencies
│   │   │   └── config.py                   # Configuration settings
│   │   │
│   │   └── get_analytics/
│   │       ├── lambda_function.py          # Analytics aggregation handler
│   │       ├── requirements.txt            # Python dependencies
│   │       └── config.py                   # Configuration settings
│   │
│   └── utils/
│       └── comprehend_helper.py            # Reusable Comprehend utilities
│
├── frontend/
│   ├── public/
│   │   └── index.html                      # Main HTML page
│   │
│   ├── src/
│   │   ├── js/
│   │   │   ├── app.js                      # Application logic
│   │   │   ├── api.js                      # API communication layer
│   │   │   └── charts.js                   # Chart visualizations
│   │   │
│   │   └── css/
│   │       └── style.css                   # Application styling
│   │
│   └── package.json                        # Frontend dependencies
│
├── infrastructure/
│   ├── cloudformation/
│   │   └── template.yaml                   # CloudFormation template
│   │
│   └── terraform/
│       ├── main.tf                         # Terraform configuration
│       ├── variables.tf                    # Terraform variables
│       └── outputs.tf                      # Terraform outputs
│
├── data/
│   ├── sample_feedback.json                # 20 test samples
│   └── processed/                          # Processed data (gitignored)
│
├── tests/
│   ├── test_lambda.py                      # Lambda unit tests
│   └── sample_requests.json                # Sample API requests
│
├── docs/
│   ├── architecture.md                     # Architecture documentation
│   ├── setup.md                            # Setup instructions
│   └── api_documentation.md                # API reference
│
├── scripts/
│   ├── deploy.sh                           # Automated deployment
│   ├── upload_sample_data.py               # Sample data uploader
│   └── validate_project.sh                 # Project validation
│
├── .gitignore                              # Git ignore patterns
├── README.md                               # This file
├── LICENSE                                 # MIT License
├── CONTRIBUTING.md                         # Contribution guidelines
├── EXPLAINED.md                            # Detailed technical explanation
├── requirements.txt                        # Python dependencies
└── config.json                             # Project configuration
```

## Deployment

### Option 1: Automated Script (Recommended)

The easiest way to deploy is using the provided deployment script:

```bash
./scripts/deploy.sh
```

### Option 2: AWS CloudFormation

Deploy using CloudFormation directly:

```bash
aws cloudformation create-stack \
  --stack-name customer-feedback-analysis \
  --template-body file://infrastructure/cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### Option 3: Terraform

Deploy using Terraform:

```bash
cd infrastructure/terraform
terraform init
terraform apply
```

### API Usage

**Analyze Feedback Endpoint:**

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "analyze_feedback",
    "feedback": "This product is amazing! Best purchase ever!",
    "customer_id": "CUST123",
    "metadata": {"category": "product"}
  }'
```

**Get Analytics Endpoint:**

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/analytics \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "get_analytics",
    "limit": 50
  }'
```

For complete API documentation, see [API Documentation](./docs/api_documentation.md)

## Testing

### Running Unit Tests

Install test dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
python -m pytest tests/ -v
```

Run tests with coverage report:

```bash
python -m pytest tests/ --cov=backend --cov-report=html
```

### Testing Frontend Locally

To test the frontend without deploying to AWS:

```bash
cd frontend/public
python3 -m http.server 8000
```

Open http://localhost:8000 in your browser. The frontend will run in mock data mode.

### Uploading Sample Data

After deployment, you can upload the sample feedback data:

```bash
# First, update the API endpoint in scripts/upload_sample_data.py
python3 scripts/upload_sample_data.py
```

### Validating the Project

Run the validation script to check all files:

```bash
./scripts/validate_project.sh
```

## Cost Estimation

### AWS Free Tier (First 12 Months)

The following free tier allowances apply:

- AWS Comprehend: 50,000 units per month
- AWS Lambda: 1 million requests + 400,000 GB-seconds per month
- Amazon DynamoDB: 25 GB storage + 25 WCU/RCU
- Amazon S3: 5 GB storage
- API Gateway: 1 million API calls per month

### Beyond Free Tier

Estimated monthly costs for processing 10,000 feedback submissions:

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| AWS Comprehend | 10,000 units | $1.00 |
| AWS Lambda | 10,000 invocations | $0.20 |
| Amazon DynamoDB | 10,000 write operations | $1.25 |
| API Gateway | 10,000 requests | $0.04 |
| Amazon S3 | 5 GB storage | $0.12 |
| **Total** | | **Approximately $2.61/month** |

Note: Actual costs may vary based on usage patterns and AWS region.

## Roadmap

Future enhancements planned for this project:

- Multi-language support for international feedback
- Email notifications for negative sentiment detection
- Batch processing capabilities for large datasets
- Historical trend analysis and reporting
- Export functionality for analytics (PDF/CSV)
- Integration with third-party platforms (Slack, Zendesk)
- User authentication using AWS Cognito
- Real-time updates using WebSocket connections

## Additional Resources

- [Detailed Technical Explanation](./EXPLAINED.md)
- [Architecture Documentation](./docs/architecture.md)
- [Setup Guide](./docs/setup.md)
- [API Reference](./docs/api_documentation.md)

---
