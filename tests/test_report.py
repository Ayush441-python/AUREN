"""Regression tests for think-tag stripping and finish_reason (issue #112)."""
from unittest.mock import MagicMock, patch

import pytest

from engine.report import ai_report, clean_output


def _fake(content, finish="stop"):
    r = MagicMock()
    r.ok = True
    r.json.return_value = {"choices": [{"message": {"content": content},
                                      "finish_reason": finish}]}
    return r


def _call(content, finish="stop"):
    with patch("engine.report.requests.post",
               return_value=_fake(content, finish)) as p:
        out = ai_report({"risk_score": 65}, "http://localhost:11434/v1",
                        "", "deepseek-r1:14b")
        return out, p


def test_closed_think_pair_stripped():
    out, _ = _call("<think>draft</think>\nYour score is 65.")
    assert out == "Your score is 65."


def test_r1_style_closing_tag_only():
    out, _ = _call("Okay, the user wants a draft.\n</think>\n\nYour risk score is 65.")
    assert out == "Your risk score is 65."
    assert "user wants" not in out


def test_truncated_inside_think_raises():
    with pytest.raises(RuntimeError, match="token limit"):
        _call("<think>Okay let me think about NVDA</think>", "length")


def test_unclosed_think_tag_yields_empty_and_errors():
    # finish_reason=stop but content ends inside an unclosed think block:
    # clean_output drops everything, ai_report raises the empty-answer error.
    with pytest.raises(RuntimeError, match="empty answer"):
        _call("<think>reasoning that never closes", "stop")


def test_normal_report_untouched():
    out, _ = _call("Your risk score is 65. Past data does not predict the future.")
    assert "65" in out
