// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `scoreboard` kind).
// The scoreboard: an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"scoreboard"`), built 2026-11-19 for the
// classification home world (classification/watch, day two: the plate archive). Lucas demos it on the projector on day
// two; students return to it at home. One tab per day-two section of the chapter, only its own controls, a Lesson in
// the book's wording:
//
//   1 Several predictors            a map of the model: barometer across, humidity up, coloured by probability_clear,
//                                   the 0.5 line where the call flips, the 48 nights on it; the two coefficients as
//                                   sliders (intercept refitted by maximum likelihood), Best fit, the likelihood as a
//                                   share of the best's; the formula with the live coefficients (log-odds unnamed).
//   2 Which predictors matter most  two invented readings in very different units (a barometer in hPa, humidity as a
//                                   0-1 fraction): each reading's spread with "one unit" drawn against it, and the
//                                   model's coefficients as bars. Raw, humidity's dwarfs the barometer's; "Scaled"
//                                   (scale_variance = TRUE) puts both in standard deviations and the ranking flips.
//                                   A night's probability_clear is shown from both models: scaling changes units, not
//                                   the model.
//   3 Judging a classifier          a held-back tally of 200 invented nights, the model's calls at the 0.5 cut-off
//                                   beside "always call cloudy": accuracy, caught and missed. A slider sets how rare yes
//                                   is; below about one night in eight, always-no wins on accuracy while catching
//                                   nothing.
//   4 Confusion matrix              the same held-back nights sorted into the 2 x 2 confusion matrix (what really
//                                   happened against what the model called: caught, missed, false alarm, correctly
//                                   called no), with precision and recall worked out from its cells. A cut-off slider
//                                   (0.5 by default) moves the calls: lower it and recall rises while precision falls.
//                                   The yes-share slider is shared with tab 3; when yes is rare, precision drops.
//
// TOY DATA ONLY (classification_math.js makeNights / tallyPool); the board carries no "invented data" caption (instruments_and_widgets.md: no text that does not teach). Never graded,
// never logged, holds no answer. Code-drawn SVG: no art, no geometry (validate_assets.py NO_GEOMETRY_KINDS).
//
//   const s = mount(hostEl, { pegs?, onPegs?(state) });
//   s.setTab("several"|"scale"|"judge"); s.setSlopes({pressure, humidity}); s.slopes(); s.bestFit(); s.tab(); s.setScaled(bool); s.scaled(); s.coefs(); s.rawCoefs(); s.scaledCoefs();
//   s.probabilities(night); s.setShare(0..1); s.share(); s.tally(); s.setCutoff(0.1..0.9); s.cutoff(); s.matrix(); s.ready; s.destroy().
//   The root element carries the API as `.scoreboard` for tests.
import { makeNights, NIGHT_PREDICTORS, fitLogistic, scaledCoefs, logistic, tallyPool, judge, alwaysNo, confusion, mean, sd }
  from "./classification_math.js?v=184";
import { shell, svgEl, el, button, slider, pct } from "./classification_ui.js?v=184";

const TABS = [["several", "Several predictors"], ["scale", "Which predictors matter most"], ["judge", "Judging a classifier"], ["matrix", "Confusion matrix"]];
const LESSONS = {
  several: ["With several predictors, logistic regression adds up one term per predictor (the predictor times its coefficient) plus an intercept, and the S-curve turns that sum into a probability_clear between 0 and 1. It is one model with several inputs: here every combination of barometer and humidity gets one probability, so the model is a map, and the 0.5 line on it separates the nights called clear from the nights called cloudy. Fitting the model means choosing all the coefficients at once: the best fit is the set that gives the highest likelihood.",
    "several predictors, and predicting held-back cases"],
  scale: ["Raw coefficients mostly reflect units: a predictor that barely changes from one case to the next gets a large coefficient for that reason alone. Scale each predictor to a mean of zero and a standard deviation of one, then rank the coefficients by size, ignoring the sign. Scaling changes the units of the coefficients, not the model: every case keeps the same probability.",
    "which predictors matter most"],
  judge: ["Accuracy is the share of calls that are right. When clear nights are rare, calling every night cloudy scores a high accuracy and catches nothing. So report how many actually clear nights were caught and how many were missed beside accuracy, never accuracy alone.",
    "judging a classifier on held-back cases"],
  matrix: ["A confusion matrix sorts every held-back case by what really happened versus what the model called, giving four counts: caught (actually clear, called clear: true positives), missed (actually clear, called cloudy: false negatives), false alarms (actually cloudy, called clear: false positives) and correctly called cloudy (actually cloudy, called cloudy: true negatives). Two numbers come from it. Precision is caught ÷ (caught + false alarms): of the cases the model called yes, the share that really were yes. Recall is caught ÷ (caught + missed): of the cases that really were yes, the share the model caught. Lowering the cut-off raises recall and lowers precision; raising it does the opposite.",
    "judging a classifier on held-back cases"],
};
const W = 960, H = 600;
const YES = "#ffc861", NO = "#8fb3d9", WRONG = "#ff7a5c", BAR_POS = "#7fd3ff", BAR_NEG = "#ff9f7a";
// held-back nights (tabs 3 and 4): black = actually clear, white = actually cloudy, on a grey backing; a right call is a filled
// square, a wrong call only its border
const CLEAR = "#000000", CLOUDY = "#ffffff", BACKING = "#6f7780";
const TALLY_LOOK = { caught: [CLEAR, "none"], missed: ["none", CLEAR], rightno: [CLOUDY, "none"], wrongyes: ["none", CLOUDY] };

