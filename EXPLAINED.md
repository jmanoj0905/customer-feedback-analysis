# Customer Feedback Analysis System - Complete Technical Explanation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Flow Detailed Walkthrough](#data-flow-detailed-walkthrough)
4. [File-by-File Explanation](#file-by-file-explanation)
5. [Component Interactions](#component-interactions)
6. [Deployment Process](#deployment-process)
7. [Request-Response Cycle](#request-response-cycle)

---

## Project Overview

This is a serverless application built on AWS that analyzes customer feedback using natural language processing. The system uses AWS Comprehend (a machine learning service) to perform sentiment analysis, extract key phrases, and identify entities in customer feedback text.

### Core Functionality

The system performs three main operations:

1. **Sentiment Analysis**: Classifies feedback as POSITIVE, NEGATIVE, NEUTRAL, or MIXED
2. **Key Phrase Extraction**: Identifies important topics and themes in the feedback
3. **Entity Recognition**: Detects people, organizations, locations, and other named entities
4. **Analytics Aggregation**: Provides statistical analysis of all collected feedback

### Technology Stack

- **Backend**: AWS Lambda (Python 3.9)
- **AI/ML**: AWS Comprehend
- **Database**: Amazon DynamoDB (NoSQL)
- **API**: Amazon API Gateway (REST)
- **Storage**: Amazon S3 (static website hosting)
- **Frontend**: Vanilla JavaScript (ES6 modules), HTML5, CSS3
- **Infrastructure**: CloudFormation and Terraform
- **Visualization**: Chart.js

---

## System Architecture

### High-Level Architecture

```
User Browser
    |
    | (HTTPS)
    v
S3 Static Website (Frontend)
    |
    | (REST API Call)
    v
API Gateway
    |
    | (Invokes)
    v
Lambda Functions
    |
    +---> AWS Comprehend (NLP Analysis)
    |
    +---> DynamoDB (Data Storage)
    |
    v
Response back to User
```

### AWS Services and Their Roles

**Amazon S3**: Hosts the static website files (HTML, CSS, JavaScript). When users visit the application, they download these files from S3.

**API Gateway**: Acts as the HTTP endpoint that the frontend calls. It receives POST requests and routes them to the appropriate Lambda function.

**AWS Lambda**: Serverless compute service that runs the backend code. There are two Lambda functions:
- `analyze_feedback`: Processes new feedback submissions
- `get_analytics`: Retrieves and aggregates existing feedback data

**AWS Comprehend**: Machine learning service that performs natural language processing. It analyzes text to determine sentiment, extract key phrases, and identify entities.

**DynamoDB**: NoSQL database that stores all analyzed feedback along with the analysis results.

**CloudWatch**: Logging and monitoring service (automatic with Lambda).

---

## Data Flow Detailed Walkthrough

### Scenario 1: User Submits New Feedback

#### Step 1: User Input (Frontend)

File: `frontend/public/index.html`

The user opens the webpage and sees a form with:
- Customer ID field (optional)
- Feedback text area (required)
- Category dropdown (optional)

When the user types feedback like "This product is amazing!" and clicks "Analyze Feedback", the following happens:

#### Step 2: Form Submission Handler

File: `frontend/src/js/app.js`

The `handleFeedbackSubmit` function is triggered:

```javascript
async function handleFeedbackSubmit(e) {
    e.preventDefault();
    
    const feedbackText = document.getElementById("feedbackText").value.trim();
    const customerId = document.getElementById("customerId").value.trim() || "anonymous";
    const category = document.getElementById("category").value;
    
    // Call API to analyze feedback
    const result = await analyzeFeedback({
        feedback: feedbackText,
        customer_id: customerId,
        metadata: { category: category }
    });
}
```

This function:
1. Extracts form values
2. Shows loading state (disables button, shows spinner)
3. Calls the `analyzeFeedback` function from the API module

#### Step 3: API Request

File: `frontend/src/js/api.js`

The `analyzeFeedback` function constructs and sends an HTTP POST request:

```javascript
export async function analyzeFeedback(data) {
    const response = await fetch(CONFIG.API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            operation: "analyze_feedback",
            ...data
        })
    });
    
    return await response.json();
}
```

The request body looks like:
```json
{
    "operation": "analyze_feedback",
    "feedback": "This product is amazing!",
    "customer_id": "CUST123",
    "metadata": {
        "category": "product"
    }
}
```

This request is sent to the API Gateway endpoint (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod/analyze`).

#### Step 4: API Gateway Processing

File: `infrastructure/cloudformation/template.yaml` (defines API Gateway)

API Gateway receives the POST request and:
1. Validates the request format
2. Adds CORS headers
3. Invokes the Lambda function using AWS_PROXY integration
4. Passes the entire HTTP request as an event object to Lambda

The event object passed to Lambda contains:
- `httpMethod`: "POST"
- `body`: JSON string of the request payload
- `headers`: HTTP headers
- `path`, `queryStringParameters`, etc.

#### Step 5: Lambda Function Execution

File: `backend/lambda/analyze_feedback/lambda_function.py`

The `lambda_handler` function is invoked:

```python
def lambda_handler(event, context):
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, '')
    
    # Parse request body
    body = parse_request_body(event)
    
    # Extract parameters
    feedback_text = body.get('feedback', '')
    customer_id = body.get('customer_id', 'anonymous')
    metadata = body.get('metadata', {})
    
    # Validate input
    is_valid, error_message = validate_text_input(feedback_text)
    if not is_valid:
        return error_response(error_message, 400)
    
    # Perform comprehensive analysis
    analysis = analyze_feedback(feedback_text, customer_id, metadata)
    
    # Store results in DynamoDB
    store_feedback(analysis)
    
    # Return success response
    return success_response(analysis)
```

The function performs these steps:

**5a. Request Parsing**

The `parse_request_body` function extracts the JSON payload from the event:

```python
def parse_request_body(event: dict) -> dict:
    body = event.get('body', {})
    
    if isinstance(body, str):
        return json.loads(body)
    
    return body
```

**5b. Input Validation**

The `validate_text_input` function checks:
- Text is not empty
- Text length does not exceed 5000 characters (AWS Comprehend limit)

```python
def validate_text_input(text: str) -> tuple:
    if not text or len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    if len(text) > config.MAX_TEXT_LENGTH:
        return False, f"Text exceeds maximum length"
    
    return True, ""
```

#### Step 6: AWS Comprehend Analysis

File: `backend/lambda/analyze_feedback/lambda_function.py` (analyze_feedback function)

The function makes four separate calls to AWS Comprehend:

**6a. Sentiment Analysis**

```python
sentiment_response = comprehend.detect_sentiment(
    Text=feedback_text,
    LanguageCode='en'
)
```

Comprehend returns:
```json
{
    "Sentiment": "POSITIVE",
    "SentimentScore": {
        "Positive": 0.95,
        "Negative": 0.01,
        "Neutral": 0.03,
        "Mixed": 0.01
    }
}
```

This tells us the feedback is 95% positive, 1% negative, 3% neutral, and 1% mixed.

**6b. Key Phrase Extraction**

```python
key_phrases_response = comprehend.detect_key_phrases(
    Text=feedback_text,
    LanguageCode='en'
)
```

Comprehend returns:
```json
{
    "KeyPhrases": [
        {"Text": "amazing product", "Score": 0.99},
        {"Text": "best purchase", "Score": 0.95}
    ]
}
```

**6c. Entity Recognition**

```python
entities_response = comprehend.detect_entities(
    Text=feedback_text,
    LanguageCode='en'
)
```

Comprehend returns:
```json
{
    "Entities": [
        {"Text": "product", "Type": "COMMERCIAL_ITEM", "Score": 0.85}
    ]
}
```

**6d. Language Detection**

```python
language_response = comprehend.detect_dominant_language(
    Text=feedback_text
)
```

Comprehend returns:
```json
{
    "Languages": [
        {"LanguageCode": "en", "Score": 0.99}
    ]
}
```

**6e. Data Compilation**

The Lambda function combines all results:

```python
result = {
    'feedback_id': 'feedback_1700000000000',
    'customer_id': 'CUST123',
    'feedback_text': 'This product is amazing!',
    'timestamp': '2024-01-15T10:30:00.000Z',
    'sentiment': 'POSITIVE',
    'sentiment_scores': {
        'positive': 0.95,
        'negative': 0.01,
        'neutral': 0.03,
        'mixed': 0.01
    },
    'key_phrases': [
        {'text': 'amazing product', 'score': 0.99}
    ],
    'entities': [
        {'text': 'product', 'type': 'COMMERCIAL_ITEM', 'score': 0.85}
    ],
    'language': {
        'language_code': 'en',
        'score': 0.99
    },
    'metadata': {
        'category': 'product'
    }
}
```

#### Step 7: DynamoDB Storage

File: `backend/lambda/analyze_feedback/lambda_function.py` (store_feedback function)

The `store_feedback` function saves the analysis to DynamoDB:

```python
def store_feedback(feedback_data: dict) -> None:
    table = dynamodb.Table(config.DYNAMODB_TABLE)
    
    # Convert floats to Decimal for DynamoDB
    item = json.loads(json.dumps(feedback_data), parse_float=Decimal)
    
    table.put_item(Item=item)
```

DynamoDB stores the item with:
- **Primary Key**: `feedback_id` (e.g., "feedback_1700000000000")
- **Attributes**: All the analysis results

The data is now persisted in DynamoDB for future retrieval.

#### Step 8: Response to Frontend

The Lambda function returns a response:

```python
def success_response(data: dict, status_code: int = 200) -> dict:
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,...',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(data)
    }
```

API Gateway receives this response and forwards it to the frontend.

#### Step 9: Frontend Display

File: `frontend/src/js/app.js` (displayAnalysisResult function)

The frontend receives the response and displays it:

```javascript
function displayAnalysisResult(result) {
    // Show sentiment badge
    const sentimentBadge = document.getElementById("sentimentBadge");
    sentimentBadge.textContent = result.sentiment; // "POSITIVE"
    sentimentBadge.className = `sentiment-badge ${result.sentiment}`;
    
    // Show sentiment scores
    const scores = result.sentiment_scores;
    document.getElementById("positiveScore").textContent = 
        `${(scores.positive * 100).toFixed(1)}%`; // "95.0%"
    
    // Display key phrases
    const keyPhrasesDiv = document.getElementById("keyPhrases");
    keyPhrasesDiv.innerHTML = result.key_phrases
        .map(phrase => `<span class="phrase-tag">${phrase.text}</span>`)
        .join("");
    
    // Display entities
    const entitiesDiv = document.getElementById("entities");
    entitiesDiv.innerHTML = result.entities
        .map(entity => `<span class="entity-tag">${entity.text} (${entity.type})</span>`)
        .join("");
}
```

The user now sees:
- A green "POSITIVE" badge
- Sentiment scores: Positive 95.0%, Negative 1.0%, etc.
- Key phrases in tags: "amazing product"
- Detected entities: "product (COMMERCIAL_ITEM)"

#### Step 10: Dashboard Update

File: `frontend/src/js/app.js`

After displaying the result, the frontend automatically refreshes the analytics:

```javascript
setTimeout(() => loadAnalytics(), 500);
```

This triggers the analytics retrieval flow (see Scenario 2 below).

---

### Scenario 2: User Views Analytics Dashboard

#### Step 1: Analytics Request

File: `frontend/src/js/app.js` (loadAnalytics function)

When the page loads or the user clicks "Refresh", this function is called:

```javascript
async function loadAnalytics() {
    const analytics = await getAnalytics(50);
    
    // Update statistics
    document.getElementById("totalFeedback").textContent = 
        analytics.total_feedback;
    document.getElementById("positiveCount").textContent = 
        analytics.sentiment_distribution.POSITIVE;
    
    // Update charts
    updateSentimentChart(analytics.sentiment_distribution);
    updateScoresChart(analytics.average_sentiment_scores);
    
    // Display recent feedback
    displayRecentFeedback(analytics.recent_feedback);
}
```

#### Step 2: API Call to Get Analytics

File: `frontend/src/js/api.js`

```javascript
export async function getAnalytics(limit = 50) {
    const response = await fetch(CONFIG.API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            operation: "get_analytics",
            limit: limit
        })
    });
    
    return await response.json();
}
```

Request sent to API Gateway:
```json
{
    "operation": "get_analytics",
    "limit": 50
}
```

#### Step 3: Analytics Lambda Execution

File: `backend/lambda/get_analytics/lambda_function.py`

The Lambda handler processes the request:

```python
def lambda_handler(event, context):
    body = parse_request_body(event)
    limit = min(body.get('limit', 50), 1000)
    
    analytics = get_analytics(limit)
    
    return success_response(analytics)
