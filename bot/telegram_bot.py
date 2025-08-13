"""Enhanced Telegram Bot with Symbol Switching & News Alerts"""
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
from utils.news_monitor import NewsMonitor

logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    def __init__(self):
        self.application = None
        self.bot = None
        self.chart_generator = EnhancedChartGenerator()
        self.news_monitor = NewsMonitor()
        self.current_symbol = "XAUUSD"  # Default
        
    async def initialize(self):
        try:
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            self.bot = self.application.bot
            
            # Enhanced Commands
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("report", self.cmd_report))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("signalchange", self.cmd_signal_change))
            self.application.add_handler(CommandHandler("symbol", self.cmd_current_symbol))
            self.application.add_handler(CommandHandler("news", self.cmd_news_status))
            
            await self.application.initialize()
            
            # Start news monitoring
            await self.news_monitor.start_monitoring(self.send_news_alert)
            
            logger.info("✅ Enhanced Telegram bot initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            return False
    
    async def start(self):
        await self.application.start()
        await self.application.updater.start_polling()
        await self.send_message(f"🚀 Enhanced Trading Bot started!\n📊 Current Symbol: {self.current_symbol}")
    
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
        """Send news alert 15 minutes before high-impact events"""
        try:
            message = f"""
🚨 <b>HIGH-IMPACT NEWS ALERT</b> 🚨

📅 <b>Time:</b> {news_data['time']} UTC
🏛️ <b>Country:</b> {news_data['country']}
📰 <b>Event:</b> {news_data['title']}
🔥 <b>Impact:</b> {news_data['impact']}

⚠️ <b>Trading Recommendation:</b>
• Close risky positions
• Reduce position sizes
• Wait for volatility to settle

⏰ Event starts in 15 minutes!
"""
            await self.send_message(message)
            logger.info(f"News alert sent: {news_data['title']}")
        except Exception as e:
            logger.error(f"Failed to send news alert: {e}")
    
    async def send_report(self, report: Dict[str, Any]):
        try:
            message = format_report_message(report)
            await self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
    
    # Enhanced Commands
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🤖 <b>Enhanced Trading Bot Active!</b>\n\n"
            f"📊 Current Symbol: <b>{self.current_symbol}</b>\n"
            f"🔄 Automated signals running\n"
            f"📰 News monitoring active\n\n"
            f"Use /help for all commands",
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
                    f"🔄 Bot will now analyze {new_symbol} markets",
                    parse_mode='HTML'
                )
                
                # Restart signal generation with new symbol
                from main import XAUUSDTradingSystem
                # Send notification to main system
                await self.send_message(f"🔄 System adapting to {new_symbol}...")
                
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
            f"💡 Use /signalchange to switch symbols",
            parse_mode='HTML'
        )
    
    async def cmd_news_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show news monitoring status"""
        news_status = await self.news_monitor.get_status()
        
        message = f"""
📰 <b>News Monitoring Status</b>

🟢 Status: {'Active' if news_status['active'] else 'Inactive'}
📊 Events Today: {news_status['events_today']} (🟡 + 🔥)
🔥 Red Folder: {news_status.get('high_impact_today', 0)}
⏰ Next Alert: {news_status['next_alert']}
🔄 Last Update: {news_status['last_update']}

📅 <b>Upcoming Events:</b>
"""
        
        for event in news_status['upcoming_events'][:6]:
            message += f"• {event['time']} {event['country']} - {event['title']}\n"
        
        message += f"""
ℹ️ <b>Alert Policy:</b>
🟡 Yellow: Shown in /news only
🔥 Red: Auto-alert 1h before event

📊 Data: {news_status.get('data_source', 'ForexFactory')}"""
        
        await update.message.reply_text(message, parse_mode='HTML')
    
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
📰 News Monitoring: Active

🔄 Use /signalchange to switch symbols"""
        
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

📊 <b>Trading Commands:</b>
/signalchange [symbol] - Switch trading symbol
• /signalchange xauusd (Gold)
• /signalchange btcusd (Bitcoin)
/symbol - Show current symbol

📰 <b>News Commands:</b>
/news - News monitoring status

💡 <b>Features:</b>
• Automatic signals with 4 TP levels
• Chart analysis with support/resistance zones
• Detailed reasoning for each signal
• News alerts 15min before high-impact events
• Symbol switching between Gold and Bitcoin
• AI learning and optimization

🤖 The bot analyzes markets every 5 minutes and sends high-quality signals automatically."""
        
        await update.message.reply_text(help_text, parse_mode='HTML')

# Make it compatible with existing code
TradingBot = EnhancedTradingBot