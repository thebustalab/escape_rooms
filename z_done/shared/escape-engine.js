/*
 * escape-engine.js — drives an escape-room scenario in one of two modes.
 *
 * LINEAR mode (window.SCENARIO.steps): the original two-screen flow — a fixed
 * sequence of multiple-choice steps, one after another. Used by alaska/.
 *
 * GRAPH / hub-and-spoke mode (window.SCENARIO.nodes): several independent
 * "spoke" puzzles the student can tackle in any order, plus one "boss" node
 * (the chapter's new technique) gated behind resolving N of the M spokes. The
 * boss is a FIGURE task — graded by hand — so the code only records that the
 * student reached it. See z_design_history/hub_and_spoke_design_notes.md.
 *
 * Both modes produce a Canvas submission code via window.EscapeCodec. The
 * graph code serialises spokes in canonical NODE order (not solve order), so a
 * skipped spoke encodes as attempts=0, and a trailing boss byte records
 * whether the figure was produced.
 */
import { WebRConsole } from "./webr-console.js";
import { MapView } from "./map-view.js";

const SECRET = "chem5725-noatak-2026"; // change per course; obfuscation only
const VERSION = 1;
const PASTE_WARN_CHARS = 40;

const S = window.SCENARIO;
const state = { studentId: "", steps: [], current: 0 };       // linear mode
const graph = { results: {}, cards: {}, bossReached: false, active: null }; // graph mode
const journey = { i: 0, results: {}, bossReached: false };  // journey / chain mode
const explore = { r: 0, v: 0, results: {}, cards: {} };      // explore / pano-rooms mode
let cardSeq = 0;      // unique radio-group names per question card
let mapView = null;   // MapView instance (graph mode only)

document.addEventListener("DOMContentLoaded", () => {
  buildScreen1();
});

/* ---------- Screen 1: the story ---------- */
function buildScreen1() {
  document.getElementById("scenario-title").textContent = S.title;
  const img = document.getElementById("scene-image");
  img.src = S.screen1.image;
  img.onerror = () => { img.style.display = "none"; };
  document.getElementById("scene-heading").textContent = S.screen1.title;
  document.getElementById("scene-story").innerHTML = S.screen1.story;
  const enterBtn = document.getElementById("enter-btn");
  enterBtn.textContent = S.screen1.enterLabel || "Enter →";

  const idInput = document.getElementById("student-id");
  enterBtn.addEventListener("click", () => {
    const id = idInput.value.trim();
    if (!id) {
      document.getElementById("id-error").textContent =
        "Please enter your x500 first — it ties your code to you.";
      return;
    }
    state.studentId = id;
    startMusic(); // triggered by this click, so autoplay is allowed
    enterWorkroom();
  });
}

/* ---------- Ambience ---------- */
function startMusic() {
  if (!S.music) return;
  const audio = document.getElementById("ambience");
  audio.src = S.music;
  audio.volume = typeof S.musicVolume === "number" ? S.musicVolume : 0.35;
  audio.loop = true;
  audio.play().catch(() => { /* some browsers still block; the toggle recovers it */ });

  const toggle = document.getElementById("music-toggle");
  toggle.classList.add("show");
  toggle.addEventListener("click", () => {
    if (audio.paused) { audio.play(); toggle.textContent = "♪ on"; }
    else { audio.pause(); toggle.textContent = "♪ off"; }
  });
}

/* ---------- Screen 2: the workroom ---------- */
async function enterWorkroom() {
  document.getElementById("screen1").classList.remove("active");
  document.getElementById("screen2").classList.add("active");
  window.scrollTo(0, 0);

  if (S.keepBackground && S.screen1.image) {
    const bg = document.getElementById("screen2-bg");
    bg.style.backgroundImage = "url('" + S.screen1.image + "')";
    bg.classList.add("show");
  }

  document.getElementById("briefing").innerHTML = S.briefing;

  const input = document.getElementById("code-input");
  input.value = S.starterCode || "";
  wirePasteWarning(input);

  const consoleUI = {
    status: document.getElementById("webr-status"),
    output: document.getElementById("webr-output"),
  };
  const rconsole = new WebRConsole(
    { packages: S.packages, datasets: S.datasets, setup: S.setup },
    consoleUI
  );

  const runBtn = document.getElementById("run-btn");
  runBtn.disabled = true;
  rconsole.init()
    .then(() => { runBtn.disabled = false; })
    .catch((e) => { consoleUI.status.textContent = "R failed to start: " + e.message; });

  runBtn.addEventListener("click", () => rconsole.run(input.value));

  if (S.flow === "explore" && Array.isArray(S.rooms)) renderExplore();
  else if (S.flow === "journey" && Array.isArray(S.nodes)) renderJourney();
  else if (Array.isArray(S.nodes)) renderGraph();
  else renderStep();
}

