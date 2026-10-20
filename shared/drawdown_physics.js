// Drawdown-board physics (shared/drawdown.js; ported 2026-10-20 from the diamonds prototype):
// a rigid rod hung on identical vertical linear springs.
//
// The rod moves vertically only. Its state is (h, s): height h at the rod's
// centre x = xc, slope s, so rod(x) = h + s * (x - xc). Each attached peg i at
// (x_i, y_i) pulls with force k * (y_i - rod(x_i)), applied at x_i. At rest the
// net force and the net torque about xc are both zero:
//     sum r_i = 0   and   sum r_i (x_i - xc) = 0,   r_i = y_i - rod(x_i)
// which are exactly the ordinary-least-squares normal equations. So the rod comes
// to rest on the OLS line whatever its mass, inertia, damping or start state.
// (Uniform gravity is deliberately left out: the rod is taken as counterbalanced.)
//
// Units: x in "rail units" (rail 1 = 0, evenly pitched rails 1 apart, unless the
// caller passes other positions); y in board value units (inches of drawdown).

export function ols(xs, ys) {
  const n = xs.length;
  if (n < 2) throw new Error('ols needs at least two points');
  let mx = 0, my = 0;
  for (let i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
  mx /= n; my /= n;
  let sxx = 0, sxy = 0;
  for (let i = 0; i < n; i++) {
    sxx += (xs[i] - mx) ** 2;
    sxy += (xs[i] - mx) * (ys[i] - my);
  }
  const slope = sxy / sxx;
  const intercept = my - slope * mx;
  return { slope, intercept, at: (x) => intercept + slope * x };
}

// Ideal vertical Hooke spring: force on the rod = k * (peg - rod).
export const verticalSpring = (k) => (dy /* peg - rod */, _dxOffset) => k * dy;

export const DEFAULTS = Object.freeze({
  k: 1,            // spring rate, force per inch
  omega: 7,        // rad/s, bounce frequency of the reference 5-peg rig
  zeta: 0.45,      // damping ratio of both modes for the reference rig
  hz: 240,         // fixed substep rate
  length: 5.8,     // rod length in rail units (rail 1 to rail 6 plus overhang)
});

export class RodSim {
  /**
   * @param {object} o
   * @param {number} o.xc        rod centre (x of its centre of mass), rail units
   * @param {number[]} o.refXs   rail positions used to size mass/inertia/damping
   *                             (the five peg rails); constants, not the live pegs
   * @param {function} [o.springLaw] (dy, x - xc) -> vertical force on the rod
   */
  constructor(o = {}) {
    const p = { ...DEFAULTS, ...o };
    this.k = p.k;
    this.dt = 1 / p.hz;
    this.xc = p.xc ?? 2.5;
    this.springLaw = p.springLaw || verticalSpring(p.k);
    const refXs = p.refXs || [0, 1, 2, 3, 4];
    const nRef = refXs.length;
    const sRef = refXs.reduce((a, x) => a + (x - this.xc) ** 2, 0);
    // Physical constants of the rod, fixed once: a uniform bar of mass m.
    this.m = (nRef * p.k) / (p.omega * p.omega);
    this.I = (this.m * p.length * p.length) / 12;
    this.cLin = 2 * p.zeta * Math.sqrt(nRef * p.k * this.m);
    this.cAng = 2 * p.zeta * Math.sqrt(sRef * p.k * this.I);
    this.pegs = [];                 // {x, y, attached}
    this.reset(0, 0);
    this._acc = 0;
  }

  reset(h, s = 0, vh = 0, vs = 0) {
    this.h = h; this.s = s; this.vh = vh; this.vs = vs;
    this.time = 0;
    this.settled = false;
    this._quiet = 0;
  }

  setPegs(pegs) {
    this.pegs = pegs.map((p) => ({ x: p.x, y: p.y, attached: p.attached !== false }));
    this.settled = false; this._quiet = 0;
  }

  setPegValue(i, y) {
    if (this.pegs[i].y !== y) { this.pegs[i].y = y; this.settled = false; this._quiet = 0; }
  }

  rodAt(x) { return this.h + this.s * (x - this.xc); }

  // Net vertical force and torque about xc from the springs.
  loads() {
    let F = 0, T = 0, n = 0;
    for (const p of this.pegs) {
      if (!p.attached) continue;
      const dx = p.x - this.xc;
      const f = this.springLaw(p.y - (this.h + this.s * dx), dx);
      F += f; T += f * dx; n++;
    }
    return { F, T, n };
  }

  substep() {
    const dt = this.dt;
    const { F, T, n } = this.loads();
    // Semi-implicit Euler: velocities first, then positions with new velocities.
    this.vh += ((F - this.cLin * this.vh) / this.m) * dt;
    this.vs += ((T - this.cAng * this.vs) / this.I) * dt;
    this.h += this.vh * dt;
    this.s += this.vs * dt;
    this.time += dt;
    // Settled = loads and motion both negligible, held for 0.25 s. This never
    // consults the OLS answer; it only says the rod has stopped moving.
    const nk = Math.max(n, 1) * this.k;
    const quiet =
      Math.abs(F) / nk < 0.01 && Math.abs(T) / nk < 0.01 &&
      Math.abs(this.vh) < 0.03 && Math.abs(this.vs) < 0.01;
    this._quiet = quiet ? this._quiet + dt : 0;
    if (this._quiet >= 0.25) this.settled = true;
    else if (!quiet) this.settled = false;
  }

  // Advance by real elapsed time using fixed substeps.
  advance(elapsed) {
    this._acc += Math.min(elapsed, 0.1);
    while (this._acc >= this.dt) { this.substep(); this._acc -= this.dt; }
  }
}
