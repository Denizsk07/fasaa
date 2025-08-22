# -*- coding: utf-8 -*-
"""
Data Manager – REAL XAUUSD via TradingView (drop-in replacement)
===============================================================

Ziel:
- 100% echte Spot-Daten (TradingView Bars) für XAUUSD liefern
- API kompatibel zu typischen Bots: `get_data`, `get_current_price`, `get_latest_bar`,
  Live-Polling (start/stop), In-Memory-Cache, optional CSV-Persistenz
- Saubere Logs + Health-Check, Resampling, Timeframe-Mapping

Primäre Feeds (automatisches Fallback):
1) TVC:GOLD (TradingView Composite Spot Index, entspricht Standard-TV-Chart)
2) FX_IDC:XAUUSD (FX-Composite)
3) FOREXCOM:XAUUSD (CFD-Feed)

Benötigt: `pip install tvdatafeed==2.1.0 pandas numpy python-dotenv`

Hinweis: tvDatafeed kann ohne Login im Gastmodus für Bars funktionieren.
Für bessere Stabilität sind Credentials möglich (ENV: TV_USERNAME, TV_PASSWORD).
"""
from __future__ import annotations

import os
import time
import json
import math
import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List, Callable, Iterable

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# =============== TradingView Client ======================
try:
    from tvDatafeed import TvDatafeed, Interval
    _TV_OK = True
except Exception as _e:  # pragma: no cover
    TvDatafeed = None
    Interval = None
    _TV_OK = False

# ================== Logging ==============================
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ================== Timeframes ===========================
# Einheitliche Eingaben wie im Projekt: '1','3','5','15','30','60','120','240','D'
_INTERVAL_MAP = {
    '1':  ('1m', 'in_1_minute'),
    '3':  ('3m', 'in_3_minute'),
    '5':  ('5m', 'in_5_minute'),
    '15': ('15m','in_15_minute'),
    '30': ('30m','in_30_minute'),
    '60': ('1h', 'in_1_hour'),
    '120':('2h', 'in_2_hour'),
    '240':('4h', 'in_4_hour'),
    'D':  ('1D', 'in_daily'),
}

# Für Resampling
_RESAMPLE_RULE = {
    '1':  '1T',
    '3':  '3T',
    '5':  '5T',
    '15': '15T',
    '30': '30T',
    '60': '60T',
    '120':'120T',
    '240':'240T',
    'D':  '1D',
}

# Reihenfolge der Quellen, wir versuchen nacheinander
_TV_SYMBOLS: List[Tuple[str,str]] = [
    ('TVC', 'GOLD'),
    ('FX_IDC', 'XAUUSD'),
    ('FOREXCOM', 'XAUUSD'),
]

# ================== Dataklassen ==========================
@dataclass
class SourceState:
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    last_ok: Optional[datetime] = None
    last_err: Optional[str] = None

@dataclass
class LiveLoop:
    thread: Optional[threading.Thread] = None
    stop_flag: threading.Event = field(default_factory=threading.Event)
    is_running: bool = False