function wirePasteWarning(input) {
  const banner = document.getElementById("paste-banner");
  input.addEventListener("paste", (e) => {
    const text = (e.clipboardData || window.clipboardData).getData("text");
    if (text && text.length > PASTE_WARN_CHARS) {
      banner.classList.add("show");
      clearTimeout(banner._t);
      banner._t = setTimeout(() => banner.classList.remove("show"), 8000);
    }
    // paste is allowed — we only nudge.
  });
  document.getElementById("paste-dismiss").addEventListener("click", () => {
    banner.classList.remove("show");
  });
}

/* ---------- A single multiple-choice card (shared by both modes) ----------
 * q: { prompt, options, correct, maxAttempts, feedback:{correct,wrong[],reveal} }
 * onResolved(answerIndex, attempts, solved) fires once, when the card reaches a
 * terminal state (correct, or attempts exhausted). `solved` is true only when
 * the student picked the correct option.
 */
function makeQuestionCard(q, label, onResolved) {
  const maxAttempts = q.maxAttempts || 4;
  let attempts = 0;
  let selected = -1;
  const group = "qopt-" + (cardSeq++);

  const card = document.createElement("div");
  card.className = "step-card";
  card.innerHTML = `
    <div class="step-number">${label}</div>
    <div class="step-prompt">${q.prompt}</div>
    <div class="step-options"></div>
    <div class="step-feedback"></div>
    <button class="submit-btn" disabled>Submit answer</button>
  `;

  const optionsEl = card.querySelector(".step-options");
  const feedbackEl = card.querySelector(".step-feedback");
  const submitBtn = card.querySelector(".submit-btn");

  q.options.forEach((opt, i) => {
    const label2 = document.createElement("label");
    label2.className = "option";
    label2.innerHTML = `<input type="radio" name="${group}" value="${i}"> <span>${opt}</span>`;
    label2.querySelector("input").addEventListener("change", () => {
      selected = i;
      submitBtn.disabled = false;
    });
    optionsEl.appendChild(label2);
  });

  function lockCard() {
    optionsEl.querySelectorAll("input").forEach((el) => (el.disabled = true));
    submitBtn.disabled = true;
    submitBtn.style.display = "none";
  }

  submitBtn.addEventListener("click", () => {
    if (selected < 0) return;
    attempts += 1;
    if (selected === q.correct) {
      feedbackEl.className = "step-feedback ok";
      feedbackEl.innerHTML = q.feedback.correct;
      lockCard();
      setTimeout(() => onResolved(selected, attempts, true), 700);
    } else if (attempts >= maxAttempts) {
      feedbackEl.className = "step-feedback out";
      feedbackEl.innerHTML = q.feedback.reveal || "Moving on.";
      lockCard();
      setTimeout(() => onResolved(selected, attempts, false), 700);
    } else {
      feedbackEl.className = "step-feedback no";
      const hints = q.feedback.wrong || [];
      const hint = hints[Math.min(attempts - 1, hints.length - 1)] ||
        "Not quite — take another look at the data and try again.";
      feedbackEl.innerHTML =
        hint + ` <span class="attempts-left">(attempt ${attempts} of ${maxAttempts})</span>`;
    }
  });

  return card;
}

