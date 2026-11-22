"""Regression tests for share-class ticker aliases (issue #108)."""
import pandas as pd

from api import _normalize_and_validate_weights
from engine.metrics import concentration


def test_goog_merges_into_googl():
    w = _normalize_and_validate_weights({"GOOGL": 25, "GOOG": 25,
                                         "MSFT": 25, "JPM": 25})
    assert "GOOG" not in w.index
    assert abs(w["GOOGL"] - 0.5) < 1e-9
    assert abs(w["MSFT"] - 0.25) < 1e-9


def test_split_alphabet_position_counts_as_one_issuer():
    w = _normalize_and_validate_weights({"GOOGL": 25, "GOOG": 25,
                                         "MSFT": 25, "JPM": 25})
    c = concentration(w)
    # Alphabet is 50% of the book: top_weight > 30% and effective assets < 4
    assert c["top_weight"] > 0.30
    assert c["effective_assets"] < 4
