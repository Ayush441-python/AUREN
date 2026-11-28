# AUREN Bug & Maths Bounty Program

> **Program Pool: $400+ USDC**  
> **Focus:** Verified engine math bugs, reproducibility, risk integrity, and community growth.

AUREN is built in public with transparent risk math. We reward developers, quants, builders, and creators who help improve, test, integrate, and promote AUREN.

## 🏆 Reward Tiers

| Category | What Qualifies | Payout |
|:---|:---|:---:|
| **X Promotion Bounty** | Publish an original, high-quality post on X showcasing AUREN, its features, dashboard, Risk API, or AI-powered risk reports. Tag AUREN and share the post link. | **$50 USDC** |
| **Maths Bounty** | Find a financial risk metric calculated incorrectly with mathematical proof and code reproduction. | **$50 USDC** |
| **Bug Bounty** | Reproducible crash, logic error, or data parsing defect reported via GitHub Issues. | **$10–$50 USDC** |
| **API Integration** | First 6 developers/agents who call the AUREN Risk API (`/risk`) from an external agent or dashboard and share a working demo. | **$25 USDC each** |
| **Shipped Idea** | High-impact product or metric suggestion implemented in a release. | **$50 USDC + release credit** |

### X Promotion Bounty Requirements

To qualify for the **$50 USDC** reward:

1. Publish an original post about AUREN on X.
2. Showcase at least one real AUREN feature, such as portfolio risk analysis, the Risk API, or AI-powered reports.
3. Tag the official AUREN account.
4. Include a screenshot, demo, or meaningful explanation.
5. Share the public post link for verification.

**Note:** Low-effort posts, copied content, spam, and engagement farming will not qualify. Quality and originality matter.

## 🎖️ Early Builder Badge

All verified testers, bug reporters, API integrators, and accepted contributors receive the **AUREN Early Builder Badge** — non-transferable proof of contribution.

## 📩 Submission Guidelines

1. Open a GitHub Issue using the appropriate issue tag (`bug`, `idea`, or `question`).
2. Include:
   - Reproduction steps (exact portfolio weights and inputs).
   - Expected vs. actual calculation results.
   - Code snippet or test case reproducing the issue.

For X Promotion Bounties and API integrations, submit the public post or demo link through the designated submission channel.

Submissions are reviewed within 24 hours.

**Payouts:** Directly in USDC on Base / Ethereum.

---

## Bug Bounty: Out-of-order Preset Analyses Issue

### Summary

After startup has fully finished, selecting portfolio A and then B can display B's name with A's holdings and risk score, marked **Live Engine**, if A's response arrives last. Both requests succeed. The real preset menu remains usable while an analysis request is pending.

### Reproduction Steps

1. Open the workstation and let its initial analysis complete entirely.
2. From the portfolio menu choose **Balanced Tech & Crypto** (A):
   NVDA 40%, MSFT 30%, GOOGL 20%, ETH-USD 10%.
3. Before A responds, reopen that same menu and choose **Magnificent 7 Tech Heavy** (B):
   NVDA 25%, MSFT 20%, AAPL 20%, AMZN 15%, GOOGL 10%, META 10%.
4. Let B succeed first, then A.

### Expected vs. Actual Results

- **Expected:** The most recently selected B remains active with B's successful analysis. An obsolete success must not replace it.
- **Actual:** B's name stays visible, but A's weights and score replace B's. The status is still live.

### Cause

The issue arises because the `handleApplyPortfolio` function updates the name immediately but applies every successful awaited response without checking whether that request is still current. A stale request's finally block also clears loading regardless of a newer pending request.

### Proposed Solution

Implement a request ID mechanism to ensure that only the latest request's response updates the UI. Here’s a suggested implementation: