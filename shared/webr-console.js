/*
 * webr-console.js — a minimal live R console backed by WebR.
 *
 * Loads WebR, installs the scenario's packages, fetches its datasets into the WebR virtual filesystem,
 * defines the `view()` data viewer, runs any setup R, and then runs student-typed R, showing text
 * output, any plots, and any `view()` tables.
 *
 * WebR runs entirely in the student's browser tab — there is no server.
 *
 * THREE surfaces share this one class (consolidated 2026-09-04; the book's runnable cells used to carry
 * a copy-pasted second implementation, which is how the boot-failure bug lived in one and not the other):
 *   - escape_rooms/shared/pano-player.js      — the in-room puzzle console
 *   - integrated_bioanalytics/sandbox.html    — the standalone class-demo console
 *   - integrated_bioanalytics/webr-cell.js    — the book's runnable chapter cells
 * The last two live in a DIFFERENT git repo and import this by its public URL, so treat the exported
 * surface below as a published API: `init()`, `run(code, outEl, note)`, `runFrom(el, outEl)`,
 * `addStatusEl()`, `plotControls(opts)`, `.ready`, `.webR`.
 */
import { WebR } from "https://webr.r-wasm.org/latest/webr.mjs";
import { VIEW_R_SHIM, VIEW_R_DRAIN, fromR, viewTableHTML, ensureViewStyles } from "./webr_view.js?v=89";
import { codeToRun, selectionNote } from "./code_sel.js?v=89";
import { PLOT_ASPECTS, PLOT_DEFAULT_ASPECT, PLOT_LIMITS, PLOT_CTL_CSS, plotGeometry } from "./plot_size.js?v=89";

const errText = e => (e && e.message ? e.message : String(e));

// Plot size + shape is remembered ACROSS pages and rooms: a student who wants tall plots wants them in
// room 4 as well as room 1, and re-picking in every puzzle modal would be its own small tax. A blocked or
// unavailable localStorage (file://, private mode, storage disabled) must degrade to the default, never
// throw — this module boots the whole console.
const PLOT_STORE_KEY = "webrPlotSize.v1";
function loadPlotSize() {
  try {
    const s = JSON.parse(window.localStorage.getItem(PLOT_STORE_KEY) || "{}");
    return {
      scale: Number.isFinite(s.scale) ? s.scale : PLOT_LIMITS.maxScale,
      aspect: PLOT_ASPECTS.some(a => a.key === s.aspect) ? s.aspect : PLOT_DEFAULT_ASPECT,
    };
  } catch (e) {
    return { scale: PLOT_LIMITS.maxScale, aspect: PLOT_DEFAULT_ASPECT };
  }
}
function savePlotSize(size) {
  try { window.localStorage.setItem(PLOT_STORE_KEY, JSON.stringify(size)); } catch (e) { /* not worth a throw */ }
}

function ensurePlotCtlStyles(doc) {
  const d = doc || document;
  if (d.getElementById("webr-plotctl-styles")) return;
  const st = d.createElement("style");
  st.id = "webr-plotctl-styles";
  st.textContent = PLOT_CTL_CSS;
  d.head.appendChild(st);
}

export class WebRConsole {
  constructor(config, ui) {
    this.config = config || {};   // { packages, datasets:[{name,url}], setup }
    this.ui = ui || {};           // { status, output } — both optional; run() can take its own output
    this.webR = null;
    this.ready = false;
    this.booting = null;          // in-flight init promise, so concurrent callers share one boot
    // Every status line to mirror the boot message onto. The book's cells register one per cell (a page
    // has many cells but ONE session, so "Starting R…" has to show wherever the student clicked).
    this.statusEls = new Set();
    if (this.ui.status) this.statusEls.add(this.ui.status);
    // Plot size/shape, shared by every surface this session drives, and every control strip showing it.
    this.plotSize = loadPlotSize();
    this.plotCtls = new Set();
    // The last thing run, so changing the size can re-render it instead of making the student press Run
    // again to see what they just chose. Null until the first run.
    this.lastRun = null;
  }

