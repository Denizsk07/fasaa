"""
Enhanced Strategy Optimizer Module
Aggressiveres Lernen für schnellere 90% Win-Rate
"""
import json
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from config import config
from learning.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class StrategyOptimizer:
    def __init__(self):
        self.tracker = PerformanceTracker()
        self.load_weights()
        self.performance_history = defaultdict(list)
        self.load_performance_history()
        
    def load_weights(self):
        try:
            with open(config.WEIGHTS_FILE, 'r') as f:
                self.weights = json.load(f)
        except:
            self.weights = config.STRATEGY_WEIGHTS
            
    def save_weights(self):
        try:
            with open(config.WEIGHTS_FILE, 'w') as f:
                json.dump(self.weights, f, indent=2)
            logger.info(f"✅ Weights saved: {self.weights}")
        except Exception as e:
            logger.error(f"Failed to save weights: {e}")
    
    def load_performance_history(self):
        """Load historical performance data"""
        try:
            with open('data/performance_history.json', 'r') as f:
                self.performance_history = json.load(f)
        except:
            self.performance_history = defaultdict(list)
    
    def save_performance_history(self):
        """Save performance history"""
        try:
            with open('data/performance_history.json', 'w') as f:
                json.dump(dict(self.performance_history), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save performance history: {e}")
            
    async def optimize(self):
        """
        ENHANCED OPTIMIZATION für 90% Win-Rate
        Aggressivere Anpassung der Strategie-Gewichte
        """
        try:
            logger.info("🧠 Starting ENHANCED optimization...")
            
            # Analyse der Performance pro Strategie
            performance_by_strategy = self.analyze_strategy_performance()
            
            # AGGRESSIVERE ANPASSUNG für schnelleres Lernen
            for strategy, perf in performance_by_strategy.items():
                win_rate = perf.get('win_rate', 50)
                trade_count = perf.get('trade_count', 0)
                avg_profit = perf.get('avg_profit', 0)
                
                # Speichere Performance Historie
                self.performance_history[strategy].append({
                    'date': datetime.now().isoformat(),
                    'win_rate': win_rate,
                    'trades': trade_count
                })
                
                # AGGRESSIVE GEWICHTSANPASSUNG
                if trade_count >= 5:  # Nur wenn genug Daten
                    
                    # SUPER PERFORMER (>80% Win-Rate)
                    if win_rate >= 80:
                        self.weights[strategy] = min(0.35, self.weights[strategy] * 1.5)
                        logger.info(f"🚀 {strategy}: SUPER PERFORMER! Weight → {self.weights[strategy]:.2f}")
                    
                    # GOOD PERFORMER (70-80% Win-Rate)
                    elif win_rate >= 70:
                        self.weights[strategy] = min(0.25, self.weights[strategy] * 1.3)
                        logger.info(f"✅ {strategy}: Good! Weight → {self.weights[strategy]:.2f}")
                    
                    # AVERAGE (60-70% Win-Rate)
                    elif win_rate >= 60:
                        self.weights[strategy] = self.weights[strategy] * 1.1
                        logger.info(f"📊 {strategy}: Average. Weight → {self.weights[strategy]:.2f}")
                    
                    # POOR PERFORMER (50-60% Win-Rate)
                    elif win_rate >= 50:
                        self.weights[strategy] = max(0.05, self.weights[strategy] * 0.8)
                        logger.info(f"⚠️ {strategy}: Below average. Weight → {self.weights[strategy]:.2f}")
                    
                    # BAD PERFORMER (<50% Win-Rate)
                    else:
                        self.weights[strategy] = max(0.02, self.weights[strategy] * 0.5)
                        logger.info(f"❌ {strategy}: Poor! Weight → {self.weights[strategy]:.2f}")
                
                # Bonus für profitable Strategien
                if avg_profit > 50:  # Mehr als 50 Pips Durchschnittsgewinn
                    self.weights[strategy] *= 1.2
                    logger.info(f"💰 {strategy}: Profit bonus applied!")
            
            # Normalisiere Gewichte (Summe = 1.0)
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: v/total for k, v in self.weights.items()}
            
            # Finde beste und schlechteste Strategie
            best_strategy = max(self.weights.items(), key=lambda x: x[1])
            worst_strategy = min(self.weights.items(), key=lambda x: x[1])
            
            logger.info(f"🏆 Best Strategy: {best_strategy[0]} ({best_strategy[1]:.2%})")
            logger.info(f"😞 Worst Strategy: {worst_strategy[0]} ({worst_strategy[1]:.2%})")
            
            # Speichere alles
            self.save_weights()
            self.save_performance_history()
            
            # Adaptive Parameter anpassen
            await self.optimize_risk_parameters()
            
            # Report
            overall_win_rate = self.calculate_overall_winrate()
            logger.info(f"📈 Overall Win-Rate: {overall_win_rate:.1f}%")
            
            if overall_win_rate >= 85:
                logger.info("🎯 EXCELLENT! Approaching 90% win-rate target!")
            elif overall_win_rate >= 75:
                logger.info("✅ GOOD! System is learning well.")
            elif overall_win_rate >= 65:
                logger.info("📊 IMPROVING. Need more data.")
            else:
                logger.info("📚 LEARNING PHASE. Collecting data...")
                
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
    
    def analyze_strategy_performance(self) -> Dict:
        """
        Detaillierte Analyse jeder Strategie
        """
        performance = {}
        
        # Lade alle Trades
        trades = self.tracker.trades
        
        for strategy in self.weights.keys():
            strategy_trades = [
                t for t in trades 
                if strategy in t.get('triggered_strategies', [])
            ]
            
            if strategy_trades:
                wins = [t for t in strategy_trades if t.get('pnl', 0) > 0]
                losses = [t for t in strategy_trades if t.get('pnl', 0) <= 0]
                
                win_rate = (len(wins) / len(strategy_trades)) * 100 if strategy_trades else 0
                avg_profit = np.mean([t.get('pnl', 0) for t in wins]) if wins else 0
                avg_loss = np.mean([abs(t.get('pnl', 0)) for t in losses]) if losses else 0
                
                performance[strategy] = {
                    'win_rate': win_rate,
                    'trade_count': len(strategy_trades),
                    'wins': len(wins),
                    'losses': len(losses),
                    'avg_profit': avg_profit,
                    'avg_loss': avg_loss,
                    'profit_factor': avg_profit / avg_loss if avg_loss > 0 else avg_profit
                }
            else:
                # Keine Trades für diese Strategie - Standardwerte
                performance[strategy] = {
                    'win_rate': 50,  # Neutral starten
                    'trade_count': 0,
                    'wins': 0,
                    'losses': 0,
                    'avg_profit': 0,
                    'avg_loss': 0,
                    'profit_factor': 1
                }
        
        return performance
    
    async def optimize_risk_parameters(self):
        """
        Optimiere SL/TP Abstände basierend auf Performance
        """
        try:
            # Analysiere optimale SL/TP Verhältnisse
            trades = self.tracker.trades
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            
            if len(winning_trades) >= 10:
                # Berechne durchschnittliche erfolgreiche TP Level
                tp_hits = defaultdict(int)
                for trade in winning_trades:
                    if trade.get('exit_level'):
                        tp_hits[trade['exit_level']] += 1
                
                # Passe TP Levels an
                if tp_hits:
                    most_hit = max(tp_hits, key=tp_hits.get)
                    logger.info(f"📊 Most hit TP level: {most_hit}")
                    
                    # Update config für bessere TP Levels
                    if most_hit == 'tp1':
                        # TP1 wird oft getroffen - konservativer
                        config.TP_LEVELS = [15, 30, 45, 80]
                    elif most_hit == 'tp2':
                        # Optimal
                        config.TP_LEVELS = [20, 40, 60, 100]
                    elif most_hit in ['tp3', 'tp4']:
                        # Markt läuft gut - aggressiver
                        config.TP_LEVELS = [25, 50, 75, 120]
                    
                    logger.info(f"✅ TP Levels optimized: {config.TP_LEVELS}")
                    
        except Exception as e:
            logger.error(f"Risk parameter optimization failed: {e}")
    
    def calculate_overall_winrate(self) -> float:
        """Berechne die Gesamt-Winrate"""
        trades = self.tracker.trades
        if not trades:
            return 0.0
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        if not closed_trades:
            return 0.0
            
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        return (len(wins) / len(closed_trades)) * 100
    
    async def quick_optimize(self):
        """
        Schnelle Optimierung nach jedem Trade
        Für TURBO-Learning
        """
        # Analysiere nur die letzten 20 Trades
        recent_trades = self.tracker.trades[-20:]
        
        if len(recent_trades) >= 5:
            for strategy in self.weights.keys():
                strategy_trades = [
                    t for t in recent_trades 
                    if strategy in t.get('triggered_strategies', [])
                ]
                
                if len(strategy_trades) >= 2:
                    wins = [t for t in strategy_trades if t.get('pnl', 0) > 0]
                    win_rate = (len(wins) / len(strategy_trades)) * 100
                    
                    # Schnelle Anpassung
                    if win_rate >= 75:
                        self.weights[strategy] = min(0.3, self.weights[strategy] * 1.1)
                    elif win_rate <= 25:
                        self.weights[strategy] = max(0.05, self.weights[strategy] * 0.9)
            
            # Normalisieren
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: v/total for k, v in self.weights.items()}
                self.save_weights()