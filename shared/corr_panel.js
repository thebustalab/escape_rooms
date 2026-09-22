// corr_panel.js — the LOWER-TRIANGLE layout of the `grid` gate (2026-09-21, clouds / THE SHADOW CITY).
//
// A correlation panel: for N attributes, one cell per unordered pair, laid out as the lower triangle of the
// N x N matrix (row attribute below-left of the diagonal, column attribute across the top), each cell
// cycling through the grid's `buckets` — for clouds, flat / up / down (uncorrelated / rises together / runs
// against). It is the biplot-reading skill made into a control: reconstruct which traits move together.
//
// WHY A LAYOUT OF `grid`, NOT A NEW HOTSPOT TYPE. A grid is already an ungraded escape gate everywhere it
// matters — gate lists, done-marking, solveRoom, validators, and BOTH box editors' type whitelists (a type
// missing from those whitelists is silently rewritten to `puzzle` on load; that is how ledgers once turned
// into puzzles). The answer check is the grid's own: every item's chosen bucket must equal `answer[item]`.
// Only the card differs, so only the card is new.
//
// Authoring: { type:"grid", layout:"lowerTriangle", axes:[{key,label}, ...], buckets:[{key,label}, ...],
//              answer:{ "<rowKey>|<colKey>": bucketKey, ... }, items?: (derived when absent) }
// The FIRST bucket is every cell's starting state ("all start flat"). Pure — no DOM, tested in Node.

// Every lower-triangle pair, row-major: row i (1..N-1) against columns 0..i-1. Key "<row>|<col>".
export function triangleItems(axes) {
  const out = [];
  for (let i = 1; i < (axes || []).length; i++) {
    for (let j = 0; j < i; j++) {
      const r = axes[i], c = axes[j];
      out.push({ key: `${r.key}|${c.key}`, label: `${r.label} · ${c.label}`, row: i, col: j });
    }
  }
  return out;
}

// The bucket after `current` in `buckets`, wrapping. An unknown current restarts at the first bucket.
export function cycleBucket(buckets, current) {
  const keys = (buckets || []).map(b => b.key);
  if (!keys.length) return undefined;
  const i = keys.indexOf(current);
  return keys[(i + 1) % keys.length];
}

// Starting selection: every cell on the first bucket.
export function initialSelection(items, buckets) {
  const first = buckets && buckets[0] && buckets[0].key;
  const sel = {};
  (items || []).forEach(it => { sel[it.key] = first; });
  return sel;
}

// Same rule as the grid card's own check, exposed for tests: every item on its answer bucket.
export function isSolved(items, sel, answer) {
  return (items || []).length > 0 && items.every(it => sel[it.key] === (answer || {})[it.key]);
}

// A small line glyph per bucket key: flat = level, up = rising left→right, down = falling. Unknown keys
// fall back to the bucket's label text, so a scenario can use its own vocabulary.
export function glyphSvg(bucketKey) {
  const path = { flat: "M4 12 H20", up: "M4 19 L20 5", down: "M4 5 L20 19" }[bucketKey];
  return path
    ? `<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path d="${path}" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" fill="none"/></svg>`
    : null;
}
