// Ghost lines — the pure half (no DOM) of the ghost-line board (shared/ghost_lines.js, kind "ghost_lines",
// regression/pits). A hidden POPULATION (a fixed, seeded set of claims: x uniform over the data range, y = a
// true line + normal noise), random SAMPLES drawn from it without replacement, and the sprung rod of the
// drawdown board (shared/drawdown_physics.js) let go on each sample until it stops. Its rest state is the
// sample's least-squares line (drawdown_physics.js proves why); `settle` runs the real physics and never
// consults ols(), so tests/ghost_lines.test.mjs can check the two agree.
import { RodSim, ols } from "./drawdown_physics.js?v=168";

export { ols };

export const POP_DEFAULTS = Object.freeze({
  seed: 2026,          // fixed per page; "New population" moves it on
  size: 400,           // claims in the hidden population
  xMin: 2, xMax: 12,   // the data range: where the population's x values lie
  intercept: 10, slope: 3, sd: 6,
});

// mulberry32: small, fast, seedable; good enough for teaching draws, identical in every browser and in node.
export function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function gauss(r) {
  let u = 0;
  while (u === 0) u = r();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r());
}

// The hidden population. Its "true line" is the population's own least-squares line (so a sample's line is
// an unbiased guess at exactly the line drawn as "true"); it sits very close to the generating line.
export function makePopulation(o = {}) {
  const p = { ...POP_DEFAULTS, ...o };
  const r = rng(p.seed);
  const xs = [], ys = [];
  for (let i = 0; i < p.size; i++) {
    const x = p.xMin + (p.xMax - p.xMin) * r();
    xs.push(x); ys.push(p.intercept + p.slope * x + p.sd * gauss(r));
  }
  const f = ols(xs, ys);
  return { ...p, xs, ys, trueLine: { slope: f.slope, intercept: f.intercept } };
}

// n distinct claims (partial Fisher-Yates), as indices into the population.
export function sampleIdx(pop, n, r) {
  const N = pop.xs.length, k = Math.max(2, Math.min(n, N));
  const idx = Array.from({ length: N }, (_, i) => i);
  for (let i = 0; i < k; i++) {
    const j = i + Math.floor(r() * (N - i));
    [idx[i], idx[j]] = [idx[j], idx[i]];
  }
  return idx.slice(0, k);
}

// A rod for one sample. Centred on the sample's mean x with mass and inertia sized from the sample itself, so
// every draw swings with the drawdown board's reference feel (omega 7 rad/s, damping ratio 0.45) in both
// height and tilt, whatever n is. (`length` here sizes the inertia only; the drawn rod spans the board.)
export function makeRod(xs) {
  const n = xs.length, xc = xs.reduce((a, x) => a + x, 0) / n;
  const s = xs.reduce((a, x) => a + (x - xc) ** 2, 0);
  const length = Math.max(1e-6, Math.sqrt((12 * s) / n));
  const sim = new RodSim({ xc, refXs: xs, length });
  sim.setPegs(xs.map((x) => ({ x, y: 0 })));
  return sim;
}

export const lineOf = (sim) => ({ slope: sim.s, intercept: sim.h - sim.s * sim.xc });

// Put a rod on the line {slope, intercept} (or park it at height `park`) at rest.
export function placeRod(sim, from) {
  sim.reset(from.intercept + from.slope * sim.xc, from.slope);
}

// Run the physics until the rod has stopped (no animation). Returns the line it came to rest on.
export function settle(xs, ys, from, maxT = 60) {
  const sim = makeRod(xs);
  sim.setPegs(xs.map((x, i) => ({ x, y: ys[i] })));
  placeRod(sim, from);
  while (!sim.settled && sim.time < maxT) sim.substep();
  return { ...lineOf(sim), settled: sim.settled, time: sim.time };
}

export function sumSquares(xs, ys, line) {
  let ss = 0;
  for (let i = 0; i < xs.length; i++) ss += (ys[i] - (line.intercept + line.slope * xs[i])) ** 2;
  return ss;
}

// What a set of lines predicts at x: each line's value, their mean, SD (n - 1) and range.
export function spreadAt(lines, x) {
  const preds = lines.map((l) => l.intercept + l.slope * x);
  const n = preds.length;
  if (!n) return { n, preds, mean: NaN, sd: NaN, min: NaN, max: NaN };
  const mean = preds.reduce((a, v) => a + v, 0) / n;
  const sd = n > 1 ? Math.sqrt(preds.reduce((a, v) => a + (v - mean) ** 2, 0) / (n - 1)) : 0;
  return { n, preds, mean, sd, min: Math.min(...preds), max: Math.max(...preds) };
}

// ---------- tab 2: the flat line (the mean-only model) and r-squared, the book's way ----------
export function totalSquares(ys) {
  const m = ys.reduce((a, v) => a + v, 0) / ys.length;
  return ys.reduce((a, v) => a + (v - m) ** 2, 0);
}
// 1 - residual sum of squares / total sum of squares, for any line (a dragged rod scores lower)
export function rSquared(xs, ys, line) {
  const tss = totalSquares(ys);
  return tss > 0 ? 1 - sumSquares(xs, ys, line) / tss : NaN;
}

