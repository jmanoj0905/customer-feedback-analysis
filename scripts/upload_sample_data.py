#!/usr/bin/env python3
"""
Upload Sample Data Script
Uploads sample feedback data to the API for testing
"""

import json
import requests
import sys
import time
from typing import List, Dict

# Configuration
API_ENDPOINT = "YOUR_API_ENDPOINT_HERE"  # Update this after deployment
SAMPLE_DATA_FILE = "../data/sample_feedback.json"


def load_sample_data(file_path: str) -> List[Dict]:
    """Load sample feedback from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        sys.exit(1)


def analyze_feedback(feedback_data: Dict) -> Dict:
    """Send feedback to API for analysis"""
    url = f"{API_ENDPOINT}/analyze"
    
    payload = {
        "operation": "analyze_feedback",
        "feedback": feedback_data.get("feedback"),
        "customer_id": feedback_data.get("customer_id"),
        "metadata": {
            "category": feedback_data.get("category"),
            "expected_sentiment": feedback_data.get("expected_sentiment")
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed - {e}")
        return None


def main():
    """Main execution"""
    print("=" * 60)
    print("Customer Feedback Analysis - Sample Data Upload")
    print("=" * 60)
    
    # Check API endpoint is configured
    if API_ENDPOINT == "YOUR_API_ENDPOINT_HERE":
        print("\nError: Please update API_ENDPOINT in this script")
        print("Get your endpoint from CloudFormation outputs:")
        print("  aws cloudformation describe-stacks \\")
        print("    --stack-name customer-feedback-analysis-prod \\")
        print("    --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue'")
        sys.exit(1)
    
    print(f"\nAPI Endpoint: {API_ENDPOINT}")
    
    # Load sample data
    print(f"\nLoading sample data from {SAMPLE_DATA_FILE}...")
    sample_data = load_sample_data(SAMPLE_DATA_FILE)
    print(f"Loaded {len(sample_data)} sample feedback items")
    
    # Upload each feedback
    successful = 0
    failed = 0
    
    print("\nUploading feedback...")
    for i, feedback in enumerate(sample_data, 1):
        print(f"\n[{i}/{len(sample_data)}] Processing: {feedback['customer_id']}")
        print(f"  Expected sentiment: {feedback.get('expected_sentiment', 'N/A')}")
        
        result = analyze_feedback(feedback)
        
        if result:
            print(f"  ✓ Detected sentiment: {result.get('sentiment')}")
            print(f"  ✓ Confidence: {result.get('sentiment_scores', {}).get(result.get('sentiment', '').lower(), 0):.2f}")
            successful += 1
        else:
            print(f"  ✗ Failed to analyze")
            failed += 1
        
        # Delay to avoid rate limiting
        if i < len(sample_data):
            time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("Upload Complete")
    print("=" * 60)
    print(f"Total: {len(sample_data)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print("\nYou can now view the analytics dashboard to see the results!")


if __name__ == "__main__":
    main()
