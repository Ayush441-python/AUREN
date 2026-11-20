# Issue #159 — Missing AAPL closes shift unrelated MSFT liquidity 30 sessions into the past

## Root cause

`analyze()` in `app.py` loaded prices and immediately reduced them to complete cases:

```python
prices = get_prices(tuple(sorted(w.index))).dropna()
```

`DataFrame.dropna()` with no arguments drops any **row** in which *any* selected ticker is
missing a price. That is the right frame for the metrics that need a common calendar —
portfolio returns, volatility, drawdown, correlation — because those compare assets to each
other day by day.

The Liquidity tab then reused that same frame:

```python
adv = avg_daily_value(prices, volumes, window=30)
```

`avg_daily_value` computes a per-asset measure: for each ticker it takes `price * volume`
and averages the **last `window` observations of that ticker**. Feeding it the complete-case
frame means the window of every asset ends at the last session on which *all* assets had a
price. One asset's data gap therefore rewinds the 30-session window of every other asset,
even when that asset's own observations are complete and unchanged.

In the reported case the last session common to MSFT and AAPL is February 13, while MSFT's
own observations continue through March 27. MSFT's window silently moved to the earlier,
high-volume half of its history: $1,000,000/day instead of $1,000/day, so a $6,000 position
at 10% participation read as 0.06 days ("Instant") instead of 60 days ("Illiquid").

The engine function is not at fault — `engine/liquidity.py` already drops NaNs per ticker.
The defect is purely the caller handing it the wrong frame.

## Fix

`app.py` only — 9 insertions, 3 deletions, no engine or config changes:

1. `analyze()` keeps **both** frames: `asset_prices` (the per-asset frame as loaded) and
   `prices = asset_prices.dropna()` (complete case). The `len(prices) < 30` sufficiency
   guard still runs against the complete-case frame, so the "not enough data" behaviour is
   unchanged.
2. Both are returned in the analysis result (`asset_prices=asset_prices` added to the dict).
3. The Liquidity tab passes `asset_prices` to `avg_daily_value`.

Everything that needs a common calendar still uses `prices`: `portfolio_returns`,
`correlation`, and the rebased performance chart (`norm = prices / prices.iloc[0] * 100`,
which needs a shared starting session to be comparable). Only the per-asset liquidity
input changed. This matches the fix proposed in the issue.

## Verification

**Engine-level, the snippet from the issue** — all three assertions hold:

```
all present, complete-case : 60.0
AAPL gaps, complete-case   : 0.06   <- the frame the app used to pass
AAPL gaps, per-asset frame : 60.0   <- the frame the app now passes
```

**Rendered app, offline Streamlit AppTest replay.** I reproduced the reporter's experiment
against the real Liquidity tab: all 60 MSFT closes, all 60 MSFT volumes, weights
(MSFT 60% / AAPL 40% of $10,000) and the 10% participation rate held fixed; only the 30
latest AAPL closes removed; `st.cache_data.clear()` between cases; `engine.data.load_prices`
/ `load_volumes` patched to serve the synthetic frames, so there are no market-data
requests. Reading the MSFT row out of the rendered table:

| Inputs | before fix | after fix |
| --- | --- | --- |
| Both assets have all 60 closing prices | $1,000 · 60.00d · Illiquid (1d+) | $1,000 · 60.00d · Illiquid (1d+) |
| Only AAPL's latest 30 closing prices missing | $1,000,000 · 0.06d · Instant (<0.1d) | $1,000 · 60.00d · Illiquid (1d+) |

The before-fix column reproduces the issue's table exactly, which confirms the replay
exercises the reported path and not something adjacent.

The replay script (run from the repository root, not committed — see Concerns):

```python
import pandas as pd, streamlit as st
from streamlit.testing.v1 import AppTest
import engine.data as data

DATES = pd.bdate_range("2026-01-05", periods=60)
VOLUMES = pd.DataFrame({"MSFT": [10_000] * 30 + [10] * 30, "AAPL": 200_000}, index=DATES)
PF = pd.DataFrame([{"ticker": "MSFT", "weight": 60.0}, {"ticker": "AAPL", "weight": 40.0}])

def serve(frame):   # synthetic columns for MSFT/AAPL, filler for any warm-up ticker
    return lambda tickers, period="2y": pd.DataFrame(
        {t: frame[t] if t in frame.columns else frame["MSFT"] for t in tickers},
        index=frame.index)

def replay(gap_aapl):
    closes = pd.DataFrame({"MSFT": 100.0, "AAPL": 50.0}, index=DATES)
    if gap_aapl:
        closes.loc[DATES[-30:], "AAPL"] = float("nan")
    data.load_prices, data.load_volumes = serve(closes), serve(VOLUMES)
    st.cache_data.clear()
    at = AppTest.from_file("app.py", default_timeout=300)
    at.session_state["size"] = 10_000.0
    at.run()                                   # warm-up run on the default preset
    at.selectbox[0].select("Custom / Edited")  # stop the preset reclaiming pf_df
    at.session_state["pf_df"] = PF
    at.session_state["pf_v"] += 1
    at.run()
    assert not at.exception, at.exception
    table = next(d.value for d in at.dataframe if "Days to Exit" in d.value.columns)
    return table.set_index("Ticker").loc["MSFT"]

for label, gap in [("all 60 closes", False), ("AAPL's latest 30 missing", True)]:
    r = replay(gap)
    print(label, r["30D Daily Traded ($)"], r["Days to Exit"], r["Liquidity Status"])
```

**Test suite:** `python -m pytest -q` → **10 passed**. `python -m py_compile app.py` clean,
`import api` clean. The repo has no lint, typecheck, or JS tooling configured.

## Concerns for a reviewer

- **No automated regression test added.** The defect is in `app.py` top-level script wiring,
  not in `engine/`, so a `tests/` unit test of `avg_daily_value` would pass both before and
  after the fix and would guard nothing. Covering it properly needs the AppTest replay
  above, which boots the whole app twice and monkeypatches `engine.data`. I kept the change
  minimal per the brief and left that out; if you want it in CI, the script is ready to drop
  into `tests/` as-is.
- **Behaviour change beyond the reported case, and it is intentional:** each asset's 30-day
  liquidity window now ends at that asset's own last observation. For an asset whose feed
  stopped long ago, the window is now that asset's own (older) sessions rather than being
  pinned to the portfolio's last common session. That is the correct per-asset reading and is
  what `avg_daily_value`'s internal per-ticker `.dropna()` already assumed, but it does mean
  a stale ticker's ADV can be computed from stale sessions without a visible warning. Out of
  scope here; worth a separate staleness indicator.
- **This does not address issue #154**, which concerns the volume available for the asset
  being measured. Only the cross-asset *price* alignment is fixed.
- **Commit scope.** The working tree arrived with all 21 tracked files rewritten with CRLF
  line endings — 3,393 insertions / 3,393 deletions and **zero** content changes
  (`git diff --ignore-all-space` is empty). I did not commit that churn. `app.py` is
  committed with LF endings, matching `HEAD`, so its diff is only the 4 hunks of this fix.
  The other files are left modified in the working tree, untouched. `BOUNTY_TASK.md` (the
  task brief) is also left uncommitted.
