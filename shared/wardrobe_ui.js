// Editing this? Read _agent_reference/instruments_and_widgets.md first (beside this file; local, gitignored).
// THE WARDROBE'S DRAWINGS (classification/lair, 2026-11-24): ONE figure renderer for the three places a player sees an
// outfit (the HUD figure, every scan-log row, the scanner card), the scan log board (instrument kind "scan_log"),
// the scanner dial and the tote's item icons. Everything is an SVG/HTML STRING built from words, so it is testable in
// Node (tests/wardrobe.test.mjs); the only DOM code is ensureWardrobeStyles, animateDial and mountScanLog.
// The rules the drawings obey: no number on the dial (the logs teach the rule; a printed probability would turn the
// gate into a calculator), no caption about where anything came from, figures never shrunk below legible on a
// 320 px phone (rows wrap instead), and a badge's kind shown as a letter on the chest card (badges carry no colour).

const COLOURS = {
  orange: "#f07f1f", gray: "#8b9198", grey: "#8b9198", white: "#f6f6f1", navy: "#22325f", yellow: "#f4d21f",
  red: "#d23a2a", blue: "#2f6fd6", green: "#3a9b46", black: "#151515", purple: "#7a3db0", silver: "#c6ccd3",
  pink: "#f39ac4", brown: "#7b4a26", gold: "#c9a227",
};
export const colourOf = word => COLOURS[String(word || "").toLowerCase()] || "#b5b5b5";
export const badgeMark = kind => String(kind || "").replace(/[^A-Za-z]/g, "").slice(0, 1).toUpperCase();

const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const STROKE = 'stroke="#1b1b1b" stroke-width="1.3" stroke-linejoin="round"';
const SKIN = "#a9aeb3";   // the plain grey person under the clothes

// The words of an outfit as one plain sentence, for aria-labels: "orange overalls, yellow hat, a visitor badge".
export function outfitText(o) {
  const p = [];
  if (o && o.overalls) p.push(o.overalls + " overalls");
  if (o && o.hat) p.push(o.hat + " hat");
  if (o && o.armband) p.push(o.armband + " armband");
  if (o && o.badge) p.push(o.badge + " badge");
  return p.join(", ") || "no work clothes";
}

// A small grey person wearing `outfit` ({overalls, hat, armband, badge}: colour words, the badge's kind word).
// size = rendered height in px (width follows the 60 x 100 drawing). An empty slot draws nothing there.
export function figureSvg(outfit, opts = {}) {
  const o = outfit || {};
  const h = opts.size || 84, w = Math.round(h * 0.6);
  const ov = o.overalls ? colourOf(o.overalls) : SKIN;
  const parts = [];
  // arms (sleeves in the overalls colour), hands, legs, torso, head
  parts.push(`<rect x="9" y="32" width="9" height="27" rx="4" fill="${ov}" ${STROKE}/>`);
  parts.push(`<rect x="42" y="32" width="9" height="27" rx="4" fill="${ov}" ${STROKE}/>`);
  parts.push(`<circle cx="13.5" cy="61.5" r="3.6" fill="${SKIN}" ${STROKE}/>`, `<circle cx="46.5" cy="61.5" r="3.6" fill="${SKIN}" ${STROKE}/>`);
  parts.push(`<rect x="20" y="58" width="9.5" height="36" rx="2.5" fill="${ov}" ${STROKE}/>`);
  parts.push(`<rect x="30.5" y="58" width="9.5" height="36" rx="2.5" fill="${ov}" ${STROKE}/>`);
  parts.push(`<rect x="18" y="30" width="24" height="32" rx="5" fill="${ov}" ${STROKE}/>`);
  parts.push(`<circle cx="30" cy="20" r="9" fill="${SKIN}" ${STROKE}/>`);
  if (o.hat) {
    const c = colourOf(o.hat);
    parts.push(`<path class="fig-hat" d="M19.5 17.5 C19.5 6.5 40.5 6.5 40.5 17.5 Z" fill="${c}" ${STROKE}/>`,
               `<rect x="16" y="16.2" width="28" height="3.6" rx="1.6" fill="${c}" ${STROKE}/>`);
  }
  if (o.armband) parts.push(`<rect class="fig-armband" x="7.6" y="37" width="11.8" height="6" rx="1.2" fill="${colourOf(o.armband)}" ${STROKE}/>`);
  if (o.badge) {
    parts.push(`<g class="fig-badge"><rect x="21" y="35" width="18" height="16" rx="2" fill="#fbfbf7" ${STROKE}/>` +
               `<text x="30" y="47.6" text-anchor="middle" font-family="system-ui,Arial,sans-serif" font-weight="800" font-size="13" fill="#1b1b1b">${esc(badgeMark(o.badge))}</text></g>`);
  }
  const label = opts.label != null ? opts.label : outfitText(o);
  return `<svg class="wfig" viewBox="0 0 60 100" width="${w}" height="${h}" role="img" aria-label="${esc(label)}">${parts.join("")}</svg>`;
}

