// net_graph.js — pure metro-map network builder for the build_world console. NO DOM, so it works in the
// browser (attaches window.NetGraph) AND under node (module.exports) — which lets tests/net_graph.test.js
// drive the layout + edge geometry headless. Extracted from build_world.html 2026-08-04 so the arrow-routing
// fixes (ring orientation + door-to-door landing) are regression-tested (see that test's header).
//
// Each room is a top-down 360 minimap circle; hotspots sit on the ring at their real panorama angle
// (x=0.5 = ahead = TOP; x=0/1 = seam/behind = bottom). A door line leaves that door's port and runs
// door-to-door to the target. Rooms are layered left→right by forward-door depth (deterministic, no jitter).
(function (root) {
  "use strict";
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const TYPE_COL = { ambient: "#8fa3b0", puzzle: "#ffd88c", door: "#7fd1ff", clue: "#7bd88c", switch: "#c79cff" };
  const DIR_COL = { forward: "#7fd1ff", back: "#8fa3b0", open: "#7bd88c" }, DIR_DASH = { forward: "", back: "5,4", open: "2,4" };

  function layoutRooms(rooms) {
    const byKey = {}; rooms.forEach(r => byKey[r.key] = r);
    const fwd = k => (byKey[k].doors || []).filter(d => d.direction !== "back" && d.to && byKey[d.to]).map(d => d.to);
    const incF = {}; rooms.forEach(r => fwd(r.key).forEach(t => incF[t] = (incF[t] || 0) + 1));
    const rank = {}; rooms.forEach(r => rank[r.key] = 0);
    for (let pass = 0; pass < rooms.length; pass++) {            // longest-path rank by relaxation (deterministic)
      let changed = false;
      rooms.forEach(r => fwd(r.key).forEach(t => { if (rank[t] < rank[r.key] + 1) { rank[t] = rank[r.key] + 1; changed = true; } }));
      if (!changed) break;
    }
    const cols = {}; rooms.forEach(r => (cols[rank[r.key]] = cols[rank[r.key]] || []).push(r.key));
    const ranks = Object.keys(cols).map(Number).sort((a, b) => a - b);
    const row = {};
    ranks.forEach(rk => {
      const list = cols[rk];
      const bary = k => { const ps = rooms.filter(r => fwd(r.key).includes(k)); return ps.length ? ps.reduce((s, p) => s + (row[p.key] || 0), 0) / ps.length : list.indexOf(k); };
      list.sort((a, b) => bary(a) - bary(b)).forEach((k, i) => row[k] = i);
    });
    return { rank, row, cols, ranks };
  }

  function buildNetSvg(spec) {                                   // pure: rooms[] -> {W,H,html}; no DOM, so unit-testable
    const byKey = {}; spec.forEach(r => byKey[r.key] = r);
    const L = layoutRooms(spec);
    const R = 36, DX = 168, DY = 128, MX = 70, MY = 66, K = 42;
    const maxRows = Math.max(1, ...L.ranks.map(rk => L.cols[rk].length)), maxRank = Math.max(0, ...L.ranks);
    const pos = {};
    L.ranks.forEach(rk => { const list = L.cols[rk], off = (maxRows - list.length) / 2; list.forEach(k => pos[k] = { x: MX + rk * DX, y: MY + (L.row[k] + off) * DY }); });
    const W = MX * 2 + maxRank * DX, H = MY * 2 + (maxRows - 1) * DY;
    const ring = (c, x) => [c.x + R * Math.sin(2 * Math.PI * (x - 0.5)), c.y - R * Math.cos(2 * Math.PI * (x - 0.5))];  // x=.5 top(ahead), 0/1 bottom(seam/behind)
    let edges = "";
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
    let nodes = "";
    spec.forEach(r => {
      const p = pos[r.key]; let dots = "";
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
      nodes += `<g><circle class="rmcircle" cx="${p.x}" cy="${p.y}" r="${R}"/>${dots}`
            + `<text class="rmlabel" x="${p.x}" y="${p.y - 1}">${esc(r.key)}</text>`
            + `<text class="rmsub" x="${p.x}" y="${p.y + 10}">${esc((r.title || "").slice(0, 18))}</text></g>`;
    });
    const defs = Object.keys(DIR_COL).map(dir => `<marker id="arw-${dir}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="${DIR_COL[dir]}"/></marker>`).join("");
    return { W, H, html: `<defs>${defs}</defs>${edges}${nodes}` };
  }

  // helpers the test asserts against without re-deriving the layout constants
  function ringPort(spec, roomKey, x) {                         // absolute (x,y) of a hotspot/door port on its circle
    const L = layoutRooms(spec), R = 36, DX = 168, DY = 128, MX = 70, MY = 66;
    const maxRows = Math.max(1, ...L.ranks.map(rk => L.cols[rk].length));
    const off = (maxRows - L.cols[L.rank[roomKey]].length) / 2;
    const cx = MX + L.rank[roomKey] * DX, cy = MY + (L.row[roomKey] + off) * DY;
    return [cx + R * Math.sin(2 * Math.PI * (x - 0.5)), cy - R * Math.cos(2 * Math.PI * (x - 0.5))];
  }

  const api = { esc, TYPE_COL, DIR_COL, DIR_DASH, layoutRooms, buildNetSvg, ringPort };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.NetGraph = api;
})(typeof self !== "undefined" ? self : this);
