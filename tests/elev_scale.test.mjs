// Tests for shared/elev_scale.js — the elevation map's pixel <-> height scale.
//
// FAILURE MODES UNDER TEST. The map's pedagogical claim is that the axis is properly SCALED, so that
// dragging junction nodes to their surveyed heights IS plotting the dendrogram, and a waterline across
// it IS a dendrogram cut. If the mapping is wrong the plot lies and the cut the player reads off it is
// wrong — silently, because a plausible-looking drawing gives no error. Specifically:
//   - y and elevation must be INVERTED (higher elevation = nearer the top); getting this backwards makes
//     every cut read the wrong way round and inverts the canyon's whole lesson;
//   - the round trip must be lossless, or nodes creep as the player nudges them;
//   - a drag past the ends must CLAMP to the axis, not record an out-of-range height;
//   - a zero-height span (a mis-authored axis) must not divide by zero;
//   - a node with no recorded height is neither above nor below the waterline.
// Run: node --test  (from escape_rooms/tests/).

import test from "node:test";
import assert from "node:assert/strict";
import { makeScale, junctionsAbove, placedCount } from "../shared/elev_scale.js";

// Canyon's real axis and its seven confluences.
const AX = { min: 800, max: 1500, height: 300, padTop: 14, padBottom: 26 };
const NODES = [
  { id: "c1", answer: 1400 }, { id: "c2", answer: 1380 }, { id: "c3", answer: 1050 },
  { id: "c4", answer: 1420 }, { id: "c5", answer: 1390 }, { id: "c6", answer: 1200 },
  { id: "c7", answer: 850 },
];
const SURVEYED = Object.fromEntries(NODES.map(n => [n.id, n.answer]));

test("the axis is inverted: a higher elevation sits nearer the top", () => {
  const s = makeScale(AX);
  assert.ok(s.yFor(1400) < s.yFor(1050), "1400 m must draw ABOVE 1050 m");
  assert.equal(s.yFor(AX.max), AX.padTop);
  assert.equal(s.yFor(AX.min), AX.padTop + s.plot);
});

test("pixel -> elevation -> pixel round-trips", () => {
  const s = makeScale(AX);
  for (const v of [800, 1050, 1125, 1200, 1500]) {
    assert.equal(s.snap(s.vFor(s.yFor(v))), v, `round trip lost ${v}`);
  }
});

test("a drag past either end clamps to the axis, never out of range", () => {
  const s = makeScale(AX);
  assert.equal(s.snap(9999), 1500);
  assert.equal(s.snap(-40), 800);
  assert.equal(s.snap(s.vFor(-500)), 1500, "dragged above the plot = the top of the scale");
  assert.equal(s.snap(s.vFor(5000)), 800, "dragged below the plot = the bottom of the scale");
});

test("step snapping rounds to the authored increment, after clamping", () => {
  const s = makeScale({ ...AX, step: 25 });
  assert.equal(s.snap(1137), 1125);
  assert.equal(s.snap(1140), 1150);
  assert.equal(s.snap(99999), 1500, "clamp first, or a huge drag snaps to a height off the axis");
});

test("a zero-span axis does not divide by zero", () => {
  const s = makeScale({ min: 1000, max: 1000, height: 300 });
  assert.ok(Number.isFinite(s.yFor(1000)));
  assert.ok(Number.isFinite(s.vFor(10)));
});

test("the canyon cut: the 1125 waterline leaves the RIGHT half whole and splits the LEFT", () => {
  // The verified escape topology. Above 1125: c1 1400, c2 1380, c4 1420, c5 1390, c6 1200 — five
  // junctions still dry. c3 (1050) and c7 (850) are drowned, which is what splits the left half.
  assert.equal(junctionsAbove(NODES, SURVEYED, 1125), 5);
  assert.equal(junctionsAbove(NODES, SURVEYED, 1300), 4, "above both mids -> every pair separate");
  assert.equal(junctionsAbove(NODES, SURVEYED, 950), 6, "below both mids -> the two halves");
});

test("an unplaced junction is neither above nor below the waterline", () => {
  const partial = { c1: 1400, c2: 1380 };
  assert.equal(junctionsAbove(NODES, partial, 1125), 2);
  assert.equal(placedCount(NODES, partial), 2);
  assert.equal(placedCount(NODES, {}), 0);
});

test("placedCount is what a {gte:[key,n]} gate reads — it must reach the full node count", () => {
  assert.equal(placedCount(NODES, SURVEYED), 7, "the canyon escape panel opens on 7 of 7");
});
