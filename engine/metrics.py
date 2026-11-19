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


def portfolio_returns(
    prices: pd.DataFrame, w: pd.Series, *, rebalance_daily: bool = False
) -> pd.Series:
    """Daily portfolio returns over the aligned price history.

    By default computes true buy-and-hold (drifting-weight) returns from initial
    weights ``w``: V_t = sum_i w_i * (P_{i,t} / P_{i,0}), r_t = V_t / V_{t-1} - 1.
    Pass ``rebalance_daily=True`` for frictionless daily constant-mix (``r @ w``).
    """
    aligned = prices[w.index].dropna()
    if len(aligned) < 2:
        return pd.Series(dtype=float, index=aligned.index[:0])
    w_norm = w / w.sum()
    if rebalance_daily:
        return aligned.pct_change().dropna() @ w_norm
    wealth = (aligned / aligned.iloc[0]) @ w_norm
    return wealth.pct_change().dropna()


def volatility(pr: pd.Series) -> float:
    return float(pr.std() * np.sqrt(252))  # annualised


def max_drawdown(pr: pd.Series) -> float:
    if pr.empty:
        return 0.0
    value = (1 + pr).cumprod()
    peaks = value.cummax().clip(lower=1.0)
    return float((value / peaks - 1).min())


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    return prices[list(tickers)].dropna().pct_change().dropna().corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]
