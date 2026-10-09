#!/usr/bin/env python3
"""Simple test script for analytics endpoints with better error handling"""

import requests
import json
import sys
import time

API_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{int(time.time())}@test.local"
TEST_PASSWORD = "TestPassword123!"

def register_test_user():
    """Register a test user"""
    try:
        print(f"Registering test user: {TEST_EMAIL}")
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={
                "firstname": "Test",
                "lastname": "User",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=15
        )
        if response.status_code == 200:
            print("[[OK]] User registered successfully")
            return True
        else:
            print(f"[!] Register returned {response.status_code}: {response.text[:200]}")
            return True  # User might already exist
    except Exception as e:
        print(f"[!] Registration error: {e}")
        return True

def login():
    """Login and get token"""
    try:
        print("Attempting login...")
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"[[OK]] Login successful, token: {token[:50]}...")
            return token
        else:
            print(f"[[FAIL]] Login failed: {response.status_code} - {response.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print("[[FAIL]] Login request timed out")
        return None
    except Exception as e:
        print(f"[[FAIL]] Login error: {e}")
        return None

def test_analytics_info(token):
    """Test analytics capabilities endpoint"""
    print("\n=== Testing Analytics Info ===")
    try:
        response = requests.get(
            f"{API_URL}/api/analytics/info",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[[OK]] Analytics info endpoint works!")
            caps = result.get('capabilities', {})
            for category, features in caps.items():
                print(f"   {category}: {features}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def test_enhanced_sentiment(token):
    """Test enhanced sentiment analysis"""
    print("\n=== Testing Enhanced Sentiment ===")
    try:
        response = requests.post(
            f"{API_URL}/api/analytics/sentiment/enhanced",
            json={"text": "This product is amazing! Great quality but a bit expensive."},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            overall = data.get('overall', {})
            emotions = data.get('emotions', {})
            
            print("[[OK]] Enhanced sentiment analysis works!")
            print(f"  Overall Sentiment: {overall.get('label')} ({overall.get('confidence_score', 0):.2f})")
            print(f"  Emotions: {emotions}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def test_batch_sentiment(token):
    """Test batch sentiment analysis"""
    print("\n=== Testing Batch Sentiment ===")
    try:
        texts = [
            "Excellent product!",
            "Terrible quality",
            "Average performance"
        ]
        
        response = requests.post(
            f"{API_URL}/api/analytics/sentiment/batch",
            json=texts,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            agg = result.get('aggregated', {})
            print("[[OK]] Batch sentiment analysis works!")
            print(f"  Texts Analyzed: {agg.get('total_analyzed', 0)}")
            print(f"  Average Sentiment: {agg.get('average_sentiment_score', 0):.3f}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def test_alert_stats(token):
    """Test alert statistics"""
    print("\n=== Testing Alert System ===")
    try:
        response = requests.get(
            f"{API_URL}/api/analytics/alerts/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            print("[[OK]] Alert system works!")
            print(f"  Total Active: {data.get('total_active', 0)}")
            print(f"  Critical: {data.get('critical', 0)}")
            print(f"  Warnings: {data.get('warning', 0)}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("Analytics Module Test Suite")
    print("=" * 70)
    
    # Register test user
    register_test_user()
    time.sleep(1)
    
    # Login
    token = login()
    if not token:
        print("\n[!] Could not obtain authentication token")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Analytics Info", test_analytics_info(token)))
    results.append(("Enhanced Sentiment", test_enhanced_sentiment(token)))
    results.append(("Batch Sentiment", test_batch_sentiment(token)))
    results.append(("Alert System", test_alert_stats(token)))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n All analytics endpoints are working!")
        print("\nNext: Visit http://localhost:5173/analytics to see the dashboard")
    else:
        print(f"\n[WARN] {total - passed} test(s) failed. Check the errors above.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
