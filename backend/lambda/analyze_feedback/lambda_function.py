"""
Lambda Function: Analyze Customer Feedback
Analyzes customer feedback using AWS Comprehend for sentiment analysis,
key phrase extraction, and entity recognition.
"""

import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

# Import local config
try:
    import config
except ImportError:
    # Fallback configuration if config.py is not found
    class config:
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')
        S3_BUCKET = os.environ.get('S3_BUCKET', 'customer-feedback-bucket')
        COMPREHEND_LANGUAGE = os.environ.get('COMPREHEND_LANGUAGE', 'en')
        MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 5000))
        MAX_KEY_PHRASES = int(os.environ.get('MAX_KEY_PHRASES', 5))
        MAX_ENTITIES = int(os.environ.get('MAX_ENTITIES', 5))
        ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

# Initialize AWS clients
comprehend = boto3.client('comprehend', region_name=config.AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)


def lambda_handler(event, context):
    """
    Main Lambda handler for analyzing customer feedback
    
    Args:
        event: Lambda event object containing feedback data
        context: Lambda context object
        
    Returns:
        API Gateway compatible response
    """
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, '')
    
    try:
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
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return error_response(f"Internal server error: {str(e)}", 500)


def validate_text_input(text: str) -> tuple:
    """
    Validate text input for Comprehend
    
    Args:
        text: Input text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    if len(text) > config.MAX_TEXT_LENGTH:
        return False, f"Text exceeds maximum length of {config.MAX_TEXT_LENGTH} characters"
    
    return True, ""


def analyze_feedback(feedback_text: str, customer_id: str, metadata: dict) -> dict:
    """
    Analyze feedback using AWS Comprehend
    
    Args:
        feedback_text: The feedback text to analyze
        customer_id: Customer identifier
        metadata: Additional metadata
        
    Returns:
        Dictionary containing analysis results
    """
    # Generate unique feedback ID
    feedback_id = f"feedback_{int(datetime.now().timestamp() * 1000)}"
    
    # Perform sentiment analysis
    sentiment_response = comprehend.detect_sentiment(
        Text=feedback_text,
        LanguageCode=config.COMPREHEND_LANGUAGE
    )
    
    # Extract key phrases
    key_phrases_response = comprehend.detect_key_phrases(
        Text=feedback_text,
        LanguageCode=config.COMPREHEND_LANGUAGE
    )
    
    # Detect entities
    entities_response = comprehend.detect_entities(
        Text=feedback_text,
        LanguageCode=config.COMPREHEND_LANGUAGE
    )
    
    # Detect language
    language_response = comprehend.detect_dominant_language(Text=feedback_text)
    
    # Extract data
    sentiment_data = {
        'sentiment': sentiment_response['Sentiment'],
        'scores': {
            'positive': float(sentiment_response['SentimentScore']['Positive']),
            'negative': float(sentiment_response['SentimentScore']['Negative']),
            'neutral': float(sentiment_response['SentimentScore']['Neutral']),
            'mixed': float(sentiment_response['SentimentScore']['Mixed'])
        }
    }
    
    key_phrases = [
        {
            'text': phrase['Text'],
            'score': float(phrase['Score'])
        }
        for phrase in key_phrases_response['KeyPhrases'][:config.MAX_KEY_PHRASES]
    ]
    
    entities = [
        {
            'text': entity['Text'],
            'type': entity['Type'],
            'score': float(entity['Score'])
        }
        for entity in entities_response['Entities'][:config.MAX_ENTITIES]
    ]
    
    language = {
        'language_code': language_response['Languages'][0]['LanguageCode'] if language_response['Languages'] else 'en',
        'score': float(language_response['Languages'][0]['Score']) if language_response['Languages'] else 1.0
    }
    
    # Compile results
    result = {
        'feedback_id': feedback_id,
        'customer_id': customer_id,
        'feedback_text': feedback_text,
        'timestamp': datetime.now().isoformat(),
        'sentiment': sentiment_data['sentiment'],
        'sentiment_scores': sentiment_data['scores'],
        'key_phrases': key_phrases,
        'entities': entities,
        'language': language,
        'metadata': metadata
    }
    
    return result


def store_feedback(feedback_data: dict) -> None:
    """
    Store feedback analysis results in DynamoDB
    
    Args:
        feedback_data: Analysis results to store
    """
    try:
        table = dynamodb.Table(config.DYNAMODB_TABLE)
        
        # Convert floats to Decimal for DynamoDB
        item = json.loads(json.dumps(feedback_data), parse_float=Decimal)
        
        table.put_item(Item=item)
        
        print(f"Successfully stored feedback: {feedback_data['feedback_id']}")
        
    except Exception as e:
        print(f"Error storing feedback in DynamoDB: {str(e)}")
        # Don't fail the request if storage fails


def parse_request_body(event: dict) -> dict:
    """Parse request body from API Gateway event"""
    body = event.get('body', {})
    
    if isinstance(body, str):
        return json.loads(body)
    
    return body


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
