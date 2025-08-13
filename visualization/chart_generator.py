"""Enhanced Chart Generator with Support/Resistance Zones"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, Any, Optional, List, Tuple
import logging

from config import config
from trading.data_manager import DataManager
from analysis.smc_analysis import SMCAnalysis

logger = logging.getLogger(__name__)

class EnhancedChartGenerator:
    def __init__(self):
        self.data_manager = DataManager()
        self.smc_analysis = SMCAnalysis()
        os.makedirs(config.CHARTS_DIR, exist_ok=True)
        
    async def generate_enhanced_signal_chart(self, signal: Dict[str, Any]) -> Optional[str]:
        try:
            timeframe = signal.get('timeframe', 'M15').replace('M', '')
            df = self.data_manager.get_data(timeframe, 150)
            
            if df is None or df.empty:
                logger.warning("No data available for chart generation")
                return None
            
            # Detect key zones
            support_resistance_zones = self._find_support_resistance_zones(df)
            order_blocks = self.smc_analysis.find_order_blocks(df)
            liquidity_zones = self.smc_analysis.find_liquidity_zones(df)
            
            # Create enhanced chart
            fig, axes = mpf.plot(
                df,
                type='candle',
                style='charles',
                title=f"{config.PRIMARY_SYMBOL} {signal['timeframe']} - {signal['direction']} Signal",
                ylabel='Price ($)',
                volume=True,
                figsize=(16, 10),
                returnfig=True,
                tight_layout=True
            )
            
            ax = axes[0]
            
            # Add Support/Resistance zones
            self._add_support_resistance_zones(ax, support_resistance_zones, len(df))
            
            # Add Order Blocks
            self._add_order_blocks(ax, order_blocks, len(df))
            
            # Add Liquidity Zones
            self._add_liquidity_zones(ax, liquidity_zones)
            
            # Add Signal Lines
            self._add_signal_lines(ax, signal)
            
            # Add Entry Arrow
            self._add_entry_arrow(ax, signal, len(df))
            
            # Add Signal Info Box
            self._add_signal_info_box(ax, signal)
            
            # Add Legend
            self._add_enhanced_legend(ax)
            
            # Save chart
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_signal_{signal['direction']}_{timestamp}.png"
            filepath = os.path.join(config.CHARTS_DIR, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            logger.info(f"Enhanced chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Enhanced chart generation failed: {e}")
            return None
    
    def _find_support_resistance_zones(self, df: pd.DataFrame) -> List[Tuple[str, float, float]]:
        """Find key support and resistance zones"""
        zones = []
        
        # Find swing highs and lows
        for i in range(20, len(df)-20):
            window = df.iloc[i-20:i+21]
            current_price = df.iloc[i]
            
            # Resistance: High point
            if current_price['high'] == window['high'].max():
                # Find zone thickness
                nearby_highs = window[window['high'] >= current_price['high'] * 0.999]['high']
                zone_top = nearby_highs.max()
                zone_bottom = nearby_highs.min()
                zones.append(('resistance', zone_top, zone_bottom))
            
            # Support: Low point  
            if current_price['low'] == window['low'].min():
                nearby_lows = window[window['low'] <= current_price['low'] * 1.001]['low']
                zone_top = nearby_lows.max()
                zone_bottom = nearby_lows.min()
                zones.append(('support', zone_top, zone_bottom))
        
        # Remove duplicates and keep strongest zones
        return self._filter_strongest_zones(zones)[-8:]  # Top 8 zones
    
    def _filter_strongest_zones(self, zones: List[Tuple[str, float, float]]) -> List[Tuple[str, float, float]]:
        """Filter to strongest zones"""
        if not zones:
            return []
        
        # Sort by zone relevance (wider zones = stronger)
        zones_with_strength = []
        for zone_type, top, bottom in zones:
            strength = abs(top - bottom)  # Zone thickness
            zones_with_strength.append((strength, zone_type, top, bottom))
        
        # Sort by strength and return unique zones
        zones_with_strength.sort(reverse=True)
        unique_zones = []
        
        for strength, zone_type, top, bottom in zones_with_strength:
            # Check if zone overlaps with existing
            overlaps = False
            avg_price = (top + bottom) / 2
            
            for _, existing_top, existing_bottom in unique_zones:
                existing_avg = (existing_top + existing_bottom) / 2
                if abs(avg_price - existing_avg) / existing_avg < 0.005:  # 0.5% overlap
                    overlaps = True
                    break
            
            if not overlaps:
                unique_zones.append((zone_type, top, bottom))
        
        return unique_zones
    
    def _add_support_resistance_zones(self, ax, zones: List[Tuple[str, float, float]], chart_length: int):
        """Add support/resistance zones to chart"""
        for zone_type, top, bottom in zones:
            color = 'red' if zone_type == 'resistance' else 'green'
            alpha = 0.2
            
            # Draw zone rectangle
            rect = plt.Rectangle((0, bottom), chart_length, top-bottom, 
                               facecolor=color, alpha=alpha, edgecolor=color, linewidth=1)
            ax.add_patch(rect)
            
            # Add zone label
            mid_price = (top + bottom) / 2
            ax.text(chart_length * 0.98, mid_price, f'{zone_type.upper()}\n${mid_price:.2f}', 
                   ha='right', va='center', fontsize=8, 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7))
    
    def _add_order_blocks(self, ax, order_blocks: List[Tuple[str, float, float]], chart_length: int):
        """Add SMC Order Blocks"""
        for i, (block_type, high, low) in enumerate(order_blocks):
            color = 'blue' if block_type == 'bullish' else 'purple'
            
            # Draw order block
            rect = plt.Rectangle((chart_length * 0.7, low), chart_length * 0.3, high-low,
                               facecolor=color, alpha=0.15, edgecolor=color, 
                               linewidth=2, linestyle='--')
            ax.add_patch(rect)
            
            # Label
            mid_price = (high + low) / 2
            ax.text(chart_length * 0.85, mid_price, f'OB\n{block_type}', 
                   ha='center', va='center', fontsize=7, color=color, weight='bold')
    
    def _add_liquidity_zones(self, ax, liquidity_zones: List[float]):
        """Add liquidity zones"""
        for zone in liquidity_zones:
            ax.axhline(y=zone, color='orange', linestyle=':', linewidth=1, alpha=0.7)
            ax.text(0.02, zone, f'LIQ ${zone:.2f}', transform=ax.get_yaxis_transform(),
                   fontsize=7, color='orange', weight='bold')
    
    def _add_signal_lines(self, ax, signal: Dict[str, Any]):
        """Add signal entry, SL, and TP lines"""
        # Entry line
        ax.axhline(y=signal['entry'], color='blue', linestyle='-', linewidth=3, label='Entry', alpha=0.9)
        
        # Stop Loss
        ax.axhline(y=signal['sl'], color='red', linestyle='--', linewidth=2, label='Stop Loss', alpha=0.8)
        
        # Take Profits with different styles
        tp_colors = ['green', 'lime', 'lightgreen', 'darkgreen']
        tp_styles = ['-', '--', '-.', ':']
        
        for i, (tp_key, color, style) in enumerate(zip(['tp1', 'tp2', 'tp3', 'tp4'], tp_colors, tp_styles)):
            if tp_key in signal:
                ax.axhline(y=signal[tp_key], color=color, linestyle=style, 
                          linewidth=2, label=f'TP{i+1}', alpha=0.8)
    
    def _add_entry_arrow(self, ax, signal: Dict[str, Any], chart_length: int):
        """Add entry arrow pointing to entry price"""
        entry_price = signal['entry']
        direction = signal['direction']
        
        # Arrow position
        arrow_x = chart_length * 0.95
        
        if direction == 'BUY':
            # Arrow pointing up
            ax.annotate('🔵 BUY ENTRY', xy=(arrow_x, entry_price), 
                       xytext=(arrow_x, entry_price - (entry_price * 0.01)),
                       arrowprops=dict(arrowstyle='->', color='blue', lw=3),
                       fontsize=12, color='blue', weight='bold', ha='center')
        else:
            # Arrow pointing down  
            ax.annotate('🔴 SELL ENTRY', xy=(arrow_x, entry_price),
                       xytext=(arrow_x, entry_price + (entry_price * 0.01)), 
                       arrowprops=dict(arrowstyle='->', color='red', lw=3),
                       fontsize=12, color='red', weight='bold', ha='center')
    
    def _add_signal_info_box(self, ax, signal: Dict[str, Any]):
        """Add detailed signal information box"""
        
        # Calculate R:R for each TP
        entry = signal['entry']
        sl_distance = abs(signal['sl'] - entry)
        
        rr_ratios = []
        for tp_key in ['tp1', 'tp2', 'tp3', 'tp4']:
            if tp_key in signal:
                tp_distance = abs(signal[tp_key] - entry)
                rr = tp_distance / sl_distance if sl_distance > 0 else 0
                rr_ratios.append(f"TP{tp_key[-1]}: 1:{rr:.1f}")
        
        info_text = f"""📊 SIGNAL DETAILS
