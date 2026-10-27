// The PCA plate ("coconuts and the stick / the mat") — an engine INSTRUMENT (hotspot `type:"instrument"`,
// `kind:"pca_plate"`). First built 2026-10-20 (3-D only); reworked 2026-10-26 into a 2-D / 3-D teaching board.
//
// 2-D mode (the default): two scaled measurements put each sample (a coconut) on a flat frame; a stick passes
// through the cloud. The player turns the stick (drag in the frame); every coconut drops onto it. Three plots
// in a row read the stick live: SCORES (a number line: where each coconut landed), ORDINATION (each
// measurement's loading, an arrow along the same line) and SCREE (share of spread along the stick and across
// it; dashed = the best possible). A board shows the arithmetic for one coconut: its Dim_1 score IS each
// (scaled) value times that measurement's loading, added up.
// 3-D mode (the toggle): the third measurement grows out of the frame, the stick becomes a woven mat, and the
// same three plots become their two-axis forms (Dim_1 vs Dim_2 scores, loading arrows in the plane, three
// scree bars). "Find the widest" swings the stick/mat to the PCA answer, where the labels become Dim_1/Dim_2.
// A scaling toggle shows the unscaled (centred only) PCA, where the measurement with the biggest numbers wins.
// READ, never graded: no notebook, no gate, no answer.
//
// The arithmetic matches runMatrixAnalysis(analysis = "pca"): scale() (n − 1 sd), then FactoMineR::PCA with
// scale.unit = FALSE, whose ind$coord is the centred (scaled) data times the unit eigenvectors. The ordination
// arrows here are those unit loadings (the weights in the sum); FactoMineR's var$coord stretches each Dim by
// sqrt(eigenvalue), so R's pca_ord arrows point the same way along each Dim but differ in length.
//
// All drawing is in IMAGE coordinates (the backdrop's pixels); one letterbox transform maps them to the
// canvas, as in drawdown.js. Geometry (from the hotspot's `geometry` JSON):
//   imageW, imageH                 backdrop size
//   frame, sum, scores, ord, scree {x,y,w,h} regions: the coconut frame, the arithmetic board, the three plots
//   data                           CSV path relative to play.html
//   axes [x, y, z]                 three numeric columns (across, up, depth); 2-D mode uses the first two
//   groupColumn, labelColumn       colour key and hover name columns
//   colours {group: "#hex"}        groups to keep (others are dropped) and their tints
// Art (hotspot `art`): board (optional: without it every region is drawn as a plain card), coconut (keyed
// sprite), weave (tileable texture for the 3-D mat).
//
//   const plate = mountPcaPlate(hostEl, { geometry, art, pegs?, onPegs?(state), debug? });
//   plate.setMode(2|3); plate.setScaled(bool); plate.findWidest(); plate.flatten(on); plate.randomTilt();
//   plate.select(i); plate.dim1Sum(i?); plate.keptPercent(); plate.bestPercent(); plate.atBest();
//   plate.axesAreDims(); plate.isSettled(); plate.ready (Promise); plate.destroy();

// ---------- small linear algebra ----------
const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const scale = (a, s) => [a[0]*s, a[1]*s, a[2]*s];
const sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
const norm = a => scale(a, 1 / Math.hypot(...a));

function jacobiEigen(A) {               // symmetric 3x3 -> {values, vectors (columns)}
  const a = A.map(r => r.slice()), V = [[1,0,0],[0,1,0],[0,0,1]];
  for (let sweep = 0; sweep < 50; sweep++) {
    let off = Math.abs(a[0][1]) + Math.abs(a[0][2]) + Math.abs(a[1][2]);
    if (off < 1e-12) break;
    for (const [p, q] of [[0,1],[0,2],[1,2]]) {
      if (Math.abs(a[p][q]) < 1e-15) continue;
      const th = 0.5 * Math.atan2(2 * a[p][q], a[q][q] - a[p][p]);
      const c = Math.cos(th), s = Math.sin(th);
      for (let k = 0; k < 3; k++) { const akp = a[k][p], akq = a[k][q]; a[k][p] = c*akp - s*akq; a[k][q] = s*akp + c*akq; }
      for (let k = 0; k < 3; k++) { const apk = a[p][k], aqk = a[q][k]; a[p][k] = c*apk - s*aqk; a[q][k] = s*apk + c*aqk; }
      for (let k = 0; k < 3; k++) { const vkp = V[k][p], vkq = V[k][q]; V[k][p] = c*vkp - s*vkq; V[k][q] = s*vkp + c*vkq; }
    }
  }
  const idx = [0, 1, 2].sort((i, j) => a[j][j] - a[i][i]);
  return { values: idx.map(i => a[i][i]), vectors: idx.map(i => [V[0][i], V[1][i], V[2][i]]) };
}

// quaternions [w, x, y, z]
const qmul = (a, b) => [
  a[0]*b[0] - a[1]*b[1] - a[2]*b[2] - a[3]*b[3],
  a[0]*b[1] + a[1]*b[0] + a[2]*b[3] - a[3]*b[2],
  a[0]*b[2] - a[1]*b[3] + a[2]*b[0] + a[3]*b[1],
  a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + a[3]*b[0]];
