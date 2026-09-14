/*
 * webr_reset.js — "reset session": put the R session back exactly as it booted.
 *
 * THE CASE IT EXISTS FOR (Lucas, 2026-09-14): a student writes
 * `algae_data <- algae_data %>% filter(...)`, and the dataset the next puzzle/exercise needs is gone.
 * Reloading the page fixes it at the cost of a 20-90 s WebR boot AND whatever is in the editor — not
 * something to do mid-puzzle, and certainly not in front of a class.
 *
 * A SNAPSHOT RESTORE, NOT A REBOOT. At the end of boot — after the datasets, after view(), after the
 * caller's own `setup` — RESET_R_SHIM mget()s the whole global environment. A reset then empties
 * globalenv and list2env()s the snapshot back. R is copy-on-modify, so the snapshot costs references
 * rather than copies and a restore is instant: no network, no re-parse, no package re-install. It also
 * restores things this code knows nothing about, which is the point — a scenario's `setup` helpers and
 * the console's own view() shim come back without anything here enumerating them.
 *
 * Do NOT "simplify" it into replaying the boot sequence. Replaying means re-fetching datasets and
 * re-evaluating every shim, i.e. a second copy of init()'s logic that can drift from the first — the
 * exact failure the 2026-09-04 console consolidation existed to remove.
 *
 * PURE: no DOM, no CDN import, no WebR. Unit-tested in tests/webr_reset.test.mjs. (Same split as
 * webr_view.js and plot_size.js — logic that can be tested in Node lives outside webr-console.js.)
 */

/*
 * Two orderings below look odd and are load-bearing:
 *
 *  - `.__reset` is added to the snapshot AFTER it is defined, so a restore puts the reset function
 *    itself back and a SECOND reset still works. (`.__reset_env` is already in the mget because it was
 *    assigned before it; re-adding it is a harmless no-op that keeps the pair readable.)
 *
 *  - inside `.__reset`, `snap` is read into a LOCAL before the rm(). The rm deletes `.__reset_env` from
 *    globalenv, so a lookup after it would fail with "object not found"; the running closure survives
 *    because R holds the function while it executes.
 *
 * Both names are dot-prefixed, so a plain ls() keeps them out of the book sandbox's Environment pane
 * with no entry in that pane's hand-maintained exclusion list.
 */
export const RESET_R_SHIM = `
.__reset_env <- new.env()
.__reset_env$snap <- mget(ls(globalenv(), all.names = TRUE), envir = globalenv())
.__reset <- function() {
  g <- globalenv()
  snap <- .__reset_env$snap
  rm(list = ls(g, all.names = TRUE), envir = g)
  list2env(snap, envir = g)
  invisible(NULL)
}
.__reset_env$snap$.__reset_env <- .__reset_env
.__reset_env$snap$.__reset <- .__reset
`;

/*
 * The exists() guard is for skew, not for paranoia: the two book surfaces live in another repo and are
 * deployed separately, so a cached page can meet a session booted by a console that predates the shim.
 * A bare .__reset() call there throws an R error the student can do nothing with; FALSE lets the caller
 * say "reload the page" instead.
 */
export const RESET_R_CALL = 'if (exists(".__reset")) { .__reset(); TRUE } else FALSE';

/* How long an armed "click again to confirm" stays armed. */
export const RESET_CONFIRM_MS = 4000;

export const RESET_LABEL = "↺ reset session";
export const RESET_CONFIRM_LABEL = "click again to confirm";

/*
 * The two-step confirm, as a pure state machine so the expiry rule is testable without a browser.
 *
 * WHY confirm at all: a reset destroys every object the student has built. One stray click in a chapter
 * they have been working down for twenty minutes is a bad way to find that out. The editor's contents
 * survive a reset, so this protects the part that does NOT come back.
 *
 * WHY it expires: an armed button that stays armed for ever is a trap — the student clicks "reset",
 * gets distracted, comes back, clicks what they think is a fresh button and loses the session.
 *
 * `state` is `{ armedAt: number|null }`; `now` is a ms timestamp. Returns the next state plus the
 * action the caller should take.
 */
export function nextConfirmState(state, now, windowMs = RESET_CONFIRM_MS) {
  const armedAt = state && typeof state.armedAt === "number" ? state.armedAt : null;
  if (armedAt !== null && now - armedAt <= windowMs) {
    return { action: "reset", armedAt: null };
  }
  return { action: "arm", armedAt: now };
}

/*
 * Styled to inherit `currentColor`, like PLOT_CTL_CSS, so one control suits the sandbox's amber-on-navy
 * card, the puzzle modal's console block and the book's cell bar without a per-surface stylesheet.
 */
export const RESET_CTL_CSS = `
.webr-resetctl { font:12px system-ui, sans-serif; color:inherit; background:rgba(0,0,0,.28);
                 border:1px solid currentColor; border-radius:6px; padding:3px 9px; cursor:pointer;
                 opacity:.7; }
.webr-resetctl:hover:not(:disabled) { opacity:1; }
.webr-resetctl:disabled { opacity:.35; cursor:default; }
.webr-resetctl.armed { opacity:1; font-weight:600; }
`;
