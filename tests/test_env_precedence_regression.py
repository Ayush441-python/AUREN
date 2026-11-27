import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "auren_env_under_test", Path(__file__).resolve().parents[1] / "engine/env.py"
)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class EnvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.cwd = Path(self.temp.name) / "launch"
        self.cwd.mkdir()
        previous = Path.cwd()
        os.chdir(self.cwd)
        self.addCleanup(os.chdir, previous)
        root_patch = patch.object(subject, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        env_patch = patch.dict(os.environ, {}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def write(self, root_text="", cwd_text=""):
        (self.root / ".env").write_text(root_text, encoding="utf-8")
        (self.cwd / ".env").write_text(cwd_text, encoding="utf-8")

    @unittest.skipUnless(importlib.util.find_spec("dotenv"), "python-dotenv not installed")
    def test_cwd_overrides_root_with_dotenv(self):
        self.write("LLM_MODEL=root-model\n", "LLM_MODEL=local-model\n")
        subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), "local-model")

    def test_cwd_overrides_root_without_dotenv(self):
        self.write("LLM_MODEL=root-model\n", "LLM_MODEL=local-model\n")
        with patch.dict(sys.modules, {"dotenv": None}):
            subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), "local-model")

    @unittest.skipUnless(importlib.util.find_spec("dotenv"), "python-dotenv not installed")
    def test_consistent_provider_configuration(self):
        self.write("LLM_BASE_URL=https://root.invalid/v1\n",
                   "LLM_BASE_URL=https://local.invalid/v1\nLLM_MODEL=local-model\n")
        subject.load_env()
        self.assertEqual(subject.setting("LLM_BASE_URL"), "https://local.invalid/v1")
        self.assertEqual(subject.setting("LLM_MODEL"), "local-model")

    def test_root_only(self):
        self.write("LLM_MODEL=root-model\n")
        subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), "root-model")

    def test_cwd_only(self):
        self.write("", "LLM_MODEL=local-model\n")
        subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), "local-model")

    def test_defaults(self):
        subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), subject.GROQ_MODEL)

    def test_same_root_and_cwd(self):
        self.write("LLM_MODEL=root-model\n")
        os.chdir(self.root)
        subject.load_env()
        self.assertEqual(subject.setting("LLM_MODEL"), "root-model")

if __name__ == "__main__":
    unittest.main()
