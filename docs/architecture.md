# System Architecture

## Overview

The Customer Feedback Analysis System is a serverless application built on AWS that analyzes customer feedback using natural language processing (NLP) to extract sentiment, key phrases, and entities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users/Clients                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Static Website (S3)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HTML/CSS/JavaScript                                     │  │
│  │  - Feedback submission form                              │  │
│  │  - Real-time analytics dashboard                         │  │
│  │  - Data visualizations (Chart.js)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (REST API)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                              │  │
│  │  - POST /analyze    → Analyze feedback                   │  │
│  │  - POST /analytics  → Get aggregated analytics           │  │
│  │  - OPTIONS *        → CORS preflight                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────┬──────────────────────────┬────────────────────────┘
              │                          │
              ▼                          ▼
┌───────────────────────────┐  ┌────────────────────────────┐
│  Lambda: AnalyzeFeedback  │  │  Lambda: GetAnalytics      │
│  ┌──────────────────────┐ │  │  ┌───────────────────────┐ │
│  │ 1. Validate input    │ │  │  │ 1. Query DynamoDB     │ │
│  │ 2. Call Comprehend   │ │  │  │ 2. Aggregate data     │ │
│  │ 3. Store in DynamoDB │ │  │  │ 3. Calculate metrics  │ │
│  │ 4. Return results    │ │  │  │ 4. Return analytics   │ │
│  └──────────────────────┘ │  │  └───────────────────────┘ │
└──────────┬────────────────┘  └─────────────┬──────────────┘
           │                                  │
           │  ┌─────────────────────────────┘
           │  │
           ▼  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Services Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Comprehend  │  │  DynamoDB    │  │  CloudWatch Logs   │   │
│  │              │  │              │  │                    │   │
│  │ - Sentiment  │  │ Table:       │  │ - Lambda logs      │   │
│  │ - Key Phrases│  │  Feedback    │  │ - API logs         │   │
│  │ - Entities   │  │              │  │ - Metrics          │   │
│  │ - Language   │  │ Indexes:     │  │                    │   │
│  │              │  │  - timestamp │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Description

### 1. Frontend Layer (S3 Static Website)

**Technology**: HTML, CSS, JavaScript (ES6 Modules), Chart.js

**Files**:
- `public/index.html` - Main application page
- `src/css/style.css` - Styling and responsive design
- `src/js/app.js` - Main application logic
- `src/js/api.js` - API communication layer
- `src/js/charts.js` - Data visualization

**Features**:
- Responsive design for mobile and desktop
- Real-time feedback submission
- Interactive analytics dashboard
- Chart visualizations
- Mock data mode for local testing

### 2. API Layer (API Gateway)

**Type**: REST API (Regional)

**Endpoints**:

