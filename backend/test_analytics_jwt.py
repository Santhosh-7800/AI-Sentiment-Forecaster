#!/usr/bin/env python3
"""Test analytics with direct JWT token generation"""

import sys
import requests
from jose import jwt
from datetime import datetime, timedelta

# Same key as in oauth2.py
SECRET_KEY = "your_super_secret_key"
ALGORITHM = "HS256"

API_URL = "http://localhost:8000"

def generate_test_token(user_id="test_user_12345"):
    """Generate a valid JWT token directly"""
    try:
        to_encode = {"user_id": user_id}
        expire = datetime.utcnow() + timedelta(minutes=60)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token
    except Exception as e:
        print(f"[[FAIL]] Token generation failed: {e}")
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
            if caps:
                for category, features in caps.items():
                    print(f"   {category}: {features}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
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
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            overall = data.get('overall', {})
            emotions = data.get('emotions', {})
            
            print("[[OK]] Enhanced sentiment analysis works!")
            print(f"  Sentiment: {overall.get('label', 'N/A')} ({overall.get('confidence_score', 0):.2f})")
            if emotions:
                print(f"  Emotions Detected: {emotions}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
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
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            agg = result.get('aggregated', {})
            print("[[OK]] Batch sentiment analysis works!")
            if agg:
                print(f"  Texts Analyzed: {agg.get('total_analyzed', 0)}")
                print(f"  Average Sentiment: {agg.get('average_sentiment_score', 0):.3f}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
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
            if data:
                print(f"  Total Active: {data.get('total_active', 0)}")
                print(f"  Critical: {data.get('critical', 0)}")
                print(f"  Warnings: {data.get('warning', 0)}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def test_topics(token):
    """Test topic modeling"""
    print("\n=== Testing Topic Modeling ===")
    try:
        # Use more sample texts for better BERTopic performance
        texts = [
            "Great product quality and excellent build",
            "Amazing performance and fast speed",
            "Poor quality materials and cheap feel",
            "Excellent durability and construction",
            "Great design and beautiful appearance",
            "Fast performance and efficient processor",
        ]
        
        response = requests.post(
            f"{API_URL}/api/analytics/topics/extract",
            json={
                "texts": texts,
                "product": "Test Product"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[[OK]] Topic modeling works!")
            data = result.get('data', {})
            if data and 'topics' in data:
                print(f"  Topics Found: {len(data.get('topics', []))}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def test_trends(token):
    """Test trend analysis"""
    print("\n=== Testing Trend Analysis ===")
    try:
        from datetime import datetime, timedelta
        dates = [(datetime.now() - timedelta(days=i)).isoformat() for i in range(5)]
        
        response = requests.post(
            f"{API_URL}/api/analytics/trends/analyze",
            json={
                "sentiments": [0.8, 0.75, 0.7, 0.65, 0.72],
                "dates": dates,
                "product": "Test Product"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[[OK]] Trend analysis works!")
            data = result.get('data', {})
            if data:
                trend_info = data.get('trend', {})
                print(f"  Trend Direction: {trend_info.get('direction', 'N/A')}")
            return True
        else:
            print(f"[[FAIL]] Error {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        print(f"[[FAIL]] Request failed: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("Analytics Module Test Suite (Direct JWT)")
    print("=" * 70)
    
    # Generate token
    token = generate_test_token()
    if not token:
        print("[!] Failed to generate test token")
        sys.exit(1)
    
    print(f"\n[OK] Generated test JWT: {token[:50]}...")
    
    # Run tests
    results = []
    results.append(("Analytics Info", test_analytics_info(token)))
    results.append(("Enhanced Sentiment", test_enhanced_sentiment(token)))
    results.append(("Batch Sentiment", test_batch_sentiment(token)))
    results.append(("Topic Modeling", test_topics(token)))
    results.append(("Trend Analysis", test_trends(token)))
    results.append(("Alert System", test_alert_stats(token)))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n All analytics endpoints are working correctly!")
    else:
        failed_count = total - passed
        print(f"\n[WARN] {failed_count} test(s) failed. See details above.")
        if passed > 0:
            print(f"[OK] {passed} endpoint(s) are working")
    
    print("\n Next Steps:")
    print("  1. Visit http://localhost:5173/analytics to see the dashboard")
    print("  2. Test real analysis with actual product reviews")
    print("  3. Generate PDF/Excel reports")
    print("=" * 70)

if __name__ == "__main__":
    main()
