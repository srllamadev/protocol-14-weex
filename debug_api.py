"""
Debug API Test - Testing signature variations
"""

import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEEX_API_KEY")
SECRET_KEY = os.getenv("WEEX_SECRET_KEY")
PASSPHRASE = os.getenv("WEEX_PASSPHRASE")

BASE_URL = "https://api-contract.weex.com"


def sign_v1(timestamp, method, request_path, query_string="", body=""):
    """
    Signature V1: timestamp + METHOD + requestPath + queryString + body
    (queryString without ?)
    """
    message = timestamp + method.upper() + request_path + query_string + body
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8'), message


def sign_v2(timestamp, method, request_path, query_string="", body=""):
    """
    Signature V2: timestamp + METHOD + requestPath + "?" + queryString + body
    (When queryString is not empty, include ?)
    """
    if query_string:
        message = timestamp + method.upper() + request_path + "?" + query_string + body
    else:
        message = timestamp + method.upper() + request_path + body
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8'), message


def sign_v3(timestamp, method, request_path, query_string="", body=""):
    """
    Signature V3: For assets endpoint (no query string)
    Just: timestamp + METHOD + requestPath
    """
    message = timestamp + method.upper() + request_path
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8'), message


def test_endpoint(name, sign_func, request_path, query_string="", base_url=None):
    """Test an endpoint with a specific signature function"""
    print(f"\n🔐 {name}")
    print("-" * 50)
    
    url_base = base_url or BASE_URL
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    
    signature, message = sign_func(timestamp, method, request_path, query_string)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US",
    }
    
    if query_string:
        url = f"{url_base}{request_path}?{query_string}"
    else:
        url = f"{url_base}{request_path}"
    
    print(f"   Message to sign: {message[:80]}...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.text:
            print(f"   Response: {response.text[:200]}")
        else:
            print(f"   Response: Empty")
        return response.status_code
    except Exception as e:
        print(f"   Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 WEEX API SIGNATURE DEBUG TEST")
    print("=" * 60)
    
    # Test different base URLs
    print("\n\n🌐 Testing with api-contract.weex.com")
    test_endpoint("V1 - /capi/v2/account/assets", sign_v1, "/capi/v2/account/assets", 
                  base_url="https://api-contract.weex.com")
    
    print("\n\n🌐 Testing Unified API endpoint")
    test_endpoint("Unified - currentPlan", sign_v2, "/api/uni/v3/order/currentPlan", 
                  "symbol=cmt_btcusdt&delegateType=0",
                  base_url="https://api-contract.weex.com")
    
    # Try with different endpoints
    print("\n\n🌐 Testing position endpoint")
    test_endpoint("V1 - allPosition", sign_v1, "/capi/v2/position/allPosition",
                  base_url="https://api-contract.weex.com")
    
    print("\n" + "=" * 60)
