"use strict";
// Tests for authoring/ui/open_target.js — which hotspot box the "Make open door" edit masks.
// Regression home for the 2026-07-20 Hawai'i-boss fix: the tool masked the ladder (a back door)
// instead of the valve keypad (a lock). Run: node --test  (from escape_rooms/tests/).

const test = require("node:test");
const assert = require("node:assert/strict");
const { pickOpenMaskHotspot, hasOpenTarget } = require("../authoring/ui/open_target.js");

const box = [0.1, 0.1, 0.2, 0.2];
const fwd  = (label = "fwd")  => ({ type: "door", label, direction: "forward", box });
const back = (label = "back") => ({ type: "door", label, direction: "back", box });
const lock = (label = "valve") => ({ type: "lock", label, box });
const legacyDoor = (label = "legacy") => ({ type: "door", label, box }); // no direction set
const open = (label = "passage") => ({ type: "door", label, direction: "open", box }); // open-world always-walkable passage

test("boss room: back-door ladder + valve lock -> masks the LOCK (the fix)", () => {
  const hs = [{ type: "puzzle", box }, back("ladder up"), lock("valve keypad"), { type: "clue", box }];
  const pick = pickOpenMaskHotspot(hs);
  assert.equal(pick.type, "lock");
  assert.equal(pick.label, "valve keypad");
  assert.equal(hasOpenTarget(hs), true);
});

test("room 1: single forward door -> masks that door", () => {
  const hs = [{ type: "puzzle", box }, fwd("the way out"), { type: "clue", box }];
  assert.equal(pickOpenMaskHotspot(hs).label, "the way out");
});

test("mid room: back door listed BEFORE forward door -> still masks the forward door", () => {
  const hs = [back("trail back"), fwd("jungle gate"), { type: "puzzle", box }];
  assert.equal(pickOpenMaskHotspot(hs).label, "jungle gate");
});

test("forward door wins even when a lock is also present", () => {
  const hs = [lock("keypad"), fwd("door onward")];
  assert.equal(pickOpenMaskHotspot(hs).type, "door");
  assert.equal(pickOpenMaskHotspot(hs).label, "door onward");
});

test("legacy door with no direction is treated as forward", () => {
  const hs = [legacyDoor("old door")];
  assert.equal(pickOpenMaskHotspot(hs).label, "old door");
});

test("room with ONLY a back door and no lock has nothing to reveal -> null / disabled", () => {
  const hs = [back("passage back"), { type: "puzzle", box }, { type: "clue", box }];
  assert.equal(pickOpenMaskHotspot(hs), null);
  assert.equal(hasOpenTarget(hs), false);
});

test("open-world room: OPEN passages listed before the forward door -> masks the FORWARD door (2026-07-31 airship-deck fix)", () => {
  // the weather deck: apothecary (open) + mast to nest (open) come before the forward bridge door
  const hs = [{ type: "puzzle", box }, open("down to apothecary"), open("up the mast"), fwd("forward to the bridge"), lock("bridge hatch keypad")];
  assert.equal(pickOpenMaskHotspot(hs).label, "forward to the bridge");
});

test("open passages never win over a lock either (forward -> lock -> nothing)", () => {
  const hs = [open("passage a"), lock("valve"), open("passage b")];
  assert.equal(pickOpenMaskHotspot(hs).type, "lock");
});

test("room whose only doors are OPEN passages has nothing to reveal -> null / disabled", () => {
  const hs = [open("north"), open("south"), { type: "puzzle", box }];
  assert.equal(pickOpenMaskHotspot(hs), null);
  assert.equal(hasOpenTarget(hs), false);
});

test("a door/lock without a drawn box is ignored", () => {
  assert.equal(pickOpenMaskHotspot([{ type: "door", direction: "forward" }]), null);
  assert.equal(pickOpenMaskHotspot([{ type: "lock" }]), null);
});

test("empty / non-array input is safe", () => {
  assert.equal(pickOpenMaskHotspot([]), null);
  assert.equal(pickOpenMaskHotspot(undefined), null);
  assert.equal(hasOpenTarget(null), false);
});
