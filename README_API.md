# 📚 WEEX API - Guía de Referencia

> Documentación basada en pruebas reales. Última actualización: Enero 2026

## 🔑 Autenticación

### Variables de Entorno (.env)
```env
WEEX_API_KEY=tu_api_key
WEEX_SECRET_KEY=tu_secret_key
WEEX_PASSPHRASE=tu_passphrase
```

### Generación de Firma
```python
import hmac
import hashlib
import base64
import time

def generate_signature(secret_key: str, timestamp: str, method: str, 
                       request_path: str, query_string: str = "", body: str = "") -> str:
    """
    Genera firma HMAC SHA256 para autenticación
    
    Args:
        secret_key: Tu SECRET_KEY de WEEX
        timestamp: Timestamp en milisegundos
        method: GET, POST, DELETE
        request_path: Ej: /capi/v2/account/assets
        query_string: Para GET con params (incluir el ?)
        body: JSON string para POST
    
    Returns:
        Firma en Base64
    """
    # Para GET: timestamp + METHOD + path + queryString
    # Para POST: timestamp + METHOD + path + queryString + body
    if method.upper() == "GET":
        prehash = timestamp + method.upper() + request_path + query_string
    else:
        prehash = timestamp + method.upper() + request_path + query_string + body
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        prehash.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')
```

### Headers Requeridos
```python
headers = {
    "ACCESS-KEY": API_KEY,
    "ACCESS-SIGN": signature,
    "ACCESS-TIMESTAMP": str(int(time.time() * 1000)),
    "ACCESS-PASSPHRASE": PASSPHRASE,
    "Content-Type": "application/json",
    "locale": "en-US",
}
```

---

## ✅ Endpoints que FUNCIONAN

### Base URL
```
https://api-contract.weex.com
```

### 📊 Cuenta y Balance

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/capi/v2/account/assets` | GET | Balance de la cuenta |
| `/capi/v2/account/singleAccount?symbol=X&marginCoin=USDT` | GET | Info cuenta por símbolo |

**Ejemplo - Obtener Balance:**
```python
path = '/capi/v2/account/assets'
timestamp = str(int(time.time() * 1000))
signature = generate_signature(SECRET_KEY, timestamp, 'GET', path)

response = requests.get(
    f'{BASE_URL}{path}',
    headers=headers,
    timeout=10
)

# Respuesta:
# [{"coinName":"USDT","available":"47.85","equity":"1014.18","frozen":"121.33","unrealizePnl":"16.00"}]
```

### 📈 Market Data (Público)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/capi/v2/market/ticker?symbol=cmt_btcusdt` | GET | Precio actual |
| `/capi/v2/market/candles?symbol=X&granularity=X` | GET | Velas/OHLCV |

**Ejemplo - Obtener Precio:**
```python
url = f"{BASE_URL}/capi/v2/market/ticker?symbol=cmt_btcusdt"
response = requests.get(url, timeout=10)
# No requiere autenticación
```

### 📋 Órdenes

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/capi/v2/order/pending?symbol=X` | GET | Órdenes abiertas |
| `/capi/v2/order/history?symbol=X&pageSize=N` | GET | Historial de órdenes |
| `/capi/v2/order/placeOrder` | POST | Colocar orden |
| `/capi/v2/order/cancel_order` | POST | ⚠️ Cancelar orden (con guión bajo!) |

**Ejemplo - Obtener Órdenes Abiertas:**
```python
path = '/capi/v2/order/pending'
query = '?symbol=cmt_btcusdt'
timestamp = str(int(time.time() * 1000))
signature = generate_signature(SECRET_KEY, timestamp, 'GET', path, query)

response = requests.get(
    f'{BASE_URL}{path}{query}',
    headers=headers,
    timeout=10
)
```

**Ejemplo - Cancelar Orden:**
```python
import json

path = '/capi/v2/order/cancel_order'  # ⚠️ IMPORTANTE: usar guión bajo!
body = json.dumps({
    'symbol': 'cmt_btcusdt',
    'orderId': '706751912426341375',
    'marginCoin': 'USDT'
})
timestamp = str(int(time.time() * 1000))
signature = generate_signature(SECRET_KEY, timestamp, 'POST', path, '', body)

response = requests.post(
    f'{BASE_URL}{path}',
    headers=headers,
    data=body,
    timeout=10
)

# Respuesta exitosa:
# {"order_id":"706751912426341375","client_oid":null,"result":true,"err_msg":null}
```

**Ejemplo - Colocar Orden:**
```python
path = '/capi/v2/order/placeOrder'
body = json.dumps({
    'symbol': 'cmt_btcusdt',
    'marginCoin': 'USDT',
    'side': 'open_long',      # open_long, open_short, close_long, close_short
    'orderType': 'limit',     # limit, market
    'price': '95000',
    'size': '0.001',
    'clientOid': 'mi_orden_123'  # Opcional, tu ID único
})
timestamp = str(int(time.time() * 1000))
signature = generate_signature(SECRET_KEY, timestamp, 'POST', path, '', body)

response = requests.post(
    f'{BASE_URL}{path}',
    headers=headers,
    data=body,
    timeout=10
)
```

### ⚙️ Configuración

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/capi/v2/account/setLeverage` | POST | Configurar apalancamiento |

**Ejemplo - Configurar Leverage:**
```python
path = '/capi/v2/account/setLeverage'
body = json.dumps({
    'symbol': 'cmt_btcusdt',
    'marginCoin': 'USDT',
    'leverage': '10'
})
```

---

## ❌ Endpoints que NO Funcionan (404)