export function mount(host, opts = {}) {
  const nights = makeNights();
  const X = nights.map((d) => d.x), y = nights.map((d) => d.y);
  const raw = fitLogistic(X, y);
  const sc = scaledCoefs(X, y);
  const cols = NIGHT_PREDICTORS.map((p, j) => ({ ...p, values: X.map((r) => r[j]), mean: mean(X.map((r) => r[j])), sd: sd(X.map((r) => r[j])) }));
  const s0 = opts.pegs && typeof opts.pegs === "object" ? opts.pegs : {};
  const st = {
    tab: TABS.some(([k]) => k === s0.tab) ? s0.tab : "several",
    b1: Number.isFinite(s0.b1) ? s0.b1 : raw[1],   // tab 1's two coefficient sliders; the intercept is refitted to them
    b2: Number.isFinite(s0.b2) ? s0.b2 : raw[2],
    scaled: !!s0.scaled,
    share: Number.isFinite(s0.share) ? s0.share : 0.3,
    night: Number.isFinite(s0.night) ? s0.night : 7,
    cutoff: Number.isFinite(s0.cutoff) ? Math.max(0.1, Math.min(0.9, s0.cutoff)) : 0.5,
  };
  let dead = false;
  const save = () => opts.onPegs && opts.onPegs({ tab: st.tab, scaled: st.scaled, share: st.share, cutoff: st.cutoff, night: st.night, b1: st.b1, b2: st.b2 });

  const F = shell(host, { cls: "scoreboard", tabs: TABS, W, H, onTab: (k) => api.setTab(k),
    ariaLabel: "The scoreboard: nights at the plate archive, two predictors' coefficients raw and scaled, and a held-back tally" });
  const svg = F.svg;
  function txt(x, yy, s, o = {}) {
    return svgEl(svg, "text", { x, y: yy, fill: o.fill || "#f3e6c4", "font-size": o.size || 20, "text-anchor": o.anchor || "start",
      "font-style": o.italic ? "italic" : null, "font-weight": o.bold ? "bold" : null, "dominant-baseline": "middle", opacity: o.opacity, class: o.cls }, s);
  }
  const coefRows = () => {
    const v = st.scaled ? sc.coefs : raw;
    return NIGHT_PREDICTORS.map((p, j) => ({ variable: p.name, value: v[j + 1] }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  };
  const probBoth = (n) => {
    const d = nights.find((t) => t.night === n); if (!d) return null;
    const pr = logistic(raw[0] + d.x[0] * raw[1] + d.x[1] * raw[2]);
    const z = d.x.map((v, j) => (v - sc.means[j]) / sc.sds[j]);
    const ps = logistic(sc.coefs[0] + z[0] * sc.coefs[1] + z[1] * sc.coefs[2]);
    return { night: n, x: d.x, raw: pr, scaled: ps };
  };

  // ---------- tab 1: several predictors, as a MAP (Lucas, 2026-11-25): barometer across, humidity up, each spot
  // coloured by the model's probability_clear, the dashed 0.5 line where the call flips, and the 48 training nights on
  // it (black = actually clear, white = actually cloudy). The two coefficients are sliders (the intercept is refitted
  // to them by maximum likelihood), "Best fit" restores glm's fit. One model, two inputs: no S-curve slices.
  const HUM = "#c9a7ff", PRS = BAR_POS, HV = [0.4, 1.0];
  const PX0 = 110, PX1 = 930, PY0 = 150, PY1 = 506, PV = [994, 1034];
  const B1 = [0, 0.5], B2 = [-25, 5];
  const sx = (v) => PX0 + ((v - PV[0]) / (PV[1] - PV[0])) * (PX1 - PX0);
  const hy = (h) => PY1 - ((h - HV[0]) / (HV[1] - HV[0])) * (PY1 - PY0);
  // the maximum-likelihood intercept for fixed slopes (Newton on one parameter; the log-likelihood is concave in it)
  function fitIntercept(b1, b2) {
    const ybar = Math.min(0.99, Math.max(0.01, y.reduce((t, v) => t + v, 0) / y.length));
    let b0 = Math.log(ybar / (1 - ybar)) - b1 * mean(X.map((r) => r[0])) - b2 * mean(X.map((r) => r[1]));
    for (let k = 0; k < 50; k++) {
      let g = 0, h = 0;
      for (let i = 0; i < X.length; i++) { const p = logistic(b0 + b1 * X[i][0] + b2 * X[i][1]); g += y[i] - p; h += p * (1 - p); }
      if (h < 1e-12) break;
      const step = g / h; b0 += step; if (Math.abs(step) < 1e-10) break;
    }
    return b0;
  }
  const logLikAt = (c) => X.reduce((t, r, i) => { const p = logistic(c[0] + c[1] * r[0] + c[2] * r[1]); return t + Math.log(Math.max(1e-300, y[i] ? p : 1 - p)); }, 0);
  const bestLL = logLikAt(raw);
  const coefNow = () => [fitIntercept(st.b1, st.b2), st.b1, st.b2];
  function eqLine(yy, pieces, size = 19) {   // one line of the equation, each piece [text, colour?, bold?]
    const t = svgEl(svg, "text", { x: 40, y: yy, "font-size": size, fill: "#f3e6c4", "dominant-baseline": "middle", class: "eq" });
    for (const [s2, c, b] of pieces) svgEl(t, "tspan", { fill: c || null, "font-weight": b ? "bold" : null }, s2);
    return t;
  }
  const neg = (v, d) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
  const sgn = (v, d) => (v < 0 ? " − " : " + ") + Math.abs(v).toFixed(d);
  // the map's colour: dark slate at probability_clear 0 to warm amber at 1
  const MAP0 = [27, 42, 56], MAP1 = [242, 194, 107];
  const mapColour = (p) => `rgb(${MAP0.map((v, i) => Math.round(v + (MAP1[i] - v) * p)).join(",")})`;
  function drawSeveral() {
    const c = coefNow();
    eqLine(66, [["probability_clear = 1 / (1 + exp(−(", null, true], [neg(c[0], 3), null, true],
      [sgn(c[1], 5), PRS, true], [" × pressure_hpa", PRS], [sgn(c[2], 3), HUM, true], [" × humidity_fraction", HUM], [")))", null, true]], 18)
      .setAttribute("class", "eq eqlive");
    const pAt = (pr, hu) => logistic(c[0] + c[1] * pr + c[2] * hu);
    // the map: one cell per small step of barometer and humidity
    const NX = 83, NY = 35, cw = (PX1 - PX0) / NX, ch = (PY1 - PY0) / NY;
    for (let i = 0; i < NX; i++) for (let j = 0; j < NY; j++) {
      const pr = PV[0] + ((i + 0.5) / NX) * (PV[1] - PV[0]), hu = HV[1] - ((j + 0.5) / NY) * (HV[1] - HV[0]);
      svgEl(svg, "rect", { x: (PX0 + i * cw).toFixed(2), y: (PY0 + j * ch).toFixed(2), width: (cw + 0.6).toFixed(2), height: (ch + 0.6).toFixed(2), fill: mapColour(pAt(pr, hu)) });
    }
    svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: PY1 - PY0, fill: "none", stroke: "rgba(255,255,255,.3)", class: "probmap" });
    // the 0.5 line, where the call flips: c0 + c1 x pressure + c2 x humidity = 0, a straight line on this map
    const seg = [];
    if (Math.abs(c[2]) > 1e-9) for (const pr of PV) seg.push([pr, -(c[0] + c[1] * pr) / c[2]]);
    if (Math.abs(c[1]) > 1e-9) for (const hu of HV) seg.push([-(c[0] + c[2] * hu) / c[1], hu]);
    const inside = seg.filter(([pr, hu]) => pr >= PV[0] - 1e-6 && pr <= PV[1] + 1e-6 && hu >= HV[0] - 1e-6 && hu <= HV[1] + 1e-6);
    if (inside.length >= 2) {
      inside.sort((u, v) => u[0] - v[0] || u[1] - v[1]);
      const [u, v] = [inside[0], inside[inside.length - 1]];
      svgEl(svg, "line", { x1: sx(u[0]), y1: hy(u[1]), x2: sx(v[0]), y2: hy(v[1]), stroke: "#fff", "stroke-width": 3, "stroke-dasharray": "9 6", class: "boundary" });
    }
    // name the two sides at the map's most and least clear corners
    const corners = [[PV[0], HV[0]], [PV[0], HV[1]], [PV[1], HV[0]], [PV[1], HV[1]]].map(([pr, hu]) => ({ pr, hu, p: pAt(pr, hu) }));
    corners.sort((u, v) => v.p - u.p);
    const cornerLabel = (k, s2, fill) => {
      const left = k.pr === PV[0], top = k.hu === HV[1];
      txt(left ? PX0 + 12 : PX1 - 12, top ? PY0 + 18 : PY1 - 18, s2, { size: 18, bold: true, italic: true, fill, anchor: left ? "start" : "end" });
    };
    if (corners[0].p >= 0.5) cornerLabel(corners[0], "called clear", "#1a1208");
    if (corners[3].p < 0.5) cornerLabel(corners[3], "called cloudy", "#f3e6c4");
    // the nights: black = actually clear, white = actually cloudy (as on the held-back tallies)
    nights.forEach((d) => svgEl(svg, "circle", { cx: sx(d.x[0]), cy: hy(d.x[1]), r: 7, fill: d.y ? "#000" : "#fff", stroke: d.y ? "#fff" : "#000", "stroke-width": 1.5, class: "night" }));
    // axes
    for (let v = PV[0]; v <= PV[1]; v += 5) {
      svgEl(svg, "line", { x1: sx(v), x2: sx(v), y1: PY1, y2: PY1 + 7, stroke: "rgba(255,255,255,.6)" });
      txt(sx(v), PY1 + 22, String(v), { anchor: "middle", size: 17 });
    }
    txt((PX0 + PX1) / 2, PY1 + 50, "Barometer (hPa) · pressure_hpa", { anchor: "middle", size: 20 });
    for (let v = 0.4; v <= 1.0001; v += 0.1) {
      svgEl(svg, "line", { x1: PX0 - 7, x2: PX0, y1: hy(v), y2: hy(v), stroke: "rgba(255,255,255,.6)" });
      txt(PX0 - 12, hy(v), v.toFixed(1), { anchor: "end", size: 17 });
    }
    const yl = txt(0, 0, "Humidity · humidity_fraction", { anchor: "middle", size: 18 });
    yl.setAttribute("transform", `translate(${PX0 - 62} ${(PY0 + PY1) / 2}) rotate(-90)`);
    // key: the colour ramp, the 0.5 line and the two kinds of dot
    const KX = 470, KY = 98, KW = 200;
    for (let i = 0; i < 40; i++) svgEl(svg, "rect", { x: KX + (i * KW) / 40, y: KY - 7, width: KW / 40 + 0.5, height: 14, fill: mapColour(i / 39) });
    txt(KX - 8, KY, "probability_clear 0", { size: 15, anchor: "end" }); txt(KX + KW + 8, KY, "1", { size: 15 });
    svgEl(svg, "line", { x1: KX + KW + 34, x2: KX + KW + 60, y1: KY, y2: KY, stroke: "#fff", "stroke-width": 3, "stroke-dasharray": "6 4" });
    txt(KX + KW + 66, KY, "0.5", { size: 15 });
    svgEl(svg, "circle", { cx: 120, cy: KY + 28, r: 7, fill: "#000", stroke: "#fff", "stroke-width": 1.5 }); txt(133, KY + 28, "actually clear", { size: 15 });
    svgEl(svg, "circle", { cx: 270, cy: KY + 28, r: 7, fill: "#fff", stroke: "#000", "stroke-width": 1.5 }); txt(283, KY + 28, "actually cloudy", { size: 15 });
  }

  // ---------- tab 2: the spreads, one unit against each, then the bars ----------
  function drawScale() {
    txt(40, 54, "response: clear_night (clear / cloudy)  ·  predictors: pressure_hpa, humidity_fraction", { size: 18, fill: "#f3e6c4" });
    const SX0 = 260, SX1 = 920;
    cols.forEach((c, j) => {
      const top = 92 + j * 112, axisY = top + 52;
      txt(40, top + 22, c.label, { size: 21, bold: true });
      txt(40, top + 48, c.name, { size: 16, fill: "#cdbf9f" });
      txt(40, top + 70, st.scaled ? "standard deviations" : c.units, { size: 16, italic: true, fill: "#cdbf9f" });
      // axis range: raw in the reading's own units, scaled in SDs (-3..3); always wide enough to show one whole unit
      let lo, hi;
      if (st.scaled) { lo = -3; hi = 3; }
      else { const mn = Math.min(...c.values), mx = Math.max(...c.values); lo = mn - 0.15 * (mx - mn); hi = mx + 0.15 * (mx - mn); }
      const xv = (v) => SX0 + ((v - lo) / (hi - lo)) * (SX1 - SX0);
      svgEl(svg, "line", { x1: SX0, x2: SX1, y1: axisY, y2: axisY, stroke: "rgba(255,255,255,.5)" });
      for (const t of ticks(lo, hi, 5)) {
        svgEl(svg, "line", { x1: xv(t), x2: xv(t), y1: axisY, y2: axisY + 6, stroke: "rgba(255,255,255,.5)" });
        txt(xv(t), axisY + 20, fmtTick(t), { anchor: "middle", size: 15, fill: "#cdbf9f" });
      }
      c.values.forEach((v, i) => {
        const z = st.scaled ? (v - c.mean) / c.sd : v;
        svgEl(svg, "circle", { cx: xv(z), cy: axisY - 12 - ((i * 7) % 4) * 6, r: 5, fill: "#e8eef2", opacity: 0.75 });
      });
      // "one unit": the step a raw coefficient is measured over
      const u0 = st.scaled ? 0 : c.mean, u1 = u0 + 1, bx0 = xv(u0), bx1 = xv(u1), by = top + 2;
      const clipped = bx1 > SX1 + 2;
      const x1 = Math.min(bx1, SX1 + 30);
      svgEl(svg, "line", { x1: bx0, x2: x1, y1: by, y2: by, stroke: YES, "stroke-width": 5, "stroke-linecap": "round", class: "oneunit" });
      svgEl(svg, "line", { x1: bx0, x2: bx0, y1: by - 8, y2: by + 8, stroke: YES, "stroke-width": 3 });
      if (!clipped) svgEl(svg, "line", { x1: bx1, x2: bx1, y1: by - 8, y2: by + 8, stroke: YES, "stroke-width": 3 });
      const unitWord = st.scaled ? "one standard deviation" : c.units === "hPa" ? "one unit: 1 hPa" : "one unit: a change of 1.0";
      const label = clipped ? unitWord + ": runs far past every night →" : unitWord;
      const lx = clipped ? SX0 + 10 : Math.min(Math.max(bx0, bx1) + 12, SX1 - 10);
      txt(lx, by - 16, label, { size: 17, bold: true, fill: YES, anchor: clipped || lx < SX1 - 300 ? "start" : "end" });
    });
    // the bars
    const rows = coefRows(), BY0 = 340, BX0 = 330, BX1 = 900, mid = (BX0 + BX1) / 2;
    const maxAbs = Math.max(...rows.map((r) => Math.abs(r.value)));
    txt(40, BY0, st.scaled ? "Scaled coefficients (scale_variance = TRUE)" : "Raw coefficients (no scaling)", { size: 22, bold: true, fill: "#ffe39a" });
    txt(40, BY0 + 28, "ranked by size, ignoring the sign: arrange(desc(abs(value)))", { size: 16, italic: true, fill: "#cdbf9f" });
    svgEl(svg, "line", { x1: mid, x2: mid, y1: BY0 + 52, y2: BY0 + 222, stroke: "rgba(255,255,255,.5)" });
    txt(mid, BY0 + 236, "0", { anchor: "middle", size: 15, fill: "#cdbf9f" });
    rows.forEach((r, i) => {
      const yy = BY0 + 82 + i * 80, len = (Math.abs(r.value) / maxAbs) * (BX1 - mid - 20);
      const x0 = r.value >= 0 ? mid : mid - len;
      txt(40, yy, `${i + 1}. ${r.variable}`, { size: 20, bold: i === 0, cls: "coefname" });
      svgEl(svg, "rect", { x: x0, y: yy - 20, width: Math.max(2, len), height: 40, rx: 5, fill: r.value >= 0 ? BAR_POS : BAR_NEG, class: "coefbar", "data-variable": r.variable });
      const vtxt = fmtCoef(r.value), outside = len < 120;
      txt(r.value >= 0 ? (outside ? mid + len + 10 : mid + len - 10) : (outside ? mid - len - 10 : mid - len + 10), yy, vtxt,
        { size: 20, bold: true, fill: outside ? "#fff6e0" : "#0b1622", anchor: (r.value >= 0) === outside ? "start" : "end" });
    });
  }

  // ---------- tab 2: the tally ----------
  function drawJudge() {
    const pool = tallyPool(st.share), m = judge(pool), a = judge(alwaysNo(pool));
    const boards = [["The model", pool, m, 40], ["Always call cloudy", alwaysNo(pool), a, 500]];
    const cell = 21, cols20 = 20;
    for (const [name, cases, r, x0] of boards) {
      const top = 84;
      txt(x0, top, name, { size: 22, bold: true, fill: "#ffe39a" });
      svgEl(svg, "rect", { x: x0 - 3, y: top + 19, width: cols20 * cell + 6, height: Math.ceil(cases.length / cols20) * cell + 6, rx: 6, fill: BACKING });
      cases.forEach((c, i) => {
        const cx = x0 + (i % cols20) * cell, cy = top + 22 + Math.floor(i / cols20) * cell;
        const kind = c.truth === "yes" ? (c.call === "yes" ? "caught" : "missed") : (c.call === "yes" ? "wrongyes" : "rightno");
        const [fill, stroke] = TALLY_LOOK[kind], wrong = kind === "missed" || kind === "wrongyes";
        svgEl(svg, "rect", { x: cx + 2.5, y: cy + 2.5, width: cell - 5, height: cell - 5, rx: 3, fill, stroke, "stroke-width": wrong ? 2.5 : 0, class: "case " + kind });
      });
      const ry = top + 22 + 10 * cell + 30;
      txt(x0, ry, "Accuracy", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry, `${pct(r.accuracy)}  (${r.right} of ${r.n} right)`, { size: 22, bold: true, anchor: "end", cls: "acc" });
      txt(x0, ry + 32, "Caught", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry + 32, `${r.caught} of ${r.yes} actually clear`, { size: 22, bold: true, anchor: "end", fill: r.caught ? "#f3e6c4" : WRONG });
      txt(x0, ry + 64, "Missed", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry + 64, String(r.missed), { size: 22, bold: true, anchor: "end" });
    }
    // which is more accurate, and what that hides
    const vy = 474, noWins = a.accuracy >= m.accuracy;
    svgEl(svg, "rect", { x: 40, y: vy - 32, width: 880, height: 64, rx: 8, fill: noWins ? "rgba(255,122,92,.14)" : "rgba(127,211,255,.1)", stroke: noWins ? WRONG : BAR_POS });
    const [l1, l2] = noWins
      ? [`Always call cloudy is ${a.accuracy > m.accuracy ? "more accurate" : "just as accurate"} (${pct(a.accuracy)} against ${pct(m.accuracy)}),`, `and catches none of the ${a.yes} actually clear nights.`]
      : [`The model is more accurate (${pct(m.accuracy)} against ${pct(a.accuracy)})`, `and catches ${m.caught} of ${m.yes} actually clear nights.`];
    const vt = svgEl(svg, "text", { x: 480, y: vy - 11, "text-anchor": "middle", "dominant-baseline": "middle", "font-size": 19, "font-weight": "bold", fill: noWins ? "#ffc2b0" : "#d8f1ff", class: "verdict" });
    svgEl(vt, "tspan", { x: 480, dy: 0 }, l1 + " "); svgEl(vt, "tspan", { x: 480, dy: 23 }, l2);
    // legend
    const items = [["caught", "actually clear, called clear (caught)"], ["missed", "actually clear, called cloudy (missed)"],
      ["rightno", "actually cloudy, called cloudy"], ["wrongyes", "actually cloudy, called clear"]];
    items.forEach(([k, label], i) => {
      const lx = 40 + (i % 2) * 440, ly = 532 + Math.floor(i / 2) * 32, [f, s] = TALLY_LOOK[k], wrong = k === "missed" || k === "wrongyes";
      svgEl(svg, "rect", { x: lx - 3, y: ly - 12, width: 24, height: 24, rx: 4, fill: BACKING });
      svgEl(svg, "rect", { x: lx + 1, y: ly - 8, width: 16, height: 16, rx: 3, fill: f, stroke: s, "stroke-width": wrong ? 2.5 : 0 });
      txt(lx + 26, ly, label, { size: 16 });
    });
  }

  // ---------- tab 4: the confusion matrix, precision and recall ----------
  const CELL = { caught: TALLY_LOOK.caught, missed: TALLY_LOOK.missed, falseAlarm: TALLY_LOOK.wrongyes, rightNo: TALLY_LOOK.rightno };
  const matrixNow = () => confusion(tallyPool(st.share), st.cutoff);
  const f2 = (v) => (v == null ? "none called" : v.toFixed(2));
  function drawMatrix() {
    const m = matrixNow();
    txt(40, 24, `${m.n} held-back nights, ${m.yes} of them actually clear  ·  the model calls clear at a probability_clear of ${st.cutoff.toFixed(2)} or more`, { size: 18, fill: "#cdbf9f" });
    const GX = 170, GY = 112, CW = 200, CH = 172;
    txt(GX + CW, 58, "What the model called", { anchor: "middle", size: 19, bold: true, fill: "#ffe39a" });
    txt(GX + CW / 2, 88, "called cloudy", { anchor: "middle", size: 19, bold: true });
    txt(GX + CW * 1.5, 88, "called clear", { anchor: "middle", size: 19, bold: true });
    const rl = svgEl(svg, "text", { x: 46, y: GY + CH, fill: "#ffe39a", "font-size": 19, "font-weight": "bold", "text-anchor": "middle", "dominant-baseline": "middle", transform: `rotate(-90 46 ${GY + CH})` }, "What really happened");
    rl.setAttribute("class", "axislabel");
    txt(GX - 14, GY + CH / 2 - 10, "actually", { anchor: "end", size: 19, bold: true }); txt(GX - 14, GY + CH / 2 + 14, "cloudy", { anchor: "end", size: 19, bold: true });
    txt(GX - 14, GY + CH * 1.5 - 10, "actually", { anchor: "end", size: 19, bold: true }); txt(GX - 14, GY + CH * 1.5 + 14, "clear", { anchor: "end", size: 19, bold: true });
    // no before yes on both axes, the order R prints the book's confusion matrix in
    const cells = [["rightNo", "correctly called cloudy", "true negative", 0, 0], ["falseAlarm", "false alarm", "false positive", 1, 0],
      ["missed", "missed", "false negative", 0, 1], ["caught", "caught", "true positive", 1, 1]];
    for (const [k, name, term, c, r] of cells) {
      const x0 = GX + c * CW, y0 = GY + r * CH, [fill, stroke] = CELL[k], good = k === "caught" || k === "rightNo";
      svgEl(svg, "rect", { x: x0, y: y0, width: CW, height: CH, fill: good ? "rgba(127,211,255,.06)" : "rgba(255,122,92,.07)", stroke: "rgba(255,255,255,.35)", class: "mcell " + k });
      txt(x0 + CW / 2, y0 + 22, name, { anchor: "middle", size: 18, bold: true, fill: k === "falseAlarm" ? "#ffc2b0" : "#f3e6c4" });
      txt(x0 + CW / 2, y0 + 42, `(${term})`, { anchor: "middle", size: 15, italic: true, fill: "#cdbf9f" });
      const cnt = m[k], per = 22, sq = 8;
      if (cnt) svgEl(svg, "rect", { x: x0 + (CW - per * sq) / 2 - 3, y: y0 + 53, width: per * sq + 6, height: Math.ceil(cnt / per) * sq + 6, rx: 3, fill: BACKING });
      for (let i = 0; i < cnt; i++) {
        const cx = x0 + 3 + (i % per) * sq + (CW - 6 - per * sq) / 2, cy = y0 + 56 + Math.floor(i / per) * sq;
        svgEl(svg, "rect", { x: cx + 1.5, y: cy + 1.5, width: sq - 3, height: sq - 3, rx: 1, fill, stroke, "stroke-width": k === "missed" || k === "falseAlarm" ? 1.2 : 0 });
      }
      txt(x0 + CW / 2, y0 + CH - 18, String(cnt), { anchor: "middle", size: 30, bold: true, cls: "mcount " + k });
    }
    // precision and recall, each worked from its two cells
    const RX = 640;
    const block = (y0, title, def, num, den, v, numName, denName, colour) => {
      txt(RX, y0, title, { size: 24, bold: true, fill: colour });
      txt(RX, y0 + 28, def, { size: 16, italic: true, fill: "#cdbf9f" });
      txt(RX, y0 + 56, `${numName} ÷ (${numName} + ${denName})`, { size: 17 });
      txt(RX, y0 + 86, `${num} ÷ (${num} + ${den}) = ${f2(v)}`, { size: 22, bold: true, cls: title.toLowerCase() });
      svgEl(svg, "rect", { x: RX, y: y0 + 106, width: 260, height: 14, rx: 7, fill: "rgba(255,255,255,.12)" });
      if (v != null) svgEl(svg, "rect", { x: RX, y: y0 + 106, width: 260 * v, height: 14, rx: 7, fill: colour });
    };
    block(GY - 4, "Precision", "of the nights called yes, the share really clear", m.caught, m.falseAlarm, m.precision, "caught", "false alarms", "#ffe39a");
    block(GY + 176, "Recall", "of the clear nights, the share the model caught", m.caught, m.missed, m.recall, "caught", "missed", BAR_POS);
    txt(RX, GY + 334, `Accuracy: ${pct(m.accuracy)}`, { size: 17, fill: "#cdbf9f" });
    txt(RX, GY + 356, "(caught + correctly called cloudy)", { size: 15, italic: true, fill: "#cdbf9f" });
    txt(480, 520, "Lower the cut-off: more nights called clear, more caught and more false alarms, so recall rises and precision falls.", { anchor: "middle", size: 17, italic: true, fill: "#cdbf9f" });
  }

  function draw() {
    if (dead) return;
    svg.replaceChildren();
    if (st.tab === "several") drawSeveral(); else if (st.tab === "scale") drawScale(); else if (st.tab === "judge") drawJudge(); else drawMatrix();
    updateRead();
  }

  // ---------- panel ----------
  let bRaw = null, bScaled = null, sShare = null, sPr = null, sHu = null, sCut = null;
  function buildPanel() {
    F.mark(st.tab);
    F.setLesson(...LESSONS[st.tab]);
    F.ctl.replaceChildren();
    bRaw = bScaled = sShare = sPr = sHu = sCut = null;
    if (st.tab === "several") {
      sPr = slider("pressure_hpa coefficient", { min: B1[0], max: B1[1], step: 0.001, value: st.b1, fmt: (v) => v.toFixed(3), onInput: (v) => api.setSlopes({ pressure: v }) });
      sHu = slider("humidity_fraction coefficient", { min: B2[0], max: B2[1], step: 0.05, value: st.b2, fmt: (v) => v.toFixed(2), onInput: (v) => api.setSlopes({ humidity: v }) });
      sHu.el.style.color = HUM; sPr.el.style.color = PRS;
      F.ctl.append(sPr.el, sHu.el, el("div", "clsbrow").appendChild(button("Best fit", "bestfit", () => api.bestFit(), "Set both coefficients to the fit with the highest likelihood")).parentNode);
    } else if (st.tab === "scale") {
      const row = el("div", "clsbrow");
      bRaw = button("Raw", "tog rawbtn", () => api.setScaled(false), "Coefficients in each predictor's own units");
      bScaled = button("Scaled", "tog scalebtn", () => api.setScaled(true), "scale_variance = TRUE: every predictor in standard deviations");
      row.append(el("span", null, "Coefficients:"), bRaw, bScaled);
      const nrow = el("div", "clsbrow");
      nrow.append(el("span", null, "A night's probability:"), button("◀", "", () => stepNight(-1), "Previous night"), button("▶", "", () => stepNight(1), "Next night"));
      F.ctl.append(row, nrow);
    } else if (st.tab === "matrix") {
      sCut = slider("Cut-off (call clear at this probability_clear or more)", { min: 0.1, max: 0.9, step: 0.05, value: st.cutoff, fmt: (v) => v.toFixed(2),
        onInput: (v) => api.setCutoff(v) });
      const row = el("div", "clsbrow");
      row.append(button("0.3", "", () => api.setCutoff(0.3)), button("0.5", "", () => api.setCutoff(0.5)), button("0.7", "", () => api.setCutoff(0.7)));
      sShare = slider("How many held-back nights are actually clear", { min: 0.02, max: 0.5, step: 0.01, value: st.share, fmt: (v) => pct(v),
        onInput: (v) => api.setShare(v) });
      F.ctl.append(sCut.el, row, sShare.el);
    } else {
      sShare = slider("How many held-back nights are actually clear", { min: 0.02, max: 0.5, step: 0.01, value: st.share, fmt: (v) => pct(v),
        onInput: (v) => api.setShare(v) });
      const row = el("div", "clsbrow");
      row.append(button("Common: 30%", "", () => api.setShare(0.3)), button("Rare: 5%", "", () => api.setShare(0.05)));
      F.ctl.append(sShare.el, row);
    }
    updateRead();
  }
  function stepNight(dir) { const n = nights.length; st.night = ((st.night - 1 + dir + n) % n) + 1; save(); draw(); }
  const para = (html, cls) => { const p = el("p", cls || null); p.innerHTML = html; return p; };
  function updateRead() {
    const R = F.read; R.replaceChildren();
    if (st.tab === "several") {
      if (sHu) sHu.set(st.b2); if (sPr) sPr.set(st.b1);
    } else if (st.tab === "scale") {
      if (bRaw) { bRaw.setAttribute("aria-pressed", String(!st.scaled)); bScaled.setAttribute("aria-pressed", String(st.scaled)); }
      const t = el("table", "clsbtable coeftable");
      t.innerHTML = "<thead><tr><th>variable</th><th>value</th></tr></thead>";
      const tb = el("tbody");
      for (const r of coefRows()) { const tr = el("tr"); tr.innerHTML = `<td>${r.variable}</td><td>${fmtCoef(r.value)}</td>`; tb.appendChild(tr); }
      t.appendChild(tb); R.append(t);
      const p = probBoth(st.night);
      R.append(para(`Night ${p.night} (${p.x[0]} hPa, humidity ${p.x[1].toFixed(2)}): probability_clear <b>${p.raw.toFixed(3)}</b> from the raw model and <b>${p.scaled.toFixed(3)}</b> from the scaled one.`, "probline"));
    } else if (st.tab === "matrix") {
      if (sCut) sCut.set(st.cutoff); if (sShare) sShare.set(st.share);
    } else {
      if (sShare) sShare.set(st.share);
    }
  }

  const api = {
    ready: Promise.resolve(),
    setTab(k) { if (!TABS.some(([kk]) => kk === k)) throw new Error("scoreboard: setTab needs several/scale/judge/matrix"); st.tab = k; save(); buildPanel(); draw(); },
    tab: () => st.tab,
    setSlopes({ pressure, humidity } = {}) {
      if (pressure != null) st.b1 = Math.max(B1[0], Math.min(B1[1], +pressure));
      if (humidity != null) st.b2 = Math.max(B2[0], Math.min(B2[1], +humidity));
      save(); draw();
    },
    bestFit() { st.b1 = raw[1]; st.b2 = raw[2]; save(); draw(); },
    slopes: () => { const c = coefNow(); return { intercept: c[0], pressure: c[1], humidity: c[2], likelihoodShare: Math.exp(logLikAt(c) - bestLL) }; },
    setScaled(on) { st.scaled = !!on; save(); draw(); },
    scaled: () => st.scaled,
    coefs: coefRows,
    rawCoefs: () => raw.slice(),
    scaledCoefs: () => sc.coefs.slice(),
    probabilities: probBoth,
    setShare(v) { st.share = Math.max(0.02, Math.min(0.5, Math.round(+v * 100) / 100)); save(); draw(); },
    setCutoff(v) { st.cutoff = Math.max(0.1, Math.min(0.9, Math.round(+v * 100) / 100)); save(); draw(); },
    cutoff: () => st.cutoff,
    matrix: () => matrixNow(),
    share: () => st.share,
    tally() { const pool = tallyPool(st.share); return { model: judge(pool), alwaysNo: judge(alwaysNo(pool)) }; },
    destroy() { if (dead) return; dead = true; F.root.remove(); },
  };
  F.root.scoreboard = api;
  buildPanel();
  draw();
  return api;
}

function ticks(lo, hi, n) {
  const span = hi - lo, raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((k) => k * mag).find((s) => s >= raw) || raw;
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(Math.round(v / step) * step);
  return out;
}
const fmtTick = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 1 || v === 0 ? String(Math.round(v * 10) / 10) : v.toFixed(2));
// three significant figures, never e-notation, a real minus sign
const fmtCoef = (v) => { const a = Math.abs(v), s = a >= 100 ? a.toFixed(0) : a >= 10 ? a.toFixed(1) : a >= 1 ? a.toFixed(2) : a.toFixed(3); return (v < 0 ? "−" : "") + s; };
