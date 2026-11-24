// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `scoreboard` kind).
// The scoreboard: an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"scoreboard"`), built 2026-11-19 for the
// classification home world (classification/watch, day two: the plate archive). Lucas demos it on the projector on day
// two; students return to it at home. One tab per day-two section of the chapter, only its own controls, a Lesson in
// the book's wording:
//
//   1 Several predictors            the S-curve of probability_yes against the barometer at the humidity on a slider
//                                   (ghost curves at 0.40 and 0.95 show how far humidity slides it), the fitted
//                                   equation (log-odds = intercept + coefficient x each predictor) and the sum worked
//                                   out live for the chosen readings. Uses the raw fit of the same 48 nights.
//   2 Which predictors matter most  two invented readings in very different units (a barometer in hPa, humidity as a
//                                   0-1 fraction): each reading's spread with "one unit" drawn against it, and the
//                                   model's coefficients as bars. Raw, humidity's dwarfs the barometer's; "Scaled"
//                                   (scale_variance = TRUE) puts both in standard deviations and the ranking flips.
//                                   A night's probability_yes is shown from both models: scaling changes units, not
//                                   the model.
//   3 Judging a classifier          a held-back tally of 200 invented nights, the model's calls at the 0.5 cut-off
//                                   beside "always say no": accuracy, caught and missed. A slider sets how rare yes
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
//   s.setTab("several"|"scale"|"judge"); s.setReadings({pressure, humidity}); s.readings(); s.tab(); s.setScaled(bool); s.scaled(); s.coefs(); s.rawCoefs(); s.scaledCoefs();
//   s.probabilities(night); s.setShare(0..1); s.share(); s.tally(); s.setCutoff(0.1..0.9); s.cutoff(); s.matrix(); s.ready; s.destroy().
//   The root element carries the API as `.scoreboard` for tests.
import { makeNights, NIGHT_PREDICTORS, fitLogistic, scaledCoefs, logistic, tallyPool, judge, alwaysNo, confusion, mean, sd }
  from "./classification_math.js?v=183";
import { shell, svgEl, el, button, slider, pct } from "./classification_ui.js?v=183";

const TABS = [["several", "Several predictors"], ["scale", "Which predictors matter most"], ["judge", "Judging a classifier"], ["matrix", "Confusion matrix"]];
const LESSONS = {
  several: ["With several predictors, logistic regression adds up one term per predictor (the predictor times its coefficient) plus an intercept. That sum is the log-odds, and the S-curve turns it into a probability_yes between 0 and 1. A coefficient's sign says which way its predictor pushes the probability: higher pressure raises the chance of a clear night, and more humidity lowers it, so changing the humidity slides the whole S-curve along the barometer.",
    "several predictors, and predicting held-back cases"],
  scale: ["Raw coefficients mostly reflect units: a predictor that barely changes from one case to the next gets a large coefficient for that reason alone. Scale each predictor to a mean of zero and a standard deviation of one, then rank the coefficients by size, ignoring the sign. Scaling changes the units of the coefficients, not the model: every case keeps the same probability.",
    "which predictors matter most"],
  judge: ["Accuracy is the share of calls that are right. When yes is rare, calling every case no scores a high accuracy and catches nothing. So report how many yes-cases were caught and how many were missed beside accuracy, never accuracy alone.",
    "judging a classifier on held-back cases"],
  matrix: ["A confusion matrix sorts every held-back case by what really happened and what the model called, giving four counts: caught (true positives), missed (false negatives), false alarms (false positives) and correctly called no (true negatives). Two numbers come from it. Precision is caught ÷ (caught + false alarms): of the cases the model called yes, the share that really were yes. Recall is caught ÷ (caught + missed): of the cases that really were yes, the share the model caught. Lowering the cut-off raises recall and lowers precision; raising it does the opposite.",
    "judging a classifier on held-back cases"],
};
const W = 960, H = 600;
const YES = "#ffc861", NO = "#8fb3d9", WRONG = "#ff7a5c", BAR_POS = "#7fd3ff", BAR_NEG = "#ff9f7a";

