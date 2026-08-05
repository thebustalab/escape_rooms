// net_graph.test.js — regression tests for the build_world console's metro-map network view
// (authoring_v2/ui/net_graph.js), pinning the geometry fixes from the 2026-08-04 art-pipeline session.
//
// FAILURE MODE THIS GUARDS (why it exists):
//   The network draws each room as a top-down 360 minimap circle and runs a line from each door to the
//   room it leads to. Two bugs shipped and were fixed:
//   (1) RING ORIENTATION was inverted — "ahead" (panorama x=0.5) was placed at the BOTTOM of the circle and
//       the seam at the top. So a right-of-centre door (x≈0.8) landed on the LEFT of its circle, and the
//       connector had to cut back ACROSS the source circle to reach a right-hand neighbour — it read as a
//       line from one part of a circle to another part of the SAME circle. Fix: x=0.5 = ahead = TOP
//       (ring uses `x-0.5`), so a forward door sits on the side facing its neighbour.
//   (2) DOOR-TO-DOOR LANDING — the edge landed on the target's ring EDGE, not its door, when the target had
//       no door pointing back to the source. A monorail car has ONE (two-view) door whose `to` points
//       onward, so station1→car_sq found no return door and missed the car's door. Fix: land on the
//       target's return door; else a single-door room's only door; else nearest-facing; else the edge.
//   Plus: a multi-view door (opensOnto → views>1) gets an outer ring; a `switch` hotspot renders in its own
//   colour (not mistaken for a puzzle).
// If any assertion below regresses, the arrow geometry / role rendering has broken again.

const test = require("node:test");
const assert = require("node:assert");
const NG = require("../authoring_v2/ui/net_graph.js");

// the trees 3-room slice, shaped exactly as /api/scenario-state returns it (planned + doors carry `x`)
const ROOMS = [
  { key: "station1", title: "Lowest station", hasSpec: true,
    planned: [{ id: "mist", type: "ambient", label: "mist", x: 0.08 },
              { id: "field_instrument", type: "puzzle", label: "instrument", x: 0.50 },
              { id: "square_door", type: "door", label: "door", x: 0.80 }],
    doors: [{ to: "car_sq", direction: "forward", views: 0, x: 0.80 }] },
  { key: "car_sq", title: "Square car", hasSpec: true,
    planned: [{ id: "beetles", type: "ambient", label: "beetles", x: 0.50 },
              { id: "drive_lever", type: "switch", label: "a heavy brass drive lever", x: 0.80 },
              { id: "square_door", type: "door", label: "car door", x: 0.92 }],
    doors: [{ to: "station2", direction: "forward", views: 2, x: 0.92 }] },
  { key: "station2", title: "Higher station", hasSpec: true,
    planned: [{ id: "square_passage", type: "door", label: "passage", x: 0.08 },
              { id: "field_instrument", type: "puzzle", label: "instrument", x: 0.50 },
              { id: "circle_door", type: "door", label: "circle door", x: 0.92 }],
    doors: [{ to: "car_sq", direction: "back", views: 0, x: 0.08 },
            { to: "car_ci", direction: "forward", views: 0, x: 0.92 }] },  // car_ci not spec'd -> no line
];

const close = (a, b, tol = 0.2) => Math.abs(a - b) <= tol;
function bezierEdges(html) {   // the real door edges (cubic C); arrowhead marker paths are "M0,0 L.." and don't match
  return [...html.matchAll(/<path d="M ([\d.]+) ([\d.]+) C [\d.-]+ [\d.-]+ [\d.-]+ [\d.-]+ ([\d.]+) ([\d.]+)"/g)]
    .map(m => ({ sx: +m[1], sy: +m[2], tx: +m[3], ty: +m[4] }));
}
const edgeFrom = (edges, port) => edges.find(e => close(e.sx, port[0]) && close(e.sy, port[1]));

test("orientation: ahead (x=0.5) is at the TOP of the circle, the seam (x=0/1) at the bottom", () => {
  const ahead = NG.ringPort(ROOMS, "station1", 0.5);
  const behind = NG.ringPort(ROOMS, "station1", 0.0);
  assert.ok(ahead[1] < behind[1], "ahead should sit above behind (smaller y = higher)");
  assert.ok(close(ahead[0], behind[0]), "ahead and behind are vertically aligned (top vs bottom)");
});

test("station1 -> car_sq edge LANDS on the car's door (bug #2: was missing to the circle edge)", () => {
  const edges = bezierEdges(NG.buildNetSvg(ROOMS).html);
  const e = edgeFrom(edges, NG.ringPort(ROOMS, "station1", 0.80));
  assert.ok(e, "there is an edge leaving station1's door port");
  const carDoor = NG.ringPort(ROOMS, "car_sq", 0.92);
  assert.ok(close(e.tx, carDoor[0]) && close(e.ty, carDoor[1]),
    `edge should end on car_sq's door port ${carDoor}, got (${e.tx},${e.ty})`);
});

test("car_sq -> station2 lands door-to-door on station2's return (back) door", () => {
  const edges = bezierEdges(NG.buildNetSvg(ROOMS).html);
  const e = edgeFrom(edges, NG.ringPort(ROOMS, "car_sq", 0.92));
  assert.ok(e, "there is an edge leaving car_sq's door port");
  const ret = NG.ringPort(ROOMS, "station2", 0.08);   // station2's square_passage back -> car_sq
  assert.ok(close(e.tx, ret[0]) && close(e.ty, ret[1]),
    `edge should end on station2's return door ${ret}, got (${e.tx},${e.ty})`);
});

test("only edges to spec'd rooms are drawn (station2 -> car_ci is skipped)", () => {
  const edges = bezierEdges(NG.buildNetSvg(ROOMS).html);
  assert.strictEqual(edges.length, 3, "station1->car_sq, car_sq->station2, station2->car_sq(back) = 3");
});

test("a multi-view door (views>1) gets an at-a-glance outer ring", () => {
  const html = NG.buildNetSvg(ROOMS).html;
  assert.ok(html.includes('r="8.5"'), "the two-view car door should draw its r=8.5 outer ring");
  // exactly one multi-view door in this slice
  assert.strictEqual((html.match(/r="8.5"/g) || []).length, 1);
});

test("a `switch` hotspot renders in the switch colour, distinct from a puzzle", () => {
  const html = NG.buildNetSvg(ROOMS).html;
  assert.ok(html.includes(NG.TYPE_COL.switch), "drive_lever should use the switch colour");
  assert.notStrictEqual(NG.TYPE_COL.switch, NG.TYPE_COL.puzzle, "switch and puzzle colours must differ");
});

test("every spec'd room becomes one circle", () => {
  const html = NG.buildNetSvg(ROOMS).html;
  assert.strictEqual((html.match(/rmcircle/g) || []).length, 3);
});
