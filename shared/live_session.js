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
 *   - the calls step 5's station and deliver hotspots make: deal(tier, track?), answer(dealId, choice), deliver(sink?);
 *   - the whole-class experiment card (harbour, comparing means): when Lucas opens a round, the student
 *     casts two nets on their own device (fish_stats.js, the fish board's Welch t), sees the catches and
 *     the p, and sends ONLY that p. Shown over the landing screen too, so it works before Enter.
 * Answers never reach the browser: the server deals a task without its answer and checks every click.
 * No student data: callsigns only, never a name or x500.
 */

import "./fish_stats.js?v=143";     // window.FishStats: the fish board's tests (Welch t), pinned to R

const POLL_MS = 2000;
const STORE = "liveSession";        // localStorage: { pid, code }

let st = null, stAt = 0, me = null, pollTimer = null, tickTimer = null, onChange = null, dismissedPhase = null;
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
  body.liveHudOn #modal { padding-top:58px; }
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
  #liveOverlay .card { position:relative; }
  #liveOverlay .lvX { position:absolute; top:6px; right:8px; display:none; width:34px; height:34px;
    border:0; border-radius:17px; background:transparent; color:#ffd88c; font:700 22px system-ui; cursor:pointer; }
  #liveOverlay .lvX:hover { background:rgba(255,216,140,.15); }
  #liveHud > * { white-space:nowrap; }
  #liveCast { position:fixed; inset:0; z-index:70; display:none; align-items:center; justify-content:center;
    background:rgba(4,10,16,.72); font:16px/1.45 system-ui; color:#ffecc8; }
  #liveCast .card { position:relative; width:min(560px, calc(100% - 24px)); box-sizing:border-box; padding:18px 20px;
    border-radius:14px; background:rgba(8,20,30,.92); border:1px solid rgba(255,216,140,.35); text-align:center; }
  #liveCast h2 { margin:0 0 6px; color:#ffd88c; font:700 24px system-ui; }
  #liveCast p { margin:6px 0; }
  #liveCast button.go { font:700 20px system-ui; padding:10px 26px; border-radius:10px; border:0; margin:10px 0 4px;
    background:#ffd88c; color:#10202c; cursor:pointer; }
  #liveCast button.go:disabled { opacity:.5; cursor:default; }
  #liveCast .lcX { position:absolute; top:6px; right:8px; width:34px; height:34px; border:0; border-radius:17px;
    background:transparent; color:#ffd88c; font:700 22px system-ui; cursor:pointer; display:none; }
  #liveCast svg { width:100%; height:auto; display:block; margin:8px 0; }
  #liveCast .lcP { font:800 40px ui-monospace,Menlo,Consolas,monospace; color:#ffecc8; }
  #liveCast .lcP.red { color:#ff8a7a; }
  #liveCast .lcNote { font-size:14px; color:rgba(255,236,200,.8); }
  @media (max-width:640px) {
    #liveHud { flex-wrap:wrap; justify-content:center; row-gap:3px; column-gap:10px; font-size:12px;
      padding:5px 10px; width:max-content; max-width:calc(100% - 20px); box-sizing:border-box; }
    #liveBar { width:54px; }
    body.liveHudOn #modal { padding-top:74px; }
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
    ov.innerHTML = `<div class="card"><button class="lvX" aria-label="Close">&times;</button><h2></h2><p></p></div>`;
    // The end cards (won, time's up) can be closed to look at the room (bathhouse: the clean tub); the
    // card stays shut until the phase changes. Paused and rejoin cards have no X.
    ov.querySelector(".lvX").onclick = () => { dismissedPhase = st && st.phase; overlay("hide"); };
    screen.appendChild(ov);
  }
  $("#liveHud").style.display = "flex";
  // The HUD floats over the top of the screen (z 25, above the modal's 20): push a modal's box below it so
  // the HUD never covers the card's close X or its top row (the sewing table's cloth, 2026-10-26).
  document.body.classList.add("liveHudOn");
  render();
  if (!tickTimer) tickTimer = setInterval(tick, 250);
}

