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
//   3 Two waters (Welch vs Wilcox, picked by Shapiro)
//   4 Four waters: four fixed waters, one boat each (three alike, one different and not normal), a small
//     p dial for each of the six pairs, and the TEST chosen from four (Welch or Wilcox on each pair with no
//     correction, Games-Howell or Dunn corrected); switching test re-reads the same catch. Replaced the
//     ten-boats-one-water act 2026-11-03; simplified 2026-11-04 (Lucas: fixed waters, choose the test,
//     dials like the earlier acts, drop every control that does not change anything).
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
//   fb.setAct(n); fb.cast(); fb.castMany(k); fb.throwMonster(); fb.setTest(key); fb.state();
//   fb.ready (Promise); fb.destroy().  (The lever sprite is still required art but no act draws it now.)
// The canvas carries the API as `canvas.fishBoard` for tests.
import "./fish_stats.js?v=154";     // window.FishStats: the board's tests (Welch, Shapiro, Wilcox, Games-Howell, Dunn), pinned to R

const loadImg = (src) => new Promise((res) => {
  if (!src) return res(null);
  const im = new Image();
  im.onload = () => res(im); im.onerror = () => res(null); im.src = src;
});
const SPRITES = ["board", "plank", "fish", "dial", "needle", "net", "lamp", "lever"];
const ACT_NAMES = ["Population and sample", "Same water, two nets", "Two waters", "Four waters"];
// Act 4's waters, fixed (Lucas, 2026-11-04): three alike, so their three pairs can only differ by chance, and
// one lake water, both different and not normal, so the Shapiro result points at the rank tests.
// Simulated at 8 fish a net: some same-water dial in the red on ~12% of casts with Welch or Wilcox per pair,
// ~2% with Games-Howell, ~0% with Dunn; the lake's pairs found ~50-60% uncorrected, ~35-40% corrected.
const ACT4_WATERS = ["open", "open", "open", "lake"];
const TESTS4 = {
  welch:  { name: "Welch t-test on each pair (no correction)", short: "Welch t-test, each pair", corrected: false },
  gh:     { name: "Games-Howell test (corrected)",             short: "Games-Howell (corrected)", corrected: true },
  wilcox: { name: "Wilcox test on each pair (no correction)",  short: "Wilcox test, each pair", corrected: false },
  dunn:   { name: "Dunn test (corrected)",                     short: "Dunn, Holm (corrected)", corrected: true },
};

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

  // ---- DOM: act tabs, then the canvas with the act's lesson beside it (in the space the letterbox used to
  // waste; below it on a narrow screen), then the controls ----
  const wrap = document.createElement("div"); wrap.className = "fishboard";
  const tabs = document.createElement("div"); tabs.className = "fishboardtabs";
  const stage = document.createElement("div"); stage.className = "fishboardstage";
  const lesson = document.createElement("div"); lesson.className = "fishboardlesson";
  const cv = document.createElement("canvas"); cv.className = "fishboardcanvas";
  cv.style.aspectRatio = `${G.imageW} / ${G.imageH}`;
  const ctl = document.createElement("div"); ctl.className = "fishboardcontrols";
  ACT_NAMES.forEach((name, i) => {
    const t = document.createElement("button"); t.type = "button"; t.className = "fishboardtab"; t.dataset.act = String(i + 1);
    t.textContent = `${i + 1} · ${name}`; t.onclick = () => setAct(i + 1); tabs.appendChild(t);
  });
  stage.append(cv, lesson);
  wrap.append(tabs, stage, ctl);
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
  const BASE = Object.keys(WATERS);            // the kinds of water a player can choose
  function stock(w, key) {
    w.fish = [];
    for (let i = 0; i < POP; i++) {
      let len;
      do { len = w.draw(); } while (len < MINLEN || len > MAXLEN - 2);
      w.fish.push({ len, x: R(), y: 0.08 + 0.84 * R(), v: (0.004 + 0.006 * R()) * (R() < 0.5 ? -1 : 1),
        ph: R() * 6.28, caught: false, water: key });
    }
    w.trueMean = S.mean(w.fish.map((f) => f.len));
  }
  for (const key of BASE) stock(WATERS[key], key);
  // Act 4's waters are their own populations ("w0".."w3"), each stocked from its kind: two waters of the
  // same kind hold different fish from the same distribution, which is exactly the null hypothesis.
  const slotKey = (i) => "w" + i;
  function stockSlots() {
    for (const k of Object.keys(WATERS)) if (!BASE.includes(k)) delete WATERS[k];
    st.slots.forEach((kind, i) => {
      const b = WATERS[kind], key = slotKey(i);
      WATERS[key] = { name: b.name, kind: b.kind, tint: b.tint, draw: b.draw, base: kind };
      stock(WATERS[key], key);
    });
  }

  // ---------- state ----------
  const st = {
    act: Math.min(4, Math.max(1, Number(saved.act) || 1)),
    n: Number(saved.n) || 8,
    numbers: saved.numbers !== false,
    water: "open", waterA: "open", waterB: "mouth",
    slots: [...ACT4_WATERS], test4: TESTS4[saved.test4] ? saved.test4 : "welch",
    drain: false,
    rows: [],            // [{ fish: [fishObj], color, label }]
    nets: [],            // nets rising out of the water: [{ ri, t0, n }]
    flights: [],         // animation of caught fish
    trail: [],           // act 1: means of every haul so far
    result: null,        // the act's latest test result
    tally: {},
    monster: false,
  };
  stockSlots();
  const remember = () => opts.onPegs && opts.onPegs({ act: st.act, n: st.n, numbers: st.numbers, test4: st.test4 });
  const C_A = "#e0a83a", C_B = "#4fc0b4";
  const BOAT_COLS = ["#e0a83a", "#4fc0b4", "#d47a6a", "#9fb85a"];

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
      case 4: {     // one board per water, filling the paving above the quay edge
        const k = st.slots.length, gap = 8, top = 10, h = (EDGE - 14 - top - gap * (k - 1)) / k, out = [];
        for (let i = 0; i < k; i++) out.push({ x: 40, y: top + i * (h + gap), w: 880, h });
        return out;
      }
    }
    return [];
  }
  const STRIP = (box) => Math.max(13, Math.min(28, box.h * 0.13));
  const stripTop = (box) => box.y + box.h - STRIP(box) - 5;
  const compact = (box) => box.h < 100;          // a short board: one line of small fish, no numbers on its scale
  const lenX = (box, len) => { const x0 = box.x + box.w * (st.act === 4 ? 0.15 : 0.04), x1 = box.x + box.w - 16; return x0 + (len / MAXLEN) * (x1 - x0); };

  // ---------- casting ----------
  function watersForAct() {
    if (st.act === 3) return [st.waterA, st.waterB];
    if (st.act === 4) return st.slots.map((_, i) => slotKey(i));
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
      st.slots.forEach((kind, i) => rows.push({ fish: netFrom(slotKey(i), n), color: BOAT_COLS[i],
        label: "Water " + (i + 1), sub: WATERS[kind].name, water: slotKey(i), kind }));
    }
    st.rows = rows;
    compute();
    st.flights = []; st.nets = [];
    if (animate) {
      // Each net rises out of its water, then its fish fly up onto its board.
      const now = performance.now(), useNets = true;
      rows.forEach((row, ri) => {
        let t0 = now;
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
      // every test is scored on every cast, so switching test shows its own record at once
      const r = st.result;
      for (const key of Object.keys(TESTS4)) {
        const ps = r.ps[key], U = (T[key] = T[key] || { flukes: 0, found: 0, realPairs: 0 });
        if (r.same.some((x, q) => x && ps[q] < 0.05)) U.flukes++;
        U.realPairs += r.same.filter((x) => !x).length;
        U.found += r.same.filter((x, q) => !x && ps[q] < 0.05).length;
      }
    }
    updateTally();
  }
  function compute3(L) {
    const shA = S.shapiro(L[0]), shB = S.shapiro(L[1]);
    const road = shA.p < 0.05 || shB.p < 0.05 ? "rank" : "parametric";
    return { shA, shB, road, welch: S.welch(L[0], L[1]), wilcox: S.wilcox(L[0], L[1]) };
  }
  function compute4(L) {
    const gh = S.gamesHowell(L), welch = S.pairwiseWelch(L), dunn = S.dunn(L);
    const pairs = gh.map((r) => [r.i, r.j]);
    const ps = {
      welch: welch.map((r) => r.p), gh: gh.map((r) => r.p),
      wilcox: pairs.map(([i, j]) => S.wilcox(L[i], L[j]).p), dunn: dunn.map((r) => r.pAdj),
    };
    const same = pairs.map(([i, j]) => st.slots[i] === st.slots[j]);    // the truth: same kind of water
    return { pairs, same, ps, sh: L.map((x) => S.shapiro(x)) };
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
    if (st.act === 4) {           // one panel per water, a jetty between each
      const k = ws.length, gap = 60, w = (WATER_BOX.w - gap * (k - 1)) / k;
      return ws.map((key, i) => ({ key, x: i * (w + gap), y: WATER_BOX.y, w, h: WATER_BOX.h, n: i + 1, color: BOAT_COLS[i] }));
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
    for (let i = 0; i + 1 < panels.length; i++) jetty(panels[i].x + panels[i].w, panels[i + 1].x);
    for (const p of panels) {
      const w = WATERS[p.key];
      ctx.save(); ctx.beginPath(); ctx.rect(p.x, p.y, p.w, p.h); ctx.clip();
      if (w.kind === "skewed") { ctx.fillStyle = "rgba(38,92,52,.38)"; ctx.fillRect(p.x, p.y, p.w, p.h); }   // the lake's greener water
      const shrink = p.w < 330 ? 0.55 : p.w < 500 ? 0.7 : 1;
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
      if (p.n) {        // act 4: the water's number in its boat colour, then what lives in it
        ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x + 24, p.y + 24, 9, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(0,0,0,.6)"; ctx.lineWidth = 1.2; ctx.stroke();
        label(String(p.n), p.x + 24, p.y + 25, 14, "#1a0f05", "center", "bold");
        label(w.name, p.x + 40, p.y + 24, 20, "#fff1d0", "left", "italic");
      } else label(w.name, p.x + 18, p.y + 24, 24, "#fff1d0", "left", "italic");
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
    const small = compact(box);
    const base = stripTop(box) - 3, avail = base - box.y - (small ? 2 : st.act === 4 ? 6 : 26);
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
    const boxes = boardRows();
    const { flying } = flightState(now);
    st.rows.forEach((row, ri) => {
      const box = boxes[ri]; if (!box) return;
      const small = compact(box);
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
      if (st.act === 4) {      // the water's number and kind at the left end of its board
        const cy = box.y + Math.min(box.h / 2 - 8, 34);
        ctx.fillStyle = row.color; ctx.beginPath(); ctx.arc(box.x + 22, cy, 7, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(40,22,6,.8)"; ctx.lineWidth = 1; ctx.stroke();
        engrave(row.label, box.x + 34, cy, 17, "left", "italic bold");
        engrave(row.sub, box.x + 16, cy + 22, 13, "left", "italic");
        const sh = st.result && st.result.sh && st.result.sh[ri];
        if (sh && row.fish.every((f) => !flying.has(f)))
          engrave(sh.p < 0.05 ? "not normal" : "normal?", box.x + 16, cy + 42, 13, "left", "bold",
            sh.p < 0.05 ? "rgba(140,30,12,.95)" : "rgba(28,70,40,.95)");
      } else if (small) {
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
      boxes.forEach((box, i) => {
        drawPlanks(box); drawScale(box, compact(box));
        if (st.act === 4) engrave("Water " + (i + 1), box.x + 34, box.y + Math.min(box.h / 2 - 8, 34), 17, "left", "italic bold");
      });
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
  // A terracotta oil lamp, lit or not (act 3's normality lamps, act 4's pair lamps).
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
      drawDials(ready);
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
  // Act 4: a small p dial for every pair of waters, read with the chosen test, titled with the truth
  // (same water or different), so a red dial over "same water" is visibly a fluke.
  function drawDials(ready) {
    const r = st.result, t = TESTS4[st.test4];
    placard(962, 4, 548, 32);
    engrave(t.name, 1236, 21, 17, "center", "bold", t.corrected ? "rgba(28,70,40,.95)" : "rgba(140,30,12,.95)");
    const W = 180, cols = [1040, 1236, 1432], tops = [42, 252];
    r.pairs.forEach(([i, j], q) => {
      const cx = cols[q % 3], top = tops[Math.floor(q / 3)], same = r.same[q];
      dial("p4_" + q, cx, top, W, ready ? r.ps[st.test4][q] : null,
        `${i + 1} & ${j + 1}: ${same ? "same" : "differ"}`, "no difference", "different", top + W * 0.539 + 6);
    });
  }

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
  // Each act's takeaway, in the book's own words (chapter 11, "comparing groups"), with the section it
  // belongs to (Lucas, 2026-11-04: short, the lesson rather than instructions, sharing the book's language).
  const LESSONS = {
    1: ["A sample is a subset of the population. Its mean is our estimate of the population's mean, and every new sample gives a slightly different one.",
      "definitions: populations and independent measurements"],
    2: ["The null hypothesis is that there is no difference between the distributions. Even when it is true, about 1 test in 20 gives p < 0.05 by chance alone.",
      "definitions: the null hypothesis, the p value"],
    3: ["Check each group with the Shapiro test first. Normal: use the t-test. Not normal: use the Wilcox test, which works on ranks, so an extreme value cannot distort it.",
      "test selection; two means"],
    4: ["Testing many pairs multiplies the chances of a false positive. The Games-Howell and Dunn tests correct the p values for the number of comparisons. Water 4 is not normal, so here it is Dunn.",
      "more than two means"],
  };
  function waterSelect(val, onChange, keys = BASE) {
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
    ctl.innerHTML = "";
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
      const tSel = document.createElement("select"); tSel.className = "fishboardtest";
      for (const [k, t] of Object.entries(TESTS4)) { const o = document.createElement("option"); o.value = k; o.textContent = t.name; if (k === st.test4) o.selected = true; tSel.appendChild(o); }
      tSel.onchange = () => setTest(tSel.value);
      ctl.appendChild(labelled("Test", tSel));
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
    if (st.act === 4) {
      const U = T[st.test4], t = TESTS4[st.test4];
      el.innerHTML = `casts <b>${h}</b>` + (U ? ` · ${t.short}: a same-water pair in the red on <b>${pct(U.flukes, h)}</b> of casts · real differences found <b>${pct(U.found, U.realPairs)}</b>` : "");
    }
  }
  // Act 4: choose the test. The catch stays; the dials and the tally re-read it with the new test.
  function setTest(key) {
    if (!TESTS4[key]) throw new Error("fish_board: setTest needs one of " + Object.keys(TESTS4).join("/"));
    st.test4 = key;
    const sel = ctl.querySelector("select.fishboardtest"); if (sel) sel.value = key;
    updateTally(); remember();
  }
  function resetAct() {
    releaseAll(); st.rows = []; st.flights = []; st.nets = []; st.result = null; st.trail = [];
    st.tally[st.act] = {};
    updateTally();
  }
  function setAct(a) {
    st.act = Math.min(4, Math.max(1, Number(a) || 1));
    tabs.querySelectorAll(".fishboardtab").forEach((t) => t.classList.toggle("on", Number(t.dataset.act) === st.act));
    const [text, where] = LESSONS[st.act];
    lesson.innerHTML = "";
    const h = document.createElement("div"); h.className = "fishboardlessonhead"; h.textContent = "Lesson";
    const t = document.createElement("p"); t.className = "fishboardlessontext"; t.textContent = text;
    const b = document.createElement("div"); b.className = "fishboardlessonbook"; b.textContent = "In the book: comparing groups, " + where;
    lesson.append(h, t, b);
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
    setAct, cast: () => cast(true), castMany, throwMonster,
    setTest,              // act 4: "welch" | "gh" | "wilcox" | "dunn"
    act: () => st.act,
    state: () => st,
    isSettled: () => flightState(performance.now()).flying.size === 0,
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
