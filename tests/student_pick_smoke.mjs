// student_pick_smoke.mjs — validation for the Type 4 pick-the-point puzzle rendering the STUDENT'S OWN
// plot (NOT in CI). Proves the chain renderStudentPickSvg() relies on, end to end in a real headless
// browser against the REAL alaska data:
//   boot WebR -> load alaska_lake_data -> install ggiraph -> the student assigns a ggplot to `p` ->
//   swap each layer's geom to its ggiraph interactive twin + splice data_id/tooltip = idColumn ->
//   dsvg render -> query [data-id] -> the room's answer lake is present + clickable.
// Two things are checked: (1) style robustness — aes in ggplot() vs in the geom, points, piped, coord_flip
// all tag correctly; (2) every shipped pick room's `answer` is clickable from a plausible student plot.
// The R block below is VERBATIM from renderStudentPickSvg() in shared/pano-player.js; if that changes,
// mirror it here. Run from tests/:  node student_pick_smoke.mjs
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, "../..");
const PORT = 8064;

// Pull every pick room's shipped { idColumn, answer } from the scenario (test what ships).
const scn = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../rooms/data_vis/alaska/scenario.json"), "utf8"));
const PICKS = [];
for (const r of scn.rooms || [])
  for (const h of r.hotspots || [])
    if (h.type === "puzzle" && h.pick)
      PICKS.push({ room: r.key, idColumn: h.pick.idColumn, answer: h.pick.answer });

const srv = spawn("python3", ["-m", "http.server", String(PORT)], { cwd: SITE_ROOT, stdio: "ignore" });
await new Promise((r) => setTimeout(r, 800));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(600_000);
page.on("pageerror", (e) => console.log("[pageerror]", String(e)));
await page.goto(`http://localhost:${PORT}/`);

const results = await page.evaluate(async ({ port, picks }) => {
  const { WebR } = await import("https://webr.r-wasm.org/latest/webr.mjs");
  const webR = new WebR({ interactive: false });
  await webR.init();
  await webR.installPackages(["dplyr", "ggplot2", "readr"], { quiet: true });
  const resp = await fetch(`http://localhost:${port}/phylochemistry/sample_data/alaska_lake_data.csv`);
  await webR.FS.writeFile("/home/web_user/alaska_lake_data.csv", new Uint8Array(await resp.arrayBuffer()));
  await webR.evalRVoid(`alaska_lake_data <- readr::read_csv("/home/web_user/alaska_lake_data.csv", show_col_types = FALSE)`);
  let have = false;
  try { have = await webR.evalRBoolean('requireNamespace("ggiraph", quietly = TRUE)'); } catch (e) {}
  if (!have) await webR.installPackages(["ggiraph"], { quiet: true });
  // Mirror the scenario `setup`: the student's console session has these attached, so `p <- ggplot(...)`
  // resolves bare ggplot()/aes()/filter() (the engine relies on this — libraries aren't re-attached when
  // the student's plot code runs, only inside the render block).
  await webR.evalRVoid(`suppressMessages({ library(dplyr); library(ggplot2); library(readr) })`);

  // VERBATIM renderStudentPickSvg() R block from shared/pano-player.js — reads `p` from the session.
  const renderStudent = async (idcolJson) => {
    const rcode = `{ suppressWarnings(suppressMessages({ library(ggplot2); library(ggiraph); library(dplyr) }))
.er_make_interactive <- function(p, idcol) {
  if (!inherits(p, "ggplot")) stop("not a ggplot")
  ns <- asNamespace("ggiraph")
  twin <- function(geom) {
    cand <- paste0("GeomInteractive", sub("^Geom", "", class(geom)[1]))
    if (exists(cand, envir = ns, inherits = FALSE)) get(cand, envir = ns) else NULL
  }
  changed <- FALSE
  for (i in seq_along(p$layers)) {
    g <- twin(p$layers[[i]]$geom)
    if (is.null(g)) next
    p$layers[[i]]$geom <- g
    add <- ggplot2::aes(data_id = !!rlang::sym(idcol), tooltip = !!rlang::sym(idcol))
    m <- p$layers[[i]]$mapping
    p$layers[[i]]$mapping <- if (is.null(m)) add else utils::modifyList(m, add)
    changed <- TRUE
  }
  if (!changed) stop("no taggable layer")
  p
}
.er_p <- .er_make_interactive(p, ${idcolJson})
.er_f <- tempfile(fileext = ".svg")
ggiraph::dsvg(file = .er_f, width = 7, height = 4.2)
print(.er_p); grDevices::dev.off()
paste(readLines(.er_f), collapse = "\\n") }`;
    return webR.evalRString(rcode);
  };
  const idsFrom = (svg) => {
    const doc = new DOMParser().parseFromString(svg, "image/svg+xml");
    return new Set(Array.from(doc.querySelectorAll("[data-id]")).map(e => e.getAttribute("data-id")));
  };

  const out = { styles: [], rooms: [] };

  // (1) style robustness — the student may write the plot several equally-valid ways.
  const STYLES = [
    { name: "aes in ggplot() + coord_flip", code: `p <- ggplot(dplyr::filter(alaska_lake_data, element=="Cl"), aes(reorder(lake, mg_per_L), mg_per_L)) + geom_col() + coord_flip()`, want: "North_Killeak_Lake" },
    { name: "aes INSIDE the geom",          code: `p <- ggplot(dplyr::filter(alaska_lake_data, element=="Cl")) + geom_col(aes(reorder(lake, mg_per_L), mg_per_L)) + coord_flip()`, want: "North_Killeak_Lake" },
    { name: "geom_point scatter",           code: `p <- ggplot(dplyr::distinct(alaska_lake_data, lake, water_temp), aes(water_temp, lake)) + geom_point()`, want: "Lava_Lake" },
    { name: "piped |> into ggplot",         code: `p <- alaska_lake_data |> dplyr::filter(element=="Cl") |> ggplot(aes(lake, mg_per_L)) + geom_col()`, want: "North_Killeak_Lake" },
  ];
  for (const s of STYLES) {
    try { await webR.evalRVoid(s.code); const ids = idsFrom(await renderStudent(JSON.stringify("lake")));
      out.styles.push({ name: s.name, ok: ids.has(s.want), tagged: ids.size }); }
    catch (e) { out.styles.push({ name: s.name, ok: false, err: String(e && (e.message || e)).slice(0, 140) }); }
  }

  // (2) every shipped pick room's answer must be clickable from a plausible per-lake plot.
  for (const pk of picks) {
    try {
      await webR.evalRVoid(`p <- ggplot(dplyr::distinct(alaska_lake_data, lake, water_temp), aes(lake, water_temp)) + geom_col()`);
      const ids = idsFrom(await renderStudent(JSON.stringify(pk.idColumn)));
      out.rooms.push({ room: pk.room, answer: pk.answer, ok: ids.has(pk.answer), tagged: ids.size });
    } catch (e) { out.rooms.push({ room: pk.room, answer: pk.answer, ok: false, err: String(e && (e.message || e)).slice(0, 140) }); }
  }
  return out;
}, { port: PORT, picks: PICKS });

console.log("\n===== student-plot pick-the-point validation =====");
console.log(JSON.stringify(results, null, 2));
console.log("==================================================\n");
await browser.close();
srv.kill("SIGKILL");
const ok = results.styles.every(s => s.ok) && results.rooms.length > 0 && results.rooms.every(r => r.ok);
process.exit(ok ? 0 : 1);
