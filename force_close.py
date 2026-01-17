#!/usr/bin/env python3
"""
🔥 FORCE CLOSE ALL - Intenta cerrar TODAS las posibles posiciones
"""

import os
import time
import hmac
import hashlib
import base64
import json
import requests
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

def close_position(symbol, side, size):
    """Intentar cerrar una posición"""
    # type: 3=close_long, 4=close_short
    type_num = '3' if side == 'long' else '4'
    
    path = '/capi/v2/order/placeOrder'
    body = {
        'symbol': symbol,
        'client_oid': f'force_close_{int(time.time())}',
        'size': str(size),
        'type': type_num,
        'order_type': '0',
        'match_price': '1',
    }
    body_str = json.dumps(body)
    ts, sig = sign('POST', path, '', body_str)
    
    try:
        resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=15)
        return resp.json()
    except Exception as e:
        return {'error': str(e)}

# Símbolos y tamaños comunes a intentar cerrar
POSITIONS_TO_TRY = [
    # SOL - sizes vistos en historial
    ('cmt_solusdt', 'short', 1.0),
    ('cmt_solusdt', 'short', 2.0),
    ('cmt_solusdt', 'short', 0.5),
    ('cmt_solusdt', 'long', 1.0),
    ('cmt_solusdt', 'long', 2.0),
    
    # ETH
    ('cmt_ethusdt', 'short', 0.1),
    ('cmt_ethusdt', 'short', 0.2),
    ('cmt_ethusdt', 'long', 0.1),
    ('cmt_ethusdt', 'long', 0.2),
    
    # BNB
    ('cmt_bnbusdt', 'short', 0.2),
    ('cmt_bnbusdt', 'short', 0.5),
    ('cmt_bnbusdt', 'long', 0.2),
    ('cmt_bnbusdt', 'long', 0.5),
    
    # ADA
    ('cmt_adausdt', 'short', 100),
    ('cmt_adausdt', 'short', 200),
    ('cmt_adausdt', 'long', 100),
    ('cmt_adausdt', 'long', 200),
    
    # DOGE
    ('cmt_dogeusdt', 'short', 500),
    ('cmt_dogeusdt', 'short', 1000),
    ('cmt_dogeusdt', 'long', 500),
    ('cmt_dogeusdt', 'long', 1000),
    
    # LTC
    ('cmt_ltcusdt', 'short', 0.5),
    ('cmt_ltcusdt', 'short', 1.0),
    ('cmt_ltcusdt', 'long', 0.5),
    ('cmt_ltcusdt', 'long', 1.0),
    
    # BTC
    ('cmt_btcusdt', 'short', 0.01),
    ('cmt_btcusdt', 'short', 0.005),
    ('cmt_btcusdt', 'long', 0.01),
    ('cmt_btcusdt', 'long', 0.005),
]

print("=" * 60)
print("🔥 FORCE CLOSE - Intentando cerrar todas las posiciones")
print("=" * 60)

closed = 0
for symbol, side, size in POSITIONS_TO_TRY:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    result = close_position(symbol, side, size)
    
    # Si tiene order_id, se cerró algo
    if result.get('order_id'):
        print(f"✅ {coin} {side.upper()} x{size} - CERRADO!")
        closed += 1
    elif result.get('code') == '40015' and 'not enough' not in str(result.get('msg', '')).lower():
        # Puede ser que la posición no existe
        pass
    elif 'position' in str(result.get('msg', '')).lower():
        print(f"ℹ️ {coin} {side} x{size}: {result.get('msg', '')[:50]}")
    
    time.sleep(0.3)

print(f"\n📊 Posiciones cerradas: {closed}")

# Verificar balance final
print("\n" + "=" * 60)
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
            
            print(f"💰 BALANCE:")
            print(f"   Equity: ${equity:,.2f}")
            print(f"   Available: ${available:,.2f}")
            print(f"   Frozen: ${frozen:,.2f}")
            print(f"   Unrealized: ${unrealized:+,.2f}")
            
            if available > 100:
                print(f"\n🚀 ¡LISTO! ${available:,.2f} disponible")
                print("   Ejecuta: python ultra_scalper.py")
            elif frozen > 0:
                print(f"\n⚠️ Aún hay ${frozen:,.2f} frozen")
                print("   Ve a la web de WEEX y cierra manualmente:")
                print("   1. Futures → Positions → Close All")
                print("   2. Orders → Open Orders → Cancel All")

print("=" * 60)