  addStatusEl(el) { if (el) this.statusEls.add(el); }

  setStatus(msg) { this.statusEls.forEach(el => { el.textContent = msg; }); }

  /*
   * Boot the session. Idempotent and safe to call from every Run: concurrent callers await the same
   * promise, and a completed boot returns immediately.
   *
   * A FAILED boot clears the cached promise and the half-built webR handle (2026-09-04). It used to
   * leave a rejected promise in place, so every later Run re-served the same failure for the life of
   * the page and the status line froze on "Installing R packages…" with nothing said — a flaky fetch
   * of the WebR runtime or one dataset permanently bricked the console.
   */
  async init() {
    if (this.ready) return;
    if (this.booting) return this.booting;
    this.booting = (async () => {
      this.setStatus("Booting R in your browser… (first load ~20–40s)");
      this.webR = new WebR({ interactive: false });
      await this.webR.init();

      const pkgs = this.config.packages || [];
      if (pkgs.length) {
        this.setStatus("Installing R packages: " + pkgs.join(", ") + " …");
        await this.webR.installPackages(pkgs, { quiet: true });
      }

      for (const ds of (this.config.datasets || [])) {
        this.setStatus("Loading data: " + ds.name + " …");
        const resp = await fetch(ds.url);
        if (!resp.ok) throw new Error("Could not fetch dataset: " + ds.url);
        const bytes = new Uint8Array(await resp.arrayBuffer());
        const path = "/home/web_user/" + ds.name + ".csv";
        await this.webR.FS.writeFile(path, bytes);
        await this.webR.evalRVoid(
          `${ds.name} <- readr::read_csv("${path}", show_col_types = FALSE)`
        );
      }

      // view() goes in BEFORE the caller's setup, so a scenario/page that wants its own wins.
      await this.webR.evalRVoid(VIEW_R_SHIM);

      if (this.config.setup) {
        this.setStatus("Preparing session…");
        await this.webR.evalRVoid(this.config.setup);
      }

      this.ready = true;
      this.setStatus("R is ready. Type code below and press Run.");
    })().catch(err => {
      this.booting = null;
      this.webR = null;
      this.setStatus("R failed to start: " + errText(err));
      throw err;
    });
    return this.booting;
  }

  clearOutput(outEl) {
    const out = outEl || this.ui.output;
    if (out) out.innerHTML = "";
  }

  appendText(text, cls, outEl) {
    const out = outEl || this.ui.output;
    if (!out) return;
    const pre = document.createElement("pre");
    pre.className = "webr-out " + (cls || "");
    pre.textContent = text;
    out.appendChild(pre);
  }

  /*
   * `geom` (optional) is the plotGeometry() the image was captured at. The canvas ELEMENT keeps the
   * bitmap's full resolution — webr::canvas hands back 2x what we asked for — while CSS displays it at
   * the logical size, so those extra pixels buy sharpness on a retina screen. Without the CSS size the
   * canvas would lay out at its bitmap size (2x too big) and `max-width:100%` would scale it back down
   * by whatever the pane happened to be, which is the magnification this whole change removes.
   *
   * `height:auto` is safe here because a canvas is a replaced element with an intrinsic aspect ratio, so
   * a pane narrower than cssWidth shrinks it proportionally instead of squashing it.
   */
  async appendImage(imageBitmap, outEl, geom) {
    const out = outEl || this.ui.output;
    if (!out) return;
    const canvas = document.createElement("canvas");
    canvas.width = imageBitmap.width;
    canvas.height = imageBitmap.height;
    canvas.className = "webr-plot";
    if (geom && geom.width) { canvas.style.width = geom.width + "px"; canvas.style.height = "auto"; }
    canvas.getContext("2d").drawImage(imageBitmap, 0, 0);
    out.appendChild(canvas);
  }

