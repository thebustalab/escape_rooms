// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `bank` kind).
// The showpiece bank: an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"bank"`), built 2026-11-24 from the
// approved prototype rooms/classification/observatory/_scratch/showpiece_bank/showpiece_bank.html (Good Seeing's dome).
// Twelve logistic models applied to one row of predictors, as a machine: four knurled shaft knobs set the readings;
// every card is geared to every shaft by its own gear (size = |weight|, a reversing idler for a negative weight); the
// card's differential sums the four drives on top of its own starting offset into a log-odds, which pushes a carriage
// sideways; a bead riding an S-shaped slot turns that into a probability; a lamp lights when the bead clears the red
// cut-off wire (one knob for the whole bank). The plate at each card's foot is engraved with the card's pointing
// (dome bearing + telescope altitude): a label, never an output of the bank.
//
// This module OWNS the maths (the pure exports below): the engine draws with them, and the scenario's tests and
// _scratch scripts import them. The card data come from the hotspot's own inline fields (`cards`, `inputs`, `span`,
// `cutStops`, `cutDefault`, `start`), handed over by openInstrument as `o.hotspot`. Nothing here knows any night's
// readings: those live in the scenario's tests only.
//
//   const b = mountBank(hostEl, { hotspot, pegs?, onPegs?({xs, cut}), sound? });
//   b.readings(); b.setReading(i, v); b.setReadings([..]); b.cut(); b.setCut(c); b.read(); b.lit(); b.isSettled();
//   b.knobCentre(k); b.knobPoint(k, value)   (client px; k 0..3 the shafts, 4 the cut-off: for real pointer tests)
//   b.ready; b.destroy().   The root element carries the API as `.showpieceBank` for tests.
//
// Code-drawn SVG, no art and no geometry. On a narrow screen the drawing keeps a minimum width and scrolls inside
// its box; it is never restacked beyond the prototype's own two arrangements (six columns landscape, four portrait).

