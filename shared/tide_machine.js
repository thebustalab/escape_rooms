// THE TIDE MACHINE — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"tide"`), ported 2026-10-28 from the
// dunes prototype (rooms/regression/dunes/_scratch/tide_machine/machine_art.js; its README.md is the full design).
// Edit THIS file from now on; the prototype page is reference only.
//
// A painted still (the engineer's tide-predicting machine) with code-drawn moving parts: four shafts that take the
// pulleys the player has CARRIED here, a crank and two wind knobs that run time, a pen drum writing the water over the
// bar, and a datum thumbscrew. Like the drawdown board it is READ, never graded: it holds no answer and solves nothing.
// The player sets it up, reads when the bar stays dry, and enters the date on the departure board (a date lock).
//
// All arithmetic is shared/tide_model.js, the module the prototype's test_model.mjs checks, so the pen drawn here is
// the number those tests prove.
//
//   const m = mountTide(hostEl, { geometry, config, held?, pegs?, onPegs?(setting), sound?, debug? });
//     geometry — the painting's calibration (instruments/tide/geometry.json; art paths relative to the scenario)
//     config   — the machine's numbers (instruments/tide/machine.json); cloned, never mutated
//     held     — pulley ids on the shelf (the carried pulleys); absent = all four (author preview)
//     pegs     — the saved setting {arr, z0, t}; onPegs(setting) is called whenever it changes
//   m.place(shaft, pid); m.arrangement(); m.setDatum(z); m.datum(); m.setTime(iso); m.time(); m.level();
//   m.penLevel(); m.shelf(); m.ready (Promise); m.destroy();
import * as M from "./tide_model.js?v=148";

const SERIF = 'Georgia, "Times New Roman", "Liberation Serif", serif';
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const HOURS_PER_TURN = 24;                                                   // one turn of the crank = one day
const ENG_HI = 'rgba(255,238,196,0.5)', ENG_LO = 'rgba(46,28,10,0.84)';

