"""Regression tests for reasoning-param gating (issue #130)."""
from unittest.mock import MagicMock, patch

from engine.report import ai_report



def _payload_for(base_url, model):
    resp = MagicMock(ok=True)
    resp.json.return_value = {"choices": [{"message": {"content": "Score is 70."},
                                          "finish_reason": "stop"}]}
    with patch("engine.report.requests.post", return_value=resp) as mock_post:
        ai_report({"risk_score": 70}, base_url, "k", model)
        return mock_post.call_args.kwargs["json"]


def test_groq_llama_gets_no_reasoning_params():
    p = _payload_for("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile")
    assert "include_reasoning" not in p
    assert "reasoning_effort" not in p
    assert [m["role"] for m in p["messages"]] == ["system", "user"]
    assert p["max_tokens"] == 1500


def test_openai_non_reasoning_gets_no_reasoning_params():
    p = _payload_for("https://api.openai.com/v1", "gpt-4o-mini")
    assert "include_reasoning" not in p
    assert "reasoning_effort" not in p
    assert [m["role"] for m in p["messages"]] == ["system", "user"]


def test_gptoss_on_non_groq_omits_include_reasoning():
    p = _payload_for("https://openrouter.ai/api/v1", "openai/gpt-oss-120b")
    assert "include_reasoning" not in p
    assert p["max_completion_tokens"] == 4096


def test_groq_gptoss_unchanged():
    p = _payload_for("https://api.groq.com/openai/v1", "openai/gpt-oss-120b")
    assert p["include_reasoning"] is False
    assert p["max_completion_tokens"] == 4096
    assert [m["role"] for m in p["messages"]] == ["user"]
