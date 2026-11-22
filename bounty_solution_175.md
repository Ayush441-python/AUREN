2. Code Patch / Fix

**File: `api.py`**

Locate the `/risk` endpoint logic where `portfolio_values` and `drawdowns` are computed and serialized. Ensure they are reindexed to match the original `dates` and that the first value is explicitly set to the baseline (100 for index, 0 for drawdown) to handle the `pct_change` NaN issue.

```python
# Inside the /risk endpoint, after computing portfolio_values and drawdowns:

# Ensure the portfolio series starts at 100 (or the initial value) and is aligned with dates
# If using pct_change, the first value is NaN. We need to fill it with the initial value.
# Assuming portfolio_values is a pd.Series or list derived from prices.

# 1. Reindex/Align to original dates
# If portfolio_values is a Series, ensure it has the same index as 'dates'
if isinstance(portfolio_values, pd.Series):
    portfolio_values = portfolio_values.reindex(dates)
else:
    # If it's a list, convert to Series with dates index
    portfolio_values = pd.Series(portfolio_values, index=dates)

# 2. Handle the first value (baseline)
# The first day's portfolio