const qaxis = (ax, ang) => { const s = Math.sin(ang / 2); return [Math.cos(ang / 2), ax[0]*s, ax[1]*s, ax[2]*s]; };
const qnorm = q => { const n = Math.hypot(...q); return q.map(v => v / n); };
function qrot(q, v) {
  const p = qmul(qmul(q, [0, ...v]), [q[0], -q[1], -q[2], -q[3]]);
  return [p[1], p[2], p[3]];
}
function qslerp(a, b, t) {
  let d = a[0]*b[0] + a[1]*b[1] + a[2]*b[2] + a[3]*b[3];
  if (d < 0) { b = b.map(v => -v); d = -d; }
  if (d > 0.9995) return qnorm(a.map((v, i) => v + t * (b[i] - v)));
  const th = Math.acos(d), s = Math.sin(th);
  return a.map((v, i) => (Math.sin((1 - t) * th) * v + Math.sin(t * th) * b[i]) / s);
}
function qfromBasis(u, v, n) {          // rotation taking ex,ey,ez to u,v,n (columns)
  const m = [[u[0], v[0], n[0]], [u[1], v[1], n[1]], [u[2], v[2], n[2]]];
  const tr = m[0][0] + m[1][1] + m[2][2];
  let q;
  if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; q = [s/4, (m[2][1]-m[1][2])/s, (m[0][2]-m[2][0])/s, (m[1][0]-m[0][1])/s]; }
  else if (m[0][0] > m[1][1] && m[0][0] > m[2][2]) { const s = Math.sqrt(1 + m[0][0] - m[1][1] - m[2][2]) * 2; q = [(m[2][1]-m[1][2])/s, s/4, (m[0][1]+m[1][0])/s, (m[0][2]+m[2][0])/s]; }
  else if (m[1][1] > m[2][2]) { const s = Math.sqrt(1 + m[1][1] - m[0][0] - m[2][2]) * 2; q = [(m[0][2]-m[2][0])/s, (m[0][1]+m[1][0])/s, s/4, (m[1][2]+m[2][1])/s]; }
  else { const s = Math.sqrt(1 + m[2][2] - m[0][0] - m[1][1]) * 2; q = [(m[1][0]-m[0][1])/s, (m[0][2]+m[2][0])/s, (m[1][2]+m[2][1])/s, s/4]; }
  return qnorm(q);
}
const wrapAngle = (a) => Math.atan2(Math.sin(a), Math.cos(a));

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/), unq = (s) => s.replace(/^"|"$/g, "");
  const head = lines[0].split(",").map(unq);
  return lines.slice(1).map((l) => {
    const f = l.split(",").map(unq), o = {};
    head.forEach((h, i) => { o[h] = f[i]; });
    return o;
  });
}

const CAM3 = { yaw: -0.6, pitch: 0.3 };      // the 3-D view the toggle swings to

