# -*- coding: utf-8 -*-
"""
utils/news_monitor.py
=====================

Robuster, leiser News-/Kalender-Monitor für den XAUUSD-Bot.

Bereitgestellte Klassen (rückwärtskompatibel):
- NewsMonitor
- RealForexFactoryNewsMonitor  (Alias, gleiche API wie früher)
- DummyNewsMonitor             (immer deaktiviert, gibt [] zurück)

Public API (stabil):
    get_events(start=None, end=None, impact=None, symbols=None) -> List[dict]
    get_today_events(impact=None, symbols=None) -> List[dict]
    start_polling(callback, poll_seconds=None, impact=None, symbols=None) -> None
    stop_polling() -> None
    # Rückwärtskompatible Aliase:
    start_monitoring(callback=None, interval_seconds=None, impact=None, symbols=None) -> None
    stop_monitoring() -> None
    set_enabled(flag: bool) -> None
    health() -> dict

ENV-Konfig:
    NEWS_MONITOR_ENABLED=true|false   (default true)
    NEWS_SOURCE=forexfactory
    NEWS_POLL_SECONDS=300
    CALENDAR_LOG_LEVEL=WARNING        (INFO/DEBUG für Details)

Abhängigkeiten (optional fürs Scraping):
    pip install requests bs4 python-dateutil
"""

from __future__ import annotations

import os
import time
import logging
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta, timezone

# ---------- optionale Dependencies ----------
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

try:
    from dateutil import parser as du  # type: ignore
except Exception:  # pragma: no cover
    du = None  # type: ignore


# ======================= Logging =========================
LOG_LEVEL = os.getenv("CALENDAR_LOG_LEVEL", "WARNING").upper()
logger = logging.getLogger("news_monitor")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | news_monitor: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.WARNING))


# ======================= Dataklassen =====================
@dataclass
class EventItem:
    time: Optional[datetime]
    currency: str
    impact: str
    event: str
    actual: str = ""
    forecast: str = ""
    previous: str = ""
    source: str = "ForexFactory"


@dataclass
class PollLoop:
    thread: Optional[threading.Thread] = None
    stop_flag: threading.Event = field(default_factory=threading.Event)
    is_running: bool = False


# ======================= Kern-Implementierung ============

