// MOVED 2026-10-28 from rooms/regression/dunes/_scratch/tide_machine/model.js, which now re-exports this file,
// so the engine instrument (shared/tide_machine.js), the prototype pages, the bench and test_model.mjs share one model.
// Tide machine model + mechanism geometry. ES module, no dependencies; shared by machine.js and test_model.mjs.
//
// Closed form (water over the bar, metres; + = above the wading line):
//   h(t) = z0 + sum over shafts of size(pulley on shaft) * cos(2*pi*t/period_h - phase)
// t = hours since cfg.epoch (UTC-naive wall clock). Empty shaft contributes 0.
//
// Mechanism: each shaft's crank pin sits at a throw of K*size px (K = GEOM.yokePxPerM), so its Scotch
// yoke moves the pulley by dy = K*size*cos(theta). The wire loops under each mounted pulley, so a pulley
// dropping by dy lengthens the wire path by 2*dy. The wire's free end winds on the small groove of a stepped
// pen drum and the pen cord hangs from the large groove, penRatio times bigger, so the pen rises by
// penRatio*2*dy. The chart is ruled at 2*K*penRatio px per metre, so the pen reads h(t) exactly. The pen has
// mechanical stops at the chart's edges (mMin, mMax): beyond them it rests on the stop.

export const GEOM = (() => {
  const chart = { x0: 730, x1: 1232, y0: 95, y1: 470, mMin: -1.5, mMax: 3.0, hoursHalf: 288 };   // +-12 days
  const pxPerM = (chart.y1 - chart.y0) / (chart.mMax - chart.mMin);
  const penRatio = 4;
  return {
    W: 1280, H: 800,
    shaftX: [230, 365, 500, 635],
    plaqueY: 92,
    driveY: 140,
    crankY: 196, crankR: 40,
    idlerY: 262, idlerR: 7,
    pulleyRestY: 345,
    pulleyDiaPerM: 34,             // pulley diameter in px per metre of swing (diameter proportional to size)
    pulleyMinDia: 18,              // smallest DRAWN diameter; the throw stays K*size whatever is drawn
    pxPerM,                        // chart scale
    penRatio,                      // stepped pen drum: pen travel / wire travel
    yokePxPerM: pxPerM / (2 * penRatio),   // K: crank throw per metre; the wire doubles it, the drum multiplies it
    anchorX: 152,
    cornerX: 712,
    penX: 981, penSheaveY: 68,
    chart,
    zeroY: chart.y1 - (0 - chart.mMin) * pxPerM,
  };
})();

// ---- time ----------------------------------------------------------------------------------------
export function isoToMs(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{1,2})(?::(\d{2}))?)?/.exec(String(iso).trim());
  if (!m) throw new Error('bad date: ' + iso);
  return Date.UTC(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0));
}
export function isoToHours(iso, cfg) { return (isoToMs(iso) - isoToMs(cfg.epoch)) / 3.6e6; }
export function hoursToDate(t, cfg) {
  const d = new Date(isoToMs(cfg.epoch) + Math.round(t * 60) * 60000);
  return { y: d.getUTCFullYear(), mo: d.getUTCMonth() + 1, d: d.getUTCDate(), h: d.getUTCHours(), mi: d.getUTCMinutes() };
}
export function hoursToIso(t, cfg) {
  const p = hoursToDate(t, cfg), z = (n) => String(n).padStart(2, '0');
  return `${p.y}-${z(p.mo)}-${z(p.d)}T${z(p.h)}:${z(p.mi)}`;
}
export function hourOfDay(t, cfg) {
  const off = ((isoToMs(cfg.epoch) / 3.6e6) % 24 + 24) % 24;     // epoch is midnight -> 0
  return (((t + off) % 24) + 24) % 24;
}
export function dateToHours(y, mo, d, cfg) { return (Date.UTC(y, mo - 1, d) - isoToMs(cfg.epoch)) / 3.6e6; }
export const dayOfWeek = (t, cfg) => new Date(isoToMs(cfg.epoch) + Math.round(t * 60) * 60000).getUTCDay();   // 0 = Sunday

// ---- closed form -----------------------------------------------------------------------------------
export function pulleySize(cfg, pid) {
  if (!pid) return 0;
  const p = cfg.pulleys.find((q) => q.id === pid);
  if (!p) throw new Error('unknown pulley ' + pid);
  return p.size;
}
export function shaftAngle(shaft, t) { return 2 * Math.PI * t / shaft.period_h - shaft.phase; }
export function level(t, arrangement, cfg) {
  let s = cfg.z0;
  for (const sh of cfg.shafts) {
    const pid = arrangement[sh.id];
    if (pid) s += pulleySize(cfg, pid) * Math.cos(shaftAngle(sh, t));
  }
  return s;
}

