// The Ghost-Line Board — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"ghost_lines"`), built
// 2026-11-05 for regression/pits (the live regression scenario's hub) on the drawdown board's physics.
//
// A hidden population of claims (shared/ghost_lines_math.js: seeded, x over the data range, y = a true line +
// noise). DRAW drops n of them, chosen at random, onto the board as brass pegs; the drawdown board's sprung
// rod (shared/drawdown_physics.js) is let go on them and swings to rest on that sample's least-squares line,
// then stays behind as a faint ghost when the next sample is drawn, so repeated draws build a fan. It teaches:
// least squares (the springs are the residuals; drag the rod off and it swings back; squares and their sum on
// demand), slope and intercept (read out), how a small sample misleads (n = 2 or 3: wild ghosts), how more data
// settles the line (the fan narrows with n), and prediction (a "new claim" marker anywhere on the x axis, also
// beyond the data, where every ghost's prediction is ticked and their spread shown: wide past the data).
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
//   g.draw({instant}); g.drawMany(k, {instant}); g.clear(); g.reroll(seed?); g.setN(n); g.n();
//   g.ghosts(); g.current(); g.olsCurrent(); g.isSettled(); g.setClaim(x); g.claim(); g.spreadAt(x);
//   g.setToggle(name, on); g.toggles(); g.population(); g.ready (Promise); g.destroy();
//   canvas.ghostLines exposes the same API for tests.
import {
  POP_DEFAULTS, makePopulation, sampleIdx, rng, makeRod, placeRod, lineOf, ols, spreadAt, slopeSd, sumSquares,
} from "./ghost_lines_math.js?v=155";

const VIEW_DEFAULTS = {
  xView: [0, 20], yView: [0, 90], xLabel: "Gravel depth (ft)", yLabel: "Carats per 100 t",
  title: "The ghost-line board", n: 5, nMax: 40, claimX: 17,
};
const GEOM_DEFAULTS = { imageW: 1400, imageH: 830, plot: { x0: 130, y0: 36, x1: 1370, y1: 712 } };
const TOGGLES = [
  ["resid", "Residuals", true], ["squares", "Squares", false], ["truth", "True line", false],
  ["pop", "Population", false], ["claim", "New claim", false],
];
const GHOST = "170,208,255", TRUE_COL = "#ffb347", CLAIM_COL = "#ffe39a", RESID_COL = "#ff8a5c";
const FAST = 5;                 // Draw x10 runs the physics this many times faster

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});