// ---------- tab 4: which measurement matters most ----------
// The board's OWN test sacks (not the deal's pit_sacks, so it never shows a Level 3 key). Five independent
// measurements, built so the chapter's warning is plain: tide height (metres, barely varies) has the biggest raw
// coefficient but is fourth once scaled (sand first, ranked ignoring the sign); seaweed has no effect at all, so
// its p value is large. `effect` is per population SD.
export const MULTI_DEFAULTS = Object.freeze({
  seed: 1109, size: 80, intercept: 30, sd: 5,
  preds: Object.freeze([
    Object.freeze({ name: "Tide height", unit: "m", mean: 1.2, sd: 0.15, effect: 2.0 }),
    Object.freeze({ name: "Pit width", unit: "m", mean: 4, sd: 1.0, effect: 4.0 }),
    Object.freeze({ name: "Sand", unit: "%", mean: 40, sd: 8, effect: -7.0 }),
    Object.freeze({ name: "Garnets", unit: "per 100 g", mean: 60, sd: 20, effect: 5.5 }),
    Object.freeze({ name: "Seaweed", unit: "%", mean: 12, sd: 4, effect: 0 }),        // no effect: a large p value
  ]),
});

export function makeMultiSet(o = {}) {
  const p = { ...MULTI_DEFAULTS, ...o };
  const r = rng(p.seed);
  const cols = p.preds.map(() => []), y = [];
  for (let i = 0; i < p.size; i++) {
    let v = p.intercept;
    p.preds.forEach((q, j) => { const x = q.mean + q.sd * gauss(r); cols[j].push(x); v += (q.effect * (x - q.mean)) / q.sd; });
    y.push(v + p.sd * gauss(r));
  }
  return { preds: p.preds.map((q) => ({ ...q })), cols, y };
}

// R's scale(): mean 0, SD 1 with the n - 1 SD
export function scaleCol(v) {
  const n = v.length, m = v.reduce((a, x) => a + x, 0) / n;
  const s = Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / (n - 1));
  return v.map((x) => (x - m) / s);
}
export function colSd(v) {
  const n = v.length, m = v.reduce((a, x) => a + x, 0) / n;
  return Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / (n - 1));
}

// ---------- Student's t p values (two-sided), as summary(lm()) reports them ----------
function lgamma(x) {                       // Lanczos, good to ~1e-14 for x > 0
  const g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
  x -= 1;
  let a = c[0];
  const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function betacf(a, b, x) {                 // continued fraction for the incomplete beta (Numerical Recipes)
  const FPMIN = 1e-300;
  let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d; let h = d;
  for (let m = 1; m <= 300; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d; h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d; const del = d * c; h *= del;
    if (Math.abs(del - 1) < 1e-15) break;
  }
  return h;
}
export function incBeta(x, a, b) {          // regularised I_x(a, b)
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? (bt * betacf(a, b, x)) / a : 1 - (bt * betacf(b, a, 1 - x)) / b;
}
export function tPValue(t, df) { return incBeta(df / (df + t * t), df / 2, 0.5); }

// Least squares with several predictors (normal equations; Gauss-Jordan with partial pivoting on [X'X | I]),
// as lm() and summary(lm()) report it: { intercept, coefs, se, p (each [intercept, ...coefs]), r2, df }.
export function olsMulti(cols, y) {
  const n = y.length, k = cols.length + 1;
  const row = (i) => [1, ...cols.map((c) => c[i])];
  const A = Array.from({ length: k }, (_, a) => { const r = new Array(2 * k).fill(0); r[k + a] = 1; return r; });
  const Xty = new Array(k).fill(0);
  for (let i = 0; i < n; i++) {
    const x = row(i);
    for (let a = 0; a < k; a++) { for (let b = 0; b < k; b++) A[a][b] += x[a] * x[b]; Xty[a] += x[a] * y[i]; }
  }
  for (let c = 0; c < k; c++) {
    let piv = c;
    for (let r = c + 1; r < k; r++) if (Math.abs(A[r][c]) > Math.abs(A[piv][c])) piv = r;
    [A[c], A[piv]] = [A[piv], A[c]];
    const d = A[c][c];
    for (let j = 0; j < 2 * k; j++) A[c][j] /= d;
    for (let r = 0; r < k; r++) {
      if (r === c) continue;
      const f = A[r][c];
      if (f) for (let j = 0; j < 2 * k; j++) A[r][j] -= f * A[c][j];
    }
  }
  const inv = A.map((r) => r.slice(k));
  const beta = inv.map((r) => r.reduce((a, v, j) => a + v * Xty[j], 0));
  let rss = 0;
  const fitted = new Array(n);
  for (let i = 0; i < n; i++) { const x = row(i); fitted[i] = x.reduce((a, v, j) => a + v * beta[j], 0); rss += (y[i] - fitted[i]) ** 2; }
  const df = n - k, s2 = rss / df;
  const se = inv.map((r, j) => Math.sqrt(s2 * r[j]));
  const p = beta.map((b, j) => tPValue(b / se[j], df));
  return { intercept: beta[0], coefs: beta.slice(1), se, p, r2: 1 - rss / totalSquares(y), df, fitted };
}

// Both fits the tab shows, on the measurements switched on (`on`: booleans, default all): on the measurements as
// dug, and on the scaled measurements. Per-measurement arrays are full length, null where a measurement is off.
export function multiFits(set, on = set.preds.map(() => true)) {
  const idx = on.map((v, i) => (v ? i : -1)).filter((i) => i >= 0);
  const spread = (f) => {
    const full = (arr) => { const o = set.preds.map(() => null); idx.forEach((i, j) => { o[i] = arr[j]; }); return o; };
    return { ...f, coefs: full(f.coefs), coefSe: full(f.se.slice(1)), coefP: full(f.p.slice(1)) };
  };
  const raw = spread(olsMulti(idx.map((i) => set.cols[i]), set.y));
  const scaled = spread(olsMulti(idx.map((i) => scaleCol(set.cols[i])), set.y));
  return { raw, scaled, on: on.slice() };
}

export function slopeSd(lines) {
  const n = lines.length;
  if (n < 2) return NaN;
  const m = lines.reduce((a, l) => a + l.slope, 0) / n;
  return Math.sqrt(lines.reduce((a, l) => a + (l.slope - m) ** 2, 0) / (n - 1));
}
