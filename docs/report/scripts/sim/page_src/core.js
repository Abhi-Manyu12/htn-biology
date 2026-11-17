/* ==========================================================================
   Orb-web cable simulation -- physics core (no DOM).
   Units inside the solver: metre, kilogram, second, newton.
   Units at the API surface: cm for lengths, mN for tensions, m/s for wind.
   ========================================================================== */
"use strict";

/* ---------- Python-compatible MT19937 (random.Random(int).random()) ---------- */
function MT(seed) {
  const mt = new Uint32Array(624); let mti = 625;
  function initGenrand(s) {
    mt[0] = s >>> 0;
    for (mti = 1; mti < 624; mti++) {
      const p = mt[mti - 1] ^ (mt[mti - 1] >>> 30);
      mt[mti] = (Math.imul(1812433253, p) + mti) >>> 0;
    }
  }
  function initByArray(key) {
    initGenrand(19650218);
    let i = 1, j = 0, k = Math.max(624, key.length);
    for (; k; k--) {
      const p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(p, 1664525)) + key[j] + j) >>> 0;
      i++; j++;
      if (i >= 624) { mt[0] = mt[623]; i = 1; }
      if (j >= key.length) j = 0;
    }
    for (k = 623; k; k--) {
      const p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(p, 1566083941)) - i) >>> 0;
      i++;
      if (i >= 624) { mt[0] = mt[623]; i = 1; }
    }
    mt[0] = 0x80000000;
  }
  function genrand() {
    let y;
    if (mti >= 624) {
      let kk;
      for (kk = 0; kk < 624 - 397; kk++) {
        y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7fffffff);
        mt[kk] = mt[kk + 397] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
      }
      for (; kk < 623; kk++) {
        y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7fffffff);
        mt[kk] = mt[kk + (397 - 624)] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
      }
      y = (mt[623] & 0x80000000) | (mt[0] & 0x7fffffff);
      mt[623] = mt[396] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
      mti = 0;
    }
    y = mt[mti++];
    y ^= (y >>> 11); y ^= (y << 7) & 0x9d2c5680; y ^= (y << 15) & 0xefc60000; y ^= (y >>> 18);
    return y >>> 0;
  }
  // key = 32-bit little-endian words of abs(seed), as CPython's random_seed()
  let a = Math.abs(Math.floor(Number(seed) || 0)); const key = [];
  if (a === 0) key.push(0);
  while (a > 0) { key.push(a % 4294967296); a = Math.floor(a / 4294967296); }
  initByArray(key);
  let spare = null;
  return {
    random() { const x = genrand() >>> 5, y = genrand() >>> 6; return (x * 67108864 + y) / 9007199254740992; },
    normal() { // Box-Muller (not CPython's gauss stream; used only for gusts)
      if (spare !== null) { const s = spare; spare = null; return s; }
      const u = this.random() * 2 * Math.PI, r = Math.sqrt(-2 * Math.log(1 - this.random()));
      spare = Math.sin(u) * r; return Math.cos(u) * r;
    },
  };
}

/* ---------- thread types: display + illustrative material defaults ---------- */
const TYPES = ["bridge", "dragline", "proto_radius", "frame", "radius", "auxiliary_spiral", "capture_spiral"];
const TYPE_LABEL = { bridge: "bridge", dragline: "dragline", proto_radius: "proto-radius", frame: "frame",
  radius: "radius", auxiliary_spiral: "auxiliary spiral", capture_spiral: "capture spiral" };
const TYPE_COLOR = { bridge: "#7F7F7F", dragline: "#A8A8A8", proto_radius: "#E69F00", frame: "#000000",
  radius: "#0072B2", auxiliary_spiral: "#8E6BBF", capture_spiral: "#D55E00" };
// mu: linear density, ug/cm   EA: axial stiffness, mN   slack: rest length / chord - 1, percent
// All ILLUSTRATIVE (no silk mechanics numbers exist in the repository).
const TYPE_DEFAULTS = {
  bridge:           { mu: 0.10, EA: 60,  slack: 0 },
  dragline:         { mu: 0.08, EA: 40,  slack: 0 },
  proto_radius:     { mu: 0.10, EA: 60,  slack: 0 },
  frame:            { mu: 0.15, EA: 100, slack: 0 },
  radius:           { mu: 0.10, EA: 60,  slack: 0 },
  auxiliary_spiral: { mu: 0.05, EA: 30,  slack: 0 },
  capture_spiral:   { mu: 0.20, EA: 3,   slack: 0 },
};
const PHASE_LABEL = { exploration: "Exploration & bridging", proto_hub: "Proto-hub establishment", frame: "Frame construction",
  radii: "Radii construction", auxiliary_spiral: "Auxiliary spiral", capture_spiral: "Capture spiral", complete: "Finalisation" };

function defaultParams(R) {
  const p = {
    mode: "final", step: -1, panel: "web",
    g: 9.81, exag: 2000, ds: 0.5,
    wind: 0, dir: 0, gust: R.noise_std, gtau: 1.0, cn: 6e-5,
    seed: R.seed, drop: 0,
    amp: 0, freq: R.mulder.frequency_hz, phase: 0,
    spider: 30, speed: 20, cap: Infinity,
    sub: 2, damp: 0.5,
    tmap: 0, ghost: 0, ui: 1, t: 0,
    vL: 16, vslack: 1, vtype: "radius", vN: 40,
    detach: "",
  };
  for (const ty of TYPES) for (const k of ["mu", "EA", "slack"]) p[k + "_" + ty] = TYPE_DEFAULTS[ty][k];
  return p;
}

/* ===================================================================
   World: lumped-mass cable network, tension-only axial springs.
   Implicit (backward) Euler, Newton iterations on the incremental
   potential, exact sparse block elimination (min-degree order).
   =================================================================== */
