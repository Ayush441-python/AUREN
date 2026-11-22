import pandas as pd
from engine.data import ExitTime


def avg_daily_value(prices: pd.DataFrame, volumes: pd.DataFrame,
                    window: int = 30) -> pd.Series:
    """Average daily traded value in USD per ticker over the last `window` days.
    Stocks and ETFs: price x share volume. Crypto (-USD): Yahoo already reports
    volume in dollars, so it is used as is."""
    out = {}
    for t in prices.columns:
        if t not in volumes.columns:
            continue
        vol = volumes[t].dropna()
        traded = vol if t.endswith("-USD") else (prices[t] * vol).dropna()
        out[t] = float(traded.tail(window).mean())
    return pd.Series(out, dtype=float)


def days_to_exit(position_values: pd.Series, adv: pd.Series,
                 participation: float = 0.10) -> pd.Series:
    """Days needed to sell each position at `participation` of average daily volume."""
    adv = adv.reindex(position_values.index).replace(0, float("nan"))
    return position_values / (participation * adv)


def find_slowest_ticker(assets: list[dict]) -> Optional[dict]:
    """Find the asset with the maximum exact days_to_exit.
    
    Uses exact values without rounding to determine the true slowest ticker.
    """
    if not assets:
        return None
    
    # Find the asset with the maximum exact days_to_exit
    slowest = max(assets, key=lambda asset: asset["days_to_exit"].exact_value)
    return slowest


def max_days_to_exit(assets: list[dict]) -> float:
    """Calculate the maximum exact days_to_exit across all assets.
    
    Uses exact values without rounding to determine the true maximum.
    """
    if not assets:
        return 0.0
    
    # Return the maximum exact value
    return max(asset["days_to_exit"].exact_value for asset in assets)