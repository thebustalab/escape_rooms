// The Variance Meter — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"variance_meter"`), built
// 2026-11-01 for anova/cellars from the v2 prototype (rooms/anova/cellars/_scratch/variance_meter/).
//
// A building's utility board over eight rooms. Each rail shows one room's load (amperes on the electrical
// switchboard, gallons an hour on the water board), fixed by the world: the player does not set loads.
// Under each rail a two-way room switch puts the room in the left or the right group. Three meters read the
// grouping: BETWEEN (each group's average from the whole building's, counted once per room), WITHIN (each
// room from its own group's average) and SHARE EXPLAINED = between / (between + within), with a red line
// engraved at the scenario's mark. The fiction: each circuit drives a current proportional to its distance
// from an average, a resistor dissipates I^2 R, so a wattmeter adds up squared distances (shared/variance_math.js,
// tested against R's aov()). It is READ, never graded: it holds no answer and never logs or gates anything.
//
// The board is code-drawn on a 1600x900 logical canvas. `art.board`, when given, is drawn as the backdrop and
// the geometry's regions place the parts over it; without it a plain panel is drawn (the prototype look).
//
//   const m = mountVarianceMeter(hostEl, { geometry, config, art?, pegs?, onPegs?(switches), sound?, debug?,
//                                          params: { utility: "amps"|"gallons", powered?: bool } });
//   config = rooms/anova/cellars/data/switchboard.json: { mark, rooms:[{name, amps, gallons, wing, ...}] }
//   geometry (all optional): { imageW, imageH, title, unit, vMax, fullScale, defaultBy, rails:{x0,x1,top,bot},
//                              switchY, dials:[{cx,cy,r}x3] }
//   m.setSwitches([bool x8]); m.switches(); m.measure(); m.isSettled(); m.ready (Promise); m.destroy();
//   canvas.varianceMeter exposes the same API for tests.
import { measure } from "./variance_math.js?v=153";

const DEFAULTS = {
  amps:    { title: "ELECTRICAL SWITCHBOARD", unit: "AMPERES", vMax: 12, fullScale: 25 },
  gallons: { title: "WATER BOARD", unit: "GALLONS AN HOUR", vMax: 60, fullScale: 1500 },
};
const COL = ["#d9a441", "#6fb0c9"];             // left group (switch up), right group (switch down)
const RED = "#b3261e";

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});

