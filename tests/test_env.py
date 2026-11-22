"""Regression tests for Streamlit secrets vs env defaults (issue #113)."""
import os
import sys
import types

import pytest

from engine import env


@pytest.fixture
def clean_llm_env(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY", "LLM_REASONING_EFFORT"):
        monkeypatch.delenv(k, raising=False)
    yield
    env.load_env()  # restore process env for other tests


def _fake_streamlit(monkeypatch, secrets):
    st = types.ModuleType("streamlit")
    st.secrets = secrets
    monkeypatch.setitem(sys.modules, "streamlit", st)


def test_secrets_not_shadowed_by_defaults(clean_llm_env, monkeypatch):
    secrets = {
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_REASONING_EFFORT": "",
    }
    _fake_streamlit(monkeypatch, secrets)
    env.load_env()
    assert env.setting("LLM_BASE_URL") == "https://api.openai.com/v1"
    assert env.setting("LLM_MODEL") == "gpt-4o-mini"
    # empty-string secret falls through to nothing (no default written)
    assert env.setting("LLM_REASONING_EFFORT") is None


def test_defaults_still_apply_without_secrets(clean_llm_env, monkeypatch):
    _fake_streamlit(monkeypatch, {})
    env.load_env()
    assert env.setting("LLM_BASE_URL") == env.GROQ_BASE_URL
    assert env.setting("LLM_MODEL") == env.GROQ_MODEL
    assert env.setting("LLM_REASONING_EFFORT") == "low"


def test_explicit_env_beats_secrets(clean_llm_env, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    _fake_streamlit(monkeypatch, {"LLM_BASE_URL": "https://api.openai.com/v1"})
    env.load_env()
    assert env.setting("LLM_BASE_URL") == "https://example.com/v1"
