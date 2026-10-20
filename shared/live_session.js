/*
 * live_session.js — LIVE scenarios (`scenario.live: true`): the room player joined to the in-class
 * live session run by authoring_v2/live_class/live_server.py.
 *
 * The live server serves play.html same-origin, so every call here is a relative `/api/...` on the
 * page's own origin. Off the live server (GitHub Pages, a static preview) those calls fail, and the
 * landing screen says the scenario is played live in class instead of offering a dead Enter button.
 * In harness test play live mode is OFF (pano-player.js never calls mountJoin there).
 *
 * What it owns:
 *   - the JOIN box on the landing screen (code → anonymous callsign; pid kept in localStorage so a
 *     refresh rejoins as the same callsign);
 *   - the HUD strip in the world: callsign, class total / goal, clock, "carrying N gourds";
 *   - polling /api/state every 2 s, and the paused / won / time-up / closed overlays;
 *   - the calls step 5's station and deliver hotspots make: deal(tier), answer(dealId, choice), deliver().
 * Answers never reach the browser: the server deals a task without its answer and checks every click.
 * No student data: callsigns only, never a name or x500.
 */

const POLL_MS = 2000;
const STORE = "liveSession";        // localStorage: { pid, code }

let st = null, stAt = 0, me = null, pollTimer = null, tickTimer = null, onChange = null;
const $ = s => document.querySelector(s);

async function api(path, body) {
  const opts = body === undefined ? { cache: "no-store" }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch("/api/" + path, opts);
  let j = {};
  try { j = await r.json(); } catch (e) { /* non-JSON: not the live server */ }
  return { ok: r.ok, status: r.status, j };
}

