// map_graph.js — pure room-graph renderer, shared by the AUTHORING harness (build_world's network view)
// and the PLAYER's in-game fog-of-war map. NO DOM, so it works in the browser (attaches
// window.MapGraph) AND under node (module.exports) — which lets tests/map_graph.test.js drive the layout
// and edge geometry headless.
//
// Moved here from authoring_v2/ui/net_graph.js on 2026-09-15 (plan: notes/player_map_plan.md, Phase 1).
// It had to move: `authoring_v2/` is gitignored and never reaches GitHub Pages, so a module living there
// can never be loaded by a student. `shared/` is the player's runtime. The harness now imports THIS copy,
// so there is one layout algorithm rather than two that drift.
//
// GEOMETRY. Each room is a top-down 360 minimap circle; hotspots sit on the ring at their real panorama
// angle (x=0.5 = ahead = TOP; x=0/1 = seam/behind = bottom). A door line leaves that door's port and runs
// door-to-door to the target.
//
// POSITIONS. Two sources, in this order:
//   1. `room.mapPos: {c,r}` — integer grid cell, hand-authored in the harness layout editor (Phase 2).
//   2. Otherwise the deterministic auto-layout (`layoutRooms`): columns by door depth, rows by
//      barycentre. Absent `mapPos` everywhere ⇒ the auto-layout is used verbatim, so a scenario that has
//      never been laid out by hand draws exactly as it always did.
// Auto-layout exists to SEED the editor, not to be shipped: it ranks left-to-right by door depth, so a
// near-linear scenario lands in one row (heist 12.5:1, trees 10.0:1 — unreadable in a portrait modal).
// Hand-placed cells are also what keeps FOG coherent: an auto-layout would re-rank and re-flow every time
// a room was revealed, so rooms would move under the player as they explored.
//
// MODES. `buildNetSvg(spec, {mode})`:
//   "author" (default) — per-hotspot type dots, tooltips, multi-view rings, direction-coded arrows.
//   "player"           — plain nodes only. The author dots show where every puzzle, clue and switch sits,
//                        which would spoil rooms outright; and the player gets undirected, deduped lines
//                        because v1 of the map is a read-only orientation aid, not a route planner.
(function (root) {
  "use strict";
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const TYPE_COL = { ambient: "#8fa3b0", puzzle: "#ffd88c", door: "#7fd1ff", clue: "#7bd88c", switch: "#c79cff" };
  const DIR_COL = { forward: "#7fd1ff", back: "#8fa3b0", open: "#7bd88c" }, DIR_DASH = { forward: "", back: "5,4", open: "2,4" };
  const R = 36, DX = 168, DY = 128, MX = 70, MY = 66, K = 42;

  function layoutRooms(rooms) {
    const byKey = {}; rooms.forEach(r => byKey[r.key] = r);
    // Rank on DIRECTED edges only. An `open` door is a bidirectional passage, so counting it as a
    // forward edge makes every open pair a 2-cycle — and the longest-path relaxation below then keeps
    // pushing ranks up until it hits the pass cap. That is how heist reached rank 20 and beacons rank
    // 34 with nothing at rank 0, leaving thousands of px of dead space to the LEFT of the first room
    // (2026-09-03). Open-world scenarios have no forward doors at all, so they fall back to BFS depth.
    const dir = k => (byKey[k].doors || []).filter(d => (d.direction || "forward") === "forward" && d.to && byKey[d.to]).map(d => d.to);
    const undir = k => (byKey[k].doors || []).filter(d => d.to && byKey[d.to]).map(d => d.to);
    // Layer by BFS depth from the entry room over the UNDIRECTED door graph — that is what gives an
    // open world a left-to-right reading ("how far from the start") instead of collapsing every room
    // into one very tall column. Then relax the genuinely DIRECTED (forward) edges on top, so a
    // forward door always steps its target at least one column right.
    // LEGACY scenarios (alaska, trees) predate `to` on doors — the engine advanced linearly, so the
    // door graph has no edges at all and BFS would leave every room at depth 0, stacking them into one
    // very tall column. Fall back to scenario.json order, which IS the linear route (2026-09-03).
    const anyTo = rooms.some(r => (r.doors || []).some(d => d.to));
    const rank = {};
    if (!anyTo) { rooms.forEach((r, i) => rank[r.key] = i); }
    else if (rooms.length) {
      const seen = { [rooms[0].key]: 0 }; let frontier = [rooms[0].key];
      while (frontier.length) {
        const next = [];
        frontier.forEach(k => undir(k).forEach(t => { if (!(t in seen)) { seen[t] = seen[k] + 1; next.push(t); } }));
        frontier = next;
      }
      rooms.forEach(r => rank[r.key] = seen[r.key] == null ? 0 : seen[r.key]);
    }
    for (let pass = 0; pass < rooms.length; pass++) {            // deterministic; forward edges win ties
      let changed = false;
      rooms.forEach(r => dir(r.key).forEach(t => { if (rank[t] < rank[r.key] + 1) { rank[t] = rank[r.key] + 1; changed = true; } }));
      if (!changed) break;
    }
    // Rebase so the leftmost column is 0. Without this the graph is drawn far to the right of the
    // viewBox origin and the panel opens on empty space.
    const minRank = Math.min(...rooms.map(r => rank[r.key]));
    rooms.forEach(r => rank[r.key] -= minRank);
    const cols = {}; rooms.forEach(r => (cols[rank[r.key]] = cols[rank[r.key]] || []).push(r.key));
    const ranks = Object.keys(cols).map(Number).sort((a, b) => a - b);
    const row = {};
    ranks.forEach(rk => {
      const list = cols[rk];
      const bary = k => { const ps = rooms.filter(r => dir(r.key).includes(k) || undir(r.key).includes(k)); return ps.length ? ps.reduce((s, p) => s + (row[p.key] || 0), 0) / ps.length : list.indexOf(k); };
      list.sort((a, b) => bary(a) - bary(b)).forEach((k, i) => row[k] = i);
    });
    return { rank, row, cols, ranks };
  }

  // Grid cell per room: authored `mapPos` wins, the auto-layout fills the rest. Pure + deterministic.
  // Returns `collided` so the harness editor and the validator can SHOW a double-booked cell rather
  // than silently dropping one of the two rooms.
  function resolvePositions(rooms) {
    const cell = {}, taken = new Set(), authored = new Set(), collided = [];
    const ck = (c, r) => c + "," + r;
    rooms.forEach(r => {
      const p = r.mapPos;
      if (!p || !isFinite(p.c) || !isFinite(p.r)) return;
      const c = Math.round(p.c), rw = Math.round(p.r);
      if (taken.has(ck(c, rw))) { collided.push(r.key); return; }   // first claimant keeps the cell; this one is auto-placed below
      cell[r.key] = { c, r: rw }; taken.add(ck(c, rw)); authored.add(r.key);
    });
    const missing = rooms.filter(r => !cell[r.key]);
    if (missing.length) {
      const L = layoutRooms(rooms);
      const maxRows = Math.max(1, ...L.ranks.map(rk => L.cols[rk].length));
      const autoCell = k => {
        const rk = L.rank[k];
        return { c: rk, r: L.row[k] + (maxRows - L.cols[rk].length) / 2 };   // fractional: vertical centring
      };
      if (!authored.size) {
        // Nothing authored. Use the auto-layout verbatim, fractional centring included, so the harness
        // view stays pixel-identical to what it drew before mapPos existed.
        missing.forEach(r => cell[r.key] = autoCell(r.key));
      } else {
        // Mixed. Authored cells are fixed points, so a stray takes the first free INTEGER cell at or
        // below its auto position. Deterministic — the same input always lands the same way.
        missing.forEach(r => {
          const a = autoCell(r.key); let c = a.c, rw = Math.round(a.r);
          while (taken.has(ck(c, rw))) rw += 1;
          cell[r.key] = { c, r: rw }; taken.add(ck(c, rw));
        });
      }
    }
    return { cell, authored, collided };
  }

  // Integer, collision-free cells for every room — what the harness layout editor opens on.
  // `resolvePositions` returns FRACTIONAL rows wherever it falls back to the auto-layout (which centres
  // each column vertically), and a snap-grid editor must never open already holding two rooms in one
  // square. Rounding can collide, so a duplicate is pushed down until it finds a free cell.
  function gridCells(rooms) {
    const { cell } = resolvePositions(rooms);
    const out = {}, taken = new Set();
    rooms.forEach(r => {
      const q = cell[r.key] || { c: 0, r: 0 };
      let c = Math.max(0, Math.round(q.c)), rw = Math.max(0, Math.round(q.r));
      while (taken.has(c + "," + rw)) rw += 1;
      taken.add(c + "," + rw);
      out[r.key] = { c: c, r: rw };
    });
    return out;
  }

  // Grid cells -> absolute pixels + the viewBox the caller needs.
  //
  // REBASE (default on). Hand-authored cells need not start at the origin — egypt was laid out at
  // columns 2–4, rows 1–4, which rendered two empty columns and an empty row of dead space and shrank
  // the rooms for no reason. `layoutRooms` already rebases its own ranks for exactly this reason ("the
  // panel opens on empty space"); authored cells were missing the same treatment.
  // The harness LAYOUT EDITOR passes `rebase:false`, deliberately: it draws its grid lines and converts
  // pointer positions back to cells in ABSOLUTE coordinates, and a view that slid sideways whenever you
  // dragged the leftmost room would be horrible to author in. Its cells are normalised on SAVE instead.
  function pixelPositions(rooms, opts) {
    const res = resolvePositions(rooms);
    const rebase = !(opts && opts.rebase === false);
    let minC = Infinity, minR = Infinity;
    rooms.forEach(r => {
      const q = res.cell[r.key]; if (!q) return;
      if (q.c < minC) minC = q.c;
      if (q.r < minR) minR = q.r;
    });
    const offC = rebase && isFinite(minC) ? minC : 0, offR = rebase && isFinite(minR) ? minR : 0;
    const pos = {}; let maxC = 0, maxR = 0;
    rooms.forEach(r => {
      const q = res.cell[r.key]; if (!q) return;
      const c = q.c - offC, rw = q.r - offR;
      pos[r.key] = { x: MX + c * DX, y: MY + rw * DY };
      if (c > maxC) maxC = c;
      if (rw > maxR) maxR = rw;
    });
    return { pos, W: MX * 2 + maxC * DX, H: MY * 2 + maxR * DY,
             cell: res.cell, authored: res.authored, collided: res.collided, offset: { c: offC, r: offR } };
  }

  // Fog tiers. Kept HERE rather than in the player so the rule has one tested home:
  //   visited  — the player has stood in it
  //   known    — not visited, but named by the `to` of a door in a room they HAVE stood in
  //   unknown  — neither; not drawn at all, so the map never previews an untouched wing
  function fogTiers(rooms, fog) {
    const visited = new Set(fog && fog.visited || []);
    const byKey = {}; rooms.forEach(r => byKey[r.key] = r);
    const known = new Set();
    rooms.forEach(r => {
      if (!visited.has(r.key)) return;
      (r.doors || []).forEach(d => { if (d.to && byKey[d.to] && !visited.has(d.to)) known.add(d.to); });
    });
    return { visited, known, visible: k => visited.has(k) || known.has(k) };
  }

  const ring = (c, x) => [c.x + R * Math.sin(2 * Math.PI * (x - 0.5)), c.y - R * Math.cos(2 * Math.PI * (x - 0.5))];  // x=.5 top(ahead), 0/1 bottom(seam/behind)

  function buildNetSvg(spec, opts) {                             // pure: rooms[] -> {W,H,html}; no DOM, so unit-testable
    const o = opts || {}, player = o.mode === "player";
    const byKey = {}; spec.forEach(r => byKey[r.key] = r);
    // Rebase defaults to the mode — the player gets the tight view, the author view stays absolute —
    // but an EXPLICIT `rebase` always wins. The harness layout editor needs player-style rendering
    // (plain nodes, straight edges) with ABSOLUTE positions, because it draws its own grid lines and
    // converts pointer positions back to cells in absolute coordinates. Forcing rebase on for any
    // `mode:"player"` call drew egypt's nodes 336px left and 128px up of its own grid (2026-09-15).
    const rebase = o.rebase === undefined ? player : !!o.rebase;
    const { pos, W, H } = pixelPositions(spec, { rebase: rebase });
    const tiers = player && o.fog ? fogTiers(spec, o.fog) : null;
    const shown = k => (!tiers ? true : tiers.visible(k));
    let edges = "";
    if (player) {
      // Undirected + deduped. A bidirectional `open` pair authors two doors and would otherwise draw
      // two identical lines on top of each other; and an orientation aid does not need arrowheads.
      // Only rooms the player has ENTERED reveal their doors — a `known` room's own exits stay hidden.
      const seen = new Set();
      spec.forEach(r => {
        if (tiers && !tiers.visited.has(r.key)) return;
        (r.doors || []).forEach(d => {
          const s = pos[r.key], t = pos[d.to];
          if (!s || !t || !shown(d.to)) return;
          const pair = r.key < d.to ? r.key + "|" + d.to : d.to + "|" + r.key;
          if (seen.has(pair)) return;
          seen.add(pair);
          // STRAIGHT, centre to centre (Lucas, 2026-09-15). The author view leaves each door's port at
          // its real panorama angle and curves out along the normal — that encodes WHERE IN THE ROOM the
          // door is, which is an authoring fact and unreadable as anything else on a grid map. A player
          // is asking one question, "do these two connect", and a straight line answers it.
          // Trimmed to the circle edge rather than run under the nodes: a `known` room's circle is
          // semi-transparent, so an undrawn-through line would show as a smudge inside it.
          const dx = t.x - s.x, dy = t.y - s.y, len = Math.hypot(dx, dy) || 1;
          const ux = dx / len, uy = dy / len;
          edges += `<line class="mapedge" x1="${(s.x + ux * R).toFixed(1)}" y1="${(s.y + uy * R).toFixed(1)}"`
                 + ` x2="${(t.x - ux * R).toFixed(1)}" y2="${(t.y - uy * R).toFixed(1)}"/>`;
        });
      });
    } else {
      spec.forEach(r => (r.doors || []).forEach(d => {
        const s = pos[r.key], t = pos[d.to]; if (!s || !t) return;   // target not spec'd yet: its port dot shows, no line
        const [px, py] = ring(s, d.x == null ? 0.5 : d.x);
        // land door-to-door: prefer the target's door that returns here; then a single-door room's only door (the
        // car's two-view door IS the way in); then the nearest-facing door; else the target ring point facing us.
        const tdoors = byKey[d.to].doors || [];
        let td = tdoors.find(b => b.to === r.key);
        if (!td && tdoors.length === 1) td = tdoors[0];
        if (!td && tdoors.length) td = tdoors.reduce((m, b) => { const [bx, by] = ring(t, b.x == null ? 0.5 : b.x), dd = (bx - px) ** 2 + (by - py) ** 2; return m && m.dd <= dd ? m : { b, dd }; }, null).b;
        let tx, ty;
        if (td) { [tx, ty] = ring(t, td.x == null ? 0.5 : td.x); }
        else { const ang = Math.atan2(py - t.y, px - t.x); tx = t.x + Math.cos(ang) * R; ty = t.y + Math.sin(ang) * R; }
        const dir = d.direction || "forward";
        // control points along each port's OUTWARD normal, so the line leaves/enters radially and never crosses a circle
        const c1x = px + (px - s.x) / R * K, c1y = py + (py - s.y) / R * K, c2x = tx + (tx - t.x) / R * K, c2y = ty + (ty - t.y) / R * K;
        edges += `<path d="M ${px.toFixed(1)} ${py.toFixed(1)} C ${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)}" fill="none" stroke="${DIR_COL[dir]}" stroke-width="1.8"${DIR_DASH[dir] ? ` stroke-dasharray="${DIR_DASH[dir]}"` : ""} marker-end="url(#arw-${dir})"/>`;
      }));
    }
    let nodes = "";
    spec.forEach(r => {
      const p = pos[r.key]; if (!p || !shown(r.key)) return;
      if (player) {
        const isVisited = !tiers || tiers.visited.has(r.key);
        const cls = ["rmnode", isVisited ? "rm-visited" : "rm-known", o.fog && o.fog.current === r.key ? "rm-current" : ""].filter(Boolean).join(" ");
        // A `known` room is somewhere the player has SEEN A DOOR TO and not entered — it gets a mark,
        // never its name, or the map would hand over the shape of rooms they have not reached.
        const label = isVisited
          ? `<text class="rmname" x="${p.x}" y="${p.y + 4}">${esc(r.title || r.key)}</text>`
          : `<text class="rmname rm-unvisited" x="${p.x}" y="${p.y + 5}">?</text>`;
        // No solved/unsolved state on the map (Lucas, 2026-09-15). It is an orientation aid — where am I,
        // how do I get back — and a progress tracker is a different tool that would invite reading the
        // map as a checklist. `solvedRooms` is deliberately NOT passed in.
        nodes += `<g class="${cls}" data-room="${esc(r.key)}"><circle class="rmcircle" cx="${p.x}" cy="${p.y}" r="${R}"/>${label}</g>`;
        return;
      }
      let dots = "";
      (r.planned || []).forEach(h => {
        const x = h.x == null ? 0.5 : h.x, [hx, hy] = ring(p, x);
        const anchor = Math.sin(2 * Math.PI * (x - 0.5)) >= 0 ? "start" : "end", lx = hx + (anchor === "start" ? 7 : -7);
        let info = `<b>${esc(h.type)}</b> — ${esc(h.label || h.id)}`, extra = "";
        if (h.type === "door") {                                // fold the door's target + view-count onto its port
          const dd = (r.doors || []).find(d => d.x === h.x) || (r.doors || [])[0];
          if (dd) {
            info += `<br>→ <b>${esc(dd.to || "?")}</b> (${esc(dd.direction)}${dd.views > 1 ? `, ${dd.views} views` : ""})`;
            if (dd.views > 1) extra = `<circle cx="${hx.toFixed(1)}" cy="${hy.toFixed(1)}" r="8.5" fill="none" stroke="${TYPE_COL.door}" stroke-width="1"/>`;  // multi-view door: at-a-glance ring
          }
        }
        dots += `<circle class="hs" cx="${hx.toFixed(1)}" cy="${hy.toFixed(1)}" r="5" fill="${TYPE_COL[h.type] || "#fff"}" data-info="${info}"/>${extra}`
             + `<text class="hstype" x="${lx.toFixed(1)}" y="${(hy + 3).toFixed(1)}" text-anchor="${anchor}" fill="${TYPE_COL[h.type] || "#fff"}">${esc(h.type)}</text>`;
      });
      nodes += `<g data-room="${esc(r.key)}"><circle class="rmcircle" cx="${p.x}" cy="${p.y}" r="${R}"/>${dots}`
            + `<text class="rmlabel" x="${p.x}" y="${p.y - 1}">${esc(r.key)}</text>`
            + `<text class="rmsub" x="${p.x}" y="${p.y + 10}">${esc((r.title || "").slice(0, 18))}</text></g>`;
    });
    if (player) return { W, H, html: `${edges}${nodes}` };
    const defs = Object.keys(DIR_COL).map(dir => `<marker id="arw-${dir}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="${DIR_COL[dir]}"/></marker>`).join("");
    return { W, H, html: `<defs>${defs}</defs>${edges}${nodes}` };
  }

  // helpers the test asserts against without re-deriving the layout constants
  function ringPort(spec, roomKey, x) {                         // absolute (x,y) of a hotspot/door port on its circle
    const c = pixelPositions(spec, { rebase: false }).pos[roomKey];
    if (!c) return null;
    return ring(c, x);
  }

  const api = { esc, TYPE_COL, DIR_COL, DIR_DASH, GEOM: { R, DX, DY, MX, MY, K },
                layoutRooms, resolvePositions, gridCells, pixelPositions, fogTiers, buildNetSvg, ringPort };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MapGraph = api;
})(typeof self !== "undefined" ? self : this);
