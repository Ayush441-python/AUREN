import math
import pandas as pd


def avg_daily_value(prices: pd.DataFrame, volumes: pd.DataFrame,
                    window: int = 30,
                    currencies: dict[str, str] | None = None,
                    fx_rates: dict[str, pd.Series | float] | None = None) -> pd.Series:
    """Average daily traded value in USD per ticker over the last `window` days.
    Stocks and ETFs: price x share volume converted to USD. Crypto (-USD): Yahoo already reports
    volume in dollars, so it is used as is."""
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
            traded = (prices[t] * vol).dropna()
            curr = currencies.get(t, "USD")
            if curr and curr.upper() != "USD":
                curr_upper = curr.upper()
                fx = fx_rates.get(curr_upper)
                if fx is None:
                    fx = fx_rates.get(curr)
                if fx is None:
                    # Missing FX series -> report as unavailable
                    continue
                if isinstance(fx, (int, float)):
                    if fx <= 0 or math.isnan(fx):
                        continue
                    traded = traded / fx
                elif isinstance(fx, pd.Series):
                    # Align by date
                    aligned_fx = fx.reindex(traded.index).ffill().bfill()
                    if aligned_fx.isna().all() or (aligned_fx <= 0).any():
                        continue
                    traded = (traded / aligned_fx).dropna()
                else:
                    continue

        if not traded.empty:
            tail_vals = traded.tail(window)
            if not tail_vals.empty:
                out[t] = float(tail_vals.mean())
    return pd.Series(out, dtype=float)


def days_to_exit(position_values: pd.Series, adv: pd.Series,
                 participation: float = 0.10) -> pd.Series:
    """Days needed to sell each position at `participation` of average daily volume."""
    adv = adv.reindex(position_values.index).replace(0, float("nan"))
    return position_values / (participation * adv)
