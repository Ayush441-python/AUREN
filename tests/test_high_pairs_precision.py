"""Regression for issue #39: correlation evidence must justify a strict cutoff."""

import numpy as np
import pandas as pd

from engine.metrics import high_pairs
from engine.score import risk_score


def _correlation_matrix(r_ab: float, r_ac: float, r_bc: float = 0.0) -> pd.DataFrame:
    """A positive-semidefinite three-asset correlation matrix."""
    corr = pd.DataFrame(
        [[1.0, r_ab, r_ac], [r_ab, 1.0, r_bc], [r_ac, r_bc, 1.0]],
        index=["A", "B", "C"], columns=["A", "B", "C"],
    )
    assert np.linalg.eigvalsh(corr.to_numpy()).min() >= -1e-12
    return corr


def test_high_pairs_just_over_threshold_keeps_auditable_value():
    corr = _correlation_matrix(0.704, 0.704)
    pairs = high_pairs(corr)
    assert pairs == [("A", "B", 0.704), ("A", "C", 0.704)]
    assert all(value > 0.7 for _, _, value in pairs)
    score, level, hits = risk_score(
        {"top_weight": 0.2, "effective_assets": 5},
        0.1, -0.05, pairs, 0.2,
    )
    assert score == 15
    assert level == "Low"
    assert len(hits) == 1


def test_high_pairs_excludes_value_exactly_at_strict_boundary():
    assert high_pairs(_correlation_matrix(0.7, 0.704)) == [
        ("A", "C", 0.704),
    ]


def test_high_pairs_preserves_precision_at_custom_threshold():
    assert high_pairs(_correlation_matrix(0.704, 0.699), threshold=0.703) == [
        ("A", "B", 0.704),
    ]


def test_high_pairs_very_small_excess_is_not_rounded_away():
    assert high_pairs(_correlation_matrix(0.7000001, 0.699)) == [
        ("A", "B", 0.7000001),
    ]


def test_high_pairs_perfect_correlation_is_unchanged():
    assert high_pairs(_correlation_matrix(1.0, 0.0)) == [
        ("A", "B", 1.0),
    ]
