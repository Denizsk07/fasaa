"""Signal Generator Module"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

from config import config
from trading.data_manager import DataManager
from trading.strategies import StrategyEngine
from trading.risk_manager import RiskManager
from analysis.technical_indicators import TechnicalAnalysis

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.data_manager = DataManager()
        self.strategy_engine = StrategyEngine()
        self.risk_manager = RiskManager()
        self.tech_analysis = TechnicalAnalysis()
        self.load_weights()
        
    def load_weights(self):
        try:
            with open(config.WEIGHTS_FILE, 'r') as f:
                self.weights = json.load(f)
        except:
            self.weights = config.STRATEGY_WEIGHTS
            
    async def generate_signal(self) -> Optional[Dict[str, Any]]:
        try:
            best_signal = None
            best_score = 0
            
            for timeframe in config.TIMEFRAMES:
                df = self.data_manager.get_data(timeframe, 500)
                if df is None:
                    continue
                
                df = self.tech_analysis.add_indicators(df)
                strategy_results = self.strategy_engine.analyze(df)
                signal = self.evaluate_signals(strategy_results, df, timeframe)
                
                if signal and signal['score'] > best_score:
                    best_signal = signal
                    best_score = signal['score']
            
            if best_signal and best_score >= config.MIN_SIGNAL_SCORE:
                best_signal = self.risk_manager.calculate_risk_parameters(best_signal)
                best_signal['timestamp'] = datetime.now().isoformat()
                return best_signal
                
            return None
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return None
    
    def evaluate_signals(self, results: Dict, df: pd.DataFrame, timeframe: str) -> Optional[Dict]:
        buy_score = 0
        sell_score = 0
        reasons = []
        
        for strategy, result in results.items():
            weight = self.weights.get(strategy, 0.1)
            if result['direction'] == 'BUY':
                buy_score += result['score'] * weight
                reasons.append(f"{strategy}: {result['reason']}")
            elif result['direction'] == 'SELL':
                sell_score += result['score'] * weight
                reasons.append(f"{strategy}: {result['reason']}")
        
        current_price = df['close'].iloc[-1]
        
        if buy_score > sell_score and buy_score >= config.MIN_SIGNAL_SCORE:
            return {
                'direction': 'BUY',
                'entry': current_price,
                'score': buy_score,
                'timeframe': f"M{timeframe}",
                'reasons': reasons[:3],
                'strategies_triggered': len([r for r in results.values() if r['direction'] == 'BUY'])
            }
        elif sell_score > buy_score and sell_score >= config.MIN_SIGNAL_SCORE:
            return {
                'direction': 'SELL',
                'entry': current_price,
                'score': sell_score,
                'timeframe': f"M{timeframe}",
                'reasons': reasons[:3],
                'strategies_triggered': len([r for r in results.values() if r['direction'] == 'SELL'])
            }
        
        return None
