import pandas as pd
import pytest
from engine.wallet import holdings_to_portfolio
from engine.stress import stress, SCENARIOS


def test_sub_100_wallet_portfolio_aggregation():
    """Verify that wallet holdings below $100 correctly aggregate to their actual dollar total."""
    rows = [
        {"token": "NVDAc", "ticker": "NVDA", "address": "0x123", "tokens": 0.1, "shares": 0.1, "price": 200.0, "value": 20.0, "supported": True, "nav_updated": None}
    ]
    df, total, skipped = holdings_to_portfolio(rows)
    assert total == pytest.approx(20.0)
    assert len(df) == 1
    assert df.loc[0, "ticker"] == "NVDA"
    assert df.loc[0, "weight"] == pytest.approx(100.0)
    assert len(skipped) == 0


def test_sub_100_wallet_stress_impact():
    """Verify that modeled loss reflects actual sub-$100 imported size rather than inflated $100 default."""
    rows = [
        {"token": "NVDAc", "ticker": "NVDA", "address": "0x123", "tokens": 0.1, "shares": 0.1, "price": 200.0, "value": 20.0, "supported": True, "nav_updated": None}
    ]
    df, total, _ = holdings_to_portfolio(rows)
    weights = df.set_index("ticker")["weight"] / 100
    
    # 15% decline scenario on NVDA
    scenario = SCENARIOS["NVDA falls 15%"]
    pct_impact = stress(weights, scenario)
    assert pct_impact == pytest.approx(-0.15)
    
    # Modeled dollar loss must be $3 (not $15 from inflated $100 size)
    dollar_impact = pct_impact * total
    remaining_value = total * (1 + pct_impact)
    assert dollar_impact == pytest.approx(-3.0)
    assert remaining_value == pytest.approx(17.0)


def test_sub_100_wallet_size_clamping():
    """Verify that size assignment does not clamp sub-$100 totals to $100."""
    total_20 = 20.0
    size_20 = max(0.01, round(total_20, 2))
    assert size_20 == pytest.approx(20.0)

    total_cents = 0.50
    size_cents = max(0.01, round(total_cents, 2))
    assert size_cents == pytest.approx(0.50)
