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
//   params = { skin: "book" | "board", start? }
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

// Mount every <div class="anova-instrument" data-config="url"> on a page (the book's embeds).
export async function mountAll(doc = document) {
  for (const host of doc.querySelectorAll("div.anova-instrument[data-config]")) {
    if (host.dataset.mounted) continue; host.dataset.mounted = "1";
    try {
      const config = await (await fetch(host.dataset.config)).json();
      mountAnovaInstrument(host, { config, params: { skin: host.dataset.skin || "book" } });
    } catch (e) { host.textContent = "The ANOVA instrument could not be loaded."; console.error(e); }
  }
}