// ------------------------------------------------------------------------------------------------ the maths
export const sigmoid = (L) => 1 / (1 + Math.exp(-L));
export const logit = (p) => Math.log(p / (1 - p));
// a shaft turns by (reading - centre): every shaft is zeroed at an ordinary night
export const shaftTurn = (input, x) => x - input.centre;
// the log-odds a card's differential is driven to: its offset b plus each shaft's turn through its gear w
export function logOdds(card, inputs, xs) {
  let L = card.b;
  for (let i = 0; i < inputs.length; i++) L += card.w[i] * shaftTurn(inputs[i], xs[i]);
  return L;
}
export const probability = (card, inputs, xs) => sigmoid(logOdds(card, inputs, xs));
// the carriage travels log-odds -span..+span between its end stops
export const carriage = (L, span) => Math.max(-span, Math.min(span, L));
// the bead's height in the S-shaped slot (what the card shows and what the lamp reads)
export const beadHeight = (card, inputs, xs, span) => sigmoid(carriage(logOdds(card, inputs, xs), span));
export const isLit = (p, cut) => p >= cut - 1e-12;
// indices of the cards whose lamp is lit at readings xs and cut-off cut
export function litSet(bank, xs, cut) {
  const out = [];
  bank.cards.forEach((c, j) => { if (isLit(beadHeight(c, bank.inputs, xs, bank.span), cut)) out.push(j); });
  return out;
}
// the 5-digit pointing engraved on a card's plate: bearing (3 digits) + altitude (2 digits)
export const pointingCode = (card) => String(card.bearing).padStart(3, "0") + String(card.altitude).padStart(2, "0");
// {moon: m, ...} -> [m, ...] in the bank's input order
export const readingsArray = (inputs, byKey) => inputs.map((inp) => byKey[inp.key]);
export function stepValues(input) {
  const out = [];
  for (let v = input.min; v <= input.max + 1e-9; v += input.step) out.push(Math.round(v * 1e6) / 1e6);
  return out;
}
export function snap(input, v) {
  const vals = stepValues(input);
  let best = vals[0], bd = Infinity;
  for (const s of vals) { const d = Math.abs(s - +v); if (d < bd) { bd = d; best = s; } }
  return best;
}
// knob dials: a shaft knob sweeps 270 degrees min..max; the cut-off knob's stops spread over 240 degrees
export const knobAngle = (input, v) => -135 + 270 * (v - input.min) / (input.max - input.min);
export const cutKnobAngle = (stops, c) => -120 + 240 * stops.indexOf(c) / (stops.length - 1);
export function valueAtAngle(input, a) {
  let best = input.min, bd = Infinity;
  for (const v of stepValues(input)) { const d = Math.abs(knobAngle(input, v) - a); if (d < bd) { bd = d; best = v; } }
  return best;
}
export function cutAtAngle(stops, a) {
  let best = stops[0], bd = Infinity;
  for (const c of stops) { const d = Math.abs(cutKnobAngle(stops, c) - a); if (d < bd) { bd = d; best = c; } }
  return best;
}
// The bank as the hotspot carries it, checked: a malformed one throws (openInstrument then shows its error card).
export function bankFrom(src) {
  const s = src || {};
  const num = (v) => typeof v === "number" && Number.isFinite(v);
  const cards = s.cards, inputs = s.inputs;
  if (!Array.isArray(inputs) || !inputs.length || !inputs.every((i) => i && num(i.min) && num(i.max) && num(i.step) && num(i.centre) && i.max > i.min && i.step > 0))
    throw new Error("showpiece bank: `inputs` must be [{key, name, min, max, step, centre}]");
  if (!Array.isArray(cards) || !cards.length || !cards.every((c) => c && num(c.b) && Array.isArray(c.w) && c.w.length === inputs.length && c.w.every(num)))
    throw new Error("showpiece bank: `cards` must be [{name, b, w[one per input], bearing, altitude}]");
  const span = num(s.span) && s.span > 0 ? s.span : 6;
  const cutStops = Array.isArray(s.cutStops) && s.cutStops.length > 1 && s.cutStops.every(num) ? s.cutStops.slice() : [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95];
  const cutDefault = cutStops.includes(s.cutDefault) ? s.cutDefault : cutStops[Math.floor(cutStops.length / 2)];
  const start = Array.isArray(s.start) && s.start.length === inputs.length ? s.start.map((v, i) => snap(inputs[i], v)) : inputs.map((i) => snap(i, i.centre));
  return { cards, inputs, span, cutStops, cutDefault, start };
}

// ------------------------------------------------------------------------------------------------ the machine
const NS = "http://www.w3.org/2000/svg";
const SHAFT_Y = [158, 183, 208, 233];            // within a card, the four shafts
const GEAR_X = [42, 78, 114, 150];               // gears staggered along each card so they never overlap
const PLOT = { x0: 30, x1: 176, y0: 14, y1: 92 };   // the S-slot box within a card: y0 = 100 %, y1 = 0 %
const MIN_SCALE = 0.5;                           // narrowest drawing (fraction of its own units) before it scrolls
const HINT = "Turn each shaft's knob (bottom) to the reading from its deck instrument. Every dial is geared to " +
  "every shaft, each by its own gear, so one turn moves all twelve by different amounts. Each card's bead rides an " +
  "S-shaped slot: the gears push it sideways, the S lifts it. The lamp lights when the bead rises past the red " +
  "cut-off wire, which the right-hand knob sets for the whole bank. The plate at each card's foot is engraved with " +
  "where to point: dome bearing and telescope altitude.";
const CSS = `
.spb { width: 100%; min-width: 0; flex: 1 1 auto; box-sizing: border-box; padding: 8px; border-radius: 4px;
  background: radial-gradient(ellipse at 50% 30%, #3a2818 0%, #1b130d 75%); color: #e9dcc0;
  font-family: Georgia, "Times New Roman", serif; -webkit-user-select: none; user-select: none; }
.spb-frame { position: relative; }
.spb-scroll { overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; }
.spb-more { position: absolute; top: 0; right: 0; bottom: 0; width: 34px; pointer-events: none; display: none;
  align-items: center; justify-content: flex-end; padding-right: 4px; font-size: 26px; color: #f0d9a8;
  background: linear-gradient(to right, rgba(27,19,13,0), rgba(27,19,13,.9)); }
.spb-frame.more .spb-more { display: flex; }
.spb-svg { display: block; }
.spb-knobhit { touch-action: none; cursor: grab; }
.spb-hint { font-size: 13px; color: #c9b48d; max-width: 520px; margin: 8px 0 0; line-height: 1.35; }`;
let _uid = 0;