class NewsMonitor:
    """
    Leiser, robuster Kalender-/News-Monitor.
    """

    def __init__(self,
                 enabled: Optional[bool] = None,
                 source: Optional[str] = None,
                 poll_seconds: Optional[int] = None,
                 tz: timezone = timezone.utc):
        # Konfiguration
        if enabled is None:
            enabled = os.getenv("NEWS_MONITOR_ENABLED", "true").lower() in ("1", "true", "yes", "y")
        if source is None:
            source = os.getenv("NEWS_SOURCE", "forexfactory").lower()
        if poll_seconds is None:
            try:
                poll_seconds = int(os.getenv("NEWS_POLL_SECONDS", "300"))
            except Exception:
                poll_seconds = 300

        self.enabled: bool = bool(enabled)
        self.source: str = source
        self.poll_seconds: int = max(10, int(poll_seconds))
        self.tz = tz

        self._loop: PollLoop = PollLoop()
        self._last_ok: Optional[datetime] = None
        self._last_error: Optional[str] = None

        # HTTP-Session (nur falls requests verfügbar)
        self._session = None
        if requests is not None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; XAU-Bot/1.0; +https://example.local)"
            })

        if not self.enabled:
            logger.info("NewsMonitor ist deaktiviert (ENV NEWS_MONITOR_ENABLED=false).")
        else:
            logger.info(f"NewsMonitor aktiviert – Quelle: {self.source}, Poll: {self.poll_seconds}s")

    # ------------------------- Public API -------------------------
    def get_today_events(self,
                         impact: Optional[str] = None,
                         symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Events für heute (UTC 00:00 bis UTC 23:59:59).
        """
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return self.get_events(start=start, end=end, impact=impact, symbols=symbols)

    def get_events(self,
                   start: Optional[datetime] = None,
                   end: Optional[datetime] = None,
                   impact: Optional[str] = None,
                   symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Liefert Events im Zeitfenster [start, end]. Bei Fehlern: [] (silent).
        """
        if not self.enabled:
            return []

        try:
            if self.source == "forexfactory":
                items = self._fetch_forexfactory(start, end)
            else:
                items = []  # unbekannte Quelle – bewusst still

            items = self._filter(items, start, end, impact, symbols)
            self._last_ok = datetime.utcnow()
            self._last_error = None
            return [self._to_dict(ev) for ev in items]
        except Exception as e:
            self._last_error = str(e)
            logger.debug(f"get_events error: {e}")
            return []

    def start_polling(self,
                      callback: Callable[[List[Dict[str, Any]]], None],
                      poll_seconds: Optional[int] = None,
                      impact: Optional[str] = None,
                      symbols: Optional[List[str]] = None) -> None:
        """
        Startet einen leisen Polling-Loop. Bei Fehlern: wartet und versucht erneut.
        Der Callback bekommt `List[dict]` (Events).
        """
        if not self.enabled:
            logger.info("NewsMonitor ist deaktiviert – Polling wird nicht gestartet.")
            return
        if self._loop.is_running:
            logger.info("NewsMonitor: Polling läuft bereits.")
            return

        if poll_seconds is None:
            poll_seconds = self.poll_seconds
        poll_seconds = max(10, int(poll_seconds))

        self._loop.stop_flag.clear()

        def _runner():
            self._loop.is_running = True
            try:
                while not self._loop.stop_flag.is_set():
                    try:
                        data = self.get_today_events(impact=impact, symbols=symbols)
                        try:
                            callback(data)
                        except Exception as cb_ex:
                            logger.debug(f"Callback error: {cb_ex}")
                    except Exception as ex:
                        logger.debug(f"Polling error: {ex}")
                    finally:
                        time.sleep(poll_seconds)
            finally:
                self._loop.is_running = False

        t = threading.Thread(target=_runner, name="NewsMonitorLoop", daemon=True)
        self._loop.thread = t
        t.start()
        logger.info(f"NewsMonitor: Polling gestartet (alle {poll_seconds}s).")

    def stop_polling(self) -> None:
        if not self._loop.is_running:
            return
        self._loop.stop_flag.set()
        if self._loop.thread and self._loop.thread.is_alive():
            self._loop.thread.join(timeout=10)
        logger.info("NewsMonitor: Polling gestoppt.")

    # --------- Rückwärtskompatible Aliase (für deinen Bot) ---------
    def start_monitoring(self,
                         callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
                         interval_seconds: Optional[int] = None,
                         impact: Optional[str] = None,
                         symbols: Optional[List[str]] = None) -> None:
        """
        Alias für start_polling(). Manche ältere Bots rufen start_monitoring() auf.
        """
        if callback is None:
            def callback(_events: List[Dict[str, Any]]) -> None:
                # standardmäßig nichts tun; Bot bleibt leise
                return
        self.start_polling(callback=callback,
                           poll_seconds=interval_seconds,
                           impact=impact,
                           symbols=symbols)

    def stop_monitoring(self) -> None:
        """Alias für stop_polling()."""
        self.stop_polling()

    def set_enabled(self, flag: bool) -> None:
        self.enabled = bool(flag)
        logger.info(f"NewsMonitor enabled={self.enabled}")

    def health(self) -> Dict[str, Any]:
        age = None
        if self._last_ok:
            age = (datetime.utcnow() - self._last_ok).total_seconds()
        return {
            "enabled": self.enabled,
            "source": self.source,
            "last_ok_utc": self._last_ok.isoformat() if self._last_ok else None,
            "last_error": self._last_error,
            "polling": self._loop.is_running,
            "poll_interval": self.poll_seconds,
        }

    # ------------------------- Internal --------------------------
    def _fetch_forexfactory(self,
                            start: Optional[datetime],
                            end: Optional[datetime]) -> List[EventItem]:
        """
        Minimaler Scraper für ForexFactory.
        Bei fehlenden Dependencies/Fehlern: gibt [] zurück (silent).
        """
        if requests is None or BeautifulSoup is None or du is None:
            logger.debug("requests/bs4/dateutil nicht verfügbar – ForexFactory wird übersprungen.")
            return []

        url = "https://www.forexfactory.com/calendar"
        try:
            r = self._session.get(url, timeout=12) if self._session else requests.get(url, timeout=12)
            r.raise_for_status()
        except Exception as e:
            logger.debug(f"HTTP-Fehler ForexFactory: {e}")
            return []

        try:
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.select("tr.calendar__row")
            if not rows:
                rows = soup.select("tr.calendar_row")  # older markup

            items: List[EventItem] = []
            for row in rows or []:
                try:
                    t = row.select_one(".calendar__time") or row.select_one(".time")
                    c = row.select_one(".calendar__currency") or row.select_one(".currency")
                    i = row.select_one(".calendar__impact") or row.select_one(".impact")
                    e = row.select_one(".calendar__event") or row.select_one(".event")
                    a = row.select_one(".calendar__actual") or row.select_one(".actual")
                    f = row.select_one(".calendar__forecast") or row.select_one(".forecast")
                    p = row.select_one(".calendar__previous") or row.select_one(".previous")

                    time_str = (t.text or "").strip() if t else ""
                    cur = (c.text or "").strip() if c else ""
                    impact_txt = (i.text or "").strip() if i else ""
                    event_name = (e.text or "").strip() if e else ""
                    actual = (a.text or "").strip() if a else ""
                    forecast = (f.text or "").strip() if f else ""
                    previous = (p.text or "").strip() if p else ""

                    when = None
                    if time_str and du is not None:
                        try:
                            when = du.parse(time_str, fuzzy=True)
                            if when.tzinfo is None:
                                when = when.replace(tzinfo=timezone.utc)
                            else:
                                when = when.astimezone(timezone.utc)
                        except Exception:
                            when = None

                    items.append(EventItem(
                        time=when,
                        currency=cur,
                        impact=impact_txt,
                        event=event_name,
                        actual=actual,
                        forecast=forecast,
                        previous=previous,
                        source="ForexFactory"
                    ))
                except Exception as row_ex:
                    logger.debug(f"Row parse error: {row_ex}")
                    continue

            return items
        except Exception as parse_ex:
            logger.debug(f"Parse-Fehler ForexFactory: {parse_ex}")
            return []

    # ---- Helper ----
    def _filter(self,
                items: List[EventItem],
                start: Optional[datetime],
                end: Optional[datetime],
                impact: Optional[str],
                symbols: Optional[List[str]]) -> List[EventItem]:
        impact_norm = impact.lower() if isinstance(impact, str) else None
        sym_set = set([s.upper() for s in symbols]) if symbols else None

        out: List[EventItem] = []
        for ev in items:
            if start and ev.time and ev.time < self._to_utc(start):
                continue
            if end and ev.time and ev.time > self._to_utc(end):
                continue
            if impact_norm and self._norm_impact(ev.impact) != impact_norm:
                continue
            if sym_set and ev.currency and ev.currency.upper() not in sym_set:
                continue
            out.append(ev)
        return out

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _norm_impact(txt: str) -> str:
        t = (txt or "").strip().lower()
        if "high" in t or "rot" in t or "red" in t:
            return "high"
        if "medium" in t or "gelb" in t or "amber" in t or "orange" in t:
            return "medium"
        if "low" in t or "grün" in t or "green" in t:
            return "low"
        return t

    @staticmethod
    def _to_dict(ev: EventItem) -> Dict[str, Any]:
        return {
            "time": ev.time.isoformat() if isinstance(ev.time, datetime) else None,
            "currency": ev.currency,
            "impact": ev.impact,
            "event": ev.event,
            "actual": ev.actual,
            "forecast": ev.forecast,
            "previous": ev.previous,
            "source": ev.source,
        }


# ======================= Backward Compatibility ==========
class RealForexFactoryNewsMonitor(NewsMonitor):
    """
    Rückwärtskompatibler Name, damit bestehende Imports funktionieren:
        from utils.news_monitor import RealForexFactoryNewsMonitor
    """
    def __init__(self, *args, **kwargs):
        if "enabled" not in kwargs:
            kwargs["enabled"] = os.getenv("NEWS_MONITOR_ENABLED", "true").lower() in ("1","true","yes","y")
        if "source" not in kwargs:
            kwargs["source"] = "forexfactory"
        super().__init__(*args, **kwargs)


class DummyNewsMonitor(NewsMonitor):
    """Komplett stumm. Gibt stets [] zurück."""
    def __init__(self, *args, **kwargs):
        kwargs["enabled"] = False
        super().__init__(*args, **kwargs)

    def get_events(self, *a, **k) -> List[Dict[str, Any]]:  # type: ignore[override]
        return []

    def get_today_events(self, *a, **k) -> List[Dict[str, Any]]:  # type: ignore[override]
        return []


__all__ = [
    "NewsMonitor",
    "RealForexFactoryNewsMonitor",
    "DummyNewsMonitor",
]
