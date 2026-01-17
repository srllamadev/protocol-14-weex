#!/usr/bin/env python3
"""Try different cancel endpoints"""
import os, time, hmac, hashlib, base64, requests, json
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('WEEX_API_KEY')
SECRET_KEY = os.getenv('WEEX_SECRET_KEY')
PASSPHRASE = os.getenv('WEEX_PASSPHRASE')
BASE = 'https://api-contract.weex.com'

def sign(m, p, q='', b=''):
    t = str(int(time.time() * 1000))
    msg = t + m + p + q + b
    s = base64.b64encode(hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return t, s

def h(t, s):
    return {
        'ACCESS-KEY': API_KEY, 
        'ACCESS-SIGN': s, 
        'ACCESS-TIMESTAMP': t, 
        'ACCESS-PASSPHRASE': PASSPHRASE, 
        'Content-Type': 'application/json'
    }

# Try different cancel endpoints
endpoints = [
    '/capi/v2/order/cancel',
    '/capi/v2/trade/cancel_order',
    '/capi/v2/trade/cancelOrder',
    '/capi/v1/order/cancelOrder',
    '/capi/v2/order/cancel_order',
]

order_id = '706751912426341375'
body = json.dumps({'symbol': 'cmt_btcusdt', 'orderId': order_id, 'marginCoin': 'USDT'})

print("Testing cancel endpoints...")
for ep in endpoints:
    t, s = sign('POST', ep, '', body)
    try:
        r = requests.post(f'{BASE}{ep}', headers=h(t, s), data=body, timeout=10)
        text = r.text[:150] if r.text else "empty"
        print(f"{ep}: {r.status_code} - {text}")
    except Exception as e:
        print(f"{ep}: Error - {e}")

# Try batch cancel
print("\nTrying batch cancel...")
body2 = json.dumps({'symbol': 'cmt_btcusdt', 'marginCoin': 'USDT'})
for ep in ['/capi/v2/order/cancel_batch', '/capi/v2/order/cancelBatch', '/capi/v2/order/cancelSymbolOrder']:
    t, s = sign('POST', ep, '', body2)
    try:
        r = requests.post(f'{BASE}{ep}', headers=h(t, s), data=body2, timeout=10)
        text = r.text[:150] if r.text else "empty"
        print(f"{ep}: {r.status_code} - {text}")
    except Exception as e:
        print(f"{ep}: Error - {e}")
