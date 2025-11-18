"""
Lambda Function: Get Analytics
Retrieves and aggregates customer feedback analytics from DynamoDB
"""

import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any

# Import local config
try:
    import config
except ImportError:
    # Fallback configuration if config.py is not found
    class config:
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')
        DEFAULT_LIMIT = int(os.environ.get('DEFAULT_LIMIT', 50))
        MAX_LIMIT = int(os.environ.get('MAX_LIMIT', 1000))
        ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)


def lambda_handler(event, context):
    """
    Main Lambda handler for retrieving analytics
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        API Gateway compatible response with analytics data
    """
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, '')
    
    try:
        # Parse request body
        body = parse_request_body(event)
        
        # Get parameters
        limit = min(body.get('limit', config.DEFAULT_LIMIT), config.MAX_LIMIT)
        
        # Retrieve analytics
        analytics = get_analytics(limit)
        
        return success_response(analytics)
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return error_response(f"Error retrieving analytics: {str(e)}", 500)


def get_analytics(limit: int) -> Dict[str, Any]:
    """
    Retrieve and aggregate analytics from DynamoDB
    
    Args:
        limit: Maximum number of items to retrieve
        
    Returns:
        Dictionary containing aggregated analytics
    """
    try:
        table = dynamodb.Table(config.DYNAMODB_TABLE)
        
        # Scan table with limit
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        
        # Convert Decimal to float for JSON serialization
        items = json.loads(json.dumps(items, default=decimal_to_float))
        
        # Calculate aggregated statistics
        analytics = calculate_analytics(items)
        
        # Add timestamp
        analytics['timestamp'] = datetime.now().isoformat()
        analytics['total_retrieved'] = len(items)
        
        return analytics
        
    except Exception as e:
        print(f"Error retrieving analytics: {str(e)}")
        # Return empty analytics if table doesn't exist or error occurs
        return get_empty_analytics()


def calculate_analytics(items: List[Dict]) -> Dict[str, Any]:
    """
    Calculate aggregated statistics from feedback items
    
    Args:
        items: List of feedback items
        
    Returns:
        Dictionary containing calculated analytics
    """
    total_feedback = len(items)
    
    # Initialize counters
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
    
    category_sentiment = {}
    customer_feedback_count = {}
    
    # Aggregate data
    for item in items:
        # Count sentiments
        sentiment = item.get('sentiment', 'NEUTRAL')
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Sum scores
        scores = item.get('sentiment_scores', {})
        for key in avg_scores:
            avg_scores[key] += scores.get(key, 0)
        
        # Track category sentiment
        category = item.get('metadata', {}).get('category', 'uncategorized')
        if category not in category_sentiment:
            category_sentiment[category] = {
                'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0
            }
        category_sentiment[category][sentiment] += 1
        
        # Track customer feedback frequency
        customer_id = item.get('customer_id', 'anonymous')
        customer_feedback_count[customer_id] = customer_feedback_count.get(customer_id, 0) + 1
    
    # Calculate averages
    if total_feedback > 0:
        for key in avg_scores:
            avg_scores[key] = round(avg_scores[key] / total_feedback, 4)
    
    # Calculate sentiment percentages
    sentiment_percentages = {}
    if total_feedback > 0:
        for sentiment, count in sentiment_counts.items():
            sentiment_percentages[sentiment] = round((count / total_feedback) * 100, 2)
    
    # Get top customers by feedback volume
    top_customers = sorted(
        customer_feedback_count.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    return {
        'total_feedback': total_feedback,
        'sentiment_distribution': sentiment_counts,
        'sentiment_percentages': sentiment_percentages,
        'average_sentiment_scores': avg_scores,
        'category_breakdown': category_sentiment,
        'top_customers': [
            {'customer_id': cid, 'feedback_count': count} 
            for cid, count in top_customers
        ],
        'recent_feedback': items[:10]  # Last 10 items
    }


def get_empty_analytics() -> Dict[str, Any]:
    """Return empty analytics structure"""
    return {
        'total_feedback': 0,
        'sentiment_distribution': {
            'POSITIVE': 0,
            'NEGATIVE': 0,
            'NEUTRAL': 0,
            'MIXED': 0
        },
        'sentiment_percentages': {
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
        'category_breakdown': {},
        'top_customers': [],
        'recent_feedback': [],
        'timestamp': datetime.now().isoformat()
    }


def parse_request_body(event: dict) -> dict:
    """Parse request body from API Gateway event"""
    body = event.get('body', {})
    
    if isinstance(body, str):
        try:
            return json.loads(body)
        except:
            return {}
    
    return body


def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def success_response(data: dict, status_code: int = 200) -> dict:
    """Create success response with CORS headers"""
    return cors_response(status_code, json.dumps(data))


def error_response(message: str, status_code: int = 500) -> dict:
    """Create error response with CORS headers"""
    return cors_response(status_code, json.dumps({'error': message}))


def cors_response(status_code: int, body: str) -> dict:
    """Create response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': config.ALLOWED_ORIGINS,
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': body
    }
