// The Drawdown Board — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"drawdown"`), ported
// 2026-10-20 from the diamonds prototype (rooms/regression/diamonds/_scratch/drawdown_board/).
//
// A painted still with code-drawn, physics-driven parts: five brass pegs on rails 1-5, a sprung rod that,
// once the lever releases it, settles on the ordinary-least-squares line through the pegs
// (drawdown_physics.js proves why), read by eye where it crosses rail 6. It is READ, never graded: it
// never logs to the notebook, never solves or gates anything, and holds no answer — the student sets the
// pegs from what the world shows them and reads the projection off the scale.
//
// All drawing happens in IMAGE coordinates (the geometry's pixels); one transform maps them to the
// letterboxed, high-DPI canvas. The geometry (calibration of the painted still) and the art paths come
// from the hotspot, so the same module serves any board.
//
//   const board = mountDrawdown(hostEl, { geometry, art: {board, peg, spring, rod, leverThrown}, pegs?,
//                                         onPegs?(values), sound?, debug? });
//   board.setPegs([...]); board.release(); board.clamp(); board.isSettled(); board.rodValueAt(i);
//   board.olsAt(i); board.pegs(); board.released; board.ready (Promise); board.destroy();
import { RodSim, ols } from "./drawdown_physics.js?v=137";

// Where things sit inside the peg sprite, as fractions of its height (measured from the prototype's
// peg_k.png; the code-drawn fallback peg uses the same proportions). Geometry may override each
// (pegIndexY, pegHookY, rodThick, springW).
const PEG_ASPECT = 621 / 729;   // fallback peg height / width
const RAIL_PLATE_W = 13;     // slim tick plates beside rails 1-5
const LEVER_FADE_MS = 150;
const LEVER_RECT_DEFAULT = { x: 1040, y: 250, w: 140, h: 270 };
const SHADOW = { dx: 4, dy: 6, blur: 6, alpha: 0.5 };   // light from upper left
const ENG_HI = "rgba(255,238,196,0.5)", ENG_LO = "rgba(46,28,10,0.82)";

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});

