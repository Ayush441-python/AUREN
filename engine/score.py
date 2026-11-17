import numpy as np

RULE_TABLE = [
    (20, "Largest holding is over 30%"),
    (15, "Effective number of assets is below 4"),
    (20, "Volatility is over 30% a year"),
    (15, "Worst past fall is deeper than -30%"),
    (15, "Two or more pairs of assets with correlation over 0.7"),
    (15, "More than 50% sits in one sector"),
]


def risk_score(conc: dict, vol: float, mdd: float, pairs: list, sector_max: float):
    vol_val = 0.0 if (vol is None or np.isnan(vol) or np.isinf(vol)) else float(vol)
    mdd_val = 0.0 if (mdd is None or np.isnan(mdd) or np.isinf(mdd)) else float(mdd)
    sector_val = 0.0 if (sector_max is None or np.isnan(sector_max) or np.isinf(sector_max)) else float(sector_max)
    top_w = conc.get("top_weight", 0.0) if conc else 0.0
    if top_w is None or np.isnan(top_w) or np.isinf(top_w):
        top_w = 0.0
    eff_a = conc.get("effective_assets", 0.0) if conc else 0.0
    if eff_a is None or np.isnan(eff_a) or np.isinf(eff_a):
        eff_a = 0.0

    rules = [
        (top_w > 0.30, 20,
         f"Largest holding is {top_w:.0%} (over 30%)"),
        (eff_a < 4, 15,
         f"Behaves like only {eff_a:.1f} assets"),
        (vol_val > 0.30, 20,
         f"Volatility is {vol_val:.0%} a year (over 30%)"),
        (mdd_val < -0.30, 15,
         f"Worst past fall was {mdd_val:.0%} (deeper than -30%)"),
        (len(pairs) >= 2, 15,
         f"{len(pairs)} pairs of assets move closely together"),
        (sector_val > 0.50, 15,
         f"{sector_val:.0%} sits in one sector"),
    ]
    hits = [(pts, why) for hit, pts, why in rules if hit]
    score = sum(p for p, _ in hits)
    level = "Low" if score < 35 else "Medium" if score < 65 else "High"
    return score, level, hits