export function mount(host, opts = {}) {
  const nights = makeNights();
  const X = nights.map((d) => d.x), y = nights.map((d) => d.y);
  const raw = fitLogistic(X, y);
  const sc = scaledCoefs(X, y);
  const cols = NIGHT_PREDICTORS.map((p, j) => ({ ...p, values: X.map((r) => r[j]), mean: mean(X.map((r) => r[j])), sd: sd(X.map((r) => r[j])) }));
  const s0 = opts.pegs && typeof opts.pegs === "object" ? opts.pegs : {};
  const st = {
    tab: TABS.some(([k]) => k === s0.tab) ? s0.tab : "several",
    pressure: Number.isFinite(s0.pressure) ? s0.pressure : 1015,
    humidity: Number.isFinite(s0.humidity) ? s0.humidity : 0.6,
    scaled: !!s0.scaled,
    share: Number.isFinite(s0.share) ? s0.share : 0.3,
    night: Number.isFinite(s0.night) ? s0.night : 7,
    cutoff: Number.isFinite(s0.cutoff) ? Math.max(0.1, Math.min(0.9, s0.cutoff)) : 0.5,
  };
  let dead = false;
  const save = () => opts.onPegs && opts.onPegs({ tab: st.tab, scaled: st.scaled, share: st.share, cutoff: st.cutoff, night: st.night, pressure: st.pressure, humidity: st.humidity });

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

  // ---------- tab 1: several predictors. The S-curve against the barometer at the humidity on the slider, the
  // fitted equation with its coefficients, and the sum worked out live for one night's readings. Dots are the 48
  // training nights, brightest where their humidity is close to the slider's.
  const HUM = "#c9a7ff", PRS = BAR_POS;
  const PX0 = 100, PX1 = 930, PY0 = 156, PY1 = 506, PV = [994, 1034];
  const sx = (v) => PX0 + ((v - PV[0]) / (PV[1] - PV[0])) * (PX1 - PX0);
  const sy = (p) => PY1 - ((p + 0.07) / 1.17) * (PY1 - PY0);
  const logOdds = (pr, hu) => raw[0] + raw[1] * pr + raw[2] * hu;
  function parts(pr, hu) { const a = raw[1] * pr, b = raw[2] * hu, z = raw[0] + a + b; return { a, b, z, p: logistic(z) }; }
  function eqLine(yy, pieces, size = 19) {   // one line of the equation, each piece [text, colour?, bold?]
    const t = svgEl(svg, "text", { x: 40, y: yy, "font-size": size, fill: "#f3e6c4", "dominant-baseline": "middle", class: "eq" });
    for (const [s2, c, b, sup] of pieces) svgEl(t, "tspan", { fill: c || null, "font-weight": b ? "bold" : null, "baseline-shift": sup ? "super" : null, "font-size": sup ? Math.round(size * 0.72) : null }, s2);
    return t;
  }
  const neg = (v, d) => (v < 0 ? "\u2212" : "") + Math.abs(v).toFixed(d);
  const sgn = (v, d) => (v < 0 ? " \u2212 " : " + ") + Math.abs(v).toFixed(d);
  function drawSeveral() {
    txt(40, 12, "Each dot is one night at the plate archive: its barometer reading,", { size: 16, italic: true, fill: "#cdbf9f" });
    txt(40, 31, "and whether it was clear enough to photograph.", { size: 16, italic: true, fill: "#cdbf9f" });
    eqLine(60, [["log-odds = ", null, true], [neg(raw[0], 3)], [sgn(raw[1], 5), PRS, true], [" \u00d7 pressure_hpa", PRS], [sgn(raw[2], 3), HUM, true], [" \u00d7 humidity_fraction", HUM]]);
    eqLine(90, [["probability_yes = 1 / (1 + e", null, true], ["\u2212log-odds", null, true, true], [")", null, true]], 19);
    const q = parts(st.pressure, st.humidity);
    eqLine(116, [[`at ${st.pressure} hPa and humidity ${st.humidity.toFixed(2)}:  `], [neg(raw[0], 3)], [sgn(q.a, 3), PRS], [sgn(q.b, 3), HUM],
      [` = ${neg(q.z, 3)}`, null, true], ["   \u2192   probability_yes = ", null], [q.p.toFixed(2), "#ffe39a", true]], 18).setAttribute("class", "eq eqlive");
    // axes
    svgEl(svg, "rect", { x: PX0, y: PY0, width: PX1 - PX0, height: PY1 - PY0, fill: "rgba(255,255,255,.025)", stroke: "rgba(255,255,255,.18)" });
    for (let v = PV[0]; v <= PV[1]; v += 5) {
      svgEl(svg, "line", { x1: sx(v), x2: sx(v), y1: PY1, y2: PY1 + 7, stroke: "rgba(255,255,255,.6)" });
      txt(sx(v), PY1 + 22, String(v), { anchor: "middle", size: 17 });
    }
    txt((PX0 + PX1) / 2, PY1 + 50, "Barometer (hPa) \u00b7 pressure_hpa", { anchor: "middle", size: 20 });
    for (const v of [0, 0.5, 1]) {
      svgEl(svg, "line", { x1: PX0, x2: PX1, y1: sy(v), y2: sy(v), stroke: "rgba(255,255,255,.28)", "stroke-dasharray": "6 6" });
      txt(PX0 - 12, sy(v), String(v), { anchor: "end", size: 17 });
    }
    const yl = txt(0, 0, "probability_yes (clear night)", { anchor: "middle", size: 18 });
    yl.setAttribute("transform", `translate(${PX0 - 56} ${(PY0 + PY1) / 2}) rotate(-90)`);
    // ghost curves at the ends of the humidity range, then the live one
    const path = (hu, attrs) => {
      const pts = []; for (let i = 0; i <= 200; i++) { const v = PV[0] + (i / 200) * (PV[1] - PV[0]); pts.push(`${i ? "L" : "M"}${sx(v).toFixed(1)} ${sy(logistic(logOdds(v, hu))).toFixed(1)}`); }
      return svgEl(svg, "path", { d: pts.join(""), fill: "none", "stroke-linecap": "round", ...attrs });
    };
    for (const hu of [0.4, 0.95]) {
      path(hu, { stroke: HUM, "stroke-width": 2, opacity: 0.35, "stroke-dasharray": "6 5" });
      const mid = (-raw[0] - raw[2] * hu) / raw[1], lab = `humidity ${hu.toFixed(2)}`, o = { size: 15, fill: HUM, opacity: 0.85, anchor: "end" };
      if (hu < 0.5) txt(sx(mid) - 8, sy(0.5) - 16, lab, o);
      else txt(PX1 - 8, sy(logistic(logOdds(PV[1], hu))) + 22, lab, o);
    }
    nights.forEach((d, i) => {
      const w = Math.max(0.12, Math.exp(-(((d.x[1] - st.humidity) / 0.1) ** 2)));
      svgEl(svg, "circle", { cx: sx(d.x[0]), cy: sy(d.y) + ((i * 5) % 3 - 1) * 5, r: 7, fill: d.y ? YES : NO, opacity: w, stroke: "rgba(0,0,0,.5)", class: "night" });
    });
    path(st.humidity, { stroke: "#7fd3ff", "stroke-width": 4, class: "scurve" });
    // the reader at the chosen pressure
    svgEl(svg, "line", { x1: sx(st.pressure), x2: sx(st.pressure), y1: PY0, y2: PY1, stroke: "#ffe39a", "stroke-width": 2, "stroke-dasharray": "5 5" });
    svgEl(svg, "circle", { cx: sx(st.pressure), cy: sy(q.p), r: 8, fill: "#ffe39a", stroke: "#fff", "stroke-width": 2, class: "reader" });
  }

  // ---------- tab 2: the spreads, one unit against each, then the bars ----------
  function drawScale() {
    txt(40, 54, "response: clear_night (yes / no)  ·  predictors: pressure_hpa, humidity_fraction", { size: 18, fill: "#f3e6c4" });
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
    txt(40, 54, `Clear nights (yes): ${m.yes} of ${m.n}  ·  the model calls yes at a probability of 0.5 or more`, { size: 19, fill: "#f3e6c4" });
    const boards = [["The model", pool, m, 40], ["Always say no", alwaysNo(pool), a, 500]];
    const cell = 21, cols20 = 20;
    for (const [name, cases, r, x0] of boards) {
      const top = 84;
      txt(x0, top, name, { size: 22, bold: true, fill: "#ffe39a" });
      cases.forEach((c, i) => {
        const cx = x0 + (i % cols20) * cell, cy = top + 22 + Math.floor(i / cols20) * cell;
        const kind = c.truth === "yes" ? (c.call === "yes" ? "caught" : "missed") : (c.call === "yes" ? "wrongyes" : "rightno");
        const fill = { caught: YES, missed: "none", wrongyes: WRONG, rightno: "rgba(143,179,217,.28)" }[kind];
        const stroke = { caught: "#1a1208", missed: YES, wrongyes: "#1a1208", rightno: "none" }[kind];
        svgEl(svg, "rect", { x: cx + 2, y: cy + 2, width: cell - 4, height: cell - 4, rx: 3, fill, stroke, "stroke-width": kind === "missed" ? 2.5 : 1, class: "case " + kind });
      });
      const ry = top + 22 + 10 * cell + 30;
      txt(x0, ry, "Accuracy", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry, `${pct(r.accuracy)}  (${r.right} of ${r.n} right)`, { size: 22, bold: true, anchor: "end", cls: "acc" });
      txt(x0, ry + 32, "Caught", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry + 32, `${r.caught} of ${r.yes} clear nights`, { size: 22, bold: true, anchor: "end", fill: r.caught ? YES : WRONG });
      txt(x0, ry + 64, "Missed", { size: 19, fill: "#cdbf9f" });
      txt(x0 + 410, ry + 64, String(r.missed), { size: 22, bold: true, anchor: "end" });
    }
    // which is more accurate, and what that hides
    const vy = 470, noWins = a.accuracy >= m.accuracy;
    svgEl(svg, "rect", { x: 40, y: vy - 22, width: 880, height: 44, rx: 8, fill: noWins ? "rgba(255,122,92,.14)" : "rgba(127,211,255,.1)", stroke: noWins ? WRONG : BAR_POS });
    txt(480, vy, noWins
      ? `Always say no is ${a.accuracy > m.accuracy ? "more accurate" : "just as accurate"} (${pct(a.accuracy)} against ${pct(m.accuracy)}), and catches none of the ${a.yes} clear nights.`
      : `The model is more accurate (${pct(m.accuracy)} against ${pct(a.accuracy)}) and catches ${m.caught} of ${m.yes} clear nights.`,
      { anchor: "middle", size: 19, bold: true, fill: noWins ? "#ffc2b0" : "#d8f1ff", cls: "verdict" });
    // legend
    const ly = 530, items = [["caught", YES, "#1a1208", "clear, called yes (caught)"], ["missed", "none", YES, "clear, called no (missed)"],
      ["wrongyes", WRONG, "#1a1208", "cloudy, called yes"], ["rightno", "rgba(143,179,217,.28)", "none", "cloudy, called no"]];
    items.forEach(([k, f, s, label], i) => {
      const lx = 40 + i * 225;
      svgEl(svg, "rect", { x: lx, y: ly - 9, width: 18, height: 18, rx: 3, fill: f, stroke: s, "stroke-width": k === "missed" ? 2.5 : 1 });
      txt(lx + 26, ly, label, { size: 16 });
    });
  }

  // ---------- tab 4: the confusion matrix, precision and recall ----------
  const CELL = { caught: [YES, "#1a1208"], missed: ["none", YES], falseAlarm: [WRONG, "#1a1208"], rightNo: ["rgba(143,179,217,.28)", "none"] };
  const matrixNow = () => confusion(tallyPool(st.share), st.cutoff);
  const f2 = (v) => (v == null ? "none called" : v.toFixed(2));
  function drawMatrix() {
    const m = matrixNow();
    txt(40, 24, `${m.n} held-back nights, ${m.yes} of them clear (yes)  ·  the model calls yes at a probability of ${st.cutoff.toFixed(2)} or more`, { size: 18, fill: "#cdbf9f" });
    const GX = 170, GY = 112, CW = 200, CH = 172;
    txt(GX + CW, 58, "What the model called", { anchor: "middle", size: 19, bold: true, fill: "#ffe39a" });
    txt(GX + CW / 2, 88, "no", { anchor: "middle", size: 19, bold: true });
    txt(GX + CW * 1.5, 88, "yes", { anchor: "middle", size: 19, bold: true });
    const rl = svgEl(svg, "text", { x: 46, y: GY + CH, fill: "#ffe39a", "font-size": 19, "font-weight": "bold", "text-anchor": "middle", "dominant-baseline": "middle", transform: `rotate(-90 46 ${GY + CH})` }, "What really happened");
    rl.setAttribute("class", "axislabel");
    txt(GX - 14, GY + CH / 2 - 10, "cloudy", { anchor: "end", size: 19, bold: true }); txt(GX - 14, GY + CH / 2 + 14, "(no)", { anchor: "end", size: 16 });
    txt(GX - 14, GY + CH * 1.5 - 10, "clear", { anchor: "end", size: 19, bold: true }); txt(GX - 14, GY + CH * 1.5 + 14, "(yes)", { anchor: "end", size: 16 });
    // no before yes on both axes, the order R prints the book's confusion matrix in
    const cells = [["rightNo", "correctly called no", "true negative", 0, 0], ["falseAlarm", "false alarm", "false positive", 1, 0],
      ["missed", "missed", "false negative", 0, 1], ["caught", "caught", "true positive", 1, 1]];
    for (const [k, name, term, c, r] of cells) {
      const x0 = GX + c * CW, y0 = GY + r * CH, [fill, stroke] = CELL[k], good = k === "caught" || k === "rightNo";
      svgEl(svg, "rect", { x: x0, y: y0, width: CW, height: CH, fill: good ? "rgba(127,211,255,.06)" : "rgba(255,122,92,.07)", stroke: "rgba(255,255,255,.35)", class: "mcell " + k });
      txt(x0 + CW / 2, y0 + 22, name, { anchor: "middle", size: 18, bold: true, fill: k === "falseAlarm" ? "#ffc2b0" : "#f3e6c4" });
      txt(x0 + CW / 2, y0 + 42, `(${term})`, { anchor: "middle", size: 15, italic: true, fill: "#cdbf9f" });
      const cnt = m[k], per = 22, sq = 8;
      for (let i = 0; i < cnt; i++) {
        const cx = x0 + 3 + (i % per) * sq + (CW - 6 - per * sq) / 2, cy = y0 + 56 + Math.floor(i / per) * sq;
        svgEl(svg, "rect", { x: cx + 1, y: cy + 1, width: sq - 2, height: sq - 2, rx: 1, fill, stroke, "stroke-width": k === "missed" ? 1.2 : 0.6 });
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
    txt(RX, GY + 340, `Accuracy: ${pct(m.accuracy)}  (caught + correctly called no)`, { size: 17, fill: "#cdbf9f" });
    txt(480, 520, "Lower the cut-off: more yes calls, more caught and more false alarms, so recall rises and precision falls.", { anchor: "middle", size: 17, italic: true, fill: "#cdbf9f" });
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
      sHu = slider("Humidity (humidity_fraction)", { min: 0.4, max: 0.95, step: 0.01, value: st.humidity, fmt: (v) => v.toFixed(2), onInput: (v) => api.setReadings({ humidity: v }) });
      sPr = slider("Barometer (pressure_hpa)", { min: PV[0], max: PV[1], step: 1, value: st.pressure, fmt: (v) => v + " hPa", onInput: (v) => api.setReadings({ pressure: v }) });
      sHu.el.style.color = HUM; sPr.el.style.color = PRS;
      F.ctl.append(sHu.el, sPr.el);
    } else if (st.tab === "scale") {
      const row = el("div", "clsbrow");
      bRaw = button("Raw", "tog rawbtn", () => api.setScaled(false), "Coefficients in each predictor's own units");
      bScaled = button("Scaled", "tog scalebtn", () => api.setScaled(true), "scale_variance = TRUE: every predictor in standard deviations");
      row.append(el("span", null, "Coefficients:"), bRaw, bScaled);
      const nrow = el("div", "clsbrow");
      nrow.append(el("span", null, "A night's probability:"), button("◀", "", () => stepNight(-1), "Previous night"), button("▶", "", () => stepNight(1), "Next night"));
      F.ctl.append(row, nrow);
    } else if (st.tab === "matrix") {
      sCut = slider("Cut-off (call yes at this probability or more)", { min: 0.1, max: 0.9, step: 0.05, value: st.cutoff, fmt: (v) => v.toFixed(2),
        onInput: (v) => api.setCutoff(v) });
      const row = el("div", "clsbrow");
      row.append(button("0.3", "", () => api.setCutoff(0.3)), button("0.5", "", () => api.setCutoff(0.5)), button("0.7", "", () => api.setCutoff(0.7)));
      sShare = slider("How many held-back nights are clear (yes)", { min: 0.02, max: 0.5, step: 0.01, value: st.share, fmt: (v) => pct(v),
        onInput: (v) => api.setShare(v) });
      F.ctl.append(sCut.el, row, sShare.el);
    } else {
      sShare = slider("How many held-back nights are clear (yes)", { min: 0.02, max: 0.5, step: 0.01, value: st.share, fmt: (v) => pct(v),
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
      if (sHu) sHu.set(st.humidity); if (sPr) sPr.set(st.pressure);
      R.append(para(`<span style="color:${PRS}">pressure_hpa</span>: coefficient <b>${fmtCoef(raw[1])}</b>, positive, so more pressure means a higher probability of a clear night.`),
        para(`<span style="color:${HUM}">humidity_fraction</span>: coefficient <b>${fmtCoef(raw[2])}</b>, negative, so more humidity means a lower probability, and the S-curve slides right.`));
    } else if (st.tab === "scale") {
      if (bRaw) { bRaw.setAttribute("aria-pressed", String(!st.scaled)); bScaled.setAttribute("aria-pressed", String(st.scaled)); }
      const t = el("table", "clsbtable coeftable");
      t.innerHTML = "<thead><tr><th>variable</th><th>value</th></tr></thead>";
      const tb = el("tbody");
      for (const r of coefRows()) { const tr = el("tr"); tr.innerHTML = `<td>${r.variable}</td><td>${fmtCoef(r.value)}</td>`; tb.appendChild(tr); }
      t.appendChild(tb); R.append(t);
      const p = probBoth(st.night);
      R.append(para(`Night ${p.night} (${p.x[0]} hPa, humidity ${p.x[1].toFixed(2)}): probability_yes <b>${p.raw.toFixed(3)}</b> from the raw model and <b>${p.scaled.toFixed(3)}</b> from the scaled one.`, "probline"));
    } else if (st.tab === "matrix") {
      if (sCut) sCut.set(st.cutoff); if (sShare) sShare.set(st.share);
      const m = matrixNow();
      R.append(para(`At a cut-off of <b>${st.cutoff.toFixed(2)}</b>: caught <b>${m.caught}</b>, missed <b>${m.missed}</b>, false alarms <b>${m.falseAlarm}</b>, correctly called no <b>${m.rightNo}</b>.`),
        para(`Precision <b>${f2(m.precision)}</b> · recall <b>${f2(m.recall)}</b> · accuracy <b>${pct(m.accuracy)}</b>.`));
    } else {
      if (sShare) sShare.set(st.share);
      const pool = tallyPool(st.share), m = judge(pool), a = judge(alwaysNo(pool));
      R.append(para(`Clear nights: <b>${m.yes}</b> of ${m.n} (${pct(m.yes / m.n)}).`),
        para(`The model: accuracy <b>${pct(m.accuracy)}</b>, caught <b>${m.caught}</b>, missed <b>${m.missed}</b>.`),
        para(`Always say no: accuracy <b>${pct(a.accuracy)}</b>, caught <b>0</b>, missed <b>${a.missed}</b>.`));
    }
  }

  const api = {
    ready: Promise.resolve(),
    setTab(k) { if (!TABS.some(([kk]) => kk === k)) throw new Error("scoreboard: setTab needs several/scale/judge/matrix"); st.tab = k; save(); buildPanel(); draw(); },
    tab: () => st.tab,
    setReadings({ pressure, humidity } = {}) {
      if (pressure != null) st.pressure = Math.max(PV[0], Math.min(PV[1], Math.round(+pressure)));
      if (humidity != null) st.humidity = Math.max(0.4, Math.min(0.95, Math.round(+humidity * 100) / 100));
      save(); draw();
    },
    readings: () => ({ pressure: st.pressure, humidity: st.humidity, ...parts(st.pressure, st.humidity) }),
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
