// BELL-PULL (mechanic #16, built 2026-10-20, comparing_means/spa) — the pure half.
//
// Two pieces of world-state plumbing, both reading and writing the ordinary `gameState` bag:
//   • a PULL control — a `dial` with `mode:"pull"` — flips one boolean key on every pull (lit ⇄ dark), so a
//     mistake is undone by pulling again. It writes real booleans, so `{eq:[key, true]}` in the condOK grammar
//     reads it anywhere (a `shownWhen`, a variant `when`, an `availableWhen`): that is the general "a far room
//     reacts" path, sibling of #8.
//   • a STATE LOCK — a `lock` with `mode:"state"` — has no keypad. It owns a list of `lamps`
//     ([{name, key, label?, colour?, shape?}]), draws them lit/dark from gameState, and opens when the lamps
//     named in its `answer` ("vermillion,yellow,purple") are exactly the lit ones. The answer string stays
//     the one readable record of the solution; the pattern is derived from it, never kept as a second copy.
//
// DOM-free so tests/bell_pull.test.mjs can pin it; pano-player.js does the card, the toast and the sound.

/** Is a pull key currently on? Truthiness, so a scenario `state` default of false/absent both read dark. */
export function isOn(state, key) {
  return !!(state && key != null && state[key]);
}

/** Pull once: flip the key, store a real boolean, return the new value. */
export function togglePull(state, key) {
  const on = !isOn(state, key);
  state[key] = on;
  return on;
}

/** The state key a pull writes: `key`, else the hotspot id (the same fallback a dial uses). */
export function pullKey(h) {
  return (h && (h.key || h.id)) || null;
}

/** The local message for a pull. Authored `onToast`/`offToast` win; the fallback is world-neutral. */
export function pullToast(h, on) {
  const authored = on ? h && h.onToast : h && h.offToast;
  if (authored != null) return authored;
  return on ? "You pull the cord. Somewhere far off, a bell rings."
            : "You pull the cord again. The far bell answers on a lower note.";
}

/** "vermillion, Yellow ,purple" → ["vermillion","yellow","purple"] (empty entries dropped). */
export function answerNames(answer) {
  return String(answer == null ? "" : answer).split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
}

/** Each lamp with its live state: [{...lamp, on, wanted}]. */
export function lampStates(lock, state) {
  const want = new Set(answerNames(lock && lock.answer));
  return ((lock && lock.lamps) || []).map(l => ({
    ...l,
    on: isOn(state, l.key),
    wanted: want.has(String(l.name || "").toLowerCase()),
  }));
}

/**
 * Does the world match the lock? Every lamp named in `answer` lit, every other lamp dark.
 * A lock with authoring problems (see lockProblems) never opens: fail closed, like cond.js.
 */
export function statePatternHolds(lock, state) {
  if (lockProblems(lock).length) return false;
  return lampStates(lock, state).every(l => l.on === l.wanted);
}

/** Authoring errors that would make a state lock unopenable or ambiguous. Empty = well-formed. */
export function lockProblems(lock) {
  const out = [];
  const lamps = (lock && lock.lamps) || [];
  if (!Array.isArray(lamps) || !lamps.length) { out.push("no `lamps`"); return out; }
  const names = new Set(), keys = new Set();
  lamps.forEach((l, i) => {
    const n = String((l && l.name) || "").toLowerCase();
    if (!n) out.push(`lamp ${i} has no \`name\``);
    else if (names.has(n)) out.push(`lamp name '${n}' repeats`);
    names.add(n);
    if (!l || !l.key) out.push(`lamp ${i} has no \`key\``);
    else if (keys.has(l.key)) out.push(`lamp key '${l.key}' repeats`);
    if (l && l.key) keys.add(l.key);
  });
  answerNames(lock.answer).forEach(n => { if (!names.has(n)) out.push(`answer names '${n}', which is not a lamp`); });
  return out;
}

// ---- drawing (string-only, so it stays testable) -----------------------------------------------------
// A lamp is a candle in its colour with its SHAPE stamped on the body (colour is never load-bearing alone),
// and a flame above it when lit. Pure SVG markup: no image, so it works before any art exists.
const SHAPES = {
  square:   '<rect x="-5" y="-5" width="10" height="10"/>',
  circle:   '<circle r="5.6"/>',
  diamond:  '<path d="M0 -7 L7 0 L0 7 L-7 0 Z"/>',
  triangle: '<path d="M0 -6.5 L6.5 5.5 L-6.5 5.5 Z"/>',
  star:     '<path d="M0 -7 L2 -2.2 L7 -2.2 L3 1 L4.4 6.4 L0 3.2 L-4.4 6.4 L-3 1 L-7 -2.2 L-2 -2.2 Z"/>',
};
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

export function lampSvg(lamp, on) {
  const col = /^#[0-9a-f]{3,8}$/i.test(lamp.colour || "") ? lamp.colour : "#c9a869";
  const mark = SHAPES[lamp.shape] || "";
  const flame = on
    ? '<g class="lampflame"><ellipse cx="0" cy="-35" rx="9" ry="13" fill="#ffd88c" opacity=".35"/>' +
      '<path d="M0 -46 C6 -38 6 -30 0 -26 C-6 -30 -6 -38 0 -46 Z" fill="#ffb347"/>' +
      '<path d="M0 -40 C3 -35 3 -31 0 -29 C-3 -31 -3 -35 0 -40 Z" fill="#fff4c2"/></g>'
    : '<path d="M0 -26 C1 -30 -1 -33 1 -37" stroke="#8a8a8a" stroke-width="1.2" fill="none" opacity=".6"/>';
  return `<svg viewBox="-20 -50 40 100" width="56" height="140" aria-hidden="true">` + flame +
    `<line x1="0" y1="-26" x2="0" y2="-20" stroke="#2b2b2b" stroke-width="1.5"/>` +
    `<rect x="-10" y="-20" width="20" height="56" rx="3" fill="${col}" opacity="${on ? 1 : 0.55}"/>` +
    `<g transform="translate(0 4)" fill="rgba(0,0,0,.45)">${mark}</g>` +
    `<rect x="-15" y="36" width="30" height="5" rx="1.5" fill="#3a3530"/></svg>`;
}

/** The whole read-out row as markup; each lamp carries an aria-label saying lit/dark in words. */
export function lampRowHtml(lock, state) {
  return '<div class="lamprow">' + lampStates(lock, state).map(l => {
    const label = l.label || l.name;
    return `<figure class="lamp${l.on ? " lit" : ""}" data-key="${esc(l.key)}" role="img" ` +
           `aria-label="${esc(label)}, ${l.on ? "lit" : "dark"}">${lampSvg(l, l.on)}` +
           `<figcaption>${esc(label)}</figcaption></figure>`;
  }).join("") + "</div>";
}

// ---- sound ---------------------------------------------------------------------------------------------
// A pull rings even before any bell recording exists: a short synthesised strike (inharmonic partials with
// an exponential decay). The "off" pull rings lower and duller, so the two pulls are told apart by ear.
// `ctx` is an AudioContext supplied by the player; nothing here runs at import time.
export function ringBell(ctx, on, volume = 0.35) {
  if (!ctx) return;
  const t = ctx.currentTime, base = on ? 660 : 440, dur = on ? 2.2 : 1.2;
  [1, 2.76, 5.4].forEach((m, i) => {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sine"; o.frequency.value = base * m;
    const peak = volume / (i + 1) / (on ? 1 : 1.6);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur / (i + 1));
    o.connect(g); g.connect(ctx.destination);
    o.start(t); o.stop(t + dur);
  });
}
