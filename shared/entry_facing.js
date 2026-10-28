// entry_facing.js — which way a player faces on walking into a room (Lucas, 2026-10-28, every scenario).
//
// RULE: arriving through a door from room `fromKey`, face the WAY OUT — the arrival room's other door, not
// the one you came in by. Two doors: the other one. Three or more: the door furthest round from the way in
// (roughly straight ahead). A dead end (no other shown door): face straight away from the way in, into the
// room. With no known way in (game start, a ride, a test-play jump, a room with no door back to `fromKey`)
// the caller's fallback is kept: the forward door, as before.
//
// Pure: the player passes in how to read a door (its target key, whether it is shown, its yaw), so this
// is unit-tested in node (tests/entry_facing.test.mjs) without a browser.

const wrap = y => ((((y + 180) % 360) + 360) % 360) - 180;

// doors: the arrival room's door hotspots that have a box. opts:
//   targetKey(h) -> room key the door leads to (null if unknown), isShown(h) -> bool, yawOf(h) -> degrees,
//   haov -> the room panorama's horizontal coverage (360 = full wrap), fallback -> yaw to use when the rule
//   cannot apply.
export function entryYaw(doors, fromKey, { targetKey, isShown, yawOf, haov = 360, fallback = 0 }) {
  if (!fromKey || !Array.isArray(doors)) return fallback;
  const inDoor = doors.find(h => targetKey(h) === fromKey);
  if (!inDoor) return fallback;
  const inYaw = yawOf(inDoor);
  const full = !(haov < 360);
  const dist = y => full ? Math.abs(wrap(y - inYaw)) : Math.abs(y - inYaw);
  const out = doors.filter(h => h !== inDoor && targetKey(h) !== fromKey && isShown(h));
  if (out.length) {
    let best = out[0], bestD = dist(yawOf(best));
    for (const h of out.slice(1)) { const d = dist(yawOf(h)); if (d > bestD) { best = h; bestD = d; } }
    return yawOf(best);
  }
  // Dead end: turn round, into the room. A partial panorama cannot turn a full half-circle, so face its far
  // edge (the viewer clamps the view to the picture).
  if (full) return wrap(inYaw + 180);
  return inYaw >= 0 ? -haov / 2 : haov / 2;
}