export function mountDrawdown(host, opts = {}) {
  const G = opts.geometry;
  if (!G || !Array.isArray(G.rails) || G.rails.length !== 6) throw new Error("drawdown: geometry needs six rails");
  const artPaths = opts.art || {};
  const DEBUG = !!opts.debug;
  const META = {
    indexY: Number.isFinite(G.pegIndexY) ? G.pegIndexY : 0.71,
    hookY: Number.isFinite(G.pegHookY) ? G.pegHookY : 0.125,
  };
  const ROD_THICK = Number.isFinite(G.rodThick) ? G.rodThick : 0.24;
  const SPRING_W = Number.isFinite(G.springW) ? G.springW : 0.3;

  const canvas = document.createElement("canvas");
  canvas.className = "drawdowncanvas";
  canvas.style.aspectRatio = `${G.imageW} / ${G.imageH}`;
  host.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  const scene = document.createElement("canvas"), sctx = scene.getContext("2d");
  const stat = document.createElement("canvas"), tctx = stat.getContext("2d");   // art + engravings, cached

  let art = {}, view = { dpr: 1, cw: 1, ch: 1, S: 1, ox: 0, oy: 0 }, brass = [176, 138, 70];
  let released = false, loaded = false, dead = false, raf = 0;
  let rod = { h: G.parkValue, s: 0 };     // displayed rod state when clamped
  let parkAnim = null;                    // {from:{h,s}, t0, dur}
  const fx = { flash: -1, jolt: -1 };
  const lever = { img: null, rect: null, patch: null, t: 0, from: 0, to: 0, t0: 0 };  // thrown-art crossfade
  let drag = null, loupe = null;
  let lastT = performance.now(), needDraw = true, leverAnimating = false;

  // Physics runs in season units: rail i sits at x = i, exactly evenly pitched, as the instrument is meant
  // to be. The painted rails are not quite even, so drawing maps x linearly through rails 1 and 6 only:
  // the rod's crossing of rail 6 then reads the season-6 value exactly.
  const pitch = (G.rails[5].x - G.rails[0].x) / 5;
  const physX = G.rails.map((_, i) => i);
  const xcPhys = (physX[0] + physX[5]) / 2;                    // rod overhang is symmetric
  const lengthPhys = (G.rails[5].x - G.rails[0].x + 2 * G.rodOverhang) / pitch;
  const sim = new RodSim({ xc: xcPhys, refXs: physX.slice(0, 5), length: lengthPhys });

  // ---------- geometry helpers ----------
  const yTop = () => G.rails[0].yTop, yBot = () => G.rails[0].yBottom;
  const valueToY = (v) => yBot() - ((v - G.vMin) / (G.vMax - G.vMin)) * (yBot() - yTop());
  const yToValue = (y) => G.vMin + ((yBot() - y) / (yBot() - yTop())) * (G.vMax - G.vMin);
  const pxToPhys = (px) => (px - G.rails[0].x) / pitch;
  const snap = (v) => {
    const d = G.detent;
    const s = G.vMin + Math.round((v - G.vMin) / d) * d;
    return Math.min(G.vMax, Math.max(G.vMin, s));
  };
  const rodState = () => (released ? { h: sim.h, s: sim.s } : rod);
  const rodValAtPhys = (x) => { const r = rodState(); return r.h + r.s * (x - xcPhys); };
  const rodYAtPx = (px) => valueToY(rodValAtPhys(pxToPhys(px)));
  const pegH = () => G.pegW * (art.peg ? art.peg.naturalHeight / art.peg.naturalWidth : PEG_ASPECT);
  const fit = () => ols(physX.slice(0, 5), pegVals);

  const start = Array.isArray(opts.pegs) ? opts.pegs : G.pegStart;
  let pegVals = G.pegStart.map((v, i) => snap(Number.isFinite(start[i]) ? start[i] : v));
  sim.setPegs(pegVals.map((y, i) => ({ x: physX[i], y })));

  // ---------- loading ----------
  const ready = (async () => {
    const [board, peg, spring, rodImg, thrown] = await Promise.all(
      [artPaths.board, artPaths.peg, artPaths.spring, artPaths.rod, artPaths.leverThrown].map(loadImg));
    if (dead) return;
    art = { board, peg, spring, rod: rodImg };
    if (board) brass = sampleBrass(board);
    if (thrown) {
      const lt = G.leverThrown || {};
      lever.img = thrown;
      lever.rect = lt.rect || LEVER_RECT_DEFAULT;
      lever.patch = featheredPatch(thrown, lever.rect, Number.isFinite(lt.feather) ? lt.feather : 10);
    }
    loaded = true;
    resize();
  })();

  // Cut the lever rect out of the thrown-lever image with feathered edges, so a slightly drifted image
  // edit blends into the base painting.
  function featheredPatch(img, r, feather) {
    const kx = img.naturalWidth / G.imageW, ky = img.naturalHeight / G.imageH;
    const w = Math.round(r.w * kx), h = Math.round(r.h * ky), f = feather * kx;
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const x = c.getContext("2d");
    x.drawImage(img, r.x * kx, r.y * ky, w, h, 0, 0, w, h);
    try {
      const d = x.getImageData(0, 0, w, h);
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        const e = Math.min(i, j, w - 1 - i, h - 1 - j);
        if (e < f) d.data[(j * w + i) * 4 + 3] *= e / f;
      }
      x.putImageData(d, 0, 0);
    } catch { /* tainted canvas: use the hard-edged patch */ }
    return c;
  }

  function leverTo(target) {
    if (!lever.img) return;
    lever.from = lever.t; lever.to = target; lever.t0 = performance.now();
  }

  function sampleBrass(img) {
    const c = document.createElement("canvas"); c.width = c.height = 1;
    const x = c.getContext("2d");
    const s = G.strip, h = yBot() - yTop();
    try {
      x.drawImage(img, s.x0 + 4, yTop() + h * 0.2, s.x1 - s.x0 - 8, h * 0.6, 0, 0, 1, 1);
      const d = x.getImageData(0, 0, 1, 1).data;
      return [d[0], d[1], d[2]];
    } catch { return brass; }
  }

  // ---------- state changes ----------
  function setPeg(i, v, sound) {
    const nv = snap(v);
    if (nv === pegVals[i]) return;
    if (sound) ratchet(Math.abs(nv - pegVals[i]) / G.detent);
    pegVals[i] = nv;
    sim.setPegValue(i, nv);
    needDraw = true;
    if (opts.onPegs) opts.onPegs(pegVals.slice());
  }

  function release() {
    if (released) return;
    const r = rod;
    parkAnim = null;
    sim.setPegs(pegVals.map((y, i) => ({ x: physX[i], y })));
    sim.reset(r.h, r.s);
    released = true;
    leverTo(1);
    fx.flash = fx.jolt = performance.now();
    clunk(); twang();
    needDraw = true;
  }

  function clamp() {
    if (!released) return;
    rod = { h: sim.h, s: sim.s };
    released = false;
    leverTo(0);
    parkAnim = { from: { ...rod }, t0: performance.now(), dur: 900 };
    fx.flash = fx.jolt = performance.now();
    clunk();
    needDraw = true;
  }

  // ---------- layout ----------
  function resize() {
    if (dead) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cw = Math.max(1, canvas.clientWidth), ch = Math.max(1, canvas.clientHeight);
    for (const c of [canvas, scene, stat]) { c.width = Math.round(cw * dpr); c.height = Math.round(ch * dpr); }
    const k = Math.min(cw / G.imageW, ch / G.imageH);
    view = { dpr, cw, ch, S: k * dpr, ox: ((cw - G.imageW * k) / 2) * dpr, oy: ((ch - G.imageH * k) / 2) * dpr };
    if (loaded) buildStatic();
    needDraw = true;
  }
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => resize()) : null;
  if (ro) ro.observe(canvas); else addEventListener("resize", resize);

  const toImage = (e) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * view.dpr - view.ox) / view.S,
             y: ((e.clientY - r.top) * view.dpr - view.oy) / view.S };
  };

  // ---------- static layer: art + engravings ----------
  function buildStatic() {
    const c = tctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.fillStyle = "#0b0806"; c.fillRect(0, 0, stat.width, stat.height);
    c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
    c.imageSmoothingQuality = "high";
    if (art.board) c.drawImage(art.board, 0, 0, G.imageW, G.imageH);
    else drawPlaceholder(c);
    engraveStrip(c);
    for (let i = 0; i < 5; i++) drawRailPlate(c, i);
    drawReadoutPlate(c);
    engravePlaques(c);
  }

  function drawPlaceholder(c) {
    c.fillStyle = "#3b3a33"; c.fillRect(0, 0, G.imageW, G.imageH);
    const x0 = G.strip.x0 - 40, y0 = yTop() - 70;
    const x1 = G.lever.x + G.lever.w + 30;
    const y1 = Math.max(...G.plaques.map((p) => p.y + p.h)) + 40;
    const g = c.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, "#4a2a18"); g.addColorStop(0.5, "#3a1f12"); g.addColorStop(1, "#2c170d");
    c.fillStyle = g; c.fillRect(x0, y0, x1 - x0, y1 - y0);
    c.strokeStyle = "#8a6a32"; c.lineWidth = 10; c.strokeRect(x0, y0, x1 - x0, y1 - y0);
    c.fillStyle = `rgb(${brass})`;
    c.fillRect(G.strip.x0, yTop() - 30, G.strip.x1 - G.strip.x0, yBot() - yTop() + 60);
    for (const r of G.rails) {
      c.fillStyle = "#8d8a80"; c.fillRect(r.x - G.railW / 2 - 4, r.yTop - 14, G.railW + 8, r.yBottom - r.yTop + 28);
      c.fillStyle = "#1d140d"; c.fillRect(r.x - G.railW / 4, r.yTop, G.railW / 2, r.yBottom - r.yTop);
    }
    for (const p of G.plaques) {
      c.fillStyle = `rgb(${brass})`; c.beginPath();
      c.ellipse(p.x + p.w / 2, p.y + p.h / 2, p.w / 2, p.h / 2, 0, 0, Math.PI * 2); c.fill();
    }
    const L = G.lever;
    c.fillStyle = "#6d5428"; c.fillRect(L.x, L.y + L.h * 0.55, L.w, L.h * 0.45);
    c.fillStyle = `rgb(${brass})`; c.fillRect(L.x + L.w * 0.65, L.y, L.w * 0.12, L.h * 0.8);
  }

  // Engraving: a light 1px highlight offset down-right, then the dark recess on top.
  function engraveLines(c, segs, w) {
    c.lineCap = "butt";
    for (const [col, off] of [[ENG_HI, 0.7], [ENG_LO, 0]]) {
      c.strokeStyle = col; c.lineWidth = w; c.beginPath();
      for (const [x1, y1, x2, y2] of segs) { c.moveTo(x1 + off, y1 + off); c.lineTo(x2 + off, y2 + off); }
      c.stroke();
    }
  }
  function engraveText(c, txt, x, y, size, align = "right") {
    c.font = `600 ${size}px Georgia, "Times New Roman", serif`;
    c.textAlign = align; c.textBaseline = "middle";
    c.fillStyle = ENG_HI; c.fillText(txt, x + 0.7, y + 0.7);
    c.fillStyle = ENG_LO; c.fillText(txt, x, y);
  }

  // minor every detent, mid every 10, numerals every 20; ticks grow leftward from xEdge
  function engraveScale(c, xEdge, lens, numX, numSize) {
    const segs = { minor: [], mid: [], major: [] };
    for (let v = G.vMin; v <= G.vMax + 1e-9; v += G.detent) {
      const y = valueToY(v);
      const kind = v % 20 === 0 ? "major" : v % 10 === 0 ? "mid" : "minor";
      segs[kind].push([xEdge - lens[kind], y, xEdge, y]);
      if (kind === "major" && numX !== null) engraveText(c, String(v), numX, y, numSize);
    }
    engraveLines(c, segs.minor, 0.8);
    engraveLines(c, segs.mid, 1.1);
    engraveLines(c, segs.major, 1.4);
  }

  function engraveStrip(c) {
    const s = G.strip, xe = s.x1 - 3;
    c.save(); c.globalAlpha = 0.92;
    engraveScale(c, xe, { minor: 5, mid: 9, major: 13 }, xe - 15, 10.5);
    c.restore();
  }

  // A narrow riveted brass scale plate on the LEFT of rail 6 (the lever is to its right).
  function plateRect() {
    const r6 = G.rails[5];
    const xr = r6.x - G.railW / 2 - 4, w = 30;
    return { x: xr - w, y: r6.yTop - 14, w, h: r6.yBottom - r6.yTop + 28 };
  }
  // Slim riveted tick plate on the left of rail i (1-5): ticks only, no numerals. Its right edge sits just
  // clear of the peg's left face so the peg's index notch meets the tick ends.
  function railPlateRect(i) {
    const r = G.rails[i], xr = r.x - G.pegW / 2 - 1;
    return { x: xr - RAIL_PLATE_W, y: r.yTop - 12, w: RAIL_PLATE_W, h: r.yBottom - r.yTop + 24 };
  }
  function drawRailPlate(c, i) {
    const p = railPlateRect(i);
    brassPlate(c, p, 2);
    engraveScale(c, p.x + p.w - 1.5, { minor: 4, mid: 7, major: 9 }, null, 0);
  }

  function drawReadoutPlate(c) {
    const p = plateRect();
    brassPlate(c, p, 2.6);
    const xe = p.x + p.w - 2;
    engraveScale(c, xe, { minor: 4, mid: 7, major: 10 }, xe - 12, 9.5);
  }

  function brassPlate(c, p, rivetR) {
    const [r, g, b] = brass;
    const lit = (f) => `rgb(${Math.min(255, r * f) | 0},${Math.min(255, g * f) | 0},${Math.min(255, b * f) | 0})`;
    c.save();
    c.shadowColor = "rgba(0,0,0,0.55)"; c.shadowBlur = 5 * view.S;
    c.shadowOffsetX = 2 * view.S; c.shadowOffsetY = 3 * view.S;
    const grad = c.createLinearGradient(p.x, p.y, p.x + p.w, p.y + p.h);
    grad.addColorStop(0, lit(1.18)); grad.addColorStop(0.45, lit(1.0)); grad.addColorStop(1, lit(0.78));
    c.fillStyle = grad; c.fillRect(p.x, p.y, p.w, p.h);
    c.restore();
    if (art.board) {
      // Re-use the painted blank strip's brass (same light, same patina), skipping its corner rivets, so
      // the plate belongs to the painting.
      const s = G.strip, sh = yBot() - yTop();
      c.drawImage(art.board, s.x0 + 2, yTop() - 10, s.x1 - s.x0 - 4, sh + 20, p.x, p.y, p.w, p.h);
    } else {
      c.save(); c.globalAlpha = 0.07; c.strokeStyle = "#fff";
      for (let i = 0; i < 60; i++) {
        const x = p.x + ((i * 7.31) % p.w); c.lineWidth = 0.4;
        c.beginPath(); c.moveTo(x, p.y); c.lineTo(x + 0.3, p.y + p.h); c.stroke();
      }
      c.restore();
    }
    c.lineWidth = 1;
    c.strokeStyle = "rgba(255,240,200,0.45)"; c.beginPath();
    c.moveTo(p.x + 0.5, p.y + p.h); c.lineTo(p.x + 0.5, p.y + 0.5); c.lineTo(p.x + p.w, p.y + 0.5); c.stroke();
    c.strokeStyle = "rgba(40,22,6,0.6)"; c.beginPath();
    c.moveTo(p.x + p.w - 0.5, p.y); c.lineTo(p.x + p.w - 0.5, p.y + p.h - 0.5); c.lineTo(p.x, p.y + p.h - 0.5); c.stroke();
    for (const yy of [p.y + 6, p.y + p.h - 6]) rivet(c, p.x + p.w / 2, yy, rivetR);
  }

  function rivet(c, x, y, r) {
    const g = c.createRadialGradient(x - r * 0.4, y - r * 0.4, r * 0.1, x, y, r);
    g.addColorStop(0, "#fff3cf"); g.addColorStop(0.4, `rgb(${brass})`); g.addColorStop(1, "#4a3212");
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
  }

  function engravePlaques(c) {
    G.plaques.forEach((p, i) => {
      if (G.years && G.years[i]) engraveText(c, G.years[i], p.x + p.w / 2, p.y + p.h / 2 + 0.5, Math.min(16, p.h * 0.46), "center");
    });
  }

  // ---------- dynamic parts ----------
  function withShadow(c, lift, fn) {
    c.save();
    c.shadowColor = `rgba(18,8,2,${SHADOW.alpha})`;
    c.shadowBlur = SHADOW.blur * lift * view.S;
    c.shadowOffsetX = SHADOW.dx * lift * view.S;
    c.shadowOffsetY = SHADOW.dy * lift * view.S;
    fn(); c.restore();
  }

  function pegGeom(i) {
    const H = pegH(), cx = G.rails[i].x, cy = valueToY(pegVals[i]);
    const top = cy - META.indexY * H;
    return { cx, cy, H, top, hookY: top + META.hookY * H };
  }

  function drawPeg(c, i) {
    const { cx, H, top } = pegGeom(i), W = G.pegW;
    const lift = drag && drag.i === i ? 1.7 : 1;
    withShadow(c, lift, () => {
      if (art.peg) c.drawImage(art.peg, cx - W / 2, top, W, H);
      else codePeg(c, cx, top, W, H);
    });
    // engraved index notch on the peg's left face, at exactly its value height
    const y = valueToY(pegVals[i]), x0 = cx - W / 2 + 0.5;
    engraveLines(c, [[x0, y, x0 + W * 0.2, y]], 1.1);
  }

  function codePeg(c, cx, top, W, H) {
    const bTop = top + 0.3 * H, bH = 0.7 * H, x = cx - W / 2;
    const g = c.createLinearGradient(x, bTop, x + W * 0.4, bTop + bH);
    g.addColorStop(0, "#f6dc97"); g.addColorStop(0.35, "#c9a04f"); g.addColorStop(1, "#6b4a1c");
    c.fillStyle = g; c.fillRect(x, bTop, W, bH);
    c.strokeStyle = "rgba(50,30,8,0.6)"; c.lineWidth = 0.8; c.strokeRect(x + 0.4, bTop + 0.4, W - 0.8, bH - 0.8);
    c.fillStyle = "rgba(40,24,8,0.5)"; c.fillRect(x, bTop + bH * 0.22, W, 1); c.fillRect(x, bTop + bH * 0.82, W, 1);
    const ky = top + META.indexY * H, kr = H * 0.17;
    const kg = c.createRadialGradient(cx - kr * 0.4, ky - kr * 0.4, 1, cx, ky, kr);
    kg.addColorStop(0, "#fff1c4"); kg.addColorStop(0.5, "#c79a45"); kg.addColorStop(1, "#5a3c14");
    c.fillStyle = kg; c.beginPath(); c.arc(cx, ky, kr, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#b08a42"; c.fillRect(cx - W * 0.07, top + 0.18 * H, W * 0.14, 0.13 * H);
    c.strokeStyle = "#d8b56a"; c.lineWidth = H * 0.05;
    c.beginPath(); c.arc(cx, top + META.hookY * H, H * 0.08, 0, Math.PI * 2); c.stroke();
  }

  function drawSpring(c, x, y1, y2) {
    const w = G.pegW * SPRING_W;
    let a = Math.min(y1, y2), len = Math.abs(y2 - y1);
    if (len < 5) { len = 5; a = y1 - (y2 < y1 ? 5 : 0); }
    withShadow(c, 0.8, () => {
      if (art.spring) { c.drawImage(art.spring, x - w / 2, a, w, len); return; }
      // code helix: coils whose pitch spreads with the stretch
      const coils = 14, steps = coils * 12;
      for (let k = 0; k < steps; k++) {
        const u0 = k / steps, u1 = (k + 1) / steps;
        const p0 = Math.sin(u0 * coils * Math.PI * 2), p1 = Math.sin(u1 * coils * Math.PI * 2);
        const front = Math.cos(u0 * coils * Math.PI * 2) > 0;
        c.strokeStyle = front ? "#e8c77a" : "#7a5523";
        c.lineWidth = front ? 1.5 : 1.1;
        c.beginPath(); c.moveTo(x + p0 * w / 2, a + u0 * len); c.lineTo(x + p1 * w / 2, a + u1 * len); c.stroke();
      }
    });
  }

  function drawRod(c) {
    const xL = G.rails[0].x - G.rodOverhang, xR = G.rails[5].x + G.rodOverhang;
    const yL = rodYAtPx(xL), yR = rodYAtPx(xR);
    const T = G.pegW * ROD_THICK, len = Math.hypot(xR - xL, yR - yL);
    withShadow(c, 1.4, () => {
      c.save(); c.translate(xL, yL); c.rotate(Math.atan2(yR - yL, xR - xL));
      if (art.rod) c.drawImage(art.rod, 0, -T / 2, len, T);
      else {
        const g = c.createLinearGradient(0, -T / 2, 0, T / 2);
        g.addColorStop(0, "#7a5520"); g.addColorStop(0.18, "#fff0bf"); g.addColorStop(0.42, "#d5a952");
        g.addColorStop(0.8, "#7d561e"); g.addColorStop(1, "#3b2508");
        c.fillStyle = g; c.beginPath();
        if (c.roundRect) c.roundRect(0, -T / 2, len, T, T / 2); else c.rect(0, -T / 2, len, T);
        c.fill();
      }
      c.restore();
    });
    // scribed reading line along the rod's centre
    c.save(); c.translate(xL, yL); c.rotate(Math.atan2(yR - yL, xR - xL));
    c.strokeStyle = "rgba(255,240,200,0.35)"; c.lineWidth = 0.6;
    c.beginPath(); c.moveTo(4, 0.6); c.lineTo(len - 4, 0.6); c.stroke();
    c.strokeStyle = "rgba(52,30,8,0.7)";
    c.beginPath(); c.moveTo(4, 0); c.lineTo(len - 4, 0); c.stroke();
    c.restore();
  }

  function drawStops(c) {
    const T = G.pegW * ROD_THICK, y = valueToY(G.parkValue) + T / 2;
    const xs = [G.rails[0].x - G.rodOverhang * 0.6, G.rails[5].x + G.rodOverhang * 0.6];
    for (const x of xs) withShadow(c, 0.6, () => {
      const [r, gg, b] = brass, sh = (f) => `rgb(${r * f | 0},${gg * f | 0},${b * f | 0})`;
      const g = c.createLinearGradient(x - 6, y, x + 6, y + 9);
      g.addColorStop(0, sh(1.15)); g.addColorStop(0.5, sh(0.85)); g.addColorStop(1, sh(0.5));
      c.fillStyle = g; c.fillRect(x - 6, y, 12, 9);
      rivet(c, x, y + 4.5, 1.8);
    });
  }

  function drawLeverArt(c, now) {
    if (!lever.patch) return false;
    const u = Math.min(1, (now - lever.t0) / LEVER_FADE_MS);
    const e = u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2;
    lever.t = lever.from + (lever.to - lever.from) * e;
    if (lever.t > 0.001) {
      const r = lever.rect;
      c.save(); c.globalAlpha = lever.t;
      c.drawImage(lever.patch, r.x, r.y, r.w, r.h);
      c.restore();
    }
    return u < 1;
  }

  function drawLeverFx(c, now) {
    const L = G.lever, cx = L.x + L.w * 0.72, cy = L.y + L.h * 0.55;
    c.save(); c.globalCompositeOperation = "lighter";
    const f = fx.flash >= 0 ? Math.max(0, 1 - (now - fx.flash) / 380) : 0;
    // the thrown-lever art carries the state change, so the flash only accents it
    const glow = lever.patch ? 0.18 * f : (released ? 0.16 : 0) + 0.55 * f;
    if (glow > 0.005) {
      const g = c.createRadialGradient(cx, cy, 4, cx, cy, L.h * 0.6);
      g.addColorStop(0, `rgba(255,214,140,${glow})`); g.addColorStop(1, "rgba(255,190,90,0)");
      c.fillStyle = g; c.fillRect(L.x - L.w, L.y - 40, L.w * 3, L.h + 80);
    }
    c.restore();
  }

  function drawDebug(c) {
    c.save();
    c.lineWidth = 1; c.setLineDash([]);
    c.strokeStyle = "rgba(0,255,255,0.8)";
    for (const r of G.rails) { c.beginPath(); c.moveTo(r.x, r.yTop - 20); c.lineTo(r.x, r.yBottom + 20); c.stroke(); }
    c.strokeStyle = "rgba(255,0,255,0.8)";
    for (const y of [yTop(), yBot()]) { c.beginPath(); c.moveTo(G.strip.x0 - 10, y); c.lineTo(G.rails[5].x + 30, y); c.stroke(); }
    c.strokeStyle = "rgba(255,255,0,0.8)";
    for (const x of [G.strip.x0, G.strip.x1]) { c.beginPath(); c.moveTo(x, yTop() - 30); c.lineTo(x, yBot() + 30); c.stroke(); }
    c.strokeStyle = "rgba(0,255,0,0.8)"; for (const p of G.plaques) c.strokeRect(p.x, p.y, p.w, p.h);
    c.strokeStyle = "rgba(255,140,0,0.9)"; c.strokeRect(G.lever.x, G.lever.y, G.lever.w, G.lever.h);
    if (lever.rect) { c.setLineDash([3, 3]); c.strokeRect(lever.rect.x, lever.rect.y, lever.rect.w, lever.rect.h); c.setLineDash([]); }
    c.strokeStyle = "rgba(255,40,40,0.9)";
    pegVals.forEach((_, i) => { const g = pegGeom(i); c.beginPath(); c.moveTo(g.cx - 30, g.cy); c.lineTo(g.cx + 30, g.cy); c.stroke(); });
    const f = fit(), xL = G.rails[0].x - G.rodOverhang, xR = G.rails[5].x + G.rodOverhang;
    c.setLineDash([6, 4]);
    c.beginPath(); c.moveTo(xL, valueToY(f.at(pxToPhys(xL)))); c.lineTo(xR, valueToY(f.at(pxToPhys(xR)))); c.stroke();
    c.restore();
    const lines = [
      `rod @ rail 6: ${api.rodValueAt(5).toFixed(2)}   OLS @ rail 6: ${api.olsAt(5).toFixed(2)}`,
      `${released ? "released" : "clamped"}   settled ${api.isSettled()}   pegs ${pegVals.join(", ")}`,
    ];
    c.save(); c.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
    c.font = "13px ui-monospace, Menlo, monospace";
    c.fillStyle = "rgba(0,0,0,0.72)"; c.fillRect(8, 8, 470, 18 * lines.length + 10);
    c.fillStyle = "#9ff"; lines.forEach((l, i) => c.fillText(l, 16, 26 + 18 * i));
    c.restore();
  }

  function drawLoupe(c) {
    const dpr = view.dpr, R = Math.min(78, 0.2 * Math.min(view.cw, view.ch)) * dpr, M = 2.5;
    const px = loupe.x * dpr, py = loupe.y * dpr;
    let cx = px, cy = py - R - 26 * dpr;
    if (cy - R < 4 * dpr) cy = py + R + 26 * dpr;
    cx = Math.min(view.cw * dpr - R - 4, Math.max(R + 4, cx));
    const sw = (2 * R) / M;
    c.save();
    c.shadowColor = "rgba(0,0,0,0.6)"; c.shadowBlur = 18 * dpr; c.shadowOffsetY = 6 * dpr;
    c.fillStyle = "#000"; c.beginPath(); c.arc(cx, cy, R, 0, Math.PI * 2); c.fill();
    c.restore();
    c.save(); c.beginPath(); c.arc(cx, cy, R, 0, Math.PI * 2); c.clip();
    c.imageSmoothingQuality = "high";
    c.drawImage(scene, px - sw / 2, py - sw / 2, sw, sw, cx - R, cy - R, 2 * R, 2 * R);
    const gl = c.createRadialGradient(cx - R * 0.45, cy - R * 0.5, R * 0.05, cx, cy, R);
    gl.addColorStop(0, "rgba(255,255,255,0.16)"); gl.addColorStop(0.5, "rgba(255,255,255,0)"); gl.addColorStop(1, "rgba(0,0,0,0.25)");
    c.fillStyle = gl; c.fillRect(cx - R, cy - R, 2 * R, 2 * R);
    // fine reticle marks at the edges, level with the sampled point
    c.strokeStyle = "rgba(20,10,4,0.7)"; c.lineWidth = 1.2 * dpr;
    c.beginPath(); c.moveTo(cx - R, cy); c.lineTo(cx - R * 0.78, cy); c.moveTo(cx + R * 0.78, cy); c.lineTo(cx + R, cy); c.stroke();
    c.restore();
    const ring = c.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
    ring.addColorStop(0, "#fbe3a3"); ring.addColorStop(0.5, "#a57a33"); ring.addColorStop(1, "#4c3210");
    c.strokeStyle = ring; c.lineWidth = 6 * dpr; c.beginPath(); c.arc(cx, cy, R + 2 * dpr, 0, Math.PI * 2); c.stroke();
  }

  // ---------- frame ----------
  const fxActive = (now) => (fx.flash >= 0 && now - fx.flash < 400) || (fx.jolt >= 0 && now - fx.jolt < 400);
  function tick(now) {
    if (dead) return;
    const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now;
    let busy = false;
    if (released) { const was = sim.settled; sim.advance(dt); busy = !sim.settled || was !== sim.settled; }
    if (parkAnim) {
      const u = Math.min(1, (now - parkAnim.t0) / parkAnim.dur);
      const e = u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2;
      rod = { h: parkAnim.from.h + (G.parkValue - parkAnim.from.h) * e, s: parkAnim.from.s * (1 - e) };
      if (u >= 1) parkAnim = null;
      busy = true;
    }
    if (loaded && (busy || needDraw || drag || loupe || leverAnimating || fxActive(now))) { draw(now); needDraw = false; }
    raf = requestAnimationFrame(tick);
  }

  function draw(now) {
    const c = sctx;
    let jy = 0;
    if (fx.jolt >= 0) { const t = (now - fx.jolt) / 1000; if (t < 0.4) jy = 1.8 * Math.exp(-t * 12) * Math.sin(t * 75); }
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.fillStyle = "#0b0806"; c.fillRect(0, 0, scene.width, scene.height);
    c.drawImage(stat, 0, jy * view.S);
    c.setTransform(view.S, 0, 0, view.S, view.ox, view.oy + jy * view.S);
    c.imageSmoothingQuality = "high";
    leverAnimating = drawLeverArt(c, now);
    drawStops(c);
    for (let i = 0; i < 5; i++) drawPeg(c, i);
    for (let i = 0; i < 5; i++) {
      const g = pegGeom(i);
      if (released) drawSpring(c, g.cx, g.hookY, rodYAtPx(g.cx));
      else drawSpring(c, g.cx, g.hookY, g.hookY + g.H * 0.42 + Math.sin(now / 900 + i) * 0.6);
    }
    drawRod(c);
    drawLeverFx(c, now);
    if (DEBUG) drawDebug(c);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(scene, 0, 0);
    if (loupe) drawLoupe(ctx);
  }

  // ---------- input ----------
  function hitPeg(p, touch) {
    let best = -1, bd = Infinity;
    const padX = G.pegW * (touch ? 0.95 : 0.6), padY = touch ? 14 : 4;
    for (let i = 0; i < 5; i++) {
      const g = pegGeom(i);
      if (Math.abs(p.x - g.cx) > padX) continue;
      if (p.y < g.top - padY || p.y > g.top + g.H + padY) continue;
      const d = Math.abs(p.y - g.cy) + Math.abs(p.x - g.cx);
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }
  const inRect = (p, r, pad) => p.x >= r.x - pad && p.x <= r.x + r.w + pad && p.y >= r.y - pad && p.y <= r.y + r.h + pad;
  // When thrown, the handle reaches out across the wall, so the hit area grows to cover it.
  const inLever = (p) => inRect(p, G.lever, 8) || (released && lever.rect && inRect(p, lever.rect, 4));
  function inLoupeZone(p) {
    const yOk = p.y > yTop() - 40 && p.y < yBot() + 40;
    const pr = plateRect();
    const near6 = p.x > pr.x - 40 && p.x < G.rails[5].x + 40;
    const nearStrip = p.x > G.strip.x0 - 40 && p.x < G.strip.x1 + 40;
    const nearPlate = [0, 1, 2, 3, 4].some((i) => { const q = railPlateRect(i); return p.x > q.x - 14 && p.x < q.x + q.w + 4; });
    return yOk && (near6 || nearStrip || nearPlate);
  }

  canvas.addEventListener("pointerdown", (e) => {
    audio();
    const p = toImage(e), touch = e.pointerType !== "mouse";
    const i = hitPeg(p, touch);
    if (i >= 0) {
      drag = { i, id: e.pointerId, grab: pegGeom(i).cy - p.y };
      canvas.setPointerCapture(e.pointerId);
    } else if (inLever(p)) {
      released ? clamp() : release();
    } else if (inLoupeZone(p)) {
      const r = canvas.getBoundingClientRect();
      loupe = { id: e.pointerId, x: e.clientX - r.left, y: e.clientY - r.top };
      canvas.setPointerCapture(e.pointerId);
    }
    needDraw = true;
    e.preventDefault();
  });
  canvas.addEventListener("pointermove", (e) => {
    const p = toImage(e);
    if (drag && e.pointerId === drag.id) setPeg(drag.i, yToValue(p.y + drag.grab), true);
    else if (loupe && e.pointerId === loupe.id) {
      const r = canvas.getBoundingClientRect();
      loupe.x = e.clientX - r.left; loupe.y = e.clientY - r.top;
    } else if (e.pointerType === "mouse") {
      canvas.style.cursor = hitPeg(p, false) >= 0 ? "grab" : inLever(p) ? "pointer" : inLoupeZone(p) ? "zoom-in" : "default";
    }
  });
  const endPointer = (e) => {
    if (drag && e.pointerId === drag.id) drag = null;
    if (loupe && e.pointerId === loupe.id) loupe = null;
    needDraw = true;
  };
  canvas.addEventListener("pointerup", endPointer);
  canvas.addEventListener("pointercancel", endPointer);
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());

  // ---------- sound (synthesised, quiet, created only inside a user gesture) ----------
  let actx = null, master = null, noiseBuf = null, lastClick = 0;
  function audio() {
    if (opts.sound === false) return;
    try {
      if (!actx) {
        actx = new (window.AudioContext || window.webkitAudioContext)();
        master = actx.createGain(); master.gain.value = 0.55; master.connect(actx.destination);
        noiseBuf = actx.createBuffer(1, actx.sampleRate * 0.3, actx.sampleRate);
        const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      }
      if (actx.state === "suspended") actx.resume();
    } catch { actx = null; }
  }
  function env(g, t, peak, decay) {
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + 0.002);
    g.gain.exponentialRampToValueAtTime(0.0001, t + decay);
  }
  function noise(t, type, freq, q, peak, decay) {
    const s = actx.createBufferSource(); s.buffer = noiseBuf;
    const f = actx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = actx.createGain(); env(g, t, peak, decay);
    s.connect(f).connect(g).connect(master); s.start(t); s.stop(t + decay + 0.02);
  }
  function tone(t, type, f0, f1, peak, decay) {
    const o = actx.createOscillator(); o.type = type;
    o.frequency.setValueAtTime(f0, t); if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + decay);
    const g = actx.createGain(); env(g, t, peak, decay);
    o.connect(g).connect(master); o.start(t); o.stop(t + decay + 0.02);
  }
  function ratchet(n) {
    if (!actx) return;
    const now = actx.currentTime;
    const count = Math.min(4, Math.max(1, Math.round(n)));
    for (let k = 0; k < count; k++) {
      const t = Math.max(now + k * 0.022, lastClick + 0.018); lastClick = t;
      noise(t, "bandpass", 3400 + Math.random() * 500, 5, 0.09, 0.014);
      tone(t, "triangle", 2650, 2650, 0.018, 0.02);
    }
  }
  function clunk() {
    if (!actx) return;
    const t = actx.currentTime + 0.005;
    tone(t, "sine", 120, 42, 0.32, 0.26);
    noise(t, "lowpass", 900, 0.8, 0.22, 0.09);
    tone(t + 0.01, "triangle", 1240, 1236, 0.028, 0.55);
    tone(t + 0.01, "triangle", 1873, 1869, 0.016, 0.4);
  }
  function twang() {
    if (!actx) return;
    const t = actx.currentTime + 0.04;
    for (const [f, a] of [[330, 0.012], [497, 0.009], [741, 0.006]]) tone(t, "sine", f, f * 0.985, a, 1.9);
  }

  const api = {
    ready,
    setPegs(arr) { arr.forEach((v, i) => { if (i < 5) setPeg(i, v, false); }); needDraw = true; },
    pegs: () => pegVals.slice(),
    release, clamp,
    isSettled: () => (released ? sim.settled : !parkAnim),
    rodValueAt: (i) => rodValAtPhys(physX[i]),
    olsAt: (i) => fit().at(physX[i]),
    get released() { return released; },
    destroy() {
      if (dead) return;
      dead = true; cancelAnimationFrame(raf);
      if (ro) ro.disconnect(); else removeEventListener("resize", resize);
      if (actx) { try { actx.close(); } catch { /* already closed */ } }
    },
  };
  canvas.drawdown = api;          // for tests and the console; harmless to students
  raf = requestAnimationFrame(tick);
  return api;
}
