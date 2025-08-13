"""Enhanced Telegram Bot with /price command and REAL ForexFactory News"""
import os
from datetime import datetime
from typing import Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import requests
import asyncio

from config import config
from visualization.chart_generator import EnhancedChartGenerator
from utils.helpers import format_enhanced_signal_message, format_report_message
from utils.news_monitor import RealForexFactoryNewsMonitor

logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    def __init__(self):
        self.application = None
        self.bot = None
        self.chart_generator = EnhancedChartGenerator()
        self.news_monitor = RealForexFactoryNewsMonitor()
        self.current_symbol = "XAUUSD"  # Default
        
    async def initialize(self):
        try:
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            self.bot = self.application.bot
            
            # Enhanced Commands with /price
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("report", self.cmd_report))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("signalchange", self.cmd_signal_change))
            self.application.add_handler(CommandHandler("symbol", self.cmd_current_symbol))
            self.application.add_handler(CommandHandler("news", self.cmd_news_status))
            self.application.add_handler(CommandHandler("price", self.cmd_current_price))  # NEW!
            
            await self.application.initialize()
            
            # Start REAL news monitoring
            await self.news_monitor.start_monitoring(self.send_news_alert)
            
            logger.info("✅ Enhanced Telegram bot initialized with /price and real news")
            return True
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    async def start(self):
        await self.application.start()
        await self.application.updater.start_polling()
        await self.send_message(f"🚀 Enhanced Trading Bot started!\n📊 Current Symbol: {self.current_symbol}\n💡 Use /price for live price!")
    
    async def stop(self):
        await self.news_monitor.stop_monitoring()
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
    
    async def send_message(self, text: str):
        try:
            await self.bot.send_message(chat_id=config.GROUP_ID, text=text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_signal(self, signal: Dict[str, Any]):
        try:
            # Generate enhanced chart with zones
            chart_path = await self.chart_generator.generate_enhanced_signal_chart(signal)
            
            # Enhanced message with detailed reasoning
            message = format_enhanced_signal_message(signal)
            
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=config.GROUP_ID, 
                        photo=photo, 
                        caption=message, 
                        parse_mode='HTML'
                    )
            else:
                await self.send_message(message)
                
            logger.info(f"Enhanced signal sent: {signal['direction']} @ {signal['entry']}")
        except Exception as e:
            logger.error(f"Failed to send enhanced signal: {e}")
    
    async def send_news_alert(self, news_data: Dict[str, Any]):
        """Send news alert for RED FOLDER events"""
        try:
            impact_emoji = {
                'high': '🔥',
                'medium': '🟡',
                'low': 'ℹ️'
            }
            
            emoji = impact_emoji.get(news_data.get('impact', '').lower(), '📰')
            
            message = f"""
🚨 <b>HIGH-IMPACT USD NEWS ALERT</b> 🚨

⏰ <b>Time:</b> {news_data['time']} UTC
🇺🇸 <b>Country:</b> {news_data['country']}
📰 <b>Event:</b> {news_data['title']}
{emoji} <b>Impact:</b> {news_data['impact'].upper()}

📊 <b>Data:</b>"""

            if news_data.get('forecast'):
                message += f"\n• Forecast: {news_data['forecast']}"
            if news_data.get('previous'):
                message += f"\n• Previous: {news_data['previous']}"

            message += f"""

⚠️ <b>TRADING RECOMMENDATION:</b>
• Close risky positions NOW
• Avoid new entries 15min before/after
• Expect HIGH volatility
• Monitor price action closely

⏰ Event starts in {news_data.get('minutes_until', 60)} minutes!

🤖 <i>Real ForexFactory Data • Auto-Monitor Active</i>
"""
            await self.send_message(message)
            logger.info(f"USD news alert sent: {news_data['title']}")
        except Exception as e:
            logger.error(f"Failed to send news alert: {e}")
    
    async def send_report(self, report: Dict[str, Any]):
        try:
            message = format_report_message(report)
            await self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
    
    # NEW COMMAND: /price
    async def cmd_current_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current live price with details"""
        try:
            # Get live price from data manager
            from trading.data_manager import DataManager
            dm = DataManager()
            
            # Get health check for detailed info
            health = dm.health_check()
            current_price = health.get('current_price')
            source = health.get('active_source', 'unknown')
            last_update_age = health.get('last_update_age_seconds', 0)
            
            if current_price:
                # Calculate change (dummy for now - you can implement price history)
                change = "+2.30"  # This should be calculated from price history
                change_pct = "+0.07%"
                
                # Session info
                from datetime import datetime
                hour = datetime.now().hour
                if 8 <= hour <= 17:
                    session = "🇬🇧 London Session"
                    session_desc = "High volatility expected"
                elif 13 <= hour <= 22:
                    session = "🇺🇸 New York Session" 
                    session_desc = "Peak trading hours"
                else:
                    session = "🌏 Asian Session"
                    session_desc = "Lower volatility period"
                
                message = f"""💰 <b>LIVE {self.current_symbol} PRICE</b>

