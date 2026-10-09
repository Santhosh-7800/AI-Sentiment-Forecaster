#!/usr/bin/env python3
"""Test script for /api/realtime/analyze endpoint with logging output"""

import requests
import json
import sys

API_URL = "http://localhost:8000"

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"
TEST_FIRSTNAME = "Test"
TEST_LASTNAME = "User"

def register_user():
    """Register a test user"""
    try:
        print("[*] Attempting to register test user...")
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={
                "firstname": TEST_FIRSTNAME,
                "lastname": TEST_LASTNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        if response.status_code == 200:
            print("[+] User registered successfully")
            return True
        elif response.status_code == 400:
            print("[*] User already exists (expected)")
            return True
        else:
            print(f"[-] Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[-] Registration error: {e}")
        return False

def login_user():
    """Login and get access token"""
    try:
        print("[*] Logging in...")
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"[+] Login successful. Token: {token[:20]}...")
            return token
        else:
            print(f"[-] Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[-] Login error: {e}")
        return None

def analyze_product(token, product_name):
    """Make request to /api/realtime/analyze"""
    try:
        print(f"\n[*] Sending analysis request for: {product_name}")
        print("[*] Watching server console for logging output...")
        print("[*] This may take 10-60 seconds...\n")
        
        response = requests.post(
            f"{API_URL}/api/realtime/analyze",
            json={
                "product": product_name,
                "max_articles": 25,
                "force_refresh": False
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=120  # 2 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[+] Analysis completed successfully!")
            print(f"[+] Product: {result.get('product')}")
            print(f"[+] Articles found: {result.get('article_count', 0)}")
            print(f"[+] Sentiment score: {result.get('sentiment_score', 'N/A')}")
            print(f"[+] Source: {result.get('source', 'N/A')}")
            return result
        elif response.status_code == 400:
            print(f"[-] Bad request: {response.text}")
            return None
        elif response.status_code == 500:
            print(f"[-] Server error: {response.text}")
            return None
        else:
            print(f"[-] Request failed: {response.status_code} - {response.text}")
            return None
            
    except requests.Timeout:
        print("[-] Request timed out after 120 seconds. Server is likely hanging.")
        return None
    except Exception as e:
        print(f"[-] Request error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("TrendAI Realtime Analysis Endpoint Tester")
    print("=" * 60)
    print()
    
    # Step 1: Register
    if not register_user():
        print("Cannot proceed without registration")
        sys.exit(1)
    
    # Step 2: Login
    token = login_user()
    if not token:
        print("Cannot proceed without token")
        sys.exit(1)
    
    # Step 3: Analyze
    product = "iPhone 15"
    result = analyze_product(token, product)
    
    if result:
        print("\n" + "=" * 60)
        print("Full Response JSON:")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("\n[!] Analysis failed. Check server console above for logs.")
    
    print("\n[*] Check the server terminal for 'Received analysis request' logging.")
