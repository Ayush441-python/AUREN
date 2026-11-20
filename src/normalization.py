"""
Robust weight normalization and concentration scoring fix for Issue #111.
Eliminates binary score flip caused by floating point precision artifacts.
"""
from decimal import Decimal, ROUND_HALF_UP

def normalize_portfolio_weights(weights_dict):
    """
    Normalizes input weights using exact Decimals to avoid float division anomalies
    (e.g., dividing by 0.9999999999999999).
    """
    raw_vals = [Decimal(str(v)) for v in weights_dict.values()]
    total = sum(raw_vals)
    if total == Decimal('0'):
        raise ValueError("Sum of weights cannot be zero.")
    
    # If weights are already percentages summing to 100
    if total > Decimal('1.5'):
        factor = total
    else:
        factor = total

    normalized = {}
    for k, v in weights_dict.items():
        d_val = Decimal(str(v))
        # Compute exact ratio rounded to 6 decimal places
        ratio = float((d_val / factor).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
        normalized[k] = ratio
        
    return normalized

def determine_concentration_tier(top_weight):
    """
    Evaluates concentration tier with explicit epsilon guard against float jitter.
    """
    EPSILON = 1e-9
    # Strict 30% boundary check: 30% exact is Low (<= 0.30 + EPSILON)
    if top_weight <= 0.30 + EPSILON:
        return 15, "Low"
    elif top_weight <= 0.50 + EPSILON:
        return 35, "Medium"
    else:
        return 50, "High"
