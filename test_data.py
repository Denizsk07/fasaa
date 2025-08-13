#!/usr/bin/env python3
"""
Live Signal Test - Mit echten Config-Weights
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def live_signal_test():
    """Teste mit echten Config-Weights"""
    
    print("🎯 LIVE SIGNAL TEST - Mit korrekten Weights")
    print("=" * 50)
    
    try:
        # Import updated config
        from config import config
        from trading.signal_generator import SignalGenerator
        
        print(f"✅ Config loaded - MIN_SCORE: {config.MIN_SIGNAL_SCORE}")
        print(f"📊 Updated weights loaded")
        
        # Show new weights
        print(f"\n⚖️ CURRENT STRATEGY WEIGHTS:")
        print("-" * 30)
        for strategy, weight in sorted(config.STRATEGY_WEIGHTS.items(), key=lambda x: x[1], reverse=True):
            percentage = weight * 100
            print(f"{strategy:15s}: {weight:.3f} ({percentage:4.1f}%)")
        
        # Initialize with updated config
        sg = SignalGenerator()
        
        # Force reload of weights
        sg.weights = config.STRATEGY_WEIGHTS
        print(f"\n🔄 Signal Generator weights updated")
        
        # Test current price
        price = sg.data_manager.get_current_price()
        print(f"💰 Current price: ${price:.2f}")
        
        # Test signal generation
        print(f"\n🎯 GENERATING LIVE SIGNAL...")
        print("-" * 30)
        
        signal = await sg.generate_signal()
        
        if signal:
            print(f"\n🎉 LIVE SIGNAL GENERATED!")
            print(f"   Direction: {signal['direction']}")
            print(f"   Entry: ${signal['entry']:.2f}")
            print(f"   Score: {signal['score']:.1f}")
            print(f"   Timeframe: {signal['timeframe']}")
            
            if 'sl' in signal:
                print(f"\n💰 RISK LEVELS:")
                print(f"   Stop Loss: ${signal['sl']:.2f}")
                print(f"   TP1: ${signal.get('tp1', 0):.2f}")
                print(f"   TP2: ${signal.get('tp2', 0):.2f}")
                print(f"   TP3: ${signal.get('tp3', 0):.2f}")
                print(f"   TP4: ${signal.get('tp4', 0):.2f}")
            
            print(f"\n📝 Reasons:")
            for i, reason in enumerate(signal.get('reasons', []), 1):
                print(f"   {i}. {reason}")
                
            # Test Telegram (optional)
            try:
                print(f"\n📱 Testing Telegram...")
                from bot.telegram_bot import TradingBot
                bot = TradingBot()
                await bot.initialize()
                
                # Format message
                from utils.helpers import format_enhanced_signal_message
                message = format_enhanced_signal_message(signal)
                
                print(f"✅ Telegram message formatted")
                print(f"📧 Ready to send to Telegram")
                
                # Uncomment to actually send:
                # await bot.send_signal(signal)
                # print(f"📤 Signal sent to Telegram!")
                
            except Exception as e:
                print(f"⚠️ Telegram test failed: {e}")
        
        else:
            print(f"\n❌ NO SIGNAL GENERATED")
            
            # Manual calculation
            print(f"\n🔍 MANUAL CALCULATION:")
            
            for timeframe in config.TIMEFRAMES:
                print(f"\n📊 Timeframe {timeframe}min:")
                
                df = sg.data_manager.get_data(timeframe, 100)
                if df is not None:
                    df = sg.tech_analysis.add_indicators(df)
                    results = sg.strategy_engine.analyze(df)
                    
                    buy_score = 0
                    sell_score = 0
                    
                    print(f"   Strategy results:")
                    for strategy, result in results.items():
                        direction = result.get('direction', 'NEUTRAL')
                        score = result.get('score', 0)
                        weight = config.STRATEGY_WEIGHTS.get(strategy, 0)
                        weighted = score * weight
                        
                        if direction == 'BUY':
                            buy_score += weighted
                        elif direction == 'SELL':
                            sell_score += weighted
                        
                        if direction != 'NEUTRAL':
                            status = "🟢" if direction == 'BUY' else "🔴"
                            print(f"     {status} {strategy}: {score} × {weight:.2f} = {weighted:.1f}")
                    
                    print(f"   TOTAL: BUY={buy_score:.1f}, SELL={sell_score:.1f}")
                    max_score = max(buy_score, sell_score)
                    
                    if max_score >= config.MIN_SIGNAL_SCORE:
                        direction = "BUY" if buy_score > sell_score else "SELL"
                        print(f"   ✅ {direction} Signal qualifies! Score: {max_score:.1f}")
                    else:
                        print(f"   ❌ Max score {max_score:.1f} < {config.MIN_SIGNAL_SCORE}")
        
        print(f"\n🚀 CONCLUSION:")
        if signal:
            print(f"✅ SUCCESS! Bot is ready for live trading!")
            print(f"💰 Signal: {signal['direction']} @ ${signal['entry']:.2f}")
            print(f"📊 Score: {signal['score']:.1f}")
        else:
            print(f"⏳ No signal right now - try again in 5-15 minutes")
            print(f"🎯 Bot will work when market conditions align")
            print(f"🔥 Threshold is now only {config.MIN_SIGNAL_SCORE} - very achievable!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🕐 Test started at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        asyncio.run(live_signal_test())
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted")
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%H:%M:%S')}")