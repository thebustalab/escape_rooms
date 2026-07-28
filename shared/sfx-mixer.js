// Sound-mixer overlay for the test player (shared/test_play.html). Loads ONLY when window.SFX_MIXER is
// set, so it never touches normal play. It talks to window.PanoMixer (defined in pano-player.js) and
// shows, top-left: a room jumper, a Music slider, and one live volume slider per ACTIVE sfx layer — so
// you can balance every sound while hearing them together. Values are live; read them off and set them
// in the harness. Re-renders whenever the room's sfx set changes (PanoMixer.onChange).
if (window.SFX_MIXER && window.PanoMixer) (function () {
  const M = window.PanoMixer;
  const panel = document.createElement("div");
  panel.id = "sfxMixer";
  panel.innerHTML = `<style>
    #sfxMixer{position:fixed;left:12px;bottom:44px;top:auto;z-index:99999;width:270px;max-height:78vh;overflow:auto;
      background:rgba(6,17,26,.93);border:1px solid rgba(255,255,255,.16);border-radius:12px;
      padding:14px 13px 12px;font:13px/1.4 system-ui,sans-serif;color:#e8eef2;box-shadow:0 8px 30px rgba(0,0,0,.5)}
    #sfxMixer.collapsed{max-height:none;overflow:visible;width:auto;min-width:160px}
    #sfxMixer.collapsed > *:not(h3):not(.tag){display:none}
    #sfxMixer .mxcaret{float:right;opacity:.7;font-size:11px;font-weight:400;margin-left:12px}
    #sfxMixer h3{margin:0 0 8px;font-size:13px;color:#ffd88c;letter-spacing:.02em}
    #sfxMixer .mrow{margin:9px 0}
    #sfxMixer label{display:block;font-size:11px;opacity:.85;margin-bottom:3px;text-transform:none}
    #sfxMixer .val{float:right;opacity:.7;font-variant-numeric:tabular-nums}
    #sfxMixer .mode{font-size:10px;opacity:.55;text-transform:uppercase;letter-spacing:.05em;margin-left:5px}
    #sfxMixer input[type=range]{width:100%;accent-color:#ffd88c}
    #sfxMixer select{width:100%;background:#0a1620;color:inherit;border:1px solid rgba(255,255,255,.16);border-radius:6px;padding:5px}
    #sfxMixer select:disabled{opacity:.5}
    #sfxMixer .none{opacity:.55;font-size:12px;margin:8px 0}
    #sfxMixer .shead{margin:12px 0 4px;font-size:11px;color:#ffd88c;opacity:.9;border-top:1px solid rgba(255,255,255,.1);padding-top:9px;letter-spacing:.03em}
    #sfxMixer .fire{display:block;width:100%;text-align:left;margin:5px 0;background:#12232f;color:#e8eef2;
      border:1px solid rgba(255,255,255,.16);border-radius:7px;padding:7px 9px;font:12px/1.2 system-ui,sans-serif;cursor:pointer}
    #sfxMixer .fire:hover{background:#1a3040;border-color:#ffd88c}
    #sfxMixer .fire:active{background:#ffd88c;color:#10202a}
    #sfxMixer .save{display:block;width:100%;text-align:center;margin:12px 0 2px;background:#1c4a2e;color:#dff5e6;
      border:1px solid rgba(120,230,160,.4);border-radius:8px;padding:9px;font:600 12px/1.2 system-ui,sans-serif;cursor:pointer}
    #sfxMixer .save:hover{background:#245c39;border-color:#8fe6a8}
    #sfxMixer .save:disabled{opacity:.5;cursor:default}
    #sfxMixer .savemsg{font-size:11px;min-height:14px;margin-top:2px;text-align:center}
    #sfxMixer .savemsg.ok{color:#8fe6a8}#sfxMixer .savemsg.err{color:#ff9a9a}
    #sfxMixer .tag{position:absolute;top:-9px;left:12px;background:#ffd88c;color:#10202a;font-size:10px;
      font-weight:700;padding:1px 7px;border-radius:8px;letter-spacing:.03em}
    #sfxMixer .hint{font-size:11px;opacity:.55;margin-top:11px;border-top:1px solid rgba(255,255,255,.1);padding-top:8px}
  </style>
  <span class="tag">TEST · SOUND MIXER</span>
  <h3>Sound mixer</h3>
  <div class="mrow"><label>Room</label><select id="mxRoom" disabled></select></div>
  <div id="mxMusic"></div>
  <div id="mxLayers"></div>
  <div id="mxSolve"></div>
  <button class="save" id="mxSave" disabled>Save volumes → harness</button>
  <div class="savemsg" id="mxSaveMsg"></div>
  <div class="hint">Type any code and hit <b>Begin</b> to start audio, then jump between rooms. Balance the sliders, then <b>Save volumes</b> to write them straight into the harness (scenario.json). <b>Solve / door sounds</b> fire on click — no need to solve the puzzle.</div>`;
  document.body.appendChild(panel);

  // collapsible (open by default) — the mixer docks bottom-left, just above the music chip; click the
  // heading to fold it away so it never covers the scene. State persists per browser.
  const head = panel.querySelector("h3");
  head.style.cursor = "pointer"; head.style.userSelect = "none";
  const caret = document.createElement("span"); caret.className = "mxcaret";
  head.appendChild(caret);
  const setCollapsed = c => {
    panel.classList.toggle("collapsed", c); caret.textContent = c ? "▸ show" : "▾ hide";
    try { localStorage.setItem("sfxMixerCollapsed", c ? "1" : "0"); } catch (e) {}
  };
  head.onclick = () => setCollapsed(!panel.classList.contains("collapsed"));
  let _c0 = false; try { _c0 = localStorage.getItem("sfxMixerCollapsed") === "1"; } catch (e) {}
  setCollapsed(_c0);

  const roomSel = panel.querySelector("#mxRoom");
  const musicHost = panel.querySelector("#mxMusic");
  const layerHost = panel.querySelector("#mxLayers");
  const solveHost = panel.querySelector("#mxSolve");
  const saveBtn = panel.querySelector("#mxSave");
  const saveMsg = panel.querySelector("#mxSaveMsg");
  roomSel.onchange = () => M.gotoRoom(roomSel.value);

  // Scenario + harness origin passed on the test_play.html URL. `harness` lets us POST the volumes
  // back to the harness server (:8751) from the playtest server (:8055) without hard-coding a host.
  const Q = new URLSearchParams(location.search);
  const CHAPTER = Q.get("chapter") || "", SCENARIO = Q.get("scenario") || "";
  const HARNESS = Q.get("harness") || "";

  // Volumes the user has actually moved — {music: v|null, rooms: {roomKey: {src: v}}}. We send ONLY
  // these (not every layer) so a room the player never touched is never rewritten from a stale value.
  const touched = { music: null, rooms: {} };
  const markMusic = v => { touched.music = v; refreshSave(); };
  const markLayer = (src, v) => {
    const key = M.current(); if (!key || !src) return;
    (touched.rooms[key] = touched.rooms[key] || {})[src] = v; refreshSave();
  };
  const nTouched = () => (touched.music != null ? 1 : 0) +
    Object.values(touched.rooms).reduce((a, o) => a + Object.keys(o).length, 0);
  function refreshSave() {
    const n = nTouched();
    saveBtn.disabled = !(HARNESS && n);
    saveBtn.textContent = n ? `Save ${n} volume${n === 1 ? "" : "s"} → harness` : "Save volumes → harness";
  }

  saveBtn.onclick = async () => {
    if (saveBtn.disabled) return;
    saveBtn.disabled = true; saveMsg.className = "savemsg"; saveMsg.textContent = "saving…";
    try {
      const r = await fetch(HARNESS.replace(/\/$/, "") + "/api/save-mix", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chapter: CHAPTER, scenario: SCENARIO,
          musicVolume: touched.music, rooms: touched.rooms })
      });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error || "save failed");
      saveMsg.className = "savemsg ok";
      saveMsg.textContent = `saved ✓ ${j.layers} layer${j.layers === 1 ? "" : "s"}${j.music ? " + music" : ""}`;
    } catch (e) {
      saveMsg.className = "savemsg err";
      saveMsg.textContent = HARNESS ? ("couldn’t save — " + e.message) : "no harness link (open via ▶ Test play)";
    } finally { refreshSave(); }
  };

  // one labelled 0–100% slider; `oninput(v)` gets the 0–1 value live
  function slider(labelText, mode, value, oninput) {
    const wrap = document.createElement("div"); wrap.className = "mrow";
    wrap.innerHTML =
      `<label>${labelText}<span class="mode">${mode}</span><span class="val">${Math.round(value * 100)}%</span></label>
       <input type="range" min="0" max="1" step="0.01" value="${value}">`;
    const val = wrap.querySelector(".val"), inp = wrap.querySelector("input");
    inp.oninput = () => { const v = parseFloat(inp.value); val.textContent = Math.round(v * 100) + "%"; oninput(v); };
    return wrap;
  }

  function renderRooms() {
    const rooms = M.rooms(), cur = M.current();
    roomSel.disabled = !cur;                 // only navigable once you've entered
    roomSel.innerHTML = "";
    rooms.forEach(r => {
      const o = document.createElement("option");
      o.value = r.key; o.textContent = r.title; if (r.key === cur) o.selected = true;
      roomSel.appendChild(o);
    });
  }

  function render() {
    renderRooms();
    musicHost.innerHTML = "";
    if (M.hasMusic()) musicHost.appendChild(slider("Music", "loop", M.musicVolume(),
      v => { M.setMusicVolume(v); markMusic(v); }));
    layerHost.innerHTML = "";
    const layers = M.layers();
    if (!layers.length) {
      const d = document.createElement("div"); d.className = "none";
      d.textContent = M.current() ? "No sound effects in this room." : "Enter to hear this scenario's sound.";
      layerHost.appendChild(d);
    } else {
      layers.forEach(l => {
        const row = slider(l.label, l.mode, l.vol, v => { M.setLayerVolume(l.i, v); markLayer(l.src, v); });
        if (l.mode === "interval") {          // interval one-shots: a test button (like the solve/door sounds)
          const b = document.createElement("button"); b.className = "fire"; b.title = l.src;
          b.textContent = "▶ test " + l.label;
          b.onclick = () => { const cl = M.layers().find(x => x.i === l.i) || l; M.fireSolve(cl.src, cl.vol); };
          row.appendChild(b);
        }
        layerHost.appendChild(row);
      });
    }
    refreshSave();

    // Solve / door-open stings for this room — one click fires each, no puzzle-solving needed.
    solveHost.innerHTML = "";
    const solves = M.solveSounds ? M.solveSounds() : [];
    if (solves.length) {
      const head = document.createElement("div"); head.className = "shead";
      head.textContent = "Solve / door sounds"; solveHost.appendChild(head);
      solves.forEach(s => {
        const b = document.createElement("button"); b.className = "fire";
        b.textContent = "▶ " + s.label; b.title = s.src;
        b.onclick = () => M.fireSolve(s.src, s.volume);
        solveHost.appendChild(b);
      });
    }
  }

  M.onChange(render);
  render();

  // Prefill the landing code so it's one click to start, and poll briefly so the room list populates
  // as soon as scenario.json loads (before the first room even starts).
  const x = document.querySelector("#x500"); if (x && !x.value) x.value = "TEST";
  let tries = 0;
  const warm = setInterval(() => { renderRooms(); if (M.rooms().length || ++tries > 60) clearInterval(warm); }, 250);
})();
