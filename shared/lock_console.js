// lock_console.js — the pure half of a limited-attempt keypad lock (observatory's pointing console, 2026-11-21).
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
//   eyepiece: { views: { <code>: text }, emptySky?: text, misses?: [text per wrong try], failure?: {title, body},
//               stateKey?: <gameState key> }
//   retry:    { label? }   (default label "Try again")
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
  let view = "";
  const want = normalizeCode(code);
  for (const k of Object.keys(views)) if (normalizeCode(k) === want) { view = views[k]; break; }
  if (!view) view = eye.emptySky || fbk.wrong || "Nothing happens.";
  if (out) {
    const failure = eye.failure && (eye.failure.title || eye.failure.body) ? eye.failure : null;
    return { kind: "out", text: failure ? view : [view, fbk.out].filter(Boolean).join(" "), failure };
  }
  const misses = Array.isArray(eye.misses) ? eye.misses : [];
  const miss = misses[Math.min(attempts, misses.length) - 1] || "";
  return { kind: "no", text: [view, miss].filter(Boolean).join(" "), failure: null };
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
