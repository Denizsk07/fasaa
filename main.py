#!/usr/bin/env python3
"""
XAUUSD Trading Bot - Enhanced Main Entry Point
Version 2.0 - Mit Turbo-Learning für 90% Win-Rate
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot import TradingBot
from utils.logger import setup_logger
from trading.signal_generator import SignalGenerator
from learning.performance_tracker import PerformanceTracker
from learning.strategy_optimizer import StrategyOptimizer

# Setup logging
logger = setup_logger('main')

class XAUUSDTradingSystem:
    """Enhanced Trading System with Turbo-Learning"""
    
    def __init__(self):
        self.bot = None
        self.signal_generator = None
        self.performance_tracker = None
        self.strategy_optimizer = None
        self.scheduler = AsyncIOScheduler()
        self.trade_counter = 0
        self.last_optimization = datetime.now()
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🚀 Initializing ENHANCED XAUUSD Trading System...")
            logger.info("🧠 Turbo-Learning Mode: ACTIVATED")
            
            # Initialize components
            self.bot = TradingBot()
            self.signal_generator = SignalGenerator()
            self.performance_tracker = PerformanceTracker()
            self.strategy_optimizer = StrategyOptimizer()
            
            # Initialize bot
            await self.bot.initialize()
            
            # Setup scheduled tasks with enhanced intervals
            self.setup_scheduled_tasks()
            
            # Send startup message
            await self.bot.send_message(
                "🚀 <b>Trading Bot Started</b>\n"
                "🧠 <b>Turbo-Learning: ACTIVE</b>\n"
                "🎯 <b>Target: 90% Win-Rate</b>\n"
                "⚡ <b>Analysis: Every 5 minutes</b>\n"
                "📊 <b>Optimization: Every 6 hours</b>"
            )
            
            # Initial system check
            await self.system_check()
            
            logger.info("✅ System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            return False
    
    def setup_scheduled_tasks(self):
        """Setup automated tasks with ENHANCED intervals for faster learning"""
        
        # TURBO MODE: Analyze market every 5 minutes (statt 15)
        self.scheduler.add_job(
            self.analyze_and_signal,
            'interval',
            minutes=5,  # Schnellere Analyse für mehr Lern-Daten
            id='market_analysis',
            replace_existing=True,
            max_instances=1
        )
        
        # Quick optimization after every 10 trades
        self.scheduler.add_job(
            self.quick_optimize_check,
            'interval',
            minutes=30,  # Check every 30 minutes
            id='quick_optimization',
            replace_existing=True
        )
        
        # Deep optimization every 6 hours (statt wöchentlich)
        self.scheduler.add_job(
            self.deep_optimize_strategies,
            'interval',
            hours=6,  # Viel häufigere Optimierung
            id='deep_optimization',
            replace_existing=True
        )
        
        # Hourly performance update
        self.scheduler.add_job(
            self.hourly_performance_update,
            'interval',
            hours=1,
            id='hourly_update',
            replace_existing=True
        )
        
        # Daily comprehensive report
        self.scheduler.add_job(
            self.daily_report,
            'cron',
            hour=22,
            minute=0,
            id='daily_report',
            replace_existing=True
        )
        
        # Morning market preparation
        self.scheduler.add_job(
            self.morning_preparation,
            'cron',
            hour=7,
            minute=0,
            id='morning_prep',
            replace_existing=True
        )
        
        logger.info("📅 Enhanced scheduler configured for Turbo-Learning")
    
    async def analyze_and_signal(self):
        """Main analysis and signal generation with learning feedback"""
        try:
            logger.info("🔍 Starting market analysis...")
            
            # Check if market is open (skip weekends for XAUUSD)
            if not self.is_market_open():
                logger.info("⏸️ Market closed - skipping analysis")
                return
            
            # Generate signal
            signal = await self.signal_generator.generate_signal()
            
            if signal and signal['score'] >= float(os.getenv('MIN_SIGNAL_SCORE', 75)):
                # Add trade counter
                self.trade_counter += 1
                signal['trade_number'] = self.trade_counter
                
                # Send signal to Telegram
                await self.bot.send_signal(signal)
                
                # Track performance
                self.performance_tracker.record_signal(signal)
                
                # Log for learning
                logger.info(f"📤 Signal #{self.trade_counter} sent: {signal['direction']} @ {signal['entry']}")
                logger.info(f"📊 Score: {signal['score']:.1f} | Strategies: {signal.get('strategies_triggered', 0)}")
                
                # Quick learn after each trade
                if self.trade_counter % 5 == 0:
                    await self.quick_learn()
                    
            else:
                if signal:
                    logger.info(f"⏸️ Signal found but score too low: {signal.get('score', 0):.1f}")
                else:
                    logger.info("⏸️ No signal detected in current market conditions")
                    
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            await self.bot.send_message(f"⚠️ Analysis error: {str(e)[:100]}")
    
    async def quick_learn(self):
        """Quick learning after every few trades"""
        try:
            logger.info("🧠 Quick learning cycle...")
            
            # Get current stats
            stats = self.performance_tracker.get_current_stats()
            
            # Quick optimization if we have enough data
            if stats['total_trades'] >= 5:
                await self.strategy_optimizer.quick_optimize()
                
                logger.info(f"📈 Current Win-Rate: {stats['win_rate']:.1f}%")
                
                # Notify if approaching target
                if stats['win_rate'] >= 85:
                    await self.bot.send_message(
                        f"🎯 <b>Approaching Target!</b>\n"
                        f"Win-Rate: {stats['win_rate']:.1f}%\n"
                        f"Trades: {stats['total_trades']}"
                    )
                    
        except Exception as e:
            logger.error(f"Quick learn error: {e}")
    
    async def quick_optimize_check(self):
        """Check if quick optimization is needed"""
        try:
            stats = self.performance_tracker.get_current_stats()
            
            # Optimize every 10 trades or if performance drops
            if (self.trade_counter > 0 and self.trade_counter % 10 == 0) or \
               (stats['win_rate'] < 60 and stats['total_trades'] >= 5):
                
                logger.info("⚡ Triggering quick optimization...")
                await self.strategy_optimizer.quick_optimize()
                
                # Send update
                await self.bot.send_message(
                    f"⚡ <b>Quick Optimization Complete</b>\n"
                    f"Trades analyzed: {stats['total_trades']}\n"
                    f"Current Win-Rate: {stats['win_rate']:.1f}%"
                )
                
        except Exception as e:
            logger.error(f"Quick optimize check error: {e}")
    
    async def deep_optimize_strategies(self):
        """Deep optimization of all strategies"""
        try:
            logger.info("🔬 Starting DEEP optimization...")
            
            # Full optimization
            await self.strategy_optimizer.optimize()
            
            # Get updated stats
            stats = self.performance_tracker.get_current_stats()
            
            # Prepare optimization report
            message = f"""
