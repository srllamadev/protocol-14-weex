#!/usr/bin/env python3
"""Test API via WeexClient"""
from weex_client import WeexClient

c = WeexClient()

print('=== ALL POSITIONS ===')
pos = c.get_all_positions()
print(f'Result: {pos}')

print('\n=== BTC POSITION ===')
pos2 = c.get_positions('cmt_btcusdt')
print(f'Result: {pos2}')

print('\n=== ETH POSITION ===')
pos3 = c.get_positions('cmt_ethusdt')
print(f'Result: {pos3}')

print('\n=== BALANCE ===')
b = c.get_account_assets()
if isinstance(b, list):
    for a in b:
        if a.get('coinName') == 'USDT':
            print(f"Equity: {a.get('equity')}")
            print(f"Available: {a.get('available')}")
            print(f"Frozen: {a.get('frozen')}")
            print(f"Unrealized: {a.get('unrealizePnl')}")

print('\n=== OPEN ORDERS BTC ===')
orders = c.get_open_orders('cmt_btcusdt')
print(f'Result: {orders}')

print('\n=== OPEN ORDERS ETH ===')
orders2 = c.get_open_orders('cmt_ethusdt')
print(f'Result: {orders2}')

print('\nDone!')
