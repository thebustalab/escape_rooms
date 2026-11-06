// Ghost lines — the pure half (no DOM) of the ghost-line board (shared/ghost_lines.js, kind "ghost_lines",
// regression/pits). A hidden POPULATION (a fixed, seeded set of claims: x uniform over the data range, y = a
// true line + normal noise), random SAMPLES drawn from it without replacement, and the sprung rod of the
// drawdown board (shared/drawdown_physics.js) let go on each sample until it stops. Its rest state is the
// sample's least-squares line (drawdown_physics.js proves why); `settle` runs the real physics and never
// consults ols(), so tests/ghost_lines.test.mjs can check the two agree.
import { RodSim, ols } from "./drawdown_physics.js?v=155";

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

export function slopeSd(lines) {
  const n = lines.length;
  if (n < 2) return NaN;
  const m = lines.reduce((a, l) => a + l.slope, 0) / n;
  return Math.sqrt(lines.reduce((a, l) => a + (l.slope - m) ** 2, 0) / (n - 1));
}
