"""Refresh the bundled CSV cache that the API falls back to when Yahoo Finance
blocks or rate-limits the server (common on cloud hosts like Render).

Run from the project root, then commit data/*.csv and redeploy:
    python scripts/refresh_cache.py
"""
import pathlib
import sys

# Make `engine` importable when the script is run directly (python scripts/refresh_cache.py)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from engine.data import CACHE, VOL_CACHE, load_prices, load_volumes  # noqa: E402
from engine.universe import SECTORS  # noqa: E402

tickers = list(SECTORS)
prices = load_prices(tickers)
volumes = load_volumes(tickers)
if prices.empty or volumes.empty:
    sys.exit("Download failed (Yahoo may be rate-limiting). Existing cache left untouched.")

prices.to_csv(CACHE)
volumes.to_csv(VOL_CACHE)
print(f"Saved {CACHE} and {VOL_CACHE} ({len(prices)} rows, last date {prices.index[-1]:%Y-%m-%d})")
