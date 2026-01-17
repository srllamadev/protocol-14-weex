#!/usr/bin/env python3
"""Cancel all pending and plan orders"""
import os
import time
import hmac
import hashlib
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('WEEX_API_KEY')
SECRET_KEY = os.getenv('WEEX_SECRET_KEY')
PASSPHRASE = os.getenv('WEEX_PASSPHRASE')
BASE_URL = 'https://api-contract.weex.com'

def sign(method, path, query='', body=''):
    ts = str(int(time.time() * 1000))
    msg = ts + method + path + query + body
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return ts, sig

def headers(ts, sig):
    return {
        'ACCESS-KEY': API_KEY, 
        'ACCESS-SIGN': sig, 
        'ACCESS-TIMESTAMP': ts, 
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }

symbols = ['cmt_solusdt', 'cmt_ethusdt', 'cmt_bnbusdt', 'cmt_adausdt', 'cmt_ltcusdt', 'cmt_dogeusdt', 'cmt_btcusdt']

print("=" * 50)
print("🔄 CANCELANDO TODAS LAS ÓRDENES")
print("=" * 50)

# Cancel all regular orders
for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    
    # Cancel all orders
    path = '/capi/v2/order/cancelAll'
    body = {"symbol": symbol, "marginCoin": "USDT"}
    body_str = json.dumps(body)
    ts, sig = sign('POST', path, '', body_str)
    
    try:
        resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=10)
        result = resp.json()
        if result.get('code') != '40015':  # Not "no orders"
            print(f"{coin} cancelAll: {result}")
    except:
        pass
    
    # Cancel plan orders (SL/TP)
    path = '/capi/v2/order/cancelPlan'
    body = {"symbol": symbol, "marginCoin": "USDT"}
    body_str = json.dumps(body)
    ts, sig = sign('POST', path, '', body_str)
    
    try:
        resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=10)
        result = resp.json()
        if result.get('code') != '40015':
            print(f"{coin} cancelPlan: {result}")
    except:
        pass
    
    time.sleep(0.3)

# Try alternative endpoints
print("\n🔄 Trying alternative cancel endpoints...")

for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    
    # Cancel trigger orders
    path = '/capi/v2/order/cancelAllTrigger'
    body = {"symbol": symbol}
    body_str = json.dumps(body)
    ts, sig = sign('POST', path, '', body_str)
    
    try:
        resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            print(f"{coin} cancelTrigger: {result}")
    except:
        pass
    
    time.sleep(0.2)

# Final balance check
print("\n" + "=" * 50)
print("💰 BALANCE FINAL")
print("=" * 50)

time.sleep(2)

path = '/capi/v2/account/assets'
ts, sig = sign('GET', path)
resp = requests.get(f'{BASE_URL}{path}', headers=headers(ts, sig), timeout=10)
data = resp.json()

if isinstance(data, list):
    for a in data:
        if a.get('coinName') == 'USDT':
            equity = float(a.get('equity', 0))
            available = float(a.get('available', 0))
            frozen = float(a.get('frozen', 0))
            unrealized = float(a.get('unrealizePnl', 0))
            
            print(f"Equity: ${equity:,.2f}")
            print(f"Available: ${available:,.2f}")
            print(f"Frozen: ${frozen:,.2f}")
            print(f"Unrealized: ${unrealized:+,.2f}")
            
            if available > 100:
                print(f"\n✅ ¡${available:,.2f} disponible para trading!")
            elif frozen > 0:
                print(f"\n⚠️ Aún hay ${frozen:,.2f} frozen")
                print("   Puede tomar unos minutos en liberarse...")
