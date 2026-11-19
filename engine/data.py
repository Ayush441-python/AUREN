import pathlib

import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
VOL_CACHE = ROOT / "volume.csv"


def _download(field: str, tickers: list[str], period: str) -> pd.DataFrame | None:
    try:
        if not tickers:
            return None
        df = yf.download(tickers, period=period, auto_adjust=True,
                         progress=False)[field]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        if not isinstance(df, pd.DataFrame):
            return None
        if not all(t in df.columns for t in tickers):
            return None
        if any(df[t].dropna().empty for t in tickers):
            return None
        if df[tickers].dropna().empty:
            return None
        df = df.dropna(how="all")
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
    return df if df is not None else _cached(CACHE, tickers)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Volume", tickers, period)
    return df if df is not None else _cached(VOL_CACHE, tickers)