```

**3a. DynamoDB Scan**

The `get_analytics` function scans the DynamoDB table:

```python
def get_analytics(limit: int) -> Dict[str, Any]:
    table = dynamodb.Table(config.DYNAMODB_TABLE)
    
    # Scan table with limit
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    
    # Convert Decimal to float for JSON serialization
    items = json.loads(json.dumps(items, default=decimal_to_float))
    
    # Calculate aggregated statistics
    analytics = calculate_analytics(items)
    
    return analytics
```

**3b. Analytics Calculation**

The `calculate_analytics` function processes all retrieved items:

```python
def calculate_analytics(items: List[Dict]) -> Dict[str, Any]:
    total_feedback = len(items)
    
    # Count sentiments
    sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0}
    
    for item in items:
        sentiment = item.get('sentiment', 'NEUTRAL')
        sentiment_counts[sentiment] += 1
    
    # Calculate average scores
    avg_scores = {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0}
    
    for item in items:
        scores = item.get('sentiment_scores', {})
        for key in avg_scores:
            avg_scores[key] += scores.get(key, 0)
    
    if total_feedback > 0:
        for key in avg_scores:
            avg_scores[key] = avg_scores[key] / total_feedback
    
    # Track category breakdown
    category_sentiment = {}
    for item in items:
        category = item.get('metadata', {}).get('category', 'uncategorized')
        sentiment = item.get('sentiment', 'NEUTRAL')
        
        if category not in category_sentiment:
            category_sentiment[category] = {
                'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0
            }
        category_sentiment[category][sentiment] += 1
    
    return {
        'total_feedback': total_feedback,
        'sentiment_distribution': sentiment_counts,
        'average_sentiment_scores': avg_scores,
        'category_breakdown': category_sentiment,
        'recent_feedback': items[:10]
    }
