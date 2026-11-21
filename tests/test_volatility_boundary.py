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


def test_exact_30_percent_annualized_volatility():
    # 253 prices yielding 252 returns: one 30% jump followed by 251 zeroes.
    # Mathematical proof: annual volatility is sqrt(252 * (0.3^2 / 252)) = 0.30 exactly.
    prices = pd.DataFrame({"NVDA": [100.0] + [130.0] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    vol = volatility(returns)
    assert len(returns) == 252
    assert vol == pytest.approx(0.30)

    score, level, hits = risk_score(
        concentration(weights),
        vol,
        max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )
    assert score == 50
    assert level == "Medium"
    assert not any("Volatility is" in why for _, why in hits)


def test_terminal_price_100_control():
    prices = pd.DataFrame({"NVDA": [100.0] + [100.0] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    vol = volatility(returns)
    score, level, hits = risk_score(
        concentration(weights),
        vol,
        max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )
    assert vol == pytest.approx(0.0)
    assert score == 50
    assert level == "Medium"
    assert not any("Volatility is" in why for _, why in hits)


def test_terminal_price_129_99_control():
    prices = pd.DataFrame({"NVDA": [100.0] + [129.99] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    vol = volatility(returns)
    score, level, hits = risk_score(
        concentration(weights),
        vol,
        max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )
    assert vol < 0.30
    assert score == 50
    assert level == "Medium"
    assert not any("Volatility is" in why for _, why in hits)


def test_terminal_price_130_01_control():
    prices = pd.DataFrame({"NVDA": [100.0] + [130.01] * 252})
    weights = pd.Series({"NVDA": 1.0})
    returns = portfolio_returns(prices, weights)
    vol = volatility(returns)
    score, level, hits = risk_score(
        concentration(weights),
        vol,
        max_drawdown(returns),
        high_pairs(correlation(prices, weights.index)),
        float(sector_exposure(weights).max()),
    )
    assert vol > 0.30
    assert score == 70
    assert level == "High"
    assert any("Volatility is" in why for _, why in hits)


def test_risk_score_exact_thirty_percent_boundary():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, level, hits = risk_score(conc, 0.30, -0.05, [], 0.20)
    assert score == 0
    assert level == "Low"
    assert hits == []


def test_risk_score_above_noise_band():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, level, hits = risk_score(conc, 0.30 + 1e-9, -0.05, [], 0.20)
    assert score == 20
    assert hits == [(20, "Volatility is 30% a year (over 30%)")]
