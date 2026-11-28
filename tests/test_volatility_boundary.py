import math
import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    correlation,
    high_pairs,
    max_drawdown,
    portfolio_returns,
    sector_exposure,
    volatility,
)
from engine.score import risk_score


def test_exact_30_percent_volatility_synthetic_jump():
    """
    Mathematical test case:
    253 prices where price moves from 100 to 130 on day 1, then constant 130 for 251 days.
    Returns: a = 0.30, followed by 251 zero returns (n = 252).
    Sample variance (ddof=1) = a^2 / n = 0.09 / 252.
    Annualized variance = 252 * (0.09 / 252) = 0.09.
    Annualized volatility = sqrt(0.09) = 0.30 (exactly 30.0%).
    Due to floating point arithmetic, sqrt(annual_var) yields 0.3000000000000001.
    Strict rule requires 'over 30%', so exact 30% must not trigger the +20 penalty.
    """
    prices = pd.DataFrame({"NVDA": [100.0] + [130.0] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    vol = volatility(returns)

    # Volatility should be mathematically 0.30, but float precision may have 1e-16 noise
    assert vol == pytest.approx(0.30, abs=1e-12)

    score, level, hits = risk_score(
        concentration(weights),
        vol,
        max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )

    # Expected: 50 points (top_weight=20, effective_assets=15, sector_max=15), Medium
    # Must NOT have the +20 volatility penalty
    assert score == 50
    assert level == "Medium"
    vol_hits = [why for pts, why in hits if "Volatility" in why]
    assert len(vol_hits) == 0, f"Spurious volatility penalty triggered: {vol_hits}"


def test_volatility_boundary_controls():
    """
    Verify control thresholds around 30% annualized volatility.
    """
    safe_conc = {"top_weight": 0.20, "effective_assets": 5}

    # 1. Exactly 30.0%
    score_30, level_30, hits_30 = risk_score(safe_conc, 0.30, 0.0, [], 0.20)
    assert score_30 == 0
    assert level_30 == "Low"

    # 2. IEEE 754 epsilon noise above 30.0% (0.30 + 1e-16)
    score_eps, level_eps, hits_eps = risk_score(safe_conc, 0.30 + 1e-16, 0.0, [], 0.20)
    assert score_eps == 0
    assert level_eps == "Low"

    # 3. Just below threshold: 29.99%
    score_below, level_below, hits_below = risk_score(safe_conc, 0.2999, 0.0, [], 0.20)
    assert score_below == 0
    assert level_below == "Low"

    # 4. Strictly over threshold: 30.01%
    score_above, level_above, hits_above = risk_score(safe_conc, 0.3001, 0.0, [], 0.20)
    assert score_above == 20
    assert any("Volatility" in why for _, why in hits_above)

    # 5. Meaningfully higher: 35.0%
    score_high, level_high, hits_high = risk_score(safe_conc, 0.35, 0.0, [], 0.20)
    assert score_high == 20
    assert any("Volatility" in why for _, why in hits_high)
