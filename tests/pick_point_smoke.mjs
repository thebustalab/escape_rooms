// pick_point_smoke.mjs — validation for the Type 4 pick-the-point puzzle (NOT in CI).
//
// Proves the exact chain buildPickCard()/renderPickSvg() rely on, end to end in a real headless
// browser, against the REAL alaska data and the SHIPPED plotCode of every pick room in the alaska
// scenario.json (currently R3 chloride + boss water-temperature):
//   boot WebR -> load alaska_lake_data -> lazy-install ggiraph -> run the engine's dsvg render wrapper
//   -> inject the SVG into a DOM -> query [data-id] -> click the answer bar -> read its data-id back.
// The R wrapper below is copied verbatim from renderPickSvg() in shared/pano-player.js; if that changes,
// mirror it here.  Run from tests/:  node pick_point_smoke.mjs
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, "../..");   // tests -> escape_rooms -> thebustalab.github.io
const PORT = 8062;

// Pull every pick room's shipped { plotCode, answer } straight from the scenario (test what ships).
const SCN = path.resolve(__dirname, "../rooms/data_vis/alaska/scenario.json");
const scn = JSON.parse(fs.readFileSync(SCN, "utf8"));
const PICKS = [];
for (const r of scn.rooms || [])
  for (const h of r.hotspots || [])
    if (h.type === "puzzle" && h.pick)
      PICKS.push({ room: r.key, label: h.label, plotCode: h.pick.plotCode, answer: h.pick.answer });

// Serve the site root so the local alaska CSV is reachable (same layout as production / playwright.config).
const srv = spawn("python3", ["-m", "http.server", String(PORT)], { cwd: SITE_ROOT, stdio: "ignore" });
await new Promise((r) => setTimeout(r, 800));

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(600_000);
page.on("pageerror", (e) => console.log("[pageerror]", String(e)));

await page.goto(`http://localhost:${PORT}/`);

const results = await page.evaluate(async ({ port, picks }) => {
  const secs = (a, b) => Math.round((b - a) / 100) / 10;
  const t0 = performance.now();
  const { WebR } = await import("https://webr.r-wasm.org/latest/webr.mjs");
  const webR = new WebR({ interactive: false });
  await webR.init();
  await webR.installPackages(["dplyr", "ggplot2", "readr"], { quiet: true });

  // Load the real dataset exactly like webr-console.js does.
  const resp = await fetch(`http://localhost:${port}/phylochemistry/sample_data/alaska_lake_data.csv`);
  const bytes = new Uint8Array(await resp.arrayBuffer());
  await webR.FS.writeFile("/home/web_user/alaska_lake_data.csv", bytes);
  await webR.evalRVoid(`alaska_lake_data <- readr::read_csv("/home/web_user/alaska_lake_data.csv", show_col_types = FALSE)`);

  // ensureGgiraph() equivalent (lazy install, once).
  let have = false;
  try { have = await webR.evalRBoolean('requireNamespace("ggiraph", quietly = TRUE)'); } catch (e) { have = false; }
  if (!have) await webR.installPackages(["ggiraph"], { quiet: true });
  const tReady = performance.now();

  const out = [];
  for (const pick of picks) {
    // renderPickSvg() wrapper — VERBATIM from pano-player.js (w/h defaults; content is what matters here).
    const rcode =
      "{ suppressWarnings(suppressMessages({ library(ggplot2); library(ggiraph); library(dplyr) }))\n" +
      pick.plotCode + "\n" +
      ".er_f <- tempfile(fileext = \".svg\")\n" +
      "ggiraph::dsvg(file = .er_f, width = 6, height = 5.5)\n" +
      "print(p); grDevices::dev.off()\n" +
      "paste(readLines(.er_f), collapse = \"\\n\") }";
    const tp0 = performance.now();
    let svg;
    try { svg = await webR.evalRString(rcode); }
    catch (e) { out.push({ room: pick.room, ok: false, stage: "render", err: String(e && (e.message || e)) }); continue; }

    // Inject + click, mirroring buildPickCard()'s wireClicks().
    const holder = document.createElement("div");
    document.body.appendChild(holder);
    holder.innerHTML = svg;
    const tagged = Array.from(holder.querySelectorAll("[data-id]"));
    const ids = tagged.map((el) => el.getAttribute("data-id"));
    const answerEl = tagged.find((el) => el.getAttribute("data-id") === pick.answer);
    let clickedId = null;
    if (answerEl) {
      let solved = false;
      answerEl.addEventListener("click", () => { if (answerEl.getAttribute("data-id") === pick.answer) solved = true; });
      answerEl.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      clickedId = solved ? pick.answer : "MISMATCH";
    }
    out.push({
      room: pick.room, label: pick.label, answer: pick.answer,
      ok: !!answerEl && clickedId === pick.answer,
      hasSvg: svg.includes("<svg"),
      taggedCount: tagged.length,
      uniqueLakes: new Set(ids).size,
      answerPresent: !!answerEl,
      clickResolvedTo: clickedId,
      render_s: secs(tp0, performance.now()),
    });
  }
  return { setup_s: secs(t0, tReady), picks: out };
}, { port: PORT, picks: PICKS });

console.log("\n===== pick-the-point validation (shipped plotCodes) =====");
console.log(`WebR + data + ggiraph ready in ${results.setup_s}s`);
console.log(JSON.stringify(results.picks, null, 2));
console.log("=========================================================\n");

await browser.close();
srv.kill("SIGKILL");
const allOk = PICKS.length > 0 && results.picks.every((r) => r.ok);
process.exit(allOk ? 0 : 1);