| Endpoint | Error | Alternativa |
|----------|-------|-------------|
| `/capi/v2/order/cancelOrder` | 404 | Usar `/capi/v2/order/cancel_order` |
| `/capi/v2/order/cancelAllOrder` | 404 | Cancelar uno por uno |
| `/capi/v2/order/cancelAll` | 404 | Cancelar uno por uno |
| `/capi/v2/order/cancelPlan` | 404 | - |

---

## ⚠️ Endpoints Inestables (521)

Estos endpoints a veces dan error 521 (Web Server Down):

| Endpoint | Descripción |
|----------|-------------|
| `/capi/v2/position/singlePosition` | Posición por símbolo |
| `/capi/v2/position/allPosition` | Todas las posiciones |

**Workaround:** Usar el balance para detectar posiciones:
- Si `frozen > 0` → Hay margin en uso (posición abierta)
- Si `unrealizePnl != 0` → Hay PnL no realizado (posición abierta)

---

## 🏷️ Símbolos Soportados

Formato: `cmt_[coin]usdt`

| Símbolo | Par |
|---------|-----|
| `cmt_btcusdt` | BTC/USDT |
| `cmt_ethusdt` | ETH/USDT |
| `cmt_solusdt` | SOL/USDT |
| `cmt_bnbusdt` | BNB/USDT |
| `cmt_adausdt` | ADA/USDT |
| `cmt_dogeusdt` | DOGE/USDT |
| `cmt_ltcusdt` | LTC/USDT |
| `cmt_xrpusdt` | XRP/USDT |

---

## 📝 Tipos de Órdenes

### Side (Dirección)
| Valor | Descripción |
|-------|-------------|
| `open_long` | Abrir posición larga (comprar) |
| `open_short` | Abrir posición corta (vender) |
| `close_long` | Cerrar posición larga |
| `close_short` | Cerrar posición corta |

### Order Type
| Valor | Descripción |
|-------|-------------|
| `limit` | Orden límite (requiere precio) |
| `market` | Orden de mercado |

### Status de Órdenes
| Valor | Descripción |
|-------|-------------|
| `open` | Pendiente/Abierta |
| `filled` | Ejecutada |
| `canceled` | Cancelada |
| `partially_filled` | Parcialmente ejecutada |

---

## 🔧 Código de Referencia Rápida

### Función Helper Completa
```python
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

def sign(method: str, path: str, query: str = '', body: str = ''):
    """Genera timestamp y firma"""
    ts = str(int(time.time() * 1000))
    msg = ts + method + path + query + body
    sig = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return ts, sig

def headers(ts: str, sig: str):
    """Genera headers de autenticación"""
    return {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': sig,
        'ACCESS-TIMESTAMP': ts,
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }

def get_balance():
    """Obtener balance de la cuenta"""
    path = '/capi/v2/account/assets'
    ts, sig = sign('GET', path)
    r = requests.get(f'{BASE_URL}{path}', headers=headers(ts, sig), timeout=10)
    return r.json()

def get_open_orders(symbol: str):
    """Obtener órdenes abiertas"""
    path = '/capi/v2/order/pending'
    query = f'?symbol={symbol}'
    ts, sig = sign('GET', path, query)
    r = requests.get(f'{BASE_URL}{path}{query}', headers=headers(ts, sig), timeout=10)
    return r.json() if r.status_code == 200 else []

def cancel_order(symbol: str, order_id: str):
    """Cancelar una orden"""
    path = '/capi/v2/order/cancel_order'
    body = json.dumps({'symbol': symbol, 'orderId': order_id, 'marginCoin': 'USDT'})
    ts, sig = sign('POST', path, '', body)
    r = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body, timeout=10)
    return r.json()

def place_order(symbol: str, side: str, order_type: str, size: str, price: str = None):
    """Colocar una orden"""
    path = '/capi/v2/order/placeOrder'
    order_data = {
        'symbol': symbol,
        'marginCoin': 'USDT',
        'side': side,
        'orderType': order_type,
        'size': size,
        'clientOid': f'order_{int(time.time())}'
    }
    if price:
        order_data['price'] = price
    
    body = json.dumps(order_data)
    ts, sig = sign('POST', path, '', body)
    r = requests.post(f'{BASE_URL}{path}', headers=headers(ts, sig), data=body, timeout=10)
    return r.json()

def get_price(symbol: str):
    """Obtener precio actual (público)"""
    url = f'{BASE_URL}/capi/v2/market/ticker?symbol={symbol}'
    r = requests.get(url, timeout=10)
    data = r.json()
    return float(data.get('last', 0)) if data else 0
```

---

## 🚨 Errores Comunes

| Código | Significado | Solución |
|--------|-------------|----------|
| 401 | No autorizado | Verificar API_KEY, SECRET_KEY, PASSPHRASE |
| 404 | Endpoint no existe | Verificar URL (ej: usar `cancel_order` no `cancelOrder`) |
| 521 | Servidor caído | Reintentar después, es temporal |
| 40015 | No hay órdenes | Normal si no hay órdenes que cancelar |

---

## 📁 Archivos Útiles del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `weex_client.py` | Cliente principal con todos los métodos |
| `check_positions.py` | Verificar posiciones y balance |
| `cancel_all_now.py` | Cancelar todas las órdenes |
| `test_client.py` | Pruebas del cliente |
| `quick_check.py` | Verificación rápida del estado |

---

## 💡 Tips

1. **Siempre usar timeout** en las requests (recomendado: 10-30 segundos)
2. **Rate limiting**: Esperar 0.3-0.5 segundos entre requests
3. **El timestamp** debe ser en milisegundos, no segundos
4. **Los precios** deben ser strings, no números
5. **El size** debe ser string con el formato correcto (ej: "0.001" para BTC)
6. **Verificar el balance** antes de operar para saber el available
