// The fish board — an engine INSTRUMENT (hotspot `type:"instrument"`, `kind:"fish_board"`), ported
// 2026-10-26 from the harbour prototype rooms/comparing_means/harbour/_scratch/fish_board/fish_board.js.
//
// WHY: a four-act teaching demo for the comparing-means chapter that Lucas works on the projector with the
// class, and students can return to between loads. The water is the population; a net is a random sample;
// the boards show the catch; bronze dials and oil lamps show the real tests (fish_stats.js, pinned to R).
// Nothing is staged: false positives turn up at their honest rate, which is the point of acts 2 and 4.
// READ, never graded: no notebook, no gate, no answer, nothing saved.
//
//   1 Population and sample   2 Same water, two nets (Welch)
//   3 Two waters (Welch vs Wilcox, picked by Shapiro)   4 Ten boats (45 pairs; the lever = Tukey / Dunn-Holm)
// An "Is the catch normal?" act (Shapiro alone) was cut 2026-10-26 (Lucas: students grasp it); act 3 still
// runs Shapiro on each catch to pick its road.
//
// All drawing is in BOARD coordinates (geometry imageW x imageH, the art's logical 1536 x 864 crop); one
// letterbox transform maps them to the canvas. Geometry (the hotspot's `geometry` JSON):
//   imageW, imageH                       the logical board
//   base {crop_y_px, edge_top_px, water_top_px}   where the crop starts, the quay edge, the water line
//   dial {pivot, band_centre, band_r}    fractions of the dial sprite; needle {ring}
// Art (hotspot `art`, paths relative to play.html): board (the quay from above) plus the sprites plank,
// fish, dial, needle, net, lamp, lever. All are required: a missing one shows "could not load".
//
//   const fb = mountFishBoard(hostEl, { geometry, art, pegs?, onPegs?(state), seed? });
//   fb.setAct(n); fb.cast(); fb.castMany(k); fb.throwMonster(); fb.toggleLever(); fb.state();
//   fb.leverClient() → client {x, y} of the act 4 lever; fb.ready (Promise); fb.destroy().
// The canvas carries the API as `canvas.fishBoard` for tests.
import "./fish_stats.js?v=143";     // window.FishStats: the board's tests (Welch, Shapiro, Wilcox, Tukey, Dunn), pinned to R

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});
const SPRITES = ["board", "plank", "fish", "dial", "needle", "net", "lamp", "lever"];
const ACT_NAMES = ["Population and sample", "Same water, two nets", "Two waters", "Ten boats"];

