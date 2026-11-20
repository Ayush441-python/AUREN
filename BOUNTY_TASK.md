# Bounty Fix

**Reward:** $50.00
**Issue:** https://github.com/Ayush441-python/AUREN/issues/133
**Repo:** https://github.com/Ayush441-python/AUREN

---

## Issue

[Maths Bounty] Exactly 50% group exposure incorrectly adds 15 risk points (Low to Medium)

<html>
<body>
<!--StartFragment--><h1>[Maths Bounty] Exactly 50% broad-group exposure adds 15 points only in certain asset orders (Low → Medium)</h1><h2>Summary — $50 USDC Maths Bounty submission</h2><p>AUREN's published strict rule is <strong>“More than 50% sits in one sector”</strong> (+15 points). With a portfolio containing exactly 50% in each of two broad groups, simply reordering the same holdings can make the group-exposure calculation equal <code dir="ltr">0.5000000000000001</code> rather than <code dir="ltr">0.5</code>. The comparison <code dir="ltr">sector_max &gt; 0.50</code> consequently adds 15 points in one order but not the other.</p><p>This report addresses a <strong>floating-point boundary defect in the group-concentration threshold</strong>. It is different from issue #16 (effective-number-of-assets / HHI threshold), #49 (drawdown threshold) and #67 (whether broad groups should be called sectors). It deliberately retains the existing <code dir="ltr">GROUPS</code> mapping.</p><h2>Portfolio weights</h2><div><div><div>
Asset | Weight | Group
-- | -- | --
NVDA | 17% | Big Tech
MSFT | 28% | Big Tech
AAPL | 5% | Big Tech
AMD | 25% | AI & Semiconductors
TSM | 25% | AI & Semiconductors

</div></div></div><p>Both have max weight 28%, effective assets above four, no correlated-pair inputs and no qualifying drawdown. Controlled volatility at 31% contributes +20. The difference is exclusively a spurious +15 group-concentration penalty.</p><h2>Expected outcome</h2><p>Both orderings must return <strong>20 / Low</strong> for the controlled inputs, because neither broad group exceeds 50%.</p><p>The issue arises in the floating-point group summation of <code dir="ltr">engine/metrics.py:sector_exposure()</code> and is amplified by <code dir="ltr">engine/score.py:risk_score()</code> performing <code dir="ltr">sector_max &gt; 0.50</code>.</p><h2>Suggested correction and tests</h2><ul><li>Use numerically stable aggregation for normalized group weights (e.g. <code dir="ltr">math.fsum</code>) or a documented strict-boundary tolerance.</li><li>Regression-test all six permutations of NVDA, MSFT and AAPL while AMD and TSM remain fixed.</li><li>Test 49.99%, exactly 50% and 50.01% to ensure only strictly greater-than-50% exposure triggers the penalty.</li><li>Preserve the existing thematic <code dir="ltr">GROUPS</code> interpretation for this report; changing industry classification is a separate issue (#67).</li></ul><h2>Verification disclosure</h2><p>I inspected AUREN's published <code dir="ltr">engine/metrics.py</code> and <code dir="ltr">engine/score.py</code>, then reproduced both orderings in Python/pandas using their function bodies. I did not call the live risk API or claim real-market volatility results. AI assistance was used for review and reproduction.</p><p>Please evaluate this distinct numerical issue against <code dir="ltr">BOUNTY.MD</code>. If awarded, the payout destination can be supplied privately. No wallet keys or private details are included here.</p><!--EndFragment-->
</body>
</html>

---

## Process

### 1. Orient yourself first
Before touching any code:
- Read the README and any relevant docs
- Run: find . -type f | grep -v node_modules | grep -v .git | grep -v dist | head -60
- Grep for the key terms from the issue title to find the relevant files
- Read the files around the bug — understand what's currently happening

### 2. Find and read the tests
- Look for test files near the relevant code (*.test.ts, *.spec.js, __tests__, etc.)
- Read them — they tell you what behavior is expected
- Understand what a passing fix looks like before writing a line

### 3. Implement the fix
- Make the MINIMAL change that fixes the issue — nothing more
- Do not refactor, rename, reorganize, or clean up unrelated code
- Do not add dependencies unless the issue explicitly requires it
- Do not modify config files (package.json, tsconfig.json, etc.) unless that IS the fix
- One logical change, one commit

### 4. Verify
- Run the test suite: check package.json scripts for "test", "lint", "typecheck"
  Common commands: npm test, yarn test, pnpm test, pytest, go test ./..., cargo test
- If TypeScript is present: npx tsc --noEmit
- Fix any test failures your change caused — if a test was wrong before, update it

### 5. Commit and document
- git add -A
- git commit -m "fix: [Maths Bounty] Exactly 50% group exposure incorrectly adds 15 risk point"
- Write AGENT_SUMMARY.md with:
  - Root cause: what was wrong and why
  - Fix: what you changed and the reasoning
  - Verification: how to confirm it works
  - Concerns: anything a reviewer should know

---

## Stop conditions

If ANY of these are true, write "UNCERTAIN: [reason]" at the top of AGENT_SUMMARY.md, make NO code changes, and stop:
- The fix requires changing more than ~5 files
- You cannot determine what the correct behavior should be
- The issue requires a database migration, API key, or external service
- You find 3+ open PRs already attempting this fix (high competition)
- The repo is not in a language/framework you can reason about confidently

A clean UNCERTAIN is better than a bad PR.
