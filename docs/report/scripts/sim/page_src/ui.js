/* ==========================================================================
   Page: parameter table, canvas rendering, playback, URL parameters, simAPI.
   ========================================================================== */
(function () {
  const C = CORE, R = REPO, $ = id => document.getElementById(id);
  const P = C.defaultParams(R);

  /* ---------------- URL parameters ---------------- */
  const STR = new Set(["mode", "panel", "vtype", "detach"]);
  function parseVal(k, v) {
    if (STR.has(k)) return v;
    if (k === "cap") { const x = Number(v); return (!isFinite(x) || x <= 0) ? Infinity : x; }
    const x = Number(v); return isFinite(x) ? x : P[k];
  }
  const q = new URLSearchParams(location.search);
  for (const [k, v] of q) {
    if (k === "slack") { for (const ty of C.TYPES) P["slack_" + ty] = Number(v); continue; }
    if (k in P) P[k] = parseVal(k, v);
  }
  if (P.ui === 0) document.body.classList.add("noui");
  let running = q.has("run") ? q.get("run") !== "0" : P.ui !== 0;
  let playing = P.mode === "play" && running && P.step < 0;

  /* ---------------- simulation ---------------- */
  let sim = new C.WebSim(R, P);
  let val = null;                               // last validation result
  const REBUILD = new Set(["ds", "drop", "seed"]);
  function applyDetach() { if (P.detach) for (const nm of String(P.detach).split(",")) if (nm) sim.detach(nm.trim()); }

  function initialState() {
    if (P.mode === "final" || P.step >= 0) { sim.buildTo(P.step >= 0 ? P.step : "final"); sim.settle(200); }
    else { sim.buildTo(0); sim.settle(50); }
    applyDetach();
    if (P.t > 0) sim.advance(P.t, P.mode === "play" && P.step < 0);
  }
  initialState();

  /* ---------------- parameter table ---------------- */
  const SPEC = {          // min, max, step, log?
    speed: [0.5, 100, 0.5], spider: [0, 300, 1], cap: [0, 2400, 10],
    g: [0, 20, 0.01], exag: [1, 1e5, 1, true], ds: [0.2, 2, 0.05],
    wind: [0, 10, 0.05], dir: [-180, 180, 1], gust: [0, 1, 0.01], gtau: [0.1, 5, 0.1], cn: [0, 3e-4, 1e-6],
    amp: [0, 15, 0.1], freq: [0, 0.2, 0.001], phase: [-180, 180, 1],
    drop: [0, 1, 0.01], seed: [0, 99999, 1],
    sub: [1, 8, 1], damp: [0, 10, 0.05],
    vL: [1, 30, 0.5], vslack: [-1, 20, 0.05], vN: [2, 200, 1],
  };
  const fmt = (k, v) => k === "cn" ? Number(v).toExponential(1) : (k === "cap" && !isFinite(v) ? 0 : +Number(v).toPrecision(6));
  const inputs = {};
  for (const tr of document.querySelectorAll("tr[data-p]")) {
    const k = tr.dataset.p, [mn, mx, st, lg] = SPEC[k];
    const num = document.createElement("input"); num.type = "number"; num.step = st; num.min = mn; num.max = mx;
    const rng = document.createElement("input"); rng.type = "range";
    if (lg) { rng.min = 0; rng.max = 1000; rng.step = 1; } else { rng.min = mn; rng.max = mx; rng.step = st; }
    tr.children[1].appendChild(num); tr.children[2].appendChild(rng);
    const toR = v => lg ? 1000 * Math.log(Math.max(v, mn) / mn) / Math.log(mx / mn) : v;
    const fromR = r => lg ? +(mn * Math.pow(mx / mn, r / 1000)).toPrecision(3) : Number(r);
    inputs[k] = { num, rng, show: () => { num.value = fmt(k, P[k]); rng.value = toR(k === "cap" && !isFinite(P[k]) ? 0 : P[k]); } };
    num.addEventListener("change", () => setParam(k, num.value === "" ? 0 : Number(num.value)));
    rng.addEventListener("input", () => setParam(k, fromR(rng.value)));
  }
  const mat = $("mattab");
  for (const ty of C.TYPES) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td><span class="ls" style="border-top:2px solid ${C.TYPE_COLOR[ty]}"></span>${C.TYPE_LABEL[ty]}</td>`;
    for (const f of ["mu", "EA", "slack"]) {
      const td = document.createElement("td"), inp = document.createElement("input");
      inp.type = "number"; inp.step = f === "slack" ? 0.1 : (f === "EA" ? 1 : 0.01); inp.min = f === "slack" ? -2 : 0;
      const k = f + "_" + ty; inputs[k] = { num: inp, show: () => { inp.value = +Number(P[k]).toPrecision(6); } };
      inp.addEventListener("change", () => setParam(k, Number(inp.value)));
      td.appendChild(inp); tr.appendChild(td);
    }
    mat.appendChild(tr);
  }
  const vsel = $("vtype"); for (const ty of C.TYPES) { const o = document.createElement("option"); o.value = ty; o.textContent = C.TYPE_LABEL[ty]; vsel.appendChild(o); }
  vsel.addEventListener("change", () => setParam("vtype", vsel.value));
  const dsel = $("detsel"); for (const nm of R.removable) { const o = document.createElement("option"); o.value = nm; o.textContent = nm; dsel.appendChild(o); }

  function showParams() {
    for (const k in inputs) inputs[k].show();
    $("ghost").checked = !!P.ghost; vsel.value = P.vtype;
    for (const b of document.querySelectorAll("button[data-k]")) b.classList.toggle("on", String(P[b.dataset.k]) === b.dataset.v);
    for (const b of document.querySelectorAll("button[data-amp]")) b.classList.toggle("on", +b.dataset.amp === +P.amp && (+P.amp === 0 || +b.dataset.freq === +P.freq));
    for (const r of document.querySelectorAll(".vrow")) r.style.display = P.panel === "validate" ? "" : "none";
    $("legend").style.visibility = P.panel === "validate" ? "hidden" : "";
    $("bRun").classList.toggle("on", running); $("bRun").textContent = running ? "Physics on" : "Physics off";
    $("bPlay").classList.toggle("on", playing); $("bPlay").textContent = playing ? "Pause" : "Play";
  }

  function setParam(k, v, quiet) {
    if (k === "cap" && !(v > 0)) v = Infinity;
    P[k] = v;
    if (k === "panel") { if (v === "validate") runVal(); }
    else if (k === "mode") { if (v === "play") { sim.buildTo(0); sim.settle(50); playing = running = true; } else { playing = false; sim.buildTo("final"); sim.settle(200); } }
    else if (REBUILD.has(k) || k.startsWith("slack_")) { const kk = sim.k; sim.P = P; sim.rebuild(); sim.buildTo(kk); sim.settle(200); }
    else if (k === "cap") { sim.applyParams(); const kk = Math.min(sim.k, sim.capIndex); sim.buildTo(kk); sim.settle(200); }
    else sim.applyParams();
    if (k.startsWith("v") || k.startsWith("mu_") || k.startsWith("EA_") || k === "g" || k === "exag") if (P.panel === "validate") runVal();
    if (!quiet) { showParams(); render(); }
  }

  /* ---------------- buttons ---------------- */
  for (const b of document.querySelectorAll("button[data-k]")) b.addEventListener("click", () => setParam(b.dataset.k, isNaN(+b.dataset.v) ? b.dataset.v : +b.dataset.v));
  for (const b of document.querySelectorAll("button[data-amp]")) b.addEventListener("click", () => { P.amp = +b.dataset.amp; P.freq = +b.dataset.freq; sim.applyParams(); showParams(); render(); });
  $("ghost").addEventListener("change", e => { P.ghost = e.target.checked ? 1 : 0; render(); });
  function jump(k) { playing = false; sim.buildTo(k); sim.settle(200); applyDetach(); showParams(); render(); }
  $("bReset").onclick = () => jump(0);
  $("bBack").onclick = () => jump(Math.max(0, sim.k - 1));
  $("bFwd").onclick = () => { playing = false; sim.stepAction(); showParams(); render(); };
  $("bEnd").onclick = () => jump("final");
  $("bPlay").onclick = () => { playing = !playing; if (playing) { running = true; if (sim.stopped === "complete") { sim.buildTo(0); sim.settle(50); } } showParams(); };
  $("bRun").onclick = () => { running = !running; if (!running) playing = false; showParams(); };
  $("bSettle").onclick = () => { sim.settle(300); render(); };
  $("scrub").addEventListener("input", e => jump(+e.target.value));
  $("bDetach").onclick = () => { sim.detach(dsel.value); running = true; showParams(); render(); };
  $("bRestore").onclick = () => { sim.detached.clear(); P.detach = ""; jump(sim.k); };

  /* ---------------- legend ---------------- */
  $("legend").innerHTML = C.TYPES.map(ty => `<span><span class="ls" style="border-top:${ty === "frame" ? 3 : 2}px solid ${C.TYPE_COLOR[ty]}"></span>${C.TYPE_LABEL[ty]}</span>`).join("") +
    `<span><span class="ls" style="border-top:3px solid #c4c4c4"></span>rig (walkable_edges)</span><span><span class="ls" style="border-top:1px dashed #9a9a9a"></span>cross-bar</span>` +
    `<span><span class="sq"></span>attachment on rig</span><span><span class="sqo"></span>removed / detached anchor</span><span><span class="sq" style="width:8px;height:8px;transform:rotate(45deg)"></span>spider</span>`;

  /* ---------------- canvas ---------------- */
  const cv = $("web"), box = $("canvasbox");
  let W = 0, H = 0, dpr = 1;
  function resize() {
    dpr = window.devicePixelRatio || 1; W = box.clientWidth; H = box.clientHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); cv.style.width = W + "px"; cv.style.height = H + "px";
    for (const id of ["pKE", "pW", "pS", "pT"]) { const c = $(id); c.width = Math.round(c.clientWidth * dpr); c.height = Math.round(66 * dpr); }
    render();
  }
  window.addEventListener("resize", resize);
  // re-fit the canvas whenever its container changes size (e.g. the transport bar changes height)
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(() => { if (box.clientWidth !== W || box.clientHeight !== H) resize(); }).observe(box);

  const TMAP = ["#fdd49e", "#fdbb84", "#fc8d59", "#ef6548", "#d7301f", "#b30000", "#7f0000", "#3d0000"];
  function rampColor(u) { u = Math.max(0, Math.min(1, u)) * (TMAP.length - 1); const i = Math.min(TMAP.length - 2, Math.floor(u)), f = u - i;
    const h = s => [1, 3, 5].map(j => parseInt(s.substr(j, 2), 16)); const a = h(TMAP[i]), b = h(TMAP[i + 1]);
    return `rgb(${a.map((x, j) => Math.round(x + f * (b[j] - x))).join(",")})`; }

  function niceStep(span, n) { const raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p; return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p; }

  function axes(ctx, X0, X1, Y0, Y1, px, py, xl, yl, ox, oy, pw, ph) {
    ctx.strokeStyle = "#000"; ctx.lineWidth = 1; ctx.fillStyle = "#000"; ctx.font = "11px Helvetica Neue, Helvetica, Arial, sans-serif";
    ctx.strokeRect(Math.round(ox) + 0.5, Math.round(oy) + 0.5, Math.round(pw), Math.round(ph));
    const sx = niceStep(X1 - X0, Math.max(3, pw / 70)), sy = niceStep(Y1 - Y0, Math.max(3, ph / 55));
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    for (let v = Math.ceil(X0 / sx) * sx; v <= X1 + 1e-9; v += sx) { const x = Math.round(px(v)) + 0.5; ctx.beginPath(); ctx.moveTo(x, oy + ph); ctx.lineTo(x, oy + ph + 4); ctx.stroke(); ctx.fillText(+v.toFixed(6), x, oy + ph + 6); }
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (let v = Math.ceil(Y0 / sy) * sy; v <= Y1 + 1e-9; v += sy) { const y = Math.round(py(v)) + 0.5; ctx.beginPath(); ctx.moveTo(ox, y); ctx.lineTo(ox - 4, y); ctx.stroke(); ctx.fillText(+v.toFixed(6), ox - 6, y); }
    ctx.textAlign = "center"; ctx.textBaseline = "bottom"; ctx.fillText(xl, ox + pw / 2, oy + ph + 34);
    ctx.save(); ctx.translate(ox - 38, oy + ph / 2); ctx.rotate(-Math.PI / 2); ctx.textBaseline = "middle"; ctx.fillText(yl, 0, 0); ctx.restore();
  }

  function renderWeb(ctx) {
    const w = sim.world, X = w.x, T = sim.topo, A = Math.abs(P.amp);
    const X0 = -1 - A, X1 = R.frame[0] + 1 + A, Y0 = -1, Y1 = R.frame[1] + 1;
    // annotations live in the margin above the axes: right line = gravity/supports, left line = wind/removed anchors
    const FONT = "11px Helvetica Neue, Helvetica, Arial, sans-serif"; ctx.font = FONT;
    const uw = sim.windNow === undefined ? +P.wind : sim.windNow;
    let rightTxt = `g = ${(+P.g).toFixed(2)} m/s\u00B2, X = ${+(+P.exag).toPrecision(3)}`;
    if (P.amp > 0) rightTxt += `;  supports A = ${P.amp} cm, f = ${P.freq} Hz, t = ${w.t.toFixed(2)} s`;
    let leftTxt = P.wind > 0 ? `wind ${uw.toFixed(2)} m/s` : "";
    if (sim.removed.names.length) leftTxt += (leftTxt ? ";  " : "") + `removed (p = ${P.drop}, seed ${P.seed}): ${sim.removed.names.map(n => n.replace("anchor_", "")).join(", ")}`;
    const arrowW = P.wind > 0 ? 26 : 0, leftW = leftTxt ? arrowW + ctx.measureText(leftTxt).width : 0, rightW = ctx.measureText(rightTxt).width;
    const mL = 52, mR = P.tmap ? 70 : 14, mB = 44;
    const oneLine = leftW + rightW + 24 <= W - mL - mR, mT = leftTxt && !oneLine ? 38 : 22;
    const s = Math.min((W - mL - mR) / (X1 - X0), (H - mT - mB) / (Y1 - Y0));
    const pw = s * (X1 - X0), ph = s * (Y1 - Y0), ox = mL + (W - mL - mR - pw) / 2, oy = mT + (H - mT - mB - ph) / 2;
    const px = v => ox + (v - X0) * s, py = v => oy + (Y1 - v) * s;
    const nx = i => px(X[2 * i] * 100), ny = i => py(X[2 * i + 1] * 100);
    axes(ctx, X0, X1, Y0, Y1, px, py, "x (cm)", "y (cm)", ox, oy, pw, ph);
    ctx.save(); ctx.beginPath(); ctx.rect(ox + 1, oy + 1, pw - 1, ph - 1); ctx.clip();
    // rig
    ctx.lineCap = "butt"; ctx.strokeStyle = "#c4c4c4"; ctx.lineWidth = 3;
    const rp = c => [px(T.pts[c].x + w.supportDisp(c, w.t) * 100), py(T.pts[c].y)];
    for (const [a, b] of R.walkable) { const p = rp(T.cid[a]), r = rp(T.cid[b]); ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(r[0], r[1]); ctx.stroke(); }
    ctx.setLineDash([4, 4]); ctx.lineWidth = 1; ctx.strokeStyle = "#9a9a9a";
    { const p = rp(T.cid.crossbar_left), r = rp(T.cid.crossbar_right); ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(r[0], r[1]); ctx.stroke(); }
    ctx.setLineDash([]);
    // straight-line plan
    if (P.ghost) { ctx.strokeStyle = "#9a9a9a"; ctx.lineWidth = 0.8; ctx.setLineDash([2, 3]);
      for (const t of T.threads) if (t.on) { ctx.beginPath(); ctx.moveTo(px(T.pts[t.a].x), py(T.pts[t.a].y)); ctx.lineTo(px(T.pts[t.b].x), py(T.pts[t.b].y)); ctx.stroke(); }
      ctx.setLineDash([]); }
    // threads
    const order = ["dragline", "bridge", "proto_radius", "auxiliary_spiral", "capture_spiral", "radius", "frame"];
    let tmax = 0; if (P.tmap) for (let s2 = 0; s2 < w.ns; s2++) if (w.on[s2]) tmax = Math.max(tmax, w.tension(s2));
    const tlo = tmax / 1000;
    ctx.lineJoin = "round";
    for (const ty of order) for (const t of T.threads) if (t.on && t.type === ty) {
      const lw = ty === "frame" ? 1.6 : (ty === "radius" || ty === "proto_radius" ? 1.3 : 1.0);
      if (!P.tmap) {
        ctx.strokeStyle = C.TYPE_COLOR[ty]; ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(nx(t.nodes[0]), ny(t.nodes[0]));
        for (let j = 1; j < t.nodes.length; j++) ctx.lineTo(nx(t.nodes[j]), ny(t.nodes[j])); ctx.stroke();
      } else {
        ctx.lineWidth = lw + 0.4;
        for (const s2 of t.segs) { const ten = w.tension(s2);
          ctx.strokeStyle = ten <= tlo ? "#cfcfcf" : rampColor(Math.log(ten / tlo) / Math.log(1000));
          ctx.beginPath(); ctx.moveTo(nx(w.sa[s2]), ny(w.sa[s2])); ctx.lineTo(nx(w.sb[s2]), ny(w.sb[s2])); ctx.stroke(); }
      }
    }
    // attachment points on the rig, removed / detached anchors
    const used = new Set(); for (const t of T.threads) if (t.on) { used.add(t.a); used.add(t.b); }
    ctx.fillStyle = "#000";
    for (const c of used) if (w.fixed[c] && T.pts[c].fixed) { ctx.fillRect(Math.round(nx(c)) - 2, Math.round(ny(c)) - 2, 5, 5); }
    ctx.strokeStyle = "#000"; ctx.lineWidth = 1;
    const hollow = [...sim.removed.cids, ...sim.detached];
    for (const c of hollow) { const x = Math.round(sim.detached.has(c) ? nx(c) : rp(c)[0]), y = Math.round(sim.detached.has(c) ? ny(c) : rp(c)[1]);
      ctx.fillStyle = "#fff"; ctx.fillRect(x - 4, y - 4, 8, 8); ctx.strokeRect(x - 3.5, y - 3.5, 7, 7); }
    // spider
    if (P.spider > 0) { const L = sim.spiderLocation(), x = px(L.x * 100), y = py(L.y * 100);
      ctx.fillStyle = "#000"; ctx.beginPath(); ctx.moveTo(x, y - 5.5); ctx.lineTo(x + 5.5, y); ctx.lineTo(x, y + 5.5); ctx.lineTo(x - 5.5, y); ctx.closePath(); ctx.fill(); }
    ctx.restore();
    // margin annotations (never inside the axes)
    ctx.font = FONT; ctx.fillStyle = "#000"; ctx.strokeStyle = "#000"; ctx.textBaseline = "middle";
    const yR = oy - 9, yL = oneLine ? oy - 9 : oy - 25;
    ctx.textAlign = "right"; ctx.fillText(rightTxt, ox + pw, yR);
    if (leftTxt) {
      let x = ox;
      if (P.wind > 0) { const th = P.dir * Math.PI / 180, L = 9, cx = ox + 10, x0 = cx - L * Math.cos(th), y0 = yL + L * Math.sin(th), x1 = cx + L * Math.cos(th), y1 = yL - L * Math.sin(th);
        ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        const a = Math.atan2(y1 - y0, x1 - x0); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - 6 * Math.cos(a - 0.4), y1 - 6 * Math.sin(a - 0.4)); ctx.lineTo(x1 - 6 * Math.cos(a + 0.4), y1 - 6 * Math.sin(a + 0.4)); ctx.closePath(); ctx.fill();
        x += arrowW; }
      ctx.textAlign = "left"; ctx.fillText(leftTxt, x, yL);
    }
    // tension colour bar
    if (P.tmap && tmax > 0) {
      const bx = ox + pw + 14, by = oy + 20, bh = Math.min(220, ph - 40), bw = 10;
      for (let j = 0; j < bh; j++) { ctx.fillStyle = rampColor(1 - j / bh); ctx.fillRect(bx, by + j, bw, 1.5); }
      ctx.strokeStyle = "#000"; ctx.lineWidth = 1; ctx.strokeRect(bx + 0.5, by + 0.5, bw, bh);
      ctx.fillStyle = "#000"; ctx.textAlign = "left"; ctx.textBaseline = "middle";
      for (const f of [0, 1 / 3, 2 / 3, 1]) { const val = tlo * Math.pow(1000, f) * 1e3; ctx.fillText(val.toPrecision(2), bx + bw + 4, by + bh * (1 - f)); }
      ctx.textBaseline = "bottom"; ctx.fillText("T (mN)", bx - 2, by - 4);
      ctx.fillStyle = "#cfcfcf"; ctx.fillRect(bx, by + bh + 10, bw, 6); ctx.fillStyle = "#000"; ctx.textBaseline = "middle"; ctx.fillText("slack", bx + bw + 4, by + bh + 13);
    }
  }

  function renderVal(ctx) {
    if (!val || !val.curves) { ctx.fillStyle = "#000"; ctx.fillText("No sag: set g > 0 and a positive weight.", 60, 40); return; }
    const L = P.vL, sag = val.sag_exact_cm, Y0 = -1.25 * Math.max(sag, 0.02), Y1 = 0.25 * Math.max(sag, 0.02);
    const mL = 60, mR = 16, top = 12, gap = 56, h1 = (H - top - gap - 48) * 0.62, h2 = (H - top - gap - 48) * 0.38;
    const pw = W - mL - mR, X0 = -0.02 * L, X1 = 1.02 * L;
    let px = v => mL + (v - X0) / (X1 - X0) * pw, py = v => top + (Y1 - v) / (Y1 - Y0) * h1;
    axes(ctx, X0, X1, Y0, Y1, px, py, "x (cm)", "y (cm)", mL, top, pw, h1);
    const line = (pts, col, lw, dash) => { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.setLineDash(dash || []); ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(px(p[0]), py(p[1])) : ctx.moveTo(px(p[0]), py(p[1]))); ctx.stroke(); ctx.setLineDash([]); };
    ctx.save(); ctx.beginPath(); ctx.rect(mL + 1, top + 1, pw - 1, h1 - 1); ctx.clip();
    line([[0, 0], [L, 0]], "#9a9a9a", 0.8, [2, 3]);
    line(val.curves.elastic, "#000", 1.3); line(val.curves.rigid, "#0072B2", 1.1, [6, 4]); line(val.curves.parabola, "#D55E00", 1.1, [1.5, 2.5]);
    ctx.fillStyle = "#000"; for (const p of val.sim_cm) ctx.fillRect(Math.round(px(p[0])) - 2, Math.round(py(p[1])) - 2, 4, 4);
    ctx.restore();
    // legend inside
    ctx.font = "11px Helvetica Neue, Helvetica, Arial, sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "middle";
    const lg = [["#000", [], "elastic catenary (exact for this cable)"], ["#0072B2", [6, 4], "catenary y = a cosh(x/a), a = H/w"], ["#D55E00", [1.5, 2.5], "parabola, sag d = wL²/(8H)"]];
    lg.forEach(([c, d, t], i) => { const y = top + h1 * 0.55 + i * 15, x = mL + pw * 0.3; ctx.strokeStyle = c; ctx.lineWidth = 1.3; ctx.setLineDash(d); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 26, y); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = "#000"; ctx.fillText(t, x + 32, y); });
    { const y = top + h1 * 0.55 + 45, x = mL + pw * 0.3; ctx.fillRect(x + 11, y - 2, 4, 4); ctx.fillText(`simulated nodes (N = ${val.N} segments)`, x + 32, y); }
    // residual panel (um): simulation, rigid catenary and parabola minus elastic catenary
    const oy2 = top + h1 + gap; const res = val.resid_um, Ls = P.vL;
    const rig = val.curves.rigid.map(p => [p[0], 0]), parr = [];
    const ca = val.curves.elastic; const interp = x => { let j = 1; while (j < ca.length - 1 && ca[j][0] < x) j++; const a = ca[j - 1], b = ca[j], f = (x - a[0]) / ((b[0] - a[0]) || 1); return a[1] + f * (b[1] - a[1]); };
    for (let j = 0; j < val.curves.rigid.length; j++) { const x = val.curves.rigid[j][0], yc = interp(x); rig[j] = [x, (val.curves.rigid[j][1] - yc) * 1e4]; parr.push([x, (val.curves.parabola[j][1] - yc) * 1e4]); }
    let m = 1e-9; for (const p of [...res, ...rig, ...parr]) m = Math.max(m, Math.abs(p[1]));
    const R0 = -1.1 * m, R1 = 1.1 * m; const py2 = v => oy2 + (R1 - v) / (R1 - R0) * h2;
    axes(ctx, X0, X1, R0, R1, px, py2, "x (cm)", "Δy (µm)", mL, oy2, pw, h2);
    ctx.save(); ctx.beginPath(); ctx.rect(mL + 1, oy2 + 1, pw - 1, h2 - 1); ctx.clip();
    const line2 = (pts, col, lw, dash) => { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.setLineDash(dash || []); ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(px(p[0]), py2(p[1])) : ctx.moveTo(px(p[0]), py2(p[1]))); ctx.stroke(); ctx.setLineDash([]); };
    line2([[X0, 0], [X1, 0]], "#000", 0.8); line2(rig, "#0072B2", 1.1, [6, 4]); line2(parr, "#D55E00", 1.1, [1.5, 2.5]);
    ctx.fillStyle = "#000"; for (const p of res) ctx.fillRect(Math.round(px(p[0])) - 2, Math.round(py2(p[1])) - 2, 4, 4);
    ctx.restore();
    ctx.textAlign = "left"; ctx.textBaseline = "bottom"; ctx.fillStyle = "#000";
    ctx.fillText(`deviation from the elastic catenary; max |simulation − exact| = ${(val.err_sim_max_cm * 1e4).toPrecision(3)} µm (${(val.err_sim_rel_sag * 100).toPrecision(2)}% of sag)`, mL, oy2 - 6);
  }

  function render() {
    if (!W) return;
    const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, W, H);
    if (P.panel === "validate") renderVal(ctx); else renderWeb(ctx);
    renderReadouts(); renderPlots();
  }

  /* ---------------- readouts ---------------- */
  let lastReadout = 0;
  function renderReadouts(force) {
    if (P.ui === 0) return;
    const now = performance.now(); if (!force && now - lastReadout < 150 && running) return; lastReadout = now;
    const m = sim.metrics(), f = (v, d) => v === undefined || v === null || !isFinite(v) ? "&ndash;" : Number(v).toFixed(d);
    const st = m.step, T = sim.topo;
    $("scrub").max = T.steps.length; $("scrub").value = st; $("stepl").textContent = `${st} / ${T.steps.length}`;
    $("status").innerHTML = `Phase: <b>${C.PHASE_LABEL[m.phase] || m.phase}</b> &nbsp; Action: ${m.action ? `<code>${m.action[0]}(${m.action.slice(1).join(", ")})</code>` : "initial state"}` +
      (m.stopped && m.stopped !== "complete" ? ` &nbsp; <b>stopped: ${m.stopped}</b>` : "") + (m.hub_fixed ? " &nbsp; hub held as construction scaffold until mark_proto_hub" : "");
    let h = `<tr class="h"><th colspan="3">State</th></tr>
      <tr><td>time</td><td class="n">${f(m.t_s, 2)}</td><td class="u">s</td></tr>
      <tr><td>plan step</td><td class="n">${st} / ${T.steps.length}</td><td class="u"></td></tr>
      <tr><td>locomotory energy so far</td><td class="n">${f(m.energy_cm, 1)}</td><td class="u">cm (plan)</td></tr>
      <tr><td>kinetic energy</td><td class="n">${m.KE_J.toExponential(2)}</td><td class="u">J</td></tr>
      <tr><td>wind speed now</td><td class="n">${f(m.wind_now_ms, 3)}</td><td class="u">m/s</td></tr>
      <tr><td>hub position</td><td class="n">${f(m.hub_xy_cm[0], 3)}, ${f(m.hub_xy_cm[1], 3)}</td><td class="u">cm</td></tr>
      <tr class="h"><th colspan="3">Sag and tension</th></tr>
      <tr><td>max thread sag</td><td class="n">${f(m.max_sag.cm, 3)}</td><td class="u">cm</td></tr>
      <tr><td colspan="3" class="note">${m.max_sag.type ? `${C.TYPE_LABEL[m.max_sag.type]} #${m.max_sag.thread}, chord ${f(m.max_sag.chord_cm, 2)} cm, at (${f(m.max_sag.x_cm, 2)}, ${f(m.max_sag.y_cm, 2)}) cm; measured from the chord between the thread's two ends` : ""}</td></tr>
      <tr><td>max span sag</td><td class="n">${f(m.max_span_sag.cm, 3)}</td><td class="u">cm</td></tr>
      <tr><td colspan="3" class="note">${m.max_span_sag.type ? `${C.TYPE_LABEL[m.max_span_sag.type]} #${m.max_span_sag.thread}, between junctions ${f(m.max_span_sag.chord_cm, 2)} cm apart` : ""}</td></tr>
      <tr><td>max height above chord</td><td class="n">${f(m.max_above_chord.cm, 3)}</td><td class="u">cm</td></tr>
      <tr><td>max tension</td><td class="n">${f(m.max_tension.mN, 3)}</td><td class="u">mN</td></tr>
      <tr><td colspan="3" class="note">${m.max_tension.type ? `${C.TYPE_LABEL[m.max_tension.type]} #${m.max_tension.thread}; max strain ${f(m.max_strain.pct, 2)}% (${C.TYPE_LABEL[m.max_strain.type] || ""})` : ""}</td></tr>
`;
    let h2 = `<tr class="h"><th>Silk by type</th><th class="n">laid (cm)</th><th class="n">n</th></tr>`;
    let tot = 0;
    for (const ty of C.TYPES) { const s = m.silk_by_type[ty]; tot += s.rest_cm; h2 += `<tr><td><span class="ls" style="border-top:2px solid ${C.TYPE_COLOR[ty]}"></span>${C.TYPE_LABEL[ty]}</td><td class="n">${f(s.rest_cm, 1)}</td><td class="n">${s.threads}</td></tr>`; }
    h2 += `<tr><td>total</td><td class="n">${f(tot, 1)}</td><td></td></tr>
      <tr><td colspan="3" class="note">For scale: control webs in <code>config.yaml</code> (empirical) have 284 &plusmn; 14 cm of radii and 1083 &plusmn; 72 cm of capture spiral.</td></tr>
      <tr class="h"><th colspan="3">Perturbations</th></tr>
      <tr><td>removed anchors</td><td colspan="2" class="n">${m.removed_anchors.length ? m.removed_anchors.map(n => n.replace("anchor_", "")).join(", ") : "none"}</td></tr>
      <tr><td>detached anchors</td><td colspan="2" class="n">${m.detached.length ? m.detached.map(n => n.replace("anchor_", "")).join(", ") : "none"}</td></tr>
      <tr class="h"><th colspan="3">Solver</th></tr>
      <tr><td>free nodes / segments</td><td class="n">${m.nodes_free} / ${m.segments_on}</td><td></td></tr>
      <tr><td>Newton iterations, last step</td><td class="n">${sim.world.lastNewton}</td><td></td></tr>
      <tr><td>last settle</td><td class="n">${m.settle ? `${m.settle.iters} it, ${m.settle.residual.toExponential(1)}` : "&ndash;"}</td><td class="u">rel. residual</td></tr>`;
    if (P.panel === "validate" && val && val.curves) {
      h = `<tr class="h"><th colspan="3">Validation: single span</th></tr>
        <tr><td>span, slack, N</td><td class="n">${P.vL} cm, ${P.vslack}%, ${val.N}</td><td></td></tr>
        <tr><td>weight per length w</td><td class="n">${val.w_N_per_m.toExponential(3)}</td><td class="u">N/m</td></tr>
        <tr><td>sag: simulated</td><td class="n">${val.sag_sim_cm.toFixed(5)}</td><td class="u">cm</td></tr>
        <tr><td>sag: elastic catenary</td><td class="n">${val.sag_exact_cm.toFixed(5)}</td><td class="u">cm</td></tr>
        <tr><td>sag: a(cosh(L/2a) &minus; 1)</td><td class="n">${val.sag_rigid_catenary_cm.toFixed(5)}</td><td class="u">cm</td></tr>
        <tr><td>sag: wL&sup2;/(8H)</td><td class="n">${val.sag_parabola_formula_cm.toFixed(5)}</td><td class="u">cm</td></tr>
        <tr><td>H: simulated</td><td class="n">${val.H_sim_mN.toExponential(4)}</td><td class="u">mN</td></tr>
        <tr><td>H: exact</td><td class="n">${val.H_exact_mN.toExponential(4)}</td><td class="u">mN</td></tr>
        <tr><td>T<sub>max</sub>: simulated / exact</td><td class="n">${val.Tmax_sim_mN.toExponential(3)} / ${val.Tmax_exact_mN.toExponential(3)}</td><td class="u">mN</td></tr>
        <tr><td>max |sim &minus; exact|</td><td class="n">${(val.err_sim_max_cm * 1e4).toPrecision(3)}</td><td class="u">&micro;m</td></tr>
        <tr><td>&nbsp; relative to sag</td><td class="n">${(val.err_sim_rel_sag * 100).toPrecision(3)}</td><td class="u">%</td></tr>
        <tr><td>max |parabola &minus; exact|</td><td class="n">${(val.err_parabola_max_cm * 1e4).toPrecision(3)}</td><td class="u">&micro;m</td></tr>
        <tr><td>max |a cosh &minus; exact|</td><td class="n">${(val.err_rigid_max_cm * 1e4).toPrecision(3)}</td><td class="u">&micro;m</td></tr>
        <tr><td>settle</td><td class="n">${val.settle.iters} it, ${val.settle.residual.toExponential(1)}</td><td class="u">rel. residual</td></tr>
        <tr><td colspan="3" class="note">Same lumped-mass, tension-only solver as the web. Exact reference: elastic catenary with unstretched length L(1 + slack), weight w per unstretched length and axial stiffness EA. The discretisation error falls as 1/N&sup2;.</td></tr>` + h;
    }
    $("rtab").innerHTML = h; $("rtab2").innerHTML = h2;
  }

  function renderPlots() {
    if (P.ui === 0) return;
    const tr = sim.trace; if (!tr.length) return;
    const tN = tr[tr.length - 1].t, t0 = Math.max(tN - 20, tr[0].t), span = Math.max(tN - t0, 1e-3);
    const pts = tr.filter(p => p.t >= t0);
    const draw = (id, key, log) => {
      const c = $(id), ctx = c.getContext("2d"), w = c.width / dpr, h = c.height / dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, w, h);
      const vals = pts.map(p => log ? Math.log10(Math.max(p[key], 1e-30)) : p[key]);
      let lo = Math.min(...vals), hi = Math.max(...vals); if (!log) lo = Math.min(lo, 0); if (hi - lo < 1e-12) { hi = lo + (log ? 1 : Math.max(1e-6, Math.abs(lo) * 0.1 + 1e-6)); }
      const ml = 46, mb = 13, mt = 3, pw = w - ml - 4, ph = h - mb - mt;
      ctx.strokeStyle = "#000"; ctx.lineWidth = 1; ctx.strokeRect(ml + 0.5, mt + 0.5, Math.round(pw), Math.round(ph));
      ctx.fillStyle = "#000"; ctx.font = "10px Helvetica Neue, Helvetica, Arial, sans-serif"; ctx.textAlign = "right"; ctx.textBaseline = "middle";
      const lab = v => log ? "1e" + Math.round(v) : (+v.toPrecision(3)).toString();
      ctx.fillText(lab(hi), ml - 3, mt + 4); ctx.fillText(lab(lo), ml - 3, mt + ph - 3);
      ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText(t0.toFixed(1) + " s", ml, mt + ph + 1); ctx.textAlign = "right"; ctx.fillText(tN.toFixed(1) + " s", ml + pw, mt + ph + 1);
      ctx.strokeStyle = "#000"; ctx.lineWidth = 1; ctx.beginPath();
      const x = t => ml + (t - t0) / span * pw, y = v => mt + (hi - v) / (hi - lo) * ph;
      pts.forEach((p, i) => i ? ctx.lineTo(x(p.t), y(vals[i])) : ctx.moveTo(x(p.t), y(vals[i]))); ctx.stroke();
    };
    draw("pKE", "KE", true); draw("pW", "wind", false); draw("pS", "sag", false); draw("pT", "T", false);
  }

  /* ---------------- validation ---------------- */
  function runVal(opts) {
    const o = Object.assign({ L: +P.vL, slack: +P.vslack, N: +P.vN, mu: +P["mu_" + P.vtype], EA: +P["EA_" + P.vtype], exag: +P.exag, g: +P.g }, opts || {});
    val = C.runValidation(o); return val;
  }

  /* ---------------- animation loop ---------------- */
  function frame() {
    if (running) { sim.advance(1 / 60, playing); if (playing && sim.stopped) { playing = false; showParams(); } render(); }
    requestAnimationFrame(frame);
  }

  /* ---------------- scripting hooks ---------------- */
  window.simAPI = {
    params: () => JSON.parse(JSON.stringify(P, (k, v) => v === Infinity ? "Infinity" : v)),
    set(o) { const keepRun = running; for (const k in o) { if (k === "slack") { for (const ty of C.TYPES) P["slack_" + ty] = +o[k]; setParam("slack_bridge", +o[k], true); } else setParam(k, STR.has(k) ? o[k] : (k === "cap" ? parseVal(k, o[k]) : +o[k]), true); } running = keepRun; showParams(); render(); return this.params(); },
    restore() { sim.detached.clear(); P.detach = ""; sim.buildTo(sim.k); render(); return true; },
    buildTo(k) { playing = false; const r = sim.buildTo(k === "final" ? "final" : +k); render(); return r; },
    settle(maxIters) { const r = sim.settle(maxIters || 200); render(); return r; },
    advance(seconds, play) { sim.advance(+seconds, play === undefined ? (P.mode === "play" && playing) : !!play); render(); return { t_s: sim.world.t, step: sim.k, KE_J: sim.world.kinetic() }; },
    play(on) { playing = !!on; if (playing) running = true; showParams(); return playing; },
    run(on) { running = !!on; if (!running) playing = false; showParams(); return running; },
    stepAction() { sim.stepAction(); render(); return sim.k; },
    buildQuasiStatic(k, maxIters) { playing = false; const r = sim.buildQuasiStatic(k === "final" ? "final" : +k, maxIters); render(); return r; },
    detach(name) { const r = sim.detach(name); render(); return r; },
    metrics: () => sim.metrics(),
    threads: () => sim.threads(),
    validate(o) { const r = runVal(o); render(); return r; },
    render() { render(); return true; },
    rig: () => ({ walkable: R.walkable.map(([a, b]) => [R.nodes[a], R.nodes[b]]), crossbar: [R.nodes.crossbar_left, R.nodes.crossbar_right], frame: R.frame }),
    supportDisp: (xcm, ycm, t) => (1 - ycm / R.frame[1]) * P.amp * Math.sin(2 * Math.PI * P.freq * t + P.phase * Math.PI / 180),
  };

  if (P.panel === "validate") runVal();
  showParams(); resize(); renderReadouts(true);
  requestAnimationFrame(frame);
})();
