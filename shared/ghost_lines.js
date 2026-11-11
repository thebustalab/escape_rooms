// The Ghost-Line Board — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"ghost_lines"`), built
// 2026-11-05 for regression/pits (the live regression scenario's hub) on the drawdown board's physics; put on
// four TABS with a Lesson panel on 2026-11-07 (Lucas: like the harbour fish board, aligned with the book's
// chapter 12 sections and the scenario's three levels).
//
//   1 The line           (single linear regression; Level 1 slope): DRAW drops n sacks, chosen at random from a
//                        hidden population (shared/ghost_lines_math.js), as brass pegs; the drawdown board's sprung
//                        rod swings to rest on the sample's least-squares line and stays as a faint ghost, so draws
//                        build a fan that narrows as n grows. Springs = residuals, squares + their sum on demand,
//                        the rod can be dragged off and swings back.
//   2 Against the flat line (single linear regression, r-squared; Level 1 r-squared): the same sample, its line's
//                        squares beside the flat line's (the mean), r-squared = 1 - residual / total; "Wider
//                        scatter" re-reads the same sacks with four times the noise. Draws here leave no ghost.
//   3 Predict a sack     (predicting with a model; Level 2): a draggable new-sack marker, past the data too; every
//                        ghost's prediction ticked, mean ± 2 SD bracket and band (wide past the data).
//   4 Which matters most (multiple linear regression, which predictors matter most; Level 3): the board's OWN
//                        five-measurement test sacks (never the deal's data); each measurement its own plot with its
//                        line (others held fixed), in or out of the model by button or tap; measured vs predicted;
//                        the metrics table (value, std_err, p_value); "Scale the measurements" re-ranks.
// It is READ, never graded: it never logs, solves or gates anything and holds no answer.
//
// Drawn on a logical canvas (geometry.imageW x imageH) letterboxed into its box. `art.board`, when given, is
// the backdrop and `geometry.plot` places the plotting face on it; without it the night board is code-drawn.
// `art.rod`, `art.spring`, `art.peg` (sprites) are optional; each falls back to code drawing.
//
//   const g = mountGhostLines(hostEl, { geometry, params, art?, pegs?, onPegs?(state), sound?, debug? });
//   geometry: { imageW, imageH, plot:{x0,y0,x1,y1} }                     (calibration of the backdrop)
//   params:   { seed, size, xMin, xMax, intercept, slope, sd,           (the hidden population)
//               xView:[a,b], yView:[a,b], xLabel, yLabel, title, n, nMax, claimX }   (the board)
//   g.setAct(1..4); g.act(); g.setWide(on); g.wide(); g.setScaled(on); g.scaled(); g.rSquared(); g.multi();
//   g.draw({instant}); g.drawMany(k, {instant}); g.clear(); g.reroll(seed?); g.setN(n); g.n();
//   g.ghosts(); g.current(); g.olsCurrent(); g.isSettled(); g.setClaim(x); g.claim(); g.spreadAt(x);
//   g.setToggle(name, on); g.toggles(); g.population(); g.ready (Promise); g.destroy();
//   canvas.ghostLines exposes the same API for tests.
import {
  POP_DEFAULTS, makePopulation, sampleIdx, rng, makeRod, placeRod, lineOf, ols, spreadAt, slopeSd, sumSquares,
  totalSquares, makeMultiSet, multiFits, colSd, scaleCol,
} from "./ghost_lines_math.js?v=165";

const VIEW_DEFAULTS = {
  xView: [0, 20], yView: [0, 90], xLabel: "Gravel depth (ft)", yLabel: "Carats per 100 t",
  title: "The ghost-line board", n: 5, nMax: 40, claimX: 17,
};
const GEOM_DEFAULTS = { imageW: 1400, imageH: 830, plot: { x0: 130, y0: 36, x1: 1370, y1: 712 } };
// [key, default]. `claim` is on by itself in tab 3 (kept as a toggle so saved state and tests still reach it).
const TOGGLES = [
  ["resid", true], ["squares", false], ["truth", false], ["pop", false], ["claim", false],
  ["linesq", true], ["flatsq", true],
];
// Each tab: its name, the toggles it shows (key, label), and its lesson: one short takeaway in the book's
// wording plus the chapter 12 section it belongs to.
const ACTS = {
  1: { name: "The line", tog: [["resid", "Residuals"], ["squares", "Squares"], ["truth", "True line"], ["pop", "Population"]],
       lesson: "The model's line is the one with the smallest sum of squared residuals, the distances between each point and the line. Its slope is the change the model expects in the response for each one-unit increase in the predictor. A small sample can give a very different line; more data settles it.",
       where: "single linear regression" },
  2: { name: "Against the flat line", tog: [["linesq", "Line's squares"], ["flatsq", "Flat line's squares"]],
       lesson: "The residual sum of squares is the noise: the spread the model leaves unexplained. The flat line at the mean gives the total sum of squares. R squared is 1 minus residual over total: the share of the variation the predictor explains, or how much better the line describes the data than the flat line.",
       where: "single linear regression (R squared)" },
  3: { name: "Predict a sack", tog: [["truth", "True line"]],
       lesson: "A fitted model can predict the response for samples whose response was never measured. A prediction is only as good as the model behind it, and past the range of the data the lines disagree more.",
       where: "predicting with a model" },
  4: { name: "Which matters most", tog: [],
       lesson: "Each predictor's p value tests whether its coefficient is different from zero: a small one marks a predictor likely to matter after accounting for the rest. Raw coefficients cannot be compared, because each is in its own predictor's units; scale the predictors to a mean of zero and a standard deviation of one, then rank by size, ignoring the sign. Scaling changes the units of the coefficients, not the fit.",
       where: "multiple linear regression; which predictors matter most" },
};
const GHOST = "170,208,255", TRUE_COL = "#ffb347", CLAIM_COL = "#ffe39a", RESID_COL = "#ff8a5c", FLAT_COL = "#8fc4ff";
const N_FLAT = 12;              // tab 2's samples: big enough for a steady R squared, small enough to see each square
const WIDE = 4;                 // "Wider scatter" multiplies the population's noise by this
const FAST = 5;                 // Draw x10 runs the physics this many times faster

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});

const CSS = `
.ghostlines { display:flex; flex-direction:column; gap:6px; width:100%; color:#f3e6c4; }
.glstage { display:flex; gap:14px; align-items:flex-start; justify-content:center; }
.ghostlinescanvas { display:block; flex:0 1 auto; height:auto; width:min(calc(100% - 354px), calc(min(76vh, 100vh - 170px) * var(--glr, 1.69)));
  background:#05080d; border-radius:8px; touch-action:none; -webkit-user-select:none; user-select:none; -webkit-touch-callout:none; }
.glpanel { flex:0 0 340px; display:flex; flex-direction:column; gap:10px; font:16px/1.35 Georgia, "Times New Roman", serif; }
.gltabs { display:flex; gap:6px 10px; justify-content:center; flex-wrap:wrap; font:16px/1.35 Georgia, "Times New Roman", serif; }
.gltab { background:#3b2a14; color:#f3e6c4; border:1px solid #8a6a32; border-radius:16px; padding:6px 14px; font:inherit; font-size:17px; cursor:pointer; }
.gltab:hover { border-color:#e0b55a; }
.gltab:focus-visible { outline:2px solid #ffe39a; outline-offset:2px; }
.gltab.on { background:linear-gradient(#a8742e,#7a5220); border-color:#e2b468; color:#fff6e0; }
.gllesson { border-left:3px solid #e2b468; padding:2px 0 4px 10px; }
.gllessontext { font-size:clamp(17px, 1.25vw, 22px); line-height:1.4; margin:4px 0 6px; color:#fff1d6; }
.gllessonbook { color:#bfae8a; font-size:13px; font-style:italic; }
.gltable tr.icpt td { color:#cdbf9f; font-style:italic; border-top:1px solid rgba(226,180,104,.25); }
.gltable { grid-column:1 / -1; border-collapse:collapse; font-size:15px; width:100%; font-variant-numeric:tabular-nums; }
.gltable th { color:#e2b468; font-weight:normal; text-align:right; padding:2px 4px; border-bottom:1px solid rgba(226,180,104,.4); }
.gltable td { text-align:right; padding:2px 4px; color:#fff6e0; }
.gltable th:first-child, .gltable td:first-child { text-align:left; }
.glmeter { grid-column:1 / -1; height:12px; background:#1a1208; border:1px solid #8a6a32; border-radius:6px; overflow:hidden; }
.glmeter > i { display:block; height:100%; background:linear-gradient(90deg,#a8742e,#ffe39a); }
.glhead { color:#e2b468; font-size:15px; font-weight:bold; letter-spacing:.08em; text-transform:uppercase; }
.glrow { display:flex; gap:6px; align-items:center; flex-wrap:wrap; }
.glpanel button { background:#3b2a14; color:#f3e6c4; border:1px solid #8a6a32; border-radius:7px; padding:7px 12px;
  font:inherit; font-size:18px; cursor:pointer; }
.glpanel button:hover { border-color:#e0b55a; }
.glpanel button:focus-visible { outline:2px solid #ffe39a; outline-offset:2px; }
.glpanel button.primary { background:linear-gradient(#a8742e,#7a5220); border-color:#e2b468; color:#fff6e0; font-weight:bold; }
.glpanel button.tog { border-radius:16px; font-size:16px; padding:5px 11px; opacity:.8; }
.glpanel button.tog[aria-pressed="true"] { background:#1f3a52; border-color:#9ccaf2; color:#eaf5ff; opacity:1; }
.glpanel button.small { font-size:14px; padding:4px 9px; opacity:.85; }
.gln { font-size:40px; font-weight:bold; min-width:2.1ch; text-align:center; color:#fff1cf; font-variant-numeric:tabular-nums; }
.glpanel input[type=range] { flex:1 1 120px; accent-color:#e2b468; min-width:100px; }
.glread { display:grid; grid-template-columns:auto auto; gap:2px 10px; font-size:18px; align-items:baseline; }
.glread dt { color:#cdbf9f; } .glread dd { margin:0; text-align:right; color:#fff6e0; font-variant-numeric:tabular-nums; }
.glread .sep { grid-column:1 / -1; height:1px; background:rgba(226,180,104,.3); margin:4px 0; }
.glread .claim { color:${CLAIM_COL}; } .glread .truth { color:${TRUE_COL}; }
.glread .resid { color:#ffb08a; } .glread .flat { color:${FLAT_COL}; }
@media (max-width: 900px) {
  .glstage { flex-direction:column; align-items:stretch; }
  .ghostlinescanvas { width:100%; height:auto; max-width:100%; }
  .glpanel { flex:1 1 auto; }
}`;

