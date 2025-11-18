import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')
S3_BUCKET = os.environ.get('S3_BUCKET', 'customer-feedback-bucket')

def lambda_handler(event, context):
    """
    Main Lambda handler for customer feedback analysis
    Supports two operations: analyze_feedback and get_analytics
    """

    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }

    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        operation = body.get('operation', 'analyze_feedback')

        if operation == 'analyze_feedback':
            return analyze_feedback(body)
        elif operation == 'get_analytics':
            return get_analytics(body)
        else:
            return error_response('Invalid operation', 400)

    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(str(e), 500)


def analyze_feedback(body):
    """
    Analyze customer feedback using AWS Comprehend
    """
    feedback_text = body.get('feedback', '')
    customer_id = body.get('customer_id', 'anonymous')
    metadata = body.get('metadata', {})

    if not feedback_text or len(feedback_text.strip()) == 0:
        return error_response('Feedback text is required', 400)

    # Perform sentiment analysis
    sentiment_response = comprehend.detect_sentiment(
        Text=feedback_text,
        LanguageCode='en'
    )

    # Extract key phrases
    key_phrases_response = comprehend.detect_key_phrases(
        Text=feedback_text,
        LanguageCode='en'
    )

    # Extract entities (optional - people, organizations, locations, etc.)
    entities_response = comprehend.detect_entities(
        Text=feedback_text,
        LanguageCode='en'
    )

    # Prepare result
    feedback_id = f"feedback_{int(datetime.now().timestamp() * 1000)}"

    result = {
        'feedback_id': feedback_id,
        'customer_id': customer_id,
        'feedback_text': feedback_text,
        'timestamp': datetime.now().isoformat(),
        'sentiment': sentiment_response['Sentiment'],
        'sentiment_scores': {
            'positive': float(sentiment_response['SentimentScore']['Positive']),
            'negative': float(sentiment_response['SentimentScore']['Negative']),
            'neutral': float(sentiment_response['SentimentScore']['Neutral']),
            'mixed': float(sentiment_response['SentimentScore']['Mixed'])
        },
        'key_phrases': [
            {
                'text': phrase['Text'],
                'score': float(phrase['Score'])
            }
            for phrase in key_phrases_response['KeyPhrases'][:5]  # Top 5
        ],
        'entities': [
            {
                'text': entity['Text'],
                'type': entity['Type'],
                'score': float(entity['Score'])
            }
            for entity in entities_response['Entities'][:5]  # Top 5
        ],
        'metadata': metadata
    }

    # Store in DynamoDB
    try:
        table = dynamodb.Table(TABLE_NAME)
        # Convert floats to Decimal for DynamoDB
        item = json.loads(json.dumps(result), parse_float=Decimal)
        table.put_item(Item=item)
    except Exception as e:
        print(f"DynamoDB error (non-critical): {str(e)}")
        # Continue even if DynamoDB fails

    return success_response(result)


def get_analytics(body):
    """
    Get aggregated analytics from stored feedback
    """
    limit = body.get('limit', 50)

    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan(Limit=limit)
        items = response.get('Items', [])

        # Convert Decimal to float for JSON serialization
        items = json.loads(json.dumps(items, default=decimal_default))

        # Calculate aggregated statistics
        total_feedback = len(items)
        sentiment_counts = {
            'POSITIVE': 0,
            'NEGATIVE': 0,
            'NEUTRAL': 0,
            'MIXED': 0
        }

        avg_scores = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'mixed': 0
        }

        for item in items:
            sentiment = item.get('sentiment', 'NEUTRAL')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            scores = item.get('sentiment_scores', {})
            for key in avg_scores:
                avg_scores[key] += scores.get(key, 0)

        # Calculate averages
        if total_feedback > 0:
            for key in avg_scores:
                avg_scores[key] = avg_scores[key] / total_feedback

        analytics = {
            'total_feedback': total_feedback,
            'sentiment_distribution': sentiment_counts,
            'average_sentiment_scores': avg_scores,
            'recent_feedback': items[:10],  # Last 10 items
            'timestamp': datetime.now().isoformat()
        }

        return success_response(analytics)

    except Exception as e:
        print(f"Analytics error: {str(e)}")
        # Return empty analytics if table doesn't exist yet
        return success_response({
            'total_feedback': 0,
            'sentiment_distribution': {
                'POSITIVE': 0,
                'NEGATIVE': 0,
                'NEUTRAL': 0,
                'MIXED': 0
            },
            'average_sentiment_scores': {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'mixed': 0
            },
            'recent_feedback': [],
            'timestamp': datetime.now().isoformat()
        })


def success_response(data):
    """Return success response with CORS headers"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(data)
    }


def error_response(message, status_code=500):
    """Return error response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': message})
    }


def get_cors_headers():
    """CORS headers for API Gateway"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }


def decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