🔬 <b>Deep Optimization Complete</b>

📊 <b>Performance Metrics:</b>
• Total Trades: {stats['total_trades']}
• Win Rate: {stats['win_rate']:.1f}%
• Avg P/L: {stats['avg_pnl']:.1f} pips
• Best Strategy: {stats['best_strategy']}

🎯 <b>Progress to 90% Target:</b>
{self.get_progress_bar(stats['win_rate'], 90)}

🧠 <b>Learning Status:</b>
{self.get_learning_status(stats['win_rate'])}

⏰ Next optimization in 6 hours
"""
            
            await self.bot.send_message(message)
            logger.info("🎯 Deep optimization completed")
            
        except Exception as e:
            logger.error(f"❌ Deep optimization error: {e}")
    
    async def hourly_performance_update(self):
        """Send hourly performance updates"""
        try:
            stats = self.performance_tracker.get_current_stats()
            
            # Only send if there are trades
            if stats['total_trades'] > 0:
                # Calculate hourly stats
                recent_trades = self.performance_tracker.trades[-10:]  # Last 10 trades
                recent_wins = len([t for t in recent_trades if t.get('pnl', 0) > 0])
                recent_winrate = (recent_wins / len(recent_trades) * 100) if recent_trades else 0
                
                message = f"""
📊 <b>Hourly Update</b>

Last 10 Trades Win-Rate: {recent_winrate:.1f}%
Overall Win-Rate: {stats['win_rate']:.1f}%
Total Trades Today: {self.trade_counter}

{"🔥 ON FIRE!" if recent_winrate >= 80 else "📈 Learning..." if recent_winrate >= 60 else "📚 Analyzing patterns..."}
"""
                
                await self.bot.send_message(message)
                
        except Exception as e:
            logger.error(f"Hourly update error: {e}")
    
    async def daily_report(self):
        """Generate and send comprehensive daily report"""
        try:
            report = await self.performance_tracker.generate_daily_report()
            
            # Enhanced report with learning progress
            enhanced_report = f"""
📊 <b>Daily Performance Report</b>
{"-" * 30}

📅 Date: {report.get('report_date', 'N/A')}

<b>📈 Trading Statistics:</b>
• Total Trades: {report.get('total_trades', 0)}
• Today's Trades: {report.get('today_trades', 0)}
• Win Rate: {report.get('win_rate', 0):.1f}%
• Avg P/L: {report.get('avg_pnl', 0):.1f} pips

<b>🧠 Learning Progress:</b>
{self.get_progress_bar(report.get('win_rate', 0), 90)}

