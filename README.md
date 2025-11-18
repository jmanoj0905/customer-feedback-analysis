# Customer Feedback Analysis System

> AI-powered sentiment analysis platform using AWS Comprehend for real-time customer feedback insights

[![AWS](https://img.shields.io/badge/AWS-Comprehend-orange)](https://aws.amazon.com/comprehend/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

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

## 🎯 Overview

The Customer Feedback Analysis System is a serverless application built on AWS that analyzes customer feedback using natural language processing (NLP). It provides real-time sentiment analysis, key phrase extraction, and entity recognition to help businesses understand customer opinions and improve their products/services.

### Why This Project?

- **Real-world Application**: Demonstrates practical use of cloud-based AI/ML services
- **Serverless Architecture**: Showcases modern cloud architecture patterns
- **End-to-End Solution**: Complete full-stack application from frontend to backend
- **Production-Ready**: Includes IaC, testing, documentation, and deployment automation
- **Resume-Worthy**: Perfect for showcasing cloud development skills

## ✨ Features

### Core Functionality

- ✅ **Real-time Sentiment Analysis** - Classify feedback as Positive, Negative, Neutral, or Mixed
- ✅ **Key Phrase Extraction** - Identify important topics and themes
- ✅ **Entity Recognition** - Detect people, organizations, locations, and more
- ✅ **Analytics Dashboard** - Visualize sentiment trends with interactive charts
- ✅ **Multi-category Support** - Organize feedback by product, service, delivery, etc.

### Technical Features

- ✅ **Serverless Architecture** - Auto-scaling with AWS Lambda
- ✅ **Infrastructure as Code** - CloudFormation and Terraform templates
- ✅ **Automated Deployment** - One-command deployment script
- ✅ **Comprehensive Testing** - Unit tests with mocking
- ✅ **Detailed Documentation** - Architecture, API, and setup guides
- ✅ **Mock Data Mode** - Test frontend without AWS deployment

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│ API Gateway  │─────▶│   Lambda    │
│  (S3/HTML)  │      │   (REST)     │      │  Functions  │
└─────────────┘      └──────────────┘      └──────┬──────┘
                                                    │
                                          ┌─────────┴────────┐
                                          │                  │
                                    ┌─────▼──────┐    ┌─────▼────────┐
                                    │ Comprehend │    │  DynamoDB    │
                                    │   (NLP)    │    │   (NoSQL)    │
                                    └────────────┘    └──────────────┘
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| **AWS Comprehend** | Sentiment analysis, key phrases, entities |
| **AWS Lambda** | Serverless compute for processing |
| **Amazon DynamoDB** | NoSQL database for feedback storage |
| **Amazon S3** | Static website hosting |
| **API Gateway** | RESTful API endpoints |
| **IAM** | Security and access management |
| **CloudWatch** | Logging and monitoring |

📖 [Detailed Architecture Documentation](./docs/architecture.md)

## 📚 Prerequisites

### Required

- **AWS Account** with administrative access
- **AWS CLI** (v2.x or later) - [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)

### Optional

- **Terraform** (v1.0+) - For infrastructure as code
- **Node.js** (v14+) - For frontend development tools

### AWS Permissions

Your AWS user needs permissions for:
- Lambda, DynamoDB, S3, API Gateway, IAM, CloudFormation, Comprehend

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/customer-sentiment-analysis.git
cd customer-sentiment-analysis
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Output format (`json`)

### 3. Deploy to AWS

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

The script will:
- ✅ Create all AWS resources
- ✅ Deploy Lambda functions
- ✅ Configure API Gateway
- ✅ Host frontend on S3
- ✅ Output URLs and endpoints

### 4. Update Frontend Configuration

After deployment, update `frontend/src/js/api.js`:

```javascript
const CONFIG = {
  API_ENDPOINT: "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
  USE_MOCK_DATA: false,  // Set to false for production
};
```

### 5. Access Your Application

Open the Website URL provided by the deployment script in your browser!

## 📁 Project Structure

```
customer-feedback-analysis/
│
├── backend/
│   ├── lambda/
│   │   ├── analyze_feedback/
│   │   │   ├── lambda_function.py          # Main sentiment analysis handler
│   │   │   ├── requirements.txt            # boto3, etc.
│   │   │   └── config.py                   # Configuration
│   │   │
│   │   └── get_analytics/
│   │       ├── lambda_function.py          # Analytics aggregation
│   │       ├── requirements.txt
│   │       └── config.py
│   │
│   └── utils/
│       └── comprehend_helper.py            # Reusable Comprehend functions
│
├── frontend/
│   ├── public/
│   │   └── index.html                      # Main HTML file
│   │
│   ├── src/
│   │   ├── js/
│   │   │   ├── app.js                      # Main application logic
│   │   │   ├── api.js                      # API communication
│   │   │   └── charts.js                   # Chart visualizations
│   │   │
│   │   └── css/
│   │       └── style.css                   # Styling
│   │
│   └── package.json                        # Frontend dependencies
│
├── infrastructure/
│   ├── cloudformation/
│   │   └── template.yaml                   # CloudFormation IaC
│   │
│   └── terraform/
│       ├── main.tf                         # Terraform main config
│       ├── variables.tf                    # Terraform variables
│       └── outputs.tf                      # Terraform outputs
│
├── data/
│   ├── sample_feedback.json                # Sample test data (20 examples)
│   └── processed/                          # Processed results (gitignored)
│
├── tests/
│   ├── test_lambda.py                      # Unit tests for Lambda
│   └── sample_requests.json                # Sample API requests
│
├── docs/
│   ├── architecture.md                     # System architecture
│   ├── setup.md                            # Detailed setup guide
│   └── api_documentation.md                # API reference
│
├── scripts/
│   ├── deploy.sh                           # Automated deployment
│   └── upload_sample_data.py               # Upload test data
│
├── .gitignore                              # Git ignore rules
├── README.md                               # This file
├── LICENSE                                 # MIT License
├── CONTRIBUTING.md                         # Contribution guidelines
├── requirements.txt                        # Python dependencies
└── config.json                             # Project configuration
```

## 🔧 Deployment

### Option 1: Automated Script (Recommended)

```bash
./scripts/deploy.sh
```

### Option 2: CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name customer-feedback-analysis \
  --template-body file://infrastructure/cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### Option 3: Terraform

```bash
cd infrastructure/terraform
terraform init
terraform apply
```

📖 [Detailed Setup Guide](./docs/setup.md)

## 💻 Usage

### Web Interface

1. **Submit Feedback**
   - Enter customer ID (optional)
   - Type or paste feedback text
   - Select category
   - Click "Analyze Feedback"

2. **View Results**
   - Sentiment classification with confidence scores
   - Extracted key phrases
   - Detected entities
   - Real-time charts and statistics

3. **Analytics Dashboard**
   - Total feedback count
   - Sentiment distribution (pie chart)
   - Average sentiment scores (bar chart)
   - Recent feedback history

### API Usage

**Analyze Feedback:**

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

**Get Analytics:**

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/analytics \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "get_analytics",
    "limit": 50
  }'
```

📖 [Full API Documentation](./docs/api_documentation.md)

## 🧪 Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

### Test Frontend Locally

```bash
cd frontend/public
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Upload Sample Data

```bash
# Update API endpoint in script first
python3 scripts/upload_sample_data.py
```

## 💰 Cost Estimation

### AWS Free Tier (First 12 Months)

- AWS Comprehend: 50,000 units/month free
- Lambda: 1M requests + 400,000 GB-seconds free
- DynamoDB: 25GB + 25 WCU/RCU free
- S3: 5GB storage free
- API Gateway: 1M API calls free

### Beyond Free Tier

**Estimated monthly cost for 10,000 feedback analyses:**

| Service | Usage | Cost |
|---------|-------|------|
| Comprehend | 10,000 units | $1.00 |
| Lambda | 10,000 invocations | $0.20 |
| DynamoDB | 10,000 writes | $1.25 |
| API Gateway | 10,000 requests | $0.04 |
| S3 | 5 GB storage | $0.12 |
| **Total** | | **~$2.61/month** |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS Comprehend for NLP capabilities
- Chart.js for data visualizations
- AWS CDK/CloudFormation for IaC templates

## 📞 Support

- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/customer-sentiment-analysis/issues)
- 📚 Docs: [Documentation](./docs/)

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Email notifications for negative feedback
- [ ] Batch processing for large datasets
- [ ] Trend analysis over time
- [ ] Export analytics to PDF/CSV
- [ ] Integration with Slack/Zendesk
- [ ] User authentication with Cognito
- [ ] Real-time WebSocket updates

---

**Built with ❤️ for learning AWS and serverless architectures**

*Perfect for demonstrating cloud development skills to potential employers!*
