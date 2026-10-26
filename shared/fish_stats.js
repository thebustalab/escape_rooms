// fish_stats.js: the statistics behind the harbour fish board (comparing-means live scenario).
//
// WHY: the board is a teaching demo. Every haul is a genuinely random sample and every verdict is the
// real test the course teaches (Welch t, Wilcox, Shapiro, Tukey, Dunn with Holm), so false positives turn
// up at their honest rate. These are ports of what R computes (shapiro.test = Royston's swilk, wilcox.test
// exact/normal, TukeyHSD via ptukey, rstatix::dunn_test), pinned against R by test_fish_stats.mjs.
// Plain script (no modules) so the prototype opens straight from the Finder via file://.
(function (root) {
  "use strict";

  // ---------- random numbers (seeded, so a demo can be replayed) ----------
  function rng(seed) {
    let a = (seed >>> 0) || 1;
    const next = function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    let spare = null;
    next.normal = function (mu = 0, sd = 1) {
      if (spare !== null) { const z = spare; spare = null; return mu + sd * z; }
      let u = 0, v = 0;
      while (u <= 1e-300) u = next();
      v = next();
      const r = Math.sqrt(-2 * Math.log(u));
      spare = r * Math.sin(2 * Math.PI * v);
      return mu + sd * r * Math.cos(2 * Math.PI * v);
    };
    next.pick = function (arr, k) {           // k distinct items, without replacement
      const idx = arr.map((_, i) => i);
      for (let i = 0; i < k; i++) {
        const j = i + Math.floor(next() * (idx.length - i));
        const t = idx[i]; idx[i] = idx[j]; idx[j] = t;
      }
      return idx.slice(0, k).map((i) => arr[i]);
    };
    return next;
  }

  // ---------- special functions ----------
  function lgamma(x) {                         // Lanczos, g = 7
    const c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
      -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
      1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lgamma(1 - x);
    x -= 1;
    let s = c[0];
    for (let i = 1; i < 9; i++) s += c[i] / (x + i);
    const t = x + 7.5;
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(s);
  }

  // Standard normal CDF, Hart (1968) as given by West (2005): double precision.
  function pnorm(x, mu = 0, sd = 1, lower = true) {
    const z = (x - mu) / sd;
    const xa = Math.abs(z);
    let c;
    if (xa > 37) c = 0;
    else {
      const e = Math.exp(-xa * xa / 2);
      if (xa < 7.07106781186547) {
        let b = 3.52624965998911e-02 * xa + 0.700383064443688;
        b = b * xa + 6.37396220353165; b = b * xa + 33.912866078383; b = b * xa + 112.079291497871;
        b = b * xa + 221.213596169931; b = b * xa + 220.206867912376;
        c = e * b;
        b = 8.83883476483184e-02 * xa + 1.75566716318264;
        b = b * xa + 16.064177579207; b = b * xa + 86.7807322029461; b = b * xa + 296.564248779674;
        b = b * xa + 637.333633378831; b = b * xa + 793.826512519948; b = b * xa + 440.413735824752;
        c = c / b;
      } else {
        let b = xa + 0.65; b = xa + 4 / b; b = xa + 3 / b; b = xa + 2 / b; b = xa + 1 / b;
        c = e / b / 2.506628274631;
      }
    }
    const lowerP = z > 0 ? 1 - c : c;
    return lower ? lowerP : (z > 0 ? c : 1 - c);
  }

  // Inverse normal: Acklam's rational approximation plus one Halley step against pnorm.
  function qnorm(p) {
    if (p <= 0) return -Infinity;
    if (p >= 1) return Infinity;
    const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
      1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
    const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
      6.680131188771972e+01, -1.328068155288572e+01];
    const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
      -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
    const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
      3.754408661907416e+00];
    const plow = 0.02425;
    let x;
    if (p < plow) {
      const q = Math.sqrt(-2 * Math.log(p));
      x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    } else if (p <= 1 - plow) {
      const q = p - 0.5, r = q * q;
      x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    } else {
      const q = Math.sqrt(-2 * Math.log(1 - p));
      x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    for (let k = 0; k < 2; k++) {
      const e = pnorm(x) - p;
      const u = e * Math.sqrt(2 * Math.PI) * Math.exp(x * x / 2);
      x = x - u / (1 + x * u / 2);
    }
    return x;
  }

  // Regularised incomplete beta I_x(a, b) (continued fraction, Lentz).
  function betacf(x, a, b) {
    const FPMIN = 1e-300, EPS = 1e-15;
    let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1 / d;
    let h = d;
    for (let m = 1; m <= 10000; m++) {
      const m2 = 2 * m;
      let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d;
      const del = d * c;
      h *= del;
      if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  function pbeta(x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(x, a, b) / a;
    return 1 - bt * betacf(1 - x, b, a) / b;
  }
  // Two-sided p for Student's t with df degrees of freedom.
  function pt2(t, df) {
    return pbeta(df / (df + t * t), df / 2, 0.5);
  }

  // ---------- descriptive ----------
  const mean = (x) => x.reduce((s, v) => s + v, 0) / x.length;
  function variance(x) {
    const m = mean(x);
    return x.reduce((s, v) => s + (v - m) * (v - m), 0) / (x.length - 1);
  }
  function median(x) {
    const s = [...x].sort((a, b) => a - b), n = s.length;
    return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  }
  // Average ranks (ties share the mean rank) plus the tie groups' sizes.
  function rank(x) {
    const idx = x.map((v, i) => i).sort((i, j) => x[i] - x[j]);
    const r = new Array(x.length), ties = [];
    for (let i = 0; i < idx.length;) {
      let j = i;
      while (j + 1 < idx.length && x[idx[j + 1]] === x[idx[i]]) j++;
      const avg = (i + j + 2) / 2;
      for (let k = i; k <= j; k++) r[idx[k]] = avg;
      if (j > i) ties.push(j - i + 1);
      i = j + 1;
    }
    return { ranks: r, ties };
  }

  // ---------- Welch's t-test (course tTest default) ----------
  function welch(x, y) {
    const vx = variance(x) / x.length, vy = variance(y) / y.length;
    const se = Math.sqrt(vx + vy);
    const t = (mean(x) - mean(y)) / se;
    const df = (vx + vy) * (vx + vy) / (vx * vx / (x.length - 1) + vy * vy / (y.length - 1));
    return { t, df, p: pt2(t, df), diff: mean(x) - mean(y) };
  }

  // ---------- Wilcoxon rank-sum (wilcox.test, two-sided, correct = TRUE) ----------
  // Number of ways to pick m of the ranks 1..m+n with W = (sum of picked) - m(m+1)/2 equal to each value.
  function wilcoxCounts(m, n) {
    // Classic recursion on (m, n): c(w; m, n) = c(w - n; m - 1, n) + c(w; m, n - 1).
    const memo = new Map();
    function c(mm, nn) {
      const key = mm + "," + nn;
      if (memo.has(key)) return memo.get(key);
      const out = new Float64Array(mm * nn + 1);
      if (mm === 0 || nn === 0) out[0] = 1;
      else {
        const a = c(mm - 1, nn), b = c(mm, nn - 1);
        for (let w = 0; w <= mm * nn; w++) {
          let v = 0;
          if (w - nn >= 0 && w - nn < a.length) v += a[w - nn];
          if (w < b.length) v += b[w];
          out[w] = v;
        }
      }
      memo.set(key, out);
      return out;
    }
    return c(m, n);
  }
  function wilcox(x, y) {
    const nx = x.length, ny = y.length;
    const all = x.concat(y);
    const { ranks, ties } = rank(all);
    let rx = 0;
    for (let i = 0; i < nx; i++) rx += ranks[i];
    const W = rx - nx * (nx + 1) / 2;
    let p, exact = nx < 50 && ny < 50 && ties.length === 0;
    if (exact) {
      const cnt = wilcoxCounts(nx, ny);
      let total = 0;
      for (const v of cnt) total += v;
      const cdf = (q) => { let s = 0; for (let w = 0; w <= Math.min(q, cnt.length - 1); w++) s += cnt[w]; return s / total; };
      const pp = W > nx * ny / 2 ? 1 - cdf(W - 1) : cdf(W);
      p = Math.min(2 * pp, 1);
    } else {
      const N = nx + ny;
      const tieSum = ties.reduce((s, t) => s + t * t * t - t, 0);
      const sigma = Math.sqrt(nx * ny / 12 * ((N + 1) - tieSum / (N * (N - 1))));
      let z = W - nx * ny / 2;
      z = (z - Math.sign(z) * 0.5) / sigma;
      p = 2 * Math.min(pnorm(z), pnorm(z, 0, 1, false));
    }
    return { W, p, exact, medianDiff: median(x) - median(y) };
  }

  // ---------- Shapiro-Wilk (Royston 1995, R's swilk.c) ----------
  function poly(cc, x) {                     // cc[0] + cc[1] x + cc[2] x^2 + ...
    let ret = cc[0];
    if (cc.length > 1) {
      let p = x * cc[cc.length - 1];
      for (let j = cc.length - 2; j > 0; j--) p = (p + cc[j]) * x;
      ret += p;
    }
    return ret;
  }
  function shapiro(xIn) {
    const x = [...xIn].sort((a, b) => a - b);
    const n = x.length;
    if (n < 3) throw new Error("shapiro: need at least 3 values");
    const nn2 = Math.floor(n / 2);
    const a = new Array(nn2 + 1);            // 1-based, a[1] largest
    if (n === 3) a[1] = Math.SQRT1_2;
    else {
      const an25 = n + 0.25;
      let summ2 = 0;
      for (let i = 1; i <= nn2; i++) { a[i] = qnorm((i - 0.375) / an25); summ2 += a[i] * a[i]; }
      summ2 *= 2;
      const ssumm2 = Math.sqrt(summ2), rsn = 1 / Math.sqrt(n);
      const c1 = [0, 0.221157, -0.147981, -2.07119, 4.434685, -2.706056];
      const c2 = [0, 0.042981, -0.293762, -1.752461, 5.682633, -3.582633];
      const a1 = poly(c1, rsn) - a[1] / ssumm2;
      let i1, fac;
      if (n > 5) {
        i1 = 3;
        const a2 = -a[2] / ssumm2 + poly(c2, rsn);
        fac = Math.sqrt((summ2 - 2 * a[1] * a[1] - 2 * a[2] * a[2]) / (1 - 2 * a1 * a1 - 2 * a2 * a2));
        a[2] = a2;
      } else {
        i1 = 2;
        fac = Math.sqrt((summ2 - 2 * a[1] * a[1]) / (1 - 2 * a1 * a1));
      }
      a[1] = a1;
      for (let i = i1; i <= nn2; i++) a[i] = -a[i] / fac;
    }
    // Full antisymmetric coefficient vector, then W = squared correlation with the ordered sample.
    const coef = new Array(n).fill(0);
    for (let i = 1; i <= nn2; i++) { coef[i - 1] = -a[i]; coef[n - i] = a[i]; }
    const mc = mean(coef), mx = mean(x);
    let sab = 0, saa = 0, sbb = 0;
    for (let i = 0; i < n; i++) {
      const u = coef[i] - mc, v = x[i] - mx;
      sab += u * v; saa += u * u; sbb += v * v;
    }
    const W = sab * sab / (saa * sbb);
    const w1 = 1 - W;
    let p;
    if (n === 3) {
      p = 1.90985931710274 * (Math.asin(Math.sqrt(W)) - 1.04719755119660);
      if (p < 0) p = 0;
    } else {
      let y = Math.log(w1);
      const lxx = Math.log(n);
      let m, s;
      if (n <= 11) {
        const gamma = poly([-2.273, 0.459], n);
        if (y >= gamma) return { W, p: 1e-99 };
        y = -Math.log(gamma - y);
        m = poly([0.544, -0.39978, 0.025054, -6.714e-4], n);
        s = Math.exp(poly([1.3822, -0.77857, 0.062767, -0.0020322], n));
      } else {
        m = poly([-1.5861, -0.31082, -0.083751, 0.0038915], lxx);
        s = Math.exp(poly([-0.4803, -0.082676, 0.0030302], lxx));
      }
      p = pnorm(y, m, s, false);
    }
    return { W, p };
  }

  // ---------- studentized range (R's ptukey.c, nranges = 1) ----------
  function wprob(w, rr, cc) {
    const nleg = 12, ihalf = 6, C1 = -30, C2 = -50, C3 = 60, bb = 8, wlar = 3, wincr1 = 2, wincr2 = 3;
    const xleg = [0.981560634246719250690549090149, 0.904117256370474856678465866119,
      0.769902674194304687036893833213, 0.587317954286617447296702418941,
      0.367831498998180193752691536644, 0.125233408511468915472441369464];
    const aleg = [0.047175336386511827194615961485, 0.106939325995318430960254718194,
      0.160078328543346226334652529543, 0.203167426723065921749064455810,
      0.233492536538354808760849898925, 0.249147045813402785000562436043];
    const qsqz = w * 0.5;
    if (qsqz >= bb) return 1;
    let prW = 2 * pnorm(qsqz) - 1;
    prW = prW >= Math.exp(C2 / cc) ? Math.pow(prW, cc) : 0;
    const wincr = w > wlar ? wincr1 : wincr2;
    let blb = qsqz;
    const binc = (bb - qsqz) / wincr;
    let bub = blb + binc, einsum = 0;
    const cc1 = cc - 1;
    for (let wi = 1; wi <= wincr; wi++) {
      let elsum = 0;
      const a = 0.5 * (bub + blb), b = 0.5 * (bub - blb);
      for (let jj = 1; jj <= nleg; jj++) {
        let j, xx;
        if (ihalf < jj) { j = nleg - jj + 1; xx = xleg[j - 1]; }
        else { j = jj; xx = -xleg[j - 1]; }
        const c = b * xx, ac = a + c, qexpo = ac * ac;
        if (qexpo > C3) break;
        const pplus = 2 * pnorm(ac), pminus = 2 * pnorm(ac, w, 1);
        let rinsum = pplus * 0.5 - pminus * 0.5;
        if (rinsum >= Math.exp(C1 / cc1)) {
          rinsum = aleg[j - 1] * Math.exp(-(0.5 * qexpo)) * Math.pow(rinsum, cc1);
          elsum += rinsum;
        }
      }
      elsum *= (2 * b) * cc / Math.sqrt(2 * Math.PI);
      einsum += elsum;
      blb = bub;
      bub += binc;
    }
    prW += einsum;
    if (prW <= Math.exp(C1 / rr)) return 0;
    prW = Math.pow(prW, rr);
    return prW >= 1 ? 1 : prW;
  }
  // P(studentized range <= q) for cc groups and df residual degrees of freedom.
  function ptukey(q, cc, df) {
    if (q <= 0) return 0;
    const rr = 1;
    if (df > 25000) return wprob(q, rr, cc);
    const nlegq = 16, ihalfq = 8, eps1 = -30, eps2 = 1e-14;
    const xlegq = [0.989400934991649932596154173450, 0.944575023073232576077988415535,
      0.865631202387831743880467897712, 0.755404408355003033895101194847,
      0.617876244402643748446671764049, 0.458016777657227386342419442984,
      0.281603550779258913230460501460, 0.950125098376374401853193354250e-1];
    const alegq = [0.271524594117540948517805724560e-1, 0.622535239386478928628438369944e-1,
      0.951585116824927848099251076022e-1, 0.124628971255533872052476282192,
      0.149595988816576732081501730547, 0.169156519395002538189312079030,
      0.182603415044923588866763667969, 0.189450610455068496285396723208];
    const f2 = df * 0.5;
    let f2lf = f2 * Math.log(df) - df * Math.LN2 - lgamma(f2);
    const f21 = f2 - 1, ff4 = df * 0.25;
    const ulen = df <= 100 ? 1 : df <= 800 ? 0.5 : df <= 5000 ? 0.25 : 0.125;
    f2lf += Math.log(ulen);
    let ans = 0, otsum = 0;
    for (let i = 1; i <= 50; i++) {
      otsum = 0;
      const twa1 = (2 * i - 1) * ulen;
      for (let jj = 1; jj <= nlegq; jj++) {
        let j, t1;
        if (ihalfq < jj) {
          j = jj - ihalfq - 1;
          t1 = f2lf + f21 * Math.log(twa1 + xlegq[j] * ulen) - (xlegq[j] * ulen + twa1) * ff4;
        } else {
          j = jj - 1;
          t1 = f2lf + f21 * Math.log(twa1 - xlegq[j] * ulen) + (xlegq[j] * ulen - twa1) * ff4;
        }
        if (t1 >= eps1) {
          const qsqz = ihalfq < jj ? q * Math.sqrt((xlegq[j] * ulen + twa1) * 0.5)
            : q * Math.sqrt((-(xlegq[j] * ulen) + twa1) * 0.5);
          otsum += wprob(qsqz, rr, cc) * alegq[j] * Math.exp(t1);
        }
      }
      if (i * ulen >= 1 && otsum <= eps2) break;
      ans += otsum;
    }
    return ans > 1 ? 1 : ans;
  }

  // ---------- several groups ----------
  // groups: array of arrays. Returns one row per pair (i < j), in R's TukeyHSD order (j outer, i inner
  // would differ; we use i < j lexicographic, and the test matches by pair, not by position).
  function pooled(groups) {
    let ss = 0, N = 0;
    for (const g of groups) { const m = mean(g); for (const v of g) ss += (v - m) * (v - m); N += g.length; }
    const df = N - groups.length;
    return { mse: ss / df, df };
  }
  function tukey(groups) {
    const { mse, df } = pooled(groups), k = groups.length, out = [];
    for (let i = 0; i < k; i++) for (let j = i + 1; j < k; j++) {
      const diff = mean(groups[j]) - mean(groups[i]);
      const se = Math.sqrt(mse / 2 * (1 / groups[i].length + 1 / groups[j].length));
      out.push({ i, j, diff, p: 1 - ptukey(Math.abs(diff) / se, k, df) });
    }
    return out;
  }
  // The same pairs with NO correction (pooled-spread t), so the only change from Tukey is the correction.
  function pairwisePooledT(groups) {
    const { mse, df } = pooled(groups), k = groups.length, out = [];
    for (let i = 0; i < k; i++) for (let j = i + 1; j < k; j++) {
      const diff = mean(groups[j]) - mean(groups[i]);
      const t = diff / Math.sqrt(mse * (1 / groups[i].length + 1 / groups[j].length));
      out.push({ i, j, diff, p: pt2(t, df) });
    }
    return out;
  }
  function holm(ps) {
    const m = ps.length, order = ps.map((p, i) => i).sort((a, b) => ps[a] - ps[b]);
    const adj = new Array(m);
    let run = 0;
    order.forEach((idx, r) => { run = Math.max(run, Math.min(1, (m - r) * ps[idx])); adj[idx] = run; });
    return adj;
  }
  // Dunn's test as rstatix::dunn_test computes it: ranks over all values, tie-corrected z per pair.
  // Returns raw p and Holm-adjusted p (the course default).
  function dunn(groups) {
    const all = [].concat(...groups), N = all.length;
    const { ranks, ties } = rank(all);
    const meanRank = [];
    let off = 0;
    for (const g of groups) { let s = 0; for (let i = 0; i < g.length; i++) s += ranks[off + i]; meanRank.push(s / g.length); off += g.length; }
    const tieSum = ties.reduce((s, t) => s + t * t * t - t, 0);
    const base = N * (N + 1) / 12 - tieSum / (12 * (N - 1));
    const out = [];
    for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
      const z = (meanRank[j] - meanRank[i]) / Math.sqrt(base * (1 / groups[i].length + 1 / groups[j].length));
      out.push({ i, j, z, p: 2 * pnorm(-Math.abs(z)) });
    }
    const adj = holm(out.map((r) => r.p));
    out.forEach((r, k) => { r.pAdj = adj[k]; });
    return out;
  }

  const api = { rng, pnorm, qnorm, pbeta, pt2, ptukey, lgamma, mean, variance, median, rank,
    welch, wilcox, shapiro, tukey, pairwisePooledT, dunn, holm };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.FishStats = api;
})(typeof window !== "undefined" ? window : globalThis);