// ---- the haul ----------------------------------------------------------------------------------------
// The bar is dry at hour t when h(t) < 0. Everything here samples whole hours since the epoch, as the escape
// set was designed (final_v5.py). A haul leaving at hour t0 needs the 72 samples t0 .. t0+71 dry.
export const haulHours = (cfg) => 24 * cfg.haul_days;
export const waterRunsOut = (cfg) => isoToHours(cfg.today, cfg) + 24 * cfg.water_days;

// Dry stretches overlapping [fromT, toT): [{ start, end }], start = first dry hour, end = first wet hour after it.
export function dryStretches(cfg, arrangement, fromT, toT) {
  const out = [], dry = (t) => level(t, arrangement, cfg) < 0;
  let t = Math.ceil(fromT - 1e-9), s = null;
  if (dry(t)) { s = t; while (dry(s - 1) && s > fromT - 24 * 366) s--; }
  for (; t < toT || (s !== null && t < toT + 24 * 366); t++) {           // a stretch open at toT runs to its end
    if (dry(t)) { if (s === null) s = t; } else if (s !== null) { out.push({ start: s, end: t }); s = null; }
  }
  return out;
}
// The first stretch of at least haul_days that starts before the water runs out, or null.
export function haulStretch(cfg, arrangement, fromT = isoToHours(cfg.today, cfg)) {
  return dryStretches(cfg, arrangement, fromT, waterRunsOut(cfg)).find((s) => s.end - s.start >= haulHours(cfg)) || null;
}

// Leaving at hour t0: how many hours the bar stays dry (capped at the haul), when the water comes back, and how
// deep it gets over the haul (overall, and from the moment it floods).
export function haulFrom(cfg, arrangement, t0) {
  const H = haulHours(cfg);
  let dryHours = 0;
  while (dryHours < H && level(t0 + dryHours, arrangement, cfg) < 0) dryHours++;
  let max = -Infinity, maxAfter = -Infinity;
  for (let k = 0; k < H; k++) {
    const h = level(t0 + k, arrangement, cfg);
    max = Math.max(max, h); if (k >= dryHours) maxAfter = Math.max(maxAfter, h);
  }
  return { t0, ok: dryHours >= H, dryHours, floodT: dryHours < H ? t0 + dryHours : null, max, maxAfter };
}
// A departure DATE (no hour): the best hour that day from today on, i.e. the one with the longest dry run (the
// earliest on a tie). Returns null for a day already gone.
export function departOn(cfg, arrangement, y, mo, d) {
  const today = isoToHours(cfg.today, cfg), d0 = dateToHours(y, mo, d, cfg);
  let best = null;
  for (let hr = 0; hr < 24; hr++) {
    if (d0 + hr < today) continue;
    const r = haulFrom(cfg, arrangement, d0 + hr);
    if (!best || r.dryHours > best.dryHours) best = r;
  }
  return best;
}
// Departure dates (as 'YYYY-MM-DD') from today up to the day the water runs out that leave a full dry haul.
export function acceptedDates(cfg, arrangement) {
  const out = [], today = isoToHours(cfg.today, cfg), last = hoursToDate(waterRunsOut(cfg), cfg);
  for (let t = today - hourOfDay(today, cfg); ; t += 24) {
    const p = hoursToDate(t, cfg);
    if (p.y * 1e4 + p.mo * 100 + p.d > last.y * 1e4 + last.mo * 100 + last.d) break;
    if (departOn(cfg, arrangement, p.y, p.mo, p.d)?.ok) out.push(hoursToIso(t, cfg).slice(0, 10));
  }
  return out;
}

// Turning points of one shaft on its own (exact): kind 'min' (its cosine at -1) or 'max', in [fromT, toT).
// The moon shaft's minima are the almanac's dark moons and its maxima the full moons.
export function shaftTurns(cfg, shaftId, kind, fromT, toT) {
  const sh = cfg.shafts.find((s) => s.id === shaftId), off = kind === 'min' ? Math.PI : 0, out = [];
  const k0 = Math.ceil(((2 * Math.PI * fromT / sh.period_h - sh.phase) - off) / (2 * Math.PI));
  for (let k = k0; ; k++) {
    const t = (sh.phase + off + 2 * Math.PI * k) * sh.period_h / (2 * Math.PI);
    if (t >= toT) break;
    if (t >= fromT) out.push(t);
  }
  return out;
}

// ---- mechanism geometry ----------------------------------------------------------------------------
// opts exist only so the test can build deliberately broken machines:
//   flipShaft: id      -> that shaft's yoke is pinned 180 degrees out (sign flip)
//   sizeFn: s => ...   -> throw computed from a different function of pulley size
//   singleRun: id      -> wire on that shaft runs down to the pulley but not back up (no doubling)
// Drawn radius only: it cancels out of the wire's length change, so a minimum drawn size keeps the machine honest.
export function pulleyRadius(size, geom = GEOM) { return Math.max(size * geom.pulleyDiaPerM, geom.pulleyMinDia || 0) / 2; }
// Stepped pen drum: the wire winds on the small groove (radius idlerR); the pen cord drops from the large
// groove at x = penX.
export function penDrum(geom = GEOM) {
  const R = geom.idlerR * geom.penRatio;
  return { cx: geom.penX - R, cy: geom.penSheaveY, R, r: geom.idlerR };
}

