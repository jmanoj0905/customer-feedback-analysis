"""
Comprehend Helper Module
Reusable functions for AWS Comprehend sentiment analysis operations
"""

import boto3
from typing import Dict, List, Any


class ComprehendHelper:
    """Helper class for AWS Comprehend operations"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize Comprehend client
        
        Args:
            region_name: AWS region name
        """
        self.comprehend = boto3.client('comprehend', region_name=region_name)
        self.language_code = 'en'
    
    def detect_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Detect sentiment in text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing sentiment and scores
        """
        try:
            response = self.comprehend.detect_sentiment(
                Text=text,
                LanguageCode=self.language_code
            )
            
            return {
                'sentiment': response['Sentiment'],
                'scores': {
                    'positive': float(response['SentimentScore']['Positive']),
                    'negative': float(response['SentimentScore']['Negative']),
                    'neutral': float(response['SentimentScore']['Neutral']),
                    'mixed': float(response['SentimentScore']['Mixed'])
                }
            }
        except Exception as e:
            raise Exception(f"Error detecting sentiment: {str(e)}")
    
    def extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[Dict[str, Any]]:
        """
        Extract key phrases from text
        
        Args:
            text: Input text to analyze
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases with scores
        """
        try:
            response = self.comprehend.detect_key_phrases(
                Text=text,
                LanguageCode=self.language_code
            )
            
            phrases = [
                {
                    'text': phrase['Text'],
                    'score': float(phrase['Score'])
                }
                for phrase in response['KeyPhrases'][:max_phrases]
            ]
            
            return phrases
        except Exception as e:
            raise Exception(f"Error extracting key phrases: {str(e)}")
    
    def detect_entities(self, text: str, max_entities: int = 5) -> List[Dict[str, Any]]:
        """
        Detect entities in text
        
        Args:
            text: Input text to analyze
            max_entities: Maximum number of entities to return
            
        Returns:
            List of entities with types and scores
        """
        try:
            response = self.comprehend.detect_entities(
                Text=text,
                LanguageCode=self.language_code
            )
            
            entities = [
                {
                    'text': entity['Text'],
                    'type': entity['Type'],
                    'score': float(entity['Score'])
                }
                for entity in response['Entities'][:max_entities]
            ]
            
            return entities
        except Exception as e:
            raise Exception(f"Error detecting entities: {str(e)}")
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect dominant language in text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing language code and score
        """
        try:
            response = self.comprehend.detect_dominant_language(Text=text)
            
            if response['Languages']:
                dominant = response['Languages'][0]
                return {
                    'language_code': dominant['LanguageCode'],
                    'score': float(dominant['Score'])
                }
            
            return {'language_code': 'en', 'score': 1.0}
        except Exception as e:
            raise Exception(f"Error detecting language: {str(e)}")
    
    def analyze_comprehensive(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including sentiment, key phrases, and entities
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing all analysis results
        """
        return {
            'sentiment': self.detect_sentiment(text),
            'key_phrases': self.extract_key_phrases(text),
            'entities': self.detect_entities(text),
            'language': self.detect_language(text)
        }


def validate_text_input(text: str, max_length: int = 5000) -> tuple[bool, str]:
    """
    Validate text input for Comprehend
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed text length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    if len(text) > max_length:
        return False, f"Text exceeds maximum length of {max_length} characters"
    
    return True, ""
