import pandas as pd


def avg_daily_value(prices: pd.DataFrame, volumes: pd.DataFrame,
                    window: int = 30,
                    return_counts: bool = False) -> pd.Series | tuple[pd.Series, pd.Series]:
    """Average daily traded value in USD per ticker over the last `window` trading sessions.
    Stocks and ETFs: price x share volume. Crypto (-USD): Yahoo already reports
    volume in dollars, so it is used as is.

    Selects the last `window` price sessions per ticker first and aligns volumes
    to those exact dates, avoiding inclusion of older trades when volume observations
    are missing within the window. If zero sessions are observed within the window,
    the estimate is unknown (NaN).
    """
    out = {}
    counts = {}
    for t in prices.columns:
        if t not in volumes.columns:
            continue
        p = prices[t].dropna()
        if p.empty or window <= 0:
            out[t] = float("nan")
            counts[t] = 0
            continue

        if isinstance(p.index, pd.DatetimeIndex) and not p.index.is_monotonic_increasing:
            p = p.sort_index()

        p_win = p.tail(window)
        vol_series = volumes[t]

        target_idx = p_win.index
        if isinstance(target_idx, pd.DatetimeIndex) and isinstance(vol_series.index, pd.DatetimeIndex):
            if target_idx.tz is not None and vol_series.index.tz is None:
                vol_series = vol_series.tz_localize(target_idx.tz)
            elif target_idx.tz is None and vol_series.index.tz is not None:
                vol_series = vol_series.tz_localize(None)
            elif target_idx.tz != vol_series.index.tz:
                vol_series = vol_series.tz_convert(target_idx.tz)

        vol = vol_series.reindex(target_idx)
        traded = vol if t.endswith("-USD") else (p_win * vol)
        valid = traded.dropna()
        counts[t] = int(len(valid))
        if valid.empty:
            out[t] = float("nan")
        else:
            out[t] = float(valid.mean())

    s_out = pd.Series(out, dtype=float)
    s_counts = pd.Series(counts, dtype=int)
    if return_counts:
        return s_out, s_counts
    return s_out


def observed_sessions(prices: pd.DataFrame, volumes: pd.DataFrame,
                      window: int = 30) -> pd.Series:
    """Number of valid trading sessions with both price and volume observed
    within the last `window` price sessions."""
    _, counts = avg_daily_value(prices, volumes, window=window, return_counts=True)
    return counts


def days_to_exit(position_values: pd.Series, adv: pd.Series,
                 participation: float = 0.10) -> pd.Series:
    """Days needed to sell each position at `participation` of average daily volume."""
    adv = adv.reindex(position_values.index).replace(0, float("nan"))
    return position_values / (participation * adv)
