import pandas as pd
import pytest
from engine.metrics import concentration


def test_share_classes_count_as_one_issuer():
    w = pd.Series({"GOOGL": 0.25, "GOOG": 0.25, "MSFT": 0.25, "JPM": 0.25})
    c = concentration(w)
    # Alphabet is 50% of the book
    assert c["top_weight"] == pytest.approx(0.50)
    assert c["effective_assets"] == pytest.approx(1 / (0.50**2 + 0.25**2 + 0.25**2))
    assert c["top_weight"] > 0.30
    assert c["effective_assets"] < 4