class World {
  constructor(n, ns) {
    this.n = n; this.ns = ns;
    this.x = new Float64Array(2 * n); this.v = new Float64Array(2 * n);
    this.base = new Float64Array(2 * n);           // reference positions of fixed nodes
    this.fixed = new Uint8Array(n);
    this.pmass = new Float64Array(n); this.pforce = new Float64Array(2 * n);
    this.m = new Float64Array(n); this.deg = new Int32Array(n);
    this.sa = new Int32Array(ns); this.sb = new Int32Array(ns);
    this.L0 = new Float64Array(ns); this.EA = new Float64Array(ns); this.mu = new Float64Array(ns);
    this.on = new Uint8Array(ns);
    this.g = 9.81; this.exag = 1; this.cn = 0; this.ct = 0; this.cnum = 0; this.W = [0, 0];
    this.support = { A: 0, f: 0, phi: 0, H: 0.18 };
    this.t = 0; this.topo = 1; this._ot = -1;
    // work arrays
    this.xn = new Float64Array(2 * n); this.xh = new Float64Array(2 * n);
    this.a = new Float64Array(n); this.B = new Float64Array(3 * n); this.Fc = new Float64Array(2 * n);
    this.D = new Float64Array(3 * n);
    this.lastNewton = 0; this.maxNewton = 60; this.slackWin = 0; this.newtonTol = 1e-11; this.newtonCapHits = 0;
  }
  setSeg(s, a, b) { this.sa[s] = a; this.sb[s] = b; }
  activate(s, on) { if (this.on[s] === on) return; this.on[s] = on; const d = on ? 1 : -1; this.deg[this.sa[s]] += d; this.deg[this.sb[s]] += d; this.topo++; }
  setFixed(i, f) { if (this.fixed[i] !== f) { this.fixed[i] = f; this.topo++; } }
  supportDisp(i, t) { // affine shear of spider_web_mulder/model.py: dx = (1 - y/H) A sin(2 pi f t + phase)
    const s = this.support; if (!s.A || !s.f) return 0;
    const y = this.base[2 * i + 1];
    return (1 - y / s.H) * s.A * Math.sin(2 * Math.PI * s.f * t + s.phi);
  }
  placeFixed(t, setVel, h) {
    for (let i = 0; i < this.n; i++) if (this.fixed[i]) {
      const nx = this.base[2 * i] + this.supportDisp(i, t), ny = this.base[2 * i + 1];
      if (setVel) { this.v[2 * i] = (nx - this.x[2 * i]) / h; this.v[2 * i + 1] = (ny - this.x[2 * i + 1]) / h; }
      else { this.v[2 * i] = 0; this.v[2 * i + 1] = 0; }
      this.x[2 * i] = nx; this.x[2 * i + 1] = ny;
    }
  }
  updateMass() {
    const m = this.m; m.fill(0);
    for (let s = 0; s < this.ns; s++) if (this.on[s]) { const mm = 0.5 * this.mu[s] * this.exag * this.L0[s]; m[this.sa[s]] += mm; m[this.sb[s]] += mm; }
    for (let i = 0; i < this.n; i++) if (this.deg[i] > 0) m[i] += this.pmass[i];
  }
  /* free-node list + minimum-degree elimination order (recomputed on topology change) */
  _prepare() {
    if (this._ot === this.topo) return;
    const n = this.n, fi = new Int32Array(n).fill(-1), free = [];
    for (let i = 0; i < n; i++) if (!this.fixed[i] && this.deg[i] > 0) { fi[i] = free.length; free.push(i); }
    const nf = free.length, adj = new Array(nf);
    for (let k = 0; k < nf; k++) adj[k] = new Set();
    for (let s = 0; s < this.ns; s++) if (this.on[s]) {
      const ia = fi[this.sa[s]], ib = fi[this.sb[s]];
      if (ia >= 0 && ib >= 0) { adj[ia].add(ib); adj[ib].add(ia); }
    }
    // lazy binary heap keyed by degree
    const heap = []; const push = (d, v) => { heap.push([d, v]); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p][0] <= heap[i][0]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
    const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
    for (let k = 0; k < nf; k++) push(adj[k].size, k);
    const done = new Uint8Array(nf), order = new Int32Array(nf); let c = 0;
    while (heap.length) {
      const [d, v] = pop(); if (done[v] || d !== adj[v].size) continue;
      done[v] = 1; order[c++] = v;
      const nb = [...adj[v]];
      for (const u of nb) { adj[u].delete(v); for (const w of nb) if (w !== u) adj[u].add(w); }
      for (const u of nb) push(adj[u].size, u);
    }
    this.free = free; this.fi = fi; this.order = order; this._ot = this.topo;
  }
  computeDrag(X) { // anisotropic linear (low-Reynolds-number) drag tensor per node, N s / m
    const D = this.D; D.fill(0); if (!(this.cn > 0)) return;
    for (let s = 0; s < this.ns; s++) if (this.on[s]) {
      const a = this.sa[s], b = this.sb[s];
      const dx = X[2 * b] - X[2 * a], dy = X[2 * b + 1] - X[2 * a + 1], L = Math.hypot(dx, dy); if (L <= 0) continue;
      const tx = dx / L, ty = dy / L, h = 0.5 * L, cn = this.cn, ct = this.ct;
      const xx = h * (cn * (1 - tx * tx) + ct * tx * tx), xy = h * (ct - cn) * tx * ty, yy = h * (cn * (1 - ty * ty) + ct * ty * ty);
      D[3 * a] += xx; D[3 * a + 1] += xy; D[3 * a + 2] += yy; D[3 * b] += xx; D[3 * b + 1] += xy; D[3 * b + 2] += yy;
    }
  }
  /* constant force on each node: weight + spider + steady drag D W */
  computeFc(Wx, Wy) {
    const Fc = this.Fc, m = this.m, D = this.D;
    for (let i = 0; i < this.n; i++) {
      Fc[2 * i] = this.pforce[2 * i] + D[3 * i] * Wx + D[3 * i + 1] * Wy;
      Fc[2 * i + 1] = -m[i] * this.g * (this.deg[i] > 0 ? 1 : 0) + this.pforce[2 * i + 1] + D[3 * i + 1] * Wx + D[3 * i + 2] * Wy;
    }
  }
  /* incremental potential  Phi(x) = sum_i [a/2 |x-xh|^2 + 1/2 (x-xn)^T B (x-xn) - Fc.(x-xn)] + sum_s k/2 (L-L0)_+^2 */
  energy(X) {
    let E = 0; const free = this.free, a = this.a, B = this.B, Fc = this.Fc, xh = this.xh, xn = this.xn;
    for (let k = 0; k < free.length; k++) {
      const i = free[k], ex = X[2 * i] - xh[2 * i], ey = X[2 * i + 1] - xh[2 * i + 1], dx = X[2 * i] - xn[2 * i], dy = X[2 * i + 1] - xn[2 * i + 1];
      E += 0.5 * a[i] * (ex * ex + ey * ey) + 0.5 * (B[3 * i] * dx * dx + 2 * B[3 * i + 1] * dx * dy + B[3 * i + 2] * dy * dy) - Fc[2 * i] * dx - Fc[2 * i + 1] * dy;
    }
    for (let s = 0; s < this.ns; s++) if (this.on[s]) {
      const p = this.sa[s], q = this.sb[s], L = Math.hypot(X[2 * q] - X[2 * p], X[2 * q + 1] - X[2 * p + 1]), e = L - this.L0[s];
      if (e > 0) E += 0.5 * (this.EA[s] / this.L0[s]) * e * e;
    }
    return E;
  }
  /* gradient and Hessian blocks (Hessian = a I + B + sum of segment stiffness, all SPD) */
  gradHess(X, wantH) {
    const free = this.free, fi = this.fi, nf = free.length, a = this.a, B = this.B, Fc = this.Fc, xh = this.xh, xn = this.xn;
    const G = new Float64Array(2 * nf), Dg = wantH ? new Float64Array(3 * nf) : null, off = wantH ? new Array(nf) : null;
    if (wantH) for (let k = 0; k < nf; k++) off[k] = new Map();
    for (let k = 0; k < nf; k++) {
      const i = free[k], dx = X[2 * i] - xn[2 * i], dy = X[2 * i + 1] - xn[2 * i + 1];
      G[2 * k] = a[i] * (X[2 * i] - xh[2 * i]) + B[3 * i] * dx + B[3 * i + 1] * dy - Fc[2 * i];
      G[2 * k + 1] = a[i] * (X[2 * i + 1] - xh[2 * i + 1]) + B[3 * i + 1] * dx + B[3 * i + 2] * dy - Fc[2 * i + 1];
      if (wantH) { Dg[3 * k] = a[i] + B[3 * i]; Dg[3 * k + 1] = B[3 * i + 1]; Dg[3 * k + 2] = a[i] + B[3 * i + 2]; }
    }
    for (let s = 0; s < this.ns; s++) if (this.on[s]) {
      const p = this.sa[s], q = this.sb[s], dx = X[2 * q] - X[2 * p], dy = X[2 * q + 1] - X[2 * p + 1], L = Math.hypot(dx, dy), L0 = this.L0[s];
      const taut = L > L0;
      // optional near-slack window (slackWin > 0) keeps the axial curvature of almost-taut segments in the Newton model;
      // off by default (it slowed static settling); kink crossings are handled by more Newton iterations instead
      if (!taut && !(wantH && L > L0 * (1 - this.slackWin) && L > 0)) continue;
      const k = this.EA[s] / L0, f = taut ? k * (L - L0) : 0, nx = dx / L, ny = dy / L;
      const kp = fi[p], kq = fi[q];
      if (kp >= 0) { G[2 * kp] -= f * nx; G[2 * kp + 1] -= f * ny; }
      if (kq >= 0) { G[2 * kq] += f * nx; G[2 * kq + 1] += f * ny; }
      if (!wantH) continue;
      const r = taut ? 1 - L0 / L : 0; // geometric (transverse) stiffness factor
      const kxx = k * (nx * nx + r * (1 - nx * nx)), kxy = k * (nx * ny - r * nx * ny), kyy = k * (ny * ny + r * (1 - ny * ny));
      if (kp >= 0) { Dg[3 * kp] += kxx; Dg[3 * kp + 1] += kxy; Dg[3 * kp + 2] += kyy; }
      if (kq >= 0) { Dg[3 * kq] += kxx; Dg[3 * kq + 1] += kxy; Dg[3 * kq + 2] += kyy; }
      if (kp >= 0 && kq >= 0) {
        let bl = off[kp].get(kq); if (!bl) { bl = new Float64Array(4); off[kp].set(kq, bl); }
        bl[0] -= kxx; bl[1] -= kxy; bl[2] -= kxy; bl[3] -= kyy;
        let bm = off[kq].get(kp); if (!bm) { bm = new Float64Array(4); off[kq].set(kp, bm); }
        bm[0] -= kxx; bm[1] -= kxy; bm[2] -= kxy; bm[3] -= kyy;
      }
    }
    return { G, Dg, off };
  }
  /* solve H d = -G by block Gaussian elimination in min-degree order */
  solve(G, Dg, off) {
    const nf = this.free.length, order = this.order, r = new Float64Array(2 * nf);
    for (let i = 0; i < 2 * nf; i++) r[i] = -G[i];
    const diag = new Float64Array(4 * nf);
    for (let k = 0; k < nf; k++) { diag[4 * k] = Dg[3 * k]; diag[4 * k + 1] = Dg[3 * k + 1]; diag[4 * k + 2] = Dg[3 * k + 1]; diag[4 * k + 3] = Dg[3 * k + 2]; }
    const rec = new Array(nf);
    for (let c = 0; c < nf; c++) {
      const v = order[c], d0 = diag[4 * v], d1 = diag[4 * v + 1], d2 = diag[4 * v + 2], d3 = diag[4 * v + 3];
      const det = d0 * d3 - d1 * d2; const i0 = d3 / det, i1 = -d1 / det, i2 = -d2 / det, i3 = d0 / det;
      const nb = off[v], us = [], bs = [];
      for (const [u, A] of nb) { us.push(u); bs.push(A); }
      const rv0 = r[2 * v], rv1 = r[2 * v + 1];
      for (let p = 0; p < us.length; p++) {
        const u = us[p], A = bs[p]; // A = A_vu ; A_uv = A^T
        // Lu = A_uv Di = A^T Di
        const l0 = A[0] * i0 + A[2] * i2, l1 = A[0] * i1 + A[2] * i3, l2 = A[1] * i0 + A[3] * i2, l3 = A[1] * i1 + A[3] * i3;
        r[2 * u] -= l0 * rv0 + l1 * rv1; r[2 * u + 1] -= l2 * rv0 + l3 * rv1;
        const ou = off[u]; ou.delete(v);
        for (let q = 0; q < us.length; q++) {
          const w = us[q], C = bs[q]; // A_vw
          const p0 = l0 * C[0] + l1 * C[2], p1 = l0 * C[1] + l1 * C[3], p2 = l2 * C[0] + l3 * C[2], p3 = l2 * C[1] + l3 * C[3];
          if (w === u) { diag[4 * u] -= p0; diag[4 * u + 1] -= p1; diag[4 * u + 2] -= p2; diag[4 * u + 3] -= p3; }
          else { let bl = ou.get(w); if (!bl) { bl = new Float64Array(4); ou.set(w, bl); } bl[0] -= p0; bl[1] -= p1; bl[2] -= p2; bl[3] -= p3; }
        }
      }
      rec[c] = [i0, i1, i2, i3, us, bs];
    }
    const x = new Float64Array(2 * nf);
    for (let c = nf - 1; c >= 0; c--) {
      const v = order[c], [i0, i1, i2, i3, us, bs] = rec[c];
      let s0 = r[2 * v], s1 = r[2 * v + 1];
      for (let p = 0; p < us.length; p++) { const u = us[p], A = bs[p]; s0 -= A[0] * x[2 * u] + A[1] * x[2 * u + 1]; s1 -= A[2] * x[2 * u] + A[3] * x[2 * u + 1]; }
      x[2 * v] = i0 * s0 + i1 * s1; x[2 * v + 1] = i2 * s0 + i3 * s1;
    }
    return x;
  }
  /* one damped Newton iteration with Armijo backtracking; returns {alpha, dmax} */
  newtonIter(X) {
    const free = this.free, nf = free.length;
    const { G, Dg, off } = this.gradHess(X, true);
    const d = this.solve(G, Dg, off);
    let slope = 0, dmax = 0;
    for (let i = 0; i < 2 * nf; i++) { slope += G[i] * d[i]; dmax = Math.max(dmax, Math.abs(d[i])); }
    if (!(slope < 0) || !isFinite(dmax)) return { alpha: 0, dmax: 0 };
    const E0 = this.energy(X), Xt = new Float64Array(X);
    let alpha = 1;
    for (let tries = 0; tries < 40; tries++) {
      for (let k = 0; k < nf; k++) { const i = free[k]; Xt[2 * i] = X[2 * i] + alpha * d[2 * k]; Xt[2 * i + 1] = X[2 * i + 1] + alpha * d[2 * k + 1]; }
      const E = this.energy(Xt);
      if (E <= E0 + 1e-4 * alpha * slope) break;
      if (alpha * dmax < 1e-13) break;            // below round-off: accept
      alpha *= 0.5;
    }
    for (let k = 0; k < nf; k++) { const i = free[k]; X[2 * i] = Xt[2 * i]; X[2 * i + 1] = Xt[2 * i + 1]; }
    return { alpha, dmax: alpha * dmax };
  }
  /* one backward-Euler time step of length h (s) */
  step(h) {
    this._prepare(); this.updateMass();
    const n = this.n, X = this.x, V = this.v, xn = this.xn, xh = this.xh;
    this.t += h;
    // prescribed support motion
    for (let i = 0; i < 2 * n; i++) xn[i] = X[i];
    this.placeFixed(this.t, true, h);
    this.computeDrag(xn); this.computeFc(this.W[0], this.W[1]);
    const free = this.free, D = this.D, m = this.m;
    for (const i of free) {
      this.a[i] = m[i] / (h * h);
      this.B[3 * i] = (D[3 * i] + this.cnum * m[i]) / h; this.B[3 * i + 1] = D[3 * i + 1] / h; this.B[3 * i + 2] = (D[3 * i + 2] + this.cnum * m[i]) / h;
      xh[2 * i] = xn[2 * i] + h * V[2 * i]; xh[2 * i + 1] = xn[2 * i + 1] + h * V[2 * i + 1];
      X[2 * i] = xh[2 * i]; X[2 * i + 1] = xh[2 * i + 1];
    }
    let it = 0;
    let ok = false;
    for (; it < this.maxNewton; it++) { const r = this.newtonIter(X); if (r.dmax < this.newtonTol) { ok = true; break; } }
    this.lastNewton = it + 1; if (!ok) this.newtonCapHits++;
    for (const i of free) { V[2 * i] = (X[2 * i] - xn[2 * i]) / h; V[2 * i + 1] = (X[2 * i + 1] - xn[2 * i + 1]) / h; }
    // nodes that are not part of the active web carry no velocity
    for (let i = 0; i < n; i++) if (!this.fixed[i] && this.deg[i] === 0) { V[2 * i] = 0; V[2 * i + 1] = 0; }
  }
  /* static residual: max |net force| on a free node, relative to max |applied force| */
  staticResidual(X, Wx, Wy) {
    this.computeDrag(X); this.computeFc(Wx, Wy);
    const save = this.a; this.a = new Float64Array(this.n); const B = this.B; this.B = new Float64Array(3 * this.n);
    const xn = this.xn; for (let i = 0; i < 2 * this.n; i++) xn[i] = X[i];
    const { G } = this.gradHess(X, false); this.a = save; this.B = B;
    let r = 0, f = 0;
    for (let k = 0; k < this.free.length; k++) { const i = this.free[k]; r = Math.max(r, Math.hypot(G[2 * k], G[2 * k + 1])); f = Math.max(f, Math.hypot(this.Fc[2 * i], this.Fc[2 * i + 1])); }
    return { abs: r, ref: f, rel: f > 0 ? r / f : r };
  }
  /* static equilibrium by Levenberg-Marquardt-damped Newton (proximal term m/hs^2) */
  settle(maxIters = 200, tol = 1e-9) {
    this._prepare(); this.updateMass();
    this.placeFixed(this.t, false, 1);
    const X = this.x, n = this.n, free = this.free;
    if (!free.length) return { iters: 0, residual: 0, converged: true, free: 0 };
    let hs = 0.02, it = 0, res = null;
    for (; it < maxIters; it++) {
      for (let i = 0; i < 2 * n; i++) { this.xn[i] = X[i]; this.xh[i] = X[i]; }
      this.computeDrag(X); this.computeFc(this.W[0], this.W[1]);
      for (const i of free) { this.a[i] = this.m[i] / (hs * hs); this.B[3 * i] = this.B[3 * i + 1] = this.B[3 * i + 2] = 0; }
      const r = this.newtonIter(X);
      hs = r.alpha === 1 ? Math.min(hs * 4, 20) : Math.max(hs / 4, 1e-4);
      if (it % 2 === 1 || r.dmax < 1e-12) {
        res = this.staticResidual(X, this.W[0], this.W[1]);
        if (res.rel < tol) { it++; break; }
      }
    }
    if (!res) res = this.staticResidual(X, this.W[0], this.W[1]);
    for (let i = 0; i < 2 * n; i++) this.v[i] = 0;
    return { iters: it, residual: res.rel, residualN: res.abs, converged: res.rel < tol, free: free.length };
  }
  kinetic() { let K = 0; for (let i = 0; i < this.n; i++) if (!this.fixed[i] && this.deg[i] > 0) K += 0.5 * this.m[i] * (this.v[2 * i] ** 2 + this.v[2 * i + 1] ** 2); return K; }
  tension(s) { const p = this.sa[s], q = this.sb[s], L = Math.hypot(this.x[2 * q] - this.x[2 * p], this.x[2 * q + 1] - this.x[2 * p + 1]); return L > this.L0[s] ? this.EA[s] * (L - this.L0[s]) / this.L0[s] : 0; }
  segLen(s) { const p = this.sa[s], q = this.sb[s]; return Math.hypot(this.x[2 * q] - this.x[2 * p], this.x[2 * q + 1] - this.x[2 * p + 1]); }
}

