// puzzle_cards.js — shared puzzle/clue/lock editor CARDS, used by BOTH puzzle_edit.html (the
// standalone all-rooms editor) and harness_gpt.html's inline story-map content section, so the
// card UI can't drift between them (Phase 2b, 2026-07-21).
// EscapePuzzleCards.make(ctx) -> { roomCardsInto(host, spots, roomKey) }.
//   ctx = { esc, getJSON, postJSON, chapter, scenario }
//   getJSON(path)->Promise<json>, postJSON(path,body)->Promise<json>  (each handles its own cache-buster)
window.EscapePuzzleCards = (function () {
  function make(ctx) {
    const esc = ctx.esc, getJSON = ctx.getJSON, postJSON = ctx.postJSON;
    const CH = ctx.chapter, SC = ctx.scenario;
    const SCQ = (CH && SC) ? ("chapter=" + encodeURIComponent(CH) + "&scenario=" + encodeURIComponent(SC)) : "";
    const linesToArr = s => String(s || "").split("\n").filter(x => x.trim().length);
    const arrToLines = a => (a || []).join("\n");
    const csvToArr = s => String(s || "").split(",").map(x => x.trim()).filter(Boolean);
    const arrToCsv = a => (a || []).join(", ");
    const checkSkel = () => ({ prompt:"", requires:[], expr:"", hint:"", maxAttempts:4, feedback:{ correct:"", wrong:[], reveal:"" } });
    const questionSkel = () => ({ prompt:"", options:[], correct:0, maxAttempts:4, feedback:{ correct:"", wrong:[], reveal:"" } });

    // solve / door-open sound — an optional per-gate one-shot the player plays when this is solved (a graded
    // puzzle OR a lock releasing). Stored on the hotspot as `solveSfx` = a path string, or { src, volume }.
    // A path (relative to play.html) + optional volume + an inline preview; reused by the puzzle & lock cards.
    function solveSfxHTML() {
      return `<div class="lbl" style="margin-top:12px">solve sound <span class="hint" style="text-transform:none">· optional — plays once when this is solved / the door opens. Audition the staged candidates and pick one, or type a path.</span></div>
        <div class="sscands"></div>
        <div class="hr" style="margin-top:6px"><input type="text" data-ss="src" placeholder="audio/door_open.mp3">
          <label style="width:auto;flex:none">vol</label><input type="number" data-ss="vol" min="0" max="1" step="0.05" style="max-width:70px" placeholder="0.9"></div>
        <audio class="ssprev" controls preload="none" style="height:28px;width:100%;margin-top:4px;display:none"></audio>`;
    }
    function wireSolveSfx(el, s, roomKey) {
      const srcEl = el.querySelector('[data-ss="src"]'), volEl = el.querySelector('[data-ss="vol"]'),
            prev = el.querySelector(".ssprev"), cands = el.querySelector(".sscands");
      const cur = s.solveSfx;
      srcEl.value = (typeof cur === "string") ? cur : (cur && cur.src) || "";
      volEl.value = (cur && typeof cur === "object" && cur.volume != null) ? cur.volume : "";
      const showPrev = () => {
        const src = srcEl.value.trim();
        if (src) { prev.src = "/sfile/" + src + (SCQ ? "?" + SCQ : ""); prev.style.display = ""; }
        else { prev.removeAttribute("src"); prev.style.display = "none"; }
      };
      const markSel = () => {
        const chosen = srcEl.value.trim().split("/").pop();
        cands.querySelectorAll("[data-cf]").forEach(r =>
          r.style.borderColor = (chosen && r.dataset.cf === chosen) ? "var(--amber)" : "transparent");
      };
      const sync = () => {
        const src = srcEl.value.trim();
        if (!src) { delete s.solveSfx; showPrev(); markSel(); return; }
        const v = parseFloat(volEl.value);
        s.solveSfx = !isNaN(v) ? { src, volume: v } : src;
        showPrev(); markSel();
      };
      srcEl.oninput = sync; volEl.oninput = sync;
      showPrev();
      loadSolveCands(cands, s, roomKey, srcEl, sync, markSel);
    }
    // Per-gate solve-sound candidates: any _scratch/audio/ mp3 named `solve_<roomKey>_<gateId>_*.mp3`.
    // Audition each, "Use this" materialises it into the committed audio/ (/api/commit-sound) and sets
    // this gate's solveSfx. Mirrors the room-sfx candidate flow (harness Step 6), but sets a single sound.
    async function loadSolveCands(cands, s, roomKey, srcEl, sync, markSel) {
      const prefix = "solve_" + roomKey + "_" + s.id + "_";
      cands.innerHTML = `<div class="hint" style="margin:2px 0">loading candidates…</div>`;
      const r = await getJSON("/api/audio-candidates" + (SCQ ? "?" + SCQ : ""));
      const mine = ((r && r.files) || []).filter(f => f.startsWith(prefix));
      if (!mine.length) {
        cands.innerHTML = `<div class="hint" style="margin:2px 0">no candidate sounds staged — they land in <code>_scratch/audio/</code> as <code>${esc(prefix)}*.mp3</code>. Type a path below meanwhile.</div>`;
        return;
      }
      cands.innerHTML = "";
      mine.forEach(f => {
        const row = document.createElement("div");
        row.dataset.cf = f;
        row.style.cssText = "display:flex;align-items:center;gap:6px;margin-top:6px;flex-wrap:wrap;border:2px solid transparent;border-radius:8px;padding:3px";
        row.innerHTML =
          `<audio controls preload="none" style="height:30px;max-width:170px" src="/sfile/_scratch/audio/${encodeURIComponent(f)}${SCQ ? "?" + SCQ : ""}"></audio>
           <button class="useCand" type="button" style="margin:0">Use this</button>
           <span class="hint" style="margin:0;flex-basis:100%">${esc(f)}</span>`;
        const btn = row.querySelector(".useCand");
        btn.onclick = async () => {
          btn.textContent = "…";
          const res = await postJSON("/api/commit-sound", { chapter: CH, scenario: SC, file: f });
          if (!res.ok) { btn.textContent = "failed"; return; }
          btn.textContent = "Use this";
          srcEl.value = res.src; sync();   // sets solveSfx + preview + highlight
        };
        cands.appendChild(row);
      });
      markSel();
    }

    function feedbackFields(prefix) {
      return `<div class="fb"><div class="lbl">feedback — correct <span class="hint" style="text-transform:none">· shown on solve AND logged verbatim to the field notebook — keep it short and name the answer (e.g. “Correct — noted: warmest lake is Lava_Lake”)</span></div><textarea data-${prefix}f="correct" rows="2"></textarea>
        <div class="lbl">feedback — wrong (one hint per line, shown per attempt)</div><textarea data-${prefix}f="wrong" rows="3"></textarea>
        <div class="lbl">feedback — reveal (after last attempt)</div><textarea data-${prefix}f="reveal" rows="2"></textarea></div>`;
    }
    function wireFeedback(root, prefix, fb) {
      root.querySelector(`[data-${prefix}f="correct"]`).value = fb.correct || "";
      root.querySelector(`[data-${prefix}f="wrong"]`).value = arrToLines(fb.wrong);
      root.querySelector(`[data-${prefix}f="reveal"]`).value = fb.reveal || "";
      root.querySelector(`[data-${prefix}f="correct"]`).oninput = e => { fb.correct = e.target.value; };
      root.querySelector(`[data-${prefix}f="wrong"]`).oninput = e => { fb.wrong = linesToArr(e.target.value); };
      root.querySelector(`[data-${prefix}f="reveal"]`).oninput = e => { fb.reveal = e.target.value; };
    }

    function renderGradeFields(host, s, mode) {
      host.innerHTML = "";
      if (mode === "check") {
        const c = s.check; c.feedback = c.feedback || { correct:"", wrong:[], reveal:"" };
        host.innerHTML =
          `<div class="lbl">prompt (HTML ok)</div><textarea data-ck="prompt" rows="3"></textarea>
           <div class="hr"><label>requires</label><input type="text" data-ck="requires" placeholder="answer  (vars that must exist, comma-separated)"></div>
           <div class="lbl">expr — one R logical, run against the student's session</div><textarea data-ck="expr" class="mono" rows="2"></textarea>
           <div class="hr"><label>hint</label><input type="text" data-ck="hint"></div>
           <div class="hr"><label>max tries</label><input type="number" data-ck="maxAttempts" min="1" max="7" style="max-width:70px"></div>
           ${feedbackFields("ck")}`;
        host.querySelector('[data-ck="prompt"]').value = c.prompt || "";
        host.querySelector('[data-ck="requires"]').value = arrToCsv(c.requires);
        host.querySelector('[data-ck="expr"]').value = c.expr || "";
        host.querySelector('[data-ck="hint"]').value = c.hint || "";
        host.querySelector('[data-ck="maxAttempts"]').value = c.maxAttempts || 4;
        host.querySelector('[data-ck="prompt"]').oninput = e => { c.prompt = e.target.value; };
        host.querySelector('[data-ck="requires"]').oninput = e => { c.requires = csvToArr(e.target.value); };
        host.querySelector('[data-ck="expr"]').oninput = e => { c.expr = e.target.value; };
        host.querySelector('[data-ck="hint"]').oninput = e => { c.hint = e.target.value; };
        host.querySelector('[data-ck="maxAttempts"]').oninput = e => { c.maxAttempts = +e.target.value || 4; };
        wireFeedback(host, "ck", c.feedback);
      } else {
        const q = s.question; q.feedback = q.feedback || { correct:"", wrong:[], reveal:"" };
        host.innerHTML =
          `<div class="lbl">prompt (HTML ok)</div><textarea data-q="prompt" rows="3"></textarea>
           <div class="lbl">options (one per line)</div><textarea data-q="options" rows="4"></textarea>
           <div class="hr"><label>correct #</label><input type="number" data-q="correct" min="0" style="max-width:70px"> <span class="hint">0-based index into the options</span></div>
           <div class="hr"><label>max tries</label><input type="number" data-q="maxAttempts" min="1" max="7" style="max-width:70px"></div>
           ${feedbackFields("q")}`;
        host.querySelector('[data-q="prompt"]').value = q.prompt || "";
        host.querySelector('[data-q="options"]').value = arrToLines(q.options);
        host.querySelector('[data-q="correct"]').value = q.correct || 0;
        host.querySelector('[data-q="maxAttempts"]').value = q.maxAttempts || 4;
        host.querySelector('[data-q="prompt"]').oninput = e => { q.prompt = e.target.value; };
        host.querySelector('[data-q="options"]').oninput = e => { q.options = linesToArr(e.target.value); };
        host.querySelector('[data-q="correct"]').oninput = e => { q.correct = +e.target.value || 0; };
        host.querySelector('[data-q="maxAttempts"]').oninput = e => { q.maxAttempts = +e.target.value || 4; };
        wireFeedback(host, "q", q.feedback);
      }
    }

    // lock card — the no-instructions keypad gate (escape objective). Code + feedback only; box/type/
    // label stay in Edit hotspots. A lock is NEVER graded and never enters the submission code.
    function lockCard(s, roomKey) {
      s.feedback = s.feedback || {};
      const el = document.createElement("div"); el.className = "puz";
      el.innerHTML =
        `<h2>Lock · <span>${esc(s.id)}</span> <span class="hint" style="text-transform:none">${esc(s.label || "")}</span></h2>
         <div class="hint">A no-instructions keypad. The student must bring the code (synthesised from earlier rooms) — no prompt is shown. Not graded; never enters the submission code.</div>
         <div class="hr"><label>answer (code)</label><input type="text" data-l="answer" placeholder="e.g. NWNL"></div>
         <div class="hr"><label>length</label><input type="number" data-l="length" min="1" max="12" style="max-width:70px"> <span class="hint">keypad slots · blank = length of the answer</span></div>
         <div class="hr"><label>max tries</label><input type="number" data-l="maxAttempts" min="0" max="20" style="max-width:70px"> <span class="hint">0 or blank = unlimited</span></div>
         <div class="fb"><div class="lbl">feedback — correct (on solve)</div><textarea data-lf="correct" rows="2"></textarea>
           <div class="lbl">feedback — wrong (on a wrong code)</div><textarea data-lf="wrong" rows="2"></textarea>
           <div class="lbl">feedback — out (if max tries is hit)</div><textarea data-lf="out" rows="2"></textarea></div>
         ${solveSfxHTML()}`;
      el.querySelector('[data-l="answer"]').value = s.answer || "";
      el.querySelector('[data-l="length"]').value = s.length || "";
      el.querySelector('[data-l="maxAttempts"]').value = s.maxAttempts || "";
      el.querySelector('[data-l="answer"]').oninput = e => { s.answer = e.target.value; };
      el.querySelector('[data-l="length"]').oninput = e => { const v = +e.target.value; if (v) s.length = v; else delete s.length; };
      el.querySelector('[data-l="maxAttempts"]').oninput = e => { const v = +e.target.value; if (v) s.maxAttempts = v; else delete s.maxAttempts; };
      el.querySelector('[data-lf="correct"]').value = s.feedback.correct || "";
      el.querySelector('[data-lf="wrong"]').value = s.feedback.wrong || "";
      el.querySelector('[data-lf="out"]').value = s.feedback.out || "";
      el.querySelector('[data-lf="correct"]').oninput = e => { s.feedback.correct = e.target.value; };
      el.querySelector('[data-lf="wrong"]').oninput = e => { s.feedback.wrong = e.target.value; };
      el.querySelector('[data-lf="out"]').oninput = e => { s.feedback.out = e.target.value; };
      wireSolveSfx(el, s, roomKey);
      return el;
    }

    // clue card — body text + optional "can be picked up" (adds an opt-in Add-to-notebook button in
    // play). box/type/label stay in Edit hotspots. `pickup`: false = not collectable; true = logs the
    // clue body; a string = logs that exact (concise) text.
    function clueCard(s, roomKey) {
      const el = document.createElement("div"); el.className = "puz";
      el.innerHTML =
        `<h2>Clue · <span>${esc(s.id)}</span> <span class="hint" style="text-transform:none">${esc(s.label || "")}</span></h2>
         <div class="lbl">clue image <span class="hint" style="text-transform:none">· optional — generate an artwork with GPT; shown above the text in play (exact numbers/shapes can be unreliable — check the result)</span></div>
         <div class="climgprev"></div>
         <textarea data-c="imgPrompt" rows="3" placeholder="Describe the artwork to generate…"></textarea>
         <div class="hr" style="margin-top:6px">
           <button class="genImg" type="button">Generate ×2</button>
           <button class="clrImg" type="button" style="background:transparent;border:1px solid var(--line);color:var(--ink);font-weight:400">Clear image</button>
           <span class="hint imgStat" style="margin-left:4px"></span>
         </div>
         <div class="climgcands" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px"></div>
         <div class="lbl" style="margin-top:12px">clue body (HTML ok) <span class="hint" style="text-transform:none">· optional if there's an image</span></div>
         <textarea data-c="body" rows="5"></textarea>
         <label class="lbl" style="display:flex;align-items:center;gap:7px;text-transform:none;margin-top:8px">
           <input type="checkbox" data-c="pickupOn"> can be picked up &amp; added to the field notebook</label>
         <div class="lbl" style="text-transform:none">notebook text <span class="hint" style="text-transform:none">· blank = log the clue body; enter a short line to log that instead</span></div>
         <textarea data-c="pickupText" rows="2" placeholder="e.g. Beacon manual: a long-lived signal means warm water."></textarea>`;
      const body = el.querySelector('[data-c="body"]');
      const on = el.querySelector('[data-c="pickupOn"]');
      const ptxt = el.querySelector('[data-c="pickupText"]');
      body.value = s.body || "";
      on.checked = !!s.pickup;
      ptxt.value = (typeof s.pickup === "string") ? s.pickup : "";
      ptxt.disabled = !on.checked;             // initial disabled state only — don't mutate untouched clues
      const syncPickup = () => {               // writes s.pickup on a real user change
        ptxt.disabled = !on.checked;
        if (!on.checked) { s.pickup = false; return; }
        const t = ptxt.value.trim();
        s.pickup = t ? t : true;               // true = log the body; string = log that text
      };
      body.oninput = e => { s.body = e.target.value; };
      on.onchange = syncPickup;
      ptxt.oninput = syncPickup;
      // ---- clue image (GPT-generated artwork) ----
      const prev = el.querySelector(".climgprev"), stat = el.querySelector(".imgStat"), cands = el.querySelector(".climgcands");
      const promptEl = el.querySelector('[data-c="imgPrompt"]');
      promptEl.value = s.imagePrompt || "";
      promptEl.oninput = e => { s.imagePrompt = e.target.value; };
      const showPrev = () => {
        prev.innerHTML = s.image
          ? `<img src="/sfile/${s.image}${SCQ ? "?" + SCQ : ""}&t=${Date.now()}" style="max-width:100%;border:1px solid var(--line);border-radius:8px;margin-bottom:6px">`
          : `<div class="hint" style="margin:0 0 6px">no image — generate one, or leave the clue text-only.</div>`;
      };
      showPrev();
      el.querySelector(".clrImg").onclick = () => {
        delete s.image; delete s.imageFrom; markPickedClue(cands, null); showPrev();
        stat.textContent = "cleared — Save to apply";
      };
      const genBtn = el.querySelector(".genImg");
      genBtn.onclick = () => genClueImage(s, roomKey, promptEl.value, stat, cands, showPrev, genBtn);
      // Show any existing _scratch candidates straight away (like the scene grid persists), so
      // reopening the editor still lists them and the committed pick stays highlighted.
      if (roomKey) renderClueCands(s, roomKey, cands, stat, showPrev);
      return el;
    }

    // generate a clue's artwork with gpt-image-2, poll, then show candidates to pick from.
    // While the job runs the button goes the "working" blue (busy) — no numeric progress text needed.
    async function genClueImage(s, roomKey, prompt, stat, cands, showPrev, btn) {
      prompt = (prompt || "").trim();
      if (!prompt) { stat.innerHTML = `<span class="err">enter a prompt first</span>`; return; }
      if (!roomKey) { stat.innerHTML = `<span class="err">no room key — reopen from a room</span>`; return; }
      s.imagePrompt = prompt;
      const setBusy = (on) => { if (btn) { btn.classList.toggle("busy", on); btn.disabled = on; } };
      const done = (html) => { setBusy(false); stat.innerHTML = html; };
      setBusy(true); stat.textContent = "";
      const r = await postJSON("/api/gen-clue-image", { chapter: CH, scenario: SC, roomKey, clueId: s.id, prompt });
      if (!r.ok) { done(`<span class="err">${r.error || "failed"}</span>`); return; }
      const poll = setInterval(async () => {
        const j = await getJSON("/api/status?slot=" + encodeURIComponent(r.slot));
        if (!j) return;
        if (j.error) { clearInterval(poll); done(`<span class="err">${j.error}</span>`); return; }
        if (!j.active) { clearInterval(poll); done(`<span class="ok2">done — pick one below</span>`); renderClueCands(s, roomKey, cands, stat, showPrev); }
      }, 1500);
    }
    async function renderClueCands(s, roomKey, cands, stat, showPrev) {
      const r = await getJSON(`/api/clue-candidates?chapter=${encodeURIComponent(CH)}&scenario=${encodeURIComponent(SC)}&roomKey=${encodeURIComponent(roomKey)}&clueId=${encodeURIComponent(s.id)}`);
      cands.innerHTML = "";
      ((r && r.files) || []).forEach(f => {
        const card = document.createElement("div");
        card.className = "climgcand"; card.dataset.file = f;
        card.style.cssText = "cursor:pointer;border:2px solid transparent;border-radius:8px;overflow:hidden";
        card.innerHTML = `<img src="/sfile/_scratch/${encodeURIComponent(f)}${SCQ ? "?" + SCQ : ""}&t=${Date.now()}" style="width:100%;display:block">`;
        card.onclick = () => pickClueImage(s, roomKey, f, cands, stat, showPrev);
        cands.appendChild(card);
      });
      markPickedClue(cands, s.imageFrom);   // keep the committed candidate highlighted (mirrors the scene grid's .sel)
    }
    // highlight the candidate that's committed (by _scratch filename); null clears all
    function markPickedClue(cands, file) {
      cands.querySelectorAll("[data-file]").forEach(card => {
        card.style.borderColor = (file && card.dataset.file === file) ? "var(--amber)" : "transparent";
      });
    }
    async function pickClueImage(s, roomKey, file, cands, stat, showPrev) {
      stat.textContent = "setting…";
      const r = await postJSON("/api/set-clue-image", { chapter: CH, scenario: SC, roomKey, clueId: s.id, file });
      if (!r.ok) { stat.innerHTML = `<span class="err">${r.error}</span>`; return; }
      // commit the pick (server copied _scratch/<file> -> <room>/clue_<id>.png) and remember WHICH
      // candidate it was, so the grid stays put and highlights it — like a scene's builtFrom/Save chip.
      s.image = r.src; s.imageFrom = file; markPickedClue(cands, file); showPrev();
      stat.innerHTML = `<span class="ok2">image set ✓ — committed to the room folder · Save to apply</span>`;
    }

    // append the editable cards (puzzle / clue / lock) for ONE room's hotspots into `host`
    function roomCardsInto(host, spots, roomKey) {
      const editable = spots.filter(s => s.type === "puzzle" || s.type === "clue" || s.type === "lock");
      if (!editable.length) {
        host.insertAdjacentHTML("beforeend", `<div class="none" style="padding:10px">No puzzle, clue or lock hotspots here yet — add them in <b>Edit hotspots</b> (draw a box, set its type), then reload.</div>`);
        return;
      }
      editable.forEach(s => {
        if (s.type === "clue") { host.appendChild(clueCard(s, roomKey)); return; }
        if (s.type === "lock") { host.appendChild(lockCard(s, roomKey)); return; }
        if (!s.check && !s.question) s.check = checkSkel();
        const mode = s.check ? "check" : "question";
        const el = document.createElement("div"); el.className = "puz";
        el.innerHTML =
          `<h2>Puzzle · <span>${esc(s.id)}</span> <span class="hint" style="text-transform:none">${esc(s.label || "")}</span></h2>
           <div class="lbl">starter code (R, pre-filled in the console)</div>
           <textarea data-c="starterCode" class="mono" rows="6"></textarea>
           <div class="hr" style="margin-top:10px"><label>grading</label>
             <select class="gmode"><option value="check"${mode==="check"?" selected":""}>console-check (grade live R)</option><option value="question"${mode==="question"?" selected":""}>multiple-choice</option></select></div>
           <div class="gfields"></div>
           ${solveSfxHTML()}`;
        el.querySelector('[data-c="starterCode"]').value = s.starterCode || "";
        el.querySelector('[data-c="starterCode"]').oninput = e => { s.starterCode = e.target.value; };
        el.querySelector(".gmode").onchange = e => {
          if (e.target.value === "check") { delete s.question; s.check = s.check || checkSkel(); }
          else { delete s.check; s.question = s.question || questionSkel(); }
          renderGradeFields(el.querySelector(".gfields"), s, e.target.value);
        };
        host.appendChild(el);
        renderGradeFields(el.querySelector(".gfields"), s, mode);
        wireSolveSfx(el, s, roomKey);
      });
    }
    return { roomCardsInto };
  }
  return { make };
})();
