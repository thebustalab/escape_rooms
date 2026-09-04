// Ambient-particle vocabulary + field density. Pure and DOM-free so it can be unit-tested directly
// (house pattern: same shape as puzzle_queue.js / variant_resolve.js). The DOM-building half lives in
// `spawnParticles` in pano-player.js; only the decisions live here.
//
// WHERE THESE RENDER (the thing everyone gets wrong): the landing screen, the per-room `entry`
// interstitial, and the submission screen — NEVER over the panorama. `scenario.ambient` is entry/bookend
// dressing; in-room atmosphere belongs in the scene art. A scenario with no `room.entry` cards shows
// particles on exactly two screens.

// The supported values. Anything NOT in this set falls through to "fireflies" at render time — that is
// deliberate (an unknown value still shows something rather than nothing), but it means a typo is silent,
// which is why the harness authors this through a dropdown rather than free text.
export const AMBIENT_KINDS = ["fireflies", "snow", "embers", "leaves", "dust", "rain", "rays", "none"];

// Density is per-KIND, not one number, because the kinds are not the same size or shape:
//   - dust  — the finest motes in the set; needs the most or it doesn't read as a haze at all
//   - snow  — larger flakes, wants a real fall of them
//   - rain  — thin fast streaks; a heavy field (just under dust) or it reads as drizzle. NOT denser
//             than dust: a streak is 10-24px long and plainly visible on its own, where a dust
//             mote is 1.5-4px and only reads in a crowd. Fineness sets the density, not speed.
//   - rays  — long blurred bars, not points; a handful reads as light, a crowd reads as a curtain
//   - rest  — drifting points (fireflies / embers / leaves)
// `big` = the full-height screens (landing + submission); false = the smaller interstitial card.
// Kept in one place so the four call sites in pano-player.js can't drift apart.
export function particleCount(kind, big) {
  if (kind === "snow") return big ? 40 : 32;
  if (kind === "dust") return big ? 46 : 34;
  if (kind === "rain") return big ? 44 : 33;
  if (kind === "rays") return big ? 7 : 5;
  return big ? 18 : 14;
}

// Whether a value names a real kind. Note "none" IS a valid authored value (it means "draw nothing"),
// so this is a vocabulary check, not a "will it draw something" check — use `kind !== "none"` for that.
export function isAmbientKind(kind) {
  return AMBIENT_KINDS.includes(kind);
}
