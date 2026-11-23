// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `sigmoid_board` kind).
// The S-curve board: an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"sigmoid_board"`), built 2026-11-19 for
// the classification home world (classification/watch, day one: the volcano station's wall). Lucas demos it on the
// projector on day one; students return to it at home. One tab per day-one section of the chapter, each with only its
// own controls and a Lesson in the book's wording:
//
//   1 From numbers to categories   yes/no dots at 0 and 1 against one reading, a straight line through them running
//                                  below 0 and past 1 (shaded "not a probability"); a draggable reader on the line;
//                                  "Compare the S-curve" lays the logistic fit over it.
//   2 A model from one predictor   the S-curve: drag its MIDDLE (where the probability is 0.5) and its STEEPNESS
//                                  (handle where it reaches 0.8), or "Best fit" (the maximum-likelihood fit, what
//                                  buildModel() finds); a switch draws the likelihood calculation on the plot.
//   3 Setting cases aside          one staged walk: the S-curve alone, held-back mornings hidden → the connect-the-dots
//                                  model (a curve through every training morning; the other curve stays faint) → reveal
//                                  the ten held-back mornings at what happened → score them: a dotted line from each to
//                                  the chosen curve, a draggable cut-off, and a ✓/✗ on each by its call at that cut-off.
//                                  Red rings mark wrong calls; no table or readout, the plot carries the score
//                                  (at 0.5: 24/30 → 9/10 vs 30/30 → 7/10, scores() for tests).
//
// TOY DATA ONLY (classification_math.js LANDING: forty invented mornings, swell height vs did the supply boat turn
// back). Never graded, never logged, holds no answer. Code-drawn SVG: no art, no
// geometry (validate_assets.py NO_GEOMETRY_KINDS).
//
//   const b = mount(hostEl, { pegs?, onPegs?(state) });
//   b.setTab("lines"|"curve"|"holdout"); b.setModel("s"|"dots"); b.setReveal(on); b.setScoring(on); b.scores(); b.marks(); b.tab(); b.curve(); b.setCurve({middle, steepness}); b.bestFit({instant});
//   b.best(); b.probability(day); b.setCutoff(c); b.cutoff();
//   b.setProbe(x); b.lineAt(x); b.ready; b.destroy().   The root element carries the API as `.sigmoidBoard` for tests.
import { LANDING, olsLine, fitLogistic, curveFromCoef, probAt, fitScore, callAt, connectDotsAt } from "./classification_math.js?v=181";
import { shell, svgEl, el, button, slider, svgPoint, fmt2 } from "./classification_ui.js?v=181";

const TABS = [["lines", "From numbers to categories"], ["curve", "A model from one predictor"], ["holdout", "Setting cases aside"]];
// Each tab's takeaway in the chapter's own wording (12d_classification.Rmd), and the section it belongs to.
const LESSONS = {
  lines: ["A model that predicts a category is a classification model. A straight line fitted to turned_back coded as 1 and 0 predicts a number, not a category: at 2.3 m it reads 0.45, but is that \"probably not\", or a 45% chance the boat turns back? It’s a bit unclear. Even worse, at the ends the straight line reads below 0 and above 1, which is impossible to interpret. The solution: logistic regression, which is built to give a probability instead: an S-shape that stays between 0 and 1, so a reading of 0.43 means a 43% chance the boat turns back on a morning with that swell.",
    "from numbers to categories"],
  curve: ["A logistic regression model gives each case a probability_yes: the chance that the response is yes at that predictor value. On a morning with a 2.3 m swell, 0.43 means a 43% chance the boat turns back. It is not the share of all mornings that turned back, and it is not a call. The fit is scored by likelihood: each morning gets the probability the curve gives to what actually happened, those are multiplied together, and the best fit is the curve with the highest likelihood.",
    "a model from one predictor"],
  holdout: ["A model always performs the best on the data used to set it up. Here, a connect-the-dots curve (an “overfitted” model) passes through every training morning and gets all 30 right, but it has memorized the noise: on the ten held-back mornings it does worse than the S-curve. So always hold back some data (a “test set”), train the model on the rest (the “training set”), and evaluate the model on the test set. To score held-back data, a cut-off (a threshold) is used to turn a probability_yes into a call: yes at or above the cut-off, no below it. predictWithModel() uses 0.5. Moving the cut-off changes the calls, never the probabilities: a lower cut-off calls more mornings yes, catching more boats that turn back, but at the price of more false alarms.",
    "a model from one predictor; several predictors, and predicting held-back cases"],
};
const W = 960, H = 600, PX0 = 100, PX1 = 930, PY0 = 74, PY1 = 524;
const YES = "#ffc861", NO = "#8fb3d9", LINE = "#ff8a5c", CURVE = "#7fd3ff", CUT = "#ffe39a", BAD = "rgba(255,90,70,.13)";
// the curve's two handles: kept clear of the yes (amber) and no (blue) dots and of the curve itself (cyan)
const MID = "#e58cff", STEEP = "#7ee0a1";
const LN4 = Math.log(4);       // the steepness handle sits where the curve reaches 0.8: logit(0.8) = ln 4
const START = { middle: 4.1, steepness: 0.8 };   // deliberately off the dots, so "Best fit" has something to do

