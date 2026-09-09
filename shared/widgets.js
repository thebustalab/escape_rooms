// Card builders for the two 2026-08-26 hotspot types, split out of pano-player.js so the DOM layer is
// reachable from a Playwright fixture (tests/e2e/widgets.spec.js) without booting a whole scenario:
// the engine's own state — the gate key, the attempt counter, the lock table, the world-state bag — is
// INJECTED as `ctx` rather than read from module scope. pano-player passes its real objects; the test
// passes plain ones.
import { confirmGroups, confirmAll } from "./ledger_rule.js?v=89";
import { makeScale, junctionsAbove, placedCount } from "./elev_scale.js?v=89";

export function buildLedgerCard(h, onSolved, ctx) {
  const rows = h.rows || [];
  // all-or-nothing: no per-group locking, no progress line — see confirmAll() for why beacons needs it
  const allOrNothing = !!h.allOrNothing;
  const opts = (h.options || []).map(o => (typeof o === "string") ? { key: o, label: o } : o);
  const fbk = h.feedback || {};
  const maxA = h.maxAttempts || 0;                    // 0 = unlimited (the escape is ungraded)
  const pid = ctx.pid;
  const attemptCounts = ctx.attemptCounts, ledgerLocks = ctx.locks;
  let attempts = attemptCounts.get(pid) || 0;
  const locked = ledgerLocks.get(pid) || new Set();
  ledgerLocks.set(pid, locked);

  // True membership per verdict, derived from the rows' own answers.
  const truth = new Map();
  rows.forEach(r => {
    if (!truth.has(r.answer)) truth.set(r.answer, new Set());
    truth.get(r.answer).add(r.id);
  });
  const groupCount = truth.size;

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const card = document.createElement("div"); card.className = "qcard ledgercard";
  card.innerHTML =
    (h.prompt ? `<div class="qprompt">${h.prompt}</div>` : "") +
    `<table class="ledger"><tbody>` +
      rows.map(r => `<tr data-row="${esc(r.id)}"><th class="rowlab">${esc(r.label)}</th>` +
        `<td><select class="verdict" data-row="${esc(r.id)}" aria-label="${esc(r.label)}">` +
          `<option value="">—</option>` +
          opts.map(o => `<option value="${esc(o.key)}">${esc(o.label)}</option>`).join("") +
        `</select></td></tr>`).join("") +
    `</tbody></table>` +
    `<div class="ledgerprog"></div><div class="qfeedback"></div>` +
    `<button class="qsubmit">Check the ledger</button>`;

  const fb = card.querySelector(".qfeedback");
  const prog = card.querySelector(".ledgerprog");
  const sub = card.querySelector(".qsubmit");
  const sels = () => Array.from(card.querySelectorAll("select.verdict"));

  const progText = () => allOrNothing ? "" : (fbk.progress || "{n} of {m} groups confirmed")
    .replace("{n}", String(locked.size)).replace("{m}", String(groupCount));

  // Re-lock the rows of any group already confirmed in an earlier visit, and paint them.
  const paintLocks = () => {
    sels().forEach(s => {
      const row = rows.find(r => r.id === s.dataset.row);
      if (row && locked.has(row.answer)) {
        s.value = row.answer; s.disabled = true;
        s.closest("tr").classList.add("locked");
      }
    });
    prog.textContent = progText();
  };
  paintLocks();

  sels().forEach(s => s.addEventListener("change", () => { fb.className = "qfeedback"; fb.innerHTML = ""; }));

  const submit = () => {
    attempts++; attemptCounts.set(pid, attempts);
    // Current assignment, then group-by-group exact match. Nothing is reported per row — only which
    // GROUPS closed on this press, which is the whole point.
    const verdict = {};
    sels().forEach(s => { if (s.value) verdict[s.dataset.row] = s.value; });
    const res = allOrNothing ? confirmAll(rows, verdict) : confirmGroups(rows, verdict, locked);
    const newly = res.newly;
    newly.forEach(v => locked.add(v));
    if (!allOrNothing) paintLocks();

    if (allOrNothing ? res.complete : locked.size === groupCount) {
      fb.className = "qfeedback ok";
      fb.innerHTML = fbk.correct || "Every group confirmed.";
      card.querySelectorAll("select, button").forEach(b => b.disabled = true);
      setTimeout(() => onSolved({ answer: 1, attempts }), 900);
      return;
    }
    if (newly.length) {
      fb.className = "qfeedback ok";
      fb.innerHTML = fbk.partial || "That group holds together. The rest do not — yet.";
    } else if (maxA && attempts >= maxA) {
      fb.className = "qfeedback out";
      fb.innerHTML = fbk.out || "The ledger closes.";
      card.querySelectorAll("select, button").forEach(b => b.disabled = true);
    } else {
      // Deliberately says NOTHING about which rows are wrong.
      fb.className = "qfeedback no";
      fb.innerHTML = fbk.wrong || "No group closes. A group confirms only when every one of its members is right — and nothing else is claiming to be one of them.";
    }
  };
  sub.addEventListener("click", submit);
  return card;
}


