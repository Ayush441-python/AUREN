from fractions import Fraction
import math

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


def _aligned_returns(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    return prices[list(tickers)].dropna().pct_change().dropna()


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    return _aligned_returns(prices, tickers).corr()


def _strict_pearson(x, y, threshold: float) -> bool:
    """Compare Pearson's r to a decimal cutoff exactly for binary64 samples."""
    def integers(values):
        # Each denominator is a power of two. Rescaling a whole column by a
        # positive constant leaves its correlation unchanged.
        parts = [float(v).as_integer_ratio() for v in values]
        scale = max(d for _, d in parts)
        return [p * (scale // d) for p, d in parts]

    valid = np.isfinite(x) & np.isfinite(y)
    n = int(valid.sum())
    if n < 2:
        return False
    x, y = integers(x[valid]), integers(y[valid])
    sx, sy = sum(x), sum(y)
    xx = n * sum(v*v for v in x) - sx*sx
    yy = n * sum(v*v for v in y) - sy*sy
    xy = n * sum(v*w for v, w in zip(x, y)) - sx*sy
    if not xx or not yy:
        return False  # constant series: r is undefined
    p, q = Fraction(str(threshold)).as_integer_ratio()
    if (xy < 0) != (p < 0):
        return xy >= 0
    # r = xy/sqrt(xx*yy). For two negative values, squaring reverses order.
    lhs, rhs = (xy*q)**2, p*p*xx*yy
    return lhs < rhs if xy < 0 else lhs > rhs


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7, *, returns=None) -> list[tuple]:
    cols = list(corr.columns)
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(corr.at[a, b])
            above = r > threshold
            if returns is not None and math.isfinite(r) and abs(r - threshold) <= 1e-12:
                # The band selects the slow path; it is NOT a tolerance on
                # the business rule. A genuinely larger correlation can pass.
                above = _strict_pearson(returns[a], returns[b], threshold)
            if above:
                pairs.append((a, b, round(r, 2)))
    return pairs


def correlation_and_pairs(prices: pd.DataFrame, tickers, threshold: float = 0.7):
    returns = _aligned_returns(prices, tickers)
    corr = returns.corr()
    return corr, high_pairs(corr, threshold, returns=returns)
