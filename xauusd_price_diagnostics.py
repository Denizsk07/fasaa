#!/usr/bin/env python3
"""
XAUUSD Price Diagnostics - Analysiert warum der Preis falsch ist
Vergleicht alle Quellen mit dem echten Chart-Preis
"""

import sys
import os
from datetime import datetime
import requests
import yfinance as yf
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_price_sources():
    """Analysiert alle Preisquellen einzeln"""
    
    print("=" * 70)
    print("🔍 XAUUSD PRICE SOURCE ANALYSIS")
    print(f"Chart zeigt: $3,345.23 (FOREX.COM)")
    print(f"Bot meldet: $3,393.90 (Differenz: +$48.67)")
    print("=" * 70)
    
    # Erwarteter Preis basierend auf Chart
    chart_price = 3345.23
    tolerance = 10.0  # ±$10 Toleranz
    
    print(f"\n🎯 Target Range: ${chart_price - tolerance:.2f} - ${chart_price + tolerance:.2f}")
    print(f"⚠️  Problem: Bot price ${3393.90:.2f} ist außerhalb der Toleranz!\n")
    
    sources_results = []
    
    # 1. Yahoo Finance Tests
    print("📊 1. YAHOO FINANCE TESTS")
    print("-" * 40)
    
    yahoo_symbols = ['XAUUSD=X', 'GC=F', 'GOLD', 'IAU', 'GLD']
    
    for symbol in yahoo_symbols:
        try:
            print(f"Testing {symbol}...")
            ticker = yf.Ticker(symbol)
            
            # Info Method
            try:
                info = ticker.info
                if 'regularMarketPrice' in info:
                    price = float(info['regularMarketPrice'])
                    difference = price - chart_price
                    status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
                    
                    print(f"   Info: ${price:.2f} ({difference:+.2f}) {status}")
                    sources_results.append(('Yahoo ' + symbol + ' Info', price, difference))
            except:
                print(f"   Info: Failed")
            
            # History Method (Last Close)
            try:
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    difference = price - chart_price
                    status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
                    
                    print(f"   Hist: ${price:.2f} ({difference:+.2f}) {status}")
                    sources_results.append(('Yahoo ' + symbol + ' Hist', price, difference))
            except:
                print(f"   Hist: Failed")
                
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print()
    
    # 2. Direct API Tests
    print("🌐 2. DIRECT API TESTS")
    print("-" * 40)
    
    # Yahoo Finance Direct API
    try:
        print("Testing Yahoo Finance Direct API...")
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    price = float(result['meta']['regularMarketPrice'])
                    difference = price - chart_price
                    status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
                    
                    print(f"   API: ${price:.2f} ({difference:+.2f}) {status}")
                    sources_results.append(('Yahoo Direct API', price, difference))
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Investing.com Test
    try:
        print("\nTesting Investing.com...")
        url = "https://www.investing.com/currencies/xau-usd"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            html = response.text
            # Einfache Regex für den Preis
            import re
            match = re.search(r'"last":"([0-9,]+\.?[0-9]*)"', html)
            if match:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)
                difference = price - chart_price
                status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
                
                print(f"   Scrape: ${price:.2f} ({difference:+.2f}) {status}")
                sources_results.append(('Investing.com', price, difference))
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print()
    
    # 3. Analysiere was dein Bot gerade verwendet
    print("🤖 3. BOT SOURCE ANALYSIS")
    print("-" * 40)
    
    try:
        from trading.data_manager import DataManager
        dm = DataManager()
        
        print("Testing current bot data manager...")
        
        # Health Check
        health = dm.health_check()
        current_price = health.get('current_price')
        active_source = health.get('active_source', 'unknown')
        
        if current_price:
            difference = current_price - chart_price
            status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
            
            print(f"   Bot Price: ${current_price:.2f} ({difference:+.2f}) {status}")
            print(f"   Bot Source: {active_source}")
            sources_results.append(('Bot Current', current_price, difference))
        
        # Teste einzelne Bot-Quellen
        if hasattr(dm, '_fetch_from_source'):
            print("\n   Testing individual bot sources:")
            for source in ['yahoo_finance_live', 'investing_com_api', 'coincodx_api']:
                try:
                    price = dm._fetch_from_source(source)
                    if price:
                        difference = price - chart_price
                        status = "✅ GOOD" if abs(difference) <= tolerance else "❌ BAD"
                        print(f"     {source}: ${price:.2f} ({difference:+.2f}) {status}")
                        sources_results.append((f'Bot {source}', price, difference))
                except:
                    print(f"     {source}: Failed")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 4. Zusammenfassung
    print("\n📋 4. SUMMARY & DIAGNOSIS")
    print("=" * 50)
    
    if sources_results:
        # Sortiere nach Genauigkeit
        sources_results.sort(key=lambda x: abs(x[2]))  # Nach Differenz sortieren
        
        print("🏆 BEST SOURCES (closest to chart price):")
        for i, (source, price, diff) in enumerate(sources_results[:5]):
            status = "✅" if abs(diff) <= tolerance else "❌"
            print(f"   {i+1}. {source}: ${price:.2f} ({diff:+.2f}) {status}")
        
        print(f"\n❌ WORST SOURCES (furthest from chart price):")
        for i, (source, price, diff) in enumerate(sources_results[-3:]):
            print(f"   {source}: ${price:.2f} ({diff:+.2f})")
        
        # Analyse des Problems
        print(f"\n🔍 PROBLEM ANALYSIS:")
        
        bot_sources = [r for r in sources_results if 'Bot' in r[0]]
        if bot_sources:
            worst_bot = max(bot_sources, key=lambda x: abs(x[2]))
            print(f"   Bot verwendet: {worst_bot[0]}")
            print(f"   Bot Preis: ${worst_bot[1]:.2f}")
            print(f"   Differenz: {worst_bot[2]:+.2f}")
            
            if abs(worst_bot[2]) > tolerance:
                print(f"   ⚠️  Bot-Quelle ist ungenau!")
                
                # Finde beste alternative Quelle
                non_bot = [r for r in sources_results if 'Bot' not in r[0]]
                if non_bot:
                    best_alt = min(non_bot, key=lambda x: abs(x[2]))
                    print(f"   💡 Bessere Alternative: {best_alt[0]} (${best_alt[1]:.2f})")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        # Empfehlungen basierend auf Analyse
        accurate_sources = [r for r in sources_results if abs(r[2]) <= tolerance]
        
        if accurate_sources:
            print(f"   ✅ {len(accurate_sources)} genaue Quellen gefunden")
            best_source = min(accurate_sources, key=lambda x: abs(x[2]))
            print(f"   🎯 Beste Quelle: {best_source[0]} (${best_source[1]:.2f})")
            
            if 'Yahoo' in best_source[0]:
                symbol = best_source[0].split()[1] if len(best_source[0].split()) > 1 else 'XAUUSD=X'
                print(f"   🔧 Bot sollte verwenden: {symbol}")
            
        else:
            print(f"   ❌ Keine genauen Quellen gefunden!")
            print(f"   🔧 Möglicherweise sind alle APIs aktuell ungenau")
            print(f"   📊 Chart-Preis ${chart_price:.2f} könnte der korrekteste sein")
        
        # Spread-Analyse
        if len(sources_results) > 1:
            prices = [r[1] for r in sources_results]
            spread = max(prices) - min(prices)
            print(f"   📏 Spread zwischen Quellen: ${spread:.2f}")
            
            if spread > 20:
                print(f"   ⚠️  Großer Spread! Verschiedene Broker/Märkte")
            
    else:
        print("❌ Keine Preisquellen funktionieren!")
    
    print(f"\n🕐 Analyse abgeschlossen: {datetime.now().strftime('%H:%M:%S')}")
    
    return sources_results

