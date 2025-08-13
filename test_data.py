#!/usr/bin/env python3
"""
XAUUSD Data Test Script - Testet alle Datenquellen
Garantiert funktionierende XAUUSD Daten für deinen Trading Bot
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_robust_data_manager():
    """Testet den robusten Data Manager"""
    
    print("=" * 60)
    print("🏆 ROBUST XAUUSD DATA MANAGER TEST")
    print("=" * 60)
    
    try:
        # Importiere den neuen Data Manager
        from trading.data_manager import RobustXAUUSDDataManager
        
        # Initialisiere
        print("🔧 Initializing Robust Data Manager...")
        dm = RobustXAUUSDDataManager()
        
        # Health Check
        print("\n🏥 HEALTH CHECK")
        print("-" * 30)
        health = dm.health_check()
        
        print(f"Status: {health['status']}")
        print(f"Source: {health['active_source']}")
        print(f"Symbol: {health['active_symbol']}")
        
        if health['current_price']:
            print(f"Current Price: ${health['current_price']:.2f}")
        
        if health['issues']:
            print("\nIssues:")
            for issue in health['issues']:
                print(f"  - {issue}")
        
        # Test einzelne Datenquellen
        print(f"\n🔍 TESTING DATA SOURCES")
        print("-" * 30)
        
        sources = [
            "yahoo_finance_direct",
            "yahoo_finance_alt", 
            "cryptocompare",
            "demo_realistic"
        ]
        
        working_sources = []
        
        for source in sources:
            try:
                price = dm._try_source(source)
                if price and dm._validate_price(price):
                    print(f"✅ {source}: ${price:.2f}")
                    working_sources.append(source)
                else:
                    print(f"❌ {source}: Failed")
            except Exception as e:
                print(f"❌ {source}: Error - {str(e)[:50]}")
        
        print(f"\nWorking sources: {len(working_sources)}/{len(sources)}")
        
        # Test Current Price
        print(f"\n💰 CURRENT PRICE TEST")
        print("-" * 30)
        
        current_price = dm.get_current_xauusd_price()
        if current_price:
            print(f"✅ Current Price: ${current_price:.2f}")
            print(f"Source: {dm.active_source}")
            
            # Validiere Preis-Bereich
            if 2000 <= current_price <= 3000:
                print("✅ Price is in realistic XAUUSD range")
            elif 150 <= current_price <= 300:
                print("📊 ETF/derivative price detected")
            else:
                print(f"⚠️ Unusual price: ${current_price:.2f}")
        else:
            print("❌ Could not get current price")
        
        # Test Historical Data
        print(f"\n📊 HISTORICAL DATA TEST")
        print("-" * 30)
        
        timeframes = ['15', '30', '60']
        success_count = 0
        
        for tf in timeframes:
            print(f"\n🕐 Testing {tf}-minute data:")
            
            try:
                df = dm.get_real_xauusd_data(tf, 100)
                
                if df is not None and not df.empty:
                    success_count += 1
                    
                    print(f"   ✅ Success: {len(df)} bars")
                    print(f"   💰 Latest: ${df['close'].iloc[-1]:.2f}")
                    print(f"   📈 Range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                    
                    # Data quality checks
                    price_std = df['close'].std()
                    if price_std > 0:
                        print(f"   ✅ Price variation: {price_std:.2f}")
                    else:
                        print(f"   ⚠️ No price variation")
                    
                    # Volume check
                    if 'volume' in df.columns:
                        avg_volume = df['volume'].mean()
                        print(f"   📊 Avg volume: {avg_volume:.0f}")
                    
                else:
                    print(f"   ❌ No data returned")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Market Status
        print(f"\n🏪 MARKET STATUS")
        print("-" * 30)
        
        status = dm.get_market_status()
        for key, value in status.items():
            print(f"{key}: {value}")
        
        # Summary
        print(f"\n📋 SUMMARY")
        print("=" * 30)
        
        if health['status'] == 'HEALTHY':
            print("🎉 STATUS: EXCELLENT - Real XAUUSD data working!")
        elif health['status'] == 'DEMO':
            print("🎭 STATUS: DEMO MODE - Using realistic simulated data")
        elif health['status'] == 'DEGRADED':
            print("⚠️ STATUS: DEGRADED - Limited functionality")
        else:
            print("❌ STATUS: CRITICAL - System needs attention")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if working_sources:
            print(f"✅ {len(working_sources)} data sources working")
            
            if 'yahoo_finance_direct' in working_sources:
                print("🚀 Yahoo Finance working - best quality data")
            elif 'cryptocompare' in working_sources:
                print("📊 CryptoCompare working - good alternative")
            elif 'demo_realistic' in working_sources:
                print("🎭 Demo mode - good for testing strategies")
        
        if success_count >= 2:
            print("✅ Trading bot ready - multiple timeframes working")
        elif success_count >= 1:
            print("📊 Partial functionality - can trade on available timeframes")
        else:
            print("⚠️ Limited data - check network connection")
        
        # Trading Bot Compatibility
        print(f"\n🤖 TRADING BOT COMPATIBILITY")
        print("-" * 30)
        
        if current_price and success_count > 0:
            print("✅ Compatible with signal generation")
            print("✅ Ready for automated trading")
            
            if health['status'] == 'HEALTHY':
                print("🚀 LIVE TRADING READY")
            else:
                print("🎭 DEMO TRADING READY")
        else:
            print("⚠️ Limited compatibility")
        
        return {
            'status': health['status'],
            'working_sources': len(working_sources),
            'current_price': current_price,
            'timeframes_working': success_count,
            'ready_for_trading': current_price is not None and success_count > 0
        }
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure the RobustXAUUSDDataManager is in your trading/data_manager.py")
        return None
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return None

def test_integration_with_bot():
    """Testet Integration mit dem Trading Bot"""
    
    print(f"\n🔧 INTEGRATION TEST")
    print("-" * 30)
    
    try:
        # Test ob der Data Manager mit dem Bot kompatibel ist
        from trading.data_manager import DataManager
        
        dm = DataManager()
        
        # Test legacy methods
        price = dm.get_current_price()
        data = dm.get_data('15', 50)
        
        if price and data is not None:
            print("✅ Legacy methods working")
            print(f"✅ Price: ${price:.2f}")
            print(f"✅ Data: {len(data)} bars")
            
            # Test mit Signal Generator
            try:
                from trading.signal_generator import SignalGenerator
                sg = SignalGenerator()
                print("✅ Signal Generator can import DataManager")
            except:
                print("⚠️ Signal Generator import issue")
            
            return True
        else:
            print("❌ Legacy methods not working")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    """Main test runner"""
    
    print(f"🕐 Test started at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Main test
        results = test_robust_data_manager()
        
        if results:
            # Integration test
            integration_ok = test_integration_with_bot()
            
            # Final verdict
            print(f"\n🎯 FINAL VERDICT")
            print("=" * 40)
            
            if results['ready_for_trading']:
                if results['status'] == 'HEALTHY':
                    print("🚀 READY FOR LIVE TRADING!")
                    print("✅ Real XAUUSD data available")
                elif results['status'] == 'DEMO':
                    print("🎭 READY FOR DEMO TRADING!")
                    print("✅ Realistic simulated data")
                else:
                    print("📊 PARTIALLY READY")
                    print("⚠️ Limited data sources")
                
                print(f"💰 Current Price: ${results['current_price']:.2f}")
                print(f"📊 Working Sources: {results['working_sources']}")
                print(f"⏰ Timeframes: {results['timeframes_working']}/3")
                
                if integration_ok:
                    print("✅ Bot integration: OK")
                else:
                    print("⚠️ Bot integration: Issues detected")
                
                print(f"\n🤖 NEXT STEPS:")
                if results['status'] == 'HEALTHY':
                    print("1. Start your trading bot: python main.py")
                    print("2. Monitor Telegram for signals")
                    print("3. Check logs for performance")
                else:
                    print("1. Trading bot will work in demo mode")
                    print("2. Try again later for real data")
                    print("3. Check internet connection")
                
            else:
                print("❌ NOT READY FOR TRADING")
                print("🔧 Issues need to be resolved first")
                
                print(f"\n🛠️ TROUBLESHOOTING:")
                print("1. Check internet connection")
                print("2. Try running test again")
                print("3. Contact support if issues persist")
        
        else:
            print("❌ CRITICAL: Data Manager test failed")
            
        print(f"\n🏁 Test completed at {datetime.now().strftime('%H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("Check your Python environment and try again")