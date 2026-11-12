import pathlib
import pandas as pd
import yfinance as yf

CACHE = pathlib.Path(__file__).parent.parent / "data" / "prices.csv"


def load_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    try:
        df = yf.download(tickers, period=period, auto_adjust=True,
                         progress=False)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        df = df.dropna(how="all")
        if not df.empty:
            return df
    except Exception:
        pass
    cached = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    return cached[[t for t in tickers if t in cached.columns]]