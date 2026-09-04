/*
 * webr_view.js — the `view()` data viewer shared by every WebR surface.
 *
 * Students arrive with RStudio muscle memory and type `view(algae_data)`. There is no RStudio pane in
 * the browser, so we define `view()` in R ourselves: it stashes a formatted snapshot of the data frame
 * in a hidden environment and returns its argument invisibly. After each run, the JS side drains that
 * queue and renders each snapshot as a scrollable table in the output area.
 *
 * Why a function rather than a "Data" tab: a tab can only ever browse the RAW loaded tables, whereas
 * `view(algae_data %>% filter(...))` shows the DERIVED table — which is the one a student actually
 * wants to look at. It also costs no screen space in the escape-room puzzle modal, which has none.
 *
 * Everything here is pure (strings in, strings out) EXCEPT ensureViewStyles, so it can be unit-tested
 * in Node without a DOM or a live WebR boot — see tests/webr_view.test.mjs. webr-console.js holds the
 * WebR-facing half (which cannot be imported in Node: it imports the runtime from a CDN URL).
 */

// R source injected during boot, BEFORE the scenario/page `setup` — so a setup that defines its own
// `view` still wins. Defined in the global environment, which masks any package's `view` (e.g.
// tibble::view) no matter what is attached later.
export const VIEW_R_SHIM = `
.__view_env <- new.env()
.__view_env$tables <- list()
view <- function(x, n = 1000L) {
  label <- paste(deparse(substitute(x)), collapse = " ")
  if (nchar(label) > 60) label <- paste0(substr(label, 1, 57), "...")
  d <- as.data.frame(x)
  total <- nrow(d)
  shown <- as.integer(min(total, n))
  d2 <- d[seq_len(shown), , drop = FALSE]
  classes <- vapply(d, function(col) class(col)[1], character(1))
  cells <- lapply(d2, function(col) {
    v <- tryCatch(as.character(format(col, trim = TRUE, justify = "none")),
                  error = function(e) rep("?", length(col)))
    if (length(v) != nrow(d2)) v <- rep("?", nrow(d2))
    v[is.na(v)] <- "NA"
    v
  })
  .__view_env$tables[[length(.__view_env$tables) + 1L]] <- list(
    label = label,
    cols = as.character(names(d)),
    classes = unname(classes),
    cells = unname(cells),
    total = as.integer(total),
    shown = shown
  )
  invisible(x)
}
.__view_take <- function() {
  out <- .__view_env$tables
  .__view_env$tables <- list()
  out
}
`;

// R expression the console evaluates after every run to collect (and clear) pending snapshots.
export const VIEW_R_DRAIN = 'if (exists(".__view_take")) .__view_take() else list()';

/*
 * webR's RObject.toJs() returns a tagged tree: {type, names, values}. Flatten it to plain JS —
 * a NAMED list becomes an object, an UNNAMED list an array, and an atomic vector its values array.
 * (An R scalar is still a length-1 vector on the way out, hence `one()` below.)
 */
export function fromR(o) {
  if (o == null) return null;
  if (o.type === "null") return null;
  if (o.type === "list") {
    const vals = (o.values || []).map(fromR);
    if (!o.names) return vals;
    const out = {};
    o.names.forEach((n, i) => { out[n] = vals[i]; });
    return out;
  }
  return o.values;
}

// R has no scalars — a length-1 vector arrives as [x].
export const one = v => (Array.isArray(v) ? v[0] : v);

const CLASS_ABBREV = {
  character: "chr", numeric: "dbl", double: "dbl", integer: "int", logical: "lgl",
  factor: "fct", Date: "date", POSIXct: "time", complex: "cpl", list: "list",
};
export const abbrevClass = c => CLASS_ABBREV[c] || String(c == null ? "" : c);

