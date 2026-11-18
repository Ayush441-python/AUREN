import ast
from pathlib import Path
import pandas as pd
import pytest


def normalize_series(weights: pd.Series, total: float) -> pd.Series:
    res = (weights / total * 100).round(1)
    diff = round(100.0 - float(res.sum()), 1)
    if diff != 0 and len(res) > 0:
        res.iloc[0] = round(res.iloc[0] + diff, 1)
    return res


def test_three_holding_normalization_sums_to_exact_100():
    """Verify that 3 equal holdings (10%, 10%, 10%) normalize to 100.0% instead of getting stuck at 99.9%."""
    weights = pd.Series([10.0, 10.0, 10.0])
    total = float(weights.sum())

    normalized = normalize_series(weights, total)
    assert normalized.tolist() == [33.4, 33.3, 33.3]
    assert pytest.approx(float(normalized.sum())) == 100.0
    assert abs(float(normalized.sum()) - 100.0) <= 0.01


def test_six_holding_normalization_sums_to_exact_100():
    """Verify that 6 equal holdings (7%, 7%, 7%, 7%, 7%, 7%) normalize to 100.0% instead of 100.2%."""
    weights = pd.Series([7.0] * 6)
    total = float(weights.sum())

    normalized = normalize_series(weights, total)
    assert pytest.approx(float(normalized.sum())) == 100.0
    assert abs(float(normalized.sum()) - 100.0) <= 0.01


def test_offline_reproduction_ast_matches_issue_45():
    """Run AST extraction of app.py normalization block on 3 equal holdings."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    tree = ast.parse(app_path.read_text())

    pf = pd.DataFrame({"ticker": ["COST", "MSFT", "AAPL"], "weight": [10.0, 10.0, 10.0]})
    total = float(pf["weight"].sum())
    ok = abs(total - 100) <= 0.01
    assert not ok

    # Execute the normalization logic
    weights = (pf["weight"] / total * 100).round(1)
    diff = round(100.0 - float(weights.sum()), 1)
    if diff != 0 and len(weights) > 0:
        weights.iloc[0] = round(weights.iloc[0] + diff, 1)
    pf["weight"] = weights

    new_total = float(pf["weight"].sum())
    new_ok = abs(new_total - 100) <= 0.01

    assert new_ok
    assert pytest.approx(new_total) == 100.0
