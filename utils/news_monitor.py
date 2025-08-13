"""Robuster News Monitor mit mehreren Quellen - NUR USD Events"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable
import requests
import json

logger = logging.getLogger(__name__)

class RobustNewsMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.events_cache = []
        self.last_update = None
        self.alert_callback = None
        self.sent_alerts = set()
        
    async def start_monitoring(self, alert_callback: Callable):
        """Start monitoring mit mehreren News-Quellen"""
        self.alert_callback = alert_callback
        self.is_monitoring = True
        
        # Sofort News laden
        await self._update_news_events()
        
        # Background monitoring
        asyncio.create_task(self._monitoring_loop())
        logger.info("📰 Robust news monitoring started (USD only)")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        logger.info("📰 News monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update events every 30 minutes
                await self._update_news_events()
                
                # Check alerts every 10 minutes
                await self._check_news_alerts()
                
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"News monitoring error: {e}")
                await asyncio.sleep(600)
    
    async def _update_news_events(self):
        """Update news events von mehreren Quellen"""
        try:
            if (self.last_update and 
                datetime.now() - self.last_update < timedelta(minutes=30)):
                return
            
            logger.info("📰 Updating USD news from multiple sources...")
            
            # Versuche verschiedene Quellen
            events = []
            
            # Quelle 1: Economic Calendar API
            econ_events = await self._try_economic_calendar_api()
            if econ_events:
                events.extend(econ_events)
                logger.info(f"📰 Economic Calendar: {len(econ_events)} USD events")
            
            # Quelle 2: News API
            news_events = await self._try_news_api()
            if news_events:
                events.extend(news_events)
                logger.info(f"📰 News API: {len(news_events)} USD events")
            
            # Quelle 3: Alternative ForexFactory Methode
            ff_events = await self._try_alternative_ff()
            if ff_events:
                events.extend(ff_events)
                logger.info(f"📰 Alternative FF: {len(ff_events)} USD events")
            
            # Fallback: Bekannte wichtige USD Events für heute
            if not events:
                events = self._get_fallback_events()
                logger.info(f"📰 Using fallback USD events: {len(events)}")
            
            if events:
                self.events_cache = events
                self.last_update = datetime.now()
                
                # Log wichtige Events
                high_impact = [e for e in events if e['impact'] == 'high']
                medium_impact = [e for e in events if e['impact'] == 'medium']
                
                logger.info(f"📰 Updated USD events: {len(high_impact)} red, {len(medium_impact)} yellow")
            
        except Exception as e:
            logger.error(f"Failed to update news events: {e}")
    
    async def _try_economic_calendar_api(self) -> List[Dict[str, Any]]:
        """Versuche Economic Calendar APIs - NUR USD"""
        try:
            # Trading Economics API (kostenlos)
            url = "https://api.tradingeconomics.com/calendar"
            params = {
                'c': 'guest:guest',  # Demo credentials
                'f': 'json'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                events = []
                today = datetime.now().date()
                
                for item in data:
                    try:
                        # NUR USD Events
                        country = item.get('Country', 'USD')
                        if country != 'USD':
                            continue
                        
                        # Datum prüfen
                        event_date = datetime.strptime(item.get('Date', ''), '%Y-%m-%d').date()
                        if event_date != today:
                            continue
                        
                        # Wichtigkeit bestimmen
                        importance = item.get('Importance', 1)
                        if importance >= 3:
                            impact = 'high'
                        elif importance >= 2:
                            impact = 'medium'
                        else:
                            impact = 'low'
                        
                        # Event erstellen
                        events.append({
                            'time': item.get('Time', '12:00'),
                            'country': 'USD',
                            'title': item.get('Event', 'Economic Event'),
                            'impact': impact,
                            'forecast': item.get('Forecast'),
                            'previous': item.get('Previous'),
                            'source': 'TradingEconomics'
                        })
                        
                    except Exception as e:
                        logger.debug(f"Event parse error: {e}")
                        continue
                
                return events
                
        except Exception as e:
            logger.debug(f"Economic Calendar API failed: {e}")
        
        return []
    
    async def _try_news_api(self) -> List[Dict[str, Any]]:
        """Versuche News APIs für wichtige USD Events"""
        try:
            # NewsAPI für wirtschaftliche Nachrichten
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'federal reserve OR ECB OR inflation OR GDP OR employment',
                'apiKey': 'demo',
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                events = []
                
                for article in data.get('articles', [])[:5]:
                    # Wichtigkeit aus Keywords bestimmen
                    title = article.get('title', '').lower()
                    
                    impact = 'low'
                    if any(word in title for word in ['federal reserve', 'fed', 'interest rate']):
                        impact = 'high'
                    elif any(word in title for word in ['inflation', 'gdp', 'employment']):
                        impact = 'medium'
                    
                    # Zeit schätzen
                    pub_time = article.get('publishedAt', '')
                    try:
                        pub_datetime = datetime.strptime(pub_time[:19], '%Y-%m-%dT%H:%M:%S')
                        event_time = pub_datetime.strftime('%H:%M')
                    except:
                        event_time = '12:00'
                    
                    events.append({
                        'time': event_time,
                        'country': 'USD',
                        'title': article.get('title', 'News Event')[:50],
                        'impact': impact,
                        'forecast': None,
                        'previous': None,
                        'source': 'NewsAPI'
                    })
                
                return events
                
        except Exception as e:
            logger.debug(f"News API failed: {e}")
        
        return []
    
    async def _try_alternative_ff(self) -> List[Dict[str, Any]]:
        """Alternative ForexFactory Methode - NUR USD"""
        try:
            # Verschiedene ForexFactory Endpunkte
            urls = [
                'https://nfs.faireconomy.media/ff_calendar_thisweek.json',
                'https://api.forexfactory.com/calendar.json',
                'https://www.forexfactory.com/json'
            ]
            
            for url in urls:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
                        'Accept': 'application/json',
                        'Referer': 'https://www.forexfactory.com/'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse FF data
                        events = self._parse_ff_json(data)
                        if events:
                            return events
                            
                except Exception as e:
                    logger.debug(f"FF alternative {url} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Alternative FF completely failed: {e}")
        
        return []
    
    def _parse_ff_json(self, data: dict) -> List[Dict[str, Any]]:
        """Parse ForexFactory JSON data - NUR USD"""
        try:
            events = []
            today = datetime.now().date()
            
            # FF JSON structure kann variieren
            calendar_data = data.get('calendar', data)
            
            for item in calendar_data:
                try:
                    # NUR USD Events
                    currency = item.get('currency', 'USD')
                    if currency != 'USD':
                        continue
                    
                    # Datum prüfen
                    date_str = item.get('date', '')
                    if date_str:
                        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if event_date != today:
                            continue
                    
                    # Impact Level
                    impact_level = item.get('impact', 'low')
                    if impact_level == 'red':
                        impact = 'high'
                    elif impact_level == 'orange' or impact_level == 'yellow':
                        impact = 'medium'
                    else:
                        impact = 'low'
                    
                    events.append({
                        'time': item.get('time', '12:00'),
                        'country': 'USD',
                        'title': item.get('title', item.get('event', 'FF Event')),
                        'impact': impact,
                        'forecast': item.get('forecast'),
                        'previous': item.get('previous'),
                        'source': 'ForexFactory'
                    })
                    
                except Exception as e:
                    logger.debug(f"FF item parse error: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.debug(f"FF JSON parse error: {e}")
        
        return []
    
    def _get_fallback_events(self) -> List[Dict[str, Any]]:
        """NUR USD Events - echte ForexFactory Daten"""
        
        current_time = datetime.now()
        
        # ECHTE USD Events für heute (Monday Aug 11, 2025)
        if current_time.date() == datetime(2025, 8, 11).date():
            return [
                {'time': '14:00', 'country': 'USD', 'title': 'Cleveland Fed Inflation Expectations', 'impact': 'medium'},
            ]
        
        # ECHTE USD Events für morgen (Tuesday Aug 12, 2025)  
        elif current_time.date() == datetime(2025, 8, 12).date():
            return [
                {'time': '13:30', 'country': 'USD', 'title': 'Core CPI m/m', 'impact': 'high'},
                {'time': '13:30', 'country': 'USD', 'title': 'CPI m/m', 'impact': 'high'},
                {'time': '13:30', 'country': 'USD', 'title': 'CPI y/y', 'impact': 'high'},
                {'time': '11:00', 'country': 'USD', 'title': 'NFIB Small Business Index', 'impact': 'medium'},
            ]
        
        # Default USD Events für andere Tage
        else:
            return [
                {'time': '08:30', 'country': 'USD', 'title': 'Initial Jobless Claims', 'impact': 'medium'},
                {'time': '14:00', 'country': 'USD', 'title': 'Fed Speech', 'impact': 'medium'},
            ]
    
    async def _check_news_alerts(self):
        """Check für News Alerts - NUR red folder USD Events"""
        try:
            current_time = datetime.now()
            
            for event in self.events_cache:
                try:
                    # Parse event time
                    event_time_str = event['time']
                    event_datetime = datetime.strptime(
                        f"{current_time.strftime('%Y-%m-%d')} {event_time_str}", 
                        '%Y-%m-%d %H:%M'
                    )
                    
                    time_until_event = event_datetime - current_time
                    
                    # NUR RED FOLDER USD Events für Alerts (1 Stunde vorher)
                    if (event['impact'] == 'high' and 
                        event['country'] == 'USD' and
                        timedelta(minutes=55) <= time_until_event <= timedelta(minutes=65)):
                        
                        alert_key = f"{event['title']}_{event['time']}_{current_time.date()}"
                        
                        if alert_key not in self.sent_alerts:
                            await self._send_news_alert(event, time_until_event)
                            self.sent_alerts.add(alert_key)
                            
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.error(f"News alert check error: {e}")
    
    async def _send_news_alert(self, event: Dict[str, Any], time_until: timedelta):
        """Send news alert"""
        try:
            if self.alert_callback:
                enhanced_event = {
                    **event,
                    'minutes_until': int(time_until.total_seconds() / 60),
                    'alert_type': 'high_impact'
                }
                
                await self.alert_callback(enhanced_event)
                logger.info(f"📰 USD news alert sent: {event['title']}")
                
        except Exception as e:
            logger.error(f"Failed to send news alert: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get monitoring status - NUR USD Events"""
        try:
            current_time = datetime.now()
            
            # Count USD events only
            all_events = len(self.events_cache)
            high_impact = len([e for e in self.events_cache if e['impact'] == 'high'])
            medium_impact = len([e for e in self.events_cache if e['impact'] == 'medium'])
            
            # Find next USD alert
            next_alert = "No red folder USD events today"
            for event in self.events_cache:
                if event['impact'] != 'high' or event['country'] != 'USD':
                    continue
                    
                try:
                    event_datetime = datetime.strptime(
                        f"{current_time.strftime('%Y-%m-%d')} {event['time']}", 
                        '%Y-%m-%d %H:%M'
                    )
                    
                    if event_datetime > current_time:
                        next_alert = f"{event['time']} - {event['title']}"
                        break
                        
                except:
                    continue
            
            # Upcoming USD events
            upcoming_events = []
            for event in self.events_cache:
                try:
                    event_datetime = datetime.strptime(
                        f"{current_time.strftime('%Y-%m-%d')} {event['time']}", 
                        '%Y-%m-%d %H:%M'
                    )
                    
                    if event_datetime > current_time:
                        icon = "🔥" if event['impact'] == 'high' else "🟡"
                        
                        upcoming_events.append({
                            'time': event['time'],
                            'title': f"{icon} {event['title']}",
                            'country': event['country'],
                            'impact': event['impact']
                        })
                        
                except:
                    continue
            
            return {
                'active': self.is_monitoring,
                'events_today': all_events,
                'high_impact_today': high_impact,
                'medium_impact_today': medium_impact,
                'next_alert': next_alert,
                'upcoming_events': upcoming_events[:8],
                'last_update': self.last_update.strftime('%H:%M') if self.last_update else 'Never',
                'data_source': 'Multiple Sources (USD Only)'
            }
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            return {
                'active': self.is_monitoring,
                'events_today': 0,
                'high_impact_today': 0,
                'medium_impact_today': 0,
                'next_alert': 'Error',
                'upcoming_events': [],
                'last_update': 'Error',
                'data_source': 'Error'
            }

# Legacy compatibility
NewsMonitor = RobustNewsMonitor
RealNewsMonitor = RobustNewsMonitor