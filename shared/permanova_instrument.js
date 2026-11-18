// Editing this? Read _agent_reference/instruments_and_widgets.md first (beside this file; local, gitignored).
// The PERMANOVA instrument (2026-11-17, session "anova"): the ANOVA instrument's table for a whole profile.
// Each sample is a point in a two-compound profile (two compounds keep it drawable; a real profile has
// hundreds and the same distances are measured across all of them). The table is built row by row as in
// shared/anova_instrument.js, each row drawn as the distances it adds up, then a last step shuffles the group
// labels to show where PERMANOVA's p comes from. Columns and rounding are the course's permanovaTest()
// (= anovaTest()'s): spread (sum of squares), free values, variance, F, p, share. Grown from the prototype
// temp/mobile_prototypes/permanova_instrument_draft.html, which Lucas approved.
//
//   mountPermanovaInstrument(host, { config, params? }) -> { destroy, show(step), steps, table(), pValue(k) }
//   config = { title?, intro?, credit?, subtitle?, noun?, question?, questions?: [{ text, steps }], lessons?,
//              x: { key, label }, y: { key, label },
//              factors: [{ key, label?, levels?, levelLabels? }] (one or two), rows: [{ x, y, <factor key>: level }] }
//   params = { skin: "book" | "board", layout?: "stacked", lessons?: bool (default true), advanced?: bool, seed? }
// Layout: WIDE by default, like the ANOVA instrument's (Lucas 2026-11-17, "full width in the book, like the anova
// instrument"): the scatter on the left, the table drawn beside it on the right, an elbow arrow from each step's
// distances into its row, the shuffle histogram between them; the book skin breaks out of the text column.
// params.layout "stacked" (book: data-layout="stacked") keeps the first, plot-over-table layout.
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

// The Lesson box keeps one height whatever step is shown (Lucas, 2026-11-18): every lesson text sits invisibly in
// the same grid cell as the live one. A copy of anova_instrument.js's lessonStack (each file loads alone).
function lessonStack(liveP, texts) {
  const st = document.createElement("div"); st.className = "lstack";
  for (const t of texts) { if (!t) continue; const g = document.createElement("p"); g.className = "lghost"; g.setAttribute("aria-hidden", "true"); g.textContent = t; st.appendChild(g); }
  st.appendChild(liveP); return st;
}

