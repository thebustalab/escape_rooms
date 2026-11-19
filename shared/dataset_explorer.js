// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `dataset_explorer` kind).
/*
 * dataset_explorer.js: the DATASET EXPLORER (2026-11-19). An interactive picture of a dataset's STRUCTURE, built so a
 * student can absorb a new table quickly: what one row is, the groups (the split and the response), and each
 * variable with its plain meaning, units and spread over all rows. Lucas also demos it on a projector, so it is
 * laptop-first, large type, calm colours, four tabs.
 *
 * STRUCTURE ONLY. It never shows the response against a variable or within a split (no coloured histograms, group
 * means, correlations or crossed counts): those are what the graded ladders test. Every number it prints comes from
 * dataset_explorer_model.js's `displayed` list, which tests/dataset_explorer_leak.test.mjs checks against each
 * room's answer key. Raw cells (the row card, the table glimpse) are the data itself, as view() shows it.
 *
 * mount(host, opts) -> { destroy, ready }. opts: { config?: descriptor object, configUrl?: its URL (the CSV path in it
 * resolves against this), descriptor?: URL to fetch the descriptor from, pegs?: {tab, row}, onPegs? }.
 * Used as instrument kind `dataset_explorer` (a hotspot `config` = descriptor path) and by the graded rooms'
 * "Dataset explorer" chip (SCENARIO.datasetExplorer). Code-drawn; CSS injected once (#dsx-style).
 */
import { buildModel, rowView, fmtCount } from "./dataset_explorer_model.js?v=177";

export const GLIMPSE_ROWS = 8;      // tests/dataset_explorer_leak.test.mjs checks the same rows' identifiers
const TABS = [["row", "One row"], ["table", "The table"], ["groups", "The groups"], ["vars", "The variables"]];
const ROLE_LABEL = { identifier: "identifier", split: "split", response: "response", predictor: "predictor", flag: "other column" };
const ROLE_HELP = {
  identifier: "names the row",
  split: "training or held back",
  response: "what the model predicts",
  predictor: "a measurement the model can use",
  flag: "recorded alongside; not a measurement",
};
const BLOCK_TINTS = ["#5fd0c0", "#86b4ff", "#c3e07a", "#f2a65a"];