/* ===================================================================
   Topology of the planned web, taken from the HTN plan.
   =================================================================== */
function buildTopology(R, dsCm) {
  const [FW, FH] = R.frame, EPS = 1e-6;
  // canonical points: plan nodes merged by coordinate
  const names = Object.keys(R.nodes), cid = {}, pts = [];
  for (const nm of names) {
    const [x, y] = R.nodes[nm];
    let id = pts.findIndex(p => Math.abs(p.x - x) < EPS && Math.abs(p.y - y) < EPS);
    if (id < 0) { id = pts.length; pts.push({ x, y, names: [] }); }
    pts[id].names.push(nm); cid[nm] = id;
  }
  // rig = rectangle given by config.yaml walkable_edges (two sticks, top and bottom bars)
  for (const p of pts) p.fixed = Math.abs(p.x) < EPS || Math.abs(p.x - FW) < EPS || Math.abs(p.y) < EPS || Math.abs(p.y - FH) < EPS;
  // replay the plan (same semantics as visualization/index_updated.html applyAction)
  const threads = [], live = [], spiderAt = [cid[R.spider_start]], hubName = "proto_hub";
  let markStep = -1;
  const add = (a, b, type, k) => { const t = { id: threads.length, a: cid[a], b: cid[b], an: a, bn: b, type, step: k, rm: Infinity }; threads.push(t); live.push(t); return t; };
  const steps = R.steps.map(([name, args, phase, energy, ce], k) => ({ k, name, args, phase, energy, ce }));
  let pos = cid[R.spider_start];
  for (const st of steps) {
    const { name, args, k } = st; st.from = pos; st.add = []; st.rmv = [];
    switch (name) {
      case "lay_thread": st.add.push(add(args[0], args[1], args[2], k)); pos = cid[args[1]]; break;
      case "lay_frame_thread": st.add.push(add(args[0], args[1], "frame", k)); pos = cid[args[1]]; break;
      case "lay_radius": st.add.push(add(args[0], args[1], "radius", k)); pos = cid[args[1]]; break;
      case "drop_down": case "swing_tarzan": st.add.push(add(args[0], args[1], "dragline", k)); pos = cid[args[1]]; break;
      case "build_spiral_segment": st.add.push(add(args[0], args[1], args[2], k)); pos = cid[args[1]]; break;
      case "insert_radius": {
        const i = live.findIndex(t => t.type === "dragline" && ((t.an === args[0] && t.bn === args[1]) || (t.an === args[1] && t.bn === args[0])));
        if (i >= 0) { live[i].rm = k; st.rmv.push(live[i]); live.splice(i, 1); }
        st.add.push(add(args[1], args[0], "proto_radius", k)); break;
      }
      case "remove_thread": {
        const i = live.findIndex(t => (t.an === args[0] && t.bn === args[1]) || (t.an === args[1] && t.bn === args[0]));
        if (i >= 0) { live[i].rm = k; st.rmv.push(live[i]); live.splice(i, 1); } break;
      }
      case "walk": case "reel_up": pos = cid[args[1]]; break;
      case "anchor": case "attach_dragline": pos = cid[args[0]]; break;
      case "mark_proto_hub": markStep = k; break;
    }
    st.to = pos; spiderAt.push(pos);
  }
  // attachment points = every thread endpoint; a thread is split wherever one lies on its chord
  const attach = new Set(); for (const t of threads) { attach.add(t.a); attach.add(t.b); }
  for (const t of threads) {
    const A = pts[t.a], B = pts[t.b], dx = B.x - A.x, dy = B.y - A.y, L2 = dx * dx + dy * dy;
    const inner = [];
    for (const c of attach) {
      if (c === t.a || c === t.b) continue;
      const P = pts[c], u = ((P.x - A.x) * dx + (P.y - A.y) * dy) / L2;
      if (u <= EPS || u >= 1 - EPS) continue;
      const ex = A.x + u * dx - P.x, ey = A.y + u * dy - P.y;
      if (Math.hypot(ex, ey) < 1e-5) inner.push([u, c]);
    }
    inner.sort((p, q) => p[0] - q[0]);
    t.pts = [t.a, ...inner.map(p => p[1]), t.b]; t.us = [0, ...inner.map(p => p[0]), 1];
    t.planLen = Math.sqrt(L2);
  }
  // spiral waypoints lie on radial threads: record which anchor supports each free point
  const hub = cid[hubName], supportAnchor = {};
  for (const t of threads) if ((t.type === "radius" || t.type === "proto_radius" || t.type === "dragline") && (t.a === hub || t.b === hub)) {
    const anc = t.a === hub ? t.b : t.a;
    for (const c of t.pts) if (c !== hub && !pts[c].fixed && c !== anc) supportAnchor[c] = anc;
  }
  // mesh: one node per canonical point, then interior nodes per span
  let nNodes = pts.length; const segs = [];
  for (const t of threads) {
    t.nodes = [t.pts[0]]; t.segs = []; t.spans = [];
    for (let s = 0; s + 1 < t.pts.length; s++) {
      const p0 = t.pts[s], p1 = t.pts[s + 1], len = Math.hypot(pts[p1].x - pts[p0].x, pts[p1].y - pts[p0].y);
      const nseg = Math.max(2, Math.ceil(len / dsCm - 1e-9));
      const span = { p0, p1, nodes: [p0], segs: [], u0: t.us[s], u1: t.us[s + 1] };
      let prev = p0;
      for (let j = 1; j <= nseg; j++) {
        const node = j === nseg ? p1 : nNodes++;
        if (j < nseg) span.nodes.push(node); else span.nodes.push(p1);
        segs.push([prev, node, t.id]); span.segs.push(segs.length - 1); t.segs.push(segs.length - 1); t.nodes.push(node); prev = node;
      }
      t.spans.push(span);
    }
  }
  return { pts, cid, threads, steps, spiderAt, markStep, hub, supportAnchor, nNodes, segs };
}

