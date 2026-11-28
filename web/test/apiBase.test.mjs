import test from "node:test";
import assert from "node:assert/strict";

import { LOCAL_API_BASE, PRODUCTION_API_BASE, resolveApiBase } from "../src/lib/apiBase.ts";

test("saved override wins over everything", () => {
  assert.equal(
    resolveApiBase({ saved: "http://localhost:9999", envUrl: "http://127.0.0.1:9000", hostname: "localhost" }),
    "http://localhost:9999",
  );
});

test("saved override loses its trailing slashes", () => {
  assert.equal(resolveApiBase({ saved: "http://localhost:9999///" }), "http://localhost:9999");
});

test("an explicit env URL wins on localhost too (#411)", () => {
  assert.equal(
    resolveApiBase({ saved: null, envUrl: "http://127.0.0.1:9000", hostname: "localhost" }),
    "http://127.0.0.1:9000",
  );
  assert.equal(
    resolveApiBase({ saved: null, envUrl: "http://127.0.0.1:9000", hostname: "127.0.0.1" }),
    "http://127.0.0.1:9000",
  );
});

test("localhost falls back to the local backend when nothing is configured", () => {
  assert.equal(resolveApiBase({ saved: null, envUrl: null, hostname: "localhost" }), LOCAL_API_BASE);
  assert.equal(resolveApiBase({ saved: "", envUrl: "", hostname: "127.0.0.1" }), LOCAL_API_BASE);
});

test("a non-local host falls back to the deployed backend", () => {
  assert.equal(resolveApiBase({ saved: null, envUrl: null, hostname: "example.org" }), PRODUCTION_API_BASE);
});

test("outside a browser the hostname is unknown and the env URL still applies", () => {
  assert.equal(resolveApiBase({ saved: null, envUrl: "http://127.0.0.1:9000", hostname: null }), "http://127.0.0.1:9000");
  assert.equal(resolveApiBase({ saved: null, envUrl: null, hostname: null }), PRODUCTION_API_BASE);
});
