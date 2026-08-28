// Guard: every test suite in this directory is actually listed in package.json's `test` script.
//
// WHY. `npm test` names its files explicitly rather than globbing, so a suite that isn't listed simply
// never runs — silently, with no error and a green result. `puzzle_queue.test.mjs` sat outside the script
// from when it was written until 2026-08-13: ten passing tests that only ran if you knew to invoke them by
// hand, while `npm test` reported a confident 56/56.
//
// The trap is sharpened by the file extensions. Suites are a mix of `.test.js` (CommonJS) and `.test.mjs`
// (ES modules), so the obvious fallback — `node --test *.test.js` — ALSO misses the .mjs ones. Both routes
// to running the tests could skip the same suite at the same time.
//
// This is the invariant rather than the instance: it fails for ANY future unlisted suite, not just that one.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

test("every *.test.js / *.test.mjs here is listed in the npm test script", () => {
  const suites = readdirSync(here)
    .filter(f => /\.test\.(js|mjs)$/.test(f))
    .sort();
  const script = JSON.parse(readFileSync(join(here, "package.json"), "utf8")).scripts?.test || "";

  assert.ok(suites.length > 0, "found no test suites at all — has the glob or the directory moved?");

  const missing = suites.filter(f => !script.split(/\s+/).includes(f));
  assert.deepEqual(missing, [],
    `these suites exist but are NOT in package.json's "test" script, so \`npm test\` skips them ` +
    `silently: ${missing.join(", ")}. Add them to the script.`);
});

test("the npm test script does not name a suite that no longer exists", () => {
  // The mirror failure: a renamed or deleted suite left in the script makes `npm test` exit non-zero on a
  // missing file, which reads as a broken test run rather than a stale script.
  const here_files = new Set(readdirSync(here));
  const script = JSON.parse(readFileSync(join(here, "package.json"), "utf8")).scripts?.test || "";
  const named = script.split(/\s+/).filter(t => /\.test\.(js|mjs)$/.test(t));

  assert.ok(named.length > 0, "the test script names no suites — did its shape change?");

  const dangling = named.filter(f => !here_files.has(f));
  assert.deepEqual(dangling, [],
    `the "test" script names files that do not exist: ${dangling.join(", ")}`);
});
