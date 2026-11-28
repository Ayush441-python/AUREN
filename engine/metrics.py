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
    """Annualized return volatility using 365 days on calendar-padded series, else 252."""
    has_weekends = isinstance(pr.index, pd.DatetimeIndex) and bool((pr.index.day_of_week >= 5).any())
    periods_per_year = 365.0 if has_weekends else 252.0
    return float(pr.std() * np.sqrt(periods_per_year))


def max_drawdown(pr: pd.Series) -> float:
    value = (1 + pr).cumprod()
    return float((value / value.cummax() - 1).min())


def correlation(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    """Pairwise return correlation, masking forward-filled weekend equity plateaus."""
    cols = list(tickers)
    r = prices[cols].dropna().pct_change().dropna()
    if isinstance(r.index, pd.DatetimeIndex):
        is_weekend = r.index.day_of_week >= 5
        if is_weekend.any():
            r = r.copy()
            for col in cols:
                if not str(col).endswith("-USD"):
                    r.loc[is_weekend, col] = np.nan
    return r.corr()


def high_pairs(corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
    cols = list(corr.columns)
    return [(a, b, round(float(corr.loc[a, b]), 2))
            for i, a in enumerate(cols) for b in cols[i + 1:]
            if corr.loc[a, b] > threshold]