// What both layouts share: names, steps, the shuffle engine (free permutations of whole label sets, vegan's
// default; every term's F is recorded, so one batch of shuffles gives every row its p, as adonis2(by = "terms")
// does), the lessons and the step captions.
function common(cfg, P) {
  const A = cfg.factors[0], B = cfg.factors[1] || null, two = !!B;
  const lab = (f, l) => (f.levelLabels && f.levelLabels[l]) || l;
  const nameA = A.label || A.key, nameB = two ? (B.label || B.key) : "", lowA = nameA.toLowerCase(), lowB = nameB.toLowerCase();
  const noun = cfg.noun || "samples", one = noun.replace(/s$/, "");
  const D0 = permanovaDecompose(cfg);
  const LA = D0.LA, LB = D0.LB, N = D0.N;
  const steps = two ? ["total", "a", "b", "ab", "noise", "shuffle"] : ["total", "a", "noise", "shuffle"];
  const stepName = { total: "Total", a: nameA, b: nameB, ab: "Interaction", noise: "Noise", shuffle: "Shuffle the labels" };
  const terms = two ? ["a", "b", "ab"] : ["a"];
  const nulls = { a: [], b: [], ab: [] };
  let seed = P.seed || 12345;
  const rnd = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const realStat = k => D0.rows.find(r => r.key === k).F;
  const pOf = k => { const real = realStat(k), n = nulls[k].length; return (nulls[k].filter(v => v >= real - 1e-9).length + 1) / (n + 1); };
  const realLabels = D0.pts.map(p => ({ a: p.a, b: p.b }));
  function shuffleOnce() {
    const l = realLabels.slice();
    for (let i = l.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [l[i], l[j]] = [l[j], l[i]]; }
    const D = permanovaDecompose(cfg, l);
    terms.forEach(k => nulls[k].push(D.rows.find(r => r.key === k).F));
    return l;
  }
  const howText = k => ({ a: `${LA.length} centers, 1 spoken for → ${LA.length - 1} free`, b: `${LB.length} centers, 1 spoken for → ${LB.length - 1} free`,
    ab: `(${LA.length} − 1) × (${LB.length} − 1) = ${(LA.length - 1) * (LB.length - 1)}`, noise: `${N} ${noun} − ${D0.cells} ${two ? "cell" : "group"} centers = ${N - D0.cells}`,
    total: `${N} − 1 spoken for (grand center)` })[k];
  const caps = (view, pairView) => ({
    start: ["#aab4bf", `Click the numbered buttons, 1 to ${steps.length}, to build the table.`],
    total: [ROWCOL.total, pairView ? `Total = every squared distance between two ${noun}, added up and divided by ${N}: ${sig4(D0.pairTotal)}, the same number as measuring to the grand center.`
                                   : `Total = how far every ${one}'s profile sits from the grand center, squared and added up.`],
    a: [ROWCOL.a, `${nameA} = how far each ${lowA} center sits from the grand center, squared, once for every ${one} in the group.`],
    b: [ROWCOL.b, `${nameB} = how far each ${lowB} center sits from the grand center, squared, once for every ${one} in the group.`],
    ab: [ROWCOL.ab, `Interaction = how far each cell's center sits from where it would be if ${lowB} shifted every ${lowA} group the same way.`],
    noise: [ROWCOL.noise, pairView ? `Noise = squared distances between ${noun} in the same cell, added up and divided by the cell size: ${sig4(D0.pairNoise)}. No centers needed.`
                                   : `Noise = how far each ${one} sits from the center of its own ${two ? "cell" : "group"}: ${noun} treated alike still differ.`],
    shuffle: ["#f0a24a", "p = how often randomly shuffled labels make a row stand out from the noise at least as much as the real labels do."],
  })[view];
  const L = Object.assign({
    start: "PERMANOVA splits the spread in a whole profile the way an ANOVA splits the spread in one measurement: a part for each factor, a part for their interaction, and the noise left over. Press 1 to begin.",
    total: `Read the total row first. Each ${one}'s profile is a point; the total spread is every ${one}'s squared distance from the grand center (the white cross), added up. Try 'between every pair': the sum of every squared ${one}-to-${one} distance, divided by the number of ${noun}, gives exactly the same number. That route needs only the distances, not the center, which is why PERMANOVA works with any distance, including Bray-Curtis on a real profile.`,
    a: `Each ${lowA} group's center is set against the grand center, once for every ${one} in the group. The row's share is how much of the total spread ${lowA} explains (the R2 column in adonis2's output).`,
    b: `The same for ${lowB}: each ${lowB} center against the grand center. Compare its share with ${lowA}'s to see which matters more for the profile.`,
    ab: `The interaction asks whether ${lowB} moves the profile of every ${lowA} group the same way. Each dotted ring is where a cell's center would be if it did: the ${lowA} center plus the average ${lowB} shift (yellow dashes). The orange bars are how far the real cell centers sit from the rings. Long bars mean the effect of ${lowB} depends on ${lowA}; read this row before the two factors' rows.`,
    noise: `Noise is the spread left inside each ${two ? "cell" : "group"}: ${noun} treated alike still differ. Every row above it, plus the noise, adds up to the total. F is a row's variance over the noise variance, as in an ANOVA.`,
    shuffle: `An ANOVA reads its p off the F distribution, which assumes normal data; chemical profiles rarely are. PERMANOVA asks the data instead: if a factor did nothing, its labels are arbitrary, and shuffled labels should make it stand out from the noise just as much. Shuffle 999 times and count how often a shuffle does at least as well${two ? "; switch rows with the buttons above the histogram" : ""}. One caution: PERMANOVA can also come out significant when one group is simply more spread out than the others, so check the spreads before calling it a shift.`,
  }, cfg.lessons || {});
  const question = cfg.question || (two ? `How much of the variation in the profile do ${lowA}, ${lowB} and their interaction explain, and is each more than chance would give?`
                                        : `How much of the variation in the profile does ${lowA} explain, and is that more than chance would give?`);
  return { A, B, two, lab, nameA, nameB, lowA, lowB, noun, one, D0, LA, LB, N, steps, stepName, terms, nulls, realStat, pOf,
           shuffleOnce, howText, caps, L, question };
}

export function mountPermanovaInstrument(host, opts = {}) {
  const cfg = opts.config || {}, P = Object.assign({ skin: "book" }, opts.params || {});
  if (!document.getElementById("perm-inst-css")) { const st = document.createElement("style"); st.id = "perm-inst-css"; st.textContent = CSS; document.head.appendChild(st); }
  const C = common(cfg, P);
  if (P.layout !== "stacked") return mountWide(host, cfg, P, C);
  const { A, B, two, lab, nameA, lowA, lowB, noun, D0, LA, LB, N, steps, stepName, terms, nulls, realStat, pOf, shuffleOnce, howText, L } = C;
  let view = "start", adv = !!P.advanced, pairView = false, shuffled = null, histTerm = "a";
  const done = new Set();

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
  $(".pi-qt").textContent = C.question;
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
    const c = C.caps(view, pairView); $(".pi-cap").style.color = c[0]; $(".pi-cap").textContent = c[1];
  }

  // ---- shuffling ----------------------------------------------------------------------------------
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

