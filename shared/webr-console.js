/*
 * webr-console.js — a minimal live R console backed by WebR.
 *
 * Loads WebR, installs the scenario's packages, fetches its datasets into the
 * WebR virtual filesystem, runs any setup R, and then runs student-typed R,
 * showing text output and rendering any plots to a canvas.
 *
 * WebR runs entirely in the student's browser tab — there is no server.
 */
import { WebR } from "https://webr.r-wasm.org/latest/webr.mjs";

export class WebRConsole {
  constructor(config, ui) {
    this.config = config;         // { packages, datasets:[{name,url}], setup }
    this.ui = ui;                 // { status, output, input, runButton }
    this.webR = null;
    this.ready = false;
  }

  setStatus(msg) {
    if (this.ui.status) this.ui.status.textContent = msg;
  }

  async init() {
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

    if (this.config.setup) {
      this.setStatus("Preparing session…");
      await this.webR.evalRVoid(this.config.setup);
    }

    this.ready = true;
    this.setStatus("R is ready. Type code below and press Run.");
  }

  clearOutput() {
    if (this.ui.output) this.ui.output.innerHTML = "";
  }

  appendText(text, cls) {
    const pre = document.createElement("pre");
    pre.className = "webr-out " + (cls || "");
    pre.textContent = text;
    this.ui.output.appendChild(pre);
  }

  async appendImage(imageBitmap) {
    const canvas = document.createElement("canvas");
    canvas.width = imageBitmap.width;
    canvas.height = imageBitmap.height;
    canvas.className = "webr-plot";
    canvas.getContext("2d").drawImage(imageBitmap, 0, 0);
    this.ui.output.appendChild(canvas);
  }

  async run(code) {
    if (!this.ready) return;
    this.clearOutput();
    const shelter = await new this.webR.Shelter();
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
      if (text.trim().length) this.appendText(text);
      for (const img of (result.images || [])) {
        await this.appendImage(img);
      }
      if (!text.trim().length && !(result.images || []).length) {
        this.appendText("(no output)", "muted");
      }
    } catch (err) {
      this.appendText("Error: " + (err && err.message ? err.message : err), "err");
    } finally {
      shelter.purge();
    }
  }
}