export function mount(host, opts = {}) {
  const T = LANDING;
  const xs = T.training.map((d) => d.x), ys = T.training.map((d) => d.y), X1 = xs.map((x) => [x]);
  const line = olsLine(xs, ys);
  const best = curveFromCoef(fitLogistic(X1, ys));
  const s0 = opts.pegs && typeof opts.pegs === "object" ? opts.pegs : {};
  const st = {
    tab: s0.tab === "cutoff" ? "holdout" : TABS.some(([k]) => k === s0.tab) ? s0.tab : "lines",   // "cutoff" was merged into holdout
    curve: s0.curve && Number.isFinite(s0.curve.middle) && Number.isFinite(s0.curve.steepness) ? { ...s0.curve } : { ...START },
    cutoff: Number.isFinite(s0.cutoff) ? s0.cutoff : 0.5,
    probe: Number.isFinite(s0.probe) ? s0.probe : 5.5,
    showS: !!s0.showS,
    showFit: !!s0.showFit,
    model: s0.model === "dots" ? "dots" : "s",
    reveal: !!s0.reveal,
    dotsSeen: !!s0.dotsSeen || s0.model === "dots",   // the connect-the-dots curve stays off the plot until first chosen
    scoring: !!s0.scoring && !!s0.reveal,
  };
  const reduced = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  let dead = false, raf = 0, drag = null;
  const save = () => opts.onPegs && opts.onPegs({ tab: st.tab, curve: { ...st.curve }, cutoff: st.cutoff, probe: st.probe, showS: st.showS, showFit: st.showFit, model: st.model, reveal: st.reveal, dotsSeen: st.dotsSeen, scoring: st.scoring });

  const F = shell(host, { cls: "sigmoidboard", tabs: TABS, W, H, onTab: (k) => api.setTab(k),
    ariaLabel: "The S-curve board: yes/no mornings against swell height, a straight line, an S-curve and a cut-off" });
  const svg = F.svg;

  // ---------- scales ----------
  const yRange = () => (st.tab === "lines" ? [-0.42, 1.56] : [-0.07, 1.1]);
  const X = (v) => PX0 + ((v - T.xView[0]) / (T.xView[1] - T.xView[0])) * (PX1 - PX0);
  const Y = (p) => { const [a, b] = yRange(); return PY1 - ((p - a) / (b - a)) * (PY1 - PY0); };
  const invX = (px) => T.xView[0] + ((px - PX0) / (PX1 - PX0)) * (T.xView[1] - T.xView[0]);
  const invY = (py) => { const [a, b] = yRange(); return a + ((PY1 - py) / (PY1 - PY0)) * (b - a); };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lineAt = (x) => line.intercept + line.slope * x;

  // ---------- drawing ----------
  function txt(x, y, s, o = {}) {
    return svgEl(svg, "text", { x, y, fill: o.fill || "#f3e6c4", "font-size": o.size || 20, "text-anchor": o.anchor || "start",
      "font-style": o.italic ? "italic" : null, "font-weight": o.bold ? "bold" : null, "dominant-baseline": "middle", opacity: o.opacity }, s);
  }
  function axes() {
    const [a, b] = yRange();
    svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: PY1 - PY0, fill: "rgba(255,255,255,.025)", stroke: "rgba(255,255,255,.18)" });
    for (let v = T.xView[0]; v <= T.xView[1]; v++) {
      svgEl(svg, "line", { x1: X(v), x2: X(v), y1: PY1, y2: PY1 + 8, stroke: "rgba(255,255,255,.6)" });
      txt(X(v), PY1 + 24, String(v), { anchor: "middle", size: 19 });
    }
    txt((PX0 + PX1) / 2, PY1 + 56, T.label + "  ·  " + T.predictor, { anchor: "middle", size: 21 });
    const step = 0.25;
    for (let v = Math.ceil(a / step) * step; v <= b + 1e-9; v += step) {
      const major = Math.abs(v) < 1e-9 || Math.abs(v - 1) < 1e-9 || Math.abs(v - 0.5) < 1e-9;
      svgEl(svg, "line", { x1: PX0 - 8, x2: PX0, y1: Y(v), y2: Y(v), stroke: "rgba(255,255,255,.6)" });
      if (major || st.tab === "lines") txt(PX0 - 14, Y(v), (Math.round(v * 100) / 100).toString(), { anchor: "end", size: major ? 19 : 15, opacity: major ? 1 : 0.7 });
    }
    const yl = st.tab === "lines" ? "turned_back coded as a number (yes = 1, no = 0)" : "probability_yes (the boat turns back)";
    const t = txt(0, 0, yl, { anchor: "middle", size: 19 });
    t.setAttribute("transform", `translate(${PX0 - 62} ${(PY0 + PY1) / 2}) rotate(-90)`);
    // what the dots are: one sentence of scene-setting
    txt(PX0 - 40, 12, "Each dot is one morning on the island: the height of the swell (the waves),", { size: 16, italic: true, fill: "#cdbf9f" });
    txt(PX0 - 40, 31, "and whether the island's supply boat turned back or landed.", { size: 16, italic: true, fill: "#cdbf9f" });
    // legend
    const lx = PX0, ly = 54;
    svgEl(svg, "circle", { cx: lx + 8, cy: ly, r: 8, fill: YES });
    txt(lx + 22, ly, "turned back: yes", { size: 17 });
    svgEl(svg, "circle", { cx: lx + 190, cy: ly, r: 8, fill: NO });
    txt(lx + 204, ly, "turned back: no (landed)", { size: 17 });
    if (st.tab === "holdout" && st.reveal) {
      svgEl(svg, "path", { d: diamond(lx + 452, ly, 9), fill: "#fff1d6" });
      txt(lx + 466, ly, "held back (never shown to the model)", { size: 17 });
    }
  }
  const diamond = (x, y, r) => `M${x} ${y - r}L${x + r} ${y}L${x} ${y + r}L${x - r} ${y}Z`;
  function dots(alpha = 1) {
    for (const d of T.training)
      svgEl(svg, "circle", { cx: X(d.x), cy: Y(d.y), r: 9, fill: d.y ? YES : NO, opacity: alpha, stroke: "rgba(0,0,0,.5)", "stroke-width": 1, class: "dot", "data-day": d.day });
  }
  function curvePath(cv, attrs) {
    const pts = [];
    for (let i = 0; i <= 240; i++) { const x = T.xView[0] + (i / 240) * (T.xView[1] - T.xView[0]); pts.push(`${i ? "L" : "M"}${X(x).toFixed(1)} ${Y(probAt(cv, x)).toFixed(1)}`); }
    return svgEl(svg, "path", { d: pts.join(""), fill: "none", stroke: CURVE, "stroke-width": 4, "stroke-linecap": "round", ...attrs });
  }
  // A grab handle: a 13 px knob with a 28 px hit ring. `side` puts the label below ("below") or below-right ("right",
  // clear of a curve that rises to the right).
  function handle(cx, cy, kind, label, color, side = "below") {
    svgEl(svg, "circle", { cx, cy, r: 13, fill: color, stroke: "#1a1208", "stroke-width": 2.5 });
    if (label && side === "right") txt(cx + 20, cy + 22, label, { size: 18, bold: true, fill: color });
    else if (label) txt(cx, cy + 30, label, { anchor: "middle", size: 17, bold: true, fill: color });
    const h = svgEl(svg, "circle", { cx, cy, r: 28, fill: "transparent", class: "hit handle-" + kind });
    h.addEventListener("pointerdown", (ev) => startDrag(ev, kind));
    return h;
  }

  function drawLines() {
    const y0 = Y(0), y1 = Y(1);
    svgEl(svg, "rect", { x: PX0, y: y0, width: PX1 - PX0, height: PY1 - y0, fill: BAD });
    svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: y1 - PY0, fill: BAD });
    // the line climbs left to right, so each band's words sit on the side the line is not
    txt(PX1 - 12, (y0 + PY1) / 2, "below 0: not a probability", { anchor: "end", size: 19, italic: true, fill: "#ffb3a0" });
    txt(PX0 + 12, (PY0 + y1) / 2, "above 1: not a probability", { anchor: "start", size: 19, italic: true, fill: "#ffb3a0" });
    for (const v of [0, 1]) svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(v), y2: Y(v), stroke: "rgba(255,255,255,.45)", "stroke-dasharray": "8 6" });
    dots();
    if (st.showS) curvePath(best, { opacity: 0.95, class: "scurve" });
    // the straight line: amber inside 0..1, red where it leaves
    const xa = T.xView[0], xb = T.xView[1], c0 = -line.intercept / line.slope, c1 = (1 - line.intercept) / line.slope;
    const seg = (u, v, col, w) => svgEl(svg, "line", { x1: X(u), y1: Y(lineAt(u)), x2: X(v), y2: Y(lineAt(v)), stroke: col, "stroke-width": w, "stroke-linecap": "round", class: "straight" });
    seg(xa, c0, "#ff4d3a", 6); seg(c0, c1, LINE, 5); seg(c1, xb, "#ff4d3a", 6);
    // the reader on the line
    const px = X(st.probe), v = lineAt(st.probe), out = v < 0 || v > 1;
    svgEl(svg, "line", { x1: px, x2: px, y1: PY0, y2: PY1, stroke: CUT, "stroke-width": 2, "stroke-dasharray": "5 5" });
    svgEl(svg, "circle", { cx: px, cy: Y(v), r: 8, fill: out ? "#ff4d3a" : LINE, stroke: "#fff", "stroke-width": 2 });
    // the reading, on a dark tag kept off the rows of dots at 0 and 1
    const lab = `line at ${st.probe.toFixed(1)} m: ${fmtSigned(v)}`;
    const left = px > (PX0 + PX1) / 2, ly = Y(Math.abs(v) < 0.18 ? 0.25 : Math.abs(v - 1) < 0.18 ? 0.75 : v) + (Math.abs(v) < 0.18 || Math.abs(v - 1) < 0.18 ? 0 : -30);
    const tw = 12 + lab.length * 10.5, tx = left ? px - 14 - tw : px + 14;
    svgEl(svg, "rect", { x: tx, y: ly - 18, width: tw, height: 36, rx: 6, fill: "rgba(8,17,26,.92)", stroke: out ? "#ff4d3a" : LINE });
    txt(tx + tw / 2, ly, lab, { anchor: "middle", size: 20, bold: true, fill: out ? "#ffb3a0" : "#fff1d6" });
    // with the S-curve shown, the reader also marks the curve, its tag on the other side of the reader line
    if (st.showS) {
      const pc = probAt(best, st.probe), cy = Y(pc);
      svgEl(svg, "circle", { cx: px, cy, r: 8, fill: CURVE, stroke: "#fff", "stroke-width": 2, class: "curvereader" });
      const clab = `curve at ${st.probe.toFixed(1)} m: ${pc.toFixed(2)}`;
      const ctw = 12 + clab.length * 10.5, ctx = left ? px + 14 : px - 14 - ctw;
      const cly = clamp(cy + (pc > 0.5 ? 30 : -30), PY0 + 20, PY1 - 20);
      svgEl(svg, "rect", { x: ctx, y: cly - 18, width: ctw, height: 36, rx: 6, fill: "rgba(8,17,26,.92)", stroke: CURVE });
      txt(ctx + ctw / 2, cly, clab, { anchor: "middle", size: 20, bold: true, fill: "#eaf5ff" });
    }
    handle(px, PY1, "probe", "drag", CUT);
  }

  function drawCurve() {
    for (const v of [0, 1]) svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(v), y2: Y(v), stroke: "rgba(255,255,255,.3)", "stroke-dasharray": "6 6" });
    const cv = st.curve;
    if (st.showFit) drawFitCalc(cv);   // under the curve, the dots and the handles, so dragging stays visible
    curvePath(cv, { class: "scurve" });
    dots();
    const mx = clamp(cv.middle, T.xView[0], T.xView[1]);
    handle(X(mx), Y(0.5), "middle", "middle " + cv.middle.toFixed(2), MID, "right");
    const x8 = cv.middle + LN4 / cv.steepness;
    if (x8 <= T.xView[1]) handle(X(x8), Y(0.8), "steep", "steepness " + cv.steepness.toFixed(2), STEEP, "right");
  }

  // The fit calculation, all mornings at once: a dotted line from each dot to the curve (its length is the probability
  // the curve did NOT give to what happened), and a box in the empty lower right doing the sum: how close this curve comes to the best.
  function drawFitCalc(cv) {
    const rows = fitRows(cv);
    for (const r of rows) svgEl(svg, "line", { x1: X(r.x), x2: X(r.x), y1: Y(r.y), y2: Y(probAt(cv, r.x)),
      stroke: r.y ? YES : NO, "stroke-width": 2, "stroke-dasharray": "3 4", opacity: 0.9, class: "fitline" });
    const f = fitSummary(cv), bw = 266, bh = 262, bx = PX1 - bw - 6, by = PY1 - bh - 34, cols = 5, cw = 48, rh = 19;
    svgEl(svg, "rect", { x: bx, y: by, width: bw, height: bh, rx: 8, fill: "rgba(8,17,26,.82)", stroke: "rgba(255,255,255,.3)", class: "fitbox" });
    txt(bx + 10, by + 16, "Each morning, left to right, gets:", { size: 15, bold: true });
    svgEl(svg, "circle", { cx: bx + 15, cy: by + 36, r: 5, fill: YES });
    txt(bx + 24, by + 36, "turned back: p", { size: 14, fill: YES });
    svgEl(svg, "circle", { cx: bx + 138, cy: by + 36, r: 5, fill: NO });
    txt(bx + 147, by + 36, "landed: 1 − p", { size: 14, fill: NO });
    rows.forEach((r, i) => txt(bx + 10 + (i % cols) * cw + cw / 2, by + 58 + Math.floor(i / cols) * rh, r.g.toFixed(2),
      { anchor: "middle", size: 14, fill: r.y ? YES : NO }));
    const y0 = by + 58 + Math.ceil(rows.length / cols) * rh + 6;
    svgEl(svg, "line", { x1: bx + 8, x2: bx + bw - 8, y1: y0 - 10, y2: y0 - 10, stroke: "rgba(255,255,255,.25)" });
    txt(bx + 10, y0 + 4, `multiply all ${rows.length}: ` + sci(f.logL), { size: 14 });
    txt(bx + 10, y0 + 24, "best possible: " + sci(f.logLBest), { size: 14, fill: "#cdbf9f" });
    txt(bx + 10, y0 + 44, `per morning: ${f.gm.toFixed(3)} (best ${f.gmBest.toFixed(3)})`, { size: 14 });
    txt(bx + 10, y0 + 64, `vs best: ${f.gm.toFixed(3)} ÷ ${f.gmBest.toFixed(3)} = ${Math.round(100 * f.score)}%`, { size: 14, bold: true, fill: "#ffe39a" });
  }
  // each training morning, in swell order, with g = the probability the curve gives to what actually happened
  const fitRows = (cv) => T.training.map((d) => { const p = probAt(cv, d.x); return { ...d, g: d.y ? p : 1 - p }; });
  function fitSummary(cv) {
    const n = T.training.length, ll = (c) => fitRows(c).reduce((a, r) => a + Math.log(Math.max(r.g, 1e-300)), 0);
    const a = ll(cv), b = ll(best);
    return { logL: a / Math.LN10, logLBest: b / Math.LN10, gm: Math.exp(a / n), gmBest: Math.exp(b / n), score: fitScore(cv, best, X1, ys) };
  }
  const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
  function sci(log10) {   // a likelihood from its log10, e.g. 4.1 × 10⁻⁸
    let e = Math.floor(log10), m = Math.pow(10, log10 - e);
    if (m >= 9.95) { m = 1; e += 1; }
    return `${m.toFixed(1)} × 10${String(e).split("").map((c) => SUP[c]).join("")}`;
  }

  // Setting cases aside, a staged walk: the S-curve alone → connect-the-dots (a curve that memorises every training
  // morning; once chosen, the other model stays on as a faint curve) → the held-back mornings revealed as diamonds at
  // what actually happened → scored: a dotted line from each to the chosen curve (its probability_yes), a draggable
  // cut-off turning that probability into a call, and a ✓/✗ by each. Red rings mark wrong calls throughout.
  const DOTS = "#ff8a5c", RIGHT = "#7ee0a1", WRONG = "#ff4d3a";
  const modelAt = (m, x) => (m === "dots" ? connectDotsAt(T.training, x) : probAt(best, x));
  const cutNow = () => (st.scoring ? st.cutoff : 0.5);
  const isRight = (m, d, c = cutNow()) => (callAt(modelAt(m, d.x), c) === "yes" ? 1 : 0) === d.y;
  function drawHoldout() {
    const c = cutNow();
    for (const v of [0, 1]) svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(v), y2: Y(v), stroke: "rgba(255,255,255,.3)", "stroke-dasharray": "6 6" });
    if (st.scoring) {
      const yc = Y(c);
      svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: yc - PY0, fill: "rgba(255,200,97,.06)" });
      svgEl(svg, "rect", { x: PX0, y: yc, width: PX1 - PX0, height: PY1 - yc, fill: "rgba(143,179,217,.06)" });
      txt(PX0 + 12, PY0 + 16, "called yes", { size: 18, italic: true, fill: YES });
      txt(PX1 - 12, PY1 - 16, "called no", { anchor: "end", size: 18, italic: true, fill: NO });
      if (Math.abs(c - 0.5) > 1e-9) {
        svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(0.5), y2: Y(0.5), stroke: "rgba(255,255,255,.4)", "stroke-dasharray": "4 6" });
        txt(PX0 + 8, Y(0.5) + (c > 0.5 ? 16 : -16), "0.5", { size: 16, fill: "#cdbf9f" });
      }
    }
    const shown = st.dotsSeen ? (st.model === "s" ? ["dots", "s"] : ["s", "dots"]) : ["s"];
    for (const m of shown) {
      const on = m === st.model, pts = [];
      for (let i = 0; i <= 600; i++) { const x = T.xView[0] + (i / 600) * (T.xView[1] - T.xView[0]); pts.push(`${i ? "L" : "M"}${X(x).toFixed(1)} ${Y(modelAt(m, x)).toFixed(1)}`); }
      svgEl(svg, "path", { d: pts.join(""), fill: "none", stroke: m === "s" ? CURVE : DOTS, "stroke-width": on ? 4 : 2.5, opacity: on ? 1 : 0.3,
        "stroke-linecap": "round", "stroke-linejoin": "round", class: m === "s" ? "scurve" : "dotscurve" });
    }
    const ring = (d) => svgEl(svg, "circle", { cx: X(d.x), cy: Y(d.y), r: 16, fill: "none", stroke: WRONG, "stroke-width": 3, class: "wrongring" });
    for (const d of T.training) if (!isRight(st.model, d)) ring(d);
    dots(st.scoring ? 0.35 : 1);
    if (st.reveal) for (const d of T.heldBack) {
      const x = X(d.x), y = Y(d.y);
      if (st.scoring) {
        const p = modelAt(st.model, d.x), ok = isRight(st.model, d);
        svgEl(svg, "line", { x1: x, x2: x, y1: y, y2: Y(p), stroke: "#fff1d6", "stroke-width": 2, "stroke-dasharray": "3 4", opacity: 0.85, class: "heldline" });
        svgEl(svg, "circle", { cx: x, cy: Y(p), r: 6, fill: callAt(p, c) === "yes" ? YES : "#0b1622", stroke: callAt(p, c) === "yes" ? "#1a1208" : NO, "stroke-width": 2.5 });
        if (!ok) ring(d);
        txt(x, d.y ? y - 30 : y + 30, ok ? "✓" : "✗", { anchor: "middle", size: 24, bold: true, fill: ok ? RIGHT : WRONG })
          .setAttribute("class", "mark mark-" + (ok ? "right" : "wrong"));
      }
      svgEl(svg, "path", { d: diamond(x, y, 12), fill: d.y ? YES : NO, stroke: "#fff", "stroke-width": 2.5, class: "held", "data-day": d.day });
    }
    if (st.scoring) {
      const yc = Y(c);
      svgEl(svg, "line", { x1: PX0, x2: PX1, y1: yc, y2: yc, stroke: CUT, "stroke-width": 4, class: "cutline" });
      txt(PX1 - 60, yc - 18, "cut-off " + c.toFixed(2), { anchor: "end", size: 20, bold: true, fill: CUT });
      const band = svgEl(svg, "rect", { x: PX0, y: yc - 16, width: PX1 - PX0, height: 32, fill: "transparent", class: "hit handle-cutband" });
      band.addEventListener("pointerdown", (ev) => startDrag(ev, "cut"));
      handle(PX1 - 26, yc, "cut", null, CUT);
    }
  }
  const score = (m, set, c) => set.filter((d) => isRight(m, d, c)).length;
  const scores = (c = cutNow()) => ({ s: { train: score("s", T.training, c), held: score("s", T.heldBack, c) }, dots: { train: score("dots", T.training, c), held: score("dots", T.heldBack, c) } });
  const marks = () => (st.scoring ? T.heldBack.map((d) => ({ day: d.day, right: isRight(st.model, d) })) : []);

  function draw() {
    if (dead) return;
    svg.replaceChildren();
    axes();
    if (st.tab === "lines") drawLines();
    else if (st.tab === "curve") drawCurve();
    else drawHoldout();
    updateRead();
  }

  // ---------- dragging (pointer captured on the svg, so a redraw under the finger never drops it) ----------
  function startDrag(ev, kind) {
    ev.preventDefault();
    drag = { kind, id: ev.pointerId };
    try { svg.setPointerCapture(ev.pointerId); } catch (e) { /* synthetic events */ }
    moveDrag(ev);
  }
  function moveDrag(ev) {
    if (!drag || ev.pointerId !== drag.id) return;
    const p = svgPoint(svg, ev);
    if (drag.kind === "probe") api.setProbe(invX(p.x));
    else if (drag.kind === "middle") api.setCurve({ middle: invX(p.x), steepness: st.curve.steepness });
    else if (drag.kind === "steep") api.setCurve({ middle: st.curve.middle, steepness: LN4 / Math.max(0.12, invX(p.x) - st.curve.middle) });
    else if (drag.kind === "cut") api.setCutoff(invY(p.y));
  }
  function endDrag(ev) { if (drag && ev.pointerId === drag.id) { drag = null; save(); } }
  svg.addEventListener("pointermove", moveDrag);
  svg.addEventListener("pointerup", endDrag);
  svg.addEventListener("pointercancel", endDrag);

  // ---------- panel ----------
  let sMid = null, sSteep = null, sCut = null, sProbe = null, sBtn = null, fBtn = null;
  function buildPanel() {
    F.mark(st.tab);
    F.setLesson(...LESSONS[st.tab]);
    F.ctl.replaceChildren();
    sMid = sSteep = sCut = sProbe = sBtn = fBtn = null;
    if (st.tab === "lines") {
      sProbe = slider("Read the line at (m)", { min: 0, max: 6, step: 0.1, value: st.probe, fmt: (v) => v.toFixed(1) + " m", onInput: (v) => api.setProbe(v) });
      sBtn = button("Compare the S-curve", "tog", () => { st.showS = !st.showS; sBtn.setAttribute("aria-pressed", String(st.showS)); save(); draw(); },
        "Lay the logistic regression curve over the straight line");
      sBtn.setAttribute("aria-pressed", String(st.showS));
      F.ctl.append(sProbe.el, el("div", "clsbrow").appendChild(sBtn).parentNode);
    } else if (st.tab === "curve") {
      const row = el("div", "clsbrow");
      row.append(button("Best fit", "bestfit", () => api.bestFit(), "Snap to the curve buildModel() would find: the maximum-likelihood fit"),
                 button("Start again", "", () => api.setCurve({ ...START }), "Put the curve back where it started"));
      sMid = slider("Middle (m), where the probability is 0.5", { min: 0.3, max: 5.7, step: 0.05, value: st.curve.middle, fmt: (v) => v.toFixed(2) + " m",
        onInput: (v) => api.setCurve({ middle: v, steepness: st.curve.steepness }) });
      sSteep = slider("Steepness", { min: 0.2, max: 6, step: 0.05, value: st.curve.steepness, fmt: (v) => v.toFixed(2),
        onInput: (v) => api.setCurve({ middle: st.curve.middle, steepness: v }) });
      sMid.el.style.color = MID; sSteep.el.style.color = STEEP;
      fBtn = button("Show the fit calculation", "tog fitcalc", () => { st.showFit = !st.showFit; fBtn.setAttribute("aria-pressed", String(st.showFit)); save(); draw(); },
        "Draw each morning's probability on the plot and multiply them out");
      fBtn.setAttribute("aria-pressed", String(st.showFit));
      F.ctl.append(row, sMid.el, sSteep.el, el("div", "clsbrow").appendChild(fBtn).parentNode);
    } else {
      const row = el("div", "clsbrow"), mS = button("S-curve", "tog model-s", () => api.setModel("s"), "Logistic regression, fit to the training mornings"),
        mD = button("Connect-the-dots", "tog model-dots", () => api.setModel("dots"), "A curve through every training morning");
      mS.setAttribute("aria-pressed", String(st.model === "s")); mD.setAttribute("aria-pressed", String(st.model === "dots"));
      row.append(el("span", null, "Model:"), mS, mD);
      const rv = button("Reveal the held-back mornings", "tog reveal", () => api.setReveal(!st.reveal),
        "Show the ten mornings that were set aside, at what actually happened");
      rv.setAttribute("aria-pressed", String(st.reveal));
      F.ctl.append(row, el("div", "clsbrow").appendChild(rv).parentNode);
      if (st.reveal) {
        const sb = button("Score the held-back mornings", "tog score", () => api.setScoring(!st.scoring),
          "Read each held-back morning's probability off the curve and call it with a cut-off");
        sb.setAttribute("aria-pressed", String(st.scoring));
        F.ctl.append(el("div", "clsbrow").appendChild(sb).parentNode);
      }
      if (st.scoring) {
        sCut = slider("Cut-off", { min: 0.05, max: 0.95, step: 0.01, value: st.cutoff, fmt: (v) => v.toFixed(2), onInput: (v) => api.setCutoff(v) });
        F.ctl.append(sCut.el, el("div", "clsbrow").appendChild(button("Back to 0.5", "", () => api.setCutoff(0.5))).parentNode);
      }
    }
    updateRead();
  }
  function updateRead() {
    const R = F.read;
    R.replaceChildren();
    if (st.tab === "lines") {
      const v = lineAt(st.probe);
      R.append(para(`The straight line through the 0/1 codes predicts <b>${fmtSigned(lineAt(0))}</b> at 0 m and <b>${fmtSigned(lineAt(6))}</b> at 6 m.`),
        para(`At ${st.probe.toFixed(1)} m it reads <b>${fmtSigned(v)}</b>${v < 0 || v > 1 ? ": not a probability." : "."}`));
      if (st.showS) R.append(para(`The S-curve at ${st.probe.toFixed(1)} m reads <b>${probAt(best, st.probe).toFixed(2)}</b>, always between 0 and 1.`));
    } else if (st.tab === "curve") {
      if (sMid) sMid.set(st.curve.middle);
      if (sSteep) sSteep.set(st.curve.steepness);
      // the live formula, its two numbers in the handles' colours, so each drag shows exactly which number it changes
      const c = st.curve;
      R.append(para(`<span class="curveeq" style="font-size:19px">probability_yes = 1 / (1 + e<sup>−<b style="color:${STEEP}">${c.steepness.toFixed(2)}</b> × (swell_m − <b style="color:${MID}">${c.middle.toFixed(2)}</b>)</sup>)</span>`));
    } else {
      if (sCut) sCut.set(st.cutoff);   // the plot carries the score: rings, ✓/✗, no table
    }
  }
  const para = (html, cls) => { const p = el("p", cls || null); p.innerHTML = html; return p; };
  const fmtSigned = (v) => (v < 0 ? "−" + Math.abs(v).toFixed(2) : v.toFixed(2));

  // ---------- best fit: a short glide, instant under reduced motion ----------
  function glideTo(target, ms = 650) {
    cancelAnimationFrame(raf);
    if (reduced || ms <= 0) { st.curve = { ...target }; save(); draw(); return; }
    const from = { ...st.curve }, t0 = performance.now();
    const step = (now) => {
      if (dead) return;
      const t = Math.min(1, (now - t0) / ms), e = t * t * (3 - 2 * t);
      st.curve = { middle: from.middle + (target.middle - from.middle) * e,
                   steepness: Math.exp(Math.log(from.steepness) + (Math.log(target.steepness) - Math.log(from.steepness)) * e) };
      draw();
      if (t < 1) raf = requestAnimationFrame(step); else { st.curve = { ...target }; save(); draw(); }
    };
    raf = requestAnimationFrame(step);
  }

  const api = {
    ready: Promise.resolve(),
    setTab(k) { if (!TABS.some(([kk]) => kk === k)) throw new Error("sigmoid_board: setTab needs lines/curve/holdout"); cancelAnimationFrame(raf); drag = null; st.tab = k; save(); buildPanel(); draw(); },
    tab: () => st.tab,
    curve: () => ({ ...st.curve }),
    setCurve(c) {
      cancelAnimationFrame(raf);
      st.curve = { middle: clamp(+c.middle, 0.3, 5.7), steepness: clamp(+c.steepness, 0.2, 6) };
      save(); draw();
    },
    bestFit({ instant } = {}) { glideTo(best, instant ? 0 : 650); },
    best: () => ({ ...best }),
    line: () => ({ ...line }),
    lineAt,
    curveAt: (x) => probAt(best, x),
    setShowFit(on) { st.showFit = !!on; if (fBtn) fBtn.setAttribute("aria-pressed", String(st.showFit)); save(); draw(); },
    showFit: () => st.showFit,
    setModel(m) { if (m !== "s" && m !== "dots") throw new Error("sigmoid_board: setModel needs s/dots"); st.model = m; if (m === "dots") st.dotsSeen = true; save(); buildPanel(); draw(); },
    model: () => st.model,
    setReveal(on) { st.reveal = !!on; if (!st.reveal) st.scoring = false; save(); buildPanel(); draw(); },
    setScoring(on) { st.scoring = !!on && st.reveal; save(); buildPanel(); draw(); },
    scoring: () => st.scoring,
    marks,
    revealed: () => st.reveal,
    scores,
    fit: () => fitSummary(st.curve),
    setProbe(x) { st.probe = clamp(Math.round(+x * 10) / 10, 0, 6); if (sProbe) sProbe.set(st.probe); save(); draw(); },
    probe: () => st.probe,
    probability(day) { const d = T.training.find((t) => t.day === +day); return d ? probAt(st.curve, d.x) : null; },
    setCutoff(c) { st.cutoff = clamp(Math.round(+c * 100) / 100, 0.05, 0.95); save(); draw(); updateRead(); },
    cutoff: () => st.cutoff,
    destroy() {
      if (dead) return;
      dead = true; cancelAnimationFrame(raf);
      svg.removeEventListener("pointermove", moveDrag); svg.removeEventListener("pointerup", endDrag); svg.removeEventListener("pointercancel", endDrag);
      F.root.remove();
    },
  };
  F.root.sigmoidBoard = api;          // for tests and the console; harmless to students
  buildPanel();
  draw();
  return api;
}