  /*
   * The capture geometry for a run, measured from the element the plot will land in — so R lays the plot
   * out for the space it will actually occupy. `clientWidth` includes padding, hence the subtraction;
   * an unmeasurable (hidden) element falls back to a print-worthy default inside plotGeometry.
   */
  plotGeometryFor(outEl) {
    const el = outEl || this.ui.output;
    let availWidth = 0;
    if (el) {
      const win = el.ownerDocument && el.ownerDocument.defaultView;
      const cs = win ? win.getComputedStyle(el) : null;
      const pad = cs ? (parseFloat(cs.paddingLeft) || 0) + (parseFloat(cs.paddingRight) || 0) : 0;
      availWidth = (el.clientWidth || 0) - pad;
    }
    return plotGeometry({ availWidth, scale: this.plotSize.scale, aspect: this.plotSize.aspect });
  }

  /*
   * Change the plot size/shape. Persists it, syncs every control strip showing it, and (unless told not
   * to) re-renders the last run so the student sees the effect of what they just picked.
   */
  setPlotSize(patch, opts) {
    const o = opts || {};
    this.plotSize = { ...this.plotSize, ...(patch || {}) };
    savePlotSize(this.plotSize);
    this.plotCtls.forEach(sync => sync());
    if (o.rerun === false || !this.lastRun || !this.lastRun.code) return;
    /*
     * Only re-render when there is actually a plot ON SCREEN to re-render. Two reasons, one of them a
     * bug this prevents: the escape rooms clear #webr-output THEMSELVES when a puzzle modal opens (the
     * console isn't told), so without this check, changing the size in room 3 before running anything
     * would re-run room 2's code and display room 2's plot in room 3's pane. It also skips a pointless
     * R evaluation when the last run was text-only.
     */
    const out = this.lastRun.outEl;
    if (!out || !out.querySelector || !out.querySelector("canvas.webr-plot")) return;
    const { code, note } = this.lastRun;
    return this.run(code, out, note);
  }

  /*
   * Build a size control strip (a width slider + an aspect picker) bound to this console, and return it
   * for the caller to drop into its own button row. Lives here rather than in each consumer so all the
   * surfaces get the same control, per this dir's AGENTS.md ("add behaviour here, not in a consumer").
   *
   * Two things it deliberately does NOT do:
   *  - No pixel spinboxes. The two things a student actually wants are "bigger" and "a different shape";
   *    a raw width/height pair invites a 200x1400 sliver. Height is always derived from the aspect.
   *  - It re-renders on `change`, not on `input`. Each re-render is a real R evaluation, so re-running on
   *    every pixel of a slider drag would queue dozens of them. Dragging updates the readout only.
   *
   * opts.rerun:false for a caller that captures the plot itself and would be left holding a stale copy
   * (the escape rooms' submission refine blocks re-run through their own button).
   */
  plotControls(opts) {
    const o = opts || {};
    const doc = o.document || document;
    ensurePlotCtlStyles(doc);
    const L = PLOT_LIMITS;

    const wrap = doc.createElement("span");
    wrap.className = "webr-plotctl";

    const sizeLab = doc.createElement("label");
    sizeLab.title = "How wide the plot is drawn, as a share of the space available";
    sizeLab.appendChild(doc.createTextNode("Plot size"));
    const range = doc.createElement("input");
    range.type = "range";
    range.min = String(Math.round(L.minScale * 100));
    range.max = String(Math.round(L.maxScale * 100));
    range.step = "5";
    sizeLab.appendChild(range);
    const val = doc.createElement("span");
    val.className = "webr-plotctl-val";
    sizeLab.appendChild(val);
    wrap.appendChild(sizeLab);

    const shapeLab = doc.createElement("label");
    shapeLab.title = "The plot's shape; its height follows from its width";
    shapeLab.appendChild(doc.createTextNode("Shape"));
    const sel = doc.createElement("select");
    PLOT_ASPECTS.forEach(a => {
      const op = doc.createElement("option");
      op.value = a.key; op.textContent = a.label;
      sel.appendChild(op);
    });
    shapeLab.appendChild(sel);
    wrap.appendChild(shapeLab);

    const sync = () => {
      range.value = String(Math.round(this.plotSize.scale * 100));
      val.textContent = Math.round(this.plotSize.scale * 100) + "%";
      sel.value = this.plotSize.aspect;
    };
    sync();
    this.plotCtls.add(sync);

    // input = readout only (cheap); change = commit + re-render (one R evaluation).
    range.addEventListener("input", () => { val.textContent = range.value + "%"; });
    range.addEventListener("change", () => this.setPlotSize({ scale: Number(range.value) / 100 }, { rerun: o.rerun }));
    sel.addEventListener("change", () => this.setPlotSize({ aspect: sel.value }, { rerun: o.rerun }));
    return wrap;
  }

