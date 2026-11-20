// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `sigmoid_board` and `scoreboard` kinds).
// classification_math.js: the pure maths behind the classification chapter's two teaching instruments
// (sigmoid_board.js, day one; scoreboard.js, day two). No DOM; node-testable (tests/classification_math.test.mjs,
// whose numbers are pinned to R's lm() and glm(family = binomial)).
//
// TOY DATA ONLY. Every number here is invented; the boards deliberately do not say so on screen (no text that does not teach). Never point these instruments at a
// graded dataset (crater_monitoring, galaxy_plates) or their practice sisters: an S-curve over real rows would show
// the response-against-predictor relationship the graded rooms test. The toy column names deliberately share
// nothing with those datasets.

// ---------- day one: forty made-up mornings at the island's landing ----------
// Did the supply boat turn back (yes/no) against the swell height that morning (m)? Days 1-30 are training,
// days 31-40 are held back.
export const LANDING = {
  predictor: "swell_m", response: "turned_back", units: "m", label: "Swell height (m)",
  training: [
    [0.4, 0], [0.6, 0], [0.8, 0], [0.9, 0], [1.1, 0], [1.2, 0], [1.4, 0], [1.5, 1], [1.6, 0], [1.8, 0],
    [1.9, 0], [2.0, 1], [2.1, 0], [2.3, 1], [2.4, 0], [2.5, 1], [2.6, 0], [2.7, 1], [2.9, 1], [3.0, 0],
    [3.1, 1], [3.3, 1], [3.4, 1], [3.6, 0], [3.7, 1], [3.9, 1], [4.1, 1], [4.4, 1], [4.6, 1], [5.0, 1],
  ].map(([x, y], i) => ({ day: i + 1, x, y })),
  // held back: swell and what actually happened, revealed only on the board's "setting cases aside" tab
  heldBack: [[0.7, 0], [1.3, 0], [1.7, 0], [2.2, 0], [2.45, 0], [2.65, 1], [2.8, 1], [3.2, 0], [3.8, 1], [4.8, 1]]
    .map(([x, y], i) => ({ day: 31 + i, x, y })),
  xView: [0, 6],
};

// ---------- day two: made-up nights at the plate archive's telescope ----------
// Was the night clear enough to photograph (yes/no), from two readings in very different units: the barometer
// (hPa, spread over tens of units) and the humidity as a fraction (0 to 1, spread over a few tenths). Invented with
// a fixed seed (see makeNights); clear nights come with high pressure and dry air.
export const NIGHTS_SPEC = { n: 48, seed: 20261125 };
export const NIGHT_PREDICTORS = [
  { name: "pressure_hpa", label: "Barometer", units: "hPa" },
  { name: "humidity_fraction", label: "Humidity", units: "fraction, 0 to 1" },
];

export function rng(seed) {
  let s = seed >>> 0 || 1;
  const r = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  r.normal = (m = 0, sd = 1) => { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r(); return m + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  return r;
}
const round = (v, d) => Math.round(v * 10 ** d) / 10 ** d;

// Each night: pressure ~ N(1012, 9) hPa, humidity ~ N(0.62, 0.13) clipped to 0.15..0.98; clear with probability
// logistic(0.2 * (pressure - 1012) - 5 * (humidity - 0.62)). Rounded as a logbook would print them. Built so the RAW
// coefficients rank humidity far above pressure (a fraction moves a few tenths, so one whole unit of it is huge)
// while the SCALED ones put pressure first: the chapter's density lesson, in the board's own units.
export function makeNights({ n, seed } = NIGHTS_SPEC) {
  const R = rng(seed), out = [];
  for (let i = 0; i < n; i++) {
    const p = round(R.normal(1012, 9), 0);
    const h = round(Math.min(0.98, Math.max(0.15, R.normal(0.62, 0.13))), 2);
    const lin = 0.2 * (p - 1012) - 5 * (h - 0.62);
    out.push({ night: i + 1, x: [p, h], y: R() < 1 / (1 + Math.exp(-lin)) ? 1 : 0 });
  }
  return out;
}

// ---------- the models ----------
export const logistic = (z) => 1 / (1 + Math.exp(-z));

// A straight line through 0/1 codes (lm(y ~ x)): {intercept, slope}.
export function olsLine(xs, ys) {
  const n = xs.length, mx = xs.reduce((a, v) => a + v, 0) / n, my = ys.reduce((a, v) => a + v, 0) / n;
  let sxy = 0, sxx = 0;
  for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; }
  const slope = sxy / sxx;
  return { intercept: my - slope * mx, slope };
}

// Logistic regression by Newton-Raphson (what glm(family = binomial) does): rows X (no intercept column), y in {0,1}.
// Returns [b0, b1, ..., bk]. Throws on complete separation (the toy data never have it).
export function fitLogistic(X, y, { iters = 50, tol = 1e-12 } = {}) {
  const k = X[0].length + 1, n = X.length;
  const row = (i) => [1, ...X[i]];
  let b = new Array(k).fill(0);
  for (let it = 0; it < iters; it++) {
    const g = new Array(k).fill(0), H = Array.from({ length: k }, () => new Array(k).fill(0));
    for (let i = 0; i < n; i++) {
      const r = row(i), p = logistic(r.reduce((a, v, j) => a + v * b[j], 0)), w = p * (1 - p);
      for (let a = 0; a < k; a++) { g[a] += (y[i] - p) * r[a]; for (let c = 0; c < k; c++) H[a][c] += w * r[a] * r[c]; }
    }
    const step = solve(H, g);
    b = b.map((v, j) => v + step[j]);
    if (step.some((v) => !Number.isFinite(v))) throw new Error("fitLogistic: did not converge");
    if (Math.max(...step.map(Math.abs)) < tol) break;
  }
  return b;
}
function solve(A, rhs) {             // Gaussian elimination with partial pivoting (k is 2 or 3)
  const k = rhs.length, M = A.map((r, i) => [...r, rhs[i]]);
  for (let c = 0; c < k; c++) {
    let p = c; for (let r = c + 1; r < k; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < k; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let j = c; j <= k; j++) M[r][j] -= f * M[c][j]; }
  }
  return M.map((r, i) => r[k] / r[i]);
}

