// Editing this? Read _agent_reference/instruments_and_widgets.md first (beside this file; local, gitignored).
// The PERMANOVA instrument (2026-11-17, session "anova"): the ANOVA instrument's table for a whole profile.
// Each sample is a point in a two-compound profile (two compounds keep it drawable; a real profile has
// hundreds and the same distances are measured across all of them). The table is built row by row as in
// shared/anova_instrument.js, each row drawn as the distances it adds up, then a last step shuffles the group
// labels to show where PERMANOVA's p comes from. Columns and rounding are the course's permanovaTest()
// (= anovaTest()'s): spread (sum of squares), free values, variance, F, p, share. Grown from the prototype
// temp/mobile_prototypes/permanova_instrument_draft.html, which Lucas approved.
//
//   mountPermanovaInstrument(host, { config, params? }) -> { destroy, show(step), steps, table() }
//   config = { title?, intro?, subtitle?, noun?, x: { key, label }, y: { key, label },
//              factors: [{ key, label?, levels?, levelLabels? }] (one or two), rows: [{ x, y, <factor key>: level }] }
//   params = { skin: "book" | "board", lessons?: bool (default true), advanced?: bool, seed? }
// Two factors assume a balanced design (equal samples per cell), where these sums of squares equal
// vegan::adonis2(by = "terms") with Euclidean distances in any term order.
// permanovaDecompose(config, labels?) is the pure arithmetic, tested by tests/permanova_instrument.test.mjs
// against R. It is READ, never graded: it holds no answer and never logs or gates anything.

const PALETTE = ["#e0709a", "#6fd08c", "#b08cf0", "#f2d14a", "#4aa8f0", "#f0a24a", "#4fd1c5", "#e8edf2"];
const ROWCOL = { a: "#4aa8f0", b: "#f2d14a", ab: "#f0a24a", noise: "#4fd1c5", total: "#b7c0c9" };

const center = ps => ({ x: ps.reduce((s, p) => s + p.x, 0) / ps.length, y: ps.reduce((s, p) => s + p.y, 0) / ps.length });
const d2 = (p, q) => (p.x - q.x) ** 2 + (p.y - q.y) ** 2;

// labels: optional [{ a, b }] per row (a shuffle); default the rows' own levels.
export function permanovaDecompose(config, labels) {
  const F = config.factors || [], A = F[0], B = F[1] || null;
  const pts = (config.rows || []).map((r, i) => ({ x: +r.x, y: +r.y,
    a: labels ? labels[i].a : String(r[A.key]), b: B ? (labels ? labels[i].b : String(r[B.key])) : null }));
  const lv = (f, k) => f.levels || [...new Set((config.rows || []).map(r => String(r[f.key])))];
  const LA = lv(A), LB = B ? lv(B) : [];
  const N = pts.length, grand = center(pts);
  const by = keyFn => { const m = new Map(); pts.forEach(p => { const k = keyFn(p); if (!m.has(k)) m.set(k, []); m.get(k).push(p); }); return m; };
  const gA = by(p => p.a), gB = B ? by(p => p.b) : null, gC = B ? by(p => p.a + "\u0000" + p.b) : gA;
  const cent = m => new Map([...m].map(([k, v]) => [k, center(v)]));
  const cA = cent(gA), cB = B ? cent(gB) : null, cC = cent(gC);
  const ssOf = (m, c) => [...m].reduce((s, [k, v]) => s + v.length * d2(c.get(k), grand), 0);
  const sst = pts.reduce((s, p) => s + d2(p, grand), 0);
  const ssa = ssOf(gA, cA), ssb = B ? ssOf(gB, cB) : 0, ssCells = ssOf(gC, cC);
  const cellKey = p => B ? p.a + "\u0000" + p.b : p.a;
  const ssn = pts.reduce((s, p) => s + d2(p, cC.get(cellKey(p))), 0);
  // the distance-only route (what lets PERMANOVA use any distance): sum of squared pairwise distances / n
  const pairSum = ps => { let t = 0; for (let i = 0; i < ps.length; i++) for (let j = i + 1; j < ps.length; j++) t += d2(ps[i], ps[j]); return t; };
  const pairTotal = pairSum(pts) / N;
  const pairNoise = [...gC.values()].reduce((s, g) => s + pairSum(g) / g.length, 0);
  const dfn = N - gC.size;
  const rows = [{ key: "a", term: A.key, label: A.label || A.key, ss: ssa, df: LA.length - 1 }];
  if (B) {
    rows.push({ key: "b", term: B.key, label: B.label || B.key, ss: ssb, df: LB.length - 1 });
    rows.push({ key: "ab", term: A.key + ":" + B.key, label: "Interaction", ss: ssCells - ssa - ssb, df: (LA.length - 1) * (LB.length - 1) });
  }
  rows.push({ key: "noise", term: "noise", label: "Noise", ss: ssn, df: dfn });
  rows.push({ key: "total", term: "total", label: "Total", ss: sst, df: N - 1 });
  const vNoise = ssn / dfn;
  rows.forEach(r => {
    r.share = r.ss / sst;
    if (r.key !== "total") r.variance = r.ss / r.df;
    if (r.key !== "total" && r.key !== "noise") r.F = r.variance / vNoise;
  });
  return { N, pts, grand, LA, LB, cA, cB, cC, gA, gB, gC, rows, pairTotal, pairNoise, cells: gC.size };
}

