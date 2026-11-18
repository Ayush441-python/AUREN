import ast
from pathlib import Path
import pandas as pd
import pytest
from engine.metrics import high_pairs, correlation, portfolio_returns


def test_zero_weight_exclusion_eliminates_spurious_correlation_pairs():
    """Verify that zero-weight stocks (e.g. AMAT, ASML, LRCX at 0%) do not add spurious high-correlation pairs."""
    prices_path = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
    if not prices_path.exists():
        pytest.skip("data/prices.csv not available")

    prices = pd.read_csv(prices_path, index_col=0)
    w_with_zero = pd.Series({"COST": 1.0, "AMAT": 0.0, "ASML": 0.0, "LRCX": 0.0})
    w_positive = w_with_zero[w_with_zero > 0]

    # Verify returns are identical
    pr_all = portfolio_returns(prices, w_with_zero)
    pr_pos = portfolio_returns(prices, w_positive)
    assert pr_all.equals(pr_pos)

    # Without filter, pairs would be non-empty due to semiconductor co-movement
    unfiltered_pairs = high_pairs(correlation(prices, w_with_zero.index))
    assert len(unfiltered_pairs) == 3

    # With zero-weight filter, pairs is strictly empty
    filtered_pairs = high_pairs(correlation(prices, w_positive.index))
    assert len(filtered_pairs) == 0


def test_analyze_function_filters_zero_weights():
    """Verify that app.py analyze() filters w[w > 0] before calculating metrics and pairs."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    app_tree = ast.parse(app_path.read_text())

    # Find analyze function in app.py
    analyze_fn = next(
        n for n in app_tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "analyze"
    )

    # Check for zero-weight filter in analyze
    fn_src = ast.unparse(analyze_fn)
    assert "w = w[w > 0]" in fn_src or "w[w > 0]" in fn_src, (
        "analyze() must filter zero-weight assets: w = w[w > 0]"
    )
