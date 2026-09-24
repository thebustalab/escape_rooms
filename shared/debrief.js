/*
 * debrief.js — the exit-debrief "how this world worked" gallery for the WebR escape rooms.
 *
 * WHAT IT IS
 *   A scenario-agnostic, static, in-room pedagogical closer: a scrollable room-by-room gallery that
 *   pulls back the curtain on how the world, its language, and its data were built to embody the
 *   technique the student just practised. pano-player.js owns the FLOW — when the reveal is offered
 *   (once the graded analysis is complete), the opt-in chip, the spoiler guard, open/close. This
 *   module owns only the CONTENT: given the scenario, it builds the gallery DOM. Split out because the
 *   player is already large and this is self-contained. Loaded as a classic script before the player
 *   (like codec.js), exposing window.EscapeDebrief.
 *
 * TWO SHAPES. The LADDER shape (preferred, Lucas 2026-09-23) is one world plate plus a numbered,
 * PLAIN-LANGUAGE line per puzzle rung saying what the player actually did, then the escape in the same
 * register. It fires whenever `scenario.ladderPlain` is a non-empty array. Everything else still gets
 * the older room-by-room GALLERY, so the scenarios not yet converted keep rendering exactly as before —
 * six of them are shipped and student-facing, and a hard cutover would have blanked all six.
 *
 * WHY THE LADDER SHAPE. A row per room re-tells the story in the story's own voice, which is the one
 * thing a debrief must not do: the student has just finished the fiction and needs to be told, flatly,
 * which analysis they performed. So the rung lines are deliberately unthemed — no shrines, no springs,
 * just "you filtered, you grouped, you cut the tree into three" — and where a rung carries a taught
 * trap the line says so positively: the answer was right, and a later rung shows what it hid.
 *
 * DATA IT READS
 *   scenario.ladderPlain : [ { room?, text } | string ]   the plain rung lines, in ladder order
 *   scenario.escapeBrief : string                    the escape, in the same plain register. NOTE this
 *                      field used to be author-only ("for us, not the player"); it became PLAYER-FACING
 *                      on 2026-09-23 at Lucas's call, and the harness label changed with it. Anything
 *                      written there is now read by students.
 *   scenario.worldPlate  : string                    the shared backdrop, shown once at the top
 *   scenario.debrief : { title?, intro? }            screen heading + an optional lead paragraph
 *   room.debrief     : string | { heading?, body }   per BUILT room — the text shown beside that
 *                      room's scene. The escape room's debrief is where the escape is framed as the
 *                      real-world version of the analysis lesson.
 *   Each built room's `panorama` (a path relative to play.html, same as the player uses) is shown as
 *   the scene image; a room's puzzle prompt is surfaced automatically above the authored text, so
 *   "each puzzle" is named in place without re-authoring it.
 *
 * Rooms are walked in scenario order (analysis, then boss, then escape) — every BUILT room carrying a
 * `debrief` gets a gallery row. If no room carries one, it falls back to the scenario-level freeform
 * body/sections (the pre-gallery shape) so older authoring still renders something.
 */
