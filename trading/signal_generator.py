"""
Enhanced Signal Generator - 1000 Candle Deep Analysis
Erweitert dein bestehendes System für tiefere Marktanalyse
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import json

from config import config
from trading.data_manager import DataManager
from trading.strategies import StrategyEngine
from trading.risk_manager import EnhancedRiskManager
from analysis.technical_indicators import TechnicalAnalysis

logger = logging.getLogger(__name__)

class Enhanced1000CandleSignalGenerator:
    """
    Enhanced Signal Generator mit 1000+ Candle Deep Analysis
    Erweitert dein bestehendes System ohne es zu ersetzen
    """
    
    def __init__(self):
        # Deine bestehenden Komponenten
        self.data_manager = DataManager()
        self.strategy_engine = StrategyEngine()
        self.risk_manager = EnhancedRiskManager()
        self.tech_analysis = TechnicalAnalysis()
        
        # Neue 1000-Candle Komponenten
        self.deep_analyzer = DeepMarketAnalyzer()
        self.pattern_detector = EnhancedPatternDetector()
        self.level_classifier = SupportResistanceLevelClassifier()
        
        self.load_weights()
        logger.info("🔥 Enhanced 1000-Candle Signal Generator initialized")
        
    def load_weights(self):
        """Load strategy weights (keeping your existing system)"""
        try:
            with open(config.WEIGHTS_FILE, 'r') as f:
                self.weights = json.load(f)
            logger.info(f"📊 Weights loaded: {self.weights}")
        except:
            self.weights = config.STRATEGY_WEIGHTS
            logger.info(f"📊 Using default weights: {self.weights}")
    
    async def generate_enhanced_signal(self) -> Optional[Dict[str, Any]]:
        """
        Enhanced Signal Generation mit 1000-Candle Deep Analysis
        """
        try:
            logger.info("🚀 Starting ENHANCED 1000-candle signal generation...")
            
            best_signal = None
            best_score = 0
            
            for timeframe in config.TIMEFRAMES:
                logger.info(f"📊 Deep analyzing timeframe: {timeframe}")
                
                # 🔥 ENHANCEMENT 1: Get 1000+ candles instead of 500
                df_deep = self.data_manager.get_data(timeframe, 1200)  # Extra buffer
                if df_deep is None or len(df_deep) < 200:
                    logger.warning(f"❌ Insufficient data for {timeframe} deep analysis")
                    continue
                
                logger.info(f"✅ Got {len(df_deep)} candles for deep analysis")
                
                # 🔥 ENHANCEMENT 2: Multi-layer analysis
                analysis_result = await self._perform_deep_analysis(df_deep, timeframe)
                
                if analysis_result and analysis_result['score'] > best_score:
                    best_signal = analysis_result
                    best_score = analysis_result['score']
                    logger.info(f"🎯 New best deep signal: {analysis_result['direction']} score {best_score:.1f}")
            
            if best_signal and best_score >= config.MIN_SIGNAL_SCORE:
                logger.info(f"✅ Enhanced signal passes threshold: {best_score:.1f}")
                
                # Enhanced risk management
                best_signal = self.risk_manager.calculate_enhanced_risk_parameters(best_signal)
                best_signal['timestamp'] = datetime.now().isoformat()
                best_signal['analysis_depth'] = '1000_candle_deep'
                
                logger.info(f"🎯 FINAL ENHANCED SIGNAL: {best_signal['direction']} @ ${best_signal['entry']:.2f}")
                return best_signal
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Enhanced signal generation failed: {e}")
            return None
    
    async def _perform_deep_analysis(self, df: pd.DataFrame, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Deep Multi-Layer Analysis auf 1000+ Kerzen
        """
        logger.info(f"🔍 Performing deep analysis on {len(df)} candles...")
        
        # Layer 1: Deine bestehenden Strategien (erweitert)
        df = self.tech_analysis.add_indicators(df)
        strategy_results = self.strategy_engine.analyze(df)
        
        # Layer 2: 🔥 NEW - Deep Support/Resistance Analysis
        deep_sr_levels = self.level_classifier.find_major_levels(df)
        
        # Layer 3: 🔥 NEW - Long-term Pattern Detection  
        patterns = self.pattern_detector.detect_major_patterns(df)
        
        # Layer 4: 🔥 NEW - Volume Profile Analysis
        volume_analysis = self.deep_analyzer.analyze_volume_profile(df)
        
        # Layer 5: 🔥 NEW - Multi-timeframe Context
        htf_context = await self._get_higher_timeframe_context(timeframe)
        
        # Combine all analyses
        enhanced_signal = self._synthesize_deep_analysis(
            strategy_results, deep_sr_levels, patterns, 
            volume_analysis, htf_context, df, timeframe
        )
        
        return enhanced_signal
    
    def _synthesize_deep_analysis(self, strategy_results, sr_levels, patterns, 
                                volume_analysis, htf_context, df, timeframe) -> Optional[Dict[str, Any]]:
        """
        Synthesize alle Analysen zu einem Enhanced Signal
        """
        logger.info(f"🧠 Synthesizing deep analysis results...")
        
        current_price = df['close'].iloc[-1]
        
        # Initialize scoring
        buy_score = 0
        sell_score = 0
        enhanced_reasons = []
        
        # 1. Deine bestehenden Strategien (mit Gewichtung)
        for strategy, result in strategy_results.items():
            weight = self.weights.get(strategy, 0.1)
            direction = result.get('direction', 'NEUTRAL')
            score = result.get('score', 0)
            
            if direction == 'BUY':
                buy_score += score * weight
            elif direction == 'SELL':
                sell_score += score * weight
        
        # 2. 🔥 Support/Resistance Level Analysis (MAJOR ENHANCEMENT)
        sr_signal = self._analyze_sr_interaction(current_price, sr_levels)
        if sr_signal['direction'] == 'BUY':
            buy_score += sr_signal['score']
            enhanced_reasons.append(f"Major S/R: {sr_signal['reason']}")
        elif sr_signal['direction'] == 'SELL':
            sell_score += sr_signal['score']
            enhanced_reasons.append(f"Major S/R: {sr_signal['reason']}")
        
        # 3. 🔥 Pattern Confirmation
        for pattern in patterns:
            if pattern['direction'] == 'BUY' and pattern['confidence'] > 0.7:
                buy_score += pattern['score']
                enhanced_reasons.append(f"Pattern: {pattern['name']}")
            elif pattern['direction'] == 'SELL' and pattern['confidence'] > 0.7:
                sell_score += pattern['score']
                enhanced_reasons.append(f"Pattern: {pattern['name']}")
        
        # 4. 🔥 Volume Profile Confirmation
        if volume_analysis['bias'] == 'BUY' and volume_analysis['strength'] > 0.6:
            buy_score += volume_analysis['score']
            enhanced_reasons.append(f"Volume: {volume_analysis['reason']}")
        elif volume_analysis['bias'] == 'SELL' and volume_analysis['strength'] > 0.6:
            sell_score += volume_analysis['score']
            enhanced_reasons.append(f"Volume: {volume_analysis['reason']}")
        
        # 5. 🔥 Higher Timeframe Bias
        if htf_context['bias'] == 'BUY':
            buy_score *= htf_context['multiplier']
            enhanced_reasons.append(f"HTF Bias: {htf_context['reason']}")
        elif htf_context['bias'] == 'SELL':
            sell_score *= htf_context['multiplier']
            enhanced_reasons.append(f"HTF Bias: {htf_context['reason']}")
        
        # Final signal evaluation
        logger.info(f"📊 DEEP ANALYSIS SCORES: BUY={buy_score:.1f}, SELL={sell_score:.1f}")
        
        if buy_score > sell_score and buy_score >= config.MIN_SIGNAL_SCORE:
            return {
                'direction': 'BUY',
                'entry': current_price,
                'score': buy_score,
                'timeframe': f"M{timeframe}",
                'reasons': enhanced_reasons[:5],  # Top 5 reasons
                'deep_analysis': True,
                'candles_analyzed': len(df),
                'major_levels': len([l for l in sr_levels if l['strength'] == 'major']),
                'patterns_detected': len(patterns),
                'symbol': config.PRIMARY_SYMBOL,
                'analysis_layers': 5
            }
        elif sell_score > buy_score and sell_score >= config.MIN_SIGNAL_SCORE:
            return {
                'direction': 'SELL', 
                'entry': current_price,
                'score': sell_score,
                'timeframe': f"M{timeframe}",
                'reasons': enhanced_reasons[:5],
                'deep_analysis': True,
                'candles_analyzed': len(df),
                'major_levels': len([l for l in sr_levels if l['strength'] == 'major']),
                'patterns_detected': len(patterns),
                'symbol': config.PRIMARY_SYMBOL,
                'analysis_layers': 5
            }
        
        return None
    
    def _analyze_sr_interaction(self, current_price: float, sr_levels: List[Dict]) -> Dict[str, Any]:
        """
        Analyze current price interaction with major S/R levels
        """
        tolerance = current_price * 0.002  # 0.2% tolerance
        
        for level in sr_levels:
            price_level = level['price']
            level_type = level['type']  # 'support' or 'resistance'
            strength = level['strength']  # 'major', 'minor', 'intermediate'
            
            if abs(current_price - price_level) <= tolerance:
                if level_type == 'support' and strength in ['major', 'intermediate']:
                    score = 25 if strength == 'major' else 15
                    return {
                        'direction': 'BUY',
                        'score': score,
                        'reason': f'{strength} support at {price_level:.2f}'
                    }
                elif level_type == 'resistance' and strength in ['major', 'intermediate']:
                    score = 25 if strength == 'major' else 15
                    return {
                        'direction': 'SELL',
                        'score': score,
                        'reason': f'{strength} resistance at {price_level:.2f}'
                    }
        
        return {'direction': 'NEUTRAL', 'score': 0, 'reason': 'No S/R interaction'}
    
    async def _get_higher_timeframe_context(self, current_timeframe: str) -> Dict[str, Any]:
        """
        Get higher timeframe context for bias
        """
        htf_map = {'15': '60', '30': '240', '60': '1440'}
        htf = htf_map.get(current_timeframe, '240')
        
        try:
            df_htf = self.data_manager.get_data(htf, 200)
            if df_htf is None or len(df_htf) < 50:
                return {'bias': 'NEUTRAL', 'multiplier': 1.0, 'reason': 'No HTF data'}
            
            # Simple HTF trend analysis
            df_htf = self.tech_analysis.add_indicators(df_htf)
            
            current_price = df_htf['close'].iloc[-1]
            ema_20 = df_htf['ema_20'].iloc[-1] if 'ema_20' in df_htf.columns else current_price
            ema_50 = df_htf['ema_50'].iloc[-1] if 'ema_50' in df_htf.columns else current_price
            
            if current_price > ema_20 > ema_50:
                return {'bias': 'BUY', 'multiplier': 1.3, 'reason': f'{htf}min uptrend'}
            elif current_price < ema_20 < ema_50:
                return {'bias': 'SELL', 'multiplier': 1.3, 'reason': f'{htf}min downtrend'}
            else:
                return {'bias': 'NEUTRAL', 'multiplier': 1.0, 'reason': f'{htf}min sideways'}
                
        except Exception as e:
            logger.debug(f"HTF analysis failed: {e}")
            return {'bias': 'NEUTRAL', 'multiplier': 1.0, 'reason': 'HTF analysis failed'}

