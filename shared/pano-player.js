/*
 * pano-player.js — the shared pseudo-360 room player, scenario-agnostic.
 *
 * A scenario shell (play.html) is tiny: link the Pannellum CSS + pano-player.css,
 * load the Pannellum script, then `<script type="module" src=".../shared/pano-player.js">`.
 * This module fetches the scenario's own `scenario.json` (relative to play.html) and
 * injects its own DOM to drive it. (Renamed 2026-07-16 from the old window.CHAPTER
 * global to a fetched scenario.json — the single source of truth also read by the
 * authoring harness; the object is the *scenario*, formerly "chapter".)
 *
 * A scenario is a set of pseudo-360 rooms. Each room has a `panorama` (+ optional
 * `panoramaOpen`), a `wrap` {haov,vaov,hfov,vOffset,pitch}, and `hotspots` with
 * boxes [x0,y0,x1,y1] (fractions of the flat scene) + per-type content:
 *   puzzle → { starterCode, question:{prompt,options,correct,maxAttempts,feedback} }  (multiple choice)
 *          OR { starterCode, check:{prompt,requires,expr,hint,maxAttempts,feedback} }  (Phase 4: graded on
 *             the LIVE R session — expr is a single R logical run against the student's globalenv)
 *   clue   → { body }
 *   door   → (box) + optional { direction:"forward"|"back", to:"<roomKey>", requires:"<gateId>"|[ids] }.
 *            forward (default): opens on its GATE — `requires` (a puzzle/lock hotspot id, or array) if
 *            set, else the room's PRIMARY gate — swaps to panoramaOpen, shows the target's entry,
 *            advances. back: always live, no gate, NO entry; returns to `to`. A door with no
 *            direction/to uses the legacy linear fallback (goThrough → next unsolved room / finish).
 *            A door may ALSO carry `availableWhen` (+ diegetic `lockedBody`) — a cross-room condition
 *            ({solved:key}|{allSolved}|{gte}) that seals it regardless of direction until met (e.g. a
 *            mast the player is too queasy to climb until the cure has cycled). 2026-07-31.
 *   lock   → { answer, length?, maxAttempts?, feedback? } — a NO-INSTRUCTIONS keypad gate for the
 *            escape objective: matches a fixed, derivable code; not in the codec (two-phase design).
 *   dial   → { key, states:[{value,label}], hint? } — a world-state control; sets gameState[key]
 *            among labelled states (no gate, no codec). Pairs with mapview (the multiple-mappings mechanic).
 *   mapview→ { key, images:{<state>:path}, caption?, empty? } — shows the image mapped to the CURRENT
 *            gameState[key], so a distant chart re-renders as the dial turns.
 *   Per-gate solve (2026-07-18): a room's puzzle + lock hotspots are independent GATES. The PRIMARY
 *   gate (first puzzle, else first lock) advances the room + records the codec; other gates just open
 *   their own `requires` door — so a boss room can hold a graded puzzle AND a separate escape lock.
 * A room may also carry `entry` (a string, or { title?, text?, button? }) — an optional
 * interstitial "loading" card shown as the player passes INTO that room (no x500 gate).
 * A room may also carry `sfx` — a sound effect (or an array of them) that plays while you're IN
 * that room: { src (path rel. to play.html), volume?=0.7, loop?=true, duckMusicTo?, delay?=0 }.
 * SFX start on room entry and stop on leave, are NOT muted by the music on/off toggle (a sound can
 * BE the puzzle, e.g. a dripped key code), and `duckMusicTo` (a 0–1 fraction of base music volume)
 * dips the music while they play. Authored per-room in the harness (Step 4).
 * Field notebook (case file): a persistent bottom-right chip holds a running list. Solving a room's
 * PUZZLE auto-logs its confirmed fact — the puzzle's `feedback.correct` text, reused so there's no
 * second field to author (the same short line confirms the answer in the modal AND is the notebook
 * entry). A `clue` hotspot may set `pickup` (true, or a string = the text to log) to show an
 * opt-in "Add to notebook" button; the clue's `image` (if any) is logged with the entry, so a picked-up
 * visual fragment (a mask/template) can be overlaid by eye in the notebook. The minted **submission code** is also logged here on analysis
 * completion, so it survives closing the code window. Session-only (cleared on Enter). It's the vehicle
 * for the meta-puzzle: e.g. an escape keypad whose code is the initials of each room's logged answer.
 * Nav is ‹ › arrows (yaw only). WebR boots once and mounts into the puzzle modal.
 *
 * scenario.json (the window.SCENARIO shape): { chapter, scenario, id, title, subtitle,
 *   story, enterLabel?, ambient?:"fireflies"|"snow"|"embers"|"leaves"|"none", cover?, coverPrompt?, done?:{title,body},
 *   packages, datasets:[{name,url}], setup,
 *   state?, rooms:[…], boss? }. Phase 4: the LINEAR graph fields are now EVALUATED — a room's
 *   `unlockedWhen` (`true` | {solved:key} | {allSolved:[keys]}) gates advancement and `onSolve`
 *   effects (`set`/`inc`) record into a `state` bag. Non-linear shapes (counter gates) are read
 *   as data but not yet evaluated (locked + a console warning). `boss` is still not played here.
 *   Phase 5: at the finish the player mints a submission code via `window.EscapeCodec` (load
 *   `shared/codec.js` in the shell before this module) using the scenario's `id` + `SECRET`.
 *   Two-objective (2026-07-17, Slice 1): a room may carry `phase:"analysis"|"escape"` (default
 *   analysis). ANALYSIS rooms are the graded set — the Canvas code mints (shown with scenario.done)
 *   the moment ALL analysis puzzles are solved (analysisComplete(), any room/order), and that window
 *   just CLOSES back to the room. ESCAPE rooms play on afterwards, are EXCLUDED from the codec (and
 *   from decoder/validate_keys.py), and end on scenario.escapeDone {title,body}. The player reaches
 *   the escape phase by walking through a door themselves (no auto hand-off — the code window is
 *   independent of room structure). See notes/two_phase_escape_design_notes.md.
 */
import { WebRConsole } from "./webr-console.js";
import { pickActiveVariants } from "./variant_resolve.js";   // Phase 3: per-hotspot state variants

let SCENARIO = null;   // assigned once scenario.json loads (see the fetch at the foot of this file)

// ---- inject the player DOM ----
const root = document.createElement("div");
root.innerHTML = `
  <section id="screen1" class="screen active">
    <div class="intro">
      <img id="s1cover" alt="" />
      <div class="introtext">
      <h1 id="s1title"></h1>
      <p id="s1story"></p>
      <div class="x500">
        <button id="enter"></button>
      </div>
      </div>
    </div>
  </section>
  <section id="screen2" class="screen">
    <div id="pano"></div>
    <div id="fxLayer"></div>
    <div id="sickness"></div>
    <div id="musicChip" style="display:none;position:absolute;bottom:10px;left:14px;z-index:20;background:rgba(0,0,0,.4);padding:4px 11px;border-radius:14px;font:12px system-ui;color:rgba(255,216,140,.9);user-select:none">♪ <a id="musicCredit" target="_blank" rel="noopener" title="Open the track on YouTube" style="color:inherit;text-decoration:underline"></a>: <span id="musicState" title="Toggle music on/off" style="cursor:pointer;text-decoration:underline;font-weight:600"></span></div>
    <div id="sfxChip" style="display:none;position:absolute;bottom:10px;left:14px;z-index:20;background:rgba(0,0,0,.4);padding:4px 11px;border-radius:14px;font:12px system-ui;color:rgba(255,216,140,.9);user-select:none">♫ sound effects: <span id="sfxState" title="Toggle sound effects on/off" style="cursor:pointer;text-decoration:underline;font-weight:600"></span></div>
    <button id="notebookChip" style="display:none;position:absolute;bottom:10px;right:14px;z-index:20;background:rgba(0,0,0,.42);padding:5px 12px;border-radius:14px;border:1px solid rgba(255,216,140,.35);font:12px system-ui;color:rgba(255,216,140,.92);cursor:pointer;user-select:none" title="Everything you've confirmed or picked up so far">🗒 Field notebook <span id="notebookCount" style="opacity:.7"></span></button>
    <button id="debriefChip" style="display:none;position:absolute;bottom:10px;left:50%;transform:translateX(-50%);z-index:20;background:rgba(0,0,0,.42);padding:5px 12px;border-radius:14px;border:1px solid rgba(255,216,140,.35);font:12px system-ui;color:rgba(255,216,140,.92);cursor:pointer;user-select:none" title="A look behind the scenes — how this world was built to teach the technique">🔎 Reveal how this world worked</button>
    <button id="skipChip" style="display:none;position:absolute;bottom:10px;left:50%;transform:translateX(-50%);z-index:20;background:rgba(0,0,0,.42);padding:5px 12px;border-radius:14px;border:1px solid rgba(255,216,140,.35);font:12px system-ui;color:rgba(255,216,140,.92);cursor:pointer;user-select:none" title="Skip the ungraded escape and go straight to your submission">Skip the ungraded escape phase →</button>
    <div id="hud"><span id="hudroom"></span></div>
    <div id="motifHud"></div>

    <button class="arrow l" id="prev">‹</button>
    <button class="arrow r" id="next">›</button>
    <div id="toast"></div>
    <div id="modal">
      <div class="mbox">
        <button class="mclose" id="mback" aria-label="Close" title="Close">✕</button>
        <div class="mtitle" id="mtitle"></div>
        <div id="mbody"></div>
      </div>
    </div>
    <div id="done">
      <div class="card">
        <button class="mclose" id="doneClose" aria-label="Close" title="Close">✕</button>
        <h2 id="doneTitle"></h2>
        <p id="doneBody"></p>
        <div id="codeWrap" style="display:none;margin:14px 0">
          <div style="font-size:13px;opacity:.75;margin-bottom:6px">Your submission code — paste it into Canvas:</div>
          <div id="codeVal" style="font:700 22px/1.3 ui-monospace,Menlo,Consolas,monospace;letter-spacing:2px;color:#ffd88c;background:rgba(0,0,0,.35);padding:10px 14px;border-radius:8px;user-select:all"></div>
          <button class="ghost" id="copyCode" style="margin-top:8px">Copy code</button>
        </div>
        <button class="ghost" id="continueOut" style="display:none">Close</button>
        <button class="ghost" id="doneDebrief" style="display:none">Reveal how this world worked</button>
        <button id="doneToSubmit" style="display:none"></button>
        <button class="ghost" id="replay">Play again</button>
      </div>
    </div>
    <div id="submitPrep">
      <div class="subintro">
        <div class="subcard">
          <button class="mclose" id="subClose" aria-label="Close" title="Close">✕</button>
          <div class="subtabs">
            <button class="subtab on" id="subTabPrep">Prepare submission</button>
            <button class="subtab" id="subTabDebrief" style="display:none">How this world worked</button>
          </div>
          <div id="subPanePrep">
            <div id="subId" style="display:none">
              <div class="lbl">Enter your x500 to generate your figures:</div>
              <div class="idrow"><input id="subX500" placeholder="your x500 (e.g. bust0037)" autocomplete="off" /><button id="subX500Go">Confirm</button></div>
            </div>
            <div id="subBody" style="display:none">
              <div id="subWork"></div>
              <div class="subactions">
                <button id="subPdf">⬇ Download PDF (figures + code)</button>
              </div>
            </div>
          </div>
          <div id="subPaneDebrief" style="display:none">
            <h2 id="debriefTitle" style="text-align:left;margin-top:4px"></h2>
            <div id="debriefBody"></div>
          </div>
        </div>
      </div>
    </div>
    <div id="loading">
      <div class="intro loadcard">
        <h1 id="loadTitle"></h1>
        <p id="loadText"></p>
        <button id="loadBtn"></button>
      </div>
    </div>
  </section>
  <div id="console-holder">
    <div id="console-block" class="console">
      <div id="webr-status">R console</div>
      <textarea id="code-input" spellcheck="false"></textarea>
      <div><button id="run-btn" disabled>▶ Run</button></div>
      <div id="webr-output"></div>
    </div>
  </div>`;
document.body.appendChild(root);

