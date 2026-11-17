import numpy as np
import pandas as pd

from engine.universe import GROUPS, SECTORS

# Hypothetical shocks, not forecasts. Keys can be a ticker, an industry or a group.
SCENARIOS = {
    "Big Tech falls 20%": {"Big Tech": -0.20},
    "Chip selloff (semis fall 25%)": {"Semiconductors": -0.25,
                                      "Semiconductor Equipment": -0.25,
                                      "Memory Chips": -0.25},
    "NVDA falls 15%": {"NVDA": -0.15},
    "Crypto crash 40%": {"Crypto": -0.40},
    "Broad selloff": {
        "Big Tech": -0.15, "AI & Semiconductors": -0.20,
        "Software & Cybersecurity": -0.15, "Internet & Communication": -0.10,
        "Consumer & Retail": -0.10, "Healthcare & Biotechnology": -0.08,
        "Industrial & Energy": -0.08, "Financials": -0.10,
        "Crypto": -0.30, "Gold": 0.03,
    },
}


def shock_for(ticker: str, shocks: dict) -> float:
    """Ticker shock beats industry shock, which beats group shock."""
    for key in (ticker, SECTORS.get(ticker), GROUPS.get(ticker)):
        if key in shocks:
            return shocks[key]
    return 0.0


def stress(w: pd.Series, shocks: dict) -> float:
    if w.empty:
        return 0.0
    val = float(sum(wt * shock_for(t, shocks) for t, wt in w.items()))
    return 0.0 if np.isnan(val) or np.isinf(val) else val


def worst_periods(pr: pd.Series) -> dict:
    if pr.empty:
        return {"worst_day": 0.0, "worst_month": 0.0}
    pr_clean = pr.dropna()
    if pr_clean.empty:
        return {"worst_day": 0.0, "worst_month": 0.0}
    w_day = float(pr_clean.min())
    worst_day = 0.0 if np.isnan(w_day) or np.isinf(w_day) else w_day
    if len(pr_clean) < 21:
        worst_month = 0.0
    else:
        month = (1 + pr_clean).rolling(21).apply(np.prod, raw=True) - 1
        m_val = month.min()
        worst_month = 0.0 if np.isnan(m_val) or np.isinf(m_val) else float(m_val)
    return {"worst_day": worst_day, "worst_month": worst_month}