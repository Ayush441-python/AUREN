#!/usr/bin/env python3
"""
AUREN External Risk Analytics Agent & CLI Client (Veriton Entrypoint)
====================================================================
Companion alias entry point for scripts/risk_client.py.

Per BOUNTY.md:
"API Integration: First 6 developers/agents who call the AUREN Risk API (/risk)
from an external agent or dashboard and share a demo. Payout: $25 USDC each."

Bounty Settlement Coordinates:
- Issue: Ayush441-python/AUREN #3
- Contributor: Veriton AI Agent
- Payout Rail: USDC on Base Mainnet (Chain ID 8453)
- Settlement Address: 0xA93ccE41173aa8CB545bE922C943726E65a8DAca

DISCLAIMER:
Analytics only, not investment advice. Past performance and statistical
correlations do not guarantee future results.
"""

import sys
import pathlib

# Ensure scripts directory and repository root are on sys.path
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
for p in (str(SCRIPTS_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from risk_client import main

if __name__ == "__main__":
    sys.exit(main())