function plural(n, unit) {
  const u = Array.isArray(unit) && unit.length === 2 ? unit : ["point", "points"];
  return n + " " + (n === 1 ? u[0] : u[1]);
}
function fmt(s) {
  s = Math.max(0, Math.round(s));
  const m = Math.floor(s / 60), r = s % 60;
  return (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r;
}

function injectStyle() {
  if ($("#liveStyle")) return;
  const css = document.createElement("style");
  css.id = "liveStyle";
  css.textContent = `
  #liveJoin { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:4px 0 10px; }
  #liveJoin input { font:700 22px ui-monospace,Menlo,Consolas,monospace; letter-spacing:6px; width:7.2em;
    text-transform:uppercase; padding:8px 10px; border-radius:8px; border:2px solid rgba(255,216,140,.55);
    background:rgba(0,0,0,.35); color:#ffd88c; }
  #liveMsg { width:100%; min-height:1.3em; font:14px system-ui; color:rgba(255,216,140,.9); }
  #liveHud { position:absolute; top:10px; left:50%; transform:translateX(-50%); z-index:25; display:none;
    gap:14px; align-items:center; background:rgba(0,0,0,.5); border:1px solid rgba(255,216,140,.35);
    border-radius:16px; padding:6px 14px; font:14px system-ui; color:rgba(255,236,200,.95);
    user-select:none; }
  #liveHud b { color:#ffd88c; }
  #liveHud .lhClock { font:700 15px ui-monospace,Menlo,Consolas,monospace; }
  #liveHud .lhClock.low { color:#ff9b8a; }
  #liveHud .lhCarry { color:#9fe7dc; }
  #liveHud .lhCarry:empty { display:none; }
  #liveBar { width:90px; height:8px; border-radius:4px; background:rgba(255,255,255,.18); overflow:hidden; }
  #liveBar i { display:block; height:100%; width:0; background:linear-gradient(90deg,#1aa6a6,#7eeedd); }
  #liveOverlay { position:absolute; inset:0; z-index:60; display:none; align-items:center; justify-content:center;
    background:rgba(4,10,16,.78); text-align:center; }
  #liveOverlay.paused { background:rgba(4,10,16,.55); }
  #liveOverlay .card { max-width:520px; padding:22px 26px; border-radius:14px; background:rgba(0,0,0,.55);
    border:1px solid rgba(255,216,140,.35); color:#ffecc8; font:16px/1.45 system-ui; }
  #liveOverlay h2 { margin:0 0 8px; color:#ffd88c; font:700 26px system-ui; }
  #liveHud > * { white-space:nowrap; }
  @media (max-width:640px) {
    #liveHud { flex-wrap:wrap; justify-content:center; row-gap:3px; column-gap:10px; font-size:12px;
      padding:5px 10px; width:max-content; max-width:calc(100% - 20px); box-sizing:border-box; }
    #liveBar { width:54px; }
  }
  `;
  document.head.appendChild(css);
}

function save(pid, code) { try { localStorage.setItem(STORE, JSON.stringify({ pid, code })); } catch (e) {} }
function load() { try { return JSON.parse(localStorage.getItem(STORE) || "null"); } catch (e) { return null; } }

/*
 * Landing screen: put a join box above the Enter button and hold Enter back until the player has a
 * callsign. `enterBtn` is the player's own Enter button (its click handler is untouched).
 */
export async function mountJoin(enterBtn) {
  injectStyle();
  const box = document.createElement("div");
  box.id = "liveJoin";
  box.innerHTML = `<input id="liveCode" maxlength="4" autocomplete="off" autocapitalize="characters"
      spellcheck="false" placeholder="CODE" aria-label="Join code from the screen">
    <button id="liveGo">Join</button><div id="liveMsg"></div>`;
  enterBtn.parentElement.insertBefore(box, enterBtn);
  enterBtn.style.display = "none";
  const msg = t => { $("#liveMsg").textContent = t || ""; };

  const joined = (pid, code, callsign) => {
    me = { pid, callsign };
    save(pid, code);
    box.style.display = "none";
    const label = enterBtn.textContent;
    enterBtn.textContent = "You are " + callsign + ". " + label;
    enterBtn.style.display = "";
    startPolling();
  };

  const tryJoin = async (code, pid) => {
    let r;
    try { r = await api("join", { code, pid }); } catch (e) { r = { ok: false, status: 0, j: {} }; }
    if (r.ok && r.j.pid) { joined(r.j.pid, code, r.j.callsign); return true; }
    if (!r.j.error) {      // no live server answered: the public site, or the server is down
      msg("This one is played live in class. Open the link from Canvas during the session.");
      return false;
    }
    msg(r.j.error);
    return false;
  };

  $("#liveGo").onclick = () => {
    const code = $("#liveCode").value.trim().toUpperCase();
    if (code.length !== 4) { msg("Type the 4-character code from the screen."); return; }
    tryJoin(code, (load() || {}).pid);
  };
  $("#liveCode").addEventListener("keydown", e => { if (e.key === "Enter") $("#liveGo").click(); });

  const saved = load();       // a refresh mid-session rejoins as the same callsign, no retyping
  if (saved && saved.code && saved.pid) {
    $("#liveCode").value = saved.code;
    const st0 = await api("state").catch(() => null);
    if (st0 && st0.ok && st0.j.phase && st0.j.phase !== "closed") await tryJoin(saved.code, saved.pid);
  }
}

/* In the world: show the HUD strip (call from beginGame). */
export function showHud(screen) {
  injectStyle();
  if (!$("#liveHud")) {
    const hud = document.createElement("div");
    hud.id = "liveHud";
    hud.innerHTML = `<span class="lhMe"></span><span id="liveBar"><i></i></span><span class="lhTotal"></span>
      <span class="lhClock"></span><span class="lhCarry"></span>`;
    screen.appendChild(hud);
    const ov = document.createElement("div");
    ov.id = "liveOverlay";
    ov.innerHTML = `<div class="card"><h2></h2><p></p></div>`;
    screen.appendChild(ov);
  }
  $("#liveHud").style.display = "flex";
  render();
  if (!tickTimer) tickTimer = setInterval(tick, 250);
}

function startPolling() {
  if (pollTimer) return;
  const poll = () => api("state?pid=" + encodeURIComponent(me ? me.pid : "")).then(r => {
    if (!r.ok) return;
    st = r.j; stAt = Date.now();
    if (me && !st.me && st.phase !== "closed") rejoinNeeded();
    render();
    if (onChange) onChange(st);
  }).catch(() => {});
  poll();
  pollTimer = setInterval(poll, POLL_MS);
}

function rejoinNeeded() {
  try { localStorage.removeItem(STORE); } catch (e) {}
  overlay("show", "Rejoin the session", "The class session was restarted. Reload the page and type the new code from the screen.");
}

function overlay(mode, title, body) {
  const ov = $("#liveOverlay");
  if (!ov) return;
  if (mode === "hide") { ov.style.display = "none"; return; }
  ov.className = mode === "paused" ? "paused" : "";
  ov.querySelector("h2").textContent = title;
  ov.querySelector("p").textContent = body || "";
  ov.style.display = "flex";
}

function render() {
  const hud = $("#liveHud");
  if (!hud || !st) return;
  const goal = st.goal || 0, total = st.total || 0;
  const label = st.goal_label || "";
  hud.querySelector(".lhMe").innerHTML = "";
  const b = document.createElement("b"); b.textContent = me ? me.callsign : "";
  hud.querySelector(".lhMe").appendChild(b);
  hud.querySelector("#liveBar i").style.width = (goal ? Math.min(100, 100 * total / goal) : 0) + "%";
  hud.querySelector(".lhTotal").textContent = total + " / " + goal + (label ? " " + label : "");
  const carrying = st.me ? st.me.carrying || 0 : 0;
  hud.querySelector(".lhCarry").textContent = carrying ? "carrying " + plural(carrying, st.unit) : "";
  const ph = st.phase;
  if (ph === "paused") overlay("paused", "Paused", "Eyes on the screen at the front.");
  else if (ph === "won") overlay("show", "You did it", total + " / " + goal + (label ? " " + label : "") + ". Nice work, crew.");
  else if (ph === "timeup") overlay("show", "Time's up", "The class got " + total + " / " + goal + (label ? " " + label : "") + ".");
  else if (ph === "closed") overlay("show", "Session over", "Thanks for playing.");
  else if (!(me && st && !st.me)) overlay("hide");
  tick();
  // The player's own room-title pill (#hud) sits top-centre too: keep it just under this strip,
  // which is one line on a laptop and two on a phone.
  const title = document.getElementById("hud");
  if (title) title.style.top = Math.round(hud.getBoundingClientRect().bottom + 6) + "px";
}

function tick() {
  const el = document.querySelector("#liveHud .lhClock");
  if (!el || !st) return;
  if (st.phase === "lobby") { el.textContent = "waiting to start"; el.classList.remove("low"); return; }
  let rem = st.remaining_s || 0;
  if (st.phase === "running") rem = Math.max(0, rem - (Date.now() - stAt) / 1000);
  el.textContent = fmt(rem);
  el.classList.toggle("low", st.phase === "running" && rem <= 60);
}

/* ---- the calls the station and deliver hotspots make (step 5) ---- */
export const isJoined = () => !!me;
export const state = () => st;
export function onState(fn) { onChange = fn; }
export async function deal(tier) { return api("deal", { pid: me && me.pid, tier }); }
export async function answer(dealId, choice) { return api("answer", { pid: me && me.pid, deal_id: dealId, choice }); }
export async function skip() { return api("skip", { pid: me && me.pid }); }
export async function deliver() {
  const r = await api("deliver", { pid: me && me.pid });
  if (r.ok && st) { st.total = r.j.total; if (st.me) st.me.carrying = 0; render(); }
  return r;
}
export function noteCarrying(n) { if (st && st.me) { st.me.carrying = n; render(); } }
