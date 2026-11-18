import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    portfolio_returns,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score


def test_zero_weight_holdings_do_not_affect_risk_score():
    # Synthetic correlated prices:
    # A is the held asset (100%)
    # B, C, D are unheld (0%) and highly correlated with each other
    days = 100
    prices = pd.DataFrame({
        "A": [100.0 + i * 0.1 for i in range(days)],
        "B": [50.0 + i * 0.5 for i in range(days)],
        "C": [50.0 + i * 0.51 for i in range(days)],
        "D": [50.0 + i * 0.49 for i in range(days)],
    })

    # Portfolio 1: Held A only
    w1 = pd.Series({"A": 1.0})
    active_w1 = w1[w1 > 0]
    corr1 = correlation(prices, active_w1.index)
    pairs1 = high_pairs(corr1)
    score1, level1, hits1 = risk_score(
        concentration(active_w1),
        volatility(portfolio_returns(prices, active_w1)),
        max_drawdown(portfolio_returns(prices, active_w1)),
        pairs1,
        float(sector_exposure(active_w1).max()),
    )

    # Portfolio 2: Held A with unheld zero-weight tickers B, C, D
    w2 = pd.Series({"A": 1.0, "B": 0.0, "C": 0.0, "D": 0.0})
    active_w2 = w2[w2 > 0]
    corr2 = correlation(prices, active_w2.index)
    pairs2 = high_pairs(corr2)
    score2, level2, hits2 = risk_score(
        concentration(active_w2),
        volatility(portfolio_returns(prices, active_w2)),
        max_drawdown(portfolio_returns(prices, active_w2)),
        pairs2,
        float(sector_exposure(active_w2).max()),
    )

    # Risk scores and pair counts must be identical
    assert pairs1 == []
    assert pairs2 == []
    assert score1 == score2
    assert level1 == level2
    assert hits1 == hits2
