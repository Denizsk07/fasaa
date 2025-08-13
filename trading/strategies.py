"""Trading Strategies Module"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)

class StrategyEngine:
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
        
    def analyze(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, strategy in self.strategies.items():
            try:
                signal = strategy(df)
                results[name] = signal
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
                results[name] = {'direction': 'NEUTRAL', 'score': 0, 'reason': str(e)}
        return results
    
    def bollinger_bands_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        last = df.iloc[-1]
        prev = df.iloc[-2]
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        bb_width = last['bb_upper'] - last['bb_lower']
        bb_width_avg = (df['bb_upper'] - df['bb_lower']).rolling(20).mean().iloc[-1]
        if bb_width < bb_width_avg * 0.7:
            if last['close'] > last['bb_upper']:
                signal = {'direction': 'BUY', 'score': 85, 'reason': 'Bollinger squeeze breakout upward'}
            elif last['close'] < last['bb_lower']:
                signal = {'direction': 'SELL', 'score': 85, 'reason': 'Bollinger squeeze breakout downward'}
        elif prev['close'] < prev['bb_lower'] and last['close'] > last['bb_lower']:
            signal = {'direction': 'BUY', 'score': 70, 'reason': 'Bounce from lower Bollinger Band'}
        elif prev['close'] > prev['bb_upper'] and last['close'] < last['bb_upper']:
            signal = {'direction': 'SELL', 'score': 70, 'reason': 'Rejection from upper Bollinger Band'}
        return signal
    
    def volume_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        last = df.iloc[-1]
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        if last['volume_ratio'] > 2.0:
            price_change = (last['close'] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            if price_change > 0.002:
                signal = {'direction': 'BUY', 'score': 75, 'reason': 'High volume bullish breakout'}
            elif price_change < -0.002:
                signal = {'direction': 'SELL', 'score': 75, 'reason': 'High volume bearish breakout'}
        return signal
    
    def price_action_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        if len(df) > 20:
            recent_high = df['high'].rolling(20).max().iloc[-1]
            recent_low = df['low'].rolling(20).min().iloc[-1]
            last = df.iloc[-1]
            if last['close'] > recent_high * 0.998:
                signal = {'direction': 'BUY', 'score': 70, 'reason': 'Breaking recent highs'}
            elif last['close'] < recent_low * 1.002:
                signal = {'direction': 'SELL', 'score': 70, 'reason': 'Breaking recent lows'}
        return signal
    
    def smc_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        if len(df) > 50:
            high_points = df['high'].rolling(5).max() == df['high']
            low_points = df['low'].rolling(5).min() == df['low']
            swing_highs = df[high_points]['high'].dropna()
            swing_lows = df[low_points]['low'].dropna()
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                if df['close'].iloc[-1] > swing_highs.iloc[-1]:
                    signal = {'direction': 'BUY', 'score': 85, 'reason': 'Bullish Break of Structure'}
                elif df['close'].iloc[-1] < swing_lows.iloc[-1]:
                    signal = {'direction': 'SELL', 'score': 85, 'reason': 'Bearish Break of Structure'}
        return signal
    
    def pattern_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No pattern detected'}
    
    def candlestick_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        upper_wick = last['high'] - max(last['close'], last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        if lower_wick > body * 2 and upper_wick < body * 0.1:
            signal = {'direction': 'BUY', 'score': 65, 'reason': 'Hammer candlestick pattern'}
        elif upper_wick > body * 2 and lower_wick < body * 0.1:
            signal = {'direction': 'SELL', 'score': 65, 'reason': 'Shooting star pattern'}
        return signal
    
    def fair_value_gap_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        if len(df) >= 3:
            for i in range(len(df)-3, max(0, len(df)-20), -1):
                gap_up = df.iloc[i]['low'] > df.iloc[i+2]['high']
                gap_down = df.iloc[i]['high'] < df.iloc[i+2]['low']
                current = df.iloc[-1]['close']
                if gap_up and df.iloc[i]['low'] <= current <= df.iloc[i+2]['high']:
                    signal = {'direction': 'BUY', 'score': 80, 'reason': 'Price returned to bullish FVG'}
                    break
                elif gap_down and df.iloc[i+2]['low'] <= current <= df.iloc[i]['high']:
                    signal = {'direction': 'SELL', 'score': 80, 'reason': 'Price returned to bearish FVG'}
                    break
        return signal
    
    def support_resistance_strategy(self, df: pd.DataFrame) -> Dict[str, Any]:
        signal = {'direction': 'NEUTRAL', 'score': 0, 'reason': ''}
        if len(df) > 50:
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
                    signal = {'direction': 'BUY', 'score': 70, 'reason': f'Bounce from support at {level:.2f}'}
                    break
                elif level_type == 'resistance' and abs(current - level) / level < 0.002:
                    signal = {'direction': 'SELL', 'score': 70, 'reason': f'Rejection from resistance at {level:.2f}'}
                    break
        return signal