```

Example response:
```json
{
    "total_feedback": 150,
    "sentiment_distribution": {
        "POSITIVE": 85,
        "NEGATIVE": 20,
        "NEUTRAL": 40,
        "MIXED": 5
    },
    "average_sentiment_scores": {
        "positive": 0.52,
        "negative": 0.15,
        "neutral": 0.28,
        "mixed": 0.05
    },
    "category_breakdown": {
        "product": {
            "POSITIVE": 45,
            "NEGATIVE": 10,
            "NEUTRAL": 15,
            "MIXED": 2
        }
    },
    "recent_feedback": [...]
}
```

#### Step 4: Chart Updates

File: `frontend/src/js/charts.js`

The frontend uses Chart.js to visualize the data:

**4a. Sentiment Distribution Chart**

```javascript
export function updateSentimentChart(distribution) {
    sentimentChart.data.datasets[0].data = [
        distribution.POSITIVE,
        distribution.NEGATIVE,
        distribution.NEUTRAL,
        distribution.MIXED
    ];
    sentimentChart.update();
}
```

This creates a doughnut chart showing the breakdown of sentiments.

**4b. Average Scores Chart**

```javascript
export function updateScoresChart(scores) {
    scoresChart.data.datasets[0].data = [
        scores.positive,
        scores.negative,
        scores.neutral,
        scores.mixed
    ];
    scoresChart.update();
}
```

This creates a bar chart showing average sentiment scores.

#### Step 5: Recent Feedback Display

File: `frontend/src/js/app.js` (displayRecentFeedback function)

```javascript
function displayRecentFeedback(feedbackList) {
    const listDiv = document.getElementById("recentFeedbackList");
    
    listDiv.innerHTML = feedbackList
        .map(item => `
            <div class="feedback-item">
                <div class="feedback-header">
                    <span class="feedback-id">${item.customer_id}</span>
                    <span class="feedback-sentiment ${item.sentiment}">
                        ${item.sentiment}
                    </span>
                </div>
                <div class="feedback-text">${truncateText(item.feedback_text, 150)}</div>
                <div class="feedback-timestamp">${formatTimestamp(item.timestamp)}</div>
            </div>
        `)
        .join("");
}
```

This displays the 10 most recent feedback items with their sentiment badges.

---

## File-by-File Explanation

### Frontend Files

#### `frontend/public/index.html`

The main HTML page that users see. Contains:

- **Form Section**: Input fields for customer ID, feedback text, and category
- **Results Section**: Displays analysis results (hidden until feedback is analyzed)
- **Analytics Dashboard**: Shows charts and statistics
- **Script Imports**: Loads Chart.js library and the main app.js module

Key elements:
```html
<form id="feedbackForm">
    <textarea id="feedbackText"></textarea>
    <button type="submit">Analyze Feedback</button>
