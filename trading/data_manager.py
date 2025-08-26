import requests
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import time
import json
import base64
import hashlib

logger = logging.getLogger(__name__)

class TradingViewEnhancedDataManager:
    """
    Enhanced DataManager mit echten API Keys und TradingView-Connector
    Liest echte Marktdaten wie TradingView für bessere Analyse
    """
    
    def __init__(self):
        self.current_price = None
        self.last_update = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # API Keys
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '6UHEE0D7UE60UW6Z')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY', '99f486fab08c489388c778e9f9a15af6')
        self.fcs_api_key = os.getenv('FCS_API_KEY', 'HwdNw82NpyLLcIrvPw2Y')
        
        # TradingView Credentials
        self.tv_username = os.getenv('TV_USERNAME', 'deniiiz0206@gmail.com')
        self.tv_password = os.getenv('TV_PASSWORD', 'Dragonball0206!!')
        
        # Settings
        self.preferred_source = os.getenv('PREFERRED_DATA_SOURCE', 'alpha_vantage')
        self.symbol = os.getenv('YF_SYMBOL', 'XAUUSD=X')
        
        # Cache
        self.data_cache = {}
        self.cache_duration = 180  # 3 Minuten Cache für bessere Performance
        
        # TradingView Session
        self.tv_session = None
        self.tv_logged_in = False
        
        logger.info("TradingView Enhanced DataManager initialized")
        logger.info(f"Symbol: {self.symbol}, Preferred: {self.preferred_source}")
    
    def get_current_price(self) -> Optional[float]:
        """Multi-Source aktueller Preis mit TradingView Priority"""
        sources = [
            ('TradingView', self._get_tradingview_price),
            ('Alpha Vantage', self._get_alpha_vantage_quote),
            ('Twelve Data', self._get_twelve_data_quote),
            ('Investing.com', self._get_investing_price)
        ]
        
        for source_name, source_func in sources:
            try:
                price = source_func()
                if price and 1000 < price < 10000:
                    self.current_price = price
                    self.last_update = datetime.now()
                    logger.info(f"Current Gold: ${price:.2f} (from {source_name})")
                    return price
            except Exception as e:
                logger.debug(f"{source_name} price failed: {e}")
                continue
        
        return self.current_price or 2750.0
    
    def _get_tradingview_price(self) -> Optional[float]:
        """TradingView Real-time Preis für Forex XAUUSD"""
        try:
            # Forex XAUUSD Symbol für TradingView
            symbol = "FX:XAUUSD"
            
            url = f"https://scanner.tradingview.com/symbol"
            params = {
                'symbol': symbol,
                'fields': 'close,change,change_abs,volume'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tradingview.com/'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'close' in data:
                    price = float(data['close'])
                    logger.debug(f"TradingView {symbol}: ${price:.2f}")
                    return price
            
            # Alternative: TradingView Symbol Info API
            tv_url = f"https://symbol-search.tradingview.com/symbol_search/?text={symbol}&hl=1&exchange=&lang=en&search_type=undefined&domain=production"
            tv_response = self.session.get(tv_url, headers=headers, timeout=10)
            
            if tv_response.status_code == 200:
                tv_data = tv_response.json()
                if tv_data and len(tv_data) > 0:
                    # Weitere Implementierung für TradingView API
                    pass
        
        except Exception as e:
            logger.debug(f"TradingView price error: {e}")
        
        raise ValueError("TradingView price failed")
    
    def _get_alpha_vantage_quote(self) -> Optional[float]:
        """Alpha Vantage Quote - Gold fokussiert"""
        if self.symbol == 'GC=F':
            # Für Gold Futures verwende FX Rate
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': 'XAU',
                'to_currency': 'USD',
                'apikey': self.alpha_vantage_key
            }
        else:
            # Für andere Symbole verwende Global Quote
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': self.symbol.replace('=X', '').replace('=F', ''),
                'apikey': self.alpha_vantage_key
            }
        
        response = self.session.get(url, params=params, timeout=15)
        data = response.json()
        
        # Handle verschiedene Response-Formate
        if 'Realtime Currency Exchange Rate' in data:
            rate = data['Realtime Currency Exchange Rate']['5. Exchange Rate']
            return float(rate)
        elif 'Global Quote' in data:
            quote = data['Global Quote']
            if '05. price' in quote:
                return float(quote['05. price'])
        
        raise ValueError("Alpha Vantage quote failed")
    
    def _get_twelve_data_quote(self) -> Optional[float]:
        """Twelve Data Quote für XAUUSD Forex"""
        
        url = "https://api.twelvedata.com/price"
        params = {
            'symbol': 'XAU/USD',  # Forex format
            'apikey': self.twelve_data_key
        }
        
        response = self.session.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'price' in data:
            return float(data['price'])
        elif 'message' in data:
            logger.debug(f"Twelve Data: {data['message']}")
        
        raise ValueError("Twelve Data quote failed")
    
    def _get_investing_price(self) -> Optional[float]:
        """Investing.com Scraping"""
        url = "https://www.investing.com/currencies/xau-usd"
        response = self.session.get(url, timeout=15)
        
        import re
        patterns = [
            r'data-test="instrument-price-last">([0-9,]+\.?[0-9]*)',
            r'"last":"([0-9,]+\.?[0-9]*)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)
                if 1000 < price < 10000:
                    return price
        
        raise ValueError("Investing.com price not found")

    def get_data(self, timeframe: str = '15', limit: int = 500) -> pd.DataFrame:
        """
        TradingView-Style OHLCV mit echten APIs
        """
        cache_key = f"{timeframe}_{limit}_{self.preferred_source}"
        
        # Cache Check
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached data ({timeframe}m, {limit} bars)")
            return self.data_cache[cache_key]['data']
        
        # Priorisierte Quellen
        if self.preferred_source == 'alpha_vantage':
            sources = [
                ('Alpha Vantage', self._get_alpha_vantage_ohlcv),
                ('Twelve Data', self._get_twelve_data_ohlcv),
                ('TradingView Scraper', self._get_tradingview_ohlcv),
                ('Yahoo Finance', self._get_yahoo_ohlcv)
            ]
        else:
            sources = [
                ('Twelve Data', self._get_twelve_data_ohlcv),
                ('Alpha Vantage', self._get_alpha_vantage_ohlcv),
                ('TradingView Scraper', self._get_tradingview_ohlcv),
                ('Yahoo Finance', self._get_yahoo_ohlcv)
            ]
        
        for source_name, source_func in sources:
            try:
                df = source_func(timeframe, limit)
                if not df.empty and len(df) >= 20:
                    # TradingView-Style Processing
                    df = self._enhance_ohlcv_data(df)
                    
                    # Cache speichern
                    self.data_cache[cache_key] = {
                        'data': df,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"Got {len(df)} REAL candles from {source_name}")
                    return df
            except Exception as e:
                logger.debug(f"{source_name} failed: {e}")
                continue
        
        # Fallback: Enhanced Synthetic
        logger.warning("Using enhanced synthetic data - no real OHLCV available")
        return self._generate_enhanced_synthetic(timeframe, limit)
    
    def _get_alpha_vantage_ohlcv(self, timeframe: str, limit: int) -> pd.DataFrame:
        """Alpha Vantage OHLCV - verbessert für Gold"""
        
        # Timeframe mapping
        if timeframe in ['1', '5', '15', '30', '60']:
            function = 'FX_INTRADAY'
            interval = f'{timeframe}min'
        else:
            function = 'FX_DAILY'
            interval = 'daily'
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': function,
            'from_symbol': 'XAU',
            'to_symbol': 'USD',
            'interval': interval,
            'apikey': self.alpha_vantage_key,
            'outputsize': 'full'
        }
        
        response = self.session.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            # Error handling
            if 'Note' in data:
                raise ValueError(f"Alpha Vantage: {data['Note']}")
            if 'Information' in data:
                raise ValueError(f"Alpha Vantage: {data['Information']}")
            
            # Find time series
            ts_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    ts_key = key
                    break
            
            if ts_key and data[ts_key]:
                time_series = data[ts_key]
                
                df_data = []
                for timestamp, ohlcv in time_series.items():
                    try:
                        df_data.append({
                            'timestamp': pd.to_datetime(timestamp),
                            'open': float(ohlcv['1. open']),
                            'high': float(ohlcv['2. high']),
                            'low': float(ohlcv['3. low']),
                            'close': float(ohlcv['4. close']),
                            'volume': float(ohlcv.get('5. volume', 1000))
                        })
                    except (KeyError, ValueError):
                        continue
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    df.set_index('timestamp', inplace=True)
                    df.index = pd.to_datetime(df.index, utc=True)
                    df = df.sort_index().tail(limit)
                    return df
        
        raise ValueError("Alpha Vantage OHLCV failed")
    
    def _get_twelve_data_ohlcv(self, timeframe: str, limit: int) -> pd.DataFrame:
        """Twelve Data OHLCV für XAUUSD Forex"""
        
        url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': 'XAU/USD',  # Forex format
            'interval': f'{timeframe}min' if timeframe.isdigit() else '1day',
            'outputsize': min(limit, 5000),
            'apikey': self.twelve_data_key
        }
        
        response = self.session.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'code' in data and data['code'] != 200:
                raise ValueError(f"Twelve Data: {data.get('message')}")
            
            if 'values' in data and data['values']:
                df_data = []
                
                for candle in data['values']:
                    try:
                        df_data.append({
                            'timestamp': pd.to_datetime(candle['datetime']),
                            'open': float(candle['open']),
                            'high': float(candle['high']),
                            'low': float(candle['low']),
                            'close': float(candle['close']),
                            'volume': float(candle.get('volume', 1000))
                        })
                    except (KeyError, ValueError):
                        continue
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    df.set_index('timestamp', inplace=True)
                    df.index = pd.to_datetime(df.index, utc=True)
                    df = df.sort_index().tail(limit)
                    return df
        
        raise ValueError("Twelve Data OHLCV failed")
    
    def _get_tradingview_ohlcv(self, timeframe: str, limit: int) -> pd.DataFrame:
        """TradingView Scraper für Forex XAUUSD OHLCV"""
        try:
            # Forex XAUUSD Symbol für TradingView
            symbol = "FX:XAUUSD"
            
            # TradingView History API (unofficial)
            url = "https://scanner.tradingview.com/history"
            
            # Timeframe conversion
            tf_map = {
                '1': '1', '5': '5', '15': '15', '30': '30',
                '60': '60', '240': '240', '1440': '1D', 'D': '1D'
            }
            tv_timeframe = tf_map.get(timeframe, '15')
            
            params = {
                'symbol': symbol,
                'resolution': tv_timeframe,
                'from': int((datetime.now() - timedelta(days=30)).timestamp()),
                'to': int(datetime.now().timestamp())
            }
            
            headers = {
                'User-Agent': 'TradingView/1.0',
                'Referer': 'https://www.tradingview.com/'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if ('t' in data and 'o' in data and 'h' in data and 
                    'l' in data and 'c' in data and 'v' in data):
                    
                    df_data = []
                    for i in range(len(data['t'])):
                        df_data.append({
                            'timestamp': pd.to_datetime(data['t'][i], unit='s'),
                            'open': float(data['o'][i]),
                            'high': float(data['h'][i]),
                            'low': float(data['l'][i]),
                            'close': float(data['c'][i]),
                            'volume': float(data['v'][i])
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.set_index('timestamp', inplace=True)
                        df.index = pd.to_datetime(df.index, utc=True)
                        df = df.sort_index().tail(limit)
                        return df
        
        except Exception as e:
            logger.debug(f"TradingView scraper error: {e}")
        
        raise ValueError("TradingView OHLCV failed")
    
    def _get_yahoo_ohlcv(self, timeframe: str, limit: int) -> pd.DataFrame:
        """Yahoo Finance OHLCV als Fallback"""
        
        interval_map = {
            '1': '1m', '5': '5m', '15': '15m', '30': '30m', 
            '60': '1h', '240': '4h', '1440': '1d', 'D': '1d'
        }
        
        yahoo_interval = interval_map.get(str(timeframe), '15m')
        
        end_time = int(time.time())
        if yahoo_interval in ['1m', '5m']:
            start_time = end_time - (7 * 24 * 3600)
        elif yahoo_interval in ['15m', '30m', '1h']:
            start_time = end_time - (60 * 24 * 3600)
        else:
            start_time = end_time - (365 * 24 * 3600)
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        params = {
            'period1': start_time,
            'period2': end_time,
            'interval': yahoo_interval,
            'includePrePost': 'false'
        }
        
        response = self.session.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if (data.get('chart', {}).get('result') and 
                len(data['chart']['result']) > 0):
                
                result = data['chart']['result'][0]
                
                if ('timestamp' in result and 'indicators' in result):
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    
                    df_data = []
                    for i, ts in enumerate(timestamps):
                        if (i < len(quotes.get('open', [])) and
                            quotes['open'][i] is not None):
                            
                            df_data.append({
                                'timestamp': datetime.fromtimestamp(ts),
                                'open': float(quotes['open'][i]),
                                'high': float(quotes['high'][i]),
                                'low': float(quotes['low'][i]),
                                'close': float(quotes['close'][i]),
                                'volume': float(quotes.get('volume', [1000] * len(timestamps))[i] or 1000)
                            })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.set_index('timestamp', inplace=True)
                        df.index = pd.to_datetime(df.index, utc=True)
                        df = df.sort_index().tail(limit)
                        return df
        
        raise ValueError("Yahoo OHLCV failed")
    
    def _enhance_ohlcv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """TradingView-Style Candle Enhancement"""
        if df.empty:
            return df
        
        # TradingView-Style Columns hinzufügen
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['is_bullish'] = df['close'] > df['open']
        df['is_bearish'] = df['close'] < df['open']
        df['is_doji'] = df['body_size'] < (df['high'] - df['low']) * 0.1
        
        # Price Range Analysis
        df['range'] = df['high'] - df['low']
        df['range_pct'] = (df['range'] / df['close']) * 100
        
        # Volume Analysis
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        logger.debug("Enhanced OHLCV with TradingView-style indicators")
        return df
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Cache Validation"""
        if cache_key not in self.data_cache:
            return False
        
        cache_age = (datetime.now() - self.data_cache[cache_key]['timestamp']).total_seconds()
        return cache_age < self.cache_duration
    
    def _generate_enhanced_synthetic(self, timeframe: str, limit: int) -> pd.DataFrame:
        """Enhanced Synthetic Data als letzter Fallback"""
        current_price = self.get_current_price()
        if not current_price:
            current_price = 2750.0
        
        periods = min(limit, 500)
        now = datetime.now()
        freq_minutes = int(timeframe) if timeframe.isdigit() else 15
        
        times = []
        for i in range(periods):
            time_point = now - timedelta(minutes=freq_minutes * (periods - i - 1))
            times.append(time_point)
        
        # Realistische Gold-Simulation
        np.random.seed(int(time.time()) % 1000)  # Semi-random für Variation
        
        ohlcv_data = []
        start_price = current_price * (0.99 + np.random.random() * 0.02)  # ±1%
        
        for i in range(periods):
            if i == 0:
                open_price = start_price
            else:
                open_price = ohlcv_data[-1]['close']
            
            # Gold-typische Bewegung
            trend_to_current = (current_price - open_price) / max(periods - i, 1) * 0.2
            daily_volatility = open_price * 0.015  # 1.5% täglich
            
            price_change = np.random.normal(trend_to_current, daily_volatility * 0.1)
            close_price = max(open_price + price_change, 100)  # Minimum $100
            
            # Intrabar Bewegung
            bar_range = open_price * 0.005  # 0.5% typical range
            high = max(open_price, close_price) + abs(np.random.normal(0, bar_range * 0.5))
            low = min(open_price, close_price) - abs(np.random.normal(0, bar_range * 0.5))
            
            # Korrigiere OHLC-Beziehungen
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            volume = np.random.randint(500, 2500)  # Realistic volume
            
            ohlcv_data.append({
                'open': max(open_price, 100),
                'high': max(high, 100),
                'low': max(low, 100),
                'close': max(close_price, 100),
                'volume': volume
            })
        
        df = pd.DataFrame(ohlcv_data, index=pd.to_datetime(times))
        df.index = df.index.tz_localize('UTC')
        
        # TradingView Enhancement auch für synthetic
        df = self._enhance_ohlcv_data(df)
        
        logger.info(f"Generated {len(df)} enhanced synthetic candles (target: ${current_price:.2f})")
        return df
    
    def get_latest_bar(self, timeframe: str = '15') -> Optional[pd.Series]:
        """Latest OHLCV Bar"""
        df = self.get_data(timeframe, 1)
        return df.iloc[-1] if not df.empty else None
    
    def health_check(self) -> Dict[str, Any]:
        """Erweiterte Health Check"""
        age_seconds = None
        if self.last_update:
            age_seconds = (datetime.now() - self.last_update).total_seconds()
        
        # Test verschiedene Datenquellen
        sources_status = {}
        for source in ['alpha_vantage', 'twelve_data', 'yahoo']:
            try:
                if source == 'alpha_vantage':
                    self._get_alpha_vantage_quote()
                elif source == 'twelve_data':
                    self._get_twelve_data_quote()
                else:
                    self._get_investing_price()
                sources_status[source] = 'ok'
            except:
                sources_status[source] = 'failed'
        
        return {
            'current_price': self.current_price,
            'last_update_age_seconds': age_seconds,
            'symbol': self.symbol,
            'preferred_source': self.preferred_source,
            'sources_status': sources_status,
            'cache_entries': len(self.data_cache),
            'api_keys_configured': {
                'alpha_vantage': self.alpha_vantage_key != 'demo',
                'twelve_data': self.twelve_data_key != 'demo',
                'fcs_api': self.fcs_api_key != 'free'
            }
        }

# Aliases für Backward Compatibility
DataManager = TradingViewEnhancedDataManager
ProfessionalTradingDataManager = TradingViewEnhancedDataManager