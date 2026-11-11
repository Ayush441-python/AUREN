import numpy as np
import pandas as pd


def concentration(w: pd.Series) -> dict:
    hhi = float((w ** 2).sum())  # 1.0 = everything in one asset
    return {
        "top_asset": w.idxmax(),
        "top_weight": float(w.max()),
        "effective_assets": 1 / hhi,  # "you really own this many assets"
    }