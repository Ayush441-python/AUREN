from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from engine.data import CACHE, VOL_CACHE, load_prices, load_volumes
from engine.universe import SECTORS


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Keep the existing cache readable until its replacement is complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = Path(temporary.name)
    try:
        with temporary:
            frame.to_csv(temporary)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> None:
    tickers = list(SECTORS)
    _write_csv(load_prices(tickers), CACHE)
    _write_csv(load_volumes(tickers), VOL_CACHE)
    print("Saved data/prices.csv and data/volume.csv")


if __name__ == "__main__":
    main()
