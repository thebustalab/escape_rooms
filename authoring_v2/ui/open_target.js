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
 * A BACK door and an open-world **`open`** passage are BOTH always-walkable routes, never an "opening", so
 * neither can win (only `forward`/legacy doors qualify at #1 — updated 2026-07-31, when open-world rooms with
 * an `open` passage listed BEFORE the forward door started mis-masking the passage, e.g. airship's weather
 * deck opening the apothecary door instead of the bridge). A room whose only doors are back/open passages has
 * nothing to reveal — pick returns null and "Make open door" stays disabled.
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
    return hs.find(function (h) { return h.type === "door" && (h.direction === "forward" || h.direction == null) && hasBox(h); })
        || hs.find(function (h) { return h.type === "lock" && hasBox(h); })
        || null;
  }

  // Whether "Make open door" is enabled for this room — true iff there is something to reveal.
  function hasOpenTarget(hotspots) {
    return pickOpenMaskHotspot(hotspots) != null;
  }

  return { pickOpenMaskHotspot: pickOpenMaskHotspot, hasOpenTarget: hasOpenTarget };
});
