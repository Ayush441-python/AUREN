import itertools
import pandas as pd
import pytest
from engine.metrics import sector_exposure
from engine.score import risk_score


def test_sector_exposure_50_percent_boundary_permutations():
    """
    Issue #133: Exactly 50% broad-group exposure adds 15 points only in certain asset orders.
    Verify that across all 6 permutations of NVDA, MSFT, and AAPL (totaling exactly 50%),
    sector_exposure produces exactly 0.5 and does not trigger the > 0.50 penalty.
    """
    big_tech_assets = [("NVDA", 0.17), ("MSFT", 0.28), ("AAPL", 0.05)]
    other_assets = [("AMD", 0.25), ("TSM", 0.25)]

    for perm in itertools.permutations(big_tech_assets):
        holdings = list(perm) + other_assets
        tickers = [t for t, _ in holdings]
        weights = [w for _, w in holdings]
        w = pd.Series(weights, index=tickers)

        exp = sector_exposure(w)
        big_tech_val = float(exp["Big Tech"])

        # Must equal 0.5 exactly without representation float skew (e.g. 0.5000000000000001)
        assert big_tech_val == 0.5
        assert big_tech_val <= 0.50

        # Risk score calculation
        conc = {"top_weight": 0.28, "effective_assets": 4.5}
        vol = 0.31  # contributes +20
        mdd = -0.20
        pairs = []

        score, level, hits = risk_score(conc, vol, mdd, pairs, big_tech_val)

        # Must score 20 (Low) and NOT 35 (Medium)
        assert score == 20
        assert level == "Low"
        assert not any("sits in one sector" in why for _, why in hits)


def test_sector_exposure_boundary_strictness():
    """
    Test thresholds strictly around 50%:
    - 49.99%: No sector penalty
    - 50.00%: No sector penalty (boundary case)
    - 50.01%: Triggers +15 sector penalty
    """
    conc = {"top_weight": 0.25, "effective_assets": 5.0}

    # 49.99%
    w_4999 = pd.Series([0.1699, 0.28, 0.05, 0.25, 0.2501], index=["NVDA", "MSFT", "AAPL", "AMD", "TSM"])
    exp_4999 = sector_exposure(w_4999)
    score_4999, level_4999, hits_4999 = risk_score(conc, 0.10, -0.10, [], float(exp_4999["Big Tech"]))
    assert score_4999 == 0
    assert not any("sits in one sector" in why for _, why in hits_4999)

    # Exactly 50.0%
    w_50 = pd.Series([0.17, 0.28, 0.05, 0.25, 0.25], index=["NVDA", "MSFT", "AAPL", "AMD", "TSM"])
    exp_50 = sector_exposure(w_50)
    score_50, level_50, hits_50 = risk_score(conc, 0.10, -0.10, [], float(exp_50["Big Tech"]))
    assert score_50 == 0
    assert not any("sits in one sector" in why for _, why in hits_50)

    # 50.01%
    w_5001 = pd.Series([0.1701, 0.28, 0.05, 0.2499, 0.25], index=["NVDA", "MSFT", "AAPL", "AMD", "TSM"])
    exp_5001 = sector_exposure(w_5001)
    score_5001, level_5001, hits_5001 = risk_score(conc, 0.10, -0.10, [], float(exp_5001["Big Tech"]))
    assert score_5001 == 15
    assert any("sits in one sector" in why for _, why in hits_5001)
