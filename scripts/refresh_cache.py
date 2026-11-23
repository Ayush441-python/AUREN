"""Refresh the bundled CSV cache that the API falls back to when Yahoo Finance
blocks or rate-limits the server (common on cloud hosts like Render).

Run from the project root, then commit data/*.csv and redeploy:
    python scripts/refresh_cache.py
"""
import pathlib
import sys
from tempfile import NamedTemporaryFile

# Make `engine` importable when the script is run directly (python scripts/refresh_cache.py)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from engine.data import CACHE, VOL_CACHE, load_prices, load_volumes  # noqa: E402
from engine.universe import SECTORS  # noqa: E402


def _write_csv(frame, path: pathlib.Path) -> None:
    """Stage a cache CSV before replacing it, preserving it on write failures."""
    temporary = NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = pathlib.Path(temporary.name)
    try:
        with temporary:
            frame.to_csv(temporary)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> None:
    tickers = list(SECTORS)
    prices = load_prices(tickers, require_download=True)
    volumes = load_volumes(tickers, require_download=True)
    if prices.empty or volumes.empty:
        sys.exit("Download failed (Yahoo may be rate-limiting). Existing cache left untouched.")

    _write_csv(prices, CACHE)
    _write_csv(volumes, VOL_CACHE)
    print(f"Saved {CACHE} and {VOL_CACHE} ({len(prices)} rows, last date {prices.index[-1]:%Y-%m-%d})")


if __name__ == "__main__":
    main()
