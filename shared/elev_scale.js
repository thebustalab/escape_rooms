// Elevation map — the scale maths, extracted so it can be tested without a browser.
//
// The map's whole pedagogical claim is that the axis is PROPERLY SCALED: dragging a junction node to its
// surveyed height is plotting the dendrogram by hand, and a horizontal waterline across that plot is a
// dendrogram cut. If the pixel<->elevation mapping is off, the plot lies and the cut the player reads off
// it is wrong — so it is worth pinning rather than trusting to a hand-checked drag.

/**
 * Build the pixel <-> elevation mapping for one plot.
 * @param {{min:number, max:number, step?:number, height:number, padTop?:number, padBottom?:number}} o
 * @returns {{yFor:(v:number)=>number, vFor:(y:number)=>number, snap:(v:number)=>number,
 *            lo:number, hi:number, span:number, plot:number, padTop:number}}
 */
export function makeScale(o) {
  const lo = Number(o.min != null ? o.min : 0);
  const hi = Number(o.max != null ? o.max : 100);
  const span = (hi - lo) || 1;                       // a zero span would divide by zero, not just look odd
  const step = Number(o.step || 0);
  const padTop = Number(o.padTop != null ? o.padTop : 0);
  const padBottom = Number(o.padBottom != null ? o.padBottom : 0);
  const plot = Number(o.height) - padTop - padBottom;
  const snap = (v) => {
    const c = Math.max(lo, Math.min(hi, Number(v)));  // clamp BEFORE rounding: a drag past the top must
    return step > 0 ? Math.round(c / step) * step     // read as the max, never as an out-of-range height
                    : Math.round(c);
  };
  return {
    lo, hi, span, plot, padTop,
    yFor: (v) => padTop + plot * (1 - (Number(v) - lo) / span),
    vFor: (y) => lo + span * (1 - (Number(y) - padTop) / plot),
    snap,
  };
}

/** How many placed junctions still stand ABOVE a waterline — the cut, read off the player's own plot.
 *  Unplaced nodes are not counted (they have no height yet, so they cannot be above or below). */
export function junctionsAbove(nodes, placements, waterline) {
  const p = placements || {};
  return (nodes || []).filter(n => p[n.id] != null && Number(p[n.id]) > Number(waterline)).length;
}

/** How many of a map's nodes carry a recorded height — the counter ordinary `condOK` gates read
 *  (e.g. the canyon escape panel opening on {gte:["heights_placed", 7]}). */
export function placedCount(nodes, placements) {
  const p = placements || {};
  return (nodes || []).filter(n => p[n.id] != null).length;
}