export function mountTide(host, opts = {}) {
const A = opts.geometry, cfg = JSON.parse(JSON.stringify(opts.config || {}));
if (!A || !Array.isArray(A.shaftX) || A.shaftX.length !== 4) throw new Error("tide: geometry needs four shafts");
if (!Array.isArray(cfg.shafts) || !Array.isArray(cfg.pulleys)) throw new Error("tide: config needs shafts and pulleys");
const DEBUG = !!opts.debug, SOUND = opts.sound !== false, saved = opts.pegs || null;
const HELD = Array.isArray(opts.held) ? new Set(opts.held) : null;
const inTray = (pid) => !HELD || HELD.has(pid);
let dead = false, raf = 0, loaded = false, loupeTimer = null;
const offs = [];
const on = (el, ev, fn, o) => { el.addEventListener(ev, fn, o); offs.push(() => el.removeEventListener(ev, fn, o)); };
const save = () => { if (opts.onPegs) opts.onPegs({ arr: { ...S.arr }, z0: cfg.z0, t: S.t }); };

// geometry handed to model.js: the painting's own numbers plus the derived chart scale
const C = A.chart;
const pxPerM = (C.y1 - C.y0) / (C.mMax - C.mMin);
const G = {
  shaftX: A.shaftX, idlerY: A.idlerY, idlerR: A.idlerR, pulleyRestY: A.pulleyRestY,
  pulleyDiaPerM: A.pulleyDiaPerM, pulleyMinDia: A.pulleyMinDia, anchorX: A.anchorX, cornerX: A.cornerX,
  penX: A.penX, penSheaveY: A.penSheaveY, chart: C, penRatio: A.penRatio,
  pxPerM, yokePxPerM: pxPerM / (2 * A.penRatio), zeroY: C.y1 - (0 - C.mMin) * pxPerM,
};
const DRUM = M.penDrum(G);
const PPH = (C.x1 - C.x0) / (2 * C.hoursHalf);
const T_MIN = 0, T_MAX = M.isoToHours('1928-12-31T23:00', cfg);
const SH = A.shadow;

// ---- the datum screw ----
// cfg.z0 is the machine's LIVE datum (the pen's rest height, the model's intercept): model.js reads it on every
// call. The machine is found with the screw knocked out (cfg.datum_start); the player resets it from the logbook.
// The true value is kept only for the debug readout.
const TRUE_Z0 = cfg.z0, DATUM_MIN = 0.5, DATUM_MAX = 6.0;
const clampDatum = (z) => Math.min(DATUM_MAX, Math.max(DATUM_MIN, z));
cfg.z0 = clampDatum(saved && Number.isFinite(saved.z0) ? saved.z0 : (cfg.datum_start ?? cfg.z0));


// ---- sprites (loaded async; the frame loop starts once they are in) ----
const loadImg = (src) => new Promise((res) => { if (!src) return res(null); const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = src; });
const SP = A.sprites;
let baseImg, pulleyImg, wheelImg, yokeImg, armImg, knobImg, penImg, pegImgs = [];

// ---- state ----
const S = {
  t: M.isoToHours(cfg.today, cfg),
  arr: Object.fromEntries(cfg.shafts.map((s) => [s.id, null])),
  inkLo: 0, inkHi: 0,
  drag: null, crank: null, hold: null, loupe: null, loupePending: null, run: null, datumDrag: null,
  lastPenY: null, lastHourTick: null,
};
S.inkLo = S.inkHi = S.t;
if (saved && Number.isFinite(saved.t)) S.t = S.inkLo = S.inkHi = Math.min(T_MAX, Math.max(T_MIN, saved.t));
if (saved && saved.arr) for (const [sh, pid] of Object.entries(saved.arr)) if (sh in S.arr && pid && inTray(pid)) placeRaw(sh, pid);
S.lastHourTick = Math.floor(S.t);

function clampT(t) { return Math.min(T_MAX, Math.max(T_MIN, t)); }
function mountedOn(pid) { return Object.keys(S.arr).find((k) => S.arr[k] === pid) || null; }
function placeRaw(shaftId, pid) {
  if (pid) { const was = mountedOn(pid); if (was) S.arr[was] = null; }
  S.arr[shaftId] = pid || null;
}
function arrangementChanged() { S.inkLo = S.inkHi = S.t; save(); }
function setDatum(z) { const v = clampDatum(z); if (v !== cfg.z0) { cfg.z0 = v; arrangementChanged(); } }

// ---- time ----
function advanceTo(t) {
  t = clampT(t);
  S.t = t;
  S.inkLo = Math.min(S.inkLo, t); S.inkHi = Math.max(S.inkHi, t);
  const hr = Math.floor(t + 1e-9);
  if (hr !== S.lastHourTick) { S.lastHourTick = hr; click(); }
}
function jumpTo(t) { S.t = clampT(t); S.inkLo = S.inkHi = S.t; S.lastHourTick = Math.floor(S.t); }

// ---- audio: ratchet clicks, muted until the first gesture ----
let actx = null, noiseBuf = null, lastClick = 0;
function unlockAudio() {
  if (!SOUND) return;
  if (actx) { if (actx.state === 'suspended') actx.resume(); return; }
  try {
    actx = new (window.AudioContext || window.webkitAudioContext)();
    noiseBuf = actx.createBuffer(1, Math.floor(actx.sampleRate * 0.04), actx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
  } catch (e) { actx = null; }
}
function click() {
  if (!actx || actx.state !== 'running') return;
  const now = actx.currentTime;
  if (now - lastClick < 0.045) return;
  lastClick = now;
  const src = actx.createBufferSource(); src.buffer = noiseBuf;
  const bp = actx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 2600 + Math.random() * 500; bp.Q.value = 4;
  const g = actx.createGain(); g.gain.setValueAtTime(0.5, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
  src.connect(bp).connect(g).connect(actx.destination); src.start(now);
  const o = actx.createOscillator(); o.type = 'square'; o.frequency.value = 1300;
  const g2 = actx.createGain(); g2.gain.setValueAtTime(0.05, now); g2.gain.exponentialRampToValueAtTime(0.0005, now + 0.012);
  o.connect(g2).connect(actx.destination); o.start(now); o.stop(now + 0.02);
}


// ---- canvas + the one letterbox transform (sized to the host card, not the window) ----
const stage = document.createElement('div');
stage.className = 'tidestage';
const cv = document.createElement('canvas'), ctx = cv.getContext('2d');
cv.className = 'tidecanvas';
cv.style.aspectRatio = `${A.view.w} / ${A.view.h}`;
cv.style.width = '100%'; cv.style.display = 'block';   // sized by the host even without pano-player.css
stage.style.position = 'relative'; stage.style.width = '100%';
const lp = document.createElement('canvas'), lctx = lp.getContext('2d');
lp.className = 'tideloupe';
lp.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;';
stage.append(cv, lp); host.appendChild(stage);
const stat = document.createElement('canvas'), sctx = stat.getContext('2d');
let view = { dpr: 1, k: 1, S: 1, ox: 0, oy: 0 };
function resize() {
  if (dead) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 3);
  const cw = Math.max(1, cv.clientWidth), ch = Math.max(1, cv.clientHeight), V = A.view;
  for (const c of [cv, lp, stat]) { c.width = Math.round(cw * dpr); c.height = Math.round(ch * dpr); }
  const k = Math.min(cw / V.w, ch / V.h);
  view = { dpr, k, S: k * dpr, ox: ((cw - V.w * k) / 2 - V.x * k) * dpr, oy: ((ch - V.h * k) / 2 - V.y * k) * dpr };
  if (loaded) buildStatic();
}
const ro = typeof ResizeObserver === 'function' ? new ResizeObserver(() => resize()) : null;
if (ro) ro.observe(cv); else on(window, 'resize', resize);
const imgTransform = (c) => c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
const toImage = (e) => {
  const r = cv.getBoundingClientRect();
  return { x: ((e.clientX - r.left) * view.dpr - view.ox) / view.S, y: ((e.clientY - r.top) * view.dpr - view.oy) / view.S };
};

// ---- drawing helpers ----
function withShadow(c, fn, lift = 1) {
  c.save();
  c.shadowColor = `rgba(0,0,0,${SH.alpha})`;
  c.shadowBlur = SH.blur * lift * view.S; c.shadowOffsetX = SH.dx * lift * view.S; c.shadowOffsetY = SH.dy * lift * view.S;
  fn(); c.restore();
}
function brassGrad(c, x0, y0, x1, y1) {
  const g = c.createLinearGradient(x0, y0, x1, y1);
  g.addColorStop(0, '#eed9a0'); g.addColorStop(0.4, '#b79552'); g.addColorStop(0.75, '#7a5b26'); g.addColorStop(1, '#c9a964');
  return g;
}
function engraveText(c, txt, x, y, size, align = 'center', weight = '700') {
  c.save(); c.font = `${weight} ${size}px ${SERIF}`; c.textAlign = align; c.textBaseline = 'middle';
  c.fillStyle = ENG_HI; c.fillText(txt, x + 0.7, y + 0.8);
  c.fillStyle = ENG_LO; c.fillText(txt, x, y);
  c.restore();
}
function engraveStroke(c, fn, lw = 1.6) {
  c.save(); c.lineCap = 'round'; c.lineJoin = 'round';
  c.translate(0.7, 0.8); c.strokeStyle = ENG_HI; c.fillStyle = ENG_HI; c.lineWidth = lw; fn();
  c.translate(-0.7, -0.8); c.strokeStyle = ENG_LO; c.fillStyle = ENG_LO; c.lineWidth = lw; fn();
  c.restore();
}

// ---- plaque symbols (engraved into the painted blank plaques) ----
function symMoon(c, x, y, s) {
  engraveStroke(c, () => {
    c.beginPath(); c.arc(x, y, s, Math.PI * 0.32, Math.PI * 1.68, false);
    c.arc(x + s * 0.55, y, s * 0.8, Math.PI * 1.52, Math.PI * 0.48, true); c.closePath(); c.fill();
  });
}
function symSun(c, x, y, s) {
  engraveStroke(c, () => {
    c.beginPath(); c.arc(x, y, s * 0.48, 0, 7); c.stroke();
    c.beginPath(); c.arc(x, y, s * 0.13, 0, 7); c.fill();
    for (let i = 0; i < 12; i++) {
      const a = i * Math.PI / 6, r0 = s * 0.68, r1 = i % 2 ? s * 0.92 : s * 1.1;
      c.beginPath(); c.moveTo(x + r0 * Math.cos(a), y + r0 * Math.sin(a)); c.lineTo(x + r1 * Math.cos(a), y + r1 * Math.sin(a)); c.stroke();
    }
  }, 1.4);
}
function symNearFar(c, x, y, s) {
  symMoon(c, x, y, s * 0.62);
  engraveStroke(c, () => {
    const ah = (x0, x1, yy) => {
      const d = Math.sign(x1 - x0);
      c.beginPath(); c.moveTo(x0, yy); c.lineTo(x1, yy); c.stroke();
      c.beginPath(); c.moveTo(x1, yy); c.lineTo(x1 - d * 4, yy - 3); c.lineTo(x1 - d * 4, yy + 3); c.closePath(); c.fill();
    };
    ah(x - s * 1.85, x - s * 0.95, y - s * 0.42);     // inward
    ah(x - s * 0.95, x - s * 1.85, y + s * 0.42);     // outward
    ah(x + s * 1.85, x + s * 0.95, y - s * 0.42);
    ah(x + s * 0.95, x + s * 1.85, y + s * 0.42);
  }, 1.3);
}
function symVane(c, x, y, s) {
  engraveStroke(c, () => {
    c.beginPath(); c.moveTo(x, y - s * 0.5); c.lineTo(x, y + s * 1.0); c.stroke();                                  // post
    c.beginPath(); c.moveTo(x - s * 0.55, y + s * 0.62); c.lineTo(x + s * 0.55, y + s * 0.62); c.stroke();           // cross arm
    c.beginPath(); c.moveTo(x - s * 1.25, y - s * 0.5); c.lineTo(x + s * 1.0, y - s * 0.5); c.stroke();              // arrow shaft
    c.beginPath(); c.moveTo(x + s * 1.35, y - s * 0.5); c.lineTo(x + s * 0.85, y - s * 0.85); c.lineTo(x + s * 0.85, y - s * 0.15); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(x - s * 1.25, y - s * 0.5); c.lineTo(x - s * 1.6, y - s * 0.95); c.lineTo(x - s * 1.0, y - s * 0.95); c.lineTo(x - s * 0.75, y - s * 0.5); c.closePath(); c.fill();
    c.font = `700 ${s * 0.55}px ${SERIF}`; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText('S', x - s * 0.95, y + s * 0.72); c.fillText('N', x + s * 0.95, y + s * 0.72);
  }, 1.3);
}
const SYMBOLS = { moon: symMoon, sun: symSun, nearfar: symNearFar, wind: symVane };

// ---- static layer: the painting + everything engraved into it ----
function buildStatic() {
  const c = sctx;
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.fillStyle = '#0b0806'; c.fillRect(0, 0, stat.width, stat.height);
  imgTransform(c);
  c.imageSmoothingQuality = 'high';
  if (baseImg) c.drawImage(baseImg, 0, 0, A.imageW, A.imageH);
  cfg.shafts.forEach((sh, i) => {
    const p = A.plaques[i];
    (SYMBOLS[sh.id] || symMoon)(c, p.x + p.w / 2, p.y + p.h / 2 + (sh.id === 'wind' ? -1 : 0), sh.id === 'nearfar' ? 9.5 : 9);
  });
  engraveDial(c);
}

// 24-hour dial engraved into the painted blank brass dial; the hand is drawn each frame.
const dialAng = (h) => -Math.PI / 2 + h / 24 * 2 * Math.PI;
function engraveDial(c) {
  const { cx, cy, r: R } = A.dial;
  c.save();
  c.beginPath(); c.moveTo(cx, cy); c.arc(cx, cy, R - 2, dialAng(cfg.daylight[1]), dialAng(cfg.daylight[0] + 24)); c.closePath();
  c.fillStyle = 'rgba(22,26,58,0.26)'; c.fill();                         // night sector, blued
  c.restore();
  const segs = [[], []];
  for (let h = 0; h < 24; h++) {
    const a = dialAng(h), major = h % 3 === 0, r0 = major ? R - 9 : R - 5;
    segs[major ? 1 : 0].push([cx + Math.cos(a) * r0, cy + Math.sin(a) * r0, cx + Math.cos(a) * (R - 1.5), cy + Math.sin(a) * (R - 1.5)]);
  }
  segs.forEach((list, k) => engraveStroke(c, () => { c.beginPath(); for (const [a, b, d, e] of list) { c.moveTo(a, b); c.lineTo(d, e); } c.stroke(); }, k ? 1.8 : 1));
  for (let h = 0; h < 24; h += 3) { const a = dialAng(h); engraveText(c, h === 0 ? '24' : String(h), cx + Math.cos(a) * (R - 18), cy + Math.sin(a) * (R - 18), 11); }
}

// ---- chart on the painted paper ----
function drawChart(c) {
  const P = A.paper;
  c.save(); c.beginPath(); c.rect(P.x0, P.y0, P.x1 - P.x0, P.y1 - P.y0); c.clip();
  const tAt = (x) => S.t + (x - A.penX) / PPH, xAt = (tau) => A.penX + (tau - S.t) * PPH;
  const tL = tAt(P.x0), tR = tAt(P.x1);
  for (let f = Math.ceil(C.mMin * 2) / 2; f <= C.mMax + 1e-9; f += 0.5) {     // metre and half-metre rules
    if (Math.abs(f) < 1e-9) continue;
    const y = M.levelToY(f, G), major = Number.isInteger(f);
    c.strokeStyle = major ? 'rgba(120,70,30,0.6)' : 'rgba(120,70,30,0.28)';
    c.lineWidth = major ? 1.1 : 0.7;
    c.beginPath(); c.moveTo(P.x0, y); c.lineTo(P.x1, y); c.stroke();
  }
  // a tick at every midnight; each Sunday a full rule, a heavy tick and its date along the foot
  for (let m = tL - M.hourOfDay(tL, cfg) + 24; m <= tR; m += 24) {
    const x = xAt(m), sunday = M.dayOfWeek(m, cfg) === 0;
    if (sunday) {
      c.strokeStyle = 'rgba(90,50,20,0.38)'; c.lineWidth = 0.9; c.beginPath(); c.moveTo(x, C.y0); c.lineTo(x, C.y1); c.stroke();
      c.strokeStyle = '#4a2a10'; c.lineWidth = 2;
      c.beginPath(); c.moveTo(x, P.y0); c.lineTo(x, P.y0 + 12); c.moveTo(x, P.y1); c.lineTo(x, P.y1 - 12); c.stroke();
      const d = M.hoursToDate(m, cfg);
      c.save(); c.font = `700 11px ${SERIF}`; c.fillStyle = 'rgba(52,26,6,0.95)'; c.textAlign = 'left'; c.textBaseline = 'bottom';
      c.fillText(`${d.d} ${MONTHS[d.mo - 1]}`, x + 2, C.y1 - 4); c.restore();
    } else {
      c.strokeStyle = 'rgba(74,42,16,0.75)'; c.lineWidth = 0.9;
      c.beginPath(); c.moveTo(x, P.y0); c.lineTo(x, P.y0 + 5); c.moveTo(x, P.y1); c.lineTo(x, P.y1 - 5); c.stroke();
    }
  }
  c.strokeStyle = '#a51d16'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(P.x0, G.zeroY); c.lineTo(P.x1, G.zeroY); c.stroke();   // wading line
  // label at the right end, below the line: ink usually lies left of the pen
  c.save(); c.font = `italic 700 9px ${SERIF}`; c.fillStyle = 'rgba(165,29,22,0.92)'; c.textAlign = 'right'; c.textBaseline = 'top';
  c.fillText('WADING LINE', C.x1 - 8, G.zeroY + 3);
  c.textAlign = 'left';
  c.font = `700 10px ${SERIF}`; c.fillStyle = 'rgba(96,52,20,0.85)'; c.textBaseline = 'middle';
  for (let f = Math.ceil(C.mMin); f <= Math.floor(C.mMax); f++) if (f) c.fillText((f > 0 ? '+' : '−') + Math.abs(f) + ' m', C.x0 - 4, M.levelToY(f, G) + (f === C.mMax ? 7 : -6));
  c.restore();
  const lo = Math.max(S.inkLo, tL), hi = Math.min(S.inkHi, tR);             // ink: only where the pen has been
  if (hi > lo) {
    c.strokeStyle = 'rgba(34,28,96,0.92)'; c.lineWidth = 1.8; c.lineJoin = 'round'; c.beginPath();
    const n = Math.max(2, Math.ceil(hi - lo));                               // hourly, so the day's wind still shows
    for (let i = 0; i <= n; i++) {                                           // beyond the stops the ink runs flat along the edge
      const tau = lo + (hi - lo) * i / n, y = M.levelToY(M.clampLevel(M.level(tau, S.arr, cfg), G), G);
      i ? c.lineTo(xAt(tau), y) : c.moveTo(xAt(tau), y);
    }
    c.stroke();
  }
  const g = c.createLinearGradient(0, P.y0, 0, P.y1);                       // the drum curving away top and bottom
  g.addColorStop(0, 'rgba(40,24,8,0.22)'); g.addColorStop(0.12, 'rgba(40,24,8,0)'); g.addColorStop(0.88, 'rgba(40,24,8,0)'); g.addColorStop(1, 'rgba(40,24,8,0.26)');
  c.fillStyle = g; c.fillRect(P.x0, P.y0, P.x1 - P.x0, P.y1 - P.y0);
  c.restore();
  drawStops(c);
}
// The pen's mechanical stops: brass blocks at the top and bottom of its travel, beside the nib.
function drawStops(c) {
  for (const [y0, h] of [[C.y0 - 6, 6], [C.y1, 6]]) {
    withShadow(c, () => {
      c.beginPath(); c.roundRect(A.penX + 2, y0, 12, h, 1.2); c.fillStyle = brassGrad(c, A.penX + 2, y0, A.penX + 14, y0 + h); c.fill();
    }, 0.4);
    c.fillStyle = 'rgba(40,24,6,0.8)'; c.beginPath(); c.arc(A.penX + 10, y0 + h / 2, 1.1, 0, 7); c.fill();
  }
}

// ---- moving parts ----
const pulleyR = (pid) => M.pulleyRadius(M.pulleySize(cfg, pid), G);
function drawPulley(c, x, y, r, rot = 0, lift = 1) {
  const s = SP.pulley, k = r / s.rGroove;                                    // groove radius = the wire radius
  withShadow(c, () => {
    c.translate(x, y); c.rotate(rot);
    c.drawImage(pulleyImg, -s.cx * k, -s.cy * k, pulleyImg.width * k, pulleyImg.height * k);
  }, lift);
}
function sheave(c, x, y, r) {
  drawPulley(c, x, y, r, 0, 0.5);
  c.beginPath(); c.arc(x, y, Math.max(1.2, r * 0.28), 0, 7); c.fillStyle = '#2a1a08'; c.fill();
}
function axleBoss(c, x, y, r = 4.5) {
  const g = c.createRadialGradient(x - 1.5, y - 1.5, 0.5, x, y, r);
  g.addColorStop(0, '#f6e7b8'); g.addColorStop(0.6, '#a4823e'); g.addColorStop(1, '#4e3812');
  c.beginPath(); c.arc(x, y, r, 0, 7); c.fillStyle = g; c.fill();
  c.beginPath(); c.arc(x, y, r * 0.35, 0, 7); c.fillStyle = '#2a1a08'; c.fill();
}

function drawShafts(c, mech) {
  const W = SP.crankwheel, Y = SP.yoke;
  const sx = A.crossheadW / yokeImg.width;                                   // yoke sprite scale
  mech.yokes.forEach((yk) => {
    const x = yk.x, R = A.crankWheelR, k = R / W.r;
    // crank wheel on the painted bearing boss; it turns with its shaft
    withShadow(c, () => {
      c.translate(x, A.bossY); c.rotate(-yk.theta);
      c.drawImage(wheelImg, -W.cx * k, -W.cy * k, wheelImg.width * k, wheelImg.height * k);
    }, 0.7);
    c.save(); c.translate(x, A.bossY); c.rotate(-yk.theta);                  // radial slide the crank pin is set in
    c.beginPath(); c.roundRect(-1.8, R * 0.1, 3.6, R * 0.62, 1.8); c.fillStyle = 'rgba(30,18,6,0.85)'; c.fill();
    c.restore();
    // Scotch yoke: crosshead slot at the pin's height, stem down the guide slot to the pulley axle
    const pinY = A.bossY + yk.dy, axleY = A.pulleyRestY + yk.dy;
    const headTop = pinY - Y.slotY * sx, headH = Y.headH * sx;
    const stemW = (Y.stemX1 - Y.stemX0) * sx;
    withShadow(c, () => {
      c.drawImage(yokeImg, Y.stemX0, Y.stemY0, Y.stemX1 - Y.stemX0, Y.stemY1 - Y.stemY0,
                  x - stemW / 2, headTop + headH - 1, stemW, axleY - (headTop + headH - 1));
      c.drawImage(yokeImg, 0, 0, yokeImg.width, Y.headH, x - A.crossheadW / 2, headTop, A.crossheadW, headH);
    }, 0.8);
    axleBoss(c, x, axleY);
    const px = x + yk.throwPx * Math.sin(yk.theta), py = A.bossY + yk.throwPx * Math.cos(yk.theta);
    const pg = c.createRadialGradient(px - 1, py - 1, 0.3, px, py, 3.4);
    pg.addColorStop(0, '#f2f2ee'); pg.addColorStop(0.6, '#9c9c96'); pg.addColorStop(1, '#3c3c3a');
    c.beginPath(); c.arc(px, py, 3.2, 0, 7); c.fillStyle = pg; c.fill();
  });
}

function drawPulleysAndWire(c, mech) {
  mech.yokes.forEach((yk) => {
    if (!yk.pid || (S.drag && S.drag.from === yk.id)) return;
    drawPulley(c, yk.x, A.pulleyRestY + yk.dy, yk.r, yk.dy / Math.max(6, yk.r));
  });
  const ri = A.idlerR, yTop = A.idlerY - ri;
  for (const [ix, iy] of mech.idlers) sheave(c, ix, iy, ri);
  sheave(c, A.cornerX - ri, yTop - ri, ri);                                  // lower corner (wire turns up)
  sheave(c, A.cornerX + ri, A.penSheaveY, ri);                               // upper corner (wire turns right)
  // stepped pen drum: the wire winds on the small groove, the pen cord hangs from the large one
  drawPulley(c, DRUM.cx, DRUM.cy, DRUM.R, mech.penY / DRUM.R, 0.6);
  drawPulley(c, DRUM.cx, DRUM.cy, DRUM.r * 1.35, mech.penY / DRUM.R, 0.3);
  axleBoss(c, DRUM.cx, DRUM.cy, 3.5);
  axleBoss(c, A.anchorX, yTop, 3.5);                                         // wire anchor
  const eyeY = mech.penY - A.penEyeToNib;
  const trace = () => {
    c.beginPath(); mech.wire.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
    c.moveTo(A.penX, A.penSheaveY); c.lineTo(A.penX, eyeY);                  // pen cord off the large groove
  };
  c.save(); c.lineJoin = 'round'; c.lineCap = 'round';
  // steel on dark mahogany: a dark casing and soft shadow so it reads on the brass, a grey core so it reads on the wood
  c.strokeStyle = 'rgba(0,0,0,0.4)'; c.lineWidth = 2; c.translate(SH.dx * 0.5, SH.dy * 0.5); trace(); c.stroke();
  c.setTransform(1, 0, 0, 1, 0, 0); imgTransform(c);
  c.strokeStyle = '#151515'; c.lineWidth = 2.1; trace(); c.stroke();
  c.strokeStyle = '#8f8e88'; c.lineWidth = 1.1; trace(); c.stroke();
  c.strokeStyle = 'rgba(246,246,238,0.75)'; c.lineWidth = 0.45; c.translate(-0.25, -0.3); trace(); c.stroke();
  c.restore();
}

function drawPen(c, mech) {
  const P = SP.pen, k = A.penEyeToNib / (P.nibY - P.eyeY);
  withShadow(c, () => c.drawImage(penImg, A.penX - P.nibX * k, mech.penY - P.nibY * k, penImg.width * k, penImg.height * k), 0.6);
  S.lastPenY = mech.penY;
}

function shelfPos(pid) {
  const i = A.shelf.order.indexOf(pid), r = pulleyR(pid);
  return [A.shelf.pegs[i].x, A.shelf.floorY - r * SP.pulley.cx / SP.pulley.rGroove];
}
function drawShelf(c) {
  for (const pid of A.shelf.order) {
    if (!inTray(pid) || mountedOn(pid) || (S.drag && S.drag.pid === pid)) continue;
    const [x, y] = shelfPos(pid);
    drawPulley(c, x, y, pulleyR(pid), 0, 0.8);
  }
  A.shelf.pegs.forEach((p, i) => { if (pegImgs[i]) c.drawImage(pegImgs[i], p.ox, p.oy); });   // pegs in front
}

// The crank's axle leaves the cabinet side, so the crank turns in a plane seen nearly edge-on: the arm is
// drawn rotated in its own plane and squashed horizontally by `persp`; the knob always points outboard.
const crankAngle = () => 2 * Math.PI * S.t / HOURS_PER_TURN;
function crankEnd(a = crankAngle()) { const K = A.crank; return [K.cx + K.persp * K.R * Math.sin(a), K.cy - K.R * Math.cos(a)]; }
function drawCrank(c) {
  const K = A.crank, AR = SP.crankArm, KN = SP.crankKnob, a = crankAngle();
  const sc = K.R / (AR.endX - AR.hubX);
  const u = [K.persp * Math.sin(a) * sc, -Math.cos(a) * sc], v = [K.persp * Math.cos(a) * sc, Math.sin(a) * sc];
  const depth = Math.sin(a);                                                 // +1 toward the viewer
  withShadow(c, () => {
    c.transform(u[0], u[1], v[0], v[1], K.cx - AR.hubX * u[0] - AR.hubY * v[0], K.cy - AR.hubX * u[1] - AR.hubY * v[1]);
    c.drawImage(armImg, 0, 0);
  }, 0.8);
  const [ex, ey] = crankEnd(a), ks = sc * (1 + 0.06 * depth), held = S.crank ? 0.94 : 1;
  withShadow(c, () => {
    c.translate(ex, ey); c.rotate(-Math.PI / 2); c.scale(ks * held, ks * held);
    c.drawImage(knobImg, -KN.baseX, -KN.baseY);
  }, 0.9);
  axleBoss(c, K.cx, K.cy, 4);
}

// Fast-wind knobs: hold to run, speeding up the longer they are held.
function knobRate(held) { return 24 + 96 * Math.min(1, Math.max(0, (held - 0.35) / 1.2)); }   // 1 day/s up to 5 days/s
function drawKnobs(c) {
  for (const [id, kb] of Object.entries(A.knobs)) {
    const pressed = S.hold && S.hold.id === id, r = kb.r * (pressed ? 0.93 : 1);
    withShadow(c, () => {
      const g = c.createRadialGradient(kb.x - r * 0.35, kb.y - r * 0.4, r * 0.1, kb.x, kb.y, r);
      g.addColorStop(0, pressed ? '#d8bf82' : '#f3e0a8'); g.addColorStop(0.55, '#a8873f'); g.addColorStop(1, '#4c3510');
      c.beginPath(); c.arc(kb.x, kb.y, r, 0, 7); c.fillStyle = g; c.fill();
    }, pressed ? 0.3 : 0.8);
    c.save(); c.strokeStyle = 'rgba(50,32,8,0.55)'; c.lineWidth = 0.8;            // knurled edge
    for (let i = 0; i < 28; i++) { const t = i * Math.PI / 14; c.beginPath(); c.moveTo(kb.x + Math.cos(t) * (r - 2.2), kb.y + Math.sin(t) * (r - 2.2)); c.lineTo(kb.x + Math.cos(t) * r, kb.y + Math.sin(t) * r); c.stroke(); }
    c.restore();
    engraveStroke(c, () => {
      const d = kb.dir;
      for (const o of [-3.2, 3.2]) {
        const x = kb.x + o * d;
        c.beginPath(); c.moveTo(x - 3.2 * d, kb.y - 4.5); c.lineTo(x + 2.8 * d, kb.y); c.lineTo(x - 3.2 * d, kb.y + 4.5); c.closePath(); c.fill();
      }
    }, 0.6);
  }
}

// The datum thumbscrew on the drum bezel: drag it up or down (geared, A.datum.pxPerM of drag per metre) and the
// pen's rest height moves with it. Its knurl turns with the setting so a change is visible even at a glance.
function drawDatum(c) {
  const D = A.datum, held = S.datumDrag, r = D.r * (held ? 0.94 : 1), turn = cfg.z0 * 2.4;
  withShadow(c, () => {
    const g = c.createRadialGradient(D.x - r * 0.35, D.y - r * 0.4, r * 0.1, D.x, D.y, r);
    g.addColorStop(0, held ? '#d8bf82' : '#f3e0a8'); g.addColorStop(0.55, '#a8873f'); g.addColorStop(1, '#4c3510');
    c.beginPath(); c.arc(D.x, D.y, r, 0, 7); c.fillStyle = g; c.fill();
  }, held ? 0.3 : 0.8);
  c.save(); c.strokeStyle = 'rgba(50,32,8,0.6)'; c.lineWidth = 0.8;
  for (let i = 0; i < 24; i++) { const t = turn + i * Math.PI / 12; c.beginPath(); c.moveTo(D.x + Math.cos(t) * (r - 2.4), D.y + Math.sin(t) * (r - 2.4)); c.lineTo(D.x + Math.cos(t) * r, D.y + Math.sin(t) * r); c.stroke(); }
  c.restore();
  engraveStroke(c, () => {                                                    // slot in the screw head, turning with it
    c.beginPath(); c.moveTo(D.x - Math.cos(turn) * r * 0.55, D.y - Math.sin(turn) * r * 0.55);
    c.lineTo(D.x + Math.cos(turn) * r * 0.55, D.y + Math.sin(turn) * r * 0.55); c.stroke();
  }, 1.6);
}

// Date: three number drums in the painted windows; the hand on the engraved 24-hour dial.
function drawDrum(c, w, labels, frac, size) {
  c.save(); c.beginPath(); c.rect(w.x, w.y, w.w, w.h); c.clip();
  const bg = c.createLinearGradient(0, w.y, 0, w.y + w.h);
  bg.addColorStop(0, '#8d8068'); bg.addColorStop(0.3, '#e9dfc4'); bg.addColorStop(0.55, '#f1e8d0'); bg.addColorStop(1, '#7b6e56');
  c.fillStyle = bg; c.fillRect(w.x, w.y, w.w, w.h);
  const pitch = w.h * 0.95, cy = w.y + w.h / 2 - frac * pitch;
  labels.forEach((t, i) => engraveText(c, t, w.x + w.w / 2, cy + (i - 1) * pitch + 1, size));
  const sh = c.createLinearGradient(0, w.y, 0, w.y + w.h);                 // the drum curving away top and bottom
  sh.addColorStop(0, 'rgba(10,6,2,0.75)'); sh.addColorStop(0.25, 'rgba(10,6,2,0)'); sh.addColorStop(0.75, 'rgba(10,6,2,0)'); sh.addColorStop(1, 'rgba(10,6,2,0.8)');
  c.fillStyle = sh; c.fillRect(w.x, w.y, w.w, w.h);
  c.restore();
}
function drawDate(c) {
  const tm = Math.floor(S.t * 60 + 1e-6) / 60;                             // floor to the minute: labels never run ahead of the roll
  const d = M.hoursToDate(tm, cfg), dPrev = M.hoursToDate(tm - 24, cfg), dNext = M.hoursToDate(tm + 24, cfg);
  const hd = M.hourOfDay(S.t, cfg), frac = hd >= 23 ? hd - 23 : 0;         // the drums roll during the last hour of the day
  const W = A.windows;
  drawDrum(c, W.day, [dPrev.d, d.d, dNext.d].map(String), frac, 20);
  drawDrum(c, W.month, [MONTHS[(d.mo + 10) % 12], MONTHS[d.mo - 1], MONTHS[d.mo % 12]], dNext.mo !== d.mo ? frac : 0, 15);
  drawDrum(c, W.year, [String(dPrev.y), String(d.y), String(dNext.y)], dNext.y !== d.y ? frac : 0, 15);
  const { cx, cy, r: R } = A.dial;
  withShadow(c, () => {
    c.translate(cx, cy); c.rotate(dialAng(hd) + Math.PI / 2);
    c.fillStyle = '#1b2036';
    c.beginPath(); c.moveTo(-1.8, 7); c.lineTo(-1.8, -R + 21); c.lineTo(-5, -R + 17); c.lineTo(0, -R + 6); c.lineTo(5, -R + 17); c.lineTo(1.8, -R + 21); c.lineTo(1.8, 7); c.closePath(); c.fill();
  }, 0.5);
  axleBoss(c, cx, cy, 4.5);
}

function draw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(stat, 0, 0);
  imgTransform(ctx);
  const mech = M.mechanism(S.t, S.arr, cfg, G);
  drawChart(ctx);
  drawShafts(ctx, mech);
  drawPulleysAndWire(ctx, mech);
  drawPen(ctx, mech);
  drawShelf(ctx);
  drawDate(ctx);
  drawKnobs(ctx);
  drawDatum(ctx);
  drawCrank(ctx);
  if (S.drag) {
    const hov = shaftUnder(S.drag.x, S.drag.y);
    if (hov !== null) {
      ctx.save(); ctx.strokeStyle = 'rgba(255,226,140,0.85)'; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(A.shaftX[hov], A.pulleyRestY, pulleyR(S.drag.pid) + 6, 0, 7); ctx.stroke(); ctx.restore();
    }
    drawPulley(ctx, S.drag.x, S.drag.y, pulleyR(S.drag.pid), 0, 2.4);
  }
  if (DEBUG) drawCalibration(ctx, mech);
  return mech;
}

// ?debug=1: every calibrated feature outlined in cyan over the painting
function drawCalibration(c, mech) {
  c.save(); c.strokeStyle = 'rgba(0,255,255,0.85)'; c.fillStyle = 'rgba(0,255,255,0.85)'; c.lineWidth = 0.8;
  const line = (x0, y0, x1, y1) => { c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); };
  const circ = (x, y, r) => { c.beginPath(); c.arc(x, y, r, 0, 7); c.stroke(); };
  const box = (r) => c.strokeRect(r.x, r.y, r.w, r.h);
  A.shaftX.forEach((x) => { line(x, A.slot.y0, x, A.slot.y1); circ(x, A.bossY, A.bossR); });
  line(A.shaftX[0] - 60, A.bossY, A.shaftX[3] + 60, A.bossY);
  A.plaques.forEach(box);
  const P = A.paper; c.strokeRect(P.x0, P.y0, P.x1 - P.x0, P.y1 - P.y0);
  c.setLineDash([3, 3]); c.strokeRect(C.x0, C.y0, C.x1 - C.x0, C.y1 - C.y0); c.setLineDash([]);
  Object.values(A.windows).forEach(box);
  circ(A.dial.cx, A.dial.cy, A.dial.r);
  const K = A.crank; circ(K.cx, K.cy, 6);
  c.beginPath(); c.ellipse(K.cx, K.cy, K.persp * K.R, K.R, 0, 0, 7); c.stroke();
  c.setLineDash([2, 4]); circ(K.cx, K.cy, K.hitR); c.setLineDash([]);
  Object.values(A.knobs).forEach((kb) => circ(kb.x, kb.y, kb.r));
  A.shelf.pegs.forEach((p) => line(p.x, A.shelf.floorY - 60, p.x, A.shelf.floorY));
  line(A.shelf.pegs[0].x - 40, A.shelf.floorY, A.shelf.pegs[3].x + 40, A.shelf.floorY);
  c.setLineDash([4, 3]); line(A.anchorX, A.idlerY, A.cornerX, A.idlerY); line(A.shaftX[0] - 60, A.pulleyRestY, A.shaftX[3] + 60, A.pulleyRestY); c.setLineDash([]);
  line(A.cornerX, A.idlerY - 30, A.cornerX, A.penSheaveY - 20);
  line(A.penX, C.y0 - 8, A.penX, C.y1 + 8);
  circ(DRUM.cx, DRUM.cy, DRUM.R); circ(DRUM.cx, DRUM.cy, DRUM.r);
  c.font = '9px ui-monospace, monospace'; c.fillText(`pen ${M.chartLevel(mech.penY, G).toFixed(3)} m${mech.stopped ? ' (stop)' : ''}`, A.penX + 6, mech.penY + 12);
  c.restore();
}

