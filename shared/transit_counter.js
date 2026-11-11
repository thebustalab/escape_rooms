// The brass date plaque over a flat door transit (`transit.counter`, dunes time-skip, 2026-11-11): pure date maths,
// import-free so tests/transit_counter.test.mjs can load it in Node.
//
//   counter: { from: "YYYY-MM-DD", to: "YYYY-MM-DD", steps?: [s, ...], toFromLock?: "<date lock hotspot id>" }
//
// Without `steps` the date runs linearly from `from` to `to` over the clip. With `steps` (absolute clip times, e.g.
// each night's darkest frame) it shows `from` until the first step and from + round(k/N × (to − from)) days once k of
// the N steps have passed, so the last step lands on `to`. Unsorted or non-numeric steps fall back to linear.

export const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
  "October", "November", "December"];

// "YYYY-MM-DD" → UTC ms, or NaN for anything else (including 31 November).
export function parseYMD(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(typeof s === "string" ? s : "");
  if (!m) return NaN;
  const [y, mo, d] = [+m[1], +m[2], +m[3]];
  const t = Date.UTC(y, mo - 1, d);
  const back = new Date(t);
  return back.getUTCFullYear() === y && back.getUTCMonth() === mo - 1 && back.getUTCDate() === d ? t : NaN;
}

// A usable steps list, or null (→ linear).
export function validSteps(steps) {
  if (!Array.isArray(steps) || !steps.length) return null;
  for (let i = 0; i < steps.length; i++) {
    if (typeof steps[i] !== "number" || !Number.isFinite(steps[i])) return null;
    if (i && steps[i] < steps[i - 1]) return null;
  }
  return steps;
}

// Fraction of the way from `from` to `to` at clip time `t`. Linear mode runs from `start` to `end`.
export function counterFraction(t, { steps, start = 0, end = 1 } = {}) {
  const S = validSteps(steps);
  if (S) return S.filter(s => t >= s).length / S.length;
  const span = Math.max(0.01, end - start);
  return Math.min(1, Math.max(0, (t - start) / span));
}

export function counterDay(from, to, u) {
  const a = parseYMD(from), b = parseYMD(to);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return "";
  const days = Math.round((b - a) / 864e5), k = Math.round(Math.min(1, Math.max(0, u)) * days);
  const d = new Date(a + k * 864e5);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

// The end date: the date posted on `toFromLock` ({day, month, year?}; year falls back to the authored `to`'s), else `to`.
export function counterTo(counter, posted) {
  const to = counter && counter.to;
  if (!counter || !counter.toFromLock || !posted) return to;
  const year = Number.isInteger(posted.year) ? posted.year : +String(to || "").slice(0, 4);
  const pad = n => String(n).padStart(2, "0");
  const ymd = `${String(year).padStart(4, "0")}-${pad(posted.month)}-${pad(posted.day)}`;
  return Number.isFinite(parseYMD(ymd)) ? ymd : to;
}

// The plaque's text at clip time `t`.
export function counterLabel(counter, t, { start = 0, end = 1, posted = null } = {}) {
  return counterDay(counter.from, counterTo(counter, posted), counterFraction(t, { steps: counter.steps, start, end }));
}
