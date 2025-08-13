"""
Enhanced Configuration for XAUUSD Trading Bot
Optimized for real XAUUSD Forex data and high win-rate trading
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime

load_dotenv()

@dataclass
class XAUUSDTradingConfig:
    """Professional XAUUSD Trading Configuration - Real Forex Data"""
    
    # Telegram Settings
    BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    GROUP_ID: str = os.getenv('TELEGRAM_GROUP_ID', '')
    
    # XAUUSD Specific Settings
    PRIMARY_SYMBOL: str = 'XAUUSD'  # The real trading symbol
    YF_SYMBOLS: List[str] = field(default_factory=lambda: [
        'XAUUSD=X',     # Yahoo Finance primary
        'XAU-USD',      # Alternative format
        'GC=F',         # Gold Futures backup
        'GOLD'          # Gold ETF backup
    ])
    
    # Real XAUUSD Trading Parameters (in USD per ounce)
    RISK_PERCENTAGE: float = float(os.getenv('RISK_PERCENTAGE', '2'))
    MIN_SIGNAL_SCORE: float = float(os.getenv('MIN_SIGNAL_SCORE', '78'))  # Higher threshold for quality
    
    # XAUUSD Optimized Timeframes
    TIMEFRAMES: List[str] = field(default_factory=lambda: ['15', '30', '60'])
    
    # XAUUSD Take Profit Levels (in USD per ounce)
    # Gold moves in larger increments than currency pairs
    TP_LEVELS: List[float] = field(default_factory=lambda: [5.0, 10.0, 15.0, 25.0])
    
    # Stop Loss for XAUUSD (in USD per ounce)
    STOP_LOSS: float = 8.0  # $8 stop loss is reasonable for XAUUSD
    
    # Enhanced Strategy Weights for XAUUSD
    STRATEGY_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        'smc': 0.25,              # Smart Money Concepts - sehr wichtig bei Gold
        'support_resistance': 0.20, # S/R Levels - Gold respektiert diese stark
        'price_action': 0.15,     # Price Action Patterns
        'bollinger': 0.12,        # Bollinger Bands
        'fvg': 0.10,             # Fair Value Gaps
        'patterns': 0.08,         # Chart Patterns
        'volume': 0.05,          # Volume (weniger wichtig bei XAUUSD)
        'candlesticks': 0.05     # Candlestick Patterns
    })
    
    # XAUUSD Market Hours (Gold trades almost 24/5)
    MARKET_HOURS: Dict[str, str] = field(default_factory=lambda: {
        'monday_open': '22:00',     # Sunday 22:00 UTC
        'friday_close': '21:00',    # Friday 21:00 UTC
        'timezone': 'UTC'
    })
    
    # Data Quality Settings
    DATA_VALIDATION: Dict[str, float] = field(default_factory=lambda: {
        'min_price': 1600.0,      # Minimum realistic XAUUSD price
        'max_price': 3000.0,      # Maximum realistic XAUUSD price
        'max_volatility': 0.05,   # 5% max volatility per period
        'min_bars': 20            # Minimum bars for analysis
    })
    
    # Professional Directory Structure
    DATA_DIR: str = 'data'
    CHARTS_DIR: str = 'charts'
    LOGS_DIR: str = 'logs'
    
    # Asset Configuration
    ASSET_TYPE: str = 'FOREX'
    SYMBOL_NAME: str = 'XAUUSD'
    ASSET_CLASS: str = 'PRECIOUS_METALS'
    
    # Enhanced Learning Parameters
    LEARNING_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'quick_learn_threshold': 5,    # Learn after every 5 trades
        'deep_learn_hours': 6,         # Deep learning every 6 hours
        'target_winrate': 90.0,        # Target win rate
        'min_trades_for_optimization': 10,  # Minimum trades before optimization
        'weight_adjustment_factor': 0.15     # How aggressively to adjust weights
    })
    
    # Risk Management for XAUUSD
    RISK_CONFIG: Dict[str, float] = field(default_factory=lambda: {
        'max_risk_per_trade': 2.0,     # 2% per trade
        'max_daily_risk': 6.0,         # 6% per day
        'max_open_positions': 3,       # Maximum concurrent positions
        'trailing_stop': 5.0,          # $5 trailing stop
        'break_even_distance': 10.0    # Move SL to BE after $10 profit
    })
    
    # Technical Analysis Settings for XAUUSD
    TECHNICAL_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'ema_periods': [20, 50, 200],
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bollinger_period': 20,
        'bollinger_std': 2.0,
        'atr_period': 14,
        'stoch_k': 14,
        'stoch_d': 3
    })
    
    # Data Source Priorities (higher number = higher priority)
    DATA_SOURCE_PRIORITY: Dict[str, int] = field(default_factory=lambda: {
        'XAUUSD=X': 100,      # Yahoo Finance XAUUSD - highest priority
        'XAU-USD': 90,        # Alternative Yahoo format
        'GC=F': 70,           # Gold Futures - good backup
        'GOLD': 60,           # Gold ETF - lower priority
        'IAU': 50             # Another Gold ETF
    })
    
    # API Configuration for alternative data sources
    API_CONFIG: Dict[str, str] = field(default_factory=lambda: {
        'fcsapi_key': os.getenv('FCSAPI_KEY', ''),
        'currencylayer_key': os.getenv('CURRENCYLAYER_KEY', ''),
        'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY', ''),
        'twelve_data_key': os.getenv('TWELVE_DATA_KEY', '')
    })
    
    # Performance Monitoring
    PERFORMANCE_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'track_slippage': True,
        'track_execution_time': True,
        'benchmark_symbol': 'GC=F',
        'performance_window': 30,  # Days to track performance
        'daily_report_time': '22:00',
        'weekly_report_day': 'sunday'
    })
    
    def __post_init__(self):
        """Initialize professional file paths and validate settings"""
        # Ensure directories exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.CHARTS_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        
        # Enhanced file paths
        self.TRADES_FILE = os.path.join(self.DATA_DIR, 'xauusd_trades.json')
        self.PERFORMANCE_FILE = os.path.join(self.DATA_DIR, 'xauusd_performance.json')
        self.WEIGHTS_FILE = os.path.join(self.DATA_DIR, 'xauusd_strategy_weights.json')
        self.HEALTH_FILE = os.path.join(self.DATA_DIR, 'data_source_health.json')
        self.OPTIMIZATION_LOG = os.path.join(self.LOGS_DIR, 'optimization.log')
        
        # Validate critical settings
        self._validate_config()
        
        # Log configuration
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"💰 XAUUSD Trading Bot Configuration Loaded")
        logger.info(f"🎯 Target: {self.LEARNING_CONFIG['target_winrate']}% win rate")
        logger.info(f"📊 Primary Symbol: {self.PRIMARY_SYMBOL}")
        logger.info(f"⚖️ Risk per trade: {self.RISK_PERCENTAGE}%")
        logger.info(f"🔄 Learning: Every {self.LEARNING_CONFIG['quick_learn_threshold']} trades")
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Validate risk settings
        if self.RISK_PERCENTAGE > 5.0:
            raise ValueError("Risk percentage too high! Maximum 5% recommended.")
        
        if self.MIN_SIGNAL_SCORE < 50 or self.MIN_SIGNAL_SCORE > 100:
            raise ValueError("Signal score must be between 50-100")
        
        # Validate strategy weights sum to 1.0
        total_weight = sum(self.STRATEGY_WEIGHTS.values())
        if abs(total_weight - 1.0) > 0.01:
            # Auto-normalize weights
            self.STRATEGY_WEIGHTS = {
                k: v/total_weight for k, v in self.STRATEGY_WEIGHTS.items()
            }
        
        # Validate price ranges
        if (self.DATA_VALIDATION['min_price'] >= self.DATA_VALIDATION['max_price']):
            raise ValueError("Invalid price validation range")
        
        # Validate TP levels are ascending
        if not all(self.TP_LEVELS[i] <= self.TP_LEVELS[i+1] for i in range(len(self.TP_LEVELS)-1)):
            raise ValueError("TP levels must be in ascending order")
    
    def get_data_source_config(self) -> Dict[str, Any]:
        """Get optimized data source configuration"""
        return {
            'primary_symbols': self.YF_SYMBOLS,
            'priorities': self.DATA_SOURCE_PRIORITY,
            'validation': self.DATA_VALIDATION,
            'fallback_enabled': True,
            'cache_duration_minutes': 1,
            'max_retries': 3,
            'timeout_seconds': 10
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get complete risk management configuration"""
        return {
            **self.RISK_CONFIG,
            'stop_loss_usd': self.STOP_LOSS,
            'tp_levels_usd': self.TP_LEVELS,
            'risk_percentage': self.RISK_PERCENTAGE
        }
    
    def get_learning_config(self) -> Dict[str, Any]:
        """Get machine learning configuration"""
        return {
            **self.LEARNING_CONFIG,
            'strategy_weights': self.STRATEGY_WEIGHTS.copy(),
            'min_signal_score': self.MIN_SIGNAL_SCORE
        }
    
    def update_strategy_weights(self, new_weights: Dict[str, float]):
        """Update strategy weights with validation"""
        # Validate weights
        if not isinstance(new_weights, dict):
            raise ValueError("Weights must be a dictionary")
        
        # Check all required strategies are present
        required_strategies = set(self.STRATEGY_WEIGHTS.keys())
        provided_strategies = set(new_weights.keys())
        
        if required_strategies != provided_strategies:
            missing = required_strategies - provided_strategies
            extra = provided_strategies - required_strategies
            raise ValueError(f"Strategy mismatch. Missing: {missing}, Extra: {extra}")
        
        # Normalize weights to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v/total for k, v in new_weights.items()}
        
        # Update weights
        self.STRATEGY_WEIGHTS = new_weights
        
        # Log the update
        import logging
        logger = logging.getLogger(__name__)
        logger.info("🔄 Strategy weights updated:")
        for strategy, weight in sorted(new_weights.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {strategy}: {weight:.3f} ({weight*100:.1f}%)")
    
    def is_market_open(self) -> bool:
        """Check if XAUUSD market is currently open"""
        from datetime import datetime, time
        import pytz
        
        try:
            # XAUUSD trades almost 24/5 (closes Friday 21:00 UTC to Sunday 22:00 UTC)
            utc_now = datetime.now(pytz.UTC)
            
            # Friday 21:00 UTC to Sunday 22:00 UTC is closed
            if utc_now.weekday() == 4:  # Friday
                if utc_now.time() >= time(21, 0):  # After 21:00
                    return False
            elif utc_now.weekday() == 5:  # Saturday
                return False
            elif utc_now.weekday() == 6:  # Sunday
                if utc_now.time() < time(22, 0):  # Before 22:00
                    return False
            
            return True
            
        except Exception:
            # If we can't determine, assume market is open
            return True
    
    def get_current_session(self) -> str:
        """Get current trading session for XAUUSD"""
        from datetime import datetime
        import pytz
        
        try:
            utc_now = datetime.now(pytz.UTC)
            hour = utc_now.hour
            
            # XAUUSD session times (approximate)
            if 22 <= hour or hour < 8:
                return "ASIAN"
            elif 8 <= hour < 15:
                return "LONDON"
            elif 15 <= hour < 22:
                return "NEW_YORK"
            else:
                return "UNKNOWN"
                
        except Exception:
            return "UNKNOWN"
    
    def get_optimal_timeframes_for_session(self) -> List[str]:
        """Get optimal timeframes based on current session"""
        session = self.get_current_session()
        
        # Optimize timeframes based on session volatility
        if session == "LONDON":
            return ['15', '30', '60']  # High volatility - all timeframes
        elif session == "NEW_YORK":
            return ['15', '30']        # Medium volatility - shorter timeframes
        elif session == "ASIAN":
            return ['30', '60']        # Lower volatility - longer timeframes
        else:
            return self.TIMEFRAMES       # Default
    
    def export_config(self) -> Dict[str, Any]:
        """Export complete configuration for backup/analysis"""
        return {
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'symbol': self.PRIMARY_SYMBOL,
            'asset_type': self.ASSET_TYPE,
            'strategy_weights': self.STRATEGY_WEIGHTS,
            'risk_config': self.get_risk_config(),
            'learning_config': self.get_learning_config(),
            'technical_config': self.TECHNICAL_CONFIG,
            'data_validation': self.DATA_VALIDATION,
            'timeframes': self.TIMEFRAMES,
            'tp_levels': self.TP_LEVELS
        }

# Create global config instance
config = XAUUSDTradingConfig()

# Backward compatibility
TradingConfig = XAUUSDTradingConfig