// One wearable's icon for the tote (16-40 px): the piece of clothing alone, in its colour; a badge with its letter.
export function itemIconSvg(item, size = 34) {
  const e = item || {};
  const c = colourOf(e.colour);
  let body = "";
  if (e.slot === "hat") body = `<path d="M7 25 C7 8 33 8 33 25 Z" fill="${c}" ${STROKE}/><rect x="3" y="23.5" width="34" height="5" rx="2" fill="${c}" ${STROKE}/>`;
  else if (e.slot === "armband") body = `<rect x="6" y="14" width="28" height="12" rx="3" fill="${c}" ${STROKE}/>`;
  else if (e.slot === "overalls") body = `<path d="M11 6 H29 V20 H31 V36 H22 V24 H18 V36 H9 V20 H11 Z" fill="${c}" ${STROKE}/>`;
  else if (e.slot === "badge") body = `<rect x="7" y="7" width="26" height="26" rx="3" fill="#fbfbf7" ${STROKE}/>` +
    `<text x="20" y="27" text-anchor="middle" font-family="system-ui,Arial,sans-serif" font-weight="800" font-size="19" fill="#1b1b1b">${esc(badgeMark(e.kind))}</text>`;
  else return "";
  return `<svg class="witem" viewBox="0 0 40 40" width="${size}" height="${size}" aria-hidden="true">${body}</svg>`;
}