/* ===================================================================
   Web model: plan + world + construction controller
   =================================================================== */
class WebSim {
  constructor(R, P) {
    this.R = R; this.P = P; this.rebuild();
  }
  rebuild() {
    const R = this.R, P = this.P;
    this.topo = buildTopology(R, P.ds);
    const T = this.topo, w = new World(T.nNodes, T.segs.length);
    w.support.H = R.frame[1] / 100;
    T.segs.forEach(([a, b], s) => w.setSeg(s, a, b));
    this.world = w; this.segType = T.segs.map(s => T.threads[s[2]].type);
    // plan positions of every mesh node (interior nodes on the straight chords)
    this.planX = new Float64Array(2 * T.nNodes);
    T.pts.forEach((p, i) => { this.planX[2 * i] = p.x / 100; this.planX[2 * i + 1] = p.y / 100; });
    for (const t of T.threads) for (const sp of t.spans) {
      const k = sp.nodes.length - 1;
      for (let j = 1; j < k; j++) { const u = j / k, n = sp.nodes[j]; this.planX[2 * n] = this.planX[2 * sp.p0] + u * (this.planX[2 * sp.p1] - this.planX[2 * sp.p0]); this.planX[2 * n + 1] = this.planX[2 * sp.p0 + 1] + u * (this.planX[2 * sp.p1 + 1] - this.planX[2 * sp.p0 + 1]); }
    }
    w.base.set(this.planX);
    this.removed = this.drawRemoved();
    this.detached = new Set();
    this.gustRng = MT(Number(P.seed) + 1); this.gustXi = 0;
    this.applyParams();
    this.trace = [];
    this.buildTo(P.step >= 0 ? P.step : (P.mode === "play" ? 0 : T.steps.length));
  }
  /* anchors dropped exactly as stochastic.select_available_anchors(seed, removal_prob) */
  drawRemoved() {
    const P = this.P, R = this.R, rng = MT(P.seed), out = new Set(), names = [];
    if (!(P.drop > 0)) return { cids: out, names };
    const cands = [...R.removable].sort();
    for (const nm of cands) if (rng.random() < P.drop) { names.push(nm); out.add(this.topo.cid[nm]); }
    return { cids: out, names };
  }
  pointAvailable(c) {
    const rm = this.removed.cids; if (rm.has(c)) return false;
    const sa = this.topo.supportAnchor[c]; return sa === undefined || !rm.has(sa);
  }
  threadAvailable(t) { return this.pointAvailable(t.a) && this.pointAvailable(t.b); }
  applyParams() {
    const P = this.P, w = this.world;
    w.g = +P.g; w.exag = +P.exag; w.cn = +P.cn; w.ct = 0.5 * P.cn; w.cnum = +P.damp;
    w.support.A = P.amp / 100; w.support.f = +P.freq; w.support.phi = P.phase * Math.PI / 180;
    for (let s = 0; s < w.ns; s++) { const ty = this.segType[s]; w.EA[s] = P["EA_" + ty] * 1e-3; w.mu[s] = P["mu_" + ty] * 1e-7; }
    this.capIndex = this.topo.steps.findIndex(st => st.ce > P.cap); if (this.capIndex < 0) this.capIndex = this.topo.steps.length;
    this.meanWind();
  }
  meanWind() { const th = this.P.dir * Math.PI / 180; this.world.W = [this.P.wind * Math.cos(th), this.P.wind * Math.sin(th)]; }
  slackOf(ty) { return this.P["slack_" + ty] / 100; }
  /* ---- activate a thread; geometry = 'plan' or current positions ---- */
  activateThread(t, mode) {
    const w = this.world, X = w.x;
    const pos = c => [X[2 * c], X[2 * c + 1]];
    const active = c => w.fixed[c] || w.deg[c] > 0;
    if (mode !== "plan") {
      // place inactive points of this thread on the chord between its (current) endpoints
      const A = active(t.a) ? pos(t.a) : [this.planX[2 * t.a] + w.supportDisp(t.a, w.t), this.planX[2 * t.a + 1]];
      const B = active(t.b) ? pos(t.b) : [this.planX[2 * t.b] + w.supportDisp(t.b, w.t), this.planX[2 * t.b + 1]];
      t.pts.forEach((c, j) => { if (!active(c)) { const u = t.us[j]; X[2 * c] = A[0] + u * (B[0] - A[0]); X[2 * c + 1] = A[1] + u * (B[1] - A[1]); w.v[2 * c] = w.v[2 * c + 1] = 0; } });
      for (const sp of t.spans) {
        const k = sp.nodes.length - 1, a = sp.p0, b = sp.p1;
        for (let j = 1; j < k; j++) { const n = sp.nodes[j], u = j / k; X[2 * n] = X[2 * a] + u * (X[2 * b] - X[2 * a]); X[2 * n + 1] = X[2 * a + 1] + u * (X[2 * b + 1] - X[2 * a + 1]); w.v[2 * n] = w.v[2 * n + 1] = 0; }
      }
    }
    const sl = this.slackOf(t.type);
    for (const s of t.segs) { w.L0[s] = Math.max(1e-6, w.segLen(s)) * (1 + sl); w.activate(s, 1); }
    // solver starting point only: a slack span is started on a downward parabola of its own rest length
    // (the equilibrium is unique for g > 0; with g = 0 a slack thread stays straight)
    if (sl > 0 && w.g > 0) for (const sp of t.spans) hangParabola(X, sp.nodes, sp.segs.reduce((acc, s) => acc + w.L0[s], 0));
    t.on = true;
  }
  deactivateThread(t) { for (const s of t.segs) this.world.activate(s, 0); t.on = false; }
  /* ---- history-free build: all threads alive after step k, laid on the planned straight lines ---- */
  buildTo(k) {
    const T = this.topo, w = this.world;
    if (k === "final" || k === undefined || k === null) k = T.steps.length;
    k = Math.max(0, Math.min(T.steps.length, Math.round(k)));
    const kmax = Math.min(k, this.capIndex);
    w.t = 0; w.x.set(this.planX); w.v.fill(0);
    for (let s = 0; s < w.ns; s++) if (w.on[s]) w.activate(s, 0);
    for (const t of T.threads) t.on = false;
    for (let i = 0; i < w.n; i++) w.setFixed(i, T.pts[i] && T.pts[i].fixed && !this.detached.has(i) ? 1 : 0);
    w.setFixed(T.hub, kmax <= T.markStep ? 1 : 0);     // construction scaffold (see notes)
    w.placeFixed(0, false, 1);
    for (const t of T.threads) if (t.step < kmax && t.rm >= kmax && this.threadAvailable(t)) this.activateThread(t, "plan");
    this.k = kmax; this.act = null; this.stopped = k > this.capIndex ? "silk capacity (perturbations.py)" : (kmax >= T.steps.length ? "complete" : "");
    this.spiderPt = T.spiderAt[kmax]; this.gustXi = 0; this.gustRng = MT(Number(this.P.seed) + 1);
    this.trace = []; this.lastSettle = null;
    this.setSpiderLoad();
    return this.k;
  }
  /* ---- path finding for walks: active thread spans + rig walkable edges (operators._can_reach) ---- */
  findPath(from, to) {
    const T = this.topo, w = this.world, P = T.pts;
    if (from === to) return { nodes: [from], loaded: [] };
    const adj = new Map(); const addE = (a, b, len, nodes, loaded) => { if (!adj.has(a)) adj.set(a, []); adj.get(a).push({ b, len, nodes, loaded }); };
    for (const t of T.threads) if (t.on) for (const sp of t.spans) {
      const len = Math.hypot(P[sp.p1].x - P[sp.p0].x, P[sp.p1].y - P[sp.p0].y);
      addE(sp.p0, sp.p1, len, sp.nodes, true); addE(sp.p1, sp.p0, len, [...sp.nodes].reverse(), true);
    }
    for (const [an, bn] of this.R.walkable) {
      const a = T.cid[an], b = T.cid[bn]; if (this.removed.cids.has(a) || this.removed.cids.has(b)) continue;
      const len = Math.hypot(P[b].x - P[a].x, P[b].y - P[a].y);
      addE(a, b, len, [a, b], false); addE(b, a, len, [b, a], false);
    }
    const dist = new Map([[from, 0]]), prev = new Map(), done = new Set();
    for (;;) {
      let u = -1, best = Infinity; for (const [c, d] of dist) if (!done.has(c) && d < best) { best = d; u = c; }
      if (u < 0 || u === to) break; done.add(u);
      for (const e of adj.get(u) || []) { const nd = best + e.len; if (nd < (dist.has(e.b) ? dist.get(e.b) : Infinity)) { dist.set(e.b, nd); prev.set(e.b, { from: u, e }); } }
    }
    if (!prev.has(to)) return { nodes: [from, to], loaded: [false] };   // not connected: straight move, no load
    const chain = []; let c = to; while (c !== from) { const p = prev.get(c); chain.unshift(p.e); c = p.from; }
    const nodes = [from], loaded = [];
    for (const e of chain) for (let j = 1; j < e.nodes.length; j++) { nodes.push(e.nodes[j]); loaded.push(e.loaded); }
    return { nodes, loaded };
  }
  /* ---- construction playback ---- */
  startAction() {
    const T = this.topo, st = T.steps[this.k];
    if (this.k >= this.capIndex) { this.stopped = "silk capacity (perturbations.py)"; return false; }
    for (const t of st.rmv) if (t.on) this.deactivateThread(t);
    let path = null;
    for (const t of st.add) if (this.threadAvailable(t)) { this.activateThread(t, "current"); path = { nodes: t.nodes, loaded: t.nodes.slice(1).map(() => true) }; }
    if (!path) path = (st.name === "walk" || st.name === "reel_up") ? this.findPath(st.from, st.to) : { nodes: [st.to], loaded: [] };
    const dur = Math.max(st.energy / Math.max(this.P.speed, 1e-6), 0.15);
    this.act = { k: this.k, path, dur, el: 0 };
    return true;
  }
  finishAction() {
    const T = this.topo, st = T.steps[this.k];
    if (st.name === "mark_proto_hub" && !this.detached.has(T.hub)) this.world.setFixed(T.hub, 0);
    this.spiderPt = st.to; this.act = null; this.k++;
    if (this.k >= T.steps.length) this.stopped = "complete";
  }
  stepAction() { // complete the current or next action instantly (physics not advanced)
    if (this.k >= this.topo.steps.length || this.stopped === "silk capacity (perturbations.py)") return;
    if (!this.act && !this.startAction()) return;
    this.finishAction(); this.setSpiderLoad();
  }
  spiderLocation() {
    const w = this.world, X = w.x;
    if (!this.act) { const c = this.spiderPt; return { x: X[2 * c], y: X[2 * c + 1], i: c, j: c, u: 0, loaded: true }; }
    const { nodes, loaded } = this.act.path, fr = Math.min(1, this.act.el / this.act.dur);
    if (nodes.length === 1) { const c = nodes[0]; return { x: X[2 * c], y: X[2 * c + 1], i: c, j: c, u: 0, loaded: true }; }
    const L = []; let tot = 0; for (let q = 0; q + 1 < nodes.length; q++) { const a = nodes[q], b = nodes[q + 1]; const l = Math.hypot(X[2 * b] - X[2 * a], X[2 * b + 1] - X[2 * a + 1]); L.push(l); tot += l; }
    let s = fr * tot, q = 0; while (q < L.length - 1 && s > L[q]) { s -= L[q]; q++; }
    const u = L[q] > 0 ? Math.min(1, s / L[q]) : 0, a = nodes[q], b = nodes[q + 1];
    return { x: X[2 * a] + u * (X[2 * b] - X[2 * a]), y: X[2 * a + 1] + u * (X[2 * b + 1] - X[2 * a + 1]), i: a, j: b, u, loaded: loaded[q] };
  }
  setSpiderLoad() {
    const w = this.world; w.pmass.fill(0); w.pforce.fill(0);
    const ms = this.P.spider * 1e-6; if (!(ms > 0)) return;
    const L = this.spiderLocation(); if (!L.loaded) return;
    const put = (i, f) => { if (w.fixed[i] || w.deg[i] === 0) return; w.pmass[i] += ms * f; w.pforce[2 * i + 1] -= ms * w.g * f; };
    if (L.i === L.j) put(L.i, 1); else { put(L.i, 1 - L.u); put(L.j, L.u); }
  }
  /* ---- dynamics ---- */
  gust(h) { // Ornstein-Uhlenbeck gust process; factor = max(1 + noise_std * xi, 0.1) as stochastic.wind_noise_factor
    const tau = Math.max(1e-3, this.P.gtau), e = Math.exp(-h / tau);
    this.gustXi = this.gustXi * e + Math.sqrt(1 - e * e) * this.gustRng.normal();
    const f = Math.max(1 + this.P.gust * this.gustXi, 0.1), th = this.P.dir * Math.PI / 180;
    this.windNow = this.P.wind * f; this.world.W = [this.windNow * Math.cos(th), this.windNow * Math.sin(th)];
  }
  advance(seconds, playing) {
    const h = 1 / (60 * Math.max(1, Math.min(8, Math.round(this.P.sub)))), n = Math.max(1, Math.round(seconds / h - 1e-9));
    for (let i = 0; i < n; i++) {
      if (playing && !this.stopped) {
        if (!this.act) this.startAction();
        if (this.act) { this.act.el += h; if (this.act.el >= this.act.dur) this.finishAction(); }
      }
      this.setSpiderLoad(); this.gust(h); this.world.step(h);
      if (i % Math.max(1, Math.round(1 / (30 * h))) === 0) this.recordTrace();
    }
  }
  settle(maxIters, tol) {
    this.meanWind(); this.windNow = this.P.wind; this.setSpiderLoad();
    const r = this.world.settle(maxIters || 400, tol || 1e-6); this.lastSettle = r; this.recordTrace(); return r;
  }
  /* quasi-static sequential construction: every action is executed on the settled web left by the previous one */
  buildQuasiStatic(k, maxIters, onStep) {
    const T = this.topo; if (k === "final" || k === undefined) k = T.steps.length;
    this.buildTo(0); this.settle(maxIters);
    let worst = 0, unconv = 0;
    while (this.k < Math.min(k, T.steps.length) && !(this.stopped && this.stopped !== "complete")) {
      this.stepAction(); const r = this.settle(maxIters); worst = Math.max(worst, r.residual); if (!r.converged) unconv++;
      if (onStep) onStep(this.k);
    }
    return { step: this.k, worst_residual: worst, unconverged_steps: unconv };
  }
  recordTrace() {
    const m = this.quickMetrics();
    this.trace.push({ t: this.world.t, KE: this.world.kinetic(), wind: this.windNow === undefined ? this.P.wind : this.windNow, sag: m.sag, T: m.T });
    if (this.trace.length > 2400) this.trace.splice(0, this.trace.length - 2400);
  }
  /* ---- measurements ---- */
  /* signed perpendicular deviation of a polyline from the chord joining its ends; positive = below the chord */
  chordDev(nodes) {
    const X = this.world.x, a = nodes[0], b = nodes[nodes.length - 1], ax = X[2 * a], ay = X[2 * a + 1], dx = X[2 * b] - ax, dy = X[2 * b + 1] - ay, L = Math.hypot(dx, dy);
    if (L <= 0) return { max: 0, min: 0, at: a, chord: 0, steep: true };
    let nx = -dy / L, ny = dx / L; if (ny > 0 || (ny === 0 && nx < 0)) { nx = -nx; ny = -ny; } // normal pointing downwards
    let mx = 0, mn = 0, at = nodes[1];
    for (let j = 1; j < nodes.length - 1; j++) { const n = nodes[j], d = (X[2 * n] - ax) * nx + (X[2 * n + 1] - ay) * ny; if (d > mx) { mx = d; at = n; } if (d < mn) mn = d; }
    return { max: mx, min: mn, at, chord: L, steep: Math.abs(dy) > Math.abs(dx) };   // 'below' is ill-defined for steep chords
  }
  spanSag(sp) { return this.chordDev(sp.nodes); }
  quickMetrics() {
    let sag = 0, T = 0; const w = this.world;
    for (const t of this.topo.threads) if (t.on) { const s = this.chordDev(t.nodes); if (s.max > sag) sag = s.max; }
    for (let s = 0; s < w.ns; s++) if (w.on[s]) { const x = w.tension(s); if (x > T) T = x; }
    return { sag: sag * 100, T: T * 1e3 };
  }
  metrics() {
    const w = this.world, T = this.topo, X = w.x, cm = v => v * 100;
    const silk = {}; for (const ty of TYPES) silk[ty] = { threads: 0, rest_cm: 0, current_cm: 0, plan_chord_cm: 0 };
    const per = []; let maxSag = { cm: 0 }, maxSpan = { cm: 0 }, maxUp = { cm: 0 }, maxT = { mN: 0 }, maxStrain = { pct: 0 };
    for (const t of T.threads) if (t.on) {
      let rest = 0, cur = 0, tmax = 0, tsum = 0, strain = 0;
      for (const s of t.segs) { rest += w.L0[s]; const l = w.segLen(s); cur += l; const ten = w.tension(s); tsum += ten; if (ten > tmax) tmax = ten; strain = Math.max(strain, l / w.L0[s] - 1); }
      const td = this.chordDev(t.nodes);
      if (td.max > maxSag.cm / 100) maxSag = { cm: cm(td.max), thread: t.id, type: t.type, x_cm: cm(X[2 * td.at]), y_cm: cm(X[2 * td.at + 1]), chord_cm: cm(td.chord) };
      if (!td.steep && td.min < -maxUp.cm / 100) maxUp = { cm: -cm(td.min), thread: t.id, type: t.type };
      let spanMax = 0, spanUp = 0;
      const spans = t.spans.map(sp => { const s = this.spanSag(sp); spanMax = Math.max(spanMax, s.max); if (!s.steep) spanUp = Math.min(spanUp, s.min);
        if (s.max > maxSpan.cm / 100) maxSpan = { cm: cm(s.max), thread: t.id, type: t.type, x_cm: cm(X[2 * s.at]), y_cm: cm(X[2 * s.at + 1]), chord_cm: cm(s.chord) };
        return { chord_cm: cm(s.chord), sag_cm: cm(s.max), above_cm: -cm(s.min), steep: s.steep }; });
      silk[t.type].threads++; silk[t.type].rest_cm += cm(rest); silk[t.type].current_cm += cm(cur); silk[t.type].plan_chord_cm += t.planLen;
      if (tmax > maxT.mN / 1e3) maxT = { mN: tmax * 1e3, thread: t.id, type: t.type };
      if (strain * 100 > maxStrain.pct) maxStrain = { pct: strain * 100, thread: t.id, type: t.type };
      per.push({ id: t.id, type: t.type, a: t.an, b: t.bn, step: t.step, rest_cm: cm(rest), length_cm: cm(cur), chord_cm: cm(td.chord),
        sag_cm: cm(td.max), above_cm: td.steep ? null : -cm(td.min), steep: td.steep, span_sag_cm: cm(spanMax), span_above_cm: -cm(spanUp),
        T_max_mN: tmax * 1e3, T_mean_mN: tsum / t.segs.length * 1e3, strain_max_pct: strain * 100, spans });
    }
    const st = T.steps[Math.min(this.k, T.steps.length - 1)], done = this.k > 0 ? T.steps[this.k - 1] : null;
    const cur = this.act ? T.steps[this.act.k] : null;
    return {
      t_s: w.t, step: this.k, total_steps: T.steps.length, stopped: this.stopped,
      phase: (cur || done || st).phase, action: cur ? [cur.name, ...cur.args] : (done ? [done.name, ...done.args] : null),
      energy_cm: cur ? cur.ce : (done ? done.ce : 0),
      KE_J: w.kinetic(), wind_now_ms: this.windNow === undefined ? this.P.wind : this.windNow,
      silk_by_type: silk, max_sag: maxSag, max_span_sag: maxSpan, max_above_chord: maxUp, max_tension: maxT, max_strain: maxStrain,
      removed_anchors: this.removed.names, detached: [...this.detached].map(c => T.pts[c].names[0]),
      hub_xy_cm: [cm(X[2 * T.hub]), cm(X[2 * T.hub + 1])], hub_fixed: !!w.fixed[T.hub],
      spider_xy_cm: (() => { const L = this.spiderLocation(); return [cm(L.x), cm(L.y)]; })(),
      settle: this.lastSettle, nodes_free: (w._prepare(), w.free.length), segments_on: w.on.reduce((a, b) => a + b, 0),
      threads: per,
    };
  }
  threads() {
    const w = this.world, X = w.x, out = [];
    for (const t of this.topo.threads) if (t.on) out.push({ id: t.id, type: t.type, a: t.an, b: t.bn, step: t.step,
      pts: t.nodes.map(n => [X[2 * n] * 100, X[2 * n + 1] * 100]), T_mN: t.segs.map(s => w.tension(s) * 1e3),
      plan: [[this.topo.pts[t.a].x, this.topo.pts[t.a].y], [this.topo.pts[t.b].x, this.topo.pts[t.b].y]] });
    return out;
  }
  detach(name) { // structural failure (perturbations.py): anchor point lets go, its threads fall
    const c = this.topo.cid[name]; if (c === undefined) return false;
    this.detached.add(c); this.world.setFixed(c, 0); return true;
  }
}

