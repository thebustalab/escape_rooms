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
//                                  buildModel() finds); click a morning to read its probability_yes off the curve.
//   3 Predicting held-back cases   the best-fit curve with the training mornings faded, ten held-back mornings placed on
//                                  it, and the cut-off as a draggable horizontal line turning each probability into a
//                                  call; calls that differ from the 0.5 call are ringed and listed.
//
// TOY DATA ONLY (classification_math.js LANDING: forty invented mornings, swell height vs did the supply boat turn
// back), labelled as invented on the board. Never graded, never logged, holds no answer. Code-drawn SVG: no art, no
// geometry (validate_assets.py NO_GEOMETRY_KINDS).
//
//   const b = mount(hostEl, { pegs?, onPegs?(state) });
//   b.setTab("lines"|"curve"|"cutoff"); b.tab(); b.curve(); b.setCurve({middle, steepness}); b.bestFit({instant});
//   b.best(); b.pick(day|null); b.picked(); b.probability(day); b.setCutoff(c); b.cutoff(); b.calls(); b.changed();
//   b.setProbe(x); b.lineAt(x); b.ready; b.destroy().   The root element carries the API as `.sigmoidBoard` for tests.
import { LANDING, olsLine, fitLogistic, curveFromCoef, probAt, fitScore, callAt } from "./classification_math.js?v=179";
import { shell, svgEl, el, button, slider, svgPoint, fmt2 } from "./classification_ui.js?v=179";

const TABS = [["lines", "From numbers to categories"], ["curve", "A model from one predictor"], ["cutoff", "Predicting held-back cases"]];
// Each tab's takeaway in the chapter's own wording (12d_classification.Rmd), and the section it belongs to.
const LESSONS = {
  lines: ["A model that predicts a category is a classification model. A straight line fitted to a yes/no response coded as 1 and 0 has no floor and no ceiling: it falls below 0 at one end and climbs past 1 at the other, and neither value can be a probability. Logistic regression bends its predictions into an S-shape that stays between 0 and 1.",
    "from numbers to categories"],
  curve: ["A logistic regression model gives each case a probability_yes: the model's probability that the response is yes, given its predictor. It is not the share of cases that are yes, and it is not a call.",
    "a model from one predictor"],
  cutoff: ["The held-back cases were never shown to the model, so it gives them a probability exactly as it would for cases not yet seen. A cut-off turns each probability into a call: yes at 0.5 or more. A lower cut-off calls more cases yes and a higher one fewer; the probabilities themselves do not change, only the line drawn across them moves.",
    "several predictors, and predicting held-back cases"],
};
const W = 960, H = 600, PX0 = 100, PX1 = 930, PY0 = 74, PY1 = 524;
const YES = "#ffc861", NO = "#8fb3d9", LINE = "#ff8a5c", CURVE = "#7fd3ff", CUT = "#ffe39a", BAD = "rgba(255,90,70,.13)";
const LN4 = Math.log(4);       // the steepness handle sits where the curve reaches 0.8: logit(0.8) = ln 4
const START = { middle: 4.1, steepness: 0.8 };   // deliberately off the dots, so "Best fit" has something to do

