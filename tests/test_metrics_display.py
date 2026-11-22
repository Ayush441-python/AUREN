"""Regression tests for HHI derivation display (issue #132)."""
import pandas as pd

from engine.metrics import concentration, weight_squared_terms


def test_displayed_terms_reproduce_hhi_for_eighths():
    w = pd.Series({t: 0.125 for t in
                   ["MSFT", "AAPL", "JPM", "COST", "GLD", "XOM", "TSLA", "AMD"]})
    terms = weight_squared_terms(w)
    assert "0.12²" not in terms
    assert terms.count("0.1250²") == 8
    # Reader can reproduce the displayed HHI from the displayed terms.
    assert abs(8 * 0.1250**2 - concentration(w)["hhi"]) < 1e-9


def test_quarter_weights_still_display_cleanly():
    w = pd.Series({"A": .25, "B": .25, "C": .25, "D": .25})
    assert weight_squared_terms(w).count("0.2500²") == 4