const $ = s => document.querySelector(s);
let viewer = null, rconsole = null, roomIdx = 0, room = null, solved = false;
// True once the analysis objective has been finished (code minted, finish shown) — makes finishAnalysis
// idempotent so the door path and the "all analysis puzzles solved" auto-trigger can't double-fire it.
let analysisFinished = false;
// True once the ESCAPE objective has been finished (escape-done card shown). Only used to decide
// whether the exit-debrief spoiler guard is still needed (opening the debrief after the escape is
// solved never needs to warn). Set in showEscapeDone(), reset on a fresh run.
let escapeFinished = false;
// Per-phase timing (2026-07-30, plain Date.now() ms — GitHub-Pages-safe, human-facing only, NOT in the
// codec/decoder). startTime is stamped when the player hits Enter; analysisFinishedTime once in
// finishAnalysis(); escapeFinishedTime once in showEscapeDone(). All reset to null on a fresh run.
// Durations surface on the submission-prep screen + the submission PDF (see computeTimings/timingLines).
let startTime = null, analysisFinishedTime = null, escapeFinishedTime = null;
// yaw the player was facing when the puzzle was opened — restored after the door swaps in,
// so solving keeps your orientation (and the "where's the door now?" hunt) instead of snapping to front.
let resumeYaw = 0;
// Graph-evaluator state (Phase 4): which rooms are completed + the world-state bag.
// The player still advances linearly, but advancement is GATED through condOK() reading each
// room's `unlockedWhen`, and `onSolve` effects are recorded — so non-linear scenarios (counter
// gates, out-of-order rooms) drop in later with no re-authoring.
let gameState = {};
const solvedRooms = new Set();
const visitedRooms = new Set();   // physically-entered rooms (incl. puzzle-less junctions) — first-visit entry cards
// Per-GATE solve state (per-gate model, 2026-07-18): hotspot ids of solved puzzle/lock gates. Lets one
// room carry two independent gates (e.g. a graded puzzle AND a separate escape lock) — each door opens
// on its own gate (`door.requires`), and only the room's PRIMARY graded gate records the codec.
const solvedGates = new Set();
// Per-room result for the submission codec (Phase 5): key -> { answer, attempts }.
// MCQ rooms store the chosen option index; console-check rooms store answer=1 (solved).
const roomResults = new Map();
let mintedCode = null;                 // the submission code, minted at analysis finish; shown on the submit-prep screen
const submissionWork = new Map();      // room.key -> { title, code, figure(dataURL|null) } captured at solve, for the PDF
function escHtml(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
// Attempts per puzzle hotspot, persisted across modal close/reopen within a session (hotspot id ->
// count). A plain in-memory Map keeps this static / GitHub-Pages-safe (no server, no storage) and
// consistent with the rest of the game state, which also resets on a full page reload.
const attemptCounts = new Map();
// Scrambling secret for shared/codec.js — MUST match decoder/decode_codes.R's SECRET
// (it moved here from the archived escape-engine.js). Change it per course, in BOTH files.
const SECRET = "chem5725-noatak-2026";
// Background music (optional): scenario.music (path relative to play.html) + scenario.musicVolume
// (0–1). Loops; starts on the Enter click (a user gesture, so autoplay policy is satisfied). An
// in-room button toggles it, and the choice is remembered in localStorage.
let music = null, musicOn = true, musicBaseVol = 0.5;   // musicBaseVol remembered for sfx ducking
let sfxOn = true;   // global sound-effects on/off (per-room ambience layers + solve/door stings); its own bottom-left chip, independent of the music toggle

// screen 1 — wired once scenario.json has loaded
function init(data) {
  SCENARIO = data;
  document.title = SCENARIO.title || "Escape room";
  const ambient = SCENARIO.ambient || "fireflies";   // "fireflies" | "snow" | "embers" | "leaves" | "none"
  if (ambient !== "none") {
    spawnParticles($("#screen1"), ambient, ambient === "snow" ? 40 : 18);   // landing screen
    spawnParticles($("#loading"), ambient, ambient === "snow" ? 32 : 14);   // inter-room interstitial
  }
  $("#s1title").textContent = SCENARIO.title || "";
  $("#s1story").textContent = SCENARIO.story || "";
  tpEditable($("#s1title"), () => SCENARIO.title || "", v => { SCENARIO.title = v; return tpPersist("/api/scenario-patch", { fields: { title: v } }); });
  tpEditable($("#s1story"), () => SCENARIO.story || "", v => { SCENARIO.story = v; return tpPersist("/api/scenario-patch", { fields: { story: v } }); });
  const s1cover = $("#s1cover");                       // landing-screen thumbnail (scenario.cover, beside play.html)
  if (SCENARIO.cover) { s1cover.src = SCENARIO.cover; s1cover.style.display = "block"; }
  else s1cover.style.display = "none";
  $("#enter").textContent = SCENARIO.enterLabel || "Begin →";
  $("#doneTitle").textContent = (SCENARIO.done && SCENARIO.done.title) || ((SCENARIO.title || "Scenario") + " — complete");
  $("#doneBody").textContent = (SCENARIO.done && SCENARIO.done.body) || "Nice work — you've finished this scenario.";
  $("#replay").onclick = () => location.reload();
  $("#copyCode").onclick = () => {
    const t = $("#codeVal").textContent;
    if (navigator.clipboard) navigator.clipboard.writeText(t).catch(() => {});
    const b = $("#copyCode"); b.textContent = "Copied ✓";
    setTimeout(() => { b.textContent = "Copy code"; }, 1500);
  };
  // submission-prep screen buttons (static — the work is filled when it opens)
  $("#subClose").onclick = () => $("#submitPrep").classList.remove("open");
  $("#subPdf").onclick = exportSubmissionPdf;
  // Two tabs in the submission card: prepare the submission, or read "how this world worked". The debrief
  // now renders INSIDE this card as a tab (fixes it opening behind the submission modal), not a separate one.
  $("#subTabPrep").onclick = () => switchSubTab("prep");
  $("#subTabDebrief").onclick = () => switchSubTab("debrief");
  // x500 is collected HERE (on the submission-prep screen), not on the landing screen — the figures are
  // personalised only at compile time.
  $("#subX500Go").onclick = confirmX500;
  $("#subX500").addEventListener("keydown", e => { if (e.key === "Enter") confirmX500(); });
  $("#notebookChip").onclick = openNotebook;
  $("#skipChip").onclick = openSubmitPrep;   // persistent in-room "skip the ungraded escape" → submission
  $("#enter").onclick = () => {
    $("#screen1").classList.remove("active");
    $("#screen2").classList.add("active");
    gameState = JSON.parse(JSON.stringify(SCENARIO.state || {}));
    solvedRooms.clear();
    solvedGates.clear();
    attemptCounts.clear();
    analysisFinished = false; escapeFinished = false;                // fresh objective state
    startTime = Date.now();                                           // per-phase timing: game starts now
    analysisFinishedTime = null; escapeFinishedTime = null;           // fresh timing state
    caseFile.length = 0; pickedClues.clear(); updateNotebookChip();   // fresh field notebook
    $("#notebookChip").style.display = "";                            // persistent chip, in-room only
    $("#debriefChip").style.display = "none";                        // appears only once analysis completes
    $("#skipChip").style.display = "none";                           // appears once analysis is done + an escape remains
    if (SCENARIO.heel) $("#pano").classList.add("heel");              // slow crash-heel of the horizon (opt-in)
    initMotif();                                                      // story-motif HUD (e.g. infection lesion)
    bootConsole();
    if (music && musicOn) music.play().catch(() => {});   // Enter is the user gesture autoplay needs
    const first = SCENARIO.rooms.findIndex(r => isBuilt(r) && condOK(r.unlockedWhen));
    if (first < 0) { finishAnalysis(); return; }   // nothing built to play yet
    startRoom(first);
  };
  setupMusic();
  setupSfxToggle();
}

// optional looping background music as ONE bottom-left chip: "♪ <credit link>: <on/off>".
// The credit (scenario.musicCredit = { text, url }) links out; the trailing on/off word
// toggles playback (remembered per browser).
function setupMusic() {
  const chip = $("#musicChip"), credit = $("#musicCredit"), state = $("#musicState");
  if (!SCENARIO.music) { chip.style.display = "none"; return; }
  music = new Audio(SCENARIO.music);
  music.loop = true;
  music.preload = "auto";
  // Attach to the DOM. A DETACHED `new Audio()` loop is fragile on mobile — heavy work elsewhere
  // (rebuilding the WebGL panorama on solve) can interrupt it and reset it to the start, which reads
  // as "the music restarts". A DOM-attached, controls-less element plays invisibly and stays stable.
  music.setAttribute("aria-hidden", "true"); music.style.display = "none";
  document.body.appendChild(music);
  musicBaseVol = (SCENARIO.musicVolume != null) ? SCENARIO.musicVolume : 0.1;   // default 10% — keep sfx audible over the music
  music.volume = musicBaseVol;
  musicOn = localStorage.getItem("panoMusic") !== "off";   // default on; remembers "off"
  const mc = SCENARIO.musicCredit;
  credit.textContent = (mc && mc.text) || "music";
  if (mc && mc.url) { credit.href = mc.url; }
  else { credit.removeAttribute("href"); credit.style.textDecoration = "none"; }  // plain text, no link
  chip.style.display = "";
  updateMusicBtn();
  state.onclick = () => {
    musicOn = !musicOn;
    localStorage.setItem("panoMusic", musicOn ? "on" : "off");
    if (musicOn) music.play().catch(() => {}); else music.pause();
    updateMusicBtn();
  };
  // Resilience: resume playback interrupted by something OTHER than the user toggle or a hidden tab —
  // e.g. a mobile browser pausing background audio when a full-screen modal overlay appears. The toggle
  // sets `musicOn = false` BEFORE calling pause(), so an intentional "off" is never fought; and we
  // resume from the current position (not the start), so this can't itself cause a restart.
  music.addEventListener("pause", () => {
    if (musicOn && !document.hidden)
      setTimeout(() => { if (musicOn && music.paused && !document.hidden) music.play().catch(() => {}); }, 60);
  });
}
function updateMusicBtn() {
  $("#musicState").textContent = musicOn ? "on" : "off";
}

// optional global sound-effects on/off as a SECOND bottom-left chip, sibling to the music chip:
// "♫ sound effects: <on/off>". SFX (per-room ambience layers + solve/door stings) are otherwise
// independent of the music toggle; this lets a player silence them without silencing the music.
// Shown ONLY if the scenario actually has sfx somewhere; stacked above the music chip when both show;
// the choice is remembered per browser. NOTE: a few scenarios use a sound AS a puzzle clue (e.g. a
// dripped key code) — turning sfx off would silence those too; none in the current data_vis scenarios.
function setupSfxToggle() {
  const chip = $("#sfxChip"), state = $("#sfxState");
  const rooms = SCENARIO.rooms || [];
  const anySfx = rooms.some(r => sfxListFor(r).length) ||
    rooms.some(r => r.solveSfx || (r.hotspots || []).some(h => h.solveSfx)) ||
    !!SCENARIO.solveSfx;
  if (!anySfx) { chip.style.display = "none"; return; }
  sfxOn = localStorage.getItem("panoSfx") !== "off";   // default on; remembers "off"
  chip.style.bottom = SCENARIO.music ? "42px" : "10px";   // stack above the music chip when both show
  chip.style.display = "";
  updateSfxBtn();
  state.onclick = () => {
    sfxOn = !sfxOn;
    localStorage.setItem("panoSfx", sfxOn ? "on" : "off");
    if (sfxOn) { if (room) startRoomSfx(room); }   // turn back on → restart the current room's layers
    else stopRoomSfx();                            // turn off → silence layers now (also un-ducks music)
    updateSfxBtn();
  };
}
function updateSfxBtn() {
  $("#sfxState").textContent = sfxOn ? "on" : "off";
}

// ---- per-room sound effects (optional) ----
// A room may carry `sfx`: one object, or an array of them (layers that play together). Each entry:
//   { src (path rel. to play.html), volume?=0.7, duckMusicTo?, delay?=0 (SECONDS before first start),
//     mode?: "loop" (default) | "interval",
//     gapMin?, gapMax?  (interval mode: the sound plays ONCE, then repeats after a gap of a random
//                        number of seconds in [gapMin,gapMax] — fixed if only gapMin; for occasional
//                        one-shots like a distant beep or a clunk),
//     crossfade?        (loop mode: seconds of overlap at the loop seam — default 4, clamped to ≤ clip/3) }
// LOOP MODE CROSSFADES ITS OWN SEAM (2026-07-21): a native `<audio loop>` clicks/dips on any clip that
// isn't sample-perfect, so a looping sfx instead ping-pongs two elements and EQUAL-POWER (cos/sin)
// crossfades the tail of one into the head of the next — constant summed power, so there's no dip at the
// loop point. `crossfade` sets the overlap seconds (clamped to ≤ clip/3); clips too short to overlap fall
// back to a native loop. (The old explicit "crossfade" mode is folded into loop; a legacy mode:"crossfade"
// still works — it's treated as loop.) They START on ENTER (a genuine room change via startRoom — NOT the
// in-room re-render that swaps in the open-door image) and STOP on leave. SFX are deliberately NOT gated
// by the music on/off toggle: a sound can BE the puzzle (e.g. a dripped key code). `duckMusicTo` (0–1)
// dips the music while the room's sfx play; the deepest duck across active sfx wins, restored on leave.
let sfxHandles = [];       // each: { stop(), setVolume(v) } — every started sound/timer for the active room
let sfxMixer = [];         // [{label,mode,vol,cfg,handle}] — active layers, exposed for the test-play mixer
function notifySfxChange() { try { if (window.__onSfxChange) window.__onSfxChange(); } catch (e) {} }

// A ONE-SHOT sfx — a solve / door-open sting. Plays once, not looped, not tracked as a room layer and not
// shown in the mixer. Authored per-puzzle as `hotspot.solveSfx` (a path string rel. to play.html, or
// { src, volume? }), with a room-level (`room.solveSfx`) then scenario-level (`SCENARIO.solveSfx`)
// fallback. NOT gated by the music on/off toggle. Fires when a gate is solved — a graded puzzle OR a lock
// releasing (i.e. the door opening).
function playOneShot(src, volume) {
  if (!src || !sfxOn) return;
  try { const a = new Audio(src); a.volume = (volume != null) ? volume : 0.9; a.play().catch(() => {}); }
  catch (e) {}
}

function sfxListFor(r) {
  const s = r && r.sfx;
  if (!s) return [];
  return (Array.isArray(s) ? s : [s]).filter(x => x && x.src);
}
function sfxLabel(cfg, i) {
  const base = (cfg.src || "").split("/").pop().replace(/\.[a-z0-9]+$/i, "");
  return (base || ("layer " + (i + 1))).replace(/[_-]+/g, " ");
}
// mode "interval": play once, then replay after a (random) gap — occasional one-shots
function _sfxInterval(src, vol, cfg) {
  const lo = (cfg.gapMin != null) ? cfg.gapMin : 8;
  const hi = (cfg.gapMax != null) ? Math.max(lo, cfg.gapMax) : Math.max(lo, 20);
  let a = null, timer = null, stopped = false, curVol = vol;
  const playOnce = () => {
    if (stopped) return;
    a = new Audio(src); a.loop = false; a.volume = curVol;
    a.addEventListener("ended", () => {
      if (!stopped) timer = setTimeout(playOnce, (lo + Math.random() * (hi - lo)) * 1000);
    });
    a.play().catch(() => {});
  };
  playOnce();
  return {
    stop() { stopped = true; if (timer) clearTimeout(timer); if (a) { try { a.pause(); } catch (e) {} } },
    setVolume(v) { curVol = v; if (a) try { a.volume = v; } catch (e) {} }
  };
}
// looping sfx with an equal-power crossfade at the seam (no dip). Two elements ping-pong: as `cur`
// nears its end, `nxt` starts and the tail fades into the head over `xf` seconds on a cos/sin curve.
function _sfxCrossfade(src, vol, cfg) {
  const want = Math.max(0.15, (cfg.crossfade != null) ? cfg.crossfade : 4);
  const a = new Audio(src), b = new Audio(src);
  a.preload = b.preload = "auto"; a.loop = b.loop = false;
  let cur = a, nxt = b, curVol = vol, stopped = false, watch = null, ramp = null, native = false;
  a.volume = curVol; b.volume = 0;
  const clearRamp = () => { if (ramp) { clearInterval(ramp); ramp = null; } };
  const cross = () => {
    clearRamp();
    const d = cur.duration, xf = (d && isFinite(d)) ? Math.min(want, d / 3) : want;
    try { nxt.currentTime = 0; } catch (e) {}
    nxt.volume = 0; nxt.play().catch(() => {});
    const steps = 24, dt = Math.max(15, (xf * 1000) / steps); let i = 0;
    ramp = setInterval(() => {
      i++; const f = Math.min(1, i / steps), g = f * Math.PI / 2;   // equal-power: cos²+sin²=1 → no dip
      try { cur.volume = curVol * Math.cos(g); nxt.volume = curVol * Math.sin(g); } catch (e) {}
      if (i >= steps) { clearRamp(); try { cur.pause(); cur.currentTime = 0; } catch (e) {} const t = cur; cur = nxt; nxt = t; }
    }, dt);
  };
  cur.play().catch(() => {});
  watch = setInterval(() => {
    if (stopped || ramp || native) return;
    try {
      const d = cur.duration;
      if (!d || !isFinite(d)) return;
      if (d < 1.2) { native = true; cur.loop = true; return; }              // too short to overlap → native loop
      if ((d - cur.currentTime) <= Math.min(want, d / 3)) cross();
    } catch (e) {}
  }, 100);
  return {
    stop() { stopped = true; if (watch) clearInterval(watch); clearRamp(); [a, b].forEach(x => { try { x.pause(); x.currentTime = 0; } catch (e) {} }); },
    setVolume(v) { curVol = v; try { if (!ramp) cur.volume = v; } catch (e) {} }   // ramp reads curVol live
  };
}
function startRoomSfx(r) {
  const list = sfxListFor(r);
  sfxMixer = [];
  if (!sfxOn || !list.length) { notifySfxChange(); return; }   // sfx toggled off → start no layers (music undisturbed)
  let deepestDuck = null;
  list.forEach((cfg, idx) => {
    const vol = (cfg.volume != null) ? cfg.volume : 0.7;
    const mode = (cfg.mode === "interval") ? "interval" : "loop";   // legacy "crossfade" ⇒ loop (now always crossfades)
    const begin = () => {
      const handle = (mode === "interval") ? _sfxInterval(cfg.src, vol, cfg) : _sfxCrossfade(cfg.src, vol, cfg);
      sfxHandles.push(handle);
      sfxMixer.push({ label: sfxLabel(cfg, idx), mode, vol, cfg, handle });
      notifySfxChange();
    };
    const delayMs = (cfg.delay || 0) * 1000;
    if (delayMs) { const t = setTimeout(begin, delayMs); sfxHandles.push({ stop: () => clearTimeout(t) }); }
    else begin();
    if (cfg.duckMusicTo != null) deepestDuck = (deepestDuck == null) ? cfg.duckMusicTo : Math.min(deepestDuck, cfg.duckMusicTo);
  });
  if (deepestDuck != null && music) music.volume = musicBaseVol * deepestDuck;
}
function stopRoomSfx() {
  sfxHandles.forEach(h => { try { h.stop(); } catch (e) {} });
  sfxHandles = [];
  sfxMixer = [];
  if (music) music.volume = musicBaseVol;                   // un-duck
  notifySfxChange();
}

// ---- test-play sound mixer API (used by shared/sfx-mixer.js on shared/test_play.html; harmless in
// normal play — nothing reads it there). Lets the mixer jump rooms and set live volumes. ----
window.PanoMixer = {
  rooms: () => (SCENARIO ? SCENARIO.rooms.filter(isBuilt).map(r => ({ key: r.key, title: r.title || r.key })) : []),
  current: () => (room ? room.key : null),
  gotoRoom: (key) => { const i = SCENARIO ? SCENARIO.rooms.findIndex(r => r.key === key && isBuilt(r)) : -1; if (i >= 0) startRoom(i); },
  layers: () => sfxMixer.map((m, i) => ({ i, label: m.label, mode: m.mode, vol: m.vol, src: m.cfg && m.cfg.src })),
  setLayerVolume: (i, v) => { const m = sfxMixer[i]; if (m) { m.vol = v; if (m.cfg) m.cfg.volume = v; if (m.handle && m.handle.setVolume) m.handle.setVolume(v); } },
  // The current room's solve / door-open stings, resolved per-gate (puzzle+lock hotspots) with the
  // room- then scenario-level fallback, deduped by src — so the mixer can fire each one WITHOUT solving
  // the puzzle. Empty until a room is entered.
  solveSounds: () => {
    if (!room) return [];
    const gates = (room.hotspots || []).filter(h => h.type === "puzzle" || h.type === "lock" || h.type === "grid");
    const out = [], seen = new Set();
    const add = (label, ss) => {
      if (!ss) return;
      const src = (typeof ss === "string") ? ss : ss.src;
      const vol = (ss && typeof ss === "object") ? ss.volume : undefined;
      if (!src || seen.has(src)) return;
      seen.add(src);
      out.push({ label, src, volume: vol });
    };
    gates.forEach(h => add(h.label || h.id || "gate", (h && h.solveSfx) || room.solveSfx || SCENARIO.solveSfx));
    if (!out.length) add("solve", room.solveSfx || SCENARIO.solveSfx);   // room with no gate-level sting
    return out;
  },
  fireSolve: (src, volume) => playOneShot(src, volume),
  hasMusic: () => !!music,
  musicSrc: () => (SCENARIO && SCENARIO.music) || null,   // for the mixer's amplitude auto-balance
  musicVolume: () => musicBaseVol,
  setMusicVolume: (v) => { musicBaseVol = v; if (music) music.volume = v; },
  onChange: (cb) => { window.__onSfxChange = cb; }
};

// ---- field notebook / case file (session) ----
// A running "case file" the player reads from a persistent bottom-right chip. Two ways things land in
// it: (1) AUTO — solving a room's puzzle logs its CONFIRMED fact, which is just that puzzle's
// `feedback.correct` text reused (deliberately one field, not two: the same short line confirms the
// answer in the modal AND is the notebook entry); (2) PICK-UP — a `clue` hotspot flagged `pickup`
// shows an "Add to notebook" button the student may choose to click. Session-only: cleared on Enter,
// like solvedRooms/attempts. Holds fragments the meta-puzzle later combines (e.g. Alaska's helicopter
// code = the initials of each room's logged answer), so it stops us punishing weaker working memory
// rather than weaker analysis.
const caseFile = [];              // [{ source, text, image, overlay, pos }] in the order they were logged
                                  // overlay: render the board tile semi-transparent (mask-overlay puzzles);
                                  // pos: {col,row} on the collage board, set lazily + updated on drag (session)
const pickedClues = new Set();    // room|hotspotId of clues already taken (guards double-add)

// the text a solved puzzle logs = its correct-feedback (a single authored source for both uses)
function puzzleNoteText(h) {
  const q = h && h.question, c = h && h.check, p = h && h.pick;   // MCQ / console-check / pick-the-point
  return (q && q.feedback && q.feedback.correct)
    || (c && c.feedback && c.feedback.correct)
    || (p && p.feedback && p.feedback.correct) || "";
}
// A notebook entry may carry TEXT and/or an IMAGE (path rel. to play.html). Image-carrying entries let
// pick-up clues log a visual fragment — e.g. a mask/template a later meta-puzzle overlays by eye in the
// notebook (Alaska's three filtered-glass templates). At least one of text/image must be present.
function logToNotebook(source, text, image, overlay) {
  if (!text && !image) return;
  caseFile.push({ source: source || "", text: text || "", image: image || "", overlay: !!overlay });
  updateNotebookChip();
}
function updateNotebookChip() {
  const cnt = $("#notebookCount"); if (cnt) cnt.textContent = caseFile.length ? "(" + caseFile.length + ")" : "";
}

// ---- collage board: pure grid helpers (a draggable snap-grid of collected image fragments) ----
// index -> {col,row} in raster order (left-to-right, top-to-bottom) for the auto-layout on collection.
function nbRasterCell(i, cols) { return { col: i % cols, row: Math.floor(i / cols) }; }
// snap a dragged pixel offset (relative to the board's top-left) to the nearest cell, clamped in-grid.
function nbSnap(leftPx, topPx, cell, cols, maxRow) {
  return {
    col: Math.max(0, Math.min(cols - 1, Math.round(leftPx / cell))),
    row: Math.max(0, Math.min(maxRow, Math.round(topPx / cell))),
  };
}
function nbStrip(html) { const x = document.createElement("div"); x.innerHTML = html || ""; return x.textContent || ""; }
const NB_CELL = 132;   // px per board cell (tile 120 + 12 gutter) — keep in sync with .nbtile in the CSS
let nbTopZ = 10;       // z-index high-water mark so a dragged tile lifts above its neighbours

// The field notebook renders in two sections: a COLLECTED-ITEMS BOARD (a draggable snap-grid holding
// every collected image) and a CLUES list (text-only entries — auto-logged puzzle answers, the submission
// code, textual pickups). Collected images auto-tile in raster order; the player drags them into any
// arrangement, snapping to the grid, and MAY stack several in one cell. This is the shared engine behind
// the hospital facet-collage escape (read a row of postcards as a code) and Alaska's Secret-of-the-Unicorn
// overlay (three translucent masks stacked on one cell). Board positions live on the caseFile entries, so
// an arrangement survives closing + reopening the notebook within a session.
function openNotebook() {
  const d = document.createElement("div");
  if (!caseFile.length) {
    d.innerHTML = `<p style="opacity:.75">Your notebook is empty. Solve a room's puzzle and its answer is noted here automatically; pick up a clue to add it yourself.</p>`;
    openModal("🗒 Field notebook", d);
    return;
  }
  const imgEntries = caseFile.filter(e => e.image);
  const textEntries = caseFile.filter(e => e.text && !e.image);

  if (imgEntries.length) {
    const cols = (SCENARIO && SCENARIO.boardCols) || 3;   // columns for the initial tidy raster tiling
    imgEntries.forEach((e, i) => { if (!e.pos) e.pos = nbRasterCell(i, cols); });
    // The draggable board is always kept a bit BIGGER than the tiles occupy — spare columns to the right
    // and spare rows below — so there's always plenty of empty space to rearrange into (never a cramped
    // exact-fit grid). Grows dynamically as tiles are dragged outward.
    const PAD_COLS = 2, PAD_ROWS = 2;
    const gridCols = cols + PAD_COLS;
    const usedRows = () => Math.max(0, ...imgEntries.map(e => e.pos.row)) + 1;
    const gridRows = () => usedRows() + PAD_ROWS;

    const sec = document.createElement("div");
    sec.innerHTML = `<div style="font:600 12px system-ui;opacity:.6;margin:0 0 6px">Collected items — drag to arrange</div>`;
    const scroll = document.createElement("div");
    scroll.style.cssText = "overflow:auto;max-width:100%";
    const board = document.createElement("div");
    board.id = "nbBoard";
    const sizeBoard = () => {
      board.style.width = (gridCols * NB_CELL) + "px";
      board.style.height = (gridRows() * NB_CELL) + "px";
    };
    sizeBoard();

    imgEntries.forEach(e => {
      const t = document.createElement("img");
      t.className = "nbtile" + (e.overlay ? " overlay" : "");
      t.src = e.image; t.alt = nbStrip(e.text); if (e.text) t.title = nbStrip(e.text);
      t.draggable = false;
      const place = () => { t.style.left = (e.pos.col * NB_CELL) + "px"; t.style.top = (e.pos.row * NB_CELL) + "px"; };
      place();
      t.addEventListener("pointerdown", ev => {
        ev.preventDefault();
        t.setPointerCapture(ev.pointerId);
        t.style.zIndex = String(++nbTopZ);
        t.classList.add("dragging");
        const sx = ev.clientX, sy = ev.clientY, ol = e.pos.col * NB_CELL, ot = e.pos.row * NB_CELL;
        const move = ev2 => { t.style.left = (ol + ev2.clientX - sx) + "px"; t.style.top = (ot + ev2.clientY - sy) + "px"; };
        const up = ev2 => {
          t.removeEventListener("pointermove", move);
          t.removeEventListener("pointerup", up);
          t.classList.remove("dragging");
          e.pos = nbSnap(ol + ev2.clientX - sx, ot + ev2.clientY - sy, NB_CELL, gridCols, gridRows() - 1);
          place(); sizeBoard();
        };
        t.addEventListener("pointermove", move);
        t.addEventListener("pointerup", up);
      });
      board.appendChild(t);
    });
    scroll.appendChild(board); sec.appendChild(scroll); d.appendChild(sec);
  }

  if (textEntries.length) {
    const sec = document.createElement("div");
    sec.style.cssText = imgEntries.length ? "margin-top:16px;padding-top:12px;border-top:1px solid rgba(255,255,255,.12)" : "";
    sec.innerHTML =
      (imgEntries.length ? `<div style="font:600 12px system-ui;opacity:.6;margin:0 0 6px">Clues</div>` : "") +
      textEntries.map(e =>
        `<div style="margin:0 0 12px;padding:0 0 12px;border-bottom:1px solid rgba(255,255,255,.08)">
           ${e.source ? `<div style="font:600 12px system-ui;opacity:.6;margin-bottom:3px">${e.source}</div>` : ""}
           <div>${e.text}</div>
         </div>`).join("");
    d.appendChild(sec);
  }
  openModal("🗒 Field notebook", d);
}

// box [x0,y0,x1,y1] fractions -> yaw/pitch across the room's wrap coverage
function boxToYP(box, c) {
  const cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
  return { yaw: cx * c.haov - c.haov / 2, pitch: c.vaov / 2 - cy * c.vaov + (c.vOffset || 0) };
}

// a room is playable once it has a committed panorama; stub rooms (built:false, no art)
// are carried in rooms[] for authoring but skipped by the player + the codec (Phase 7).
const isBuilt = r => !!(r && r.panorama);

// A room belongs to the ANALYSIS objective (default — graded, in the codec) or the ESCAPE
// objective (phase:"escape" — ungraded, excluded from the codec + key validation). The boss ends
// the analysis phase and mints the Canvas code; escape rooms play on afterwards (two_phase design).
const phaseOf = r => (r && r.phase) || "analysis";

// The ANALYSIS objective is complete when every built analysis room that carries a graded puzzle is
// solved — regardless of room order or which door you walk through. This is the sole trigger for the
// analysis finish (mint the Canvas code, then Close back to the room): a scenario may put escape puzzles in
// early rooms and the last analysis puzzle in a later room, so completion — not position — is what ends
// the objective. Returns false if there are no graded analysis rooms (an all-escape scenario never
// "finishes analysis").
function analysisComplete() {
  const need = (SCENARIO.rooms || []).filter(r =>
    isBuilt(r) && phaseOf(r) === "analysis" && (r.hotspots || []).some(h => h.type === "puzzle"));
  return need.length > 0 && need.every(r => solvedRooms.has(r.key));
}

// ---- condition evaluator ----
// Condition shapes: `true` (or absent), { solved:key }, { allSolved:[keys] }, and { gte:[stateKey,n] }
// (a counter/world-state gate reading gameState — e.g. { gte:["rooms_solved",3] } or the maze's
// { gte:["heights_read",7] }). Used by room `unlockedWhen` AND (2026-07-26) by the OPEN-WORLD MAZE
// fields — all optional + backward-compatible (absent ⇒ open):
//   • puzzle/lock `availableWhen` (+ `lockedBody`): a gated puzzle shows its diegetic lockedBody instead
//     of launching until met — free roam, ordered puzzles (see onHotspot / openLocked).
//   • door `direction:"open"`: an always-walkable maze passage (entry card on first visit; see doorIsOpen).
//   • clue `onPickup` (effects like {inc:"heights_read"}): runs applyEffects when a pickup is taken, so a
//     downstream gate can require e.g. all N junction heights read (see openClue).
// First consumer: hierarchical_clustering/canyon ("The Confluence"). Browser-tested 2026-07-26 via
// Playwright (headless Chromium): a synthetic maze exercised open-door nav, availableWhen+lockedBody on
// puzzle AND lock, onPickup→counter, and the {gte} gate — 8/8; alaska+henges still boot clean (no regression).
function condOK(cond) {
  if (cond === undefined || cond === true) return true;
  if (cond === false) return false;
  if (cond && typeof cond === "object") {
    if ("solved" in cond) return solvedRooms.has(cond.solved);
    if ("allSolved" in cond) return (cond.allSolved || []).every(k => solvedRooms.has(k));
    if ("gte" in cond) { const g = cond.gte || []; return (Number(gameState[g[0]]) || 0) >= Number(g[1]); }
    if ("eq" in cond) { const e = cond.eq || []; return String(gameState[e[0]]) === String(e[1]); }  // dial/state equality (variants)
  }
  console.warn("pano-player: unsupported unlockedWhen (treating as locked):", cond);
  return false;
}
// record a room's onSolve effects into the world-state bag (data-only for now; a future
// counter-gate evaluator reads these back)
function applyEffects(effects) {
  (effects || []).forEach(e => {
    if (!e || typeof e !== "object") return;
    if ("set" in e) gameState[e.set] = ("to" in e) ? e.to : true;
    if ("inc" in e) gameState[e.inc] = (gameState[e.inc] || 0) + (e.by || 1);
  });
}

// ---- per-gate solve model (2026-07-18) ----
// A room's GATES are its puzzle + lock hotspots. The PRIMARY gate (first puzzle, else first lock) is the
// one that advances the room + records the codec; other gates (e.g. an escape lock beside a graded
// puzzle) are independent. A door opens on its own requirement: `door.requires` (a gate id, or array of
// ids) if set, else the room's primary gate. Back doors are always open. This keeps every existing
// single-puzzle room working (no `requires` → gate on the primary) while letting a boss room carry a
// separate escape lock that gates its own exit.
// Gates are tracked per hotspot id, but ids are only unique WITHIN a room (the harness reuses
// obj_1/obj_2/… across rooms), so the solved-set is keyed by room + hotspot id — otherwise solving
// room1's obj_3 would mark room3's obj_3 solved too. `door.requires` names gate ids in the SAME room,
// so it resolves against that room's key.
const gateKey = (roomKey, id) => roomKey + "|" + id;
function primaryGate(r) {
  const gates = (r.hotspots || []).filter(h => h.type === "puzzle" || h.type === "lock" || h.type === "grid");
  return gates.find(h => h.type === "puzzle") || gates[0] || null;
}
function isPrimarySolved(r) {
  const g = primaryGate(r);
  return g ? solvedGates.has(gateKey(r.key, g.id)) : false;
}
function doorIsOpen(h, r) {
  if (h.availableWhen != null && !condOK(h.availableWhen)) return false;  // cross-room door gate (e.g. cured) — 2026-07-31
  if (h.direction === "open") return true;                     // maze passage: always walkable (entry on first visit)
  if ((h.direction || "forward") === "back") return true;      // back doors always live
  if (h.requires != null) {                                    // gate on specific gate(s) in THIS room
    const ids = Array.isArray(h.requires) ? h.requires : [h.requires];
    return ids.every(id => solvedGates.has(gateKey(r.key, id)));
  }
  return isPrimarySolved(r);                                    // legacy: the room's primary gate
}

// --- Three-phase portals (opt-in: SCENARIO.stonePortals) --------------------------------------------
// A forward arch is ASLEEP (black) until the analysis (primary puzzle) is solved -> AWAKENED (a dim
// starfield kindles in the arch) -> UNLOCKED (open galaxy, walkable) once its keypad lock is keyed.
// Everything here is gated on SCENARIO.stonePortals so no other scenario's behaviour changes.
function forwardDoor(r) {
  return (r.hotspots || []).find(h => h.type === "door" && (h.direction || "forward") === "forward") || null;
}
function portalUnlocked(r) {            // show the open panorama + make the forward door walkable
  const fd = forwardDoor(r);
  return fd ? doorIsOpen(fd, r) : isPrimarySolved(r);
}
function portalAwakened(r) {            // analysis solved (or a pre-awakened room), keypad not yet
  return !!(SCENARIO && SCENARIO.stonePortals) && (r.preAwakened || isPrimarySolved(r)) && !portalUnlocked(r);
}

// yaw of a room's forward (closed) door hotspot, so we can face it on entry; 0 if none.
// Prefer a forward door; fall back to whatever door exists (a room may have only a back door).
function doorYaw(r) {
  const c = r.wrap || { haov: 360, vaov: 90 };
  const doors = (r.hotspots || []).filter(h => h.type === "door" && Array.isArray(h.box));
  const door = doors.find(h => (h.direction || "forward") === "forward") || doors[0];
  return door ? boxToYP(door.box, c).yaw : 0;
}

function startRoom(i) {
  stopRoomSfx();                     // stop the previous room's ambience + restore music volume
  roomIdx = i; room = SCENARIO.rooms[i];
  if (room && room.key) visitedRooms.add(room.key);   // mark entered (so a puzzle-less junction's entry card won't re-show)
  applyFx();                         // setting-matched environment overlays (scenario.fx + room.fx)
  // Re-entry: a room already solved (reached again via a back door) opens in its solved state —
  // open panorama, forward door live, puzzle short-circuits as done.
  solved = !!(room.key && solvedRooms.has(room.key));
  $("#hudroom").textContent = room.title || "";
  const openState = portalUnlocked(room);   // open panorama once the room's FORWARD door is actually open (its gate solved) — generalised from `solved` 2026-07-31 so a door gated on a SECONDARY lock (airship room2's bridge hatch) opens the art at the right moment; a no-op where the forward door gates on the primary
  const img = basePanorama(room, openState);
  buildViewer(img, doorYaw(room));   // face the forward (closed) door on entry
  startRoomSfx(room);                // start this room's sound effect(s) (+ optional music duck)
  updateEnvironment();               // progressive heel/sickness reflect current state (persist across rooms)
}

// Ambient particles behind the card on an entry screen, chosen by scenario.ambient
// ("fireflies" | "snow" | "embers" | "leaves" | "none"). Each particle gets a random position/size/timing (negative
// animation-delay starts it mid-cycle) so the field moves organically. Decorative; GitHub-Pages-safe.
function spawnParticles(parent, kind, n) {
  if (!parent || parent.querySelector(".particles")) return;   // once per screen
  const layer = document.createElement("div"); layer.className = "particles";
  for (let i = 0; i < n; i++) {
    const f = document.createElement("span");
    if (kind === "snow") {
      const drifts = ["snowFall", "snowFall2", "snowFall3"];
      const size = (2 + Math.random() * 4).toFixed(1);         // 2–6px flakes
      const fd = 15 + Math.random() * 13;                      // 15–28s fall (gentle, slow drift)
      f.className = "snowflake";
      f.style.left = (Math.random() * 100).toFixed(2) + "%";
      f.style.width = f.style.height = size + "px";
      f.style.opacity = (0.5 + Math.random() * 0.5).toFixed(2);
      f.style.animation = `${drifts[i % drifts.length]} ${fd.toFixed(1)}s linear ${(-Math.random() * fd).toFixed(1)}s infinite`;
    } else if (kind === "leaves") {
      const drifts = ["leafBlow", "leafBlow2", "leafBlow3"];
      const size = (9 + Math.random() * 9).toFixed(1);        // 9–18px leaves
      const fd = 9 + Math.random() * 8;                        // 9–17s crossing on the wind
      f.className = "leaf";
      f.style.left = (Math.random() * 100).toFixed(2) + "%";
      f.style.top = (Math.random() * 70).toFixed(2) + "%";     // scattered through the upper/mid field
      f.style.width = f.style.height = size + "px";
      f.style.opacity = (0.55 + Math.random() * 0.4).toFixed(2);
      f.style.animation = `${drifts[i % drifts.length]} ${fd.toFixed(1)}s linear ${(-Math.random() * fd).toFixed(1)}s infinite`;
    } else if (kind === "embers") {
      const drifts = ["ffFloat", "ffFloat2", "ffFloat3"];
      const size = (2 + Math.random() * 3).toFixed(1);        // 2–5px sparks
      const fd = 7 + Math.random() * 8;                        // drift 7–15s
      const pd = 1.6 + Math.random() * 2.2;                    // flicker 1.6–3.8s
      f.className = "ember";
      f.style.left = (Math.random() * 100).toFixed(2) + "%";
      f.style.top = (55 + Math.random() * 45).toFixed(2) + "%";   // rise from the lower half
      f.style.width = f.style.height = size + "px";
      f.style.animation =
        `${drifts[i % drifts.length]} ${fd.toFixed(1)}s ease-in-out ${(-Math.random() * fd).toFixed(1)}s infinite, ` +
        `ffPulse ${pd.toFixed(1)}s ease-in-out ${(-Math.random() * pd).toFixed(1)}s infinite`;
    } else {
      const drifts = ["ffFloat", "ffFloat2", "ffFloat3"];
      const size = (3 + Math.random() * 4).toFixed(1);         // 3–7px
      const fd = 9 + Math.random() * 10;                       // drift 9–19s
      const pd = 2.2 + Math.random() * 2.6;                    // pulse 2.2–4.8s
      f.className = "firefly";
      f.style.left = (Math.random() * 100).toFixed(2) + "%";
      f.style.top = (Math.random() * 100).toFixed(2) + "%";
      f.style.width = f.style.height = size + "px";
      f.style.animation =
        `${drifts[i % drifts.length]} ${fd.toFixed(1)}s ease-in-out ${(-Math.random() * fd).toFixed(1)}s infinite, ` +
        `ffPulse ${pd.toFixed(1)}s ease-in-out ${(-Math.random() * pd).toFixed(1)}s infinite`;
    }
    layer.appendChild(f);
  }
  parent.insertBefore(layer, parent.firstChild);
}

// ---- story-motif HUD (opt-in: scenario.hud = { kind:"infection", healAt?:"analysis"|"escape" }) ----
// A small in-room emblem that tracks the narrative — currently the alien-infection lesion: it pulses,
// SPREADS (grows) as analysis rooms are solved, and HEALS (fades away) at the cure. Purely cosmetic;
// no gate, no codec. Generalise `kind` for other scenarios' motifs.
const MOTIF_KINDS = ["infection", "vitals"];
const motifOn = () => SCENARIO.hud && MOTIF_KINDS.includes(SCENARIO.hud.kind);
function initMotif() {
  const m = $("#motifHud");
  if (!motifOn()) { m.style.display = "none"; return; }
  const kind = SCENARIO.hud.kind;
  m.className = "motif-" + kind;                    // reset any prior state (resolved) + set kind
  m.innerHTML = kind === "vitals" ? '<div class="vitals"></div>' : '<div class="lesion"></div>';
  m.style.transform = "";
  m.style.display = "block";
  updateMotif();
}
function updateMotif() {
  if (!motifOn()) return;
  const m = $("#motifHud");
  if (m.classList.contains("resolved")) return;
  // infection: the lesion SPREADS (grows) with each analysis room solved. vitals: a steady weak beat until cured.
  if (SCENARIO.hud.kind === "infection") {
    const solvedA = SCENARIO.rooms.filter(r => phaseOf(r) === "analysis" && solvedRooms.has(r.key)).length;
    m.style.transform = "scale(" + (1 + solvedA * 0.16) + ")";
  }
}
function healMotif() {
  if (motifOn()) $("#motifHud").classList.add("resolved");   // per-kind: lesion fades, vitals steadies + strengthens
}

// fx — setting-matched environment overlays over the room (opt-in: scenario.fx and/or room.fx, an array
// of names: "flicker" | "frost" | "godrays" | "rain" | "dust" | "haze" | …). Data-driven: each name maps to
// a .fx-<name> CSS overlay in pano-player.css, so adding an effect is CSS-only. Gentle by design, never a
// horror strobe. Re-applied per room.
function applyFx() {
  const layer = $("#fxLayer"); if (!layer) return;
  layer.innerHTML = "";
  const names = [...new Set((SCENARIO.fx || []).concat((room && room.fx) || []))];
  names.forEach(n => { const d = document.createElement("div"); d.className = "fx-" + n; layer.appendChild(d); });
}

// ---- progressive, state-driven ENVIRONMENT (opt-in; backward-compatible) ----------------------------
// Two effects that ride WORLD-STATE instead of a HUD emblem, so tension is felt in the scene itself:
//   • scenario.heel = { mode:"progressive", by:"analysis", toward:"left"|"right", maxDeg } — the ship
//     LISTS further to one side as graded analysis rooms are solved (0 → maxDeg at the last one). A plain
//     `heel:true` stays the constant nautical roll (no listing). Realised via the CSS var `--heel-base`
//     that the heelRoll keyframe rolls ±1.3° around.
//   • scenario.sickness = { ramp:"analysis", clearOn:"cure", maxDim } — a vignette that DEEPENS over the
//     practice rooms (0 → maxDim) then CLEARS when the cure completes (analysisComplete()). No health bar.
// Both recompute on every room-enter and every solve, so they persist across free-roam nav. Counts mirror
// analysisComplete()'s "built analysis room with a graded puzzle" set. Absent fields ⇒ no-op (unchanged).
function gradedAnalysisRooms() {
  return (SCENARIO.rooms || []).filter(r =>
    isBuilt(r) && phaseOf(r) === "analysis" && (r.hotspots || []).some(h => h.type === "puzzle"));
}
// pure (unit-testable): base list angle in deg for the current solve count
function heelBaseDeg(heel, solvedA, totalA) {
  if (!heel || typeof heel !== "object" || heel.mode !== "progressive" || !totalA) return 0;
  const maxDeg = Number(heel.maxDeg) || 6;
  return (heel.toward === "left" ? -1 : 1) * maxDeg * Math.min(1, solvedA / totalA);
}
// pure (unit-testable): sickness vignette opacity (0..maxDim), cleared when cured
function sicknessDim(sick, solvedPractice, totalPractice, cured) {
  if (!sick || typeof sick !== "object" || cured) return 0;
  const maxDim = (sick.maxDim != null) ? Number(sick.maxDim) : 0.5;
  return totalPractice ? +(maxDim * Math.min(1, solvedPractice / totalPractice)).toFixed(3) : 0;
}
function updateEnvironment() {
  const graded = gradedAnalysisRooms();
  const solvedA = graded.filter(r => solvedRooms.has(r.key)).length;
  if (SCENARIO.heel && typeof SCENARIO.heel === "object" && SCENARIO.heel.mode === "progressive") {
    const pano = $("#pano");
    if (pano) { pano.classList.add("heel"); pano.style.setProperty("--heel-base", heelBaseDeg(SCENARIO.heel, solvedA, graded.length).toFixed(2) + "deg"); }
  }
  const el = $("#sickness");
  if (SCENARIO.sickness && el) {
    const practice = graded.filter(r => !r.isBoss);        // the boss IS the cure — it clears, doesn't add
    const solvedP = practice.filter(r => solvedRooms.has(r.key)).length;
    const cured = (SCENARIO.sickness.clearOn === "cure") ? analysisComplete() : false;
    el.style.opacity = String(sicknessDim(SCENARIO.sickness, solvedP, practice.length, cured));
  }
}

// Optional per-room interstitial "loading" card (schema: room.entry — a string, or
// { title?, text?, button? }). Shown as you pass into a room; rooms with no `entry` go
// straight through. No x500 gate — that's only on the landing screen.
function showInterstitial(r, onContinue) {
  const e = r.entry;
  const text = !e ? "" : (typeof e === "string" ? e : (e.text || ""));
  const title = (e && typeof e === "object" && e.title) || r.title || "";
  if (!text) return onContinue();                    // nothing authored → skip the card
  // per-room ambient override on this interstitial (e.g. jungle fireflies vs. an underground room's none)
  const amb = r.ambient || SCENARIO.ambient || "fireflies";
  const load = $("#loading"); const oldP = load.querySelector(".particles"); if (oldP) oldP.remove();
  if (amb !== "none") spawnParticles(load, amb, amb === "snow" ? 32 : 14);
  $("#loadTitle").textContent = title;
  // normal play renders the entry's HTML; test-play shows the raw source so edits round-trip (not flattened)
  if (isTestPlay()) $("#loadText").textContent = text; else $("#loadText").innerHTML = text;
  // test-play: edit the entry card in place. Writes r.entry as an object {title,text,button}; persists it.
  const _tpEntry = patch => {
    const cur = (r.entry && typeof r.entry === "object") ? r.entry : (r.entry ? { text: String(r.entry) } : {});
    r.entry = { ...cur, ...patch };
    return tpPersist("/api/room-patch", { roomKey: r.key, fields: { entry: r.entry } });
  };
  tpEditable($("#loadTitle"), () => title, v => _tpEntry({ title: v }));
  tpEditable($("#loadText"), () => text, v => _tpEntry({ text: v }));
  $("#loadBtn").textContent = (e && e.button) || "Continue →";
  $("#loadBtn").onclick = () => { $("#loading").classList.remove("open"); onContinue(); };
  $("#loading").classList.add("open");
}

// Bake a dim starfield INTO the equirectangular texture at the forward arch's box, so it tracks the
// view perfectly and wraps to 360 (a DOM hotspot overlay stays flat and drifts as you rotate around).
function drawStarfield(ctx, bx, by, bw, bh) {
  const w = Math.max(2, Math.round(bw)), h = Math.max(2, Math.round(bh));
  const off = document.createElement("canvas"); off.width = w; off.height = h;
  const o = off.getContext("2d"); const cx = w / 2, cy = h / 2;
  const g = o.createRadialGradient(cx, cy, 0, cx, cy, Math.max(cx, cy));
  g.addColorStop(0, "rgba(40,70,130,0.85)"); g.addColorStop(0.55, "rgba(14,26,54,0.6)"); g.addColorStop(1, "rgba(6,10,24,0.15)");
  o.fillStyle = g; o.fillRect(0, 0, w, h);
  const n = Math.max(24, Math.round(w * h / 850));
  for (let i = 0; i < n; i++) {
    const sx = Math.random() * w, sy = Math.random() * h, r = Math.random() * 1.6 + 0.35;
    o.globalAlpha = 0.45 + Math.random() * 0.55;
    o.fillStyle = "rgb(" + (200 + (Math.random() * 55 | 0)) + "," + (215 + (Math.random() * 40 | 0)) + ",255)";
    o.beginPath(); o.arc(sx, sy, r, 0, 6.29); o.fill();
  }
  o.globalAlpha = 1;
  o.globalCompositeOperation = "destination-in";     // feather the edges so it isn't a hard rectangle
  const m = o.createRadialGradient(cx, cy, Math.min(cx, cy) * 0.35, cx, cy, Math.max(cx, cy));
  m.addColorStop(0, "rgba(0,0,0,1)"); m.addColorStop(0.82, "rgba(0,0,0,1)"); m.addColorStop(1, "rgba(0,0,0,0)");
  o.fillStyle = m; o.fillRect(0, 0, w, h);
  ctx.drawImage(off, bx, by);
}
function compositeAwakened(room, baseUrl, cb) {
  const fd = forwardDoor(room);
  if (!fd || !Array.isArray(fd.box)) return cb(baseUrl);
  const base = new Image();
  base.onload = () => {
    try {
      const w = base.naturalWidth || base.width, h = base.naturalHeight || base.height;
      const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
      const ctx = cv.getContext("2d"); ctx.drawImage(base, 0, 0);
      const b = fd.box; drawStarfield(ctx, b[0] * w, b[1] * h, (b[2] - b[0]) * w, (b[3] - b[1]) * h);
      cb(cv.toDataURL("image/png"));
    } catch (e) { console.error("awakened composite failed", e); cb(baseUrl); }
  };
  base.onerror = () => cb(baseUrl);
  base.src = baseUrl;
}
// --- Per-hotspot state variants (Phase 3 / Option 2) ------------------------------------------------
// A hotspot may carry `variants:[{state,when,box,panorama}]`. The ACTIVE variant per object is the last
// whose `when` (condOK) holds; multiple objects can be active at once. We composite each active
// variant's box region over the base panorama on a canvas, so independent object states render together.
// Inert for every room without variants (the vast majority) — activeVariants returns [] and buildViewer
// renders exactly as before.
function activeVariants(r) {
  const vs = pickActiveVariants(r.hotspots, condOK);
  // Per-door open art: a door carrying `openImage` composites (exactly like a variant — box region stamped
  // from a base-sized image) when it is open. `doorIsOpen` already handles per-door gating (each door's own
  // `requires` gate, back doors, cross-room availability), so MULTIPLE doors can be open at once, each
  // showing its own art, and the base panorama stays "all closed" (see basePanorama). Inert for rooms with
  // no `openImage` door (they use the legacy room-level `panoramaOpen` swap).
  const openDoors = (r.hotspots || [])
    .filter(h => h && h.type === "door" && h.openImage && Array.isArray(h.box) && doorIsOpen(h, r))
    .map(h => ({ box: h.box, panorama: h.openImage }));
  return openDoors.length ? vs.concat(openDoors) : vs;
}
// The base panorama for a room: the closed scene — UNLESS the room uses the legacy room-level
// `panoramaOpen` whole-scene swap (and has NO per-door `openImage`) and its forward door is open. A per-door
// room keeps the closed base and composites each open door (activeVariants). Guards the two mechanisms from
// double-opening if a room ever carries both.
function basePanorama(room, openState) {
  const perDoor = (room.hotspots || []).some(h => h && h.type === "door" && h.openImage);
  return (openState && room.panoramaOpen && !perDoor) ? room.panoramaOpen : room.panorama;
}
function _loadImg(src) {
  return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("img " + src)); im.src = src; });
}
function compositeVariants(baseUrl, active, cb) {
  _loadImg(baseUrl).then(base => {
    const w = base.naturalWidth || base.width, h = base.naturalHeight || base.height;
    const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const ctx = cv.getContext("2d"); ctx.drawImage(base, 0, 0);
    return Promise.all(active.map(v => _loadImg(v.panorama).then(img => ({ v, img })))).then(loaded => {
      loaded.forEach(({ v, img }) => {
        const b = v.box, iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
        // Copy just this object's box region from the (base-sized) variant PNG onto the base canvas.
        // Source rect is taken from the variant's OWN dimensions so a size mismatch still maps correctly.
        ctx.drawImage(img,
          Math.round(b[0] * iw), Math.round(b[1] * ih), Math.round((b[2] - b[0]) * iw), Math.round((b[3] - b[1]) * ih),
          Math.round(b[0] * w),  Math.round(b[1] * h),  Math.round((b[2] - b[0]) * w),  Math.round((b[3] - b[1]) * h));
      });
      cb(cv.toDataURL("image/png"));
    });
  }).catch(e => { console.error("variant composite failed", e); cb(baseUrl); });  // never block render on a bad variant
}
// --- Ambient cinemagraphs (Phase: living scenes) ----------------------------------------------------
// A hotspot may carry `cinemagraph:{box, video}` — a small looping video that animates ONLY its box over
// the (otherwise still) scene. At render time we draw the composited still base once per frame, stamp each
// cinemagraph's box region from its <video> (feathered), and feed the canvas to Pannellum with
// dynamic:true so it re-uploads each frame. Everything else — pan, hotspots, doors, variants — is
// unchanged. Inert for every room without a `cinemagraph` field (the vast majority).
let _cineStop = null;   // tears down the current room's cinemagraph rAF + <video>s (set by startCinemagraph)
function activeCinemagraphs(r) {
  return (r.hotspots || [])
    .filter(h => h && h.cinemagraph && h.cinemagraph.video && Array.isArray(h.cinemagraph.box))
    .map(h => h.cinemagraph);
}
function startCinemagraph(baseUrl, cines, yaw) {
  _loadImg(baseUrl).then(baseImg => {
    const W = baseImg.naturalWidth || baseImg.width, H = baseImg.naturalHeight || baseImg.height;
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d");
    const vids = cines.map(c => {
      const v = document.createElement("video");
      v.src = c.video; v.muted = true; v.loop = true; v.playsInline = true; v.autoplay = true;
      v.play().catch(() => {});
      return { v, box: c.box };
    });
    _renderViewer(cv, yaw, true);                       // dynamic:true → Pannellum re-uploads the canvas
    let raf = 0;
    const draw = () => {
      ctx.drawImage(baseImg, 0, 0, W, H);               // the crisp composited still, every frame
      vids.forEach(({ v, box }) => {
        if (v.readyState < 2) return;
        const [x0, y0, x1, y1] = box;
        // A WRAP box (x0 > x1) straddles the L/R seam: region [x0..1] ∪ [0..x1]. The clip was generated from a
        // rolled, contiguous crop (see cinemagraph_gen), so we feather the whole thing then draw it in TWO
        // slices — left part onto the right edge, right part onto the left edge. Normal boxes are one draw.
        const wrap = x0 > x1;
        const wfrac = wrap ? (1 - x0) + x1 : (x1 - x0), bh = (y1 - y0) * H, bw = wfrac * W;
        if (bw < 1 || bh < 1) return;
        const fc = document.createElement("canvas"); fc.width = Math.round(bw); fc.height = Math.round(bh);
        const fx = fc.getContext("2d");
        fx.drawImage(v, 0, 0, v.videoWidth, v.videoHeight, 0, 0, fc.width, fc.height);
        fx.globalCompositeOperation = "destination-in";  // feather edges → blends into the still, no seam
        const g = fx.createRadialGradient(fc.width/2, fc.height/2, Math.min(fc.width,fc.height)*0.12,
                                          fc.width/2, fc.height/2, Math.max(fc.width,fc.height)*0.62);
        g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(0.7, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)");
        fx.fillStyle = g; fx.fillRect(0, 0, fc.width, fc.height);
        if (!wrap) {
          ctx.drawImage(fc, x0 * W, y0 * H);
        } else {
          const leftW = Math.round((1 - x0) * W);          // right-edge slice width (feather intact at the seam)
          ctx.drawImage(fc, 0, 0, leftW, fc.height, x0 * W, y0 * H, leftW, fc.height);            // → right edge
          ctx.drawImage(fc, leftW, 0, fc.width - leftW, fc.height, 0, y0 * H, fc.width - leftW, fc.height);  // → left edge
        }
      });
      try { viewer && viewer.setUpdate && viewer.setUpdate(true); } catch (e) {}
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    _cineStop = () => { cancelAnimationFrame(raf); vids.forEach(({ v }) => { try { v.pause(); v.removeAttribute("src"); v.load(); } catch (e) {} }); };
  }).catch(e => { console.error("cinemagraph start failed", e); _renderViewer(baseUrl, yaw); });
}
function buildViewer(img, yaw = 0) {
  const withCinemagraph = url => {
    const cines = activeCinemagraphs(room);
    if (!cines.length) return _renderViewer(url, yaw);   // no cinemagraph → static render (all existing rooms)
    startCinemagraph(url, cines, yaw);
  };
  const withVariants = url => {
    const active = activeVariants(room);
    if (!active.length) return withCinemagraph(url);     // no variants → straight to cinemagraph check
    compositeVariants(url, active, withCinemagraph);
  };
  // Awakened portal: bake the starfield into the texture so it tracks + wraps (see compositeAwakened),
  // THEN stamp any active variants, THEN run any ambient cinemagraphs on top of that composited base.
  if (SCENARIO.stonePortals && portalAwakened(room) && img === room.panorama) {
    return compositeAwakened(room, img, withVariants);
  }
  withVariants(img);
}
function _renderViewer(img, yaw = 0, dynamic = false) {
  // Stop any prior room's cinemagraph rAF + <video>s before we tear down its viewer (else the loop keeps
  // drawing into a destroyed viewer). No-op for non-cinemagraph rooms.
  if (_cineStop) { try { _cineStop(); } catch (e) {} _cineStop = null; }
  // Snapshot music position: tearing down + rebuilding the WebGL viewer can interrupt/reset the
  // background loop on some browsers. We restore it once the new scene is in (see `reveal`), so a
  // door-swap rebuild can't make the music jump back to the start.
  const musicPos = (music && !music.paused) ? music.currentTime : -1;
  if (viewer) { try { viewer.destroy(); } catch (e) {} }
  // A built room should carry a tuned `wrap`, but a room committed before its wrap was
  // saved (harness "Send to room" with no wrap.json) is built:true + panorama with NO wrap.
  // Guard so that case degrades to a sane pseudo-360 instead of a TypeError on `c.pitch`.
  const c = room.wrap || { haov: 360, vaov: 90 };
  const p = c.pitch || 0, f = c.hfov || 110;
  // Build hotspots up front and pass them in the config (the reliable path on a
  // static, non-draggable viewer — addHotSpot-after-load leaves them unpositioned).
  // `ambient` hotspots are decoration-only: they carry a cinemagraph (composited by activeCinemagraphs,
  // independent of markers) but get NO player marker/ring and aren't clickable. Every other type gets a marker.
  const hotSpots = (room.hotspots || []).filter(h => h.type !== "ambient").map(h => {
    const { yaw, pitch } = boxToYP(h.box, c);
    let cssClass = "hsmark " + h.type;
    if (h.type === "door") { cssClass += doorIsOpen(h, room) ? " open" : " locked"; if ((h.direction || "forward") === "forward" && portalAwakened(room)) cssClass += " awakened"; }
    if ((h.type === "puzzle" || h.type === "lock" || h.type === "grid") && solvedGates.has(gateKey(room.key, h.id))) cssClass += " done";
    return { id: h.id, yaw, pitch, cssClass, clickHandlerFunc: onHotspot, clickHandlerArgs: h };
  });
  // (Awakened starfield is now baked into the texture by compositeAwakened — no DOM overlay hotspot.)
  // No up/down / no zoom is enforced by disabling drag + zoom and only moving yaw
  // via the arrows — NOT by min===max pitch/hfov locks (those break hotspot projection).
  const stage = $("#pano");
  stage.style.opacity = "0";                  // hidden until the new scene loads, so no white/blank flash
  viewer = pannellum.viewer("pano", {
    type: "equirectangular", panorama: img, dynamic: dynamic,
    haov: c.haov, vaov: c.vaov, vOffset: c.vOffset || 0,
    hfov: f, pitch: p, yaw,
    autoLoad: true, showControls: false, autoRotate: 0,
    draggable: false, mouseZoom: false, doubleClickZoom: false,
    keyboardZoom: false, disableKeyboardCtrl: true,
    hotSpots: hotSpots,
    backgroundColor: [0.02, 0.05, 0.09],
  });
  const reveal = () => {
    stage.style.opacity = "1";               // fade up from black once the panorama is in
    // If rebuilding the viewer interrupted the music (paused it, or reset it toward the start) while
    // it should be playing, resume from where it was — so the loop is continuous across a scene swap.
    if (music && musicOn && musicPos >= 0 && (music.paused || music.currentTime < musicPos - 1)) {
      try { music.currentTime = musicPos; } catch (e) {}
      music.play().catch(() => {});
    }
  };
  viewer.on("load", reveal);
  setTimeout(reveal, 1200);                   // safety net if 'load' doesn't fire (e.g. image error)
}
const TURN = 45;
$("#prev").onclick = () => viewer && viewer.setYaw(viewer.getYaw() - TURN, 600);
$("#next").onclick = () => viewer && viewer.setYaw(viewer.getYaw() + TURN, 600);

function onHotspot(evt, h) {   // Pannellum calls clickHandlerFunc(event, clickHandlerArgs)
  try {
    if (h.type === "clue") return openClue(h);
    if (h.type === "dial") return openDial(h);
    if (h.type === "mapview") return openMapview(h);
    if (h.type === "puzzle") {
      if (solvedGates.has(gateKey(room.key, h.id))) return toast("You've already solved this one.");
      if (!condOK(h.availableWhen)) return openLocked(h);   // maze: puzzle gated by availableWhen (undefined ⇒ open)
      return openPuzzle(h);
    }
    if (h.type === "lock") {
      if (solvedGates.has(gateKey(room.key, h.id))) return toast("The lock is already open.");
      if (!condOK(h.availableWhen)) return openLocked(h);   // e.g. the escape panel until the map is complete
      if (SCENARIO.stonePortals) {                     // a keypad behind an unsolved analysis is inert
        const pg = primaryGate(room);
        if (pg && pg.type === "puzzle" && pg.id !== h.id && !solvedGates.has(gateKey(room.key, pg.id)))
          return toast("This portal must be awakened first.");
      }
      return openLock(h);
    }
    if (h.type === "grid") {                          // matrix selector (#15) — the data-free grouping escape
      if (solvedGates.has(gateKey(room.key, h.id))) return toast("The cache-frame is already set.");
      if (!condOK(h.availableWhen)) return openLocked(h);
      return openGrid(h);
    }
    if (h.type === "door") return handleDoor(h);
  } catch (e) { console.error("hotspot handler error", e); }  // Pannellum swallows handler throws
}

// Door navigation. A door is `direction:"forward"` (default) or `"back"`, with an optional explicit
// target `to:"<roomKey>"`. forward is gated on the room being solved and shows the target's entry;
// back is always live and shows no entry. Absent direction/to ⇒ the legacy linear fallback.
function handleDoor(h) {
  if ((h.direction || "forward") === "back") {
    return navigateTo(resolveDoorTarget(h, "back"), false);   // back: no gate, no entry
  }
  if (!doorIsOpen(h, room)) {
    // Test-play only: authors walk through locked doors so they can check downstream rooms without
    // solving each gate. isTestPlay() is set by shared/test_play.html; a real student run (play.html)
    // sets neither flag, so this bypass never fires for students — the door stays gated for them.
    if (isTestPlay()) toast("Test-play: locked door bypassed.");
    else if (h.availableWhen != null && !condOK(h.availableWhen))
      return toast(h.lockedBody || "Not yet — something else must be done first.");  // diegetic cross-room gate (e.g. too queasy to climb)
    else return toast((SCENARIO.stonePortals && portalAwakened(room))
      ? "The portal is awake, but sealed — key the stones to open it."
      : "The door won't budge — solve the puzzle first.");
  }
  if (h.endsEscape) return showEscapeDone();                  // a terminal escape exit inside any room
  if (h.to) {                                                  // explicit forward target
    const idx = SCENARIO.rooms.findIndex(r => r.key === h.to && isBuilt(r));
    if (idx >= 0) return navigateTo(idx, true);
  }
  return goThrough();                                          // linear fallback (also boss → finish)
}

// Resolve a door's destination room index: explicit `to` first; for a back door, fall back to the
// nearest earlier built room.
function resolveDoorTarget(h, dir) {
  if (h.to) {
    const idx = SCENARIO.rooms.findIndex(r => r.key === h.to && isBuilt(r));
    if (idx >= 0) return idx;
  }
  if (dir === "back") {
    for (let j = roomIdx - 1; j >= 0; j--) if (isBuilt(SCENARIO.rooms[j])) return j;
  }
  return -1;
}

// Go to a room by index. `withEntry` shows the target's interstitial ONLY on a first visit — a
// re-visited (already-solved) room, forward or back, never re-shows its entry text.
function navigateTo(idx, withEntry) {
  if (idx == null || idx < 0) return;
  const target = SCENARIO.rooms[idx];
  const firstVisit = !(target.key && (visitedRooms.has(target.key) || solvedRooms.has(target.key)));
  if (withEntry && firstVisit) return showInterstitial(target, () => startRoom(idx));
  startRoom(idx);
}

// ---- modal helpers ----
// Test-play only. The generic test player (shared/test_play.html) sets these flags; a real student run
// (play.html) never does — so the "Solve" shortcut below is invisible to students.
const isTestPlay = () => !!(window.TEST_PLAY || window.SFX_MIXER);

// ---- test-play inline text editing (gated on isTestPlay) --------------------------------------------
// In the test player ONLY, key TEXT surfaces — the opening story, room entry cards, clue bodies, and the
// finish screens — are click-to-edit; edits persist to the harness (scenario.json) via the same
// cross-origin API + chapter/scenario/harness URL params the sound mixer already uses. Puzzles are
// intentionally NOT editable here (their content/answers are complex — author them in the harness). A
// real student run (play.html) sets neither TEST_PLAY nor SFX_MIXER, so isTestPlay() is false and none of
// this attaches — students see plain, non-editable text.
const _tpQ = () => new URLSearchParams(location.search);
async function tpPersist(route, body) {
  const h = (_tpQ().get("harness") || "").replace(/\/$/, "");
  if (!h) return { ok: false, error: "no harness link — open via ▶ Test play" };
  const q = _tpQ();
  const r = await fetch(h + route, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chapter: q.get("chapter") || "", scenario: q.get("scenario") || "", ...body })
  });
  return r.json();
}
// Make a text element inline-editable in test-play. getVal() → current string; save(newText) → a promise
// resolving to {ok}. A coloured outline shows saving/saved/error. No-op outside test-play. Idempotent —
// re-binding a shared element (e.g. #doneTitle for done vs escapeDone) overwrites via the onblur property.
function tpEditable(el, getVal, save) {
  if (!el || !isTestPlay()) return;
  el.classList.add("tpedit"); el.setAttribute("contenteditable", "true"); el.spellcheck = false;
  el.title = "Test edit — type to change, click away to save to the harness";
  el.onkeydown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); } };
  el.onblur = async () => {
    const v = el.innerText.replace(/\n+$/, "");
    if (v === (getVal() || "")) return;
    el.classList.remove("tpok", "tperr"); el.classList.add("tpsaving");
    try { const j = await save(v); el.classList.remove("tpsaving"); el.classList.add(j && j.ok ? "tpok" : "tperr"); if (!(j && j.ok)) console.warn("test edit save failed:", j && j.error); }
    catch (err) { el.classList.remove("tpsaving"); el.classList.add("tperr"); console.warn("test edit save error:", err); }
  };
}