function hangParabola(X, nodes, S) {
  const a = nodes[0], b = nodes[nodes.length - 1], L = Math.hypot(X[2 * b] - X[2 * a], X[2 * b + 1] - X[2 * a + 1]);
  if (!(S > L)) return; const d = Math.sqrt(3 * L * (S - L) / 8), k = nodes.length - 1;
  for (let j = 1; j < k; j++) { const u = j / k; X[2 * nodes[j] + 1] -= 4 * d * u * (1 - u); }
}

/* ===================================================================
   Validation: one thread between two level supports, same World/solver,
   compared with the elastic catenary, the rigid catenary and the parabola.
   =================================================================== */
function elasticCatenary(Lspan, L0, w, EA) {
  // Lagrangian coordinate p in [0, L0]; level supports; V = w L0 / 2 at each support
  const V = w * L0 / 2;
  const xEnd = H => H * L0 / EA + (H / w) * (Math.asinh(V / H) - Math.asinh((V - w * L0) / H));
  if (xEnd(1e-30) >= Lspan) return null; // would need compression: not a hanging cable
  let lo = 1e-30, hi = 1; while (xEnd(hi) < Lspan) hi *= 2;
  for (let i = 0; i < 300; i++) { const m = Math.sqrt(lo * hi); if (xEnd(m) > Lspan) hi = m; else lo = m; if (hi / lo - 1 < 1e-15) break; }
  const H = Math.sqrt(lo * hi);
  const at = p => [H * p / EA + (H / w) * (Math.asinh(V / H) - Math.asinh((V - w * p) / H)),
    -((V * p - w * p * p / 2) / EA + (Math.hypot(H, V) - Math.hypot(H, V - w * p)) / w)];
  return { H, V, at, sag: -at(L0 / 2)[1], Tmax: Math.hypot(H, V) };
}
function runValidation(o) {
  // o: {L (cm), slack (%), mu (ug/cm), EA (mN), exag, g, N}
  const N = Math.max(2, Math.round(o.N)), Ls = o.L / 100, L0 = Ls * (1 + o.slack / 100), EA = o.EA * 1e-3, mu = o.mu * 1e-7;
  const w = new World(N + 1, N);
  for (let s = 0; s < N; s++) w.setSeg(s, s, s + 1);
  for (let i = 0; i <= N; i++) { w.x[2 * i] = Ls * i / N; w.x[2 * i + 1] = 0; }
  w.base.set(w.x); w.setFixed(0, 1); w.setFixed(N, 1);
  for (let s = 0; s < N; s++) { w.L0[s] = L0 / N; w.EA[s] = EA; w.mu[s] = mu; w.activate(s, 1); }
  w.g = o.g; w.exag = o.exag;
  if (o.g > 0 && o.slack > 0) hangParabola(w.x, Array.from({ length: N + 1 }, (_, i) => i), L0);   // starting point only
  const t0 = (typeof performance !== "undefined" ? performance.now() : Date.now());
  const st = w.settle(2000, 1e-7);
  const ms = (typeof performance !== "undefined" ? performance.now() : Date.now()) - t0;
  const wl = mu * o.exag * o.g; // weight per unstretched length, N/m
  const cat = wl > 0 ? elasticCatenary(Ls, L0, wl, EA) : null;
  const sim = []; for (let i = 0; i <= N; i++) sim.push([w.x[2 * i], w.x[2 * i + 1]]);
  const Tsim = []; for (let s = 0; s < N; s++) Tsim.push(w.tension(s));
  const out = { N, sim_cm: sim.map(p => [p[0] * 100, p[1] * 100]), settle: st, ms, w_N_per_m: wl };
  if (!cat) return out;
  // compare node by node: node i carries Lagrangian coordinate p_i = i L0 / N
  let err = 0, errY = 0;
  for (let i = 0; i <= N; i++) { const c = cat.at(i * L0 / N); err = Math.max(err, Math.hypot(sim[i][0] - c[0], sim[i][1] - c[1])); }
  const H = cat.H, a = H / wl;                            // rigid catenary with the same H and w
  const rigid = x => a * Math.cosh((x - Ls / 2) / a) - a * Math.cosh(Ls / 2 / a);
  const dPar = wl * Ls * Ls / (8 * H), par = x => -4 * dPar * x * (Ls - x) / (Ls * Ls);
  // vertical deviation of the curves from the elastic catenary, sampled densely
  let eRigid = 0, ePar = 0; const curves = { elastic: [], rigid: [], parabola: [] };
  for (let j = 0; j <= 400; j++) {
    const c = cat.at(j * L0 / 400); curves.elastic.push([c[0] * 100, c[1] * 100]);
    eRigid = Math.max(eRigid, Math.abs(rigid(c[0]) - c[1])); ePar = Math.max(ePar, Math.abs(par(c[0]) - c[1]));
  }
  for (let j = 0; j <= 200; j++) { const x = Ls * j / 200; curves.rigid.push([x * 100, rigid(x) * 100]); curves.parabola.push([x * 100, par(x) * 100]); }
  for (let i = 0; i <= N; i++) { const x = sim[i][0]; const k = Math.min(399, Math.floor(x / Ls * 400)); errY = Math.max(errY, Math.abs(sim[i][1] - cat.at(i * L0 / N)[1])); }
  const Hsim = Tsim[0] * (sim[1][0] - sim[0][0]) / Math.hypot(sim[1][0] - sim[0][0], sim[1][1] - sim[0][1]);
  const sagSim = -sim[Math.floor(N / 2)][1] * (N % 2 === 0 ? 1 : 1);
  const resid = []; for (let i = 0; i <= N; i++) { const c = cat.at(i * L0 / N); resid.push([sim[i][0] * 100, (sim[i][1] - c[1]) * 1e4]); } // um
  return Object.assign(out, {
    H_exact_mN: H * 1e3, H_sim_mN: Hsim * 1e3, Tmax_exact_mN: cat.Tmax * 1e3, Tmax_sim_mN: Math.max(...Tsim) * 1e3,
    sag_exact_cm: cat.sag * 100, sag_sim_cm: (N % 2 === 0 ? -sim[N / 2][1] : -0.5 * (sim[(N - 1) / 2][1] + sim[(N + 1) / 2][1])) * 100,
    sag_parabola_formula_cm: dPar * 100, sag_rigid_catenary_cm: (a * Math.cosh(Ls / 2 / a) - a) * 100,
    err_sim_max_cm: err * 100, err_sim_rel_sag: err / cat.sag, err_parabola_max_cm: ePar * 100, err_rigid_max_cm: eRigid * 100,
    curves, resid_um: resid, a_cm: a * 100,
  });
}

const CORE = { MT, World, WebSim, buildTopology, runValidation, elasticCatenary, defaultParams, TYPES, TYPE_LABEL, TYPE_COLOR, TYPE_DEFAULTS, PHASE_LABEL };
if (typeof module !== "undefined") module.exports = CORE;
