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
// Reduced motion: the still, centred, no pan and no clip. The landing is PROJECTED by default (below): the room
// as the viewer will show it, turning slowly; `landingProjected: false` keeps the flat pan.

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

// ---- PROJECTED landing (Lucas, 2026-10-29; the DEFAULT for every scenario since 2026-10-30) -------------------
// The flat pan shows the panorama's raw equirectangular strip, warped at the edges. The projected landing
// renders it as the player will see it (a rectilinear camera like the room viewer) and turns slowly. A scenario
// opts back into the flat pan with `landingProjected: false`. Drawn by
// a WebGL fragment shader that samples the still or the live clip each frame; no WebGL → the flat pan.

const RAD = Math.PI / 180;

// Projected unless the scenario opts out with `landingProjected: false` (absent = projected).
export function landingProjected(scenario) {
  return !(scenario && scenario.landingProjected === false);
}

// The room's projection: horizontal and vertical coverage, the picture's centre pitch, the camera's pitch
// and horizontal field of view, from rooms[0].wrap (defaults as the player's for a wrap-less room).
export function projectionOf(scenario) {
  const r = scenario && Array.isArray(scenario.rooms) ? scenario.rooms[0] : null;
  const w = (r && r.wrap) || {};
  const num = (v, d) => (typeof v === "number" && isFinite(v) ? v : d);
  return { haov: num(w.haov, 360), vaov: num(w.vaov, 90), vOffset: num(w.vOffset, 0),
           pitch: num(w.pitch, 0), hfov: num(w.hfov, 100) };
}

// The camera yaw (degrees) at time ms: a full panorama turns slowly and continuously; a partial one sweeps
// between its edges (keeping the view inside the picture) on the flat pan's ease-in-out curve.
export function projectedYaw(ms, proj, { degPerSec = 2, periodMs = 90000 } = {}) {
  if (!(proj.haov < 360)) return ((ms / 1000) * degPerSec) % 360;
  const span = Math.max(0, proj.haov - proj.hfov) / 2;
  return -span + 2 * span * panPhase(ms, periodMs);
}

// Texture coordinate (u, v in 0..1, v down) seen through screen point (x, y in -1..1, y up) for a camera
// at yaw/pitch (degrees) with horizontal fov hfov over a viewport of the given aspect (width / height), or
// null when the ray misses a partial picture. The shader below is this function, line for line.
export function projectToTex(x, y, yaw, pitch, hfov, aspect, proj) {
  const t = Math.tan(hfov * RAD / 2);
  let dx = x * t, dy = (y * t) / aspect, dz = 1;
  const n = Math.hypot(dx, dy, dz); dx /= n; dy /= n; dz /= n;
  const cp = Math.cos(pitch * RAD), sp = Math.sin(pitch * RAD);
  const y1 = dy * cp + dz * sp, z1 = -dy * sp + dz * cp;            // tilt up by pitch
  const cy = Math.cos(yaw * RAD), sy = Math.sin(yaw * RAD);
  const x2 = dx * cy + z1 * sy, z2 = -dx * sy + z1 * cy;            // turn right by yaw
  const lon = Math.atan2(x2, z2) / RAD, lat = Math.asin(Math.max(-1, Math.min(1, y1))) / RAD;
  let u = lon / proj.haov + 0.5;
  const v = 0.5 - (lat - proj.vOffset) / proj.vaov;
  if (!(proj.haov < 360)) u -= Math.floor(u);
  if (u < 0 || u > 1 || v < 0 || v > 1) return null;
  return { u, v };
}

