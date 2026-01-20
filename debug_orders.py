#!/usr/bin/env python3
"""Debug: Ver estructura de órdenes"""
import json
from weex_client import WeexClient

client = WeexClient()
orders = client.get_order_history("cmt_btcusdt", page_size=5)

print("=== ESTRUCTURA DE ORDENES ===")
if orders and len(orders) > 0:
    print(json.dumps(orders[0], indent=2))
    print("\n=== KEYS DISPONIBLES ===")
    print(list(orders[0].keys()))
else:
    print("Sin órdenes")