export function mount(host, opts = {}) {
  const T = LANDING;
  const xs = T.training.map((d) => d.x), ys = T.training.map((d) => d.y), X1 = xs.map((x) => [x]);
  const line = olsLine(xs, ys);
  const best = curveFromCoef(fitLogistic(X1, ys));
  const s0 = opts.pegs && typeof opts.pegs === "object" ? opts.pegs : {};
  const st = {
    tab: TABS.some(([k]) => k === s0.tab) ? s0.tab : "lines",
    curve: s0.curve && Number.isFinite(s0.curve.middle) && Number.isFinite(s0.curve.steepness) ? { ...s0.curve } : { ...START },
    picked: Number.isFinite(s0.picked) ? s0.picked : null,
    cutoff: Number.isFinite(s0.cutoff) ? s0.cutoff : 0.5,
    probe: Number.isFinite(s0.probe) ? s0.probe : 5.5,
    showS: !!s0.showS,
  };
  const reduced = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  let dead = false, raf = 0, drag = null;
  const save = () => opts.onPegs && opts.onPegs({ tab: st.tab, curve: { ...st.curve }, picked: st.picked, cutoff: st.cutoff, probe: st.probe, showS: st.showS });

  const F = shell(host, { cls: "sigmoidboard", tabs: TABS, W, H, onTab: (k) => api.setTab(k),
    ariaLabel: "The S-curve board: invented yes/no mornings against swell height, a straight line, an S-curve and a cut-off" });
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
    // the toy label: invented, and not from any room's data
    txt(PX0, 22, "Invented readings: forty made-up mornings at the island's landing (not from any room's data)", { size: 17, italic: true, fill: "#cdbf9f" });
    // legend
    const lx = PX0, ly = 50;
    svgEl(svg, "circle", { cx: lx + 8, cy: ly, r: 8, fill: YES });
    txt(lx + 22, ly, "turned back: yes", { size: 17 });
    svgEl(svg, "circle", { cx: lx + 190, cy: ly, r: 8, fill: NO });
    txt(lx + 204, ly, "turned back: no (landed)", { size: 17 });
    if (st.tab === "cutoff") {
      svgEl(svg, "path", { d: diamond(lx + 452, ly, 9), fill: "#fff1d6" });
      txt(lx + 466, ly, "held back (never shown to the model)", { size: 17 });
    }
  }
  const diamond = (x, y, r) => `M${x} ${y - r}L${x + r} ${y}L${x} ${y + r}L${x - r} ${y}Z`;
  function dots(alpha = 1, pickable = false) {
    for (const d of T.training) {
      const c = svgEl(svg, "circle", { cx: X(d.x), cy: Y(d.y), r: 9, fill: d.y ? YES : NO, opacity: alpha,
        stroke: st.picked === d.day && st.tab === "curve" ? "#fff" : "rgba(0,0,0,.5)", "stroke-width": st.picked === d.day && st.tab === "curve" ? 3 : 1,
        class: pickable ? "pickable dot" : "dot", "data-day": d.day });
      if (pickable) {
        const hit = svgEl(svg, "circle", { cx: X(d.x), cy: Y(d.y), r: 16, fill: "transparent", class: "pickable dothit", "data-day": d.day });
        hit.addEventListener("click", () => api.pick(st.picked === d.day ? null : d.day));
        c.addEventListener("click", () => api.pick(st.picked === d.day ? null : d.day));
      }
    }
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
    handle(px, PY1, "probe", "drag", CUT);
  }

  function drawCurve() {
    for (const v of [0, 1]) svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(v), y2: Y(v), stroke: "rgba(255,255,255,.3)", "stroke-dasharray": "6 6" });
    const cv = st.curve;
    curvePath(cv, { class: "scurve" });
    const d = st.picked != null ? T.training.find((t) => t.day === st.picked) : null;
    if (d) {
      const p = probAt(cv, d.x);
      svgEl(svg, "line", { x1: X(d.x), x2: X(d.x), y1: Y(d.y), y2: Y(p), stroke: "#fff", "stroke-width": 2, "stroke-dasharray": "5 5" });
      svgEl(svg, "line", { x1: X(d.x), x2: PX0, y1: Y(p), y2: Y(p), stroke: "#fff", "stroke-width": 2, "stroke-dasharray": "5 5" });
      svgEl(svg, "circle", { cx: X(d.x), cy: Y(p), r: 7, fill: "#fff" });
      svgEl(svg, "rect", { x: PX0 + 6, y: Y(p) - 17, width: 92, height: 34, rx: 6, fill: "#1f3a52", stroke: "#9ccaf2" });
      txt(PX0 + 52, Y(p), p.toFixed(2), { anchor: "middle", size: 21, bold: true, fill: "#eaf5ff" });
    }
    dots(1, true);
    const mx = clamp(cv.middle, T.xView[0], T.xView[1]);
    handle(X(mx), Y(0.5), "middle", "middle", CUT, "right");
    const x8 = cv.middle + LN4 / cv.steepness;
    if (x8 <= T.xView[1]) handle(X(x8), Y(0.8), "steep", "steepness", "#9ccaf2", "right");
  }

  function drawCutoff() {
    const c = st.cutoff, yc = Y(c);
    svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: yc - PY0, fill: "rgba(255,200,97,.07)" });
    svgEl(svg, "rect", { x: PX0, y: yc, width: PX1 - PX0, height: PY1 - yc, fill: "rgba(143,179,217,.07)" });
    txt(PX0 + 12, PY0 + 18, "called yes", { size: 18, italic: true, fill: YES });
    txt(PX0 + 12, PY1 - 18, "called no", { size: 18, italic: true, fill: NO });
    dots(0.22);
    curvePath(best, { opacity: 0.9, class: "scurve" });
    if (Math.abs(c - 0.5) > 1e-9) {
      svgEl(svg, "line", { x1: PX0, x2: PX1, y1: Y(0.5), y2: Y(0.5), stroke: "rgba(255,255,255,.4)", "stroke-dasharray": "4 6" });
      txt(PX1 - 8, Y(0.5) + (c > 0.5 ? 16 : -16), "0.5", { anchor: "end", size: 16, fill: "#cdbf9f" });
    }
    for (const r of calls()) {
      const x = X(r.x), y = Y(r.p);
      if (r.changed) svgEl(svg, "circle", { cx: x, cy: y, r: 19, fill: "none", stroke: "#ffb36b", "stroke-width": 3.5, class: "changedring" });
      svgEl(svg, "path", { d: diamond(x, y, 12), fill: r.call === "yes" ? YES : "#0b1622", stroke: r.call === "yes" ? "#1a1208" : NO, "stroke-width": 3, class: "held", "data-day": r.day, "data-call": r.call });
      txt(x, y - 26, String(r.day), { anchor: "middle", size: 15, fill: r.changed ? "#ffb36b" : "#cdbf9f", bold: r.changed });
    }
    svgEl(svg, "line", { x1: PX0, x2: PX1, y1: yc, y2: yc, stroke: CUT, "stroke-width": 4, class: "cutline" });
    txt(PX1 - 60, yc - 18, "cut-off " + c.toFixed(2), { anchor: "end", size: 20, bold: true, fill: CUT });
    const band = svgEl(svg, "rect", { x: PX0, y: yc - 16, width: PX1 - PX0, height: 32, fill: "transparent", class: "hit handle-cutband" });
    band.addEventListener("pointerdown", (ev) => startDrag(ev, "cut"));
    handle(PX1 - 26, yc, "cut", null, CUT);
  }

  function draw() {
    if (dead) return;
    svg.replaceChildren();
    axes();
    if (st.tab === "lines") drawLines();
    else if (st.tab === "curve") drawCurve();
    else drawCutoff();
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
  let sMid = null, sSteep = null, sCut = null, sProbe = null, fitBar = null, sBtn = null;
  function buildPanel() {
    F.mark(st.tab);
    F.setLesson(...LESSONS[st.tab]);
    F.ctl.replaceChildren();
    sMid = sSteep = sCut = sProbe = fitBar = sBtn = null;
    if (st.tab === "lines") {
      sProbe = slider("Read the line at (m)", { min: 0, max: 6, step: 0.1, value: st.probe, fmt: (v) => v.toFixed(1) + " m", onInput: (v) => api.setProbe(v) });
      sBtn = button("Compare the S-curve", "tog", () => { st.showS = !st.showS; sBtn.setAttribute("aria-pressed", String(st.showS)); save(); draw(); },
        "Lay the logistic regression curve over the straight line");
      sBtn.setAttribute("aria-pressed", String(st.showS));
      F.ctl.append(sProbe.el, el("div", "clsbrow").appendChild(sBtn).parentNode);
    } else if (st.tab === "curve") {
      const row = el("div", "clsbrow");
      row.append(button("Best fit", "primary bestfit", () => api.bestFit(), "Snap to the curve buildModel() would find: the maximum-likelihood fit"),
                 button("Start again", "", () => { api.setCurve({ ...START }); api.pick(null); }, "Put the curve back where it started"));
      sMid = slider("Middle (m), where the probability is 0.5", { min: 0.3, max: 5.7, step: 0.05, value: st.curve.middle, fmt: (v) => v.toFixed(2) + " m",
        onInput: (v) => api.setCurve({ middle: v, steepness: st.curve.steepness }) });
      sSteep = slider("Steepness", { min: 0.2, max: 6, step: 0.05, value: st.curve.steepness, fmt: (v) => v.toFixed(2),
        onInput: (v) => api.setCurve({ middle: st.curve.middle, steepness: v }) });
      const pick = el("div", "clsbrow");
      pick.append(el("span", null, "Read a morning:"),
        button("◀", "", () => stepPick(-1), "Previous morning"), button("▶", "", () => stepPick(1), "Next morning"));
      const fb = el("div"); fb.style.cssText = "display:flex;flex-direction:column;gap:4px";
      const track = el("div"); track.style.cssText = "height:14px;background:#1a1208;border:1px solid #8a6a32;border-radius:7px;overflow:hidden";
      fitBar = el("i"); fitBar.style.cssText = "display:block;height:100%;background:linear-gradient(90deg,#a8742e,#ffe39a)";
      track.appendChild(fitBar);
      fb.append(el("span", "dim", "How well the curve fits the dots (full at the best fit)"), track);
      F.ctl.append(row, sMid.el, sSteep.el, pick, fb);
    } else {
      sCut = slider("Cut-off", { min: 0.05, max: 0.95, step: 0.01, value: st.cutoff, fmt: (v) => v.toFixed(2), onInput: (v) => api.setCutoff(v) });
      F.ctl.append(sCut.el, el("div", "clsbrow").appendChild(button("Back to 0.5", "", () => api.setCutoff(0.5))).parentNode);
    }
    updateRead();
  }
  function stepPick(dir) {
    const days = T.training.map((d) => d.day);
    const i = st.picked == null ? (dir > 0 ? -1 : days.length) : days.indexOf(st.picked);
    api.pick(days[(i + dir + days.length) % days.length]);
  }
  function updateRead() {
    const R = F.read;
    R.replaceChildren();
    if (st.tab === "lines") {
      const v = lineAt(st.probe);
      R.append(para(`The straight line through the 0/1 codes predicts <b>${fmtSigned(lineAt(0))}</b> at 0 m and <b>${fmtSigned(lineAt(6))}</b> at 6 m.`),
        para(`At ${st.probe.toFixed(1)} m it reads <b>${fmtSigned(v)}</b>${v < 0 || v > 1 ? ": not a probability." : "."}`));
    } else if (st.tab === "curve") {
      if (sMid) sMid.set(st.curve.middle);
      if (sSteep) sSteep.set(st.curve.steepness);
      if (fitBar) fitBar.style.width = (100 * fitScore(st.curve, best, X1, ys)).toFixed(1) + "%";
      const d = st.picked != null ? T.training.find((t) => t.day === st.picked) : null;
      if (d) {
        R.append(para(`Morning ${d.day}: swell ${d.x.toFixed(1)} m, turned_back <b>${d.y ? "yes" : "no"}</b>.`),
          para(`On this curve, probability_yes = <b>${probAt(st.curve, d.x).toFixed(2)}</b>.`));
      } else R.append(para("Click a morning's dot to read its probability_yes off the curve.", "dim"));
    } else {
      if (sCut) sCut.set(st.cutoff);
      const rows = calls(), yesNow = rows.filter((r) => r.call === "yes").length, yes05 = rows.filter((r) => r.call05 === "yes").length;
      R.append(para(`Called yes: <b>${yesNow}</b> of ${rows.length} held-back mornings (at 0.5: ${yes05}).`));
      const t = el("table", "clsbtable");
      t.innerHTML = `<thead><tr><th>day</th><th>swell_m</th><th>probability_yes</th><th>call at 0.5</th><th>at ${st.cutoff.toFixed(2)}</th></tr></thead>`;
      const tb = el("tbody");
      for (const r of rows) {
        const tr = el("tr", r.changed ? "changed" : ""); tr.dataset.day = r.day;
        tr.innerHTML = `<td>${r.day}</td><td>${r.x.toFixed(2)}</td><td>${r.p.toFixed(3)}</td><td class="${r.call05}">${r.call05}</td><td class="${r.call}">${r.call}</td>`;
        tb.appendChild(tr);
      }
      t.appendChild(tb); R.append(t);
    }
  }
  const para = (html, cls) => { const p = el("p", cls || null); p.innerHTML = html; return p; };
  const fmtSigned = (v) => (v < 0 ? "−" + Math.abs(v).toFixed(2) : v.toFixed(2));

  function calls() {
    return T.heldBack.map((h) => {
      const p = probAt(best, h.x), call = callAt(p, st.cutoff), call05 = callAt(p, 0.5);
      return { day: h.day, x: h.x, p, call, call05, changed: call !== call05 };
    });
  }

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
    setTab(k) { if (!TABS.some(([kk]) => kk === k)) throw new Error("sigmoid_board: setTab needs lines/curve/cutoff"); cancelAnimationFrame(raf); drag = null; st.tab = k; save(); buildPanel(); draw(); },
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
    setProbe(x) { st.probe = clamp(Math.round(+x * 10) / 10, 0, 6); if (sProbe) sProbe.set(st.probe); save(); draw(); },
    probe: () => st.probe,
    pick(day) { st.picked = day == null ? null : +day; save(); draw(); },
    picked: () => st.picked,
    probability(day) { const d = T.training.find((t) => t.day === +day); return d ? probAt(st.curve, d.x) : null; },
    setCutoff(c) { st.cutoff = clamp(Math.round(+c * 100) / 100, 0.05, 0.95); save(); draw(); },
    cutoff: () => st.cutoff,
    calls, changed: () => calls().filter((r) => r.changed).map((r) => r.day),
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
