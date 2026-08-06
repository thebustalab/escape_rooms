// variant_resolve.js — pure selection logic for per-hotspot STATE VARIANTS (Phase 3 / Option 2).
//
// A hotspot (object) may carry `variants: [{state, when, box, prompt, panorama}]`. At runtime each
// object's ACTIVE variant is the LAST one whose `when` condition is satisfied by current world state
// (author order = priority); if none match, that object shows the base scene (no overlay). Multiple
// objects can be active at once — the player composites each active variant's box region over the base
// panorama (see compositeVariants in pano-player.js), so independent object states render together.
//
// This module is intentionally DOM-free and evaluator-injected so it unit-tests without a browser:
// the caller passes `evalCond`, which in the player is `condOK` (supports true / {solved} / {allSolved}
// / {gte} / {eq}). Kept as an ES module so pano-player.js (itself type="module") can import it directly
// with no per-scenario play.html change; the Node test imports it the same way.

export function pickActiveVariants(hotspots, evalCond) {
  const out = [];
  (hotspots || []).forEach(h => {
    const vs = h && Array.isArray(h.variants) ? h.variants : null;
    if (!vs || !vs.length) return;
    let chosen = null;
    for (const v of vs) {                       // last satisfied wins → author order is priority
      if (!v || !v.panorama) continue;          // a variant with no image can't be shown
      if (evalCond(v.when)) chosen = v;
    }
    if (!chosen) return;                          // none satisfied → object shows base
    const box = Array.isArray(chosen.box) ? chosen.box
      : (Array.isArray(h.box) ? h.box : null);   // variant box defaults to the hotspot's own box
    if (!box || box.length !== 4) return;        // no region to composite into → skip
    out.push({ panorama: chosen.panorama, box, hotspotId: h.id, state: chosen.state });
  });
  return out;
}

// Cheap presence check the authoring UI / callers can use to skip work when a room has no variants.
export function roomHasVariants(hotspots) {
  return (hotspots || []).some(h => h && Array.isArray(h.variants) && h.variants.some(v => v && v.panorama));
}

// The active NAVIGATION variant of a single door (the monorail world-state switch, 2026-08-05). A door may
// carry `variants:[{state, when, to, direction?, panorama?}]`; a world-state lever (a `dial`) flips which
// one is live, so ONE door leads to different rooms — and shows a different open-view — per state. The
// active variant is the LAST whose `when` holds (author order = priority), the same rule pickActiveVariants
// uses for art. The KEY difference: a nav variant does NOT need `panorama` — it only has to say WHERE the
// door goes, so the mechanic works before (or without) the state-specific door art existing; the art rides
// in on the same variant via pickActiveVariants once generated. Returns the chosen variant, or null when the
// door has no variants / none match (caller falls back to the door's own `to`/`direction`).
export function activeDoorVariant(hotspot, evalCond) {
  const vs = hotspot && Array.isArray(hotspot.variants) ? hotspot.variants : null;
  if (!vs || !vs.length) return null;
  let chosen = null;
  for (const v of vs) { if (v && evalCond(v.when)) chosen = v; }
  return chosen;
}
