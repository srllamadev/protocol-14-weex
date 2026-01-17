#!/usr/bin/env python3
"""
🚀💎 ULTRA AGGRESSIVE SCALPER + WHALE FOLLOWER
WEEX AI HACKATHON - META: $2,000

Combina:
1. Momentum Scalper (RSI extremo + trailing stop)
2. Whale Follower (detecta volumen anormal de ballenas)

Configuración ULTRA AGRESIVA:
- Leverage: 25x (máximo riesgo controlado)
- RSI: 25/75 (más extremo = más señales fuertes)
- Trailing Stop: 1.5% (lock profits fast)
- Volumen anormal: >2x promedio = ballena detectada
"""

import sys
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from weex_client import WeexClient

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN ULTRA AGRESIVA
# ═══════════════════════════════════════════════════════════════

# Gestión de Capital - USA TODO EL MARGEN DISPONIBLE
MARGIN_USAGE_PCT = 95        # Usar 95% del margen disponible
MIN_TRADE_USD = 1            # Mínimo $1 por trade (muy pequeño pero funciona)
LEVERAGE = 25                # 25x = máxima exposición
MAX_POSITIONS = 4            # Máximo 4 posiciones simultáneas
MAX_DAILY_LOSS = 100         # Máximo pérdida diaria $100

# Señales RSI - MÁS AGRESIVO
RSI_OVERSOLD = 30            # RSI < 30 = LONG
RSI_OVERBOUGHT = 70          # RSI > 70 = SHORT
RSI_PERIOD = 14

# Whale Detection (volumen anormal)
WHALE_VOLUME_MULTIPLIER = 2.0  # Volumen > 2x promedio = ballena
WHALE_BOOST = 20               # Bonus de fuerza si hay ballena

# Take Profit & Stop Loss
TAKE_PROFIT_PCT = 4.0        # 4% TP (más alcanzable con alta volatilidad)
STOP_LOSS_PCT = 2.0          # 2% SL (tight, protege capital)
TRAILING_STOP_PCT = 1.5      # 1.5% trailing 
TRAILING_ACTIVATION = 1.0    # Activa trailing después de +1%

# Timing
SCAN_INTERVAL = 10           # Escanear cada 10 segundos (más rápido)
COOLDOWN_SECONDS = 60        # 1 minuto entre trades misma moneda

# Monedas a tradear (las más volátiles)
COINS = ['SOL', 'ETH', 'DOGE', 'ADA', 'LTC', 'BNB']

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


