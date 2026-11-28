RULE_TABLE = [
    (20, "Largest holding is over 30%"),
    (15, "Effective number of assets is below 4"),
    (20, "Volatility is over 30% a year"),
    (15, "Worst past fall is deeper than -30%"),
    (15, "Two or more pairs of assets with correlation over 0.7"),
    (15, "More than 50% sits in one sector"),
]


def risk_score(conc: dict, vol: float, mdd: float, pairs: list, sector_max: float):
    rules = [
        (conc["top_weight"] > 0.30, 20,
         f"Largest holding is {conc['top_weight']:.0%} (over 30%)"),
        (conc["effective_assets"] < 4, 15,
         f"Behaves like only {conc['effective_assets']:.1f} assets"),
        (vol > 0.30, 20,
         f"Volatility is {vol:.0%} a year (over 30%)"),
        (mdd < -0.30, 15,
         f"Worst past fall was {mdd:.0%} (deeper than -30%)"),
        (len(pairs) >= 2, 15,
         f"{len(pairs)} pairs of assets move closely together"),
        (sector_max > 0.50, 15,
         f"{sector_max:.0%} sits in one sector"),
    ]
    hits = [(pts, why) for hit, pts, why in rules if hit]
    score = sum(p for p, _ in hits)
    level = "Low" if score < 35 else "Medium" if score < 65 else "High"
    return score, level, hits