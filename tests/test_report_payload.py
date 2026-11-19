from unittest.mock import MagicMock, patch

import pytest

from engine.report import ai_report

METRICS = {"risk_score": 70, "risk_level": "High"}


def _ok_response(content: str = "Portfolio risk score is 70."):
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def test_groq_non_reasoning_model_omits_reasoning_params(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    with patch("engine.report.requests.post", return_value=_ok_response()) as mock_post:
        out = ai_report(
            METRICS,
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test",
            model="llama-3.3-70b-versatile",
        )
    assert out == "Portfolio risk score is 70."
    payload = mock_post.call_args.kwargs["json"]
    assert "include_reasoning" not in payload
    assert "reasoning_effort" not in payload
    assert payload["max_tokens"] == 1500
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]


@pytest.mark.parametrize(
    ("base_url", "api_key", "model"),
    [
        ("https://api.openai.com/v1", "sk-test", "gpt-4o-mini"),
        ("http://localhost:11434/v1", "", "llama3.2"),
    ],
)
def test_non_groq_non_reasoning_models_omit_reasoning_params(
    monkeypatch, base_url, api_key, model
):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    with patch("engine.report.requests.post", return_value=_ok_response()) as mock_post:
        ai_report(METRICS, base_url=base_url, api_key=api_key, model=model)
    payload = mock_post.call_args.kwargs["json"]
    assert "include_reasoning" not in payload
    assert "reasoning_effort" not in payload
    assert payload["max_tokens"] == 1500
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]


def test_non_groq_gpt_oss_omits_groq_only_include_reasoning(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "medium")
    with patch("engine.report.requests.post", return_value=_ok_response()) as mock_post:
        ai_report(
            METRICS,
            base_url="https://openrouter.ai/api/v1",
            api_key="or-test",
            model="openai/gpt-oss-120b",
        )
    payload = mock_post.call_args.kwargs["json"]
    assert "include_reasoning" not in payload
    assert payload["max_completion_tokens"] == 4096
    assert payload["reasoning_effort"] == "medium"
    assert [m["role"] for m in payload["messages"]] == ["user"]


def test_groq_gpt_oss_preserves_reasoning_payload(monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    with patch("engine.report.requests.post", return_value=_ok_response()) as mock_post:
        ai_report(
            METRICS,
            base_url="https://api.groq.com/openai/v1",
            api_key="gsk-test",
            model="openai/gpt-oss-120b",
        )
    payload = mock_post.call_args.kwargs["json"]
    assert payload["include_reasoning"] is False
    assert payload["max_completion_tokens"] == 4096
    assert payload["temperature"] == 0.6
    assert payload["reasoning_effort"] == "low"
    assert [m["role"] for m in payload["messages"]] == ["user"]
