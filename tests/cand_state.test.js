"use strict";
// Tests for authoring/ui/cand_state.js — the four build-step chip states (wrap · spots · door · save)
// for one candidate image in the harness "build rooms" step. Regression home for the 2026-07-21 fix:
// after Save, commit-room clears the room's _scratch draft, so wrap/spots must fall back to the node —
// otherwise the chips wrongly drop back to grey the moment the room is saved. Run: node --test.

const test = require("node:test");
const assert = require("node:assert/strict");
const { compute } = require("../authoring/ui/cand_state.js");

const FILE = "gpt_room1_3.png";
const OPEN = "gpt_room1_3_open.png";

test("blank candidate: no draft, not committed -> all chips off", () => {
  const st = compute({}, {}, FILE, []);
  assert.deepEqual(st, { wrap: false, hotspots: false, door: false, save: false });
});

test("draft-only progress lights wrap / spots / door (uncommitted)", () => {
  const st = compute({ wrap: { haov: 360 }, hotspots: [{ type: "door" }] }, {}, FILE, [FILE, OPEN]);
  assert.equal(st.wrap, true);
  assert.equal(st.hotspots, true);   // non-empty hotspots array
  assert.equal(st.door, true);       // <stem>_open.png present in _scratch
  assert.equal(st.save, false);      // not committed yet
});

test("empty hotspots array does NOT light spots", () => {
  assert.equal(compute({ hotspots: [] }, {}, FILE, []).hotspots, false);
});

test("THE FIX: committed candidate with a cleared draft reads the node (all four green)", () => {
  const room = {
    built: true, builtFrom: FILE,
    wrap: { haov: 360 }, hotspots: [{ type: "puzzle" }], panoramaOpen: "room1/scene_open.png"
  };
  // per={} models the draft cleared by commit-room; lastScenes=[] models the _open.png no longer in _scratch
  const st = compute({}, room, FILE, []);
  assert.deepEqual(st, { wrap: true, hotspots: true, door: true, save: true });
});

test("committed-fallback is scoped to the built candidate only", () => {
  const room = { built: true, builtFrom: "gpt_room1_7.png", wrap: {}, hotspots: [{}], panoramaOpen: "x" };
  const st = compute({}, room, FILE, []);   // FILE is NOT the committed candidate
  assert.deepEqual(st, { wrap: false, hotspots: false, door: false, save: false });
});

test("door lights from either _scratch OR the committed node's panoramaOpen", () => {
  assert.equal(compute({}, {}, FILE, [OPEN]).door, true);   // in _scratch
  assert.equal(compute({}, { built: true, builtFrom: FILE, panoramaOpen: "room1/scene_open.png" }, FILE, []).door, true);
});
