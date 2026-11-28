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
VOL_CACHE = ROOT / "volume.csv"

# In-memory cache so /risk, /liquidity and the what-if tab do not each hit
# Yahoo Finance again for the same tickers (slow, and Yahoo rate-limits).
TTL_SECONDS = 3600
_memo: dict = {}
_lock = threading.Lock()


def _download(field: str, tickers: list[str], period: str) -> pd.DataFrame | None:
    if yf is None:
        return None
    try:
        df = yf.download(tickers, period=period, auto_adjust=True,
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


STABLECOINS = {"USDC", "USDT", "DAI", "USD", "BUSD"}


def _cached(path: pathlib.Path, tickers: list[str]) -> pd.DataFrame:
    try:
        cached = pd.read_csv(path, index_col=0, parse_dates=True)
    except FileNotFoundError:
        return pd.DataFrame()
    return cached[[t for t in tickers if t in cached.columns]]


def _load(field: str, tickers: list[str], period: str,
          cache_path: pathlib.Path) -> pd.DataFrame:
    tickers = list(dict.fromkeys(tickers))
    key = (field, tuple(sorted(tickers)), period)
    now = time.time()
    with _lock:
        hit = _memo.get(key)
        if hit and now - hit[0] < TTL_SECONDS:
            return hit[1].copy()

    stable_tickers = [t for t in tickers if t.upper() in STABLECOINS]
    query_tickers = [t for t in tickers if t.upper() not in STABLECOINS]

    if query_tickers:
        df = _download(field, query_tickers, period)
        if df is None:
            df = _cached(cache_path, query_tickers)
        else:
            # Yahoo skipped some tickers: backfill them from the bundled CSV cache.
            missing = [t for t in query_tickers if t not in df.columns]
            if missing:
                fill = _cached(cache_path, missing)
                if not fill.empty:
                    try:
                        df = df.join(fill, how="left")
                    except Exception:
                        pass
    else:
        df = pd.DataFrame()

    if stable_tickers:
        if df.empty or df.index.empty:
            try:
                cached_idx = pd.read_csv(cache_path, index_col=0, parse_dates=True).index
                df = pd.DataFrame(index=cached_idx)
            except Exception:
                idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=252)
                df = pd.DataFrame(index=idx)
        for s in stable_tickers:
            if field == "Close":
                df[s] = 1.0
            else:
                df[s] = 5_000_000_000.0

    df = df[[t for t in tickers if t in df.columns]]
    if not df.empty:
        with _lock:
            _memo[key] = (now, df)
    return df.copy()


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    return _load("Close", tickers, period, CACHE)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    return _load("Volume", tickers, period, VOL_CACHE)