// The result a correct solve of hotspot h would report to solveRoom — used by the test-play "Solve"
// shortcut so a skipped puzzle still records the RIGHT codec answer (MCQ: the correct option index;
// everything else: answer=1 "solved"). attempts=1 so a skipped puzzle doesn't read as a struggle.
function correctResult(h) {
  if (h && h.question && typeof h.question.correct === "number") return { answer: h.question.correct, attempts: 1 };
  return { answer: 1, attempts: 1 };
}
// The test-play dev-solve action for a puzzle/lock hotspot: mirror the card's own success path
// (close the modal, then solveRoom with the correct result) with no answering required.
const devSolveThunk = h => () => { closeModal(); solveRoom(correctResult(h), h); };

function openModal(title, node, onDevSolve) {
  $("#mtitle").textContent = title;
  const body = $("#mbody"); body.innerHTML = ""; body.appendChild(node);
  // Test-play only: a one-click "Solve" so the author can skip a puzzle while testing. Gated on the
  // test player's flag, so students never see it. Re-created per open (ids repeat across modals).
  const old = document.getElementById("devSolveBtn"); if (old) old.remove();
  if (onDevSolve && isTestPlay()) {
    const b = document.createElement("button");
    b.id = "devSolveBtn"; b.className = "ghost"; b.textContent = "⏭ Solve";
    b.title = "Test play only — mark this puzzle solved and move on";
    b.onclick = onDevSolve;
    document.querySelector("#modal .mbox").appendChild(b);
  }
  $("#modal").classList.add("open");
}
$("#mback").onclick = closeModal;
function closeModal() { unmountConsole(); $("#modal").classList.remove("open"); }
function unmountConsole() { $("#console-holder").appendChild($("#console-block")); }