// ---- loupe ----
function drawLoupe() {
  lctx.setTransform(1, 0, 0, 1, 0, 0);
  lctx.clearRect(0, 0, lp.width, lp.height);
  if (!S.loupe) return;
  const Z = 2.5, R = 70;                                                     // image px
  const { x, y } = S.loupe, V = A.view;
  const lx = Math.min(V.x + V.w - R - 4, Math.max(V.x + R + 4, x));
  const ly = y - R - 34 > V.y + R ? y - R - 34 : Math.min(V.y + V.h - R - 4, y + R + 34);
  const dev = (px, py) => [px * view.S + view.ox, py * view.S + view.oy];
  const [cxD, cyD] = dev(lx, ly), RD = R * view.S, [sx, sy] = dev(x - R / Z, y - R / Z), sw = 2 * R / Z * view.S;
  lctx.save(); lctx.beginPath(); lctx.arc(cxD, cyD, RD, 0, 7); lctx.clip();
  lctx.drawImage(cv, sx, sy, sw, sw, cxD - RD, cyD - RD, 2 * RD, 2 * RD);
  lctx.restore();
  lctx.beginPath(); lctx.arc(cxD, cyD, RD, 0, 7);
  lctx.lineWidth = 6 * view.S; lctx.strokeStyle = '#b48535'; lctx.stroke();
  lctx.lineWidth = 1.5 * view.S; lctx.strokeStyle = '#3a2408'; lctx.stroke();
}

