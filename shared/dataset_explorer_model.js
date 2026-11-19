// Editing this? Read _agent_reference/instruments_and_widgets.md first (the `dataset_explorer` kind).
/*
 * dataset_explorer_model.js: the pure half of the dataset explorer (no DOM, no fetch, no imports), so node can
 * test it and the leak guard can read EXACTLY what the board shows.
 *
 * STRUCTURE ONLY (Lucas, 2026-11-19). The explorer shows what one row is, the groups (split and response) and each
 * variable with its units and spread over ALL rows. It never puts the response against any variable: no counts of
 * the response within a split, no per-response summaries, no correlations. Those are what the graded ladders test.
 * Every number the board prints is produced here and listed in `model.displayed`, which the leak guard
 * (tests/dataset_explorer_leak.test.mjs) checks against each room's private answer key.
 *
 * Descriptor (JSON beside the CSV):
 *   { title, dataset, csv (path relative to the descriptor),
 *     row: { noun, nounPlural, phrase, kicker?, look: "logsheet"|"plate" },
 *     blocks?: [{ id, title, blurb? }],
 *     columns: [{ name, role: identifier|split|response|predictor|flag, block?, meaning, units?,
 *                 levels?: { <value>: <plain meaning> } }] }
 */

export const ROLES = ["identifier", "split", "response", "predictor", "flag"];

// Words that would label a predictor with its ladder role or rank it: answers, never descriptions.
export const FORBIDDEN_WORDS = ["driver", "drivers", "trap", "traps", "noise", "noisy", "decoy", "decoys", "rank",
  "ranked", "ranking", "important", "importance", "strongest", "weakest", "signal", "irrelevant", "useless"];

export function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
    } else cell += c;
  }
  if (cell !== "" || row.length) { row.push(cell); if (row.length > 1 || row[0] !== "") rows.push(row); }
  const header = rows.shift() || [];
  return { header, rows };
}

const isNum = s => s !== "" && s !== "NA" && Number.isFinite(Number(s));
const decimalsOf = s => { const m = /\.(\d+)$/.exec(String(s).trim()); return m ? m[1].length : 0; };
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

// R's default quantile (type 7) on a sorted array
export function quantile(sorted, p) {
  if (!sorted.length) return NaN;
  const h = (sorted.length - 1) * p, lo = Math.floor(h), hi = Math.ceil(h);
  return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
}

