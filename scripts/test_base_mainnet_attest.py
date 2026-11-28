"""Verify Base Mainnet ERC-8021 Risk Attestation calldata & inspect live Base Mainnet transactions."""
from __future__ import annotations

import argparse
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import requests
from engine.wallet import (
    PRIMARY_BASE_RPC,
    encode_risk_attestation_calldata,
    decode_erc8021_calldata,
)


def verify_tx_on_base_mainnet(tx_hash: str, rpc_url: str = PRIMARY_BASE_RPC) -> dict:
    """Fetch a live transaction from Base Mainnet RPC and decode its AUREN + ERC-8021 calldata."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getTransactionByHash",
        "params": [tx_hash.strip()],
    }
    r = requests.post(rpc_url, json=payload, timeout=15)
    r.raise_for_status()
    tx = r.json().get("result")
    if not tx:
        return {"found": False, "tx_hash": tx_hash}

    input_data = tx.get("input", "0x")
    decoded = decode_erc8021_calldata(input_data)
    block_hex = tx.get("blockNumber")
    return {
        "found": True,
        "tx_hash": tx.get("hash"),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "block_number": int(block_hex, 16) if block_hex else None,
        "basescan_url": f"https://basescan.org/tx/{tx.get('hash')}",
        **decoded,
    }


def main():
    parser = argparse.ArgumentParser(description="AUREN Base Mainnet Attestation Tool")
    parser.add_argument("--builder-code", default="bc_auren", help="Base Builder Code (bc_...)")
    parser.add_argument("--score", type=int, default=28, help="Portfolio Risk Score (0-100)")
    parser.add_argument("--level", default="Low", help="Risk Level (Low/Medium/High)")
    parser.add_argument("--top-asset", default="NVDA", help="Top Asset Ticker")
    parser.add_argument("--verify-tx", default=None, help="Verify a live Base Mainnet txHash (0x...)")
    args = parser.parse_args()

    if args.verify_tx:
        result = verify_tx_on_base_mainnet(args.verify_tx)
        print(json.dumps(result, indent=2))
        return

    attest = encode_risk_attestation_calldata(
        score=args.score,
        level=args.level,
        top_asset=args.top_asset,
        portfolio_name="Base Tokenized Stocks & RWA",
        builder_code=args.builder_code,
    )
    decoded = decode_erc8021_calldata(attest["calldata"])
    print("=== AUREN Base Mainnet ERC-8021 Attestation Payload ===")
    print(json.dumps({**attest, "decoded_verification": decoded}, indent=2))


if __name__ == "__main__":
    main()
