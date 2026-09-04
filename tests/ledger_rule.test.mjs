// Tests for shared/ledger_rule.js — the deduction ledger's (#9) group confirmation rule.
//
// FAILURE MODES UNDER TEST. The ledger's whole pedagogical value is that it confirms a GROUP and never a
// row, so the ways it can silently rot are:
//   - it confirms a group that merely CONTAINS the right members, while a stray row also claims to be one
//     (a false positive) — then the player can shotgun every row into one verdict and watch it lock;
//   - it confirms a row at a time, or leaks which row is wrong — which turns the mechanic into
//     guess-and-check and kills the reason for using it over an MCQ;
//   - it re-reports an already-locked group as "newly confirmed", so the feedback line lies;
//   - unassigned rows are treated as belonging to something.
// Run: node --test  (from escape_rooms/tests/).

import test from "node:test";
import assert from "node:assert/strict";
import { trueGroups, assignedGroups, confirmGroups, confirmAll } from "../shared/ledger_rule.js";

// Nine shrines in three families — temple's shape (2 + 3 + 4).
const ROWS = [
  { id: "s1", label: "Red banner", answer: "Sea" },
  { id: "s2", label: "Yellow banner", answer: "Sea" },
  { id: "s3", label: "Green banner", answer: "Hearth" },
  { id: "s4", label: "Blue banner", answer: "Hearth" },
  { id: "s5", label: "White banner", answer: "Hearth" },
  { id: "s6", label: "Black banner", answer: "Grove" },
  { id: "s7", label: "Grey banner", answer: "Grove" },
  { id: "s8", label: "Purple banner", answer: "Grove" },
  { id: "s9", label: "Amber banner", answer: "Grove" },
];
const ALL_RIGHT = Object.fromEntries(ROWS.map(r => [r.id, r.answer]));

test("groups are derived from the answers — no separate config to drift", () => {
  const t = trueGroups(ROWS);
  assert.deepEqual(Array.from(t.keys()).sort(), ["Grove", "Hearth", "Sea"]);
  assert.equal(t.get("Sea").size, 2);
  assert.equal(t.get("Hearth").size, 3);
  assert.equal(t.get("Grove").size, 4);
});

test("a fully correct ledger confirms every group and completes", () => {
  const r = confirmGroups(ROWS, ALL_RIGHT, new Set());
  assert.equal(r.groupCount, 3);
  assert.equal(r.locked.size, 3);
  assert.equal(r.complete, true);
  assert.deepEqual(r.newly.sort(), ["Grove", "Hearth", "Sea"]);
});

test("one correct group confirms on its own while the rest stay open", () => {
  const partial = { s1: "Sea", s2: "Sea" };            // Sea complete, nothing else assigned
  const r = confirmGroups(ROWS, partial, new Set());
  assert.deepEqual(r.newly, ["Sea"]);
  assert.equal(r.complete, false);
});

test("THE RULE: a group with all its members but ALSO a stray does NOT confirm", () => {
  // s3 is a Hearth shrine wrongly filed under Sea. Sea's true members are both present, so a
  // subset-check would wrongly lock it — this is the false-positive footgun the rule exists to stop.
  const withStray = { s1: "Sea", s2: "Sea", s3: "Sea" };
  const r = confirmGroups(ROWS, withStray, new Set());
  assert.deepEqual(r.newly, [], "a group must not confirm while a stray row claims membership");
  assert.equal(r.locked.size, 0);
});

test("THE RULE: shotgunning every row into one verdict confirms nothing", () => {
  const shotgun = Object.fromEntries(ROWS.map(r => [r.id, "Grove"]));
  const r = confirmGroups(ROWS, shotgun, new Set());
  assert.deepEqual(r.newly, []);
  assert.equal(r.complete, false);
});

test("a group missing one member does not confirm (no partial credit within a group)", () => {
  const short = { s6: "Grove", s7: "Grove", s8: "Grove" };   // s9 missing
  assert.deepEqual(confirmGroups(ROWS, short, new Set()).newly, []);
});