export const escapeHTML = s =>
  String(s == null ? "" : s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

/*
 * Render one snapshot as the inner HTML of a .webr-view container. Built as a STRING, not per-cell DOM
 * nodes: a 1000-row × 12-column table is 12k cells, and one innerHTML assignment is far cheaper than
 * 12k appendChild calls. Every value goes through escapeHTML, so string-building is not an injection
 * route — data values are chemistry text, but they are still untrusted as far as the DOM is concerned.
 */
export function viewTableHTML(t) {
  t = t || {};
  const label = String(one(t.label) == null ? "data" : one(t.label));
  const cols = (t.cols || []).map(String);
  const classes = (t.classes || []).map(c => (Array.isArray(c) ? c[0] : c));
  const cells = t.cells || [];
  const total = Number(one(t.total) || 0);
  const shown = Number(one(t.shown) || 0);

  const cap = `${label} — ${total} ${total === 1 ? "row" : "rows"} × ` +
              `${cols.length} ${cols.length === 1 ? "column" : "columns"}` +
              (shown < total ? ` · showing the first ${shown}` : "");

  const head = ['<th class="rn"></th>'].concat(cols.map((c, i) =>
    `<th><span class="n">${escapeHTML(c)}</span><span class="c">${escapeHTML(abbrevClass(classes[i]))}</span></th>`
  )).join("");

  const rows = [];
  for (let r = 0; r < shown; r++) {
    const tds = [`<td class="rn">${r + 1}</td>`];
    for (let c = 0; c < cols.length; c++) {
      const col = cells[c] || [];
      tds.push(`<td>${escapeHTML(col[r] == null ? "NA" : col[r])}</td>`);
    }
    rows.push(`<tr>${tds.join("")}</tr>`);
  }
  const body = rows.length
    ? rows.join("")
    : `<tr><td class="rn"></td><td class="empty" colspan="${Math.max(1, cols.length)}">(no rows)</td></tr>`;

  return `<div class="webr-view-cap">${escapeHTML(cap)}</div>` +
         `<div class="webr-view-scroll"><table class="webr-view-table">` +
         `<thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

/*
 * The viewer ships its OWN stylesheet, injected once per document. Three surfaces render these tables
 * — the escape-room puzzle modal (pano-player.css), the book sandbox (inline <style>) and the book's
 * runnable cells (webr-cell.css) — and duplicating the rules into all three is how they drift. All
 * three are dark-themed, so one palette serves; a host sheet can still override by specificity.
 */
export const VIEW_CSS = `
.webr-view { border:1px solid rgba(255,255,255,.14); border-radius:8px; margin:8px 0; overflow:hidden; background:#08131c; }
.webr-view-cap { font:12px ui-monospace,Menlo,Consolas,monospace; padding:6px 10px; color:#ffd88c; border-bottom:1px solid rgba(255,255,255,.14); }
.webr-view-scroll { max-height:340px; overflow:auto; }
.webr-view-table { border-collapse:collapse; font:12px/1.45 ui-monospace,Menlo,Consolas,monospace; width:max-content; min-width:100%; }
.webr-view-table th, .webr-view-table td { padding:3px 10px; border-bottom:1px solid rgba(255,255,255,.07); white-space:nowrap; text-align:left; }
.webr-view-table thead th { position:sticky; top:0; background:#0d1e2b; color:#e8eef2; z-index:1; }
.webr-view-table thead th .n { display:block; }
.webr-view-table thead th .c { display:block; font-weight:400; font-size:10.5px; opacity:.55; }
.webr-view-table td { color:#cfe0ea; }
.webr-view-table th.rn, .webr-view-table td.rn { position:sticky; left:0; text-align:right; color:rgba(255,255,255,.35); background:#08131c; }
.webr-view-table thead th.rn { background:#0d1e2b; z-index:2; }
.webr-view-table td.empty { color:rgba(255,255,255,.45); font-style:italic; }
.webr-view-table tbody tr:hover td { background:rgba(255,216,140,.06); }
`;

const STYLE_ID = "webr-view-styles";
export function ensureViewStyles(doc) {
  const d = doc || (typeof document !== "undefined" ? document : null);
  if (!d || d.getElementById(STYLE_ID)) return;
  const el = d.createElement("style");
  el.id = STYLE_ID;
  el.textContent = VIEW_CSS;
  (d.head || d.documentElement).appendChild(el);
}