/* ---------- LINEAR mode ---------- */
function renderStep() {
  const container = document.getElementById("steps");
  const idx = state.current;

  if (idx >= S.steps.length) {
    emitCode(state.steps);
    return;
  }
  const step = S.steps[idx];
  const card = makeQuestionCard(
    step,
    `Question ${idx + 1} of ${S.steps.length}`,
    (answer, attempts) => {
      state.steps.push({ answer, attempts });
      state.current += 1;
      renderStep();
    }
  );
  container.appendChild(card);
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- GRAPH / hub-and-spoke mode ---------- */
function spokeNodes() { return S.nodes.filter((n) => n.type === "spoke"); }
function bossNode() { return S.nodes.find((n) => n.type === "boss"); }
function resolvedCount() {
  return spokeNodes().filter((n) => graph.results[n.key] && graph.results[n.key].resolved).length;
}
function gateRequires() {
  return (S.bossGate && typeof S.bossGate.requires === "number")
    ? S.bossGate.requires : spokeNodes().length;
}
function gateMet() { return resolvedCount() >= gateRequires(); }

function renderGraph() {
  const mapEl = document.getElementById("node-map");
  mapView = new MapView({
    mapEl: mapEl,
    nodes: S.nodes,
    scene: !!(S.scene && S.scene.image),
    background: S.scene && S.scene.image,
    status: nodeStatus,
    gate: () => ({
      resolved: resolvedCount(),
      requires: gateRequires(),
      total: spokeNodes().length,
      met: gateMet(),
    }),
    onOpen: openDetail,
  });
  mapView.render();
}

// The status a node presents on the map (drives styling + fog clarity).
function nodeStatus(node) {
  if (node.type === "spoke") {
    const r = graph.results[node.key];
    return (r && r.resolved) ? "resolved" : "open";
  }
  // boss
  if (!gateMet()) return "locked";
  return graph.bossReached ? "resolved" : "ready";
}

// Open a node's detail as an overlay over the map.
function openDetail(node) {
  graph.active = node.key;
  const detail = document.getElementById("node-detail");
  detail.innerHTML = "";

  const back = document.createElement("button");
  back.className = "detail-back";
  back.innerHTML = "← Back to the map";
  back.addEventListener("click", closeDetail);
  detail.appendChild(back);

  if (node.type === "spoke") {
    // Cache the card so attempts persist if a student leaves a lead and returns
    // — reopening must not silently reset the attempt counter.
    let card = graph.cards[node.key];
    if (!card) {
      card = makeQuestionCard(node, node.title, (answer, attempts, solved) => {
        graph.results[node.key] = { answer, attempts, solved, resolved: true };
        if (mapView) mapView.update();
        setTimeout(closeDetail, 900); // let the feedback land, then back to the map
      });
      graph.cards[node.key] = card;
    }
    detail.appendChild(card);
  } else {
    detail.appendChild(makeBossCard(node));
  }

  detail.classList.add("open");
}

function closeDetail() {
  const detail = document.getElementById("node-detail");
  detail.classList.remove("open");
  graph.active = null;
}

function makeBossCard(node, onRecord) {
  // The figure download + x500/code watermark are still to come (deferred).
  const card = document.createElement("div");
  card.className = "step-card boss-card";
  card.innerHTML = `
    <div class="step-number">Final challenge${node.technique ? " — " + node.technique : ""}</div>
    <div class="step-prompt">${node.brief || ""}</div>
    ${node.figureSpec ? `<div class="figure-spec"><strong>Your figure must show:</strong> ${node.figureSpec}</div>` : ""}
    <div class="boss-placeholder">Build your figure in the R console on the left.
      <em>(Placeholder — the “Download your figure” button and the x500 + code
      watermark are still to come.)</em></div>
    <button class="submit-btn boss-record">I’ve produced my figure — record it &amp; finish</button>
  `;
  card.querySelector(".boss-record").addEventListener("click", () => {
    if (onRecord) { onRecord(); return; }
    graph.bossReached = true;
    if (mapView) mapView.update();
    closeDetail();
    finishGraph();
  });
  return card;
}

/* ---------- JOURNEY / chain-of-rooms mode ----------
 * Rooms are worked in order. Each is its own scene; solving a room's MC (the
 * product of the analysis) unlocks a door onward. The last room is the boss —
 * the figure deliverable. Later chapters simply list more rooms.
 */
function journeySpokes() { return S.nodes.filter((n) => n.type !== "boss"); }

function renderJourney() {
  const mapEl = document.getElementById("node-map");
  mapEl.classList.add("map-ready", "scene", "journey");
  mapEl.innerHTML =
    '<div class="map-bg"></div>' +
    '<div class="room-caption"></div>' +
    '<button class="journey-door" hidden></button>';
  showRoom(0);
}

function showRoom(i) {
  journey.i = i;
  const node = S.nodes[i];
  const mapEl = document.getElementById("node-map");
  if (node.scene) {
    mapEl.querySelector(".map-bg").style.backgroundImage = "url('" + node.scene + "')";
  }
  const total = journeySpokes().length;
  mapEl.querySelector(".room-caption").innerHTML = node.type === "boss"
    ? "Final task — " + node.title
    : "Case " + (i + 1) + " of " + total + " — " + node.title;

  // Refresh the console's starter code for this room, if it brings its own.
  if (node.starterCode) {
    const input = document.getElementById("code-input");
    if (input) input.value = node.starterCode;
  }

  mapEl.querySelector(".journey-door").hidden = true;
  openRoomIntro(node);
}

function openRoomIntro(node) {
  const detail = document.getElementById("node-detail");
  detail.innerHTML = "";
  const card = document.createElement("div");
  card.className = "step-card";
  card.innerHTML =
    '<div class="step-number">' + (node.type === "boss" ? "Final task" : (node.technique || "")) + "</div>" +
    '<div class="step-prompt">' + (node.intro || node.brief || "") + "</div>" +
    '<button class="submit-btn room-begin">' +
      (node.type === "boss" ? "Take on the final task" : "Begin the analysis") + "</button>";
  detail.appendChild(card);
  card.querySelector(".room-begin").addEventListener("click", () => openRoomPuzzle(node));
  detail.classList.add("open");
}

function openRoomPuzzle(node) {
  const detail = document.getElementById("node-detail");
  detail.innerHTML = "";

  if (node.type === "boss") {
    detail.appendChild(makeBossCard(node, () => {
      journey.bossReached = true;
      detail.classList.remove("open");
      finishJourney();
    }));
    detail.classList.add("open");
    return;
  }

  const card = makeQuestionCard(node, node.title, (answer, attempts, solved) => {
    journey.results[node.key] = { answer, attempts, solved, resolved: true };
    detail.classList.remove("open"); // step back into the scene to find the door
    revealDoor();
  });
  detail.appendChild(card);
  detail.classList.add("open");
}

function revealDoor() {
  const mapEl = document.getElementById("node-map");
  const door = mapEl.querySelector(".journey-door");
  const nextNode = S.nodes[journey.i + 1];
  door.textContent = (nextNode && nextNode.type === "boss")
    ? "Approach the final task →" : "Travel onward →";
  door.hidden = false;
  door.onclick = () => showRoom(journey.i + 1);
}

function finishJourney() {
  const steps = journeySpokes().map((n) => {
    const r = journey.results[n.key];
    return r ? { answer: r.answer, attempts: r.attempts } : { answer: 0, attempts: 0 };
  });
  steps.push({ answer: journey.bossReached ? 1 : 0, attempts: 0 }); // boss byte
  emitCode(steps);
}

/* ---------- EXPLORE / pannable multi-room mode ----------
 * A case is several rooms worked in order. Each room is a set of "views"
 * (images) the student pans between with left/right arrows. Each room has
 * clickable artifacts on its views — some are flavour clues, one is the real
 * multiple-choice question. Solving a room's question opens the door onward;
 * the last room ends the case. Encodes one answer per room + a trailing byte.
 */
function exploreRoom() { return S.rooms[explore.r]; }
function exploreRoomSolved(room) { return !!explore.results[room.key]; }

function renderExplore() {
  const mapEl = document.getElementById("node-map");
  mapEl.classList.add("map-ready", "pano");
  mapEl.innerHTML =
    '<div class="pano-fill"></div>' +
    '<div class="pano-bg"></div>' +
    '<canvas class="pano-canvas"></canvas>' +
    '<div class="pano-artifacts"></div>' +
    '<button class="pano-arrow left" aria-label="pan left">‹</button>' +
    '<button class="pano-arrow right" aria-label="pan right">›</button>' +
    '<div class="room-caption"></div>' +
    '<div class="view-dots"></div>' +
    '<button class="journey-door" hidden></button>';
  mapEl.querySelector(".pano-arrow.left").addEventListener("click", () => panView(-1));
  mapEl.querySelector(".pano-arrow.right").addEventListener("click", () => panView(1));
  window.addEventListener("resize", exploreResize);
  showRoomExplore(0);
}

function exploreResize() {
  if (S.flow !== "explore" || !S.rooms) return;
  const room = S.rooms[explore.r];
  if (room && room.panorama) showPanoFacing(room);
}

/* ---- panorama rooms: slice + draw a facing live on a canvas ---- */
const panoCache = {};
function loadImg(url) {
  return new Promise((resolve, reject) => {
    if (panoCache[url]) { resolve(panoCache[url]); return; }
    const im = new Image();
    im.onload = () => { panoCache[url] = im; resolve(im); };
    im.onerror = reject;
    im.src = url;
  });
}

function facingRectFor(img, facing, n, slice) {
  const iw = img.width, ih = img.height;
  const cropH = Math.min(slice.cropHeight || ih, ih);
  const top = Math.floor((ih - cropH) / 2);
  const step = iw / n;
  const half = (step + (slice.overlap || 0)) / 2;
  const c = (facing + 0.5) * step;
  const x0 = Math.max(0, Math.round(c - half));
  const x1 = Math.min(iw, Math.round(c + half));
  return { sx: x0, sy: top, sw: x1 - x0, sh: cropH };
}

function drawPanoFacing(canvas, img, facing, n, slice, blur) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const W = rect.width, H = rect.height;
  if (!W || !H) return;
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);

  const r = facingRectFor(img, facing, n, slice);
  const scale = Math.min(W / r.sw, H / r.sh); // contain
  const dw = r.sw * scale, dh = r.sh * scale;
  const dx = (W - dw) / 2, dy = (H - dh) / 2;

  ctx.filter = "blur(" + (blur || 26) + "px)";
  const fcover = Math.max(W / r.sw, H / r.sh);
  ctx.drawImage(img, r.sx, r.sy, r.sw, r.sh, (W - r.sw * fcover) / 2, (H - r.sh * fcover) / 2, r.sw * fcover, r.sh * fcover);
  const bandDx = dx - r.sx * scale;
  ctx.drawImage(img, 0, r.sy, img.width, r.sh, bandDx, dy, img.width * scale, r.sh * scale);
  ctx.filter = "none";
  ctx.fillStyle = "rgba(6,14,20,0.28)";
  ctx.fillRect(0, 0, W, H);
  ctx.drawImage(img, r.sx, r.sy, r.sw, r.sh, dx, dy, dw, dh);
}