// A clue modal. If the clue is flagged `pickup` (true, or a string = the exact text to log), it shows
// an "Add to notebook" button the student must CHOOSE to click — pickups are opt-in, unlike the
// automatic puzzle-answer log. `pickup:true` logs the clue body; a string logs that string (concise).
// A clue's `image` (if any) is ALSO logged with the entry, so a picked-up visual fragment (a mask /
// template) lands in the notebook and can be overlaid there by eye — the meta-puzzle vehicle.
// A puzzle/lock whose `availableWhen` isn't met yet shows its diegetic `lockedBody` (a "not yet"
// message) instead of launching — the open-world ordering mechanic: roam freely, puzzles gate.
function openLocked(h) {
  const d = document.createElement("div");
  d.innerHTML = `<p>${h.lockedBody || "Not yet — something else must be done first."}</p>`;
  openModal(h.label || "Not yet", d);
}

function openClue(h) {
  const d = document.createElement("div");
  // a clue may carry an `image` (path rel. to play.html — a generated artwork), shown above the body
  const img = h.image ? `<img src="${h.image}" alt="" style="max-width:50%;display:block;margin:0 auto 8px;border-radius:8px">` : "";
  d.innerHTML = img;
  // clue body as its own element so test-play can make it editable (persists back to the room's hotspots)
  const bodyEl = document.createElement("p");
  if (isTestPlay()) bodyEl.textContent = h.body || "";   // test-play: show the raw source so HTML edits round-trip
  else bodyEl.innerHTML = h.body || "";                  // normal play: render the clue's HTML properly
  if (h.body || isTestPlay()) d.appendChild(bodyEl);
  tpEditable(bodyEl, () => h.body || "", v => { h.body = v; return tpPersist("/api/room-patch", { roomKey: room.key, fields: { hotspots: room.hotspots } }); });
  if (h.pickup) {
    const gk = gateKey(room.key, h.id || h.label || "");
    const btn = document.createElement("button"); btn.className = "qsubmit";
    const setTaken = () => { btn.textContent = "✓ In your notebook"; btn.disabled = true; };
    if (pickedClues.has(gk)) setTaken();
    else {
      btn.textContent = "Add to notebook";
      btn.onclick = () => {
        if (pickedClues.has(gk)) return;
        pickedClues.add(gk);
        logToNotebook(h.label || room.title,
          (typeof h.pickup === "string") ? h.pickup : (h.body || h.label || ""),
          h.image || "", h.overlay);
        if (h.onPickup) applyEffects(Array.isArray(h.onPickup) ? h.onPickup : [h.onPickup]);   // e.g. inc a heights-read counter
        setTaken();
      };
    }
    d.appendChild(btn);
  }
  openModal(h.label || "Clue", d);
}

