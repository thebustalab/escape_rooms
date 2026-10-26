// landing_backdrop.js — the landing screen's moving backdrop (2026-10-23, Lucas).
//
// The opening text used to sit on the plain background with the ambient particles. It now sits over a
// slow pan of the FIRST room's cinemagraph (rooms[0], the room the player is about to enter), under a
// dark scrim, with the particles kept on top as an overlay. Every scenario gets it with no authoring:
// a scenario whose first room has no full-scene clip falls back to that room's still, and one with
// neither keeps the old landing exactly.
//
// The pan is painted onto a <canvas> each animation frame rather than by moving the <video>: a CSS pan
// lands on whole pixels and judders, which is why the stage projector does it this way (stage.html).
// Reduced motion: the still, centred, no pan and no clip.

// What to show: { video, still } relative to play.html, or null when the first room has nothing.
// The base clip is the full-scene cinemagraph with NO state (the room as first met); a state clip
// (night, flooded…) is never the landing's.
export function landingBackdropSource(scenario) {
  const r = scenario && Array.isArray(scenario.rooms) ? scenario.rooms[0] : null;
  if (!r) return null;
  let video = null;
  for (const h of (r.hotspots || [])) {
    const c = h && h.cinemagraph;
    if (c && c.video && !c.state && Array.isArray(c.box) && c.box.join() === "0,0,1,1") { video = c.video; break; }
  }
  const still = r.panorama || null;
  if (!video && !still) return null;
  return { video, still };
}

// Horizontal offset fraction 0..1 for a time in ms: an ease-in-out sweep from the left edge to the
// right edge and back, `periodMs` each way (the stage projector's curve).
export function panPhase(ms, periodMs = 90000) {
  const u = (((ms % (2 * periodMs)) + 2 * periodMs) % (2 * periodMs)) / periodMs;
  const k = u < 1 ? u : 2 - u;
  return 0.5 - 0.5 * Math.cos(Math.PI * k);
}

// Mount behind the landing card. Returns stop(), which removes everything and stops the clip.
export function mountLandingBackdrop(screen, scenario, opts = {}) {
  const src = landingBackdropSource(scenario);
  if (!screen || !src) return () => {};
  const reduce = opts.reducedMotion != null ? opts.reducedMotion
    : !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const wrap = document.createElement("div");
  wrap.className = "landingBackdrop";
  wrap.setAttribute("aria-hidden", "true");
  const canvas = document.createElement("canvas");
  const scrim = document.createElement("div");
  scrim.className = "landingScrim";
  wrap.append(canvas, scrim);
  screen.prepend(wrap);

  const img = new Image();
  if (src.still) img.src = src.still;
  let video = null;
  if (src.video && !reduce) {
    video = document.createElement("video");
    video.muted = true; video.loop = true; video.playsInline = true; video.autoplay = true;
    video.preload = "auto";
    video.setAttribute("muted", ""); video.setAttribute("playsinline", "");
    video.src = src.video;
    const p = video.play(); if (p && p.catch) p.catch(() => {});   // autoplay refused: the still stands in
  }
  const t0 = performance.now();
  let raf = 0, stopped = false;
  function paint(now) {
    if (stopped) return;
    const dpr = window.devicePixelRatio || 1;
    const cw = Math.round(canvas.clientWidth * dpr), ch = Math.round(canvas.clientHeight * dpr);
    if (cw && ch && (canvas.width !== cw || canvas.height !== ch)) { canvas.width = cw; canvas.height = ch; }
    const v = video && video.readyState >= 2 && video.videoWidth ? video : null;
    const s = v || (img.complete && img.naturalWidth ? img : null);
    if (s && cw && ch) {
      const sw = s.videoWidth || s.naturalWidth, sh = s.videoHeight || s.naturalHeight;
      const k = Math.max(cw / sw, ch / sh), dw = sw * k, dh = sh * k;
      const e = reduce ? 0.5 : panPhase(now - t0, opts.periodMs);
      canvas.getContext("2d").drawImage(s, -(dw - cw) * e, (ch - dh) / 2, dw, dh);
      wrap.classList.add("shown");
    }
    if (!reduce || !s) raf = requestAnimationFrame(paint);   // reduced motion: draw once and stop
  }
  raf = requestAnimationFrame(paint);
  const onResize = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(paint); };
  window.addEventListener("resize", onResize);
  return function stop() {
    stopped = true;
    window.removeEventListener("resize", onResize);
    cancelAnimationFrame(raf);
    if (video) { try { video.pause(); } catch (e) {} video.removeAttribute("src"); try { video.load(); } catch (e) {} }
    wrap.remove();
  };
}