const sig4 = v => String(+v.toPrecision(4));
const fmtP = p => p < 0.001 ? "<0.001" : String(+p.toPrecision(2));

const CSS = `
.perm-inst{--bg:#14181d;--card:#1e242b;--ink:#e8edf2;--dim:#8c97a3;--line:#2d3640;--btn:#2b3540;--btnb:#3a4755;
  background:var(--bg);color:var(--ink);border-radius:12px;padding:12px;font:15px/1.45 -apple-system,system-ui,"Segoe UI",sans-serif;
  max-width:1100px;margin:1em auto;box-sizing:border-box}
.perm-inst.skin-board{--bg:#2a2118;--card:#3a2d20;--ink:#f3e6c8;--dim:#bfa982;--line:#5a4630;--btn:#4a3a28;--btnb:#7a6040;font-family:Georgia,"Times New Roman",serif}
.perm-inst h4{margin:0 0 4px;font-size:17px;color:var(--ink)} .perm-inst .pi-sub{color:var(--dim);font-size:13px;margin:0 0 8px}
.perm-inst .pi-intro{margin:4px 0 6px;font-size:14px}
.perm-inst .pi-btns{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 8px;align-items:center}
.perm-inst .pi-lab{color:var(--dim);font-size:12px;margin-right:2px}
.perm-inst button{background:var(--btn);color:var(--ink);border:1px solid var(--btnb);border-radius:8px;padding:7px 10px;font:inherit;font-size:14px;cursor:pointer}
.perm-inst button.on{background:#3b5b7a;border-color:#6aa6d8} .perm-inst button.next{border-color:#f0a24a;box-shadow:0 0 8px #f0a24a99}
.perm-inst button.small{font-size:12px;padding:5px 9px;color:var(--dim)} .perm-inst button[disabled]{opacity:.4;cursor:default}
.perm-inst .pi-q,.perm-inst .pi-lesson{background:var(--card);border-radius:10px;padding:8px 10px;margin:6px 0;font-size:14px}
.perm-inst .pi-q b,.perm-inst .pi-lesson b{display:block;color:var(--dim);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.perm-inst .pi-q.on{outline:1px solid #6aa6d8}
.perm-inst .pi-row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start}
.perm-inst .pi-plot{flex:1 1 440px;min-width:290px} .perm-inst .pi-tab{flex:1 1 400px;min-width:290px}
.perm-inst svg{width:100%;height:auto;display:block;background:var(--card);border-radius:10px}
.perm-inst table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:14px;margin:0;background:var(--card);border-radius:10px}
.perm-inst th{color:var(--dim);font-weight:500;font-size:12px;text-align:right;padding:6px 6px 4px;line-height:1.2;border:0}
.perm-inst th small{display:block;color:#7b8693;font-size:10.5px}
.perm-inst td{text-align:right;padding:6px;border-top:1px solid var(--line);font-weight:700}
.perm-inst th:first-child,.perm-inst td:first-child{text-align:left}
.perm-inst td small{display:block;font-weight:400;color:var(--dim);font-size:11px}
.perm-inst tr.hidden td{color:transparent!important} .perm-inst tr.hidden td:first-child{color:#4a5561!important} .perm-inst tr.hidden td small{color:transparent}
.perm-inst tr.active td{background:rgba(106,166,216,.14)}
.perm-inst.adv-off .adv{display:none}
.perm-inst .pi-cap{min-height:2.6em;font-size:14px;margin:8px 2px;font-weight:600}
.perm-inst .pi-shuf{background:var(--card);border-radius:10px;padding:8px;margin-top:10px}
.perm-inst .pi-tally{font-size:14px;margin:6px 2px}
`;