(function () {
  function el(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }

  // The prompt of a room's first graded puzzle, if any — shown (muted) so each puzzle is named in
  // place. Covers every puzzle shape: MCQ (question), console (check), map-pick and plot-pick (pick/map).
  function puzzlePrompt(room) {
    var hs = (room && room.hotspots) || [];
    for (var i = 0; i < hs.length; i++) {
      var h = hs[i];
      if (h.type !== "puzzle") continue;
      if (h.question && h.question.prompt) return h.question.prompt;
      if (h.check && h.check.prompt) return h.check.prompt;
      if (h.pick && h.pick.prompt) return h.pick.prompt;
      if (h.map && h.map.instructions) return h.map.instructions;
    }
    return "";
  }

  // Resolve a room.debrief (string or {heading,body}) into { heading, body } (or null if absent/empty).
  function roomText(room) {
    var d = room && room.debrief;
    if (!d) return null;
    if (typeof d === "string") return d.trim() ? { heading: "", body: d } : null;
    var body = d.body || d.text || "";
    return body ? { heading: d.heading || d.title || "", body: body } : null;
  }

  // Fallback (pre-gallery) renderer: scenario-level freeform string or list of sections.
  function renderFreeform(bodyEl, debrief) {
    var sections = Array.isArray(debrief.sections) ? debrief.sections
                 : Array.isArray(debrief.body) ? debrief.body : null;
    if (sections) {
      sections.forEach(function (s) {
        var sec = el("div", "dbsec");
        var heading = (s && typeof s === "object") ? (s.heading || s.title || "") : "";
        var text = (typeof s === "string") ? s : ((s && (s.body || s.text)) || "");
        if (heading) { var h = el("h3"); h.textContent = heading; sec.appendChild(h); }
        var p = el("p"); p.textContent = text; sec.appendChild(p);
        bodyEl.appendChild(sec);
      });
    } else {
      var p = el("p"); p.textContent = (typeof debrief.body === "string") ? debrief.body : "";
      bodyEl.appendChild(p);
    }
  }

  // Normalise scenario.ladderPlain into [{ text }] — tolerates bare strings and drops empties.
  function ladderLines(scenario) {
    var raw = scenario && scenario.ladderPlain;
    if (!Array.isArray(raw)) return [];
    var out = [];
    for (var i = 0; i < raw.length; i++) {
      var e = raw[i];
      var t = (typeof e === "string") ? e : ((e && (e.text || e.body)) || "");
      t = (t || "").trim();
      if (t) out.push({ text: t });
    }
    return out;
  }

  // THE LADDER SHAPE — world plate, then one plain numbered line per rung, then the escape.
  function renderLadder(bodyEl, scenario, lines) {
    var debrief = scenario.debrief || {};
    if (debrief.intro) {
      var intro = el("p", "dbintro"); intro.textContent = debrief.intro; bodyEl.appendChild(intro);
    }
    // The plate, or the COVER if the scenario has none. The three oldest scenarios (alaska, hawaii,
    // hospital) predate the world-plate convention entirely, and the ladder shape has only this one
    // image — without a fallback their debrief would open on nothing at all, which is worse than the
    // gallery it replaced. Any scenario built since has a plate and never reaches the fallback.
    var plate = scenario.worldPlate || scenario.cover;
    if (plate) {
      var img = el("img", "dbplate");
      img.src = plate; img.alt = scenario.title || ""; img.loading = "lazy";
      bodyEl.appendChild(img);
    }
    var h = el("h3", "dbladderh"); h.textContent = "What you did"; bodyEl.appendChild(h);
    var ol = el("ol", "dbladder");
    lines.forEach(function (l) { var li = el("li"); li.textContent = l.text; ol.appendChild(li); });
    bodyEl.appendChild(ol);
    var esc = (scenario.escapeBrief || "").trim();
    if (esc) {
      var h2 = el("h3", "dbladderh"); h2.textContent = "And to get out"; bodyEl.appendChild(h2);
      var p = el("p", "dbescape"); p.textContent = esc; bodyEl.appendChild(p);
    }
  }

  // Build the debrief content into bodyEl. helpers = { isBuilt, phaseOf } supplied by the player.
  function renderGallery(bodyEl, scenario, helpers) {
    bodyEl.innerHTML = "";
    var debrief = scenario.debrief || {};
    var isBuilt = helpers.isBuilt;

    var lines = ladderLines(scenario);
    if (lines.length) { renderLadder(bodyEl, scenario, lines); return; }

    if (debrief.intro) {
      var intro = el("p", "dbintro"); intro.textContent = debrief.intro; bodyEl.appendChild(intro);
    }

    var rooms = (scenario.rooms || []).filter(function (r) { return isBuilt(r) && roomText(r); });
    if (!rooms.length) { renderFreeform(bodyEl, debrief); return; }   // pre-gallery fallback

    rooms.forEach(function (r) {
      var t = roomText(r);
      var row = el("div", "dbroom");
      if (r.panorama) {
        var img = el("img", "dbshot");
        img.src = r.panorama; img.alt = r.title || r.key || ""; img.loading = "lazy";
        row.appendChild(img);
      }
      var txt = el("div", "dbtext");
      var h = el("h3"); h.textContent = t.heading || r.title || r.key || ""; txt.appendChild(h);
      var pz = puzzlePrompt(r);
      if (pz) { var q = el("p", "dbpuzzle"); q.textContent = pz; txt.appendChild(q); }
      var p = el("p"); p.textContent = t.body; txt.appendChild(p);
      row.appendChild(txt);
      bodyEl.appendChild(row);
    });
  }

  window.EscapeDebrief = { renderGallery: renderGallery };
})();
