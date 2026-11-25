import pathlib
import threading
import time

import pandas as pd

from engine.universe import SECTORS

try:
    import yfinance as yf
except ImportError:
    yf = None

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
VOL_CACHE = ROOT / "volume.csv"

# Pre-registered universe tickers are all USD-quoted (US equities, ETFs, *-USD crypto).
_STATIC_USD_TICKERS = frozenset(SECTORS)

# Yahoo Finance quotes some markets in minor currency sub-units (e.g. LSE pence).
_SUBUNIT_CURRENCY: dict[str, tuple[str, float]] = {
    "GBp": ("GBP", 100.0),
    "GBX": ("GBP", 100.0),
    "ILA": ("ILS", 100.0),
    "ILX": ("ILS", 100.0),
    "ZAc": ("ZAR", 100.0),
    "ZAC": ("ZAR", 100.0),
}


class FxUnavailableError(RuntimeError):
    """Raised when a non-USD asset cannot be converted to USD."""

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

    df = _download(field, tickers, period)
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


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    return _load("Close", tickers, period, CACHE)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    return _load("Volume", tickers, period, VOL_CACHE)


def get_ticker_currency(ticker: str) -> str | None:
    """Return the Yahoo Finance quote currency for `ticker`, or None if unknown."""
    t = ticker.strip().upper()
    if t in _STATIC_USD_TICKERS or t.endswith("-USD"):
        return "USD"

    key = ("CURRENCY", t)
    now = time.time()
    with _lock:
        hit = _memo.get(key)
        if hit and now - hit[0] < TTL_SECONDS:
            return hit[1]

    ccy: str | None = None
    if yf is not None:
        try:
            info = yf.Ticker(t).info or {}
            raw = info.get("currency")
            if isinstance(raw, str) and raw.strip():
                ccy = raw.strip()
        except Exception:
            ccy = None

    if ccy is not None:
        with _lock:
            _memo[key] = (now, ccy)
    return ccy


def convert_prices_to_usd(prices: pd.DataFrame, period: str = "2y") -> pd.DataFrame:
    """Convert non-USD price columns to USD using session-aligned FX closes.

    Raises FxUnavailableError if a non-USD asset's quote currency is unknown or
    its FX rate history cannot be loaded.
    """
    if prices.empty:
        return prices

    conversions: list[tuple[str, float, str | None]] = []
    needed_fx: set[str] = set()

    for col in prices.columns:
        ccy = get_ticker_currency(str(col))
        if ccy is None:
            raise FxUnavailableError(
                f"USD performance is unavailable: unknown quote currency for {col}."
            )
        if ccy.upper() == "USD":
            continue

        base_ccy, scale = _SUBUNIT_CURRENCY.get(ccy, (ccy.upper(), 1.0))
        if base_ccy == "USD":
            conversions.append((col, scale, None))
        else:
            fx_ticker = f"{base_ccy}=X"
            conversions.append((col, scale, fx_ticker))
            needed_fx.add(fx_ticker)

    if not conversions:
        return prices

    fx_df = load_prices(sorted(needed_fx), period=period) if needed_fx else pd.DataFrame()
    out = prices.copy()

    for col, scale, fx_ticker in conversions:
        if fx_ticker is None:
            out[col] = out[col] / scale
            continue

        if fx_df.empty or fx_ticker not in fx_df.columns:
            raise FxUnavailableError(
                f"USD performance is unavailable: missing FX rate data for {col} ({fx_ticker})."
            )

        fx_series = fx_df[fx_ticker].dropna()
        if fx_series.empty:
            raise FxUnavailableError(
                f"USD performance is unavailable: empty FX rate data for {col} ({fx_ticker})."
            )

        fx_aligned = (
            fx_series.reindex(out.index.union(fx_series.index))
            .sort_index()
            .ffill(limit=3)
            .reindex(out.index)
        )
        fx_aligned = fx_aligned.where(fx_aligned > 0)
        if (out[col].notna() & fx_aligned.notna()).sum() == 0:
            raise FxUnavailableError(
                f"USD performance is unavailable: no overlapping FX rate data for {col} ({fx_ticker})."
            )

        out[col] = (out[col] / scale) / fx_aligned

    return out
