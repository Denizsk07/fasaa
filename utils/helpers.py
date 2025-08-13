"""Enhanced Helper Functions with Detailed Signal Formatting"""
from typing import Dict, Any

def format_enhanced_signal_message(signal: Dict[str, Any]) -> str:
    """Enhanced signal message with detailed analysis and reasoning"""
    
    direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
    arrow = "📈" if signal['direction'] == 'BUY' else "📉"
    
    # Calculate R:R ratios for each TP
    entry = signal['entry']
    sl_distance = abs(signal['sl'] - entry)
    
    tp_lines = []
    for i, tp_key in enumerate(['tp1', 'tp2', 'tp3', 'tp4'], 1):
        if tp_key in signal:
            tp_distance = abs(signal[tp_key] - entry)
            rr = tp_distance / sl_distance if sl_distance > 0 else 0
            tp_lines.append(f"🎯 <b>TP {i}:</b> ${signal[tp_key]:.2f} (R:R 1:{rr:.1f})")
    
    # Enhanced reasoning section
    reasoning_section = _format_detailed_reasoning(signal)
    
    # Market context
    market_context = _get_market_context(signal)
    
    message = f"""{direction_emoji} <b>{signal['direction']} SIGNAL</b> {direction_emoji}
{arrow} <b>{signal.get('symbol', 'XAUUSD')} {signal['timeframe']}</b>

💰 <b>ENTRY LEVELS:</b>
🔵 <b>Entry:</b> ${signal['entry']:.2f}
🛑 <b>Stop Loss:</b> ${signal['sl']:.2f}

🎯 <b>TAKE PROFIT LEVELS:</b>
{chr(10).join(tp_lines)}

📊 <b>SIGNAL STRENGTH:</b>
⚡ Score: <b>{signal['score']:.1f}/100</b>
🎯 Strategies: <b>{signal.get('strategies_triggered', 0)} triggered</b>
📈 Timeframe: <b>{signal['timeframe']}</b>
💎 Position Size: <b>{signal.get('position_size', 0.1):.3f} lots</b>

{reasoning_section}

{market_context}

⏰ <b>Signal Time:</b> {signal['timestamp'][:19]} UTC

🤖 <i>Enhanced AI Analysis • Auto-Learning Active</i>"""
    
    return message

def _format_detailed_reasoning(signal: Dict[str, Any]) -> str:
    """Format detailed reasoning for the signal"""
    
    reasons = signal.get('reasons', [])
    if not reasons:
        return "📝 <b>ANALYSIS:</b>\nTechnical confluence detected"
    
    reasoning = "📝 <b>DETAILED ANALYSIS:</b>\n"
    
    # Categorize reasons
    smc_reasons = [r for r in reasons if any(word in r.lower() for word in ['smc', 'structure', 'liquidity', 'order block'])]
    technical_reasons = [r for r in reasons if any(word in r.lower() for word in ['bollinger', 'rsi', 'macd', 'support', 'resistance'])]
    pattern_reasons = [r for r in reasons if any(word in r.lower() for word in ['pattern', 'candlestick', 'hammer', 'doji'])]
    volume_reasons = [r for r in reasons if 'volume' in r.lower()]
    
    # Format by category
    if smc_reasons:
        reasoning += "🧠 <b>Smart Money Concepts:</b>\n"
        for reason in smc_reasons[:2]:
            reasoning += f"  • {reason}\n"
    
    if technical_reasons:
        reasoning += "📊 <b>Technical Indicators:</b>\n"
        for reason in technical_reasons[:2]:
            reasoning += f"  • {reason}\n"
    
    if pattern_reasons:
        reasoning += "🕯️ <b>Price Action:</b>\n"
        for reason in pattern_reasons[:1]:
            reasoning += f"  • {reason}\n"
    
    if volume_reasons:
        reasoning += "📈 <b>Volume Analysis:</b>\n"
        for reason in volume_reasons[:1]:
            reasoning += f"  • {reason}\n"
    
    # Add confluence note
    num_confirmations = len([r for r in [smc_reasons, technical_reasons, pattern_reasons, volume_reasons] if r])
    if num_confirmations >= 2:
        reasoning += f"\n✅ <b>Multi-timeframe confluence:</b> {num_confirmations} confirmations"
    
    return reasoning

def _get_market_context(signal: Dict[str, Any]) -> str:
    """Get market context and trading advice"""
    
    score = signal.get('score', 0)
    direction = signal['direction']
    
    if score >= 90:
        strength = "🔥 EXTREMELY STRONG"
        advice = "High conviction trade • Consider larger position"
    elif score >= 85:
        strength = "💪 VERY STRONG" 
        advice = "Strong setup • Good for swing trading"
    elif score >= 80:
        strength = "✅ STRONG"
        advice = "Solid setup • Standard position size"
    elif score >= 75:
        strength = "📊 MODERATE"
        advice = "Decent setup • Reduced position size recommended"
    else:
        strength = "⚠️ WEAK"
        advice = "Low confidence • Consider paper trading"
    
    context = f"""🎯 <b>MARKET CONTEXT:</b>
💪 Signal Strength: {strength}
💡 Trading Advice: {advice}
🎲 Risk Level: {"Low" if score >= 85 else "Medium" if score >= 75 else "High"}

⚠️ <b>RISK MANAGEMENT:</b>
• Never risk more than 2% per trade
• Wait for price confirmation at entry
• Consider partial profits at TP1 and TP2
• Move SL to breakeven after TP1 hit"""
    
    return context