export function logLik(b, X, y) {
  let s = 0;
  for (let i = 0; i < X.length; i++) {
    const p = logistic(b[0] + X[i].reduce((a, v, j) => a + v * b[j + 1], 0));
    s += y[i] ? Math.log(Math.max(p, 1e-300)) : Math.log(Math.max(1 - p, 1e-300));
  }
  return s;
}

// The S-curve in the board's own terms: its MIDDLE (where the probability is 0.5) and STEEPNESS (the slope b1).
export const curveFromCoef = ([b0, b1]) => ({ middle: -b0 / b1, steepness: b1 });
export const coefFromCurve = ({ middle, steepness }) => [-middle * steepness, steepness];
export const probAt = (curve, x) => logistic(curve.steepness * (x - curve.middle));

// How close a hand-set curve is to the best fit, 0..1 (1 at the best): the per-case likelihood ratio,
// exp((logLik(curve) - logLik(best)) / n). Shown as a bar, never as a number.
export function fitScore(curve, best, X, y) {
  const d = logLik(coefFromCurve(curve), X, y) - logLik(coefFromCurve(best), X, y);
  return Math.max(0, Math.min(1, Math.exp(d / X.length)));
}

// The connect-the-dots curve for "setting cases aside": it passes through every training morning (so it gets all of
// them right) and swings to the next morning's answer within the first half of each gap. It memorises the noise; on
// the held-back mornings it does worse than the S-curve. `pts` must be sorted by x.
export function connectDotsAt(pts, x) {
  if (x <= pts[0].x) return pts[0].y;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1];
    if (x <= b.x) {
      const t = Math.max(0, Math.min(1, ((x - a.x) / (b.x - a.x) - 0.1) / 0.35));
      return a.y + (b.y - a.y) * t * t * (3 - 2 * t);
    }
  }
  return pts[pts.length - 1].y;
}

// A probability becomes a call through the cut-off: yes at the cut-off or above (predictWithModel()'s rule at 0.5).
export const callAt = (p, cutoff = 0.5) => (p >= cutoff ? "yes" : "no");

// ---------- scaling (scale_variance = TRUE) ----------
export const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
export const sd = (a) => { const m = mean(a); return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / (a.length - 1)); };
// Scaled coefficients: fit on (x - mean) / sd. For logistic regression that is exactly raw slope x sd, and every
// case keeps the same probability (the board's test checks both).
export function scaledCoefs(X, y) {
  const cols = X[0].map((_, j) => X.map((r) => r[j]));
  const ms = cols.map(mean), ss = cols.map(sd);
  const Z = X.map((r) => r.map((v, j) => (v - ms[j]) / ss[j]));
  return { coefs: fitLogistic(Z, y), means: ms, sds: ss };
}

// ---------- judging: the held-back tally ----------
// 200 made-up held-back nights. Each yes-night and each no-night gets a model probability from fixed quantiles, so
// the model catches about 71% of the yes-cases and calls about 90% of the no-cases no, whatever the mix. The slider
// sets how many of the 200 are yes; the tally counts at the 0.5 cut-off. Always-no's accuracy beats the model's once
// yes falls below about one case in eight.
export const TALLY = { n: 200, yesMu: 0.9, noMu: -2.1, spread: 1.6, seed: 31 };
function normQuantile(p) {             // Acklam's rational approximation (|error| < 1.2e-9)
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const q0 = Math.min(p, 1 - p);
  if (q0 < 0.02425) {
    const q = Math.sqrt(-2 * Math.log(q0));
    const x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    return p < 0.5 ? x : -x;
  }
  const q = p - 0.5, r = q * q;
  return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}
// The probabilities for k cases of one truth, spread evenly over its distribution, in a fixed shuffled order.
function spreadProbs(k, mu, s, seed) {
  const ps = Array.from({ length: k }, (_, i) => logistic(mu + s * normQuantile((i + 0.5) / k)));
  const R = rng(seed);
  for (let i = ps.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [ps[i], ps[j]] = [ps[j], ps[i]]; }
  return ps;
}
// The pool at a given share of yes (0..1): cases in a fixed shuffled grid order, each {truth, p, call}.
export function tallyPool(yesShare, T = TALLY) {
  const nYes = Math.max(0, Math.min(T.n, Math.round(T.n * yesShare)));
  const yes = spreadProbs(nYes, T.yesMu, T.spread, T.seed).map((p) => ({ truth: "yes", p }));
  const no = spreadProbs(T.n - nYes, T.noMu, T.spread, T.seed + 1).map((p) => ({ truth: "no", p }));
  const all = [...yes, ...no];
  const R = rng(T.seed + 7);
  for (let i = all.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [all[i], all[j]] = [all[j], all[i]]; }
  return all.map((c) => ({ ...c, call: callAt(c.p) }));
}
// Accuracy, caught and missed for a list of {truth, call}; the book's three numbers.
export function judge(cases) {
  const right = cases.filter((c) => c.call === c.truth).length;
  const yes = cases.filter((c) => c.truth === "yes");
  const caught = yes.filter((c) => c.call === "yes").length;
  return { n: cases.length, right, accuracy: cases.length ? right / cases.length : 0, yes: yes.length, caught, missed: yes.length - caught };
}
export const alwaysNo = (cases) => cases.map((c) => ({ ...c, call: "no" }));