</form>

<div id="analysisResult" style="display: none">
    <div id="sentimentBadge"></div>
    <div id="keyPhrases"></div>
</div>

<canvas id="sentimentChart"></canvas>
<canvas id="scoresChart"></canvas>
```

#### `frontend/src/css/style.css`

Stylesheet that provides:

- **Responsive Layout**: Grid system for two-column layout (form on left, analytics on right)
- **Component Styling**: Cards, buttons, forms, badges
- **Color Scheme**: CSS variables for consistent theming
- **Sentiment Colors**: Green for positive, red for negative, gray for neutral, yellow for mixed
- **Animations**: Loading spinners, transitions, hover effects

Example CSS variables:
```css
:root {
    --primary-color: #4f46e5;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    --neutral-color: #6b7280;
}
```

#### `frontend/src/js/app.js`

Main application logic. Responsibilities:

- **Event Handling**: Form submissions, button clicks
- **DOM Manipulation**: Updates HTML elements with data
- **Application Flow**: Coordinates between API calls and UI updates
- **User Feedback**: Shows loading states, error messages, success notifications

Key functions:
- `handleFeedbackSubmit()`: Processes form submission
- `displayAnalysisResult()`: Shows analysis on page
- `loadAnalytics()`: Fetches and displays dashboard data
- `updateCharCount()`: Shows character count for textarea
- `showToast()`: Displays notification messages

#### `frontend/src/js/api.js`

API communication layer. Responsibilities:

- **HTTP Requests**: Makes fetch calls to API Gateway
- **Request Formatting**: Constructs JSON payloads
- **Response Parsing**: Converts JSON responses to JavaScript objects
- **Mock Data Mode**: Generates fake data for local testing
- **Error Handling**: Catches network errors and timeouts

Key functions:
- `analyzeFeedback()`: Sends feedback to backend
- `getAnalytics()`: Retrieves analytics data
- `generateMockAnalysis()`: Creates fake analysis for testing
- `fetchWithTimeout()`: Adds timeout to fetch requests

#### `frontend/src/js/charts.js`

Chart management using Chart.js. Responsibilities:

- **Chart Initialization**: Creates Chart.js instances
- **Chart Updates**: Updates chart data without recreation
- **Chart Configuration**: Sets colors, labels, tooltips
- **Chart Cleanup**: Destroys charts when needed

Key functions:
- `initializeCharts()`: Creates initial empty charts
- `updateSentimentChart()`: Updates pie chart with new data
- `updateScoresChart()`: Updates bar chart with new data

#### `frontend/package.json`

Node.js package configuration for frontend development tools:

```json
{
    "name": "customer-feedback-analysis-frontend",
    "scripts": {
        "dev": "python3 -m http.server 8000 --directory public",
        "lint": "eslint src/js/**/*.js",
        "format": "prettier --write 'src/**/*.{js,css,html}'"
    },
    "devDependencies": {
        "eslint": "^8.45.0",
        "prettier": "^3.0.0"
    }
}
```

### Backend Files

#### `backend/lambda/analyze_feedback/lambda_function.py`

The main Lambda function for analyzing feedback. Process flow:

1. Receive event from API Gateway
2. Parse JSON body from request
3. Validate input text
4. Call AWS Comprehend for sentiment, key phrases, entities, language
5. Combine all results into single object
6. Store in DynamoDB
7. Return results to frontend

Key components:
- `lambda_handler()`: Main entry point
- `analyze_feedback()`: Performs Comprehend calls
- `store_feedback()`: Saves to DynamoDB
- `validate_text_input()`: Checks input validity
- CORS response helpers

#### `backend/lambda/analyze_feedback/config.py`

Configuration constants for the analyze_feedback Lambda:

```python
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')
COMPREHEND_LANGUAGE = os.environ.get('COMPREHEND_LANGUAGE', 'en')
MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 5000))
MAX_KEY_PHRASES = int(os.environ.get('MAX_KEY_PHRASES', 5))
MAX_ENTITIES = int(os.environ.get('MAX_ENTITIES', 5))
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
```

These can be overridden by Lambda environment variables.

#### `backend/lambda/analyze_feedback/requirements.txt`

Python dependencies for the Lambda function:

```
boto3>=1.26.0
botocore>=1.29.0
```

Note: boto3 is already available in AWS Lambda environment, but this file documents the dependency.

#### `backend/lambda/get_analytics/lambda_function.py`

Lambda function for retrieving analytics. Process flow:

1. Receive request with limit parameter
2. Scan DynamoDB table (up to limit)
3. Aggregate data: count sentiments, calculate averages
4. Group by category
5. Identify top customers by feedback volume
6. Return comprehensive analytics object

Key components:
- `lambda_handler()`: Main entry point
- `get_analytics()`: Retrieves from DynamoDB
- `calculate_analytics()`: Performs aggregations
- `get_empty_analytics()`: Returns default structure if no data

#### `backend/lambda/get_analytics/config.py`

Configuration for the analytics Lambda:

```python
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')
DEFAULT_LIMIT = int(os.environ.get('DEFAULT_LIMIT', 50))
MAX_LIMIT = int(os.environ.get('MAX_LIMIT', 1000))
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
```

#### `backend/utils/comprehend_helper.py`

Reusable helper class for AWS Comprehend operations. This is a utility module for local development and testing, but the Lambda functions have Comprehend calls integrated directly for deployment simplicity.

Features:
- `ComprehendHelper` class with methods for each Comprehend operation
- `detect_sentiment()`: Returns sentiment and scores
- `extract_key_phrases()`: Returns key phrases with confidence
- `detect_entities()`: Returns entities with types
- `detect_language()`: Returns language code
- `analyze_comprehensive()`: Performs all analyses at once
- `validate_text_input()`: Input validation utility

### Infrastructure Files

#### `infrastructure/cloudformation/template.yaml`

AWS CloudFormation template that defines all infrastructure. Resources created:

**DynamoDB Table**:
```yaml
FeedbackTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: customer-feedback-analysis-prod-feedback
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: feedback_id
        AttributeType: S
    KeySchema:
      - AttributeName: feedback_id
        KeyType: HASH
