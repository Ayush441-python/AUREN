from __future__ import annotations

import os
from pathlib import Path

from engine import env


def test_parse_env_file_basic(tmp_path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\n# comment\nBAZ='qux'\nSPACED = value \n", encoding="utf-8")
    parsed = env._parse_env_file(f)
    assert parsed["FOO"] == "bar"
    assert parsed["BAZ"] == "qux"
    assert parsed["SPACED"] == "value"


def test_load_env_precedence_cwd_over_root(tmp_path, monkeypatch):
    root_dir = tmp_path / "project_root"
    cwd_dir = tmp_path / "working_dir"
    root_dir.mkdir()
    cwd_dir.mkdir()

    (root_dir / ".env").write_text("LLM_MODEL=root-model\nSHARED_VAR=from-root\nROOT_ONLY=1\n", encoding="utf-8")
    (cwd_dir / ".env").write_text("LLM_MODEL=local-model\nSHARED_VAR=from-cwd\nCWD_ONLY=2\n", encoding="utf-8")

    monkeypatch.setattr(env, "ROOT", root_dir)
    monkeypatch.chdir(cwd_dir)

    for k in ["LLM_MODEL", "SHARED_VAR", "ROOT_ONLY", "CWD_ONLY"]:
        monkeypatch.delenv(k, raising=False)

    env.load_env()

    assert os.environ.get("LLM_MODEL") == "local-model"
    assert os.environ.get("SHARED_VAR") == "from-cwd"
    assert os.environ.get("ROOT_ONLY") == "1"
    assert os.environ.get("CWD_ONLY") == "2"


def test_setting_precedence(monkeypatch):
    monkeypatch.setenv("AUREN_TEST_KEY", "env-value")
    assert env.setting("AUREN_TEST_KEY") == "env-value"
    assert env.setting("NON_EXISTENT_KEY", default="fallback") == "fallback"
