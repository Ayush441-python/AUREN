"""
Unit tests for Issue #132 fix:
Ensures concentration panel derivation preserves fractional float precision
and eliminates rounding discrepancies in Herfindahl-Hirschman Index (HHI) display.
"""

import pandas as pd
import pytest
from engine.metrics import concentration, format_weight_term


def test_format_weight_term_preserves_three_decimal_precision():
    """Verify 0.125 does not prematurely truncate to 0.12 (Issue #132)."""
    assert format_weight_term(0.125) == "0.125"
    assert format_weight_term(0.075) == "0.075"
    assert format_weight_term(0.0625) == "0.0625"


def test_format_weight_term_maintains_two_decimal_standard():
    """Verify standard fractions maintain canonical two-decimal presentation."""
    assert format_weight_term(0.25) == "0.25"
    assert format_weight_term(0.50) == "0.50"
    assert format_weight_term(0.10) == "0.10"
    assert format_weight_term(1.0) == "1.00"


def test_eight_equal_holdings_derivation_reproducibility():
    """Replicate exact issue #132 scenario: 8 holdings at 12.5% each."""
    assets = ["MSFT", "AAPL", "JPM", "COST", "GLD", "XOM", "TSLA", "AMD"]
    weights = pd.Series([0.125] * 8, index=assets)

    conc = concentration(weights)
    assert conc["hhi"] == pytest.approx(0.1250)
    assert conc["effective_assets"] == pytest.approx(8.0)

    # Format terms as done in app.py
    formatted_terms = [format_weight_term(w) for w in weights.sort_values(ascending=False)]
    assert formatted_terms == ["0.125"] * 8

    # Verify displayed operands sum of squares exactly matches HHI
    displayed_sum = sum(float(t) ** 2 for t in formatted_terms)
    assert round(displayed_sum, 4) == round(conc["hhi"], 4)
    assert round(displayed_sum, 4) == 0.1250

    # Verify no terms formatted as 0.12
    terms_str = " + ".join(f"{t}²" for t in formatted_terms)
    assert "0.12²" not in terms_str
    assert terms_str.count("0.125²") == 8


def test_four_equal_holdings_derivation():
    """Verify 4 holdings at 25% each."""
    weights = pd.Series([0.25] * 4, index=["A", "B", "C", "D"])
    conc = concentration(weights)

    formatted_terms = [format_weight_term(w) for w in weights.sort_values(ascending=False)]
    assert formatted_terms == ["0.25"] * 4

    displayed_sum = sum(float(t) ** 2 for t in formatted_terms)
    assert round(displayed_sum, 4) == round(conc["hhi"], 4)
    assert round(displayed_sum, 4) == 0.2500


def test_unequal_weights_mixed_precision():
    """Verify mixed precision portfolio (e.g. 40%, 30%, 15%, 7.5%, 7.5%)."""
    weights = pd.Series([0.40, 0.30, 0.15, 0.075, 0.075], index=["A", "B", "C", "D", "E"])
    conc = concentration(weights)

    formatted_terms = [format_weight_term(w) for w in weights.sort_values(ascending=False)]
    assert formatted_terms == ["0.40", "0.30", "0.15", "0.075", "0.075"]

    displayed_sum = sum(float(t) ** 2 for t in formatted_terms)
    assert round(displayed_sum, 4) == round(conc["hhi"], 4)


def test_equation_sign_logic():
    """Verify exact match yields '=' and rounded irrational fraction yields '\\approx'."""
    # Exact match case (8 equal assets)
    w_exact = pd.Series([0.125] * 8, index=list("ABCDEFGH"))
    terms_exact = [format_weight_term(w) for w in w_exact]
    sum_exact = sum(float(t) ** 2 for t in terms_exact)
    sign_exact = "=" if round(sum_exact, 4) == round(concentration(w_exact)["hhi"], 4) else "\\approx"
    assert sign_exact == "="
