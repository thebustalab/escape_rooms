// lock_console.js — the pure half of a limited-attempt keypad lock (observatory's pointing console, 2026-11-21).
// Editing this? Read _agent_reference/doors_and_progression.md first.
//
// Before this, a lock's `maxAttempts` only greyed the keypad for the current opening: closing and reopening
// it reset nothing visible, and a right code still passed, so no lock could actually be failed. Observatory's
// escape is three pointings and a hard fail, so the lock now:
//   - stays LOCKED OUT once the attempts are spent (checked on every opening, not just after the last try);
//   - can answer each wrong code with what the world shows for it (`eyepiece`: the view for a known code,
//     empty sky otherwise, then a per-miss line such as the headlights coming a bend closer);
//   - ends on a failure (`eyepiece.failure` {title, body}) instead of a bare "out" line;
//   - offers a RETRY (`retry: {label}`) that resets only this lock's attempts. A page reload wipes the whole
//     run, graded answers included (nothing persists), so "reload to try again" would send a student back
//     through every graded puzzle; the retry keeps the analysis and replays only the escape's last step.
//
// Schema additions on a `lock` (all optional; a lock without them behaves exactly as before, apart from the
// lockout now holding across openings, which only a lock with maxAttempts can reach):
//   eyepiece: { views: { <code>: view }, emptySky?: view, misses?: [text per wrong try], failure?: {title, body},
//               stateKey?: <gameState key>, solved?: view }
//   retry:    { label? }   (default label "Try again")
// A `view` is TEXT (a string, rendered exactly as before) or a PICTURE `{image, text?}`: `image` a path relative to
// play.html, drawn as an <img> above `text`, its optional caption (alt = the caption, else "eyepiece view"), sized to
// fit the modal on a 320 px phone. `eyepiece.solved` (opt-in) shows on the RIGHT code, above `feedback.correct`,
// before the escape proceeds (a `deferCard` lock keeps the popup open, so it stays up until the player closes it).
// validate_assets.py FAILs an eyepiece image missing on disk.
// `eyepiece.stateKey` makes the misses visible in the world: each wrong try sets gameState[stateKey] to the attempt
// count including that try, and the retry sets it back to 0, so a `mapview` keyed on it (images[0..maxAttempts]) and
// any panorama variant whose `when` is {eq:[stateKey, n]} follow the pointings (observatory's headlights).
// Import-free, so tests/lock_console.test.mjs can pin it.

export const normalizeCode = s => (s || "").toUpperCase().replace(/[^A-Z0-9]/g, "");

// True once a lock with an attempt limit has used every attempt.
export function isLockedOut(h, attempts) {
  const maxA = (h && h.maxAttempts) || 0;
  return !!maxA && attempts >= maxA;
}

// What the player sees after a WRONG code, given the attempt count INCLUDING this try.
// Returns { kind: "no" | "out", text, failure: {title, body} | null }.
export function wrongResult(h, code, attempts) {
  const fbk = (h && h.feedback) || {};
  const eye = (h && h.eyepiece) || null;
  const out = isLockedOut(h, attempts);
  if (!eye) {
    return out ? { kind: "out", text: fbk.out || "The keypad goes dark.", failure: null }
               : { kind: "no", text: fbk.wrong || "Nothing happens.", failure: null };
  }
  const views = eye.views || {};
  let view = null;
  const want = normalizeCode(code);
  for (const k of Object.keys(views)) if (normalizeCode(k) === want) { view = viewOf(views[k]); break; }
  if (!view) view = viewOf(eye.emptySky) || { text: fbk.wrong || "Nothing happens.", image: null };
  // A picture view adds `image` + `alt`; a text view returns exactly the old {kind, text, failure}.
  const pic = r => (view.image ? Object.assign(r, { image: view.image, alt: view.text || GENERIC_ALT }) : r);
  if (out) {
    const failure = eye.failure && (eye.failure.title || eye.failure.body) ? eye.failure : null;
    return pic({ kind: "out", text: failure ? view.text : [view.text, fbk.out].filter(Boolean).join(" "), failure });
  }
  const misses = Array.isArray(eye.misses) ? eye.misses : [];
  const miss = misses[Math.min(attempts, misses.length) - 1] || "";
  return pic({ kind: "no", text: [view.text, miss].filter(Boolean).join(" "), failure: null });
}

