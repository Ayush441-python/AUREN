from unittest.mock import MagicMock, patch

import pytest
from engine.report import ai_report, clean_output


def test_clean_output_closed_think():
    text = "<think>internal reasoning</think>\nYour score is 65."
    assert clean_output(text) == "Your score is 65."


def test_clean_output_r1_style_without_open_tag():
    text = "Drafting internal thoughts...\n</think>\n\nYour risk score is 65."
    assert clean_output(text) == "Your risk score is 65."


def test_clean_output_unclosed_think():
    text = "<think>Truncated reasoning without closing tag"
    assert clean_output(text) == ""


def test_ai_report_raises_on_length_truncation():
    metrics = {"risk_score": 65}
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {"content": "<think>Truncated inside think..."},
                "finish_reason": "length",
            }
        ]
    }
    with patch("engine.report.requests.post", return_value=mock_resp), pytest.raises(
        RuntimeError, match="hit the token limit"
    ):
        ai_report(metrics, "http://localhost:11434/v1", "", "deepseek-r1:14b")