export function sunSvg(size = 18) {
  const rays = [0, 45, 90, 135, 180, 225, 270, 315].map(a => {
    const r = a * Math.PI / 180, x1 = 10 + Math.cos(r) * 6.4, y1 = 10 + Math.sin(r) * 6.4, x2 = 10 + Math.cos(r) * 9, y2 = 10 + Math.sin(r) * 9;
    return `<line x1="${x1.toFixed(2)}" y1="${y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}" stroke="#e8a50c" stroke-width="1.8" stroke-linecap="round"/>`;
  }).join("");
  return `<svg class="wsun" viewBox="0 0 20 20" width="${size}" height="${size}" role="img" aria-label="day">${rays}<circle cx="10" cy="10" r="4.6" fill="#ffd23a" stroke="#e8a50c" stroke-width="1"/></svg>`;
}
export function moonSvg(size = 18) {
  return `<svg class="wmoon" viewBox="0 0 20 20" width="${size}" height="${size}" role="img" aria-label="night">` +
         `<path d="M13.5 3.2 A7.4 7.4 0 1 0 16.8 14.6 A6 6 0 1 1 13.5 3.2 Z" fill="#dfe6f5" stroke="#7d8db3" stroke-width="1"/></svg>`;
}
export const timeSvg = (time, size) => (time === "night" ? moonSvg(size) : sunSvg(size));
export function tickSvg(size = 20) {
  return `<svg class="wtick" viewBox="0 0 20 20" width="${size}" height="${size}" role="img" aria-label="admitted">` +
         `<circle cx="10" cy="10" r="9" fill="#2e9d4b"/><path d="M5.4 10.4 L8.7 13.6 L14.8 6.8" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
export function crossSvg(size = 20) {
  return `<svg class="wcross" viewBox="0 0 20 20" width="${size}" height="${size}" role="img" aria-label="refused">` +
         `<circle cx="10" cy="10" r="9" fill="#c8312b"/><path d="M6.4 6.4 L13.6 13.6 M13.6 6.4 L6.4 13.6" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></svg>`;
}

// An entry log: one small card per past scan (the figure, a sun or moon, a tick or cross), in the board's order,
// numbered so two partners can point at the same row. Cards wrap; on a 320 px phone four sit side by side.
export function logBoardHtml(scanLog, opts = {}) {
  const rows = (scanLog && Array.isArray(scanLog.rows)) ? scanLog.rows : [];
  const title = opts.title ? `<div class="scanlog-title">${esc(opts.title)}</div>` : "";
  const cards = rows.map((r, i) => {
    const ok = !!r.admitted;
    const aria = `${i + 1}: ${outfitText(r)}, ${r.time === "night" ? "night" : "day"}, ${ok ? "admitted" : "refused"}`;
    return `<li class="scanrow ${ok ? "admitted" : "refused"}" data-row="${i}" data-time="${r.time === "night" ? "night" : "day"}" aria-label="${esc(aria)}">` +
           `<span class="scanrow-n" aria-hidden="true">${i + 1}</span>` +
           `<span class="scanfig">${figureSvg(r, { size: opts.figSize || 84, label: "" })}</span>` +
           `<span class="scanrow-meta" aria-hidden="true">${timeSvg(r.time, 18)}${ok ? tickSvg(20) : crossSvg(20)}</span></li>`;
  }).join("");
  return `<div class="scanlog">${title}<ol class="scanlog-rows">${cards}</ol></div>`;
}

// ---- the scanner dial: the S-curve itself is the scale -------------------------------------------------------
// Across: the outfit's summed weight (the score), from -6 to 6. Up: the probability, the S-curve 1/(1+e^-score).
// One marked line at `opensAbove`; above it the door opens. The needle stands at the scan's score and its bead rides
// the curve. Nothing on it is a number.
const DX0 = 18, DX1 = 222, DY0 = 16, DY1 = 112, SMAX = 6;
const clampS = s => Math.max(-SMAX, Math.min(SMAX, s));
export const logit = p => { const q = Math.min(1 - 1e-6, Math.max(1e-6, +p || 0)); return Math.log(q / (1 - q)); };
const sx = s => DX0 + (clampS(s) + SMAX) / (2 * SMAX) * (DX1 - DX0);
const py = p => DY1 - p * (DY1 - DY0);
export function needleAt(prob) {
  const s = clampS(logit(prob)), p = 1 / (1 + Math.exp(-s));
  return { x: +sx(s).toFixed(2), y: +py(p).toFixed(2), score: s, prob: p };
}
export function dialSvg(prob, opensAbove = 0.5) {
  const pts = [];
  for (let i = 0; i <= 60; i++) { const s = -SMAX + i * (2 * SMAX) / 60; pts.push(`${sx(s).toFixed(1)},${py(1 / (1 + Math.exp(-s))).toFixed(1)}`); }
  const ty = py(Math.min(1, Math.max(0, +opensAbove || 0))).toFixed(1);
  const n = needleAt(prob);
  return `<svg class="scandial" viewBox="0 0 240 132" role="img" aria-label="scanner dial" data-prob="${n.prob.toFixed(4)}">` +
    `<rect x="4" y="4" width="232" height="124" rx="10" fill="#14181d" stroke="#5c6670" stroke-width="2"/>` +
    `<rect class="scandial-open" x="${DX0}" y="${DY0}" width="${DX1 - DX0}" height="${(+ty - DY0).toFixed(1)}" fill="rgba(60,190,95,.16)"/>` +
    `<line x1="${DX0}" y1="${DY1}" x2="${DX1}" y2="${DY1}" stroke="#56606a" stroke-width="1.5"/>` +
    `<polyline points="${pts.join(" ")}" fill="none" stroke="#e9eef3" stroke-width="3" stroke-linecap="round"/>` +
    `<line class="scandial-line" x1="${DX0}" y1="${ty}" x2="${DX1}" y2="${ty}" stroke="#ff5a4a" stroke-width="2.4"/>` +
    `<g class="scandial-needle"><line class="scandial-stem" x1="${n.x}" y1="${DY1 + 6}" x2="${n.x}" y2="${n.y}" stroke="#ffb02e" stroke-width="3" stroke-linecap="round"/>` +
    `<circle class="scandial-bead" cx="${n.x}" cy="${n.y}" r="7" fill="#ffb02e" stroke="#2a1a00" stroke-width="1.5"/></g></svg>`;
}
// Move the needle of a dialSvg already in the page to `prob`, easing from `from` (default the far left) over `ms`.
// Reduced motion (opts.reduced) sets it at once. `onDone` runs once, after the needle has arrived.
export function animateDial(svg, prob, opts = {}) {
  const stem = svg && svg.querySelector(".scandial-stem"), bead = svg && svg.querySelector(".scandial-bead");
  const set = p => {
    const n = needleAt(p);
    if (stem) { stem.setAttribute("x1", n.x); stem.setAttribute("x2", n.x); stem.setAttribute("y2", n.y); }
    if (bead) { bead.setAttribute("cx", n.x); bead.setAttribute("cy", n.y); }
    if (svg) svg.setAttribute("data-prob", n.prob.toFixed(4));
  };
  const done = typeof opts.onDone === "function" ? opts.onDone : () => {};
  const ms = opts.ms != null ? +opts.ms : 1400;
  if (opts.reduced || !(ms > 0) || typeof requestAnimationFrame !== "function") { set(prob); setTimeout(done, 0); return; }
  const s0 = opts.from != null ? logit(opts.from) : -SMAX, s1 = logit(prob);
  const t0 = performance.now();
  const step = now => {
    const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3);
    set(1 / (1 + Math.exp(-(s0 + (s1 - s0) * e))));
    if (k < 1 && svg.isConnected) requestAnimationFrame(step);
    else { set(prob); done(); }
  };
  set(1 / (1 + Math.exp(-s0)));
  requestAnimationFrame(step);
}

// Scan-budget lamps: one per allowed scan, the spent ones lit red. The world's way of saying how many are left.
export function budgetLampsHtml(budget, spent) {
  if (!budget) return "";
  let s = "";
  for (let i = 0; i < budget; i++) s += `<span class="scanlamp${i < spent ? " spent" : ""}"></span>`;
  return `<div class="scanlamps" role="img" aria-label="${budget - spent} of ${budget} scans left">${s}</div>`;
}

// Instrument kind "scan_log": the log board, read by eye; no geometry, art or config.
export function mountScanLog(host, o) {
  const h = (o && o.hotspot) || {};
  ensureWardrobeStyles(host.ownerDocument || document);
  const wrap = host.ownerDocument.createElement("div");
  wrap.className = "scanlog-host";        // fills the card (an .instrumentcard is a centring flex row)
  wrap.innerHTML = logBoardHtml(h.scanLog, { title: h.label });
  host.appendChild(wrap);
  return { destroy: () => wrap.remove() };
}

const CSS = `
.scanlog-host{flex:1 1 auto;width:100%;min-width:0}
.scanlog{color:#eee}
.scanlog-title{font:600 15px/1.3 system-ui,sans-serif;margin:0 0 10px;color:#ffd88c}
.scanlog-rows{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:8px}
.scanrow{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px;padding:6px 2px 6px;border-radius:9px;background:#d7dadd;border:2px solid #9aa1a8}
.scanrow.admitted{border-color:#2e9d4b}.scanrow.refused{border-color:#c8312b}
.scanrow-n{position:absolute;top:2px;left:5px;font:700 11px system-ui,sans-serif;color:#3a3f45}
.scanrow-meta{display:flex;gap:5px;align-items:center}
.scanfig svg,.wfig{display:block}
.scancard{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center}
.scancard-top{display:flex;align-items:center;gap:14px}
.scancard-fig{background:#d7dadd;border-radius:12px;padding:8px 10px;border:2px solid #9aa1a8}
.scancard .scandial{width:min(100%,300px);height:auto}
.scancard .qfeedback{min-height:1.3em}
.scanlamps{display:flex;gap:8px;justify-content:center}
.scanlamp{width:14px;height:14px;border-radius:50%;background:#3b4148;border:2px solid #22272c;box-shadow:inset 0 0 3px rgba(0,0,0,.6)}
.scanlamp.spent{background:#ff4a3a;box-shadow:0 0 8px rgba(255,74,58,.8)}
#wardrobeHud{position:absolute;right:14px;z-index:20;padding:4px 7px;border-radius:12px;background:rgba(215,218,221,.86);border:1px solid rgba(255,216,140,.55);cursor:pointer;line-height:0}
#wardrobeHud .wfig{filter:drop-shadow(0 1px 1px rgba(0,0,0,.5))}
.nbtote .itemtile .witem{display:block}
.nbtote .wearbtn{margin-top:2px;padding:3px 10px;font:600 12px system-ui;border-radius:8px;border:1px solid rgba(255,216,140,.5);background:rgba(255,216,140,.14);color:#ffd88c;cursor:pointer}
.nbtote .wearing{margin-top:2px;font:600 12px system-ui;color:#8fe0a0}
.nbtote .itemtile.worn{border-color:#8fe0a0}
.totefig{display:flex;justify-content:center;margin:0 0 10px}
.totefig .wfig{background:#d7dadd;border-radius:12px;padding:6px 8px;border:2px solid #9aa1a8}
`;
export function ensureWardrobeStyles(doc) {
  if (!doc || doc.getElementById("wardrobe-style")) return;
  const s = doc.createElement("style"); s.id = "wardrobe-style"; s.textContent = CSS;
  (doc.head || doc.documentElement).appendChild(s);
}