```

**S3 Bucket for Website**:
```yaml
WebsiteBucket:
  Type: AWS::S3::Bucket
  Properties:
    WebsiteConfiguration:
      IndexDocument: index.html
```

**IAM Role for Lambda**:
```yaml
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    Policies:
      - PolicyName: ComprehendAccess
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - comprehend:DetectSentiment
                - comprehend:DetectEntities
                - comprehend:DetectKeyPhrases
```

**Lambda Functions**:
```yaml
AnalyzeFeedbackFunction:
  Type: AWS::Lambda::Function
  Properties:
    Runtime: python3.9
    Handler: lambda_function.lambda_handler
    Role: !GetAtt LambdaExecutionRole.Arn
```

**API Gateway**:
```yaml
FeedbackAPI:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: customer-feedback-analysis-prod-api
```

#### `infrastructure/terraform/main.tf`

Terraform configuration (alternative to CloudFormation). Creates the same resources using HashiCorp Configuration Language (HCL):

```hcl
resource "aws_dynamodb_table" "feedback_table" {
  name           = "${var.project_name}-${var.environment}-feedback"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "feedback_id"
  
  attribute {
    name = "feedback_id"
    type = "S"
  }
}

resource "aws_lambda_function" "analyze_feedback" {
  filename      = "../../backend/lambda/analyze_feedback/lambda_deployment.zip"
  function_name = "${var.project_name}-${var.environment}-analyze-feedback"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
}
```

#### `infrastructure/terraform/variables.tf`

Terraform input variables:

```hcl
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "customer-feedback-analysis"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}
```

#### `infrastructure/terraform/outputs.tf`

Terraform outputs (values returned after deployment):

```hcl
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_deployment.api_deployment.invoke_url}"
}

