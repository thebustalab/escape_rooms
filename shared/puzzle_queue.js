// puzzle_queue.js — location-independent puzzle serving ("the dynamic puzzle queue").
//
// THE PROBLEM IT SOLVES. The normal model pins one puzzle to one room and orders them with an
// `availableWhen` chain, so the ladder's order and the world's geography are the same thing. That
// breaks for a scenario where the player roams freely and meets puzzle-bearing objects in an order
// nobody can predict — e.g. `networks/subway`, where each locked train car must present the NEXT
// rung of the ladder whichever car you happen to reach first. The ladder ESCALATES, so its order is
// load-bearing; the geography is not. This module separates the two.
//
// THE MODEL. `SCENARIO.puzzleQueue` is an ordered array of puzzle payloads (the same fields a
// `puzzle` hotspot carries: label / starterCode / question | check / feedback / solveSfx). Any
// hotspot marked `queue: true` is a SLOT: opening it serves the next unsolved queue entry, merged
// over the slot's own fields. Solve it and the queue advances, so the next slot you reach serves
// the next rung — regardless of where it is.
//
// STICKINESS MATTERS. Once a slot has been shown entry i it keeps entry i until that entry is
// solved. Without this, closing the modal and reopening a different slot could reshuffle which
// puzzle is where, and a student who walked away mid-question would come back to a different one.
//
// THE CODEC IS THE SHARP EDGE. The normal codec emits one step per graded ROOM in room order, and
// the decoder's answer key maps step k to that room's correct index. Under a queue the puzzle
// served at a given room DIFFERS BETWEEN STUDENTS, so a room-keyed code cannot be graded. Queue
// results are therefore keyed by QUEUE INDEX and emitted in queue order: step k is always queue
// entry k, for every student, which is what keeps the decoder key well-defined. `queueSteps` below
// is the only thing mintCode needs.
//
// DOM-free and evaluator-injected, like variant_resolve.js, so it unit-tests without a browser.

// The lowest queue index not yet solved, or -1 when the ladder is finished.
export function nextUnsolvedIndex(queue, solvedIdx) {
  const q = Array.isArray(queue) ? queue : [];
  for (let i = 0; i < q.length; i++) if (!solvedIdx.has(i)) return i;
  return -1;
}

// Stable identity for a slot. Ids repeat across rooms, so the room key has to be part of it.
export function slotKey(roomKey, hotspotId) {
  return `${roomKey || "?"}::${hotspotId || "?"}`;
}

// Which queue entry does this slot serve right now?
//
// `assignments` is a Map of slotKey -> index, carried across openings so a slot keeps its puzzle.
// A slot holding an already-solved index has done its job and is released back to the queue head
// (so re-entering a solved room doesn't re-serve a solved rung, and a fresh slot gets the next one).
// Returns null when the ladder is exhausted — the caller should then treat the slot as inert.
export function resolveSlot(queue, solvedIdx, assignments, key) {
  const q = Array.isArray(queue) ? queue : [];
  if (!q.length) return null;
  const held = assignments.get(key);
  if (held != null && !solvedIdx.has(held)) return { index: held, puzzle: q[held] };
  const idx = nextUnsolvedIndex(q, solvedIdx);
  if (idx < 0) return null;
  assignments.set(key, idx);
  return { index: idx, puzzle: q[idx] };
}

// The puzzle the player actually sees: the queue entry's content over the slot's own fields.
// `id`, `type` and `box` stay the SLOT's — they anchor the hotspot, the gate key and the codec's
// per-slot attempt counting, none of which should move when the content does.
export function mergeSlot(hotspot, entry) {
  const h = hotspot || {}, e = entry || {};
  return Object.assign({}, h, e, { id: h.id, type: h.type, box: h.box, queue: true });
}

// Is the graded ladder finished? An empty queue is NOT complete — same rule analysisComplete()
// uses for "no graded rooms", so a scenario can't finish an objective it never had.
export function queueComplete(queue, solvedIdx) {
  const q = Array.isArray(queue) ? queue : [];
  return q.length > 0 && q.every((_, i) => solvedIdx.has(i));
}

// Codec steps in QUEUE order — see "THE CODEC IS THE SHARP EDGE" above. Entries not yet solved are
// skipped rather than zero-filled, so a partial run encodes exactly the rungs actually answered and
// stays the same length the decoder expects for that many steps.
export function queueSteps(queue, results) {
  const q = Array.isArray(queue) ? queue : [];
  const out = [];
  for (let i = 0; i < q.length; i++) {
    if (!results.has(i)) continue;
    const r = results.get(i) || {};
    out.push({ answer: r.answer, attempts: r.attempts });
  }
  return out;
}

// Does this scenario use the queue at all? Everything above is inert unless a queue is authored,
// which is what keeps every existing scenario byte-for-byte unchanged.
export function usesQueue(scenario) {
  return !!(scenario && Array.isArray(scenario.puzzleQueue) && scenario.puzzleQueue.length);
}
