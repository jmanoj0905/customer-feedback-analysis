"""
Configuration settings for the analyze_feedback Lambda function
"""

import os

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# DynamoDB Configuration
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')

# S3 Configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'customer-feedback-bucket')

# Comprehend Configuration
COMPREHEND_LANGUAGE = os.environ.get('COMPREHEND_LANGUAGE', 'en')
MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 5000))

# Analysis Configuration
MAX_KEY_PHRASES = int(os.environ.get('MAX_KEY_PHRASES', 5))
MAX_ENTITIES = int(os.environ.get('MAX_ENTITIES', 5))

# CORS Configuration
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
