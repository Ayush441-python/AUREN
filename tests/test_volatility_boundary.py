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


@pytest.mark.parametrize(
    "terminal_price, expected_score, expected_level",
    [(100, 50, "Medium"), (129.99, 50, "Medium"),
     (130, 50, "Medium"), (130.01, 70, "High")],
)
def test_volatility_threshold_from_prices(terminal_price, expected_score, expected_level):
    # For 252 returns [a, 0, ..., 0], sample variance is a**2 / 252,
    # so annualised volatility is exactly abs(a). 100 -> 130 gives 30%.
    prices = pd.DataFrame({"NVDA": [100.0] + [terminal_price] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    score, level, hits = risk_score(
        concentration(weights), volatility(returns), max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )
    assert (score, level) == (expected_score, expected_level)
    assert any("Volatility is" in reason for _, reason in hits) == (expected_score == 70)


@pytest.mark.parametrize("vol, expected_score", [(0.30 - 1e-9, 0), (0.30 + 1e-9, 20)])
def test_volatility_threshold_preserves_nearby_exceedances(vol, expected_score):
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, _, _ = risk_score(conc, vol, 0.0, [], 0.20)
    assert score == expected_score
