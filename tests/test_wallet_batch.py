"""Synthetic RPC tests; no requests reach a network."""
import unittest
from unittest.mock import Mock, patch

from engine.wallet import token_balances


class BalanceBatchTests(unittest.TestCase):
    address = "0x" + "a" * 40
    tokens = [
        {"contract_address": "0x" + "1" * 40, "decimals": 18},
        {"contract_address": "0x" + "2" * 40, "decimals": 6},
    ]

    def invoke(self, batch):
        response = Mock()
        response.json.return_value = batch
        with patch("engine.wallet.requests.post", return_value=response) as post:
            result = token_balances(self.address, self.tokens)
            post.assert_called_once()
            return result

    def test_reordered_responses_map_by_id_with_distinct_decimals(self):
        result = self.invoke([
            {"jsonrpc": "2.0", "id": 1, "result": hex(2_500_000)},
            {"jsonrpc": "2.0", "id": 0, "result": hex(990 * 10**18)},
        ])
        self.assertEqual(result, {
            self.tokens[0]["contract_address"]: 990,
            self.tokens[1]["contract_address"]: 2.5,
        })

    def test_valid_zero_balances_are_omitted(self):
        self.assertEqual(self.invoke([
            {"id": 0, "result": "0x" + "0" * 64},
            {"id": 1, "result": "0x0"},
        ]), {})

    def test_invalid_batches_fail_without_returning_a_partial_portfolio(self):
        good = {"jsonrpc": "2.0", "id": 1, "result": "0x1"}
        cases = {
            "per-call error": [good, {"id": 0, "error": {"code": -32000}}],
            "missing response": [good],
            "empty response": [],
            "duplicate ID": [good, good],
            "unexpected ID": [good, {"id": 2, "result": "0x1"}],
            "negative ID": [good, {"id": -1, "result": "0x1"}],
            "boolean ID": [good, {"id": False, "result": "0x1"}],
            "string ID": [good, {"id": "0", "result": "0x1"}],
            "missing result": [good, {"id": 0}],
            "empty data": [good, {"id": 0, "result": "0x"}],
            "nonhex result": [good, {"id": 0, "result": "0xnothex"}],
            "integer result": [good, {"id": 0, "result": 1}],
            "null result": [good, {"id": 0, "result": None}],
            "error with result": [good, {"id": 0, "result": "0x1", "error": {}}],
            "invalid item": [good, None],
            "invalid batch": None,
            "batch rejection": {"error": {"message": "batch not supported"}},
        }
        for name, batch in cases.items():
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                self.invoke(batch)

    def test_later_chunk_failure_does_not_return_earlier_balances(self):
        responses = [Mock(), Mock()]
        responses[0].json.return_value = [{"id": 0, "result": "0x1"}]
        responses[1].json.return_value = [{"id": 0, "error": {"code": -32000}}]
        with patch("engine.wallet.requests.post", side_effect=responses) as post:
            with self.assertRaises(RuntimeError):
                token_balances(self.address, self.tokens, chunk=1)
            self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
