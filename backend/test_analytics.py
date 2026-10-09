#!/usr/bin/env python3
"""Test script for analytics endpoints"""

import requests
import json
import sys

API_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

def login():
    """Login and get token"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        elif response.status_code == 404:
            print("[WARN] Login endpoint not available, trying public endpoints...")
            return None
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("[WARN] Login request timed out. Testing public endpoints...")
        return None
    except Exception as e:
        print(f"[WARN] Login error: {e}. Trying guest access...")
        return None

def test_enhanced_sentiment(token):
    """Test enhanced sentiment analysis"""
    print("\n=== Testing Enhanced Sentiment Analysis ===")
    
    response = requests.post(
        f"{API_URL}/api/analytics/sentiment/enhanced",
        json={"text": "This product is amazing! Great quality but a bit expensive."},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("[[OK]] Enhanced sentiment analysis works!")
        print(f"  Sentiment: {result['data']['overall']['label']}")
        print(f"  Confidence: {result['data']['overall']['confidence_score']}")
        print(f"  Emotions: {result['data']['emotions']}")
        print(f"  Aspects Found: {list(result['data']['aspects'].keys())}")
        return result['data']
    else:
        print(f"[[FAIL]] Error: {response.status_code} - {response.text}")
        return None

def test_alert_system(token):
    """Test alert system"""
    print("\n=== Testing Alert System ===")
    
    response = requests.get(
        f"{API_URL}/api/analytics/alerts/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("[[OK]] Alert system works!")
        print(f"  Active Alerts: {result['data']['total_active']}")
        print(f"  Critical: {result['data']['critical']}")
        print(f"  Warnings: {result['data']['warning']}")
        return result['data']
    else:
        print(f"[[FAIL]] Error: {response.status_code} - {response.text}")
        return None

def test_analytics_info(token):
    """Get analytics capabilities"""
    print("\n=== Testing Analytics Info ===")
    
    response = requests.get(
        f"{API_URL}/api/analytics/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("[[OK]] Analytics info retrieved!")
        print("  Available Capabilities:")
        for category, features in result['capabilities'].items():
            print(f"    - {category}: {features}")
        return result
    else:
        print(f"[[FAIL]] Error: {response.status_code} - {response.text}")
        return None

def test_batch_sentiment(token):
    """Test batch sentiment analysis"""
    print("\n=== Testing Batch Sentiment Analysis ===")
    
    texts = [
        "Excellent product, highly recommended!",
        "Not satisfied with the quality",
        "Average performance, nothing special",
        "Perfect for my needs, great value",
        "Waste of money, stopped working"
    ]
    
    response = requests.post(
        f"{API_URL}/api/analytics/sentiment/batch",
        json=texts,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("[[OK]] Batch sentiment analysis works!")
        print(f"  Texts Analyzed: {result['aggregated']['total_analyzed']}")
        print(f"  Average Sentiment: {result['aggregated']['average_sentiment_score']}")
        print(f"  Dominant Emotion: {result['aggregated']['dominant_emotion']}")
        return result
    else:
        print(f"[[FAIL]] Error: {response.status_code} - {response.text}")
        return None

def main():
    print("=" * 70)
    print("Analytics Module Test Suite")
    print("=" * 70)
    
    # Get token
    print("\nLogging in...")
    token = login()
    if not token:
        print("Cannot proceed without authentication")
        return
    
    print(f"[[OK]] Login successful!")
    
    # Run tests
    test_enhanced_sentiment(token)
    test_batch_sentiment(token)
    test_alert_system(token)
    test_analytics_info(token)
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Access API docs: http://localhost:8000/docs")
    print("2. Try analytics page: http://localhost:5173/analytics")
    print("3. Generate reports and analyze trends")

if __name__ == "__main__":
    main()