# ================== DataManager ==========================
class DataManager:
    """
    Liefert echte OHLCV-Daten & Preisupdates für XAUUSD über TradingView.

    Öffentliche API (stabil):
    - get_data(timeframe: str='15', limit: int=500, start: datetime|None=None, end: datetime|None=None) -> pd.DataFrame
    - get_current_price() -> float|None
    - get_latest_bar(timeframe: str='15') -> pd.Series|None
    - start_live_updates(callback, timeframe='1', poll_seconds=5)
    - stop_live_updates()
    - health_check() -> dict
    - resample(df, timeframe_out) -> pd.DataFrame
    - to_csv(path, timeframe), from_csv(path) -> pd.DataFrame
    - save_cache(dir_path), load_cache(dir_path)
    """

    def __init__(self,
                 symbol_preference: List[Tuple[str,str]] | None = None,
                 default_symbol: Tuple[str,str] = ('TVC','GOLD')):
        load_dotenv()
        self.symbols = symbol_preference or list(_TV_SYMBOLS)
        # ensure default first
        if default_symbol in self.symbols:
            self.symbols.remove(default_symbol)
        self.symbols.insert(0, default_symbol)

        self._tv = None
        self.source_state = SourceState()
        self._cache: Dict[str, pd.DataFrame] = {}  # timeframe -> df
        self._live: LiveLoop = LiveLoop()
        self.current_price: Optional[float] = None
        self.last_price_at: Optional[datetime] = None

        self._init_tv_client()

    # -------------------- intern -------------------------
    def _init_tv_client(self):
        """Initialisiert tvDatafeed versionssicher.
        Unterstützt:
        - Alte Builds: TvDatafeed(username=..., password=...)
        - Mittel: TvDatafeed() ohne Argumente
        - Neue Builds: TvDatafeed(auto_login=True)
        Reihenfolge: Creds -> No-Arg -> Auto-Login
        """
        if not _TV_OK:
            logger.error("tvDatafeed nicht installiert. `pip install tvdatafeed` ")
            return
        user = os.getenv('TV_USERNAME')
        pwd  = os.getenv('TV_PASSWORD')

        # 1) Mit Credentials (falls vorhanden)
        if user and pwd:
            try:
                self._tv = TvDatafeed(username=user, password=pwd)
                logger.info("✅ TradingView Client mit Login initialisiert (Credentials).")
                return
            except TypeError as e:
                logger.debug(f"TvDatafeed creds-Init nicht unterstützt: {e}")
            except Exception as e:
                logger.warning(f"Login mit Credentials fehlgeschlagen: {e}")

        # 2) Ohne Argumente
        try:
            self._tv = TvDatafeed()
            logger.info("✅ TradingView Client initialisiert (no-arg).")
            return
        except TypeError as e:
            logger.debug(f"TvDatafeed no-arg-Init nicht unterstützt: {e}")
        except Exception as e:
            logger.debug(f"TvDatafeed no-arg-Init Fehler: {e}")

        # 3) Neues Schema: auto_login=True
        try:
            self._tv = TvDatafeed(auto_login=True)  # nur falls Version es unterstützt
            logger.info("✅ TradingView Client initialisiert (auto_login=True).")
            return
        except TypeError as e:
            logger.debug(f"TvDatafeed auto_login nicht unterstützt: {e}")
        except Exception as e:
            logger.debug(f"TvDatafeed auto_login Fehler: {e}")

        # Wenn alles fehlschlägt
        self._tv = None
        self.source_state.last_err = "tvDatafeed konnte nicht initialisiert werden (Version inkompatibel)."
        logger.error("Fehler beim Initialisieren von tvDatafeed – bitte Version prüfen: `pip show tvdatafeed` | Empfohlen: `pip install --upgrade tvdatafeed`")

    def _tv_interval(self, timeframe: str):
        if timeframe not in _INTERVAL_MAP:
            raise ValueError(f"Unsupported timeframe '{timeframe}'. Supported: {list(_INTERVAL_MAP)}")
        _, attr = _INTERVAL_MAP[timeframe]
        return getattr(Interval, attr)

    def _fetch_tv(self, exchange: str, symbol: str, timeframe: str, n_bars: int) -> pd.DataFrame:
        assert self._tv is not None, "tvDatafeed Client nicht verfügbar"
        tv_int = self._tv_interval(timeframe)
        df = self._tv.get_hist(symbol=symbol, exchange=exchange, interval=tv_int, n_bars=n_bars)
        if df is None or df.empty:
            raise RuntimeError("Empty dataframe")
        df = df.rename(columns=str.lower)
        df = df[['open','high','low','close','volume']].astype(float)
        # Index als UTC-Datetime (robust gegen already tz-aware)
        idx = pd.to_datetime(df.index)
        if getattr(idx, "tz", None) is None:
            df.index = idx.tz_localize('UTC', nonexistent='shift_forward', ambiguous='NaT')
        else:
            df.index = idx.tz_convert('UTC')
        # einfache Plausibilisierung
        df = df[(df[['open','high','low','close']]>0).all(axis=1)]
        if df.empty:
            raise RuntimeError("All invalid bars after filtering")
        return df

    def _update_cache(self, timeframe: str, df: pd.DataFrame):
        # Cache immer als vollständige, de-duplizierte, nach Zeit sortierte Serie halten
        if timeframe in self._cache and not self._cache[timeframe].empty:
            merged = pd.concat([self._cache[timeframe], df])
        else:
            merged = df.copy()
        merged = merged[~merged.index.duplicated(keep='last')].sort_index()
        self._cache[timeframe] = merged

    # -------------------- Public API ---------------------
    def get_data(self,
                 timeframe: str = '15',
                 limit: int = 500,
                 start: Optional[datetime] = None,
                 end: Optional[datetime] = None) -> pd.DataFrame:
        """Holt OHLCV-Bars für XAUUSD (echte TradingView-Daten).
        *timeframe*: '1','3','5','15','30','60','120','240','D'
        *limit*: Anzahl Bars (Obergrenze der API beachten)
        *start/end*: optionales Zeitfenster (UTC). Wenn gesetzt, wird nachträglich gefiltert.
        """
        if self._tv is None:
            raise RuntimeError("tvDatafeed Client nicht initialisiert")
        last_err: Optional[Exception] = None
        for exch, sym in self.symbols:
            try:
                df = self._fetch_tv(exch, sym, timeframe, limit)
                self.source_state.exchange = exch
                self.source_state.symbol = sym
                self.source_state.last_ok = datetime.utcnow()
                # Cache + Preis
                self._update_cache(timeframe, df)
                self.current_price = float(df['close'].iloc[-1])
                self.last_price_at = datetime.utcnow()
                # Optionales Zeitfenster
                if start or end:
                    df = df.copy()
                    if start:
                        df = df[df.index >= pd.Timestamp(start, tz='UTC')]
                    if end:
                        df = df[df.index <= pd.Timestamp(end, tz='UTC')]
                logger.info(f"✅ {len(df)} Bars @ {exch}:{sym} {timeframe}")
                return df
            except Exception as e:
                last_err = e
                self.source_state.last_err = f"{exch}:{sym} {e}"
                logger.debug(f"TV Fetch fail {exch}:{sym} {timeframe}: {e}")
                continue
        raise RuntimeError(f"TradingView Fetch failed (all sources). Last error: {last_err}")

    def get_current_price(self) -> Optional[float]:
        """Schneller Preis-Check: nimmt Close der neuesten 1m-Kerze."""
        try:
            df = self.get_data('1', limit=1)
            if not df.empty:
                price = float(df['close'].iloc[-1])
                self.current_price = price
                self.last_price_at = datetime.utcnow()
                return price
        except Exception as e:
            logger.warning(f"get_current_price fallback (cache) wegen: {e}")
        return self.current_price

    def get_latest_bar(self, timeframe: str = '15') -> Optional[pd.Series]:
        """Gibt die letzte Bar aus Cache zurück (holt sie ggf. frisch)."""
        if timeframe not in self._cache or self._cache[timeframe].empty:
            try:
                self.get_data(timeframe=timeframe, limit=2)
            except Exception as e:
                logger.warning(f"get_latest_bar konnte nicht aktualisieren: {e}")
        df = self._cache.get(timeframe)
        if df is None or df.empty:
            return None
        return df.iloc[-1]

    def start_live_updates(self,
                           callback: Callable[[pd.DataFrame], None],
                           timeframe: str = '1',
                           poll_seconds: int = 5,
                           limit: int = 200) -> None:
        """Einfaches Live-Polling: ruft periodisch `get_data` auf und liefert das
        komplette DataFrame an `callback(df)`.
        """
        if self._live.is_running:
            logger.info("Live-Loop läuft bereits.")
            return
        self._live.stop_flag.clear()

        def _loop():
            self._live.is_running = True
            try:
                while not self._live.stop_flag.is_set():
                    try:
                        df = self.get_data(timeframe=timeframe, limit=limit)
                        callback(df)
                    except Exception as e:
                        logger.warning(f"Live-Loop Fehler: {e}")
                    time.sleep(max(1, int(poll_seconds)))
            finally:
                self._live.is_running = False

        t = threading.Thread(target=_loop, name="DataManagerLive", daemon=True)
        self._live.thread = t
        t.start()
        logger.info(f"▶️ Live-Updates gestartet ({timeframe}, {poll_seconds}s)")

    def stop_live_updates(self):
        if not self._live.is_running:
            return
        self._live.stop_flag.set()
        if self._live.thread and self._live.thread.is_alive():
            self._live.thread.join(timeout=10)
        logger.info("⏹️ Live-Updates gestoppt")

    def health_check(self) -> Dict[str, Any]:
        age = None
        if self.last_price_at:
            age = (datetime.utcnow() - self.last_price_at).total_seconds()
        return {
            'active_exchange': self.source_state.exchange,
            'active_symbol': self.source_state.symbol,
            'last_ok_utc': self.source_state.last_ok.isoformat() if self.source_state.last_ok else None,
            'last_error': self.source_state.last_err,
            'price_age_seconds': age,
            'tv_client_ready': bool(self._tv is not None),
        }

    # ------------------ Utilities ------------------------
    def resample(self, df: pd.DataFrame, timeframe_out: str) -> pd.DataFrame:
        if timeframe_out not in _RESAMPLE_RULE:
            raise ValueError(f"Unsupported timeframe_out '{timeframe_out}'")
        rule = _RESAMPLE_RULE[timeframe_out]
        # sicherstellen, dass der Index DatetimeIndex und sortiert ist
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.copy()
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        o = df['open'].resample(rule).first()
        h = df['high'].resample(rule).max()
        l = df['low'].resample(rule).min()
        c = df['close'].resample(rule).last()
        v = df['volume'].resample(rule).sum()
        out = pd.concat([o, h, l, c, v], axis=1)
        out.columns = ['open', 'high', 'low', 'close', 'volume']
        out = out.dropna(how='any')
        return out

    def to_csv(self, path: str, timeframe: str = '15') -> str:
        df = self._cache.get(timeframe)
        if df is None or df.empty:
            df = self.get_data(timeframe=timeframe, limit=1000)
        df.to_csv(path, index=True)
        logger.info(f"💾 Cache {timeframe} -> {path} ({len(df)} Zeilen)")
        return path

    def from_csv(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        # als UTC interpretieren
        if getattr(df.index, "tz", None) is None:
            df.index = df.index.tz_localize('UTC')
        # Spaltennamen harmonisieren
        df = df.rename(columns=str.lower)[['open','high','low','close','volume']]
        return df

    def save_cache(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)
        for tf, df in self._cache.items():
            p = os.path.join(dir_path, f"cache_{tf}.csv")
            df.to_csv(p)
        meta = {
            'exchange': self.source_state.exchange,
            'symbol': self.source_state.symbol,
            'last_ok': self.source_state.last_ok.isoformat() if self.source_state.last_ok else None,
        }
        with open(os.path.join(dir_path, 'cache_meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Cache gespeichert in {dir_path}")

    def load_cache(self, dir_path: str) -> None:
        loaded = 0
        for tf in _RESAMPLE_RULE.keys():
            p = os.path.join(dir_path, f"cache_{tf}.csv")
            if os.path.exists(p):
                df = pd.read_csv(p, index_col=0, parse_dates=True)
                if getattr(df.index, "tz", None) is None:
                    df.index = df.index.tz_localize('UTC')
                df = df.rename(columns=str.lower)[['open','high','low','close','volume']]
                self._cache[tf] = df
                loaded += 1
        meta_p = os.path.join(dir_path, 'cache_meta.json')
        if os.path.exists(meta_p):
            try:
                with open(meta_p, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                self.source_state.exchange = meta.get('exchange')
                self.source_state.symbol = meta.get('symbol')
            except Exception:
                pass
        logger.info(f"📦 Cache geladen: {loaded} Timeframes")

# Für Rückwärtskompatibilität mit älteren Imports
ProfessionalTradingDataManager = DataManager
TradingViewDataManager = DataManager
MT5DataManager = DataManager
