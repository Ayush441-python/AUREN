from typing import Optional, Dict, Union
import pandas as pd


def avg_daily_value(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    window: int = 30,
    currencies: Optional[Dict[str, str]] = None,
    fx_rates: Optional[Dict[str, Union[float, pd.Series]]] = None,
) -> pd.Series:
    """Average daily traded value in USD per ticker over the last `window` days.
    Stocks and ETFs: price x share volume x fx_rate_to_usd.
    Crypto (-USD): Yahoo already reports volume in dollars, so it is used as is.
    If an asset is quoted in a non-USD currency and no valid FX conversion rate
    is available, its ADV is reported as NaN (unavailable) to prevent dangerous
    understatements of liquidation times.
    """
    out = {}
    currencies = currencies or {}
    fx_rates = fx_rates or {}

    for t in prices.columns:
        if t not in volumes.columns:
            continue
        vol = volumes[t].dropna()
        if t.endswith("-USD"):
            traded = vol
        else:
            curr = (currencies.get(t) or "USD").upper()
            if curr == "USD":
                traded = (prices[t] * vol).dropna()
            else:
                # Non-USD quoted asset: requires currency conversion to USD
                rate = fx_rates.get(curr)
                if rate is None:
                    # Missing FX series/rate: report as unavailable
                    out[t] = float("nan")
                    continue
                if isinstance(rate, (int, float)):
                    if rate <= 0 or not pd.notna(rate):
                        out[t] = float("nan")
                        continue
                    traded = (prices[t] * vol * float(rate)).dropna()
                elif isinstance(rate, pd.Series):
                    aligned_rate = rate.reindex(prices.index).ffill().bfill()
                    if aligned_rate.isna().all() or (aligned_rate <= 0).any():
                        out[t] = float("nan")
                        continue
                    traded = (prices[t] * vol * aligned_rate).dropna()
                else:
                    out[t] = float("nan")
                    continue

        if traded.empty:
            out[t] = float("nan")
        else:
            out[t] = float(traded.tail(window).mean())
    return pd.Series(out, dtype=float)


def days_to_exit(position_values: pd.Series, adv: pd.Series,
                 participation: float = 0.10) -> pd.Series:
    """Days needed to sell each position at `participation` of average daily volume."""
    adv = adv.reindex(position_values.index).replace(0, float("nan"))
    return position_values / (participation * adv)