// ---- dial (world-state control) + map-view (state-conditioned image) — the multiple-mappings
// mechanic (2026-07-18). A `dial` writes gameState[key] among labelled states (no gate, no codec); a
// `mapview` in a possibly-distant room shows the image mapped to the CURRENT dial state, so the same
// chart re-reads differently as the dial is flipped. Cross-referencing the states IS the puzzle.
//   dial    → { key, states:[{value,label}], hint? }
//   mapview → { key, images:{<state>:"path"}, caption?, empty? }
function dialLabel(h, val) {
  const s = (h.states || []).find(x => x.value === val);
  return s ? (s.label || s.value) : (val == null ? "—" : val);
}
function openDial(h) {
  const key = h.key || h.id;
  const states = h.states || [];
  const wrap = document.createElement("div");
  // brass gauge face + swinging needle (decorative; the sigil buttons below are what you click)
  const face = document.createElement("div"); face.className = "dialface";
  const needle = document.createElement("div"); needle.className = "needle";
  const hub = document.createElement("div"); hub.className = "hub";
  face.appendChild(needle); face.appendChild(hub);
  const row = document.createElement("div");
  row.style.cssText = "display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:10px 0";
  const caption = document.createElement("div"); caption.className = "qfeedback";
  const angleFor = i => states.length > 1 ? (-52 + 104 * i / (states.length - 1)) : 0;
  const refresh = () => {
    const cur = gameState[key];
    const idx = states.findIndex(s => s.value === cur);
    needle.style.transform = "translateX(-50%) rotate(" + (idx < 0 ? 0 : angleFor(idx)) + "deg)";
    caption.textContent = (cur != null)
      ? ("The dial rests on " + dialLabel(h, cur) + ".")
      : (h.hint || "Turn the dial — somewhere in the ship, something answers.");
    row.querySelectorAll("button").forEach(b => {
      const on = b.dataset.v === cur;
      b.style.outline = on ? "2px solid #ffd88c" : "";
      b.style.opacity = on ? "1" : ".75";
    });
  };
  states.forEach(s => {
    const b = document.createElement("button"); b.className = "ghost"; b.dataset.v = s.value;
    b.textContent = s.label || s.value;
    b.onclick = () => { gameState[key] = s.value; toast("The dial clicks to " + (s.label || s.value) + "."); refresh(); };
    row.appendChild(b);
  });
  wrap.appendChild(face); wrap.appendChild(row); wrap.appendChild(caption);
  openModal(h.label || "The dial", wrap);
  refresh();
}
function openMapview(h) {
  const key = h.key || "dial";
  const state = gameState[key];
  const src = (h.images && h.images[state]) || null;
  const d = document.createElement("div");
  if (src) {
    const img = document.createElement("img");
    img.src = src; img.alt = "";
    img.style.cssText = "max-width:100%;border-radius:8px;display:block;margin:0 auto";
    d.appendChild(img);
  } else {
    const p = document.createElement("div"); p.className = "qfeedback";
    p.textContent = h.empty || "The chart is dark — the dial hasn't been set to a mapping yet.";
    d.appendChild(p);
  }
  if (h.caption) {
    const c = document.createElement("div"); c.className = "qfeedback"; c.style.marginTop = "8px";
    c.textContent = (state != null ? (dialLabel(h, state) + " — ") : "") + h.caption;
    d.appendChild(c);
  }
  openModal(h.label || "The chart", d);
}

// Pick-a-point-on-the-plot puzzle (used by the escape "map on the wall"). `h.map` =
// { image (path rel. to play.html), points:[{lake, box:[x0,y0,x1,y1] as image fractions}],
//   answer:"<lake>", instructions?, feedback?:{correct, wrong} }. The plot is deliberately UNLABELLED
// (built from the real data), so the player recreates it with geom_text to find their lake, then clicks
// its point. Ungraded (escape phase) — clicking the correct point's box solves the room.
function openMapPuzzle(h) {
  if (viewer) resumeYaw = viewer.getYaw();
  openModal(h.label || "The survey chart", buildMapCard(h.map, (result) => { closeModal(); solveRoom(result, h); }), devSolveThunk(h));
}
function buildMapCard(map, onSolved) {
  const card = document.createElement("div"); card.className = "mapcard";
  // No instructions by default — deliberately blank, like the combination lock (the absence of a prompt
  // IS the puzzle). Only shows a line if a scenario explicitly authors `map.instructions`.
  const instrHTML = map.instructions ? `<div class="mapinstr">${map.instructions}</div>` : "";
  card.innerHTML =
    `${instrHTML}
     <div class="mapholder"><img class="mapimg" src="${map.image}" alt=""><div class="mappts"></div></div>
     <div class="qfeedback"></div>`;
  const pts = card.querySelector(".mappts"), fb = card.querySelector(".qfeedback");
  let done = false;
  (map.points || []).forEach(p => {
    const b = p.box || [0, 0, 0, 0];
    const dot = document.createElement("button"); dot.className = "mappt"; dot.type = "button";
    dot.setAttribute("aria-label", "a lake");
    dot.style.left = (b[0] * 100) + "%"; dot.style.top = (b[1] * 100) + "%";
    dot.style.width = ((b[2] - b[0]) * 100) + "%"; dot.style.height = ((b[3] - b[1]) * 100) + "%";
    dot.addEventListener("click", () => {
      if (done) return;
      if (p.lake === map.answer) {
        done = true; dot.classList.add("hit");
        fb.className = "qfeedback ok"; fb.innerHTML = (map.feedback && map.feedback.correct) || "That's the one.";
        setTimeout(() => onSolved({ answer: 1, attempts: 1 }), 900);
      } else {
        // Neutral, no hint (matches the combination lock's "Nothing happens.") — the puzzle stays blank.
        fb.className = "qfeedback no";
        fb.innerHTML = (map.feedback && map.feedback.wrong) || "Nothing happens.";
      }
    });
    pts.appendChild(dot);
  });
  return card;
}

function openPuzzle(h) {
  if (h.map) return openMapPuzzle(h);         // pick-a-point-on-the-plot puzzle (static image, no console)
  if (h.pick) return openPickPuzzle(h);       // Type 4: make-the-plot, click the tagged point (live console + picker)
  if (viewer) resumeYaw = viewer.getYaw();   // remember where we're facing, to restore after the door opens
  // Set code/output while the console block is still in the document — querying
  // #code-input after moving it into a detached div would return null.
  $("#code-input").value = h.starterCode || "";
  $("#webr-output").innerHTML = "";
  const cb = $("#console-block");
  const grid = document.createElement("div"); grid.className = "qa";
  const left = document.createElement("div");   // console pane
  const right = document.createElement("div");   // question pane
  left.appendChild(cb);                          // move the live console in
  const onSolved = (result) => { closeModal(); solveRoom(result, h); };
  // A puzzle grades EITHER on the live R session (`check`) OR by multiple choice (`question`).
  const pid = gateKey(room.key, h.id);   // per-room attempt-count key (ids repeat across rooms)
  right.appendChild(h.check ? buildCheckCard(h.check, onSolved, pid) : buildQuestion(h.question, onSolved, pid));
  grid.appendChild(left); grid.appendChild(right);
  openModal(h.label || "Puzzle", grid, devSolveThunk(h));
}

// multiple-choice card — gate is the *product* of running the analysis
function buildQuestion(q, onSolved, pid) {
  const maxA = q.maxAttempts || 4; let attempts = attemptCounts.get(pid) || 0, sel = -1;
  const card = document.createElement("div"); card.className = "qcard";
  const grp = "q" + Math.round(performance.now());
  card.innerHTML =
    `<div class="qprompt">${q.prompt}</div><div class="qopts"></div>
     <div class="qfeedback"></div><button class="qsubmit" disabled>Submit answer</button>`;
  const opts = card.querySelector(".qopts"), fb = card.querySelector(".qfeedback"), sub = card.querySelector(".qsubmit");
  q.options.forEach((o, i) => {
    const l = document.createElement("label"); l.className = "qopt";
    l.innerHTML = `<input type="radio" name="${grp}"><span>${o}</span>`;
    l.querySelector("input").addEventListener("change", () => { sel = i; sub.disabled = false; });
    opts.appendChild(l);
  });
  sub.addEventListener("click", () => {
    if (sel < 0) return;
    attempts++; attemptCounts.set(pid, attempts);
    if (sel === q.correct) {
      fb.className = "qfeedback ok"; fb.innerHTML = q.feedback.correct;
      sub.disabled = true; opts.style.pointerEvents = "none";
      setTimeout(() => onSolved({ answer: sel, attempts }), 900);   // MCQ: report chosen index + tries
    } else if (attempts >= maxA) {
      fb.className = "qfeedback out"; fb.innerHTML = q.feedback.reveal || "Out of attempts.";
      sub.disabled = true; opts.style.pointerEvents = "none";
    } else {
      fb.className = "qfeedback no";
      const hints = q.feedback.wrong || [];
      fb.innerHTML = (hints[Math.min(attempts - 1, hints.length - 1)] || "Not quite.") +
        ` <span class="attempts">(attempt ${attempts} of ${maxA})</span>`;
    }
  });
  // restore state if the student closed the modal and came back (attempts persist for the session)
  if (attempts >= maxA) {
    fb.className = "qfeedback out"; fb.innerHTML = q.feedback.reveal || "Out of attempts.";
    sub.disabled = true; opts.style.pointerEvents = "none";
  } else if (attempts > 0) {
    fb.className = "qfeedback no";
    fb.innerHTML = `<span class="attempts">(${attempts} of ${maxA} attempts used)</span>`;
  }
  return card;
}

