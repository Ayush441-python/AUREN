from unittest.mock import MagicMock, patch

import pytest

from engine.report import ai_report, clean_output


def test_clean_output_complete_think():
    text = "<think>Drafting some thoughts...</think>\nYour risk score is 65."
    assert clean_output(text) == "Your risk score is 65."


def test_clean_output_r1_style_without_opening_tag():
    text = "Okay, user wants a report...\n</think>\n\nYour risk score is 65."
    assert clean_output(text) == "Your risk score is 65."


def test_clean_output_unclosed_think():
    text = "<think>Model truncated mid thought"
    assert clean_output(text) == ""


def test_ai_report_finish_reason_length():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {"content": "<think>Truncated reasoning..."},
                "finish_reason": "length",
            }
        ]
    }
    with (
        patch("engine.report.requests.post", return_value=mock_resp),
        pytest.raises(
            RuntimeError,
            match="The model hit the token limit before finishing the report",
        ),
    ):
        ai_report({"risk_score": 65}, "http://localhost:11434/v1", "", "deepseek-r1:14b")


def test_ai_report_strips_reasoning_and_returns_content():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Reasoning here...\n</think>\n\nYour portfolio is balanced."
                },
                "finish_reason": "stop",
            }
        ]
    }
    with patch("engine.report.requests.post", return_value=mock_resp):
        res = ai_report({"risk_score": 50}, "http://localhost:11434/v1", "", "model")
        assert res == "Your portfolio is balanced."
