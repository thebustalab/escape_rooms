// THE INVENTORY (Lucas, 2026-10-24, first consumer regression/dunes): things the player CARRIES — a key, a
// rope — and a door that asks which one to use. Pure logic only, so it is unit-tested without a browser
// (tests/inventory.test.mjs); pano-player.js owns the DOM (the "use what?" card, the notebook's
// "Carrying" row).
//
// Authoring (all optional; a scenario that uses none of it behaves exactly as before):
//   SCENARIO.items = { store_key: { name: "the store key", image?: "items/store_key.png" }, ... }
//   a gate (puzzle/lock/grid/ledger) or a clue: `gives: "store_key"` (or an array). A gate grants on its
//     first solve; a clue grants when the player takes it.
//   a door: `needsItem: "store_key"` — locked until the player picks that item from the door's card.
//     `consumes: true` takes the item away when it is used (a rope tied off at the winch); default keeps it.
//     `useBody` (the line shown when it works), `wrongItemBody` (when the wrong thing is tried), `onUse`
//     (world-state effects, the same {set,to}/{inc} grammar as onSolve/onPass).
//   Once the right item has been used the door stays unlocked for the session, consumed item or not.
//
// WHY THE DOOR ASKS (not auto-use): with two keys in hand the player should choose which to try. A door
// that silently picks the right one turns carrying into bookkeeping (Lucas, 2026-10-24).
//
// World state: holding an item mirrors to gameState["has_<key>"] = true (false once consumed), so the
// existing condition grammar can gate on it — e.g. a cliff that refuses until you hold both pulleys:
//   availableWhen: {all: [{eq: ["has_moon_pulley", true]}, {eq: ["has_sun_pulley", true]}]}

export function createInventory() {
  return { held: [], unlocked: new Set() };   // held: item keys in the order taken
}

export function resetInventory(inv) {
  inv.held.length = 0;
  inv.unlocked.clear();
}

const asList = x => (x == null ? [] : Array.isArray(x) ? x : [x]).filter(k => typeof k === "string" && k);

// Add the item(s) a gate or clue gives. Returns the keys newly added (an item already held is not doubled).
export function grantItems(inv, gives, state) {
  const added = [];
  for (const k of asList(gives)) {
    if (inv.held.includes(k)) continue;
    inv.held.push(k);
    added.push(k);
    if (state) state["has_" + k] = true;
  }
  return added;
}

export const doorUnlockKey = (roomKey, door) => roomKey + "|" + (door.id || door.label || "door");

// True while an item door has not yet been opened with its item. A door with no `needsItem` is never
// item-locked.
export function itemLocked(inv, roomKey, door) {
  return !!(door && door.needsItem) && !inv.unlocked.has(doorUnlockKey(roomKey, door));
}

// The player picks `itemKey` on `door`'s card. Wrong or not-held → {ok:false}. Right → the door is
// unlocked for the session and, if the door `consumes`, the item leaves the inventory.
export function useItem(inv, roomKey, door, itemKey, state) {
  if (!door || !door.needsItem || !inv.held.includes(itemKey) || itemKey !== door.needsItem)
    return { ok: false };
  inv.unlocked.add(doorUnlockKey(roomKey, door));
  let consumed = false;
  if (door.consumes) {
    inv.held.splice(inv.held.indexOf(itemKey), 1);
    consumed = true;
    if (state) state["has_" + itemKey] = false;
  }
  return { ok: true, consumed };
}

// Display info for an item: the catalogue entry, else a readable name made from the key.
export function itemInfo(scenario, key) {
  const cat = (scenario && scenario.items) || {};
  const e = cat[key] || {};
  return { key, name: e.name || String(key).replace(/_/g, " "), image: e.image || "" };
}
