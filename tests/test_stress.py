import pytest
import pandas as pd
from unittest.mock import patch
import api


def test_nvda_stress_dollar_calculation():
    """Test that NVDA stress scenarios calculate dollar values with proper precision"""
    dates = pd.bdate_range("2026-01-02", periods=30)
    prices = pd.DataFrame({"NVDA": range(100, 130), "COST": range(150, 180)}, index=dates)
    
    with patch.object(api, "_load_aligned_prices", return_value=prices):
        # Test the 0.1% NVDA weight case that was showing $100 instead of $150
        request = api.PortfolioRequest(weights={"NVDA": 0.1, "COST": 99.9})
        impact = api.compute_risk(request)["stress"]["NVDA falls 15%"]
        
        # Calculate expected dollar change with full precision
        portfolio_size = 1_000_000
        expected_dollar_change = portfolio_size * impact
        
        # The impact should be -0.00015 (0.1% * 15%)
        assert abs(impact - (-0.00015)) < 1e-10, f"Expected impact -0.00015, got {impact}"
        
        # The dollar change should be -$150 (not -$100)
        assert abs(expected_dollar_change - (-150)) < 0.01, f"Expected dollar change -150, got {expected_dollar_change}"
        
        # The portfolio value after shock should be $999,850
        final_value = portfolio_size + expected_dollar_change
        assert abs(final_value - 999850) < 0.01, f"Expected final value 999850, got {final_value}"
