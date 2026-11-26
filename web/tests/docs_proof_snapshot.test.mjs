import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import Module from "node:module";
import { fileURLToPath } from "node:url";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");
const srcRoot = path.join(webRoot, "src");

function loadTsModule(relPathFromSrc, stubs = {}) {
  const cache = new Map();
  const originalLoad = Module._load;

  function compile(filePath) {
    if (cache.has(filePath)) return cache.get(filePath).exports;
    const source = fs.readFileSync(filePath, "utf8");
    const { outputText } = ts.transpileModule(source, {
      fileName: filePath,
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2020,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
      },
    });
    const mod = { exports: {} };
    cache.set(filePath, mod);
    const dir = path.dirname(filePath);
    const localRequire = (specifier) => {
      if (Object.hasOwn(stubs, specifier)) return stubs[specifier];
      if (specifier.startsWith("@/")) {
        return resolveAndLoad(path.join(srcRoot, specifier.slice(2)));
      }
      if (specifier.startsWith(".")) {
        return resolveAndLoad(path.resolve(dir, specifier));
      }
      return Module.createRequire(filePath)(specifier);
    };
    const fn = new Function("exports", "require", "module", "__filename", "__dirname", outputText);
    fn(mod.exports, localRequire, mod, filePath, dir);
    return mod.exports;
  }

  function resolveAndLoad(basePath) {
    const candidates = [
      basePath,
      `${basePath}.ts`,
      `${basePath}.tsx`,
      path.join(basePath, "index.ts"),
      path.join(basePath, "index.tsx"),
    ];
    const resolved = candidates.find((p) => fs.existsSync(p) && fs.statSync(p).isFile());
    if (!resolved) {
      throw new Error(`Cannot resolve module: ${basePath}`);
    }
    return compile(resolved);
  }

  Module._load = function patchedLoad(request, parent, isMain) {
    if (Object.hasOwn(stubs, request)) return stubs[request];
    return originalLoad.call(this, request, parent, isMain);
  };

  try {
    return resolveAndLoad(path.join(srcRoot, relPathFromSrc));
  } finally {
    Module._load = originalLoad;
  }
}

test("getSnapshotTitle maps every provenance state accurately", () => {
  const { getSnapshotTitle } = loadTsModule("components/views/DocsProofView");
  assert.equal(getSnapshotTitle("reference"), "Reference snapshot");
  assert.equal(getSnapshotTitle("live"), "Live snapshot");
  assert.equal(getSnapshotTitle("stale"), "Previous snapshot");
  assert.equal(getSnapshotTitle(undefined), "Analysis snapshot");
  assert.equal(getSnapshotTitle("unexpected"), "Analysis snapshot");
});

test("DocsProofView distinguishes reference, live, stale, unknown, and absent snapshots", () => {
  const { DocsProofView } = loadTsModule("components/views/DocsProofView");
  const { BASE_PORTFOLIO_ANALYSIS } = loadTsModule("lib/mock");

  const refHtml = renderToStaticMarkup(
    React.createElement(DocsProofView, { data: BASE_PORTFOLIO_ANALYSIS, status: "reference" })
  );
  assert.match(refHtml, /<h2[^>]*>Reference snapshot<\/h2>/);
  assert.doesNotMatch(refHtml, /Live snapshot/);

  const liveHtml = renderToStaticMarkup(
    React.createElement(DocsProofView, { data: BASE_PORTFOLIO_ANALYSIS, status: "live" })
  );
  assert.match(liveHtml, /<h2[^>]*>Live snapshot<\/h2>/);

  const staleHtml = renderToStaticMarkup(
    React.createElement(DocsProofView, { data: BASE_PORTFOLIO_ANALYSIS, status: "stale" })
  );
  assert.match(staleHtml, /<h2[^>]*>Previous snapshot<\/h2>/);
  assert.doesNotMatch(staleHtml, /Live snapshot/);

  const unknownHtml = renderToStaticMarkup(
    React.createElement(DocsProofView, { data: BASE_PORTFOLIO_ANALYSIS })
  );
  assert.match(unknownHtml, /<h2[^>]*>Analysis snapshot<\/h2>/);
  assert.doesNotMatch(unknownHtml, /Live snapshot/);

  const noDataHtml = renderToStaticMarkup(React.createElement(DocsProofView));
  assert.doesNotMatch(noDataHtml, /Current analysis/);
  assert.doesNotMatch(noDataHtml, /snapshot/i);
});
