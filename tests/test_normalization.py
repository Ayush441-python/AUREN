import pandas as pd
import pytest


def normalize_portfolio_weights(pf: pd.DataFrame) -> pd.DataFrame:
    """Replicates normalization in app.py."""
    total = float(pf["weight"].sum())
    if total <= 0:
        return pf
    weights = (pf["weight"] / total * 100).round(1)
    diff = round(100.0 - float(weights.sum()), 1)
    if diff != 0 and len(weights) > 0:
        idx = weights.idxmax()
        weights.loc[idx] = round(weights.loc[idx] + diff, 1)
    pf["weight"] = weights
    return pf


def test_normalization_three_equal_holdings():
    # Issue #45 case: 3 holdings at 10% each -> previously 33.3% each (total 99.9%)
    pf = pd.DataFrame({"ticker": ["COST", "MSFT", "AAPL"], "weight": [10.0, 10.0, 10.0]})
    res = normalize_portfolio_weights(pf)
    total = float(res["weight"].sum())
    assert abs(total - 100.0) <= 0.01
    assert set(res["weight"].tolist()) == {33.3, 33.4}


def test_normalization_arbitrary_holdings():
    # 7 equal holdings (100 / 7 = 14.2857...)
    pf = pd.DataFrame({"ticker": [f"T{i}" for i in range(7)], "weight": [1.0] * 7})
    res = normalize_portfolio_weights(pf)
    total = float(res["weight"].sum())
    assert abs(total - 100.0) <= 0.01
