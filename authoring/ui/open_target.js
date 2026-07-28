/*
 * open_target.js — which hotspot's box the "Make open door" edit should mask.
 *
 * The scene-open image (`scene_open.png` / `panoramaOpen`) is what the room swaps to
 * on solve. That swap is ROOM-LEVEL and decoupled from any hotspot, so the masked box
 * only decides what the open image DEPICTS. The right box to mask is whatever the open
 * image should REVEAL, in priority order:
 *   1. a FORWARD door (or a legacy door with no `direction` set) — the normal "door opens" case;
 *   2. else a LOCK — an escape/boss room whose scene-open reveals a valve / keypad panel, not a
 *      door (e.g. the Hawai'i boss: the ladder is a BACK door and it's the valve keypad that opens).
 * A bare BACK door is never an opening (it's an always-open passage), so a room whose ONLY hotspot is
 * a back door has nothing to reveal — pick returns null and "Make open door" stays disabled. (A legacy
 * door with no `direction` counts as forward via #1, so there is deliberately no "any door" fallback:
 * the only thing such a fallback could add is a lone back door, which is exactly what we must exclude.)
 *
 * Dual-mode: loads as a browser global (window.EscapeOpenTarget) for the :8751 harness AND is
 * require()-able from Node so authoring/tests can exercise this exact logic. Keep it dependency-free.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.EscapeOpenTarget = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function hasBox(h) { return h && Array.isArray(h.box); }

  // The hotspot whose box the open-door edit masks (null if the room has nothing to reveal).
  function pickOpenMaskHotspot(hotspots) {
    var hs = Array.isArray(hotspots) ? hotspots : [];
    return hs.find(function (h) { return h.type === "door" && h.direction !== "back" && hasBox(h); })
        || hs.find(function (h) { return h.type === "lock" && hasBox(h); })
        || null;
  }

  // Whether "Make open door" is enabled for this room — true iff there is something to reveal.
  function hasOpenTarget(hotspots) {
    return pickOpenMaskHotspot(hotspots) != null;
  }

  return { pickOpenMaskHotspot: pickOpenMaskHotspot, hasOpenTarget: hasOpenTarget };
});
