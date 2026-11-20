from itertools import permutations

import numpy as np
import pandas as pd
import pytest

from engine.metrics import correlation_and_pairs
from engine.score import risk_score


def fixture_prices(b_first=0):
    # Sum(a)=sum(b)=0, a.b=7, a.a=b.b=10 before the optional perturbation.
    a = np.array([2., 1., -1., -2., 0., 0.] + [0.]*24)
    b = np.array([b_first, 2., -1., -2., 0., 1.] + [0.]*24)
    returns = np.column_stack((a, a, b, -a)) / 64
    return pd.DataFrame(64 * np.vstack([np.ones(4), np.cumprod(1 + returns, axis=0)]),
                        columns=['AAPL', 'MSFT', 'COST', 'GLD'])


def test_strict_seven_tenths_does_not_score_in_any_asset_order():
    prices = fixture_prices()
    expected = {frozenset(('AAPL', 'MSFT'))}
    for order in permutations(prices.columns):
        _, pairs = correlation_and_pairs(prices, order)
        assert {frozenset((a, b)) for a, b, _ in pairs} == expected
        assert risk_score({'top_weight': .5, 'effective_assets': 32/11},
                          .105, -.035, pairs, .75)[:2] == (50, 'Medium')


@pytest.mark.parametrize('delta,qualifies', [(2.**-38, True), (-2.**-38, False)])
def test_genuinely_distinct_nearby_correlations_are_not_folded_into_a_tolerance(delta, qualifies):
    prices = fixture_prices(delta)
    for order in (list(prices), list(reversed(prices.columns))):
        _, result = correlation_and_pairs(prices, order)
        pairs = {frozenset((a, b)) for a, b, _ in result}
        assert (frozenset(('AAPL', 'COST')) in pairs) == qualifies
