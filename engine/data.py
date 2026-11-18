import pathlib

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
VOL_CACHE = ROOT / "volume.csv"


def _download(field: str, tickers: list[str], period: str) -> pd.DataFrame | None:
    if yf is None:
        return None
    try:
        df = yf.download(tickers, period=period, auto_adjust=True,
                         progress=False)[field]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        df = df.dropna(how="all")
        if df.empty:
            return None
        if any(t not in df.columns or df[t].dropna().empty for t in tickers):
            return None
        if df[tickers].dropna().empty:
            return None
        return df[tickers]
    except Exception:
        pass
    return None


def _cached(path: pathlib.Path, tickers: list[str]) -> pd.DataFrame:
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    return cached[[t for t in tickers if t in cached.columns]]


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Close", tickers, period)
    if df is not None:
        return df
    cached = _cached(CACHE, tickers)
    if any(t not in cached.columns or cached[t].dropna().empty for t in tickers):
        return pd.DataFrame()
    return cached


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Volume", tickers, period)
    if df is not None:
        return df
    return _cached(VOL_CACHE, tickers)
