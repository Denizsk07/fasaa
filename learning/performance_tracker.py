"""Performance Tracker Module"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from config import config

logger = logging.getLogger(__name__)

class PerformanceTracker:
    def __init__(self):
        self.ensure_data_files()
        self.load_data()
        
    def ensure_data_files(self):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        if not os.path.exists(config.TRADES_FILE):
            with open(config.TRADES_FILE, 'w') as f:
                json.dump([], f)
        if not os.path.exists(config.PERFORMANCE_FILE):
            with open(config.PERFORMANCE_FILE, 'w') as f:
                json.dump({}, f)
                
    def load_data(self):
        try:
            with open(config.TRADES_FILE, 'r') as f:
                self.trades = json.load(f)
            with open(config.PERFORMANCE_FILE, 'r') as f:
                self.performance = json.load(f)
        except:
            self.trades = []
            self.performance = {}
            
    def save_data(self):
        try:
            with open(config.TRADES_FILE, 'w') as f:
                json.dump(self.trades, f, indent=2)
            with open(config.PERFORMANCE_FILE, 'w') as f:
                json.dump(self.performance, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            
    def record_signal(self, signal: Dict[str, Any]):
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': signal['timestamp'],
            'direction': signal['direction'],
            'entry': signal['entry'],
            'sl': signal['sl'],
            'tp1': signal['tp1'],
            'tp2': signal['tp2'],
            'tp3': signal['tp3'],
            'tp4': signal['tp4'],
            'score': signal['score'],
            'timeframe': signal['timeframe'],
            'status': 'open',
            'pnl': None
        }
        self.trades.append(trade)
        self.save_data()
        
    def get_current_stats(self) -> Dict[str, Any]:
        if not self.trades:
            return {'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'best_strategy': 'N/A'}
        
        closed_trades = [t for t in self.trades if t.get('status') == 'closed']
        if not closed_trades:
            return {'total_trades': len(self.trades), 'win_rate': 0, 'avg_pnl': 0, 'best_strategy': 'N/A'}
        
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = (len(wins) / len(closed_trades)) * 100 if closed_trades else 0
        avg_pnl = sum(t.get('pnl', 0) for t in closed_trades) / len(closed_trades) if closed_trades else 0
        
        return {
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'best_strategy': 'SMC'
        }
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        today = datetime.now().date()
        today_trades = [t for t in self.trades if datetime.fromisoformat(t['timestamp']).date() == today]
        
        stats = self.get_current_stats()
        stats['today_trades'] = len(today_trades)
        stats['report_date'] = today.isoformat()
        
        return stats
