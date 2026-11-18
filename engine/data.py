import pathlib

import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
RAW_CACHE = ROOT / "raw_prices.csv"
VOL_CACHE = ROOT / "volume.csv"


def _download(field: str, tickers: list[str], period: str, auto_adjust: bool = True) -> pd.DataFrame | None:
    try:
        df = yf.download(tickers, period=period, auto_adjust=auto_adjust,
                         progress=False)[field]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        df = df.dropna(how="all")
        if not df.empty:
            return df
    except Exception:
        pass
    return None


def _cached(path: pathlib.Path, tickers: list[str]) -> pd.DataFrame:
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    return cached[[t for t in tickers if t in cached.columns]]


def load_prices(tickers: list[str], period: str = "2y", adjusted: bool = True) -> pd.DataFrame:
    """Load closing prices for tickers.
    If adjusted=True (default), loads dividend-adjusted Close prices suitable for return calculations.
    If adjusted=False, loads raw non-dividend-adjusted Close prices suitable for historical dollar volume & liquidity calculations.
    """
    if adjusted:
        df = _download("Close", tickers, period, auto_adjust=True)
        return df if df is not None else _cached(CACHE, tickers)
    else:
        df = _download("Close", tickers, period, auto_adjust=False)
        cache_path = RAW_CACHE if RAW_CACHE.exists() else CACHE
        return df if df is not None else _cached(cache_path, tickers)


def load_unadjusted_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """Load non-dividend-adjusted Close prices for volume and liquidity analysis."""
    return load_prices(tickers, period=period, adjusted=False)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Volume", tickers, period)
    return df if df is not None else _cached(VOL_CACHE, tickers)