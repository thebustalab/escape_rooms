// ride.js — pure planning logic for THE RIDE (networks/subway, settled with Lucas 2026-09-17).
//
// THE MODEL. A line is an ordered list of named stops. Some stops are BERTHS — a berth room on this line
// exists there, so the player can alight (the transfer stations). Every other stop is passed without
// stopping: a GHOST station (on no map; `cfg.ghosts`) or a LIVE one (a working station). A cab's one
// control is a LEVER that runs the train EXPRESS to the NEXT berth in the chosen direction, so the player
// is never left at a platform they cannot leave. "up" = towards the END of `stops`, "down" = towards the
// start. At the end of the served stretch only one direction is offered.
//
// THE SEQUENCE. A run is a list of segments, each a full-scene clip state looped N times:
//   tunnel = "running", a LIVE pass = "live", a GHOST pass = "ghost", then arrival on "energised".
//   no passes:  running × loops.hop
//   passes:     running × tunnel, pass1 × pass, running × tunnel, pass2 × pass, …, running × tunnel
// which is exactly what `rooms/networks/subway/_scratch/ride_preview.py` composites (RIDES) and what
// Lucas signed off. The engine (pano-player.js) turns loops into seconds and crossfades where the state
// changes; this module never touches time, media or the DOM.
//
// CONFIG (scenario.ride):
//   { loops: {hop, tunnel, pass}, loopSeconds, crossfade, ghosts: [station…],
//     states: {tunnel, live, ghost, arrive},            // optional renames of the four clip states
//     labels: {up, down},                               // optional lever wording
//     lines: { <line>: { cab, stops: [station…], berths: {station: roomKey}, atKey? } } }
//
// DOM-free and import-free, like puzzle_queue.js / variant_resolve.js, so it unit-tests in Node
// (tests/ride.test.mjs) and pano-player.js imports it directly.

export const DEFAULT_LOOPS = { hop: 3, tunnel: 2, pass: 2 };
export const DEFAULT_STATES = { tunnel: "running", live: "live", ghost: "ghost", arrive: "energised" };
export const DEFAULT_LOOP_SECONDS = 2.5;
export const DEFAULT_CROSSFADE = 0.4;

// Is the ride authored at all? Everything below is inert otherwise, which is what keeps every other
// scenario byte-for-byte unchanged.
export function usesRide(scenario) {
  const r = scenario && scenario.ride;
  return !!(r && r.lines && typeof r.lines === "object" && Object.keys(r.lines).length);
}

function lineCfg(cfg, line) {
  const l = cfg && cfg.lines && cfg.lines[line];
  return l && Array.isArray(l.stops) ? l : null;
}

// The world-state key that remembers where this line's train stands (a berth ROOM key).
export function atKey(cfg, line) {
  const l = cfg && cfg.lines && cfg.lines[line];
  return (l && l.atKey) || ("at_" + line);
}

export function loopsOf(cfg) {
  return Object.assign({}, DEFAULT_LOOPS, (cfg && cfg.loops) || {});
}
export function statesOf(cfg) {
  return Object.assign({}, DEFAULT_STATES, (cfg && cfg.states) || {});
}

// "berth" (the player can alight), "ghost", or "live". Null for a name not on the line.
export function stopKind(cfg, line, station) {
  const l = lineCfg(cfg, line);
  if (!l || !l.stops.includes(station)) return null;
  if (l.berths && l.berths[station]) return "berth";
  return (cfg.ghosts || []).includes(station) ? "ghost" : "live";
}

export function berthRoom(cfg, line, station) {
  const l = lineCfg(cfg, line);
  return (l && l.berths && l.berths[station]) || null;
}

export function stationOfRoom(cfg, line, roomKey) {
  const l = lineCfg(cfg, line);
  if (!l || !l.berths) return null;
  const hit = Object.keys(l.berths).find(st => l.berths[st] === roomKey);
  return hit || null;
}

// Where the train stands, given the remembered berth room key. An unset / foreign value falls back to the
// line's first berth in stop order (only reachable by a test-play jump straight into a cab — a real player
// always boards through a berth door, which sets the key).
export function currentStation(cfg, line, roomKey) {
  const l = lineCfg(cfg, line);
  if (!l) return null;
  const st = stationOfRoom(cfg, line, roomKey);
  if (st) return st;
  return l.stops.find(s => l.berths && l.berths[s]) || null;
}

// The next berth from `station` in direction `dir`, with the stops passed on the way.
export function nextTransfer(cfg, line, station, dir) {
  const l = lineCfg(cfg, line);
  if (!l || (dir !== "up" && dir !== "down")) return null;
  const i = l.stops.indexOf(station);
  if (i < 0) return null;
  const step = dir === "up" ? 1 : -1;
  const passed = [];
  for (let j = i + step; j >= 0 && j < l.stops.length; j += step) {
    const st = l.stops[j];
    if (l.berths && l.berths[st]) return { station: st, room: l.berths[st], passed };
    passed.push(st);
  }
  return null;                                   // end of the served stretch: no berth further on
}

// The directions the lever offers from here, in a fixed order (up first).
export function availableDirections(cfg, line, station) {
  return ["up", "down"].filter(d => nextTransfer(cfg, line, station, d));
}

// The full plan for one pull of the lever, or null when that direction goes nowhere.
export function planRide(cfg, line, station, dir) {
  const hop = nextTransfer(cfg, line, station, dir);
  if (!hop) return null;
  const loops = loopsOf(cfg), S = statesOf(cfg);
  const segments = [];
  const tunnel = n => segments.push({ state: S.tunnel, kind: "tunnel", loops: n });
  if (!hop.passed.length) {
    tunnel(loops.hop);
  } else {
    tunnel(loops.tunnel);
    hop.passed.forEach((st, k) => {
      const kind = stopKind(cfg, line, st);       // never "berth": the express stops at the first berth
      segments.push({ state: kind === "ghost" ? S.ghost : S.live, kind, station: st, loops: loops.pass });
      tunnel(loops.tunnel);
    });
  }
  return {
    line, dir, from: station, to: hop.station, toRoom: hop.room,
    segments,
    arrival: { state: S.arrive, station: hop.station, room: hop.room },
  };
}

// The lever's buttons: one per available direction, naming where it runs to.
export function leverOptions(cfg, line, station) {
  const lab = Object.assign({ up: "Up-line", down: "Down-line" }, (cfg && cfg.labels) || {});
  return availableDirections(cfg, line, station).map(dir => {
    const hop = nextTransfer(cfg, line, station, dir);
    return { dir, to: hop.station, toRoom: hop.room, label: `${lab[dir]} — to ${hop.station}` };
  });
}

// Seconds on screen for a plan, given a per-state clip length (seconds) — a missing length means the
// state's still stands in for the nominal loopSeconds. Crossfades overlap neighbouring segments where the
// state changes, as in ride_preview.py. Used by tests and by anyone budgeting ride length.
export function rideSeconds(cfg, plan, clipSeconds) {
  if (!plan) return 0;
  const loopS = (cfg && cfg.loopSeconds) || DEFAULT_LOOP_SECONDS;
  const xf = (cfg && cfg.crossfade != null) ? cfg.crossfade : DEFAULT_CROSSFADE;
  const len = st => (clipSeconds && clipSeconds[st] > 0) ? clipSeconds[st] : loopS;
  let t = 0, prev = null;
  plan.segments.forEach(s => {
    if (prev != null && prev !== s.state) t -= xf;
    t += s.loops * len(s.state); prev = s.state;
  });
  return t;
}
