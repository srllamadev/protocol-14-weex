"""
🔍 WEEX API Quick Test
Run this script to check if your IP is whitelisted

Expected response when IP is whitelisted:
- Status 200 + account balance data

Current response when IP NOT whitelisted:
- Status 521 (Web server is down / IP not whitelisted)
"""

import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

# Your credentials from .env
API_KEY = os.getenv("WEEX_API_KEY")
SECRET_KEY = os.getenv("WEEX_SECRET_KEY")
PASSPHRASE = os.getenv("WEEX_PASSPHRASE")

BASE_URL = "https://api-contract.weex.com"


def get_public_ip():
    """Get your current public IP"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip", "Unknown")
    except:
        return "Could not determine"


def test_public_api():
    """Test public endpoint (no auth needed)"""
    print("\n📡 Testing Public API (Ticker)...")
    try:
        response = requests.get(
            f"{BASE_URL}/capi/v2/market/ticker?symbol=cmt_btcusdt",
            timeout=10
        )
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   💰 BTC/USDT Price: ${data.get('last', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_private_api():
    """Test private endpoint (auth required)"""
    print("\n🔐 Testing Private API (Account Assets)...")
    
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    request_path = "/capi/v2/account/assets"
    query_string = ""
    
    # Generate signature: timestamp + METHOD + requestPath + queryString
    message = timestamp + method + request_path + query_string
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode()
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature_b64,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}{request_path}",
            headers=headers,
            timeout=30
        )
        
        print(f"   📊 Status Code: {response.status_code}")
        
        if response.status_code == 521:
            print("\n   ❌ ERROR 521: IP NOT WHITELISTED!")
            print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("   Your IP is not in the WEEX whitelist yet.")
            print("   Wait for admin response and try again.")
            return False
        elif response.status_code == 200:
            data = response.json()
            print("\n   ✅ SUCCESS! IP IS WHITELISTED!")
            print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            if isinstance(data, list):
                for asset in data:
                    coin = asset.get('coinName', 'N/A')
                    available = asset.get('available', '0')
                    equity = asset.get('equity', '0')
                    print(f"   💰 {coin}: Available={available}, Equity={equity}")
            else:
                print(f"   📋 Response: {data}")
            return True
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
            print(f"   📋 Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 WEEX API CONNECTION TEST")
    print("=" * 60)
    
    # Show current IP
    current_ip = get_public_ip()
    print(f"\n🌐 Your Current Public IP: {current_ip}")
    print(f"   (This IP must be whitelisted by WEEX)")
    
    # Show credentials status
    print(f"\n🔑 Credentials Status:")
    print(f"   API Key: {'✅ Loaded' if API_KEY else '❌ Missing'}")
    print(f"   Secret:  {'✅ Loaded' if SECRET_KEY else '❌ Missing'}")
    print(f"   Pass:    {'✅ Loaded' if PASSPHRASE else '❌ Missing'}")
    
    # Run tests
    test_public_api()
    test_private_api()
    
    print("\n" + "=" * 60)
    print("Test completed! Run again after IP is whitelisted.")
    print("=" * 60)