function injectStyle() {
  if (document.getElementById("ghostlines-style")) return;
  const s = document.createElement("style"); s.id = "ghostlines-style"; s.textContent = CSS;
  document.head.appendChild(s);
}

const fmt = (v, d = 1) => (Number.isFinite(v) ? v.toFixed(d) : "–");
// three significant figures, never e-notation (0.272, 5.30, 13.8)
const sig = (v) => { if (!Number.isFinite(v)) return "–"; const a = Math.abs(v); return v.toFixed(a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3); };

export function mountGhostLines(host, opts = {}) {
  injectStyle();
  const P0 = opts.params || {};
  const V = { ...VIEW_DEFAULTS, ...P0 };
  const G = { ...GEOM_DEFAULTS, ...(opts.geometry || {}) };
  G.plot = { ...GEOM_DEFAULTS.plot, ...((opts.geometry || {}).plot || {}) };
  const W = G.imageW, H = G.imageH, PL = G.plot;
  const artPaths = opts.art || {};
  const reduced = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const popOpts = {};
  for (const k of Object.keys(POP_DEFAULTS)) if (Number.isFinite(P0[k])) popOpts[k] = P0[k];

  // ---------- state (everything in `saved` survives closing and reopening the modal) ----------
  const st0 = opts.pegs && typeof opts.pegs === "object" && !Array.isArray(opts.pegs) ? opts.pegs : {};
  let seed = Number.isFinite(st0.seed) ? st0.seed : (popOpts.seed ?? POP_DEFAULTS.seed);
  let popNarrow = makePopulation({ ...popOpts, seed });
  let popWide = makePopulation({ ...popOpts, seed, sd: popNarrow.sd * WIDE });   // same sacks, same draws, 4x the noise
  let wide = false;        // tab 2 only; turned off whenever tab 2 is left
  let pop = popNarrow;
  let n = clampN(Number.isFinite(st0.n) ? st0.n : V.n);
  let drawCount = Number.isFinite(st0.drawCount) ? st0.drawCount : 0;
  let ghosts = Array.isArray(st0.ghosts) ? st0.ghosts.slice() : [];
  const tog = Object.fromEntries(TOGGLES.map(([k, d]) => [k, st0.toggles && k in st0.toggles ? !!st0.toggles[k] : d]));
  let claimX = Number.isFinite(st0.claimX) ? st0.claimX : V.claimX;
  let act = [1, 2, 3, 4].includes(st0.act) ? st0.act : 1;
  let scaled = !!st0.scaled;
  const multiSet = makeMultiSet();
  const multiSd = multiSet.cols.map(colSd), multiZ = multiSet.cols.map(scaleCol);
  const multiMean = multiSet.cols.map((c) => c.reduce((a, v) => a + v, 0) / c.length);
  const yBar = multiSet.y.reduce((a, v) => a + v, 0) / multiSet.y.length;
  let multiOn = Array.isArray(st0.multiOn) && st0.multiOn.length === multiSet.preds.length && st0.multiOn.some(Boolean)
    ? st0.multiOn.map(Boolean) : multiSet.preds.map(() => true);
  let multi = multiFits(multiSet, multiOn);
  let cur = null;          // {idx, xs, ys, sim, t0, speed, done, noGhost}
  let queue = 0, drag = null, dead = false, raf = 0, needDraw = true, lastT = performance.now();
  let envCache = null;

  function clampN(v) { return Math.max(2, Math.min(V.nMax, Math.round(v))); }
  const seedFor = (k) => (Math.imul(seed, 1000003) + k * 7919 + 17) >>> 0;
  const parkLine = () => ({ slope: 0, intercept: V.yView[0] + 0.04 * (V.yView[1] - V.yView[0]) });

  function save() {
    if (!opts.onPegs) return;
    opts.onPegs({ seed, n, drawCount, ghosts: ghosts.slice(), toggles: { ...tog }, claimX, act, scaled, multiOn: multiOn.slice(),
                  curIdx: cur ? cur.idx.slice() : null });
  }

  function rebuildCur(idx, line) {
    const xs = idx.map((i) => pop.xs[i]), ys = idx.map((i) => pop.ys[i]);
    const sim = makeRod(xs);
    sim.setPegs(xs.map((x, i) => ({ x, y: ys[i] })));
    placeRod(sim, line);
    return { idx, xs, ys, sim, t0: -1e9, speed: 1, done: true, noGhost: true };
  }
  if (Array.isArray(st0.curIdx) && st0.curIdx.length >= 2) {
    cur = rebuildCur(st0.curIdx, ghosts.length ? ghosts[ghosts.length - 1] : parkLine());
    while (!cur.sim.settled && cur.sim.time < 60) cur.sim.substep();
  }

  // ---------- DOM ----------
  const root = document.createElement("div"); root.className = "ghostlines";
  const stage = document.createElement("div"); stage.className = "glstage";
  const canvas = document.createElement("canvas"); canvas.className = "ghostlinescanvas";
  canvas.style.aspectRatio = `${W} / ${H}`;
  canvas.style.setProperty("--glr", String(W / H));
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", `${V.title}: sampled sacks, their fitted line and the ghosts of earlier samples`);
  const panel = document.createElement("div"); panel.className = "glpanel";
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn, title) => { const b = el("button", cls, txt); b.type = "button"; if (title) b.title = title; b.addEventListener("click", () => { audio(); fn(); }); return b; };
  const tabs = el("div", "gltabs");
  const tabBtns = {};
  for (const k of [1, 2, 3, 4]) {
    const t = btn(`${k} · ${ACTS[k].name}`, "gltab", () => api.setAct(k)); t.dataset.act = String(k);
    tabBtns[k] = t; tabs.append(t);
  }
  stage.append(canvas, panel); root.append(tabs, stage); host.appendChild(root);
  const ctx = canvas.getContext("2d");

  const lesson = el("div", "gllesson");
  const ctl = el("div", "glctl");
  ctl.style.cssText = "display:flex;flex-direction:column;gap:10px";
  const read = el("dl", "glread");
  panel.append(lesson, ctl, read);
  let nOut = null, range = null, togBtns = {}, wideBtn = null, scaleBtn = null, predBtns = [];

  // the controls a tab needs, and nothing else (the fish board's rule)
  function buildPanel() {
    for (const [k, t] of Object.entries(tabBtns)) { t.classList.toggle("on", +k === act); t.setAttribute("aria-pressed", String(+k === act)); }
    const A = ACTS[act];
    lesson.replaceChildren(el("div", "glhead", "Lesson"), el("p", "gllessontext", A.lesson),
                           el("div", "gllessonbook", "In the book: regression models, " + A.where));
    ctl.replaceChildren();
    nOut = range = wideBtn = scaleBtn = null; togBtns = {}; predBtns = [];
    if (act === 1 || act === 3) {
      ctl.append(el("div", "glhead", "Sample size n"));
      const nRow = el("div", "glrow");
      nOut = el("output", "gln", String(n));
      range = el("input"); range.type = "range"; range.min = 2; range.max = V.nMax; range.step = 1; range.value = n;
      range.setAttribute("aria-label", "Sample size");
      range.addEventListener("input", () => api.setN(+range.value));
      nRow.append(btn("−", "", () => api.setN(n - 1), "Smaller sample"), nOut, btn("+", "", () => api.setN(n + 1), "Larger sample"), range);
      ctl.append(nRow);
      const drawRow = el("div", "glrow");
      drawRow.append(btn("Draw", "primary", () => api.draw(), "Dig n random sacks and let the rod go"),
                     btn("Draw ×10", "", () => api.drawMany(10), "Ten samples, quickly"),
                     btn("Clear", "", () => api.clear(), "Remove every ghost"));
      ctl.append(drawRow);
    } else if (act === 2) {
      const drawRow = el("div", "glrow");
      drawRow.append(btn("New sample", "primary", () => api.draw(), `Dig ${N_FLAT} random sacks and let the rod go`));
      wideBtn = btn("Wider scatter", "tog", () => api.setWide(!wide), "The same sacks with four times the scatter");
      wideBtn.setAttribute("aria-pressed", String(wide));
      drawRow.append(wideBtn);
      ctl.append(drawRow);
    } else {
      ctl.append(el("div", "glhead", "In the model (predictors)"));
      const pRow = el("div", "glrow");
      predBtns = multiSet.preds.map((q, i) => {
        const b = btn(q.name, "tog", () => api.setPredictor(i, !multiOn[i]), `Put ${q.name} in the model or take it out`);
        b.setAttribute("aria-pressed", String(multiOn[i])); pRow.append(b); return b;
      });
      ctl.append(pRow);
      scaleBtn = btn("Scale the measurements", "primary tog", () => api.setScaled(!scaled),
                     "mutate(across(c(...), scale)), then refit");
      scaleBtn.setAttribute("aria-pressed", String(scaled));
      const sRow = el("div", "glrow"); sRow.append(scaleBtn); ctl.append(sRow);
    }
    if (A.tog.length) {
      const togRow = el("div", "glrow");
      for (const [k, label] of A.tog) {
        const b = btn(label, "tog", () => api.setToggle(k, !tog[k]));
        b.setAttribute("aria-pressed", String(tog[k])); togBtns[k] = b; togRow.append(b);
      }
      ctl.append(togRow);
    }
    if (act === 1) {
      const footRow = el("div", "glrow");
      footRow.append(btn("New population", "small", () => api.reroll(), "A fresh hidden population (clears the ghosts)"));
      ctl.append(footRow);
    }
    lastRead = "";
  }

  // ---------- art ----------
  let art = {}, loaded = false;
  const ready = (async () => {
    const [board, rod, spring, peg] = await Promise.all([artPaths.board, artPaths.rod, artPaths.spring, artPaths.peg].map(loadImg));
    if (dead) return;
    art = { board, rod, spring, peg };
    loaded = true; resize();
  })();

  // ---------- layout ----------
  let view = { dpr: 1, S: 1, ox: 0, oy: 0 };
  const stat = document.createElement("canvas"), sx = stat.getContext("2d");
  function resize() {
    if (dead) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cw = Math.max(1, canvas.clientWidth), ch = Math.max(1, canvas.clientHeight);
    for (const c of [canvas, stat]) { c.width = Math.round(cw * dpr); c.height = Math.round(ch * dpr); }
    const k = Math.min(cw / W, ch / H);
    view = { dpr, S: k * dpr, ox: ((cw - W * k) / 2) * dpr, oy: ((ch - H * k) / 2) * dpr };
    if (loaded) buildStatic();
    needDraw = true;
  }
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => resize()) : null;
  if (ro) ro.observe(canvas); else addEventListener("resize", resize);

  const X = (x) => PL.x0 + ((x - V.xView[0]) / (V.xView[1] - V.xView[0])) * (PL.x1 - PL.x0);
  const Y = (y) => PL.y1 - ((y - V.yView[0]) / (V.yView[1] - V.yView[0])) * (PL.y1 - PL.y0);
  const Xinv = (px) => V.xView[0] + ((px - PL.x0) / (PL.x1 - PL.x0)) * (V.xView[1] - V.xView[0]);
  const Yinv = (py) => V.yView[0] + ((PL.y1 - py) / (PL.y1 - PL.y0)) * (V.yView[1] - V.yView[0]);
  const toImage = (e) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * view.dpr - view.ox) / view.S, y: ((e.clientY - r.top) * view.dpr - view.oy) / view.S };
  };

  function niceStep(span, target) {
    const raw = span / target, p = 10 ** Math.floor(Math.log10(raw)), f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }

  // ---------- static layer: board, grid, axes ----------
  function buildStatic() {
    const c = sx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.fillStyle = "#05080d"; c.fillRect(0, 0, stat.width, stat.height);
    c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
    if (act === 4) {                    // tab 4 draws its own six plots (drawMulti) on a plain night wall
      const bg = c.createLinearGradient(0, 0, 0, H);
      bg.addColorStop(0, "#1a120b"); bg.addColorStop(1, "#0b0806");
      c.fillStyle = bg; c.fillRect(0, 0, W, H);
      return;
    }
    if (art.board) c.drawImage(art.board, 0, 0, W, H);
    else codeBoard(c);
    const dx0 = X(pop.xMin), dx1 = X(pop.xMax);
    // the data range is lantern-lit; beyond it the face is in moonlight
    c.save(); c.beginPath(); c.rect(PL.x0, PL.y0, PL.x1 - PL.x0, PL.y1 - PL.y0); c.clip();
    const lit = c.createLinearGradient(dx0, 0, dx1, 0);
    lit.addColorStop(0, "rgba(255,190,110,0.05)"); lit.addColorStop(0.5, "rgba(255,200,120,0.085)"); lit.addColorStop(1, "rgba(255,190,110,0.05)");
    c.fillStyle = lit; c.fillRect(dx0, PL.y0, dx1 - dx0, PL.y1 - PL.y0);
    c.fillStyle = act === 3 ? "rgba(40,70,120,0.20)" : "rgba(0,0,0,0)";
    if (dx0 > PL.x0) c.fillRect(PL.x0, PL.y0, dx0 - PL.x0, PL.y1 - PL.y0);
    if (dx1 < PL.x1) c.fillRect(dx1, PL.y0, PL.x1 - dx1, PL.y1 - PL.y0);
    // engraved grid
    const xs = niceStep(V.xView[1] - V.xView[0], 10), ys = niceStep(V.yView[1] - V.yView[0], 8);
    c.lineWidth = 1;
    for (let x = Math.ceil(V.xView[0] / xs) * xs; x <= V.xView[1] + 1e-9; x += xs) {
      c.strokeStyle = "rgba(255,236,200,0.09)"; c.beginPath(); c.moveTo(X(x), PL.y0); c.lineTo(X(x), PL.y1); c.stroke();
    }
    for (let y = Math.ceil(V.yView[0] / ys) * ys; y <= V.yView[1] + 1e-9; y += ys) {
      c.strokeStyle = "rgba(255,236,200,0.09)"; c.beginPath(); c.moveTo(PL.x0, Y(y)); c.lineTo(PL.x1, Y(y)); c.stroke();
    }
    if (act === 3 && dx1 < PL.x1 - 120) {
      c.font = "italic 26px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "bottom";
      c.fillStyle = "rgba(190,215,255,0.55)"; c.fillText("beyond the data", (dx1 + PL.x1) / 2, PL.y1 - 34);
    }
    c.restore();
    // axes, ticks, numerals
    c.strokeStyle = "#d9b46a"; c.lineWidth = 3;
    c.beginPath(); c.moveTo(PL.x0, PL.y0); c.lineTo(PL.x0, PL.y1); c.lineTo(PL.x1, PL.y1); c.stroke();
    c.fillStyle = "#f6e3b4"; c.font = "26px Georgia, serif";
    c.textAlign = "center"; c.textBaseline = "top";
    for (let x = Math.ceil(V.xView[0] / xs) * xs; x <= V.xView[1] + 1e-9; x += xs) {
      c.beginPath(); c.moveTo(X(x), PL.y1); c.lineTo(X(x), PL.y1 + 9); c.stroke();
      c.fillText(String(+x.toFixed(6)), X(x), PL.y1 + 12);
    }
    c.textAlign = "right"; c.textBaseline = "middle";
    for (let y = Math.ceil(V.yView[0] / ys) * ys; y <= V.yView[1] + 1e-9; y += ys) {
      c.beginPath(); c.moveTo(PL.x0 - 9, Y(y)); c.lineTo(PL.x0, Y(y)); c.stroke();
      c.fillText(String(+y.toFixed(6)), PL.x0 - 14, Y(y));
    }
    // the data range bar under the axis
    c.fillStyle = "rgba(255,200,120,0.75)"; c.fillRect(dx0, PL.y1 + 46, dx1 - dx0, 5);
    c.font = "italic 20px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "top";
    c.fillText("data range", (dx0 + dx1) / 2, PL.y1 + 54);
    c.font = "30px Georgia, serif"; c.fillStyle = "#f6e3b4";
    c.textAlign = "right"; c.textBaseline = "alphabetic"; c.fillText(V.xLabel, PL.x1, H - 12);
    c.save(); c.translate(36, (PL.y0 + PL.y1) / 2); c.rotate(-Math.PI / 2);
    c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(V.yLabel, 0, 0); c.restore();
  }

  function codeBoard(c) {
    // night wall, a lantern glow from the upper left, a dark plank face in a brass frame
    const bg = c.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, "#0d1420"); bg.addColorStop(1, "#070a10");
    c.fillStyle = bg; c.fillRect(0, 0, W, H);
    const face = c.createLinearGradient(0, PL.y0, 0, PL.y1);
    face.addColorStop(0, "#2a1c12"); face.addColorStop(1, "#1d140d");
    c.fillStyle = face; c.fillRect(PL.x0, PL.y0, PL.x1 - PL.x0, PL.y1 - PL.y0);
    c.save(); c.globalAlpha = 0.05; c.strokeStyle = "#e8c48a";      // plank grain and seams
    for (let i = 0; i < 90; i++) {
      const y = PL.y0 + ((i * 37.7) % (PL.y1 - PL.y0)); c.lineWidth = 0.6 + (i % 3) * 0.4;
      c.beginPath(); c.moveTo(PL.x0, y); c.bezierCurveTo(PL.x0 + 300, y + 3, PL.x1 - 400, y - 4, PL.x1, y + 1); c.stroke();
    }
    c.globalAlpha = 0.35; c.strokeStyle = "#0a0604"; c.lineWidth = 2;
    for (let y = PL.y0 + 112; y < PL.y1; y += 112) { c.beginPath(); c.moveTo(PL.x0, y); c.lineTo(PL.x1, y); c.stroke(); }
    c.restore();
    const glow = c.createRadialGradient(PL.x0 + 260, PL.y0 + 80, 20, PL.x0 + 260, PL.y0 + 80, 900);
    glow.addColorStop(0, "rgba(255,190,100,0.20)"); glow.addColorStop(1, "rgba(255,170,80,0)");
    c.fillStyle = glow; c.fillRect(0, 0, W, H);
    c.strokeStyle = "#8a6a32"; c.lineWidth = 8; c.strokeRect(PL.x0 - 6, PL.y0 - 6, PL.x1 - PL.x0 + 12, PL.y1 - PL.y0 + 12);
    c.strokeStyle = "rgba(255,230,170,0.35)"; c.lineWidth = 1.5; c.strokeRect(PL.x0 - 9, PL.y0 - 9, PL.x1 - PL.x0 + 18, PL.y1 - PL.y0 + 18);
    for (const [x, y] of [[PL.x0 - 6, PL.y0 - 6], [PL.x1 + 6, PL.y0 - 6], [PL.x0 - 6, PL.y1 + 6], [PL.x1 + 6, PL.y1 + 6]]) rivet(c, x, y, 5);
  }

  function rivet(c, x, y, r) {
    const g = c.createRadialGradient(x - r * 0.4, y - r * 0.4, r * 0.1, x, y, r);
    g.addColorStop(0, "#fff3cf"); g.addColorStop(0.4, "#b08a46"); g.addColorStop(1, "#4a3212");
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
  }

  // ---------- dynamic parts ----------
  const rodLine = () => (cur ? lineOf(cur.sim) : parkLine());

  function lineAcross(c, l) {
    c.beginPath(); c.moveTo(PL.x0, Y(l.intercept + l.slope * V.xView[0])); c.lineTo(PL.x1, Y(l.intercept + l.slope * V.xView[1]));
  }

  function envelope() {
    if (envCache && envCache.count === ghosts.length) return envCache;
    const pts = [];
    for (let i = 0; i <= 80; i++) {
      const x = V.xView[0] + (i / 80) * (V.xView[1] - V.xView[0]), s = spreadAt(ghosts, x);
      pts.push([x, s.mean - 2 * s.sd, s.mean + 2 * s.sd]);
    }
    envCache = { count: ghosts.length, pts };
    return envCache;
  }

  function drawSpring(c, x, y1, y2, alpha) {
    const a = Math.min(y1, y2), len = Math.max(2, Math.abs(y2 - y1)), w = 12;
    c.save(); c.globalAlpha = alpha;
    if (art.spring) c.drawImage(art.spring, x - w / 2, a, w, len);
    else {
      const coils = Math.max(3, Math.min(12, Math.round(len / 14))), steps = coils * 10;
      c.lineWidth = 1.6;
      for (let k = 0; k < steps; k++) {
        const u0 = k / steps, u1 = (k + 1) / steps;
        const front = Math.cos(u0 * coils * Math.PI * 2) > 0;
        c.strokeStyle = front ? "#e8c77a" : "#7a5523";
        c.beginPath();
        c.moveTo(x + Math.sin(u0 * coils * Math.PI * 2) * w / 2, a + u0 * len);
        c.lineTo(x + Math.sin(u1 * coils * Math.PI * 2) * w / 2, a + u1 * len); c.stroke();
      }
    }
    c.restore();
  }

  function drawRod(c, l) {
    const xL = PL.x0 - 20, xR = PL.x1 + 20;
    const yL = Y(l.intercept + l.slope * Xinv(xL)), yR = Y(l.intercept + l.slope * Xinv(xR));
    const T = 13, len = Math.hypot(xR - xL, yR - yL);
    c.save();
    c.shadowColor = "rgba(0,0,0,0.55)"; c.shadowBlur = 8 * view.S; c.shadowOffsetX = 3 * view.S; c.shadowOffsetY = 5 * view.S;
    c.translate(xL, yL); c.rotate(Math.atan2(yR - yL, xR - xL));
    if (art.rod) c.drawImage(art.rod, 0, -T / 2, len, T);
    else {
      const g = c.createLinearGradient(0, -T / 2, 0, T / 2);
      g.addColorStop(0, "#7a5520"); g.addColorStop(0.18, "#fff0bf"); g.addColorStop(0.42, "#d5a952");
      g.addColorStop(0.8, "#7d561e"); g.addColorStop(1, "#3b2508");
      c.fillStyle = g; c.beginPath();
      if (c.roundRect) c.roundRect(0, -T / 2, len, T, T / 2); else c.rect(0, -T / 2, len, T);
      c.fill();
    }
    c.restore();
  }

  function drawPeg(c, x, y, scale) {
    if (scale <= 0) return;
    const r = 10 * scale;
    c.save();
    c.shadowColor = "rgba(0,0,0,0.6)"; c.shadowBlur = 5 * view.S; c.shadowOffsetX = 2 * view.S; c.shadowOffsetY = 3 * view.S;
    if (art.peg) c.drawImage(art.peg, x - r * 1.2, y - r * 1.2, r * 2.4, r * 2.4);
    else {
      const g = c.createRadialGradient(x - r * 0.4, y - r * 0.45, r * 0.1, x, y, r);
      g.addColorStop(0, "#fff4cc"); g.addColorStop(0.45, "#d4a64e"); g.addColorStop(1, "#5a3c14");
      c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
    }
    c.restore();
  }

  function pegScale(i, now) {
    if (!cur || reduced) return 1;
    const stagger = (0.35 / cur.speed) * (i / Math.max(1, cur.xs.length - 1));
    const u = ((now - cur.t0) / 1000 - stagger) / (0.18 / cur.speed);
    return Math.max(0, Math.min(1, u));
  }

  function drawSquares(c, resid, fill, stroke) {
    for (const [px, py, ry] of resid) {
      const sz = Math.abs(ry - py), left = px + sz > PL.x1 ? px - sz : px;
      c.fillStyle = fill; c.fillRect(left, Math.min(py, ry), sz, sz);
      c.strokeStyle = stroke; c.lineWidth = 1.2; c.strokeRect(left, Math.min(py, ry), sz, sz);
    }
  }

  function draw(now) {
    const c = ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.drawImage(stat, 0, 0);
    c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
    if (act === 4) { drawMulti(c); return; }
    c.save(); c.beginPath(); c.rect(PL.x0, PL.y0, PL.x1 - PL.x0, PL.y1 - PL.y0); c.clip();
    const T = pop.trueLine;
    const showGhosts = act !== 2, showTruth = tog.truth && act !== 2, showClaim = act === 3;
    if (tog.pop && act === 1) {
      c.fillStyle = "rgba(230,220,200,0.32)";
      for (let i = 0; i < pop.xs.length; i++) { c.beginPath(); c.arc(X(pop.xs[i]), Y(pop.ys[i]), 2.6, 0, Math.PI * 2); c.fill(); }
    }
    if (showClaim && ghosts.length >= 3) {
      const e = envelope().pts;
      c.fillStyle = "rgba(150,195,255,0.12)"; c.beginPath();
      e.forEach(([x, lo], i) => (i ? c.lineTo(X(x), Y(lo)) : c.moveTo(X(x), Y(lo))));
      for (let i = e.length - 1; i >= 0; i--) c.lineTo(X(e[i][0]), Y(e[i][2]));
      c.closePath(); c.fill();
    }
    // the ghosts (the current draw's own ghost sits under its rod, so a dragged rod shows where it belongs)
    if (showGhosts && ghosts.length) {
      const a = Math.max(0.08, Math.min(0.45, 1.6 / Math.sqrt(ghosts.length + 8)));
      c.strokeStyle = `rgba(${GHOST},${a})`; c.lineWidth = 2;
      for (const g of ghosts) { lineAcross(c, g); c.stroke(); }
    }
    if (showTruth) {
      c.strokeStyle = TRUE_COL; c.lineWidth = 3.5; c.setLineDash([16, 10]);
      lineAcross(c, T); c.stroke(); c.setLineDash([]);
    }
    const l = rodLine();
    const settledView = cur && cur.sim.settled && !drag;
    if (cur) {
      const resid = cur.xs.map((x, i) => [X(x), Y(cur.ys[i]), Y(l.intercept + l.slope * x)]);
      if (act === 2) {
        const my = cur.ys.reduce((a, v) => a + v, 0) / cur.ys.length;
        if (tog.flatsq) drawSquares(c, cur.xs.map((x, i) => [X(x), Y(cur.ys[i]), Y(my)]), "rgba(120,180,255,0.13)", "rgba(150,200,255,0.65)");
        if (tog.linesq) drawSquares(c, resid, "rgba(255,120,80,0.18)", "rgba(255,150,110,0.7)");
        c.strokeStyle = FLAT_COL; c.lineWidth = 3; c.setLineDash([12, 8]);
        c.beginPath(); c.moveTo(PL.x0, Y(my)); c.lineTo(PL.x1, Y(my)); c.stroke(); c.setLineDash([]);
        c.font = "italic 24px Georgia, serif"; c.fillStyle = FLAT_COL; c.textAlign = "left"; c.textBaseline = "bottom";
        c.fillText("flat line: the mean", PL.x0 + 12, Y(my) - 6);
      } else if (tog.squares && act === 1) drawSquares(c, resid, "rgba(255,120,80,0.16)", "rgba(255,150,110,0.6)");
      const showResid = act === 1 ? tog.resid : act === 2;
      const springA = settledView && !showResid ? 0 : 1;
      resid.forEach(([px, py, ry], i) => { if (pegScale(i, now) >= 1 && springA) drawSpring(c, px, py, ry, springA); });
      if (showResid && settledView) {
        c.strokeStyle = RESID_COL; c.lineWidth = 2;
        for (const [px, py, ry] of resid) { c.beginPath(); c.moveTo(px, py); c.lineTo(px, ry); c.stroke(); }
      }
    }
    drawRod(c, l);
    if (cur) cur.xs.forEach((x, i) => drawPeg(c, X(x), Y(cur.ys[i]), pegScale(i, now)));
    if (showClaim) {
      const cx = X(claimX);
      c.strokeStyle = "rgba(255,227,154,0.55)"; c.lineWidth = 2; c.setLineDash([6, 6]);
      c.beginPath(); c.moveTo(cx, PL.y0); c.lineTo(cx, PL.y1); c.stroke(); c.setLineDash([]);
      const s = spreadAt(ghosts, claimX);
      c.strokeStyle = `rgba(${GHOST},0.75)`; c.lineWidth = 2;
      for (const p of s.preds) { c.beginPath(); c.moveTo(cx - 13, Y(p)); c.lineTo(cx + 13, Y(p)); c.stroke(); }
      if (s.n >= 3) {
        const top = Y(s.mean + 2 * s.sd), bot = Y(s.mean - 2 * s.sd), bx = cx + 26;
        c.strokeStyle = CLAIM_COL; c.lineWidth = 3;
        c.beginPath(); c.moveTo(bx - 8, top); c.lineTo(bx, top); c.lineTo(bx, bot); c.lineTo(bx - 8, bot); c.stroke();
        c.font = "bold 26px Georgia, serif"; c.fillStyle = CLAIM_COL; c.textBaseline = "middle";
        const txt = `± ${fmt(2 * s.sd)}`, tw = c.measureText(txt).width;
        const tx = bx + 10 + tw > PL.x1 - 4 ? cx - 26 - tw : bx + 10;
        c.fillStyle = "rgba(5,8,13,0.7)"; c.fillRect(tx - 4, (top + bot) / 2 - 17, tw + 8, 34);
        c.fillStyle = CLAIM_COL; c.textAlign = "left"; c.fillText(txt, tx, (top + bot) / 2);
      }
      if (cur) {
        c.fillStyle = "#fff6e0"; c.beginPath(); c.arc(cx, Y(l.intercept + l.slope * claimX), 7, 0, Math.PI * 2); c.fill();
      }
    }
    c.restore();
    if (showClaim) {                        // the new-sack handle on the x axis: drag it anywhere, past the data too
      const cx = X(claimX), y = PL.y1 - 2;
      c.fillStyle = CLAIM_COL; c.strokeStyle = "rgba(5,8,13,0.8)"; c.lineWidth = 2;
      c.beginPath(); c.moveTo(cx, y - 26); c.lineTo(cx - 15, y); c.lineTo(cx + 15, y); c.closePath(); c.fill(); c.stroke();
      c.font = "bold 24px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "top";
      const t = `new sack: x = ${fmtX(claimX)}`, tw = c.measureText(t).width;
      const tx = Math.min(PL.x1 - tw / 2 - 6, Math.max(PL.x0 + tw / 2 + 6, cx)), ty = PL.y0 + 50;
      c.fillStyle = "rgba(5,8,13,0.85)"; c.fillRect(tx - tw / 2 - 6, ty - 3, tw + 12, 32);
      c.fillStyle = CLAIM_COL; c.fillText(t, tx, ty);
    }
    if (opts.debug && cur) {
      const f = ols(cur.xs, cur.ys);
      c.save(); c.strokeStyle = "rgba(255,0,255,0.9)"; c.setLineDash([4, 4]); c.lineWidth = 1;
      lineAcross(c, { slope: f.slope, intercept: f.intercept }); c.stroke(); c.restore();
    }
  }

  // ---------- tab 4: several predictors, one small plot each, plus measured against predicted ----------
  const fitNow = () => (scaled ? multi.scaled : multi.raw);
  const multiCoefs = () => fitNow().coefs;
  // the measurements in the model, biggest coefficient first, ignoring the sign (the intercept is not ranked)
  const multiOrder = () => multiCoefs().map((v, i) => [v == null ? -1 : Math.abs(v), i]).filter((p) => p[0] >= 0)
    .sort((a, b) => b[0] - a[0]).map((p) => p[1]);
  const pfmt = (p) => (!Number.isFinite(p) ? "–" : p < 0.001 ? p.toExponential(1) : p.toFixed(3));
  const CELL = { x0: 24, y0: 12, gap: 14, cols: 3, rows: 2, eq: 74 };   // eq: the strip for the equation
  function cellRect(k) {
    const w = (W - 2 * CELL.x0 - (CELL.cols - 1) * CELL.gap) / CELL.cols;
    const h = (H - 2 * CELL.y0 - (CELL.rows - 1) * CELL.gap - CELL.eq) / CELL.rows;
    const cx = k % CELL.cols, cy = Math.floor(k / CELL.cols);
    const x = CELL.x0 + cx * (w + CELL.gap), y = CELL.y0 + cy * (h + CELL.gap);
    return { x, y, w, h, px0: x + 62, px1: x + w - 14, py0: y + 74, py1: y + h - 40 };
  }
  const cellAt = (p) => { for (let k = 0; k < 6; k++) { const r = cellRect(k); if (p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h) return k; } return -1; };

  // the regression equation, y = b + m1 x1 + m2 x2 ..., terms in the table's order (biggest first)
  function equationParts() {
    const fit = fitNow(), order = multiOrder();
    const parts = [["diamonds per sack", "#fff1cf", "bold "], [" = ", "#f3e6c4", ""], [sig(fit.intercept), "#e9d6a8", ""]];
    for (const i of order) {
      const m = fit.coefs[i], name = (scaled ? "scaled " : "") + multiSet.preds[i].name.toLowerCase();
      parts.push([m < 0 ? " − " : " + ", "#f3e6c4", ""], [sig(Math.abs(m)), m < 0 ? "#cfe6ff" : "#ffe39a", "bold "],
                 [" × ", "#f3e6c4", ""], [name, "#f3e6c4", "italic "]);
    }
    return parts;
  }
  function drawEquation(c) {
    const parts = equationParts(), y = H - CELL.y0 - CELL.eq / 2 + 4, maxW = W - 2 * CELL.x0;
    let size = 28, total;
    const width = () => parts.reduce((a, [t, , st]) => { c.font = `${st}${size}px Georgia, serif`; return a + c.measureText(t).width; }, 0);
    while ((total = width()) > maxW && size > 14) size -= 1;
    let x = (W - total) / 2;
    c.textAlign = "left"; c.textBaseline = "middle";
    for (const [t, col, st] of parts) { c.font = `${st}${size}px Georgia, serif`; c.fillStyle = col; c.fillText(t, x, y - 8); x += c.measureText(t).width; }
    c.font = "italic 16px Georgia, serif"; c.fillStyle = "#cdbf9f"; c.textAlign = "center";
    c.fillText(scaled ? "y = b + m₁x₁ + m₂x₂ + …   each x in SDs from its mean; each m is a value in the table, b the (Intercept)"
                      : "y = b + m₁x₁ + m₂x₂ + …   each m is a value in the table, b the (Intercept)", W / 2, y + 22);
  }

  function drawMulti(c) {
    const fit = fitNow(), P = multiSet.preds, n = multiSet.y.length, order = multiOrder();
    const resid = multiSet.y.map((y, i) => y - fit.fitted[i]);
    // what each plot shows: on = the measurement's part of the prediction plus the residual (so the points sit
    // around the model's line for it, the others held at their means); off = the sacks as measured, no line
    const ptsFor = (j) => {
      const xs = scaled ? multiZ[j] : multiSet.cols[j], b = fit.coefs[j], xm = scaled ? 0 : multiMean[j];
      const ys = b == null ? multiSet.y : xs.map((x, i) => yBar + b * (x - xm) + resid[i]);
      return { xs, ys, b, xm };
    };
    const all = P.map((_, j) => ptsFor(j));
    let ylo = Infinity, yhi = -Infinity;
    for (const a of all) for (const y of a.ys) { ylo = Math.min(ylo, y); yhi = Math.max(yhi, y); }
    for (const y of fit.fitted) { ylo = Math.min(ylo, y); yhi = Math.max(yhi, y); }
    const pad = 0.06 * (yhi - ylo); ylo -= pad; yhi += pad;
    const zMax = Math.ceil(Math.max(...multiZ.flat().map(Math.abs)) * 2) / 2;
    const yStep = niceStep(yhi - ylo, 4);

    const frame = (r, on) => {
      c.fillStyle = on ? "rgba(255,200,120,0.07)" : "rgba(0,0,0,0.25)"; c.fillRect(r.x, r.y, r.w, r.h);
      c.strokeStyle = on ? "#b38a44" : "rgba(138,106,50,0.45)"; c.lineWidth = on ? 2.5 : 1.5; c.strokeRect(r.x, r.y, r.w, r.h);
    };
    const axes = (r, xlo, xhi, xlab) => {
      c.strokeStyle = "rgba(217,180,106,0.8)"; c.lineWidth = 1.5;
      c.beginPath(); c.moveTo(r.px0, r.py0); c.lineTo(r.px0, r.py1); c.lineTo(r.px1, r.py1); c.stroke();
      c.font = "17px Georgia, serif"; c.fillStyle = "#e9d6a8"; c.textAlign = "right"; c.textBaseline = "middle";
      for (let y = Math.ceil(ylo / yStep) * yStep; y <= yhi; y += yStep) {
        const py = r.py1 - ((y - ylo) / (yhi - ylo)) * (r.py1 - r.py0);
        c.fillText(String(+y.toFixed(6)), r.px0 - 6, py);
        c.strokeStyle = "rgba(255,236,200,0.07)"; c.beginPath(); c.moveTo(r.px0, py); c.lineTo(r.px1, py); c.stroke();
      }
      const xs = niceStep(xhi - xlo, 4);
      c.textAlign = "center"; c.textBaseline = "top";
      for (let x = Math.ceil(xlo / xs) * xs; x <= xhi + 1e-9; x += xs) c.fillText(String(+x.toFixed(6)), r.px0 + ((x - xlo) / (xhi - xlo)) * (r.px1 - r.px0), r.py1 + 4);
      c.font = "italic 16px Georgia, serif"; c.fillStyle = "#cdbf9f"; c.textAlign = "right"; c.textBaseline = "bottom";
      c.fillText(xlab, r.px1, r.y + r.h - 2);
    };
    P.forEach((q, j) => {
      const r = cellRect(j), on = multiOn[j], a = all[j];
      let xlo, xhi;
      if (scaled) { xlo = -zMax; xhi = zMax; }
      else { const mn = Math.min(...a.xs), mx = Math.max(...a.xs), pd = 0.05 * (mx - mn); xlo = mn - pd; xhi = mx + pd; }
      const PX = (x) => r.px0 + ((x - xlo) / (xhi - xlo)) * (r.px1 - r.px0);
      const PY = (y) => r.py1 - ((y - ylo) / (yhi - ylo)) * (r.py1 - r.py0);
      frame(r, on);
      axes(r, xlo, xhi, scaled ? `${q.name} (SDs from its mean)` : `${q.name} (${q.unit})`);
      c.save(); c.beginPath(); c.rect(r.px0, r.py0 - 4, r.px1 - r.px0, r.py1 - r.py0 + 4); c.clip();
      c.fillStyle = on ? "rgba(255,226,170,0.75)" : "rgba(200,190,170,0.25)";
      for (let i = 0; i < n; i++) { c.beginPath(); c.arc(PX(a.xs[i]), PY(a.ys[i]), on ? 3.6 : 3, 0, Math.PI * 2); c.fill(); }
      if (on) {
        const neg = a.b < 0, y0 = yBar + a.b * (xlo - a.xm), y1 = yBar + a.b * (xhi - a.xm);
        c.shadowColor = "rgba(0,0,0,0.6)"; c.shadowBlur = 6 * view.S; c.shadowOffsetY = 3 * view.S;
        c.strokeStyle = neg ? "#9cc8f2" : "#e9c46a"; c.lineWidth = 6; c.lineCap = "round";
        c.beginPath(); c.moveTo(PX(xlo), PY(y0)); c.lineTo(PX(xhi), PY(y1)); c.stroke();
        c.shadowColor = "transparent"; c.strokeStyle = neg ? "#e6f3ff" : "#fff3c8"; c.lineWidth = 1.6;
        c.beginPath(); c.moveTo(PX(xlo), PY(y0) - 1.5); c.lineTo(PX(xhi), PY(y1) - 1.5); c.stroke();
      }
      c.restore();
      c.save(); c.translate(r.x + 14, (r.py0 + r.py1) / 2); c.rotate(-Math.PI / 2);
      c.font = "italic 14px Georgia, serif"; c.fillStyle = "#cdbf9f"; c.textAlign = "center"; c.textBaseline = "top";
      c.fillText(on ? "diamonds per sack, others held fixed" : "diamonds per sack", 0, 0); c.restore();
      // title: rank, name; coefficient and p value
      c.textBaseline = "alphabetic"; c.textAlign = "left";
      if (on) {
        const rank = order.indexOf(j) + 1;
        c.font = "bold 30px Georgia, serif"; c.fillStyle = "#e2b468"; c.fillText(String(rank), r.x + 12, r.y + 34);
      }
      c.font = "bold 23px Georgia, serif"; c.fillStyle = on ? "#fff1cf" : "rgba(243,230,196,0.5)";
      c.fillText(`${q.name} (${q.unit})`, r.x + 40, r.y + 30);
      c.font = "18px Georgia, serif";
      if (on) {
        const v = a.b, p = fit.coefP[j];
        c.fillStyle = v < 0 ? "#cfe6ff" : "#ffe39a";
        c.fillText(`${v < 0 ? "−" : "+"}${sig(Math.abs(v))} per ${scaled ? "SD" : q.unit.replace(/^per /, "")}`, r.x + 40, r.y + 56);
        c.fillStyle = p < 0.05 ? "#ffe39a" : "#ff9f86"; c.textAlign = "right";
        c.fillText(`p_value ${pfmt(p)}`, r.x + r.w - 12, r.y + 56);
      } else {
        c.fillStyle = "rgba(205,191,159,0.7)"; c.font = "italic 18px Georgia, serif";
        c.fillText("not in the model: tap to add", r.x + 40, r.y + 56);
      }
    });
    // the sixth plot: measured against predicted, as the book judges a model
    const r = cellRect(5);
    frame(r, true);
    const mlo = ylo, mhi = yhi;
    const PX = (x) => r.px0 + ((x - mlo) / (mhi - mlo)) * (r.px1 - r.px0);
    const PY = (y) => r.py1 - ((y - ylo) / (yhi - ylo)) * (r.py1 - r.py0);
    axes(r, mlo, mhi, "measured diamonds per sack");
    c.save(); c.beginPath(); c.rect(r.px0, r.py0, r.px1 - r.px0, r.py1 - r.py0); c.clip();
    c.strokeStyle = "rgba(143,196,255,0.8)"; c.lineWidth = 2; c.setLineDash([8, 6]);
    c.beginPath(); c.moveTo(PX(mlo), PY(mlo)); c.lineTo(PX(mhi), PY(mhi)); c.stroke(); c.setLineDash([]);
    c.fillStyle = "rgba(255,226,170,0.8)";
    for (let i = 0; i < n; i++) { c.beginPath(); c.arc(PX(multiSet.y[i]), PY(fit.fitted[i]), 3.6, 0, Math.PI * 2); c.fill(); }
    c.restore();
    c.textAlign = "left"; c.textBaseline = "alphabetic"; c.font = "bold 23px Georgia, serif"; c.fillStyle = "#fff1cf";
    c.fillText("Predicted against measured", r.x + 14, r.y + 30);
    c.font = "18px Georgia, serif"; c.fillStyle = "#ffe39a";
    c.fillText(`R squared ${fit.r2.toFixed(3)} · ${order.length} of ${P.length} measurements`, r.x + 14, r.y + 56);
    c.save(); c.translate(r.x + 14, (r.py0 + r.py1) / 2); c.rotate(-Math.PI / 2);
    c.font = "italic 16px Georgia, serif"; c.fillStyle = "#cdbf9f"; c.textAlign = "center"; c.textBaseline = "top";
    c.fillText("predicted", 0, 0); c.restore();
    drawEquation(c);
  }

  // ---------- readout ----------
  let lastRead = "";
  const fmtX = (x) => fmt(x, V.xView[1] - V.xView[0] >= 50 ? 0 : 1);
  function readout() {
    const rows = [];
    const l = cur ? lineOf(cur.sim) : null;
    if (act === 4) {
      const fit = fitNow(), order = multiOrder();
      rows.push([scaled ? "Coefficients, scaled (per 1 SD)" : "Coefficients, as dug (per unit)", ""]);
      rows.push(["table", [["variable", "value", "std_err", "p_value"],
        ...order.map((i) => [multiSet.preds[i].name, sig(fit.coefs[i]), sig(fit.coefSe[i]), pfmt(fit.coefP[i])]),
        ["(Intercept)", sig(fit.intercept), sig(fit.se[0]), pfmt(fit.p[0])]]]);
      rows.push(["sep"], ["r_squared", fit.r2.toFixed(3)]);
    } else if (act === 2) {
      if (cur) {
        const rss = sumSquares(cur.xs, cur.ys, l), tss = totalSquares(cur.ys), r2 = 1 - rss / tss;
        rows.push([`This sample${wide ? " (wider)" : ""}`, `n = ${cur.xs.length}`],
                  ["residual sum of squares", fmt(rss, 0), "resid"], ["total sum of squares", fmt(tss, 0), "flat"],
                  ["sep"], ["R squared = 1 − (residual ÷ total)", fmt(r2, 3)], ["meter", Math.max(0, Math.min(1, r2))]);
      } else rows.push(["Press New sample", ""]);
    } else {
      if (cur) {
        rows.push(["This sample", `n = ${cur.xs.length}`], ["slope", sig(l.slope)], ["intercept", fmt(l.intercept, 1)]);
        if (act === 1) rows.push(["sum of squares", fmt(sumSquares(cur.xs, cur.ys, l), 0)]);
      } else rows.push(["Press Draw", ""]);
      rows.push(["sep"]);
      const ns = new Set(ghosts.map((g) => g.n));
      rows.push(["Lines drawn", ghosts.length + (ns.size > 1 ? " (mixed n)" : "")]);
      if (act === 1 && ghosts.length >= 2) rows.push(["slope spread (SD)", sig(slopeSd(ghosts))]);
      if (tog.truth && act === 1) rows.push(["true slope", sig(pop.trueLine.slope), "truth"], ["true intercept", fmt(pop.trueLine.intercept, 1), "truth"]);
      if (act === 3) {
        const s = spreadAt(ghosts, claimX);
        rows.push(["sep"], [`New sack at x = ${fmtX(claimX)}`, "", "claim"]);
        if (l) rows.push(["this line says", fmt(l.intercept + l.slope * claimX), "claim"]);
        if (s.n >= 3) rows.push(["the lines say", `${fmt(s.mean)} ± ${fmt(2 * s.sd)}`, "claim"]);
        else rows.push(["Draw a few samples", "to see the spread", "claim"]);
        if (tog.truth) rows.push(["true line says", fmt(pop.trueLine.intercept + pop.trueLine.slope * claimX), "truth"]);
      }
    }
    const key = JSON.stringify(rows);
    if (key === lastRead) return;
    lastRead = key;
    read.replaceChildren(...rows.flatMap(([a, b, cls]) => {
      if (a === "sep") return [el("div", "sep")];
      if (a === "table") {
        const t = el("table", "gltable");
        b.forEach((cells, ri) => { const tr = el("tr", cells[0] === "(Intercept)" ? "icpt" : ""); cells.forEach((v) => tr.append(el(ri ? "td" : "th", "", v))); t.append(tr); });
        return [t];
      }
      if (a === "meter") { const m = el("div", "glmeter"); const f = el("i"); f.style.width = `${(b * 100).toFixed(1)}%`; m.append(f); return [m]; }
      const dt = el("dt", cls || "", a), dd = el("dd", cls || "", b);
      return [dt, dd];
    }));
  }

  // ---------- draws ----------
  function commit() {
    if (!cur || cur.done) return;
    cur.done = true;
    if (cur.noGhost) { save(); return; }          // tab 2's samples (and its wider re-reads) never join the fan
    ghosts.push({ ...lineOf(cur.sim), n: cur.xs.length });
    if (ghosts.length > 600) ghosts.splice(0, ghosts.length - 600);
    envCache = null;
    save();
  }

  function finishNow() {
    if (!cur) return;
    while (!cur.sim.settled && cur.sim.time < 60) cur.sim.substep();
    commit();
  }

  function startDraw(speed, instant) {
    if (cur && !cur.done) finishNow();
    const from = cur ? lineOf(cur.sim) : parkLine();
    const idx = sampleIdx(pop, act === 2 ? N_FLAT : n, rng(seedFor(drawCount++)));
    const xs = idx.map((i) => pop.xs[i]), ys = idx.map((i) => pop.ys[i]);
    const sim = makeRod(xs);
    sim.setPegs(xs.map((x, i) => ({ x, y: ys[i] })));
    placeRod(sim, from);
    cur = { idx, xs, ys, sim, t0: instant || reduced ? -1e9 : performance.now(), speed, done: false, noGhost: act === 2 };
    if (instant || reduced) finishNow();
    else plink(speed);
    needDraw = true;
  }

  function reread() {
    if (!cur) return;
    if (!cur.done) finishNow();
    const from = lineOf(cur.sim);
    const ys = cur.idx.map((i) => pop.ys[i]);
    cur.sim.setPegs(cur.xs.map((x, i) => ({ x, y: ys[i] })));
    placeRod(cur.sim, from);
    cur.ys = ys; cur.done = false; cur.noGhost = true; cur.t0 = -1e9; cur.speed = 1;
    if (reduced) finishNow(); else twang();
    needDraw = true;
  }

  // ---------- frame ----------
  function tick(now) {
    if (dead) return;
    const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now;
    let busy = !!cur && now - cur.t0 < 700 / cur.speed;      // pegs still dropping in
    if (cur && !drag && !cur.sim.settled) {
      // pegs land first (a short drop), then the rod is let go
      const dropped = reduced || (now - cur.t0) / 1000 > (0.35 + 0.18) / cur.speed;
      if (dropped) cur.sim.advance(dt * cur.speed);
      busy = true;
      if (cur.sim.settled) {
        commit();
        if (queue > 0) { queue--; startDraw(FAST); }
      }
    }
    if (busy || needDraw || drag) {
      if (loaded) draw(now);
      readout();
      needDraw = false;
    }
    raf = requestAnimationFrame(tick);
  }

  // ---------- input: drag the rod off its line, drag the claim marker ----------
  function rodHit(p, touch) {
    if (act === 4 || !cur || p.x < PL.x0 || p.x > PL.x1) return false;
    const l = lineOf(cur.sim);
    return Math.abs(Y(l.intercept + l.slope * Xinv(p.x)) - p.y) < (touch ? 34 : 20);
  }
  function claimHit(p, touch) {
    if (act !== 3) return false;
    const pad = touch ? 34 : 22;
    return (Math.abs(p.x - X(claimX)) < pad && p.y > PL.y0 && p.y < PL.y1 + 56) || (p.y > PL.y1 && p.y < PL.y1 + 56 && p.x > PL.x0 && p.x < PL.x1);
  }
  const clampClaim = (x) => Math.max(V.xView[0], Math.min(V.xView[1], x));

  canvas.addEventListener("pointerdown", (e) => {
    audio();
    const p = toImage(e), touch = e.pointerType !== "mouse";
    if (act === 4) {
      const k = cellAt(p);
      if (k >= 0 && k < multiSet.preds.length) { api.setPredictor(k, !multiOn[k]); e.preventDefault(); }
      return;
    }
    if (claimHit(p, touch) && !(rodHit(p, touch) && Math.abs(p.x - X(claimX)) > 22)) {
      drag = { kind: "claim", id: e.pointerId };
      api.setClaim(Xinv(p.x));
    } else if (rodHit(p, touch)) {
      if (!cur.done) finishNow();
      const sim = cur.sim, xv = Xinv(p.x);
      const tilt = Math.abs(xv - sim.xc) > 0.18 * (V.xView[1] - V.xView[0]);
      drag = { kind: "rod", id: e.pointerId, tilt, xv, off: Yinv(p.y) - sim.rodAt(xv) };
    } else return;
    canvas.setPointerCapture(e.pointerId);
    needDraw = true;
    e.preventDefault();
  });
  canvas.addEventListener("pointermove", (e) => {
    const p = toImage(e), touch = e.pointerType !== "mouse";
    if (drag && e.pointerId === drag.id) {
      if (drag.kind === "claim") api.setClaim(Xinv(p.x));
      else {
        const sim = cur.sim, v = Yinv(p.y) - drag.off;
        if (drag.tilt) { const dx = drag.xv - sim.xc; sim.s = (v - sim.h) / dx; }
        else sim.h = v - sim.s * (drag.xv - sim.xc);
        sim.vh = sim.vs = 0; sim.settled = false; sim._quiet = 0;
      }
      needDraw = true;
    } else if (e.pointerType === "mouse") {
      if (act === 4) { const k = cellAt(p); canvas.style.cursor = k >= 0 && k < multiSet.preds.length ? "pointer" : "default"; return; }
      canvas.style.cursor = claimHit(p, touch) ? "ew-resize" : rodHit(p, touch) ? "grab" : "default";
    }
  });
  const endPointer = (e) => {
    if (drag && e.pointerId === drag.id) {
      if (drag.kind === "rod") { cur.sim._acc = 0; if (reduced) finishNow(); twang(); }
      drag = null; needDraw = true;
    }
  };
  canvas.addEventListener("pointerup", endPointer);
  canvas.addEventListener("pointercancel", endPointer);
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());

  // ---------- sound (synthesised, quiet, only after a user gesture) ----------
  let actx = null, master = null;
  function audio() {
    if (opts.sound === false) return;
    try {
      if (!actx) {
        actx = new (window.AudioContext || window.webkitAudioContext)();
        master = actx.createGain(); master.gain.value = 0.4; master.connect(actx.destination);
      }
      if (actx.state === "suspended") actx.resume();
    } catch { actx = null; }
  }
  function tone(t, type, f0, f1, peak, decay) {
    const o = actx.createOscillator(); o.type = type;
    o.frequency.setValueAtTime(f0, t); if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + decay);
    const g = actx.createGain();
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, t + decay);
    o.connect(g).connect(master); o.start(t); o.stop(t + decay + 0.02);
  }
  function plink(speed) {
    if (!actx) return;
    const t = actx.currentTime + 0.01, k = Math.min(6, n), q = speed > 1 ? 0.4 : 1;
    for (let i = 0; i < k; i++) tone(t + (i * 0.3) / k / speed, "triangle", 1900 + 140 * i, 1880 + 140 * i, 0.03 * q, 0.06);
    tone(t + 0.5 / speed, "sine", 330, 324, 0.02 * q, 1.0 / speed);
  }
  function twang() { if (actx) tone(actx.currentTime + 0.01, "sine", 300, 292, 0.02, 1.2); }

  // ---------- API ----------
  const api = {
    ready,
    draw(o = {}) { startDraw(1, !!o.instant); },
    drawMany(k = 10, o = {}) {
      if (o.instant || reduced) { for (let i = 0; i < k; i++) startDraw(FAST, true); return; }
      queue += k - 1; startDraw(FAST, false);
    },
    clear() { queue = 0; cur = null; ghosts = []; envCache = null; needDraw = true; save(); },
    reroll(newSeed) {
      seed = Number.isFinite(newSeed) ? newSeed : seed + 1;
      popNarrow = makePopulation({ ...popOpts, seed });
      popWide = makePopulation({ ...popOpts, seed, sd: popNarrow.sd * WIDE });
      wide = false; pop = popNarrow;
      drawCount = 0; queue = 0; cur = null; ghosts = []; envCache = null;
      buildPanel();
      if (act === 2) startDraw(1, true);
      if (loaded) buildStatic();
      needDraw = true; save();
    },
    setN(v) { n = clampN(v); if (nOut) nOut.textContent = String(n); if (range) range.value = n; needDraw = true; save(); },
    n: () => n,
    ghosts: () => ghosts.map((g) => ({ ...g })),
    current: () => (cur ? { xs: cur.xs.slice(), ys: cur.ys.slice(), ...lineOf(cur.sim) } : null),
    olsCurrent: () => { if (!cur) return null; const f = ols(cur.xs, cur.ys); return { slope: f.slope, intercept: f.intercept }; },
    isSettled: () => queue === 0 && !drag && (!cur || cur.sim.settled),
    setClaim(x) { claimX = clampClaim(x); needDraw = true; save(); },
    claim: () => claimX,
    spreadAt: (x) => spreadAt(ghosts, x),
    setToggle(k, on) {
      if (!(k in tog)) return;
      tog[k] = !!on; if (togBtns[k]) togBtns[k].setAttribute("aria-pressed", String(tog[k])); needDraw = true; save();
    },
    toggles: () => ({ ...tog }),
    setAct(k) {
      if (![1, 2, 3, 4].includes(k)) return;
      if (k !== act) { queue = 0; if (cur && !cur.done) finishNow(); }   // a Draw ×10 never runs on into another tab
      if (act === 2 && k !== 2 && wide) api.setWide(false);
      act = k;
      if (k === 3) tog.claim = true;
      if (k === 2 && (!cur || cur.xs.length !== N_FLAT)) startDraw(1, false);
      buildPanel();
      if (loaded) buildStatic();
      needDraw = true; save();
    },
    act: () => act,
    setWide(on) {
      on = !!on;
      if (on === wide) return;
      wide = on; pop = wide ? popWide : popNarrow;
      if (wideBtn) wideBtn.setAttribute("aria-pressed", String(wide));
      reread();
    },
    wide: () => wide,
    setScaled(on) {
      scaled = !!on;
      if (scaleBtn) scaleBtn.setAttribute("aria-pressed", String(scaled));
      needDraw = true; save();
    },
    scaled: () => scaled,
    rSquared: () => (cur ? 1 - sumSquares(cur.xs, cur.ys, lineOf(cur.sim)) / totalSquares(cur.ys) : NaN),
    setPredictor(i, on) {
      if (!(i >= 0 && i < multiOn.length)) return;
      if (!on && multiOn.filter(Boolean).length === 1) return;        // a model needs at least one measurement
      multiOn[i] = !!on;
      multi = multiFits(multiSet, multiOn);
      if (predBtns[i]) predBtns[i].setAttribute("aria-pressed", String(multiOn[i]));
      needDraw = true; save();
    },
    predictors: () => multiOn.slice(),
    equation: () => equationParts().map((p) => p[0]).join(""),
    multi: () => {
      const cp = (f) => ({ intercept: f.intercept, coefs: f.coefs.slice(), coefSe: f.coefSe.slice(), coefP: f.coefP.slice(), r2: f.r2 });
      return { preds: multiSet.preds.map((q) => ({ ...q })), sd: multiSd.slice(), on: multiOn.slice(), raw: cp(multi.raw),
               scaled: cp(multi.scaled), order: multiOrder(), size: multiSet.y.length };
    },
    population: () => ({ seed, size: pop.size, xMin: pop.xMin, xMax: pop.xMax, trueLine: { ...pop.trueLine } }),
    view: () => ({ xView: V.xView.slice(), yView: V.yView.slice(), plot: { ...PL }, imageW: W, imageH: H }),
    get reducedMotion() { return reduced; },
    destroy() {
      if (dead) return;
      dead = true; cancelAnimationFrame(raf);
      if (ro) ro.disconnect(); else removeEventListener("resize", resize);
      if (actx) { try { actx.close(); } catch { /* already closed */ } }
    },
  };
  canvas.ghostLines = api;          // for tests and the console; harmless to students
  buildPanel();
  if (act === 3) tog.claim = true;
  if (act === 2 && (!cur || cur.xs.length !== N_FLAT)) startDraw(1, true);
  readout();
  raf = requestAnimationFrame(tick);
  return api;
}

export const mount = mountGhostLines;
