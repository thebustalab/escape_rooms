// Tests for shared/cond.js — the gate-condition grammar behind unlockedWhen / availableWhen / variants.
//
// FAILURE MODES UNDER TEST. A gate that evaluates wrongly is invisible in review and catastrophic in
// play: too loose and the world opens early (a player reaches an escape without doing the survey it
// tests); too tight and the scenario is unfinishable. The specific ways this rots:
//   - a composed gate silently ignoring one of its clauses, so "boss AND nine tiles" opens on either;
//   - an unknown/typo'd clause failing OPEN, which would let a mis-authored gate unlock everything;
//   - `gte` treating a missing counter as anything but zero;
//   - `eq`/`ne` comparing types rather than values (dial state arrives as a string).
// Run: node --test  (from escape_rooms/tests/).

import test from "node:test";
import assert from "node:assert/strict";
import { condHolds } from "../shared/cond.js";

const CTX = { solved: new Set(["fenwatch", "sisters", "whistlegate"]), state: { tiles: 9, lever: "north" } };
const h = (c) => condHolds(c, CTX);

test("the trivial forms", () => {
  assert.equal(h(undefined), true, "absent gate is open");
  assert.equal(h(true), true);
  assert.equal(h(false), false);
});

test("solved / allSolved read the solved set", () => {
  assert.equal(h({ solved: "fenwatch" }), true);
  assert.equal(h({ solved: "crown" }), false);
  assert.equal(h({ allSolved: ["fenwatch", "sisters"] }), true);
  assert.equal(h({ allSolved: ["fenwatch", "crown"] }), false);
});

test("gte reads counters, and a missing counter is zero, not undefined", () => {
  assert.equal(h({ gte: ["tiles", 9] }), true);
  assert.equal(h({ gte: ["tiles", 10] }), false);
  assert.equal(h({ gte: ["never_set", 1] }), false);
  assert.equal(h({ gte: ["never_set", 0] }), true, "zero counter still satisfies >= 0");
});

test("eq / ne compare as strings, because dial state arrives as one", () => {
  assert.equal(h({ eq: ["lever", "north"] }), true);
  assert.equal(h({ ne: ["lever", "north"] }), false);
  assert.equal(h({ ne: ["lever", "south"] }), true);
});

test("THE POINT: `all` needs every clause — beacons' escape gate", () => {
  const gate = { all: [{ solved: "whistlegate" }, { gte: ["tiles", 9] }] };
  assert.equal(h(gate), true, "boss solved and nine tiles -> open");
  assert.equal(condHolds(gate, { solved: new Set(["whistlegate"]), state: { tiles: 8 } }), false,
               "boss solved but a tile short -> shut");
  assert.equal(condHolds(gate, { solved: new Set(), state: { tiles: 9 } }), false,
               "all nine tiles but no boss -> shut");
});

test("`any` needs only one, and both composers nest", () => {
  assert.equal(h({ any: [{ solved: "crown" }, { gte: ["tiles", 9] }] }), true);
  assert.equal(h({ any: [{ solved: "crown" }, { gte: ["tiles", 99] }] }), false);
  assert.equal(h({ all: [{ any: [{ solved: "crown" }, { solved: "sisters" }] },
                         { gte: ["tiles", 9] }] }), true, "nested composition");
});

test("an unknown clause fails CLOSED — a gate nobody can evaluate must not open the world", () => {
  assert.equal(h({ unlockedWhenever: true }), false);
  assert.equal(h({}), false);
  assert.equal(h({ all: [{ solved: "fenwatch" }, { typo: 1 }] }), false,
               "one unreadable clause shuts the whole composition");
});
