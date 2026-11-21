import numpy as np
import pandas as pd
from engine.universe import GROUPS


def sector_exposure(w: pd.Series) -> pd.Series:
    """Weight per broad group (Big Tech, Crypto, ...)."""
    return w.groupby(w.index.map(lambda t: GROUPS.get(t, "Other"))).sum().sort_values(ascending=False)


def concentration(w: pd.Series) -> dict:
    if w.empty:
        return {
            "top_asset": "",
            "top_weight": 0.0,
            "top3_weight": 0.0,
            "hhi": 0.0,
            "effective_assets": 0.0,
        }
    abs_w = w.abs()
    hhi = float((w ** 2).sum())  # 1.0 = everything in one asset
    return {
        "top_asset": abs_w.idxmax(),
        "top_weight": float(abs_w.max()),
        "top3_weight": float(abs_w.nlargest(3).sum()),
        "hhi": hhi,
        "effective_assets": 1 / hhi if hhi > 0 else 0.0,  # "you really own this many assets"
    }


def portfolio_returns(prices: pd.DataFrame, w: pd.Series) -> pd.Series:
    r = prices[w.index].dropna().pct_change().dropna()
    return r @ w  # assumes weights held constant each day


def volatility(pr: pd.Series) -> float:
    return float(pr.std() * np.sqrt(252))  # annualised


def max_drawdown(pr: pd.Series) -> float:
    value = (1 + pr).cumprod()
    return float((value / value.cummax() - 1).min())


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    return prices[list(tickers)].dropna().pct_change().dropna().corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]