// ---- the WIDE layout (the default; params.layout "stacked" opts out) --------------------------------------
// The ANOVA instrument's wide layout carried over to a profile, so the two instruments in chapter 12b read as one
// family: one wide drawing with the scatter on the left, the table drawn on the right, an elbow arrow from each step's
// distances into the row they add up to, and (step "Shuffle the labels") the histogram of shuffled F values between
// the two. Same row colours, button rows, question and lesson boxes and advanced-stats toggle as the ANOVA board. On a
// phone the drawing keeps a minimum width and scrolls inside its own box, as the ANOVA one does.
const WIDE_CSS = `
.perm-inst.wide{max-width:1700px;font-size:15px;line-height:1.4}
.perm-inst.wide.skin-book{width:min(96vw,1700px);max-width:none;position:relative;z-index:30;box-shadow:0 0 0 1px var(--line)}
.perm-inst .pi-credit{margin:0 0 8px;font-size:12px;font-style:italic;color:var(--dim)}
.perm-inst .pw-scroll{overflow-x:auto} .perm-inst .pw-inner{min-width:900px}
.perm-inst.wide svg.pw-svg{background:none;border-radius:0}
.perm-inst .pw-row{display:grid;grid-template-columns:50% 1fr;gap:0 2%;align-items:start;margin:0 0 4px}
.perm-inst .pw-steps{display:grid;gap:6px;margin:0 3% 0 5%}
.perm-inst .pw-steps button{padding:9px 4px;font-size:13px;line-height:1.2}
.perm-inst .pw-right{display:grid;padding-left:1%}
.perm-inst .pw-right>.pw-ctl{grid-area:1/1;display:flex;flex-wrap:wrap;gap:6px;align-items:center;align-content:flex-start}
.perm-inst .pw-right>.pw-ctl.off{visibility:hidden}
.perm-inst .pw-ctl button{font-size:13px;padding:7px 10px}
.perm-inst .pw-ctl .pw-gap{width:14px}
.perm-inst .pi-qs{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 8px}
.perm-inst .pi-qq{flex:1 1 280px;border:1px solid var(--line);border-radius:8px;padding:6px 10px;color:var(--dim);font-size:15px;transition:all .2s}
.perm-inst .pi-qq b{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:600}
.perm-inst .pi-qq.on{color:var(--ink);border-color:#f0a24a;box-shadow:0 0 8px #f0a24a66;background:rgba(240,162,74,.10)}
.perm-inst .pw-lesson{border-left:3px solid #e2b468;padding:2px 0 4px 10px;margin:4px 0 10px;min-height:4.6em}
.perm-inst .pw-lesson b{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#e2b468}
.perm-inst .pw-lesson p{margin:3px 0 0;font-size:clamp(15px,1.15vw,19px);line-height:1.45}
.perm-inst .lstack{display:grid} .perm-inst .lstack>p{grid-area:1/1} .perm-inst .lstack>p.lghost{visibility:hidden}
.perm-inst .pw-adv-row{display:flex;justify-content:flex-end;margin:6px 0 0}
`;
// Greedy word wrap for svg text (no foreignObject): about `n` characters a line.
const wrap = (s, n) => String(s).split(" ").reduce((ls, w) => {
  if (ls.length && (ls[ls.length - 1] + " " + w).length <= n) ls[ls.length - 1] += " " + w; else ls.push(w); return ls; }, []);