const VERT = "attribute vec2 p; varying vec2 q; void main(){ q = p; gl_Position = vec4(p, 0.0, 1.0); }";
const FRAG = `precision highp float;
varying vec2 q; uniform sampler2D tex; uniform float yaw, pitch, tanH, aspect, haov, vaov, voff, full;
const float R = 0.017453292519943295;
void main(){
  vec3 d = normalize(vec3(q.x * tanH, q.y * tanH / aspect, 1.0));
  float cp = cos(pitch * R), sp = sin(pitch * R);
  float y1 = d.y * cp + d.z * sp, z1 = -d.y * sp + d.z * cp;
  float cy = cos(yaw * R), sy = sin(yaw * R);
  float x2 = d.x * cy + z1 * sy, z2 = -d.x * sy + z1 * cy;
  float lon = atan(x2, z2) / R, lat = asin(clamp(y1, -1.0, 1.0)) / R;
  float u = lon / haov + 0.5, v = 0.5 - (lat - voff) / vaov;
  if (full > 0.5) u = fract(u);
  if (u < 0.0 || u > 1.0 || v < 0.0 || v > 1.0) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
  gl_FragColor = texture2D(tex, vec2(u, v));
}`;

// A WebGL painter for `canvas`, or null when WebGL (or the shader) is unavailable.
function projectedPainter(canvas, proj) {
  // preserveDrawingBuffer: the e2e test reads the picture back (tests/e2e/landing_backdrop.spec.js)
  const opts = { premultipliedAlpha: false, preserveDrawingBuffer: true };
  const gl = canvas.getContext("webgl", opts) || canvas.getContext("experimental-webgl", opts);
  if (!gl) return null;
  const sh = (type, src) => { const o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o);
    return gl.getShaderParameter(o, gl.COMPILE_STATUS) ? o : null; };
  const vs = sh(gl.VERTEX_SHADER, VERT), fs = sh(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) return null;
  const prog = gl.createProgram(); gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return null;
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR],
                        [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  const U = n => gl.getUniformLocation(prog, n);
  gl.uniform1f(U("haov"), proj.haov); gl.uniform1f(U("vaov"), proj.vaov); gl.uniform1f(U("voff"), proj.vOffset);
  gl.uniform1f(U("full"), proj.haov < 360 ? 0 : 1); gl.uniform1f(U("pitch"), proj.pitch);
  return function paint(source, yaw, cw, ch) {
    gl.viewport(0, 0, cw, ch);
    try { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, source); } catch (e) { return false; }
    // the room's hfov is a horizontal field; on a tall (portrait) screen keep the vertical field sane
    const aspect = cw / ch, h = aspect < 1 ? Math.min(proj.hfov, 75) : proj.hfov;
    gl.uniform1f(U("tanH"), Math.tan(h * RAD / 2)); gl.uniform1f(U("aspect"), aspect); gl.uniform1f(U("yaw"), yaw);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    return true;
  };
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
  let canvas = document.createElement("canvas");
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
  const proj = projectionOf(scenario);
  // the projected painter owns the canvas's context once made, so decide before any 2D draw
  const projected = landingProjected(scenario) ? projectedPainter(canvas, proj) : null;
  // A canvas that took a WebGL context can never give a 2D one, so if the shader failed (WebGL present but the
  // painter came back null) swap in a fresh canvas for the flat pan.
  if (landingProjected(scenario) && !projected) {
    const fresh = document.createElement("canvas");
    canvas.replaceWith(fresh);
    canvas = fresh;
  }
  let raf = 0, stopped = false;
  function paint(now) {
    if (stopped) return;
    const dpr = window.devicePixelRatio || 1;
    const cw = Math.round(canvas.clientWidth * dpr), ch = Math.round(canvas.clientHeight * dpr);
    if (cw && ch && (canvas.width !== cw || canvas.height !== ch)) { canvas.width = cw; canvas.height = ch; }
    const v = video && video.readyState >= 2 && video.videoWidth ? video : null;
    const s = v || (img.complete && img.naturalWidth ? img : null);
    if (projected) {
      if (s && cw && ch && projected(s, reduce ? 0 : projectedYaw(now - t0, proj, opts), cw, ch)) wrap.classList.add("shown");
    } else if (s && cw && ch) {
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
