#!/usr/bin/env python3
"""
🚀 MOMENTUM SCALPER - WEEX AI HACKATHON
Estrategia agresiva con acción constante y trailing stop

Configuración:
- RSI < 30: LONG | RSI > 70: SHORT
- Trailing Stop: 2% (protege ganancias)
- Take Profit: 6% objetivo
- Stop Loss: 3% máximo
- Apalancamiento: 15x
- Monto base: $80 (escalable)
"""

import sys
import time
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from weex_client import WeexClient

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN AGRESIVA
# ═══════════════════════════════════════════════════════════════
TRADE_SIZE_USD = 30          # $30 por trade (reducido para permitir más trades)
LEVERAGE = 20                # 20x apalancamiento = $600 exposición
RSI_OVERSOLD = 30            # RSI < 30 = LONG
RSI_OVERBOUGHT = 70          # RSI > 70 = SHORT
STOP_LOSS_PCT = 2.5          # 2.5% stop loss (más ajustado)
TAKE_PROFIT_PCT = 5.0        # 5% take profit
TRAILING_STOP_PCT = 1.5      # 1.5% trailing (se activa cuando hay +2% ganancia)
TRAILING_ACTIVATION = 1.0    # Activar trailing después de +1%
SCAN_INTERVAL = 15           # Escanear cada 15 segundos (más rápido)
MAX_POSITIONS_PER_COIN = 2   # Máximo 2 posiciones por moneda
MAX_TOTAL_POSITIONS = 10     # Máximo 10 posiciones totales
COOLDOWN_SECONDS = 120       # 2 minutos entre trades misma moneda

# Monedas a tradear
COINS = ['SOL', 'ETH', 'BNB', 'DOGE', 'ADA', 'LTC']

# Step sizes por moneda
STEP_SIZES = {
    'cmt_btcusdt': 0.001,
    'cmt_ethusdt': 0.01,
    'cmt_solusdt': 0.1,
    'cmt_bnbusdt': 0.1,
    'cmt_adausdt': 10,
    'cmt_dogeusdt': 100,
    'cmt_ltcusdt': 0.1,
}