export function mountFishBoard(host, opts = {}) {
  const G = opts.geometry;
  for (const k of ["imageW", "imageH", "base", "dial", "needle"]) if (!G || !G[k]) throw new Error("fish_board: geometry needs " + k);
  const S = window.FishStats;
  if (!S) throw new Error("fish_board: fish_stats.js did not load");
  const artPaths = opts.art || {};
  const saved = opts.pegs || {};
  const seed = Number(opts.seed) || (Date.now() % 1e9);
  const R = S.rng(seed);
  let dead = false, raf = 0;

  // ---- DOM: act tabs, caption, the letterboxed canvas, controls ----
  const wrap = document.createElement("div"); wrap.className = "fishboard";
  const tabs = document.createElement("div"); tabs.className = "fishboardtabs";
  const caption = document.createElement("div"); caption.className = "fishboardcaption";
  const cv = document.createElement("canvas"); cv.className = "fishboardcanvas";
  cv.style.aspectRatio = `${G.imageW} / ${G.imageH}`;
  const ctl = document.createElement("div"); ctl.className = "fishboardcontrols";
  ACT_NAMES.forEach((name, i) => {
    const t = document.createElement("button"); t.type = "button"; t.className = "fishboardtab"; t.dataset.act = String(i + 1);
    t.textContent = `${i + 1} · ${name}`; t.onclick = () => setAct(i + 1); tabs.appendChild(t);
  });
  wrap.append(tabs, caption, cv, ctl);
  host.appendChild(wrap);
  const ctx = cv.getContext("2d");

  // ---------- the waters (populations) ----------
  // Lengths in cm. Normal waters: a shoal of similar fish. Skewed waters: mostly small fry, the odd monster.
  const WATERS = {
    open:  { name: "Open harbor",   kind: "normal", tint: "#1d4a63", draw: () => R.normal(30, 5) },
    mouth: { name: "Harbor mouth",  kind: "normal", tint: "#1f5568", draw: () => R.normal(35, 5) },
    // Skewed waters: a shoal of small fry plus about one big fish in seven. Tuned (2026-10-25) so Shapiro
    // flags about 30% of 5-fish catches, 60% of 8 and 90% of 15: small nets often hide the skew.
    lake:  { name: "Lake harbor",   kind: "skewed", tint: "#24524a", draw: () => (R() < 0.15 ? R.normal(45, 7) : 15 * Math.exp(R.normal(0, 0.3))) },
    inlet: { name: "Lake inlet",    kind: "skewed", tint: "#2a5a48", draw: () => (R() < 0.15 ? R.normal(52, 7) : 20 * Math.exp(R.normal(0, 0.3))) },
  };
  const POP = 300, MAXLEN = 80, MINLEN = 6;
  for (const key of Object.keys(WATERS)) {
    const w = WATERS[key];
    w.fish = [];
    for (let i = 0; i < POP; i++) {
      let len;
      do { len = w.draw(); } while (len < MINLEN || len > MAXLEN - 2);
      w.fish.push({ len, x: R(), y: 0.08 + 0.84 * R(), v: (0.004 + 0.006 * R()) * (R() < 0.5 ? -1 : 1),
        ph: R() * 6.28, caught: false, water: key });
    }
    w.trueMean = S.mean(w.fish.map((f) => f.len));
  }

  // ---------- state ----------
  const st = {
    act: Math.min(4, Math.max(1, Number(saved.act) || 1)),
    n: Number(saved.n) || 8,
    numbers: saved.numbers !== false,
    water: "open", waterA: "open", waterB: "mouth", water5: "open",
    drain: false, elsewhere: false, corrected: false, road5: "parametric",
    rows: [],            // [{ fish: [fishObj], color, label }]
    nets: [],            // nets rising out of the water: [{ ri, t0, n }]
    flights: [],         // animation of caught fish
    trail: [],           // act 1: means of every haul so far
    result: null,        // the act's latest test result
    tally: {},
    monster: false,
  };
  const remember = () => opts.onPegs && opts.onPegs({ act: st.act, n: st.n, numbers: st.numbers });
  const C_A = "#e0a83a", C_B = "#4fc0b4";
  const BOAT_COLS = ["#e0a83a", "#4fc0b4", "#d47a6a", "#9fb85a", "#b48ad6", "#e6d26a", "#6aa6e0", "#e08ab4", "#8ad6c8", "#c8a07a"];

  // ---------- canvas, letterboxed to the logical board ----------
  // The board is the edge of the quay seen from straight above (Lucas, 2026-10-25): the measuring boards lie
  // on the paving at the TOP, the harbor is at the BOTTOM, and a net rises out of the water with each catch.
  const LW = G.imageW, LH = G.imageH;
  const EDGE = G.base.edge_top_px, WATER_TOP = G.base.water_top_px;
  let scale = 1, ox = 0, oy = 0, dpr = 1;
  function resize() {
    if (dead) return;
    dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cw = Math.max(1, cv.clientWidth), ch = Math.max(1, cv.clientHeight);
    cv.width = Math.round(cw * dpr); cv.height = Math.round(ch * dpr);
    scale = Math.min(cv.width / LW, cv.height / LH);
    ox = (cv.width - LW * scale) / 2; oy = (cv.height - LH * scale) / 2;
  }
  const ro = typeof ResizeObserver === "function" ? new ResizeObserver(() => resize()) : null;
  if (ro) ro.observe(cv); else addEventListener("resize", resize);
  const toBoard = (ev) => {
    const r = cv.getBoundingClientRect();
    return { x: ((ev.clientX - r.left) * dpr - ox) / scale, y: ((ev.clientY - r.top) * dpr - oy) / scale };
  };

  // ---------- art ----------
  let IMG = {}, artReady = false, artFailed = false, SHADOW = null;
  const TINTS = new Map();
  function offscreen(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  // The fish in the water are dark shadows of the fish sprite; the fish on a board are tinted by net.
  function buildDerived() {
    const f = IMG.fish;
    SHADOW = offscreen(f.width, f.height);
    const g = SHADOW.getContext("2d");
    g.drawImage(f, 0, 0); g.globalCompositeOperation = "source-in"; g.fillStyle = "#06232b"; g.fillRect(0, 0, f.width, f.height);
  }
  function tinted(color) {
    if (!TINTS.has(color)) {
      const f = IMG.fish, c = offscreen(f.width, f.height), g = c.getContext("2d");
      g.drawImage(f, 0, 0);
      g.globalCompositeOperation = "multiply"; g.globalAlpha = 0.6; g.fillStyle = color; g.fillRect(0, 0, f.width, f.height);
      g.globalAlpha = 1; g.globalCompositeOperation = "destination-in"; g.drawImage(f, 0, 0);
      TINTS.set(color, c);
    }
    return TINTS.get(color);
  }


  // ---------- layout per act (boards on the paving, above the quay edge) ----------
  const WATER_BOX = { x: 0, y: WATER_TOP, w: LW, h: LH - WATER_TOP };
  function boardRows() {
    switch (st.act) {
      case 1: return [{ x: 40, y: 26, w: 1060, h: 250 }];
      case 2: return [{ x: 40, y: 16, w: 1060, h: 212 }, { x: 40, y: 240, w: 1060, h: 212 }];
      case 3: return [{ x: 40, y: 10, w: 1060, h: 142 }, { x: 40, y: 160, w: 1060, h: 142 }];
      case 4: { const out = []; for (let i = 0; i < 10; i++) out.push({ x: 40, y: 12 + i * 45, w: 880, h: 40 }); return out; }
    }
    return [];
  }
  const STRIP = (box) => Math.max(13, Math.min(28, box.h * 0.13));
  const stripTop = (box) => box.y + box.h - STRIP(box) - 5;
  const lenX = (box, len) => { const x0 = box.x + box.w * (st.act === 4 ? 0.13 : 0.04), x1 = box.x + box.w - 16; return x0 + (len / MAXLEN) * (x1 - x0); };

  // ---------- casting ----------
  function watersForAct() {
    if (st.act === 3) return [st.waterA, st.waterB];
    if (st.act === 4) return [st.water5];
    return [st.water];
  }
  function releaseAll() { for (const k in WATERS) for (const f of WATERS[k].fish) f.caught = false; }
  function netFrom(waterKey, n) {
    const free = WATERS[waterKey].fish.filter((f) => !f.caught);
    const got = R.pick(free, n);
    got.forEach((f) => { f.caught = true; });
    return got;
  }
  function cast(animate = true) {
    releaseAll();
    st.monster = false;
    const n = st.n, rows = [];
    if (st.act === 1) rows.push({ fish: netFrom(st.water, n), color: C_A, label: "Net", water: st.water });
    else if (st.act === 2) {
      rows.push({ fish: netFrom(st.water, n), color: C_A, label: "Net A", water: st.water });
      rows.push({ fish: netFrom(st.water, n), color: C_B, label: "Net B", water: st.water });
    } else if (st.act === 3) {
      rows.push({ fish: netFrom(st.waterA, n), color: C_A, label: WATERS[st.waterA].name, water: st.waterA });
      rows.push({ fish: netFrom(st.waterB, n), color: C_B, label: WATERS[st.waterB].name, water: st.waterB });
    } else if (st.act === 4) {
      const other = WATERS[st.water5].kind === "normal" ? "mouth" : "inlet";
      for (let b = 0; b < 10; b++) {
        const wk = st.elsewhere && b === 0 ? (st.water5 === other ? "open" : other) : st.water5;
        rows.push({ fish: netFrom(wk, n), color: BOAT_COLS[b], label: "Boat " + (b + 1), water: wk });
      }
    }
    st.rows = rows;
    compute();
    st.flights = []; st.nets = [];
    if (animate) {
      // Acts 1-3: each net rises out of the water, then its fish fly up onto the board. Act 4's ten boats
      // land straight from the water (ten nets at once would bury the lamps).
      const now = performance.now(), useNets = st.act !== 4;
      rows.forEach((row, ri) => {
        let t0 = now + (st.act === 4 ? ri * 40 : 0);
        if (useNets) { st.nets.push({ ri, t0: now + ri * 140, n: row.fish.length }); t0 = now + ri * 140 + RISE; }
        row.fish.forEach((f, k) => st.flights.push({ f, ri, t0: t0 + k * 45, dur: useNets ? 600 : 700, fromNet: useNets }));
      });
    }
  }

  function compute() {
    const L = st.rows.map((r) => r.fish.map((f) => f.len));
    const T = (st.tally[st.act] = st.tally[st.act] || {});
    T.hauls = (T.hauls || 0) + 1;
    if (st.act === 1) {
      const m = S.mean(L[0]);
      st.trail.push(m);
      if (st.trail.length > 400) st.trail.shift();
      st.result = { mean: m };
    } else if (st.act === 2) {
      const w = S.welch(L[0], L[1]);
      st.result = w;
      T.sig = (T.sig || 0) + (w.p < 0.05 ? 1 : 0);
    } else if (st.act === 3) {
      st.result = compute3(L);
    } else if (st.act === 4) {
      st.result = compute4(L);
      const r = st.result;
      T.anyRaw = (T.anyRaw || 0) + (r.raw.some((p) => p < 0.05) ? 1 : 0);
      T.anyCor = (T.anyCor || 0) + (r.cor.some((p) => p < 0.05) ? 1 : 0);
      T.litRaw = (T.litRaw || 0) + r.raw.filter((p) => p < 0.05).length;
      T.litCor = (T.litCor || 0) + r.cor.filter((p) => p < 0.05).length;
    }
    updateTally();
  }
  function compute3(L) {
    const shA = S.shapiro(L[0]), shB = S.shapiro(L[1]);
    const road = shA.p < 0.05 || shB.p < 0.05 ? "rank" : "parametric";
    return { shA, shB, road, welch: S.welch(L[0], L[1]), wilcox: S.wilcox(L[0], L[1]) };
  }
  function compute4(L) {
    // The road is Lucas's choice here (a toggle), not ten Shapiro tests: with ten catches, one of them
    // fails Shapiro by chance often enough to flip the road mid-demo, which would bury the lesson.
    const road = st.road5;
    let raw, cor, pairs;
    if (road === "parametric") {
      const u = S.pairwisePooledT(L), t = S.tukey(L);
      raw = u.map((r) => r.p); cor = t.map((r) => r.p); pairs = t.map((r) => [r.i, r.j]);
    } else {
      const d = S.dunn(L);
      raw = d.map((r) => r.p); cor = d.map((r) => r.pAdj); pairs = d.map((r) => [r.i, r.j]);
    }
    return { road, raw, cor, pairs };
  }
  function throwMonster() {
    if (st.act !== 3 || !st.rows.length || st.monster) return;
    const f = { len: 76, x: 0.5, y: 0.5, v: 0, ph: 0, caught: true, water: st.waterA, monster: true };
    st.rows[0].fish.push(f);
    st.monster = true;
    st.result = compute3(st.rows.map((r) => r.fish.map((x) => x.len)));
    st.flights.push({ f, ri: 0, t0: performance.now(), dur: 900, fromTop: true });   // a passer-by throws it on
  }

  // ---------- drawing helpers ----------
  const fishPx = (len) => 8 + len * 0.42;
  // Ink on wood or stone: dark with a faint light edge, the way a scale is cut into bronze.
  function engrave(s, x, y, size, align = "left", style = "", color = "rgba(45,25,6,.93)") {
    ctx.font = `${style} ${size}px Georgia, serif`; ctx.textAlign = align; ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(255,236,190,.5)"; ctx.fillText(s, x + 1, y + 1);
    ctx.fillStyle = color; ctx.fillText(s, x, y);
  }
  function engraveLine(x0, y0, x1, y1, w = 1.6) {
    ctx.lineWidth = w;
    ctx.strokeStyle = "rgba(255,232,170,.5)"; ctx.beginPath(); ctx.moveTo(x0 + 1, y0 + 1); ctx.lineTo(x1 + 1, y1 + 1); ctx.stroke();
    ctx.strokeStyle = "rgba(45,25,6,.9)"; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  // Light lettering over water (and anything dark): cream with a soft dark halo.
  function label(s, x, y, size, color = "#fff1d0", align = "left", style = "") {
    ctx.save();
    ctx.font = `${style} ${size}px Georgia, serif`; ctx.textAlign = align; ctx.textBaseline = "middle";
    ctx.shadowColor = "rgba(0,0,0,.85)"; ctx.shadowBlur = 6; ctx.fillStyle = color; ctx.fillText(s, x, y);
    ctx.restore();
  }
  const text = (s, x, y, size = 20, color = "#3a2412", align = "left", weight = "") => engrave(s, x, y, size, align, weight, color);
  const fmtP = (p) => (p < 0.001 ? "< 0.001" : p.toFixed(p < 0.01 ? 3 : 2));

  function drawFish(x, y, w, color, dir = 1, alpha = 1) {
    const img = color ? tinted(color) : IMG.fish, h = (w * img.height) / img.width;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y); ctx.scale(-dir, 1);           // the sprite faces left; dir 1 = nose toward the stop block
    ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = 4; ctx.shadowOffsetY = 2;
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
    ctx.restore();
  }
  // Wooden boards: one plank sprite, stretched to the box (stacked planks read as a second scale).
  function drawPlanks(box) {
    const pl = IMG.plank, n = 1, ph = box.h;
    ctx.save();
    ctx.shadowColor = "rgba(20,10,0,.5)"; ctx.shadowBlur = 14; ctx.shadowOffsetY = 6;
    ctx.fillStyle = "rgba(60,40,20,1)"; ctx.fillRect(box.x + 4, box.y + 4, box.w - 8, box.h - 8);
    ctx.restore();
    for (let i = 0; i < n; i++) ctx.drawImage(pl, box.x, box.y + i * ph, box.w, ph + (i < n - 1 ? 1 : 0));
  }
  // The bronze strip along the board's lower edge, with the scale cut into it.
  function drawScale(box, small) {
    const sh = STRIP(box), y = stripTop(box);
    const x0 = lenX(box, 0) - 8, x1 = lenX(box, MAXLEN) + 8;
    const g = ctx.createLinearGradient(0, y, 0, y + sh);
    g.addColorStop(0, "#e2b468"); g.addColorStop(0.45, "#b9843a"); g.addColorStop(1, "#7c5222");
    ctx.fillStyle = g; ctx.fillRect(x0, y, x1 - x0, sh);
    ctx.strokeStyle = "rgba(55,32,8,.85)"; ctx.lineWidth = 1; ctx.strokeRect(x0 + 0.5, y + 0.5, x1 - x0 - 1, sh - 1);
    for (let L = 0; L <= MAXLEN; L += small ? 10 : 5) {
      const x = lenX(box, L), big = L % 10 === 0;
      engraveLine(x, y + 1, x, y + (big ? sh * 0.5 : sh * 0.3), small ? 1.2 : 1.6);
      if (big && !small) engrave(String(L), x, y + sh * 0.74, Math.round(sh * 0.46), "center", "bold");
    }
    if (!small) engrave("cm", x1 + 4, y + sh * 0.6, Math.round(sh * 0.42), "left", "italic", "rgba(40,22,6,.85)");
  }
  // The mean marker: a bronze wedge set on the strip, pointing down at the scale.
  function wedge(x, y, s = 13, fill = "#f2d48a") {
    ctx.save();
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - s * 0.75, y - s * 1.2); ctx.lineTo(x + s * 0.75, y - s * 1.2); ctx.closePath();
    ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 4; ctx.shadowOffsetY = 2;
    ctx.fillStyle = fill; ctx.fill();
    ctx.shadowColor = "transparent"; ctx.strokeStyle = "rgba(60,35,8,.9)"; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.restore();
  }
  function placard(x, y, w, h) { drawPlanks({ x, y, w, h }); }

  // ---------- the water (bottom) ----------
  function waterPanels() {
    const ws = watersForAct();
    if (st.act === 4 && st.elsewhere && st.rows.length) {
      const other = st.rows[0].water, w0 = Math.round(WATER_BOX.w * 0.76);
      return [{ key: st.water5, x: 0, y: WATER_BOX.y, w: w0 - 30, h: WATER_BOX.h },
        { key: other, x: w0 + 30, y: WATER_BOX.y, w: WATER_BOX.w - w0 - 30, h: WATER_BOX.h }];
    }
    if (ws.length === 2 && ws[0] !== ws[1]) {
      const half = WATER_BOX.w / 2;
      return [{ key: ws[0], x: 0, y: WATER_BOX.y, w: half - 30, h: WATER_BOX.h },
        { key: ws[1], x: half + 30, y: WATER_BOX.y, w: half - 30, h: WATER_BOX.h }];
    }
    return [{ key: ws[0], ...WATER_BOX }];
  }
  function fishWaterPos(f, panels) {
    const p = panels.find((q) => q.key === f.water) || panels[0];
    return { x: p.x + f.x * p.w, y: p.y + (0.1 + 0.85 * f.y) * p.h, p };
  }
  // A stone jetty between two waters: a slice of the painted quay edge, turned to run down into the harbor.
  function jetty(x0, x1) {
    const len = LH - WATER_TOP + 10, w = x1 - x0;
    ctx.save();
    ctx.shadowColor = "rgba(0,20,25,.6)"; ctx.shadowBlur = 16;
    ctx.translate((x0 + x1) / 2, WATER_TOP - 10); ctx.rotate(Math.PI / 2);
    ctx.drawImage(IMG.board, 260, EDGE + G.base.crop_y_px + 8, 520, G.base.water_top_px - EDGE - 16, 0, -w / 2, len, w);
    ctx.restore();
  }
  function drawWater(now) {
    const panels = waterPanels();
    if (panels.length === 2) jetty(panels[0].x + panels[0].w, panels[1].x);
    for (const p of panels) {
      const w = WATERS[p.key];
      ctx.save(); ctx.beginPath(); ctx.rect(p.x, p.y, p.w, p.h); ctx.clip();
      if (w.kind === "skewed") { ctx.fillStyle = "rgba(38,92,52,.38)"; ctx.fillRect(p.x, p.y, p.w, p.h); }   // the lake's greener water
      const shrink = p.w < 500 ? 0.7 : 1;
      for (const f of w.fish) {
        if (f.caught) continue;
        f.x += f.v * 0.016 * 6; if (f.x > 1.03) f.x = -0.03; if (f.x < -0.03) f.x = 1.03;
        const y = p.y + (0.1 + 0.85 * f.y + 0.01 * Math.sin(now / 700 + f.ph)) * p.h;
        const fw = fishPx(f.len) * 1.7 * shrink, fh = (fw * SHADOW.height) / SHADOW.width;
        ctx.save(); ctx.globalAlpha = 0.5;
        ctx.translate(p.x + f.x * p.w, y); ctx.scale(f.v > 0 ? -1 : 1, 1);
        ctx.drawImage(SHADOW, -fw / 2, -fh / 2, fw, fh);
        ctx.restore();
      }
      ctx.restore();
      label(w.name, p.x + 18, p.y + 24, 24, "#fff1d0", "left", "italic");
      if (st.drain && st.act === 1) label(`every fish here: mean ${w.trueMean.toFixed(1)} cm`, p.x + p.w - 18, p.y + 24, 20, "#fff1d0", "right");
    }
    return panels;
  }

  // ---------- the boards (top) ----------
  function maxStack(fish) {
    const c = new Map(); let m = 0;
    for (const f of fish) { const b = Math.round(f.len / 2.5); const k = (c.get(b) || 0) + 1; c.set(b, k); m = Math.max(m, k); }
    return m;
  }
  function stackPositions(box, fish) {
    const bins = new Map(), out = new Map();
    const small = st.act === 4;
    const base = stripTop(box) - 3, avail = base - box.y - (small ? 2 : 26);
    const step = small ? 0 : Math.min(34, avail / Math.max(4, maxStack(fish)));
    const w = small ? 34 : Math.min(72, step * 2.4);
    for (const f of [...fish].sort((a, b) => a.len - b.len)) {
      const b = Math.round(f.len / 2.5);
      const k = bins.get(b) || 0; bins.set(b, k + 1);
      out.set(f, { x: lenX(box, f.len), y: small ? box.y + (base - box.y) / 2 + 1 : base - step * (k + 0.5) });
    }
    return { pos: out, w };
  }
  function drawPopulationShadow(box, waterKey) {
    // The whole harbor's lengths, as a faint histogram burned into the board behind the catch.
    const w = WATERS[waterKey], bins = new Array(MAXLEN / 2.5 + 1).fill(0);
    for (const f of w.fish) bins[Math.round(f.len / 2.5)]++;
    const mx = Math.max(...bins), bw = lenX(box, 2.5) - lenX(box, 0), base = stripTop(box) - 2;
    ctx.fillStyle = "rgba(60,32,10,.22)";
    bins.forEach((c, i) => { const h = (c / mx) * (base - box.y - 30); ctx.fillRect(lenX(box, i * 2.5) - bw / 2, base - h, bw - 1, h); });
    const x = lenX(box, w.trueMean);
    ctx.strokeStyle = "rgba(50,25,6,.8)"; ctx.setLineDash([7, 5]); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x, box.y + 10); ctx.lineTo(x, base); ctx.stroke(); ctx.setLineDash([]);
    engrave("true mean", x + 7, box.y + 18, 15, "left", "italic");
  }
  const flightState = (now) => {
    const landed = new Set(), flying = new Set();
    for (const fl of st.flights) (now >= fl.t0 + fl.dur ? landed : flying).add(fl.f);
    return { landed, flying };
  };
  function drawBoards(now) {
    const boxes = boardRows(), small = st.act === 4;
    const { flying } = flightState(now);
    st.rows.forEach((row, ri) => {
      const box = boxes[ri]; if (!box) return;
      drawPlanks(box);
      drawScale(box, small);
      if (st.drain && st.act === 1) drawPopulationShadow(box, st.water);
      const { pos, w } = stackPositions(box, row.fish);
      for (const f of row.fish) {
        if (flying.has(f)) continue;
        const p = pos.get(f);
        drawFish(p.x, p.y, w, f.monster ? "#ff7a4a" : row.color, 1);
      }
      if (row.fish.length && row.fish.every((f) => !flying.has(f))) wedge(lenX(box, S.mean(row.fish.map((f) => f.len))), stripTop(box) + 2, small ? 8 : 13);
      if (small) {
        ctx.fillStyle = row.color; ctx.beginPath(); ctx.arc(box.x + 42, box.y + box.h / 2 - 2, 6, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(40,22,6,.8)"; ctx.lineWidth = 1; ctx.stroke();
        engrave(row.label, box.x + 54, box.y + box.h / 2 - 2, 16, "left", "italic bold");
      } else {
        ctx.fillStyle = row.color; ctx.beginPath(); ctx.arc(box.x + box.w * 0.05, box.y + 34, 7, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(40,22,6,.8)"; ctx.lineWidth = 1.2; ctx.stroke();
        engrave(row.label, box.x + box.w * 0.05 + 14, box.y + 34, 19, "left", "italic");
        wedge(box.x + box.w - 196, box.y + 40, 9);
        engrave("mean of the catch", box.x + box.w - 184, box.y + 33, 15, "left", "italic");
      }
    });
    if (!st.rows.length) {      // before the first cast: the empty boards, waiting
      boxes.forEach((box) => { drawPlanks(box); drawScale(box, small); });
    }
    return st.flights.every((fl) => now >= fl.t0 + fl.dur);
  }

  // ---------- the net and the fish in flight ----------
  const RISE = 650;
  function netAnchor(net, panels) {
    const row = st.rows[net.ri]; if (!row) return null;
    const key = row.water || (row.fish[0] && row.fish[0].water) || panels[0].key;
    const p = panels.find((q) => q.key === key) || panels[0];
    const same = st.rows.map((r, i) => i).filter((i) => (st.rows[i].water || (st.rows[i].fish[0] || {}).water) === key);
    const idx = same.indexOf(net.ri), n = same.length;
    return { x: p.x + p.w * (n > 1 ? 0.3 + (0.4 * idx) / (n - 1) : 0.5) };
  }
  function netY(net, now) {
    const t = Math.min(1, Math.max(0, (now - net.t0) / RISE)), e = 1 - Math.pow(1 - t, 3);
    return LH + 120 + (EDGE + 30 - (LH + 120)) * e;
  }
  function drawNets(now, panels) {
    for (const net of st.nets || []) {
      if (now < net.t0) continue;
      const end = net.t0 + RISE + net.n * 45 + 500, a = Math.max(0, Math.min(1, (end - now) / 300));
      if (a <= 0) continue;
      const anc = netAnchor(net, panels); if (!anc) continue;
      const y = netY(net, now), img = IMG.net, w = 170, h = (w * img.height) / img.width;
      ctx.save();
      ctx.globalAlpha = a * (y > WATER_TOP + 40 ? 0.7 : 1);
      ctx.shadowColor = "rgba(0,0,0,.45)"; ctx.shadowBlur = 10; ctx.shadowOffsetY = 8;
      ctx.translate(anc.x, y); ctx.rotate(Math.sin(now / 260 + net.ri) * 0.05);
      ctx.drawImage(img, -w / 2, -h / 2, w, h);
      ctx.restore();
    }
  }
  function drawFlights(now, panels) {
    const boxes = boardRows();
    for (const fl of st.flights) {
      const t = (now - fl.t0) / fl.dur;
      if (t < 0 || t >= 1) continue;
      const box = boxes[fl.ri]; if (!box) continue;
      const sp = stackPositions(box, st.rows[fl.ri].fish), to = sp.pos.get(fl.f);
      let from;
      if (fl.fromTop) from = { x: to.x, y: -60 };
      else if (fl.fromNet) { const net = st.nets.find((n) => n.ri === fl.ri), anc = netAnchor(net, panels); from = { x: anc.x, y: netY(net, now) + 20 }; }
      else from = fishWaterPos(fl.f, panels);
      const e = t * t * (3 - 2 * t);
      const x = from.x + (to.x - from.x) * e, y = from.y + (to.y - from.y) * e - Math.sin(Math.PI * e) * 90;
      drawFish(x, y, Math.max(sp.w, 46), fl.f.monster ? "#ff7a4a" : st.rows[fl.ri].color, 1);
    }
  }

  // ---------- the bronze dial: log-p needle, red inlay below 0.05 ----------
  const gaugeAnim = {};
  function dial(id, cx, top, W, p, title, okWord, sigWord, textY, off) {
    const d = IMG.dial, H = (W * d.height) / d.width, x0 = cx - W / 2;
    const px = x0 + G.dial.pivot[0] * W, py = top + G.dial.pivot[1] * H;
    const bx = x0 + G.dial.band_centre[0] * W, by = top + G.dial.band_centre[1] * H;
    const r0 = G.dial.band_r[0] * W, r1 = G.dial.band_r[1] * W, rm = (r0 + r1) / 2;
    ctx.save(); ctx.shadowColor = "rgba(20,10,0,.55)"; ctx.shadowBlur = 16; ctx.shadowOffsetY = 7;
    ctx.drawImage(d, x0, top, W, H); ctx.restore();
    const ang = (v) => Math.PI + (v / -3) * Math.PI;      // p = 1 at the left, 0.001 at the right
    const a05 = ang(Math.log10(0.05));
    ctx.lineWidth = (r1 - r0) * 0.95;                     // re-inlay the band: plain patina, then red past 0.05
    ctx.strokeStyle = "rgba(84,58,26,.9)"; ctx.beginPath(); ctx.arc(bx, by, rm, Math.PI, a05); ctx.stroke();
    ctx.strokeStyle = "rgba(160,36,18,.6)"; ctx.beginPath(); ctx.arc(bx, by, rm, a05, 2 * Math.PI); ctx.stroke();
    const rt = r0 - (by - py) - W * 0.012, tl = W * 0.045;
    for (const v of [1, 0.5, 0.1, 0.05, 0.01, 0.001]) {
      const a = ang(Math.log10(v)), c = Math.cos(a), s = Math.sin(a);
      engraveLine(px + c * (rt - tl), py + s * (rt - tl), px + c * rt, py + s * rt, v === 0.05 ? 3 : 2);
      engrave(String(v), px + c * (rt - tl - W * 0.05), py + s * (rt - tl - W * 0.05), Math.round(W * 0.042), "center", "bold");
    }
    const target = p == null ? 0 : Math.max(-3, Math.min(0, Math.log10(Math.max(p, 1e-6))));
    gaugeAnim[id] = (gaugeAnim[id] ?? 0) + (target - (gaugeAnim[id] ?? 0)) * 0.12;
    if (p != null) {
      const nd = IMG.needle, nl = rt - tl * 0.3, Wn = nl / (1 - G.needle.ring[0]), Hn = (Wn * nd.height) / nd.width;
      ctx.save(); ctx.translate(px, py); ctx.rotate(ang(gaugeAnim[id]));
      ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 5; ctx.shadowOffsetY = 3;
      ctx.drawImage(nd, -G.needle.ring[0] * Wn, -Hn / 2, Wn, Hn);
      ctx.restore();
    }
    // the reading, lettered on a small board below
    const ty = textY ?? top + H + 10, ph = st.numbers ? 96 : 72;
    placard(cx - W * 0.46, ty, W * 0.92, ph);
    if (off) {      // the road not taken: a dark film over the dial and its board, still readable underneath
      ctx.save(); ctx.fillStyle = "rgba(25,16,8,.5)";
      ctx.beginPath(); ctx.arc(bx, by, r1 * 1.035, Math.PI, 2 * Math.PI); ctx.lineTo(x0 + W, top + H); ctx.lineTo(x0, top + H); ctx.closePath(); ctx.fill();
      ctx.fillRect(cx - W * 0.46, ty, W * 0.92, ph);
      ctx.restore();
    }
    engrave(title, cx, ty + 22, Math.round(Math.max(16, W * 0.05)), "center", "italic");
    if (p != null) {
      const sig = p < 0.05;
      engrave(sig ? sigWord : okWord, cx, ty + 50, Math.round(Math.max(17, W * 0.055)), "center", "bold", sig ? "rgba(140,30,12,.95)" : "rgba(28,70,40,.95)");
      if (st.numbers) engrave("p = " + fmtP(p), cx, ty + 76, Math.round(Math.max(15, W * 0.045)), "center");
    }
  }
  // A terracotta oil lamp, lit or not (act 3's normality lamps, act 4's 45 pair lamps).
  function lampSprite(cx, cy, w, on) {
    const im = IMG.lamp, h = (w * im.height) / im.width;
    ctx.save(); ctx.shadowColor = "rgba(20,10,0,.45)"; ctx.shadowBlur = 5; ctx.shadowOffsetY = 3;
    ctx.drawImage(im, cx - w / 2, cy - h / 2, w, h); ctx.restore();
    if (on) {
      const fx = cx + w * 0.4, fy = cy - h * 0.05, r = w * 0.9;
      const g = ctx.createRadialGradient(fx, fy, 1, fx, fy, r);
      g.addColorStop(0, "rgba(255,246,210,.95)"); g.addColorStop(0.25, "rgba(255,190,90,.75)"); g.addColorStop(1, "rgba(255,140,40,0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(fx, fy, r, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#fff4cf"; ctx.beginPath(); ctx.ellipse(fx, fy - w * 0.08, w * 0.07, w * 0.15, 0, 0, Math.PI * 2); ctx.fill();
    }
  }

  function drawSide(ready) {
    const r = st.result;
    if (st.act === 1) {
      const box = { x: 40, y: 300, w: 1060, h: 128 };
      drawPlanks(box);
      engrave("the mean of every cast so far, one pebble each", box.x + box.w * 0.05, box.y + 18, 16, "left", "italic");
      const bins = new Map(), base = box.y + box.h - 12;
      for (const m of st.trail) { const b = Math.round(m / 0.5); bins.set(b, (bins.get(b) || 0) + 1); }
      for (const [b, c] of bins) for (let k = 0; k < c; k++) {
        const x = lenX(box, b * 0.5), y = base - k * 8;
        const g = ctx.createRadialGradient(x - 1.5, y - 1.5, 0.5, x, y, 4.5);
        g.addColorStop(0, "#c9c2b6"); g.addColorStop(1, "#4a4640");
        ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(x, y, 4.6, 3.8, 0, 0, Math.PI * 2); ctx.fill();
      }
      if (st.drain) {
        const x = lenX(box, WATERS[st.water].trueMean);
        ctx.strokeStyle = "rgba(50,25,6,.8)"; ctx.setLineDash([7, 5]); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x, box.y + 30); ctx.lineTo(x, box.y + box.h - 4); ctx.stroke(); ctx.setLineDash([]);
      }
      placard(1150, 40, 340, st.drain ? 260 : 160);
      if (r && ready) {
        engrave("this cast", 1320, 72, 18, "center", "italic");
        engrave(`mean ${r.mean.toFixed(1)} cm`, 1320, 108, 30, "center", "bold");
        engrave(`${st.n} fish`, 1320, 142, 16, "center", "italic");
        if (st.drain) { engrave("the whole harbor", 1320, 200, 18, "center", "italic"); engrave(`mean ${WATERS[st.water].trueMean.toFixed(1)} cm`, 1320, 236, 30, "center", "bold"); }
      } else engrave("cast the net", 1320, 120, 20, "center", "italic");
    } else if (st.act === 2) {
      dial("p2", 1316, 30, 400, ready && r ? r.p : null, "Welch's t-test", "no difference found", "“significant”!");
      engrave("both nets: the same water", 1316, 380, 17, "center", "italic", "rgba(40,22,6,.9)");
    } else if (st.act === 3 && r) {
      const boxes = boardRows();
      [r.shA, r.shB].forEach((sh, i) => {
        const bx = boxes[i];
        lampSprite(bx.x + bx.w + 66, bx.y + 44, 62, ready && sh.p < 0.05);
        placard(bx.x + bx.w + 16, bx.y + 76, 100, 34);
        engrave(ready ? (sh.p < 0.05 ? "not normal" : "normal?") : "", bx.x + bx.w + 66, bx.y + 93, 15, "center", "italic bold",
          ready && sh.p < 0.05 ? "rgba(140,30,12,.95)" : "rgba(40,22,6,.93)");
      });
      if (ready) {
        const park = r.road === "parametric";
        dial("w4", 1390, 6, 250, r.welch.p, "Welch's t-test", "no difference", "different", 146, !park);
        dial("x4", 1390, 252, 250, r.wilcox.p, "Wilcox test", "no difference", "different", 392, park);
      }
      drawRankLine(ready);
    } else if (st.act === 4 && r) {
      drawTriangle(ready);
    }
  }
  // Act 3: both catches nose to tail by size, coloured by net, rank tags, mean-rank wedges.
  function drawRankLine(ready) {
    const box = { x: 40, y: 312, w: 1060, h: 140 };
    drawPlanks(box);
    engrave("the rank road: every fish in one line, smallest to largest", box.x + box.w * 0.05, box.y + 18, 15, "left", "italic");
    if (!ready || st.rows.length < 2) return;
    const all = [];
    st.rows.forEach((row, ri) => row.fish.forEach((f) => all.push({ f, ri })));
    all.sort((a, b) => a.f.len - b.f.len);
    const x0 = box.x + box.w * 0.04, w = box.w * 0.93, N = all.length, dx = w / N;
    const sums = [0, 0], cnt = [0, 0];
    all.forEach((o, k) => {
      const x = x0 + dx * (k + 0.5);
      drawFish(x, box.y + 62, Math.min(dx * 1.1, 10 + o.f.len * 0.6), o.f.monster ? "#ff7a4a" : st.rows[o.ri].color, 1);
      engrave(String(k + 1), x, box.y + 92, 14, "center", "bold");
      sums[o.ri] += k + 1; cnt[o.ri]++;
    });
    [0, 1].forEach((ri) => {
      const x = x0 + dx * (sums[ri] / cnt[ri] - 0.5);
      wedge(x, box.y + 112, 10, st.rows[ri].color);
      engrave("mean rank", x, box.y + 126, 13, "center", "italic");
    });
  }
  // Act 4: 45 pair lamps in a triangle, lit when p < 0.05 (raw, or corrected with the lever).
  function drawTriangle(ready) {
    const r = st.result, x0 = 950, y0 = 18, cell = 44;
    const head = st.corrected ? (r.road === "parametric" ? "Tukey (corrected)" : "Dunn, Holm (corrected)") : (r.road === "parametric" ? "every pair, no correction" : "every pair (ranks), no correction");
    placard(x0 + 150, y0 - 6, 330, 40);
    engrave(head, x0 + 315, y0 + 14, 18, "center", "bold", st.corrected ? "rgba(28,70,40,.95)" : "rgba(140,30,12,.95)");
    for (let b = 0; b < 9; b++) {           // columns are boats 1-9, rows boats 2-10
      engrave(String(b + 1), x0 + 26 + b * cell + cell / 2, y0 + 50, 15, "center", "bold");
      engrave(String(b + 2), x0 + 12, y0 + 70 + b * cell + cell / 2, 15, "center", "bold");
    }
    const ps = st.corrected ? r.cor : r.raw;
    r.pairs.forEach(([i, j], k) => {
      lampSprite(x0 + 26 + i * cell + cell / 2, y0 + 70 + (j - 1) * cell + cell / 2, 40, ready && ps[k] < 0.05);
    });
    // the lever: upright = no correction, thrown = corrected
    const lv = IMG.lever, lw = 34, lh = (lw * lv.height) / lv.width;
    ctx.save(); ctx.translate(LEVER.x, LEVER.y); ctx.rotate(st.corrected ? 0.5 : -0.12);
    ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 8; ctx.shadowOffsetY = 5;
    ctx.drawImage(lv, -lw / 2, -lh + 20, lw, lh); ctx.restore();
    if (ready) {
      const lit = ps.filter((p) => p < 0.05).length;
      placard(1236, y0 + 50, 250, 80);
      engrave(`${lit} of 45 pairs lit`, 1361, y0 + 78, 22, "center", "bold");
      engrave(r.road === "parametric" ? "parametric road: Tukey" : "rank road: Dunn", 1361, y0 + 108, 15, "center", "italic");
    }
    placard(LEVER.x - 62, LEVER.y + 18, 124, 32);
    engrave(st.corrected ? "corrected" : "no correction", LEVER.x, LEVER.y + 34, 15, "center", "italic bold",
      st.corrected ? "rgba(28,70,40,.95)" : "rgba(140,30,12,.95)");
  }

  // The act 4 lever stands on the paving between the lamps and the count; click it to throw it.
  const LEVER = { x: 1345, y: 322 };     // above the triangle's diagonal, clear of the lamps and the amphora
  const onLever = (p) => Math.abs(p.x - LEVER.x) < 50 && p.y > LEVER.y - 170 && p.y < LEVER.y + 45;
  let leverBtn = null;
  function toggleLever() {
    st.corrected = !st.corrected;
    if (leverBtn) leverBtn.textContent = st.corrected ? "Lever: corrected" : "Lever: no correction";
  }
  cv.addEventListener("click", (ev) => { if (st.act === 4 && onLever(toBoard(ev))) toggleLever(); });
  cv.addEventListener("mousemove", (ev) => { cv.style.cursor = st.act === 4 && onLever(toBoard(ev)) ? "pointer" : ""; });

  // ---------- frame loop ----------
  function frame(now) {
    if (dead) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "#0d0a07"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.setTransform(scale, 0, 0, scale, ox, oy);
    if (!artReady) {
      label(artFailed ? "The fish board could not be loaded." : "loading the harbor…", LW / 2, LH / 2, 28, "#e8d6a8", "center", "italic");
      if (!artFailed) raf = requestAnimationFrame(frame);
      return;
    }
    ctx.drawImage(IMG.board, 0, G.base.crop_y_px, LW, LH, 0, 0, LW, LH);
    const panels = drawWater(now);
    const ready = drawBoards(now);
    drawSide(ready);
    drawNets(now, panels);
    drawFlights(now, panels);
    raf = requestAnimationFrame(frame);
  }

  // ---------- controls ----------
  const CAPTIONS = {
    1: "The harbor holds every fish: that is the population. A net brings up a sample, and its mean is our best guess at the harbor's mean. Cast again: every sample, and every sample mean, comes out a little different.",
    2: "Two nets in the same water, so the null hypothesis is true: there is no difference to find. The needle shows the Welch t-test's p-value. Keep casting, and about one cast in twenty still lands in the red.",
    3: "Two waters. Check each catch for normality, then take the matching road. Welch's t-test compares the means against their spread; the Wilcox test lines every fish up by size and asks whether one net's fish tend to run larger.",
    4: "Ten boats fishing the same water, so every difference is chance. Compare all 45 pairs with no correction and a couple of lamps light on most casts. Pull the lever to correct for the number of comparisons.",
  };
  function waterSelect(val, onChange, keys = Object.keys(WATERS)) {
    const s = document.createElement("select");
    for (const k of keys) { const o = document.createElement("option"); o.value = k; o.textContent = WATERS[k].name; if (k === val) o.selected = true; s.appendChild(o); }
    s.onchange = () => { onChange(s.value); resetAct(); };
    return s;
  }
  function btn(text, fn, primary) { const b = document.createElement("button"); b.type = "button"; b.textContent = text; if (primary) b.className = "primary"; b.onclick = fn; return b; }
  function labelled(t, el) { const l = document.createElement("label"); l.textContent = t + " "; l.appendChild(el); return l; }
  function check(t, val, fn) { const c = document.createElement("input"); c.type = "checkbox"; c.checked = val; c.onchange = () => fn(c.checked); return labelled(t, c); }
  function castMany(k) { for (let i = 0; i < k - 1; i++) cast(false); cast(true); }
  let tallyEl = null;
  function buildControls() {
    ctl.innerHTML = ""; leverBtn = null;
    ctl.appendChild(btn("Cast the net", () => cast(true), true));
    ctl.appendChild(btn("Cast 20 times", () => castMany(20)));
    const nSel = document.createElement("select");
    const sizes = st.act === 4 ? [5, 8, 15] : [5, 8, 15, 30];
    if (!sizes.includes(st.n)) st.n = 8;
    for (const n of sizes) { const o = document.createElement("option"); o.value = n; o.textContent = n + " fish"; if (n === st.n) o.selected = true; nSel.appendChild(o); }
    nSel.onchange = () => { st.n = Number(nSel.value); remember(); resetAct(); };
    ctl.appendChild(labelled("Net size", nSel));
    if (st.act === 1 || st.act === 2) ctl.appendChild(labelled("Water", waterSelect(st.water, (v) => { st.water = v; })));
    if (st.act === 1) ctl.appendChild(check("Drain the harbor (show every fish)", st.drain, (v) => { st.drain = v; }));
    if (st.act === 3) {
      ctl.appendChild(labelled("Net A", waterSelect(st.waterA, (v) => { st.waterA = v; })));
      ctl.appendChild(labelled("Net B", waterSelect(st.waterB, (v) => { st.waterB = v; })));
      ctl.appendChild(btn("Throw in a monster", throwMonster));
    }
    if (st.act === 4) {
      ctl.appendChild(labelled("Water", waterSelect(st.water5, (v) => { st.water5 = v; st.road5 = WATERS[v].kind === "normal" ? "parametric" : "rank"; buildControls(); }, ["open", "lake"])));
      const road = document.createElement("select");
      for (const [k, t] of [["parametric", "parametric road (Tukey)"], ["rank", "rank road (Dunn)"]]) { const o = document.createElement("option"); o.value = k; o.textContent = t; if (k === st.road5) o.selected = true; road.appendChild(o); }
      road.onchange = () => { st.road5 = road.value; resetAct(); };
      ctl.appendChild(labelled("Road", road));
      ctl.appendChild(check("Boat 1 fishes elsewhere", st.elsewhere, (v) => { st.elsewhere = v; resetAct(); }));
      leverBtn = btn(st.corrected ? "Lever: corrected" : "Lever: no correction", toggleLever);
      ctl.appendChild(leverBtn);
    }
    ctl.appendChild(btn("Clear the tally", () => { st.tally[st.act] = {}; st.trail = []; updateTally(); }));
    ctl.appendChild(check("p-values", st.numbers, (v) => { st.numbers = v; remember(); }));
    tallyEl = document.createElement("span"); tallyEl.className = "fishboardtally"; ctl.appendChild(tallyEl);
    updateTally();
  }
  function pct(a, b) { return b ? Math.round((100 * a) / b) + "%" : "-"; }
  function updateTally() {
    const el = tallyEl; if (!el) return;
    const T = st.tally[st.act] || {}, h = T.hauls || 0;
    if (st.act === 1) el.innerHTML = `casts <b>${h}</b>`;
    if (st.act === 2) el.innerHTML = `casts <b>${h}</b> · in the red <b>${T.sig || 0}</b> (${pct(T.sig || 0, h)})`;
    if (st.act === 3) el.innerHTML = `casts <b>${h}</b>`;
    if (st.act === 4) el.innerHTML = `casts <b>${h}</b> · any lamp lit: no correction <b>${pct(T.anyRaw || 0, h)}</b>, corrected <b>${pct(T.anyCor || 0, h)}</b> · lamps per cast <b>${h ? ((T.litRaw || 0) / h).toFixed(1) : "-"}</b> vs <b>${h ? ((T.litCor || 0) / h).toFixed(1) : "-"}</b>`;
  }
  function resetAct() {
    releaseAll(); st.rows = []; st.flights = []; st.nets = []; st.result = null; st.trail = [];
    st.tally[st.act] = {};
    updateTally();
  }
  function setAct(a) {
    st.act = Math.min(4, Math.max(1, Number(a) || 1));
    tabs.querySelectorAll(".fishboardtab").forEach((t) => t.classList.toggle("on", Number(t.dataset.act) === st.act));
    caption.textContent = CAPTIONS[st.act];
    resetAct();
    buildControls();
    remember();
  }

  const ready = (async () => {
    const imgs = await Promise.all(SPRITES.map((k) => loadImg(artPaths[k])));
    if (dead) return;
    const missing = SPRITES.filter((k, i) => !imgs[i]);
    if (missing.length) { artFailed = true; console.error("fish_board: art did not load:", missing.join(", ")); return; }
    SPRITES.forEach((k, i) => { IMG[k] = imgs[i]; });
    buildDerived();
    artReady = true;
  })();

  setAct(st.act);
  resize();

  const api = {
    ready, seed,
    setAct, cast: () => cast(true), castMany, throwMonster, toggleLever,
    act: () => st.act,
    state: () => st,
    isSettled: () => flightState(performance.now()).flying.size === 0,
    // client coordinates of the act 4 lever's handle, for a real click in tests
    leverClient: () => { const r = cv.getBoundingClientRect();
      return { x: r.left + (LEVER.x * scale + ox) / dpr, y: r.top + ((LEVER.y - 80) * scale + oy) / dpr }; },
    destroy() {
      if (dead) return;
      dead = true; cancelAnimationFrame(raf);
      if (ro) ro.disconnect(); else removeEventListener("resize", resize);
    },
  };
  cv.fishBoard = api;          // for tests and the console; harmless to students
  raf = requestAnimationFrame(frame);
  return api;
}
