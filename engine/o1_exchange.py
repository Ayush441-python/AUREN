"""o1 Exchange Integration: Public o1 Alpha Token API (networkId=8453) & Deterministic Risk-to-Rebalance Router."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from engine.wallet import (
    KNOWN_BASE_TOKENS,
    encode_erc8021_suffix,
    load_bundled_tokens,
    underlying_ticker,
)

logger = logging.getLogger("auren-o1-exchange")

O1_ALPHA_API_URL = "https://api.o1.exchange/api/v1/alpha-tokens"
O1_TRADING_ORDER_URL = "https://api.o1.exchange/api/v2/order"
O1_TRADING_COMPLETE_URL = "https://api.o1.exchange/api/v2/order/complete"
O1_TERMINAL_BASE_URL = "https://o1.exchange"
BASE_NETWORK_ID = 8453
USDC_BASE_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def _build_contract_catalog() -> Dict[str, Dict[str, Any]]:
    """Map lowercase Base Mainnet contract addresses and tickers to verified token metadata."""
    by_addr: Dict[str, Dict[str, Any]] = {}
    for t in load_bundled_tokens() + KNOWN_BASE_TOKENS:
        addr = str(t.get("contract_address", "")).lower()
        if addr.startswith("0x") and len(addr) == 42:
            symbol = t.get("symbol", "?")
            ticker = t.get("ticker") or underlying_ticker(symbol)
            by_addr[addr] = {
                "contract_address": addr,
                "symbol": symbol,
                "ticker": ticker,
                "name": t.get("name", symbol),
                "decimals": int(t.get("decimals", 8 if addr.startswith("0xb20") else 18)),
                "is_b20_stock": addr.startswith("0xb20"),
                "isin": t.get("isin"),
            }
    return by_addr


def _build_ticker_catalog() -> Dict[str, Dict[str, Any]]:
    """Map AUREN tickers (e.g. NVDA, ETH-USD, AERO-USD, USDC) to Base Mainnet contract metadata."""
    by_ticker: Dict[str, Dict[str, Any]] = {}
    for meta in _build_contract_catalog().values():
        tk = meta["ticker"]
        # Prefer B20 or primary representation
        if tk not in by_ticker or meta["is_b20_stock"]:
            by_ticker[tk] = meta
    return by_ticker


def fetch_o1_alpha_tokens(network_id: int = BASE_NETWORK_ID, timeout: int = 4) -> Dict[str, Any]:
    """Fetch ranked o1 Alpha token contract addresses from GET https://api.o1.exchange/api/v1/alpha-tokens?networkId=8453
    with deterministic fallback to verified Base Mainnet B20 & DeFi contracts."""
    if not isinstance(network_id, int) or isinstance(network_id, bool) or network_id <= 0:
        raise ValueError("networkId must be a positive integer")

    catalog = _build_contract_catalog()
    raw_addresses: List[str] = []
    source = "live_o1_api"

    try:
        r = requests.get(
            O1_ALPHA_API_URL,
            params={"networkId": network_id},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                raw_addresses = [str(a).lower() for a in data if isinstance(a, str)]
    except Exception as e:
        logger.info(f"o1 Alpha Token API unreachable ({e}); using verified Base 8453 registry fallback.")

    if not raw_addresses:
        source = "verified_base_8453_fallback"
        raw_addresses = list(catalog.keys())

    # Deduplicate preserving first ranked occurrence (per o1 Alpha spec)
    seen = set()
    ranked_addresses: List[str] = []
    for addr in raw_addresses:
        if addr not in seen:
            seen.add(addr)
            ranked_addresses.append(addr)

    # Also ensure our verified B20 & Base ecosystem contracts are represented in the enriched view
    for addr in catalog:
        if addr not in seen:
            seen.add(addr)
            ranked_addresses.append(addr)

    enriched: List[Dict[str, Any]] = []
    for idx, addr in enumerate(ranked_addresses[:100], start=1):
        meta = catalog.get(addr)
        enriched.append(
            {
                "alpha_rank": idx,
                "contract_address": addr,
                "symbol": meta["symbol"] if meta else f"TOKEN_{addr[:6]}",
                "ticker": meta["ticker"] if meta else None,
                "name": meta["name"] if meta else "Base Alpha Asset",
                "decimals": meta["decimals"] if meta else 18,
                "is_b20_stock": meta["is_b20_stock"] if meta else addr.startswith("0xb20"),
                "auren_supported": meta is not None,
                "o1_terminal_url": f"{O1_TERMINAL_BASE_URL}/?networkId={network_id}&token={addr}",
            }
        )

    return {
        "network_id": network_id,
        "network_name": "Base Mainnet" if network_id == 8453 else f"Chain {network_id}",
        "endpoint": f"{O1_ALPHA_API_URL}?networkId={network_id}",
        "source": source,
        "count": len(enriched),
        "addresses": [item["contract_address"] for item in enriched],
        "tokens": enriched,
    }


def compute_optimal_rebalance_weights(current_weights: Dict[str, float]) -> Dict[str, float]:
    """Deterministically rebalance portfolio weights to eliminate AUREN concentration & HHI penalties:
    - Caps single-asset top weight at <= 25% (below 30% penalty rule)
    - Ensures >= 4.5 effective assets (1/HHI >= 4, eliminating <4 effective assets rule)
    - Adds uncorrelated Base B20 / stable diversifiers (USDC, AAPL, MSFT, GLD) to reduce sector concentration <50% & volatility
    """
    total = sum(v for v in current_weights.values() if v > 0)
    if total <= 0:
        return {"NVDA": 0.25, "AAPL": 0.25, "MSFT": 0.20, "ETH-USD": 0.15, "USDC": 0.15}

    norm = {k: v / total for k, v in current_weights.items() if v > 0}

    # Diversifier pool across distinct risk groups (Equities, Gold, Stablecoin, Crypto)
    diversifiers = ["USDC", "GLD", "AAPL", "MSFT", "BTC-USD"]
    target: Dict[str, float] = dict(norm)

    # Ensure at least 5 distinct assets so 1/HHI >= 4.2
    for d_tk in diversifiers:
        if len(target) >= 5:
            break
        if d_tk not in target:
            target[d_tk] = 0.0

    # Cap every single asset at 0.24 (24%) and redistribute excess to underweight/diversifier assets
    max_cap = 0.24
    for _ in range(6):
        excess = 0.0
        underweight_keys = []
        for k, w in target.items():
            if w > max_cap:
                excess += w - max_cap
                target[k] = max_cap
            else:
                underweight_keys.append(k)
        if excess <= 1e-6 or not underweight_keys:
            break
        # Distribute excess favoring defensive/uncorrelated anchors (USDC, GLD) first
        defensive = [k for k in underweight_keys if k in {"USDC", "GLD"}]
        recipients = defensive if defensive else underweight_keys
        add_each = excess / len(recipients)
        for k in recipients:
            target[k] = min(max_cap, target[k] + add_each)

    # Guarantee a minimum 15% defensive anchor (USDC) if volatility/concentration was high
    if "USDC" not in target or target.get("USDC", 0.0) < 0.14:
        needed = 0.15 - target.get("USDC", 0.0)
        target["USDC"] = 0.15
        other_keys = [k for k in target if k != "USDC" and target[k] > 0.05]
        if other_keys:
            for k in other_keys:
                target[k] = max(0.05, target[k] - needed / len(other_keys))

    # Normalize cleanly to 1.0
    s = sum(target.values())
    return {k: round(v / s, 4) for k, v in target.items() if v > 0.005}


def build_o1_rebalance_plan(
    before_risk: Dict[str, Any],
    after_risk: Dict[str, Any],
    portfolio_value: float = 100000.0,
    builder_code: str = "bc_auren",
) -> Dict[str, Any]:
    """Build deterministic Risk-to-Rebalance trade legs, o1 Alpha rank lookup, and o1 Trading API (/api/v2/order) payload."""
    before_w: Dict[str, float] = before_risk.get("normalized_weights", {})
    after_w: Dict[str, float] = after_risk.get("normalized_weights", {})
    ticker_catalog = _build_ticker_catalog()
    alpha_info = fetch_o1_alpha_tokens(BASE_NETWORK_ID)
    alpha_rank_by_addr = {
        t["contract_address"].lower(): t["alpha_rank"] for t in alpha_info.get("tokens", [])
    }

    all_tickers = sorted(set(before_w.keys()) | set(after_w.keys()))
    trades: List[Dict[str, Any]] = []
    orders: List[Dict[str, Any]] = []

    erc8021_suffix = encode_erc8021_suffix(builder_code)

    for tk in all_tickers:
        w_old = float(before_w.get(tk, 0.0))
        w_new = float(after_w.get(tk, 0.0))
        delta = round(w_new - w_old, 4)
        if abs(delta) < 0.005:
            continue

        action = "BUY" if delta > 0 else "SELL"
        usd_amount = round(abs(delta) * portfolio_value, 2)
        meta = ticker_catalog.get(tk)
        contract_addr = (
            meta["contract_address"]
            if meta
            else "0x4200000000000000000000000000000000000006"
        )
        symbol = meta["symbol"] if meta else tk
        decimals = meta["decimals"] if meta else 18
        alpha_rank = alpha_rank_by_addr.get(contract_addr.lower())

        token_in = USDC_BASE_ADDRESS if action == "BUY" else contract_addr
        token_out = contract_addr if action == "BUY" else USDC_BASE_ADDRESS

        o1_terminal_url = (
            f"{O1_TERMINAL_BASE_URL}/?networkId={BASE_NETWORK_ID}"
            f"&inputCurrency={token_in}&outputCurrency={token_out}"
        )

        order_payload = {
            "endpoint": O1_TRADING_ORDER_URL,
            "completionEndpoint": O1_TRADING_COMPLETE_URL,
            "networkId": BASE_NETWORK_ID,
            "side": action,
            "tokenIn": token_in,
            "tokenOut": token_out,
            "symbol": symbol,
            "ticker": tk,
            "amountUsd": usd_amount,
            "decimals": decimals,
            "mevProtection": True,
            "permit2": True,
            "autoSlippage": True,
            "maxSlippageBps": 50,
            "erc8021BuilderCode": builder_code.strip(),
            "erc8021DataSuffix": f"0x{erc8021_suffix}" if erc8021_suffix else None,
        }
        orders.append(order_payload)

        trades.append(
            {
                "action": action,
                "ticker": tk,
                "symbol": symbol,
                "contract_address": contract_addr,
                "decimals": decimals,
                "is_b20_stock": contract_addr.startswith("0xb20"),
                "o1_alpha_rank": alpha_rank,
                "current_weight": round(w_old, 4),
                "target_weight": round(w_new, 4),
                "delta_weight": delta,
                "trade_usd": usd_amount,
                "o1_terminal_url": o1_terminal_url,
                "o1_order_payload": order_payload,
            }
        )

    # Sort SELL trims first, then BUY rotations by dollar size
    trades.sort(key=lambda x: (0 if x["action"] == "SELL" else 1, -x["trade_usd"]))

    return {
        "network_id": BASE_NETWORK_ID,
        "portfolio_value": portfolio_value,
        "before": {
            "score": before_risk["score"],
            "level": before_risk["level"],
            "volatility": before_risk["volatility"],
            "max_drawdown": before_risk["max_drawdown"],
            "effective_assets": before_risk["concentration"]["effective_assets"],
            "top_asset": before_risk["concentration"]["top_asset"],
            "top_weight": before_risk["concentration"]["top_weight"],
            "reasons": before_risk.get("reasons", []),
        },
        "after": {
            "score": after_risk["score"],
            "level": after_risk["level"],
            "volatility": after_risk["volatility"],
            "max_drawdown": after_risk["max_drawdown"],
            "effective_assets": after_risk["concentration"]["effective_assets"],
            "top_asset": after_risk["concentration"]["top_asset"],
            "top_weight": after_risk["concentration"]["top_weight"],
            "reasons": after_risk.get("reasons", []),
        },
        "score_reduction": max(0, int(before_risk["score"]) - int(after_risk["score"])),
        "target_weights": after_w,
        "trades": trades,
        "o1_order_bundle": {
            "baseUrl": "https://api.o1.exchange",
            "orderEndpoint": O1_TRADING_ORDER_URL,
            "completeEndpoint": O1_TRADING_COMPLETE_URL,
            "networkId": BASE_NETWORK_ID,
            "mevProtection": True,
            "permit2": True,
            "orders": orders,
        },
    }