test("unassigned rows belong to nothing", () => {
  const blanks = { s1: "Sea", s2: "Sea", s3: "", s4: null, s5: undefined };
  const r = confirmGroups(ROWS, blanks, new Set());
  assert.deepEqual(r.newly, ["Sea"], "blank verdicts must not count toward any group");
  assert.equal(assignedGroups(blanks).size, 1);
});

test("an already-locked group is not re-reported as newly confirmed", () => {
  const r = confirmGroups(ROWS, ALL_RIGHT, new Set(["Sea"]));
  assert.equal(r.newly.includes("Sea"), false, "the progress line would lie about what just happened");
  assert.deepEqual(r.newly.sort(), ["Grove", "Hearth"]);
  assert.equal(r.complete, true);
});

test("confirmGroups does not mutate the caller's locked set", () => {
  const locked = new Set();
  confirmGroups(ROWS, ALL_RIGHT, locked);
  assert.equal(locked.size, 0, "the caller decides whether to adopt the new locks");
});

test("a Map assignment works as well as an object", () => {
  const m = new Map(Object.entries(ALL_RIGHT));
  assert.equal(confirmGroups(ROWS, m, new Set()).complete, true);
});

test("two groups minimum — a single-group ledger degrades to all-or-nothing (design rule)", () => {
  const oneGroup = [{ id: "a", answer: "X" }, { id: "b", answer: "X" }];
  assert.equal(confirmGroups(oneGroup, { a: "X", b: "X" }, new Set()).groupCount, 1,
    "authors: >=2 groups, or partial confirmation can never guide the player");
});

// ---- ALL-OR-NOTHING mode (networks/beacons) -------------------------------------------------------
// FAILURE MODE UNDER TEST. The group rule is unfishable only when groups have SEVERAL members. A ledger
// whose rows each hold a different answer degenerates to one-member groups, so a single correct dropdown
// locks its own row and the widget leaks the answer a row at a time. Beacons is that shape (four fire
// slots, four different watchtowers) AND has unlimited attempts, so the leak is fatal: ~36 submits solve
// it with no survey done. These tests pin the flag that closes it.

const FIRES = [
  { id: "f_south", label: "the southern fire", answer: "t3" },
  { id: "f_mid", label: "the middle fire", answer: "t5" },
  { id: "f_north", label: "the northern fire", answer: "t6" },
  { id: "f_far", label: "the far fire", answer: "t7" },
];
const FIRES_RIGHT = Object.fromEntries(FIRES.map(r => [r.id, r.answer]));

test("all-or-nothing: a fully correct ledger completes", () => {
  const r = confirmAll(FIRES, FIRES_RIGHT);
  assert.equal(r.complete, true);
});

test("THE POINT: three of four right confirms and locks NOTHING", () => {
  const near = { ...FIRES_RIGHT, f_far: "t0" };
  const r = confirmAll(FIRES, near);
  assert.equal(r.complete, false);
  assert.equal(r.newly.length, 0, "must not report which rows landed");
  assert.equal(r.locked.size, 0, "must not lock a correct row");
});

test("all-or-nothing closes the row-at-a-time leak that confirmGroups has here", () => {
  const oneRight = { f_south: "t3" };                     // probe a single dropdown
  assert.equal(confirmGroups(FIRES, oneRight, new Set()).newly.length, 1,
               "baseline: the group rule DOES leak on one-member groups");
  assert.equal(confirmAll(FIRES, oneRight).newly.length, 0,
               "all-or-nothing must not");
});

test("all-or-nothing: an unassigned row is never complete", () => {
  const { f_far, ...rest } = FIRES_RIGHT;
  assert.equal(confirmAll(FIRES, rest).complete, false);
});

test("all-or-nothing returns the same shape as confirmGroups", () => {
  const r = confirmAll(FIRES, FIRES_RIGHT);
  assert.deepEqual(Object.keys(r).sort(), ["complete", "groupCount", "locked", "newly"]);
  assert.equal(r.groupCount, 4);
});
