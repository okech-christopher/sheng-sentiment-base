"""Demo script for Sheng-Native API.

This script demonstrates the API with 3 test cases:
1. General/Negative: Financial distress message
2. Logistics/Neutral: Traffic and route report
3. General/Positive: Party/celebration message
"""

import requests
import json
from typing import Dict, Any


def analyze_text(text: str, url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Send text to the API for analysis.
    
    Args:
        text: Sheng text to analyze
        url: Base URL of the API
        
    Returns:
        Analysis response as dictionary
    """
    endpoint = f"{url}/v1/analyze"
    payload = {
        "text": text,
        "include_logistics": True,
        "include_code_switches": True
    }
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {text}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"\nSentiment: {result['sentiment_label']} (score: {result['sentiment_score']})")
        print(f"Slang terms: {', '.join(result['slang_terms'])}")
        print(f"Is Logistics: {result['is_logistics']} (confidence: {result['confidence']})")
        
        if result['logistics_intent']:
            li = result['logistics_intent']
            print(f"Logistics Intent: {li['intent']}")
            print(f"Severity: {li['severity']}")
            print(f"Description: {li['description']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def main():
    """Run demo test cases."""
    
    print("\n" + "="*60)
    print("SHENG-NATIVE API DEMO")
    print("="*60)
    
    # Test Case 1: General/Negative - Financial distress
    print("\n📌 TEST CASE 1: General/Negative (Financial Distress)")
    analyze_text("Buda niko sapa, nisaidie chapaa.")
    
    # Test Case 2: Logistics/Neutral - Traffic and route report
    print("\n📌 TEST CASE 2: Logistics/Neutral (Traffic Report)")
    analyze_text("Traffic imestand stage ya mabs, avoid panya route.")
    
    # Test Case 3: General/Positive - Party/celebration
    print("\n📌 TEST CASE 3: General/Positive (Celebration)")
    analyze_text("Leo tunadunda sherehe na mzinga!")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
