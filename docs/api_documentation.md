# API Documentation

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Example:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

## Authentication

Currently, the API does not require authentication. For production use, consider implementing:
- API Keys
- AWS IAM authentication
- AWS Cognito user pools
- OAuth 2.0

## Common Headers

```http
Content-Type: application/json
```

## Endpoints

### 1. Analyze Feedback

Analyzes customer feedback using AWS Comprehend for sentiment analysis, key phrase extraction, and entity recognition.

**Endpoint**: `POST /analyze`

**Request Body**:
```json
{
  "operation": "analyze_feedback",
  "feedback": "string (required, max 5000 chars)",
  "customer_id": "string (optional)",
  "metadata": {
    "category": "string (optional)",
    "source": "string (optional)",
    "timestamp": "string (optional, ISO 8601)"
  }
}
```

**Request Example**:
```bash
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "analyze_feedback",
    "feedback": "This product is amazing! Best purchase ever!",
    "customer_id": "CUST123",
    "metadata": {
      "category": "product",
      "source": "web"
    }
  }'
```

**Success Response** (200 OK):
```json
{
  "feedback_id": "feedback_1234567890123",
  "customer_id": "CUST123",
  "feedback_text": "This product is amazing! Best purchase ever!",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "sentiment": "POSITIVE",
  "sentiment_scores": {
    "positive": 0.95,
    "negative": 0.01,
    "neutral": 0.03,
    "mixed": 0.01
  },
  "key_phrases": [
    {
      "text": "amazing product",
      "score": 0.99
    },
    {
      "text": "best purchase",
      "score": 0.95
    }
  ],
  "entities": [
    {
      "text": "product",
      "type": "COMMERCIAL_ITEM",
      "score": 0.85
    }
  ],
  "language": {
    "language_code": "en",
    "score": 1.0
  },
  "metadata": {
    "category": "product",
    "source": "web"
  }
}
```

**Error Responses**:

```json
// 400 Bad Request - Empty feedback
{
  "error": "Text cannot be empty"
}

// 400 Bad Request - Text too long
{
  "error": "Text exceeds maximum length of 5000 characters"
}

// 500 Internal Server Error
{
  "error": "Internal server error: <error message>"
}
```

---

### 2. Get Analytics

Retrieves aggregated analytics from all stored customer feedback.

**Endpoint**: `POST /analytics`

**Request Body**:
```json
{
  "operation": "get_analytics",
  "limit": 50  // Optional, default: 50, max: 1000
}
```

**Request Example**:
```bash
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/analytics \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "get_analytics",
    "limit": 100
  }'
```

**Success Response** (200 OK):
```json
{
  "total_feedback": 150,
  "sentiment_distribution": {
    "POSITIVE": 85,
    "NEGATIVE": 20,
    "NEUTRAL": 40,
    "MIXED": 5
  },
  "sentiment_percentages": {
    "POSITIVE": 56.67,
    "NEGATIVE": 13.33,
    "NEUTRAL": 26.67,
    "MIXED": 3.33
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
    },
    "service": {
      "POSITIVE": 30,
      "NEGATIVE": 8,
      "NEUTRAL": 20,
      "MIXED": 3
    }
  },
  "top_customers": [
    {
      "customer_id": "CUST001",
      "feedback_count": 15
    },
    {
      "customer_id": "CUST002",
      "feedback_count": 12
    }
  ],
  "recent_feedback": [
    {
      "feedback_id": "feedback_1234567890123",
      "customer_id": "CUST123",
      "feedback_text": "This product is amazing!",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "sentiment": "POSITIVE",
      "sentiment_scores": {
        "positive": 0.95,
        "negative": 0.01,
        "neutral": 0.03,
        "mixed": 0.01
      }
    }
  ],
  "timestamp": "2024-01-15T10:35:00.000Z",
  "total_retrieved": 100
}
```

**Error Response**:
```json
// 500 Internal Server Error
{
  "error": "Error retrieving analytics: <error message>"
}
```

---

## Data Models

### Sentiment Values

| Value | Description |
|-------|-------------|
| `POSITIVE` | The text contains positive sentiment |
| `NEGATIVE` | The text contains negative sentiment |
| `NEUTRAL` | The text is neutral or factual |
| `MIXED` | The text contains both positive and negative sentiment |