export function mountBank(host, o = {}) {
  const B = bankFrom(o.hotspot || o.bank || o);
  const { cards, inputs, span, cutStops } = B;
  const NI = inputs.length, NK = NI + 1;
  const s0 = o.pegs && typeof o.pegs === "object" ? o.pegs : {};
  const xs = Array.isArray(s0.xs) && s0.xs.length === NI ? s0.xs.map((v, i) => snap(inputs[i], v)) : B.start.slice();
  const xsDisp = xs.slice();                      // what the machine shows: glides towards xs
  let cut = cutStops.includes(s0.cut) ? s0.cut : B.cutDefault;
  const reduced = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const uid = "spb" + (++_uid);
  let drag = null, moving = -1, animId = null, actx = null, dead = false;

  if (!document.getElementById("spb-style")) {
    const st = document.createElement("style"); st.id = "spb-style"; st.textContent = CSS; document.head.appendChild(st);
  }
  const root = document.createElement("div"); root.className = "spb";
  const scroller = document.createElement("div"); scroller.className = "spb-scroll";
  const svg = document.createElementNS(NS, "svg"); svg.setAttribute("class", "spb-svg");
  svg.setAttribute("aria-label", "Showpiece bank"); svg.setAttribute("role", "img");
  const hint = document.createElement("p"); hint.className = "spb-hint"; hint.textContent = HINT;
  // On a narrow screen the drawing scrolls sideways; a right-edge arrow says more knobs and cards lie that way.
  const frame = document.createElement("div"); frame.className = "spb-frame";
  const more = document.createElement("div"); more.className = "spb-more"; more.textContent = "\u203a";
  more.setAttribute("aria-hidden", "true");
  const updateMore = () => frame.classList.toggle("more", scroller.scrollWidth - scroller.clientWidth - scroller.scrollLeft > 4);
  scroller.addEventListener("scroll", updateMore, { passive: true });
  scroller.appendChild(svg); frame.append(scroller, more); root.append(frame, hint); host.appendChild(root);

  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const pol = (cx, cy, r, a) => [cx + r * Math.sin(a * Math.PI / 180), cy - r * Math.cos(a * Math.PI / 180)];
  function gearPath(r, teeth) {
    const pts = [], rIn = r * 0.82;
    for (let k = 0; k < teeth * 2; k++) {
      const a0 = (k / (teeth * 2)) * 360, a1 = ((k + 1) / (teeth * 2)) * 360, rr = k % 2 ? rIn : r;
      pts.push(pol(0, 0, rr, a0 + 2), pol(0, 0, rr, a1 - 2));
    }
    return "M" + pts.map((p) => p.map((v) => v.toFixed(2)).join(" ")).join("L") + "Z";
  }
  function text(parent, s, x, y, size, attrs) {
    const t = el("text", Object.assign({ x, y, "font-size": size, "text-anchor": "middle", "dominant-baseline": "central",
      "font-family": "Georgia, serif", fill: "#2a1a08", "letter-spacing": ".04em" }, attrs || {}), parent);
    t.textContent = s;
    return t;
  }
  const ref = (name) => `url(#${uid}-${name})`;

  // layout: 6 columns landscape, 4 portrait (the prototype's two arrangements)
  let L = {};
  const isPortrait = () => window.innerHeight > window.innerWidth;
  function layout() {
    const cols = isPortrait() ? Math.min(4, cards.length) : Math.min(6, cards.length), rows = Math.ceil(cards.length / cols);
    const cw = 190, ch = 268, gap = 10, left = 70, top = 10, strip = 190;
    const W = left + cols * (cw + gap) + 10, H = top + rows * (ch + gap) + strip;
    L = { cols, rows, cw, ch, gap, left, top, strip, W, H, portrait: isPortrait() };
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.style.width = `max(100%, ${Math.round(W * MIN_SCALE)}px)`;
    requestAnimationFrame(updateMore);
  }
  const px = (Lo) => PLOT.x0 + (carriage(Lo, span) + span) / (2 * span) * (PLOT.x1 - PLOT.x0);
  const py = (p) => PLOT.y1 - p * (PLOT.y1 - PLOT.y0);
  const cardOrigin = (j) => {
    const c = j % L.cols, r = Math.floor(j / L.cols);
    return [L.left + c * (L.cw + L.gap), L.top + r * (L.ch + L.gap)];
  };

  let gDyn = null, cardGroups = [], gears = [], shaftMarks = [];
  function build() {
    layout();
    svg.textContent = "";
    cardGroups = []; gears = []; shaftMarks = [];
    const defs = el("defs", {}, svg);
    defs.innerHTML = `
      <linearGradient id="${uid}-brassv" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#e8c97f"/><stop offset=".5" stop-color="#b8883a"/><stop offset="1" stop-color="#7a5521"/></linearGradient>
      <radialGradient id="${uid}-face" cx="45%" cy="35%" r="80%">
        <stop offset="0" stop-color="#f7efd9"/><stop offset="1" stop-color="#d9caa3"/></radialGradient>
      <radialGradient id="${uid}-knob" cx="35%" cy="30%" r="80%">
        <stop offset="0" stop-color="#f1d58e"/><stop offset=".5" stop-color="#c79a45"/><stop offset="1" stop-color="#6d4a1c"/></radialGradient>
      <linearGradient id="${uid}-steel" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#e6e6e0"/><stop offset=".5" stop-color="#9a9a92"/><stop offset="1" stop-color="#55554f"/></linearGradient>
      <radialGradient id="${uid}-lampon" cx="50%" cy="45%" r="60%">
        <stop offset="0" stop-color="#fffbe0"/><stop offset=".4" stop-color="#ffd36a"/><stop offset="1" stop-color="#a8621a"/></radialGradient>`;
    // cabinet
    el("rect", { x: 2, y: 2, width: L.W - 4, height: L.H - 4, rx: 10, fill: "#3a2614", stroke: "#b8924a", "stroke-width": 2 }, svg);
    // chain linking each row's shafts to the knobs
    for (let i = 0; i < NI; i++) {
      const x = 18 + i * 3;
      el("line", { x1: x, y1: L.top + SHAFT_Y[i], x2: x, y2: L.H - L.strip + 40, stroke: "#9a9a92", "stroke-width": 1.2, "stroke-dasharray": "2 2" }, svg);
    }
    // cards
    const gearLayers = [];
    cards.forEach((s, j) => {
      const [x0, y0] = cardOrigin(j);
      const g = el("g", { transform: `translate(${x0} ${y0})`, class: "spb-card", "data-card": s.name, "data-code": pointingCode(s) }, svg);
      cardGroups.push(g);
      el("rect", { x: 0, y: 0, width: L.cw, height: L.ch, rx: 6, fill: ref("brassv"), stroke: "#4a3216", "stroke-width": 1 }, g);
      // the S-shaped slot and its 0-100 scale
      el("rect", { x: PLOT.x0 - 4, y: PLOT.y0 - 5, width: PLOT.x1 - PLOT.x0 + 8, height: PLOT.y1 - PLOT.y0 + 16, rx: 3,
        fill: ref("face"), stroke: "#4a3216", "stroke-width": 1.1 }, g);
      [0, 25, 50, 75, 100].forEach((v) => {
        const y = py(v / 100);
        el("line", { x1: PLOT.x0, y1: y, x2: PLOT.x1, y2: y, stroke: "#2a1a08", "stroke-width": 0.4, opacity: 0.35 }, g);
        text(g, String(v), PLOT.x0 - 14, y, 8.5, { fill: "#2a1a08", "font-weight": "bold" });
      });
      let d = "";
      for (let k = 0; k <= 60; k++) {
        const Lo = -span + 2 * span * k / 60;
        d += (k ? "L" : "M") + px(Lo).toFixed(2) + " " + py(sigmoid(Lo)).toFixed(2);
      }
      el("path", { d, fill: "none", stroke: "#2a1a08", "stroke-width": 4.2, "stroke-linecap": "round" }, g);
      el("path", { d, fill: "none", stroke: "#6b4a26", "stroke-width": 2.2, "stroke-linecap": "round" }, g);
      // the carriage rail along the bottom
      el("line", { x1: PLOT.x0, y1: PLOT.y1 + 7, x2: PLOT.x1, y2: PLOT.y1 + 7, stroke: "#7a5521", "stroke-width": 2 }, g);
      // name plate
      el("rect", { x: 14, y: 110, width: L.cw - 28, height: 18, rx: 2, fill: "#2a1a08" }, g);
      text(g, String(s.name).toUpperCase(), L.cw / 2 - 8, 119, 9.5, { fill: "#f1d58e" });
      if (s.brochure) text(g, "★ IN THE BROCHURE", L.cw / 2, 137, 7.5, { fill: "#5a1e10" });
      // engraved pointing plate: dome bearing and telescope altitude (a label, not a bank output)
      el("rect", { x: 22, y: 248, width: L.cw - 44, height: 15, rx: 2, fill: "#8a6428", stroke: "#4a3216", "stroke-width": 0.8 }, g);
      const lab = `DOME ${String(s.bearing).padStart(3, "0")}°   ALT ${String(s.altitude).padStart(2, "0")}°`;
      text(g, lab, L.cw / 2, 256.2, 11, { fill: "#f3dc9c", opacity: 0.55, "font-weight": "bold" });
      text(g, lab, L.cw / 2, 255.5, 11, { fill: "#2a1a08", "font-weight": "bold", class: "spb-plate" });
      // gears: size = |weight|, reversing idler when negative (own layer, above the shafts)
      const maxw = 1.0;
      gearLayers.push(() => {
        const gl = el("g", { transform: `translate(${x0} ${y0})` }, svg);
        s.w.forEach((w, i) => {
          const gx = GEAR_X[i % GEAR_X.length], gy = SHAFT_Y[i % SHAFT_Y.length];
          if (Math.abs(w) < 1e-9) {
            el("circle", { cx: gx, cy: gy, r: 2.2, fill: "#4a3216" }, gl);   // no gear: this shaft passes by
            return;
          }
          const rad = 4.5 + 8 * Math.abs(w) / maxw;
          const base = `translate(${gx} ${gy})`;
          const gg = el("g", { class: `gear sh${i}`, transform: base }, gl);
          el("path", { d: gearPath(rad, Math.max(7, Math.round(rad * 1.3))), fill: "#e8c77e", stroke: "#3b2810", "stroke-width": 0.8 }, gg);
          el("line", { x1: 0, y1: 0, x2: 0, y2: -rad * 0.78, stroke: "#3b2810", "stroke-width": 1.8, "stroke-linecap": "round" }, gg);
          el("circle", { r: rad * 0.42, fill: "none", stroke: "#3b2810", "stroke-width": 0.6, opacity: 0.6 }, gg);
          el("circle", { r: 1.6, fill: "#3b2810" }, gg);
          let idler = null, ibase = null;
          if (w < 0) {
            ibase = `translate(${gx + rad + 4.5} ${gy - 3})`;
            idler = el("g", { class: `idler sh${i}`, transform: ibase }, gl);
            el("path", { d: gearPath(3.6, 7), fill: "#b07c3a", stroke: "#3b2810", "stroke-width": 0.6 }, idler);
            el("line", { x1: 0, y1: 0, x2: 0, y2: -2.8, stroke: "#3b2810", "stroke-width": 1.1 }, idler);
          }
          gears.push({ g: gg, base, idler, ibase, w, i });
        });
      });
    });
    for (let r = 0; r < L.rows; r++) {
      const y0 = L.top + r * (L.ch + L.gap);
      // shafts run the full row
      for (let i = 0; i < NI; i++) {
        const sy = SHAFT_Y[i % SHAFT_Y.length];
        el("rect", { x: 14, y: y0 + sy - 2.5, width: L.W - 28, height: 5, fill: ref("steel"), rx: 2.5 }, svg);
        shaftMarks.push({ i, e: el("line", { x1: 14, y1: y0 + sy, x2: L.W - 14, y2: y0 + sy, class: "shm", stroke: "#3a3a34", "stroke-width": 4,
          "stroke-dasharray": "2 7", opacity: 0.55 }, svg) });
        text(svg, inputs[i].name, 40, y0 + sy, 9, { fill: "#e9dcc0", "font-weight": "bold" });
      }
    }
    gearLayers.forEach((f) => f());
    // control strip: a knob per shaft + the cut-off knob
    const sy = L.H - L.strip + 70;
    const spanX = L.W - 80;
    L.knobs = [];
    for (let k = 0; k < NK; k++) {
      const kx = 40 + spanX * (k + 0.5) / NK;
      L.knobs.push({ x: kx, y: sy, r: 34 });
      el("circle", { cx: kx, cy: sy, r: 60, fill: "#2b1c0e", stroke: "#b8924a", "stroke-width": 1 }, svg);
      if (k < NI) {
        const inp = inputs[k];
        for (const v of stepValues(inp)) {
          const a = knobAngle(inp, v), big = (v - inp.min) % (inp.max > 10 ? 5 : 2) === 0;
          const [x1, y1] = pol(kx, sy, 40, a), [x2, y2] = pol(kx, sy, big ? 48 : 44, a);
          el("line", { x1, y1, x2, y2, stroke: "#e9dcc0", "stroke-width": big ? 1.3 : 0.7 }, svg);
          if (big) { const [tx, ty] = pol(kx, sy, 54, a); text(svg, String(v), tx, ty, 9, { fill: "#e9dcc0" }); }
        }
        text(svg, inp.name, kx, sy + 72, 11, { fill: "#f1d58e", "font-weight": "bold" });
      } else {
        cutStops.forEach((c) => {
          const a = cutKnobAngle(cutStops, c);
          const [x1, y1] = pol(kx, sy, 40, a), [x2, y2] = pol(kx, sy, 48, a);
          el("line", { x1, y1, x2, y2, stroke: "#ff8a7a", "stroke-width": 1.2 }, svg);
          const [tx, ty] = pol(kx, sy, 55, a); text(svg, String(Math.round(c * 100)), tx, ty, 9, { fill: "#ff8a7a" });
        });
        text(svg, "CUT-OFF %", kx, sy + 72, 11, { fill: "#ff8a7a", "font-weight": "bold" });
      }
    }
    gDyn = el("g", { class: "spb-dyn" }, svg);
    // the knobs' grab areas, above everything (touch-action:none here only, so the drawing still scrolls)
    L.knobs.forEach((kb, k) => {
      const hit = el("circle", { cx: kb.x, cy: kb.y, r: 62, fill: "transparent", class: "spb-knobhit", "data-k": k }, svg);
      hit.addEventListener("pointerdown", (ev) => onDown(ev, k));
    });
    render();
  }

  function animate() {
    if (animId || dead) return;
    const step = () => {
      let any = false; moving = -1;
      for (let i = 0; i < NI; i++) {
        const d = xs[i] - xsDisp[i];
        if (Math.abs(d) > 0.005) { xsDisp[i] += d * 0.12; any = true; moving = i; } else xsDisp[i] = xs[i];
      }
      render();
      animId = any ? requestAnimationFrame(step) : null;
      if (!any) { moving = -1; render(); }
    };
    animId = requestAnimationFrame(step);
  }
  function glide() {
    if (reduced) { for (let i = 0; i < NI; i++) xsDisp[i] = xs[i]; render(); } else { render(); animate(); }
  }

  function render() {
    if (dead) return;
    gDyn.textContent = "";
    const yc = py(cut);
    cards.forEach((s, j) => {
      const [x0, y0] = cardOrigin(j);
      const g = el("g", { transform: `translate(${x0} ${y0})` }, gDyn);
      // the red cut-off: a taut wire across the slot at the cut-off height
      el("line", { x1: PLOT.x0 - 3, y1: yc, x2: PLOT.x1 + 3, y2: yc, stroke: "#c0180c", "stroke-width": 1.6, "stroke-dasharray": "5 2" }, g);
      // the carriage (log-odds) and the bead riding the S
      const Lj = logOdds(s, inputs, xsDisp), x = px(Lj), p = sigmoid(carriage(Lj, span)), y = py(p);
      el("line", { x1: x, y1: PLOT.y1 + 7, x2: x, y2: y, stroke: "#1a0e04", "stroke-width": 1, opacity: 0.6 }, g);
      el("rect", { x: x - 5, y: PLOT.y1 + 3, width: 10, height: 8, rx: 1.5, fill: "#5a3a16", stroke: "#e9cf8a", "stroke-width": 0.7 }, g);
      const lit = isLit(p, cut);
      el("circle", { cx: x, cy: y, r: 5, fill: lit ? ref("lampon") : "#d9d2c0", stroke: "#1a0e04", "stroke-width": 1.2 }, g);
      // lamp on the name plate
      el("circle", { cx: L.cw - 24, cy: 119, r: 6, fill: lit ? ref("lampon") : "#3a2a1a", stroke: "#e9cf8a", "stroke-width": 0.8, class: "spb-lamp" + (lit ? " on" : "") }, g);
      if (lit) el("circle", { cx: L.cw - 24, cy: 119, r: 11, fill: "#ffd36a", opacity: 0.3 }, g);
      cardGroups[j].setAttribute("data-lit", lit ? "1" : "0");
    });
    // turn the gears in proportion to their drive (visual only); light the driven shaft
    const active = drag && drag.k < NI ? drag.k : (moving >= 0 ? moving : -1);
    gears.forEach(({ g, base, idler, ibase, w, i }) => {
      const turn = shaftTurn(inputs[i], xsDisp[i]) * w * 70;
      g.setAttribute("transform", `${base} rotate(${turn})`);
      if (idler) idler.setAttribute("transform", `${ibase} rotate(${-turn * 2})`);
      const hot = i === active;
      [g, idler].forEach((e) => {
        if (!e) return;
        const f = e.firstChild;
        f.setAttribute("stroke", hot ? "#fff1b8" : "#3b2810"); f.setAttribute("stroke-width", hot ? 1.8 : 0.8);
        e.style.filter = hot ? "drop-shadow(0 0 3px #ffcf5a)" : "";
      });
    });
    shaftMarks.forEach(({ i, e }) => {
      e.setAttribute("stroke-dashoffset", (-shaftTurn(inputs[i], xsDisp[i]) * 14).toFixed(2));
      e.setAttribute("stroke", i === active ? "#ffcf5a" : "#3a3a34");
      e.setAttribute("opacity", i === active ? 0.95 : 0.55);
    });
    // knobs
    L.knobs.forEach((kb, k) => {
      el("circle", { cx: kb.x, cy: kb.y, r: kb.r, fill: ref("knob"), stroke: "#4a3216", "stroke-width": 1.2 }, gDyn);
      const a = k < NI ? knobAngle(inputs[k], xs[k]) : cutKnobAngle(cutStops, cut);
      const [qx, qy] = pol(kb.x, kb.y, kb.r - 4, a);
      el("line", { x1: kb.x, y1: kb.y, x2: qx, y2: qy, stroke: k < NI ? "#2a1a08" : "#c0180c", "stroke-width": 3, "stroke-linecap": "round" }, gDyn);
    });
  }

  // ---- interaction: drag a knob round ----
  function click() {
    if (o.sound === false) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const t = actx.currentTime, osc = actx.createOscillator(), gn = actx.createGain();
      osc.type = "square"; osc.frequency.setValueAtTime(1600, t); osc.frequency.exponentialRampToValueAtTime(380, t + 0.03);
      gn.gain.setValueAtTime(0.05, t); gn.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);
      osc.connect(gn); gn.connect(actx.destination); osc.start(t); osc.stop(t + 0.05);
    } catch (e) { /* no audio: the knob still turns */ }
  }
  const save = () => { if (typeof o.onPegs === "function") o.onPegs({ xs: xs.slice(), cut }); };
  function pt(ev) {
    const r = svg.getBoundingClientRect();
    return [(ev.clientX - r.left) / r.width * L.W, (ev.clientY - r.top) / r.height * L.H];
  }
  function onDown(ev, k) {
    try { svg.setPointerCapture(ev.pointerId); } catch (e) { /* synthetic pointer */ }
    drag = { k };
    const [x, y] = pt(ev);
    turnTo(k, x, y);
    ev.preventDefault();
  }
  const onMove = (ev) => { if (drag) { const [x, y] = pt(ev); turnTo(drag.k, x, y); } };
  const onUp = () => { if (!drag) return; drag = null; render(); };
  svg.addEventListener("pointermove", onMove);
  svg.addEventListener("pointerup", onUp);
  svg.addEventListener("pointercancel", onUp);
  function turnTo(k, x, y) {
    const kb = L.knobs[k];
    if (Math.hypot(x - kb.x, y - kb.y) < 6) return;          // too close to the spindle to read an angle
    const a = Math.atan2(x - kb.x, -(y - kb.y)) * 180 / Math.PI;
    if (k < NI) {
      const v = valueAtAngle(inputs[k], a);
      if (v !== xs[k]) { xs[k] = v; click(); save(); glide(); }
    } else {
      const c = cutAtAngle(cutStops, a);
      if (c !== cut) { cut = c; click(); save(); render(); }
    }
  }

  let lastPortrait = isPortrait();
  const onResize = () => { const p = isPortrait(); if (p !== lastPortrait) { lastPortrait = p; build(); } else updateMore(); };
  window.addEventListener("resize", onResize);

  const toClient = (x, y) => {
    const r = svg.getBoundingClientRect();
    return { x: r.left + x / L.W * r.width, y: r.top + y / L.H * r.height };
  };
  const readOne = (s) => { const p = beadHeight(s, inputs, xs, span); return { name: s.name, code: pointingCode(s), p, lit: isLit(p, cut) }; };
  const api = {
    ready: Promise.resolve(),
    readings: () => xs.slice(),
    setReading(i, v) { if (!(i >= 0 && i < NI)) throw new Error("showpiece bank: no shaft " + i); xs[i] = snap(inputs[i], v); save(); glide(); },
    setReadings(arr) { arr.forEach((v, i) => { xs[i] = snap(inputs[i], v); }); save(); glide(); },
    cut: () => cut,
    setCut(c) { if (!cutStops.includes(c)) throw new Error("showpiece bank: the cut-off knob has no stop at " + c); cut = c; save(); render(); },
    read: () => cards.map(readOne),
    lit: () => cards.map(readOne).filter((r) => r.lit).map((r) => r.name),
    isSettled: () => xs.every((v, i) => v === xsDisp[i]) && !animId,
    knobCentre(k) { const kb = L.knobs[k]; return toClient(kb.x, kb.y); },
    knobPoint(k, value) {
      const kb = L.knobs[k];
      const a = k < NI ? knobAngle(inputs[k], value) : cutKnobAngle(cutStops, value);
      const [x, y] = pol(kb.x, kb.y, 50, a);
      return toClient(x, y);
    },
    destroy() {
      if (dead) return;
      dead = true;
      if (animId) cancelAnimationFrame(animId);
      animId = null;
      window.removeEventListener("resize", onResize);
      svg.removeEventListener("pointermove", onMove); svg.removeEventListener("pointerup", onUp); svg.removeEventListener("pointercancel", onUp);
      if (actx && actx.close) actx.close().catch(() => {});
      root.remove();
    },
  };
  root.showpieceBank = api;          // for tests; harmless to students
  build();
  return api;
}
export const mount = mountBank;
