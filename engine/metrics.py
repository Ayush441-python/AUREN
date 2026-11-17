import numpy as np
import pandas as pd
from engine.universe import GROUPS


def sector_exposure(w: pd.Series) -> pd.Series:
    """Weight per broad group (Big Tech, Crypto, ...)."""
    if w.empty:
        return pd.Series(dtype=float)
    return w.groupby(w.index.map(lambda t: GROUPS.get(t, "Other"))).sum().sort_values(ascending=False)


def concentration(w: pd.Series) -> dict:
    if w.empty:
        return {
            "top_asset": None,
            "top_weight": 0.0,
            "top3_weight": 0.0,
            "hhi": 0.0,
            "effective_assets": 0.0,
        }
    hhi = float((w ** 2).sum())  # 1.0 = everything in one asset
    if np.isnan(hhi) or np.isinf(hhi):
        hhi = 0.0
    effective_assets = float(1 / hhi) if hhi > 0 else 0.0
    if np.isnan(effective_assets) or np.isinf(effective_assets):
        effective_assets = 0.0
    top_w = float(w.max())
    if np.isnan(top_w) or np.isinf(top_w):
        top_w = 0.0
    top3_w = float(w.nlargest(3).sum())
    if np.isnan(top3_w) or np.isinf(top3_w):
        top3_w = 0.0
    return {
        "top_asset": w.idxmax(),
        "top_weight": top_w,
        "top3_weight": top3_w,
        "hhi": hhi,
        "effective_assets": effective_assets,
    }


def portfolio_returns(prices: pd.DataFrame, w: pd.Series) -> pd.Series:
    missing = [t for t in w.index if t not in prices.columns]
    if missing:
        raise KeyError(f"Historical price series unavailable for: {missing}")
    if prices.empty or w.empty:
        return pd.Series(dtype=float)
    r = prices[w.index].dropna().pct_change().dropna()
    if r.empty:
        return pd.Series(dtype=float)
    return r @ w  # assumes weights held constant each day


def volatility(pr: pd.Series) -> float:
    if pr.empty:
        return 0.0
    pr_clean = pr.dropna()
    if len(pr_clean) < 2:
        return 0.0
    vol = float(pr_clean.std() * np.sqrt(252))  # annualised
    return 0.0 if np.isnan(vol) or np.isinf(vol) else vol


def max_drawdown(pr: pd.Series) -> float:
    if pr.empty:
        return 0.0
    pr_clean = pr.dropna()
    if pr_clean.empty:
        return 0.0
    value = (1 + pr_clean).cumprod()
    cummax = value.cummax()
    mdd = float((value / cummax - 1).min())
    return 0.0 if np.isnan(mdd) or np.isinf(mdd) else mdd


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    cols = [t for t in tickers if t in prices.columns]
    if not cols:
        return pd.DataFrame()
    return prices[cols].dropna().pct_change().dropna().corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    if corr.empty:
        return []
    cols = list(corr.columns)
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            val = corr.loc[a, b]
            if not np.isnan(val) and not np.isinf(val) and val > threshold:
                pairs.append((a, b, round(float(val), 2)))
    return pairs