// Tests for shared/variant_resolve.js — which per-hotspot state variant is active given world state.
// Phase 3 / Option 2: multiple objects can be active at once; last satisfied variant wins per object;
// no match → object shows base (omitted from the active set). Evaluator is injected (here a fake that
// mimics condOK's {eq}/{solved} shapes) so the selection logic is tested without a browser.

import test from "node:test";
import assert from "node:assert/strict";
import { pickActiveVariants, roomHasVariants } from "../shared/variant_resolve.js";

const box = [0.1, 0.1, 0.2, 0.2];
const box2 = [0.5, 0.5, 0.7, 0.7];

// fake evaluator: true / {solved:k} against a set / {eq:[k,v]} against a bag
const makeEval = (solved = new Set(), bag = {}) => (cond) => {
  if (cond === undefined || cond === true) return true;
  if (cond === false) return false;
  if (cond && typeof cond === "object") {
    if ("solved" in cond) return solved.has(cond.solved);
    if ("eq" in cond) return String(bag[cond.eq[0]]) === String(cond.eq[1]);
  }
  return false;
};

test("no variants anywhere → empty active set", () => {
  const hs = [{ id: "a", type: "puzzle", box }, { id: "b", type: "door", box }];
  assert.deepEqual(pickActiveVariants(hs, makeEval()), []);
  assert.equal(roomHasVariants(hs), false);
});

test("single object: variant fires only when its condition is met", () => {
  const hs = [{ id: "lamp", type: "clue", box, variants: [
    { state: "on", when: { eq: ["lamp", "on"] }, panorama: "r/lamp_on.png" },
  ] }];
  assert.deepEqual(pickActiveVariants(hs, makeEval(new Set(), { lamp: "off" })), []);
  const on = pickActiveVariants(hs, makeEval(new Set(), { lamp: "on" }));
  assert.equal(on.length, 1);
  assert.equal(on[0].panorama, "r/lamp_on.png");
  assert.deepEqual(on[0].box, box);           // defaults to the hotspot box
  assert.equal(roomHasVariants(hs), true);
});

test("two independent objects active simultaneously (Option 2 core case)", () => {
  const hs = [
    { id: "lever", type: "puzzle", box, variants: [
      { state: "thrown", when: { solved: "room1" }, panorama: "r/lever.png" }] },
    { id: "lamp", type: "clue", box: box2, variants: [
      { state: "on", when: { eq: ["lamp", "on"] }, panorama: "r/lamp.png" }] },
  ];
  const both = pickActiveVariants(hs, makeEval(new Set(["room1"]), { lamp: "on" }));
  assert.equal(both.length, 2);
  assert.deepEqual(both.map(v => v.hotspotId).sort(), ["lamp", "lever"]);
});

test("last satisfied variant wins (author order = priority)", () => {
  const hs = [{ id: "dial", type: "dial", box, variants: [
    { state: "m1", when: { eq: ["m", "1"] }, panorama: "r/m1.png" },
    { state: "hot", when: true, panorama: "r/hot.png" },          // always-true → wins over m1
    { state: "m3", when: { eq: ["m", "3"] }, panorama: "r/m3.png" },
  ] }];
  const got = pickActiveVariants(hs, makeEval(new Set(), { m: "1" }));
  assert.equal(got.length, 1);
  assert.equal(got[0].panorama, "r/hot.png");  // last satisfied (m1 true, hot true, m3 false) → hot
});

test("variant with an explicit box overrides the hotspot box; imageless/boxless variants skipped", () => {
  const hs = [{ id: "x", type: "clue", box, variants: [
    { state: "a", when: true, panorama: "r/a.png", box: box2 },
    { state: "b", when: true },                                  // no panorama → cannot be shown
  ] }];
  const got = pickActiveVariants(hs, makeEval());
  assert.equal(got.length, 1);
  assert.deepEqual(got[0].box, box2);           // explicit variant box used
});