output "website_url" {
  description = "S3 website URL"
  value       = "http://${aws_s3_bucket.website_bucket.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}
```

### Configuration Files

#### `config.json`

Project-wide configuration:

```json
{
  "aws": {
    "region": "us-east-1",
    "profile": "default"
  },
  "lambda": {
    "function_name": "CustomerFeedbackAnalyzer",
    "runtime": "python3.9",
    "timeout": 60,
    "memory_size": 256
  },
  "dynamodb": {
    "table_name": "CustomerFeedback",
    "read_capacity": 5,
    "write_capacity": 5
  },
  "s3": {
    "bucket_name": "customer-feedback-analysis-bucket",
    "website_bucket": "customer-feedback-website"
  },
  "comprehend": {
    "language_code": "en",
    "max_text_length": 5000
  }
}
```

#### `requirements.txt`

Python dependencies for local development and testing:

```
boto3>=1.26.0
pytest>=7.4.0
pytest-cov>=4.1.0
moto>=4.1.0
pylint>=2.17.0
black>=23.3.0
```

#### `.gitignore`

Specifies files to exclude from version control:

```
__pycache__/
*.pyc
venv/
.env
*.zip
deployment-package/
node_modules/
.DS_Store
```

### Script Files

#### `scripts/deploy.sh`

Automated deployment script. Process:

1. **Check Prerequisites**: Verify AWS CLI, Python are installed
2. **Create Deployment Packages**: 
   - Install dependencies in Lambda directories
   - Create ZIP files for Lambda deployment
3. **Deploy CloudFormation Stack**:
   - Create or update stack
   - Wait for completion
4. **Update Lambda Code**:
   - Upload new ZIP files to existing Lambda functions
5. **Deploy Frontend**:
   - Upload HTML/CSS/JS to S3 bucket
6. **Display Outputs**:
   - Show API endpoint, website URL

Key functions:
```bash
create_deployment_packages() {
    cd backend/lambda/analyze_feedback
    pip3 install -r requirements.txt -t .
    zip -r lambda_deployment.zip .
}

deploy_cloudformation() {
    aws cloudformation create-stack \
        --stack-name customer-feedback-analysis-prod \
        --template-body file://infrastructure/cloudformation/template.yaml \
        --capabilities CAPABILITY_NAMED_IAM
}
```

#### `scripts/upload_sample_data.py`

Python script to upload test data. Process:

1. Load sample feedback from `data/sample_feedback.json`
2. For each feedback item:
   - Send POST request to API endpoint
   - Wait for response
   - Print results
3. Display summary statistics

Usage:
```bash
python3 scripts/upload_sample_data.py
```

#### `scripts/validate_project.sh`

Validation script that checks:

- Python syntax (all .py files)
- JavaScript syntax (all .js files)
- JSON validity (all .json files)
- Shell script syntax (all .sh files)
- Required files exist
- Required directories exist

Outputs color-coded results and exits with error code if any checks fail.

### Test Files

#### `tests/test_lambda.py`

Unit tests for Lambda functions using pytest and mocking:

```python
@patch('boto3.client')
def test_analyze_feedback_positive_sentiment(mock_comprehend):
    # Mock Comprehend response
    mock_comprehend.return_value.detect_sentiment.return_value = {
        'Sentiment': 'POSITIVE',
        'SentimentScore': {'Positive': 0.95, ...}
    }
    
    # Test function
    result = analyze_feedback("Great product!", "TEST001", {})
    
    # Assert
    assert result['sentiment'] == 'POSITIVE'
```

Test coverage includes:
- Sentiment analysis with various inputs
- Input validation
- Error handling
- DynamoDB operations (mocked)
- API response formatting

#### `tests/sample_requests.json`

Example API requests for manual testing:

```json
{
  "analyze_feedback_request": {
    "operation": "analyze_feedback",
    "feedback": "This product exceeded my expectations!",
    "customer_id": "CUST001",
    "metadata": {
      "category": "product"
    }
  },
  "get_analytics_request": {
    "operation": "get_analytics",
    "limit": 50
  }
}
```

Can be used with curl or Postman for API testing.

### Data Files

#### `data/sample_feedback.json`

20 realistic customer feedback examples with varied sentiments:

```json
[
  {
    "customer_id": "CUST001",
    "feedback": "The product quality is excellent! Very satisfied.",
    "category": "product",
    "expected_sentiment": "POSITIVE"
  },
  {
    "customer_id": "CUST002",
    "feedback": "Terrible experience. Item arrived damaged.",
    "category": "service",
    "expected_sentiment": "NEGATIVE"
  }
]
```

Used for testing and demonstration purposes.

### Documentation Files

#### `README.md`

Main project documentation with:
- Quick start guide
- Architecture overview
- Feature list
- Deployment instructions
- API usage examples
- Cost estimation
- Screenshots and badges

#### `docs/architecture.md`

Detailed technical architecture documentation:
- System diagram
- Component descriptions
- Data flow diagrams
- Security architecture
- Scalability considerations
- Cost breakdown

#### `docs/setup.md`

Step-by-step setup guide:
- Prerequisites and requirements
- Installation instructions
- Configuration steps
- Deployment options
- Troubleshooting guide
- Testing procedures

#### `docs/api_documentation.md`

Complete API reference:
- Endpoint descriptions
- Request/response formats
- Error codes
- Rate limits
- Code examples in multiple languages
- Best practices

#### `CONTRIBUTING.md`

Guidelines for contributors:
- Code of conduct
- How to report bugs
- Pull request process
- Coding standards
- Development setup
- Testing requirements

#### `LICENSE`

MIT License - allows free use, modification, and distribution.

#### `PROJECT_SUMMARY.md`

Resume-focused summary:
- Skills demonstrated
- Talking points for interviews
- Demo script
- How to showcase the project

---

## Component Interactions

### Frontend to Backend

**Request Flow**:
1. User action in browser
2. JavaScript event handler triggered
3. API module constructs HTTP request
4. Fetch API sends request to API Gateway
5. API Gateway invokes Lambda
6. Lambda processes and returns response
7. API Gateway forwards response
8. JavaScript receives and parses response
9. DOM updated to display results

**Data Format**:
All communication uses JSON over HTTPS with CORS headers.

### Lambda to AWS Services

**AWS Comprehend**:
- Lambda uses boto3 SDK to call Comprehend
- Synchronous API calls
- Each analysis type is a separate API call
- Charged per unit (100 characters)

**DynamoDB**:
- Lambda uses boto3 SDK for table operations
- PUT operations to store feedback
- SCAN operations to retrieve analytics
- Automatic retry logic built into SDK

### Infrastructure Components

**CloudFormation/Terraform to AWS**:
- Infrastructure as Code defines desired state
- CloudFormation/Terraform creates resources via AWS APIs
- Resources are linked via references (ARNs, IDs)
- Outputs are generated after successful deployment

---

## Deployment Process

### Manual Deployment Steps

1. **Package Lambda Functions**:
```bash
cd backend/lambda/analyze_feedback
pip install -r requirements.txt -t .
zip -r deployment.zip .
```

2. **Create CloudFormation Stack**:
```bash
aws cloudformation create-stack \
  --stack-name customer-feedback-analysis \
  --template-body file://infrastructure/cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

3. **Wait for Stack Creation**:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name customer-feedback-analysis
```

4. **Upload Lambda Code**:
```bash
aws lambda update-function-code \
  --function-name CustomerFeedbackAnalyzer \
  --zip-file fileb://deployment.zip
```

5. **Deploy Frontend**:
```bash
aws s3 sync frontend/public s3://your-bucket-name/
```

6. **Get Outputs**:
```bash
aws cloudformation describe-stacks \
  --stack-name customer-feedback-analysis \
  --query 'Stacks[0].Outputs'
```

### Automated Deployment

Run the deployment script:
```bash
./scripts/deploy.sh
```

This executes all manual steps automatically.

---

## Request-Response Cycle

### Complete Cycle Example

**User Action**: User types "Great service!" and clicks "Analyze"

**Frontend Processing**:
```
index.html → app.js (handleFeedbackSubmit)
    ↓
api.js (analyzeFeedback)
    ↓
HTTP POST to API Gateway
```

**Request**:
```http
POST https://abc123.execute-api.us-east-1.amazonaws.com/prod/analyze
Content-Type: application/json

{
  "operation": "analyze_feedback",
  "feedback": "Great service!",
  "customer_id": "CUST123",
  "metadata": {"category": "service"}
}
```

**API Gateway**:
```
Receives POST request
    ↓
Validates request format
    ↓
Invokes Lambda with event object
```

**Lambda Processing**:
```
lambda_handler receives event
    ↓
parse_request_body extracts JSON
    ↓
validate_text_input checks input
    ↓
analyze_feedback calls Comprehend
    ↓
    ├─ detect_sentiment
    ├─ detect_key_phrases
    ├─ detect_entities
    └─ detect_dominant_language
    ↓
Combine all results
    ↓
store_feedback saves to DynamoDB
    ↓
Return success_response
```

**Comprehend Processing** (for each call):
```
Receive text from Lambda
    ↓
Apply ML model
    ↓
Generate predictions
    ↓
Return JSON with scores
```

**DynamoDB Storage**:
```
Receive put_item request
    ↓
Validate item structure
    ↓
Store in table
    ↓
Return success confirmation
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *

{
  "feedback_id": "feedback_1700000000000",
  "sentiment": "POSITIVE",
  "sentiment_scores": {
    "positive": 0.89,
    "negative": 0.02,
    "neutral": 0.08,
    "mixed": 0.01
  },
  "key_phrases": [
    {"text": "Great service", "score": 0.99}
  ],
  "entities": [],
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Frontend Display**:
```
app.js receives response
    ↓
displayAnalysisResult updates DOM
    ↓
    ├─ Show "POSITIVE" badge (green)
    ├─ Display scores: 89% positive
    ├─ Show key phrase: "Great service"
    └─ Make results visible
    ↓
loadAnalytics refreshes dashboard
    ↓
charts.js updates visualizations
```

**Total Time**: Typically 1-3 seconds from submit to display

---

## Summary

This system demonstrates a complete serverless architecture where:

1. **Frontend** handles user interaction and display
2. **API Gateway** routes requests to appropriate Lambda functions
3. **Lambda Functions** orchestrate the business logic
4. **AWS Comprehend** provides AI-powered NLP analysis
5. **DynamoDB** stores all data persistently
6. **Infrastructure as Code** makes deployment repeatable and consistent

All components communicate via JSON over HTTPS, with proper error handling, validation, and CORS support. The architecture is scalable, cost-effective, and follows AWS best practices.
