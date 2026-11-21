"""
AUREN Quant Engine - Independent Asset Liquidity Calculation
Fix for Issue #159: Ensure missing cross-asset closing prices do not shift
unrelated holding's 30-session lookback window.
"""
from typing import Dict, List, Any
import numpy as np

def calculate_holding_liquidity_independent(
    asset_symbol: str,
    asset_prices: List[float],
    asset_volumes: List[float],
    portfolio_weights: Dict[str, float],
    portfolio_size_usd: float,
    participation_rate: float = 0.10,
    lookback_sessions: int = 30
) -> Dict[str, Any]:
    # Ensure calculation evaluates strictly the holding's own contiguous valid trading sessions
    valid_pairs = [(p, v) for p, v in zip(asset_prices, asset_volumes) if p is not None and v is not None and not np.isnan(p) and not np.isnan(v)]
    
    if len(valid_pairs) < lookback_sessions:
        # Fallback to available window without shifting cross-asset dates
        target_pairs = valid_pairs
    else:
        target_pairs = valid_pairs[-lookback_sessions:]
        
    if not target_pairs:
        return {'daily_traded_usd': 0.0, 'days_to_exit': float('inf'), 'status': 'Illiquid'}
        
    daily_traded_usd = float(np.mean([p * v for p, v in target_pairs]))
    asset_weight = portfolio_weights.get(asset_symbol, 0.0)
    position_usd = portfolio_size_usd * asset_weight
    
    daily_capacity_usd = daily_traded_usd * participation_rate
    
    if daily_capacity_usd <= 0.0:
        days_to_exit = float('inf')
    else:
        days_to_exit = position_usd / daily_capacity_usd
        
    if days_to_exit < 0.1:
        status = 'Instant (<0.1d)'
    elif days_to_exit <= 1.0:
        status = 'Liquid (<=1d)'
    else:
        status = 'Illiquid (1d+)'
        
    return {
        'asset': asset_symbol,
        'daily_traded_usd': round(daily_traded_usd, 2),
        'days_to_exit': round(days_to_exit, 2),
        'status': status
    }

if __name__ == '__main__':
    # Test case 1: MSFT with full 60 prices
    msft_p = [100.0] * 60
    msft_v = [10.0] * 60
    weights = {'MSFT': 1.0}
    res = calculate_holding_liquidity_independent('MSFT', msft_p, msft_v, weights, 6000.0, participation_rate=0.10)
    assert res['days_to_exit'] == 60.0, f'Expected 60.0 got {res["days_to_exit"]}'
    assert res['status'] == 'Illiquid (1d+)'
    print('Auren #159 Unit Test: PASS (Exit 0)')
