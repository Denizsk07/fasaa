"""Enhanced Risk Manager for XAUUSD and BTCUSD"""
import numpy as np
from typing import Dict, Any, List  # <- List hinzufügen
from config import config

class EnhancedRiskManager:
    def __init__(self):
        self.symbol_configs = {
            'XAUUSD': {
                'default_sl': 8.0,
                'tp_levels': [5.0, 10.0, 15.0, 25.0],
                'pip_value': 0.1,
                'min_distance': 2.0,
                'max_sl': 20.0
            },
            'BTCUSD': {
                'default_sl': 300.0,
                'tp_levels': [500, 1000, 1500, 2500],
                'pip_value': 1.0,
                'min_distance': 100.0,
                'max_sl': 1000.0
            }
        }
    
    def calculate_enhanced_risk_parameters(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced risk parameters based on symbol and market conditions"""
        
        entry = signal['entry']
        direction = signal['direction']
        symbol = signal.get('symbol', config.PRIMARY_SYMBOL)
        
        # Get symbol-specific configuration
        symbol_config = self.symbol_configs.get(symbol, self.symbol_configs['XAUUSD'])
        
        # Calculate dynamic stop loss based on volatility
        sl_distance = self._calculate_dynamic_sl(signal, symbol_config)
        
        # Calculate entry levels
        if direction == 'BUY':
            signal['sl'] = entry - sl_distance
            signal['tp1'] = entry + symbol_config['tp_levels'][0]
            signal['tp2'] = entry + symbol_config['tp_levels'][1]
            signal['tp3'] = entry + symbol_config['tp_levels'][2]
            signal['tp4'] = entry + symbol_config['tp_levels'][3]
        else:  # SELL
            signal['sl'] = entry + sl_distance
            signal['tp1'] = entry - symbol_config['tp_levels'][0]
            signal['tp2'] = entry - symbol_config['tp_levels'][1]
            signal['tp3'] = entry - symbol_config['tp_levels'][2]
            signal['tp4'] = entry - symbol_config['tp_levels'][3]
        
        # Enhanced risk calculations
        signal = self._add_enhanced_risk_metrics(signal, symbol_config)
        
        # Position sizing
        signal['position_size'] = self._calculate_enhanced_position_size(signal, symbol_config)
        
        # Add risk warnings
        signal['risk_warnings'] = self._generate_risk_warnings(signal, symbol_config)
        
        return signal
    
    def _calculate_dynamic_sl(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> float:
        """Calculate dynamic stop loss based on market volatility and signal strength"""
        
        base_sl = symbol_config['default_sl']
        score = signal.get('score', 75)
        
        # Adjust SL based on signal strength
        if score >= 90:
            # Very strong signal - tighter SL
            sl_multiplier = 0.8
        elif score >= 85:
            # Strong signal - slightly tighter SL
            sl_multiplier = 0.9
        elif score >= 80:
            # Good signal - normal SL
            sl_multiplier = 1.0
        elif score >= 75:
            # Moderate signal - wider SL
            sl_multiplier = 1.2
        else:
            # Weak signal - much wider SL
            sl_multiplier = 1.5
        
        # Apply volatility adjustment (would need real volatility data)
        volatility_multiplier = 1.0  # Placeholder
        
        dynamic_sl = base_sl * sl_multiplier * volatility_multiplier
        
        # Ensure within limits
        dynamic_sl = max(symbol_config['min_distance'], 
                        min(symbol_config['max_sl'], dynamic_sl))
        
        return dynamic_sl
    
    def _add_enhanced_risk_metrics(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add enhanced risk metrics to signal"""
        
        entry = signal['entry']
        sl = signal['sl']
        
        # Calculate risk metrics for each TP
        sl_distance = abs(sl - entry)
        
        risk_metrics = {}
        total_reward = 0
        
        for i, tp_key in enumerate(['tp1', 'tp2', 'tp3', 'tp4'], 1):
            if tp_key in signal:
                tp_distance = abs(signal[tp_key] - entry)
                rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
                
                risk_metrics[f'rr_{i}'] = round(rr_ratio, 2)
                total_reward += tp_distance
        
        # Overall metrics
        signal['risk_metrics'] = risk_metrics
        signal['average_rr'] = round(total_reward / (4 * sl_distance), 2) if sl_distance > 0 else 0
        signal['max_loss_usd'] = self._calculate_max_loss(signal, symbol_config)
        signal['potential_profit_usd'] = self._calculate_potential_profit(signal, symbol_config)
        
        return signal
    
    def _calculate_enhanced_position_size(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> float:
        """Calculate position size with enhanced risk management"""
        
        account_balance = 10000  # Default account size
        risk_percentage = config.RISK_PERCENTAGE / 100
        max_risk_usd = account_balance * risk_percentage
        
        sl_distance = abs(signal['sl'] - signal['entry'])
        symbol = signal.get('symbol', config.PRIMARY_SYMBOL)
        
        if symbol == 'BTCUSD':
            # For Bitcoin: Calculate in BTC units
            risk_per_unit = sl_distance  # USD per BTC
            position_size = max_risk_usd / risk_per_unit
            
            # Limit to reasonable BTC amounts
            position_size = min(position_size, 0.1)  # Max 0.1 BTC
            return round(position_size, 6)
            
        elif symbol == 'XAUUSD':
            # For Gold: Calculate in ounces
            risk_per_ounce = sl_distance  # USD per ounce
            position_size = max_risk_usd / risk_per_ounce
            
            # Convert to standard lot size (100 ounces = 1 lot)
            lots = position_size / 100
            
            # Limit to reasonable lot sizes
            lots = min(lots, 1.0)  # Max 1 lot
            return round(lots, 3)
        
        else:
            # Default calculation
            return 0.1
    
    def _calculate_max_loss(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> float:
        """Calculate maximum loss in USD"""
        
        sl_distance = abs(signal['sl'] - signal['entry'])
        position_size = signal.get('position_size', 0.1)
        symbol = signal.get('symbol', config.PRIMARY_SYMBOL)
        
        if symbol == 'BTCUSD':
            return sl_distance * position_size
        elif symbol == 'XAUUSD':
            return sl_distance * position_size * 100  # 100 oz per lot
        else:
            return sl_distance * position_size * 100
    
    def _calculate_potential_profit(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> float:
        """Calculate potential profit at TP2 in USD"""
        
        entry = signal['entry']
        tp2 = signal.get('tp2', entry)
        tp_distance = abs(tp2 - entry)
        position_size = signal.get('position_size', 0.1)
        symbol = signal.get('symbol', config.PRIMARY_SYMBOL)
        
        if symbol == 'BTCUSD':
            return tp_distance * position_size
        elif symbol == 'XAUUSD':
            return tp_distance * position_size * 100
        else:
            return tp_distance * position_size * 100
    
    def _generate_risk_warnings(self, signal: Dict[str, Any], symbol_config: Dict[str, Any]) -> List[str]:
        """Generate risk warnings based on signal analysis"""
        
        warnings = []
        score = signal.get('score', 75)
        avg_rr = signal.get('average_rr', 0)
        max_loss = signal.get('max_loss_usd', 0)
        
        # Score-based warnings
        if score < 80:
            warnings.append("⚠️ Below-average signal strength")
        
        # Risk-reward warnings
        if avg_rr < 1.5:
            warnings.append("📊 Low risk-reward ratio")
        
        # Loss amount warnings
        if max_loss > 200:  # $200 max loss warning
            warnings.append(f"💰 High risk trade: ${max_loss:.0f} max loss")
        
        # Symbol-specific warnings
        symbol = signal.get('symbol', config.PRIMARY_SYMBOL)
        if symbol == 'BTCUSD':
            warnings.append("₿ High volatility asset - use tight risk management")
        elif symbol == 'XAUUSD':
            warnings.append("🥇 Gold can gap during news events")
        
        return warnings
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol-specific information"""
        
        symbol_info = {
            'XAUUSD': {
                'name': 'Gold',
                'type': 'Precious Metal',
                'typical_spread': '0.3',
                'trading_hours': '24/5',
                'volatility': 'Medium',
                'news_sensitivity': 'High'
            },
            'BTCUSD': {
                'name': 'Bitcoin',
                'type': 'Cryptocurrency', 
                'typical_spread': '10-50',
                'trading_hours': '24/7',
                'volatility': 'Very High',
                'news_sensitivity': 'Very High'
            }
        }
        
        return symbol_info.get(symbol, {})

# Legacy compatibility
RiskManager = EnhancedRiskManager