| Method | Path        | Lambda Function   | Purpose                  |
|--------|-------------|-------------------|--------------------------|
| POST   | /analyze    | AnalyzeFeedback   | Analyze customer feedback|
| POST   | /analytics  | GetAnalytics      | Retrieve analytics       |
| OPTIONS| /*          | N/A               | CORS preflight           |

**Features**:
- CORS enabled for cross-origin requests
- AWS_PROXY integration with Lambda
- Regional endpoint for low latency

### 3. Compute Layer (AWS Lambda)

#### AnalyzeFeedback Function

**Runtime**: Python 3.9  
**Timeout**: 60 seconds  
**Memory**: 256 MB

**Process Flow**:
1. Validate input (text length, required fields)
2. Call AWS Comprehend for:
   - Sentiment analysis
   - Key phrase extraction
   - Entity recognition
   - Language detection
3. Store results in DynamoDB
4. Return analysis results

**Environment Variables**:
- `DYNAMODB_TABLE` - Target DynamoDB table
- `AWS_REGION` - AWS region
- `MAX_TEXT_LENGTH` - Maximum feedback text length (5000)

#### GetAnalytics Function

**Runtime**: Python 3.9  
**Timeout**: 60 seconds  
**Memory**: 256 MB

**Process Flow**:
1. Query DynamoDB with limit
2. Aggregate sentiment distribution
3. Calculate average sentiment scores
4. Identify top customers by feedback volume
5. Return formatted analytics

### 4. NLP Layer (AWS Comprehend)

**Services Used**:
- **Sentiment Detection** - POSITIVE, NEGATIVE, NEUTRAL, MIXED
- **Key Phrase Extraction** - Important topics and themes
- **Entity Recognition** - People, organizations, locations, etc.
- **Language Detection** - Automatic language identification

**Input**: Text (max 5000 UTF-8 bytes)  
**Output**: JSON with scores and confidence levels

### 5. Data Layer (DynamoDB)

**Table**: CustomerFeedback

**Schema**:
```
Primary Key:
  - feedback_id (String, HASH)

Attributes:
  - feedback_id (String)
  - customer_id (String)
  - feedback_text (String)
  - timestamp (String, ISO 8601)
  - sentiment (String)
  - sentiment_scores (Map)
  - key_phrases (List)
  - entities (List)
  - language (Map)
  - metadata (Map)

Global Secondary Index:
  - timestamp-index (HASH: timestamp)
```

**Billing Mode**: PAY_PER_REQUEST (On-Demand)

### 6. Monitoring Layer (CloudWatch)

**Logs**:
- Lambda function execution logs
- API Gateway access logs
- Error tracking

**Metrics**:
- Lambda invocations
- Function duration
- Error rates
- API request count

## Data Flow

### Analyze Feedback Flow

```
User Input
    ↓
Frontend Validation
    ↓
API Gateway → POST /analyze
    ↓
Lambda: AnalyzeFeedback
    ├→ Validate Input
    ├→ AWS Comprehend
    │   ├→ Detect Sentiment
    │   ├→ Extract Key Phrases
    │   ├→ Detect Entities
    │   └→ Detect Language
    ├→ Store in DynamoDB
    └→ Return Results
    ↓
Frontend Display
```

### Get Analytics Flow

```
User Request (Refresh)
    ↓
API Gateway → POST /analytics
    ↓
Lambda: GetAnalytics
    ├→ Query DynamoDB
    ├→ Aggregate Data
    │   ├→ Count sentiments
    │   ├→ Calculate averages
    │   ├→ Identify top customers
    │   └→ Format recent feedback
    └→ Return Analytics
    ↓
Frontend Update Charts
```

## Security Architecture

### IAM Roles and Permissions

**Lambda Execution Role**:
```json
{
  "Comprehend": [
    "comprehend:DetectSentiment",
    "comprehend:DetectEntities",
    "comprehend:DetectKeyPhrases",
    "comprehend:DetectDominantLanguage"
  ],
  "DynamoDB": [
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "dynamodb:Scan",
    "dynamodb:Query"
  ],
  "CloudWatch Logs": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ]
}
```

### Network Security

- **S3 Bucket**: Public read access for static website
- **API Gateway**: Public endpoint with CORS
- **Lambda**: Runs in AWS-managed VPC
- **DynamoDB**: AWS-managed, encrypted at rest

### Data Security

- All data encrypted in transit (HTTPS/TLS)
- DynamoDB encryption at rest (AWS-managed keys)
- No personally identifiable information (PII) stored
- Input validation on all user inputs

## Scalability

### Automatic Scaling

- **Lambda**: Automatic scaling up to account limits
- **API Gateway**: Handles up to 10,000 RPS by default
- **DynamoDB**: On-demand capacity, auto-scaling
- **Comprehend**: Automatic throughput management

### Performance Characteristics

- **Average Response Time**: < 2 seconds
- **P99 Response Time**: < 5 seconds
- **Concurrent Users**: Thousands (limited by Lambda concurrency)
- **Max Feedback Length**: 5000 characters

## Cost Optimization

### Strategies

1. **Lambda**: Right-sized memory allocation (256 MB)
2. **DynamoDB**: On-demand billing for variable workloads
3. **S3**: Static website hosting (minimal cost)
4. **Comprehend**: Batch processing for high volume (future)

### Cost Breakdown (Estimated)

| Service       | Usage                  | Cost/Month      |
|---------------|------------------------|-----------------|
| Lambda        | 10,000 invocations     | $0.20          |
| API Gateway   | 10,000 requests        | $0.04          |
| DynamoDB      | 10,000 writes          | $1.25          |
| Comprehend    | 10,000 units           | $1.00          |
| S3            | 5 GB storage           | $0.12          |
| **Total**     |                        | **~$2.61**     |

## Future Enhancements

1. **CloudFront CDN** - Global content delivery
2. **Cognito Authentication** - User management
3. **SQS Queue** - Asynchronous processing
4. **ElastiCache** - Response caching
5. **Step Functions** - Complex workflows
6. **EventBridge** - Event-driven architecture
