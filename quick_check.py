#!/usr/bin/env python3
"""Quick check positions and orders"""
import os, time, hmac, hashlib, base64, requests
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

symbols = ['cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_bnbusdt', 'cmt_adausdt', 'cmt_dogeusdt', 'cmt_ltcusdt', 'cmt_xrpusdt']

print("=" * 50)
print("CHECKING POSITIONS")
print("=" * 50)

for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    path = '/capi/v2/position/singlePosition'
    query = f'?symbol={symbol}&marginCoin=USDT'
    ts, sig = sign('GET', path, query)
    
    try:
        resp = requests.get(f'{BASE_URL}{path}{query}', headers=headers(ts, sig), timeout=10)
        if resp.status_code == 200 and resp.text:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                for pos in data:
                    total = float(pos.get('total', 0))
                    margin = float(pos.get('margin', 0))
                    if total > 0 or margin > 0:
                        side = pos.get('holdSide', '?')
                        entry = pos.get('averageOpenPrice', 0)
                        pnl = pos.get('unrealizedPL', 0)
                        liq = pos.get('liquidationPrice', 0)
                        print(f"\n{coin} - {side.upper()}")
                        print(f"  Size: {total}")
                        print(f"  Entry: ${float(entry):,.4f}")
                        print(f"  Margin: ${margin:.2f}")
                        print(f"  PnL: ${float(pnl):+,.4f}")
                        print(f"  Liquidation: ${float(liq):,.4f}")
    except Exception as e:
        print(f"{coin}: Error - {e}")
    time.sleep(0.3)

print("\n" + "=" * 50)
print("CHECKING PENDING ORDERS")
print("=" * 50)

for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    path = '/capi/v2/order/pending'
    query = f'?symbol={symbol}'
    ts, sig = sign('GET', path, query)
    
    try:
        resp = requests.get(f'{BASE_URL}{path}{query}', headers=headers(ts, sig), timeout=10)
        if resp.status_code == 200 and resp.text:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"\n{coin}: {len(data)} pending orders")
                for o in data:
                    side = o.get('side', '?')
                    price = float(o.get('price', 0))
                    size = o.get('size', '?')
                    print(f"  {side} @ ${price:,.2f} size={size}")
    except Exception as e:
        print(f"{coin}: Error - {e}")
    time.sleep(0.2)

print("\n" + "=" * 50)
print("BALANCE")
print("=" * 50)

path = '/capi/v2/account/assets'
ts, sig = sign('GET', path)
resp = requests.get(f'{BASE_URL}{path}', headers=headers(ts, sig), timeout=10)
if resp.status_code == 200:
    data = resp.json()
    for a in data:
        if a.get('coinName') == 'USDT':
            print(f"Equity: ${float(a.get('equity', 0)):,.2f}")
            print(f"Available: ${float(a.get('available', 0)):,.2f}")
            print(f"Frozen: ${float(a.get('frozen', 0)):,.2f}")
            print(f"Unrealized PnL: ${float(a.get('unrealizePnl', 0)):+,.2f}")

print("\nDone!")