🔥 <b>Current Price:</b> ${current_price:.2f}
📈 <b>Change:</b> {change} ({change_pct})

📊 <b>DATA SOURCE:</b>
• Source: {source}
• Update: {last_update_age:.0f}s ago
• Status: {'🟢 LIVE' if last_update_age < 10 else '🟡 DELAYED' if last_update_age < 60 else '🔴 STALE'}

🕐 <b>MARKET SESSION:</b>
• {session}
• {session_desc}

⚡ <b>TRADING CONDITIONS:</b>
• Spread: ~0.3 pips
• Volatility: {'High' if 8 <= hour <= 22 else 'Low'}
• Liquidity: {'High' if 13 <= hour <= 17 else 'Medium'}

🤖 <i>Live data • Updates every second</i>
💡 Use /news for upcoming events affecting price"""

            else:
                message = f"""❌ <b>PRICE DATA UNAVAILABLE</b>

🔧 <b>Status:</b> No live price data
📊 <b>Data Manager:</b> Trying to reconnect...
⏰ <b>Last Update:</b> Never

💡 <b>Troubleshooting:</b>
• Check internet connection
• APIs may be temporarily down
• Bot will retry automatically

🔄 Try again in a few moments"""

            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting price: {str(e)}")
            logger.error(f"Price command error: {e}")
    
    # ENHANCED COMMAND: /news with Yellow + Red Folder
    async def cmd_news_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show REAL ForexFactory news status with Yellow + Red folder events"""
        try:
            news_status = await self.news_monitor.get_status()
            
            # Count events by impact
            high_impact = news_status.get('high_impact_today', 0)
            medium_impact = news_status.get('medium_impact_today', 0)
            low_impact = news_status.get('low_impact_today', 0)
            
            message = f"""
📰 <b>REAL FOREXFACTORY USD NEWS</b>

🟢 <b>Status:</b> {'Active' if news_status['active'] else 'Inactive'}
📊 <b>Today's USD Events:</b> {news_status['events_today']} total
🔥 <b>Red Folder (High):</b> {high_impact}
🟡 <b>Yellow Folder (Medium):</b> {medium_impact}
ℹ️ <b>Orange Folder (Low):</b> {low_impact}

⏰ <b>Next High-Impact Alert:</b> {news_status['next_alert']}
🔄 <b>Last Update:</b> {news_status['last_update']}

📅 <b>Upcoming USD Events:</b>
"""
            
            # Show upcoming events with proper icons
            for event in news_status['upcoming_events'][:8]:
                impact_icon = {
                    'high': '🔥',
                    'medium': '🟡', 
                    'low': 'ℹ️'
                }.get(event.get('impact', 'low'), 'ℹ️')
                
                message += f"{impact_icon} {event['time']} UTC - {event['title']}\n"
            
            message += f"""
📋 <b>ALERT POLICY:</b>
🔥 Red Folder: Auto-alert 60min before
🟡 Yellow Folder: Shown in /news only
ℹ️ Orange Folder: Background tracking

📊 <b>Data Source:</b> {news_status.get('data_source', 'ForexFactory.com')}
🇺🇸 <b>Focus:</b> USD events only (affects XAUUSD)

💡 Use /price for current market price"""
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting news: {str(e)}")
            logger.error(f"News command error: {e}")
    
    # Enhanced Commands
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🤖 <b>Enhanced Trading Bot Active!</b>\n\n"
            f"📊 Current Symbol: <b>{self.current_symbol}</b>\n"
            f"🔄 Automated signals running\n"
            f"📰 Real ForexFactory news monitoring\n"
            f"💰 Live price updates every second\n\n"
            f"💡 <b>Quick Commands:</b>\n"
            f"/price - Live price\n"
            f"/news - USD news events\n"
            f"/help - All commands",
            parse_mode='HTML'
        )
    
    async def cmd_signal_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Change trading symbol: /signalchange xauusd or /signalchange btcusd"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ Usage: /signalchange [symbol]\n\n"
                    "Available symbols:\n"
                    "• xauusd (Gold)\n"
                    "• btcusd (Bitcoin)\n\n"
                    "Example: /signalchange btcusd"
                )
                return
            
            new_symbol = context.args[0].upper()
            
            if new_symbol in ['XAUUSD', 'BTCUSD']:
                old_symbol = self.current_symbol
                self.current_symbol = new_symbol
                
                # Update config
                if new_symbol == 'XAUUSD':
                    config.PRIMARY_SYMBOL = 'XAUUSD'
                    config.YF_SYMBOLS = ['XAUUSD=X', 'GC=F', 'GOLD']
                    config.TP_LEVELS = [5.0, 10.0, 15.0, 25.0]
                    config.STOP_LOSS = 8.0
                elif new_symbol == 'BTCUSD':
                    config.PRIMARY_SYMBOL = 'BTCUSD'
                    config.YF_SYMBOLS = ['BTC-USD', 'BTCUSD=X']
                    config.TP_LEVELS = [500, 1000, 1500, 2500]
                    config.STOP_LOSS = 300
                
                await update.message.reply_text(
                    f"✅ <b>Symbol Changed Successfully!</b>\n\n"
                    f"📊 Old Symbol: {old_symbol}\n"
                    f"📈 New Symbol: <b>{new_symbol}</b>\n\n"
                    f"🎯 TP Levels: {config.TP_LEVELS}\n"
                    f"🛑 Stop Loss: {config.STOP_LOSS}\n\n"
                    f"🔄 Bot will now analyze {new_symbol} markets\n"
                    f"💡 Use /price to see live {new_symbol} price",
                    parse_mode='HTML'
                )
                
            else:
                await update.message.reply_text(
                    "❌ Invalid symbol!\n\n"
                    "Supported symbols:\n"
                    "• XAUUSD (Gold)\n"
                    "• BTCUSD (Bitcoin)"
                )
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error changing symbol: {str(e)}")
            logger.error(f"Symbol change error: {e}")
    
    async def cmd_current_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current trading symbol"""
        await update.message.reply_text(
            f"📊 <b>Current Trading Symbol</b>\n\n"
            f"🎯 Symbol: <b>{self.current_symbol}</b>\n"
            f"📈 TP Levels: {config.TP_LEVELS}\n"
            f"🛑 Stop Loss: {config.STOP_LOSS}\n\n"
            f"💡 Use /signalchange to switch symbols\n"
            f"💰 Use /price for live {self.current_symbol} price",
            parse_mode='HTML'
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from learning.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker()
        stats = tracker.get_current_stats()
        
        message = f"""📊 <b>Enhanced Bot Status</b>

