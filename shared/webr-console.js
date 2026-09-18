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
 * `addStatusEl()`, `plotControls(opts)`, `resetSession()`, `resetControl(opts)`, `.ready`, `.webR`.
 */
import { WebR } from "https://webr.r-wasm.org/latest/webr.mjs";
import { VIEW_R_SHIM, VIEW_R_DRAIN, fromR, viewTableHTML, ensureViewStyles } from "./webr_view.js?v=105";
import { codeToRun, selectionNote } from "./code_sel.js?v=105";
import { PLOT_ASPECTS, PLOT_DEFAULT_ASPECT, PLOT_LIMITS, PLOT_CTL_CSS, plotGeometry } from "./plot_size.js?v=105";
import { RESET_R_SHIM, RESET_R_CALL, RESET_CTL_CSS, RESET_LABEL, RESET_CONFIRM_LABEL, RESET_CONFIRM_MS, nextConfirmState } from "./webr_reset.js?v=105";
import { explainError, looksLikeOrphanLayer } from "./r_diagnose.js?v=105";

const errText = e => (e && e.message ? e.message : String(e));

/*
 * The error line as a student should read it. webR builds its message as "Error in `<call>`: <msg>", so
 * the old `"Error: " + errText(err)` rendered "Error: Error in `mean(x)`: …" — the word twice, before
 * they have read anything. Prefix only when R has not already said it.
 */
/*
 * A message() or warning() condition as the line a student should see. Read from the condition object
 * while its shelter is still alive (run() calls this before purge). Warnings are labelled the way R labels
 * them, because "Warning message:" is what the student will meet again in RStudio; a message() is shown
 * bare, as R shows it. Unreadable → nothing, never a throw: a missing warning is a nuisance, a run that
 * dies on its way to the output is not.
 */
async function conditionLine(o) {
  try {
    const msg = String(await (await o.data.get("message")).toString()).replace(/\n+$/, "");
    return o.type === "warning" ? "Warning message:\n" + msg : msg;
  } catch (e) {
    return "";
  }
}

function errLine(err) {
  const t = errText(err);
  return /^Error\b/.test(t.trim()) ? t : "Error: " + t;
}

/*
 * The plain-English gloss under an R error. Injected HERE rather than written into each surface's CSS,
 * because the whole point of moving the hints into the shared console is that a room and the book cannot
 * drift apart — and a hint that renders unstyled in one of them is exactly that drift, in a form nobody
 * notices until a student meets it.
 *
 * Styled SUBORDINATE to R's own message on purpose: the student reads R's words first and ours second,
 * because R's are the ones they will meet again in RStudio where we are not there to translate.
 *
 * Colours are hard-coded rather than taken from CSS variables: the three surfaces define different
 * variable names (the rooms' palette is per-scenario), and a var() that does not resolve renders
 * invisible text. These are the sandbox's amber/green on a dark pane, which all three share.
 */
const HINT_CSS = `
.webr-hintbox { border-left:3px solid #ffd88c; background:rgba(255,216,140,.06);
                padding:8px 12px; margin:-2px 0 8px; border-radius:0 6px 6px 0; font-size:13px;
                line-height:1.45; color:inherit; }
.webr-hintbox .webr-hlabel { font-size:11px; letter-spacing:.06em; color:#ffd88c; opacity:.85;
                             display:block; margin-bottom:3px; }
.webr-hintbox .webr-htry { display:block; margin-top:6px;
                           font:12.5px ui-monospace, Menlo, Consolas, monospace; color:#9be89b; }
`;

function ensureHintStyles(doc) {
  const d = doc || document;
  if (d.getElementById("webr-hint-styles")) return;
  const st = d.createElement("style");
  st.id = "webr-hint-styles";
  st.textContent = HINT_CSS;
  d.head.appendChild(st);
}


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

