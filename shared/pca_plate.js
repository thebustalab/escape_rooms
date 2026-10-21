// The PCA plate ("coconuts and the mat") — an engine INSTRUMENT (hotspot `type:"instrument"`,
// `kind:"pca_plate"`), ported 2026-10-20 from the harness prototype authoring_v2/ui/pca_plate_art.html.
//
// Three scaled measurements put each sample (a coconut) in a 3-D bamboo frame; a woven mat passes through
// the cloud. The player tilts the mat (drag it) or walks round the frame (drag elsewhere); every coconut
// drops straight onto the mat, the easel panel shows the mat face-on, and the koa board shows how much of
// the spread the mat keeps plus a live scree plot (solid = the mat's two axes now, dashed = Dim_1, Dim_2).
// "Find the widest" swings the mat to the PCA plane, where the panel IS the Dim_1 vs Dim_2 plot. READ,
// never graded: no notebook, no gate, no answer.
//
// All drawing is in IMAGE coordinates (the backdrop's pixels); one letterbox transform maps them to the
// canvas, as in drawdown.js. Geometry (from the hotspot's `geometry` JSON):
//   imageW, imageH                 backdrop size
//   view3d, panel, plank           {x,y,w,h} regions: the frame, the easel's woven square, the koa board
//   data                           CSV path relative to play.html
//   axes [x, y, z]                 three numeric columns (across, height, depth)
//   groupColumn, labelColumn       colour key and hover name columns
//   colours {group: "#hex"}        groups to keep (others are dropped) and their tints
// Art (hotspot `art`): board (required), coconut (keyed sprite), weave (tileable texture).
//
//   const plate = mountPcaPlate(hostEl, { geometry, art, pegs?, onPegs?(state), debug? });
//   plate.findWidest(); plate.flatten(on); plate.randomTilt(); plate.keptPercent(); plate.bestPercent();
//   plate.atBest(); plate.ready (Promise); plate.destroy();

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