const CSS = `
.dsx { --dsx-id:#a9bccf; --dsx-split:#b9a0f2; --dsx-resp:#ffc861; --dsx-flag:#f0909f; --dsx-ink:#e8eef2; --dsx-dim:rgba(232,238,242,.66);
  width:100%; max-width:1180px; margin:0 auto; color:var(--dsx-ink); font:17px/1.5 system-ui, sans-serif; text-align:left; }
.dsx code, .dsx .dsx-name { font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.dsx-head { display:flex; align-items:baseline; flex-wrap:wrap; gap:6px 18px; margin:2px 0 12px; padding-right:36px; }
.dsx-kicker { font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--dsx-dim); width:100%; }
.dsx-title { font-size:28px; font-weight:650; margin:0; }
.dsx-sub { color:var(--dsx-dim); font-size:17px; }
.dsx-sub code { color:var(--dsx-ink); background:rgba(255,255,255,.08); padding:1px 7px; border-radius:6px; }
.dsx-tabs { display:flex; gap:6px; border-bottom:1px solid rgba(255,255,255,.16); margin-bottom:18px; flex-wrap:wrap; }
.dsx-tab { background:transparent; color:var(--dsx-dim); border:1px solid transparent; border-bottom:none; border-radius:10px 10px 0 0;
  padding:9px 18px; font:600 17px system-ui, sans-serif; cursor:pointer; margin-bottom:-1px; }
.dsx-tab:hover { color:var(--dsx-ink); }
.dsx-tab.on { color:var(--dsx-ink); background:rgba(255,255,255,.06); border-color:rgba(255,255,255,.16); border-bottom:1px solid #0b1b28; }
.dsx-tab .n { opacity:.55; margin-right:6px; font-weight:500; }
.dsx-pane[hidden] { display:none; }
.dsx-lead { font-size:21px; margin:0 0 14px; }
.dsx-lead b { color:#fff; }
.dsx-note { color:var(--dsx-dim); font-size:15px; margin:10px 0 0; }
.dsx-btn { background:rgba(255,216,140,.12); color:#ffd88c; border:1px solid rgba(255,216,140,.45); border-radius:10px;
  padding:9px 18px; font:600 16px system-ui, sans-serif; cursor:pointer; }
.dsx-btn:hover { background:rgba(255,216,140,.2); }
.dsx-dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:8px; vertical-align:0; flex:none; }
.dsx-err { color:#ffb3a8; font-size:18px; }
/* one row, as a card */
.dsx-rowwrap { display:flex; flex-direction:column; align-items:center; gap:14px; }
.dsx-card { position:relative; overflow:hidden; width:min(760px, 100%); border-radius:12px; padding:18px 28px 16px; box-shadow:0 10px 34px rgba(0,0,0,.45); }
.dsx-card.logsheet { background:#f4ecd6; color:#2b2418; border-left:6px solid rgba(160,60,40,.35); }
.dsx-card.plate { background:radial-gradient(ellipse at 50% 40%, #1a2027 0%, #0c0f13 70%); color:#e9edf1;
  border:1px solid rgba(255,255,255,.28); outline:6px solid rgba(255,255,255,.05); }
.dsx-card .dsx-stars { position:absolute; left:0; top:0; width:100%; height:100%; pointer-events:none; overflow:hidden; }
.dsx-cardhead { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:10px; position:relative; }
.dsx-cardkicker { font-size:13px; letter-spacing:.14em; text-transform:uppercase; opacity:.7; }
.dsx-cardid { font:700 26px ui-monospace, Menlo, Consolas, monospace; }
.dsx-stamp { border:2.5px solid var(--dsx-split); color:var(--dsx-split); border-radius:8px; padding:3px 12px; font:800 15px system-ui;
  letter-spacing:.12em; text-transform:uppercase; transform:rotate(-4deg); white-space:nowrap; }
.dsx-card.logsheet .dsx-stamp { border-color:#6a4fb0; color:#6a4fb0; }
.dsx-cardsec { position:relative; margin-top:8px; }
.dsx-cardsec h4 { margin:0 0 2px; font-size:14px; letter-spacing:.08em; text-transform:uppercase; opacity:.72; font-weight:700; }
.dsx-line { display:flex; align-items:baseline; gap:10px; padding:2px 0; font-size:18px; }
.dsx-line .dsx-name { flex:1 1 auto; overflow:hidden; text-overflow:ellipsis; }
.dsx-line .dsx-val { font:700 20px ui-monospace, Menlo, Consolas, monospace; }
.dsx-line .dsx-units { opacity:.7; font-size:15px; min-width:120px; }
.dsx-card.logsheet .dsx-line { border-bottom:1px dotted rgba(43,36,24,.25); }
.dsx-card.plate .dsx-line { border-bottom:1px dotted rgba(255,255,255,.16); }
.dsx-respline { margin-top:10px; padding:5px 12px; border-radius:8px; }
.dsx-card.logsheet .dsx-respline { background:rgba(214,150,20,.16); }
.dsx-card.plate .dsx-respline { background:rgba(255,200,97,.12); }
/* table glimpse */
.dsx-legend { display:flex; flex-wrap:wrap; gap:8px 22px; margin:0 0 12px; font-size:16px; }
.dsx-legend span { display:inline-flex; align-items:center; }
.dsx-legend em { font-style:normal; color:var(--dsx-dim); margin-left:6px; }
.dsx-tablewrap { overflow-x:auto; border:1px solid rgba(255,255,255,.14); border-radius:10px; }
.dsx-table { border-collapse:collapse; font:15px ui-monospace, Menlo, Consolas, monospace; white-space:nowrap; width:100%; }
.dsx-table th { position:sticky; top:0; background:#102434; text-align:left; padding:9px 12px 7px; font-weight:700; border-top:5px solid; }
.dsx-table td { padding:6px 12px; border-top:1px solid rgba(255,255,255,.07); }
.dsx-table tbody tr:nth-child(odd) td { background:rgba(255,255,255,.025); }
/* groups */
.dsx-groups { display:grid; grid-template-columns:1fr; gap:26px; }
.dsx-group h3 { margin:0 0 4px; font-size:21px; }
.dsx-group p { margin:0 0 12px; color:var(--dsx-dim); }
.dsx-bar { display:flex; height:58px; border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,.2); }
.dsx-seg { display:flex; align-items:center; justify-content:center; font:700 18px system-ui; color:#0b1b28; min-width:6px; }
.dsx-keys { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:10px 26px; margin-top:12px; }
.dsx-key { display:flex; gap:10px; align-items:flex-start; font-size:17px; }
.dsx-key .sw { width:18px; height:18px; border-radius:4px; flex:none; margin-top:4px; }
.dsx-key b { font-family:ui-monospace, Menlo, Consolas, monospace; }
/* variables */
.dsx-block { margin:0 0 22px; padding:14px 16px 16px; border-radius:12px; border:1px solid rgba(255,255,255,.12); border-left:6px solid; background:rgba(255,255,255,.02); }
.dsx-block h3 { margin:0; font-size:21px; }
.dsx-block > p { margin:2px 0 12px; color:var(--dsx-dim); }
.dsx-vars { display:grid; grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); gap:14px; }
.dsx-var { display:flex; flex-direction:column; align-items:flex-start; background:rgba(0,0,0,.18); border:1px solid rgba(255,255,255,.1); border-radius:10px; padding:12px 14px 10px; }
.dsx-var .dsx-strip { margin-top:auto; padding-top:8px; }
.dsx-var .dsx-name { font-weight:700; font-size:17px; display:block; overflow-wrap:anywhere; }
.dsx-var .dsx-meaning { margin:4px 0 6px; font-size:16px; }
.dsx-var .dsx-unitchip { display:inline-block; font-size:14px; padding:1px 9px; border-radius:999px; border:1px solid rgba(255,255,255,.25); color:var(--dsx-dim); }
.dsx-strip { display:block; width:100%; height:auto; }
.dsx-strip text { fill:rgba(232,238,242,.75); font:13px system-ui, sans-serif; }
.dsx-roletag { font-size:13px; letter-spacing:.06em; text-transform:uppercase; font-weight:700; }
@media (max-width:700px) { .dsx { font-size:15px; } .dsx-title { font-size:22px; } .dsx-lead { font-size:18px; } .dsx-tab { padding:7px 10px; font-size:15px; } }
`;