function showRoomExplore(r) {
  explore.r = r;
  explore.v = 0;
  const room = exploreRoom();
  if (room.starterCode) {
    const input = document.getElementById("code-input");
    if (input) input.value = room.starterCode;
  }
  if (room.panorama) {
    const urls = [room.panorama];
    if (room.panoramaOpen) urls.push(room.panoramaOpen);
    Promise.all(urls.map(loadImg)).then(() => {
      if (exploreRoom() === room) showViewExplore(); // ignore if we've since moved on
    }).catch(() => showViewExplore());
  } else {
    showViewExplore();
  }
}

function panView(d) {
  const room = exploreRoom();
  const n = room.panorama ? (room.facings || 4) : room.views.length;
  explore.v = (explore.v + d + n) % n;
  showViewExplore();
}

function showViewExplore() {
  const room = exploreRoom();
  if (room.panorama) { showPanoFacing(room); return; }

  const mapEl = document.getElementById("node-map");
  const view = room.views[explore.v];
  const solved = exploreRoomSolved(room);

  // background — a door view swaps to its open image once the room is solved.
  // .pano-fill sits behind as a blurred cover so tall slices don't hard-letterbox.
  const bgImg = (view.door && solved && view.openImage) ? view.openImage : view.image;
  if (bgImg) {
    const url = "url('" + bgImg + "')";
    mapEl.querySelector(".pano-bg").style.backgroundImage = url;
    const fill = mapEl.querySelector(".pano-fill");
    if (fill) fill.style.backgroundImage = url;
  }

  mapEl.querySelector(".room-caption").innerHTML =
    "Room " + (explore.r + 1) + " of " + S.rooms.length + " — " + room.title +
    '<span class="view-hint"> · use ‹ › to look around</span>';

  // view dots
  const dots = mapEl.querySelector(".view-dots");
  dots.innerHTML = "";
  room.views.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.className = "view-dot" + (i === explore.v ? " on" : "");
    dots.appendChild(dot);
  });

  // positioned artifacts on this view (hotspot style — used by non-pano rooms)
  const layer = mapEl.querySelector(".pano-artifacts");
  layer.innerHTML = "";
  (room.artifacts || []).forEach((art) => {
    if (art.view !== explore.v) return;
    const solvedQ = art.type === "question" && solved;
    const btn = document.createElement("button");
    btn.className = "artifact " + art.type + (solvedQ ? " solved" : "");
    btn.style.left = (art.pos ? art.pos.x : 50) + "%";
    btn.style.top = (art.pos ? art.pos.y : 55) + "%";
    btn.innerHTML =
      '<span class="artifact-dot"></span>' +
      '<span class="artifact-label">' + (art.label || (art.type === "question" ? "Examine" : "Clue")) + "</span>";
    btn.addEventListener("click", () => openArtifact(art, room));
    layer.appendChild(btn);
  });

  // per-view action button (pano rooms: one labelled action for this facing)
  const oldAction = mapEl.querySelector(".view-action-btn");
  if (oldAction) oldAction.remove();
  if (view.action) {
    const solvedQ = view.action.type === "question" && solved;
    const ab = document.createElement("button");
    ab.className = "view-action-btn " + view.action.type + (solvedQ ? " done" : "");
    ab.textContent = (solvedQ ? "✓ " : "") +
      (view.action.label || (view.action.type === "question" ? "Examine" : "Look"));
    ab.onclick = () => openArtifact(view.action, room);
    mapEl.appendChild(ab);
  }

  // advance control — on a room with a door view it lives ON the open door
  // (pan to it); on a door-less room it falls back to a generic button.
  const door = mapEl.querySelector(".journey-door");
  const hasDoorView = room.views.some((v) => v.door);
  const last = explore.r === S.rooms.length - 1;
  let showDoor = false;
  if (solved) {
    if (view.door) showDoor = true;
    else if (!hasDoorView) showDoor = true;
  }
  if (showDoor) {
    door.textContent = view.door ? (last ? "^ Step outside" : "^ Go through")
                                 : (last ? "Leave →" : "To the next room →");
    door.hidden = false;
    door.onclick = () => (last ? finishExplore() : showRoomExplore(explore.r + 1));
  } else {
    door.hidden = true;
  }
}

