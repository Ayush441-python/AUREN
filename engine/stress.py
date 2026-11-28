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
    return float(sum(wt * shock_for(t, shocks) for t, wt in w.items()))


def worst_periods(pr: pd.Series) -> dict:
    month = (1 + pr).rolling(21).apply(np.prod, raw=True) - 1
    return {"worst_day": float(pr.min()), "worst_month": float(month.min())}