class DeepMarketAnalyzer:
    """Deep market analysis on 1000+ candles"""
    
    def analyze_volume_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume profile over 1000 candles"""
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            return {'bias': 'NEUTRAL', 'strength': 0, 'score': 0, 'reason': 'No volume data'}
        
        # Calculate volume-weighted average price levels
        recent_volume = df['volume'].iloc[-100:].mean()
        historical_volume = df['volume'].iloc[:-100].mean() if len(df) > 100 else recent_volume
        
        volume_ratio = recent_volume / historical_volume if historical_volume > 0 else 1
        
        # Price analysis with volume
        recent_close = df['close'].iloc[-1]
        recent_high = df['high'].iloc[-20:].max()
        recent_low = df['low'].iloc[-20:].min()
        
        if volume_ratio > 1.3:  # High volume
            if recent_close > (recent_high + recent_low) / 2:
                return {'bias': 'BUY', 'strength': 0.8, 'score': 15, 'reason': 'High volume bullish bias'}
            else:
                return {'bias': 'SELL', 'strength': 0.8, 'score': 15, 'reason': 'High volume bearish bias'}
        
        return {'bias': 'NEUTRAL', 'strength': 0.3, 'score': 0, 'reason': 'Normal volume'}

class EnhancedPatternDetector:
    """Enhanced pattern detection over 1000 candles"""
    
    def detect_major_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect major chart patterns over 1000 candles"""
        patterns = []
        
        # Triangle pattern detection
        triangle = self._detect_triangle_pattern(df)
        if triangle:
            patterns.append(triangle)
        
        # Channel pattern detection  
        channel = self._detect_channel_pattern(df)
        if channel:
            patterns.append(channel)
        
        # Head and shoulders detection
        h_and_s = self._detect_head_shoulders(df)
        if h_and_s:
            patterns.append(h_and_s)
        
        return patterns
    
    def _detect_triangle_pattern(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect triangle patterns"""
        if len(df) < 100:
            return None
        
        # Simple triangle detection based on converging highs and lows
        recent_100 = df.iloc[-100:]
        
        # Find swing highs and lows
        highs = []
        lows = []
        
        for i in range(10, len(recent_100) - 10):
            if recent_100['high'].iloc[i] == recent_100['high'].iloc[i-10:i+11].max():
                highs.append((i, recent_100['high'].iloc[i]))
            if recent_100['low'].iloc[i] == recent_100['low'].iloc[i-10:i+11].min():
                lows.append((i, recent_100['low'].iloc[i]))
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Check if highs are descending and lows are ascending (symmetrical triangle)
            high_trend = np.polyfit([h[0] for h in highs], [h[1] for h in highs], 1)[0]
            low_trend = np.polyfit([l[0] for l in lows], [l[1] for l in lows], 1)[0]
            
            if high_trend < 0 and low_trend > 0:  # Converging
                return {
                    'name': 'Symmetrical Triangle',
                    'direction': 'BUY',  # Breakout direction to be determined
                    'confidence': 0.7,
                    'score': 20
                }
        
        return None
    
    def _detect_channel_pattern(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect channel patterns"""
        if len(df) < 200:
            return None
        
        # Simple channel detection - parallel highs and lows
        recent_200 = df.iloc[-200:]
        
        # Linear regression on highs and lows
        from scipy import stats
        
        try:
            high_indices = np.arange(len(recent_200))
            low_indices = np.arange(len(recent_200))
            
            high_slope, _, high_r, _, _ = stats.linregress(high_indices, recent_200['high'])
            low_slope, _, low_r, _, _ = stats.linregress(low_indices, recent_200['low'])
            
            # Check if slopes are similar (parallel channel)
            if abs(high_slope - low_slope) < 0.1 and high_r > 0.3 and low_r > 0.3:
                direction = 'BUY' if high_slope > 0 else 'SELL'
                return {
                    'name': f'{"Ascending" if high_slope > 0 else "Descending"} Channel',
                    'direction': direction,
                    'confidence': min(high_r, low_r),
                    'score': 18
                }
        except:
            pass
        
        return None
    
    def _detect_head_shoulders(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Detect head and shoulders pattern"""
        # Simplified H&S detection
        if len(df) < 150:
            return None
        
        recent_150 = df.iloc[-150:]
        
        # Find three major peaks
        peaks = []
        for i in range(20, len(recent_150) - 20):
            if recent_150['high'].iloc[i] == recent_150['high'].iloc[i-20:i+21].max():
                peaks.append((i, recent_150['high'].iloc[i]))
        
        if len(peaks) >= 3:
            # Sort peaks by height
            peaks_sorted = sorted(peaks[-3:], key=lambda x: x[1])
            
            # Check if middle peak is highest (head)
            if peaks_sorted[-1][0] > peaks_sorted[0][0] and peaks_sorted[-1][0] < peaks_sorted[1][0]:
                return {
                    'name': 'Head and Shoulders',
                    'direction': 'SELL',
                    'confidence': 0.6,
                    'score': 22
                }
        
        return None

class SupportResistanceLevelClassifier:
    """Enhanced S/R level detection and classification"""
    
    def find_major_levels(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find and classify major S/R levels over 1000 candles"""
        levels = []
        
        # Multi-period level detection
        periods = [50, 100, 200, 500, 1000]
        
        for period in periods:
            if len(df) >= period:
                period_levels = self._find_levels_in_period(df, period)
                levels.extend(period_levels)
        
        # Remove duplicates and classify
        levels = self._classify_and_filter_levels(levels, df['close'].iloc[-1])
        
        return levels
    
    def _find_levels_in_period(self, df: pd.DataFrame, period: int) -> List[Dict[str, Any]]:
        """Find S/R levels in specific period"""
        levels = []
        recent_data = df.iloc[-period:] if len(df) >= period else df
        
        window_size = max(10, period // 50)  # Adaptive window
        
        for i in range(window_size, len(recent_data) - window_size):
            window = recent_data.iloc[i-window_size:i+window_size+1]
            current = recent_data.iloc[i]
            
            # Resistance level
            if current['high'] == window['high'].max():
                levels.append({
                    'price': current['high'],
                    'type': 'resistance',
                    'period': period,
                    'strength_raw': period / 100,  # Will be classified later
                    'touches': 1
                })
            
            # Support level
            if current['low'] == window['low'].min():
                levels.append({
                    'price': current['low'],
                    'type': 'support', 
                    'period': period,
                    'strength_raw': period / 100,
                    'touches': 1
                })
        
        return levels
    
    def _classify_and_filter_levels(self, levels: List[Dict], current_price: float) -> List[Dict[str, Any]]:
        """Classify levels by strength and remove duplicates"""
        if not levels:
            return []
        
        # Group similar levels
        tolerance = current_price * 0.005  # 0.5% tolerance
        grouped_levels = []
        
        for level in levels:
            # Find if similar level already exists
            found_group = False
            for group in grouped_levels:
                if abs(group['price'] - level['price']) <= tolerance:
                    # Merge into existing group
                    group['touches'] += 1
                    group['strength_raw'] = max(group['strength_raw'], level['strength_raw'])
                    group['period'] = max(group['period'], level['period'])
                    found_group = True
                    break
            
            if not found_group:
                grouped_levels.append(level.copy())
        
        # Classify strength based on touches and period
        for level in grouped_levels:
            touches = level['touches']
            period = level['period']
            
            # Strength classification
            if touches >= 4 and period >= 500:
                level['strength'] = 'major'
            elif touches >= 3 and period >= 200:
                level['strength'] = 'intermediate'
            else:
                level['strength'] = 'minor'
        
        # Sort by strength and return top levels
        grouped_levels.sort(key=lambda x: (
            x['touches'] * x['period'],  # Combined importance
            -abs(x['price'] - current_price)  # Proximity bonus
        ), reverse=True)
        
        return grouped_levels[:15]  # Top 15 levels

# Replace your existing SignalGenerator
SignalGenerator = Enhanced1000CandleSignalGenerator