function injectCss() {
  if (document.getElementById("dsx-style")) return;
  const s = document.createElement("style"); s.id = "dsx-style"; s.textContent = CSS;
  document.head.appendChild(s);
}
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

export function roleColour(col, model) {
  if (col.role === "identifier") return "var(--dsx-id)";
  if (col.role === "split") return "var(--dsx-split)";
  if (col.role === "response") return "var(--dsx-resp)";
  if (col.role === "flag") return "var(--dsx-flag)";
  const bi = Math.max(0, model.blocks.findIndex(b => b.columns.includes(col)));
  return BLOCK_TINTS[bi % BLOCK_TINTS.length];
}

export function mount(host, opts = {}) {
  injectCss();
  const root = el("div", "dsx");
  host.appendChild(root);
  let dead = false, model = null;
  const state = Object.assign({ tab: "row", row: null }, opts.pegs || {});
  const save = () => { if (opts.onPegs) opts.onPegs({ tab: state.tab, row: state.row }); };
  root.appendChild(el("p", "dsx-note", "Loading the dataset…"));

  const ready = (async () => {
    let desc = opts.config, base = opts.configUrl || opts.descriptor;
    const baseHref = new URL(base || ".", document.baseURI).href;
    if (!desc) desc = await (await fetch(baseHref)).json();
    const csvUrl = new URL(desc.csv, baseHref).href;
    const res = await fetch(csvUrl);
    if (!res.ok) throw new Error("CSV " + res.status);
    const text = await res.text();
    if (dead) return;
    model = buildModel(desc, text);
    if (model.problems.length) console.warn("dataset explorer: descriptor problems", model.problems);
    if (state.row == null || state.row >= model.nRows) state.row = Math.floor(Math.random() * model.nRows);
    render();
  })().catch(e => {
    if (dead) return;
    console.error("dataset explorer failed to load", e);
    root.innerHTML = ""; root.appendChild(el("p", "dsx-err", "The dataset could not be loaded."));
  });

  function render() {
    root.innerHTML = "";
    const head = el("div", "dsx-head");
    head.appendChild(el("div", "dsx-kicker", "Dataset explorer"));
    head.appendChild(el("h2", "dsx-title", model.title));
    const sub = el("div", "dsx-sub");
    sub.append("In R: ", el("code", null, model.dataset), ` · ${model.text.nRows} rows · ${model.text.nCols} columns`);
    head.appendChild(sub);
    root.appendChild(head);
    const bar = el("div", "dsx-tabs"); bar.setAttribute("role", "tablist");
    root.appendChild(bar);
    const panes = {};
    TABS.forEach(([k, label], i) => {
      const b = el("button", "dsx-tab dsx-tab-" + k); b.type = "button"; b.setAttribute("role", "tab");
      b.append(el("span", "n", String.fromCharCode(0x2460 + i)), label);  // circled digits read as tab marks, not data
      b.onclick = () => show(k);
      bar.appendChild(b);
      const p = el("section", "dsx-pane dsx-pane-" + k); p.setAttribute("role", "tabpanel");
      panes[k] = p; root.appendChild(p);
    });
    const builders = { row: buildRow, table: buildTable, groups: buildGroups, vars: buildVars };
    const built = new Set();
    function show(k) {
      if (!panes[k]) k = "row";
      state.tab = k; save();
      if (!built.has(k)) { builders[k](panes[k]); built.add(k); }
      for (const [kk, p] of Object.entries(panes)) p.hidden = kk !== k;
      [...bar.children].forEach((b, i) => { const on = TABS[i][0] === k; b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); });
    }
    root.dsx = { show, tab: () => state.tab, row: () => state.row, model: () => model, draw };
    show(state.tab);
  }

  // ① One row, as a card in the world's terms
  let cardHost = null;
  function buildRow(p) {
    const lead = el("p", "dsx-lead");
    lead.append(model.row.phrase || "");
    p.appendChild(lead);
    const wrap = el("div", "dsx-rowwrap");
    cardHost = el("div"); cardHost.style.width = "100%"; cardHost.style.display = "flex"; cardHost.style.justifyContent = "center";
    const btn = el("button", "dsx-btn dsx-draw", "Draw another " + (model.row.noun || "row"));
    btn.type = "button"; btn.onclick = () => draw();
    wrap.append(cardHost, btn);
    p.appendChild(wrap);
    p.appendChild(el("p", "dsx-note", `Every one of the ${model.text.nRows} rows looks like this card: the same columns, different values. In R, view(${model.dataset}) shows them all.`));
    drawCard();
  }
  function draw() {
    if (!model) return;
    let i = Math.floor(Math.random() * model.nRows);
    if (model.nRows > 1 && i === state.row) i = (i + 1) % model.nRows;
    state.row = i; save();
    if (cardHost) drawCard();
  }
  function drawCard() {
    const v = rowView(model, state.row);
    const look = model.row.look === "plate" ? "plate" : "logsheet";
    const card = el("div", "dsx-card " + look);
    card.dataset.row = String(state.row);
    if (look === "plate") card.appendChild(starfield(state.row));
    const head = el("div", "dsx-cardhead");
    const left = el("div");
    left.appendChild(el("div", "dsx-cardkicker", model.row.kicker || model.title));
    left.appendChild(el("div", "dsx-cardid", v.id));
    head.appendChild(left);
    if (model.split) {
      const st = el("div", "dsx-stamp", v.split);
      st.title = `${model.split.column.name}: ${v.split}`;
      head.appendChild(st);
    }
    card.appendChild(head);
    for (const b of v.blocks) {
      const sec = el("div", "dsx-cardsec");
      if (model.blocks.length > 1 || b.title) sec.appendChild(el("h4", null, b.title || "Measurements"));
      for (const c of b.cells) sec.appendChild(line(c.column, c.value));
      card.appendChild(sec);
    }
    if (v.flags.length) {
      const sec = el("div", "dsx-cardsec");
      sec.appendChild(el("h4", null, "Also recorded"));
      for (const f of v.flags) sec.appendChild(line(f.column, f.value));
      card.appendChild(sec);
    }
    if (model.response) {
      const r = line(model.response.column, v.response);
      r.classList.add("dsx-respline");
      card.appendChild(r);
    }
    cardHost.innerHTML = ""; cardHost.appendChild(card);
  }
  function line(col, value) {
    const d = el("div", "dsx-line");
    const dot = el("span", "dsx-dot"); dot.style.background = roleColour(col, model);
    d.append(dot, el("span", "dsx-name", col.name), el("span", "dsx-val", value), el("span", "dsx-units", col.units || ""));
    return d;
  }
  function starfield(seed) {
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "dsx-stars"); svg.setAttribute("viewBox", "0 0 100 60"); svg.setAttribute("preserveAspectRatio", "none");
    let s = (seed * 2654435761) >>> 0 || 1;
    const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
    for (let i = 0; i < 70; i++) {              // decoration only: positions from the row number, never from its values
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", (rnd() * 100).toFixed(2)); c.setAttribute("cy", (rnd() * 60).toFixed(2));
      c.setAttribute("r", (0.08 + rnd() * 0.22).toFixed(2)); c.setAttribute("fill", `rgba(255,255,255,${(0.25 + rnd() * 0.5).toFixed(2)})`);
      svg.appendChild(c);
    }
    return svg;
  }

  // ② The table, first rows, columns coloured by role
  function buildTable(p) {
    const lead = el("p", "dsx-lead");
    lead.append("The first rows of ", el("code", null, model.dataset), ", as ", el("code", null, "view()"),
                " shows them. Each column has a job:");
    p.appendChild(lead);
    p.appendChild(legend());
    const wrap = el("div", "dsx-tablewrap");
    const t = el("table", "dsx-table");
    const thead = el("thead"), tr = el("tr");
    const cols = model.header.map(h => model.columns.find(c => c.name === h)).filter(Boolean);
    for (const c of cols) {
      const th = el("th", null, c.name); th.style.borderTopColor = roleColour(c, model);
      th.title = `${ROLE_LABEL[c.role]}: ${c.meaning}`; th.dataset.role = c.role;
      tr.appendChild(th);
    }
    thead.appendChild(tr); t.appendChild(thead);
    const tb = el("tbody");
    for (const r of model.rows.slice(0, GLIMPSE_ROWS)) {
      const row = el("tr");
      for (const c of cols) row.appendChild(el("td", null, r[c.index]));
      tb.appendChild(row);
    }
    t.appendChild(tb); wrap.appendChild(t); p.appendChild(wrap);
    p.appendChild(el("p", "dsx-note", `…and so on, one row per ${model.row.noun || "row"}, ${model.text.nRows} rows in all.`));
  }
  function legend() {
    const lg = el("div", "dsx-legend");
    const item = (colour, name, help) => {
      const s = el("span"); const d = el("span", "dsx-dot"); d.style.background = colour;
      s.append(d, el("b", null, name), el("em", null, help)); lg.appendChild(s);
    };
    const has = r => model.columns.some(c => c.role === r);
    if (has("identifier")) item("var(--dsx-id)", "identifier", ROLE_HELP.identifier);
    if (has("split")) item("var(--dsx-split)", "split", ROLE_HELP.split);
    if (has("response")) item("var(--dsx-resp)", "response", ROLE_HELP.response);
    if (model.blocks.length > 1) model.blocks.forEach((b, i) => item(BLOCK_TINTS[i % BLOCK_TINTS.length], "predictor", b.title));
    else item(BLOCK_TINTS[0], "predictors", ROLE_HELP.predictor);
    if (has("flag")) item("var(--dsx-flag)", "other column", ROLE_HELP.flag);
    return lg;
  }

  // ③ The groups: the split and the response, each counted over all rows on its own
  function buildGroups(p) {
    const lead = el("p", "dsx-lead");
    lead.append(`Two columns sort the ${model.text.nRows} ${model.plural} into groups.`);
    p.appendChild(lead);
    const g = el("div", "dsx-groups");
    if (model.split) g.appendChild(groupBlock(model.split, "The split: training and held back",
      "The model is built on the training rows only; the held-back rows are kept aside to test it on rows it has not seen.",
      ["var(--dsx-split)", "rgba(185,160,242,.45)"]));
    if (model.response) g.appendChild(groupBlock(model.response, "The response: " + model.response.column.name,
      model.response.column.meaning + " This is what the model predicts.", ["var(--dsx-resp)", "rgba(255,200,97,.4)"]));
    p.appendChild(g);
  }
  function groupBlock(grp, title, blurb, colours) {
    const d = el("div", "dsx-group dsx-group-" + grp.column.role);
    const h = el("h3"); h.append(title + " "); d.appendChild(h);
    d.appendChild(el("p", null, blurb));
    const bar = el("div", "dsx-bar");
    const total = grp.groups.reduce((a, l) => a + l.count, 0) || 1;
    grp.groups.forEach((l, i) => {
      const s = el("div", "dsx-seg"); s.style.flex = `${l.count} 0 0`; s.style.background = colours[i % colours.length];
      s.title = `${l.value}: ${l.countText}`;
      if (l.count / total > 0.12) s.textContent = l.value;
      bar.appendChild(s);
    });
    d.appendChild(bar);
    const keys = el("div", "dsx-keys");
    grp.groups.forEach((l, i) => {
      const k = el("div", "dsx-key"); const sw = el("span", "sw"); sw.style.background = colours[i % colours.length];
      const t = el("div");
      t.append(el("b", null, l.value), ` · ${l.countText} ${model.plural}`);
      if (l.first) t.append(` (${l.first} to ${l.last})`);
      if (l.meaning) { t.appendChild(document.createElement("br")); t.append(el("span", null, l.meaning)); }
      k.append(sw, t); keys.appendChild(k);
    });
    d.appendChild(keys);
    return d;
  }

  // ④ The variables: one card per predictor, grouped by block; then the other columns in plain words
  function buildVars(p) {
    const lead = el("p", "dsx-lead");
    lead.append(`The predictors: the measurements on each ${model.row.noun || "row"}. Each strip shows how its values spread across all ${model.text.nRows} ${model.plural}.`);
    p.appendChild(lead);
    model.blocks.forEach((b, bi) => {
      const blk = el("div", "dsx-block"); blk.style.borderLeftColor = BLOCK_TINTS[bi % BLOCK_TINTS.length];
      blk.dataset.block = b.id || "";
      if (b.title) blk.appendChild(el("h3", null, b.title));
      if (b.blurb) blk.appendChild(el("p", null, b.blurb));
      const grid = el("div", "dsx-vars");
      for (const c of b.columns) grid.appendChild(varCard(c, BLOCK_TINTS[bi % BLOCK_TINTS.length]));
      blk.appendChild(grid); p.appendChild(blk);
    });
    const others = el("div", "dsx-block dsx-others"); others.style.borderLeftColor = "rgba(255,255,255,.35)";
    others.appendChild(el("h3", null, "The other columns"));
    others.appendChild(el("p", null, "Not measurements: they name, sort or flag each row."));
    const grid = el("div", "dsx-vars");
    for (const c of model.others) {
      const v = el("div", "dsx-var"); v.dataset.col = c.name;
      const tag = el("div", "dsx-roletag", ROLE_LABEL[c.role] + " · " + ROLE_HELP[c.role]); tag.style.color = roleColour(c, model);
      v.append(tag, el("span", "dsx-name", c.name), el("div", "dsx-meaning", c.meaning));
      if (c.role === "flag" && c.groups) {
        const t = el("div", "dsx-meaning");
        t.textContent = c.groups.map(l => `${l.value}: ${l.countText} ${model.plural}`).join(" · ");
        v.appendChild(t);
      }
      if (c.role === "identifier" && model.identifier) {
        const t = el("div", "dsx-meaning");
        t.textContent = model.identifier.dates
          ? `From ${model.identifier.first} to ${model.identifier.last}.`
          : `For example ${model.identifier.example}.`;
        v.appendChild(t);
      }
      grid.appendChild(v);
    }
    others.appendChild(grid); p.appendChild(others);
  }
  function varCard(c, tint) {
    const v = el("div", "dsx-var"); v.dataset.col = c.name;
    v.append(el("span", "dsx-name", c.name), el("div", "dsx-meaning", c.meaning));
    if (c.units) v.appendChild(el("span", "dsx-unitchip", c.units));
    if (c.summary) v.appendChild(strip(c, tint));
    return v;
  }
  // A distribution strip over ALL rows: histogram, the middle half shaded, a median tick. Only the axis ends are
  // labelled (rounded; see niceBounds in the model).
  function strip(c, tint) {
    const NS = "http://www.w3.org/2000/svg";
    const W = 320, H = 76, top = 6, base = 50, { lo, hi } = c.axis;
    const x = val => ((val - lo) / (hi - lo)) * W;
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "dsx-strip"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("role", "img"); svg.setAttribute("aria-label", `How ${c.name} is spread across all rows`);
    const add = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); svg.appendChild(e); return e; };
    const s = c.summary;
    add("rect", { x: x(s.q1), y: top, width: Math.max(1, x(s.q3) - x(s.q1)), height: base - top, fill: "rgba(255,255,255,.07)" });
    const peak = Math.max(...c.bins) || 1, nb = c.bins.length;
    const perValue = c.integer && (s.max - s.min) <= 40;
    c.bins.forEach((n, i) => {
      if (!n) return;
      const x0 = perValue ? x(s.min + i - 0.4) : x(s.min + (i / nb) * (s.max - s.min));
      const x1 = perValue ? x(s.min + i + 0.4) : x(s.min + ((i + 1) / nb) * (s.max - s.min));
      const h = Math.max(1.5, (n / peak) * (base - top));
      add("rect", { x: x0, y: base - h, width: Math.max(1, x1 - x0 - (perValue ? 0 : 0.6)), height: h, fill: tint, opacity: 0.85 });
    });
    add("line", { x1: x(s.median), x2: x(s.median), y1: top - 2, y2: base, stroke: "#fff", "stroke-width": 1.5, "vector-effect": "non-scaling-stroke" });
    add("line", { x1: 0, x2: W, y1: base + 0.5, y2: base + 0.5, stroke: "rgba(255,255,255,.4)", "vector-effect": "non-scaling-stroke" });
    const t1 = add("text", { x: 1, y: H - 6, "text-anchor": "start" }); t1.textContent = c.text.lo;
    const t2 = add("text", { x: W - 1, y: H - 6, "text-anchor": "end" }); t2.textContent = c.text.hi;
    if (x(s.median) > W * 0.2 && x(s.median) < W * 0.8) {      // only where it cannot sit on an axis label
      const t3 = add("text", { x: x(s.median), y: H - 6, "text-anchor": "middle", class: "dsx-medlabel" }); t3.textContent = "median";
    }
    return svg;
  }

  return {
    ready,
    destroy() { dead = true; root.remove(); },
  };
}

export { fmtCount };