def recommend_fix(sources_results):
    """Empfiehlt konkrete Lösung"""
    
    print(f"\n🛠️  KONKRETE LÖSUNG")
    print("=" * 30)
    
    chart_price = 3345.23
    tolerance = 10.0
    
    # Finde beste Quelle
    accurate_sources = [r for r in sources_results if abs(r[2]) <= tolerance]
    
    if accurate_sources:
        best_source = min(accurate_sources, key=lambda x: abs(x[2]))
        
        print(f"1. Ändere Bot zur besten Quelle:")
        print(f"   Source: {best_source[0]}")
        print(f"   Price: ${best_source[1]:.2f}")
        print(f"   Accuracy: {best_source[2]:+.2f}")
        
        # Code-Empfehlung
        if 'Yahoo' in best_source[0] and 'XAUUSD' in best_source[0]:
            print(f"\n2. Code-Änderung in data_manager.py:")
            print(f"   Priorität auf 'XAUUSD=X' setzen")
            print(f"   Andere Yahoo-Symbole als Backup")
        elif 'Yahoo' in best_source[0] and 'GC=F' in best_source[0]:
            print(f"\n2. Code-Änderung in data_manager.py:")
            print(f"   'GC=F' (Gold Futures) als primäre Quelle")
        elif 'Investing' in best_source[0]:
            print(f"\n2. Code-Änderung in data_manager.py:")
            print(f"   Investing.com Scraping verbessern")
            print(f"   Als primäre Quelle setzen")
    
    else:
        print(f"❌ Keine genaue Quelle gefunden!")
        print(f"🔧 Mögliche Lösungen:")
        print(f"   1. Broker-spezifische API verwenden (FOREX.COM)")
        print(f"   2. Mehrere Quellen mitteln")
        print(f"   3. Chart-Preis als Referenz nehmen")

if __name__ == "__main__":
    try:
        print(f"🔍 Starting XAUUSD price diagnosis...")
        sources_results = analyze_price_sources()
        recommend_fix(sources_results)
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Analysis interrupted")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()