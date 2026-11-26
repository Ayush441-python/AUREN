import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import Module from "node:module";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mockTsPath = path.resolve(__dirname, "..", "src", "lib", "mock.ts");

function loadMockModule() {
  const source = fs.readFileSync(mockTsPath, "utf8");
  const { outputText } = ts.transpileModule(source, {
    fileName: mockTsPath,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
    },
  });
  const mod = { exports: {} };
  const req = Module.createRequire(mockTsPath);
  const fn = new Function("exports", "require", "module", "__filename", "__dirname", outputText);
  fn(mod.exports, req, mod, mockTsPath, path.dirname(mockTsPath));
  return mod.exports;
}

test("BASE_PORTFOLIO_ANALYSIS obeys deterministic scoring and concentration rules", () => {
  const { BASE_PORTFOLIO_ANALYSIS } = loadMockModule();

  const weights = Object.values(BASE_PORTFOLIO_ANALYSIS.normalized_weights);
  const weightSum = weights.reduce((acc, w) => acc + w, 0);
  assert.ok(Math.abs(weightSum - 1.0) < 1e-12);

  const expectedHhi = weights.reduce((acc, w) => acc + w * w, 0);
  const expectedEff = 1 / expectedHhi;
  assert.equal(BASE_PORTFOLIO_ANALYSIS.concentration.hhi, Number(expectedHhi.toFixed(4)));
  assert.equal(BASE_PORTFOLIO_ANALYSIS.concentration.effective_assets, Number(expectedEff.toFixed(2)));

  assert.equal(BASE_PORTFOLIO_ANALYSIS.correlated_pairs.length, 2);
  for (const pair of BASE_PORTFOLIO_ANALYSIS.correlated_pairs) {
    assert.ok(pair[2] > 0.70, `Expected pair correlation > 0.70, got ${pair[2]}`);
  }

  const hitsTotal = BASE_PORTFOLIO_ANALYSIS.hits.reduce((acc, [pts]) => acc + pts, 0);
  assert.equal(hitsTotal, 65);
  assert.equal(BASE_PORTFOLIO_ANALYSIS.score, 65);
  assert.equal(BASE_PORTFOLIO_ANALYSIS.level, "High");
  assert.deepEqual(
    BASE_PORTFOLIO_ANALYSIS.reasons,
    BASE_PORTFOLIO_ANALYSIS.hits.map(([, reason]) => reason)
  );
});
