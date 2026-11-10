// escape_hints.js — the escape phase's time-unlocked Hint chip, pure half (tests/escape_hints.test.mjs).
// No DOM: pano-player.js owns the chip and the card; this decides what they show.
//
// Why (Lucas, 2026-11-08): the escape is ungraded and wordless, and a student stuck in it had nothing but
// the Skip chip. `SCENARIO.escapeHints` is an optional list of 1–3 tiers, each unlocked `after` minutes
// from the start of the escape phase:
//   [{ "after": 5,  "text": "WHERE to look" },
//    { "after": 10, "text": "WHAT kind of thing matters" },
//    { "after": 15, "text": "close to the rule, never the answer" }]
// The student chooses to open the card; nothing is recorded in the codec. Absent or invalid ⇒ no chip.

export const MAX_TIERS = 3;

// Returns { ok, errors, tiers }. `tiers` is a normalised copy ({after (minutes), text}) when ok, else [].
export function validateEscapeHints(hints) {
  const errors = [];
  if (hints == null) return { ok: false, errors: ["escapeHints absent"], tiers: [] };
  if (!Array.isArray(hints)) return { ok: false, errors: ["escapeHints must be an array"], tiers: [] };
  if (hints.length < 1 || hints.length > MAX_TIERS) errors.push(`escapeHints needs 1–${MAX_TIERS} tiers, got ${hints.length}`);
  let prev = -Infinity;
  hints.forEach((t, i) => {
    const after = t && t.after, text = t && t.text;
    if (typeof after !== "number" || !isFinite(after) || after < 0) errors.push(`tier ${i + 1}: "after" must be a number of minutes ≥ 0`);
    else if (after <= prev) errors.push(`tier ${i + 1}: "after" must be later than the tier before it`);
    if (typeof after === "number" && isFinite(after)) prev = after;
    if (typeof text !== "string" || !text.trim()) errors.push(`tier ${i + 1}: "text" must be non-empty`);
    else if (/<[a-z/!]/i.test(text)) errors.push(`tier ${i + 1}: "text" must be plain text, not HTML`);
  });
  if (errors.length) return { ok: false, errors, tiers: [] };
  return { ok: true, errors, tiers: hints.map(t => ({ after: t.after, text: t.text.trim() })) };
}

// Given the scenario's escapeHints and the seconds elapsed since the escape phase began:
//   { tiers: [{tier (1-based), after, text}, ...unlocked, in order], nextInSec: seconds until the next
//     tier unlocks (null when all are open), total: tier count }
// Invalid or absent hints ⇒ { tiers: [], nextInSec: null, total: 0 }, which the player reads as "no chip".
export function hintState(hints, elapsedSec) {
  const v = validateEscapeHints(hints);
  if (!v.ok) return { tiers: [], nextInSec: null, total: 0 };
  const t = Math.max(0, Number(elapsedSec) || 0);
  const open = [];
  let nextInSec = null;
  v.tiers.forEach((h, i) => {
    const at = h.after * 60;
    if (t >= at) open.push({ tier: i + 1, after: h.after, text: h.text });
    else if (nextInSec == null) nextInSec = Math.ceil(at - t);
  });
  return { tiers: open, nextInSec, total: v.tiers.length };
}

// The chip's gentle countdown wording before a tier is open: whole minutes, rounded up.
export function countdownLabel(sec) {
  if (sec == null) return "";
  const m = Math.ceil(sec / 60);
  return m <= 1 ? "in under a minute" : `in about ${m} min`;
}
