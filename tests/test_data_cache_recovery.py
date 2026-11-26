"""Offline regression tests for incomplete in-memory market-data cache entries."""
import unittest
from unittest.mock import patch

import pandas as pd

from engine import data


class DataCacheRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.memo_patch = patch.object(data, "_memo", {})
        self.memo_patch.start()
        self.addCleanup(self.memo_patch.stop)
        self.dates = pd.date_range("2026-01-01", periods=40, freq="B")
        self.complete = pd.DataFrame(
            {"AAPL": range(100, 140), "SPY": range(200, 240)},
            index=self.dates,
            dtype=float,
        )

    def test_retry_after_partial_csv_fallback_fetches_recovered_provider(self):
        partial = self.complete[["AAPL"]]
        with patch.object(data, "_download", side_effect=[None, self.complete]) as download:
            with patch.object(data, "_cached", return_value=partial):
                first = data.load_prices(["AAPL", "SPY"], period="1y")
                recovered = data.load_prices(["AAPL", "SPY"], period="1y")
        self.assertEqual(list(first.columns), ["AAPL"])
        self.assertEqual(list(recovered.columns), ["AAPL", "SPY"])
        self.assertEqual(download.call_count, 2)
        pd.testing.assert_frame_equal(recovered, self.complete)

    def test_partial_live_download_does_not_poison_combined_key(self):
        with patch.object(data, "_download", side_effect=[self.complete[["AAPL"]], self.complete]) as download:
            with patch.object(data, "_cached", return_value=pd.DataFrame()):
                data.load_prices(["AAPL", "SPY"], period="1y")
                recovered = data.load_prices(["AAPL", "SPY"], period="1y")
        self.assertEqual(download.call_count, 2)
        pd.testing.assert_frame_equal(recovered, self.complete)

    def test_complete_result_is_still_cached_and_returned_as_copy(self):
        with patch.object(data, "_download", return_value=self.complete) as download:
            first = data.load_prices(["AAPL", "SPY"], period="1y")
            first.loc[self.dates[0], "AAPL"] = -999
            second = data.load_prices(["AAPL", "SPY"], period="1y")
        self.assertEqual(download.call_count, 1)
        pd.testing.assert_frame_equal(second, self.complete)

    def test_complete_csv_fallback_retains_existing_cache_behavior(self):
        with patch.object(data, "_download", return_value=None) as download:
            with patch.object(data, "_cached", return_value=self.complete):
                data.load_prices(["AAPL", "SPY"], period="1y")
                second = data.load_prices(["AAPL", "SPY"], period="1y")
        self.assertEqual(download.call_count, 1)
        pd.testing.assert_frame_equal(second, self.complete)


if __name__ == "__main__":
    unittest.main()
