"use strict";
// Tests for shared/codec.js — the submission-code encoder that ships to the browser.
// Loads the REAL file unmodified in a vm sandbox (it assigns window.EscapeCodec), so this exercises
// the exact arithmetic that must stay in lockstep with decoder/decode_codes.R.
//
// The golden vectors below were captured from the codec verified byte-for-byte against decode_codes.R
// (contract check, 2026-07-16). They use a FIXED TEST secret (not the live SECRET, which changes per
// course), so they stay stable across course rekeys. If one of these changes, the codec's byte scheme
// changed — re-sync decode_codes.R and re-run its Rscript self-test before trusting the new output.
// The two footguns these guard: base32 accumulator precision on long codes, and version/scenarioId
// arg order.  Run: node --test  (from escape_rooms/tests/).

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

function loadCodec() {
  const src = fs.readFileSync(path.join(__dirname, "../shared/codec.js"), "utf8");
  const ctx = { window: {} };
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  return ctx.window.EscapeCodec;
}

const S = "TEST_SECRET_v1";
const encode = loadCodec().encode;

const GOLDEN = {
  short_s6:  { code: "2FNB-9GAF",
    opts: { version: 1, scenarioId: 6, secret: S, studentId: "busta0001",
      steps: [{ answer: 2, attempts: 1 }, { answer: 4, attempts: 2 }, { answer: 1, attempts: 1 }] } },
  hawaii_s7: { code: "2BN9-9GB2-XR",
    opts: { version: 1, scenarioId: 7, secret: S, studentId: "busta0001",
      steps: [{ answer: 2, attempts: 1 }, { answer: 4, attempts: 3 }, { answer: 1, attempts: 1 }, { answer: 3, attempts: 2 }] } },
  long10:    { code: "KZ7Q-MXN2-1J2E-FQMA-ZVW0",
    opts: { version: 1, scenarioId: 7, secret: S, studentId: "x500zzzz",
      steps: Array.from({ length: 10 }, (_, i) => ({ answer: (i * 3) % 32, attempts: (i % 7) + 1 })) } },
  edge_lo:   { code: "NSG3-Y",
    opts: { version: 1, scenarioId: 6, secret: S, studentId: "anon", steps: [{ answer: 0, attempts: 0 }] } },
  edge_hi:   { code: "NYFN-T",
    opts: { version: 1, scenarioId: 7, secret: S, studentId: "anon", steps: [{ answer: 31, attempts: 7 }] } },
};

for (const [name, g] of Object.entries(GOLDEN)) {
  test(`golden vector: ${name} encodes stably (arithmetic drift guard)`, () => {
    assert.equal(encode(g.opts), g.code);
  });
}

test("encoding is deterministic", () => {
  const o = GOLDEN.hawaii_s7.opts;
  assert.equal(encode(o), encode(o));
});

test("student id is part of the keystream (different id -> different code)", () => {
  const base = GOLDEN.hawaii_s7.opts;
  const other = Object.assign({}, base, { studentId: "someoneElse" });
  assert.notEqual(encode(base), encode(other));
});

test("output uses only Crockford base32 (no I, L, O, U) plus dash grouping", () => {
  const code = encode(GOLDEN.long10.opts);
  assert.match(code, /^[0-9A-HJKMNP-TV-Z]+(-[0-9A-HJKMNP-TV-Z]+)*$/);
  assert.equal(/[ILOU]/.test(code.replace(/-/g, "")), false);
});

test("long (>6 byte) codes do not overflow — the base32 precision footgun", () => {
  // A 20-step run is well past the 2^53 danger zone; must still be stable + well-formed.
  const opts = { version: 1, scenarioId: 7, secret: S, studentId: "busta0001",
    steps: Array.from({ length: 20 }, (_, i) => ({ answer: (i * 7) % 32, attempts: (i % 7) + 1 })) };
  const a = encode(opts), b = encode(opts);
  assert.equal(a, b);
  assert.match(a, /^[0-9A-HJKMNP-TV-Z-]+$/);
});