Direction: {signal['direction']}
Score: {signal['score']:.1f}/100
Timeframe: {signal['timeframe']}

💰 LEVELS:
Entry: ${signal['entry']:.2f}
SL: ${signal['sl']:.2f}

🎯 TARGETS & R:R:
{chr(10).join(rr_ratios)}

⚡ STRATEGIES:
{signal.get('strategies_triggered', 0)} triggered
"""
        
        # Position info box
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', horizontalalignment='left',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    def _add_enhanced_legend(self, ax):
        """Add comprehensive legend"""
        
        # Create custom legend elements
        legend_elements = [
            plt.Line2D([0], [0], color='blue', lw=3, label='Entry'),
            plt.Line2D([0], [0], color='red', lw=2, linestyle='--', label='Stop Loss'),
            plt.Line2D([0], [0], color='green', lw=2, label='Take Profits'),
            plt.Rectangle((0,0),1,1, facecolor='red', alpha=0.2, label='Resistance Zone'),
            plt.Rectangle((0,0),1,1, facecolor='green', alpha=0.2, label='Support Zone'),
            plt.Rectangle((0,0),1,1, facecolor='blue', alpha=0.15, label='Order Block'),
            plt.Line2D([0], [0], color='orange', lw=1, linestyle=':', label='Liquidity')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

# Legacy compatibility  
ChartGenerator = EnhancedChartGenerator