// console-check card (Phase 4) — grade on the LIVE R session, not a radio index. The answer is
// the *product* of running the analysis: the student assigns result var(s), hits "Check my
// answer", and the engine evaluates check.expr (a single R logical) against their session. Same
// feedback ladder as the MCQ card. A puzzle carries EITHER `check` OR `question`.
// check: { prompt, requires:[vars], expr, hint, maxAttempts?, feedback?:{correct,wrong[],reveal} }
function buildCheckCard(check, onSolved, pid) {
  const maxA = check.maxAttempts || 4; let attempts = attemptCounts.get(pid) || 0;
  const fbk = check.feedback || {};
  const card = document.createElement("div"); card.className = "qcard";
  card.innerHTML =
    `<div class="qprompt">${check.prompt || "Assign your result, then check it."}</div>
     <div class="qfeedback"></div><button class="qsubmit">Check my answer</button>`;
  const fb = card.querySelector(".qfeedback"), sub = card.querySelector(".qsubmit");
  sub.addEventListener("click", async () => {
    if (!rconsole || !rconsole.ready) {
      fb.className = "qfeedback no"; fb.innerHTML = "R is still starting — give it a moment, run your code, then check.";
      return;
    }
    sub.disabled = true; const label = sub.textContent; sub.textContent = "checking…";
    const res = await checkAnswer(check, rconsole.webR);
    sub.textContent = label;
    if (res.reason === "missing") {   // required var not defined yet — nudge, don't spend an attempt
      fb.className = "qfeedback no";
      fb.innerHTML = check.hint ||
        ("Assign your result to " + (check.requires || []).map(v => `<code>${v}</code>`).join(", ") + " first, then run it.");
      sub.disabled = false; return;
    }
    attempts++; attemptCounts.set(pid, attempts);
    if (res.ok) {
      fb.className = "qfeedback ok"; fb.innerHTML = fbk.correct || "Correct — the door gives way.";
      setTimeout(() => onSolved({ answer: 1, attempts }), 900);   // console-check: answer=1 (solved) + tries
    } else if (attempts >= maxA) {
      fb.className = "qfeedback out"; fb.innerHTML = fbk.reveal || check.hint || "Out of attempts.";
    } else {
      fb.className = "qfeedback no";
      const hints = fbk.wrong || (check.hint ? [check.hint] : []);
      fb.innerHTML = (hints[Math.min(attempts - 1, hints.length - 1)] || "Not quite — check your pipeline and rerun.") +
        ` <span class="attempts">(attempt ${attempts} of ${maxA})</span>`;
      sub.disabled = false;
    }
  });
  // restore state if the student closed the modal and came back (attempts persist for the session)
  if (attempts >= maxA) {
    fb.className = "qfeedback out"; fb.innerHTML = fbk.reveal || check.hint || "Out of attempts.";
    sub.disabled = true;
  } else if (attempts > 0) {
    fb.className = "qfeedback no";
    fb.innerHTML = `<span class="attempts">(${attempts} of ${maxA} attempts used)</span>`;
  }
  return card;
}

// evaluate a check against the live R session: every `requires` var must exist, then `expr`
// must return a single TRUE. Returns { ok } or { ok:false, reason:"missing"|"error" }.
async function checkAnswer(check, webR) {
  for (const v of (check.requires || [])) {
    let ex = false;
    try { ex = await webR.evalRBoolean(`exists(${JSON.stringify(v)})`); } catch (e) { ex = false; }
    if (!ex) return { ok: false, reason: "missing" };
  }
  try {
    const val = await webR.evalRBoolean(check.expr);
    return { ok: !!val };
  } catch (e) {
    return { ok: false, reason: "error" };
  }
}

// ---- Type 4: pick-the-point (make the plot, click the answer) ----
// The student builds their OWN plot in the live console (left pane) and assigns it to `p`; the engine
// then renders THAT plot as the clickable surface (right pane) by swapping each layer's geom for its
// ggiraph interactive twin and splicing `data_id`/`tooltip = <idColumn>` (renderStudentPickSvg). Clicking
// the mark whose `data-id` === `pick.answer` solves the room. Graded like a `check`: reports { answer:1,
// attempts } so it flows through solveRoom -> roomResults -> codec with NO schema change (a pick room's
// decoder-key slot is therefore 1, the "solved" byte, same as a console-check). ggiraph is installed
// LAZILY on first use so only picker rooms pay its ~6.5s install (it's off the scenario-wide boot).
// Rendering the student's own plot (2026-07-28): robust to aes() in ggplot() OR the geom, coord_flip,
// points/bars, piped data — validated in tests/student_pick_smoke.mjs. `pick.plotCode` (the authored
// plot) is retained as a reference/fallback but is NOT rendered in normal play.
// pick: { prompt, answer, idColumn, idNoun?, plotCode?, width?, height?, maxAttempts?, hint?, feedback?:{correct,wrong[],reveal} }
let ggiraphReady = false;
async function ensureGgiraph(webR) {
  if (ggiraphReady) return;
  let have = false;
  try { have = await webR.evalRBoolean('requireNamespace("ggiraph", quietly = TRUE)'); } catch (e) { have = false; }
  if (!have) await webR.installPackages(["ggiraph"], { quiet: true });
  ggiraphReady = true;
}
// LEGACY / reference: render the AUTHORED plot code (which must leave its ggplot in `p`) through
// ggiraph's dsvg device. Retained for the smoke test + as an optional fallback; NOT used in normal play
// now that the picker renders the student's own plot (renderStudentPickSvg below).
async function renderPickSvg(webR, pick) {
  const w = pick.width || 7, h = pick.height || 4.2;
  const rcode =
    "{ suppressWarnings(suppressMessages({ library(ggplot2); library(ggiraph); library(dplyr) }))\n" +
    pick.plotCode + "\n" +
    ".er_f <- tempfile(fileext = \".svg\")\n" +
    "ggiraph::dsvg(file = .er_f, width = " + w + ", height = " + h + ")\n" +
    "print(p); grDevices::dev.off()\n" +
    "paste(readLines(.er_f), collapse = \"\\n\") }";
  return webR.evalRString(rcode);
}
// Render the STUDENT'S own plot (the ggplot they assigned to `p` in the console) as the clickable picker:
// swap each layer's geom for its ggiraph interactive twin and splice data_id/tooltip = <pick.idColumn>,
// so the marks on their chart become clickable + identity-tagged. `data_id` only needs the id column to
// exist in the layer data, so it's robust to WHERE aes() lives (ggplot() vs the geom), to coord_flip,
// points/bars, and piped data (validated: tests/student_pick_smoke.mjs). Throws if `p` isn't a taggable
// ggplot — the caller turns that into a "use a standard ggplot" nudge.
async function renderStudentPickSvg(webR, pick) {
  const w = pick.width || 7, h = pick.height || 4.2;
  const idcol = JSON.stringify(pick.idColumn || "");
  const rcode = `{ suppressWarnings(suppressMessages({ library(ggplot2); library(ggiraph); library(dplyr) }))
.er_make_interactive <- function(p, idcol) {
  if (!inherits(p, "ggplot")) stop("not a ggplot")
  ns <- asNamespace("ggiraph")
  twin <- function(geom) {
    cand <- paste0("GeomInteractive", sub("^Geom", "", class(geom)[1]))
    if (exists(cand, envir = ns, inherits = FALSE)) get(cand, envir = ns) else NULL
  }
  changed <- FALSE
  for (i in seq_along(p$layers)) {
    g <- twin(p$layers[[i]]$geom)
    if (is.null(g)) next
    p$layers[[i]]$geom <- g
    add <- ggplot2::aes(data_id = !!rlang::sym(idcol), tooltip = !!rlang::sym(idcol))
    m <- p$layers[[i]]$mapping
    p$layers[[i]]$mapping <- if (is.null(m)) add else utils::modifyList(m, add)
    changed <- TRUE
  }
  if (!changed) stop("no taggable layer")
  p
}
.er_p <- .er_make_interactive(p, ${idcol})
.er_f <- tempfile(fileext = ".svg")
ggiraph::dsvg(file = .er_f, width = ${w}, height = ${h})
print(.er_p); grDevices::dev.off()
paste(readLines(.er_f), collapse = "\\n") }`;
  return webR.evalRString(rcode);
}
function openPickPuzzle(h) {
  if (viewer) resumeYaw = viewer.getYaw();
  // Seed the console while it's still in the document (querying #code-input after the move returns null).
  $("#code-input").value = h.starterCode || "";
  $("#webr-output").innerHTML = "";
  // Clear any `p` left over from an earlier pick room so THIS room requires the student to build their
  // own plot (the draw gate is `p` being a fresh ggplot). Best-effort, fire-and-forget.
  if (rconsole && rconsole.ready) rconsole.webR.evalRVoid('suppressWarnings(if (exists("p")) rm(p))').catch(() => {});
  const cb = $("#console-block");
  const grid = document.createElement("div"); grid.className = "qa";
  const left = document.createElement("div");    // live console pane
  const right = document.createElement("div");    // prompt + interactive picker
  left.appendChild(cb);
  const onSolved = (result) => { closeModal(); solveRoom(result, h); };
  const pid = gateKey(room.key, h.id);            // per-room attempt-count key (ids repeat across rooms)
  right.appendChild(buildPickCard(h.pick, onSolved, pid));
  grid.appendChild(left); grid.appendChild(right);
  openModal(h.label || "Puzzle", grid, devSolveThunk(h));
}
function buildPickCard(pick, onSolved, pid) {
  const maxA = pick.maxAttempts || 4; let attempts = attemptCounts.get(pid) || 0;
  const fbk = pick.feedback || {};
  // STUDENT mode (`pick.idColumn` set) renders the student's own plot (`p`) tagged by idColumn; LEGACY
  // mode (no idColumn) renders the authored `pick.plotCode`. Both no longer auto-draw.
  const studentMode = !!pick.idColumn;
  const card = document.createElement("div"); card.className = "qcard";
  card.innerHTML =
    `<div class="qprompt">${pick.prompt || "Plot the data, then click your answer on the chart."}</div>
     <div class="pickholder" style="margin:8px 0;min-height:60px"></div>
     <div class="qfeedback"></div>
     <button class="qsubmit">${studentMode ? "Draw the clickable chart" : "Draw the chart"}</button>`;
  const holder = card.querySelector(".pickholder"), fb = card.querySelector(".qfeedback"),
        btn = card.querySelector(".qsubmit");
  let done = attempts >= maxA;
  // STUDENT mode: they build a ggplot in the console and assign it to `p`, and the engine renders THAT.
  // `p` is cleared on modal open, so this gate only passes once they've built a fresh plot in THIS puzzle.
  const hasStudentPlot = async () => {
    try { return await rconsole.webR.evalRBoolean('exists("p") && inherits(p, "ggplot")'); }
    catch (e) { return false; }
  };

  const wireClicks = () => {
    holder.querySelectorAll("[data-id]").forEach(el => {
      el.style.cursor = "pointer";
      el.addEventListener("click", () => {
        if (done) return;
        if (el.getAttribute("data-id") === pick.answer) {
          done = true; holder.style.pointerEvents = "none";
          fb.className = "qfeedback ok"; fb.innerHTML = fbk.correct || "That's the one.";
          setTimeout(() => onSolved({ answer: 1, attempts: attempts + 1 }), 900);   // graded like a check
        } else {
          attempts++; attemptCounts.set(pid, attempts);
          if (attempts >= maxA) {
            done = true; holder.style.pointerEvents = "none";
            fb.className = "qfeedback out"; fb.innerHTML = fbk.reveal || pick.hint || "Out of attempts.";
          } else {
            fb.className = "qfeedback no";
            const hints = fbk.wrong || (pick.hint ? [pick.hint] : []);
            fb.innerHTML = (hints[Math.min(attempts - 1, hints.length - 1)] || "Not that one — read the chart again.") +
              ` <span class="attempts">(attempt ${attempts} of ${maxA})</span>`;
          }
        }
      });
    });
  };

  const noun = pick.idNoun || "point";
  const draw = async () => {
    if (!rconsole || !rconsole.ready) {
      fb.className = "qfeedback no"; fb.innerHTML = "R is still starting — give it a moment, then press Draw.";
      return;
    }
    if (studentMode && !(await hasStudentPlot())) {   // enforce "make the plot yourself": build + assign `p`
      fb.className = "qfeedback no";
      fb.innerHTML = `Build your chart in the console and assign it to <code>p</code> (e.g. <code>p &lt;- ggplot(...) + geom_col()</code>), run it, then draw the clickable chart.`;
      return;
    }
    btn.disabled = true; const label = btn.textContent; btn.textContent = "drawing…";
    try {
      await ensureGgiraph(rconsole.webR);
      const svg = studentMode
        ? await renderStudentPickSvg(rconsole.webR, pick)   // render the STUDENT'S own plot, tagged
        : await renderPickSvg(rconsole.webR, pick);         // legacy: render the authored plot
      holder.innerHTML = svg;
      const svgEl = holder.querySelector("svg");
      if (svgEl) {   // make it responsive within the pane (keep the viewBox, drop fixed px size)
        svgEl.removeAttribute("width"); svgEl.removeAttribute("height");
        svgEl.style.maxWidth = "100%"; svgEl.style.height = "auto";
      }
      wireClicks();
      btn.textContent = "Redraw";
    } catch (e) {
      // Student mode has two distinct failure modes: their code errored vs. their plot can't be tagged.
      const msg = !studentMode
        ? "The chart didn't render — check your code and try again."
        : /not a ggplot/.test(String(e && (e.message || e)))
          ? `Assign your finished plot to <code>p</code> and run it, then draw.`
          : `That plot can’t be made clickable — use a standard ggplot with one mark per ${noun} (points or bars), then draw again.`;
      fb.className = "qfeedback no"; fb.innerHTML = msg;
      btn.textContent = label;
    } finally {
      btn.disabled = false;
    }
  };
  btn.addEventListener("click", draw);
  // NO auto-draw (either mode): the student presses Draw. In student mode they must first build the plot
  // in the console and assign it to `p`.
  // Restore end-state if attempts were exhausted earlier this session.
  if (done && attempts >= maxA) {
    fb.className = "qfeedback out"; fb.innerHTML = fbk.reveal || pick.hint || "Out of attempts.";
  } else if (attempts > 0) {
    fb.className = "qfeedback no"; fb.innerHTML = `<span class="attempts">(${attempts} of ${maxA} attempts used)</span>`;
  } else if (studentMode) {
    fb.className = "qfeedback no"; fb.innerHTML = "Build your graph in the console using ggplot and assign it to an object <code>p</code>. Then click “Draw the clickable chart” to render the clickable version of your graph and click on the geometric object that represents the answer to the question.";
  } else {
    fb.className = "qfeedback no"; fb.innerHTML = "Press “Draw the chart”, then click your answer on it.";
  }
  return card;
}

