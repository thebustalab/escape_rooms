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
 * `addStatusEl()`, `.ready`, `.webR`.
 */
import { WebR } from "https://webr.r-wasm.org/latest/webr.mjs";
import { VIEW_R_SHIM, VIEW_R_DRAIN, fromR, viewTableHTML, ensureViewStyles } from "./webr_view.js?v=88";
import { codeToRun, selectionNote } from "./code_sel.js?v=88";

const errText = e => (e && e.message ? e.message : String(e));

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

  async appendImage(imageBitmap, outEl) {
    const out = outEl || this.ui.output;
    if (!out) return;
    const canvas = document.createElement("canvas");
    canvas.width = imageBitmap.width;
    canvas.height = imageBitmap.height;
    canvas.className = "webr-plot";
    canvas.getContext("2d").drawImage(imageBitmap, 0, 0);
    out.appendChild(canvas);
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
    if (note) this.appendText(note, "muted", out);
    if (!this.ready) {
      try { await this.init(); }
      catch (err) { this.appendText("R failed to start: " + errText(err), "err", out); return; }
    }
    const shelter = await new this.webR.Shelter();
    let rendered = 0;
    try {
      const result = await shelter.captureR(code, {
        withAutoprint: true,
        captureStreams: true,
        captureGraphics: { width: 720, height: 460 },
      });
      const text = result.output
        .filter((o) => o.type === "stdout" || o.type === "stderr")
        .map((o) => o.data)
        .join("\n");
      if (text.trim().length) { this.appendText(text, "", out); rendered++; }
      for (const img of (result.images || [])) { await this.appendImage(img, out); rendered++; }
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
