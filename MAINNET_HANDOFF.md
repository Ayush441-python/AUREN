# AUREN — Base Mainnet, B20 Tokenized Stocks, ERC-8021 & o1 Exchange Handoff Guide

This document summarizes all engineering upgrades implemented for the **Base Mainnet (Chain ID 8453)** launch, **Base Stocks Maxxing Season**, **o1 Exchange Integration**, and **Builder Circle Verification**.

---

## 1. Summary of Changes by Layer

### A. Python Engine & Data Layer (`engine/` & `data/`)

1. **[`data/tokenized_stocks.json`](file:///Users/prakharmishra/Downloads/AUREN-main/data/tokenized_stocks.json) — Verified Base Mainnet B20 Contracts (`decimals: 8`)**
   - Replaced all placeholder `0x1111...` addresses with 10 verified Coinbase B20 tokenized stock contracts on Base Mainnet (`0xb20...`) using **`decimals: 8`** and official ISIN metadata:
     - `NVDAc` (`0xb20000000000000000000078ee7ce2fe4908108c`)
     - `AAPLc` (`0xb200000000000000000000c2e324d24d7eecd1fb`)
     - `MSFTc` (`0xb200000000000000000000ab99cfa739e253872b`)
     - `AMZNc` (`0xb200000000000000000000d9192b6b456483c2e8`)
     - `GOOGLc` (`0xb2000000000000000000002d0ba3164cc74f58b7`)
     - `METAc` (`0xb2000000000000000000008bc8786b856e61707c`)
     - `TSLAc` (`0xb2000000000000000000001e800a7f5189430cd0`)
     - `COINc` (`0xb200000000000000000000c85a31389d71f3ecfb`)
     - `PLTRc` (`0xb2000000000000000000007d16372840df4dabbe`)
     - `MSTRc` (`0xb2000000000000000000004884b426556b92883d`)

2. **[`engine/wallet.py`](file:///Users/prakharmishra/Downloads/AUREN-main/engine/wallet.py) — B20 Multiplier Math, Base Tokens & ERC-8021 Encoder**
   - **Multiplier Valuation Fix:** Updated position valuation to `shares = round(amount * multiplier, 6)` and `value = round(shares * price, 2)` to properly account for B20 corporate-action multipliers.
   - **8-Decimal Default for B20:** Automatically defaults `0xb20...` contracts to 8 decimals.
   - **Expanded `KNOWN_BASE_TOKENS`:** Added `WETH` (`0x4200000000000000000000000000000000000006`), `AERO` (`0x940181a94a35a4569e4529a3cdfb74e38fd98631`), and `VIRTUAL` (`0x0b3e328455c4059eeb9e3f84b5543f74e24e7e1b`) alongside `cbBTC` and `USDC`.
   - **Dynamic Pricing:** Pulls latest cached/live prices via `get_latest_prices()` from `engine/data.py` instead of hardcoded constants.
   - **ERC-8021 Base Builder Code Attribution:** Added `encode_erc8021_suffix()`, `encode_risk_attestation_calldata()`, and `decode_erc8021_calldata()` implementing the canonical Schema 0 layout (`[ASCII_CODES][LENGTH_1B][0x00][0x80218021802180218021802180218021]`).

3. **[`engine/o1_exchange.py`](file:///Users/prakharmishra/Downloads/AUREN-main/engine/o1_exchange.py) *(New)* — o1 Exchange Partner Integration**
   - **o1 Alpha Token Discovery (`fetch_o1_alpha_tokens`):** Queries `GET https://api.o1.exchange/api/v1/alpha-tokens?networkId=8453` and enriches ranked addresses with AUREN B20 & Base DeFi metadata (with offline fallback to verified Base 8453 contracts).
   - **Deterministic Risk-to-Rebalance Calculator (`compute_optimal_rebalance_weights` & `build_o1_rebalance_plan`):** Solves for target portfolio weights that cap single-name concentration $\le 24\%$ and raise effective assets $1/\text{HHI} \ge 4.2$, generating 1-click o1 Terminal deep links and MEV-protected `POST https://api.o1.exchange/api/v2/order` payloads.

4. **[`engine/data.py`](file:///Users/prakharmishra/Downloads/AUREN-main/engine/data.py) & [`engine/universe.py`](file:///Users/prakharmishra/Downloads/AUREN-main/engine/universe.py)**
   - Added `AERO-USD` and `VIRTUAL-USD` to `SECTORS` and `GROUPS`.
   - Added `get_latest_prices()` and deterministic offline proxy series for `USDC`, `AERO-USD`, `VIRTUAL-USD`, `COIN`, `MSTR`, `SOL-USD`, `SPY`, and `QQQ` so `/risk` and `/liquidity` never throw 502 errors when Yahoo Finance is rate-limited.

---

### B. FastAPI Backend Layer (`backend/`)

- **[`backend/app/api/endpoints/analytics.py`](file:///Users/prakharmishra/Downloads/AUREN-main/backend/app/api/endpoints/analytics.py) & [`backend/app/schemas/requests.py`](file:///Users/prakharmishra/Downloads/AUREN-main/backend/app/schemas/requests.py):**
  - `POST /attest/encode`: Generates Base Mainnet calldata with ERC-8021 Builder Code suffix.
  - `POST /attest/decode`: Decodes Base Mainnet transaction input data to verify AUREN audit proofs and ERC-8021 Builder Codes.
  - `GET /o1/alpha-tokens?networkId=8453`: Returns ranked o1 Alpha tokens on Base Mainnet.
  - `POST /rebalance`: Computes Before vs. After deterministic risk score reduction, trade legs, and o1 Exchange `/api/v2/order` bundle.
  - `GET /dashboard` & `GET /attest`: Serves the standalone institutional workstation from `frontend/index.html`.
- **[`backend/app/core/config.py`](file:///Users/prakharmishra/Downloads/AUREN-main/backend/app/core/config.py):**
  - Added `https://aurenfrontend-delta.vercel.app` and `http://127.0.0.1:8080` to `BACKEND_CORS_ORIGINS`.

---

### C. Next.js Vercel Frontend (`web/`)

1. **[`web/src/components/modals/OnchainAttestModal.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/modals/OnchainAttestModal.tsx) *(New)***
   - Full Base Mainnet (`0x2105` / Chain ID 8453) on-chain transaction modal.
   - Lets users input their `bc_...` Base Builder Code, inspect the ASCII proof and ERC-8021 hex suffix, broadcast a real transaction via `eth_sendTransaction`, poll `eth_getTransactionReceipt`, and open the confirmed transaction on `BaseScan.org`.
2. **[`web/src/components/modals/ShareScorecardModal.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/modals/ShareScorecardModal.tsx) *(New)* & [`web/src/app/api/og/route.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/app/api/og/route.tsx) *(New)***
   - **4-Theme Custom Risk Passport Studio** (*Obsidian Gold*, *Base Cobalt*, *Emerald Quant*, *Crimson Stress*).
   - Computes a dynamic **Investor Archetype** & unique serial hash (`#AUR-8453-XXXX`) for every portfolio.
   - Renders a custom 1200×630 PNG on an HTML5 `<canvas>` (with live 2Y equity curve sparkline, semi-circular risk gauge dial, and multi-asset allocation bar) and shares via zero-API-key Twitter Web Intents.
3. **[`web/src/components/modals/O1RebalanceModal.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/modals/O1RebalanceModal.tsx) *(New)***
   - Displays Before vs. After Risk Score reduction, 1-click o1 Terminal swap execution buttons, and applies the rebalanced portfolio directly to the workstation.
4. **[`web/src/components/modals/PortfolioBuilderModal.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/modals/PortfolioBuilderModal.tsx) & [`WalletConnectModal.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/modals/WalletConnectModal.tsx)**
   - Added zero-fail empty-wallet handling with a 1-click **"Load Base Stocks Demo Portfolio"** button.
5. **[`web/src/components/landing/LandingPage.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/landing/LandingPage.tsx), [`Hero.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/landing/Hero.tsx), [`OverviewView.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/views/OverviewView.tsx), [`DashboardTopBar.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/dashboard/DashboardTopBar.tsx), [`Workstation.tsx`](file:///Users/prakharmishra/Downloads/AUREN-main/web/src/components/dashboard/Workstation.tsx)**
   - Restored 3D `<ArchitectureStory />` and `<ProductPreview />` on the landing page, polished institutional copy, and wired `Attest On-Chain`, `o1 Rebalance`, and `Share to X` into the top bar and overview header.

---

## 2. Deployment Checklist (Render Backend + Vercel Frontend)

### Step 1: Deploy Backend API on Render (`render.yaml` / `Dockerfile`)
- **Build / Runtime:** Docker (`Dockerfile` runs `uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}`).
- **Environment Variables on Render:**
  - `BASE_RPC_URL` = `https://mainnet.base.org`
  - `LLM_BASE_URL` = `https://api.groq.com/openai/v1`
  - `LLM_MODEL` = `openai/gpt-oss-120b`
  - `LLM_API_KEY` = `<your-groq-api-key>`
- **Health Check Path:** `/healthz`

### Step 2: Deploy Next.js Frontend on Vercel (`web/`)
- **Root Directory:** `web`
- **Environment Variables on Vercel:**
  - `NEXT_PUBLIC_API_URL` = `https://auren-api-8yrq.onrender.com` *(or your live Render backend URL)*

### Step 3: Base Dashboard & Builder Circle Verification
1. Visit [dashboard.base.org](https://dashboard.base.org), register **AUREN**, and copy your **Builder Code (`bc_xxxxxxxx`)** under *Settings → Project Settings → Builder Code*.
2. Open your live deployed site (`/dashboard`), click **"⚡ Attest On-Chain (Base)"**, paste your `bc_xxxxxxxx` code, and click **"Sign & Attest on Base Mainnet"**.
3. Screenshot the confirmed BaseScan transaction and submit your `bc_xxxxxxxx` code on [Builder Circle (`builder-circle.xyz/verify`)](https://builder-circle.xyz/verify).
