from unittest.mock import patch
import pandas as pd
import api


def test_concentration_rule_agreement():
    tickers = ["NVDA", "COST", "MSFT", "XOM"]
    prices = pd.DataFrame(
        {ticker: range(100 + i, 130 + i) for i, ticker in enumerate(tickers)},
        index=pd.bdate_range("2026-01-02", periods=30),
    )
    with patch.object(api, "load_prices", return_value=prices):
        for first, expected_hit in [(30, False), (30.004, True), (30.01, True)]:
            weights = dict(zip(tickers, [first, 24, 23, 53 - first]))
            result = api.compute_risk(api.PortfolioRequest(weights=weights))
            hit = any(n == 20 and why.startswith("Largest holding") for n, why in result["hits"])
            is_conc = result["concentration"]["is_concentrated"]
            assert hit == expected_hit
            assert is_conc == expected_hit
