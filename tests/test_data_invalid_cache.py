"""Offline fallback must survive corrupted CSV caches without modifying source files."""
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from engine import data


class InvalidCacheFallbackTests(unittest.TestCase):
    def verify_fallback(self, payload: bytes, *, expect_warning: bool):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "prices.csv"
            path.write_bytes(payload)
            with patch.object(data, "_download", return_value=None), patch.object(data, "_memo", {}):
                with warnings.catch_warnings(record=True) as seen:
                    warnings.simplefilter("always")
                    result = data._load("Close", ["NVDA"], "2y", path)
            self.assertTrue(result.empty)
            self.assertEqual(path.read_bytes(), payload, "Original cache must be preserved")
            self.assertEqual(any(issubclass(m.category, RuntimeWarning) for m in seen),
                             expect_warning)

    def test_zero_byte_cache(self):
        self.verify_fallback(b"", expect_warning=True)

    def test_truncated_quoted_cache(self):
        self.verify_fallback(b'Date,NVDA\n2026-01-01,"123\n', expect_warning=True)

    def test_invalid_utf8_cache(self):
        self.verify_fallback(b'Date,NVDA\n2026-01-01,\xff\n', expect_warning=True)

    def test_missing_cache_still_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"missing.csv"
            with patch.object(data, "_download", return_value=None), patch.object(data, "_memo", {}):
                self.assertTrue(data._load("Close", ["NVDA"], "2y", path).empty)

    def test_healthy_cache_still_parses(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"prices.csv"
            path.write_text("Date,NVDA\n2026-01-01,100\n2026-01-02,110\n",encoding="utf-8")
            with patch.object(data, "_download", return_value=None), patch.object(data, "_memo", {}):
                result=data._load("Close", ["NVDA"], "2y", path)
            self.assertEqual(result.shape,(2,1))
            self.assertEqual(float(result.loc["2026-01-02", "NVDA"]),110.0)


if __name__=="__main__":
    unittest.main()
