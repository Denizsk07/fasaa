#!/usr/bin/env python3
"""
Schneller Signal Test - Prüft ob Bot Signale generieren kann
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def quick_test():
    print("🚀 QUICK SIGNAL TEST")
    print("=" * 30)
    
    try:
        from config import config
        from trading.signal_generator import SignalGenerator
        
        print(f"✅ Imports successful")
        print(f"📊 Current threshold: {config.MIN_SIGNAL_SCORE}")
        
        # Test signal generation
        sg = SignalGenerator()
        print(f"🔍 Testing signal generation...")
        
        signal = await sg.generate_signal()
        
        if signal:
            print(f"\n🎉 SUCCESS! Signal generated:")
            print(f"   Direction: {signal['direction']}")
            print(f"   Entry: ${signal['entry']:.2f}")
            print(f"   Score: {signal['score']:.1f}")
            print(f"   Timeframe: {signal['timeframe']}")
            
            print(f"\n💰 Risk Levels:")
            print(f"   Stop Loss: ${signal.get('sl', 0):.2f}")
            print(f"   TP1: ${signal.get('tp1', 0):.2f}")
            print(f"   TP2: ${signal.get('tp2', 0):.2f}")
            
            print(f"\n📝 Reasons:")
            for reason in signal.get('reasons', []):
                print(f"   • {reason}")
                
            print(f"\n✅ YOUR BOT WORKS! It will send signals when market conditions are right.")
            
        else:
            print(f"\n⏸️ No signal right now")
            print(f"🔍 Let's test with lower threshold...")
            
            # Test with lower threshold
            original = config.MIN_SIGNAL_SCORE
            config.MIN_SIGNAL_SCORE = 15.0
            
            print(f"📉 Testing with threshold: {config.MIN_SIGNAL_SCORE}")
            
            signal = await sg.generate_signal()
            
            if signal:
                print(f"✅ Signal found with lower threshold!")
                print(f"   {signal['direction']} @ ${signal['entry']:.2f} (Score: {signal['score']:.1f})")
                print(f"💡 Bot will work - just needs right market conditions!")
            else:
                print(f"❌ Still no signal - market may be very stable right now")
                print(f"💡 Try switching to Bitcoin (/signalchange btcusd) for more volatility")
            
            # Restore threshold
            config.MIN_SIGNAL_SCORE = original
        
        # Test current price
        price = sg.data_manager.get_current_price()
        print(f"\n📊 Current price: ${price:.2f}")
        
        # Test strategies individually
        print(f"\n🧠 Testing individual strategies:")
        df = sg.data_manager.get_data('15', 100)
        if df is not None:
            df = sg.tech_analysis.add_indicators(df)
            results = sg.strategy_engine.analyze(df)
            
            active_strategies = 0
            for name, result in results.items():
                if result.get('direction') != 'NEUTRAL':
                    active_strategies += 1
                    print(f"   ✅ {name}: {result.get('direction')} (Score: {result.get('score', 0)})")
            
            print(f"\n📈 Active strategies: {active_strategies}/8")
            if active_strategies == 0:
                print(f"💤 Market is quiet - all strategies neutral")
            elif active_strategies < 3:
                print(f"📊 Low activity - waiting for confluence")
            else:
                print(f"🔥 Good activity - signal may come soon!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🕐 Test started at {datetime.now().strftime('%H:%M:%S')}")
    asyncio.run(quick_test())
    print(f"🏁 Test completed at {datetime.now().strftime('%H:%M:%S')}")