// ---- input ----
function shaftUnder(x, y) {
  if (y < A.bossY - 40 || y > A.slot.y1 + 40) return null;
  let best = null, bd = 62;
  A.shaftX.forEach((sx, i) => { const d = Math.abs(x - sx); if (d < bd) { bd = d; best = i; } });
  return best;
}
function pulleyAt(x, y) {
  const mech = M.mechanism(S.t, S.arr, cfg, G);
  for (const yk of mech.yokes) if (yk.pid && Math.hypot(x - yk.x, y - (A.pulleyRestY + yk.dy)) <= Math.max(yk.r, 20) + 4) return { pid: yk.pid, from: yk.id };
  for (const pid of A.shelf.order) {
    if (!inTray(pid) || mountedOn(pid)) continue;
    const [tx, ty] = shelfPos(pid);
    if (Math.hypot(x - tx, y - ty) <= Math.max(pulleyR(pid) * 1.06, 22) + 4) return { pid, from: 'tray' };
  }
  return null;
}
function datumHit(x, y) { const D = A.datum; return Math.hypot(x - D.x, y - D.y) < D.r + 12; }
function knobAt(x, y) { return Object.entries(A.knobs).find(([, kb]) => Math.hypot(x - kb.x, y - kb.y) < kb.r + 9)?.[0] || null; }
function crankHit(x, y) { const K = A.crank; return x < K.hitMaxX && Math.hypot(x - K.cx, y - K.cy) < K.hitR; }
function crankPointerAngle(x, y) { const K = A.crank; return Math.atan2((x - K.cx) / K.inputPersp, -(y - K.cy)); }

