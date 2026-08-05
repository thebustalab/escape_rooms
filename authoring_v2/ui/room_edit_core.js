// room_edit_core.js — shared authoring core for the 360 room editor.
// Phase 0 of the hub-and-spoke plan (notes/hub_and_spoke_plan.md): one home for the fetch helpers,
// node/draft load, room save, and the live cinemagraph compositor that reproject_test.html (the future
// hub) — and, in a later phase, hotspots_edit.html — share. Plain script (no ES modules) to match how the
// authoring pages load scripts; exposes window.RoomEditCore.
//
// The Cinemagraph compositor below MIRRORS shared/pano-player.js `startCinemagraph` (the game runtime's
// canonical copy). Keep the two in lockstep until a later phase unifies them: pano-player.js ships to
// players, so it is deliberately NOT refactored to import this authoring-only module.
(function (global) {
  "use strict";

  // Query-aware cache-buster: "/api/scenario?chapter=…&scenario=…" must gain "&t=", NOT a second "?", or
  // the server parses scenario as "…?t=123" and 500s (this broke room mode once). Returns null on error so
  // callers can degrade.
  async function getJSON(p) {
    try { return await (await fetch(p + (p.includes("?") ? "&" : "?") + "t=" + Date.now())).json(); }
    catch (e) { return null; }
  }
  const postJSON = async (p, b) =>
    (await fetch(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();

  // "chapter=…&scenario=…" (or "" for the active scenario) — the SCQ every room route carries.
  const scq = (ch, sc) => (ch && sc) ? ("chapter=" + encodeURIComponent(ch) + "&scenario=" + encodeURIComponent(sc)) : "";

  // Load the whole scenario doc (for a room's siblings — e.g. door "to" targets). SCQ or "".
  async function loadDoc(SCQ) {
    return await getJSON("/api/scenario" + (SCQ ? "?" + SCQ : ""));
  }
  // Load one room node from the scenario doc. SCQ = "chapter=…&scenario=…" or "".
  async function loadNode(SCQ, roomKey) {
    const doc = await loadDoc(SCQ);
    return doc && (doc.rooms || []).find(r => r.key === roomKey);
  }
  // Load a room's _scratch draft (per-candidate wrap/hotspots), or null.
  async function loadDraft(roomKey, SCQ) {
    return await getJSON("/api/draft?roomKey=" + encodeURIComponent(roomKey) + (SCQ ? "&" + SCQ : ""));
  }
  // A room is "committed" once it has a built panorama (mirrors hotspots_edit.html isCommitted()).
  const isCommitted = node => !!(node && (node.panorama || node.built));

  // Project a hotspot box (0–1 fractions) to {yaw,pitch} on the sphere, given wrap coverage
  // c={haov,vaov,vOffset}. Byte-identical to shared/pano-player.js boxToYP — how the game places markers.
  const boxToYP = (box, c) => {
    const cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
    return { yaw: cx * c.haov - c.haov / 2, pitch: c.vaov / 2 - cy * c.vaov + (c.vOffset || 0) };
  };

  // Save committed-room fields → scenario.json (e.g. {wrap} or {hotspots}).
  const saveRoomFields = (chapter, scenario, roomKey, fields) =>
    postJSON("/api/room-patch", { chapter, scenario, roomKey, fields });
  // Save a candidate's draft; patch is the per-image payload (e.g. {wrap} or {hotspots}).
  const saveDraft = (chapter, scenario, roomKey, image, patch) =>
    postJSON("/api/draft-save", Object.assign({ chapter, scenario, roomKey, image }, patch));

  // --- Live cinemagraph compositor (mirrors shared/pano-player.js startCinemagraph) -------------------
  // A room's hotspot may carry cinemagraph:{box,video}. init() preloads the still + one looping <video> per
  // clip onto an offscreen canvas; start() runs the per-frame rAF that stamps each video's box (feathered)
  // over the still and pokes Pannellum (dynamic:true) to re-upload. Inert until init() finds a cinemagraph
  // (active() stays false), so a plain room renders its still unchanged.
  const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("img " + src)); im.src = src; });

  const Cinemagraph = {
    _cines: [], _base: null, _cv: null, _vids: [], _raf: 0,
    active() { return this._cines.length > 0; },
    canvas() { return this._cv; },
    // node: the room node; imgUrl: the committed still URL; SCQ: chapter/scenario query (or "").
    async init(node, imgUrl, SCQ) {
      this.stop(); this._cines = []; this._vids = [];
      const list = ((node && node.hotspots) || [])
        .filter(h => h && h.cinemagraph && h.cinemagraph.video && Array.isArray(h.cinemagraph.box))
        .map(h => h.cinemagraph);
      if (!list.length) return;
      try {
        this._base = await loadImg(imgUrl);
        this._cv = document.createElement("canvas");
        this._cv.width = this._base.naturalWidth || this._base.width;
        this._cv.height = this._base.naturalHeight || this._base.height;
        this._cv.getContext("2d").drawImage(this._base, 0, 0);   // seed the first texture with the still
        this._vids = list.map(c => {
          const v = document.createElement("video");
          // video path is room-relative like `panorama` → served through /sfile the same way as the still
          v.src = "/sfile/" + c.video + "?t=" + Date.now() + (SCQ ? "&" + SCQ : "");
          v.muted = true; v.loop = true; v.playsInline = true; v.autoplay = true;
          v.play().catch(() => {});
          return { v, box: c.box };
        });
        this._cines = list;
      } catch (e) { console.error("cinemagraph init failed", e); this._cines = []; }
    },
    // getViewer: () => the current Pannellum viewer (poked each frame via setUpdate to re-upload the canvas).
    start(getViewer) {
      this.stop();
      const cv = this._cv, ctx = cv.getContext("2d"), W = cv.width, H = cv.height, base = this._base, vids = this._vids, self = this;
      const draw = () => {
        ctx.drawImage(base, 0, 0, W, H);                  // repaint the crisp still every frame
        vids.forEach(({ v, box }) => {
          if (v.readyState < 2) return;
          // WRAP box (x0 > x1): [x0..1] ∪ [0..x1]. Clip made from a rolled contiguous crop → feather whole,
          // draw in two slices (left→right edge, right→left edge). Kept in lockstep with pano-player.js.
          const [x0, y0, x1, y1] = box;
          const wrap = x0 > x1;
          const wfrac = wrap ? (1 - x0) + x1 : (x1 - x0), bh = (y1 - y0) * H, bw = wfrac * W;
          if (bw < 1 || bh < 1) return;
          const fc = document.createElement("canvas"); fc.width = Math.round(bw); fc.height = Math.round(bh);
          const fx = fc.getContext("2d");
          fx.drawImage(v, 0, 0, v.videoWidth, v.videoHeight, 0, 0, fc.width, fc.height);
          fx.globalCompositeOperation = "destination-in";  // feather edges → blends into the still, no seam
          const g = fx.createRadialGradient(fc.width/2, fc.height/2, Math.min(fc.width, fc.height)*0.12,
                                            fc.width/2, fc.height/2, Math.max(fc.width, fc.height)*0.62);
          g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(0.7, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)");
          fx.fillStyle = g; fx.fillRect(0, 0, fc.width, fc.height);
          if (!wrap) {
            ctx.drawImage(fc, x0 * W, y0 * H);
          } else {
            const leftW = Math.round((1 - x0) * W);
            ctx.drawImage(fc, 0, 0, leftW, fc.height, x0 * W, y0 * H, leftW, fc.height);
            ctx.drawImage(fc, leftW, 0, fc.width - leftW, fc.height, 0, y0 * H, fc.width - leftW, fc.height);
          }
        });
        const vw = getViewer && getViewer();
        try { vw && vw.setUpdate && vw.setUpdate(true); } catch (e) {}
        self._raf = requestAnimationFrame(draw);
      };
      self._raf = requestAnimationFrame(draw);
    },
    stop() { if (this._raf) cancelAnimationFrame(this._raf); this._raf = 0; },
  };

  global.RoomEditCore = { getJSON, postJSON, scq, loadDoc, loadNode, loadDraft, isCommitted, boxToYP, saveRoomFields, saveDraft, Cinemagraph };
})(window);