// A panorama room: draw the current facing on the canvas (with continuous blur),
// plus its caption / dots / action button / door — mirrors the views-PNG path.
function showPanoFacing(room) {
  const mapEl = document.getElementById("node-map");
  const nF = room.facings || 4;
  const solved = exploreRoomSolved(room);
  const isDoor = room.doorFacing != null && explore.v === room.doorFacing;

  const canvas = mapEl.querySelector(".pano-canvas");
  canvas.style.display = "block";
  mapEl.querySelector(".pano-bg").style.display = "none";
  mapEl.querySelector(".pano-fill").style.display = "none";

  const img = (isDoor && solved && room.panoramaOpen && panoCache[room.panoramaOpen])
    ? panoCache[room.panoramaOpen] : panoCache[room.panorama];
  if (img) drawPanoFacing(canvas, img, explore.v, nF, room.slice || {}, room.blur);

  mapEl.querySelector(".room-caption").innerHTML =
    "Room " + (explore.r + 1) + " of " + S.rooms.length + " — " + room.title +
    '<span class="view-hint"> · use ‹ › to look around</span>';

  const dots = mapEl.querySelector(".view-dots");
  dots.innerHTML = "";
  for (let i = 0; i < nF; i++) {
    const d = document.createElement("span");
    d.className = "view-dot" + (i === explore.v ? " on" : "");
    dots.appendChild(d);
  }
  mapEl.querySelector(".pano-artifacts").innerHTML = "";

  const oldAction = mapEl.querySelector(".view-action-btn");
  if (oldAction) oldAction.remove();
  const action = room.actions ? room.actions[explore.v] : null;
  if (action) {
    const solvedQ = action.type === "question" && solved;
    const ab = document.createElement("button");
    ab.className = "view-action-btn " + action.type + (solvedQ ? " done" : "");
    ab.textContent = (solvedQ ? "✓ " : "") +
      (action.label || (action.type === "question" ? "Examine" : "Look"));
    ab.onclick = () => openArtifact(action, room);
    mapEl.appendChild(ab);
  }

  const door = mapEl.querySelector(".journey-door");
  const last = explore.r === S.rooms.length - 1;
  if (solved && (isDoor || room.doorFacing == null)) {
    door.textContent = isDoor ? (last ? "^ Step outside" : "^ Go through")
                              : (last ? "Leave →" : "To the next room →");
    door.hidden = false;
    door.onclick = () => (last ? finishExplore() : showRoomExplore(explore.r + 1));
  } else {
    door.hidden = true;
  }
}