on(cv, 'pointerdown', (e) => {
  unlockAudio();
  e.preventDefault();
  if (S.run) return;
  const p = toImage(e);
  cv.setPointerCapture(e.pointerId);
  if (datumHit(p.x, p.y)) { S.datumDrag = { y: p.y, z: cfg.z0, pointer: e.pointerId }; return; }
  const kid = knobAt(p.x, p.y);
  if (kid) { S.hold = { id: kid, dir: A.knobs[kid].dir, t0: performance.now(), pointer: e.pointerId }; return; }
  if (crankHit(p.x, p.y)) { S.crank = { a: crankPointerAngle(p.x, p.y), pointer: e.pointerId }; return; }
  const hit = pulleyAt(p.x, p.y);
  if (hit) { S.drag = { ...hit, x: p.x, y: p.y, pointer: e.pointerId }; return; }
  S.loupePending = { x: p.x, y: p.y, pointer: e.pointerId };
  loupeTimer = setTimeout(() => { if (S.loupePending) S.loupe = { ...S.loupePending }; }, 180);
});
on(cv, 'pointermove', (e) => {
  const p = toImage(e);
  if (S.drag && S.drag.pointer === e.pointerId) { S.drag.x = p.x; S.drag.y = p.y; }
  else if (S.datumDrag && S.datumDrag.pointer === e.pointerId) setDatum(S.datumDrag.z + (S.datumDrag.y - p.y) / A.datum.pxPerM);
  else if (S.crank && S.crank.pointer === e.pointerId) {
    const a = crankPointerAngle(p.x, p.y);
    let d = a - S.crank.a; if (d > Math.PI) d -= 2 * Math.PI; if (d < -Math.PI) d += 2 * Math.PI;
    S.crank.a = a;
    advanceTo(S.t + d / (2 * Math.PI) * HOURS_PER_TURN);                    // clockwise = forward in time
  } else if (S.loupe && S.loupe.pointer === e.pointerId) { S.loupe.x = p.x; S.loupe.y = p.y; }
  else if (S.loupePending && S.loupePending.pointer === e.pointerId) { S.loupePending.x = p.x; S.loupePending.y = p.y; }
});
function endPointer(e) {
  clearTimeout(loupeTimer); S.loupePending = null;
  if (S.drag && S.drag.pointer === e.pointerId) {
    const { pid, from } = S.drag, i = shaftUnder(S.drag.x, S.drag.y);
    S.drag = null;
    if (i !== null) {
      const target = cfg.shafts[i].id, occupant = S.arr[target];
      if (target !== from) {
        S.arr[target] = pid;
        if (from !== 'tray') S.arr[from] = occupant && occupant !== pid ? occupant : null;   // swap between shafts
        arrangementChanged();
      }
    } else if (from !== 'tray') { S.arr[from] = null; arrangementChanged(); }
  }
  if (S.crank && S.crank.pointer === e.pointerId) { S.crank = null; save(); }
  if (S.datumDrag && S.datumDrag.pointer === e.pointerId) { S.datumDrag = null; save(); }
  if (S.hold && S.hold.pointer === e.pointerId) { S.hold = null; save(); }
  if (S.loupe && S.loupe.pointer === e.pointerId) S.loupe = null;
}
on(cv, 'pointerup', endPointer);
on(cv, 'pointercancel', endPointer);
on(cv, 'contextmenu', (e) => e.preventDefault());


