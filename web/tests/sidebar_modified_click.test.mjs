import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const sidebarPath = path.resolve(
  import.meta.dirname,
  "../src/components/navigation/AurenSidebar.tsx"
);
const source = fs.readFileSync(sidebarPath, "utf8");

function loadSidebarClickGuard() {
  const match = source.match(
    /export function shouldInterceptSidebarClick\([\s\S]*?\): boolean (\{[\s\S]*?\n\})/
  );
  assert.ok(match, "shouldInterceptSidebarClick must be exported from AurenSidebar.tsx");
  const handleMatch = source.match(
    /const handleItemClick = \(entry: NavEntry, e: React\.MouseEvent\) => (\{[\s\S]*?\n  \};)/
  );
  assert.ok(handleMatch, "handleItemClick must exist in AurenSidebar.tsx");
  assert.ok(
    handleMatch[1].indexOf("shouldInterceptSidebarClick(e)") <
      handleMatch[1].indexOf("e.preventDefault()"),
    "handleItemClick must check shouldInterceptSidebarClick(e) before calling e.preventDefault()"
  );
  return vm.runInNewContext(`
    function shouldInterceptSidebarClick(e) ${match[1]}
    shouldInterceptSidebarClick;
  `);
}

function makeEvent(overrides = {}) {
  return {
    defaultPrevented: false,
    button: 0,
    metaKey: false,
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    ...overrides,
  };
}

test("modified and non-primary clicks preserve native browser behavior", () => {
  const shouldIntercept = loadSidebarClickGuard();
  for (const mod of [
    { ctrlKey: true },
    { metaKey: true },
    { shiftKey: true },
    { altKey: true },
    { button: 1 },
    { button: 2 },
    { defaultPrevented: true },
  ]) {
    assert.equal(
      shouldIntercept(makeEvent(mod)),
      false,
      `expected false for ${JSON.stringify(mod)}`
    );
  }
});

test("plain primary click is intercepted for client-side tab switching", () => {
  const shouldIntercept = loadSidebarClickGuard();
  assert.equal(shouldIntercept(makeEvent()), true);
});