function mountWide(host, cfg, P, C) {
  if (!document.getElementById("perm-inst-wide-css")) {
    const st = document.createElement("style"); st.id = "perm-inst-wide-css"; st.textContent = WIDE_CSS; document.head.appendChild(st);
  }
  const { A, B, two, lab, nameA, lowA, lowB, noun, one, D0, LA, LB, N, steps, stepName, terms, nulls, realStat, pOf, shuffleOnce, howText, L } = C;
  let view = "start", adv = !!P.advanced, pairView = false, shuffled = null, histTerm = "a";
  const done = new Set();

  const VW = 1990, VH = 990, X0 = 116, X1 = 980, PT = 20, PB = 760, GX = X1 + 34;
  const TX = 1310, TW = 650, HP = 664, HX0 = 1340, HX1 = 1680, HY0 = 730, HY1 = 900;
  const root = document.createElement("div");
  root.className = "perm-inst wide skin-" + P.skin;
  const cols = steps.length > 4 ? 3 : steps.length;
  root.innerHTML = `<h4></h4><p class="pi-sub"></p>
    <div class="pw-scroll"><div class="pw-inner"><div class="pw-row">
      <div class="pw-steps ai-btns" style="grid-template-columns:repeat(${cols},1fr)"></div>
      <div class="pw-right">
        <div class="pw-ctl pw-spread"><span class="pi-lab">Measure spread:</span>
          <button type="button" class="pi-vc on">to the centers</button><button type="button" class="pi-vp">between every pair</button></div>
        <div class="pw-ctl pw-shuf off"><button type="button" class="pi-s1">Shuffle once</button>
          <button type="button" class="pi-s999">Shuffle 999 times</button><button type="button" class="pi-sr">Show the real labels</button>
          <button type="button" class="small pi-sc">Clear</button><span class="pw-gap"></span><span class="pw-ht"></span></div>
      </div></div>
      <svg class="pw-svg" viewBox="0 0 ${VW} ${VH}" role="img" aria-label="scatter plot of the profiles beside the PERMANOVA table"></svg>
    </div></div>
    <div class="pw-adv-row"><button type="button" class="small pi-adv"></button></div>`;
  host.appendChild(root);
  const $ = s => root.querySelector(s);
  // In the book the text column is too narrow for the drawing: centre it on the window instead, above the sidebars.
  const centre = () => {
    if (P.skin !== "book") return;
    root.style.marginLeft = "0px";
    const left = root.getBoundingClientRect().left, vw = document.documentElement.clientWidth;
    root.style.marginLeft = Math.round((vw - root.offsetWidth) / 2 - left) + "px";
  };
  centre(); addEventListener("resize", centre);
  // No preamble in the wide layout (Lucas, 2026-11-18), as in anova_instrument.js; .pi-sub stays, hidden, as an anchor.
  $("h4").hidden = true; $(".pi-sub").hidden = true;
  let qEls = [], qs = [], lessonP = null;
  if (P.lessons !== false) {
    qs = cfg.questions || [{ text: C.question, steps: two ? ["a", "b", "ab", "shuffle"] : ["a", "shuffle"] }];
    const box = document.createElement("div"); box.className = "pi-qs";
    qEls = qs.map((q, i) => {
      const d = document.createElement("div"); d.className = "pi-qq";
      const h = document.createElement("b"); h.textContent = qs.length > 1 ? `Question ${i + 1}` : "The question";
      d.append(h, document.createTextNode(q.text)); box.appendChild(d); return d;
    });
    const ls = document.createElement("div"); ls.className = "pw-lesson";
    const lh = document.createElement("b"); lh.textContent = "Lesson"; lessonP = document.createElement("p");
    ls.append(lh, lessonStack(lessonP, Object.values(L)));
    $(".pi-sub").after(box, ls);
  }
  const btn = {};
  steps.forEach((s, i) => { const b = document.createElement("button"); b.type = "button"; b.textContent = `${i + 1} · ${stepName[s]}`;
    b.onclick = () => show(s); $(".pw-steps").appendChild(b); btn[s] = b; });
  const htBtn = {};
  if (two) {
    const t = document.createElement("span"); t.className = "pi-lab"; t.textContent = "Histogram:"; $(".pw-ht").before(t);
    terms.forEach(k => { const b = document.createElement("button"); b.type = "button"; b.className = "small"; b.textContent = stepName[k];
      b.onclick = () => { histTerm = k; draw(); }; $(".pw-ht").before(b); htBtn[k] = b; });
  }

  // ---- scales -----------------------------------------------------------------------------------------
  const nice = (lo, hi) => { const span = (hi - lo) || 1, s0 = Math.pow(10, Math.floor(Math.log10(span / 6))), m = span / 6 / s0;
    const t = s0 * (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10); return [Math.floor((lo - 0.06 * span) / t) * t, Math.ceil((hi + 0.06 * span) / t) * t, t]; };
  const [XMIN, XMAX, XT] = nice(Math.min(...D0.pts.map(p => p.x)), Math.max(...D0.pts.map(p => p.x)));
  const [YMIN, YMAX, YT] = nice(Math.min(...D0.pts.map(p => p.y)), Math.max(...D0.pts.map(p => p.y)));
  const sx = v => X0 + (v - XMIN) / (XMAX - XMIN) * (X1 - X0), sy = v => PB - (v - YMIN) / (YMAX - YMIN) * (PB - PT);
  const tick = v => String(+v.toFixed(6));
  const colA = l => PALETTE[LA.indexOf(l) % PALETTE.length];
  const NS = "http://www.w3.org/2000/svg", svg = $(".pw-svg");
  const el = (n, a, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; svg.appendChild(e); return e; };
  const seg = (p, q, a) => el("line", Object.assign({ x1: sx(p.x), y1: sy(p.y), x2: sx(q.x), y2: sy(q.y) }, a));
  const cross = (c, col, size, w) => { el("line", { x1: sx(c.x) - size, x2: sx(c.x) + size, y1: sy(c.y), y2: sy(c.y), stroke: col, "stroke-width": w });
    el("line", { x1: sx(c.x), x2: sx(c.x), y1: sy(c.y) - size, y2: sy(c.y) + size, stroke: col, "stroke-width": w }); };
  // marker shape = the second factor's level (open circle, filled circle, square), as on the ANOVA board
  const shape = (cx, cy, k, col) => {
    if (k === 0) return el("circle", { cx, cy, r: 6.5, stroke: col, "stroke-width": 2.6, style: "fill:var(--card)" });
    if (k === 1) return el("circle", { cx, cy, r: 7, fill: col, stroke: "#fff", "stroke-width": 1.2 });
    return el("rect", { x: cx - 6.5, y: cy - 6.5, width: 13, height: 13, fill: col, stroke: "#fff", "stroke-width": 1.2 });
  };
  const marker = (p, col) => shape(sx(p.x), sy(p.y), two ? LB.indexOf(p.b) : 1, col);
  const ROWY = two ? { a: 124, b: 220, ab: 316, noise: 412, total: 540 } : { a: 124, noise: 220, total: 348 };
  function arrowTo(fromX, fromY, col, label, k) {
    const ex = fromX + 26, tx = TX - 12, ty = ROWY[k] - 6, Ls = [].concat(label || []);
    el("path", { d: `M${fromX},${fromY} H${ex} V${ty} H${tx}`, fill: "none", stroke: col, "stroke-width": 2, class: "pw-arrow" });
    el("path", { d: `M${tx + 2},${ty} l-9,-5 v10 z`, fill: col });
    Ls.forEach((t, i) => el("text", { x: ex + 6, y: ty - 8 - (Ls.length - 1 - i) * 16, fill: col, "font-size": 15 }, t));
  }
  // dashed leaders from each drawn distance's midpoint to a bracket at GX, then one arrow into the row (ANOVA board style)
  function gather(mids, col, label, k) {
    mids.forEach(m => el("line", { x1: m.x + 6, x2: GX, y1: m.y, y2: m.y, stroke: col, "stroke-width": 1.3, "stroke-dasharray": "2 4", "stroke-opacity": .7 }));
    const top = Math.min(...mids.map(m => m.y)), bot = Math.max(...mids.map(m => m.y));
    el("line", { x1: GX, x2: GX, y1: top, y2: bot, stroke: col, "stroke-width": 2 });
    arrowTo(GX, (top + bot) / 2, col, label, k);
  }
  const midOf = (p, q) => ({ x: (sx(p.x) + sx(q.x)) / 2, y: (sy(p.y) + sy(q.y)) / 2 });

  // ---- the plot ---------------------------------------------------------------------------------------
  function drawPlot() {
    for (let t = XMIN; t <= XMAX + 1e-9; t += XT) { el("line", { x1: sx(t), x2: sx(t), y1: PT, y2: PB, stroke: "#2a323b" });
      el("text", { x: sx(t), y: PB + 24, fill: "#8c97a3", "font-size": 15, "text-anchor": "middle" }, tick(t)); }
    for (let t = YMIN; t <= YMAX + 1e-9; t += YT) { el("line", { x1: X0, x2: X1, y1: sy(t), y2: sy(t), stroke: "#2a323b" });
      el("text", { x: X0 - 10, y: sy(t) + 5, fill: "#8c97a3", "font-size": 15, "text-anchor": "end" }, tick(t)); }
    el("text", { x: (X0 + X1) / 2, y: PB + 52, fill: "#aab4bf", "font-size": 16, "text-anchor": "middle" }, (cfg.x && cfg.x.label) || "compound 1");
    el("text", { x: 36, y: (PT + PB) / 2, fill: "#aab4bf", "font-size": 16, "text-anchor": "middle", transform: `rotate(-90 36 ${(PT + PB) / 2})` }, (cfg.y && cfg.y.label) || "compound 2");
    const D = shuffled && view === "shuffle" ? permanovaDecompose(cfg, shuffled) : D0, pts = D.pts;
    const cellC = p => D.cC.get(two ? p.a + "\u0000" + p.b : p.a);
    const grouped = view !== "start" && view !== "total";
    const hT = view === "shuffle" ? (two ? histTerm : "a") : null;
    const nA = Math.round(N / LA.length), nB = two ? Math.round(N / LB.length) : 0, nC = Math.round(N / D0.cells);
    // distances and connectors first, so they sit behind the points
    if (view === "total" || view === "noise") {
      const nz = view === "noise", col = nz ? ROWCOL.noise : ROWCOL.total;
      if (pairView) {
        if (nz) [...D.gC.values()].forEach(gr => { for (let i = 0; i < gr.length; i++) for (let j = i + 1; j < gr.length; j++) seg(gr[i], gr[j], { stroke: colA(gr[i].a), "stroke-width": 1.4, "stroke-opacity": .6 }); });
        else for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) seg(pts[i], pts[j], { stroke: ROWCOL.total, "stroke-width": .8, "stroke-opacity": .28 });
      } else if (nz) pts.forEach(p => seg(p, cellC(p), { stroke: ROWCOL.noise, "stroke-width": 2, "stroke-dasharray": "4 3" }));
      else pts.forEach(p => seg(p, D.grand, { stroke: ROWCOL.total, "stroke-width": 1.6, "stroke-dasharray": "4 4" }));
      const yy = pts.map(p => sy(p.y)), top = Math.min(...yy), bot = Math.max(...yy);
      el("path", { d: `M${GX - 10},${top} H${GX} V${bot} H${GX - 10}`, fill: "none", stroke: col, "stroke-width": 2, "stroke-dasharray": "4 4" });
      arrowTo(GX, (top + bot) / 2, col, nz ? (pairView ? [`Σ (pairs in a ${two ? "cell" : "group"})²`, `÷ ${two ? "cell" : "group"} size`] : `Σ (to own ${two ? "cell" : "group"} center)²`)
                                           : (pairView ? `Σ (every pair)² ÷ ${N}` : "Σ (all distances)²"), view);
    }
    if (view === "a" || hT === "a") {
      D.cA.forEach(c => seg(c, D.grand, { stroke: ROWCOL.a, "stroke-width": 6, "stroke-linecap": "round", "stroke-opacity": .9 }));
      if (view === "a") gather([...D.cA.values()].map(c => midOf(c, D.grand)), ROWCOL.a, `Σ ${nA} × (blue line)²`, "a");
    }
    if (view === "b" || hT === "b") {
      D.cB.forEach(c => seg(c, D.grand, { stroke: ROWCOL.b, "stroke-width": 6, "stroke-linecap": "round", "stroke-opacity": .9 }));
      if (view === "b") gather([...D.cB.values()].map(c => midOf(c, D.grand)), ROWCOL.b, `Σ ${nB} × (yellow line)²`, "b");
    }
    if (view === "ab" || hT === "ab") {
      const mids = [];
      D.cC.forEach((c, k) => {
        const [a, b] = k.split("\u0000"), ca = D.cA.get(a), cb = D.cB.get(b);
        const pr = { x: ca.x + cb.x - D.grand.x, y: ca.y + cb.y - D.grand.y };
        seg(ca, pr, { stroke: ROWCOL.b, "stroke-width": 2.6, "stroke-dasharray": "5 4", "stroke-opacity": .85 });
        el("circle", { cx: sx(pr.x), cy: sy(pr.y), r: 9, fill: "none", stroke: "#e8edf2", "stroke-width": 2, "stroke-dasharray": "3 3" });
        seg(pr, c, { stroke: ROWCOL.ab, "stroke-width": 6, "stroke-linecap": "round" });
        mids.push(midOf(pr, c));
      });
      if (view === "ab") gather(mids, ROWCOL.ab, `Σ ${nC} × (orange bar)²`, "ab");
    }
    pts.forEach(p => marker(p, grouped ? colA(p.a) : "#b7c0c9"));
    if (view === "a" || hT === "a") D.cA.forEach((c, l) => cross(c, colA(l), 14, 4.5));
    if (view === "b" || hT === "b") D.cB.forEach(c => cross(c, ROWCOL.b, 14, 4.5));
    if (view === "ab" || view === "noise" || hT === "ab") D.cC.forEach((c, k) => cross(c, colA(k.split("\u0000")[0]), 11, 3.4));
    if (view !== "start") { cross(D.grand, "#ffffff", 16, 3.2); el("text", { x: sx(D.grand.x) + 16, y: sy(D.grand.y) - 12, fill: "#fff", "font-size": 14 }, "grand center"); }
    if (view === "b" || hT === "b") D.cB.forEach((c, l) => el("text", { x: sx(c.x) + 14, y: sy(c.y) + 24, fill: ROWCOL.b, "font-size": 14 }, lab(B, l)));
    if (view === "shuffle" && shuffled) el("text", { x: X1, y: PT + 18, fill: "#f0a24a", "font-size": 15, "font-weight": 700, "text-anchor": "end" }, "labels shuffled at random");
    // legend: colour = the first factor, shape = the second
    let lx = X0, ly = PB + 84;
    if (grouped) { LA.forEach(l => { el("circle", { cx: lx + 6, cy: ly - 5, r: 6.5, fill: colA(l) }); const t = `${nameA} ${lab(A, l)}`;
      el("text", { x: lx + 18, y: ly, fill: "#aab4bf", "font-size": 15 }, t); lx += 36 + 8.2 * t.length; }); ly += 24; }
    if (two) { lx = X0; LB.forEach((l, k) => { shape(lx + 6, ly - 5, k, "#8c97a3"); el("text", { x: lx + 18, y: ly, fill: "#aab4bf", "font-size": 15 }, lab(B, l));
      lx += 38 + 8.2 * String(lab(B, l)).length; }); ly += 24; }
    const note = { a: "+ = each group's center", b: "+ = each group's center", noise: `+ = each ${two ? "cell" : "group"}'s center`,
                   ab: `dotted ring = ${lowA} center + the average ${lowB} shift;  orange = actual cell center minus the ring` }[hT || view];
    if (note) { el("text", { x: X0, y: ly, fill: "#8c97a3", "font-size": 14 }, note); ly += 24; }
    if (view === "start") { el("text", { x: X0, y: ly + 8, fill: "#f0a24a", "font-size": 15, "font-weight": 700 }, "Start here: click 1 · Total."); return; }
    const c = C.caps(view, pairView);
    wrap(c[1], 82).forEach((t, i) => el("text", { x: X0, y: ly + 8 + i * 21, fill: c[0], "font-size": 16, "font-weight": 700, class: "pw-cap" }, t));
  }

  // ---- the table (drawn in the svg, columns as anova's wide board) ------------------------------------
  function drawTable() {
    const noiseDone = done.has("noise");
    const [SSX, DFX, VX, FX, PX, SHX] = adv ? [TX + 185, TX + 275, TX + 370, TX + 445, TX + 540, TX + 640]
                                            : [TX + 260, 0, 0, 0, TX + 450, TX + 640];
    el("rect", { x: TX - 10, y: 12, width: TW + 14, height: HP - 24, rx: 10, style: "fill:var(--card)" });
    const H = (x, y, t, sz, c) => el("text", { x, y, fill: c, "font-size": sz, "text-anchor": "end" }, t);
    // the small gloss goes on two lines when the advanced columns crowd the header
    const head = (x, a, b, c) => { H(x, 30, a, 13, "#aab4bf"); H(x, 45, b, 13, "#aab4bf");
      [].concat(c).forEach((t, i) => H(x, 60 + 12 * i, t, 10.5, "#7b8693")); };
    head(SSX, "Sum of", "squares", "spread");
    if (adv) { head(DFX, "Free", "values", ["degrees", "of freedom"]); head(VX, "", "Variance", ["spread ÷", "free values"]); head(FX, "", "F", ["÷ noise", "variance"]); }
    head(PX, "", "p", adv ? ["from", "shuffles"] : "from shuffles");
    head(SHX, "Share", "of the total", adv ? ["spread ÷", "total"] : "spread ÷ total");
    D0.rows.forEach(r => {
      const k = r.key, y = ROWY[k], col = ROWCOL[k], shown = done.has(k), on = view === k || (view === "shuffle" && k === (two ? histTerm : "a"));
      if (on) el("rect", { x: TX - 6, y: y - 22, width: TW + 6, height: 42, rx: 6, fill: col, "fill-opacity": .18, stroke: col, "stroke-opacity": .7 });
      el("line", { x1: TX - 6, x2: TX + TW, y1: y - 28, y2: y - 28, stroke: k === "total" ? "#8c97a3" : "#2f3a45" });
      el("text", { x: TX, y, fill: shown ? col : "#4a5561", "font-size": 15, "font-weight": on ? 700 : 500 }, r.label);
      if (!shown) return;
      const V = (x, t, sz) => el("text", { x, y, fill: col, "font-size": sz || 15, "font-weight": sz ? 400 : 700, "text-anchor": "end" }, t);
      V(SSX, sig4(r.ss));
      if (adv) {
        V(DFX, String(r.df));
        el("text", { x: TX, y: y + 14, fill: "#8c97a3", "font-size": 10.5 }, howText(k));
        if (r.variance != null) V(VX, sig4(r.variance));
        if (noiseDone && r.F != null) V(FX, r.F.toFixed(2));
        else if (noiseDone && k === "noise") el("text", { x: FX, y: y + 14, fill: col, "font-size": 11, "text-anchor": "end" }, "the yardstick");
      }
      if (r.F != null && nulls[k].length) V(PX, fmtP(pOf(k))).setAttribute("class", "pi-p");
      V(SHX, r.share.toFixed(3)).setAttribute("class", "pi-share");
    });
    (two ? ["b", "ab", "noise"] : ["noise"]).forEach(k => {
      if (!done.has(k)) return;
      el("text", { x: SSX - 62, y: ROWY[k], fill: "#6b7683", "font-size": 14, "text-anchor": "end" }, "+");
      if (adv) el("text", { x: DFX - 32, y: ROWY[k], fill: "#6b7683", "font-size": 14, "text-anchor": "end" }, "+");
    });
    const last = steps.length;
    const CAP = view === "noise" ? ["#4fd1c5", adv ? ["F = a row’s variance ÷ the noise variance.", `p comes from shuffling the labels: press ${last}.`]
                                                   : [`p comes from shuffling the labels: press ${last}.`]]
      : view === "shuffle" ? ["#f0a24a", ["p = (shuffles at least as large + 1) ÷ (shuffles + 1)."]]
      : view === "total" ? ["#aab4bf", ["Share of the total = a row’s spread ÷ the total spread."]]
      : view === "start" ? ["#aab4bf", [`Click the numbered buttons, 1 to ${last}, to build the table.`]]
      : (adv ? ["#aab4bf", ["Variance = spread ÷ free values,", "so terms with different free values can be compared."]] : null);
    if (CAP) CAP[1].forEach((t, i) => el("text", { x: TX, y: 588 + i * 20, fill: CAP[0], "font-size": 14, "font-weight": 700 }, t));
  }

  // ---- the shuffle histogram, in a panel under the table, with an elbow arrow up into the row it gives p for ----
  function drawHist() {
    const k = two ? histTerm : "a", real = realStat(k), vals = nulls[k], col = ROWCOL[k];
    el("rect", { x: TX - 10, y: HP, width: TW + 14, height: VH - HP - 6, rx: 10, style: "fill:var(--card)" });
    el("text", { x: TX + 6, y: HP + 34, fill: "#aab4bf", "font-size": 15, "font-weight": 700 }, `${stepName[k]}: F from shuffled labels`);
    const cap = Math.max(4, ...vals.slice().sort((x, y) => x - y).slice(Math.floor(vals.length * 0.995)));
    // keep the shuffles readable: a real F far out in the tail is drawn at the edge with its value, not to scale
    const vmax = real <= cap * 3 ? Math.max(real, cap) * 1.08 : cap * 1.4, NB = 30, bw = vmax / NB, bins = new Array(NB).fill(0);
    vals.forEach(v => bins[Math.min(NB - 1, Math.floor(v / bw))]++);
    const top = Math.max(1, ...bins), hx = v => HX0 + Math.min(v, vmax) / vmax * (HX1 - HX0);
    bins.forEach((n, i) => { if (!n) return; const y = HY1 - n / top * (HY1 - HY0);
      el("rect", { x: hx(i * bw) + .5, y, width: (HX1 - HX0) / NB - 1, height: HY1 - y, fill: (i + 1) * bw > real ? "#f0a24a" : "#5b6874" }); });
    el("line", { x1: HX0, x2: HX1, y1: HY1, y2: HY1, stroke: "#8c97a3" });
    for (let i = 0; i <= 4; i++) { const v = vmax * i / 4; el("text", { x: hx(v), y: HY1 + 20, fill: "#8c97a3", "font-size": 13, "text-anchor": "middle" }, v.toFixed(1)); }
    el("text", { x: (HX0 + HX1) / 2, y: HY1 + 42, fill: "#aab4bf", "font-size": 13, "text-anchor": "middle" }, "F");
    const off = real > vmax;
    el("line", { x1: hx(real), x2: hx(real), y1: HY0 - 6, y2: HY1, stroke: col, "stroke-width": 3.5 });
    el("text", { x: hx(real) - 6, y: HY0 + 8, fill: col, "font-size": 14, "font-weight": 700, "text-anchor": "end" }, off ? `real labels: F = ${real.toFixed(1)} →` : "real labels");
    let sF = null;
    if (shuffled) { sF = permanovaDecompose(cfg, shuffled).rows.find(r => r.key === k).F; el("circle", { cx: hx(sF), cy: HY1 - 8, r: 7, fill: "#fff" }); }
    const n = vals.length, beat = vals.filter(v => v >= real - 1e-9).length;
    const lines = n ? [...wrap(`${n} shuffles; ${beat} gave ${stepName[k].toLowerCase()} at least as large an F as the real labels.`, 30),
                       `p = (${beat} + 1) ÷ (${n} + 1)`, `   = ${fmtP(pOf(k))}`, ...(sF != null ? wrap(`This shuffle: F = ${sF.toFixed(2)} (white dot).`, 30) : [])]
                    : wrap(`No shuffles yet. Each shuffle deals the ${N} sets of labels out to the ${noun} at random and recomputes the table.`, 30);
    lines.forEach((t, i) => { const pl = /^p =|^ *=/.test(t);
      el("text", { x: HX1 + 34, y: HY0 + 4 + i * 20, fill: pl ? "#f0a24a" : "#e8edf2", "font-size": 14, "font-weight": pl ? 700 : 400, class: "pw-tally", "xml:space": "preserve" }, t); });
    // the elbow: out of the panel's left edge, up, and into the row's p
    if (n) {
      const y0 = (HY0 + HY1) / 2, ty = ROWY[k] - 6, ex = TX - 34;
      el("path", { d: `M${TX - 10},${y0} H${ex} V${ty} H${TX - 12}`, fill: "none", stroke: col, "stroke-width": 2, class: "pw-arrow" });
      el("path", { d: `M${TX - 10},${ty} l-9,-5 v10 z`, fill: col });
    }
    terms.forEach(t => htBtn[t] && htBtn[t].classList.toggle("on", t === k));
  }

  // ---- wiring -----------------------------------------------------------------------------------------
  function draw() {
    svg.innerHTML = "";
    drawPlot(); drawTable();
    if (view === "shuffle") drawHist();
    const nxt = steps.find(k => !done.has(k));
    steps.forEach(k => { btn[k].classList.toggle("on", k === view); btn[k].classList.toggle("next", k === nxt); });
    if (lessonP) { lessonP.textContent = L[view] || ""; qs.forEach((q, i) => qEls[i].classList.toggle("on", (q.steps || []).includes(view))); }
    $(".pw-shuf").classList.toggle("off", view !== "shuffle");
    $(".pw-spread").classList.toggle("off", view === "shuffle");
    $(".pi-vc").disabled = $(".pi-vp").disabled = !(view === "total" || view === "noise");
    $(".pi-adv").textContent = adv ? "Hide advanced stats" : "Show advanced stats";
    $(".pi-adv").setAttribute("aria-pressed", String(adv));
  }
  function show(s) { if (!steps.includes(s)) return; view = s; done.add(s); if (s !== "shuffle") shuffled = null; draw(); }
  $(".pi-vc").onclick = () => { pairView = false; $(".pi-vc").classList.add("on"); $(".pi-vp").classList.remove("on"); draw(); };
  $(".pi-vp").onclick = () => { pairView = true; $(".pi-vp").classList.add("on"); $(".pi-vc").classList.remove("on"); draw(); };
  $(".pi-adv").onclick = () => { adv = !adv; draw(); };
  $(".pi-s1").onclick = () => { shuffled = shuffleOnce(); draw(); };
  $(".pi-s999").onclick = () => { for (let i = 0; i < 999; i++) shuffleOnce(); shuffled = null; draw(); };
  $(".pi-sr").onclick = () => { shuffled = null; draw(); };
  $(".pi-sc").onclick = () => { terms.forEach(k => { nulls[k] = []; }); shuffled = null; draw(); };
  draw();

  const api = { show, steps, table: () => D0.rows.map(r => Object.assign({}, r)), pValue: k => (nulls[k] && nulls[k].length ? pOf(k) : null), done: () => [...done] };
  root.permanovaInstrument = api;
  return Object.assign({ destroy: () => { removeEventListener("resize", centre); root.remove(); } }, api);
}

// Mount every <div class="permanova-instrument" data-config="url"> on a page (the book's embeds).
export async function mountAll(doc = document) {
  for (const host of doc.querySelectorAll("div.permanova-instrument[data-config]")) {
    if (host.dataset.mounted) continue; host.dataset.mounted = "1";
    try {
      const config = await (await fetch(host.dataset.config)).json();
      mountPermanovaInstrument(host, { config, params: { skin: host.dataset.skin || "book", layout: host.dataset.layout } });
    } catch (e) { host.textContent = "The PERMANOVA instrument could not be loaded."; console.error(e); }
  }
}