def format_report_message(report: Dict[str, Any]) -> str:
    """Enhanced performance report formatting"""
    
    win_rate = report.get('win_rate', 0)
    total_trades = report.get('total_trades', 0)
    
    # Performance emoji
    if win_rate >= 85:
        performance_emoji = "🏆"
        status = "EXCELLENT"
    elif win_rate >= 75:
        performance_emoji = "🎯"
        status = "VERY GOOD"
    elif win_rate >= 65:
        performance_emoji = "📈"
        status = "GOOD"
    elif win_rate >= 55:
        performance_emoji = "📊"
        status = "AVERAGE"
    else:
        performance_emoji = "📚"
        status = "LEARNING"
    
    message = f"""
📊 <b>{performance_emoji} PERFORMANCE REPORT</b>

📅 <b>Date:</b> {report.get('report_date', 'N/A')}
📈 <b>Status:</b> {status}

<b>📊 TRADING STATISTICS:</b>
• Total Trades: <b>{total_trades}</b>
• Today's Trades: <b>{report.get('today_trades', 0)}</b>
• Win Rate: <b>{win_rate:.1f}%</b>
• Average P/L: <b>{report.get('avg_pnl', 0):.1f} pips</b>
• Best Strategy: <b>{report.get('best_strategy', 'N/A')}</b>

<b>🎯 PROGRESS TO TARGET:</b>
{_create_progress_bar(win_rate, 90)}

<b>💡 PERFORMANCE INSIGHT:</b>
{_get_performance_insight(win_rate, total_trades)}

🤖 <i>AI continuously learning and optimizing</i>
"""
    
    return message

def _create_progress_bar(current: float, target: float) -> str:
    """Create visual progress bar"""
    progress = min(current / target, 1.0)
    filled = int(progress * 10)
    empty = 10 - filled
    
    bar = "█" * filled + "░" * empty
    return f"{bar} {current:.1f}% / {target}%"

def _get_performance_insight(win_rate: float, total_trades: int) -> str:
    """Get performance insight based on statistics"""
    
    if total_trades < 10:
        return "📚 Collecting data - More trades needed for reliable statistics"
    elif win_rate >= 85:
        return "🏆 Outstanding performance! System is operating at peak efficiency"
    elif win_rate >= 75:
        return "🎯 Excellent results! Minor optimizations can push to 90%+"
    elif win_rate >= 65:
        return "📈 Good progress! System is learning market patterns effectively"
    elif win_rate >= 55:
        return "📊 Average performance - Optimization cycles will improve results"
    else:
        return "🔧 Learning phase - System adapting to current market conditions"

# Additional utility functions
def format_news_alert(news_data: Dict[str, Any]) -> str:
    """Format news alert message für echte ForexFactory Events"""
    
    impact_emoji = {
        'high': '🔥',
        'medium': '⚠️', 
        'low': 'ℹ️'
    }
    
    emoji = impact_emoji.get(news_data.get('impact', '').lower(), '📰')
    minutes_until = news_data.get('minutes_until', 60)
    
    message = f"""
🚨 <b>HIGH-IMPACT NEWS ALERT</b> 🚨

⏰ <b>Time:</b> {news_data.get('time', 'Unknown')} UTC
🌍 <b>Country:</b> {news_data.get('country', 'Unknown')}
📰 <b>Event:</b> {news_data.get('title', 'Economic Event')}
{emoji} <b>Impact:</b> {news_data.get('impact', 'Unknown').upper()}

📊 <b>Data:</b>"""

    if news_data.get('forecast'):
        message += f"\n• Forecast: {news_data['forecast']}"
    if news_data.get('previous'):
        message += f"\n• Previous: {news_data['previous']}"

    message += f"""

⚠️ <b>TRADING ADVICE:</b>
• Close risky positions NOW
• Avoid new entries until after event
• Expect HIGH volatility
• Monitor price action closely

⏰ <b>Event starts in {minutes_until} minutes!</b>

🤖 <i>Real ForexFactory Data • Auto-Monitor Active</i>
"""
    
    return message

def format_symbol_change_confirmation(old_symbol: str, new_symbol: str, config_data: Dict[str, Any]) -> str:
    """Format symbol change confirmation"""
    
    symbol_info = {
        'XAUUSD': {'name': 'Gold', 'emoji': '🥇', 'type': 'Precious Metal'},
        'BTCUSD': {'name': 'Bitcoin', 'emoji': '₿', 'type': 'Cryptocurrency'}
    }
    
    old_info = symbol_info.get(old_symbol, {'name': old_symbol, 'emoji': '📊', 'type': 'Asset'})
    new_info = symbol_info.get(new_symbol, {'name': new_symbol, 'emoji': '📊', 'type': 'Asset'})
    
    message = f"""
✅ <b>SYMBOL CHANGE SUCCESSFUL</b>

📊 <b>TRANSITION:</b>
{old_info['emoji']} {old_info['name']} → {new_info['emoji']} {new_info['name']}

🎯 <b>NEW CONFIGURATION:</b>
• Asset Type: {new_info['type']}
• TP Levels: {config_data.get('tp_levels', [])}
• Stop Loss: ${config_data.get('stop_loss', 0)}
• Risk per Trade: {config_data.get('risk_percentage', 2)}%

🤖 <b>SYSTEM STATUS:</b>
• Strategies adapted to {new_symbol}
• Learning weights optimized
• Market analysis active

🔄 Bot now analyzing {new_info['name']} markets!
"""
    
    return message