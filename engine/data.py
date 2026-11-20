import pathlib

import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent.parent / "data"
CACHE = ROOT / "prices.csv"
VOL_CACHE = ROOT / "volume.csv"


def _parse_period_dates(period: str, data_df: pd.DataFrame) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Parse period string and return (start_date, end_date) for filtering."""
    if period == "ytd":
        # For YTD, use the current year from the most recent data
        max_date = data_df.index.max()
        current_year = str(max_date.year)
        start_date = pd.Timestamp(f"{current_year}-01-01")
        end_date = max_date  # Or use the snapshot end date if known
        return start_date, end_date
    
    # Handle year-based periods like "2y", "5y"
    if len(period) == 2 and period[0].isdigit():
        years_back = int(period[1:])
        max_date = data_df.index.max()
        end_date = max_date
        start_date = max_date - pd.Timedelta(days=years_back * 365)
        return start_date, end_date
    
    # Handle date range like "2024-01-01:2024-12-31"
    if "-" in period and len(period) > 10:
        try:
            parts = period.split(":")
            start_date = pd.Timestamp(parts[0])
            end_date = pd.Timestamp(parts[1])
            return start_date, end_date
        except (ValueError, IndexError):
            pass
    
    # Default: use all available data
    return None, None


def _cached_with_period(path: pathlib.Path, tickers: list[str], 
                         start_date: pd.Timestamp | None, 
                         end_date: pd.Timestamp | None) -> pd.DataFrame:
    """Load cached data and optionally filter by date range."""
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    cached = cached[[t for t in tickers if t in cached.columns]]
    
    if start_date is not None or end_date is not None:
        mask = pd.Series(True, index=cached.index)
        if start_date is not None:
            mask &= cached.index >= start_date
        if end_date is not None:
            mask &= cached.index <= end_date
        return cached[mask].copy()
    
    return cached.copy()


def _download(field: str, tickers: list[str], period: str) -> pd.DataFrame | None:
    try:
        df = yf.download(tickers, period=period, auto_adjust=True,
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


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Close", tickers, period)
    if df is not None:
        return df
    
    # Parse dates for fallback filtering
    max_date = pd.read_csv(CACHE, nrows=1, index_col=0, parse_dates=True).index.max()
    start_date, end_date = _parse_period_dates(period, pd.DataFrame(index=[max_date]))
    
    return _cached_with_period(CACHE, tickers, start_date, end_date)


def load_volumes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    df = _download("Volume", tickers, period)
    if df is not None:
        return df
    
    # Parse dates for fallback filtering
    max_date = pd.read_csv(VOL_CACHE, nrows=1, index_col=0, parse_dates=True).index.max()
    start_date, end_date = _parse_period_dates(period, pd.DataFrame(index=[max_date]))
    
    return _cached_with_period(VOL_CACHE, tickers, start_date, end_date)