export function mountPermanovaInstrument(host, opts = {}) {
  const cfg = opts.config || {}, P = Object.assign({ skin: "book" }, opts.params || {});
  if (!document.getElementById("perm-inst-css")) { const st = document.createElement("style"); st.id = "perm-inst-css"; st.textContent = CSS; document.head.appendChild(st); }
  const A = cfg.factors[0], B = cfg.factors[1] || null, two = !!B;
  const lab = (f, l) => (f.levelLabels && f.levelLabels[l]) || l;
  const nameA = A.label || A.key, nameB = two ? (B.label || B.key) : "", lowA = nameA.toLowerCase(), lowB = nameB.toLowerCase();
  const noun = cfg.noun || "samples", one = noun.replace(/s$/, "");
  const D0 = permanovaDecompose(cfg);
  const LA = D0.LA, LB = D0.LB, N = D0.N;
  const steps = two ? ["total", "a", "b", "ab", "noise", "shuffle"] : ["total", "a", "noise", "shuffle"];
  const stepName = { total: "Total", a: nameA, b: nameB, ab: "Interaction", noise: "Noise", shuffle: "Shuffle the labels" };
  const terms = two ? ["a", "b", "ab"] : ["a"];
  let view = "start", adv = !!P.advanced, pairView = false, shuffled = null, histTerm = "a";
  const done = new Set(), nulls = { a: [], b: [], ab: [] };
  let seed = P.seed || 12345;
  const rnd = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

  const root = document.createElement("div");
  root.className = "perm-inst skin-" + P.skin + (adv ? "" : " adv-off");
  root.innerHTML = `<h4></h4><p class="pi-intro" hidden></p><p class="pi-sub"></p>
    <div class="pi-q"><b>The question</b><span class="pi-qt"></span></div>
    <div class="pi-lesson"><b>Lesson</b><span class="pi-lt"></span></div>
    <div class="pi-btns pi-steps"></div>
    <div class="pi-row">
      <div class="pi-plot"><svg class="pi-svg" viewBox="0 0 560 520" role="img" aria-label="scatter plot of the profiles"></svg>
        <div class="pi-btns" style="margin-top:6px"><span class="pi-lab">Measure spread:</span>
          <button type="button" class="pi-vc on">to the centers</button><button type="button" class="pi-vp">between every pair</button></div></div>
      <div class="pi-tab"><table></table>
        <div style="display:flex;justify-content:flex-end;margin-top:6px"><button type="button" class="small pi-adv"></button></div>
        <div class="pi-cap"></div>
        <div class="pi-shuf" hidden>
          <div class="pi-btns" style="margin:0 0 6px"><button type="button" class="pi-s1">Shuffle once</button>
            <button type="button" class="pi-s999">Shuffle 999 times</button><button type="button" class="pi-sr">Show the real labels</button>
            <button type="button" class="small pi-sc">Clear</button></div>
          <div class="pi-btns pi-ht" style="margin:0 0 6px"></div>
          <svg class="pi-hist" viewBox="0 0 460 210" role="img" aria-label="histogram of shuffled results"></svg>
          <div class="pi-tally"></div></div></div></div>`;
  host.appendChild(root);
  const $ = s => root.querySelector(s);
  $("h4").textContent = cfg.title || "Permutational analysis of variance (PERMANOVA)";
  if (cfg.intro) { $(".pi-intro").hidden = false; $(".pi-intro").textContent = cfg.intro; }
  $(".pi-sub").textContent = cfg.subtitle || `${N} ${noun}, each with a two-compound profile. Press the numbered buttons in order to build the table.`;
  $(".pi-qt").textContent = cfg.question || (two ? `How much of the variation in the profile do ${lowA}, ${lowB} and their interaction explain, and is each more than chance would give?`
                                                 : `How much of the variation in the profile does ${lowA} explain, and is that more than chance would give?`);
  if (P.lessons === false) { $(".pi-q").hidden = true; $(".pi-lesson").hidden = true; }

  const btn = {};
  steps.forEach((s, i) => { const b = document.createElement("button"); b.type = "button"; b.textContent = `${i + 1} · ${stepName[s]}`; b.onclick = () => show(s); $(".pi-steps").appendChild(b); btn[s] = b; });
  const htBtn = {};
  if (two) terms.forEach(k => { const b = document.createElement("button"); b.type = "button"; b.className = "small"; b.textContent = stepName[k];
    b.onclick = () => { histTerm = k; draw(); }; $(".pi-ht").appendChild(b); htBtn[k] = b; });

  // ---- scales -------------------------------------------------------------------------------------
  const PX0 = 62, PX1 = 540, PY0 = 18, PY1 = 430;
  const nice = (lo, hi) => { const span = (hi - lo) || 1, s0 = Math.pow(10, Math.floor(Math.log10(span / 6))), m = span / 6 / s0;
    const t = s0 * (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10); return [Math.floor((lo - 0.06 * span) / t) * t, Math.ceil((hi + 0.06 * span) / t) * t, t]; };
  const [XMIN, XMAX, XT] = nice(Math.min(...D0.pts.map(p => p.x)), Math.max(...D0.pts.map(p => p.x)));
  const [YMIN, YMAX, YT] = nice(Math.min(...D0.pts.map(p => p.y)), Math.max(...D0.pts.map(p => p.y)));
  const sx = v => PX0 + (v - XMIN) / (XMAX - XMIN) * (PX1 - PX0), sy = v => PY1 - (v - YMIN) / (YMAX - YMIN) * (PY1 - PY0);
  const colA = l => PALETTE[LA.indexOf(l) % PALETTE.length];
  const NS = "http://www.w3.org/2000/svg";
  const el = (par, n, a, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; par.appendChild(e); return e; };
  const cross = (par, c, col, size, w) => { el(par, "line", { x1: sx(c.x) - size, x2: sx(c.x) + size, y1: sy(c.y), y2: sy(c.y), stroke: col, "stroke-width": w });
    el(par, "line", { x1: sx(c.x), x2: sx(c.x), y1: sy(c.y) - size, y2: sy(c.y) + size, stroke: col, "stroke-width": w }); };
  const seg = (par, p, q, a) => el(par, "line", Object.assign({ x1: sx(p.x), y1: sy(p.y), x2: sx(q.x), y2: sy(q.y) }, a));
  function marker(par, p, col) {
    const k = two ? LB.indexOf(p.b) : 1, cx = sx(p.x), cy = sy(p.y);
    if (k === 0) return el(par, "circle", { cx, cy, r: 5, stroke: col, "stroke-width": 2.4, style: "fill:var(--card)" });
    if (k === 1) return el(par, "circle", { cx, cy, r: 5.5, fill: col, stroke: "#fff", "stroke-width": 1 });
    return el(par, "rect", { x: cx - 5, y: cy - 5, width: 10, height: 10, fill: col, stroke: "#fff", "stroke-width": 1 });
  }

  // ---- plot ---------------------------------------------------------------------------------------
  function drawPlot() {
    const svg = $(".pi-svg"); svg.innerHTML = "";
    for (let t = XMIN; t <= XMAX + 1e-9; t += XT) { el(svg, "line", { x1: sx(t), x2: sx(t), y1: PY0, y2: PY1, stroke: "#262e37" }); el(svg, "text", { x: sx(t), y: PY1 + 18, fill: "#8c97a3", "font-size": 12, "text-anchor": "middle" }, +t.toFixed(6)); }
    for (let t = YMIN; t <= YMAX + 1e-9; t += YT) { el(svg, "line", { x1: PX0, x2: PX1, y1: sy(t), y2: sy(t), stroke: "#262e37" }); el(svg, "text", { x: PX0 - 8, y: sy(t) + 4, fill: "#8c97a3", "font-size": 12, "text-anchor": "end" }, +t.toFixed(6)); }
    el(svg, "text", { x: (PX0 + PX1) / 2, y: PY1 + 40, fill: "#aab4bf", "font-size": 13, "text-anchor": "middle" }, (cfg.x && cfg.x.label) || "compound 1");
    el(svg, "text", { x: 16, y: (PY0 + PY1) / 2, fill: "#aab4bf", "font-size": 13, "text-anchor": "middle", transform: `rotate(-90 16 ${(PY0 + PY1) / 2})` }, (cfg.y && cfg.y.label) || "compound 2");
    const D = shuffled && view === "shuffle" ? permanovaDecompose(cfg, shuffled) : D0, pts = D.pts, g = el(svg, "g", {});
    const cellC = p => D.cC.get(two ? p.a + "\u0000" + p.b : p.a);
    const grouped = view !== "start" && view !== "total";
    if (view === "total") {
      if (pairView) { for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) seg(g, pts[i], pts[j], { stroke: ROWCOL.total, "stroke-width": .6, "stroke-opacity": .3 }); }
      else pts.forEach(p => seg(g, p, D.grand, { stroke: ROWCOL.total, "stroke-width": 1.3, "stroke-dasharray": "3 3" }));
    }
    if (view === "noise") {
      if (pairView) [...D.gC.values()].forEach(gr => { for (let i = 0; i < gr.length; i++) for (let j = i + 1; j < gr.length; j++) seg(g, gr[i], gr[j], { stroke: colA(gr[i].a), "stroke-width": 1.1, "stroke-opacity": .6 }); });
      else pts.forEach(p => seg(g, p, cellC(p), { stroke: ROWCOL.noise, "stroke-width": 1.6, "stroke-dasharray": "3 2" }));
    }
    if (view === "a" || (view === "shuffle" && (!two || histTerm === "a"))) D.cA.forEach(c => seg(g, c, D.grand, { stroke: ROWCOL.a, "stroke-width": 5, "stroke-linecap": "round", "stroke-opacity": .9 }));
    if (view === "b" || (view === "shuffle" && histTerm === "b")) D.cB.forEach(c => seg(g, c, D.grand, { stroke: ROWCOL.b, "stroke-width": 5, "stroke-linecap": "round", "stroke-opacity": .9 }));
    if (view === "ab" || (view === "shuffle" && histTerm === "ab")) {
      D.cC.forEach((c, k) => {
        const [a, b] = k.split("\u0000"), ca = D.cA.get(a), cb = D.cB.get(b);
        const pr = { x: ca.x + cb.x - D.grand.x, y: ca.y + cb.y - D.grand.y };
        seg(g, ca, pr, { stroke: ROWCOL.b, "stroke-width": 2, "stroke-dasharray": "4 3", "stroke-opacity": .8 });
        el(g, "circle", { cx: sx(pr.x), cy: sy(pr.y), r: 6, fill: "none", stroke: "#e8edf2", "stroke-width": 1.6, "stroke-dasharray": "2 2" });
        seg(g, pr, c, { stroke: ROWCOL.ab, "stroke-width": 5, "stroke-linecap": "round" });
      });
    }
    pts.forEach(p => marker(svg, p, grouped ? colA(p.a) : "#b7c0c9"));
    if (view === "a" || (view === "shuffle" && histTerm === "a")) D.cA.forEach((c, l) => cross(svg, c, colA(l), 9, 3.5));
    if (view === "b" || (view === "shuffle" && histTerm === "b")) D.cB.forEach(c => cross(svg, c, ROWCOL.b, 9, 3.5));
    if (view === "ab" || view === "noise" || (view === "shuffle" && histTerm === "ab")) D.cC.forEach((c, k) => cross(svg, c, colA(k.split("\u0000")[0]), 7, 2.6));
    if (view !== "start") { cross(svg, D.grand, "#ffffff", 11, 2.5); el(svg, "text", { x: sx(D.grand.x) + 12, y: sy(D.grand.y) - 10, fill: "#fff", "font-size": 12 }, "grand center"); }
    if (view === "b" || (view === "shuffle" && histTerm === "b")) D.cB.forEach((c, l) => el(svg, "text", { x: sx(c.x) + 10, y: sy(c.y) + 18, fill: ROWCOL.b, "font-size": 12 }, lab(B, l)));
    // legend
    let lx = PX0; const ly = PY1 + 66;
    if (grouped) LA.forEach(l => { el(svg, "circle", { cx: lx + 5, cy: ly - 4, r: 5, fill: colA(l) }); const t = `${nameA} ${lab(A, l)}`; el(svg, "text", { x: lx + 14, y: ly, fill: "#aab4bf", "font-size": 12 }, t); lx += 26 + 6.6 * t.length; });
    if (two) { lx = PX0; LB.forEach((l, k) => { marker(svg, { x: XMIN + (lx + 5 - PX0) / (PX1 - PX0) * (XMAX - XMIN), y: YMIN + (PY1 - (ly + 14)) / (PY1 - PY0) * (YMAX - YMIN), b: l }, "#8c97a3");
      el(svg, "text", { x: lx + 14, y: ly + 18, fill: "#aab4bf", "font-size": 12 }, lab(B, l)); lx += 30 + 6.6 * String(lab(B, l)).length; }); }
    const note = { a: "+ = each group's center", b: "+ = each group's center", noise: "+ = each cell's center",
                   ab: `dotted ring = ${lowA} center + the average ${lowB} shift;  orange = actual cell center minus the ring` }[view];
    if (note) el(svg, "text", { x: PX0, y: ly + (two ? 38 : 20), fill: "#8c97a3", "font-size": 11.5 }, note);
    if (view === "shuffle" && shuffled) el(svg, "text", { x: PX1, y: PY0 + 14, fill: "#f0a24a", "font-size": 13, "font-weight": 700, "text-anchor": "end" }, "labels shuffled at random");
  }

  // ---- table --------------------------------------------------------------------------------------
  const realStat = k => D0.rows.find(r => r.key === k).F;
  const pOf = k => { const real = realStat(k), n = nulls[k].length; return (nulls[k].filter(v => v >= real - 1e-9).length + 1) / (n + 1); };
  const howText = k => ({ a: `${LA.length} centers, 1 spoken for → ${LA.length - 1} free`, b: `${LB.length} centers, 1 spoken for → ${LB.length - 1} free`,
    ab: `(${LA.length} − 1) × (${LB.length} − 1) = ${(LA.length - 1) * (LB.length - 1)}`, noise: `${N} ${noun} − ${D0.cells} ${two ? "cell" : "group"} centers = ${N - D0.cells}`,
    total: `${N} − 1 spoken for (grand center)` })[k];
  function drawTable() {
    const t = $("table");
    t.innerHTML = `<tr><th></th><th>Sum of squares<small>spread</small></th><th class="adv">Free values<small>degrees of freedom</small></th>
      <th class="adv">Variance<small>spread ÷ free values</small></th><th class="adv">F<small>÷ noise variance</small></th>
      <th>p<small>from shuffles</small></th><th>Share<small>spread ÷ total</small></th></tr>`;
    D0.rows.forEach(r => {
      const tr = document.createElement("tr"), c = ROWCOL[r.key];
      tr.className = (done.has(r.key) ? "" : "hidden") + (view === r.key ? " active" : "");
      const Fc = r.F != null && done.has("noise") ? r.F.toFixed(2) : (r.key === "noise" && done.has("noise") ? "the yardstick" : "");
      const pc = r.F != null && nulls[r.key].length ? fmtP(pOf(r.key)) : "";
      tr.innerHTML = `<td style="color:${c}">${r.label}<small class="adv">${howText(r.key)}</small></td><td style="color:${c}">${sig4(r.ss)}</td>
        <td class="adv" style="color:${c}">${r.df}</td><td class="adv" style="color:${c}">${r.variance != null ? sig4(r.variance) : ""}</td>
        <td class="adv" style="color:${c}">${Fc}</td><td style="color:${c}">${pc}</td><td style="color:${c}">${r.share.toFixed(3)}</td>`;
      t.appendChild(tr);
    });
    const caps = {
      start: ["#aab4bf", `Click the numbered buttons, 1 to ${steps.length}, to build the table.`],
      total: [ROWCOL.total, pairView ? `Total = every squared distance between two ${noun}, added up and divided by ${N}: ${sig4(D0.pairTotal)}, the same number as measuring to the grand center.`
                                     : `Total = how far every ${one}'s profile sits from the grand center, squared and added up.`],
      a: [ROWCOL.a, `${nameA} = how far each ${lowA} center sits from the grand center, squared, once for every ${one} in the group.`],
      b: [ROWCOL.b, `${nameB} = how far each ${lowB} center sits from the grand center, squared, once for every ${one} in the group.`],
      ab: [ROWCOL.ab, `Interaction = how far each cell's center sits from where it would be if ${lowB} shifted every ${lowA} group the same way.`],
      noise: [ROWCOL.noise, pairView ? `Noise = squared distances between ${noun} in the same cell, added up and divided by the cell size: ${sig4(D0.pairNoise)}. No centers needed.`
                                     : `Noise = how far each ${one} sits from the center of its own ${two ? "cell" : "group"}: ${noun} treated alike still differ.`],
      shuffle: ["#f0a24a", "p = how often randomly shuffled labels make a row stand out from the noise at least as much as the real labels do."],
    };
    const c = caps[view]; $(".pi-cap").style.color = c[0]; $(".pi-cap").textContent = c[1];
  }

  // ---- shuffling ----------------------------------------------------------------------------------
  // Whole label sets move between samples (vegan's default free permutation); every term's F is recorded,
  // so one batch of shuffles gives every row its p, as adonis2(by = "terms") does.
  const realLabels = D0.pts.map(p => ({ a: p.a, b: p.b }));
  function shuffleOnce() {
    const l = realLabels.slice();
    for (let i = l.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [l[i], l[j]] = [l[j], l[i]]; }
    const D = permanovaDecompose(cfg, l);
    terms.forEach(k => nulls[k].push(D.rows.find(r => r.key === k).F));
    return l;
  }
  function drawHist() {
    const h = $(".pi-hist"); h.innerHTML = "";
    const k = histTerm, real = realStat(k), vals = nulls[k];
    const HX0 = 36, HX1 = 448, HY0 = 14, HY1 = 168;
    const cap = Math.max(4, ...vals.slice().sort((x, y) => x - y).slice(Math.floor(vals.length * 0.995)));
    // keep the shuffles readable: a real F far out in the tail is drawn at the edge with its value, not to scale
    const vmax = real <= cap * 3 ? Math.max(real, cap) * 1.08 : cap * 1.4, NB = 30, bw = vmax / NB, bins = new Array(NB).fill(0);
    vals.forEach(v => bins[Math.min(NB - 1, Math.floor(v / bw))]++);
    const top = Math.max(1, ...bins), hx = v => HX0 + Math.min(v, vmax) / vmax * (HX1 - HX0);
    bins.forEach((n, i) => { if (!n) return; const y = HY1 - n / top * (HY1 - HY0);
      el(h, "rect", { x: hx(i * bw) + .5, y, width: (HX1 - HX0) / NB - 1, height: HY1 - y, fill: (i + 1) * bw > real ? "#f0a24a" : "#5b6874" }); });
    el(h, "line", { x1: HX0, x2: HX1, y1: HY1, y2: HY1, stroke: "#8c97a3" });
    for (let i = 0; i <= 4; i++) { const v = vmax * i / 4; el(h, "text", { x: hx(v), y: HY1 + 16, fill: "#8c97a3", "font-size": 11, "text-anchor": "middle" }, v.toFixed(1)); }
    el(h, "text", { x: (HX0 + HX1) / 2, y: HY1 + 36, fill: "#aab4bf", "font-size": 12, "text-anchor": "middle" }, `${stepName[k].toLowerCase()} F from shuffled labels`);
    const off = real > vmax;
    el(h, "line", { x1: hx(real), x2: hx(real), y1: HY0 - 4, y2: HY1, stroke: ROWCOL[k], "stroke-width": 3 });
    el(h, "text", { x: hx(real) - 4, y: HY0 + 8, fill: ROWCOL[k], "font-size": 12, "font-weight": 700, "text-anchor": "end" }, off ? `real labels: F = ${real.toFixed(1)} →` : "real labels");
    if (shuffled) { const s = permanovaDecompose(cfg, shuffled).rows.find(r => r.key === k).F; el(h, "circle", { cx: hx(s), cy: HY1 - 6, r: 5, fill: "#fff" }); }
    const n = vals.length, beat = vals.filter(v => v >= real - 1e-9).length;
    $(".pi-tally").innerHTML = n
      ? `${n} shuffles; <b>${beat}</b> gave ${stepName[k].toLowerCase()} at least as large an F as the real labels. p = (${beat} + 1) ÷ (${n} + 1) = <b>${fmtP(pOf(k))}</b>` +
        (shuffled ? `<br>This shuffle: F = ${permanovaDecompose(cfg, shuffled).rows.find(r => r.key === k).F.toFixed(2)} (white dot).` : "")
      : `No shuffles yet. Each shuffle deals the ${N} sets of labels out to the ${noun} at random and recomputes the table.`;
    terms.forEach(t => htBtn[t] && htBtn[t].classList.toggle("on", t === k));
  }

  // ---- lessons ------------------------------------------------------------------------------------
  const L = Object.assign({
    start: "PERMANOVA splits the spread in a whole profile the way an ANOVA splits the spread in one measurement: a part for each factor, a part for their interaction, and the noise left over. Press 1 to begin.",
    total: `Read the total row first. Each ${one}'s profile is a point; the total spread is every ${one}'s squared distance from the grand center (the white cross), added up. Try 'between every pair': the sum of every squared ${one}-to-${one} distance, divided by the number of ${noun}, gives exactly the same number. That route needs only the distances, not the center, which is why PERMANOVA works with any distance, including Bray-Curtis on a real profile.`,
    a: `Each ${lowA} group's center is set against the grand center, once for every ${one} in the group. The row's share is how much of the total spread ${lowA} explains (the R2 column in adonis2's output).`,
    b: `The same for ${lowB}: each ${lowB} center against the grand center. Compare its share with ${lowA}'s to see which matters more for the profile.`,
    ab: `The interaction asks whether ${lowB} moves the profile of every ${lowA} group the same way. Each dotted ring is where a cell's center would be if it did: the ${lowA} center plus the average ${lowB} shift (yellow dashes). The orange bars are how far the real cell centers sit from the rings. Long bars mean the effect of ${lowB} depends on ${lowA}; read this row before the two factors' rows.`,
    noise: `Noise is the spread left inside each ${two ? "cell" : "group"}: ${noun} treated alike still differ. Every row above it, plus the noise, adds up to the total. F is a row's variance over the noise variance, as in an ANOVA.`,
    shuffle: `An ANOVA reads its p off the F distribution, which assumes normal data; chemical profiles rarely are. PERMANOVA asks the data instead: if a factor did nothing, its labels are arbitrary, and shuffled labels should make it stand out from the noise just as much. Shuffle 999 times and count how often a shuffle does at least as well${two ? "; switch rows with the buttons above the histogram" : ""}. One caution: PERMANOVA can also come out significant when one group is simply more spread out than the others, so check the spreads before calling it a shift.`,
  }, cfg.lessons || {});

  // ---- wiring -------------------------------------------------------------------------------------
  function draw() {
    drawPlot(); drawTable();
    const nxt = steps.find(k => !done.has(k));
    steps.forEach(k => { btn[k].classList.toggle("on", k === view); btn[k].classList.toggle("next", k === nxt); });
    $(".pi-lt").textContent = L[view] || "";
    $(".pi-shuf").hidden = view !== "shuffle";
    if (view === "shuffle") drawHist();
    const pairOK = view === "total" || view === "noise";
    $(".pi-vc").disabled = $(".pi-vp").disabled = !pairOK;
    $(".pi-adv").textContent = adv ? "Hide advanced stats" : "Show advanced stats";
  }
  function show(s) { if (!steps.includes(s)) return; view = s; done.add(s); if (s !== "shuffle") shuffled = null; draw(); }
  $(".pi-vc").onclick = () => { pairView = false; $(".pi-vc").classList.add("on"); $(".pi-vp").classList.remove("on"); draw(); };
  $(".pi-vp").onclick = () => { pairView = true; $(".pi-vp").classList.add("on"); $(".pi-vc").classList.remove("on"); draw(); };
  $(".pi-adv").onclick = () => { adv = !adv; root.classList.toggle("adv-off", !adv); draw(); };
  $(".pi-s1").onclick = () => { shuffled = shuffleOnce(); draw(); };
  $(".pi-s999").onclick = () => { for (let i = 0; i < 999; i++) shuffleOnce(); shuffled = null; draw(); };
  $(".pi-sr").onclick = () => { shuffled = null; draw(); };
  $(".pi-sc").onclick = () => { terms.forEach(k => { nulls[k] = []; }); shuffled = null; draw(); };
  draw();

  const api = { show, steps, table: () => D0.rows.map(r => Object.assign({}, r)), pValue: k => (nulls[k] && nulls[k].length ? pOf(k) : null) };
  root.permanovaInstrument = api;
  return Object.assign({ destroy: () => root.remove() }, api);
}

// Mount every <div class="permanova-instrument" data-config="url"> on a page (the book's embeds).
export async function mountAll(doc = document) {
  for (const host of doc.querySelectorAll("div.permanova-instrument[data-config]")) {
    if (host.dataset.mounted) continue; host.dataset.mounted = "1";
    try {
      const config = await (await fetch(host.dataset.config)).json();
      mountPermanovaInstrument(host, { config, params: { skin: host.dataset.skin || "book" } });
    } catch (e) { host.textContent = "The PERMANOVA instrument could not be loaded."; console.error(e); }
  }
}