export function mountVarianceMeter(host, opts = {}) {
  const P = opts.params || {};
  const utility = P.utility === "gallons" ? "gallons" : "amps";
  const powered = P.powered !== false;
  const G = Object.assign({ imageW: 1600, imageH: 900 }, DEFAULTS[utility], opts.geometry || {});
  const W = G.imageW, H = G.imageH;
  const rooms = (opts.config && opts.config.rooms) || [];
  const MARK = (opts.config && opts.config.mark) || 0.35;
  const N = rooms.length;
  const loads = rooms.map(r => +r[utility]);
  const RAILS = Object.assign({ x0: 130, x1: 1470, top: 470, bot: 730 }, G.rails || {});
  const SWITCH_Y = G.switchY || 800;
  const DIALS = G.dials || [{ cx: 300, cy: 300, r: 170 }, { cx: 800, cy: 300, r: 170 }, { cx: 1300, cy: 300, r: 170 }];
  const defaultBy = G.defaultBy || "wing";
  const firstVal = rooms.length ? rooms[0][defaultBy] : null;
  const printed = rooms.map(r => r[defaultBy] !== firstVal);       // the board's printed default wiring
  let sw = Array.isArray(opts.pegs) && opts.pegs.length === N ? opts.pegs.map(Boolean) : printed.slice();

  host.style.position = "relative";
  const cv = document.createElement("canvas");
  cv.style.cssText = "display:block;width:100%;height:auto;touch-action:manipulation;cursor:pointer";
  cv.setAttribute("aria-label", G.title + ": eight room switches and three meters");
  host.appendChild(cv);
  const ctx = cv.getContext("2d");
  let scale = 1, raf = 0, dead = false, audio = null;

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(320, host.clientWidth || 800);
    scale = w / W;
    cv.width = Math.round(W * scale * dpr); cv.height = Math.round(H * scale * dpr);
    cv.style.height = (H * scale) + "px";
    ctx.setTransform(scale * dpr, 0, 0, scale * dpr, 0, 0);
  }
  const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
  if (ro) ro.observe(host); resize();

  let backdrop = null;
  const ready = loadImg((opts.art || {}).board).then(im => { backdrop = im; });

  const railX = i => RAILS.x0 + (N > 1 ? i * (RAILS.x1 - RAILS.x0) / (N - 1) : 0);
  const yPix = v => RAILS.bot - Math.max(0, Math.min(1, v / G.vMax)) * (RAILS.bot - RAILS.top);
  const groups = () => sw.map(b => (b ? 1 : 0));
  const now = () => measure(loads, groups());

  const needles = [0, 0, 0].map(() => ({ a: 0, v: 0 }));
  const targets = m => powered ? [m.between / G.fullScale, m.within / G.fullScale, m.share] : [0, 0, 0];
  function step(dt, m) {
    const t = targets(m);
    needles.forEach((nd, k) => {
      for (let s = 0; s < 4; s++) {
        nd.v += (40 * (t[k] - nd.a) - 7 * nd.v) * dt / 4; nd.a += nd.v * dt / 4;
        nd.a = Math.max(-0.02, Math.min(1.04, nd.a));
      }
    });
  }
  const settled = () => { const t = targets(now()); return needles.every((nd, k) => Math.abs(nd.a - t[k]) < 0.004 && Math.abs(nd.v) < 0.02); };

  function click() {
    if (opts.sound === false) return;
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      const o = audio.createOscillator(), g = audio.createGain(), t = audio.currentTime;
      o.type = "square"; o.frequency.setValueAtTime(190, t); o.frequency.exponentialRampToValueAtTime(70, t + 0.05);
      g.gain.setValueAtTime(0.12, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.07);
      o.connect(g).connect(audio.destination); o.start(t); o.stop(t + 0.08);
    } catch (e) { /* no audio: the switch still flips */ }
  }

  function engrave(text, x, y, font, align = "center", fill = "#2a1d12") {
    ctx.font = font; ctx.textAlign = align;
    ctx.fillStyle = "rgba(255,238,196,0.35)"; ctx.fillText(text, x + 1, y + 1);
    ctx.fillStyle = fill; ctx.fillText(text, x, y);
  }

  function dial(d, frac, title, sub, mark) {
    const { cx, cy, r } = d;
    ctx.save();
    ctx.fillStyle = "#2a1d12"; ctx.beginPath(); ctx.arc(cx, cy, r + 22, Math.PI, 0); ctx.lineTo(cx + r + 22, cy + 34);
    ctx.lineTo(cx - r - 22, cy + 34); ctx.closePath(); ctx.fill(); ctx.strokeStyle = "#b08a4a"; ctx.lineWidth = 4; ctx.stroke();
    ctx.fillStyle = powered ? "#efe3c4" : "#7d7461"; ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, 0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = "#2a1d12"; ctx.lineWidth = 2;
    for (let t = 0; t <= 20; t++) {
      const a = Math.PI + Math.PI * t / 20, r1 = r - (t % 10 === 0 ? 26 : t % 2 === 0 ? 16 : 9);
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
      ctx.lineTo(cx + Math.cos(a) * (r - 4), cy + Math.sin(a) * (r - 4)); ctx.stroke();
    }
    if (mark != null) {                                    // the engraved red line
      const a = Math.PI + Math.PI * mark;
      ctx.strokeStyle = RED; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * (r * 0.55), cy + Math.sin(a) * (r * 0.55));
      ctx.lineTo(cx + Math.cos(a) * (r - 2), cy + Math.sin(a) * (r - 2)); ctx.stroke();
    }
    engrave(title, cx, cy - r * 0.45, "bold 21px Georgia");
    engrave(sub, cx, cy - r * 0.45 + 22, "italic 15px Georgia");
    const a = Math.PI + Math.PI * Math.max(0, Math.min(1, frac));
    ctx.strokeStyle = "#1a1a1a"; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * (r - 10), cy + Math.sin(a) * (r - 10)); ctx.stroke();
    ctx.fillStyle = "#b08a4a"; ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 2 * Math.PI); ctx.fill();
    ctx.restore();
  }

  function lamp(x, y, r, colour, glow) {
    const g = powered ? Math.max(0, Math.min(1, glow)) : 0;
    if (g > 0.02) {
      const grd = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
      grd.addColorStop(0, colour + "aa"); grd.addColorStop(1, colour + "00");
      ctx.fillStyle = grd; ctx.beginPath(); ctx.arc(x, y, r * 3, 0, 2 * Math.PI); ctx.fill();
    }
    ctx.fillStyle = g > 0.02 ? colour : "#3b3128"; ctx.strokeStyle = "#8a6d3b"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
  }

  function draw(m) {
    if (backdrop) ctx.drawImage(backdrop, 0, 0, W, H);
    else {
      ctx.fillStyle = "#3a2716"; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 40; i++) { ctx.fillStyle = `rgba(0,0,0,${0.03 + (i % 3) * 0.02})`; ctx.fillRect(0, i * 23, W, 11); }
      engrave(G.title, W / 2, 50, "bold 30px Georgia", "center", "#d8c79f");
    }
    dial(DIALS[0], needles[0].a, "BETWEEN", "each group's average from the whole");
    dial(DIALS[1], needles[1].a, "WITHIN", "each room from its group's average");
    dial(DIALS[2], needles[2].a, "SHARE EXPLAINED", "between ÷ (between + within)", MARK);
    if (!powered) engrave("The board is dead: no current reaches the meters.", W / 2, 432, "italic 20px Georgia", "center", "#cbb68a");

    engrave(G.unit, RAILS.x0 - 70, RAILS.top - 24, "bold 15px Georgia", "left", "#cbb68a");
    if (powered) {                                         // the whole building's average
      const gy = yPix(m.grand);
      ctx.strokeStyle = "rgba(255,240,200,0.6)"; ctx.lineWidth = 1.5; ctx.setLineDash([2, 6]);
      ctx.beginPath(); ctx.moveTo(RAILS.x0 - 50, gy); ctx.lineTo(RAILS.x1 + 50, gy); ctx.stroke(); ctx.setLineDash([]);
    }
    for (let i = 0; i < N; i++) {
      const x = railX(i), g = sw[i] ? 1 : 0;
      ctx.strokeStyle = "#6e5634"; ctx.lineWidth = 8;
      ctx.beginPath(); ctx.moveTo(x, RAILS.top); ctx.lineTo(x, RAILS.bot); ctx.stroke();
      ctx.strokeStyle = "#b08a4a"; ctx.lineWidth = 1;
      for (let t = 0; t <= 6; t++) { const y = RAILS.bot - t * (RAILS.bot - RAILS.top) / 6;
        ctx.beginPath(); ctx.moveTo(x - 11, y); ctx.lineTo(x + 11, y); ctx.stroke(); }
      const ky = yPix(loads[i]);
      if (powered) {                                       // this room's group average, and its distance from it
        const gy = yPix(m.mean.get(g));
        ctx.strokeStyle = COL[g]; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(x - 30, gy); ctx.lineTo(x + 30, gy); ctx.stroke();
        ctx.strokeStyle = "rgba(255,190,90,0.85)"; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(x + 22, ky); ctx.lineTo(x + 22, gy); ctx.stroke();
      }
      ctx.fillStyle = "#c9a25a"; ctx.strokeStyle = "#4a3418"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x - 18, ky - 9, 36, 18, 5); ctx.fill(); ctx.stroke();
      engrave(rooms[i].name, x, RAILS.bot + 30, "bold 16px Georgia", "center", "#d8c79f");
      // the room switch: lever up = left group, down = right group
      const sy = SWITCH_Y;
      ctx.fillStyle = "#2a1d12"; ctx.strokeStyle = "#b08a4a"; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.roundRect(x - 26, sy - 34, 52, 68, 8); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = "#c9a25a"; ctx.lineWidth = 9; ctx.lineCap = "round";
      ctx.beginPath(); ctx.moveTo(x, sy); ctx.lineTo(x, sy + (g ? 24 : -24)); ctx.stroke(); ctx.lineCap = "butt";
      ctx.fillStyle = "#4a3418"; ctx.beginPath(); ctx.arc(x, sy, 7, 0, 2 * Math.PI); ctx.fill();
      lamp(x + 42, sy + (g ? 18 : -18), 7, COL[g], 1);
    }
    if (opts.debug) {
      ctx.fillStyle = "#fff"; ctx.font = "16px monospace"; ctx.textAlign = "left";
      ctx.fillText(`between ${m.between.toFixed(3)}  within ${m.within.toFixed(3)}  share ${(100 * m.share).toFixed(1)}%`, 20, H - 12);
    }
  }

  function hitSwitch(e) {
    const r = cv.getBoundingClientRect();
    const x = (e.clientX - r.left) * W / r.width, y = (e.clientY - r.top) * H / r.height;
    if (Math.abs(y - SWITCH_Y) > 50) return -1;
    for (let i = 0; i < N; i++) if (Math.abs(x - railX(i)) < 40) return i;
    return -1;
  }
  function onDown(e) {
    const i = hitSwitch(e);
    if (i < 0) return;
    sw[i] = !sw[i]; click();
    if (opts.onPegs) opts.onPegs(sw.slice());
  }
  cv.addEventListener("pointerdown", onDown);

  let last = performance.now();
  function frame(t) {
    if (dead) return;
    const dt = Math.min(0.033, (t - last) / 1000); last = t;
    const m = now(); step(dt, m); draw(m);
    raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);

  const api = {
    ready,
    setSwitches(a) { sw = a.map(Boolean); if (opts.onPegs) opts.onPegs(sw.slice()); },
    switches: () => sw.slice(),
    measure: now,
    isSettled: settled,
    powered,
    destroy() {
      dead = true; cancelAnimationFrame(raf); if (ro) ro.disconnect();
      cv.removeEventListener("pointerdown", onDown);
      if (audio) audio.close().catch(() => {});
      cv.remove();
    },
  };
  cv.varianceMeter = api;
  return api;
}
