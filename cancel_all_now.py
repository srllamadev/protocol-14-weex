#!/usr/bin/env python3
"""Cancel all orders using correct endpoint"""
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

def get_open_orders(symbol):
    path = '/capi/v2/order/pending'
    query = f'?symbol={symbol}'
    t, s = sign('GET', path, query)
    r = requests.get(f'{BASE}{path}{query}', headers=h(t, s), timeout=10)
    if r.status_code == 200 and r.text:
        return r.json()
    return []

def cancel_order(symbol, order_id):
    path = '/capi/v2/order/cancel_order'
    body = json.dumps({'symbol': symbol, 'orderId': order_id, 'marginCoin': 'USDT'})
    t, s = sign('POST', path, '', body)
    r = requests.post(f'{BASE}{path}', headers=h(t, s), data=body, timeout=10)
    return r.json() if r.text else {}

print("=" * 50)
print("CANCELLING ALL REMAINING ORDERS")
print("=" * 50)

for symbol in ['cmt_btcusdt', 'cmt_ethusdt']:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    orders = get_open_orders(symbol)
    
    if isinstance(orders, list) and len(orders) > 0:
        print(f"\n{coin}: {len(orders)} orders to cancel")
        for o in orders:
            order_id = o.get('order_id')
            price = float(o.get('price', 0))
            print(f"  Cancelling {order_id} @ ${price:,.2f}...")
            result = cancel_order(symbol, order_id)
            if result.get('result') == True:
                print(f"    ✓ Cancelled")
            else:
                print(f"    ✗ Failed: {result}")
            time.sleep(0.3)
    else:
        print(f"{coin}: No orders")

# Verify
print("\n" + "=" * 50)
print("VERIFICATION")
print("=" * 50)

for symbol in ['cmt_btcusdt', 'cmt_ethusdt']:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    orders = get_open_orders(symbol)
    if isinstance(orders, list) and len(orders) > 0:
        print(f"{coin}: Still has {len(orders)} orders!")
    else:
        print(f"{coin}: ✓ No orders")

# Balance
print("\n" + "=" * 50)
print("BALANCE")
print("=" * 50)

path = '/capi/v2/account/assets'
t, s = sign('GET', path)
r = requests.get(f'{BASE}{path}', headers=h(t, s), timeout=10)
if r.status_code == 200:
    for a in r.json():
        if a.get('coinName') == 'USDT':
            print(f"Equity: ${float(a.get('equity', 0)):,.2f}")
            print(f"Available: ${float(a.get('available', 0)):,.2f}")
            print(f"Frozen: ${float(a.get('frozen', 0)):,.2f}")
            print(f"Unrealized: ${float(a.get('unrealizePnl', 0)):+,.2f}")

print("\n✅ Done!")
