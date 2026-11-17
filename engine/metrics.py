import numpy as np
import pandas as pd
from engine.universe import GROUPS


def sector_exposure(w: pd.Series) -> pd.Series:
    """Weight per broad group (Big Tech, Crypto, ...)."""
    return w.groupby(w.index.map(lambda t: GROUPS.get(t, "Other"))).sum().sort_values(ascending=False)


def concentration(w: pd.Series) -> dict:
    hhi = float((w ** 2).sum()) if not w.empty else 0.0  # 1.0 = everything in one asset
    return {
        "top_asset": str(w.idxmax()) if not w.empty else "N/A",
        "top_weight": float(w.max()) if not w.empty else 0.0,
        "top3_weight": float(w.nlargest(3).sum()) if not w.empty else 0.0,
        "hhi": hhi,
        "effective_assets": (1.0 / hhi) if hhi > 0 else 0.0,  # "you really own this many assets"
    }


def portfolio_returns(prices: pd.DataFrame, w: pd.Series) -> pd.Series:
    missing = [t for t in w.index if t not in prices.columns]
    if missing:
        raise KeyError(f"Missing historical price data for tickers: {missing}")
    # Forward-fill prices across non-trading days so 24/7 assets (crypto) preserve weekend risk
    r = prices[w.index].ffill().dropna().pct_change().dropna()
    return r @ w  # assumes weights held constant each day


def volatility(pr: pd.Series, crypto_weight: float = 0.0) -> float:
    if pr.empty or pr.isna().all() or len(pr) < 2:
        return 0.0
    trading_days = 365.0 * crypto_weight + 252.0 * (1.0 - crypto_weight)
    return float(pr.std() * np.sqrt(trading_days))  # annualised


def max_drawdown(pr: pd.Series) -> float:
    if pr.empty:
        return 0.0
    value = (1 + pr).cumprod()
    cummax = value.cummax()
    dd = (value / cummax - 1).min()
    return float(dd) if not np.isnan(dd) else 0.0


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    return prices[list(tickers)].ffill().dropna().pct_change().dropna().corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if not np.isnan(corr.loc[a, b]) and corr.loc[a, b] > threshold]
