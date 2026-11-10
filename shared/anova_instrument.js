// The ANOVA instrument (2026-11-05, session "variance"): builds an analysis-of-variance table one row at a
// time, each row drawn as the distances it adds up. Shared by the book (chapter 12b, imported by URL), the
// Rothamsted rooms (engine instrument kind "anova_board") and the live ANOVA class scenario, so every
// surface shows the same picture in the same words as the course's anovaTest(): spread (sum of squares),
// free values (what is left once the values the model fixes are spoken for), variance (spread per free
// value), F (a row's variance over the noise variance), p, and share (a row's spread over the total).
// Grown from the prototype temp/mobile_prototypes/anova_step5_fertiliser.html.
//
//   mountAnovaInstrument(host, { config, params?, pegs?, onPegs? }) -> { destroy, show(step), steps, table() }
//   config = { title?, intro?, credit?, subtitle?, response, unit?, factors: [{ key, label, levels?, levelLabels? }] (one or two),
//              rows: [{ y, <factor key>: level, ... }] }
//   params = { skin: "book" | "board", layout?: "stacked", start? }   (default: the WIDE layout, plot left, table right,
//            elbow arrows; "stacked" keeps the older plot-over-table layout. config.noun, e.g. "plots", names the measurements.)
// Two factors assume a balanced (or proportional) design, where these sums of squares equal anovaTest()'s.
// anovaDecompose(config) is the pure arithmetic, tested by tests/anova_instrument.test.mjs against R.
// The engine passes { geometry, config, params, pegs, onPegs }; geometry is unused. It is READ, never
// graded: it holds no answer and never logs or gates anything.

const PALETTE = ["#e0709a", "#6fd08c", "#b08cf0", "#f2d14a", "#4aa8f0", "#f0a24a", "#4fd1c5", "#e8edf2"];
const ROWCOL = { a: "#4aa8f0", b: "#f2d14a", ab: "#f0a24a", noise: "#4fd1c5", total: "#b7c0c9" };

const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;

export function anovaDecompose(config) {
  const F = config.factors || [];
  const rows = (config.rows || []).map(r => Object.assign({}, r, { y: +r.y }));
  const lv = f => f.levels || [...new Set(rows.map(r => String(r[f.key])))];
  const A = F[0], B = F[1];
  const aL = lv(A), bL = B ? lv(B) : null;
  const N = rows.length, grand = mean(rows.map(r => r.y));
  const groupMeans = (keyFn) => {
    const g = new Map();
    rows.forEach(r => { const k = keyFn(r); if (!g.has(k)) g.set(k, []); g.get(k).push(r.y); });
    return g;
  };
  const ssOf = g => [...g.values()].reduce((s, v) => s + v.length * (mean(v) - grand) ** 2, 0);
  const gA = groupMeans(r => String(r[A.key]));
  const gB = B ? groupMeans(r => String(r[B.key])) : null;
  const gC = B ? groupMeans(r => String(r[A.key]) + "\u0000" + String(r[B.key])) : gA;
  const sst = rows.reduce((s, r) => s + (r.y - grand) ** 2, 0);
  const ssa = ssOf(gA), ssb = B ? ssOf(gB) : 0;
  const ssCells = ssOf(gC);
  const cellMean = r => mean(gC.get(B ? String(r[A.key]) + "\u0000" + String(r[B.key]) : String(r[A.key])));
  const ssn = rows.reduce((s, r) => s + (r.y - cellMean(r)) ** 2, 0);
  const out = [];
  const dfn = N - gC.size;
  out.push({ key: "a", term: A.key, label: A.label || A.key, ss: ssa, df: aL.length - 1 });
  if (B) {
    out.push({ key: "b", term: B.key, label: B.label || B.key, ss: ssb, df: bL.length - 1 });
    out.push({ key: "ab", term: A.key + ":" + B.key, label: "Interaction", ss: ssCells - ssa - ssb,
               df: (aL.length - 1) * (bL.length - 1) });
  }
  out.push({ key: "noise", term: "noise", label: "Noise", ss: ssn, df: dfn });
  out.push({ key: "total", term: "total", label: "Total", ss: sst, df: N - 1 });
  const vNoise = ssn / dfn;
  out.forEach(r => {
    r.share = r.ss / sst;
    if (r.key !== "total") r.variance = r.ss / r.df;
    if (r.key !== "total" && r.key !== "noise") { r.F = r.variance / vNoise; r.p = fUpperTail(r.F, r.df, dfn); }
  });
  return { rows: out, N, grand, levelsA: aL, levelsB: bL, cells: gC.size, groupA: gA, groupB: gB, groupCells: gC, cellMean };
}