export function mountPcaPlate(host, opts = {}) {
  const G = opts.geometry;
  for (const k of ["view3d", "panel", "plank"]) if (!G || !G[k]) throw new Error("pca_plate: geometry needs " + k);
  const AXES = G.axes, COLOURS = G.colours || {};
  const artPaths = opts.art || {};

  // ---- DOM: a toolbar above the letterboxed canvas ----
  const wrap = document.createElement("div"); wrap.className = "pcaplate";
  const bar = document.createElement("div"); bar.className = "pcaplatebar";
  const mkBtn = (txt) => { const b = document.createElement("button"); b.type = "button"; b.textContent = txt; bar.appendChild(b); return b; };
  const btnWide = mkBtn("Find the widest"), btnFlat = mkBtn("Flatten onto the mat"), btnRand = mkBtn("Random tilt");
  const arrowsLab = document.createElement("label"), arrowsBox = document.createElement("input");
  arrowsBox.type = "checkbox"; arrowsLab.append(arrowsBox, " measurement arrows"); bar.appendChild(arrowsLab);
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
  const S = { pts: [], groups: [], names: [], pca: null, q: saved.q || [1, 0, 0, 0], yaw: saved.yaw ?? -0.6,
              pitch: saved.pitch ?? 0.3, flat: 0, flatTarget: 0, anim: null, box: 1, ready: false };
  let IMG = {}, view = { S: 1, ox: 0, oy: 0, dpr: 1 }, raf = 0, dead = false;
  const remember = () => opts.onPegs && opts.onPegs({ q: S.q.slice(), yaw: S.yaw, pitch: S.pitch });

  // ---- maths on the current mat ----
  const plateBasis = () => [qrot(S.q, [1, 0, 0]), qrot(S.q, [0, 1, 0]), qrot(S.q, [0, 0, 1])];
  function axisShares() {
    const [u, v] = plateBasis(), n = S.pts.length;
    let su = 0, sv = 0;
    for (const p of S.pts) { su += dot(p, u) ** 2; sv += dot(p, v) ** 2; }
    return [su, sv].map((x) => 100 * x / (n - 1) / S.pca.total);
  }
  const bestPercent = () => 100 * (S.pca.values[0] + S.pca.values[1]) / S.pca.total;
  function atBest() {
    const [, , nrm] = plateBasis();
    return Math.abs(Math.abs(dot(nrm, qrot(S.pca.q, [0, 0, 1]))) - 1) < 2e-4;
  }
  function axesAreDims() {
    const [u, v] = plateBasis();
    return atBest() && Math.abs(dot(u, qrot(S.pca.q, [1, 0, 0]))) > 1 - 2e-4 && Math.abs(dot(v, qrot(S.pca.q, [0, 1, 0]))) > 1 - 2e-4;
  }

  function setData(rows) {
    rows = rows.filter((r) => r[G.groupColumn] in COLOURS && AXES.every((a) => Number.isFinite(+r[a])));
    const X = rows.map((r) => AXES.map((a) => +r[a])), n = X.length;
    const mean = [0, 1, 2].map((j) => X.reduce((s, r) => s + r[j], 0) / n);
    const sd = [0, 1, 2].map((j) => Math.sqrt(X.reduce((s, r) => s + (r[j] - mean[j]) ** 2, 0) / (n - 1)) || 1);
    S.pts = X.map((r) => r.map((v, j) => (v - mean[j]) / sd[j]));
    S.groups = rows.map((r) => r[G.groupColumn]);
    S.names = rows.map((r) => String(r[G.labelColumn] || "").replace(/_/g, " "));
    S.box = Math.max(...S.pts.flat().map(Math.abs)) * 1.03;
    const C = [0, 1, 2].map((i) => [0, 1, 2].map((j) => S.pts.reduce((s, p) => s + p[i] * p[j], 0) / (n - 1)));
    const e = jacobiEigen(C), v1 = e.vectors[0], v2 = e.vectors[1];
    S.pca = { values: e.values, total: e.values.reduce((a, b) => a + b, 0), q: qfromBasis(v1, v2, cross(v1, v2)) };
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
  function coconut(x, y, r, col, alpha = 1) {
    g.globalAlpha = alpha;
    if (IMG.coconut) g.drawImage(tinted(col), x - r, y - r, 2 * r, 2 * r);
    else { g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
    g.strokeStyle = col; g.lineWidth = 1.5; g.beginPath(); g.arc(x, y, r * 0.98, 0, 7); g.stroke();
    g.globalAlpha = 1;
  }
  function text(s, x, y, { align = "left", size = 18, fill = "#2b1a08", glow = null } = {}) {
    g.font = `600 ${size}px Georgia, serif`; g.textAlign = align;
    if (glow) { g.shadowColor = glow; g.shadowBlur = 5; }
    g.fillStyle = fill; g.fillText(s, x, y); g.shadowBlur = 0; g.textAlign = "left";
  }
  const label3d = (s, x, y) => text(s, x, y, { size: 20, fill: "#fff2cf", glow: "#000" });
  const ink = (s, x, y, align, size) => text(s, x, y, { align, size });
  const chalk = (s, x, y, align, size) => text(s, x, y, { align, size, fill: "#f6e7c4", glow: "rgba(0,0,0,0.8)" });

  // ---- camera ----
  const CAMD = 14;
  function camBasis() {
    const cy = Math.cos(S.yaw), sy = Math.sin(S.yaw), cp = Math.cos(S.pitch), sp = Math.sin(S.pitch);
    const fwd = [sy * cp, sp, cy * cp], right = norm(cross([0, 1, 0], fwd)), up = cross(fwd, right);
    return { right, up, fwd, pos: scale(fwd, CAMD) };
  }
  function project(p, cam) {
    const R = G.view3d, x = dot(p, cam.right), y = dot(p, cam.up), z = dot(p, cam.fwd);
    const k = CAMD / (CAMD - z), s = Math.min(R.w, R.h) / (3.05 * S.box);
    return { x: R.x + R.w / 2 + x * k * s, y: R.y + R.h / 2 - y * k * s, z, k };
  }

  // ---- drawing ----
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
  function draw3d() {
    const R = G.view3d, cam = camBasis(), P = (p) => project(p, cam);
    const [u, v, nrm] = plateBasis(), camSide = Math.sign(dot(cam.pos, nrm)) || 1;
    const grd = g.createRadialGradient(R.x + R.w / 2, R.y + R.h / 2, R.h * 0.05, R.x + R.w / 2, R.y + R.h / 2, R.h * 0.5);
    grd.addColorStop(0, "rgba(10,14,16,0.42)"); grd.addColorStop(1, "rgba(10,14,16,0)");
    g.fillStyle = grd; g.fillRect(R.x, R.y, R.w, R.h);
    const B = S.box, PLATE = S.box * 1.1, edges = [];
    for (const a of [-B, B]) for (const b of [-B, B]) edges.push([[a, b, -B], [a, b, B]], [[a, -B, b], [a, B, b]], [[-B, a, b], [B, a, b]]);
    edges.sort((e1, e2) => (dot(e1[0], cam.fwd) + dot(e1[1], cam.fwd)) - (dot(e2[0], cam.fwd) + dot(e2[1], cam.fwd)));
    edges.slice(0, 6).forEach(([a, b]) => bamboo(P(a), P(b), 6));
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]].forEach((ax, i) => {
      const s = P(scale(ax, -B)), e = P(scale(ax, B));
      g.strokeStyle = "rgba(255,240,200,0.35)"; g.lineWidth = 2; g.setLineDash([8, 8]);
      g.beginPath(); g.moveTo(s.x, s.y); g.lineTo(e.x, e.y); g.stroke(); g.setLineDash([]);
      label3d(AXES[i] + " →", e.x + 6, e.y);
    });
    const items = S.pts.map((p, i) => {
      const d = dot(p, nrm), shown = sub(p, scale(nrm, d * S.flat)), foot = sub(p, scale(nrm, d));
      return { i, shown, foot, side: Math.sign(d) === camSide ? 1 : -1, s: P(shown) };
    });
    const drops = (list) => {
      g.strokeStyle = "rgba(255,248,225,0.55)"; g.lineWidth = 1.5;
      for (const it of list) { const a = P(it.shown), b = P(it.foot); g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); }
    };
    const nuts = (list, alpha) => list.sort((a, b) => a.s.z - b.s.z)
      .forEach((it) => coconut(it.s.x, it.s.y, 13 * it.s.k, COLOURS[S.groups[it.i]], alpha));
    const behind = items.filter((it) => it.side < 0 && S.flat < 1), front = items.filter((it) => it.side > 0 || S.flat >= 1);
    drops(behind); nuts(behind, 0.85);
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => P([0, 1, 2].map((k) => (u[k] * a + v[k] * b) * PLATE)));
    drawMat3d(corners, 0.45);
    S.plateScreen = corners;
    const named = axesAreDims(), o = P([0, 0, 0]), ue = P(scale(u, PLATE)), ve = P(scale(v, PLATE));
    g.strokeStyle = "#3b240c"; g.lineWidth = 3;
    g.beginPath(); g.moveTo(o.x, o.y); g.lineTo(ue.x, ue.y); g.moveTo(o.x, o.y); g.lineTo(ve.x, ve.y); g.stroke();
    label3d(named ? "Dim_1" : "across", ue.x + 6, ue.y); label3d(named ? "Dim_2" : "up", ve.x + 6, ve.y);
    drops(front); nuts(front, 1);
    edges.slice(6).forEach(([a, b]) => bamboo(P(a), P(b), 6));
  }
  function drawPanel() {
    const R = G.panel, cx = R.x + R.w / 2, cy = R.y + R.h / 2, s = Math.min(R.w, R.h) / (2.5 * S.box);
    const [u, v] = plateBasis(), named = axesAreDims(), pc = S.pca.values.map((x) => Math.round(100 * x / S.pca.total));
    g.save(); g.beginPath(); g.rect(R.x, R.y, R.w, R.h); g.clip();
    g.strokeStyle = "rgba(43,26,8,0.55)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(R.x + 10, cy); g.lineTo(R.x + R.w - 10, cy); g.moveTo(cx, R.y + 10); g.lineTo(cx, R.y + R.h - 10); g.stroke();
    ink(named ? `Dim_1 (${pc[0]}%)` : "across", R.x + R.w - 12, cy - 10, "right", 18);
    g.save(); g.translate(cx - 10, R.y + 14); g.rotate(-Math.PI / 2); ink(named ? `Dim_2 (${pc[1]}%)` : "up", 0, 0, "right", 18); g.restore();
    S.p2 = S.pts.map((p, i) => {
      const x = cx + dot(p, u) * s, y = cy - dot(p, v) * s;
      coconut(x, y, 10, COLOURS[S.groups[i]]);
      return [x, y];
    });
    if (arrowsBox.checked) {
      [[1, 0, 0], [0, 1, 0], [0, 0, 1]].forEach((ax, i) => {
        const L = 0.8 * S.box, x = cx + dot(ax, u) * L * s, y = cy - dot(ax, v) * L * s, a = Math.atan2(y - cy, x - cx);
        g.strokeStyle = "#2b1a08"; g.fillStyle = "#2b1a08"; g.lineWidth = 3;
        g.beginPath(); g.moveTo(cx, cy); g.lineTo(x, y); g.stroke();
        g.beginPath(); g.moveTo(x, y); g.lineTo(x - 14 * Math.cos(a - 0.4), y - 14 * Math.sin(a - 0.4)); g.lineTo(x - 14 * Math.cos(a + 0.4), y - 14 * Math.sin(a + 0.4)); g.fill();
        ink(AXES[i], x + 10 * Math.cos(a), y + 10 * Math.sin(a) + 6, "center", 18);
      });
    }
    g.restore();
  }
  function drawPlank() {
    const R = G.plank, pad = 14, shares = axisShares(), kept = shares[0] + shares[1];
    const dims = S.pca.values.slice(0, 2).map((x) => 100 * x / S.pca.total), bestF = dims[0] + dims[1];
    const gx = R.x + pad, gw = R.w * 0.40, gy = R.y + R.h * 0.62, gh = R.h * 0.16;
    chalk("spread kept", gx, R.y + 26, "left", 16);
    chalk(`${kept.toFixed(1)}%${atBest() ? " ✔" : ""}`, gx, R.y + 52, "left", 24);
    g.fillStyle = "rgba(250,235,200,0.18)"; g.fillRect(gx, gy, gw, gh);
    g.fillStyle = "rgba(250,236,200,0.9)"; g.fillRect(gx, gy, gw * kept / 100, gh);
    g.strokeStyle = "#f6e7c4"; g.lineWidth = 1.5; g.strokeRect(gx, gy, gw, gh);
    g.lineWidth = 3; g.beginPath(); g.moveTo(gx + gw * bestF / 100, gy - 5); g.lineTo(gx + gw * bestF / 100, gy + gh + 5); g.stroke();
    chalk(`best ${bestF.toFixed(1)}%`, gx + gw, R.y + 52, "right", 13);
    const top = R.y + 20, bot = R.y + R.h - 20, sh = bot - top, named = axesAreDims();
    const x0 = R.x + R.w * 0.52, x1 = R.x + R.w - pad, xs = [x0 + (x1 - x0) * 0.32, x0 + (x1 - x0) * 0.74], bw = (x1 - x0) * 0.24;
    g.strokeStyle = "#f6e7c4"; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x0, top); g.lineTo(x0, bot); g.lineTo(x1, bot); g.stroke();
    chalk("scree", x0 + 4, top - 4, "left", 12);
    shares.forEach((v, i) => {
      const y = bot - sh * v / 100, yd = bot - sh * dims[i] / 100;
      g.fillStyle = "rgba(250,236,200,0.85)"; g.fillRect(xs[i] - bw / 2, y, bw, bot - y);
      g.setLineDash([5, 3]); g.strokeStyle = "#f6e7c4"; g.lineWidth = 1.5; g.strokeRect(xs[i] - bw / 2, yd, bw, bot - yd); g.setLineDash([]);
      chalk(v.toFixed(0) + "%", xs[i] + bw / 2 + 4, Math.max(Math.min(y, yd) + 12, top + 10), "left", 12);
      chalk(named ? "Dim_" + (i + 1) : ["across", "up"][i], xs[i], bot + 15, "center", 12);
    });
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

  function tick() {
    if (dead) return;
    if (S.ready) {
      if (S.anim) {
        const t = Math.min(1, (performance.now() - S.anim.t0) / S.anim.dur), e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
        S.q = qslerp(S.anim.from, S.anim.to, e);
        if (t >= 1) { S.q = S.anim.to; S.anim = null; remember(); }
      }
      if (S.flat !== S.flatTarget) {
        const d = S.flatTarget - S.flat;
        S.flat = Math.abs(d) < 0.02 ? S.flatTarget : S.flat + Math.sign(d) * 0.02;
      }
      g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, canvas.width, canvas.height);
      g.setTransform(view.S, 0, 0, view.S, view.ox, view.oy);
      if (IMG.board) g.drawImage(IMG.board, 0, 0, G.imageW, G.imageH);
      draw3d(); drawPanel(); drawPlank();
      if (opts.debug) {
        g.lineWidth = 3; g.setLineDash([10, 6]);
        for (const [k, col] of [["view3d", "#0f0"], ["panel", "#f0f"], ["plank", "#ff0"]]) { const R = G[k]; g.strokeStyle = col; g.strokeRect(R.x, R.y, R.w, R.h); }
        g.setLineDash([]);
      }
    }
    raf = requestAnimationFrame(tick);
  }

  // ---- controls ----
  const animateTo = (q, dur = 1400) => { S.anim = { from: S.q, to: q, t0: performance.now(), dur }; };
  function randomTilt(anim = true) {
    const keep = S.q, best = bestPercent();
    let q;
    for (let k = 0; k < 200; k++) {
      q = qnorm([Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5]);
      S.q = q; const sh = axisShares();
      if (sh[0] + sh[1] < best - 15) break;
    }
    S.q = keep; S.anim = null;
    if (anim) animateTo(q, 900); else { S.q = q; remember(); }
  }
  function findWidest(dur = 1400) {
    const base = S.pca.q, cands = [base, qmul(base, [0, 1, 0, 0]), qmul(base, [0, 0, 1, 0]), qmul(base, [0, 0, 0, 1])];
    let bestQ = base, bd = -1;
    for (const c of cands) { const d = Math.abs(c[0] * S.q[0] + c[1] * S.q[1] + c[2] * S.q[2] + c[3] * S.q[3]); if (d > bd) { bd = d; bestQ = c; } }
    animateTo(bestQ, dur);
  }
  function flatten(on) {
    S.flatTarget = on ? 1 : 0;
    btnFlat.textContent = on ? "Lift them back up" : "Flatten onto the mat";
  }
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
  let drag = null;
  canvas.addEventListener("pointerdown", (e) => {
    if (!S.ready) return;
    const p = toImg(e);
    if (S.plateScreen && inPoly(p.x, p.y, S.plateScreen)) drag = { mode: "plate" };
    else if (inRect(p, G.view3d)) drag = { mode: "orbit" };
    else return;
    drag.x = e.clientX; drag.y = e.clientY; S.anim = null; canvas.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!S.ready) return;
    if (!drag) {
      const p = toImg(e); let bi = -1, bd = 200;
      if (inRect(p, G.panel)) (S.p2 || []).forEach(([x, y], i) => { const d = (x - p.x) ** 2 + (y - p.y) ** 2; if (d < bd) { bd = d; bi = i; } });
      canvas.style.cursor = (S.plateScreen && inPoly(p.x, p.y, S.plateScreen)) || inRect(p, G.view3d) ? "grab" : "default";
      if (bi < 0) { tip.style.display = "none"; return; }
      const r = stage.getBoundingClientRect();
      tip.style.display = "block"; tip.style.left = (e.clientX - r.left + 12) + "px"; tip.style.top = (e.clientY - r.top - 10) + "px";
      tip.textContent = `${S.names[bi]} (${String(S.groups[bi]).replace(/_/g, " ")})`;
      return;
    }
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.x = e.clientX; drag.y = e.clientY;
    if (drag.mode === "orbit") { S.yaw -= dx * 0.008; S.pitch = Math.max(-1.4, Math.min(1.4, S.pitch + dy * 0.008)); }
    else { const cam = camBasis(); S.q = qnorm(qmul(qmul(qaxis(cam.up, dx * 0.01), qaxis(cam.right, dy * 0.01)), S.q)); }
  });
  const endDrag = () => { if (drag) remember(); drag = null; };
  canvas.addEventListener("pointerup", endDrag); canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("pointerleave", () => { tip.style.display = "none"; });

  const ready = (async () => {
    const [board, coconutImg, weave, csvText] = await Promise.all([
      loadImg(artPaths.board), loadImg(artPaths.coconut), loadImg(artPaths.weave),
      fetch(G.data).then((r) => { if (!r.ok) throw new Error("pca_plate: data " + r.status); return r.text(); })]);
    if (dead) return;
    IMG = { board, coconut: coconutImg, weave };
    setData(parseCsv(csvText));
    if (!saved.q) randomTilt(false);
    resize();
    S.ready = true;
  })();

  const api = {
    ready,
    findWidest, flatten, randomTilt: () => randomTilt(true),
    keptPercent: () => { const s = axisShares(); return s[0] + s[1]; },
    bestPercent, atBest, axesAreDims,
    isSettled: () => !S.anim && S.flat === S.flatTarget,
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