// ---- combination lock (two-phase escape — the no-instructions synthesis gate) ----
// A `lock` hotspot opens a keypad modal with NO printed prompt: the player must BRING the code,
// synthesised from the earlier rooms' answers (see notes/two_phase_escape_design_notes.md). It
// matches a FIXED, derivable `answer` (compared case/whitespace-insensitively via normalizeCode),
// is NOT recorded in the codec (escape-phase rooms are excluded there), and on success solves the
// room like any puzzle. Schema:
//   { type:"lock", box, label?, answer, length?, maxAttempts?, feedback?:{correct,wrong,out} }
const normalizeCode = s => (s || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
function openLock(h) {
  if (viewer) resumeYaw = viewer.getYaw();   // restore facing after the door swaps in on solve
  openModal(h.label || "Keypad", buildLockCard(h, (result) => { closeModal(); solveRoom(result, h); }), devSolveThunk(h));
}
function buildLockCard(h, onSolved) {
  if (h.mode === "stones") return buildStoneLockCard(h, onSolved);
  const target = normalizeCode(h.answer || "");
  const len = h.length || (h.answer ? h.answer.length : 4);
  const maxA = h.maxAttempts || 0;               // 0 = unlimited (this is the ungraded escape puzzle)
  const fbk = h.feedback || {};
  const pid = gateKey(room.key, h.id);           // per-room attempt-count key (ids repeat across rooms)
  let attempts = attemptCounts.get(pid) || 0;
  const card = document.createElement("div"); card.className = "qcard";
  // Deliberately NO prompt text — the absence of instructions IS the puzzle (Myst/Riven ethos).
  card.innerHTML =
    `<div style="text-align:center;margin:6px 0 12px">
       <input id="lockInput" maxlength="${len}" autocomplete="off" spellcheck="false"
         placeholder="${"·".repeat(len)}"
         style="font:700 26px/1.4 ui-monospace,Menlo,Consolas,monospace;letter-spacing:10px;text-align:center;text-transform:uppercase;width:100%;max-width:240px;padding:10px 12px;border-radius:8px;border:1px solid rgba(255,216,140,.4);background:rgba(0,0,0,.35);color:#ffd88c">
     </div>
     <div class="qfeedback"></div>
     <button class="qsubmit">Enter</button>`;
  const input = card.querySelector("#lockInput"), fb = card.querySelector(".qfeedback"), sub = card.querySelector(".qsubmit");
  const tryCode = () => {
    const val = normalizeCode(input.value);
    if (!val) { input.focus(); return; }
    attempts++; attemptCounts.set(pid, attempts);
    if (val === target) {
      fb.className = "qfeedback ok"; fb.innerHTML = fbk.correct || "The lock releases.";
      sub.disabled = true; input.disabled = true;
      setTimeout(() => onSolved({ answer: 1, attempts }), 900);
    } else if (maxA && attempts >= maxA) {
      fb.className = "qfeedback out"; fb.innerHTML = fbk.out || "The keypad goes dark.";
      sub.disabled = true; input.disabled = true;
    } else {
      fb.className = "qfeedback no"; fb.innerHTML = fbk.wrong || "Nothing happens.";
      input.select();
    }
  };
  sub.addEventListener("click", tryCode);
  input.addEventListener("keydown", e => { if (e.key === "Enter") tryCode(); });
  setTimeout(() => { try { input.focus(); } catch (e) {} }, 60);
  return card;
}

// Stone keypad (lock `mode:"stones"`): a display of N slots + four keys — standing "|", fallen "_",
// clear "X", and a spiral to submit. Answer is a raw "|"/"_" string (NOT normalizeCode'd, so the
// stone alphabet survives). Reports { answer:1 } on match, exactly like the text lock.
function buildStoneLockCard(h, onSolved) {
  const target = (h.answer || "").replace(/[^|_]/g, "");
  const len = h.length || target.length || 3;
  const maxA = h.maxAttempts || 0;                // 0 = unlimited (ungraded escape puzzle)
  const fbk = h.feedback || {};
  const pid = gateKey(room.key, h.id);
  let attempts = attemptCounts.get(pid) || 0;
  let entry = "";
  const card = document.createElement("div"); card.className = "qcard stonelock";
  const STAND = '<span class="stone stand" aria-hidden="true"></span>';
  const FALL = '<span class="stone fall" aria-hidden="true"></span>';
  const SPIRAL = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M13.5 15 a2 2 0 1 1 -2 -2 a4 4 0 1 1 4 4 a6 6 0 1 1 -6 -6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';
  card.innerHTML =
    `<div class="slots"></div>
     <div class="qfeedback"></div>
     <div class="keys">
       <button class="key kstand" title="standing stone" aria-label="standing stone">${STAND}</button>
       <button class="key kfall" title="fallen stone" aria-label="fallen stone">${FALL}</button>
       <button class="key kclear" title="clear" aria-label="clear">✕</button>
       <button class="key ksubmit" title="submit" aria-label="submit">${SPIRAL}</button>
     </div>`;
  const slots = card.querySelector(".slots"), fb = card.querySelector(".qfeedback");
  const clearFb = () => { fb.className = "qfeedback"; fb.innerHTML = ""; };
  const render = () => {
    slots.innerHTML = "";
    for (let i = 0; i < len; i++) {
      const s = document.createElement("span"); s.className = "slot";
      if (entry[i] === "|") s.classList.add("s-stand");
      else if (entry[i] === "_") s.classList.add("s-fall");
      slots.appendChild(s);
    }
  };
  const append = ch => { if (entry.length < len) { entry += ch; clearFb(); render(); } };
  const submit = () => {
    if (!entry) return;
    attempts++; attemptCounts.set(pid, attempts);
    if (entry === target) {
      fb.className = "qfeedback ok"; fb.innerHTML = fbk.correct || "The stones settle, and the portal opens.";
      card.querySelectorAll("button").forEach(b => b.disabled = true);
      setTimeout(() => onSolved({ answer: 1, attempts }), 900);
    } else if (maxA && attempts >= maxA) {
      fb.className = "qfeedback out"; fb.innerHTML = fbk.out || "The stones go cold.";
      card.querySelectorAll("button").forEach(b => b.disabled = true);
    } else {
      fb.className = "qfeedback no"; fb.innerHTML = fbk.wrong || "Nothing stirs. The stones are wrong, or out of order.";
    }
  };
  card.querySelector(".kstand").onclick = () => append("|");
  card.querySelector(".kfall").onclick = () => append("_");
  card.querySelector(".kclear").onclick = () => { entry = ""; clearFb(); render(); };
  card.querySelector(".ksubmit").onclick = submit;
  render();
  return card;
}

// ---- grid-select (matrix selector, mechanic #15) — the data-free grouping escape ----------------
// A `grid` hotspot renders a matrix: one ROW per item (`items:[{key,label}]`) × one COLUMN per bucket
// (`buckets:[{key,label}]`). The player assigns each item to exactly one bucket (click a cell; one
// selection per row; buckets may be shared). On submit, every item's chosen bucket must equal
// `answer` (an object `{itemKey: bucketKey}`). Ungraded — never in the codec (like `lock`); solving it
// solves the room (fires escapeDone in an escape-phase room). Recognition, not computation: the player
// brings the grouping they inferred in-world (e.g. tree heights), no printed method. Schema:
//   { type:"grid", box, label?, prompt?, items:[{key,label}], buckets:[{key,label}], answer:{}, maxAttempts?, feedback?:{correct,wrong,out} }
function openGrid(h) {
  if (viewer) resumeYaw = viewer.getYaw();   // restore facing after the door swaps in on solve
  openModal(h.label || "Panel", buildGridCard(h, (result) => { closeModal(); solveRoom(result, h); }), devSolveThunk(h));
}
function buildGridCard(h, onSolved) {
  const items = h.items || [], buckets = h.buckets || [], answer = h.answer || {};
  const maxA = h.maxAttempts || 0;                 // 0 = unlimited (ungraded escape)
  const fbk = h.feedback || {};
  const pid = gateKey(room.key, h.id);
  let attempts = attemptCounts.get(pid) || 0;
  const sel = {};                                  // itemKey -> bucketKey
  const card = document.createElement("div"); card.className = "qcard gridcard";
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  card.innerHTML =
    (h.prompt ? `<div class="qprompt">${h.prompt}</div>` : "") +
    `<table class="gridsel"><thead><tr><th></th>` +
      buckets.map(b => `<th>${esc(b.label)}</th>`).join("") + `</tr></thead><tbody>` +
      items.map(it => `<tr><th class="rowlab">${esc(it.label)}</th>` +
        buckets.map(b => `<td><button class="cell" data-item="${esc(it.key)}" data-bucket="${esc(b.key)}" aria-label="${esc(it.label)}: ${esc(b.label)}"></button></td>`).join("") +
        `</tr>`).join("") +
    `</tbody></table><div class="qfeedback"></div><button class="qsubmit">Set the cache</button>`;
  const fb = card.querySelector(".qfeedback"), sub = card.querySelector(".qsubmit");
  card.querySelectorAll(".cell").forEach(btn => btn.addEventListener("click", () => {
    const it = btn.dataset.item;
    sel[it] = btn.dataset.bucket;
    card.querySelectorAll(".cell").forEach(c => { if (c.dataset.item === it) c.classList.remove("on"); });
    btn.classList.add("on");
    fb.className = "qfeedback"; fb.innerHTML = "";
  }));
  const submit = () => {
    if (items.some(it => !sel[it.key])) { fb.className = "qfeedback no"; fb.innerHTML = "Place every kind first."; return; }
    attempts++; attemptCounts.set(pid, attempts);
    if (items.every(it => sel[it.key] === answer[it.key])) {
      fb.className = "qfeedback ok"; fb.innerHTML = fbk.correct || "The cache-frame settles into place.";
      card.querySelectorAll("button").forEach(b => b.disabled = true);
      setTimeout(() => onSolved({ answer: 1, attempts }), 900);
    } else if (maxA && attempts >= maxA) {
      fb.className = "qfeedback out"; fb.innerHTML = fbk.out || "The frame goes dark.";
      card.querySelectorAll("button").forEach(b => b.disabled = true);
    } else {
      fb.className = "qfeedback no"; fb.innerHTML = fbk.wrong || "That doesn't sit right — look again at how the kinds stand.";
    }
  };
  sub.addEventListener("click", submit);
  return card;
}

// A GATE (puzzle/lock hotspot `h`) was solved. Mark the gate. If it's the room's PRIMARY gate, advance
// the room: record the codec result (graded gates only — locks never), add to solvedRooms + run onSolve
// once. Non-primary gates (e.g. an escape lock beside a graded puzzle) just open their own `requires`
// door. Re-render with the open image once the primary gate is solved; keep facing where you were.
function solveRoom(result, h) {
  if (h && h.id) solvedGates.add(gateKey(room.key, h.id));
  // Optional solve / door-open sting: per-puzzle `solveSfx`, falling back to room then scenario level.
  const ss = (h && h.solveSfx) || room.solveSfx || SCENARIO.solveSfx;
  if (ss) playOneShot(typeof ss === "string" ? ss : ss.src, (typeof ss === "object") ? ss.volume : undefined);
  // Auto-log the confirmed fact for a solved PUZZLE (its feedback.correct, reused as the note). Runs
  // once per gate: a re-entered solved gate short-circuits in onHotspot and never re-enters here.
  if (h && h.type === "puzzle") logToNotebook(room.title, puzzleNoteText(h));
  const prim = primaryGate(room);
  const isPrimary = !!(h && prim && h.id === prim.id);
  const graded = !!(h && h.type === "puzzle");        // locks are never graded / never in the codec
  if (isPrimary) {
    const firstSolve = !(room.key && solvedRooms.has(room.key));   // guard: never re-record on re-entry
    if (room.key) {
      if (firstSolve && graded) { roomResults.set(room.key, result || { answer: 1, attempts: 1 }); captureSubmissionWork(room, h); }
      solvedRooms.add(room.key);                      // room completion for the graph evaluator
    }
    if (firstSolve) applyEffects(room.onSolve);        // world-state effects once (don't double-inc)
    solved = true;
  }
  updateMotif();                                       // story-motif HUD (e.g. the lesion spreads)
  updateEnvironment();                                 // progressive heel lists further; sickness dim deepens/clears
  const openState = portalUnlocked(room);   // see startRoom: follow the forward door's actual open state (handles a door gated on a secondary lock)
  const img = basePanorama(room, openState);
  buildViewer(img, resumeYaw);                         // stay facing where you were, not snap to front
  // An escape gate flagged `endsEscape` (e.g. a boss-room valve keypad) ends the ungraded escape when
  // solved — the in-room analogue of an endsEscape DOOR (handleDoor). Terminal: show the escape finish.
  if (h && h.endsEscape) return showEscapeDone();
  // If solving THIS analysis puzzle completes the whole analysis objective, end it here — the trigger is
  // "all analysis puzzles solved", not reaching a particular door/room. Let the scene settle, then show
  // the finish (mint code, then Close). Solving an escape puzzle, or a non-final analysis one,
  // falls through to the normal door prompt.
  if (graded && phaseOf(room) === "analysis" && analysisComplete()) {
    toast("Analysis complete.");
    setTimeout(finishAnalysis, 650);
    return;
  }
  if (SCENARIO.stonePortals && isPrimary && !portalUnlocked(room))
    toast("The portal wakes — stars kindle beyond the arch.");
  else
    toast(isPrimary ? "The door is open. Look for the way through." : "The lock releases — a way opens.");
}

function goThrough() {
  // next = the first not-yet-solved room IN THE CURRENT PHASE whose unlock condition now passes.
  // Staying within-phase is what creates the objective boundary: when the ANALYSIS phase runs out
  // of rooms (the boss is solved) we mint the graded Canvas code; when the ESCAPE phase runs out we
  // show the ungraded escape finish. Routing through condOK() keeps it robust to gated graphs later.
  const cur = phaseOf(room);
  const nextIdx = SCENARIO.rooms.findIndex(r =>
    isBuilt(r) && phaseOf(r) === cur && !solvedRooms.has(r.key) && condOK(r.unlockedWhen));
  if (nextIdx >= 0) return showInterstitial(SCENARIO.rooms[nextIdx], () => startRoom(nextIdx));
  if (cur === "escape") return showEscapeDone();
  // Analysis fallback: only finish if the objective is genuinely complete (all analysis puzzles solved).
  // The auto-trigger in solveRoom normally fires this first; guarding on analysisComplete() here stops a
  // door reached with a still-locked analysis room left over from minting an incomplete code.
  if (analysisComplete()) return finishAnalysis();
  return toast("There's still analysis to finish first.");
}

// ---- objective finishes (two-phase, 2026-07-17) ----
// End of the ANALYSIS objective: mint the graded per-student submission code (the "Canvas code")
// over the ANALYSIS rooms only, show it, and — if the scenario has an escape phase — offer to step
// outside into the (ungraded) escape objective. Recast of the former single showDone().
function finishAnalysis() {
  if (analysisFinished) return;                     // once only — auto-complete + door path both call this
  analysisFinished = true;
  if (analysisFinishedTime == null) analysisFinishedTime = Date.now();   // stamp analysis-phase end (once)
  if (!(SCENARIO.hud && SCENARIO.hud.healAt === "escape")) healMotif();   // the cure is named → lesion heals
  // Deliberately does NOT navigate or stop the room ambience: the window just presents the code and
  // CLOSES back to the room. The player walks on themselves (e.g. through the door to the escape phase),
  // so the code window is independent of room structure — it can fire from any room, in any order.
  // The code is NOT minted here: it's keyed on the student's x500, which is now collected on the
  // submission-prep screen (mintCode runs in buildSubmission after x500 is confirmed).
  // No escape phase → the graded work IS the end: go straight to the submission-prep screen.
  if (!hasEscapePhase() && !hasPendingEscape()) { openSubmitPrep(); return; }
  // Escape phase exists → show the analysis finish card, offering to skip the (ungraded) escape.
  $("#doneTitle").textContent = (SCENARIO.done && SCENARIO.done.title) ||
    ((SCENARIO.title || "Scenario") + " — analysis complete");
  $("#doneBody").textContent = (SCENARIO.done && SCENARIO.done.body) ||
    "Analysis complete — copy your submission code for Canvas, then close this and carry on.";
  tpEditable($("#doneTitle"), () => (SCENARIO.done && SCENARIO.done.title) || "", v => { SCENARIO.done = { ...(SCENARIO.done || {}), title: v }; return tpPersist("/api/scenario-patch", { fields: { done: SCENARIO.done } }); });
  tpEditable($("#doneBody"), () => (SCENARIO.done && SCENARIO.done.body) || "", v => { SCENARIO.done = { ...(SCENARIO.done || {}), body: v }; return tpPersist("/api/scenario-patch", { fields: { done: SCENARIO.done } }); });
  $("#codeWrap").style.display = "none";                      // the code now lives on the submission-prep screen
  $("#continueOut").style.display = "none";
  $("#doneDebrief").style.display = "none";                   // "how this world worked" now lives on the submission screen
  $("#doneClose").onclick = () => $("#done").classList.remove("open");   // X → back to the room to do the escape
  // Analysis-finish card is just the finish message + the ✕. The "skip the ungraded escape" affordance is
  // NOT on this card — it's a persistent bottom-of-screen chip (#skipChip, like the music/notebook chips),
  // revealed here so the player can try the escape and bail to submission from the room if stuck. No
  // play-again. (2026-07-28, Lucas)
  $("#doneToSubmit").style.display = "none";
  $("#replay").style.display = "none";
  $("#skipChip").style.display = "";
  $("#done").classList.add("open");
}

// End of the ESCAPE objective (ungraded) — terminal. No code here; it was already minted at the end
// of the analysis phase. Content from scenario.escapeDone {title, body}.
function showEscapeDone() {
  escapeFinished = true;                            // the escape is solved → debrief no longer needs a spoiler guard
  if (escapeFinishedTime == null) escapeFinishedTime = Date.now();   // stamp escape-phase end (once)
  $("#skipChip").style.display = "none";            // escape is done — nothing left to skip
  stopRoomSfx();                                    // silence the escape-room ambience on the finish card
  const e = SCENARIO.escapeDone || {};
  $("#doneTitle").textContent = e.title || "You escaped!";
  $("#doneBody").textContent = e.body || "You made it out. Nicely done.";
  tpEditable($("#doneTitle"), () => (SCENARIO.escapeDone && SCENARIO.escapeDone.title) || "", v => { SCENARIO.escapeDone = { ...(SCENARIO.escapeDone || {}), title: v }; return tpPersist("/api/scenario-patch", { fields: { escapeDone: SCENARIO.escapeDone } }); });
  tpEditable($("#doneBody"), () => (SCENARIO.escapeDone && SCENARIO.escapeDone.body) || "", v => { SCENARIO.escapeDone = { ...(SCENARIO.escapeDone || {}), body: v }; return tpPersist("/api/scenario-patch", { fields: { escapeDone: SCENARIO.escapeDone } }); });
  $("#codeWrap").style.display = "none";
  $("#continueOut").style.display = "none";
  $("#doneDebrief").style.display = "none";                   // "how this world worked" stays on the in-room chip
  $("#doneClose").onclick = () => $("#done").classList.remove("open");
  const toSub = $("#doneToSubmit");
  toSub.className = "";                           // default button style (the analysis card uses the chip style)
  toSub.style.display = "";
  toSub.textContent = "Prepare submission →";
  toSub.onclick = openSubmitPrep;
  $("#replay").style.display = "none";           // no play-again on the escape finish card (2026-07-28, Lucas)
  $("#done").classList.add("open");
}

// ---- submission preparation screen (2026-07-26) ----
// A landing-style screen (ambient particles) with the student's minted code, every graded puzzle's code +
// the figure it generated, and a one-click PDF of all figures + code. Reached from BOTH finishes (skip the
// escape, or after solving it). Code + figure are captured per graded room at solve time (submissionWork).
function captureSubmissionWork(r, h) {
  const ci = $("#code-input");
  const code = ci ? (ci.value || "").trim() : "";
  const out = $("#webr-output");
  const plots = out ? out.querySelectorAll("canvas.webr-plot") : [];
  const src = plots[plots.length - 1];
  // Store the figure RAW here — the x500 stamp/watermark is applied later, on the submission screen,
  // once the student enters their x500 (see stampAllFigures). Figures aren't shown until then.
  let figureRaw = null;
  if (src) { try { figureRaw = src.toDataURL("image/png"); } catch (e) { figureRaw = null; } }
  const question = (h && h.question && h.question.prompt) || (h && h.prompt) || "";   // carry the question forward
  submissionWork.set(r.key, { title: r.title || r.key, code, figure: null, figureRaw, question });
}
// ---- per-phase timing (human-facing only; NOT in the codec/decoder) ----
// Format a duration in ms as "12m 34s" (or "1h 05m 39s" past an hour); "—" for a missing/invalid span.
function fmtDuration(ms) {
  if (ms == null || !isFinite(ms) || ms < 0) return "—";
  const total = Math.round(ms / 1000);
  const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
  const pad = n => String(n).padStart(2, "0");
  return h > 0 ? `${h}h ${pad(m)}m ${pad(s)}s` : `${m}m ${pad(s)}s`;
}
// Compute the three spans from the stamped timestamps. Analysis = analysisFinished − start. Escape =
// escapeFinished − analysisFinished, but is null when the escape was SKIPPED (escapeFinishedTime never
// set — the #skipChip path jumps to submission without showEscapeDone). Total runs to the escape finish
// if it happened, else to now (submission time) so a skipped run still reads sensibly.
function computeTimings() {
  const escaped = escapeFinishedTime != null;
  const analysisMs = (startTime != null && analysisFinishedTime != null) ? analysisFinishedTime - startTime : null;
  const escapeMs = (escaped && analysisFinishedTime != null) ? escapeFinishedTime - analysisFinishedTime : null;
  const endTime = escaped ? escapeFinishedTime : Date.now();   // skipped escape → count total to submission time
  const totalMs = (startTime != null) ? endTime - startTime : null;
  return { escaped, analysisMs, escapeMs, totalMs };
}
// The three display strings — escape reads "not completed (escape skipped)" when the escape wasn't done.
function timingLines() {
  const t = computeTimings();
  return {
    analysis: fmtDuration(t.analysisMs),
    escape: t.escaped ? fmtDuration(t.escapeMs) : "not completed (escape skipped)",
    total: fmtDuration(t.totalMs),
  };
}
function renderSubmitWork() {
  const host = $("#subWork"); if (!host) return;
  host.innerHTML = "";
  const rooms = (SCENARIO.rooms || []).filter(r => isBuilt(r) && phaseOf(r) === "analysis" && submissionWork.has(r.key));
  if (!rooms.length) { host.innerHTML = `<div class="swnone">No puzzle code captured yet.</div>`; return; }
  const intro = document.createElement("div"); intro.className = "swintro";
  intro.textContent = "The R console from each puzzle in this scenario is shown below, pre-filled with the code you ran. You can refine that code, styling the plot, adding labels and colors, and more. Press Run to update the figure. At the end, use the download button to download a PDF of your work and submit it on Canvas.";
  host.appendChild(intro);
  // Per-phase timing summary (also printed in the PDF). Human-facing only; the graded code is unaffected.
  const tl = timingLines();
  const timing = document.createElement("div"); timing.className = "swtiming";
  timing.style.cssText = "margin:10px 0 4px;font:13px system-ui;opacity:.85;line-height:1.6";
  timing.innerHTML =
    `<span style="font-weight:600">Your times —</span> ` +
    `Analysis: ${escHtml(tl.analysis)} · Escape: ${escHtml(tl.escape)} · Total: ${escHtml(tl.total)}`;
  host.appendChild(timing);
  rooms.forEach(r => {
    const w = submissionWork.get(r.key);
    const div = document.createElement("div"); div.className = "swroom";
    const h = document.createElement("h3"); h.textContent = w.title || r.title || r.key; div.appendChild(h);
    if (w.question) {                                        // remind the student what they were asked
      const q = document.createElement("div"); q.className = "swq";
      q.innerHTML = `<span class="swqlbl">The question:</span> ${w.question}`;   // author content, trusted → HTML allowed
      div.appendChild(q);
    }
    const ta = document.createElement("textarea"); ta.className = "swcode"; ta.spellcheck = false; ta.value = w.code || ""; div.appendChild(ta);
    const rowEl = document.createElement("div"); rowEl.className = "swbtnrow";
    const runBtn = document.createElement("button"); runBtn.className = "swrun"; runBtn.textContent = "▶ Run & update figure";
    const stat = document.createElement("span"); stat.className = "swstat";
    rowEl.appendChild(runBtn); rowEl.appendChild(stat); div.appendChild(rowEl);
    const figWrap = document.createElement("div"); figWrap.className = "swfig";
    figWrap.innerHTML = w.figure ? `<img src="${w.figure}" alt="figure">` : `<div class="swnone">No figure yet — edit the code and Run.</div>`;
    div.appendChild(figWrap);
    runBtn.onclick = () => runSubmitBlock(r.key, ta, figWrap, stat, runBtn);
    host.appendChild(div);
  });
}
// Re-run a submission block's (edited) code through the shared WebR console and refresh its figure. The
// updated code + figure replace the captured ones, so the PDF picks up the nicer plot. Reuses the single
// in-game WebR instance (same packages/datasets/session), so the pre-filled code just runs.
async function runSubmitBlock(roomKey, ta, figWrap, stat, runBtn) {
  const w = submissionWork.get(roomKey) || {};
  w.code = ta.value; submissionWork.set(roomKey, w);        // persist the edit even before running
  bootConsole();                                            // ensure WebR is up (idempotent)
  if (!rconsole || !rconsole.ready) { stat.textContent = "R is still booting — try again in a moment."; return; }
  runBtn.disabled = true; stat.textContent = "running…";
  try {
    await rconsole.run(ta.value);
    const plots = $("#webr-output").querySelectorAll("canvas.webr-plot");
    const src = plots[plots.length - 1];
    if (src) {
      w.figureRaw = src.toDataURL("image/png");                 // keep raw as the re-stampable source of truth
      w.figure = stampedFigureDataURL(src); submissionWork.set(roomKey, w);   // x500 is known on this screen
      figWrap.innerHTML = `<img src="${w.figure}" alt="figure">`; stat.textContent = "figure updated ✓";
    } else stat.textContent = "ran — but no figure was drawn";
  } catch (e) { stat.textContent = "error: " + (e && e.message ? e.message : e); }
  finally { runBtn.disabled = false; setTimeout(() => { if (/updated|no figure/.test(stat.textContent)) stat.textContent = ""; }, 3500); }
}
function openSubmitPrep() {
  $("#done").classList.remove("open");
  bootConsole();                                            // warm up WebR so the refine-consoles are ready
  // x500 is collected HERE, not on the landing screen. Until it's entered, show only the x500 prompt;
  // once confirmed (this session, or on a re-open) show the code + figures + PDF.
  const confirmed = !!window.__x500;
  $("#subId").style.display = confirmed ? "none" : "";
  $("#subBody").style.display = confirmed ? "" : "none";
  if (confirmed) buildSubmission();
  else setTimeout(() => $("#subX500").focus(), 30);
  const host = $("#submitPrep .subintro");
  const old = host.querySelector(".particles"); if (old) old.remove();
  const amb = SCENARIO.ambient || "fireflies";
  if (amb !== "none") spawnParticles(host, amb, amb === "snow" ? 40 : 18);
  $("#subTabDebrief").style.display = SCENARIO.debrief ? "" : "none";   // "how this world worked" tab only if authored
  switchSubTab("prep");                                                 // always open on the prepare-submission tab
  $("#submitPrep").classList.add("open");
}
// Switch the submission card between its two tabs: prepare-submission and the "how this world worked"
// debrief. The debrief renders inline here (into #debriefBody), so it can't open behind the modal (#6).
function switchSubTab(which) {
  const dbg = which === "debrief";
  $("#subPanePrep").style.display = dbg ? "none" : "";
  $("#subPaneDebrief").style.display = dbg ? "" : "none";
  $("#subTabPrep").classList.toggle("on", !dbg);
  $("#subTabDebrief").classList.toggle("on", dbg);
  if (dbg) renderDebrief();                                             // (re)render the gallery into #debriefBody
}
// Confirm the entered x500, then reveal + build the submission payload (code + stamped figures).
function confirmX500() {
  const id = $("#subX500").value.trim();
  if (!/\S/.test(id)) { $("#subX500").focus(); return; }
  window.__x500 = id;
  $("#subId").style.display = "none";
  $("#subBody").style.display = "";
  buildSubmission();
}
// Fill the submission payload once the x500 is known: mint the (x500-keyed) code, personalise every
// figure captured during play with the x500 stamp + watermark, then render the refine blocks.
async function buildSubmission() {
  mintCode("analysis");                                     // keyed on the confirmed x500 — goes into the PDF ONLY.
  // The submission code is NOT shown on screen and has no copy button (2026-07-28): it's baked into the
  // downloaded PDF the student submits (see exportSubmissionPdf), so they never handle it directly.
  $("#subTabDebrief").style.display = SCENARIO.debrief ? "" : "none";
  await stampAllFigures();                                  // apply the x500 stamp to figures captured during play
  renderSubmitWork();
}
// Build a PDF of the student's figures + code with jsPDF (loaded from a CDN in play.html/test_play.html).
function exportSubmissionPdf() {
  const J = window.jspdf && window.jspdf.jsPDF;
  if (!J) { toast("PDF library didn't load — check your connection and reload."); return; }
  const who = window.__x500 || "anon";
  const doc = new J({ unit: "pt", format: "a4" });
  const M = 40, W = doc.internal.pageSize.getWidth(), H = doc.internal.pageSize.getHeight();
  let y = M;
  const ensure = h => { if (y + h > H - M) { doc.addPage(); y = M; } };
  doc.setFont("helvetica", "bold"); doc.setFontSize(16);
  doc.text(`${SCENARIO.title || SCENARIO.scenario || "Scenario"} — submission`, M, y); y += 22;
  doc.setFont("helvetica", "normal"); doc.setFontSize(11);
  doc.text(`x500: ${who}`, M, y); y += 16;
  if (mintedCode) {
    doc.text("Submission code (Canvas):", M, y); y += 14;
    doc.setFont("courier", "normal");
    doc.splitTextToSize(mintedCode, W - 2 * M).forEach(ln => { ensure(12); doc.text(ln, M, y); y += 12; });
    doc.setFont("helvetica", "normal"); y += 8;
  }
  // Per-phase timing (human-facing only — NOT in the submission code, so grading is unaffected).
  const tl = timingLines();
  doc.setFontSize(11);
  ensure(14); doc.text(`Analysis time: ${tl.analysis}`, M, y); y += 14;
  ensure(14); doc.text(`Escape time: ${tl.escape}`, M, y); y += 14;
  ensure(14); doc.text(`Total: ${tl.total}`, M, y); y += 16;
  (SCENARIO.rooms || []).filter(r => isBuilt(r) && phaseOf(r) === "analysis" && submissionWork.has(r.key)).forEach(r => {
    const w = submissionWork.get(r.key);
    ensure(26); doc.setFont("helvetica", "bold"); doc.setFontSize(13); doc.text(w.title || r.key, M, y); y += 18;
    if (w.question) {
      doc.setFont("helvetica", "italic"); doc.setFontSize(10);
      doc.splitTextToSize("Q: " + w.question.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(), W - 2 * M)
        .forEach(ln => { ensure(12); doc.text(ln, M, y); y += 12; });
      y += 4; doc.setFont("helvetica", "normal");
    }
    if (w.code) {
      doc.setFont("courier", "normal"); doc.setFontSize(9);
      doc.splitTextToSize(w.code, W - 2 * M).forEach(ln => { ensure(11); doc.text(ln, M, y); y += 11; });
      y += 6; doc.setFont("helvetica", "normal");
    }
    if (w.figure) {
      try {
        const props = doc.getImageProperties(w.figure);
        const iw = W - 2 * M, ih = iw * props.height / props.width;
        ensure(ih + 6); doc.addImage(w.figure, "PNG", M, y, iw, ih); y += ih + 10;
      } catch (e) {}
    }
    y += 6;
  });
  doc.save(`${SCENARIO.scenario || "submission"}_${who}.pdf`);
}

// ---- exit debrief (2026-07-22): a standalone, opt-in "how this world worked" screen ----
// Scenario-agnostic engine feature. Each scenario supplies its own text via scenario.debrief
// { title, body } where body is a plain string OR a list of sections ({ heading, body }, or plain
// strings) for a point-by-point walkthrough — why the lanterns / bells / paddies / map-picks mean what
// they mean. Gated on analysisComplete() (the graded boss), NOT on the OPTIONAL escape, so every
// student who finishes the graded work reaches it (Lucas: "I want all my students to learn"). Surfaced
// as a persistent in-room chip that appears once analysis is complete, plus a button on the escape-done
// card. Opened from the chip while the escape is still unsolved, it warns first (it gives the escape
// away). Static and in-room — no server, no LLM (that's the deliberately out-of-band interview).
const hasEscapePhase = () => (SCENARIO.rooms || []).some(r => isBuilt(r) && phaseOf(r) === "escape");
// In-room escape (2026-07-28): a boss/analysis room can carry the escape as a `lock` gate flagged
// `endsEscape` instead of a separate phase:"escape" room. An UNSOLVED such lock is a *pending* escape, so
// the analysis finish must not jump straight to submission while one remains, and the exit debrief keeps
// its spoiler guard. Composes with the phase model — either shape defers the jump and reaches showEscapeDone.
// (The lock should carry `availableWhen` so it can't be keyed before it's meant to — same as an escape
// DOOR being gated by `requires`; onHotspot enforces that. See handleDoor's endsEscape door path.)
const hasPendingEscape = () => (SCENARIO.rooms || []).some(r => isBuilt(r) &&
  (r.hotspots || []).some(h => h.type === "lock" && h.endsEscape && !solvedGates.has(gateKey(r.key, h.id))));

// Reveal the in-room "reveal how this world worked" chip. Called once the analysis objective finishes.
// No-op unless the scenario carries debrief text — the feature is opt-in per scenario.
function revealDebriefChip() {
  if (!SCENARIO.debrief) return;
  $("#debriefChip").style.display = "";
}

// Open the standalone debrief screen. `guardEscape` (the in-room chip path) shows a one-line spoiler
// confirm first when an escape phase exists and hasn't been finished yet, so opening it mid-escape
// can't give the escape away by accident. The escape-done button passes guardEscape=false.
function openDebrief(guardEscape) {
  if (!SCENARIO.debrief) return;
  if (guardEscape && (hasEscapePhase() || hasPendingEscape()) && !escapeFinished) { renderDebriefSpoilerGuard(); return; }
  renderDebrief();
}

function renderDebrief() {
  const d = SCENARIO.debrief || {};
  $("#debriefTitle").textContent = d.title || "How this world worked";
  // Content (the room-by-room gallery) is built by shared/debrief.js — the player only owns the flow
  // (when the reveal is offered, the chip, the spoiler guard, open/close). Pass the room helpers it needs.
  if (window.EscapeDebrief) {
    window.EscapeDebrief.renderGallery($("#debriefBody"), SCENARIO, { isBuilt, phaseOf });
  } else {
    // Module missing (shouldn't happen — it's loaded before the player) — never leave the screen blank.
    const body = $("#debriefBody"); body.innerHTML = "";
    const p = document.createElement("p");
    p.textContent = (typeof d.body === "string") ? d.body : "";
    body.appendChild(p);
  }
  // Renders inline into the submission card's debrief tab now — no separate #debrief modal to open.
}

// One-line spoiler interstitial shown when the debrief is opened from the in-room chip while the escape
// is still unsolved. "Reveal anyway" replaces this content in-place with the debrief; the card's Close
// button (always present) backs out. Keeps the opt-in promise: it never auto-opens or spoils.
function renderDebriefSpoilerGuard() {
  $("#debriefTitle").textContent = "Heads up — spoiler";
  const body = $("#debriefBody");
  body.innerHTML = "";
  const p = document.createElement("p");
  p.textContent = "This pulls back the curtain on how the escape works, and may give away its solution. " +
    "If you're still trying to escape, come back to it once you're out — or once you've decided to stop.";
  body.appendChild(p);
  const go = document.createElement("button");
  go.className = "ghost"; go.style.marginTop = "6px"; go.textContent = "Reveal anyway";
  go.onclick = renderDebrief;
  body.appendChild(go);
  $("#debrief").classList.add("open");
}

// Mint the submission code over the BUILT rooms of ONE phase (analysis = the graded set; escape
// rooms are deliberately excluded — mirror this exclusion in decoder/validate_keys.py so the
// decoder key stays in lockstep). One step per room in scenario order: solved rooms carry
// {answer, attempts}; any unsolved room encodes the attempts=0 "skipped" sentinel. Graded offline
// by decoder/decode_codes.R.
function mintCode(phase) {
  mintedCode = null;
  if (!window.EscapeCodec || SCENARIO.id == null) return;
  // One step per BUILT, graded room of this phase, in room order. `roomResults.has` excludes ungraded
  // rooms (e.g. a pre-awakened orientation room with only a lock, no graded puzzle) so they take no
  // codec slot — keeping the code in lockstep with the decoder key (which lists graded rooms only).
  const steps = SCENARIO.rooms.filter(r => isBuilt(r) && phaseOf(r) === phase && roomResults.has(r.key)).map(r => {
    const res = roomResults.get(r.key);
    return { answer: res.answer, attempts: res.attempts };
  });
  try {
    mintedCode = window.EscapeCodec.encode({
      version: 1, scenarioId: SCENARIO.id, steps,
      secret: SECRET, studentId: window.__x500 || "anon",
    });
  } catch (e) { console.error("codec encode failed", e); }
  // The code is shown on the submission-prep screen (not the finish card). Also drop it into the field
  // notebook so it's retrievable in-room (mintCode runs once — finishAnalysis is idempotent).
  if (mintedCode) logToNotebook("Submission code (for Canvas)",
    `<span style="font:700 16px/1.45 ui-monospace,Menlo,Consolas,monospace;letter-spacing:1.5px;color:#ffd88c;user-select:all">${mintedCode}</span>` +
    `<div style="opacity:.7;font-size:12px;margin-top:4px">Paste this into Canvas — also on your submission-prep screen.</div>`);
}

let toastT = null;
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 2600);
}