function wireLength(cfg, arrangement, dys, geom, opts) {
  const ri = geom.idlerR, yTop = geom.idlerY - ri;
  const pts = [[geom.anchorX, yTop]];
  const arc = (cx, cy, r, a0, a1, n = 8) => { for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } };
  let L = 0, x = geom.anchorX;
  const idlers = [];
  // L is accumulated analytically segment by segment; pts is the same path sampled for drawing.
  cfg.shafts.forEach((sh, i) => {
    const pid = arrangement[sh.id];
    if (!pid) return;                                         // empty shaft: wire runs straight over
    const sx = geom.shaftX[i], r = pulleyRadius(pulleySize(cfg, pid), geom);
    const cy = geom.pulleyRestY + dys[i];
    const xl = sx - r, xr = sx + r;
    L += (xl - ri) - x;                                       // top run to the left guide sheave
    L += Math.PI * ri / 2;                                    // over it
    L += cy - geom.idlerY;                                    // down to the pulley
    L += Math.PI * r;                                         // under the pulley
    L += opts.singleRun === sh.id ? (geom.pulleyRestY - geom.idlerY) : (cy - geom.idlerY);   // back up
    L += Math.PI * ri / 2;                                    // over the right guide sheave
    idlers.push([xl - ri, geom.idlerY], [xr + ri, geom.idlerY]);
    arc(xl - ri, geom.idlerY, ri, -Math.PI / 2, 0, 4);       // over the left sheave, ends at (xl, idlerY)
    arc(sx, cy, r, Math.PI, 0, 16);                           // under the pulley (canvas y is down)
    arc(xr + ri, geom.idlerY, ri, Math.PI, Math.PI * 1.5, 4); // up and over the right sheave
    x = xr + ri;
  });
  const hubX = penDrum(geom).cx;
  L += geom.cornerX - x;                                      // to the corner sheave
  L += yTop - (geom.penSheaveY - ri);                         // up the post
  L += hubX - geom.cornerX;                                   // across to the top of the pen drum's small groove
  pts.push([geom.cornerX, yTop], [geom.cornerX, geom.penSheaveY - ri], [hubX, geom.penSheaveY - ri]);
  return { L, pts, idlers };
}

// Full mechanism state at time t. penY is where the pen nib is drawn (penYFree: where it would be without the
// stops); h is the closed-form sum that the yokes are driven by (same components), so level() and the pen come
// from one code path.
export function mechanism(t, arrangement, cfg, geom = GEOM, opts = {}) {
  const K = geom.yokePxPerM, sizeFn = opts.sizeFn || ((s) => s);
  const yokes = cfg.shafts.map((sh, i) => {
    const pid = arrangement[sh.id] || null;
    const size = pid ? pulleySize(cfg, pid) : 0;
    const theta = shaftAngle(sh, t) + (opts.flipShaft === sh.id ? Math.PI : 0);
    const throwPx = K * sizeFn(size);
    return { id: sh.id, pid, size, theta, throwPx, dy: throwPx * Math.cos(theta), x: geom.shaftX[i],
             r: pulleyRadius(size, geom) };
  });
  const dys = yokes.map((y) => y.dy);
  const now = wireLength(cfg, arrangement, dys, geom, opts);
  const rest = wireLength(cfg, arrangement, dys.map(() => 0), geom, opts);   // datum screw, reset on refit
  const penRestY = geom.zeroY - cfg.z0 * geom.pxPerM;
  const penYFree = penRestY - geom.penRatio * (now.L - rest.L);
  const penY = Math.min(geom.chart.y1, Math.max(geom.chart.y0, penYFree));   // the stops
  let h = cfg.z0;
  for (const y of yokes) h += y.dy / K;                    // = sum size*cos(theta) for an honest machine
  return { yokes, wire: now.pts, idlers: now.idlers, penY, penYFree, stopped: penY !== penYFree, h,
           dL: now.L - rest.L, dLdrawn: polylineLength(now.pts) - polylineLength(rest.pts) };
}

export function polylineLength(pts) {
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return L;
}
export function chartLevel(penY, geom = GEOM) { return (geom.zeroY - penY) / geom.pxPerM; }
export function levelToY(h, geom = GEOM) { return geom.zeroY - h * geom.pxPerM; }
// What the pen can show: h held at the stops.
export function clampLevel(h, geom = GEOM) { return Math.min(geom.chart.mMax, Math.max(geom.chart.mMin, h)); }