function ensureResetCtlStyles(doc) {
  const d = doc || document;
  if (d.getElementById("webr-resetctl-styles")) return;
  const st = d.createElement("style");
  st.id = "webr-resetctl-styles";
  st.textContent = RESET_CTL_CSS;
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
    // Every reset button built for this session, so init() can enable them all when R comes up. Same
    // pattern as statusEls/plotCtls: consumers build the control before boot (the rooms do it in
    // bootConsole, the sandbox at module scope), and a reset before .__reset exists would report a
    // failure the student can do nothing about.
    this.resetCtls = new Set();
    // Extra context for the error hints, set by the surface after construction. Only for things that
    // differ BETWEEN surfaces — e.g. sandbox.html sets {envLabel:"Environment pane"}, which a room must
    // not say because it has no such pane. See hintCtx().
    this.hintContext = null;
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
        // Off the live site (test play on localhost, the e2e servers), prefer THIS checkout's copy of a
        // dataset published under thebustalab.github.io — otherwise every local test silently reads the last
        // DEPLOYED CSV, not the one just engineered (beacons' v2 ledger, 2026-09-16). On the live site the
        // URL is used as-is; locally a missing copy falls back to the published one.
        const SITE = "https://thebustalab.github.io";
        let resp = null;
        if (location.origin !== SITE && ds.url.startsWith(SITE + "/")) {
          try { const r = await fetch(location.origin + ds.url.slice(SITE.length), { cache: "no-store" }); if (r.ok) resp = r; } catch (e) {}
        }
        if (!resp) resp = await fetch(ds.url);
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

      /*
       * LAST, on purpose: resetSession() restores whatever the global environment holds at this moment,
       * so anything evaluated after this line would be missing from the state a reset restores. Keep new
       * boot steps ABOVE it. A failure here would brick the boot for a convenience feature, so it is
       * swallowed — resetSession()'s exists() guard then reports the control as unavailable.
       */
      try { await this.webR.evalRVoid(RESET_R_SHIM); } catch (e) { /* reset is optional; the session is not */ }

      this.ready = true;
      this.resetCtls.forEach(b => { b.disabled = false; });
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

  // Returns the <pre> it appended (or null), so a caller can attach a hint box directly after it.
  appendText(text, cls, outEl) {
    const out = outEl || this.ui.output;
    if (!out) return null;
    const pre = document.createElement("pre");
    pre.className = "webr-out " + (cls || "");
    pre.textContent = text;
    out.appendChild(pre);
    return pre;
  }

  /*
   * Render one hint from r_diagnose.js directly beneath `afterEl`.
   *
   * `.dataset.hinted` guards against a second pass double-annotating the same line. It also lets a
   * surface that still runs its OWN annotation (sandbox.html did, before the hints moved in here) win
   * the race without the student seeing two boxes — which matters during the push window, when the
   * rooms repo has deployed and the book repo has not yet.
   */
  appendHint(hint, afterEl) {
    if (!hint || !afterEl || afterEl.dataset.hinted) return false;
    afterEl.dataset.hinted = "1";
    ensureHintStyles(afterEl.ownerDocument);
    const div = afterEl.ownerDocument.createElement("div");
    div.className = "webr-hintbox";
    const lab = afterEl.ownerDocument.createElement("span");
    lab.className = "webr-hlabel";
    lab.textContent = "WHAT THAT MEANS";
    div.appendChild(lab);
    div.appendChild(afterEl.ownerDocument.createTextNode(hint.message));
    if (hint.try) {
      const t = afterEl.ownerDocument.createElement("span");
      t.className = "webr-htry";
      t.textContent = hint.try;
      div.appendChild(t);
    }
    afterEl.insertAdjacentElement("afterend", div);
    return true;
  }

  /*
   * The names that exist in the student's session RIGHT NOW, as candidates for "did you mean".
   *
   * Read on demand — only when a run has actually errored — so the common path pays nothing. Failure is
   * not interesting: no candidates simply means the hint says "check the spelling" instead of naming a
   * near-miss, which is still a useful hint.
   */
  async hintObjects(shelter) {
    try {
      const js = await (await shelter.evalR("ls()")).toJs();
      return Array.isArray(js.values) ? js.values.filter(v => typeof v === "string") : [];
    } catch (e) {
      return [];
    }
  }

  /*
   * Context handed to r_diagnose.js. `hintContext` is the hook a surface uses to say what IT has on
   * screen — sandbox.html sets {envLabel:"Environment pane"}; a room leaves it unset, because naming a
   * pane a student cannot see sends them hunting for UI that is not there.
   */
  hintCtx(source, objects) {
    const cfg = this.config || {};
    return Object.assign({
      source: source || "",
      objects: objects || [],
      packages: cfg.packages || [],
      datasets: (cfg.datasets || []).map(d => d && d.name).filter(Boolean),
    }, this.hintContext || {});
  }

  /*
   * Put a plain-English hint under what just went wrong — the shared half of what used to be
   * sandbox.html's annotateErrors().
   *
   * `code` is what ACTUALLY ran, which is the highlighted selection when there is one. That matters: the
   * structural analysis reads the source to find the real bracket fault, and handing it the whole editor
   * would make it report brackets R was never asked to read. (A stray part-line selection producing a
   * baffling parse error is itself one of the commonest confusions on this console.)
   *
   * Two distinct cases, and the second has no error at all: `ggplot(...)` followed by `geom_point()` with
   * no trailing `+` runs as two expressions, prints the layer's internals and draws a blank panel. The
   * student sees output and reasonably assumes it worked. It must NOT be gated on "no plot present" —
   * `ggplot(d, aes(...))` alone DOES render a blank panel, so the case produces a canvas AND the stray
   * text; gating on the absence of a plot made the check never fire (caught 2026-09-13 in the browser).
   */
  async annotateErrors(shelter, out, code, errEl, plainEl) {
    if (errEl) {
      // Candidate names are read only now, on the error path, so a working run pays nothing for them.
      const objects = await this.hintObjects(shelter);
      this.appendHint(explainError(errEl.textContent || "", this.hintCtx(code, objects)), errEl);
      return;
    }
    if (!plainEl) return;
    this.appendHint(looksLikeOrphanLayer(plainEl.textContent || ""), plainEl);
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
   * Put the R session back exactly as it booted: datasets restored to their loaded values, everything
   * the student has made since removed, the caller's `setup` helpers and view() back. The EDITOR is
   * never touched — that is the whole reason this exists rather than "reload the page".
   *
   * Resolves true on success, false if the session predates the shim (a cached page meeting an older
   * console across the two repos' separate deploys). A caller should say "reload the page for a full
   * restart" on false rather than pretending it worked.
   *
   * Clears `lastRun` as well as the output: otherwise the next plot-size change would re-run code
   * against objects the reset has just removed.
   */
  async resetSession(outEl) {
    if (!this.webR) return false;
    let done = false;
    let shelter = null;
    try {
      shelter = await new this.webR.Shelter();
      const r = await (await shelter.evalR(RESET_R_CALL)).toJs();
      done = Array.isArray(r.values) && r.values[0] === true;
    } catch (e) {
      done = false;
    } finally {
      if (shelter) shelter.purge();
    }
    if (!done) return false;
    const out = outEl || this.ui.output;
    this.clearOutput(out);
    this.lastRun = null;
    this.appendText(
      "Session reset. The datasets are back as they loaded and everything made since is gone. Your code is untouched.",
      "muted", out);
    return true;
  }

  /*
   * Build a "reset session" button bound to this console and return it for the caller to place — same
   * contract as plotControls(): the console owns the behaviour, consumers only choose where it goes.
   *
   * TWO-STEP CONFIRM, and it expires. A reset destroys every object the student has built; one stray
   * click after twenty minutes of work is a bad way to learn that. The arming window lives in
   * webr_reset.js's nextConfirmState() so the expiry rule is unit-tested without a browser — an armed
   * button that stayed armed for ever would be its own trap.
   *
   * opts.output — the element to clear and report into (the book's cells each have their own).
   * opts.onDone — called after a successful reset, e.g. to refresh the sandbox's Environment pane.
   * opts.document — for a consumer building into another document.
   */
  resetControl(opts) {
    const o = opts || {};
    const doc = o.document || document;
    ensureResetCtlStyles(doc);

    const btn = doc.createElement("button");
    btn.type = "button";
    btn.className = "webr-resetctl";
    btn.textContent = RESET_LABEL;
    btn.disabled = !this.ready;
    this.resetCtls.add(btn);
    btn.title = "Put the R session back exactly as it loaded: the datasets restored, everything you have made since removed. Your code is untouched.";

    let state = { armedAt: null };
    let timer = null;
    const disarm = () => {
      state = { armedAt: null };
      if (timer) { clearTimeout(timer); timer = null; }
      btn.classList.remove("armed");
      btn.textContent = RESET_LABEL;
    };

    btn.addEventListener("click", async () => {
      if (btn.disabled) return;
      const next = nextConfirmState(state, Date.now());
      state = { armedAt: next.armedAt };
      if (next.action === "arm") {
        btn.classList.add("armed");
        btn.textContent = RESET_CONFIRM_LABEL;
        if (timer) clearTimeout(timer);
        timer = setTimeout(disarm, RESET_CONFIRM_MS);
        return;
      }
      disarm();
      btn.disabled = true;
      this.setStatus("Resetting the R session…");
      let done = false;
      try { done = await this.resetSession(o.output); } catch (e) { done = false; }
      this.setStatus(done ? "R is ready. Type code below and press Run."
                          : "Could not reset the session — reload the page for a full restart.");
      btn.disabled = false;
      if (done && typeof o.onDone === "function") { try { await o.onDone(); } catch (e) { /* never break the reset */ } }
    });
    return btn;
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
    // Held for the hint pass in `finally`: the error line to explain, and the plain output line that a
    // stray ggplot layer would have been printed into (the one failure that produces no error at all).
    let errEl = null, plainEl = null;
    // Measured AFTER the boot await, so the geometry reflects the pane as it is when the plot lands.
    const geom = this.plotGeometryFor(out);
    try {
      const result = await shelter.captureR(code, {
        withAutoprint: true,
        captureStreams: true,
        // Do NOT pass `captureConditions: false`. It looks like the one-flag way to make message() and
        // warning() visible, and it was shipped as exactly that on 2026-09-17 — and it silently switched
        // off every error hint on all three surfaces. With the flag, an R error is no longer THROWN: R
        // prints it to stderr and captureR returns normally, so the catch below never runs, nothing is
        // marked as an error, and annotateErrors() has nothing to explain. It also buys nothing for the
        // error text — measured against real webR, it gives the same one-line headline, minus the
        // function name the thrown version carries. Warnings and messages are rendered below instead.
        captureGraphics: { width: geom.width, height: geom.height },
      });
      // Output in the order R produced it. message() and warning() arrive as CONDITION entries rather
      // than stream text, so they are turned into lines here — without this a run whose only output was
      // a warning showed "(no output)", and students never saw R's warnings at all.
      const lines = [];
      for (const o of result.output) {
        if (o.type === "stdout" || o.type === "stderr") lines.push(o.data);
        else if (o.type === "warning" || o.type === "message") {
          const line = await conditionLine(o);
          if (line) lines.push(line);
        }
      }
      const text = lines.join("\n");
      if (text.trim().length) { plainEl = this.appendText(text, "", out); rendered++; }
      for (const img of (result.images || [])) { await this.appendImage(img, out, geom); rendered++; }
    } catch (err) {
      errEl = this.appendText(errLine(err), "err", out);
      rendered++;
    } finally {
      // Drain views even after an error: view() may have run on a line BEFORE the one that failed, and
      // an undrained queue would otherwise surface those tables on the student's next, unrelated run.
      try { rendered += await this.appendViews(shelter, out); } catch (e) { /* viewer never breaks a run */ }
      if (!rendered) this.appendText("(no output)", "muted", out);
      // Explain the error in plain English — for EVERY surface, which is the point of it living here.
      // This used to be wired into sandbox.html alone, so the rooms (the homework for the very chapters
      // the sandbox demonstrates in class) showed a raw, misleading parse error with no explanation.
      //
      // Wrapped so a hint can never break a run: a missing explanation is a nuisance, a Run button that
      // throws is the 2026-09-04 outage again. Same reasoning as appendViews above.
      try { await this.annotateErrors(shelter, out, code, errEl, plainEl); }
      catch (e) { /* a hint never breaks a run */ }
      shelter.purge();
    }
  }
}
