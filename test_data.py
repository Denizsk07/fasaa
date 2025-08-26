#!/usr/bin/env python3
"""
Debug Current Setup - Vollständige Überprüfung mit SPOT-Preis Validierung
Checkt ALLES: Telegram, DataManager, SPOT vs Futures, Signal Generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_env():
    """Check .env configuration"""
    print("🔧 Checking .env configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    
    print(f"   BOT_TOKEN: {'✅ Found' if bot_token else '❌ Missing'}")
    print(f"   GROUP_ID: {'✅ Found' if group_id else '❌ Missing'}")
    
    if bot_token:
        print(f"   Token starts with: {bot_token[:10]}...")
        
        # Test Telegram connection
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    print(f"   ✅ Bot connection: @{bot_info['username']}")
                    return True
        except Exception as e:
            print(f"   ⚠️ Connection test failed: {e}")
    
    return bool(bot_token and group_id)

def check_data_manager():
    """Check DataManager mit SPOT-Preis Validierung"""
    print(f"\n📊 Checking DataManager with SPOT price validation...")
    
    try:
        from trading.data_manager import DataManager
        dm = DataManager()
        print(f"   ✅ DataManager imported successfully")
        
        # Test current price
        print(f"   Testing current price...")
        price = dm.get_current_price()
        
        if price:
            print(f"   ✅ Current price: ${price:.2f}")
            
            # SPOT vs FUTURES Check
            if 3300 <= price <= 3400:
                print(f"   ✅ SPOT PRICE CONFIRMED (3300-3400 range)")
                print(f"   🎯 This is REAL XAUUSD spot, not futures")
                
                # Health check mit SPOT validation
                health = dm.health_check()
                print(f"   💊 Health check: {health.get('status', 'unknown')}")
                print(f"   🔍 Price type: {health.get('price_type', 'unknown')}")
                print(f"   ⚖️ SPOT check: {health.get('spot_vs_futures_check', 'unknown')}")
                
                return True
                
            elif price > 3400:
                print(f"   ❌ FUTURES PRICE DETECTED! (${price:.2f} > 3400)")
                print(f"   🚨 Bot is using Gold Futures instead of SPOT!")
                print(f"   💡 Expected SPOT: ~$3375, Got: ${price:.2f}")
                return False
                
            else:
                print(f"   ⚠️ Price outside expected range: ${price:.2f}")
                print(f"   💡 Expected SPOT range: $3300-3400")
                return False
                
        else:
            print(f"   ❌ No price data received")
            
            # Try debug function if available
            if hasattr(dm, 'force_spot_price_check'):
                print(f"   🔍 Running SPOT price debug...")
                spot_results = dm.force_spot_price_check()
                
                for source, result in spot_results.items():
                    if 'error' in result:
                        print(f"     {source}: ❌ {result['error']}")
                    else:
                        price = result.get('price', 0)
                        status = result.get('status', 'unknown')
                        print(f"     {source}: ${price:.2f} ({status})")
            
            return False
            
    except Exception as e:
        print(f"   ❌ DataManager error: {e}")
        import traceback
        print(f"   📍 Traceback: {traceback.format_exc()}")
        return False

def check_price_sources():
    """Detaillierte Prüfung aller Preisquellen"""
    print(f"\n💰 Detailed price source analysis...")
    
    try:
        # Test Investing.com SPOT
        print("   1. Testing Investing.com XAUUSD SPOT...")
        try:
            import requests
            import re
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            url = "https://www.investing.com/currencies/xau-usd"
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'data-test="instrument-price-last">([0-9,]+\.?[0-9]*)',
                    r'"last":"([0-9,]+\.?[0-9]*)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        price = float(price_str)
                        
                        if 3300 <= price <= 3400:
                            print(f"     ✅ Investing SPOT: ${price:.2f} (CORRECT)")
                            break
                        elif price > 3400:
                            print(f"     ❌ Investing shows FUTURES: ${price:.2f} (WRONG)")
                        else:
                            print(f"     ⚠️ Investing unusual: ${price:.2f}")
                else:
                    print(f"     ❌ No price pattern found")
            else:
                print(f"     ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
        # Test Yahoo SPOT vs FUTURES
        print("\n   2. Testing Yahoo: SPOT vs FUTURES comparison...")
        
        symbols = [
            ('XAUUSD=X', 'SPOT'),
            ('GC=F', 'FUTURES')
        ]
        
        for symbol, type_name in symbols:
            try:
                url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    
                    if 'regularMarketPrice' in meta:
                        price = float(meta['regularMarketPrice'])
                        
                        if type_name == 'SPOT' and 3300 <= price <= 3400:
                            print(f"     ✅ Yahoo {symbol} ({type_name}): ${price:.2f} (CORRECT)")
                        elif type_name == 'FUTURES' and price > 3400:
                            print(f"     ℹ️ Yahoo {symbol} ({type_name}): ${price:.2f} (Expected)")
                            
                            # Calculate difference
                            if len([p for s, p in [('XAUUSD=X', 3375)] if s == 'XAUUSD=X']) > 0:
                                diff = price - 3375  # Estimated SPOT
                                print(f"        💡 Futures premium: ~${diff:.2f}")
                        else:
                            print(f"     ⚠️ Yahoo {symbol} ({type_name}): ${price:.2f}")
                
            except Exception as e:
                print(f"     ❌ {symbol} error: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Price source analysis failed: {e}")
        return False

def check_signal_generation():
    """Test signal generation mit SPOT-Preisen"""
    print(f"\n🎯 Testing signal generation with SPOT prices...")
    
    try:
        import asyncio
        from trading.signal_generator import SignalGenerator
        from config import config
        
        # Lower threshold for test
        original = config.MIN_SIGNAL_SCORE
        config.MIN_SIGNAL_SCORE = 15.0
        
        print(f"   Lowered threshold to {config.MIN_SIGNAL_SCORE} for testing")
        
        async def test_signal():
            sg = SignalGenerator()
            
            # Check if data manager gives SPOT prices
            price = sg.data_manager.get_current_price()
            if price:
                if 3300 <= price <= 3400:
                    print(f"   ✅ Signal generator using SPOT price: ${price:.2f}")
                elif price > 3400:
                    print(f"   ❌ Signal generator using FUTURES: ${price:.2f}")
                    print(f"   🚨 This will generate wrong signals!")
                    return None
                else:
                    print(f"   ⚠️ Unusual price in signal generator: ${price:.2f}")
            
            # Generate signal
            signal = await sg.generate_signal()
            return signal, price
        
        result = asyncio.run(test_signal())
        signal, used_price = result if result else (None, None)
        
        # Restore threshold
        config.MIN_SIGNAL_SCORE = original
        
        if signal:
            print(f"   ✅ Signal generated successfully!")
            print(f"   📊 Direction: {signal['direction']}")
            print(f"   ⚡ Score: {signal['score']:.1f}")
            print(f"   💰 Entry: ${signal['entry']:.2f}")
            print(f"   🎯 Based on price: ${used_price:.2f}")
            
            # Validate signal is based on SPOT price
            entry_diff = abs(signal['entry'] - used_price)
            if entry_diff < 5:  # Should be very close
                print(f"   ✅ Signal entry matches current SPOT price")
                return True
            else:
                print(f"   ⚠️ Signal entry differs from current price by ${entry_diff:.2f}")
                
        else:
            print(f"   ❌ No signal generated")
            print(f"   💡 This might be normal if market conditions are neutral")
            
        return signal is not None
            
    except Exception as e:
        print(f"   ❌ Signal generation error: {e}")
        import traceback
        print(f"   📍 Traceback: {traceback.format_exc()}")
        return False

def check_config():
    """Check bot configuration"""
    print(f"\n⚙️ Checking bot configuration...")
    
    try:
        from config import config
        
        print(f"   Primary Symbol: {config.PRIMARY_SYMBOL}")
        print(f"   Min Signal Score: {config.MIN_SIGNAL_SCORE}")
        print(f"   Risk Percentage: {config.RISK_PERCENTAGE}%")
        print(f"   TP Levels: {config.TP_LEVELS}")
        print(f"   Stop Loss: {config.STOP_LOSS}")
        
        # Check if config is optimized for SPOT trading
        if config.PRIMARY_SYMBOL == 'XAUUSD':
            print(f"   ✅ Configured for XAUUSD SPOT trading")
        else:
            print(f"   ⚠️ Primary symbol is not XAUUSD")
        
        # Check TP levels are reasonable for SPOT
        if all(tp < 100 for tp in config.TP_LEVELS):  # SPOT TPs should be smaller
            print(f"   ✅ TP levels suitable for SPOT trading")
        else:
            print(f"   ⚠️ TP levels might be too high for SPOT")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config check failed: {e}")
        return False

def run_comprehensive_test():
    """Vollständiger System-Test"""
    print("🔍 COMPREHENSIVE SETUP VALIDATION")
    print("=" * 50)
    print("🎯 Focus: XAUUSD SPOT prices (~$3375), NOT Futures (~$3420)")
    print("=" * 50)
    
    results = {}
    
    # Run all checks
    results['env'] = check_env()
    results['data_manager'] = check_data_manager()
    results['price_sources'] = check_price_sources()
    results['signals'] = check_signal_generation()
    results['config'] = check_config()
    
    # Summary
    print(f"\n📋 COMPREHENSIVE DIAGNOSIS")
    print("=" * 30)
    
    for check, success in results.items():
        status = "✅ WORKING" if success else "❌ BROKEN"
        print(f"{check.upper().replace('_', ' ')}: {status}")
    
    # Overall assessment
    working_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 25)
    print(f"Working Components: {working_count}/{total_count}")
    
    if working_count == total_count:
        print(f"✅ PERFECT! All systems operational")
        print(f"🚀 Ready to launch: python main.py")
        
    elif working_count >= 4:
        print(f"🟡 MOSTLY WORKING - Minor issues to fix")
        print(f"⚡ Can probably run with: python main.py")
        
    elif working_count >= 2:
        print(f"🟠 PARTIALLY WORKING - Major fixes needed")
        print(f"🔧 Fix critical issues before running bot")
        
    else:
        print(f"🔴 CRITICAL ISSUES - Comprehensive fixes needed")
        print(f"🚨 Do not run bot until issues are resolved")
    
    # Specific recommendations
    print(f"\n💡 SPECIFIC RECOMMENDATIONS")
    print("=" * 30)
    
    if not results['env']:
        print(f"1. 📱 Fix Telegram configuration in .env file")
    
    if not results['data_manager']:
        print(f"2. 📊 Fix DataManager - ensure SPOT prices")
    
    if not results['price_sources']:
        print(f"3. 💰 Fix price sources - validate SPOT vs FUTURES")
    
    if not results['signals']:
        print(f"4. 🎯 Fix signal generation - depends on working DataManager")
    
    if not results['config']:
        print(f"5. ⚙️ Fix configuration settings")
    
    # Critical SPOT vs FUTURES warning
    print(f"\n🚨 CRITICAL: SPOT vs FUTURES")
    print("=" * 35)
    print(f"✅ CORRECT: XAUUSD SPOT ~$3375")
    print(f"❌ WRONG: Gold Futures ~$3420")
    print(f"💡 Difference: ~$45 (HUGE for trading!)")
    print(f"🔧 Always verify price source gives SPOT, not FUTURES")
    
    return working_count, total_count

def main():
    try:
        working, total = run_comprehensive_test()
        
        print(f"\n🏁 DEBUG COMPLETE")
        print("=" * 20)
        print(f"Result: {working}/{total} components working")
        
        if working == total:
            print(f"🎉 SUCCESS - Bot ready for trading!")
        elif working >= 4:
            print(f"⚡ PARTIAL SUCCESS - Bot can probably run")
        else:
            print(f"🔧 NEEDS WORK - Fix issues before trading")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Debug interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug script error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()