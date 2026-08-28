// Unit tests for shared/particles.js — the ambient-particle vocabulary + per-kind field density.
//
// WHY THIS EXISTS. The density map is the part of the ambient system most likely to regress silently.
// It began as a `kind === "snow" ? 40 : 18` ternary COPY-PASTED across four call sites in
// pano-player.js; adding `dust` (2026-08-13) meant a third case, and a fourth (`rays`) landed the same
// day. With the ternary duplicated, adding a kind meant remembering all four sites, and forgetting one
// produced no error — just a landing screen with the wrong density, which nobody would spot as a bug.
// So the map was pulled into one pure function and pinned here.
//
// The other trap: an UNKNOWN kind deliberately falls through to the fireflies default rather than
// throwing, so a typo'd `ambient` value renders something plausible and stays invisible. These tests
// pin that fallback as intended behaviour so nobody "fixes" it into a throw — but see the vocabulary
// tests, which are what actually catch a typo, and are why the harness authors this via a dropdown.

import { test } from "node:test";
import assert from "node:assert/strict";
import { AMBIENT_KINDS, particleCount, isAmbientKind } from "../shared/particles.js";

test("every supported kind is in the vocabulary, including none", () => {
  for (const k of ["fireflies", "snow", "embers", "leaves", "dust", "rays", "none"]) {
    assert.ok(AMBIENT_KINDS.includes(k), `${k} missing from AMBIENT_KINDS`);
  }
  assert.equal(AMBIENT_KINDS.length, 7, "a kind was added or removed without updating this test");
});

test("isAmbientKind accepts real kinds and rejects typos", () => {
  assert.equal(isAmbientKind("dust"), true);
  assert.equal(isAmbientKind("rays"), true);
  assert.equal(isAmbientKind("none"), true, "'none' is a valid authored value, not an absence");
  assert.equal(isAmbientKind("dusts"), false);
  assert.equal(isAmbientKind("sunrays"), false);
  assert.equal(isAmbientKind(""), false);
  assert.equal(isAmbientKind(undefined), false);
});

test("the big screens always get at least as many particles as the interstitial", () => {
  for (const k of AMBIENT_KINDS) {
    assert.ok(particleCount(k, true) >= particleCount(k, false),
      `${k}: landing/submission density must not be below the interstitial's`);
  }
});

test("every kind returns a positive integer count on both screen sizes", () => {
  for (const k of AMBIENT_KINDS) {
    for (const big of [true, false]) {
      const n = particleCount(k, big);
      assert.ok(Number.isInteger(n) && n > 0, `${k} (big=${big}) returned ${n}`);
    }
  }
});

test("density is genuinely per-kind — the three special cases differ from the default", () => {
  const dflt = particleCount("fireflies", true);
  assert.notEqual(particleCount("snow", true), dflt, "snow should not have collapsed to the default");
  assert.notEqual(particleCount("dust", true), dflt, "dust should not have collapsed to the default");
  assert.notEqual(particleCount("rays", true), dflt, "rays should not have collapsed to the default");
});

test("dust is the densest field and rays the sparsest — the shape rule behind the map", () => {
  // dust motes are the finest thing drawn (1.5–4px) so they need the most to read as a haze;
  // rays are long blurred BARS, so a handful reads as light and a crowd reads as a curtain.
  const counts = AMBIENT_KINDS.filter(k => k !== "none").map(k => [k, particleCount(k, true)]);
  const densest = counts.reduce((a, b) => (b[1] > a[1] ? b : a));
  const sparsest = counts.reduce((a, b) => (b[1] < a[1] ? b : a));
  assert.equal(densest[0], "dust");
  assert.equal(sparsest[0], "rays");
});

test("fireflies, embers and leaves share the default density", () => {
  for (const big of [true, false]) {
    const n = particleCount("fireflies", big);
    assert.equal(particleCount("embers", big), n);
    assert.equal(particleCount("leaves", big), n);
  }
});

test("an UNKNOWN kind falls back to the default density rather than throwing", () => {
  // Deliberate: the renderer draws fireflies for anything it doesn't recognise, so the count must
  // match what actually gets drawn. Don't "fix" this into a throw — a live scenario would go blank.
  for (const big of [true, false]) {
    assert.equal(particleCount("kelp", big), particleCount("fireflies", big));
    assert.equal(particleCount(undefined, big), particleCount("fireflies", big));
  }
});

test("'none' still returns a count — the caller, not the map, decides to skip drawing", () => {
  // pano-player guards with `if (amb !== "none")` before calling. If that guard is ever removed the
  // map must not be the thing that silently starts drawing a field on a scenario that asked for none.
  assert.ok(particleCount("none", true) > 0);
});
