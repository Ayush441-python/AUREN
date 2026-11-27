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
    return prices[list(tickers)].dropna().pct_change().dropna().corr()


def portfolio_beta(pr: pd.Series, benchmark_pr: pd.Series | None) -> float | None:
    """Calculate portfolio beta against benchmark returns: Beta = Cov(Rp, Rb) / Var(Rb).
    Returns None if benchmark returns are missing, insufficient, or have zero variance.
    """
    if benchmark_pr is None:
        return None
    aligned = pd.concat([pr.rename("portfolio"), benchmark_pr.rename("benchmark")], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return None
    var_b = float(aligned["benchmark"].var())
    if var_b <= 1e-12 or not np.isfinite(var_b):
        return None
    cov = float(aligned["portfolio"].cov(aligned["benchmark"]))
    beta = cov / var_b
    if not np.isfinite(beta):
        return None
    return float(beta)


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]
