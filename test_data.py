#!/usr/bin/env python3
"""
Quick Price Debug - Check warum Bot falschen Preis zeigt
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_price_issue():
    print("🔍 PRICE DEBUG")
    print("=" * 20)
    print("Bot shows: $3,373.23")
    print("Real price: $3,385.18") 
    print("Difference: -$11.95 (Bot too low)")
    print()
    
    try:
        from trading.data_manager import DataManager
        dm = DataManager()
        
        # Test current price method
        print("📊 Testing DataManager current price...")
        price = dm.get_current_price()
        print(f"   Bot price: ${price:.2f}")
        
        # Test health check
        health = dm.health_check()
        print(f"   Last update: {health.get('last_update_age_seconds', 'unknown')}s ago")
        print(f"   Active source: {health.get('active_source', 'unknown')}")
        
        # Test individual sources manually
        print(f"\n🔍 Testing individual sources:")
        
        # 1. Manual Investing.com test
        print(f"1. Testing Investing.com directly...")
        try:
            import requests
            import re
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            url = "https://www.investing.com/currencies/xau-usd"
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Try multiple patterns
                patterns = [
                    r'data-test="instrument-price-last">([0-9,]+\.?[0-9]*)',
                    r'"last":"([0-9,]+\.?[0-9]*)"',
                    r'<span[^>]*>([0-9,]+\.[0-9]+)</span>'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        manual_price = float(price_str)
                        print(f"   ✅ Investing.com: ${manual_price:.2f}")
                        
                        if abs(manual_price - 3385.18) < 5:
                            print(f"   🎯 MATCHES real price!")
                        else:
                            print(f"   ⚠️ Different from expected $3,385.18")
                        break
                else:
                    print(f"   ❌ No price found in HTML")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 2. Manual Yahoo test
        print(f"\n2. Testing Yahoo Finance directly...")
        try:
            import yfinance as yf
            
            ticker = yf.Ticker("XAUUSD=X")
            info = ticker.info
            
            if 'regularMarketPrice' in info:
                yahoo_price = float(info['regularMarketPrice'])
                print(f"   ✅ Yahoo XAUUSD=X: ${yahoo_price:.2f}")
                
                if abs(yahoo_price - 3385.18) < 5:
                    print(f"   🎯 MATCHES real price!")
                else:
                    print(f"   ⚠️ Different from expected")
            else:
                print(f"   ❌ No regularMarketPrice in Yahoo data")
                
        except Exception as e:
            print(f"   ❌ Yahoo error: {e}")
        
        # 3. Test your API keys
        print(f"\n3. Testing API keys...")
        
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        twelve_key = os.getenv('TWELVE_DATA_API_KEY', 'demo')
        
        print(f"   Alpha Vantage: {'Real key' if alpha_key != 'demo' else 'Demo key'}")
        print(f"   Twelve Data: {'Real key' if twelve_key != 'demo' else 'Demo key'}")
        
        if alpha_key != 'demo':
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': 'XAU',
                    'to_currency': 'USD',
                    'apikey': alpha_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate = data['Realtime Currency Exchange Rate']['5. Exchange Rate']
                    api_price = float(rate)
                    print(f"   ✅ Alpha Vantage API: ${api_price:.2f}")
                    
                    if abs(api_price - 3385.18) < 5:
                        print(f"   🎯 MATCHES real price!")
                else:
                    print(f"   ❌ Alpha Vantage error: {data.get('Note', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ Alpha Vantage error: {e}")
        
        return price
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return None

def recommend_fix():
    print(f"\n🔧 IMMEDIATE FIX:")
    print("=" * 15)
    print("The bot is probably using:")
    print("• Cached/old data")
    print("• Wrong API endpoint") 
    print("• Stale Yahoo Finance data")
    print()
    print("Quick fixes to try:")
    print("1. Restart bot (clears cache)")
    print("2. Use /price command to see current source")
    print("3. Check if bot uses real API keys")
    print()
    print("🎯 Expected: Bot should show ~$3,385.18")

if __name__ == "__main__":
    price = debug_price_issue()
    recommend_fix()
    
    if price:
        diff = abs(price - 3385.18)
        if diff < 2:
            print(f"✅ PRICE IS CORRECT")
        else:
            print(f"❌ PRICE IS WRONG - Difference: ${diff:.2f}")
    else:
        print(f"❌ COULD NOT GET PRICE")