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

## 🛠️ Bug Bounty Details

### Issue Summary

The workstation's System Preferences page exposes editable covariance-window, VaR-confidence, and risk-free-rate controls, but all three are uncontrolled DOM fields. Changing them appears to work until the user navigates away: Risk Metrics still shows the original values, and returning to Settings resets every edit. There is no save/apply action or notice that these controls are nonfunctional.

### Steps to Reproduce

1. Open `/dashboard?tab=settings`.
2. Change Covariance Estimation Window from 252 to 126 trading days.
3. Change VaR Confidence Level from 95% to 99%.
4. Change Risk-Free Benchmark Rate from 4.25% to 1.00%.
5. Open Risk Metrics, then return to System Preferences.

### Expected Behavior

Supported edits persist across in-app navigation and are used by the relevant analysis; otherwise, the UI must identify them as unavailable/read-only instead of suggesting they configure calculations.

### Actual Behavior

The metric header still says Confidence 95.0%, the Sharpe card still says Rf = 4.25% (US 10Y), and Settings returns to 252 / 95 / 4.25%.

### Cause

`SettingsView` has no state, event handlers, persistence, or configuration callback. Its two selects and defaultValue input can only change their own DOM values. `Workstation` conditionally mounts `<SettingsView />`; it holds no shared model-settings state. `RiskMetricsView` hardcodes the displayed confidence and Rf.

### Proposed Solution

Implement state management for the `SettingsView` component to persist user inputs and update the `RiskMetricsView` accordingly.

### Code Implementation