// ---- frame loop ----
let lastFrame = performance.now();
function frame(now) {
  if (dead) return;
  const dt = Math.min(0.1, (now - lastFrame) / 1000); lastFrame = now;
  if (S.hold) advanceTo(S.t + S.hold.dir * knobRate((now - S.hold.t0) / 1000) * dt);
  if (S.run) {
    const u = Math.min(1, (now - S.run.t0) / S.run.ms), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
    advanceTo(S.run.from + (S.run.to - S.run.from) * e);
    if (u >= 1) { const r = S.run; S.run = null; save(); r.resolve(api.time()); }
  }
  draw();
  drawLoupe();
  raf = requestAnimationFrame(frame);
}

const ready = Promise.all([(opts.art && opts.art.board) || A.base, SP.pulley.src, SP.crankwheel.src, SP.yoke.src, SP.crankArm.src, SP.crankKnob.src, SP.pen.src,
  ...A.shelf.pegs.map((p) => p.sprite)].map(loadImg)).then((ims) => {
  [baseImg, pulleyImg, wheelImg, yokeImg, armImg, knobImg, penImg, ...pegImgs] = ims;
  for (const [n, im] of Object.entries({ baseImg, pulleyImg, wheelImg, yokeImg, armImg, knobImg, penImg })) if (!im) console.error('tide: missing art ' + n);
  if (dead) return;
  loaded = true; resize();
  raf = requestAnimationFrame(frame);
});

