"""
Quick API Test for WEEX Hackathon
Tests both public and private endpoints
"""

import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

# Credentials
API_KEY = os.getenv("WEEX_API_KEY")
SECRET_KEY = os.getenv("WEEX_SECRET_KEY")
PASSPHRASE = os.getenv("WEEX_PASSPHRASE")

BASE_URL = "https://api-contract.weex.com"

def generate_signature(secret_key: str, timestamp: str, method: str, 
                       request_path: str, query_string: str = "") -> str:
    """Generate HMAC SHA256 signature"""
    prehash = timestamp + method.upper() + request_path + query_string
    signature = hmac.new(
        secret_key.encode('utf-8'),
        prehash.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')


def test_public_endpoint():
    """Test public ticker endpoint"""
    print("\n📡 Testing Public Endpoint (Ticker)...")
    try:
        url = f"{BASE_URL}/capi/v2/market/ticker?symbol=cmt_btcusdt"
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False


def test_private_endpoint():
    """Test private account endpoint"""
    print("\n🔐 Testing Private Endpoint (Account)...")
    
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    request_path = "/capi/v2/account/assets"
    
    signature = generate_signature(SECRET_KEY, timestamp, method, request_path)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US",
    }
    
    print(f"   Timestamp: {timestamp}")
    print(f"   API Key: {API_KEY[:20]}...")
    print(f"   Signature: {signature[:30]}...")
    
    try:
        url = f"{BASE_URL}{request_path}"
        print(f"   URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response: {response.text[:500] if response.text else 'Empty'}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False


def test_alternative_endpoint():
    """Test alternative account endpoint with coin parameter"""
    print("\n🔐 Testing Alternative Endpoint (getAccount)...")
    
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    request_path = "/capi/v2/account/getAccount"
    query_string = "?coin=USDT"
    
    signature = generate_signature(SECRET_KEY, timestamp, method, request_path, query_string)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US",
    }
    
    try:
        url = f"{BASE_URL}{request_path}{query_string}"
        print(f"   URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:500] if response.text else 'Empty'}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 WEEX API QUICK TEST")
    print("=" * 60)
    
    print(f"\nCredentials loaded:")
    print(f"   API Key: {API_KEY[:20]}..." if API_KEY else "   API Key: NOT FOUND")
    print(f"   Secret: {SECRET_KEY[:20]}..." if SECRET_KEY else "   Secret: NOT FOUND")
    print(f"   Passphrase: {PASSPHRASE}" if PASSPHRASE else "   Passphrase: NOT FOUND")
    
    test_public_endpoint()
    test_private_endpoint()
    test_alternative_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
