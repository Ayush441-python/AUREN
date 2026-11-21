import numpy as np
import pandas as pd
from engine.universe import GROUPS


def sector_exposure(w: pd.Series) -> pd.Series:
    """Weight per broad group (Big Tech, Crypto, ...)."""
    return w.groupby(w.index.map(lambda t: GROUPS.get(t, "Other"))).sum().sort_values(ascending=False)


def concentration(w: pd.Series) -> dict:
    hhi = float((w ** 2).sum())  # 1.0 = everything in one asset
    return {
        "top_asset": w.idxmax(),
        "top_weight": float(w.max()),
        "top3_weight": float(w.nlargest(3).sum()),
        "hhi": hhi,
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
    cols = list(tickers)
    n = len(cols)
    matrix = np.full((n, n), np.nan, dtype=float)
    for i, a in enumerate(cols):
        if a in prices:
            s = prices[a].dropna().pct_change(fill_method=None).dropna()
            if len(s) > 1 and s.std() > 0:
                matrix[i, i] = 1.0
        for j in range(i + 1, n):
            b = cols[j]
            if a == b:
                matrix[i, j] = matrix[i, i]
                matrix[j, i] = matrix[i, i]
            elif a in prices and b in prices:
                paired = prices[[a, b]].dropna().pct_change(fill_method=None).dropna()
                if len(paired) > 1:
                    r = paired[a].corr(paired[b])
                    matrix[i, j] = r
                    matrix[j, i] = r
    return pd.DataFrame(matrix, index=cols, columns=cols)


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]