class MomentumScalper:
    def __init__(self):
        self.client = WeexClient()
        self.active_positions = {}  # {symbol: [positions]}
        self.cooldowns = {}  # {symbol: last_trade_time}
        self.daily_pnl = 0
        self.trades_today = 0
        self.trailing_stops = {}  # {order_id: {'highest': price, 'stop': price}}
    
    def calculate_rsi(self, closes: list, period: int = 14) -> float:
        """Calcular RSI manualmente"""
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def get_symbol(self, coin: str) -> str:
        return f"cmt_{coin.lower()}usdt"
    
    def get_step_size(self, symbol: str) -> float:
        return STEP_SIZES.get(symbol, 0.01)
    
    def calculate_size(self, symbol: str, price: float) -> float:
        """Calcular tamaño de posición"""
        notional = TRADE_SIZE_USD * LEVERAGE
        raw_size = notional / price
        step = self.get_step_size(symbol)
        return round(raw_size / step) * step
    
    def is_on_cooldown(self, symbol: str) -> bool:
        """Verificar si la moneda está en cooldown"""
        if symbol not in self.cooldowns:
            return False
        elapsed = (datetime.now() - self.cooldowns[symbol]).total_seconds()
        return elapsed < COOLDOWN_SECONDS
    
    def get_remaining_cooldown(self, symbol: str) -> int:
        """Obtener segundos restantes de cooldown"""
        if symbol not in self.cooldowns:
            return 0
        elapsed = (datetime.now() - self.cooldowns[symbol]).total_seconds()
        remaining = COOLDOWN_SECONDS - elapsed
        return max(0, int(remaining))
    
    def analyze_coin(self, coin: str) -> dict:
        """Analizar una moneda y generar señal"""
        symbol = self.get_symbol(coin)
        
        try:
            # Obtener datos
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None
            
            # La API devuelve directamente el objeto o con wrapper 'data'
            ticker_data = ticker.get('data', ticker) if isinstance(ticker, dict) else ticker
            price = float(ticker_data.get('last', 0))
            if price <= 0:
                return None
            
            # Obtener velas para RSI y Momentum
            candles = self.client.get_candles(symbol, granularity='1m', limit=50)
            if not candles or not isinstance(candles, list) or len(candles) < 20:
                return None
            
            # Ordenar por timestamp (más antiguo primero)
            candles_sorted = sorted(candles, key=lambda x: int(x[0]))
            
            closes = [float(c[4]) for c in candles_sorted]
            highs = [float(c[2]) for c in candles_sorted]
            lows = [float(c[3]) for c in candles_sorted]
            
            if len(closes) < 20:
                return None
            
            # Calcular indicadores
            rsi = self.calculate_rsi(closes, period=14)
            
            # Momentum: cambio porcentual en últimas 5 velas
            momentum = ((closes[-1] - closes[-5]) / closes[-5]) * 100 if closes[-5] > 0 else 0
            
            # Volatilidad: rango promedio
            ranges = [(h - l) / l * 100 for h, l in zip(highs[-10:], lows[-10:]) if l > 0]
            volatility = sum(ranges) / len(ranges) if ranges else 0
            
            # Generar señal
            signal = None
            strength = 0
            
            if rsi < RSI_OVERSOLD:
                signal = 'long'
                # Fuerza basada en qué tan bajo está el RSI
                strength = min(100, 50 + (RSI_OVERSOLD - rsi) * 2.5)
                # Bonus por momentum negativo (sobreventa extrema)
                if momentum < -1:
                    strength = min(100, strength + 10)
                    
            elif rsi > RSI_OVERBOUGHT:
                signal = 'short'
                # Fuerza basada en qué tan alto está el RSI
                strength = min(100, 50 + (rsi - RSI_OVERBOUGHT) * 2.5)
                # Bonus por momentum positivo (sobrecompra extrema)
                if momentum > 1:
                    strength = min(100, strength + 10)
            
            return {
                'coin': coin,
                'symbol': symbol,
                'price': price,
                'rsi': rsi,
                'momentum': momentum,
                'volatility': volatility,
                'signal': signal,
                'strength': strength
            }
            
        except Exception as e:
            return None
    
    def execute_trade(self, analysis: dict) -> dict:
        """Ejecutar un trade"""
        symbol = analysis['symbol']
        price = analysis['price']
        signal = analysis['signal']
        
        # Calcular tamaño
        size = self.calculate_size(symbol, price)
        
        # Calcular SL y TP
        if signal == 'long':
            stop_loss = round(price * (1 - STOP_LOSS_PCT / 100), 6)
            take_profit = round(price * (1 + TAKE_PROFIT_PCT / 100), 6)
            side = 'open_long'
        else:
            stop_loss = round(price * (1 + STOP_LOSS_PCT / 100), 6)
            take_profit = round(price * (1 - TAKE_PROFIT_PCT / 100), 6)
            side = 'open_short'
        
        # Ejecutar orden de mercado
        result = self.client.place_order(
            symbol=symbol,
            side=side,
            order_type='market',
            size=str(size),
            margin_coin='USDT',
            client_oid=str(uuid.uuid4())
        )
        
        # Verificar respuesta - WEEX devuelve order_id directamente o en data
        order_id = None
        if result:
            order_id = result.get('order_id') or (result.get('data', {}) or {}).get('orderId')
        
        if order_id:
            # Registrar para trailing stop
            self.trailing_stops[order_id] = {
                'symbol': symbol,
                'side': signal,  # 'long' o 'short'
                'entry_price': price,
                'highest': price if signal == 'long' else price,
                'lowest': price if signal == 'short' else price,
                'trailing_active': False,
                'size': size
            }
            
            # Actualizar cooldown
            self.cooldowns[symbol] = datetime.now()
            self.trades_today += 1
            
            return {
                'success': True,
                'order_id': order_id,
                'side': side,
                'price': price,
                'size': size,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        else:
            error = result.get('msg', 'Unknown error') if result else 'No response'
            # Si es error de margen, no crashear
            if 'margin' in str(error).lower() or 'not enough' in str(error).lower():
                print(f"   ⚠️ Margen insuficiente, saltando...")
            return {'success': False, 'error': error}
    
    def check_trailing_stops(self):
        """Verificar y actualizar trailing stops"""
        to_remove = []
        
        for order_id, data in self.trailing_stops.items():
            try:
                symbol = data['symbol']
                side = data['side']
                entry_price = data['entry_price']
                
                # Obtener precio actual
                ticker = self.client.get_ticker(symbol)
                if not ticker or 'data' not in ticker:
                    continue
                
                current_price = float(ticker['data'].get('last', 0))
                if current_price <= 0:
                    continue
                
                # Calcular PnL actual
                if side == 'long':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    
                    # Actualizar highest
                    if current_price > data['highest']:
                        data['highest'] = current_price
                    
                    # Activar trailing si ganancia > TRAILING_ACTIVATION
                    if pnl_pct >= TRAILING_ACTIVATION and not data['trailing_active']:
                        data['trailing_active'] = True
                        print(f"   📈 Trailing activado para {symbol} (+{pnl_pct:.1f}%)")
                    
                    # Si trailing activo, verificar si cerrar
                    if data['trailing_active']:
                        drawdown = ((data['highest'] - current_price) / data['highest']) * 100
                        if drawdown >= TRAILING_STOP_PCT:
                            # Cerrar posición
                            close_result = self.client.place_order(
                                symbol=symbol,
                                side='close_long',
                                order_type='market',
                                size=str(data['size']),
                                margin_coin='USDT',
                                client_oid=str(uuid.uuid4())
                            )
                            if close_result and 'data' in close_result:
                                profit = (current_price - entry_price) * data['size']
                                self.daily_pnl += profit
                                print(f"   ✅ Trailing cerró {symbol}: +${profit:.2f}")
                                to_remove.append(order_id)
                    
                    # Stop loss normal
                    elif pnl_pct <= -STOP_LOSS_PCT:
                        close_result = self.client.place_order(
                            symbol=symbol,
                            side='close_long',
                            order_type='market',
                            size=str(data['size']),
                            margin_coin='USDT',
                            client_oid=str(uuid.uuid4())
                        )
                        if close_result and 'data' in close_result:
                            loss = (current_price - entry_price) * data['size']
                            self.daily_pnl += loss
                            print(f"   ⛔ Stop loss {symbol}: ${loss:.2f}")
                            to_remove.append(order_id)
                    
                    # Take profit
                    elif pnl_pct >= TAKE_PROFIT_PCT:
                        close_result = self.client.place_order(
                            symbol=symbol,
                            side='close_long',
                            order_type='market',
                            size=str(data['size']),
                            margin_coin='USDT',
                            client_oid=str(uuid.uuid4())
                        )
                        if close_result and 'data' in close_result:
                            profit = (current_price - entry_price) * data['size']
                            self.daily_pnl += profit
                            print(f"   🎯 Take profit {symbol}: +${profit:.2f}")
                            to_remove.append(order_id)
                
                else:  # short
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                    
                    # Actualizar lowest
                    if current_price < data['lowest']:
                        data['lowest'] = current_price
                    
                    # Activar trailing
                    if pnl_pct >= TRAILING_ACTIVATION and not data['trailing_active']:
                        data['trailing_active'] = True
                        print(f"   📉 Trailing activado para {symbol} (+{pnl_pct:.1f}%)")
                    
                    # Si trailing activo
                    if data['trailing_active']:
                        drawdown = ((current_price - data['lowest']) / data['lowest']) * 100
                        if drawdown >= TRAILING_STOP_PCT:
                            close_result = self.client.place_order(
                                symbol=symbol,
                                side='close_short',
                                order_type='market',
                                size=str(data['size']),
                                margin_coin='USDT',
                                client_oid=str(uuid.uuid4())
                            )
                            if close_result and 'data' in close_result:
                                profit = (entry_price - current_price) * data['size']
                                self.daily_pnl += profit
                                print(f"   ✅ Trailing cerró {symbol}: +${profit:.2f}")
                                to_remove.append(order_id)
                    
                    # Stop loss
                    elif pnl_pct <= -STOP_LOSS_PCT:
                        close_result = self.client.place_order(
                            symbol=symbol,
                            side='close_short',
                            order_type='market',
                            size=str(data['size']),
                            margin_coin='USDT',
                            client_oid=str(uuid.uuid4())
                        )
                        if close_result and 'data' in close_result:
                            loss = (entry_price - current_price) * data['size']
                            self.daily_pnl += loss
                            print(f"   ⛔ Stop loss {symbol}: ${loss:.2f}")
                            to_remove.append(order_id)
                    
                    # Take profit
                    elif pnl_pct >= TAKE_PROFIT_PCT:
                        close_result = self.client.place_order(
                            symbol=symbol,
                            side='close_short',
                            order_type='market',
                            size=str(data['size']),
                            margin_coin='USDT',
                            client_oid=str(uuid.uuid4())
                        )
                        if close_result and 'data' in close_result:
                            profit = (entry_price - current_price) * data['size']
                            self.daily_pnl += profit
                            print(f"   🎯 Take profit {symbol}: +${profit:.2f}")
                            to_remove.append(order_id)
                            
            except Exception as e:
                continue
        
        # Limpiar posiciones cerradas
        for order_id in to_remove:
            del self.trailing_stops[order_id]
    
    def print_status(self, analyses: list):
        """Mostrar estado actual"""
        print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Escaneando...")
        print("-" * 60)
        
        for a in analyses:
            if a is None:
                continue
            
            # Icono de señal
            if a['signal'] == 'long':
                icon = "🟢"
                signal_text = f"LONG {a['strength']:.0f}%"
            elif a['signal'] == 'short':
                icon = "🔴"
                signal_text = f"SHORT {a['strength']:.0f}%"
            else:
                icon = "⚪"
                signal_text = "Neutral"
            
            # Barra de fuerza
            bars = int(a.get('strength', 0) / 10)
            bar = "█" * bars + "░" * (10 - bars)
            
            # Cooldown
            cooldown = self.get_remaining_cooldown(a['symbol'])
            cooldown_text = f" ⏳{cooldown}s" if cooldown > 0 else ""
            
            print(f"{icon} {a['coin']:>5} | ${a['price']:>10.4f} | RSI: {a['rsi']:>5.1f} | "
                  f"Mom: {a['momentum']:>+5.1f}% | [{bar}] {signal_text}{cooldown_text}")
        
        print("-" * 60)
        print(f"📊 Posiciones activas: {len(self.trailing_stops)} | "
              f"Trades hoy: {self.trades_today} | PnL: ${self.daily_pnl:+.2f}")
    
    def run(self):
        """Loop principal"""
        print("=" * 60)
        print("🚀 MOMENTUM SCALPER - WEEX AI HACKATHON")
        print("=" * 60)
        print(f"💰 Monto: ${TRADE_SIZE_USD} x {LEVERAGE}x = ${TRADE_SIZE_USD * LEVERAGE}")
        print(f"📊 RSI: < {RSI_OVERSOLD} (LONG) | > {RSI_OVERBOUGHT} (SHORT)")
        print(f"📈 Trailing Stop: {TRAILING_STOP_PCT}% (activa en +{TRAILING_ACTIVATION}%)")
        print(f"🎯 Take Profit: {TAKE_PROFIT_PCT}% | Stop Loss: {STOP_LOSS_PCT}%")
        print(f"⏱️ Escaneo cada: {SCAN_INTERVAL}s")
        print(f"🪙 Monedas: {', '.join(COINS)}")
        print("=" * 60)
        print("\n🔥 Iniciando... Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                # Analizar todas las monedas
                analyses = []
                for coin in COINS:
                    analysis = self.analyze_coin(coin)
                    if analysis:
                        analyses.append(analysis)
                    time.sleep(0.2)  # Rate limiting
                
                # Mostrar estado
                self.print_status(analyses)
                
                # Verificar trailing stops
                if self.trailing_stops:
                    self.check_trailing_stops()
                
                # Buscar oportunidades de entrada
                for a in analyses:
                    if a is None or a['signal'] is None:
                        continue
                    
                    # Verificar cooldown
                    if self.is_on_cooldown(a['symbol']):
                        continue
                    
                    # Verificar máximo de posiciones
                    if len(self.trailing_stops) >= MAX_TOTAL_POSITIONS:
                        continue
                    
                    # Solo ejecutar si señal es fuerte (>50%)
                    if a['strength'] < 50:
                        continue
                    
                    # Ejecutar trade
                    side_emoji = "🟢 LONG" if a['signal'] == 'long' else "🔴 SHORT"
                    print(f"\n{'🔥' * 20}")
                    print(f"   ¡SEÑAL DETECTADA!")
                    print(f"{'🔥' * 20}")
                    print(f"\n{side_emoji} en {a['coin']}")
                    print(f"   💰 Precio: ${a['price']:.4f}")
                    print(f"   📊 RSI: {a['rsi']:.1f} | Momentum: {a['momentum']:+.1f}%")
                    print(f"   📈 Fuerza: {a['strength']:.0f}%")
                    
                    result = self.execute_trade(a)
                    
                    if result['success']:
                        print(f"   ✅ Orden ejecutada: {result['order_id']}")
                        print(f"   📦 Size: {result['size']}")
                        print(f"   🛑 SL: ${result['stop_loss']:.4f} ({STOP_LOSS_PCT}%)")
                        print(f"   🎯 TP: ${result['take_profit']:.4f} ({TAKE_PROFIT_PCT}%)")
                        print(f"   📈 Trailing: {TRAILING_STOP_PCT}% (activa en +{TRAILING_ACTIVATION}%)")
                    else:
                        print(f"   ⚠️ Error: {result.get('error', 'Unknown')}")
                
                # Esperar
                print(f"\n⏳ Próximo escaneo en {SCAN_INTERVAL}s...")
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Momentum Scalper detenido")
            print(f"   Trades ejecutados: {self.trades_today}")
            print(f"   PnL del día: ${self.daily_pnl:+.2f}")
            print(f"   Posiciones abiertas: {len(self.trailing_stops)}")


if __name__ == "__main__":
    scalper = MomentumScalper()
    scalper.run()
