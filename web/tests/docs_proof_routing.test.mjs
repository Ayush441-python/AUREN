import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const webRoot = path.resolve(import.meta.dirname, "../src");
const read = (rel) => fs.readFileSync(path.join(webRoot, rel), "utf8");

test("dashboard/page.tsx maps tab=docs, proof, and api-docs to docs (never help-support)", () => {
  const dash = read("app/dashboard/page.tsx");
  assert.match(dash, /"docs"/);
  assert.doesNotMatch(dash, /docs\s*:\s*"help-support"/);
  assert.match(dash, /proof:\s*"docs"/);
  assert.match(dash, /"api-docs":\s*"docs"/);
});

test("navigationTypes.ts includes docs as a first-class NavItemKey", () => {
  const navTypes = read("lib/navigationTypes.ts");
  assert.match(navTypes, /\|\s*"docs"/);
  assert.match(navTypes, /\|\s*"help-support"/);
});

test("Workstation.tsx includes docs in ALL_NAV_TABS and renders DocsProofView for docs", () => {
  const ws = read("components/dashboard/Workstation.tsx");
  assert.match(ws, /"docs"/);
  assert.match(ws, /activeTab === "docs"\s*&&\s*<DocsProofView\s+data=\{data\}\s*\/>/);
  assert.match(ws, /activeTab === "help-support"\s*&&\s*<HelpSupportView\s*\/>/);
});

test("sidebars point API & Proof entries to tab docs", () => {
  const compact = read("components/dashboard/CompactSidebar.tsx");
  assert.match(compact, /id:\s*"docs",\s*label:\s*"API & Proof"/);
  const full = read("components/navigation/AurenSidebar.tsx");
  assert.match(full, /id:\s*"docs"[\s\S]{0,160}route:\s*"\/dashboard\?tab=docs"/);
});