// The R console is a single live widget parked in #console-holder; a question
// pop-up borrows it (moving the DOM node preserves the booted WebR session and
// all wiring), and it goes back to the holder when the pop-up closes.
function mountConsole(target) {
  const block = document.getElementById("console-block");
  if (block && target) target.appendChild(block);
}
function unmountConsole() {
  const holder = document.getElementById("console-holder");
  const block = document.getElementById("console-block");
  if (holder && block) holder.appendChild(block);
}
function closeExploreDetail() {
  unmountConsole(); // return the console before the overlay is torn down/hidden
  document.getElementById("node-detail").classList.remove("open");
}

function openArtifact(art, room) {
  unmountConsole(); // safety: never let innerHTML = "" destroy the live console
  const detail = document.getElementById("node-detail");
  detail.innerHTML = "";

  const box = document.createElement("div");
  box.className = "modal-box";
  const back = document.createElement("button");
  back.className = "detail-back";
  back.innerHTML = "← Back to the room";
  back.addEventListener("click", closeExploreDetail);
  box.appendChild(back);

  if (art.type === "clue") {
    const card = document.createElement("div");
    card.className = "step-card";
    card.innerHTML =
      '<div class="step-number">' + (art.label || "Clue") + "</div>" +
      '<div class="step-prompt">' + (art.body || "") + "</div>";
    box.appendChild(card);
    detail.appendChild(box);
    detail.classList.add("open");
    return;
  }

  // question artifact — pops up the R console alongside the multiple choice
  if (art.starterCode) {
    const input = document.getElementById("code-input");
    if (input) input.value = art.starterCode;
  }
  if (exploreRoomSolved(room)) {
    const card = document.createElement("div");
    card.className = "step-card";
    card.innerHTML =
      '<div class="step-number">' + (art.label || "Solved") + "</div>" +
      '<div class="step-prompt">You have already answered this. The way onward is open.</div>';
    box.appendChild(card);
    detail.appendChild(box);
    detail.classList.add("open");
    return;
  }

  box.classList.add("wide");
  const grid = document.createElement("div");
  grid.className = "qa-grid";
  const consolePane = document.createElement("div");
  consolePane.className = "qa-console";
  mountConsole(consolePane);
  const qPane = document.createElement("div");
  qPane.className = "qa-question";
  let card = explore.cards[room.key];
  if (!card) {
    card = makeQuestionCard(art, art.label || room.title, (answer, attempts, solved) => {
      explore.results[room.key] = { answer, attempts, solved, resolved: true };
      closeExploreDetail(); // return to the room to find the door
      showViewExplore();
    });
    explore.cards[room.key] = card;
  }
  qPane.appendChild(card);
  grid.appendChild(consolePane);
  grid.appendChild(qPane);
  box.appendChild(grid);
  detail.appendChild(box);
  detail.classList.add("open");
}