export function mountPcaPlate(host, opts = {}) {
  const G = opts.geometry;
  for (const k of ["frame", "sum", "scores", "ord", "scree"]) if (!G || !G[k]) throw new Error("pca_plate: geometry needs " + k);
  const AXES = G.axes, COLOURS = G.colours || {};
  const artPaths = opts.art || {};

  // ---- DOM: a toolbar above the letterboxed canvas ----
  const wrap = document.createElement("div"); wrap.className = "pcaplate";
  const bar = document.createElement("div"); bar.className = "pcaplatebar";
  const mkBtn = (txt) => { const b = document.createElement("button"); b.type = "button"; b.textContent = txt; bar.appendChild(b); return b; };
  const btnMode = mkBtn("Switch to 3D"), btnScale = mkBtn("Scaling: on"), btnWide = mkBtn("Find the widest"),
        btnFlat = mkBtn("Drop onto the stick"), btnRand = mkBtn("Random turn");
  btnMode.dataset.role = "mode"; btnScale.dataset.role = "scale"; btnWide.dataset.role = "widest";
  btnFlat.dataset.role = "flatten"; btnRand.dataset.role = "random";
  const canvas = document.createElement("canvas");
  canvas.className = "pcaplatecanvas";
  canvas.style.aspectRatio = `${G.imageW} / ${G.imageH}`;
  const tip = document.createElement("div"); tip.className = "pcaplatetip";
  const stage = document.createElement("div"); stage.className = "pcaplatestage";
  stage.append(canvas, tip);
  wrap.append(bar, stage);
  host.appendChild(wrap);
  const g = canvas.getContext("2d");

  const saved = opts.pegs || {};
  const S = {
    raw: [], groups: [], names: [], mean: [0, 0, 0], sd: [1, 1, 1], pts: [], box: 1, eig: { 2: null, 3: null },
    mode: saved.mode === 3 ? 3 : 2, scaled: saved.scaled !== false,
    theta: saved.theta ?? null, q: saved.q || null,
    yaw: saved.mode === 3 ? (saved.yaw ?? CAM3.yaw) : 0, pitch: saved.mode === 3 ? (saved.pitch ?? CAM3.pitch) : 0,
    zGrow: saved.mode === 3 ? 1 : 0, sel: saved.sel ?? null,
    flat: 0, flatTarget: 0, anim: null, camAnim: null, ready: false,
  };
  let IMG = {}, view = { S: 1, ox: 0, oy: 0, dpr: 1 }, raf = 0, dead = false;
  const remember = () => opts.onPegs && opts.onPegs({ mode: S.mode, scaled: S.scaled, theta: S.theta, q: S.q && S.q.slice(),
                                                       yaw: S.yaw, pitch: S.pitch, sel: S.sel });

  // ---- maths on the current stick / mat ----
  // Points are always 3-vectors; in 2-D mode the third coordinate is ignored (taken as 0).
  const pt = (i) => S.mode === 3 ? S.pts[i] : [S.pts[i][0], S.pts[i][1], 0];
  function basis() {                       // [u, v, n]: u = Dim_1 direction, v = Dim_2 (or across the stick)
    if (S.mode === 2) { const c = Math.cos(S.theta), s = Math.sin(S.theta); return [[c, s, 0], [-s, c, 0], [0, 0, 1]]; }
    return [qrot(S.q, [1, 0, 0]), qrot(S.q, [0, 1, 0]), qrot(S.q, [0, 0, 1])];
  }
  const E = () => S.eig[S.mode];
  function shares() {                      // % of the spread along each basis direction (2 in 2-D, 3 in 3-D)
    const B = basis().slice(0, S.mode), n = S.pts.length;
    return B.map((b) => 100 * S.pts.reduce((s, _, i) => s + dot(pt(i), b) ** 2, 0) / (n - 1) / E().total);
  }
  const keptPercent = () => { const s = shares(); return S.mode === 2 ? s[0] : s[0] + s[1]; };
  const bestPercent = () => { const e = E(); return 100 * (S.mode === 2 ? e.values[0] : e.values[0] + e.values[1]) / e.total; };
  function atBest() {
    const [u, , n] = basis(), e = E();
    if (S.mode === 2) return Math.abs(Math.abs(dot(u, e.vectors[0])) - 1) < 1e-7;
    return Math.abs(Math.abs(dot(n, cross(e.vectors[0], e.vectors[1]))) - 1) < 1e-7;
  }
  function axesAreDims() {
    if (S.mode === 2) return atBest();
    const [u, v] = basis(), e = E();
    return atBest() && Math.abs(dot(u, e.vectors[0])) > 1 - 1e-7 && Math.abs(dot(v, e.vectors[1])) > 1 - 1e-7;
  }
  // score along u for coconut i, and the worked arithmetic behind it
  function dim1Sum(i = S.sel) {
    const [u] = basis(), m = S.mode, terms = [];
    for (let j = 0; j < m; j++) {
      const value = S.raw[i][j], centred = value - S.mean[j], used = S.scaled ? centred / S.sd[j] : centred;
      terms.push({ axis: AXES[j], value, mean: S.mean[j], sd: S.sd[j], used, loading: u[j], product: used * u[j] });
    }
    return { index: i, name: S.names[i], scaled: S.scaled, terms, total: terms.reduce((s, t) => s + t.product, 0) };
  }

  function standardise() {
    const n = S.raw.length;
    S.pts = S.raw.map((r) => r.map((v, j) => (v - S.mean[j]) / (S.scaled ? S.sd[j] : 1)));
    S.box = Math.max(...S.pts.flat().map(Math.abs)) * 1.03;
    S.reach = { 2: Math.max(...S.pts.map((p) => Math.hypot(p[0], p[1]))), 3: Math.max(...S.pts.map((p) => Math.hypot(...p))) };
    for (const m of [2, 3]) {
      const P = S.pts.map((p) => m === 3 ? p : [p[0], p[1], 0]);
      const C = [0, 1, 2].map((a) => [0, 1, 2].map((b) => P.reduce((s, p) => s + p[a] * p[b], 0) / (n - 1)));
      const e = jacobiEigen(C);
      S.eig[m] = { values: e.values, vectors: e.vectors, total: e.values.slice(0, m).reduce((a, b) => a + b, 0) };
    }
    const e3 = S.eig[3];
    S.eig[3].q = qfromBasis(e3.vectors[0], e3.vectors[1], cross(e3.vectors[0], e3.vectors[1]));
  }
  function setData(rows) {
    rows = rows.filter((r) => r[G.groupColumn] in COLOURS && AXES.every((a) => Number.isFinite(+r[a])));
    S.raw = rows.map((r) => AXES.map((a) => +r[a]));
    const n = S.raw.length;
    S.mean = [0, 1, 2].map((j) => S.raw.reduce((s, r) => s + r[j], 0) / n);
    S.sd = [0, 1, 2].map((j) => Math.sqrt(S.raw.reduce((s, r) => s + (r[j] - S.mean[j]) ** 2, 0) / (n - 1)) || 1);
    S.groups = rows.map((r) => r[G.groupColumn]);
    S.names = rows.map((r) => String(r[G.labelColumn] || "").replace(/_/g, " "));
    standardise();
    if (S.sel == null || S.sel >= n) {      // default: the coconut furthest out, so its sum is worth reading
      let bi = 0, bd = -1;
      S.pts.forEach((p, i) => { const d = p[0] ** 2 + p[1] ** 2; if (d > bd) { bd = d; bi = i; } });
      S.sel = bi;
    }
  }

  // ---- art helpers ----
  const TINT = {};
  function tinted(col) {
    if (TINT[col]) return TINT[col];
    const src = IMG.coconut, c = document.createElement("canvas");
    c.width = src.width; c.height = src.height;
    const t = c.getContext("2d");
    t.drawImage(src, 0, 0);
    t.globalCompositeOperation = "source-atop"; t.globalAlpha = 0.55; t.fillStyle = col; t.fillRect(0, 0, c.width, c.height);
    return (TINT[col] = c);
  }
  function coconut(x, y, r, col, alpha = 1, picked = false) {
    g.globalAlpha = alpha;
    if (IMG.coconut) g.drawImage(tinted(col), x - r, y - r, 2 * r, 2 * r);
    else { g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
    g.strokeStyle = col; g.lineWidth = 1.5; g.beginPath(); g.arc(x, y, r * 0.98, 0, 7); g.stroke();
    if (picked) {
      g.strokeStyle = "#fff"; g.lineWidth = 3; g.beginPath(); g.arc(x, y, r + 5, 0, 7); g.stroke();
      g.strokeStyle = "#111"; g.lineWidth = 1.2; g.beginPath(); g.arc(x, y, r + 7.5, 0, 7); g.stroke();
    }
    g.globalAlpha = 1;
  }
  function text(s, x, y, { align = "left", size = 18, fill = "#2b1a08", glow = null, weight = 600, mono = false } = {}) {
    g.font = mono ? `${weight} ${size}px ui-monospace, Menlo, Consolas, monospace` : `${weight} ${size}px Georgia, serif`;
    g.textAlign = align;
    if (glow) { g.shadowColor = glow; g.shadowBlur = 5; }
    g.fillStyle = fill; g.fillText(s, x, y); g.shadowBlur = 0; g.textAlign = "left";
  }
  const label3d = (s, x, y, align = "left") => text(s, x, y, { align, size: 20, fill: "#fff2cf", glow: "#000" });
  const ink = (s, x, y, align, size, extra = {}) => text(s, x, y, { align, size, ...extra });
  const chalk = (s, x, y, align, size, extra = {}) => text(s, x, y, { align, size, fill: "#f6e7c4", glow: "rgba(0,0,0,0.8)", ...extra });
  const fmt = (v, d = 2) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
  const named = () => axesAreDims();
  const dimName = (k) => named() ? `Dim_${k + 1}` : (S.mode === 2 ? ["along the stick", "across the stick"][k] : ["mat across", "mat up", "off the mat"][k]);

  // plain cards when there is no painted board (the harness prototype, or a missing still)
  function card(R, kind) {
    if (IMG.board) {                       // a parchment wash so the plot reads against the weave
      if (kind === "koa") return;
      g.save(); g.fillStyle = "rgba(246,236,208,0.78)";
      g.beginPath(); g.roundRect ? g.roundRect(R.x, R.y, R.w, R.h, 8) : g.rect(R.x, R.y, R.w, R.h); g.fill(); g.restore();
      return;
    }
    g.save();
    g.fillStyle = kind === "koa" ? "#5b3418" : "#e9dcb6";
    g.strokeStyle = kind === "koa" ? "#2e1a0a" : "#7a5c28"; g.lineWidth = 6;
    g.beginPath(); g.roundRect ? g.roundRect(R.x, R.y, R.w, R.h, 10) : g.rect(R.x, R.y, R.w, R.h); g.fill(); g.stroke();
    g.restore();
  }

  // ---- camera ----
  const CAMD = 5.2;                        // in units of the frame's half-width (S.box), whatever the data's scale
  function camBasis() {
    const cy = Math.cos(S.yaw), sy = Math.sin(S.yaw), cp = Math.cos(S.pitch), sp = Math.sin(S.pitch);
    const fwd = [sy * cp, sp, cy * cp], right = norm(cross([0, 1, 0], fwd)), up = cross(fwd, right);
    return { right, up, fwd, pos: scale(fwd, CAMD) };
  }
  function project(p, cam) {
    const R = G.frame, q = scale(p, 1 / S.box), x = dot(q, cam.right), y = dot(q, cam.up), z = dot(q, cam.fwd);
    const k = CAMD / (CAMD - z), s = Math.min(R.w, R.h) / (2.9 + 0.75 * S.zGrow);
    return { x: R.x + R.w / 2 + x * k * s, y: R.y + R.h / 2 - y * k * s, z, k };
  }

  // ---- drawing: the frame ----
  function bamboo(a, b, w) {
    g.lineCap = "round";
    g.strokeStyle = "#3a2a12"; g.lineWidth = w + 3; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    g.strokeStyle = "#cdb06e"; g.lineWidth = w; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    g.strokeStyle = "#7a5c28"; g.lineWidth = 2;
    const L = Math.hypot(b.x - a.x, b.y - a.y) || 1, nx = -(b.y - a.y) / L * (w / 2 + 1), ny = (b.x - a.x) / L * (w / 2 + 1);
    for (const t of [0.25, 0.5, 0.75]) {
      const x = a.x + (b.x - a.x) * t, y = a.y + (b.y - a.y) * t;
      g.beginPath(); g.moveTo(x - nx, y - ny); g.lineTo(x + nx, y + ny); g.stroke();
    }
  }
  function drawMat3d(corners, alpha) {
    g.save();
    g.beginPath(); corners.forEach((c, i) => (i ? g.lineTo(c.x, c.y) : g.moveTo(c.x, c.y))); g.closePath();
    g.globalAlpha = alpha;
    if (IMG.weave && typeof DOMMatrix === "function") {
      const pat = g.createPattern(IMG.weave, "repeat"), T = IMG.weave.width * 2.5, [c0, c1, , c3] = corners;
      pat.setTransform(new DOMMatrix([(c1.x - c0.x) / T, (c1.y - c0.y) / T, (c3.x - c0.x) / T, (c3.y - c0.y) / T, c0.x, c0.y]));
      g.fillStyle = pat;
    } else g.fillStyle = "#c4a05c";
    g.fill();
    g.globalAlpha = 1; g.strokeStyle = "#5a3c14"; g.lineWidth = 4; g.stroke();
    g.strokeStyle = "#e6c98a"; g.lineWidth = 1.5; g.stroke();
    g.restore();
  }
  function stick(a, b) {
    g.lineCap = "round";
    g.strokeStyle = "#1e1206"; g.lineWidth = 11; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    g.strokeStyle = "#8a5a2b"; g.lineWidth = 7; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
  }
  function drawFrame() {
    const R = G.frame, cam = camBasis(), P = (p) => project(p, cam);
    const [u, v, nrm] = basis(), dropDir = S.mode === 2 ? v : nrm, camSide = Math.sign(dot(cam.pos, dropDir)) || 1;
    if (IMG.board) {
      const grd = g.createRadialGradient(R.x + R.w / 2, R.y + R.h / 2, R.h * 0.05, R.x + R.w / 2, R.y + R.h / 2, R.h * 0.6);
      grd.addColorStop(0, "rgba(10,14,16,0.55)"); grd.addColorStop(1, "rgba(10,14,16,0)");
      g.fillStyle = grd; g.fillRect(R.x, R.y, R.w, R.h);
    } else { g.fillStyle = "#1a2226"; g.fillRect(R.x, R.y, R.w, R.h); }
    const B = S.box, Bz = S.box * S.zGrow, PLATE = S.box * 1.1, edges = [];
    for (const a of [-B, B]) for (const b of [-B, B]) edges.push([[a, b, -Bz], [a, b, Bz]]);
    for (const a of [-B, B]) for (const z of [-Bz, Bz]) edges.push([[a, -B, z], [a, B, z]], [[-B, a, z], [B, a, z]]);
    const live = edges.filter(([a, b]) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) > 1e-6);
    live.sort((e1, e2) => (dot(e1[0], cam.fwd) + dot(e1[1], cam.fwd)) - (dot(e2[0], cam.fwd) + dot(e2[1], cam.fwd)));
    const half = Math.ceil(live.length / 2);
    live.slice(0, half).forEach(([a, b]) => bamboo(P(a), P(b), 6));
    const axLab = [];
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]].forEach((ax, i) => {
      const L = i === 2 ? Bz : B;
      if (L < 1e-6) return;
      const s = P(scale(ax, -L)), e = P(scale(ax, L));
      g.strokeStyle = "rgba(255,240,200,0.35)"; g.lineWidth = 2; g.setLineDash([8, 8]);
      g.beginPath(); g.moveTo(s.x, s.y); g.lineTo(e.x, e.y); g.stroke(); g.setLineDash([]);
      axLab.push([AXES[i] + (S.scaled ? " (scaled)" : "") + (i === 1 && S.zGrow < 0.5 ? " ↑" : " →"), i === 0 && S.zGrow < 0.5 ? { x: e.x, y: e.y + 34 } : e]);
    });
    S.framePts = [];
    const items = S.pts.map((p0, i) => {
      const p = [p0[0], p0[1], p0[2] * S.zGrow], d = dot(p, dropDir);
      const shown = sub(p, scale(dropDir, d * S.flat)), foot = sub(p, scale(dropDir, d));
      return { i, shown, foot, side: Math.sign(d) === camSide ? 1 : -1, s: P(shown) };
    });
    const drops = (list) => {
      g.strokeStyle = "rgba(255,248,225,0.55)"; g.lineWidth = 1.5;
      for (const it of list) { const a = P(it.shown), b = P(it.foot); g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); }
    };
    const nuts = (list, alpha) => list.sort((a, b) => a.s.z - b.s.z).forEach((it) => {
      const r = Math.max(3, 12 * it.s.k);
      coconut(it.s.x, it.s.y, r, COLOURS[S.groups[it.i]], alpha, it.i === S.sel);
      S.framePts[it.i] = [it.s.x, it.s.y];
    });
    const o = P([0, 0, 0]);
    if (S.mode === 3) {
      const behind = items.filter((it) => it.side < 0 && S.flat < 1), front = items.filter((it) => it.side > 0 || S.flat >= 1);
      drops(behind); nuts(behind, 0.85);
      const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => P([0, 1, 2].map((k) => (u[k] * a + v[k] * b) * PLATE)));
      drawMat3d(corners, 0.45);
      S.grab = corners;
      const ue = P(scale(u, PLATE)), ve = P(scale(v, PLATE));
      g.strokeStyle = "#3b240c"; g.lineWidth = 3;
      g.beginPath(); g.moveTo(o.x, o.y); g.lineTo(ue.x, ue.y); g.moveTo(o.x, o.y); g.lineTo(ve.x, ve.y); g.stroke();
      label3d(named() ? "Dim_1" : "mat across", ue.x + 6, ue.y); label3d(named() ? "Dim_2" : "mat up", ve.x + 6, ve.y);
      drops(front); nuts(front, 1);
    } else {
      drops(items);
      const a = P(scale(u, -PLATE * 1.25)), b = P(scale(u, PLATE * 1.25));
      stick(a, b);
      S.grab = null;
      label3d(named() ? "Dim_1" : "the stick", b.x + (b.x >= o.x ? 10 : -10), b.y - 8, b.x >= o.x ? "left" : "right");
      nuts(items, 1);
    }
    live.slice(half).forEach(([a, b]) => bamboo(P(a), P(b), 6));
    axLab.forEach(([s, e]) => label3d(s, e.x + 6, e.y - 6));
  }

  // ---- drawing: the three plots ----
  const pad = (R) => Math.max(14, R.h * 0.06);
  const plotFs = (R) => Math.round(Math.max(15, R.h * 0.062));
  function plotTitle(R, s) { ink(s, R.x + R.w / 2, R.y + pad(R) + 14, "center", Math.round(plotFs(R) * 1.25), { weight: 700 }); }
  function drawScores() {
    const R = G.scores; card(R, "weave");
    const p = pad(R), top = R.y + p + 30, cx = R.x + R.w / 2, cy = (top + R.y + R.h - p - 26) / 2;
    const span = Math.min(R.w - 2 * p - 40, R.y + R.h - p - 26 - top), s = span / (2.1 * S.reach[S.mode]), [u, v] = basis();
    const sh = shares(), fs = plotFs(R);
    plotTitle(R, "Scores");
    g.save(); g.beginPath(); g.rect(R.x, R.y, R.w, R.h); g.clip();
    g.strokeStyle = "rgba(43,26,8,0.6)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(R.x + p, cy); g.lineTo(R.x + R.w - p, cy);
    if (S.mode === 3) { g.moveTo(cx, top); g.lineTo(cx, R.y + R.h - p); }
    g.stroke();
    ink(`${dimName(0)} (${sh[0].toFixed(0)}%) →`, cx, R.y + R.h - p * 0.6, "center", fs);
    if (S.mode === 3) { g.save(); g.translate(R.x + p * 0.6 + fs * 0.4, cy); g.rotate(-Math.PI / 2); ink(`${dimName(1)} (${sh[1].toFixed(0)}%) →`, 0, 0, "center", fs); g.restore(); }
    // ticks on the number line make it a number line
    const RE = S.reach[S.mode], step = RE > 12 ? 5 : RE > 6 ? 2 : 1;
    for (let t = -Math.floor(RE / step) * step; t <= RE; t += step) {
      const x = cx + t * s; g.beginPath(); g.moveTo(x, cy - 4); g.lineTo(x, cy + 4); g.stroke();
      if (S.mode === 2) ink(String(t).replace("-", "−"), x, cy + 20, "center", Math.round(fs * 0.8), { weight: 400 });
    }
    S.scorePts = S.pts.map((_, i) => {
      const q = [S.pts[i][0], S.pts[i][1], S.mode === 3 ? S.pts[i][2] : 0];
      const jit = S.mode === 2 ? (((i * 37) % 11) / 10 - 0.5) * Math.min(28, R.h * 0.1) : 0;
      return [cx + dot(q, u) * s, S.mode === 3 ? cy - dot(q, v) * s : cy + jit];
    });
    S.scorePts.forEach(([x, y], i) => { if (i !== S.sel) coconut(x, y, 8, COLOURS[S.groups[i]], 0.95); });
    if (S.sel != null) coconut(S.scorePts[S.sel][0], S.scorePts[S.sel][1], 8, COLOURS[S.groups[S.sel]], 1, true);
    g.restore();
  }
  function arrow(x0, y0, x1, y1, col, w = 3) {
    const a = Math.atan2(y1 - y0, x1 - x0), L = Math.hypot(x1 - x0, y1 - y0), h = Math.min(14, L * 0.4);
    g.strokeStyle = col; g.fillStyle = col; g.lineWidth = w;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    if (L > 2) { g.beginPath(); g.moveTo(x1, y1); g.lineTo(x1 - h * Math.cos(a - 0.4), y1 - h * Math.sin(a - 0.4)); g.lineTo(x1 - h * Math.cos(a + 0.4), y1 - h * Math.sin(a + 0.4)); g.fill(); }
  }
  const ARROW_COLS = ["#8c1d18", "#1b4f8a", "#2f6b2a"];
  function drawOrd() {
    const R = G.ord; card(R, "weave");
    const p = pad(R), top = R.y + p + 30, cx = R.x + R.w / 2, cy = (top + R.y + R.h - p - 26) / 2;
    const L = Math.min(R.w / 2 - p - 40, (R.y + R.h - p - 26 - top) / 2 - 6), [u, v] = basis(), fs = plotFs(R);
    plotTitle(R, "Ordination (loadings)");
    g.strokeStyle = "rgba(43,26,8,0.6)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(cx - L - 8, cy); g.lineTo(cx + L + 8, cy);
    if (S.mode === 3) { g.moveTo(cx, cy - L - 8); g.lineTo(cx, cy + L + 8); }
    g.stroke();
    g.setLineDash([4, 5]); g.strokeStyle = "rgba(43,26,8,0.4)";
    if (S.mode === 3) { g.beginPath(); g.arc(cx, cy, L, 0, 7); g.stroke(); }
    else for (const e of [-1, 1]) { g.beginPath(); g.moveTo(cx + e * L, cy - 30); g.lineTo(cx + e * L, cy + 30); g.stroke(); }
    g.setLineDash([]);
    ink(dimName(0) + " →", cx, R.y + R.h - p * 0.6, "center", fs);
    if (S.mode === 3) { g.save(); g.translate(R.x + p * 0.6 + fs * 0.4, cy); g.rotate(-Math.PI / 2); ink(dimName(1) + " →", 0, 0, "center", fs); g.restore(); }
    if (S.mode === 2) { ink("−1", cx - L, cy + 46, "center", Math.round(fs * 0.8), { weight: 400 }); ink("+1", cx + L, cy + 46, "center", Math.round(fs * 0.8), { weight: 400 }); }
    for (let j = 0; j < S.mode; j++) {
      const lx = u[j], ly = S.mode === 3 ? v[j] : 0;
      const yoff = S.mode === 2 ? (j === 0 ? -14 : 14) : 0;
      const x1 = cx + lx * L, y1 = cy + yoff - ly * L;
      arrow(cx, cy + yoff, x1, y1, ARROW_COLS[j]);
      const a = Math.atan2(y1 - cy - yoff, x1 - cx);
      const tx = S.mode === 2 ? x1 + (lx >= 0 ? 8 : -8) : x1 + 12 * Math.cos(a), ty = S.mode === 2 ? y1 + 6 : y1 + 12 * Math.sin(a) + 6;
      const al = S.mode === 2 ? (lx >= 0 ? "left" : "right") : (Math.cos(a) >= 0 ? "left" : "right");
      ink(`${AXES[j]} ${fmt(lx)}`, tx, ty, al, fs, { fill: ARROW_COLS[j] });
    }
  }
  function drawScree() {
    const R = G.scree; card(R, "weave");
    const p = pad(R), top = R.y + p + 70, bot = R.y + R.h - p - 22, sh = shares(), e = E();
    const best = e.values.slice(0, S.mode).map((x) => 100 * x / e.total), fs = plotFs(R);
    plotTitle(R, "Scree");
    const kept = keptPercent();
    ink(`kept by the ${S.mode === 2 ? "stick" : "mat"}: ${kept.toFixed(1)}%${atBest() ? " ✔" : ""}  (best ${bestPercent().toFixed(1)}%)`,
        R.x + R.w / 2, R.y + p + 42, "center", Math.round(fs * 0.85), { weight: 400 });
    const x0 = R.x + p + 30, x1 = R.x + R.w - p, h = bot - top, slot = (x1 - x0) / S.mode, bw = slot * 0.5;
    g.strokeStyle = "#2b1a08"; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x0, top); g.lineTo(x0, bot); g.lineTo(x1, bot); g.stroke();
    for (const t of [0, 50, 100]) ink(t + "%", x0 - 5, bot - h * t / 100 + 5, "right", Math.round(fs * 0.7), { weight: 400 });
    sh.forEach((val, i) => {
      const xc = x0 + slot * (i + 0.5), y = bot - h * val / 100, yd = bot - h * best[i] / 100;
      g.fillStyle = "rgba(92,58,22,0.85)"; g.fillRect(xc - bw / 2, y, bw, bot - y);
      g.setLineDash([5, 3]); g.strokeStyle = "#2b1a08"; g.lineWidth = 1.5; g.strokeRect(xc - bw / 2, yd, bw, bot - yd); g.setLineDash([]);
      ink(val.toFixed(0) + "%", xc, Math.min(y, yd) - 6, "center", Math.round(fs * 0.8));
      ink(named() ? "Dim_" + (i + 1) : ["along", "across", "off"][i], xc, bot + 18, "center", Math.round(fs * 0.8));
    });
  }

  // ---- drawing: the arithmetic board ----
  function drawSum() {
    const R = G.sum; card(R, "koa");
    if (S.sel == null) return;
    const d = dim1Sum(), p = Math.max(18, R.w * 0.04), fs = Math.round(Math.min(R.h * 0.058, R.w * 0.042));
    const lh = fs * 1.55;
    let y = R.y + p + fs;
    const who = d.name ? d.name : "this coconut";
    chalk(`How ${who} gets its ${named() ? "Dim_1" : "stick"} score`, R.x + R.w / 2, y, "center", Math.round(fs * 1.05), { weight: 700 });
    y += lh * 0.95;
    chalk(S.scaled ? "scaled = (value − mean) ÷ sd" : "centred = value − mean (scaling off)", R.x + R.w / 2, y, "center", Math.round(fs * 0.75), { weight: 400 });
    y += lh * 1.15;
    const cols = [0.0, 0.26, 0.48, 0.72, 1.0].map((f) => R.x + p + f * (R.w - 2 * p));
    const head = ["", "value", S.scaled ? "scaled" : "centred", "× loading", "= part"];
    head.forEach((h, k) => chalk(h, cols[k], y, k ? "right" : "left", Math.round(fs * 0.8), { weight: 400 }));
    y += lh * 0.9;
    d.terms.forEach((t, j) => {
      chalk(t.axis, cols[0], y, "left", fs, { fill: "#ffe2b8" });
      chalk(t.value.toFixed(2), cols[1], y, "right", fs, { mono: true, weight: 500 });
      chalk(fmt(t.used), cols[2], y, "right", fs, { mono: true, weight: 500 });
      chalk("× " + fmt(t.loading), cols[3], y, "right", fs, { mono: true, weight: 500 });
      chalk("= " + fmt(t.product), cols[4], y, "right", fs, { mono: true, weight: 700 });
      g.fillStyle = ARROW_COLS[j]; g.fillRect(cols[0] - p * 0.55, y - fs * 0.7, 5, fs * 0.8);
      y += lh;
    });
    g.strokeStyle = "rgba(246,231,196,0.8)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(cols[2] - R.w * 0.05, y - lh + fs * 0.45); g.lineTo(cols[4], y - lh + fs * 0.45); g.stroke();
    const totalLine = `${named() ? "Dim_1" : "score"} = ${d.terms.map((t) => fmt(t.product)).join(" + ").replace(/\+ −/g, "− ")} = ${fmt(d.total)}`;
    let tfs = Math.round(fs * 1.05);
    g.font = `700 ${tfs}px ui-monospace, Menlo, Consolas, monospace`;
    const tw = g.measureText(totalLine).width, room = R.w - 2 * p;
    if (tw > room) tfs = Math.floor(tfs * room / tw);
    chalk(totalLine, cols[4], y + fs * 0.2, "right", tfs, { mono: true, weight: 700, fill: "#fff6dd" });
    y += lh * 1.2;
    const notes = ["Each loading is that measurement's arrow on the Ordination board,",
                   "and the score is where this coconut sits on the Scores board.",
                   S.scaled ? "Turn scaling off: the measurement with the biggest numbers takes over."
                            : "Unscaled, the measurement with the biggest numbers takes over.",
                   "Tap any coconut to see its sum."];
    notes.forEach((t, k) => chalk(t, R.x + R.w / 2, Math.min(y + fs * 0.4 + k * fs * 1.15, R.y + R.h - p - (notes.length - 1 - k) * fs * 1.15), "center", Math.round(fs * 0.68), { weight: 400 }));
  }

  function resize() {
    if (dead) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cw = Math.max(1, canvas.clientWidth), ch = Math.max(1, canvas.clientHeight);
    canvas.width = Math.round(cw * dpr); canvas.height = Math.round(ch * dpr);
    const k = Math.min(cw / G.imageW, ch / G.imageH);
    view = { dpr, k, S: k * dpr, ox: ((cw - G.imageW * k) / 2) * dpr, oy: ((ch - G.imageH * k) / 2) * dpr };
  }
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => resize()) : null;
  if (ro) ro.observe(canvas); else addEventListener("resize", resize);

  const ease = (t) => t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
  function tick() {
    if (dead) return;
    if (S.ready) {
      const now = performance.now();
      if (S.anim) {
        const t = Math.min(1, (now - S.anim.t0) / S.anim.dur), e = ease(t);
        if (S.anim.kind === "q") S.q = qslerp(S.anim.from, S.anim.to, e);
        else S.theta = S.anim.from + wrapAngle(S.anim.to - S.anim.from) * e;
        if (t >= 1) { if (S.anim.kind === "q") S.q = S.anim.to; else S.theta = S.anim.to; S.anim = null; remember(); }
      }
      if (S.camAnim) {
        const A = S.camAnim, t = Math.min(1, (now - A.t0) / A.dur), e = ease(t);
        S.yaw = A.from.yaw + (A.to.yaw - A.from.yaw) * e; S.pitch = A.from.pitch + (A.to.pitch - A.from.pitch) * e;
        S.zGrow = A.from.z + (A.to.z - A.from.z) * e;
        if (t >= 1) { S.camAnim = null; remember(); }
      }
      if (S.flat !== S.flatTarget) {
        const d = S.flatTarget - S.flat;
        S.flat = Math.abs(d) < 0.02 ? S.flatTarget : S.flat + Math.sign(d) * 0.02;
      }
      g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, canvas.width, canvas.height);
      g.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
      if (IMG.board) g.drawImage(IMG.board, 0, 0, G.imageW, G.imageH);
      else { g.fillStyle = "#2a2018"; g.fillRect(0, 0, G.imageW, G.imageH); }
      try { drawFrame(); drawScores(); drawOrd(); drawScree(); drawSum(); }
      catch (err) { if (!S.drawErr) { S.drawErr = true; console.error("pca_plate draw", err); } }
      if (opts.debug) {
        g.lineWidth = 3; g.setLineDash([10, 6]);
        for (const [k, col] of [["frame", "#0f0"], ["sum", "#f0f"], ["scores", "#ff0"], ["ord", "#0ff"], ["scree", "#f80"]]) { const R = G[k]; g.strokeStyle = col; g.strokeRect(R.x, R.y, R.w, R.h); }
        g.setLineDash([]);
      }
    }
    raf = requestAnimationFrame(tick);
  }

  // ---- controls ----
  function animateTo(target, dur = 1400) {
    S.anim = S.mode === 3 ? { kind: "q", from: S.q, to: target, t0: performance.now(), dur }
                          : { kind: "theta", from: S.theta, to: target, t0: performance.now(), dur };
  }
  function randomTilt(anim = true) {
    const best = bestPercent();
    let pick = null;
    if (S.mode === 2) {
      const keep = S.theta; let low = Infinity;
      for (let k = 0; k < 200; k++) {
        S.theta = Math.random() * Math.PI * 2;
        const kp = keptPercent();
        if (kp < low) { low = kp; pick = S.theta; }
        if (kp < best - 15) { pick = S.theta; break; }
      }
      S.theta = keep;
    } else {
      const keep = S.q; let low = Infinity;
      for (let k = 0; k < 200; k++) {
        S.q = qnorm([Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5]);
        const kp = keptPercent();
        if (kp < low) { low = kp; pick = S.q; }
        if (kp < best - 15) { pick = S.q; break; }
      }
      S.q = keep;
    }
    S.anim = null;
    if (anim) animateTo(pick, 900);
    else { if (S.mode === 2) S.theta = pick; else S.q = pick; remember(); }
  }
  function findWidest(dur = 1400) {
    if (S.mode === 2) {
      const e = S.eig[2].vectors[0], a = Math.atan2(e[1], e[0]);
      // of the two ends, go to the one nearer the stick's current heading
      const target = Math.abs(wrapAngle(a - S.theta)) <= Math.PI / 2 ? a : wrapAngle(a + Math.PI);
      return animateTo(S.theta + wrapAngle(target - S.theta), dur);
    }
    const base = S.eig[3].q, cands = [base, qmul(base, [0, 1, 0, 0]), qmul(base, [0, 0, 1, 0]), qmul(base, [0, 0, 0, 1])];
    let bestQ = base, bd = -1;
    for (const c of cands) { const d = Math.abs(c[0] * S.q[0] + c[1] * S.q[1] + c[2] * S.q[2] + c[3] * S.q[3]); if (d > bd) { bd = d; bestQ = c; } }
    animateTo(bestQ, dur);
  }
  function flatten(on) {
    S.flatTarget = on ? 1 : 0;
    labelButtons();
  }
  function labelButtons() {
    btnMode.textContent = S.mode === 2 ? "Switch to 3D" : "Back to 2D";
    btnScale.textContent = S.scaled ? "Scaling: on" : "Scaling: off";
    btnFlat.textContent = S.flatTarget ? "Lift them back up" : (S.mode === 2 ? "Drop onto the stick" : "Drop onto the mat");
    btnRand.textContent = S.mode === 2 ? "Random turn" : "Random tilt";
  }
  function setMode(m, dur = 1300) {
    m = m === 3 ? 3 : 2;
    if (m === S.mode) return;
    S.anim = null;
    if (m === 3) {                         // the stick becomes the mat's first axis; the mat starts in the old plane
      const c = Math.cos(S.theta), s = Math.sin(S.theta);
      S.q = qfromBasis([c, s, 0], [-s, c, 0], [0, 0, 1]);
      S.mode = 3;
      S.camAnim = { from: { yaw: S.yaw, pitch: S.pitch, z: S.zGrow }, to: { yaw: CAM3.yaw, pitch: CAM3.pitch, z: 1 }, t0: performance.now(), dur };
    } else {                               // the mat's first axis, laid flat, becomes the stick
      const u = qrot(S.q, [1, 0, 0]);
      S.theta = Math.hypot(u[0], u[1]) > 1e-6 ? Math.atan2(u[1], u[0]) : 0;
      S.mode = 2;
      S.camAnim = { from: { yaw: S.yaw, pitch: S.pitch, z: S.zGrow }, to: { yaw: 0, pitch: 0, z: 0 }, t0: performance.now(), dur };
    }
    if (!dur) { const A = S.camAnim; S.yaw = A.to.yaw; S.pitch = A.to.pitch; S.zGrow = A.to.z; S.camAnim = null; }
    labelButtons(); remember();
  }
  function setScaled(on) {
    S.scaled = !!on; S.anim = null; standardise(); labelButtons(); remember();
  }
  btnMode.onclick = () => { flatten(false); setMode(S.mode === 2 ? 3 : 2); };
  btnScale.onclick = () => setScaled(!S.scaled);
  btnWide.onclick = () => findWidest();
  btnFlat.onclick = () => flatten(!S.flatTarget);
  btnRand.onclick = () => { flatten(false); randomTilt(true); };

  const toImg = (e) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * view.dpr - view.ox) / view.S, y: ((e.clientY - r.top) * view.dpr - view.oy) / view.S };
  };
  function inPoly(x, y, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const a = poly[i], b = poly[j];
      if ((a.y > y) !== (b.y > y) && x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x) inside = !inside;
    }
    return inside;
  }
  const inRect = (p, R) => p.x >= R.x && p.x <= R.x + R.w && p.y >= R.y && p.y <= R.y + R.h;
  function nearest(p) {                    // the coconut under the pointer, in the frame or the scores plot
    const list = inRect(p, G.frame) ? S.framePts : inRect(p, G.scores) ? S.scorePts : null;
    if (!list) return -1;
    let bi = -1, bd = 18 * 18;
    list.forEach((q, i) => { if (!q) return; const d = (q[0] - p.x) ** 2 + (q[1] - p.y) ** 2; if (d < bd) { bd = d; bi = i; } });
    return bi;
  }
  const frameCentre = () => ({ x: G.frame.x + G.frame.w / 2, y: G.frame.y + G.frame.h / 2 });
  let drag = null;
  canvas.addEventListener("pointerdown", (e) => {
    if (!S.ready) return;
    const p = toImg(e);
    if (inRect(p, G.scores)) { const i = nearest(p); if (i >= 0) { S.sel = i; remember(); } return; }
    if (!inRect(p, G.frame)) return;
    if (S.mode === 2) { const c = frameCentre(); drag = { mode: "stick", a: Math.atan2(-(p.y - c.y), p.x - c.x) }; }
    else if (S.grab && inPoly(p.x, p.y, S.grab)) drag = { mode: "plate" };
    else drag = { mode: "orbit" };
    drag.x = drag.x0 = e.clientX; drag.y = drag.y0 = e.clientY; drag.p0 = p; S.anim = null;
    canvas.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!S.ready) return;
    if (!drag) {
      const p = toImg(e), bi = nearest(p);
      canvas.style.cursor = bi >= 0 ? "pointer" : inRect(p, G.frame) ? "grab" : "default";
      if (bi < 0) { tip.style.display = "none"; return; }
      const r = stage.getBoundingClientRect();
      tip.style.display = "block"; tip.style.left = (e.clientX - r.left + 12) + "px"; tip.style.top = (e.clientY - r.top - 10) + "px";
      tip.textContent = `${S.names[bi]} (${String(S.groups[bi]).replace(/_/g, " ")})`;
      return;
    }
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.x = e.clientX; drag.y = e.clientY;
    if (drag.mode === "stick") {
      const p = toImg(e), c = frameCentre(), a = Math.atan2(-(p.y - c.y), p.x - c.x);
      S.theta += wrapAngle(a - drag.a); drag.a = a;
    } else if (drag.mode === "orbit") { S.yaw -= dx * 0.008; S.pitch = Math.max(-1.4, Math.min(1.4, S.pitch + dy * 0.008)); }
    else { const cam = camBasis(); S.q = qnorm(qmul(qmul(qaxis(cam.up, dx * 0.01), qaxis(cam.right, dy * 0.01)), S.q)); }
  });
  const endDrag = (e) => {
    if (!drag) return;
    if (e && Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 4) {   // a tap, not a turn: pick a coconut
      const i = nearest(drag.p0); if (i >= 0) S.sel = i;
    }
    remember(); drag = null;
  };
  canvas.addEventListener("pointerup", endDrag); canvas.addEventListener("pointercancel", () => endDrag(null));
  canvas.addEventListener("pointerleave", () => { tip.style.display = "none"; });

  const ready = (async () => {
    const [board, coconutImg, weave, csvText] = await Promise.all([
      loadImg(artPaths.board), loadImg(artPaths.coconut), loadImg(artPaths.weave),
      fetch(G.data).then((r) => { if (!r.ok) throw new Error("pca_plate: data " + r.status); return r.text(); })]);
    if (dead) return;
    IMG = { board, coconut: coconutImg, weave };
    setData(parseCsv(csvText));
    if (S.theta == null) { const keep = S.mode; S.mode = 2; S.theta = 0; randomTilt(false); S.mode = keep; }
    if (!S.q) { const keep = S.mode; S.mode = 3; S.q = [1, 0, 0, 0]; randomTilt(false); S.mode = keep; }
    labelButtons();
    resize();
    S.ready = true;
  })();

  const api = {
    ready,
    setMode: (m, dur) => setMode(m, dur), mode: () => S.mode,
    setScaled, scaled: () => S.scaled,
    findWidest, flatten, randomTilt: () => randomTilt(true),
    select: (i) => { S.sel = i; remember(); }, selected: () => S.sel, dim1Sum: (i) => dim1Sum(i ?? S.sel),
    keptPercent, bestPercent, atBest, axesAreDims,
    isSettled: () => !S.anim && !S.camAnim && S.flat === S.flatTarget,
    destroy() {
      if (dead) return;
      dead = true; cancelAnimationFrame(raf);
      if (ro) ro.disconnect(); else removeEventListener("resize", resize);
    },
  };
  canvas.pcaPlate = api;          // for tests and the console; harmless to students
  raf = requestAnimationFrame(tick);
  return api;
}
