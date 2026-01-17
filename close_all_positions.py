#!/usr/bin/env python3
"""
🔥 CERRAR TODAS LAS POSICIONES
Libera todo el margen para el Momentum Scalper
"""

import os
import time
import hmac
import hashlib
import base64
import json
import uuid
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

# Todos los símbolos posibles
SYMBOLS = [
    'cmt_solusdt', 'cmt_ethusdt', 'cmt_bnbusdt', 
    'cmt_btcusdt', 'cmt_adausdt', 'cmt_dogeusdt', 
    'cmt_ltcusdt', 'cmt_xrpusdt', 'cmt_avaxusdt'
]

print("=" * 60)
print("🔥 CERRANDO TODAS LAS POSICIONES")
print("=" * 60)

positions_found = []

# Buscar posiciones en todos los símbolos
for symbol in SYMBOLS:
    try:
        path = '/capi/v2/position/singlePosition'
        query = f'?symbol={symbol}&marginCoin=USDT'
        ts, sig = sign('GET', path, query)
        resp = requests.get(f'{BASE_URL}{path}{query}', headers=headers(ts, sig), timeout=10)
        
        if resp.text and resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                for pos in data:
                    total = float(pos.get('total', 0))
                    if total > 0:
                        coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
                        side = pos.get('holdSide', '')
                        entry = float(pos.get('averageOpenPrice', 0))
                        pnl = float(pos.get('unrealizedPL', 0))
                        margin = float(pos.get('margin', 0))
                        
                        positions_found.append({
                            'symbol': symbol,
                            'coin': coin,
                            'side': side,
                            'size': total,
                            'entry': entry,
                            'pnl': pnl,
                            'margin': margin
                        })
                        
                        print(f"\n📍 {coin} {side.upper()}")
                        print(f"   Size: {total}")
                        print(f"   Entry: ${entry:,.4f}")
                        print(f"   PnL: ${pnl:+,.2f}")
                        print(f"   Margin: ${margin:,.2f}")
    except Exception as e:
        pass

if not positions_found:
    print("\n✅ No hay posiciones abiertas!")
    
    # Verificar balance
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
                
                print(f"\n💰 Balance USDT:")
                print(f"   Equity: ${equity:,.2f}")
                print(f"   Available: ${available:,.2f}")
                print(f"   Frozen: ${frozen:,.2f}")
                print(f"   Unrealized PnL: ${unrealized:+,.2f}")
                
                if frozen > 0:
                    print(f"\n⚠️ Hay ${frozen:,.2f} frozen - puede haber órdenes pendientes")
else:
    print(f"\n\n🔄 Cerrando {len(positions_found)} posiciones...")
    
    total_pnl = 0
    
    for pos in positions_found:
        symbol = pos['symbol']
        side = pos['side']
        size = pos['size']
        coin = pos['coin']
        
        # Determinar el lado de cierre
        if side == 'long':
            close_side = 'close_long'
        else:
            close_side = 'close_short'
        
        # Colocar orden de cierre
        path = '/capi/v2/order/placeOrder'
        body = {
            "symbol": symbol,
            "marginCoin": "USDT",
            "size": str(size),
            "side": close_side,
            "orderType": "market",
            "clientOid": str(uuid.uuid4()).replace('-', '')[:32]
        }
        body_str = json.dumps(body)
        
        ts, sig = sign('POST', path, '', body_str)
        
        try:
            resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=10)
            result = resp.json()
            
            if result.get('order_id') or result.get('code') == '00000':
                print(f"   ✅ {coin} {side.upper()} cerrado")
                total_pnl += pos['pnl']
            else:
                print(f"   ❌ Error cerrando {coin}: {result.get('msg', result)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Pequeña pausa entre órdenes
    
    print(f"\n💰 PnL total realizado: ${total_pnl:+,.2f}")

# Cancelar órdenes pendientes
print("\n🔄 Cancelando órdenes pendientes...")

for symbol in SYMBOLS:
    try:
        path = '/capi/v2/order/cancelAll'
        body = {
            "symbol": symbol,
            "marginCoin": "USDT"
        }
        body_str = json.dumps(body)
        ts, sig = sign('POST', path, '', body_str)
        
        resp = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body_str, timeout=10)
        result = resp.json()
        
        if result.get('code') == '00000' or 'success' in str(result).lower():
            coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
            # Solo mostrar si había algo que cancelar
    except:
        pass

# Balance final
print("\n" + "=" * 60)
print("💰 BALANCE FINAL")
print("=" * 60)

time.sleep(1)  # Esperar a que se procesen las órdenes

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
            
            print(f"\n   Equity: ${equity:,.2f}")
            print(f"   Available: ${available:,.2f}")
            print(f"   Frozen: ${frozen:,.2f}")
            
            if available > 0:
                print(f"\n✅ ¡Listo! ${available:,.2f} disponible para trading")
            else:
                print(f"\n⚠️ Aún hay margen congelado, espera unos segundos...")

print("\n" + "=" * 60)
