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
// arg order.
//
// V2 (2026-09-02) widened the scenario id to its own byte. v1 packed it into four bits, so ids above 15
// were SILENTLY TRUNCATED to id & 15 — a code then never matched its own decoder key and every
// submission graded "invalid/mismatched code", points NA. Two BUILT scenarios were affected (egypt 17,
// temple 18). The v2 vectors below were cross-checked byte-for-byte against decode_codes.R the same way
// the v1 ones were; both paths are pinned because v1 codes must stay decodable.
// Run: node --test  (from escape_rooms/tests/).

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

// ---- v2: the two-byte header -----------------------------------------------------------------------
// Cross-checked against decode_codes.R on 2026-09-02 (identical strings for every id below).
const V2_STEPS = [{ answer: 2, attempts: 1 }, { answer: 3, attempts: 1 },
                  { answer: 0, attempts: 1 }, { answer: 1, attempts: 1 }];
const V2_VECTORS = [
  [6,   "JXTA-BHM2-9AMG"],
  [15,  "JXYT-BHM2-98S0"],
  [17,  "JXHT-BHM2-98Y0"],   // wrangling/egypt — ungradeable under v1
  [18,  "JXGA-BHM2-9AYG"],   // hierarchical_clustering/temple — ungradeable under v1
  [19,  "JXGT-BHM2-98Z0"],   // networks/beacons
  [255, "JY6T-BHM2-98H0"],   // the top of the widened range
];

test("v2 golden vectors — must stay byte-identical to decode_codes.R", () => {
  for (const [id, expected] of V2_VECTORS) {
    assert.equal(encode({ version: 2, scenarioId: id, secret: "TEST_SECRET_v1",
                          studentId: "xcheck", steps: V2_STEPS }), expected,
                 `v2 scenarioId ${id}`);
  }
});

test("THE POINT: ids above 15 are now DISTINCT, not aliased onto id & 15", () => {
  const mint = (id) => encode({ version: 2, scenarioId: id, secret: "TEST_SECRET_v1",
                                studentId: "xcheck", steps: V2_STEPS });
  // under v1 these pairs collided (17&15==1, 18&15==2, 19&15==3); under v2 they must not
  for (const [a, b] of [[17, 1], [18, 2], [19, 3], [16, 32]]) {
    assert.notEqual(mint(a), mint(b), `${a} must not alias onto ${b}`);
  }
});

test("out-of-range ids are REFUSED, never silently truncated", () => {
  const mint = (v, id) => encode({ version: v, scenarioId: id, secret: "TEST_SECRET_v1",
                                   studentId: "x", steps: V2_STEPS });
  // NB: the codec is loaded in a `vm` realm, so the RangeError it throws is that realm's constructor
  // and cross-realm `instanceof` is FALSE. Assert on the error's name, not its identity — passing
  // `RangeError` here silently never matches and the test would pass for the wrong reason.
  const refuses = (v, id, why) =>
    assert.throws(() => mint(v, id), (e) => e.name === "RangeError" && /scenarioId/.test(e.message), why);
  refuses(1, 19, "v1 must refuse an id it cannot represent");
  refuses(2, 256, "v2 must refuse above its own range");
  refuses(2, 0, "zero is not a valid scenario id");
  // and the happy path still mints
  assert.equal(typeof mint(2, 19), "string");
});