<b>🎯 Strategy Performance:</b>
• Best: {report.get('best_strategy', 'N/A')}
• Optimization Cycles: {self.trade_counter // 10}

<b>💡 Recommendation:</b>
{self.get_recommendation(report.get('win_rate', 0))}

<b>📈 Projected Win-Rate (7 days):</b>
{self.project_winrate(report.get('win_rate', 0))}%

{"-" * 30}
🤖 <i>Bot Learning: {self.get_learning_status(report.get('win_rate', 0))}</i>
"""
            
            await self.bot.send_message(enhanced_report)
            logger.info("📊 Daily report sent")
            
        except Exception as e:
            logger.error(f"❌ Report error: {e}")
    
    async def morning_preparation(self):
        """Morning market preparation and system check"""
        try:
            await self.bot.send_message(
                "☀️ <b>Good Morning!</b>\n\n"
                "🤖 Bot Status: Active\n"
                "🧠 Learning Mode: Engaged\n"
                "📊 Preparing for today's trading...\n"
                "🎯 Target: 90% Win-Rate"
            )
            
            # Run system check
            await self.system_check()
            
        except Exception as e:
            logger.error(f"Morning prep error: {e}")
    
    async def system_check(self):
        """Check system health and data availability"""
        try:
            from trading.data_manager import DataManager
            dm = DataManager()
            
            price = dm.get_current_price()
            if price:
                logger.info(f"✅ System check OK - Current price: ${price:.2f}")
            else:
                logger.warning("⚠️ Could not fetch current price")
                
        except Exception as e:
            logger.error(f"System check error: {e}")
    
    def is_market_open(self):
        """Check if market is open (skip weekends for XAUUSD)"""
        now = datetime.now()
        
        # For crypto (BTC, ETH) - always open
        symbol = os.getenv('YF_SYMBOL', 'XAUUSD=X')
        if 'BTC' in symbol or 'ETH' in symbol or 'CRYPTO' in symbol:
            return True
        
        # For XAUUSD - closed on weekends
        if symbol == 'XAUUSD=X':
            # Market closed from Friday 22:00 to Sunday 22:00 (UTC)
            if now.weekday() == 5:  # Saturday
                return False
            if now.weekday() == 6:  # Sunday
                return now.hour >= 22  # Open after 22:00 UTC
                
        return True
    
    def get_progress_bar(self, current: float, target: float) -> str:
        """Create a visual progress bar"""
        progress = min(current / target * 100, 100)
        filled = int(progress / 10)
        empty = 10 - filled
        
        bar = "█" * filled + "░" * empty
        return f"{bar} {current:.1f}% / {target}%"
    
    def get_learning_status(self, winrate: float) -> str:
        """Get learning status message based on win rate"""
        if winrate >= 85:
            return "🏆 EXCELLENT - Approaching mastery!"
        elif winrate >= 75:
            return "🎯 ADVANCED - System performing well"
        elif winrate >= 65:
            return "📈 IMPROVING - Learning patterns"
        elif winrate >= 55:
            return "📚 LEARNING - Gathering data"
        else:
            return "🔬 ANALYZING - Calibrating strategies"
    
    def get_recommendation(self, winrate: float) -> str:
        """Get recommendation based on performance"""
        if winrate >= 80:
            return "✅ Excellent performance! Consider increasing position size."
        elif winrate >= 70:
            return "👍 Good performance. Maintain current settings."
        elif winrate >= 60:
            return "📊 System is learning. Be patient."
        else:
            return "⏳ Early learning phase. More data needed."
    
    def project_winrate(self, current: float) -> float:
        """Project future win rate based on learning curve"""
        # Simple projection based on learning rate
        if current < 60:
            return min(current + 15, 90)  # Fast initial learning
        elif current < 75:
            return min(current + 10, 90)  # Medium learning
        elif current < 85:
            return min(current + 5, 90)   # Slower refinement
        else:
            return min(current + 2, 92)   # Fine tuning
    
    async def run(self):
        """Main run loop"""
        if not await self.initialize():
            logger.error("Failed to initialize system")
            return
        
        try:
            # Start scheduler
            self.scheduler.start()
            
            # Start bot
            await self.bot.start()
            
            logger.info("🤖 Enhanced Bot is running... Press Ctrl+C to stop")
            logger.info("🧠 Turbo-Learning activated - Target: 90% Win-Rate")
            logger.info("📊 Analysis every 5 minutes, Optimization every 6 hours")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Shutting down...")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
            await self.bot.send_message(f"⚠️ Bot error: {str(e)[:100]}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            # Send shutdown message
            stats = self.performance_tracker.get_current_stats()
            await self.bot.send_message(
                f"⏹️ <b>Bot Shutting Down</b>\n\n"
                f"Final Stats:\n"
                f"• Trades: {stats['total_trades']}\n"
                f"• Win Rate: {stats['win_rate']:.1f}%\n"
                f"• Learning Cycles: {self.trade_counter // 10}\n\n"
                f"👋 See you soon!"
            )
            
            # Shutdown components
            self.scheduler.shutdown()
            if self.bot:
                await self.bot.stop()
                
            logger.info("👋 System shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

async def main():
    """Main entry point"""
    print("="*60)
    print("🚀 XAUUSD TRADING BOT - ENHANCED VERSION 2.0")
    print("🧠 TURBO-LEARNING MODE FOR 90% WIN-RATE")
    print("="*60)
    
    system = XAUUSDTradingSystem()
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())