  // Drain any tables queued by view() during the last run and render them. Evaluated inside the run's
  // own shelter so the returned R object is freed with everything else. A viewer failure must never
  // take down the run that produced real output, hence the swallow.
  async appendViews(shelter, outEl) {
    const out = outEl || this.ui.output;
    if (!out) return 0;
    let tables = [];
    try {
      tables = fromR(await (await shelter.evalR(VIEW_R_DRAIN)).toJs()) || [];
    } catch (e) {
      return 0;
    }
    if (!tables.length) return 0;
    ensureViewStyles(out.ownerDocument);
    for (const t of tables) {
      const wrap = document.createElement("div");
      wrap.className = "webr-view";
      wrap.innerHTML = viewTableHTML(t);
      out.appendChild(wrap);
    }
    return tables.length;
  }

  /*
   * Run whatever the student has highlighted in `el`, or all of `el` if nothing is. Prefer this over
   * run() for any editor a student types into, so the three surfaces behave identically.
   *
   * NOT for the escape rooms' submission refine console: that re-runs a block to regenerate the figure
   * that goes into a GRADED PDF, so a stray selection would silently submit a partial figure. That path
   * calls run() with the whole block on purpose.
   */
  async runFrom(el, outEl) {
    if (!el) return;
    const picked = codeToRun(el.value, el.selectionStart, el.selectionEnd);
    return this.run(picked.code, outEl, selectionNote(picked));
  }

  /*
   * Run `code`, rendering into `outEl` (default: the console's own output element). Boots the session
   * first if needed, so a caller can simply call run() — the book's cells rely on that, since they
   * boot lazily on the student's first click rather than on page load.
   *
   * `note` is an optional muted line rendered above the output (see runFrom). It is deliberately NOT
   * counted as rendered output, so a selection that produces nothing still reports "(no output)".
   */
  async run(code, outEl, note) {
    const out = outEl || this.ui.output;
    this.clearOutput(out);
    // Remembered so setPlotSize() can re-render this exact run at the new size. Recorded BEFORE the boot
    // check, so a size change after a failed boot still has something to retry.
    this.lastRun = { code, outEl: out, note };
    if (note) this.appendText(note, "muted", out);
    if (!this.ready) {
      try { await this.init(); }
      catch (err) { this.appendText("R failed to start: " + errText(err), "err", out); return; }
    }
    const shelter = await new this.webR.Shelter();
    let rendered = 0;
    // Measured AFTER the boot await, so the geometry reflects the pane as it is when the plot lands.
    const geom = this.plotGeometryFor(out);
    try {
      const result = await shelter.captureR(code, {
        withAutoprint: true,
        captureStreams: true,
        captureGraphics: { width: geom.width, height: geom.height },
      });
      const text = result.output
        .filter((o) => o.type === "stdout" || o.type === "stderr")
        .map((o) => o.data)
        .join("\n");
      if (text.trim().length) { this.appendText(text, "", out); rendered++; }
      for (const img of (result.images || [])) { await this.appendImage(img, out, geom); rendered++; }
    } catch (err) {
      this.appendText("Error: " + errText(err), "err", out);
      rendered++;
    } finally {
      // Drain views even after an error: view() may have run on a line BEFORE the one that failed, and
      // an undrained queue would otherwise surface those tables on the student's next, unrelated run.
      try { rendered += await this.appendViews(shelter, out); } catch (e) { /* viewer never breaks a run */ }
      if (!rendered) this.appendText("(no output)", "muted", out);
      shelter.purge();
    }
  }
}