class UltraScalper:
    def __init__(self):
        self.client = WeexClient()
        self.positions = {}
        self.cooldowns = {}
        self.daily_pnl = 0
        self.trades_today = 0
        self.wins = 0
        self.losses = 0
        self.trailing_data = {}
        
        # Verificar balance inicial
        self.check_balance()
    
    def check_balance(self):
        """Verificar y mostrar balance"""
        try:
            assets = self.client.get_account_assets()
            if isinstance(assets, list):
                for a in assets:
                    if a.get('coinName') == 'USDT':
                        self.equity = float(a.get('equity', 0))
                        self.available = float(a.get('available', 0))
                        self.frozen = float(a.get('frozen', 0))
                        self.unrealized = float(a.get('unrealizePnl', 0))
                        return True
        except:
            pass
        return False
    
    def get_symbol(self, coin: str) -> str:
        return f"cmt_{coin.lower()}usdt"
    
    def get_step_size(self, symbol: str) -> float:
        return STEP_SIZES.get(symbol, 0.01)
    
    def calculate_size(self, symbol: str, price: float) -> float:
        """Calcular tamaño usando el margen disponible"""
        # Usar porcentaje del margen disponible
        trade_margin = self.available * MARGIN_USAGE_PCT / 100
        
        # Mínimo requerido
        if trade_margin < MIN_TRADE_USD:
            trade_margin = MIN_TRADE_USD
        
        # Calcular notional con leverage
        notional = trade_margin * LEVERAGE
        raw_size = notional / price
        step = self.get_step_size(symbol)
        size = round(raw_size / step) * step
        
        # Asegurar decimales correctos
        decimals = len(str(step).split('.')[-1]) if '.' in str(step) else 0
        return round(size, decimals)
    
    def calculate_rsi(self, closes: list, period: int = RSI_PERIOD) -> float:
        """Calcular RSI"""
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def detect_whale(self, volumes: list) -> tuple:
        """Detectar actividad de ballena (volumen anormal)"""
        if len(volumes) < 20:
            return False, 1.0
        
        avg_volume = sum(volumes[-20:-1]) / 19  # Promedio sin la última vela
        current_volume = volumes[-1]
        
        if avg_volume <= 0:
            return False, 1.0
        
        volume_ratio = current_volume / avg_volume
        is_whale = volume_ratio >= WHALE_VOLUME_MULTIPLIER
        
        return is_whale, volume_ratio
    
    def is_on_cooldown(self, symbol: str) -> bool:
        if symbol not in self.cooldowns:
            return False
        elapsed = (datetime.now() - self.cooldowns[symbol]).total_seconds()
        return elapsed < COOLDOWN_SECONDS
    
    def analyze_coin(self, coin: str) -> dict:
        """Análisis completo de una moneda"""
        symbol = self.get_symbol(coin)
        
        try:
            # Obtener ticker
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None
            
            ticker_data = ticker.get('data', ticker) if isinstance(ticker, dict) else ticker
            price = float(ticker_data.get('last', 0))
            if price <= 0:
                return None
            
            # Obtener velas
            candles = self.client.get_candles(symbol, granularity='1m', limit=50)
            if not candles or len(candles) < 25:
                return None
            
            candles_sorted = sorted(candles, key=lambda x: int(x[0]))
            
            closes = [float(c[4]) for c in candles_sorted]
            volumes = [float(c[5]) for c in candles_sorted]
            highs = [float(c[2]) for c in candles_sorted]
            lows = [float(c[3]) for c in candles_sorted]
            
            # Calcular indicadores
            rsi = self.calculate_rsi(closes)
            is_whale, volume_ratio = self.detect_whale(volumes)
            
            # Momentum: cambio % en últimas 3 velas
            momentum = ((closes[-1] - closes[-4]) / closes[-4]) * 100 if closes[-4] > 0 else 0
            
            # Volatilidad
            ranges = [(h - l) / l * 100 for h, l in zip(highs[-10:], lows[-10:]) if l > 0]
            volatility = sum(ranges) / len(ranges) if ranges else 0
            
            # Generar señal
            signal = None
            strength = 0
            whale_detected = False
            
            # RSI extremo = señal fuerte
            if rsi < RSI_OVERSOLD:
                signal = 'long'
                strength = min(100, 50 + (RSI_OVERSOLD - rsi) * 3)
                if momentum < -0.5:  # Caída fuerte = mejor entrada
                    strength = min(100, strength + 10)
                    
            elif rsi > RSI_OVERBOUGHT:
                signal = 'short'
                strength = min(100, 50 + (rsi - RSI_OVERBOUGHT) * 3)
                if momentum > 0.5:  # Subida fuerte = mejor entrada short
                    strength = min(100, strength + 10)
            
            # WHALE BOOST: Si detectamos ballena, boost la señal
            if signal and is_whale:
                strength = min(100, strength + WHALE_BOOST)
                whale_detected = True
            
            # Si volatilidad es muy baja, reducir señal
            if volatility < 0.3:
                strength = int(strength * 0.8)
            
            return {
                'coin': coin,
                'symbol': symbol,
                'price': price,
                'rsi': round(rsi, 1),
                'momentum': round(momentum, 2),
                'volatility': round(volatility, 2),
                'volume_ratio': round(volume_ratio, 1),
                'is_whale': whale_detected,
                'signal': signal,
                'strength': int(strength)
            }
            
        except Exception as e:
            return None
    
    def execute_trade(self, analysis: dict) -> dict:
        """Ejecutar trade"""
        symbol = analysis['symbol']
        price = analysis['price']
        signal = analysis['signal']
        coin = analysis['coin']
        
        # Verificar margen disponible
        if not self.check_balance():
            return {'success': False, 'error': 'No se pudo verificar balance'}
        
        if self.available < MIN_TRADE_USD:
            return {'success': False, 'error': f'Margen insuficiente: ${self.available:.2f}'}
        
        # Calcular tamaño
        size = self.calculate_size(symbol, price)
        trade_margin = self.available * MARGIN_USAGE_PCT / 100
        
        # Definir side
        if signal == 'long':
            side = 'open_long'
            stop_loss = round(price * (1 - STOP_LOSS_PCT / 100), 6)
            take_profit = round(price * (1 + TAKE_PROFIT_PCT / 100), 6)
        else:
            side = 'open_short'
            stop_loss = round(price * (1 + STOP_LOSS_PCT / 100), 6)
            take_profit = round(price * (1 - TAKE_PROFIT_PCT / 100), 6)
        
        # Ejecutar orden
        result = self.client.place_order(
            symbol=symbol,
            side=side,
            order_type='market',
            size=str(size)
        )
        
        # Verificar resultado
        order_id = None
        if result:
            order_id = result.get('order_id') or (result.get('data', {}) or {}).get('orderId')
        
        if order_id:
            # Registrar posición para trailing
            self.trailing_data[order_id] = {
                'symbol': symbol,
                'coin': coin,
                'side': signal,
                'entry_price': price,
                'size': size,
                'highest': price if signal == 'long' else 999999,
                'lowest': price if signal == 'short' else 0,
                'trailing_active': False,
                'entry_time': datetime.now()
            }
            
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
            error = result.get('msg', 'Unknown') if result else 'No response'
            return {'success': False, 'error': error}
    
    def manage_positions(self):
        """Gestionar posiciones abiertas con trailing stop"""
        to_close = []
        
        for order_id, pos in list(self.trailing_data.items()):
            try:
                symbol = pos['symbol']
                side = pos['side']
                entry = pos['entry_price']
                size = pos['size']
                
                # Obtener precio actual
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                ticker_data = ticker.get('data', ticker) if isinstance(ticker, dict) else ticker
                current = float(ticker_data.get('last', 0))
                if current <= 0:
                    continue
                
                # Calcular PnL
                if side == 'long':
                    pnl_pct = ((current - entry) / entry) * 100
                    pos['highest'] = max(pos['highest'], current)
                    drawdown = ((pos['highest'] - current) / pos['highest']) * 100
                else:
                    pnl_pct = ((entry - current) / entry) * 100
                    pos['lowest'] = min(pos['lowest'], current)
                    drawdown = ((current - pos['lowest']) / pos['lowest']) * 100 if pos['lowest'] > 0 else 0
                
                should_close = False
                close_reason = ""
                
                # Activar trailing
                if pnl_pct >= TRAILING_ACTIVATION and not pos['trailing_active']:
                    pos['trailing_active'] = True
                    print(f"   📈 Trailing activado {pos['coin']} (+{pnl_pct:.1f}%)")
                
                # Trailing stop hit
                if pos['trailing_active'] and drawdown >= TRAILING_STOP_PCT:
                    should_close = True
                    close_reason = f"Trailing ({pnl_pct:+.1f}%)"
                
                # Take profit
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    should_close = True
                    close_reason = f"TP ({pnl_pct:+.1f}%)"
                
                # Stop loss
                elif pnl_pct <= -STOP_LOSS_PCT:
                    should_close = True
                    close_reason = f"SL ({pnl_pct:+.1f}%)"
                
                if should_close:
                    close_side = 'close_long' if side == 'long' else 'close_short'
                    
                    close_result = self.client.place_order(
                        symbol=symbol,
                        side=close_side,
                        order_type='market',
                        size=str(size)
                    )
                    
                    if close_result and (close_result.get('order_id') or close_result.get('data')):
                        # Calcular PnL real basado en el tamaño de posición
                        pnl_usd = pnl_pct * size * entry / 100
                        
                        self.daily_pnl += pnl_usd
                        
                        if pnl_usd > 0:
                            self.wins += 1
                            emoji = "✅"
                        else:
                            self.losses += 1
                            emoji = "❌"
                        
                        print(f"   {emoji} {pos['coin']} {close_reason}: ${pnl_usd:+.2f}")
                        to_close.append(order_id)
                        
            except Exception as e:
                continue
        
        for oid in to_close:
            if oid in self.trailing_data:
                del self.trailing_data[oid]
    
    def display_status(self, analyses: list):
        """Mostrar estado actual"""
        print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Escaneando...")
        print("-" * 65)
        
        for a in analyses:
            if a is None:
                continue
            
            coin = a['coin']
            price = a['price']
            rsi = a['rsi']
            strength = a['strength']
            signal = a['signal']
            is_whale = a.get('is_whale', False)
            
            # Emoji por estado
            if signal == 'long':
                emoji = "🟢"
                bar = "█" * (strength // 10)
            elif signal == 'short':
                emoji = "🔴"
                bar = "█" * (strength // 10)
            else:
                emoji = "⚪"
                bar = "░" * 10
            
            bar = bar.ljust(10, "░")
            
            # Whale indicator
            whale = "🐋" if is_whale else "  "
            
            signal_text = f"{signal.upper()} {strength}%" if signal else "Neutral"
            
            print(f"{emoji} {whale} {coin:5} | ${price:>10,.4f} | RSI: {rsi:5.1f} | [{bar}] {signal_text}")
        
        print("-" * 65)
        
        win_rate = (self.wins / (self.wins + self.losses) * 100) if (self.wins + self.losses) > 0 else 0
        print(f"📊 Posiciones: {len(self.trailing_data)} | Trades: {self.trades_today} | W/L: {self.wins}/{self.losses} ({win_rate:.0f}%)")
        print(f"💰 PnL Hoy: ${self.daily_pnl:+.2f} | Balance: ${self.equity:,.2f} | Disponible: ${self.available:,.2f}")
    
    def run(self):
        """Loop principal"""
        self.check_balance()
        
        print("=" * 65)
        print("🚀💎 ULTRA AGGRESSIVE SCALPER + WHALE FOLLOWER")
        print("=" * 65)
        print(f"💰 Margen: {MARGIN_USAGE_PCT}% del disponible x {LEVERAGE}x")
        print(f"📊 RSI: < {RSI_OVERSOLD} (LONG) | > {RSI_OVERBOUGHT} (SHORT)")
        print(f"🐋 Whale Detection: Volumen > {WHALE_VOLUME_MULTIPLIER}x promedio")
        print(f"📈 Trailing: {TRAILING_STOP_PCT}% (activa en +{TRAILING_ACTIVATION}%)")
        print(f"🎯 TP: {TAKE_PROFIT_PCT}% | SL: {STOP_LOSS_PCT}%")
        print(f"⏱️ Scan: {SCAN_INTERVAL}s | Cooldown: {COOLDOWN_SECONDS}s")
        print(f"🪙 Coins: {', '.join(COINS)}")
        print(f"💵 Balance: ${self.equity:.2f} | Disponible: ${self.available:.2f}")
        print("=" * 65)
        
        if self.available <= 0:
            print(f"\n⚠️ Sin margen disponible (${self.available:.2f})")
            print(f"   Frozen: ${self.frozen:.2f}")
            print(f"   Esperando a que se libere el margen...")
        
        print("\n🔥 Iniciando... Ctrl+C para detener\n")
        
        try:
            while True:
                # Check si hay margen
                self.check_balance()
                
                # Gestionar posiciones existentes
                if self.trailing_data:
                    self.manage_positions()
                
                # Verificar pérdida máxima diaria
                if self.daily_pnl <= -MAX_DAILY_LOSS:
                    print(f"\n⛔ Pérdida máxima diaria alcanzada: ${self.daily_pnl:.2f}")
                    print("   Deteniendo bot para proteger capital...")
                    break
                
                # Analizar todas las monedas
                analyses = []
                for coin in COINS:
                    a = self.analyze_coin(coin)
                    if a:
                        analyses.append(a)
                    time.sleep(0.2)
                
                # Mostrar estado
                self.display_status(analyses)
                
                # Filtrar señales - AGRESIVO: 40% mínimo
                signals = [a for a in analyses if a and a['signal'] and a['strength'] >= 40]
                
                # Ordenar por fuerza (whale primero, luego por strength)
                signals.sort(key=lambda x: (x.get('is_whale', False), x['strength']), reverse=True)
                
                # Ejecutar trades
                for a in signals[:2]:  # Máximo 2 trades por scan
                    symbol = a['symbol']
                    
                    if self.is_on_cooldown(symbol):
                        continue
                    
                    if len(self.trailing_data) >= MAX_POSITIONS:
                        print(f"   ⚠️ Máximo {MAX_POSITIONS} posiciones alcanzado")
                        break
                    
                    whale = "🐋" if a.get('is_whale') else ""
                    signal_type = "LONG" if a['signal'] == 'long' else "SHORT"
                    color = "🟢" if a['signal'] == 'long' else "🔴"
                    
                    print(f"\n{'🔥' * 10}")
                    print(f"   {whale} ¡SEÑAL {a['strength']}%!")
                    print(f"{'🔥' * 10}")
                    print(f"\n{color} {signal_type} en {a['coin']}")
                    print(f"   💰 Precio: ${a['price']:,.4f}")
                    print(f"   📊 RSI: {a['rsi']} | Vol: {a['volume_ratio']}x")
                    
                    result = self.execute_trade(a)
                    
                    if result['success']:
                        print(f"   ✅ Orden ejecutada: {result['order_id']}")
                        print(f"   📦 Size: {result['size']}")
                        print(f"   🛑 SL: ${result['stop_loss']:,.4f}")
                        print(f"   🎯 TP: ${result['take_profit']:,.4f}")
                    else:
                        print(f"   ⚠️ Error: {result['error']}")
                    
                    time.sleep(0.5)
                
                print(f"\n⏳ Próximo scan en {SCAN_INTERVAL}s...")
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Ultra Scalper detenido")
            print(f"   Trades: {self.trades_today}")
            print(f"   Win/Loss: {self.wins}/{self.losses}")
            print(f"   PnL: ${self.daily_pnl:+.2f}")


if __name__ == "__main__":
    scalper = UltraScalper()
    scalper.run()
