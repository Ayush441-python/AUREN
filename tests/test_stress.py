"""Regression tests for custom shock simulator feedback (issue #127)."""
import pandas as pd

from engine.stress import any_shock_active, stress


def test_offsetting_shocks_net_zero_but_sliders_active():
    w = pd.Series({"MSFT": 0.5, "COST": 0.5})
    shocks = {"Big Tech": -0.10, "Consumer & Retail": 0.10}
    assert stress(w, shocks) == 0
    assert any_shock_active(shocks)


def test_untouched_sliders_still_prompt():
    shocks = {"Big Tech": 0, "Consumer & Retail": 0}
    assert not any_shock_active(shocks)


def test_single_nonzero_shock_is_active():
    assert any_shock_active({"Big Tech": -0.10})
    assert not any_shock_active({})