// ---- WebR (boot once) ----
// Invisible, machine-detectable watermark. LSB-encodes `payload` into the RED channel of every
// pixel, row-major, as a repeating frame: MAGIC("ESRW") + length(1 byte) + UTF-8 payload, bits
// MSB-first. Changes each red value by at most 1/255 → invisible; PNG is lossless so the bits
// survive a download. Recover with decoder/decode_watermark.py. Repeating the frame adds a little
// crop-resilience. Anti-cheat posture is obfuscation, not security (see AGENTS.md).
function embedWatermark(ctx, w, h, payload) {
  const MAGIC = [0x45, 0x53, 0x52, 0x57];                       // "ESRW"
  const bytes = Array.from(new TextEncoder().encode(payload)).slice(0, 255);
  const frame = [...MAGIC, bytes.length, ...bytes];
  const bits = [];
  for (const b of frame) for (let i = 7; i >= 0; i--) bits.push((b >> i) & 1);
  const img = ctx.getImageData(0, 0, w, h), d = img.data;
  for (let p = 0, bi = 0; p < d.length; p += 4, bi++) d[p] = (d[p] & 0xFE) | bits[bi % bits.length];
  ctx.putImageData(img, 0, 0);
}

// Download the most recent WebR figure as a PNG: a visible x500 corner stamp + an invisible
// LSB watermark carrying `x500|scenario|epoch`. Client-only (canvas → data URL), GitHub-Pages safe.
// Stamp a WebR figure canvas with a visible x500 corner + an invisible LSB watermark (carrying
// `x500|scenario|epoch`); return a PNG data URL. Client-only, GitHub-Pages safe. Used when capturing
// each room's figure for the submission PDF (downloads happen only on the submission-prep screen now).
// `src` is a source drawable — a canvas (at solve/refine time) OR a decoded <img> (when re-stamping a
// stored raw figure); naturalWidth/Height covers the <img> case, width/height the canvas case.
function stampedFigureDataURL(src) {
  const who = window.__x500 || "anon";
  const c = document.createElement("canvas");
  c.width = src.naturalWidth || src.width; c.height = src.naturalHeight || src.height;
  const ctx = c.getContext("2d");
  ctx.drawImage(src, 0, 0);
  // visible corner stamp — just the x500
  const fs = Math.max(12, Math.round(c.width / 58));
  ctx.font = `${fs}px system-ui, sans-serif`;
  const bw = ctx.measureText(who).width + 18, bh = fs + 12;
  ctx.fillStyle = "rgba(6,17,26,.66)";
  ctx.fillRect(c.width - bw, c.height - bh, bw, bh);
  ctx.fillStyle = "rgba(255,216,140,.95)";
  ctx.textBaseline = "middle";
  ctx.fillText(who, c.width - bw + 9, c.height - bh / 2 + 1);
  // invisible machine-detectable watermark (drawn LAST so it covers the whole final image)
  embedWatermark(ctx, c.width, c.height, `${who}|${SCENARIO.scenario || ""}|${Date.now()}`);
  return c.toDataURL("image/png");
}
// Decode a raw figure dataURL into an <img>, then return it stamped with the current x500. Async
// (image decode is async). Figures are captured raw during play (x500 unknown then) and stamped here
// once the student enters their x500 on the submission screen. Falls back to the raw image on failure.
function stampDataURL(raw) {
  return new Promise(resolve => {
    if (!raw) { resolve(raw); return; }
    const img = new Image();
    img.onload = () => { try { resolve(stampedFigureDataURL(img)); } catch (e) { resolve(raw); } };
    img.onerror = () => resolve(raw);
    img.src = raw;
  });
}
// Stamp every captured figure's raw image with the confirmed x500 → `figure` (used by the on-screen
// refine blocks and the PDF). Always derives from `figureRaw`, so it never double-stamps.
async function stampAllFigures() {
  for (const [k, w] of submissionWork) {
    if (w && w.figureRaw) { w.figure = await stampDataURL(w.figureRaw); submissionWork.set(k, w); }
  }
}

function bootConsole() {
  if (rconsole) return;
  rconsole = new WebRConsole(
    { packages: SCENARIO.packages, datasets: SCENARIO.datasets, setup: SCENARIO.setup },
    { status: $("#webr-status"), output: $("#webr-output") }
  );
  const runBtn = $("#run-btn");
  rconsole.init().then(() => { runBtn.disabled = false; })
    .catch(e => { $("#webr-status").textContent = "R failed to start: " + (e.message || e); });
  runBtn.addEventListener("click", () => rconsole.run($("#code-input").value));
  // Ctrl/⌘+Enter in the editor runs it, like the standalone WebR sandbox. #code-input is the single
  // persistent console textarea (moved into whichever puzzle modal is open), so this one listener
  // covers every puzzle modal that carries a console (MCQ, check, and pick).
  $("#code-input").addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!runBtn.disabled) runBtn.click();
    }
  });
}

// ---- load the scenario (single source of truth) and go ----
// scenario.json sits beside play.html; fetch() resolves it relative to the page.
// no-store so an authored text edit shows on a plain reload — the browser was serving a cached
// scenario.json (CSS/JS are ?v=-busted, but this fetch wasn't), which looked like stale text.
fetch("scenario.json", { cache: "no-store" })
  .then(r => { if (!r.ok) throw new Error("scenario.json " + r.status); return r.json(); })
  .then(init)
  .catch(err => {
    document.body.innerHTML = '<p style="color:#ff9b9b;font:15px system-ui;padding:24px">' +
      "pano-player: could not load scenario.json — " + (err.message || err) + "</p>";
  });