// Upper-tail p of the F distribution, via the regularised incomplete beta function (Numerical Recipes).
function lgam(x) {
  const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
  let y = x, t = x + 5.5; t -= (x + 0.5) * Math.log(t);
  let a = 1.000000000190015; for (const k of c) a += k / ++y;
  return -t + Math.log(2.5066282746310005 * a / x);
}
function betacf(a, b, x) {
  const qab = a + b, qap = a + 1, qam = a - 1; let c = 1, d = 1 - qab * x / qap;
  if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d; let h = d;
  for (let m = 1; m <= 300; m++) {
    const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; d = 1 / d; h *= d * c;
    aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; d = 1 / d;
    const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-14) break;
  }
  return h;
}
function betai(a, b, x) {
  if (x <= 0) return 0; if (x >= 1) return 1;
  const bt = Math.exp(lgam(a + b) - lgam(a) - lgam(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
}
export function fUpperTail(F, d1, d2) { return betai(d2 / 2, d1 / 2, d2 / (d2 + d1 * F)); }

// Rounded as the course's anovaTest() prints (signif 4, F to 2 places, share to 3 places); p below 0.001 reads <0.001.
const sig4 = v => String(+v.toPrecision(4));
const fmt = {
  ss: sig4,
  v: sig4,
  F: v => v.toFixed(2),
  p: v => v < 0.001 ? "<0.001" : String(+v.toPrecision(3)),
  share: v => v.toFixed(3),
};

const CSS = `
.anova-inst{--bg:#14181d;--card:#1e242b;--ink:#e8edf2;--dim:#8c97a3;--line:#2d3640;--btn:#2b3540;--btnb:#3a4755;
  background:var(--bg);color:var(--ink);border-radius:12px;padding:12px;font:15px/1.4 -apple-system,system-ui,"Segoe UI",sans-serif;
  max-width:860px;margin:1em auto}
.anova-inst.skin-board{--bg:#2a2118;--card:#3a2d20;--ink:#f3e6c8;--dim:#bfa982;--line:#5a4630;--btn:#4a3a28;--btnb:#7a6040;
  font-family:Georgia,"Times New Roman",serif}
.anova-inst .ai-intro{margin:4px 0 2px;font-size:14px;line-height:1.5} .anova-inst .ai-credit{margin:0 0 8px;font-size:12px;font-style:italic;color:var(--dim)}
.anova-inst h4{margin:0 0 4px;font-size:16px;color:var(--ink)} .anova-inst .ai-sub{color:var(--dim);font-size:13px;margin:0 0 8px}
.anova-inst .ai-btns{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 8px}
.anova-inst button{background:var(--btn);color:var(--ink);border:1px solid var(--btnb);border-radius:8px;padding:7px 10px;font:inherit;font-size:14px;cursor:pointer}
.anova-inst button.on{background:#3b5b7a;border-color:#6aa6d8} .anova-inst button.next{border-color:#f0a24a;box-shadow:0 0 8px #f0a24a99}
.anova-inst svg{width:100%;height:auto;display:block;background:var(--card);border-radius:10px}
.anova-inst .ai-cap{min-height:2.8em;color:var(--ink);font-size:14px;margin:8px 2px}
.anova-inst table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:14px;margin:0;background:var(--card);border-radius:10px}
.anova-inst th{color:var(--dim);font-weight:500;font-size:12px;text-align:right;padding:6px 6px 4px;line-height:1.2;border:0}
.anova-inst td{text-align:right;padding:5px 6px;border-top:1px solid var(--line);font-weight:600}
.anova-inst th:first-child,.anova-inst td:first-child{text-align:left}
.anova-inst td small{display:block;font-weight:400;color:var(--dim);font-size:11px}
.anova-inst tr.hidden td{color:transparent} .anova-inst tr.hidden td:first-child{color:var(--dim);opacity:.5}
.anova-inst tr.hidden td small{color:transparent}
.anova-inst tr.active td{background:rgba(106,166,216,.14)}
.anova-inst .ai-wrap{overflow-x:auto}
.anova-inst.narrow{padding:6px} .anova-inst.narrow table{font-size:11.5px}
.anova-inst.narrow th small,.anova-inst.narrow td small{display:none}
.anova-inst.narrow th,.anova-inst.narrow td{padding:4px 2px} .anova-inst.narrow th{font-size:11px}
`;

export function mountAnovaInstrument(host, opts = {}) {
  const cfg = opts.config || {};
  const P = Object.assign({ skin: "book" }, opts.params || {});
  const D = anovaDecompose(cfg);
  const two = (cfg.factors || []).length > 1;
  const A = cfg.factors[0], B = two ? cfg.factors[1] : null;
  const lab = (f, l) => (f.levelLabels && f.levelLabels[l]) || l;
  const steps = two ? ["total", "a", "b", "ab", "noise"] : ["total", "a", "noise"];
  const stepName = { total: "Total", a: A.label || A.key, b: B ? (B.label || B.key) : "", ab: "Interaction", noise: "Noise" };
  const done = new Set(Array.isArray(opts.pegs) ? opts.pegs : []);
  let view = done.size ? [...done].slice(-1)[0] : "start";

  if (!document.getElementById("anova-inst-css")) {
    const st = document.createElement("style"); st.id = "anova-inst-css"; st.textContent = CSS; document.head.appendChild(st);
  }
  if (P.layout !== "stacked") return mountWide(host, cfg, P, D, opts);
  const root = document.createElement("div");
  root.className = "anova-inst skin-" + P.skin;
  root.innerHTML = `<h4></h4><p class="ai-sub"></p><div class="ai-btns"></div>
    <svg viewBox="0 0 720 400" role="img"></svg><div class="ai-cap"></div><div class="ai-wrap"><table></table></div>`;
  host.appendChild(root);
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => root.classList.toggle("narrow", root.clientWidth < 600)) : null;
  if (ro) ro.observe(root);
  root.querySelector("h4").textContent = cfg.title || "Analysis of variance";
  if (cfg.intro) {
    const intro = document.createElement("p"); intro.className = "ai-intro"; intro.textContent = cfg.intro;
    root.querySelector(".ai-sub").before(intro);
    if (cfg.credit) { const c = document.createElement("p"); c.className = "ai-credit"; c.textContent = cfg.credit; intro.after(c); }
  }
  root.querySelector(".ai-sub").textContent = cfg.subtitle ||
    `${D.N} measurements of ${cfg.response || "the response"}${cfg.unit ? " (" + cfg.unit + ")" : ""}. Press the numbered buttons in order to build the table.`;
  const svg = root.querySelector("svg"), cap = root.querySelector(".ai-cap"), tbl = root.querySelector("table");
  const btnBox = root.querySelector(".ai-btns");
  const btns = {};
  steps.forEach((s, i) => {
    const b = document.createElement("button"); b.type = "button";
    b.textContent = `${i + 1} · ${stepName[s]}`;
    b.addEventListener("click", () => show(s));
    btnBox.appendChild(b); btns[s] = b;
  });

  // ---- the table --------------------------------------------------------------------------------------
  const howText = (r) => {
    const aN = D.levelsA.length, bN = two ? D.levelsB.length : 0;
    if (r.key === "total") return `${D.N} values − 1 spoken for by the grand mean`;
    if (r.key === "a") return `${aN} ${A.label || A.key} means − 1 spoken for`;
    if (r.key === "b") return `${bN} ${B.label || B.key} means − 1 spoken for`;
    if (r.key === "ab") return `(${aN} − 1) × (${bN} − 1)`;
    return `${D.N} values − ${D.cells} ${two ? "cell" : "group"} means`;
  };
  function drawTable() {
    const noiseDone = done.has("noise");
    const order = D.rows.map(r => r.key);
    tbl.innerHTML = `<thead><tr><th></th><th>Sum of squares<br><small>spread</small></th><th>Free values<br><small>degrees of freedom</small></th>
      <th>Variance<br><small>spread ÷ free values</small></th><th>F<br><small>÷ noise variance</small></th><th>p<br><small>noise alone</small></th>
      <th>Share<br><small>of the total</small></th></tr></thead><tbody></tbody>`;
    const body = tbl.querySelector("tbody");
    order.forEach(k => {
      const r = D.rows.find(x => x.key === k);
      const tr = document.createElement("tr");
      const shown = done.has(k);
      if (!shown) tr.className = "hidden";
      if (view === k) tr.classList.add("active");
      const c = ROWCOL[k];
      const cell = (txt, small) => `<td style="color:${c}">${txt}${small ? `<small>${small}</small>` : ""}</td>`;
      tr.innerHTML = `<td style="color:${c}">${r.label}</td>` + cell(fmt.ss(r.ss)) + cell(r.df, howText(r)) +
        cell(r.variance == null ? "" : fmt.v(r.variance), r.key === "noise" && noiseDone ? "the yardstick" : "") +
        cell(noiseDone && r.F != null ? fmt.F(r.F) : "") + cell(noiseDone && r.p != null ? fmt.p(r.p) : "") +
        cell(fmt.share(r.share));
      body.appendChild(tr);
    });
  }

  // ---- the plot ---------------------------------------------------------------------------------------
  const NS = "http://www.w3.org/2000/svg";
  const W = 720, H = 400, X0 = 70, X1 = 600, PT = 18, PB = 340;
  const ys = (cfg.rows || []).map(r => +r.y);
  const lo = Math.min(...ys), hi = Math.max(...ys), pad = (hi - lo) * 0.08 || 1;
  const YMIN = lo - pad, YMAX = hi + pad;
  const sy = v => PB - (v - YMIN) / (YMAX - YMIN) * (PB - PT);
  const el = (n, a, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; svg.appendChild(e); return e; };
  const pts = (cfg.rows || []).map((r, i) => ({ i, y: +r.y, a: String(r[A.key]), b: two ? String(r[B.key]) : null }));
  const aIdx = l => D.levelsA.indexOf(l), bIdx = l => two ? D.levelsB.indexOf(l) : 0;
  let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const shuffled = pts.slice(); for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]; }
  const meanA = l => mean(D.groupA.get(l)), meanB = l => mean(D.groupB.get(l));
  const cellM = (a, b) => two ? mean(D.groupCells.get(a + "\u0000" + b)) : meanA(a);
  const bShift = b => two ? meanB(b) - D.grand : 0;
  const pred = (a, b) => meanA(a) + bShift(b);           // where the cell would sit if B acted the same everywhere

  function groupsFor(v) {
    if (v === "total" || v === "start") return [{ label: `${D.N} values, no grouping`, pts: shuffled }];
    if (v === "a") return D.levelsA.map(l => ({ label: lab(A, l), a: l, pts: pts.filter(p => p.a === l).sort((p, q) => bIdx(p.b) - bIdx(q.b)), m: meanA(l) }));
    if (v === "b") return D.levelsB.map(l => ({ label: lab(B, l), b: l, pts: pts.filter(p => p.b === l).sort((p, q) => aIdx(p.a) - aIdx(q.a)), m: meanB(l) }));
    if (!two) return D.levelsA.map(l => ({ label: lab(A, l), a: l, pts: pts.filter(p => p.a === l), m: meanA(l) }));
    const g = []; D.levelsA.forEach(a => D.levelsB.forEach(b => g.push({ label: `${lab(A, a)} · ${lab(B, b)}`, a, b, pts: pts.filter(p => p.a === a && p.b === b), m: cellM(a, b) })));
    return g;
  }
  function marker(x, p) {
    const col = PALETTE[aIdx(p.a) % PALETTE.length];
    const k = bIdx(p.b);
    if (!two || k === 1) return el("circle", { cx: x, cy: sy(p.y), r: 4.5, fill: col, stroke: "#fff", "stroke-width": 1 });
    if (k === 0) return el("circle", { cx: x, cy: sy(p.y), r: 4, fill: "none", stroke: col, "stroke-width": 2.2 });
    return el("rect", { x: x - 4, y: sy(p.y) - 4, width: 8, height: 8, fill: col, stroke: "#fff", "stroke-width": 1 });
  }
  function drawPlot() {
    svg.innerHTML = "";
    const ticks = niceTicks(YMIN, YMAX);
    ticks.forEach(t => { el("line", { x1: X0, x2: X1, y1: sy(t), y2: sy(t), stroke: "#2a323b" });
      el("text", { x: X0 - 6, y: sy(t) + 4, fill: "#8c97a3", "font-size": 11, "text-anchor": "end" }, String(t)); });
    el("text", { x: 14, y: (PT + PB) / 2, fill: "#8c97a3", "font-size": 12, "text-anchor": "middle", transform: `rotate(-90 14 ${(PT + PB) / 2})` }, cfg.response || "response");
    const G = groupsFor(view), Wg = (X1 - X0) / G.length, half = Wg * 0.42;
    const cx = gi => X0 + Wg * gi + Wg / 2;
    const xs = new Map();
    G.forEach((g, gi) => { const w = Wg * 0.8, x0 = X0 + Wg * gi + (Wg - w) / 2; g.pts.forEach((p, i) => xs.set(p, x0 + (i + 0.5) * w / g.pts.length)); });
    // grand mean
    if (view !== "start") {
      el("line", { x1: X0, x2: X1, y1: sy(D.grand), y2: sy(D.grand), stroke: "#b7c0c9", "stroke-width": 1.5, "stroke-dasharray": "6 4" });
      el("text", { x: X1 + 6, y: sy(D.grand) + 4, fill: "#e8edf2", "font-size": 11 }, "grand mean");
    }
    if (view === "total") xs.forEach((x, p) => el("line", { x1: x, x2: x, y1: sy(p.y), y2: sy(D.grand), stroke: "#b7c0c9", "stroke-width": 1.2, "stroke-dasharray": "3 3" }));
    if (view === "a" || view === "b") {
      const col = ROWCOL[view];
      G.forEach((g, gi) => {
        el("line", { x1: cx(gi), x2: cx(gi), y1: sy(g.m), y2: sy(D.grand), stroke: col, "stroke-width": 6, "stroke-linecap": "round", opacity: 0.9 });
        el("line", { x1: cx(gi) - half, x2: cx(gi) + half, y1: sy(g.m), y2: sy(g.m), stroke: view === "a" ? PALETTE[gi % PALETTE.length] : "#e8edf2", "stroke-width": 3 });
      });
    }
    if (view === "ab") {
      G.forEach((g, gi) => {
        const pr = pred(g.a, g.b);
        el("line", { x1: cx(gi) - half, x2: cx(gi) + half, y1: sy(meanA(g.a)), y2: sy(meanA(g.a)), stroke: PALETTE[aIdx(g.a) % PALETTE.length], "stroke-width": 1.4, "stroke-dasharray": "1 3" });
        el("line", { x1: cx(gi) - 8, x2: cx(gi) - 8, y1: sy(meanA(g.a)), y2: sy(pr), stroke: ROWCOL.b, "stroke-width": 4, "stroke-linecap": "round" });
        el("line", { x1: cx(gi) - half, x2: cx(gi) + half, y1: sy(pr), y2: sy(pr), stroke: "#e8edf2", "stroke-width": 1.6, "stroke-dasharray": "3 3" });
        el("line", { x1: cx(gi), x2: cx(gi), y1: sy(pr), y2: sy(g.m), stroke: ROWCOL.ab, "stroke-width": 6, "stroke-linecap": "round" });
        el("line", { x1: cx(gi) - half, x2: cx(gi) + half, y1: sy(g.m), y2: sy(g.m), stroke: PALETTE[aIdx(g.a) % PALETTE.length], "stroke-width": 3 });
      });
    }
    if (view === "noise") {
      G.forEach((g, gi) => el("line", { x1: cx(gi) - half, x2: cx(gi) + half, y1: sy(g.m), y2: sy(g.m), stroke: two ? PALETTE[aIdx(g.a) % PALETTE.length] : PALETTE[gi % PALETTE.length], "stroke-width": 3 }));
      xs.forEach((x, p) => el("line", { x1: x, x2: x, y1: sy(p.y), y2: sy(cellM(p.a, p.b)), stroke: ROWCOL.noise, "stroke-width": 1.6, "stroke-dasharray": "3 2" }));
    }
    xs.forEach((x, p) => marker(x, p));
    G.forEach((g, gi) => {
      const t = el("text", { x: cx(gi), y: PB + 18, fill: "#aab4bf", "font-size": G.length > 6 ? 9 : 12, "text-anchor": "middle" }, g.label);
      if (G.length > 6) t.setAttribute("transform", `rotate(-25 ${cx(gi)} ${PB + 18})`);
    });
    // legend
    const ly = H - 14; let lx = X0;
    if (two) {
      D.levelsB.slice(0, 3).forEach((l, k) => {
        const g = "#8c97a3", cy = ly - 4, x = lx + 4;
        if (k === 0) el("circle", { cx: x, cy, r: 4, fill: "none", stroke: g, "stroke-width": 2.2 });
        else if (k === 1) el("circle", { cx: x, cy, r: 4.5, fill: g, stroke: "#fff", "stroke-width": 1 });
        else el("rect", { x: x - 4, y: cy - 4, width: 8, height: 8, fill: g, stroke: "#fff", "stroke-width": 1 });
        el("text", { x: lx + 13, y: ly, fill: g, "font-size": 11 }, lab(B, l)); lx += 22 + 7 * String(lab(B, l)).length; });
      el("text", { x: lx + 6, y: ly, fill: "#8c97a3", "font-size": 11 }, `colour = ${A.label || A.key}`);
    }
  }
  function niceTicks(a, b) {
    const span = b - a, step0 = Math.pow(10, Math.floor(Math.log10(span / 5))), m = span / 5 / step0;
    const step = step0 * (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10);
    const out = []; for (let t = Math.ceil(a / step) * step; t <= b; t += step) out.push(+t.toFixed(10));
    return out;
  }

  const CAPS = {
    start: "Start with 1 · Total.",
    total: "Total: every value's distance from the grand mean, squared and added up. One value is spoken for by the grand mean, so the rest are free.",
    a: () => `${stepName.a}: each group mean's distance from the grand mean (the blue bars), squared, counted once per value in the group, and added up.`,
    b: () => `${stepName.b}: each group mean's distance from the grand mean (the yellow bars), squared, counted once per value, and added up.`,
    ab: () => `Interaction: where each cell would sit if ${stepName.b} did the same for every ${stepName.a} (dashed line), and how far the real cell mean is from there (the orange bars).`,
    noise: "Noise: each value's distance from its own " + (two ? "cell" : "group") + " mean, the spread nothing in the model explains. Its variance is the yardstick for F.",
  };
  function show(s) {
    if (!steps.includes(s)) return;
    view = s; done.add(s);
    if (opts.onPegs) opts.onPegs([...done]);
    const next = steps.find(x => !done.has(x));
    steps.forEach(x => { btns[x].classList.toggle("on", x === view); btns[x].classList.toggle("next", x === next); });
    const c = CAPS[s]; cap.textContent = typeof c === "function" ? c() : c;
    drawPlot(); drawTable();
  }
  function start() {
    steps.forEach((x, i) => btns[x].classList.toggle("next", i === 0));
    cap.textContent = CAPS.start; drawPlot(); drawTable();
  }
  if (view === "start") start(); else show(view);
  if (P.start && steps.includes(P.start)) show(P.start);

  const api = { show, steps, table: () => D.rows.map(r => Object.assign({}, r)), done: () => [...done], ready: Promise.resolve() };
  root.anovaInstrument = api;
  return Object.assign({ destroy: () => { if (ro) ro.disconnect(); root.remove(); } }, api);
}

