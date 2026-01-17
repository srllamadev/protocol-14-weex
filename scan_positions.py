#!/usr/bin/env python3
"""Scan all positions"""
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

def sign(method, path, query=''):
    ts = str(int(time.time() * 1000))
    msg = ts + method + path + query
    sig = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return ts, sig

def headers(ts, sig):
    return {'ACCESS-KEY': API_KEY, 'ACCESS-SIGN': sig, 'ACCESS-TIMESTAMP': ts, 'ACCESS-PASSPHRASE': PASSPHRASE}

symbols = ['cmt_solusdt', 'cmt_ethusdt', 'cmt_bnbusdt', 'cmt_adausdt', 'cmt_ltcusdt', 'cmt_dogeusdt', 'cmt_btcusdt', 'cmt_xrpusdt']

print("Scanning all positions...")
found_any = False

for symbol in symbols:
    path = '/capi/v2/position/singlePosition'
    query = f'?symbol={symbol}&marginCoin=USDT'
    ts, sig = sign('GET', path, query)
    resp = requests.get(f'{BASE_URL}{path}{query}', headers=headers(ts, sig), timeout=10)
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    
    if resp.text and resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            for pos in data:
                total = float(pos.get('total', 0))
                available = float(pos.get('available', 0))
                margin = float(pos.get('margin', 0))
                side = pos.get('holdSide', '?')
                if total > 0 or margin > 0:
                    found_any = True
                    print(f'{coin}: total={total}, avail={available}, margin=${margin:.2f}, side={side}')
    time.sleep(0.3)

if not found_any:
    print("No positions found in any symbol")

# Check balance
print("\n--- Balance ---")
path = '/capi/v2/account/assets'
ts, sig = sign('GET', path)
resp = requests.get(f'{BASE_URL}{path}', headers=headers(ts, sig), timeout=10)
data = resp.json()
if isinstance(data, list):
    for a in data:
        if a.get('coinName') == 'USDT':
            print(f"Equity: ${float(a.get('equity', 0)):,.2f}")
            print(f"Available: ${float(a.get('available', 0)):,.2f}")
            print(f"Frozen: ${float(a.get('frozen', 0)):,.2f}")
            print(f"Unrealized: ${float(a.get('unrealizePnl', 0)):+,.2f}")
