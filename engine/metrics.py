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


def _corr_exceeds_exact(x: pd.Series, y: pd.Series, threshold: float) -> bool:
    """Order-independent Pearson ``> threshold`` decision.

    pandas' float covariance can land a mathematically exact tie (e.g. 7/10)
    a few ULPs above or below the cutoff depending on column order. For
    coefficients within float noise of the threshold, recompute the decision
    with exact rational arithmetic on the float inputs — Fraction sums are
    exact, so the result cannot depend on summation order.
    """
    from fractions import Fraction

    xs = [Fraction(v) for v in x]
    ys = [Fraction(v) for v in y]
    n = len(xs)
    if n < 2:
        return False
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    if sxy <= 0:
        return False
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    t = Fraction(str(threshold))
    return sxy * sxy > t * t * sxx * syy


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7,
               returns: pd.DataFrame | None = None) -> list[tuple]:
    cols = list(corr.columns)
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(corr.loc[a, b])
            if abs(r - threshold) <= 1e-9 and returns is not None \
                    and a in returns.columns and b in returns.columns:
                hit = _corr_exceeds_exact(returns[a], returns[b], threshold)
            else:
                hit = r > threshold
            if hit:
                pairs.append((a, b, round(r, 2)))
    return pairs