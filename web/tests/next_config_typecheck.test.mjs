import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const nextConfigPath = path.resolve(import.meta.dirname, "../next.config.ts");
const source = fs.readFileSync(nextConfigPath, "utf8");

test("next.config.ts removes deprecated Next.js 16 eslint key", () => {
  assert.doesNotMatch(source, /\beslint\s*:/);
});

test("next.config.ts preserves NextConfig properties and all five redirects", () => {
  assert.match(source, /reactStrictMode:\s*true/);
  assert.match(source, /ignoreBuildErrors:\s*false/);
  for (const route of ["/proof", "/api-docs", "/new", "/p/:id", "/workstation"]) {
    assert.ok(source.includes(`"${route}"`), `missing redirect source ${route}`);
  }
});