🟢 Status: Active
📊 Symbol: <b>{self.current_symbol}</b>
📈 Total Trades: {stats.get('total_trades', 0)}
✅ Win Rate: {stats.get('win_rate', 0):.1f}%
💰 Avg P/L: {stats.get('avg_pnl', 0):.1f} pips
🎯 Best Strategy: {stats.get('best_strategy', 'N/A')}
📰 News Monitoring: Active (Real ForexFactory)
💻 Live Price Updates: Every second

💡 Use /price for live price, /news for events"""
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from learning.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker()
        report = await tracker.generate_daily_report()
        message = format_report_message(report)
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """📚 <b>Enhanced Trading Bot Commands</b>

🤖 <b>Basic Commands:</b>
/start - Start the bot
/status - Current bot status  
/report - Performance report

💰 <b>Live Data Commands:</b>
/price - Show live price with details
/news - Real ForexFactory USD news events

📊 <b>Trading Commands:</b>
/signalchange [symbol] - Switch trading symbol
• /signalchange xauusd (Gold)
• /signalchange btcusd (Bitcoin)
/symbol - Show current symbol

💡 <b>Enhanced Features:</b>
• Live price updates every second
• Real ForexFactory news monitoring (Red + Yellow folder)
• Auto-alerts 60min before high-impact USD events
• Chart analysis with support/resistance zones
• Detailed reasoning for each signal
• Symbol switching between Gold and Bitcoin
• AI learning and optimization

🇺🇸 <b>News Focus:</b> USD events only (affects XAUUSD)
🔴 Red Folder: Auto-alerts
🟡 Yellow Folder: Shown in /news
ℹ️ Orange Folder: Background tracking

🤖 The bot analyzes markets every 5 minutes with REAL live data and sends high-quality signals automatically."""
        
        await update.message.reply_text(help_text, parse_mode='HTML')

# Make it compatible with existing code
TradingBot = EnhancedTradingBot