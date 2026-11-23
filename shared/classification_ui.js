// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `sigmoid_board` and `scoreboard` kinds).
// classification_ui.js: the shared frame of the classification chapter's two instruments (sigmoid_board.js, scoreboard.js):
// tabs across the top, an SVG drawing on the left, a panel on the right holding the Lesson (the book's wording plus
// "In the book: classification models, <section>"), the tab's own controls and its readout. The ghost-line board's
// visual grammar (brass tabs, dark face, panel right, wrapping below under 900 px). CSS injected once (#clsb-style).

const CSS = `
.clsb { display:flex; flex-direction:column; gap:8px; width:100%; color:#f3e6c4; font:17px/1.4 Georgia, "Times New Roman", serif; }
.clsbtabs { display:flex; gap:6px 10px; justify-content:center; flex-wrap:wrap; }
.clsbtab { background:#3b2a14; color:#f3e6c4; border:1px solid #8a6a32; border-radius:16px; padding:6px 15px; font:inherit; font-size:18px; cursor:pointer; }
.clsbtab:hover { border-color:#e0b55a; }
.clsbtab:focus-visible, .clsb button:focus-visible, .clsb input:focus-visible { outline:2px solid #ffe39a; outline-offset:2px; }
.clsbtab.on { background:linear-gradient(#a8742e,#7a5220); border-color:#e2b468; color:#fff6e0; }
.clsbstage { display:flex; gap:16px; align-items:flex-start; justify-content:center; }
.clsbsvg { display:block; flex:0 1 auto; width:min(calc(100% - 476px), calc(min(76vh, 100vh - 170px) * var(--clsbr, 1.6))); height:auto;
  background:#08111a; border-radius:10px; touch-action:none; -webkit-user-select:none; user-select:none; }
.clsbpanel { flex:0 0 460px; display:flex; flex-direction:column; gap:12px; }
.clsblesson { border-left:3px solid #e2b468; padding:2px 0 4px 11px; }
.clsbhead { color:#e2b468; font-size:15px; font-weight:bold; letter-spacing:.08em; text-transform:uppercase; }
.clsblessontext { font-size:clamp(17px, 1.25vw, 21px); line-height:1.42; margin:4px 0 6px; color:#fff1d6; }
.clsblessonbook { color:#bfae8a; font-size:14px; font-style:italic; }
.clsbctl { display:flex; flex-direction:column; gap:10px; }
.clsbrow { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.clsb button { background:#3b2a14; color:#f3e6c4; border:1px solid #8a6a32; border-radius:8px; padding:8px 14px; font:inherit; font-size:18px; cursor:pointer; }
.clsb button:hover { border-color:#e0b55a; }
/* one button look on both boards: every control button is the same brass rectangle; a toggle shows "on" in blue */
.clsb button[aria-pressed="true"] { background:#1f3a52; border-color:#9ccaf2; color:#eaf5ff; }
.clsb label.clsbslider { display:grid; grid-template-columns:1fr auto; gap:2px 10px; align-items:center; font-size:17px; }
.clsb label.clsbslider input { grid-column:1 / -1; width:100%; accent-color:#e2b468; height:26px; }
.clsb label.clsbslider output { color:#fff6e0; font-variant-numeric:tabular-nums; font-weight:bold; }
.clsbread { font-size:18px; color:#fff6e0; }
.clsbread p { margin:0 0 6px; }
.clsbread .dim { color:#cdbf9f; font-size:15px; }
.clsbread b { color:#ffe39a; }
.clsbtable { border-collapse:collapse; width:100%; font:15px ui-monospace, Menlo, Consolas, monospace; font-variant-numeric:tabular-nums; }
.clsbtable th { color:#e2b468; font-weight:normal; text-align:right; padding:2px 5px; border-bottom:1px solid rgba(226,180,104,.4); font-size:13px; }
.clsbtable td { text-align:right; padding:2px 5px; }
.clsbtable th:first-child, .clsbtable td:first-child { text-align:left; }
.clsbtable tr.changed td { color:#ffb36b; font-weight:bold; }
.clsbtable td.yes { color:#ffd27a; } .clsbtable td.no { color:#9fc3e8; }
.clsbsvg text { font-family:Georgia, "Times New Roman", serif; }
.clsbsvg .hit { cursor:grab; } .clsbsvg .hit:active { cursor:grabbing; }
.clsbsvg .pickable { cursor:pointer; }
@media (max-width: 900px) {
  .clsbstage { flex-direction:column; align-items:stretch; }
  .clsbsvg { width:100%; }
  .clsbpanel { flex:1 1 auto; }
}`;

export function injectCss() {
  if (document.getElementById("clsb-style")) return;
  const s = document.createElement("style"); s.id = "clsb-style"; s.textContent = CSS;
  document.head.appendChild(s);
}

export const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const NS = "http://www.w3.org/2000/svg";
export function svgEl(parent, tag, attrs = {}, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}
export function button(txt, cls, fn, title) {
  const b = el("button", cls || "", txt); b.type = "button"; if (title) b.title = title; b.addEventListener("click", fn); return b;
}
export function slider(label, { min, max, step, value, fmt = (v) => String(v), onInput }) {
  const l = el("label", "clsbslider"); const out = el("output", null, fmt(value));
  const r = el("input"); r.type = "range"; r.min = min; r.max = max; r.step = step; r.value = value;
  r.setAttribute("aria-label", label);
  r.addEventListener("input", () => { out.textContent = fmt(+r.value); onInput(+r.value); });
  l.append(el("span", null, label), out, r);
  return { el: l, set(v) { r.value = v; out.textContent = fmt(+v); }, input: r };
}

// The frame: tabs [[key, name]], a W x H svg, the panel. `where(key)` is the chapter section a tab belongs to.
export function shell(host, { cls, tabs, W, H, ariaLabel, onTab }) {
  injectCss();
  const root = el("div", "clsb " + cls);
  const bar = el("div", "clsbtabs"); bar.setAttribute("role", "tablist");
  const stage = el("div", "clsbstage");
  const svg = svgEl(null, "svg", { class: "clsbsvg", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": ariaLabel });
  svg.style.setProperty("--clsbr", String(W / H));
  const panel = el("div", "clsbpanel"), lesson = el("div", "clsblesson"), ctl = el("div", "clsbctl"), read = el("div", "clsbread");
  panel.append(lesson, ctl, read);
  const tabBtns = {};
  tabs.forEach(([k, name], i) => {
    const b = button(`${i + 1} · ${name}`, "clsbtab clsbtab-" + k, () => onTab(k));
    b.setAttribute("role", "tab"); b.dataset.tab = k; tabBtns[k] = b; bar.appendChild(b);
  });
  stage.append(svg, panel); root.append(bar, stage); host.appendChild(root);
  return {
    root, svg, panel, lesson, ctl, read,
    mark(k) { for (const [kk, b] of Object.entries(tabBtns)) { b.classList.toggle("on", kk === k); b.setAttribute("aria-selected", String(kk === k)); } },
    setLesson(text, where) {
      lesson.replaceChildren(el("div", "clsbhead", "Lesson"), el("p", "clsblessontext", text),
                             el("div", "clsblessonbook", "In the book: classification models, " + where));
    },
  };
}

// The pointer position in the svg's own units.
export function svgPoint(svg, ev) {
  const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
  const m = svg.getScreenCTM(); return m ? pt.matrixTransform(m.inverse()) : { x: 0, y: 0 };
}

export const fmt2 = (v) => (Number.isFinite(v) ? v.toFixed(2) : "–");
export const pct = (v) => Math.round(v * 100) + "%";
