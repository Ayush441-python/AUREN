# AGENT_SUMMARY — Issue #133 (Maths Bounty)

**Issue:** [Maths Bounty] Exactly 50% broad-group exposure adds 15 points only in certain asset orders (Low → Medium)
**Commit:** `7865cb1`
**Files touched:** `engine/metrics.py`, `engine/score.py`, `tests/test_metrics.py`

---

## Root cause

Two compounding problems on a strict `>` boundary.

1. **Order-dependent summation.** `engine/metrics.py:sector_exposure()` aggregated group
   weights with pandas `.sum()`, which is pairwise float addition and therefore *not*
   associative. For the reported portfolio (NVDA 17%, MSFT 28%, AAPL 5% = Big Tech 50%;
   AMD 25% + TSM 25% = AI & Semiconductors 50%) the Big Tech total came out as
   `0.5000000000000001` when the holdings were entered in the order NVDA → MSFT → AAPL,
   and exactly `0.5` in the other five permutations. Reproduced before touching anything:

   ```
   ('NVDA', 'MSFT', 'AAPL') 0.5000000000000001  -> rule fires
   ('NVDA', 'AAPL', 'MSFT') 0.5                 -> rule does not fire
   ('MSFT', 'NVDA', 'AAPL') 0.5                 -> rule does not fire
   ... (remaining 3 orderings also 0.5)
   ```

2. **Zero-slack threshold.** `engine/score.py:risk_score()` evaluated `sector_max > 0.50`.
   The published rule is "More than 50% sits in one sector", so a value one ULP above 0.5
   was enough to add +15 — pushing the controlled portfolio from 20/Low to 35/Medium purely
   on representation noise.

`math.fsum` alone is not sufficient in general: the per-asset `w / w.sum()` normalization
rounds each weight *before* aggregation, so an exactly-balanced portfolio can still land one
ULP above 0.5. A randomized probe over 300k exactly-balanced float portfolios produced 4954
cases (~1.6%) where a correctly-rounded `fsum` group total was still `0.5000000000000001`.
That is why both halves were fixed, matching the issue's two suggested corrections.

## Fix

**`engine/metrics.py`** — aggregate with `math.fsum`, which is exactly rounded and therefore
order-independent:

```python
groups = w.index.map(lambda t: GROUPS.get(t, "Other"))
return w.groupby(groups).agg(lambda g: math.fsum(g)).sort_values(ascending=False)
```

**`engine/score.py`** — a documented strict-boundary tolerance, scoped to the group rule:

```python
SECTOR_LIMIT = 0.50
SECTOR_LIMIT_TOL = 1e-9
...
(sector_max > SECTOR_LIMIT + SECTOR_LIMIT_TOL, 15, ...)
```

`1e-9` is ~4.5 million ULPs of headroom at 0.5 — far above any accumulation noise — while
still being 100,000× smaller than the 0.01 percentage-point granularity the UI accepts, so
no real exposure a user can express is swallowed. 50.01% still scores.

**`tests/test_metrics.py`** — the three regressions the issue asked for:
`test_exact_half_group_is_order_independent` (all six permutations of NVDA/MSFT/AAPL with
AMD and TSM fixed, asserting exact `== 0.5`), `test_exact_half_group_scores_low_in_every_order`
(same six orderings through `risk_score` with the issue's controlled 31% volatility →
asserts 20/Low and that no sector reason is emitted), and
`test_only_strictly_over_half_triggers_the_sector_rule` (49.99% → 0, exactly 50% → 0,
50.01% → 15).

The existing `GROUPS` mapping is untouched, per the issue's request to keep classification
(#67) separate. No threshold other than the group rule was changed — #16 (effective assets)
and #49 (drawdown) are out of scope. No dependencies added; `math` is stdlib.

## Verification

```
python -m pytest -q     ->  25 passed
```

Fail-first confirmed — the new tests were run against the *original* `engine/` (stash,
run, restore) and failed on exactly the ordering the issue names:

```
FAILED tests/test_metrics.py::test_exact_half_group_is_order_independent[order0]
FAILED tests/test_metrics.py::test_exact_half_group_scores_low_in_every_order[order0]
   At index 0 diff: 35 != 20
2 failed, 23 passed
```

End-to-end through the real `/risk` computation path (`load_prices` + cached
`data/prices.csv`), all six orderings now report `max_group = 0.5` with no
"sits in one sector" reason:

```
('NVDA','MSFT','AAPL') max_group=0.5 35 Medium ['Volatility is 35% a year (over 30%)',
                                                'Worst past fall was -31% (deeper than -30%)']
... identical for all six orderings
```

Also ran `python -m py_compile app.py api.py engine/*.py tests/*.py` (clean) and spot-checked
that `sector_exposure` still returns a descending `float64` Series with working `.idxmax()` /
`.items()` / `.get()`, which `app.py` (lines 163–165, 372, 410–413, 850) and `api.py`
(lines 70, 83) rely on.

## Concerns for a reviewer

- **The 35/Medium above is not the bug.** With the repo's real cached prices this portfolio
  genuinely trips volatility (35%) and drawdown (-31%). The issue's "20/Low" expectation
  holds under its *controlled* inputs (vol 31%, no qualifying drawdown), which is what the
  unit test asserts. What the fix guarantees is order-independence and no spurious group
  penalty — verified in both paths.
- **Tolerance is deliberately asymmetric and local.** It is applied only to the group rule,
  the one the issue scopes. The other five rules (`> 0.30`, `< 4`, `> 0.30`, `< -0.30`,
  `>= 2`) still use bare comparisons and remain exposed to the same class of boundary noise
  — tracked by #16 and #49. I did not widen the fix to them.
- `.agg(lambda g: math.fsum(g))` is a Python-level callback rather than a vectorized
  reduction, so it is slower than `.sum()`. Irrelevant at portfolio sizes (≤ 60 tickers),
  worth knowing if group aggregation ever moves to a hot loop.
- `float(exposure.max())` in both callers is unchanged; `max()` over already-exact group
  totals introduces no new error.
- Two process notes: `BOUNTY_TASK.md` and this file were left **untracked** rather than
  swept in with `git add -A`, to keep the commit to one logical change. Add them if your
  pipeline expects them. Git reported CRLF normalization warnings on commit (repo-wide
  setting, not introduced here).