export function buildElevmapCard(h, ctx) {
  const ax = h.axis || {};
  const lo = Number(ax.min != null ? ax.min : 0), hi = Number(ax.max != null ? ax.max : 100);
  const span = (hi - lo) || 1;
  const step = Number(ax.step || 0);
  const unit = ax.unit || "";
  const nodes = h.nodes || [];
  const stateKey = h.key || h.id;
  const countKey = h.countKey || "heights_placed";
  const gameState = ctx.gameState;
  const placed = (gameState[stateKey] && typeof gameState[stateKey] === "object")
    ? gameState[stateKey] : (gameState[stateKey] = {});

  const H = 300, PADT = 14, PADB = 26, PLOT = H - PADT - PADB;
  const SC = makeScale({ min: lo, max: hi, step, height: H, padTop: PADT, padBottom: PADB });
  const yFor = SC.yFor, vFor = SC.vFor, snap = SC.snap;

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const card = document.createElement("div"); card.className = "qcard elevmapcard";
  card.innerHTML =
    (h.prompt ? `<div class="qprompt">${h.prompt}</div>` : "") +
    `<div class="elevplot" style="height:${H}px">` +
      `<div class="elevaxis"></div>` +
      (h.waterline && h.waterline.enabled ? `<div class="waterline" tabindex="0"><span class="wlab"></span></div>` : "") +
      nodes.map(n => `<div class="elevnode" data-node="${esc(n.id)}" style="left:${(Number(n.x) || 0) * 100}%">` +
        `<span class="ndot"></span><span class="nlab">${esc(n.label)}</span><span class="nval"></span></div>`).join("") +
    `</div>` +
    `<div class="elevfoot"><span class="elevprog"></span>` +
      (ax.label ? `<span class="elevunit">${esc(ax.label)}${unit ? " (" + esc(unit) + ")" : ""}</span>` : "") +
    `</div>`;

  const plot = card.querySelector(".elevplot");
  const prog = card.querySelector(".elevprog");

  // Axis ticks — five evenly spaced gridlines, so the scale is readable and a cut can be eyeballed.
  const axis = card.querySelector(".elevaxis");
  for (let i = 0; i <= 4; i++) {
    const v = lo + span * (i / 4);
    const t = document.createElement("div");
    t.className = "elevtick"; t.style.top = yFor(v) + "px";
    t.innerHTML = `<span>${snap(v)}</span>`;
    axis.appendChild(t);
  }

  const countPlaced = () => placedCount(nodes, placed);
  const refreshProg = () => {
    prog.textContent = (h.feedback && h.feedback.placed || "{n} of {m} heights marked")
      .replace("{n}", String(countPlaced())).replace("{m}", String(nodes.length));
    gameState[countKey] = countPlaced();      // the counter ordinary gates read
  };

  const nodeEls = new Map();
  nodes.forEach(n => {
    const el = card.querySelector(`.elevnode[data-node="${CSS.escape(n.id)}"]`);
    nodeEls.set(n.id, el);
    const avail = !n.requires || !!gameState[n.requires];
    if (!avail) el.classList.add("unread");
    const v = placed[n.id];
    el.style.top = (v != null ? yFor(v) : (PADT + PLOT)) + "px";
    el.querySelector(".nval").textContent = v != null ? (v + (unit ? " " + unit : "")) : (avail ? "—" : "?");

    if (!avail) return;                        // not yet read out in the world: shown, but not draggable
    el.classList.add("draggable");
    const move = (clientY) => {
      const r = plot.getBoundingClientRect();
      const y = Math.max(PADT, Math.min(PADT + PLOT, clientY - r.top));
      const val = snap(vFor(y));
      placed[n.id] = val;
      el.style.top = yFor(val) + "px";
      el.querySelector(".nval").textContent = val + (unit ? " " + unit : "");
      if (n.answer != null) {
        const tol = Number(n.tol != null ? n.tol : 0);
        el.classList.toggle("onmark", Math.abs(val - Number(n.answer)) <= tol);
      }
      refreshProg();
      if (wl) paintWaterline();
    };
    el.addEventListener("pointerdown", (ev) => {
      ev.preventDefault(); el.setPointerCapture(ev.pointerId); el.classList.add("dragging");
      const onMove = e => move(e.clientY);
      const onUp = e => {
        el.classList.remove("dragging");
        el.removeEventListener("pointermove", onMove);
        el.removeEventListener("pointerup", onUp);
        try { el.releasePointerCapture(ev.pointerId); } catch (_) {}
      };
      el.addEventListener("pointermove", onMove);
      el.addEventListener("pointerup", onUp);
      move(ev.clientY);
    });
    // Keyboard: the drag must not be the only way in (phones aside, this is also the accessible path).
    el.tabIndex = 0;
    el.addEventListener("keydown", (ev) => {
      const d = step > 0 ? step : Math.max(1, Math.round(span / 100));
      if (ev.key === "ArrowUp") { move(yFor((placed[n.id] != null ? placed[n.id] : lo) + d) + plot.getBoundingClientRect().top); ev.preventDefault(); }
      if (ev.key === "ArrowDown") { move(yFor((placed[n.id] != null ? placed[n.id] : lo) - d) + plot.getBoundingClientRect().top); ev.preventDefault(); }
    });
  });

  // Optional waterline: a draggable horizontal rule. It reports how many separate groups the current
  // cut leaves — reading a dendrogram cut off your own plotted tree, which is the whole lesson.
  const wl = card.querySelector(".waterline");
  let wlVal = (h.waterline && h.waterline.start != null) ? Number(h.waterline.start) : lo + span / 2;
  function paintWaterline() {
    if (!wl) return;
    wl.style.top = yFor(wlVal) + "px";
    const above = junctionsAbove(nodes, placed, wlVal);
    wl.querySelector(".wlab").textContent =
      `${(h.waterline.label || "waterline")} ${snap(wlVal)}${unit ? " " + unit : ""} — ${above} junction${above === 1 ? "" : "s"} still above it`;
  }
  if (wl) {
    paintWaterline();
    const wmove = (clientY) => {
      const r = plot.getBoundingClientRect();
      const y = Math.max(PADT, Math.min(PADT + PLOT, clientY - r.top));
      wlVal = snap(vFor(y)); paintWaterline();
    };
    wl.addEventListener("pointerdown", (ev) => {
      ev.preventDefault(); wl.setPointerCapture(ev.pointerId);
      const onMove = e => wmove(e.clientY);
      const onUp = () => { wl.removeEventListener("pointermove", onMove); wl.removeEventListener("pointerup", onUp); };
      wl.addEventListener("pointermove", onMove); wl.addEventListener("pointerup", onUp);
      wmove(ev.clientY);
    });
    wl.addEventListener("keydown", (ev) => {
      const d = step > 0 ? step : Math.max(1, Math.round(span / 100));
      if (ev.key === "ArrowUp") { wlVal = snap(wlVal + d); paintWaterline(); ev.preventDefault(); }
      if (ev.key === "ArrowDown") { wlVal = snap(wlVal - d); paintWaterline(); ev.preventDefault(); }
    });
  }
  refreshProg();
  return card;
}

