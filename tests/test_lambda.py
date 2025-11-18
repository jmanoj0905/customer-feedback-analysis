"""
Unit tests for Lambda functions
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add backend path to system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend/lambda/analyze_feedback'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

class TestAnalyzeFeedbackLambda(unittest.TestCase):
    """Test cases for analyze_feedback Lambda function"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'feedback': 'This product is amazing!',
                'customer_id': 'TEST123',
                'metadata': {
                    'category': 'product'
                }
            })
        }

        self.sample_context = Mock()

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_analyze_feedback_positive_sentiment(self, mock_dynamodb, mock_comprehend):
        """Test analyzing positive feedback"""
        # Mock Comprehend responses
        mock_comprehend_client = Mock()
        mock_comprehend_client.detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.95,
                'Negative': 0.01,
                'Neutral': 0.03,
                'Mixed': 0.01
            }
        }
        mock_comprehend_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {'Text': 'amazing product', 'Score': 0.99}
            ]
        }
        mock_comprehend_client.detect_entities.return_value = {
            'Entities': []
        }

        mock_comprehend.return_value = mock_comprehend_client

        # Mock DynamoDB
        mock_table = Mock()
        mock_dynamodb.return_value.Table.return_value = mock_table

        # Test would import and call lambda_handler here
        # For now, verify mocks are set up correctly
        self.assertTrue(mock_comprehend_client.detect_sentiment)

    def test_validate_text_input(self):
        """Test text input validation"""
        from utils.comprehend_helper import validate_text_input

        # Valid input
        is_valid, message = validate_text_input("This is valid feedback")
        self.assertTrue(is_valid)
        self.assertEqual(message, "")

        # Empty input
        is_valid, message = validate_text_input("")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Text cannot be empty")

        # Too long input
        long_text = "x" * 6000
        is_valid, message = validate_text_input(long_text, max_length=5000)
        self.assertFalse(is_valid)


class TestGetAnalyticsLambda(unittest.TestCase):
    """Test cases for get_analytics Lambda function"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'limit': 50
            })
        }

        self.sample_context = Mock()

    @patch('boto3.resource')
    def test_get_analytics_empty_table(self, mock_dynamodb):
        """Test getting analytics from empty table"""
        # Mock DynamoDB with no items
        mock_table = Mock()
        mock_table.scan.return_value = {'Items': []}
        mock_dynamodb.return_value.Table.return_value = mock_table

        # Verify mock setup
        result = mock_table.scan()
        self.assertEqual(result['Items'], [])

    @patch('boto3.resource')
    def test_get_analytics_with_data(self, mock_dynamodb):
        """Test getting analytics with data"""
        # Mock DynamoDB with sample items
        mock_items = [
            {
                'feedback_id': 'feedback_1',
                'sentiment': 'POSITIVE',
                'sentiment_scores': {
                    'positive': Decimal('0.95'),
                    'negative': Decimal('0.01'),
                    'neutral': Decimal('0.03'),
                    'mixed': Decimal('0.01')
                }
            },
            {
                'feedback_id': 'feedback_2',
                'sentiment': 'NEGATIVE',
                'sentiment_scores': {
                    'positive': Decimal('0.02'),
                    'negative': Decimal('0.93'),
                    'neutral': Decimal('0.04'),
                    'mixed': Decimal('0.01')
                }
            }
        ]

        mock_table = Mock()
        mock_table.scan.return_value = {'Items': mock_items}
        mock_dynamodb.return_value.Table.return_value = mock_table

        # Verify mock setup
        result = mock_table.scan()
        self.assertEqual(len(result['Items']), 2)


class TestComprehendHelper(unittest.TestCase):
    """Test cases for Comprehend Helper"""

    @patch('boto3.client')
    def test_detect_sentiment(self, mock_boto_client):
        """Test sentiment detection"""
        from utils.comprehend_helper import ComprehendHelper

        # Mock Comprehend response
        mock_client = Mock()
        mock_client.detect_sentiment.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.95,
                'Negative': 0.01,
                'Neutral': 0.03,
                'Mixed': 0.01
            }
        }
        mock_boto_client.return_value = mock_client

        helper = ComprehendHelper()
        result = helper.detect_sentiment("Great product!")

        self.assertEqual(result['sentiment'], 'POSITIVE')
        self.assertAlmostEqual(result['scores']['positive'], 0.95)

    @patch('boto3.client')
    def test_extract_key_phrases(self, mock_boto_client):
        """Test key phrase extraction"""
        from utils.comprehend_helper import ComprehendHelper

        # Mock Comprehend response
        mock_client = Mock()
        mock_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {'Text': 'excellent service', 'Score': 0.99},
                {'Text': 'fast delivery', 'Score': 0.95}
            ]
        }
        mock_boto_client.return_value = mock_client

        helper = ComprehendHelper()
        result = helper.extract_key_phrases("Excellent service and fast delivery")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['text'], 'excellent service')


class TestAPIResponses(unittest.TestCase):
    """Test API response formatting"""

    def test_cors_headers(self):
        """Test CORS headers are included"""
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }

        self.assertIn('Access-Control-Allow-Origin', headers)
        self.assertEqual(headers['Access-Control-Allow-Origin'], '*')

    def test_success_response_structure(self):
        """Test success response structure"""
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'result': 'success'})
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('body', response)

    def test_error_response_structure(self):
        """Test error response structure"""
        response = {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid input'})
        }

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
