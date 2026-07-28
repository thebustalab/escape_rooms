/*
 * map-view.js — the explorable "mist map" for hub-and-spoke scenarios.
 *
 * Lays the scenario's nodes out in space (boss at the centre, spokes in a ring
 * around it — or per-node `pos:{x,y}` percentage overrides), paints a canvas
 * fog-of-war over the top, and draws faint ribbons from each resolved spoke in
 * toward the boss. As leads resolve, their fog clears; when the gate opens, the
 * fog over the centre dissolves and the boss emerges.
 *
 * The engine owns all state and the detail panel. MapView is purely visual +
 * click routing: it calls opts.onOpen(node) when a reachable node is clicked,
 * and re-reads state through opts.status()/opts.gate() whenever update() runs.
 *
 * opts = {
 *   mapEl,                       // container div (MapView fills it with layers)
 *   nodes,                       // window.SCENARIO.nodes
 *   status: (node) => "open" | "resolved" | "locked" | "ready",
 *   gate:   () => ({ resolved, requires, total, met }),
 *   onOpen: (node) => void,      // fired on click of an open spoke / ready boss
 * }
 */

const FOG_MAP = "rgba(10, 20, 28, 0.90)";   // abstract map: heavy mist
const FOG_SCENE = "rgba(6, 14, 20, 0.50)";  // over painted art: a light haze

function stateGlyph(status) {
  return { open: "lead", resolved: "✓", locked: "locked", ready: "▶ final" }[status] || "";
}

export class MapView {
  constructor(opts) {
    this.opts = opts;
    this.nodes = opts.nodes;
    this.spokes = this.nodes.filter((n) => n.type === "spoke");
    this.boss = this.nodes.find((n) => n.type === "boss") || null;
    this.scene = !!opts.scene;
    this.background = opts.background || null;
    this.fogColor = this.scene ? FOG_SCENE : FOG_MAP;
    this.markerEls = {};
    this.ribbonEls = {};
    this.clarity = {};   // current, animated
    this.target = {};    // where clarity is heading
    this._raf = 0;
  }

  /* ----- layout: percentage coordinates on the map ----- */
  pos(node) {
    if (node.pos && typeof node.pos.x === "number") return node.pos;
    if (node.type === "boss") return { x: 50, y: 50 };
    const i = this.spokes.indexOf(node);
    const m = this.spokes.length || 1;
    const ang = (-90 + (i * 360) / m) * (Math.PI / 180); // start at top, clockwise
    const radius = 34;
    return { x: 50 + radius * Math.cos(ang), y: 50 + radius * Math.sin(ang) };
  }
  posPx(node) {
    const p = this.pos(node);
    return { x: (p.x / 100) * this.w, y: (p.y / 100) * this.h };
  }

  /* ----- build ----- */
  render() {
    this.mapEl.innerHTML = "";
    this.mapEl.classList.add("map-ready");
    this.mapEl.insertAdjacentHTML("beforeend",
      '<div class="map-bg"></div>' +
      '<svg class="map-ribbons" viewBox="0 0 100 100" preserveAspectRatio="none"></svg>' +
      '<div class="map-nodes"></div>' +
      '<canvas class="map-fog"></canvas>' +
      '<div class="map-progress"></div>');

    this.ribbonSvg = this.mapEl.querySelector(".map-ribbons");
    this.nodesEl = this.mapEl.querySelector(".map-nodes");
    this.canvas = this.mapEl.querySelector(".map-fog");
    this.progressEl = this.mapEl.querySelector(".map-progress");
    this.ctx = this.canvas.getContext("2d");

    if (this.background) {
      this.mapEl.classList.add("scene");
      this.mapEl.querySelector(".map-bg").style.backgroundImage =
        "url('" + this.background + "')";
    }

    this.buildRibbons();
    this.buildNodes();
    this.nodes.forEach((n) => { this.clarity[n.key] = 0; this.target[n.key] = 0; });

    this.resize();
    this._ro = new ResizeObserver(() => this.resize());
    this._ro.observe(this.mapEl);

    this.update(); // set targets from status, then animate the mist parting
  }

  get mapEl() { return this.opts.mapEl; }

