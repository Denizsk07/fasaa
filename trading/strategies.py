"""Fixed Trading Strategies Module - Alle Strategien funktionieren"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)

class FixedStrategyEngine:
    def __init__(self):
        self.strategies = {
            'bollinger': self.bollinger_bands_strategy,
            'volume': self.volume_strategy,
            'price_action': self.price_action_strategy,
            'smc': self.smc_strategy,
            'patterns': self.pattern_strategy,
            'candlesticks': self.candlestick_strategy,
            'fvg': self.fair_value_gap_strategy,
            'support_resistance': self.support_resistance_strategy
        }
        logger.info("🔧 Fixed Strategy Engine initialized")
        
    def analyze(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, strategy in self.strategies.items():
            try:
                signal = strategy(df)
                results[name] = signal
                
                # Debug log
                direction = signal.get('direction', 'NEUTRAL')
                score = signal.get('score', 0)
                if direction != 'NEUTRAL':
                    logger.debug(f"📊 {name}: {direction} score {score}")
                    
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
                results[name] = {'direction': 'NEUTRAL', 'score': 0, 'reason': f'Error: {str(e)}'}
        return results
    
    def bollinger_bands_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: More sensitive Bollinger Bands"""
        try:
            # Calculate Bollinger Bands
            bb = ta.bbands(df['close'], length=20, std=2)
            if bb is None:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'BB calculation failed'}
            
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_middle'] = bb['BBM_20_2.0'] 
            df['bb_lower'] = bb['BBL_20_2.0']
            
            # Check for NaN values
            if df[['bb_upper', 'bb_middle', 'bb_lower']].iloc[-1].isna().any():
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'BB values are NaN'}
            
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            # BB Width Analysis
            bb_width = last['bb_upper'] - last['bb_lower']
            bb_width_avg = (df['bb_upper'] - df['bb_lower']).rolling(20).mean().iloc[-1]
            
            # Price position relative to bands
            bb_position = (last['close'] - last['bb_lower']) / (last['bb_upper'] - last['bb_lower'])
            
            # FIXED: More sensitive conditions
            
            # Squeeze Breakout (STRONG signal)
            if bb_width < bb_width_avg * 0.8:  # Tighter squeeze detection
                if last['close'] > last['bb_middle'] and bb_position > 0.6:
                    return {'direction': 'BUY', 'score': 80, 'reason': 'BB squeeze breakout bullish'}
                elif last['close'] < last['bb_middle'] and bb_position < 0.4:
                    return {'direction': 'SELL', 'score': 80, 'reason': 'BB squeeze breakout bearish'}
            
            # Band Touches (MEDIUM signal)
            if bb_position <= 0.1:  # Near lower band
                return {'direction': 'BUY', 'score': 65, 'reason': 'BB lower band bounce'}
            elif bb_position >= 0.9:  # Near upper band  
                return {'direction': 'SELL', 'score': 65, 'reason': 'BB upper band rejection'}
            
            # Middle Band Cross (WEAK signal)
            if (prev['close'] < prev['bb_middle'] and last['close'] > last['bb_middle'] and
                last['close'] > prev['close']):
                return {'direction': 'BUY', 'score': 55, 'reason': 'BB middle cross bullish'}
            elif (prev['close'] > prev['bb_middle'] and last['close'] < last['bb_middle'] and
                  last['close'] < prev['close']):
                return {'direction': 'SELL', 'score': 55, 'reason': 'BB middle cross bearish'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No BB signal'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'BB error: {str(e)}'}
    
    def volume_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: More realistic volume analysis"""
        try:
            # Volume moving average
            df['volume_sma'] = df['volume'].rolling(20).mean()
            
            # Check for valid volume data
            if df['volume'].iloc[-1] == 0 or df['volume_sma'].iloc[-1] == 0:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No volume data'}
            
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            last = df.iloc[-1]
            
            # Price change
            price_change = (last['close'] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            
            # FIXED: More sensitive thresholds
            
            # High volume breakout
            if last['volume_ratio'] > 1.5:  # Lower threshold
                if price_change > 0.001:  # 0.1% move
                    return {'direction': 'BUY', 'score': 70, 'reason': 'High volume bullish breakout'}
                elif price_change < -0.001:
                    return {'direction': 'SELL', 'score': 70, 'reason': 'High volume bearish breakout'}
            
            # Medium volume with direction
            if last['volume_ratio'] > 1.2:
                if price_change > 0.0005:
                    return {'direction': 'BUY', 'score': 55, 'reason': 'Increased volume bullish'}
                elif price_change < -0.0005:
                    return {'direction': 'SELL', 'score': 55, 'reason': 'Increased volume bearish'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Low volume activity'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'Volume error: {str(e)}'}
    
    def price_action_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: More sensitive price action"""
        try:
            if len(df) < 20:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Insufficient data'}
            
            # Multiple timeframe highs/lows
            recent_high_5 = df['high'].rolling(5).max().iloc[-1]
            recent_low_5 = df['low'].rolling(5).min().iloc[-1]
            recent_high_10 = df['high'].rolling(10).max().iloc[-1]
            recent_low_10 = df['low'].rolling(10).min().iloc[-1]
            recent_high_20 = df['high'].rolling(20).max().iloc[-1]
            recent_low_20 = df['low'].rolling(20).min().iloc[-1]
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # FIXED: Multiple levels of breakouts
            
            # Strong breakout (20-period)
            if last['close'] > recent_high_20:
                return {'direction': 'BUY', 'score': 75, 'reason': 'Breaking 20-period highs'}
            elif last['close'] < recent_low_20:
                return {'direction': 'SELL', 'score': 75, 'reason': 'Breaking 20-period lows'}
            
            # Medium breakout (10-period)
            if last['close'] > recent_high_10 and last['close'] > prev['close']:
                return {'direction': 'BUY', 'score': 65, 'reason': 'Breaking 10-period highs'}
            elif last['close'] < recent_low_10 and last['close'] < prev['close']:
                return {'direction': 'SELL', 'score': 65, 'reason': 'Breaking 10-period lows'}
            
            # Weak breakout (5-period)
            if last['close'] > recent_high_5 and last['close'] > prev['close']:
                return {'direction': 'BUY', 'score': 55, 'reason': 'Breaking recent highs'}
            elif last['close'] < recent_low_5 and last['close'] < prev['close']:
                return {'direction': 'SELL', 'score': 55, 'reason': 'Breaking recent lows'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No clear breakout'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'PA error: {str(e)}'}
    
    def smc_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: Simplified but working SMC"""
        try:
            if len(df) < 20:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Insufficient data for SMC'}
            
            # Find swing points (simplified)
            swing_period = 5
            highs = df['high'].rolling(swing_period*2+1, center=True).max()
            lows = df['low'].rolling(swing_period*2+1, center=True).min()
            
            # Current and recent swing levels
            current_price = df['close'].iloc[-1]
            
            # Find recent swing highs and lows
            recent_data = df.iloc[-20:]  # Last 20 bars
            swing_highs = []
            swing_lows = []
            
            for i in range(swing_period, len(recent_data) - swing_period):
                if recent_data['high'].iloc[i] == recent_data['high'].iloc[i-swing_period:i+swing_period+1].max():
                    swing_highs.append(recent_data['high'].iloc[i])
                if recent_data['low'].iloc[i] == recent_data['low'].iloc[i-swing_period:i+swing_period+1].min():
                    swing_lows.append(recent_data['low'].iloc[i])
            
            # FIXED: Structure breaks
            if swing_highs:
                last_swing_high = max(swing_highs)
                if current_price > last_swing_high:
                    return {'direction': 'BUY', 'score': 80, 'reason': 'Bullish Break of Structure'}
                elif current_price > last_swing_high * 0.999:  # Close to breaking
                    return {'direction': 'BUY', 'score': 60, 'reason': 'Approaching resistance break'}
            
            if swing_lows:
                last_swing_low = min(swing_lows)
                if current_price < last_swing_low:
                    return {'direction': 'SELL', 'score': 80, 'reason': 'Bearish Break of Structure'}
                elif current_price < last_swing_low * 1.001:  # Close to breaking
                    return {'direction': 'SELL', 'score': 60, 'reason': 'Approaching support break'}
            
            # Liquidity grab (price goes beyond swing then reverses)
            if len(df) >= 3:
                last_3 = df.iloc[-3:]
                if (last_3['low'].iloc[0] > last_3['low'].iloc[1] and 
                    last_3['close'].iloc[-1] > last_3['low'].iloc[1]):
                    return {'direction': 'BUY', 'score': 65, 'reason': 'Liquidity grab bullish'}
                elif (last_3['high'].iloc[0] < last_3['high'].iloc[1] and 
                      last_3['close'].iloc[-1] < last_3['high'].iloc[1]):
                    return {'direction': 'SELL', 'score': 65, 'reason': 'Liquidity grab bearish'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No SMC structure detected'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'SMC error: {str(e)}'}
    
    def pattern_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: Simple but working patterns"""
        try:
            if len(df) < 10:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Insufficient data'}
            
            # Higher highs, higher lows (uptrend)
            recent_closes = df['close'].iloc[-5:]
            recent_highs = df['high'].iloc[-5:]
            recent_lows = df['low'].iloc[-5:]
            
            # Uptrend pattern
            if (recent_closes.iloc[-1] > recent_closes.iloc[0] and
                recent_highs.iloc[-1] > recent_highs.iloc[0] and
                recent_lows.iloc[-1] > recent_lows.iloc[0]):
                return {'direction': 'BUY', 'score': 60, 'reason': 'Higher highs and lows pattern'}
            
            # Downtrend pattern  
            if (recent_closes.iloc[-1] < recent_closes.iloc[0] and
                recent_highs.iloc[-1] < recent_highs.iloc[0] and
                recent_lows.iloc[-1] < recent_lows.iloc[0]):
                return {'direction': 'SELL', 'score': 60, 'reason': 'Lower highs and lows pattern'}
            
            # Flag pattern (consolidation after move)
            last_10 = df.iloc[-10:]
            price_range = last_10['high'].max() - last_10['low'].min()
            recent_range = df['close'].iloc[-3:].max() - df['close'].iloc[-3:].min()
            
            if recent_range < price_range * 0.3:  # Tight consolidation
                trend_direction = 1 if df['close'].iloc[-1] > df['close'].iloc[-10] else -1
                if trend_direction > 0:
                    return {'direction': 'BUY', 'score': 65, 'reason': 'Bullish flag pattern'}
                else:
                    return {'direction': 'SELL', 'score': 65, 'reason': 'Bearish flag pattern'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No clear pattern'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'Pattern error: {str(e)}'}
    
    def candlestick_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: More sensitive candlestick patterns"""
        try:
            if len(df) < 2:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Need at least 2 candles'}
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Calculate candle components
            body = abs(last['close'] - last['open'])
            upper_wick = last['high'] - max(last['close'], last['open'])
            lower_wick = min(last['close'], last['open']) - last['low']
            total_range = last['high'] - last['low']
            
            if total_range == 0:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No price movement'}
            
            # FIXED: More sensitive patterns
            
            # Hammer (bullish)
            if (lower_wick > body * 1.5 and upper_wick < body * 0.5 and 
                last['close'] > last['open']):
                return {'direction': 'BUY', 'score': 65, 'reason': 'Hammer candlestick'}
            
            # Shooting star (bearish)
            if (upper_wick > body * 1.5 and lower_wick < body * 0.5 and 
                last['close'] < last['open']):
                return {'direction': 'SELL', 'score': 65, 'reason': 'Shooting star candlestick'}
            
            # Doji (reversal)
            if body < total_range * 0.1:  # Very small body
                if prev['close'] > prev['open']:  # Previous was bullish
                    return {'direction': 'SELL', 'score': 55, 'reason': 'Doji after bullish candle'}
                elif prev['close'] < prev['open']:  # Previous was bearish
                    return {'direction': 'BUY', 'score': 55, 'reason': 'Doji after bearish candle'}
            
            # Engulfing patterns
            if len(df) >= 2:
                prev_body = abs(prev['close'] - prev['open'])
                if (last['close'] > last['open'] and prev['close'] < prev['open'] and
                    last['open'] < prev['close'] and last['close'] > prev['open']):
                    return {'direction': 'BUY', 'score': 70, 'reason': 'Bullish engulfing'}
                elif (last['close'] < last['open'] and prev['close'] > prev['open'] and
                      last['open'] > prev['close'] and last['close'] < prev['open']):
                    return {'direction': 'SELL', 'score': 70, 'reason': 'Bearish engulfing'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No candlestick pattern'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'Candlestick error: {str(e)}'}
    
    def fair_value_gap_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """FIXED: Simpler FVG detection"""
        try:
            if len(df) < 5:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Need at least 5 candles for FVG'}
            
            current_price = df['close'].iloc[-1]
            
            # Look for gaps in recent candles
            for i in range(len(df)-5, len(df)-2):
                if i < 0:
                    continue
                    
                candle1 = df.iloc[i]
                candle2 = df.iloc[i+1] 
                candle3 = df.iloc[i+2]
                
                # Bullish FVG: gap between candle1 high and candle3 low
                if candle1['high'] < candle3['low']:
                    gap_high = candle3['low']
                    gap_low = candle1['high']
                    
                    # Price returning to gap
                    if gap_low <= current_price <= gap_high:
                        return {'direction': 'BUY', 'score': 75, 'reason': 'Price in bullish FVG'}
                
                # Bearish FVG: gap between candle1 low and candle3 high
                if candle1['low'] > candle3['high']:
                    gap_high = candle1['low']
                    gap_low = candle3['high']
                    
                    # Price returning to gap
                    if gap_low <= current_price <= gap_high:
                        return {'direction': 'SELL', 'score': 75, 'reason': 'Price in bearish FVG'}
            
            # Alternative: Look for imbalances (simpler)
            last_3 = df.iloc[-3:]
            
            # Price gap up
            if (last_3['low'].iloc[-1] > last_3['high'].iloc[0] and
                last_3['close'].iloc[-1] > last_3['close'].iloc[0]):
                return {'direction': 'BUY', 'score': 60, 'reason': 'Bullish gap/imbalance'}
            
            # Price gap down
            if (last_3['high'].iloc[-1] < last_3['low'].iloc[0] and
                last_3['close'].iloc[-1] < last_3['close'].iloc[0]):
                return {'direction': 'SELL', 'score': 60, 'reason': 'Bearish gap/imbalance'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No FVG detected'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'FVG error: {str(e)}'}
    
    def support_resistance_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """WORKING: Keep the original that works"""
        try:
            if len(df) < 50:
                return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'Insufficient data for S/R'}
            
            levels = []
            for i in range(10, len(df)-10, 5):
                window = df.iloc[i-10:i+10]
                if df.iloc[i]['high'] == window['high'].max():
                    levels.append(('resistance', df.iloc[i]['high']))
                if df.iloc[i]['low'] == window['low'].min():
                    levels.append(('support', df.iloc[i]['low']))
            
            current = df.iloc[-1]['close']
            for level_type, level in levels[-5:]:
                if level_type == 'support' and abs(current - level) / level < 0.002:
                    return {'direction': 'BUY', 'score': 70, 'reason': f'Bounce from support at {level:.2f}'}
                elif level_type == 'resistance' and abs(current - level) / level < 0.002:
                    return {'direction': 'SELL', 'score': 70, 'reason': f'Rejection from resistance at {level:.2f}'}
            
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No S/R level interaction'}
            
        except Exception as e:
            return {'direction': 'NEUTRAL', 'score': 0, 'reason': f'S/R error: {str(e)}'}

# Replace the original StrategyEngine
StrategyEngine = FixedStrategyEngine