const api = {
  place(shaftId, pulleyId) {
    if (!(shaftId in S.arr)) throw new Error('unknown shaft ' + shaftId);
    if (pulleyId && !inTray(pulleyId)) throw new Error('pulley not carried ' + pulleyId);
    placeRaw(shaftId, pulleyId || null); arrangementChanged(); return api.arrangement();
  },
  arrangement() { return { ...S.arr }; },
  datum() { return cfg.z0; },
  setDatum(z) { setDatum(z); return cfg.z0; },
  setTime(iso) { jumpTo(M.isoToHours(iso, cfg)); save(); return api.time(); },
  time() { return M.hoursToIso(S.t, cfg); },
  level() { return M.mechanism(S.t, S.arr, cfg, G).h; },
  penLevel() { return M.chartLevel(M.mechanism(S.t, S.arr, cfg, G).penY, G); },
  runTo(iso, ms = 2000) {
    return new Promise((resolve) => { S.run = { from: S.t, to: clampT(M.isoToHours(iso, cfg)), t0: performance.now(), ms: Math.max(1, ms), resolve }; });
  },
  shelf() { return A.shelf.order.filter(inTray); },
  ready,
  destroy() {
    dead = true; cancelAnimationFrame(raf); clearTimeout(loupeTimer);
    if (ro) ro.disconnect();
    offs.forEach((f) => f()); offs.length = 0;
    if (actx) { try { actx.close(); } catch (e) { /* already closed */ } }
    stage.remove();
  },
};
return api;
}
