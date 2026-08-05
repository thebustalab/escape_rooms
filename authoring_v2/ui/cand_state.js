/*
 * cand_state.js — the four build-step chip states (wrap · spots · door · save) for ONE candidate image
 * under a room in the harness "build rooms" step.
 *
 * The subtlety this exists to guard (2026-07-21 fix): on Save, commit-room PROMOTES the committed
 * candidate's wrap + hotspots onto the room NODE and then CLEARS the room's _scratch draft. So once a
 * candidate is committed, its per-candidate draft (`per`) is gone — the chip states must fall back to the
 * node (`room.wrap` / `room.hotspots` / `room.panoramaOpen`) or wrap and spots wrongly drop back to grey
 * right after Save. `save` is simply "this candidate is the one the node was built from".
 *
 * compute(per, room, file, lastScenes):
 *   per        — the candidate's draft entry: { wrap?, hotspots? } (or {} if none / cleared on commit)
 *   room       — the room node: { built?, builtFrom?, wrap?, hotspots?, panoramaOpen? }
 *   file       — the candidate filename, e.g. "gpt_room1_3.png"
 *   lastScenes — the _scratch scene filenames on disk (for the "<stem>_open.png exists" door check)
 *
 * Dual-mode: browser global (window.EscapeCandState) for the :8751 harness AND require()-able from Node
 * tests, so the test exercises this exact shipping logic. Keep it dependency-free.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.EscapeCandState = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function stem(f) { return String(f || "").replace(/\.png$/i, ""); }

  function compute(per, room, file, lastScenes) {
    per = per || {};
    room = room || {};
    var scenes = Array.isArray(lastScenes) ? lastScenes : [];
    // committed = the node was built from THIS candidate; its draft is cleared, so read the node.
    var committed = !!(room.built && room.builtFrom === file);
    return {
      wrap: !!per.wrap || (committed && !!room.wrap),
      hotspots: (Array.isArray(per.hotspots) && per.hotspots.length > 0)
        || (committed && Array.isArray(room.hotspots) && room.hotspots.length > 0),
      door: scenes.indexOf(stem(file) + "_open.png") !== -1
        || (committed && !!room.panoramaOpen),
      save: committed
    };
  }

  return { compute: compute, stem: stem };
});
