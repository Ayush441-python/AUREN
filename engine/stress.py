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


def custom_shock_feedback(
    custom_impact: float | pd.Series,
    custom_dollar: float | dict = 0.0,
    custom_shocks: dict | None = None,
) -> tuple[str, dict]:
    """Generate feedback text and callout styling options for custom sector shocks."""
    if isinstance(custom_dollar, dict):
        custom_shocks = custom_dollar
        custom_dollar = 0.0
    if custom_shocks is None:
        custom_shocks = {}

    if isinstance(custom_impact, pd.Series):
        weights = custom_impact
        custom_impact = stress(weights, custom_shocks)
        size = float(custom_dollar) if custom_dollar else 10000.0
        custom_dollar = custom_impact * size

    if custom_impact < -1e-9:
        return (
            f"Under this custom shock, your portfolio declines by <b>{custom_impact:.1%}</b> "
            f"(a drop of <b>${abs(custom_dollar):,.0f}</b>).",
            {"danger": True},
        )
    elif custom_impact > 1e-9:
        return (
            f"Under this custom shock, your portfolio gains <b>{custom_impact:+.1%}</b> "
            f"(a rise of <b>${custom_dollar:,.0f}</b>).",
            {},
        )
    elif any(abs(v) > 1e-9 for v in custom_shocks.values()):
        return (
            "Under this custom shock, the selected shocks offset.",
            {"muted": True},
        )
    else:
        return (
            "Move the sliders to see hypothetical stress test impact.",
            {"muted": True},
        )
