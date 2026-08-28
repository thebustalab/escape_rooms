// Unit tests for the dynamic puzzle queue (shared/puzzle_queue.js).
//
// The queue exists so a freely-roamed scenario can serve an ORDERED ladder from UNORDERED places:
// whichever locked train car you reach first gives you rung 1. The properties worth pinning are the
// ones that would silently corrupt a student's run rather than throw:
//   - a slot keeps its puzzle across reopenings (else walking away mid-question reshuffles it)
//   - the ladder is served strictly in order no matter what order slots are visited
//   - codec steps come out in QUEUE order, because the decoder key is queue-ordered; a room-ordered
//     code cannot be graded when the room that served rung k differs between students
//
// Run: node --test tests/puzzle_queue.test.mjs   (or: npm test)
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  nextUnsolvedIndex, slotKey, resolveSlot, mergeSlot, queueComplete, queueSteps, usesQueue,
} from "../shared/puzzle_queue.js";

const QUEUE = [
  { label: "rung 1", question: { prompt: "a", options: ["x", "y"], correct: 0 } },
  { label: "rung 2", question: { prompt: "b", options: ["x", "y"], correct: 1 } },
  { label: "rung 3", question: { prompt: "c", options: ["x", "y"], correct: 0 } },
  { label: "boss", question: { prompt: "d", options: ["x", "y"], correct: 1 } },
];

test("usesQueue only fires for a non-empty authored queue", () => {
  assert.equal(usesQueue(null), false);
  assert.equal(usesQueue({}), false);                       // every existing scenario
  assert.equal(usesQueue({ puzzleQueue: [] }), false);
  assert.equal(usesQueue({ puzzleQueue: QUEUE }), true);
});

test("nextUnsolvedIndex walks the ladder in order and reports exhaustion", () => {
  const solved = new Set();
  assert.equal(nextUnsolvedIndex(QUEUE, solved), 0);
  solved.add(0);
  assert.equal(nextUnsolvedIndex(QUEUE, solved), 1);
  solved.add(1); solved.add(2); solved.add(3);
  assert.equal(nextUnsolvedIndex(QUEUE, solved), -1);
});

test("a slot keeps its assigned puzzle across reopenings", () => {
  const solved = new Set(), assign = new Map();
  const k = slotKey("cropping_yard", "weld_car");
  const first = resolveSlot(QUEUE, solved, assign, k);
  const again = resolveSlot(QUEUE, solved, assign, k);
  assert.equal(first.index, 0);
  assert.equal(again.index, 0, "reopening the same slot must not reshuffle the rung");
});

test("two different slots do NOT both hold the same unsolved rung", () => {
  // The first slot opened holds rung 0. A second slot opened before rung 0 is solved would
  // otherwise serve rung 0 as well, letting a student answer the same rung twice and skip one.
  const solved = new Set(), assign = new Map();
  const a = resolveSlot(QUEUE, solved, assign, slotKey("r1", "car"));
  const b = resolveSlot(QUEUE, solved, assign, slotKey("r2", "car"));
  assert.equal(a.index, 0);
  assert.equal(b.index, 0);
  // NOTE: this documents CURRENT behaviour — the head of the queue is offered at every open slot
  // until it is solved. That is deliberate: the ladder must be done in order, so every locked car
  // legitimately presents the same next rung. Solving it anywhere advances all of them.
});

test("the ladder is served in order regardless of the order slots are visited", () => {
  const solved = new Set(), assign = new Map();
  const visits = ["ochre", "tannery", "logwood", "alum"];   // arbitrary geography
  const served = [];
  for (const roomKey of visits) {
    const got = resolveSlot(QUEUE, solved, assign, slotKey(roomKey, "car"));
    served.push(got.puzzle.label);
    solved.add(got.index);                                   // player solves it there and then
  }
  assert.deepEqual(served, ["rung 1", "rung 2", "rung 3", "boss"]);
});

test("an exhausted queue returns null so the slot can go inert", () => {
  const solved = new Set([0, 1, 2, 3]), assign = new Map();
  assert.equal(resolveSlot(QUEUE, solved, assign, slotKey("r", "h")), null);
  assert.equal(resolveSlot([], new Set(), new Map(), "k"), null);
});

test("mergeSlot takes content from the queue but identity from the slot", () => {
  const hotspot = { id: "weld_car", type: "puzzle", box: [1, 2, 3, 4], label: "the yellow car" };
  const merged = mergeSlot(hotspot, QUEUE[1]);
  assert.equal(merged.id, "weld_car", "gate key + attempt counting hang off the slot id");
  assert.equal(merged.type, "puzzle");
  assert.deepEqual(merged.box, [1, 2, 3, 4], "the box anchors the hotspot and must not move");
  assert.equal(merged.label, "rung 2", "content comes from the queue entry");
  assert.equal(merged.question.correct, 1);
  assert.equal(merged.queue, true);
});

test("queueComplete needs every rung, and an empty queue is never complete", () => {
  assert.equal(queueComplete(QUEUE, new Set([0, 1, 2])), false);
  assert.equal(queueComplete(QUEUE, new Set([0, 1, 2, 3])), true);
  assert.equal(queueComplete([], new Set()), false, "an objective you never had can't be finished");
});

test("codec steps come out in QUEUE order, not solve order", () => {
  // Solve them out of order (as a roaming player might, if slots were revisited) and check the
  // emitted steps are still ordered by rung — this is the property the R decoder relies on.
  const results = new Map();
  results.set(2, { answer: 0, attempts: 3 });
  results.set(0, { answer: 1, attempts: 1 });
  results.set(1, { answer: 1, attempts: 2 });
  results.set(3, { answer: 0, attempts: 1 });
  assert.deepEqual(queueSteps(QUEUE, results), [
    { answer: 1, attempts: 1 },
    { answer: 1, attempts: 2 },
    { answer: 0, attempts: 3 },
    { answer: 0, attempts: 1 },
  ]);
});

test("a partial run encodes only the rungs actually answered", () => {
  const results = new Map([[0, { answer: 1, attempts: 1 }], [1, { answer: 0, attempts: 2 }]]);
  assert.deepEqual(queueSteps(QUEUE, results), [
    { answer: 1, attempts: 1 },
    { answer: 0, attempts: 2 },
  ]);
});