// ---- the WIDE layout (the default everywhere; params.layout "stacked" opts out) ----------------------------
// The original instrument's layout (temp/mobile_prototypes/anova_step5_fertiliser.html); Lucas, 2026-11-08: "that
// layout is critical". One wide drawing: the plot on the left, the table drawn beside it on the right, and an elbow
// arrow from each step's distances into the row they add up to. The cell steps (interaction and noise; one factor:
// noise) add a second plot to the right of the first. The table keeps the settled words (spread, free values, share).
// The book skin breaks out of the text column so the drawing is not shrunk to the column's width.
const WIDE_CSS = `
.anova-inst.wide{max-width:1700px}
.anova-inst .aw-row{position:relative;height:44px}
.anova-inst .aw-btns{position:absolute;top:0;display:grid;gap:6px;transform:translateX(-50%);margin:0}
.anova-inst .aw-btns button{padding:9px 0;font-size:13px}
.anova-inst .aw-scroll{overflow-x:auto} .anova-inst .aw-inner{min-width:900px}
.anova-inst.wide svg{background:none}
.anova-inst.wide.skin-book{width:min(96vw,1700px);max-width:none;position:relative;z-index:30;box-shadow:0 0 0 1px var(--line)}
`;
function mountWide(host, cfg, P, D, opts) {
  if (!document.getElementById("anova-inst-wide-css")) {
    const st = document.createElement("style"); st.id = "anova-inst-wide-css"; st.textContent = WIDE_CSS; document.head.appendChild(st);
  }
  const A = cfg.factors[0], B = cfg.factors[1] || null, two = !!B;
  const lab = (f, l) => (f.levelLabels && f.levelLabels[l]) || l;
  const nameA = A.label || A.key, nameB = two ? (B.label || B.key) : "", lowA = nameA.toLowerCase(), lowB = nameB.toLowerCase();
  const noun = cfg.noun || "values", one = noun.replace(/s$/, "");
  const LA = D.levelsA, LB = two ? D.levelsB : [], aIdx = l => LA.indexOf(l), bIdx = l => LB.indexOf(l);
  const steps = two ? ["total", "a", "b", "ab", "noise"] : ["total", "a", "noise"];
  const nLeft = two ? 3 : 2, unitWord = two ? "cell" : "group";
  const done = new Set(Array.isArray(opts.pegs) ? opts.pegs.filter(s => steps.includes(s)) : []);
  let view = done.size ? [...done].slice(-1)[0] : "start";

  const VW = 1990, VH = 800, X0 = 250, X1 = 550, PT = 12, PB = 624, DX = 520;
  const TX = 1310, TW = 650, SSX = TX + 185, DFX = TX + 275, VX = TX + 370, FX = TX + 445, PX = TX + 540, SHX = TX + 640;
  const root = document.createElement("div");
  root.className = "anova-inst wide skin-" + P.skin;
  const pc = x => (100 * x / VW).toFixed(2) + "%";
  root.innerHTML = `<h4></h4><p class="ai-sub"></p><div class="aw-scroll"><div class="aw-inner"><div class="aw-row">
    <div class="aw-btns ai-btns" style="left:${pc((X0 + X1) / 2)};width:${pc(two ? 330 : 230)};min-width:${two ? 250 : 170}px;grid-template-columns:repeat(${nLeft},1fr)"></div>
    <div class="aw-btns ai-btns" style="left:${pc(DX + (X0 + X1) / 2)};width:${pc(two ? 300 : 150)};min-width:${two ? 200 : 90}px;grid-template-columns:repeat(${steps.length - nLeft},1fr)"></div>
    </div><svg viewBox="0 0 ${VW} ${VH}" role="img"></svg></div></div>`;
  host.appendChild(root);
  // In the book the text column is too narrow for the drawing: centre it on the window instead, above the sidebars.
  const centre = () => {
    if (P.skin !== "book") return;
    root.style.marginLeft = "0px";
    const left = root.getBoundingClientRect().left, vw = document.documentElement.clientWidth;
    root.style.marginLeft = Math.round((vw - root.offsetWidth) / 2 - left) + "px";
  };
  centre(); addEventListener("resize", centre);
  root.querySelector("h4").textContent = cfg.title || "Analysis of variance";
  if (cfg.intro) {
    const intro = document.createElement("p"); intro.className = "ai-intro"; intro.textContent = cfg.intro;
    root.querySelector(".ai-sub").before(intro);
    if (cfg.credit) { const c = document.createElement("p"); c.className = "ai-credit"; c.textContent = cfg.credit; intro.after(c); }
  }
  root.querySelector(".ai-sub").textContent = cfg.subtitle ||
    `${D.N} measurements of ${cfg.response || "the response"}${cfg.unit ? " (" + cfg.unit + ")" : ""}. Press the numbered buttons in order to build the table.`;
  const svg = root.querySelector("svg");
  const stepName = { total: "Total", a: nameA, b: nameB, ab: "Interaction", noise: "Noise" };
  const boxes = root.querySelectorAll(".aw-btns"), btns = {};
  steps.forEach((s, i) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = `${i + 1} · ${stepName[s]}`;
    b.addEventListener("click", () => show(s));
    boxes[i < nLeft ? 0 : 1].appendChild(b); btns[s] = b;
  });

  // ---- data -------------------------------------------------------------------------------------------
  const ys = (cfg.rows || []).map(r => +r.y);
  const lo = Math.min(...ys), hi = Math.max(...ys);
  const span = (hi - lo) || 1, s0 = Math.pow(10, Math.floor(Math.log10(span / 6))), m0 = span / 6 / s0;
  const TICK = s0 * (m0 < 1.5 ? 1 : m0 < 3 ? 2 : m0 < 7 ? 5 : 10);
  const YMIN = Math.floor((lo - 0.06 * span) / TICK) * TICK, YMAX = Math.ceil((hi + 0.06 * span) / TICK) * TICK;
  const sy = v => PB - (v - YMIN) / (YMAX - YMIN) * (PB - PT);
  const f1 = x => x.toFixed(1);
  const pts = (cfg.rows || []).map(r => ({ y: +r.y, a: String(r[A.key]), b: two ? String(r[B.key]) : null }));
  let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const SHUF = pts.slice(); for (let i = SHUF.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [SHUF[i], SHUF[j]] = [SHUF[j], SHUF[i]]; }
  const meanA = l => mean(D.groupA.get(l)), meanB = l => two ? mean(D.groupB.get(l)) : D.grand;
  const cellM = (a, b) => two ? mean(D.groupCells.get(a + "\u0000" + b)) : meanA(a);
  const pred = (a, b) => meanA(a) + meanB(b) - D.grand;     // where the cell would sit if B acted the same everywhere
  const nA = Math.round(D.N / LA.length), nB = two ? Math.round(D.N / LB.length) : 0, nC = Math.round(D.N / D.cells);
  const CELLS = []; LA.forEach(a => (two ? LB : [null]).forEach(b => CELLS.push({ a, b })));
  const perA = two ? LB.length : 1;
  const YM = CELLS.map(c => sy((meanA(c.a) + pred(c.a, c.b)) / 2));
  const YMID = (Math.min(...YM) + Math.max(...YM)) / 2;
  const colA = l => PALETTE[aIdx(l) % PALETTE.length];

  // ---- drawing ----------------------------------------------------------------------------------------
  const NS = "http://www.w3.org/2000/svg";
  let cur = svg, ox = 0;
  const el = (n, a, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; cur.appendChild(e); return e; };
  const grp = tx => { const g = document.createElementNS(NS, "g"); if (tx) g.setAttribute("transform", `translate(${tx},0)`); svg.appendChild(g); return g; };
  function marker(x, p) {
    const col = colA(p.a), k = two ? bIdx(p.b) : 1, cy = sy(p.y);
    if (k === 0) return el("circle", { cx: x, cy, r: 4, stroke: col, "stroke-width": 2.2, style: "fill:var(--card)" });
    if (k === 1) return el("circle", { cx: x, cy, r: 4.5, fill: col, stroke: "#fff", "stroke-width": 1 });
    return el("rect", { x: x - 4, y: cy - 4, width: 8, height: 8, fill: col, stroke: "#fff", "stroke-width": 1 });
  }
  function layout(v) {
    if (v === "total" || v === "start") return { groups: [SHUF], labels: [`${D.N} ${noun}, no grouping`] };
    if (v === "a") return { groups: LA.map(l => pts.filter(p => p.a === l).sort((p, q) => bIdx(p.b) - bIdx(q.b))),
      labels: LA.map(l => lab(A, l)), cols: LA.map(colA), means: LA.map(meanA), bar: ROWCOL.a };
    if (v === "b") return { groups: LB.map(l => pts.filter(p => p.b === l).sort((p, q) => aIdx(p.a) - aIdx(q.a))),
      labels: LB.map(l => lab(B, l)), cols: LB.map(() => ROWCOL.b), means: LB.map(meanB), bar: ROWCOL.b };
    return { groups: CELLS.map(c => pts.filter(p => p.a === c.a && p.b === c.b)), labels: CELLS.map(c => two ? lab(B, c.b) : lab(A, c.a)), cell: true };
  }

  const ROWY = two ? { a: 124, b: 220, ab: 316, noise: 412, total: 540 } : { a: 124, noise: 220, total: 348 };
  const toTable = k => [TX - 12, ROWY[k] - 6];
  function arrowTo(fromX, fromY, col, label, toXabs, ty) {
    const ex = fromX + 26, tx = toXabs - ox, L = [].concat(label);
    el("path", { d: `M${fromX},${fromY} H${ex} V${ty} H${tx}`, fill: "none", stroke: col, "stroke-width": 2 });
    el("path", { d: `M${tx + 2},${ty} l-9,-5 v10 z`, fill: col });
    L.forEach((t, i) => el("text", { x: ex + 6, y: ty - 7 - (L.length - 1 - i) * 13, fill: col, "font-size": L.length > 1 ? 10.5 : 12 }, t));
  }
  const howText = k => {
    if (k === "a") return `${LA.length} means, 1 spoken for → ${LA.length - 1} free`;
    if (k === "b") return `${LB.length} means, 1 spoken for → ${LB.length - 1} free`;
    if (k === "ab") return `(${LA.length} − 1) × (${LB.length} − 1) = ${(LA.length - 1) * (LB.length - 1)}`;
    if (k === "noise") return `${D.N} ${noun} − ${D.cells} ${unitWord} means = ${D.N - D.cells}`;
    return `${D.N} − 1 spoken for (grand mean)`;
  };
  function drawTable() {
    const noiseDone = done.has("noise");
    el("rect", { x: TX - 10, y: 12, width: TW + 14, height: 660, rx: 10, style: "fill:var(--card)" });
    const H = (x, y, t, sz, c) => el("text", { x, y, fill: c, "font-size": sz, "text-anchor": "end" }, t);
    const head = (x, a, b, c) => { H(x, 34, a, 13, "#aab4bf"); H(x, 49, b, 13, "#aab4bf"); H(x, 64, c, 10.5, "#7b8693"); };
    head(SSX, "Sum of", "squares", "spread"); head(DFX, "Free", "values", "degrees of freedom");
    head(VX, "", "Variance", "spread ÷ free values"); head(SHX, "Share", "of the total", "spread ÷ total");
    if (noiseDone) { head(FX, "", "F", "÷ noise variance"); head(PX, "", "p", "noise alone"); }
    D.rows.forEach(r => {
      const k = r.key, y = ROWY[k], col = ROWCOL[k], shown = done.has(k), on = view === k;
      if (on) el("rect", { x: TX - 6, y: y - 22, width: TW + 6, height: 42, rx: 6, fill: col, "fill-opacity": .18, stroke: col, "stroke-opacity": .7 });
      el("line", { x1: TX - 6, x2: TX + TW, y1: y - 28, y2: y - 28, stroke: k === "total" ? "#8c97a3" : "#2f3a45" });
      el("text", { x: TX, y, fill: shown ? col : "#4a5561", "font-size": 15, "font-weight": on ? 700 : 500 }, r.label);
      if (!shown) return;
      const V = (x, t, sz) => el("text", { x, y, fill: col, "font-size": sz || 15, "font-weight": sz ? 400 : 700, "text-anchor": "end" }, t);
      V(SSX, fmt.ss(r.ss)); V(DFX, String(r.df));
      el("text", { x: TX, y: y + 14, fill: "#8c97a3", "font-size": 10.5 }, howText(k));
      if (r.variance != null) V(VX, fmt.v(r.variance));
      if (noiseDone && r.F != null) { V(FX, fmt.F(r.F)); V(PX, fmt.p(r.p)); }
      else if (noiseDone && k === "noise") V(PX, "the yardstick", 12);
      V(SHX, fmt.share(r.share)).setAttribute("class", "ai-share");
    });
    (two ? ["b", "ab", "noise"] : ["noise"]).forEach(k => {
      if (!done.has(k)) return;
      el("text", { x: SSX - 62, y: ROWY[k], fill: "#6b7683", "font-size": 14, "text-anchor": "end" }, "+");
      el("text", { x: DFX - 32, y: ROWY[k], fill: "#6b7683", "font-size": 14, "text-anchor": "end" }, "+");
    });
    const CAP = view === "noise" ? ["#4fd1c5", ["F = a row’s variance ÷ the noise variance.", "F near 1: no more spread than noise alone would give.",
        "Large F: that term explains real spread.", "p = how often noise alone would give an F this big."]]
      : (["a", "b", "ab"].includes(view) ? ["#aab4bf", ["Variance = spread ÷ free values,", "so terms with different free values can be compared."]]
      : (view === "total" ? ["#aab4bf", ["Share of the total = a row’s spread ÷ the total spread."]]
      : (view === "start" ? ["#aab4bf", [`Click the numbered buttons, 1 to ${steps.length}, to build the table.`]] : null)));
    if (CAP) CAP[1].forEach((t, i) => el("text", { x: TX, y: 600 + i * 20, fill: CAP[0], "font-size": 14, "font-weight": 700 }, t));
  }

  // o.arrow: "table" | "plot2" | "none";  o.note: the grand-mean note in the left margin;  o.cap: the caption below
  function drawPlot(v, o) {
    for (let t = YMIN; t <= YMAX + 1e-9; t += TICK) {
      const tt = +t.toFixed(10);
      el("line", { x1: X0, x2: X1, y1: sy(tt), y2: sy(tt), stroke: "#2a323b" });
      if (v === "start" || Math.abs(sy(tt) - sy(D.grand)) > 13) el("text", { x: X0 - 6, y: sy(tt) + 4, fill: "#8c97a3", "font-size": 12, "text-anchor": "end" }, String(tt));
    }
    const L = layout(v), G = L.groups.length, W = (X1 - X0) / G, GX = X1 + 56, half = W * 0.42, pos = [];
    L.groups.forEach((g, gi) => {
      const w = W * (G === 1 ? 0.96 : (L.cell ? 0.9 : 0.8)), x0 = X0 + W * gi + (W - w) / 2;
      g.forEach((p, i) => pos.push({ p, x: x0 + (i + 0.5) * w / g.length }));
    });
    const cxs = L.groups.map((_, gi) => X0 + W * gi + W / 2);
    const lowY = L.cell && two ? 14 : 0;     // the cell views carry a second label line, so everything below drops a line
    if (v === "start") {
      pos.forEach(q => marker(q.x, q.p));
      el("text", { x: cxs[0], y: PB + 22, fill: "#8c97a3", "font-size": 13, "text-anchor": "middle" }, L.labels[0]);
      el("text", { x: X0, y: PB + 76, fill: "#f0a24a", "font-size": 14, "font-weight": 700 }, "Start here: click 1 · Total.");
      return;
    }
    // connectors first, so they sit behind the dots
    if (L.means) {
      const col = L.bar, mids = L.means.map(m => sy((m + D.grand) / 2));
      if (o.arrow !== "none") {
        mids.forEach((y, i) => el("line", { x1: cxs[i] + 4, x2: GX, y1: y, y2: y, stroke: col, "stroke-width": 1.3, "stroke-dasharray": "2 4", "stroke-opacity": .8 }));
        const top = Math.min(...mids), bot = Math.max(...mids), mid = (top + bot) / 2;
        el("line", { x1: GX, x2: GX, y1: top, y2: bot, stroke: col, "stroke-width": 2 });
        if (v === "a") arrowTo(GX, mid, col, `Σ ${nA} × (blue line)²`, ...toTable("a"));
        else if (o.arrow === "plot2") arrowTo(GX, mid, col, LB.length === 2
          ? ["same shift of", `±${f1(Math.abs(meanB(LB[1]) - D.grand))} for every`, lowA] : ["same shift", "for every", lowA], DX + X0 - 92, YMID);
        else arrowTo(GX, mid, col, `Σ ${nB} × (yellow line)²`, ...toTable("b"));
      }
    } else if (L.cell && v === "ab") {
      if (!o.note) {
        YM.forEach((y, i) => el("line", { x1: X0 - 86, x2: cxs[i] - 7, y1: y, y2: y, stroke: ROWCOL.b, "stroke-width": 1.3, "stroke-dasharray": "2 4", "stroke-opacity": .8 }));
        el("line", { x1: X0 - 86, x2: X0 - 86, y1: Math.min(...YM), y2: Math.max(...YM), stroke: ROWCOL.b, "stroke-width": 2 });
      }
      const col = ROWCOL.ab, mids = CELLS.map(c => sy((pred(c.a, c.b) + cellM(c.a, c.b)) / 2));
      mids.forEach((y, i) => el("line", { x1: cxs[i] + 4, x2: GX, y1: y, y2: y, stroke: col, "stroke-width": 1.3, "stroke-dasharray": "2 4", "stroke-opacity": .8 }));
      const top = Math.min(...mids), bot = Math.max(...mids), mid = (top + bot) / 2;
      el("line", { x1: GX, x2: GX, y1: top, y2: bot, stroke: col, "stroke-width": 2 });
      arrowTo(GX, mid, col, `Σ ${nC} × (orange bar)²`, ...toTable("ab"));
    } else {
      const nz = v === "noise", tc = nz ? ROWCOL.noise : ROWCOL.total;
      const yy = pts.map(p => sy(p.y)), top = Math.min(...yy), bot = Math.max(...yy), mid = (top + bot) / 2;
      el("path", { d: `M${GX - 8},${top} H${GX} V${bot} H${GX - 8}`, fill: "none", stroke: tc, "stroke-width": 2, "stroke-dasharray": "4 4" });
      if (nz) arrowTo(GX, mid, tc, `Σ (to own ${unitWord} mean)²`, ...toTable("noise"));
      else arrowTo(GX, mid, tc, "Σ (all distances)²", ...toTable("total"));
    }

    el("line", { x1: X0, x2: X1, y1: sy(D.grand), y2: sy(D.grand), stroke: "#b7c0c9", "stroke-width": 1.5, "stroke-dasharray": "6 4" });
    el("text", { x: X0 - 6, y: sy(D.grand) + 4, fill: "#e8edf2", "font-size": 12, "text-anchor": "end" }, "grand " + f1(D.grand));

    if (L.means) {
      L.groups.forEach((_, gi) => {
        el("line", { x1: cxs[gi] - half, x2: cxs[gi] + half, y1: sy(L.means[gi]), y2: sy(L.means[gi]), stroke: L.cols[gi], "stroke-width": 3 });
        el("line", { x1: cxs[gi], x2: cxs[gi], y1: sy(L.means[gi]), y2: sy(D.grand), stroke: L.bar, "stroke-width": 5, "stroke-linecap": "round" });
      });
    } else if (L.cell) {
      if (v === "noise") pos.forEach(q => el("line", { x1: q.x, x2: q.x, y1: sy(q.p.y), y2: sy(cellM(q.p.a, q.p.b)), stroke: ROWCOL.noise, "stroke-width": 1.6, "stroke-dasharray": "3 2" }));
      if (v === "ab") LA.forEach((a, j) => {
        const first = cxs[j * perA], last = cxs[j * perA + perA - 1];
        el("line", { x1: first - half, x2: last + half, y1: sy(meanA(a)), y2: sy(meanA(a)), stroke: colA(a), "stroke-width": 1.6, "stroke-dasharray": "1 3" });
      });
      CELLS.forEach((c, gi) => {
        const cm = cellM(c.a, c.b), pr = pred(c.a, c.b);
        if (v === "ab") {
          el("line", { x1: cxs[gi] - 7, x2: cxs[gi] - 7, y1: sy(meanA(c.a)), y2: sy(pr), stroke: ROWCOL.b, "stroke-width": 4, "stroke-linecap": "round" });
          el("line", { x1: cxs[gi] - half, x2: cxs[gi] + half, y1: sy(pr), y2: sy(pr), stroke: "#e8edf2", "stroke-width": 2, "stroke-dasharray": "3 3" });
          el("line", { x1: cxs[gi], x2: cxs[gi], y1: sy(cm), y2: sy(pr), stroke: ROWCOL.ab, "stroke-width": 5, "stroke-linecap": "round" });
        }
        el("line", { x1: cxs[gi] - half, x2: cxs[gi] + half, y1: sy(cm), y2: sy(cm), stroke: colA(c.a), "stroke-width": 3 });
      });
    } else {
      pos.forEach(q => el("line", { x1: q.x, x2: q.x, y1: sy(q.p.y), y2: sy(D.grand), stroke: "#b7c0c9", "stroke-width": 1.3, "stroke-dasharray": "3 3" }));
    }
    pos.forEach(q => marker(q.x, q.p));

    L.groups.forEach((_, gi) => {
      const col = v === "a" ? L.cols[gi] : (v === "b" ? ROWCOL.b : (L.cell ? colA(CELLS[gi].a) : "#8c97a3"));
      el("text", { x: cxs[gi], y: PB + 22, fill: col, "font-size": L.cell ? 11 : 13, "text-anchor": "middle" }, L.labels[gi]);
    });
    if (L.cell && two) LA.forEach((a, j) => {
      const mid = (cxs[j * perA] + cxs[j * perA + perA - 1]) / 2;
      el("text", { x: mid, y: PB + 36, fill: colA(a), "font-size": 11, "font-weight": 700, "text-anchor": "middle" }, lab(A, a));
    });
    let lx = X0; const ly = PB + 48 + lowY;
    LB.slice(0, 3).forEach((l, k) => {
      const g = "#8c97a3", x = lx + 4, cy = ly - 4;
      if (k === 0) el("circle", { cx: x, cy, r: 4, stroke: g, "stroke-width": 2.2, style: "fill:var(--card)" });
      else if (k === 1) el("circle", { cx: x, cy, r: 4.5, fill: g, stroke: "#fff", "stroke-width": 1 });
      else el("rect", { x: x - 4, y: cy - 4, width: 8, height: 8, fill: g, stroke: "#fff", "stroke-width": 1 });
      el("text", { x: lx + 14, y: ly, fill: g, "font-size": 11 }, lab(B, l)); lx += 24 + 6.5 * String(lab(B, l)).length;
    });
    if (two) el("text", { x: lx + 6, y: ly, fill: "#8c97a3", "font-size": 11 }, `colour = ${lowA}`);
    const T = (y, t) => el("text", { x: X0, y: PB + y + lowY, fill: "#aab4bf", "font-size": 11 }, t);
    if (v === "ab" && !o.note) {
      T(64, `solid line = actual cell mean;  dotted = ${lowA} mean`);
      T(78, `yellow = the ${lowB} shift, the same for every ${lowA}`);
      T(92, `white dashes = ${lowA} mean + ${lowB} shift;  orange = actual minus white dashes`);
    }
    if (v === "noise" && !o.note) T(two ? 64 : 48, `teal dashes = how far each ${one} sits from the mean of its own ${unitWord}`);
    if (o.cap) {
      const C = { total: [ROWCOL.total, `Total = how far every ${one} sits from the grand mean,`, "squared and added up."],
                  a: [ROWCOL.a, `${nameA} = how much the ${lowA} averages differ`, "from the grand mean."],
                  b: [ROWCOL.b, `${nameB} = how much the ${lowB} averages differ`, "from the grand mean."],
                  ab: [ROWCOL.ab, `Interaction = how much each ${lowA}’s ${lowB} effect`, `differs from the average ${lowB} effect.`],
                  noise: [ROWCOL.noise, `Noise = how much ${noun} given exactly the same treatment`, "still differ from each other."] }[v];
      const y0 = (v === "ab" ? 120 : (v === "noise" ? (two ? 88 : 72) : (two ? 76 : 56))) + lowY;
      el("text", { x: X0, y: PB + y0, fill: C[0], "font-size": 14, "font-weight": 700 }, C[1]);
      el("text", { x: X0, y: PB + y0 + 18, fill: C[0], "font-size": 14, "font-weight": 700 }, C[2]);
    }
    if (o.note) ["The grand mean is fixed:", "all spread is measured", "from it, and it pins", "down one value, so",
                 `total free values: ${D.N - 1}, not ${D.N}.`].forEach((t, i) =>
      el("text", { x: X0 - 92, y: sy(D.grand) + 4 + (i - 2) * 16, fill: "#e8edf2", "font-size": 12, "text-anchor": "end" }, t));
  }

  function draw() {
    svg.innerHTML = "";
    const inP2 = view === "ab" || view === "noise";
    cur = grp(0); ox = 0;
    drawPlot(inP2 ? (two ? "b" : "a") : view, { arrow: !inP2 ? "table" : (view === "ab" ? "plot2" : "none"), note: true, cap: !inP2 });
    if (view === "noise") cur.setAttribute("opacity", .35);
    if (inP2) { cur = grp(DX); ox = DX; drawPlot(view, { arrow: "table", note: false, cap: true }); }
    cur = svg; ox = 0; drawTable();
    const nxt = steps.find(k => !done.has(k));
    steps.forEach(k => { btns[k].classList.toggle("on", k === view); btns[k].classList.toggle("next", k === nxt); });
  }
  function show(s) {
    if (!steps.includes(s)) return;
    view = s; done.add(s);
    if (opts.onPegs) opts.onPegs([...done]);
    draw();
  }
  draw();
  if (P.start && steps.includes(P.start)) show(P.start);

  const api = { show, steps, table: () => D.rows.map(r => Object.assign({}, r)), done: () => [...done], ready: Promise.resolve() };
  root.anovaInstrument = api;
  return Object.assign({ destroy: () => { removeEventListener("resize", centre); root.remove(); } }, api);
}

// Mount every <div class="anova-instrument" data-config="url"> on a page (the book's embeds).
export async function mountAll(doc = document) {
  for (const host of doc.querySelectorAll("div.anova-instrument[data-config]")) {
    if (host.dataset.mounted) continue; host.dataset.mounted = "1";
    try {
      const config = await (await fetch(host.dataset.config)).json();
      mountAnovaInstrument(host, { config, params: { skin: host.dataset.skin || "book", layout: host.dataset.layout } });
    } catch (e) { host.textContent = "The ANOVA instrument could not be loaded."; console.error(e); }
  }
}
