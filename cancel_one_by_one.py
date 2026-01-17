#!/usr/bin/env python3
"""Cancel orders one by one"""
from weex_client import WeexClient
import time

c = WeexClient()

print("=" * 50)
print("CANCELLING ORDERS ONE BY ONE")
print("=" * 50)

# Get BTC orders
orders = c.get_open_orders('cmt_btcusdt')
if isinstance(orders, list):
    for order in orders:
        order_id = order.get('order_id')
        client_oid = order.get('client_oid')
        price = order.get('price')
        print(f"\nCancelling BTC order {order_id} @ ${float(price):,.2f}")
        result = c.cancel_order('cmt_btcusdt', order_id=order_id)
        print(f"Result: {result}")
        time.sleep(0.5)

# Get ETH orders  
orders = c.get_open_orders('cmt_ethusdt')
if isinstance(orders, list):
    for order in orders:
        order_id = order.get('order_id')
        price = order.get('price')
        print(f"\nCancelling ETH order {order_id} @ ${float(price):,.2f}")
        result = c.cancel_order('cmt_ethusdt', order_id=order_id)
        print(f"Result: {result}")
        time.sleep(0.5)

# Verify
print("\n" + "=" * 50)
print("VERIFICATION")
print("=" * 50)

for symbol in ['cmt_btcusdt', 'cmt_ethusdt']:
    coin = symbol.replace('cmt_', '').replace('usdt', '').upper()
    orders = c.get_open_orders(symbol)
    if isinstance(orders, list) and len(orders) > 0:
        print(f"{coin}: Still has {len(orders)} orders!")
        for o in orders:
            print(f"  - {o.get('order_id')} @ ${float(o.get('price', 0)):,.2f}")
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
