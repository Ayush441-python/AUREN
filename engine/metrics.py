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


def align_prices(prices: pd.DataFrame, w: pd.Series) -> pd.DataFrame:
    """Reindex the weighted price columns onto one shared calendar.

    Crypto tickers trade every day of the week while equities trade only on
    business days, so ``prices`` holds gaps (NaN) for each asset on the other
    market's off days. Dropping those rows (``dropna``) silently folds a
    3-day crypto weekend move into a single "day" in a Monday return, and
    makes a 21-observation rolling window span 21 calendar days for a pure
    crypto book but ~31 calendar days for a mixed book (issue #63).

    Forward-filling each column onto the union of dates keeps every calendar
    day as one observation for every asset, so daily returns measure one
    calendar day and a 21-observation window is always 21 calendar days.
    Rows that only precede an asset's first known price are dropped.
    """
    cols = [c for c in w.index if c in prices.columns]
    return prices[cols].ffill().dropna()


def portfolio_returns(prices: pd.DataFrame, w: pd.Series) -> pd.Series:
    r = align_prices(prices, w).pct_change().dropna()
    return r @ w.loc[r.columns]  # assumes weights held constant each day


def volatility(pr: pd.Series) -> float:
    return float(pr.std() * np.sqrt(252))  # annualised


def max_drawdown(pr: pd.Series) -> float:
    value = (1 + pr).cumprod()
    return float((value / value.cummax() - 1).min())


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    cols = list(tickers)
    return align_prices(prices, pd.Series(1.0, index=cols)).pct_change().dropna().corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]