  buildNodes() {
    this.nodes.forEach((node) => {
      const p = this.pos(node);
      const btn = document.createElement("button");
      btn.className = "map-node " + node.type;
      btn.style.left = p.x + "%";
      btn.style.top = p.y + "%";
      btn.innerHTML =
        '<span class="marker-dot"></span>' +
        '<span class="marker-label">' + node.title + "</span>" +
        '<span class="marker-state"></span>';
      btn.addEventListener("click", () => {
        const st = this.opts.status(node);
        if (st === "open" || st === "ready") this.opts.onOpen(node);
      });
      this.markerEls[node.key] = btn;
      this.nodesEl.appendChild(btn);
    });
  }

  buildRibbons() {
    if (!this.boss) return;
    const b = this.pos(this.boss);
    this.spokes.forEach((node) => {
      const s = this.pos(node);
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M " + s.x + " " + s.y + " L " + b.x + " " + b.y);
      path.setAttribute("class", "ribbon");
      path.setAttribute("pathLength", "100");
      this.ribbonEls[node.key] = path;
      this.ribbonSvg.appendChild(path);
    });
  }

  /* ----- state sync ----- */
  update() {
    const gate = this.opts.gate();
    const done = this.boss && this.opts.status(this.boss) === "resolved";
    this.progressEl.innerHTML = done
      ? "The path is clear — the dossier is closed."
      : "Resolved <strong>" + gate.resolved + "</strong> of " + gate.total +
        " leads — reach <strong>" + gate.requires + "</strong> to part the mist.";

    this.nodes.forEach((node) => {
      const st = this.opts.status(node);
      const el = this.markerEls[node.key];
      el.className = "map-node " + node.type + " " + st;
      el.querySelector(".marker-state").textContent = stateGlyph(st);
      this.target[node.key] = this.clarityFor(node, st);
    });

    this.spokes.forEach((node) => {
      if (this.opts.status(node) === "resolved") {
        this.ribbonEls[node.key] && this.ribbonEls[node.key].classList.add("drawn");
      }
    });
    if (this.boss) {
      const bs = this.opts.status(this.boss);
      this.ribbonSvg.classList.toggle("boss-open", bs === "ready" || bs === "resolved");
    }

    this.animate();
  }

  // How clear a node's surroundings should be, by status (0 = fog, 1 = clear).
  clarityFor(node, status) {
    if (node.type === "boss") return status === "locked" ? 0 : 1;
    if (status === "resolved") return 1;
    return this.scene ? 0.62 : 0.42; // scene art stays lightly visible; abstract map glimmers
  }

  /* ----- fog animation ----- */
  animate() {
    cancelAnimationFrame(this._raf);
    const step = () => {
      let moving = false;
      for (const n of this.nodes) {
        const t = this.target[n.key];
        let c = this.clarity[n.key];
        if (Math.abs(t - c) > 0.004) { c += (t - c) * 0.12; moving = true; }
        else c = t;
        this.clarity[n.key] = c;
      }
      this.drawFog();
      if (moving) this._raf = requestAnimationFrame(step);
    };
    this._raf = requestAnimationFrame(step);
  }

  drawFog() {
    if (!this.ctx || !this.w) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.w, this.h);
    ctx.globalCompositeOperation = "source-over";
    ctx.fillStyle = this.fogColor;
    ctx.fillRect(0, 0, this.w, this.h);

    ctx.globalCompositeOperation = "destination-out";
    for (const node of this.nodes) {
      const c = this.clarity[node.key];
      if (c <= 0.004) continue;
      const p = this.posPx(node);
      const baseR = (node.type === "boss" ? 1.7 : 1) * this.R;
      const r = Math.max(1, baseR * c);
      const g = ctx.createRadialGradient(p.x, p.y, r * 0.15, p.x, p.y, r);
      g.addColorStop(0, "rgba(0,0,0," + (0.96 * Math.min(1, c)) + ")");
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
  }

  resize() {
    const rect = this.mapEl.getBoundingClientRect();
    if (!rect.width) return;
    this.w = rect.width;
    this.h = rect.height;
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.round(this.w * dpr);
    this.canvas.height = Math.round(this.h * dpr);
    this.canvas.style.width = this.w + "px";
    this.canvas.style.height = this.h + "px";
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.R = Math.min(this.w, this.h) * 0.17;
    this.drawFog();
  }

  destroy() {
    cancelAnimationFrame(this._raf);
    this._ro && this._ro.disconnect();
  }
}
