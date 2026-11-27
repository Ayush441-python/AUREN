"""Load `.env` from the project root and read settings."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key:
            values[key] = val
    return values


def load_env() -> None:
    """Read `.env` next to app.py. Does not require python-dotenv."""
    parsed = _parse_env_file(ROOT / ".env")
    parsed.update(_parse_env_file(Path.cwd() / ".env"))
    for key, val in parsed.items():
        os.environ[key] = val
    # Defaults so Groq works once LLM_API_KEY is set
    os.environ.setdefault("LLM_BASE_URL", GROQ_BASE_URL)
    os.environ.setdefault("LLM_MODEL", GROQ_MODEL)
    os.environ.setdefault("LLM_REASONING_EFFORT", "low")
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)
        cwd_env = Path.cwd() / ".env"
        if cwd_env.resolve() != (ROOT / ".env").resolve() and cwd_env.is_file():
            load_dotenv(cwd_env, override=True)
    except ImportError:
        pass


def secret(name: str):
    # Only consult Streamlit secrets when running inside Streamlit. Importing it
    # from the FastAPI server is slow and pointless.
    import sys
    if "streamlit" not in sys.modules:
        return None
    try:
        import streamlit as st
        return st.secrets[name]
    except Exception:
        return None


def setting(name: str, default=None):
    """Prefer environment / `.env`, then Streamlit secrets."""
    value = os.getenv(name)
    if value is not None:
        value = value.strip()
        if value:
            return value
    found = secret(name)
    if found is not None and str(found).strip():
        return str(found).strip()
    return default
