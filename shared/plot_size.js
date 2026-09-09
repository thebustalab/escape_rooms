/*
 * plot_size.js — the pure half of WebR plot sizing: aspect ratios, the capture-geometry maths, and the
 * size-control stylesheet. No imports, so this is unit-testable in Node (see tests/plot_size.test.mjs);
 * `webr-console.js` can't be, because it imports the WebR runtime from a CDN URL. Same split as
 * `webr_view.js` — keep anything worth pinning on this side of the line.
 *
 * WHY THIS EXISTS. Plots were captured at a hardcoded 720x460 and shown with nothing but
 * `max-width:100%`. R therefore laid every plot out for a 720px-wide device and the browser then
 * MAGNIFIED that layout to fill whatever pane held it — ~1100-1200px in the escape-room puzzle modal.
 * Chunky axis text, fat points, and a plot that ignores the shape of the space it's in. Capture geometry
 * is now derived from the output element's real width, so R lays the plot out for the pane it will
 * actually occupy.
 *
 * THE 2x IS ALREADY THERE (verified live 2026-09-09, tests/plot_size_smoke.mjs). `webr::canvas` returns a
 * bitmap at exactly TWICE the requested width/height — a fixed supersample, NOT derived from
 * devicePixelRatio (a DPR-2 browser gets the same 2x as a DPR-1 one). So ask for LOGICAL px and display
 * the result at that same logical size: the free 2x becomes retina sharpness instead of magnification.
 * Do not multiply by devicePixelRatio here — that compounds with the device's own 2x and asks R for a
 * bitmap four times too big.
 */

// Ratios are width/height. `std` (3:2) is the default because the old hardcoded 720x460 was 1.57 — near
// enough that existing puzzle plots keep their familiar shape. Order = the order they appear in the picker.
export const PLOT_ASPECTS = [
  { key: "wide",   label: "Wide 16:9",  ratio: 16 / 9 },
  { key: "std",    label: "Standard",   ratio: 3 / 2 },
  { key: "square", label: "Square",     ratio: 1 },
  { key: "tall",   label: "Tall 3:4",   ratio: 3 / 4 },
];
export const PLOT_DEFAULT_ASPECT = "std";

export const PLOT_LIMITS = {
  minScale: 0.4,        // the slider's floor: 40% of the available pane
  maxScale: 1,          // no point past 100% — `max-width:100%` would only shrink it back
  minWidth: 320,        // logical px; below this ggplot's axis labels and legends start colliding
  maxWidth: 1400,       // logical px, so the device's own 2x lands at 2800 — the real bitmap ceiling
  fallbackWidth: 900,   // used when the output element can't be measured (see plotGeometry)
};

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export function aspectRatio(key) {
  const a = PLOT_ASPECTS.find(x => x.key === key);
  return (a || PLOT_ASPECTS.find(x => x.key === PLOT_DEFAULT_ASPECT)).ratio;
}

/*
 * Work out what to ask webr::canvas for. The same numbers are ALSO the CSS size to display the returned
 * bitmap at, which is the whole point: R lays out for `width`, the device hands back 2x that many pixels,
 * and showing it at `width` CSS px spends those pixels on sharpness rather than on magnification.
 *
 *   availWidth — the output element's usable inner width in CSS px. Pass 0/null when it can't be
 *                measured and `fallbackWidth` is used instead: the escape rooms' submission refine
 *                console renders into the UNMOUNTED (`display:none`) #webr-output and copies the canvas
 *                out, so it genuinely measures 0 while still needing a good, print-worthy figure.
 *   scale      — the size slider, 0.4-1, as a fraction of availWidth.
 *   aspect     — a PLOT_ASPECTS key; height falls out of width / ratio, so a student can never drag out
 *                a 200x1400 sliver by hand.
 *
 * `pointsize` is deliberately NOT set. It stays at R's default 12, so text keeps a constant on-screen
 * size while the plot area grows — which is how resizing a plot pane behaves in RStudio. Scaling it with
 * the width instead would make every large plot look like a poster.
 */
export function plotGeometry(opts) {
  const o = opts || {};
  const L = PLOT_LIMITS;
  const avail = o.availWidth > 0 ? o.availWidth : L.fallbackWidth;
  const scale = clamp(Number.isFinite(o.scale) ? o.scale : L.maxScale, L.minScale, L.maxScale);
  const width = Math.round(clamp(avail * scale, L.minWidth, L.maxWidth));
  return { width, height: Math.round(width / aspectRatio(o.aspect)) };
}

/*
 * The size control's stylesheet, injected once per document by webr-console.js.
 *
 * Deliberately colour-free: it inherits `currentColor` and uses translucent blacks, because the same
 * strip has to sit on the sandbox's amber-on-navy card AND in the escape rooms' puzzle modal without
 * either surface's CSS being touched. `option` is the exception — the dropdown list is painted by the OS
 * on a light background in most browsers, so inheriting a pale ink there renders it invisible.
 */
export const PLOT_CTL_CSS = `
.webr-plotctl { display:inline-flex; align-items:center; gap:8px; font:12px system-ui, sans-serif;
                color:inherit; opacity:.85; flex-wrap:wrap; }
.webr-plotctl:hover { opacity:1; }
.webr-plotctl > label { display:inline-flex; align-items:center; gap:6px; cursor:pointer; }
.webr-plotctl input[type=range] { width:104px; accent-color:currentColor; cursor:pointer; }
.webr-plotctl select { font:12px system-ui, sans-serif; color:inherit; background:rgba(0,0,0,.28);
                       border:1px solid currentColor; border-radius:6px; padding:2px 5px; cursor:pointer; }
.webr-plotctl select option { color:#111; background:#fff; }
.webr-plotctl .webr-plotctl-val { font-variant-numeric:tabular-nums; opacity:.7; min-width:4.2em; }
`;
