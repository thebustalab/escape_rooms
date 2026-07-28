// ggiraph_smoke.mjs — one-off feasibility probe (NOT part of the CI suite).
//
// Question it answers: can WebR, in a real headless browser, install ggiraph and render an
// INTERACTIVE ggplot whose SVG carries per-point `data-id` attributes we can click-map back to
// the underlying data row? That is the mechanism for a "make the plot, click the point to pick
// your answer" puzzle. Availability in the wasm repo is already confirmed; this proves it renders.
//
// Run:  node ggiraph_smoke.mjs      (from the tests/ dir, so "playwright" resolves)
import { chromium } from "playwright";
import http from "node:http";

// Minimal same-origin page so the module dynamic-import + WebR fetches have a real http origin
// (mirrors how the app boots WebR over python -m http.server, no COOP/COEP needed).
const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "text/html");
  res.end("<!doctype html><title>ggiraph probe</title><body>probe</body>");
});
await new Promise((r) => server.listen(0, r));
const port = server.address().port;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(600_000);
page.on("console", (m) => console.log("[page]", m.text()));
page.on("pageerror", (e) => console.log("[pageerror]", String(e)));

await page.goto(`http://localhost:${port}/`);

const R_CODE = String.raw`
res <- tryCatch({
  suppressWarnings(suppressMessages({ library(ggplot2); library(ggiraph) }))
  df <- data.frame(
    lake = c("Lava_Lake","Walker_Lake","North_Killeak_Lake","Wild_Lake","Iniakuk_Lake"),
    temp = c(20.18, 15.30, 7.50, 12.10, 9.40)
  )
  p <- ggplot(df, aes(lake, temp)) +
    geom_point_interactive(aes(data_id = lake, tooltip = lake), size = 5)
  f <- tempfile(fileext = ".svg")
  dsvg(file = f, width = 6, height = 4)
  print(p)
  dev.off()
  paste(readLines(f), collapse = "\n")
}, error = function(e) paste0("R_ERROR: ", conditionMessage(e)))
res
`;

const result = await page.evaluate(async (rcode) => {
  const secs = (a, b) => Math.round((b - a) / 100) / 10;
  const t0 = performance.now();
  const { WebR } = await import("https://webr.r-wasm.org/latest/webr.mjs");
  const webR = new WebR({ interactive: false });
  await webR.init();
  const tInit = performance.now();
  await webR.installPackages(["ggiraph"], { quiet: true });
  const tPkg = performance.now();
  let svg;
  try { svg = await webR.evalRString(rcode); }
  catch (e) { svg = "JS_ERROR: " + (e && (e.message || e)); }
  const tRender = performance.now();
  const ids = (svg.match(/data-id=(['"])[^'"]*\1/g) || []);       // either quote style
  const lakeHits = (svg.match(/Lava_Lake|Walker_Lake|North_Killeak_Lake/g) || []).length;
  // grab the first <circle ...> element to inspect what attributes a point carries
  const circle = (svg.match(/<circle[^>]*>/) || [""])[0];
  return {
    ok: svg.includes("<svg") && !svg.startsWith("R_ERROR") && !svg.startsWith("JS_ERROR"),
    hasSvg: svg.includes("<svg"),
    dataIdCount: ids.length,
    dataIds: ids.slice(0, 10),
    lakeNameHits: lakeHits,
    firstCircle: circle,
    circleCount: (svg.match(/<circle/g) || []).length,
    svgLen: svg.length,
    head: svg.slice(0, 300),
    timings_s: { init: secs(t0, tInit), install: secs(tInit, tPkg), render: secs(tPkg, tRender), total: secs(t0, tRender) },
  };
}, R_CODE);

console.log("\n===== ggiraph WebR smoke result =====");
console.log(JSON.stringify(result, null, 2));
console.log("=====================================\n");

await browser.close();
server.close();
process.exit(result.ok ? 0 : 1);