const GENERIC_ALT = "eyepiece view";

// A view as {text, image}: a string is text only; `{image, text?}` is a picture with an optional caption. Empty or
// malformed (no text and no image) is null, so the caller falls back exactly as it did for an empty string.
export function viewOf(v) {
  if (typeof v === "string") return v ? { text: v, image: null } : null;
  if (!v || typeof v !== "object") return null;
  const image = typeof v.image === "string" && v.image ? v.image : null;
  const text = typeof v.text === "string" ? v.text : "";
  return image || text ? { text, image } : null;
}

const escAttr = s => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// The picture: the card's width at most (a 320 px phone included) and never more than half the screen tall.
function imgHtml(src, alt) {
  alt = String(alt).replace(/<[^>]*>/g, "").trim() || GENERIC_ALT;   // a caption may carry markup; alt is plain text
  return `<img class="eyepiece-view" src="${escAttr(src)}" alt="${escAttr(alt)}" draggable="false" ` +
    `style="display:block;max-width:100%;width:auto;height:auto;max-height:min(50vh,360px);margin:0 auto 8px;` +
    `border-radius:8px;border:1px solid rgba(201,163,90,.45)">`;
}

// The feedback markup for a wrongResult/lockedOutResult: a text view's text alone (unchanged, authored HTML), or
// the picture above its text.
export function resultHtml(res) {
  if (!res) return "";
  if (!res.image) return res.text || "";
  return imgHtml(res.image, res.alt || GENERIC_ALT) + (res.text ? `<div>${res.text}</div>` : "");
}

// The success view (`eyepiece.solved`) as markup to sit above `feedback.correct`; "" when the lock has none.
export function solvedHtml(h) {
  const v = viewOf(h && h.eyepiece && h.eyepiece.solved);
  if (!v) return "";
  return (v.image ? imgHtml(v.image, v.text || GENERIC_ALT) : "") + (v.text ? `<div>${v.text}</div>` : "");
}

// Every eyepiece image a lock names (views, emptySky, solved), for asset checks.
export function eyepieceImages(h) {
  const eye = (h && h.eyepiece) || {};
  return Object.values(eye.views || {}).concat([eye.emptySky, eye.solved])
    .map(viewOf).filter(v => v && v.image).map(v => v.image);
}

// The retry button's label, or null when the lock offers no retry.
export function retryLabel(h) {
  if (!h || !h.retry) return null;
  return (typeof h.retry === "object" && h.retry.label) || "Try again";
}

// The world-state key a lock's misses drive (`eyepiece.stateKey`), or null when it has none.
export function stateKeyOf(h) {
  const k = h && h.eyepiece && h.eyepiece.stateKey;
  return (typeof k === "string" && k) ? k : null;
}

// The value gameState[stateKeyOf(h)] takes after a wrong try (attempts = the count INCLUDING it; 0 on a retry),
// never above maxAttempts; null when the lock has no stateKey (the caller then writes nothing).
export function nextStateValue(h, attempts) {
  if (!stateKeyOf(h)) return null;
  const n = Math.max(0, Math.floor(Number(attempts) || 0));
  const maxA = (h && h.maxAttempts) || 0;
  return maxA ? Math.min(n, maxA) : n;
}

// What a locked-out lock shows when it is opened again: the failure if authored, else the "out" line.
export function lockedOutResult(h) {
  const eye = (h && h.eyepiece) || {};
  const failure = eye.failure && (eye.failure.title || eye.failure.body) ? eye.failure : null;
  return { kind: "out", text: failure ? "" : (((h && h.feedback) || {}).out || "The keypad goes dark."), failure };
}