function startPolling() {
  if (pollTimer) return;
  const poll = () => api("state?pid=" + encodeURIComponent(me ? me.pid : "")).then(r => {
    if (!r.ok) return;
    st = r.j; stAt = Date.now();
    if (me && !st.me && st.phase !== "closed") rejoinNeeded();
    renderCast();
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

function overlay(mode, title, body, closable) {
  const ov = $("#liveOverlay");
  if (!ov) return;
  if (mode === "hide") { ov.style.display = "none"; return; }
  ov.querySelector(".lvX").style.display = closable ? "block" : "none";
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
  // What you carry: the pool's own unit, then any second item (bathhouse: herb bundles, then bath tokens).
  const carrying = st.me ? st.me.carrying || 0 : 0, heldItems = (st.me && st.me.held) || {}, bits = [];
  if (carrying) bits.push(plural(carrying, st.unit));
  for (const [k, n] of Object.entries(heldItems))
    if (n) bits.push(plural(n, ((st.items || {})[k] || {}).unit));
  hud.querySelector(".lhCarry").textContent = bits.length ? "carrying " + bits.join(" and ") : "";
  const ph = st.phase;
  if (dismissedPhase && dismissedPhase !== ph) dismissedPhase = null;    // a new phase brings its card back
  if (dismissedPhase === ph) overlay("hide");
  else if (ph === "paused") overlay("paused", "Paused", "Eyes on the screen at the front.");
  else if (ph === "won") overlay("show", "You did it", total + " / " + goal + (label ? " " + label : "") + ". Nice work, crew.", true);
  else if (ph === "timeup") overlay("show", "Time's up", "The class got " + total + " / " + goal + (label ? " " + label : "") + ".", true);
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
// `track` (optional): the station's track ("ord"); absent or "" deals from the pool's default track.
export async function deal(tier, track) {
  return api("deal", track ? { pid: me && me.pid, tier, track } : { pid: me && me.pid, tier });
}
export async function answer(dealId, choice) { return api("answer", { pid: me && me.pid, deal_id: dealId, choice }); }
export async function skip() { return api("skip", { pid: me && me.pid }); }
// `sink` (optional): a sink id (bathhouse: "bath_1") spends that sink's cost of a second item to fill it.
export async function deliver(sink) {
  const r = await api("deliver", sink ? { pid: me && me.pid, sink } : { pid: me && me.pid });
  if (r.ok && st) {
    st.total = r.j.total;
    if (sink) { st.filled = r.j.filled_all || st.filled; if (st.me) (st.me.held = st.me.held || {})[r.j.item] = r.j.carrying; }
    else if (st.me) st.me.carrying = 0;
    render();
  }
  return r;
}
export function noteCarrying(n, item) {
  if (!(st && st.me)) return;
  if (item) (st.me.held = st.me.held || {})[item] = n; else st.me.carrying = n;
  render();
}

/* ---- the whole-class experiment: cast two nets, send the p ---- */
// The waters match the fish board's normal waters (open harbor N(30, 5), harbor mouth N(35, 5)), so what a
// student casts here is what Lucas showed on the projector. A cast is a fresh random draw every time.
const CAST_WATERS = {
  same: { a: ["Open harbor", 30], b: ["Open harbor", 30],
          intro: "Both nets go into the same water, the open harbor. The fish there are all one population." },
  two:  { a: ["Open harbor", 30], b: ["Harbor mouth", 35],
          intro: "One net goes into the open harbor, the other into the harbor mouth." },
};
const CAST_SD = 5, ALPHA = 0.05;
let castDone = null, castHidden = null;      // castDone: {round, a, b, p}; castHidden: round the student closed

function castCard() {
  injectStyle();
  let el = $("#liveCast");
  if (el) return el;
  el = document.createElement("div");
  el.id = "liveCast";
  el.innerHTML = `<div class="card"><button class="lcX" aria-label="Close">&times;</button>
    <h2>Cast your two nets</h2><div class="lcBody"></div></div>`;
  el.querySelector(".lcX").onclick = () => { castHidden = st && st.exp && st.exp.round; el.style.display = "none"; };
  document.body.appendChild(el);
  return el;
}

function castSvg(a, b, names) {
  const all = a.concat(b), lo = Math.floor(Math.min(...all, 15) / 5) * 5, hi = Math.ceil(Math.max(...all, 50) / 5) * 5;
  const W = 520, x = v => 20 + (W - 40) * (v - lo) / (hi - lo);
  const S = window.FishStats, rows = [[a, "#7fd3ff", names[0], 34], [b, "#ffb36b", names[1], 88]];
  let g = "";
  for (const [fish, col, name, y] of rows) {
    g += `<text x="20" y="${y - 16}" fill="${col}" font-size="13">${name}</text>`;
    for (const v of fish) g += `<circle cx="${x(v).toFixed(1)}" cy="${y}" r="6" fill="${col}" fill-opacity=".85"/>`;
    const m = x(S.mean(fish));
    g += `<line x1="${m}" x2="${m}" y1="${y - 11}" y2="${y + 11}" stroke="#fff" stroke-width="2.5"/>`;
  }
  let ax = `<line x1="20" x2="${W - 20}" y1="116" y2="116" stroke="#9aa6ae"/>`;
  for (let v = lo; v <= hi; v += 5) ax += `<line x1="${x(v)}" x2="${x(v)}" y1="116" y2="121" stroke="#9aa6ae"/>` +
    `<text x="${x(v)}" y="135" fill="#9aa6ae" font-size="11" text-anchor="middle">${v}</text>`;
  ax += `<text x="${W / 2}" y="150" fill="#9aa6ae" font-size="11" text-anchor="middle">length (cm); white tick = net's mean</text>`;
  return `<svg viewBox="0 0 ${W} 156" role="img" aria-label="Your two catches">${g}${ax}</svg>`;
}

function castResultHtml(c) {
  const W = CAST_WATERS[c.water] || CAST_WATERS.same, red = c.p < ALPHA;
  const pTxt = c.p < 0.001 ? "p < 0.001" : "p = " + c.p.toFixed(3);
  return castSvg(c.a, c.b, ["Net A: " + W.a[0].toLowerCase(), "Net B: " + W.b[0].toLowerCase()]) +
    `<div class="lcP${red ? " red" : ""}">${pTxt}</div>` +
    `<p>${red ? "In the red: under 0.05, so this cast says the two nets differ." : "Not in the red: 0.05 or more, so this cast can't tell the two nets apart."}</p>` +
    `<p class="lcNote">p is the probability of getting data this extreme if the fish in the two waters really have the same distribution.` +
    ` Watch the screen to see every cast in the class.</p>`;
}

function renderCast() {
  const e = st && st.exp;
  const el = $("#liveCast");
  if (!e || !e.open || !me || !st.me || castHidden === e.round || st.phase === "closed") {
    if (el) el.style.display = "none";
    return;
  }
  const card = castCard(), body = card.querySelector(".lcBody"), X = card.querySelector(".lcX");
  const key = e.round + ":" + (castDone && castDone.round === e.round ? "done" : st.me.cast ? "sent" : "ready");
  card.style.display = "flex";
  if (body.dataset.key === key) return;            // nothing changed: leave the card alone between polls
  body.dataset.key = key;
  const W = CAST_WATERS[e.water] || CAST_WATERS.same;
  if (castDone && castDone.round === e.round) {
    body.innerHTML = castResultHtml(castDone);
    X.style.display = "block";
  } else if (st.me.cast) {                         // cast already (a refresh lost the picture)
    body.innerHTML = `<p>You've cast this round. Watch the screen to see every cast in the class.</p>`;
    X.style.display = "block";
  } else {
    body.innerHTML = `<p>${W.intro}</p><p>Each net brings up ${e.n} fish. Your device measures them and runs` +
      ` Welch's t-test.</p><button class="go">Cast</button><p class="lcNote lcErr"></p>`;
    X.style.display = "none";
    body.querySelector(".go").onclick = ev => doCast(e, ev.target);
  }
}

async function doCast(e, btn) {
  btn.disabled = true;
  const S = window.FishStats, R = S.rng(crypto.getRandomValues(new Uint32Array(1))[0]);
  const W = CAST_WATERS[e.water] || CAST_WATERS.same;
  const net = mu => Array.from({ length: e.n }, () => R.normal(mu, CAST_SD));
  const a = net(W.a[1]), b = net(W.b[1]);
  const p = S.welch(a, b).p;
  const r = await api("cast", { pid: me && me.pid, round: e.round, p }).catch(() => ({ ok: false, j: {} }));
  if (!r.ok) {
    btn.disabled = false;
    const err = $("#liveCast .lcErr");
    if (err) err.textContent = r.j.error || "That didn't reach the class. Try again.";
    return;
  }
  castDone = { round: e.round, water: e.water, a, b, p };
  if (st && st.me) st.me.cast = true;
  renderCast();
}
