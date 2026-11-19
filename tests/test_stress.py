import pandas as pd
import pytest
from engine.stress import stress, custom_shock_feedback


def test_stress_offsetting_shocks():
    # 50% MSFT (Big Tech) and 50% COST (Consumer & Retail)
    weights = pd.Series({"MSFT": 0.5, "COST": 0.5})
    shocks = {"Big Tech": -0.10, "Consumer & Retail": 0.10}
    net = stress(weights, shocks)
    assert net == pytest.approx(0.0)


def test_custom_shock_feedback_all_zero():
    shocks = {"Big Tech": 0.0, "Consumer & Retail": 0.0}
    msg, opts = custom_shock_feedback(0.0, 0.0, shocks)
    assert "Move the sliders" in msg
    assert opts.get("muted") is True


def test_custom_shock_feedback_offsetting_shocks():
    # Issue #127: Two nonzero shocks offset to 0 net impact
    shocks = {"Big Tech": -0.10, "Consumer & Retail": 0.10}
    msg, opts = custom_shock_feedback(0.0, 0.0, shocks)
    assert "selected shocks offset" in msg or "selected sector shocks offset" in msg
    assert "Move the sliders" not in msg


def test_custom_shock_feedback_gain():
    shocks = {"Consumer & Retail": 0.10}
    msg, opts = custom_shock_feedback(0.05, 500.0, shocks)
    assert "gains" in msg
    assert "+5.0%" in msg


def test_custom_shock_feedback_loss():
    shocks = {"Big Tech": -0.10}
    msg, opts = custom_shock_feedback(-0.05, -500.0, shocks)
    assert "declines" in msg
    assert "-5.0%" in msg
    assert opts.get("danger") is True