function finishExplore() {
  const steps = S.rooms.map((room) => {
    const res = explore.results[room.key];
    return res ? { answer: res.answer, attempts: res.attempts } : { answer: 0, attempts: 0 };
  });
  steps.push({ answer: 0, attempts: 0 }); // reserved boss byte (no figure in this prototype)
  emitCode(steps);
}

function finishGraph() {
  // Serialise spokes in canonical node order; a skipped spoke -> attempts 0.
  const steps = spokeNodes().map((n) => {
    const r = graph.results[n.key];
    return r ? { answer: r.answer, attempts: r.attempts } : { answer: 0, attempts: 0 };
  });
  steps.push({ answer: graph.bossReached ? 1 : 0, attempts: 0 }); // boss byte
  emitCode(steps);
}

/* ---------- Finish: build the code (both modes) ---------- */
function emitCode(steps) {
  const code = window.EscapeCodec.encode({
    version: VERSION,
    scenarioId: S.id,
    steps: steps,
    studentId: state.studentId,
    secret: SECRET,
  });

  const panel = document.getElementById("finish");
  panel.classList.add("show");
  document.getElementById("final-code").textContent = code;
  document.getElementById("finish-body").innerHTML = S.finishMessage || "";
  panel.scrollIntoView({ behavior: "smooth" });

  document.getElementById("copy-code").addEventListener("click", () => {
    navigator.clipboard.writeText(code).then(() => {
      document.getElementById("copy-code").textContent = "Copied ✓";
    });
  });
}
