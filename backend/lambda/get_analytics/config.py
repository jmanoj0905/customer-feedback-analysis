"""
Configuration settings for the get_analytics Lambda function
"""

import os

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# DynamoDB Configuration
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'CustomerFeedback')

# Query Configuration
DEFAULT_LIMIT = int(os.environ.get('DEFAULT_LIMIT', 50))
MAX_LIMIT = int(os.environ.get('MAX_LIMIT', 1000))

# CORS Configuration
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')
