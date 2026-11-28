import pytest
from engine.report import clean_output, unverified_numbers


def test_clean_output_removes_think_blocks():
    text = "<think>Analyzing volatility and drawdown metrics...</think>Your portfolio has moderate risk."
    assert clean_output(text) == "Your portfolio has moderate risk."


def test_unverified_numbers_flags_hallucinations_issue_65():
    # Reproduction from Issue #65
    metrics = {
        "risk_score": 65,
        "risk_level": "High",
        "score_reasons": [
            "Largest holding is 40% (over 30%)",
            "Behaves like only 3.3 assets",
            "Worst past fall was -31% (deeper than -30%)",
            "90% sits in one sector",
        ],
        "portfolio_value_usd": 10000.0,
        "holdings_weight": {"NVDA": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "ETH-USD": 0.1},
        "largest_holding": {"NVDA": 0.4},
        "top_3_holdings_weight": 0.9,
        "concentration_index_hhi": 0.3,
        "effective_assets": 3.33,
        "volatility_annualised": 0.2965,
        "max_drawdown": -0.3083,
        "worst_day": -0.1066,
        "worst_month": -0.1752,
        "sector_exposure": {"Big Tech": 0.9, "Crypto": 0.1},
        "correlated_pairs_above_0.7": [],
        "scenario_stress_shocks": {
            "Big Tech falls 20%": -0.18,
            "Chip selloff (semis fall 25%)": -0.1,
            "NVDA falls 15%": -0.06,
            "Crypto crash 40%": -0.04,
            "Broad selloff": -0.165,
        },
    }

    hallucinated_report = (
        "Your ,000,000 portfolio has a Risk Score of 70 / 100, "
        "with 333 effective assets, a 70% annualized volatility, and a ,500 stress loss."
    )

    bad = unverified_numbers(hallucinated_report, metrics)
    assert 1000000.0 in bad
    assert 70.0 in bad
    assert 333.0 in bad
    assert 6500.0 in bad


def test_unverified_numbers_accepts_verified_percentages_and_dollars():
    metrics = {
        "risk_score": 50,
        "risk_level": "Medium",
        "portfolio_value_usd": 20000.0,
        "holdings_weight": {"NVDA": 0.40, "MSFT": 0.60},
        "volatility_annualised": 0.22,
        "max_drawdown": -0.18,
        "score_reasons": ["Largest holding is 60% (over 30%)"],
        "scenario_stress_shocks": {"Big Tech falls 20%": -0.20},
    }

    valid_report = (
        "The portfolio is valued at ,000 with a Risk Score of 50. "
        "The largest asset represents 60% of capital, with 22% annual volatility "
        "and a past maximum drawdown of 18%. In a stress event, estimated loss is ,000."
    )

    bad = unverified_numbers(valid_report, metrics)
    assert bad == []
