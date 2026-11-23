import pandas as pd
from engine.data import STABLECOIN_TICKERS


def avg_daily_value(prices: pd.DataFrame, volumes: pd.DataFrame,
                    window: int = 30) -> pd.Series:
    """Average daily traded value in USD per ticker over the last `window` days.
    Stocks and ETFs: price x share volume. Crypto (-USD) and stablecoins:
    already dollar-denominated, so volume is used as is without FX conversion."""
    out = {}
    for t in prices.columns:
        if t not in volumes.columns:
            continue
        vol = volumes[t].dropna()
        traded = vol if (t.endswith("-USD") or t in STABLECOIN_TICKERS) else (prices[t] * vol).dropna()
        out[t] = float(traded.tail(window).mean())
    return pd.Series(out, dtype=float)


def days_to_exit(position_values: pd.Series, adv: pd.Series,
                 participation: float = 0.10) -> pd.Series:
    """Days needed to sell each position at `participation` of average daily volume."""
    adv = adv.reindex(position_values.index).replace(0, float("nan"))
    return position_values / (participation * adv)