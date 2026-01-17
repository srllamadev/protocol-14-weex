#!/usr/bin/env python3
"""Cancel all orders using WeexClient"""
from weex_client import WeexClient

c = WeexClient()

symbols = ['cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_bnbusdt']

print("=" * 50)
print("CANCELLING ALL ORDERS")
print("=" * 50)

for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    
    # Get open orders first
    orders = c.get_open_orders(symbol)
    if isinstance(orders, list) and len(orders) > 0:
        print(f"\n{coin}: Found {len(orders)} open orders")
        
        # Cancel all
        result = c.cancel_all_orders(symbol)
        print(f"Cancel result: {result}")
    else:
        print(f"{coin}: No open orders")

# Verify
print("\n" + "=" * 50)
print("VERIFICATION")
print("=" * 50)

for symbol in symbols:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    orders = c.get_open_orders(symbol)
    if isinstance(orders, list) and len(orders) > 0:
        print(f"{coin}: Still has {len(orders)} orders!")
    else:
        print(f"{coin}: ✓ No orders")

# Balance
print("\n" + "=" * 50)
print("BALANCE")
print("=" * 50)

b = c.get_account_assets()
if isinstance(b, list):
    for a in b:
        if a.get('coinName') == 'USDT':
            print(f"Equity: ${float(a.get('equity', 0)):,.2f}")
            print(f"Available: ${float(a.get('available', 0)):,.2f}")
            print(f"Frozen: ${float(a.get('frozen', 0)):,.2f}")
            print(f"Unrealized: ${float(a.get('unrealizePnl', 0)):+,.2f}")
