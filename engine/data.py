import pathlib
import threading
import time

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
RAW_CACHE = ROOT / "raw_prices.csv"
VOL_CACHE = ROOT / "volume.csv"

# In-memory cache so /risk, /liquidity and the what-if tab do not each hit
# Yahoo Finance again for the same tickers (slow, and Yahoo rate-limits).
TTL_SECONDS = 3600
_memo: dict = {}
_lock = threading.Lock()


def _download(field: str, tickers: list[str], period: str, auto_adjust: bool = True) -> pd.DataFrame | None:
    if yf is None:
        return None
    try:
        df = yf.download(tickers, period=period, auto_adjust=auto_adjust,
                         progress=False)[field]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        # Drop empty rows AND tickers Yahoo returned nothing for.
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if not df.empty:
            return df
    except Exception:
        pass
    return None


def _cached(path: pathlib.Path, tickers: list[str]) -> pd.DataFrame:
    try:
        cached = pd.read_csv(path, index_col=0, parse_dates=True)
    except FileNotFoundError:
        return pd.DataFrame()
    return cached[[t for t in tickers if t in cached.columns]]


def _load(field: str, tickers: list[str], period: str,
          cache_path: pathlib.Path, auto_adjust: bool = True) -> pd.DataFrame:
    tickers = list(dict.fromkeys(tickers))
    key = (field, tuple(sorted(tickers)), period, auto_adjust)
    now = time.time()
    with _lock:
        hit = _memo.get(key)
        if hit and now - hit[0] < TTL_SECONDS:
            return hit[1].copy()

    df = _download(field, tickers, period, auto_adjust=auto_adjust)
    if df is None:
        df = _cached(cache_path, tickers)
    else:
        # Yahoo skipped some tickers: backfill them from the bundled CSV cache.
        missing = [t for t in tickers if t not in df.columns]
        if missing:
            fill = _cached(cache_path, missing)
            if not fill.empty:
                try:
                    df = df.join(fill, how="left")
                except Exception:
                    pass

    df = df[[t for t in tickers if t in df.columns]]
    if not df.empty:
        with _lock:
            _memo[key] = (now, df)
    return df.copy()


def load_prices(tickers: list[str], period: str = "2y", adjusted: bool = True) -> pd.DataFrame:
    """Load closing prices for tickers.
    If adjusted=True (default), loads dividend-adjusted Close prices suitable for return calculations.
    If adjusted=False, loads raw non-dividend-adjusted Close prices suitable for historical dollar volume & liquidity calculations.
    """
    if adjusted:
        return _load("Close", tickers, period, CACHE, auto_adjust=True)
    cache_path = RAW_CACHE if RAW_CACHE.exists() else CACHE
    return _load("Close", tickers, period, cache_path, auto_adjust=False)


def load_unadjusted_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """Load non-dividend-adjusted Close prices for volume and liquidity analysis."""
    return load_prices(tickers, period=period, adjusted=False)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    return _load("Volume", tickers, period, VOL_CACHE, auto_adjust=True)
