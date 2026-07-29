// door_graph.test.js — regression guard for the door-wiring bug where a door with no explicit `to`
// target leans on the engine's positional fallback and mis-routes. On 2026-07-28 hawaii room3's "beach"
// back door had `to:null` (a hotspot redraw after an art re-gen dropped the target; the Edit-tab "to room"
// dropdown defaults to none), and the fallback — which skips non-`built` rooms and assumes linear array
// order — sent players to the START instead of room2.
//
// RULE: every door in a BUILT room must name its target `to`, EXCEPT the single legitimate terminal case
// — a FORWARD door in the LAST built room of the scenario (the finish door, which routes via the engine's
// `goThrough()` fallback, e.g. alaska escape1's "helicopter hatch"). A `back` door must ALWAYS name its
// target; a non-terminal forward door must too. Runs on every shipped scenario.json. (comparing_means/spa
// was converted from the all-`to:null` fallback pattern to explicit targets on 2026-07-28 to satisfy this.)
const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const ROOMS_DIR = path.resolve(__dirname, "../rooms");

function scenarioFiles(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== "z_done") out.push(...scenarioFiles(p)); }
    else if (e.name === "scenario.json") out.push(p);
  }
  return out;
}

for (const file of scenarioFiles(ROOMS_DIR)) {
  const rel = path.relative(ROOMS_DIR, file);
  test(`door graph: every door names its target — ${rel}`, () => {
    const scn = JSON.parse(fs.readFileSync(file, "utf8"));
    const rooms = scn.rooms || [];
    const isBuilt = r => r && r.built !== false && (r.built === true || (r.hotspots || []).length > 0);
    const lastBuiltIdx = rooms.reduce((acc, r, i) => (isBuilt(r) ? i : acc), -1);

    const offenders = [];
    rooms.forEach((r, i) => {
      if (!isBuilt(r)) return;
      for (const h of (r.hotspots || [])) {
        if (h.type !== "door") continue;
        if (h.to) continue;                                   // explicit target → fine
        const dir = h.direction || "forward";
        const terminalFinish = dir === "forward" && i === lastBuiltIdx;   // the one allowed to be `to:null`
        if (!terminalFinish) {
          offenders.push(`${r.key}: "${h.label || h.id}" (${dir}) has no \`to\` — falls back to positional routing`);
        }
      }
    });

    assert.deepStrictEqual(offenders, [],
      `door(s) missing an explicit target in ${rel}:\n  ${offenders.join("\n  ")}`);
  });
}