export function fmtCount(n) {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// A measurement at the column's own precision; a value that precision cannot hold (an even-count median between two
// integers) gets one more decimal rather than being silently rounded.
export function fmtValue(v, dec) {
  let s = v.toFixed(dec);
  if (Math.abs(Number(s) - v) > 1e-9) s = v.toFixed(dec + 1);
  return s;
}

export function descriptorProblems(desc, header) {
  const out = [];
  if (!desc || typeof desc !== "object") return ["the descriptor is not an object"];
  for (const k of ["title", "dataset", "csv"]) if (!desc[k] || typeof desc[k] !== "string") out.push(`needs a \`${k}\``);
  const row = desc.row || {};
  for (const k of ["noun", "nounPlural", "phrase"]) if (!row[k]) out.push(`row needs a \`${k}\``);
  if (row.look && !["logsheet", "plate"].includes(row.look)) out.push(`row.look must be "logsheet" or "plate"`);
  const cols = Array.isArray(desc.columns) ? desc.columns : [];
  if (!cols.length) out.push("needs `columns`");
  const blockIds = new Set((desc.blocks || []).map(b => b.id));
  const count = r => cols.filter(c => c.role === r).length;
  for (const r of ["identifier", "split", "response"]) if (count(r) !== 1) out.push(`needs exactly one ${r} column (has ${count(r)})`);
  if (count("predictor") < 1) out.push("needs at least one predictor column");
  for (const c of cols) {
    if (!c.name) { out.push("a column has no name"); continue; }
    if (!ROLES.includes(c.role)) out.push(`column ${c.name}: role ${JSON.stringify(c.role)} is not one of ${ROLES.join(", ")}`);
    if (!c.meaning) out.push(`column ${c.name}: needs a plain \`meaning\``);
    if (c.role === "predictor" && blockIds.size && !blockIds.has(c.block)) out.push(`column ${c.name}: block ${JSON.stringify(c.block)} is not declared in \`blocks\``);
  }
  for (const [where, text] of descriptorTexts(desc)) {
    const hit = FORBIDDEN_WORDS.find(w => new RegExp(`\\b${w}\\b`, "i").test(text));
    if (hit) out.push(`${where}: the word "${hit}" labels or ranks a variable (a ladder answer); describe it neutrally`);
  }
  if (header) {
    const names = cols.map(c => c.name);
    const missing = header.filter(h => !names.includes(h)), extra = names.filter(n => !header.includes(n));
    if (missing.length) out.push(`the CSV has columns the descriptor does not describe: ${missing.join(", ")}`);
    if (extra.length) out.push(`the descriptor describes columns the CSV lacks: ${extra.join(", ")}`);
  }
  return out;
}

// Every piece of descriptor prose the board prints, with where it came from.
export function descriptorTexts(desc) {
  const out = [["title", desc.title], ["row.phrase", (desc.row || {}).phrase], ["row.kicker", (desc.row || {}).kicker],
               ["row.noun", (desc.row || {}).noun], ["row.nounPlural", (desc.row || {}).nounPlural]];
  for (const b of desc.blocks || []) out.push([`block ${b.id} title`, b.title], [`block ${b.id} blurb`, b.blurb]);
  for (const c of desc.columns || []) {
    out.push([`column ${c.name} meaning`, c.meaning], [`column ${c.name} units`, c.units]);
    for (const [lv, m] of Object.entries(c.levels || {})) out.push([`column ${c.name} level ${lv}`, m]);
  }
  return out.filter(([, t]) => typeof t === "string" && t);
}

function histogram(vals, min, max, integer) {
  const span = max - min;
  const nb = integer && span <= 40 ? Math.max(1, span + 1) : 30;
  const bins = new Array(nb).fill(0);
  for (const v of vals) {
    let i = integer && span <= 40 ? v - min : Math.floor(((v - min) / (span || 1)) * nb);
    if (i >= nb) i = nb - 1;
    if (i < 0) i = 0;
    bins[i]++;
  }
  return bins;
}

export function buildModel(desc, csvText) {
  const { header, rows } = parseCsv(csvText);
  const problems = descriptorProblems(desc, header);
  const idx = Object.fromEntries(header.map((h, i) => [h, i]));
  const n = rows.length;
  const displayed = [];
  const show = (where, text, kind = "number") => { displayed.push({ where, text: String(text), kind }); return String(text); };
  const plural = (desc.row && desc.row.nounPlural) || "rows";

  const columns = (desc.columns || []).filter(c => c.name in idx).map(c => {
    const raw = rows.map(r => r[idx[c.name]]);
    const numeric = c.role === "predictor" && raw.every(isNum);
    const col = { ...c, raw, numeric, index: idx[c.name] };
    if (numeric) {
      const vals = raw.map(Number), sorted = [...vals].sort((a, b) => a - b);
      const dec = Math.max(...raw.map(decimalsOf));
      const integer = dec === 0;
      const min = sorted[0], max = sorted[sorted.length - 1];
      col.decimals = dec;
      col.summary = { min, q1: quantile(sorted, 0.25), median: quantile(sorted, 0.5), q3: quantile(sorted, 0.75), max };
      col.bins = histogram(vals, min, max, integer);
      col.integer = integer;
      col.axis = niceBounds(min, max);
      const tick = v => { const s = v.toFixed(col.axis.dec); return s.includes(".") ? s.replace(/0+$/, "").replace(/\.$/, "") : s; };   // "1.00" -> "1", "1.50" -> "1.5", "30" stays
      col.text = {      // the only numbers a variable card prints: its axis ends
        lo: show(`${c.name} axis low end`, tick(col.axis.lo)),
        hi: show(`${c.name} axis high end`, tick(col.axis.hi)),
      };
    } else {
      // categories in descriptor order first, then any others in order of first appearance
      const order = Object.keys(c.levels || {});
      for (const v of raw) if (!order.includes(v)) order.push(v);
      col.levels = order.map(v => ({ value: v, meaning: (c.levels || {})[v] || "", count: raw.filter(x => x === v).length }));
      if (c.role === "predictor") problems.push(`column ${c.name}: a predictor must be numeric (found non-numbers)`);
      for (const lv of Object.keys(c.levels || {}))
        if (!raw.includes(lv)) problems.push(`column ${c.name}: level ${JSON.stringify(lv)} never occurs in the CSV`);
    }
    return col;
  });
  const byRole = r => columns.filter(c => c.role === r);
  const id = byRole("identifier")[0], split = byRole("split")[0], response = byRole("response")[0];

  const model = {
    title: desc.title, dataset: desc.dataset, row: desc.row || {}, nRows: n, nCols: header.length, header, rows,
    columns, problems, displayed,
    blocks: (desc.blocks && desc.blocks.length ? desc.blocks : [{ id: null, title: "Predictors" }])
      .map(b => ({ ...b, columns: byRole("predictor").filter(c => desc.blocks && desc.blocks.length ? c.block === b.id : true) })),
    others: columns.filter(c => c.role !== "predictor"),
    text: {
      nRows: show("rows", fmtCount(n)),
      nCols: show("columns", fmtCount(header.length)),
    },
  };

  if (id) {
    const dates = id.raw.every(s => DATE_RE.test(s));
    const ids = dates ? [...id.raw].sort() : id.raw;
    model.identifier = { column: id, dates, distinct: new Set(id.raw).size,
                         first: show(`${id.name} first`, ids[0], "string"),
                         last: show(`${id.name} last`, ids[ids.length - 1], "string"),
                         example: show(`${id.name} example`, id.raw[0], "string") };
    model.identifier.distinctText = show(`${id.name} distinct`, fmtCount(model.identifier.distinct));
  }
  // The two groupings, each counted over ALL rows on its own (never crossed with each other or with a variable).
  // The RESPONSE is never counted exactly (Lucas, 2026-11-19): its exact counts give the always-"no" accuracy, which
  // the graded bosses use (observatory: 2,180 of 2,300 = a key). Its bar is drawn to scale and worded roughly.
  const total = n || 1;
  const roughText = (what, l) => {
    if (l.count / total >= 0.5) return show(`${what} ${l.value} rough`, "most", "string");
    // A rare response is worded only as "fewer than 1 in 10": "about 1 in 22" still carried the whole-record
    // always-"no" accuracy (lair's 95.5% trap figure; adversarial check, 2026-11-19).
    show(`${what} ${l.value} rough one`, "1", "phrase");
    if (l.count / total < 0.1) { show(`${what} ${l.value} rough`, "10", "phrase"); return "fewer than 1 in 10"; }
    const k = Math.max(2, Math.round(total / Math.max(1, l.count)));
    show(`${what} ${l.value} rough`, String(k));
    return `about 1 in ${fmtCount(k)}`;
  };
  const groups = (col, what) => col && col.levels.map(l => {
    const g = { ...l, countText: what === "response" ? roughText(what, l) : show(`${what} ${l.value}`, fmtCount(l.count)) };
    if (what === "split" && model.identifier && model.identifier.dates) {
      const ds = id.raw.filter((_, i) => col.raw[i] === l.value).sort();
      g.first = show(`split ${l.value} first ${id.name}`, ds[0], "string");
      g.last = show(`split ${l.value} last ${id.name}`, ds[ds.length - 1], "string");
    }
    return g;
  });
  model.split = split && { column: split, groups: groups(split, "split") };
  model.response = response && { column: response, groups: groups(response, "response") };
  // Flags are never counted: lair's alarm count beside the response bounded how many eruption days the alarm
  // missed, the lair boss's insight (adversarial check, 2026-11-19). The board names them and their values only.
  // Numbers written into the descriptor's own prose are displayed too, so the guard sees them.
  for (const [where, t] of descriptorTexts(desc))
    for (const m of t.matchAll(/(?<![\w.-])\d[\d,]*(?:\.\d+)?/g)) show(`descriptor ${where}`, m[0]);
  model.plural = plural;
  return model;
}

// The row-card values for one row: raw cells, grouped as the board shows them.
export function rowView(model, i) {
  const r = model.rows[i] || [];
  const cell = c => r[c.index];
  return {
    index: i,
    id: model.identifier ? cell(model.identifier.column) : "",
    split: model.split ? cell(model.split.column) : "",
    response: model.response ? cell(model.response.column) : "",
    blocks: model.blocks.map(b => ({ ...b, cells: b.columns.map(c => ({ column: c, value: cell(c) })) })),
    flags: model.columns.filter(c => c.role === "flag").map(c => ({ column: c, value: cell(c) })),
  };
}

// The guard's comparison: does a displayed number equal a key at the number's displayed precision? An exactly equal
// key always matches. A key that only ROUNDS to the shown number matches when the shown number carries at least two
// significant figures ("0.50" or "28" can hand over a key; "0.5" or "1" says nothing about 0.4983 or 0.9945).
export function sigFigs(t) {
  const digits = String(t).replace(/[^0-9]/g, "").replace(/^0+/, "");
  return Math.max(1, digits.length);
}
export function numberMatchesKey(text, key) {
  const t = String(text).replace(/,/g, "").replace(/%$/, "");
  if (!isNum(t) || !isNum(String(key))) return false;
  const shown = Number(t), k = String(text).endsWith("%") ? Number(key) * 100 : Number(key), dec = decimalsOf(t);
  if (Math.abs(k - shown) < 1e-9) return true;
  return sigFigs(t) >= 2 && Math.abs(k - shown) <= 0.5 * 10 ** -dec + 1e-12;
}

// Rounded axis ends for a variable's strip: a step of 1, 2, 2.5 or 5 x 10^k about a quarter of the range, and the
// data's range widened out to whole steps. The board prints these, never the raw extremes or the median (a raw
// extreme can equal a key by coincidence: lair's largest daily quake count did).
export function niceBounds(min, max) {
  const span = max - min || Math.abs(max) || 1;
  const raw = span / 4, p = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(m => m * p).find(s => s >= raw);
  const lo = Math.floor(min / step + 1e-9) * step, hi = Math.ceil(max / step - 1e-9) * step;
  const dec = Math.max(0, -Math.floor(Math.log10(step) + 1e-9)) + (String(step / p).includes(".") ? 1 : 0);
  return { lo, hi: hi > lo ? hi : lo + step, step, dec };
}
