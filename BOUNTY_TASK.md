# Bounty Fix

**Reward:** $1,000.00
**Issue:** https://github.com/Ayush441-python/AUREN/issues/159
**Repo:** https://github.com/Ayush441-python/AUREN

---

## Issue

[Maths Bounty] Missing AAPL closes shift unrelated MSFT liquidity 30 sessions into the past

## Observed

The Liquidity tab can silently move the 30-session calculation backward for an unrelated holding. In a local Streamlit AppTest on main commit 22d21fdfd29778c0c0dbd857853b41a13fb765fc, I held all 60 MSFT prices, all 60 MSFT volumes, weights, portfolio size and participation rate fixed. Removing only the 30 latest AAPL closes flipped MSFT's label from Illiquid to Instant.

| Inputs | MSFT 30D daily traded | MSFT Days to Exit | MSFT status |
| --- | ---: | ---: | --- |
| Both assets have all 60 closing prices | $1,000 | 60.00 | Illiquid (1d+) |
| Only AAPL's latest 30 closing prices are missing | $1,000,000 | 0.06 | Instant (<0.1d) |
| Second case, with the proposed fix | $1,000 | 60.00 | Illiquid (1d+) |

The two runs clear Streamlit's data cache between cases. This is a synthetic offline replay with no market-data requests. Related issue #154 changes the volume available for the asset being measured. Here all MSFT observations are present and unchanged. The cross-asset price alignment alone causes the error.

## Reproduce

From the repository root, run with pandas installed:

~~~python
import pandas as pd
from engine.liquidity import avg_daily_value, days_to_exit

dates = pd.bdate_range("2026-01-05", periods=60)
closes = pd.DataFrame({"MSFT": 100.0, "AAPL": 50.0}, index=dates)
volumes = pd.DataFrame({"MSFT": [10_000] * 30 + [10] * 30,
                        "AAPL": 200_000}, index=dates)
positions = pd.Series({"MSFT": 6_000.0, "AAPL": 4_000.0})

def msft_days(price_history):
    adv = avg_daily_value(price_history, volumes, window=30)
    return days_to_exit(positions, adv, participation=0.10).loc["MSFT"]

assert msft_days(closes.dropna()) == 60
closes.loc[dates[-30:], "AAPL"] = float("nan")
assert msft_days(closes.dropna()) == 0.06  # The app's current liquidity input
assert msft_days(closes) == 60           # The same MSFT observations
~~~

## Cause and proposed fix

[The portfolio analysis](https://github.com/Ayush441-python/AUREN/blob/22d21fdfd29778c0c0dbd857853b41a13fb765fc/app.py#L151-L170) drops a row whenever any selected ticker lacks a price. [The Liquidity tab](https://github.com/Ayush441-python/AUREN/blob/22d21fdfd29778c0c0dbd857853b41a13fb765fc/app.py#L651-L659) reuses that frame. The last common session is February 13, while MSFT observations continue through March 27. At 10% participation, a $6,000 position divided by $100/day implies 60 days. The stale window implies $100,000/day and 0.06 days.

Keep both frames in the analysis result. Keep using the complete-case frame for the portfolio return and correlation calculations, and pass the original per-asset price frame to avg_daily_value. The local rendered liquidity replay then reports 60 days in both cases. All 10 repository tests passed with the proposed change.

[Technical post tagging @Aurenz_io](https://x.com/bountyco2026/status/2123812716683088376)

If accepted under the $50 maths bounty, the Base USDC payout address is 0x7fdd87b05d8f006298dcb0dd13e15e4eb7c77084. A minimal patch and the full AppTest replay are available for review.

---

## Process

### 1. Orient yourself first
Before touching any code:
- Read the README and any relevant docs
- Run: find . -type f | grep -v node_modules | grep -v .git | grep -v dist | head -60
- Grep for the key terms from the issue title to find the relevant files
- Read the files around the bug — understand what's currently happening

### 2. Find and read the tests
- Look for test files near the relevant code (*.test.ts, *.spec.js, __tests__, etc.)
- Read them — they tell you what behavior is expected
- Understand what a passing fix looks like before writing a line

### 3. Implement the fix
- Make the MINIMAL change that fixes the issue — nothing more
- Do not refactor, rename, reorganize, or clean up unrelated code
- Do not add dependencies unless the issue explicitly requires it
- Do not modify config files (package.json, tsconfig.json, etc.) unless that IS the fix
- One logical change, one commit

### 4. Verify
- Run the test suite: check package.json scripts for "test", "lint", "typecheck"
  Common commands: npm test, yarn test, pnpm test, pytest, go test ./..., cargo test
- If TypeScript is present: npx tsc --noEmit
- Fix any test failures your change caused — if a test was wrong before, update it

### 5. Commit and document
- git add -A
- git commit -m "fix: [Maths Bounty] Missing AAPL closes shift unrelated MSFT liquidity 30 ses"
- Write AGENT_SUMMARY.md with:
  - Root cause: what was wrong and why
  - Fix: what you changed and the reasoning
  - Verification: how to confirm it works
  - Concerns: anything a reviewer should know

---

## Stop conditions

If ANY of these are true, write "UNCERTAIN: [reason]" at the top of AGENT_SUMMARY.md, make NO code changes, and stop:
- The fix requires changing more than ~5 files
- You cannot determine what the correct behavior should be
- The issue requires a database migration, API key, or external service
- You find 3+ open PRs already attempting this fix (high competition)
- The repo is not in a language/framework you can reason about confidently

A clean UNCERTAIN is better than a bad PR.
