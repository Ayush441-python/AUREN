from engine.data import load_prices, load_volumes
import api


def test_usdc_constant_price():
    prices = load_prices(["USDC"], period="1mo")
    assert "USDC" in prices.columns
    assert (prices["USDC"] == 1.0).all()
    assert len(prices) >= 30


def test_usdc_constant_volume():
    vols = load_volumes(["USDC"], period="1mo")
    assert "USDC" in vols.columns
    assert (vols["USDC"] > 0).all()
    assert len(vols) >= 30


def test_pure_usdc_risk_calculation():
    # 100% USDC should have zero volatility and zero drawdown, resulting in score 50 (Medium)
    result = api.compute_risk(api.PortfolioRequest(weights={"USDC": 1.0}))
    assert result["score"] == 50
    assert result["level"] == "Medium"
    assert result["volatility"] == 0.0
    assert result["max_drawdown"] == 0.0
    assert "Volatility is over 30% a year" not in result["reasons"]


def test_macro_defensive_reserve_usdc_scaling():
    # Adding 10% USDC cash should scale down volatility rather than exploding
    result = api.compute_risk(
        api.PortfolioRequest(weights={"SPY": 0.40, "GLD": 0.30, "QQQ": 0.20, "USDC": 0.10})
    )
    # Volatility should be ~14.9% (below 25%), not 80%+
    assert result["volatility"] < 0.25
    assert result["score"] == 50


def test_usdc_liquidity():
    result = api.compute_liquidity(
        api.LiquidityRequest(weights={"USDC": 100}, portfolio_value=10000)
    )
    row = result["assets"][0]
    assert row["ticker"] == "USDC"
    assert row["adv"] == 5_000_000_000.0
    assert row["days_to_exit"] == 0.0
