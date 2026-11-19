import importlib
import sys
import types


def test_streamlit_secrets_override_builtin_defaults(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_REASONING_EFFORT"):
        monkeypatch.delenv(k, raising=False)
    st = types.ModuleType("streamlit")
    st.secrets = {
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_MODEL": "gpt-4o-mini",
    }
    monkeypatch.setitem(sys.modules, "streamlit", st)
    env = importlib.reload(importlib.import_module("engine.env"))
    env.load_env()
    assert env.setting("LLM_BASE_URL") == "https://api.openai.com/v1"
    assert env.setting("LLM_MODEL") == "gpt-4o-mini"
    assert env.setting("LLM_REASONING_EFFORT") == "low"


def test_defaults_still_apply_when_nothing_configured(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_REASONING_EFFORT"):
        monkeypatch.delenv(k, raising=False)
    st = types.ModuleType("streamlit")
    st.secrets = {}
    monkeypatch.setitem(sys.modules, "streamlit", st)
    env = importlib.reload(importlib.import_module("engine.env"))
    env.load_env()
    assert env.setting("LLM_BASE_URL") == env.GROQ_BASE_URL
    assert env.setting("LLM_MODEL") == env.GROQ_MODEL
    assert env.setting("LLM_REASONING_EFFORT") == "low"


def test_explicitly_empty_reasoning_effort(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_REASONING_EFFORT"):
        monkeypatch.delenv(k, raising=False)
    st = types.ModuleType("streamlit")
    st.secrets = {"LLM_REASONING_EFFORT": ""}
    monkeypatch.setitem(sys.modules, "streamlit", st)
    env = importlib.reload(importlib.import_module("engine.env"))
    env.load_env()
    assert env.setting("LLM_REASONING_EFFORT") is None
