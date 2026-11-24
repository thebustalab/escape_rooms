// Editing this? Read _agent_reference/doors_and_progression.md first (beside this file; local, gitignored).
// THE WARDROBE (first consumer classification/lair, 2026-11-24): things the player WEARS, and the outfit scanners
// that weigh them. Pure logic only, no DOM, so it is unit-tested in Node (tests/wardrobe.test.mjs); the drawing is
// shared/wardrobe_ui.js and pano-player.js owns the cards (the tote, the HUD figure, the scanner card).
//
// Authoring (all optional; a scenario that uses none of it behaves exactly as before):
//   SCENARIO.items[key].slot   "overalls" | "hat" | "armband" | "badge" (wearable) or "carried" (held, never worn).
//                       .colour / .kind   the word a scan log uses for it ("gray", "engineer"). Log rows are
//                       matched to items through these words, never by building key strings (ov_grey is "gray").
//                       .decoy   true: never weighted by any scanner, on purpose (validate_assets item_wiring).
//   SCENARIO.startingItems   keys granted at Begin; the wearables among them are WORN from the start.
//   SCENARIO.scanTime        "night" | "day" (absent => "day"): the time every scan in the scenario reads.
//   door.scannerWeights      {bias, terms:[{time:"any"|"day"|"night", item?|anyOf?, weight}], opensAbove}.
//                            score = bias + the weights of the terms that match; p = 1/(1+e^-score); passes iff
//                            p > opensAbove. A term with neither item nor anyOf applies on time alone.
//   door.scanner             graph metadata; the engine reads scanBudget (refusals before a lockdown) and
//                            lockdownTo (the room a lockdown sends the player to) from it.
//
// The tote IS the inventory (shared/inventory.js): a worn item stays held, so has_<key> keeps meaning "owns it".
// Wearing one item in a slot takes the previous one off (it goes back to the tote, still held).
// World state: worn_<slot> = the key worn in that slot, so an ordinary condition can read it.
import { grantItems } from "./inventory.js?v=183";

export const WEAR_SLOTS = ["overalls", "hat", "armband", "badge"];

const catalogue = scenario => (scenario && scenario.items) || {};

// The slot an item is worn in, or null for anything not wearable ("carried", unknown, no slot).
export function slotOf(items, key) {
  const e = items && items[key];
  return e && WEAR_SLOTS.includes(e.slot) ? e.slot : null;
}
export const isWearable = (items, key) => slotOf(items, key) !== null;

// True when the scenario has anything to wear at all: the switch for the whole feature.
export function hasWardrobe(scenario) {
  const items = catalogue(scenario);
  return Object.keys(items).some(k => isWearable(items, k));
}

export function createWardrobe() {
  return { worn: {}, passed: new Set(), refusals: new Map() };   // worn: slot -> key
}
export function resetWardrobe(w) {
  for (const s of Object.keys(w.worn)) delete w.worn[s];
  w.passed.clear();
  w.refusals.clear();
}

const mirror = (w, state) => {
  if (!state) return;
  for (const s of WEAR_SLOTS) state["worn_" + s] = w.worn[s] || null;
};

// Put on `key` (it must be held and wearable). Returns {ok, slot, displaced}; displaced is the key taken off.
export function wear(w, items, key, held, state) {
  const slot = slotOf(items, key);
  if (!slot || !(held || []).includes(key)) return { ok: false, slot, displaced: null };
  const displaced = w.worn[slot] && w.worn[slot] !== key ? w.worn[slot] : null;
  w.worn[slot] = key;
  mirror(w, state);
  return { ok: true, slot, displaced };
}

export const worn = w => ({ ...w.worn });
export const wornKeys = w => WEAR_SLOTS.map(s => w.worn[s]).filter(Boolean);
export const isWorn = (w, key) => Object.values(w.worn).includes(key);

// Begin: grant the scenario's startingItems into the inventory and wear the wearables among them (the first
// of each slot, in the order listed). Returns the keys granted.
export function startOutfit(w, scenario, inv, state) {
  const start = Array.isArray(scenario && scenario.startingItems) ? scenario.startingItems : [];
  const added = grantItems(inv, start, state);
  if (!hasWardrobe(scenario)) return added;      // nothing to wear: no worn_<slot> keys in the world state at all
  const items = catalogue(scenario);
  for (const k of start) {
    const s = slotOf(items, k);
    if (s && !w.worn[s]) w.worn[s] = k;
  }
  mirror(w, state);
  return added;
}

// The outfit as the words a figure or a log row uses: {overalls:"orange", hat:"yellow", armband:..., badge:"visitor"}.
export function outfitWords(w, items) {
  const out = {};
  for (const s of WEAR_SLOTS) {
    const e = w.worn[s] && items && items[w.worn[s]];
    if (e) out[s] = e.kind || e.colour || null;
  }
  return out;
}

// A log row's words -> item keys, through each item's colour/kind. A word no item carries is dropped.
export function rowKeys(items, row) {
  const keys = [];
  for (const s of WEAR_SLOTS) {
    const word = row && row[s];
    if (!word) continue;
    const k = Object.keys(items || {}).find(k => items[k].slot === s && (items[k].colour === word || items[k].kind === word));
    if (k) keys.push(k);
  }
  return keys;
}

export const scanTimeOf = scenario => (scenario && scenario.scanTime === "night" ? "night" : "day");

function termMatches(t, keys, time) {
  if (!t || !isFinite(+t.weight)) return false;
  const tt = t.time || "any";
  if (tt !== "any" && tt !== time) return false;
  if (t.item != null) return keys.includes(t.item);
  if (Array.isArray(t.anyOf)) return t.anyOf.some(k => keys.includes(k));
  return true;                                   // no item: applies on time alone (the gate's night -1.5)
}
export function scanScore(weights, keys, time) {
  const W = weights || {};
  let s = isFinite(+W.bias) ? +W.bias : 0;
  for (const t of Array.isArray(W.terms) ? W.terms : []) if (termMatches(t, keys || [], time)) s += +t.weight;
  return s;
}
export const sigmoid = x => 1 / (1 + Math.exp(-x));
export const scanProb = (weights, keys, time) => sigmoid(scanScore(weights, keys, time));
export const opensAbove = weights => (weights && isFinite(+weights.opensAbove) ? +weights.opensAbove : 0.5);
export const passes = (weights, keys, time) => scanProb(weights, keys, time) > opensAbove(weights);

// D1: a scanner door once passed stays open for the session. `doorKey` is gateKey(roomKey, id).
export const markPassed = (w, doorKey) => { w.passed.add(doorKey); };
export const hasPassed = (w, doorKey) => w.passed.has(doorKey);

// The scan budget (door.scanner.scanBudget, a positive whole number; absent = unlimited). A refusal counts down;
// the last one returns lockdown:true and resets the count, so the player arrives in the lockdown room with a
// fresh budget. left = refusals still allowed before the lockdown (Infinity with no budget).
export function budgetOf(door) {
  const b = door && door.scanner && door.scanner.scanBudget;
  return Number.isInteger(b) && b > 0 ? b : null;
}
export function recordRefusal(w, doorKey, budget) {
  if (!budget) return { left: Infinity, lockdown: false };
  const n = (w.refusals.get(doorKey) || 0) + 1;
  if (n >= budget) { w.refusals.delete(doorKey); return { left: 0, lockdown: true }; }
  w.refusals.set(doorKey, n);
  return { left: budget - n, lockdown: false };
}
export const refusalsSoFar = (w, doorKey) => w.refusals.get(doorKey) || 0;
