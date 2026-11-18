import pandas as pd

from engine.report import unverified_numbers
from engine.stress import SCENARIOS, stress


def test_unverified_numbers_flags_reversed_sign_on_stress_loss():
    weights = pd.Series({"NVDA": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "ETH-USD": 0.1})
    impact = round(stress(weights, SCENARIOS["Big Tech falls 20%"]), 4)
    assert impact == -0.18

    metrics = {"scenario_stress_shocks": {"tech": impact}}

    # -18.0% (ASCII minus) is valid and matches -0.18
    assert unverified_numbers("Modeled portfolio return: -18.0%", metrics) == []

    # −18.0% (Unicode minus \u2212) is valid and matches -0.18
    assert unverified_numbers("Modeled portfolio return: \u221218.0%", metrics) == []

    # +18.0% (reversed return claiming gain) must be flagged
    assert unverified_numbers("Modeled portfolio return: +18.0%", metrics) == [18.0]

    # +37.6% (unrelated return) must be flagged
    assert unverified_numbers("Modeled portfolio return: +37.6%", metrics) == [37.6]


def test_unverified_numbers_handles_positive_gains_and_allocations():
    metrics = {
        "holdings_weight": {"NVDA": 0.4},
        "portfolio_gain": 0.15,
    }

    # Legitimate positive returns and allocations match
    assert unverified_numbers("Allocation is 40% with return +15.0%", metrics) == []

    # Inverted negative sign (-15.0%) on a positive gain (+15.0%) must be flagged
    assert unverified_numbers("Portfolio had return -15.0%", metrics) == [-15.0]


def test_unverified_numbers_currency_with_signs():
    metrics = {
        "ending_value": 8200.0,
        "pnl": -1800.0,
    }

    # Legitimate currency values with correct signs match
    assert unverified_numbers("Ending value $8,200 with loss -$1,800", metrics) == []

    # Inverted sign (+1,800) for a negative loss must be flagged
    assert unverified_numbers("Ending value $8,200 with gain +$1,800", metrics) == [
        1800.0
    ]
