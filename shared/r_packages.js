/**
 * r_packages.js — THE list of R packages every WebR surface installs. One file, no drift.
 *
 * WHY THIS EXISTS
 * ---------------
 * Before this, four places each kept their own hand-maintained package array: every room's
 * `scenario.json`, the book's `sandbox.html`, each chapter's `window.WEBR_CELL_CONFIG`, and the
 * cell demo page. They drifted — a chapter had `ggrepel` the sandbox didn't, rooms varied one to
 * the next — so R that worked in the book failed in a room for no reason a student could see.
 *
 * `webr-console.js` now installs BASE_PACKAGES + ANALYSIS_PACKAGES on every surface and merges
 * whatever extra a caller asks for. A consumer's own list is now ADDITIVE and optional: it names
 * only what is genuinely special to that page, and never has to repeat the baseline.
 *
 * ADDING A PACKAGE: put it in the right list here and nowhere else. Then check it actually has a
 * WebAssembly build before you rely on it —
 *     curl -s https://repo.r-wasm.org/bin/emscripten/contrib/4.6/PACKAGES | grep -x 'Package: <name>'
 * and if it is missing there, try `bioc.r-universe.dev` / `cran.r-universe.dev` with the same path.
 * A package with no wasm binary in any of the three CANNOT be installed at runtime, full stop
 * (that is why `shipunov` is vendored into the runMatrixAnalysis shim instead of installed).
 */

/**
 * Repositories for the ONE package that is not in WebR's default repo.
 *
 * READ THIS BEFORE ADDING A `repos:` ANYWHERE ELSE. Passing `repos` REPLACES WebR's default rather
 * than extending it, and installing a broad list through the r-universe mirrors gives you binaries
 * built with a different toolchain than the ones already in the image. Doing exactly that broke two
 * things at once in testing (2026-09-22): `FactoMineR::PCA` died with "could not load dynamic lib
 * mvtnorm.so", and even base `parallel` stopped loading — a mixed-ABI library, from an install that
 * reported success. Nothing local catches it; it only shows up in a real browser.
 *
 * So: install everything from the DEFAULT repo (pass no `repos` at all), and use this list for the
 * Bioconductor set alone. `repo.r-wasm.org` stays first here so the dependency chain still resolves
 * against the same binaries as the rest of the session. Measured, that split is also FASTER than one
 * combined call — 10.3 s + 8.5 s against 24.8 s.
 */
export const R_BIOC_REPOS = [
  "https://repo.r-wasm.org",
  "https://bioc.r-universe.dev",
  "https://cran.r-universe.dev",
];

/**
 * The tidyverse floor. Every surface gets these, because every surface's starter code assumes them
 * and a student typing `library(dplyr)` in any room must not hit an install error.
 */
export const BASE_PACKAGES = [
  "dplyr",
  "ggplot2",
  "tidyr",
  "readr",
  "stringr",
  "tibble",
];

/**
 * What `runMatrixAnalysis()` reaches for, and can get from WebR's default repo. All of these are
 * namespace-qualified inside the shim, so they are INSTALLED but never attached — a student's search
 * path stays exactly as clean as it was before.
 *
 * NOT HERE, and none of these is an oversight — each was tried in a real browser and failed:
 *   `shipunov` — no wasm build anywhere. `Bclust` is vendored into the shim instead.
 *   `ips`      — HAS a wasm binary and installs cleanly, then dies on first use: it imports `XML`,
 *                which has no wasm build. `descendants()` is vendored instead.
 *   `fpc`      — same trap. Its NAMESPACE says `import(mclust)` and `mclust` is not in the wasm
 *                repo, so `fpc::dbscan` never loads. The shim calls `dbscan::dbscan` instead.
 *   `umap`     — imports `reticulate`, which wants a Python a browser has not got.
 *   `Rfast`    — no binary; it was there for one euclidean distance, now `stats::dist`.
 * THE LESSON, because it cost three browser runs to learn: a package appearing in the wasm PACKAGES
 * index only means it INSTALLS. Whether its namespace LOADS depends on its whole import chain, and
 * the only way to find out is to call it in a browser. Do not add anything here on the strength of
 * a grep against the index.
 */
export const ANALYSIS_PACKAGES = [
  "FactoMineR", // pca / mca
  "ape",        // as.phylo
  "cluster",    // daisy(), gower distance
  "dbscan",     // dbscan clustering (replaces fpc, which cannot load)
  "Rtsne",      // tsne
  // The three below are for `buildNetwork()` (book ch.7), added 2026-09-22. All three have wasm
  // binaries in the default repo, which — per the warning above — proves only that they INSTALL.
  // What makes them safe to rely on is that `tests/matrix_analysis_smoke.mjs` now calls
  // buildNetwork() in a real headless browser and asserts on the frames it returns, so the
  // install-but-do-not-load trap that caught ips/fpc/umap is covered here too.
  "network",    // network() object buildNetwork() builds the graph in
  "ggnetwork",  // ggnetwork() — turns that object into the tidy node/edge frame the book plots
  "igraph",     // layout_with_fr() — the weighted force-directed layout
];

/**
 * The Bioconductor set — installed SEPARATELY, with `R_BIOC_REPOS`. Only `ggtree`, and it is not
 * optional: the `hclust` branch calls `ggtree::fortify()` to turn the tree into the tidy frame the
 * whole course plots from. Confirmed working in a headless browser on 2026-09-22 (the smoke test's
 * `ggtree_fortify` case), which closes the "still owed: a browser smoke test" note that sat in the
 * root AGENTS.md from 2026-08-26.
 */
export const BIOC_PACKAGES = ["ggtree"];

/**
 * Everything a session ends up with, in one call — for a caller that wants to know, and for the
 * tests. `webr-console.js` does the actual installing in three stages; see it for why.
 */
export function resolvePackages(extra) {
  return [...new Set([...BASE_PACKAGES, ...ANALYSIS_PACKAGES, ...BIOC_PACKAGES, ...(extra || [])])];
}
