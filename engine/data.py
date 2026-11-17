import pathlib

import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
VOL_CACHE = ROOT / "volume.csv"


def _download(field: str, tickers: list[str], period: str) -> pd.DataFrame | None:
    try:
        df = yf.download(tickers, period=period, auto_adjust=True,
                         progress=False)[field]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        if not df.empty:
            return df
    except Exception:
        pass
    return None


def _cached(path: pathlib.Path, tickers: list[str]) -> pd.DataFrame:
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    return cached[[t for t in tickers if t in cached.columns]]


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Close", tickers, period)
    if df is not None:
        missing = [t for t in tickers if t not in df.columns or df[t].dropna().empty]
        if not missing:
            return df
        cached = _cached(CACHE, tickers)
        cached_missing = [t for t in tickers if t not in cached.columns or cached[t].dropna().empty]
        if not cached_missing:
            return cached
        combined = df.copy()
        for t in tickers:
            if (t not in combined.columns or combined[t].dropna().empty) and t in cached.columns and not cached[t].dropna().empty:
                combined[t] = cached[t]
        return combined
    return _cached(CACHE, tickers)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Volume", tickers, period)
    if df is not None:
        missing = [t for t in tickers if t not in df.columns or df[t].dropna().empty]
        if not missing:
            return df
        cached = _cached(VOL_CACHE, tickers)
        cached_missing = [t for t in tickers if t not in cached.columns or cached[t].dropna().empty]
        if not cached_missing:
            return cached
        combined = df.copy()
        for t in tickers:
            if (t not in combined.columns or combined[t].dropna().empty) and t in cached.columns and not cached[t].dropna().empty:
                combined[t] = cached[t]
        return combined
    return _cached(VOL_CACHE, tickers)