const CSS = `
.ghostlines { display:flex; flex-direction:column; gap:6px; width:100%; color:#f3e6c4; }
.glstage { display:flex; gap:14px; align-items:flex-start; justify-content:center; }
.ghostlinescanvas { display:block; flex:0 1 auto; height:auto; width:min(calc(100% - 324px), calc(min(80vh, 100vh - 130px) * var(--glr, 1.69)));
  background:#05080d; border-radius:8px; touch-action:none; -webkit-user-select:none; user-select:none; -webkit-touch-callout:none; }
.glpanel { flex:0 0 310px; display:flex; flex-direction:column; gap:10px; font:16px/1.35 Georgia, "Times New Roman", serif; }
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
  let pop = makePopulation({ ...popOpts, seed });
  let n = clampN(Number.isFinite(st0.n) ? st0.n : V.n);
  let drawCount = Number.isFinite(st0.drawCount) ? st0.drawCount : 0;
  let ghosts = Array.isArray(st0.ghosts) ? st0.ghosts.slice() : [];
  const tog = Object.fromEntries(TOGGLES.map(([k, , d]) => [k, st0.toggles && k in st0.toggles ? !!st0.toggles[k] : d]));
  let claimX = Number.isFinite(st0.claimX) ? st0.claimX : V.claimX;
  let cur = null;          // {idx, xs, ys, sim, t0, speed, done}
  let queue = 0, drag = null, dead = false, raf = 0, needDraw = true, lastT = performance.now();
  let envCache = null;

  function clampN(v) { return Math.max(2, Math.min(V.nMax, Math.round(v))); }
  const seedFor = (k) => (Math.imul(seed, 1000003) + k * 7919 + 17) >>> 0;
  const parkLine = () => ({ slope: 0, intercept: V.yView[0] + 0.04 * (V.yView[1] - V.yView[0]) });

  function save() {
    if (!opts.onPegs) return;
    opts.onPegs({ seed, n, drawCount, ghosts: ghosts.slice(), toggles: { ...tog }, claimX,
                  curIdx: cur ? cur.idx.slice() : null });
  }

  function rebuildCur(idx, line) {
    const xs = idx.map((i) => pop.xs[i]), ys = idx.map((i) => pop.ys[i]);
    const sim = makeRod(xs);
    sim.setPegs(xs.map((x, i) => ({ x, y: ys[i] })));
    placeRod(sim, line);
    return { idx, xs, ys, sim, t0: -1e9, speed: 1, done: true };
  }
  if (Array.isArray(st0.curIdx) && st0.curIdx.length >= 2 && ghosts.length) {
    cur = rebuildCur(st0.curIdx, ghosts[ghosts.length - 1]);
    while (!cur.sim.settled && cur.sim.time < 60) cur.sim.substep();
  }

  // ---------- DOM ----------
  const root = document.createElement("div"); root.className = "ghostlines";
  const stage = document.createElement("div"); stage.className = "glstage";
  const canvas = document.createElement("canvas"); canvas.className = "ghostlinescanvas";
  canvas.style.aspectRatio = `${W} / ${H}`;
  canvas.style.setProperty("--glr", String(W / H));
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", `${V.title}: sampled points, their fitted line and the ghosts of earlier samples`);
  const panel = document.createElement("div"); panel.className = "glpanel";
  stage.append(canvas, panel); root.append(stage); host.appendChild(root);
  const ctx = canvas.getContext("2d");

  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (txt, cls, fn, title) => { const b = el("button", cls, txt); b.type = "button"; if (title) b.title = title; b.addEventListener("click", () => { audio(); fn(); }); return b; };

  panel.append(el("div", "glhead", V.title));
  panel.append(el("div", "glhead", "Sample size n"));
  const nRow = el("div", "glrow");
  const nOut = el("output", "gln", String(n));
  const range = el("input"); range.type = "range"; range.min = 2; range.max = V.nMax; range.step = 1; range.value = n;
  range.setAttribute("aria-label", "Sample size");
  range.addEventListener("input", () => api.setN(+range.value));
  nRow.append(btn("−", "", () => api.setN(n - 1), "Smaller sample"), nOut, btn("+", "", () => api.setN(n + 1), "Larger sample"), range);
  panel.append(nRow);
  const drawRow = el("div", "glrow");
  drawRow.append(btn("Draw", "primary", () => api.draw(), "Dig n random claims and let the rod go"),
                 btn("Draw ×10", "", () => api.drawMany(10), "Ten samples, quickly"),
                 btn("Clear", "", () => api.clear(), "Remove every ghost"));
  panel.append(drawRow);
  const togRow = el("div", "glrow");
  const togBtns = {};
  for (const [k, label] of TOGGLES) {
    const b = btn(label, "tog", () => api.setToggle(k, !tog[k]));
    b.setAttribute("aria-pressed", String(tog[k])); togBtns[k] = b; togRow.append(b);
  }
  panel.append(togRow);
  const read = el("dl", "glread");
  panel.append(read);
  const footRow = el("div", "glrow");
  footRow.append(btn("New population", "small", () => api.reroll(), "A fresh hidden population (clears the ghosts)"));
  panel.append(footRow);

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
    if (art.board) c.drawImage(art.board, 0, 0, W, H);
    else codeBoard(c);
    const dx0 = X(pop.xMin), dx1 = X(pop.xMax);
    // the data range is lantern-lit; beyond it the face is in moonlight
    c.save(); c.beginPath(); c.rect(PL.x0, PL.y0, PL.x1 - PL.x0, PL.y1 - PL.y0); c.clip();
    const lit = c.createLinearGradient(dx0, 0, dx1, 0);
    lit.addColorStop(0, "rgba(255,190,110,0.05)"); lit.addColorStop(0.5, "rgba(255,200,120,0.085)"); lit.addColorStop(1, "rgba(255,190,110,0.05)");
    c.fillStyle = lit; c.fillRect(dx0, PL.y0, dx1 - dx0, PL.y1 - PL.y0);
    c.fillStyle = "rgba(40,70,120,0.20)";
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
    if (dx1 < PL.x1 - 120) {
      c.font = "italic 26px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "top";
      c.fillStyle = "rgba(190,215,255,0.55)"; c.fillText("beyond the data", (dx1 + PL.x1) / 2, PL.y0 + 14);
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

  function draw(now) {
    const c = ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.drawImage(stat, 0, 0);
    c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
    c.save(); c.beginPath(); c.rect(PL.x0, PL.y0, PL.x1 - PL.x0, PL.y1 - PL.y0); c.clip();
    const T = pop.trueLine;
    if (tog.pop) {
      c.fillStyle = "rgba(230,220,200,0.32)";
      for (let i = 0; i < pop.xs.length; i++) { c.beginPath(); c.arc(X(pop.xs[i]), Y(pop.ys[i]), 2.6, 0, Math.PI * 2); c.fill(); }
    }
    if (tog.claim && ghosts.length >= 3) {
      const e = envelope().pts;
      c.fillStyle = "rgba(150,195,255,0.12)"; c.beginPath();
      e.forEach(([x, lo], i) => (i ? c.lineTo(X(x), Y(lo)) : c.moveTo(X(x), Y(lo))));
      for (let i = e.length - 1; i >= 0; i--) c.lineTo(X(e[i][0]), Y(e[i][2]));
      c.closePath(); c.fill();
    }
    // the ghosts (the current draw's own ghost sits under its rod, so a dragged rod shows where it belongs)
    if (ghosts.length) {
      const a = Math.max(0.08, Math.min(0.45, 1.6 / Math.sqrt(ghosts.length + 8)));
      c.strokeStyle = `rgba(${GHOST},${a})`; c.lineWidth = 2;
      for (const g of ghosts) { lineAcross(c, g); c.stroke(); }
    }
    if (tog.truth) {
      c.strokeStyle = TRUE_COL; c.lineWidth = 3.5; c.setLineDash([16, 10]);
      lineAcross(c, T); c.stroke(); c.setLineDash([]);
    }
    const l = rodLine();
    const settledView = cur && cur.sim.settled && !drag;
    if (cur) {
      const resid = cur.xs.map((x, i) => [X(x), Y(cur.ys[i]), Y(l.intercept + l.slope * x)]);
      if (tog.squares) {
        for (const [px, py, ry] of resid) {
          const s = Math.abs(ry - py), left = px + s > PL.x1 ? px - s : px;
          c.fillStyle = "rgba(255,120,80,0.16)"; c.fillRect(left, Math.min(py, ry), s, s);
          c.strokeStyle = "rgba(255,150,110,0.6)"; c.lineWidth = 1.2; c.strokeRect(left, Math.min(py, ry), s, s);
        }
      }
      const springA = settledView && !tog.resid ? 0 : 1;
      resid.forEach(([px, py, ry], i) => { if (pegScale(i, now) >= 1 && springA) drawSpring(c, px, py, ry, springA); });
      if (tog.resid && settledView) {
        c.strokeStyle = RESID_COL; c.lineWidth = 2;
        for (const [px, py, ry] of resid) { c.beginPath(); c.moveTo(px, py); c.lineTo(px, ry); c.stroke(); }
      }
    }
    drawRod(c, l);
    if (cur) cur.xs.forEach((x, i) => drawPeg(c, X(x), Y(cur.ys[i]), pegScale(i, now)));
    if (tog.claim) {
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
    if (tog.claim) {                        // the claim handle on the x axis: drag it anywhere, past the data too
      const cx = X(claimX), y = PL.y1 - 2;
      c.fillStyle = CLAIM_COL; c.strokeStyle = "rgba(5,8,13,0.8)"; c.lineWidth = 2;
      c.beginPath(); c.moveTo(cx, y - 26); c.lineTo(cx - 15, y); c.lineTo(cx + 15, y); c.closePath(); c.fill(); c.stroke();
      c.font = "bold 24px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "top";
      const t = `new claim x = ${fmt(claimX)}`, tw = c.measureText(t).width;
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

  // ---------- readout ----------
  let lastRead = "";
  function readout() {
    const rows = [];
    const l = cur ? lineOf(cur.sim) : null;
    if (cur) {
      rows.push(["This sample", `n = ${cur.xs.length}`], ["slope", fmt(l.slope, 2)], ["intercept", fmt(l.intercept, 1)],
                ["sum of squares", fmt(sumSquares(cur.xs, cur.ys, l), 0)]);
    } else rows.push(["Press Draw", ""]);
    rows.push(["sep"]);
    const ns = new Set(ghosts.map((g) => g.n));
    rows.push(["Lines drawn", ghosts.length + (ns.size > 1 ? " (mixed n)" : "")]);
    if (ghosts.length >= 2) rows.push(["slope spread (SD)", fmt(slopeSd(ghosts), 2)]);
    if (tog.truth) rows.push(["true slope", fmt(pop.trueLine.slope, 2), "truth"], ["true intercept", fmt(pop.trueLine.intercept, 1), "truth"]);
    if (tog.claim) {
      const s = spreadAt(ghosts, claimX);
      rows.push(["sep"], [`At x = ${fmt(claimX)}`, "", "claim"]);
      if (l) rows.push(["this line says", fmt(l.intercept + l.slope * claimX), "claim"]);
      if (s.n >= 3) rows.push(["the lines say", `${fmt(s.mean)} ± ${fmt(2 * s.sd)}`, "claim"]);
      if (tog.truth) rows.push(["true line says", fmt(pop.trueLine.intercept + pop.trueLine.slope * claimX), "truth"]);
    }
    const key = JSON.stringify(rows);
    if (key === lastRead) return;
    lastRead = key;
    read.replaceChildren(...rows.flatMap(([a, b, cls]) => {
      if (a === "sep") return [el("div", "sep")];
      const dt = el("dt", cls || "", a), dd = el("dd", cls || "", b);
      return [dt, dd];
    }));
  }

  // ---------- draws ----------
  function commit() {
    if (!cur || cur.done) return;
    cur.done = true;
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
    const idx = sampleIdx(pop, n, rng(seedFor(drawCount++)));
    const xs = idx.map((i) => pop.xs[i]), ys = idx.map((i) => pop.ys[i]);
    const sim = makeRod(xs);
    sim.setPegs(xs.map((x, i) => ({ x, y: ys[i] })));
    placeRod(sim, from);
    cur = { idx, xs, ys, sim, t0: instant || reduced ? -1e9 : performance.now(), speed, done: false };
    if (instant || reduced) finishNow();
    else plink(speed);
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
    if (!cur || p.x < PL.x0 || p.x > PL.x1) return false;
    const l = lineOf(cur.sim);
    return Math.abs(Y(l.intercept + l.slope * Xinv(p.x)) - p.y) < (touch ? 34 : 20);
  }
  function claimHit(p, touch) {
    if (!tog.claim) return false;
    const pad = touch ? 34 : 22;
    return (Math.abs(p.x - X(claimX)) < pad && p.y > PL.y0 && p.y < PL.y1 + 56) || (p.y > PL.y1 && p.y < PL.y1 + 56 && p.x > PL.x0 && p.x < PL.x1);
  }
  const clampClaim = (x) => Math.max(V.xView[0], Math.min(V.xView[1], x));

  canvas.addEventListener("pointerdown", (e) => {
    audio();
    const p = toImage(e), touch = e.pointerType !== "mouse";
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
      pop = makePopulation({ ...popOpts, seed });
      drawCount = 0; queue = 0; cur = null; ghosts = []; envCache = null;
      if (loaded) buildStatic();
      needDraw = true; save();
    },
    setN(v) { n = clampN(v); nOut.textContent = String(n); range.value = n; needDraw = true; save(); },
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
      tog[k] = !!on; togBtns[k].setAttribute("aria-pressed", String(tog[k])); needDraw = true; save();
    },
    toggles: () => ({ ...tog }),
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
  readout();
  raf = requestAnimationFrame(tick);
  return api;
}

export const mount = mountGhostLines;
