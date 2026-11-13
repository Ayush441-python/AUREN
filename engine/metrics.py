import numpy as np
import pandas as pd


def concentration(w: pd.Series) -> dict:
    hhi = float((w ** 2).sum())  # 1.0 = everything in one asset
    return {
        "top_asset": w.idxmax(),
        "top_weight": float(w.max()),
        "effective_assets": 1 / hhi,  # "you really own this many assets"
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