### Entity Types

Common entity types detected by AWS Comprehend:

| Type | Description | Example |
|------|-------------|---------|
| `PERSON` | People, including fictional characters | "John Smith" |
| `LOCATION` | Physical locations | "New York" |
| `ORGANIZATION` | Companies, agencies, institutions | "Amazon" |
| `COMMERCIAL_ITEM` | Products and services | "iPhone" |
| `EVENT` | Named events | "World Cup" |
| `DATE` | Dates and times | "January 15, 2024" |
| `QUANTITY` | Numerical quantities | "5 items" |
| `TITLE` | Titles of books, songs, etc. | "The Great Gatsby" |

## Rate Limits

### AWS Service Limits

- **AWS Comprehend**: 
  - 20 transactions per second (TPS) per operation
  - 100 KB max request size
  - 5000 UTF-8 characters max per text

- **Lambda**:
  - 1000 concurrent executions (default)
  - 6 MB max request/response payload

- **API Gateway**:
  - 10,000 requests per second (burst)
  - 5,000 requests per second (steady state)

### Recommended Client-Side Limits

- Max 10 requests per second
- Implement exponential backoff for retries
- Cache analytics data client-side (refresh every 30 seconds)

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 403 | Forbidden - Authentication required |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Temporary issue |

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) with the following headers:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization, X-Api-Key
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## Best Practices

### 1. Input Validation

Always validate input before sending to the API:

```javascript
function validateFeedback(text) {
  if (!text || text.trim().length === 0) {
    throw new Error("Feedback text is required");
  }
  
  if (text.length > 5000) {
    throw new Error("Feedback text exceeds maximum length");
  }
  
  return text.trim();
}
```

### 2. Error Handling

Implement proper error handling:

```javascript
try {
  const result = await analyzeFeedback(data);
  // Handle success
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error("API Error:", error.response.data.error);
  } else if (error.request) {
    // No response received
    console.error("Network Error:", error.message);
  } else {
    // Request setup error
    console.error("Error:", error.message);
  }
}
```

### 3. Retry Logic

Implement exponential backoff for failed requests:

```javascript
async function retryRequest(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      const delay = Math.pow(2, i) * 1000; // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### 4. Batch Processing

For multiple feedback items, send requests sequentially with delays:

```javascript
async function processBatch(feedbackList) {
  const results = [];
  
  for (const feedback of feedbackList) {
    const result = await analyzeFeedback(feedback);
    results.push(result);
    
    // Delay between requests to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  return results;
}
```

## Code Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_ENDPOINT = 'https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod';

async function analyzeFeedback(feedback, customerId, metadata = {}) {
  const response = await axios.post(`${API_ENDPOINT}/analyze`, {
    operation: 'analyze_feedback',
    feedback: feedback,
    customer_id: customerId,
    metadata: metadata
  });
  
  return response.data;
}

async function getAnalytics(limit = 50) {
  const response = await axios.post(`${API_ENDPOINT}/analytics`, {
    operation: 'get_analytics',
    limit: limit
  });
  
  return response.data;
}

// Usage
(async () => {
  const result = await analyzeFeedback(
    "Great product!",
    "CUST001",
    { category: "product" }
  );
  console.log(result);
})();
```

### Python

```python
import requests
import json

API_ENDPOINT = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"

def analyze_feedback(feedback, customer_id, metadata=None):
    url = f"{API_ENDPOINT}/analyze"
    payload = {
        "operation": "analyze_feedback",
        "feedback": feedback,
        "customer_id": customer_id,
        "metadata": metadata or {}
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def get_analytics(limit=50):
    url = f"{API_ENDPOINT}/analytics"
    payload = {
        "operation": "get_analytics",
        "limit": limit
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

# Usage
if __name__ == "__main__":
    result = analyze_feedback(
        "Great product!",
        "CUST001",
        {"category": "product"}
    )
    print(json.dumps(result, indent=2))
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Sentiment analysis endpoint
- Analytics endpoint
- CORS support

## Support

For API support and questions:
- Email: api-support@example.com
- GitHub Issues: https://github.com/yourusername/customer-sentiment-analysis/issues
- Documentation: https://docs.example.com
