// Fig 5: moving supports (spider_web_mulder affine shear)
const out = { params: DEF, rig: S.rig(), runs: [] };
for (const [amp, freq] of [[10, 0.05], [5, 0.05], [10, 0.1]]) {
  S.set({ amp, freq, phase: 0, wind: 0 }); S.buildTo("final"); S.settle(400);
  const run = { amp, freq, series: [], snaps: [] }; const T = 1 / freq, dt = T / 80;
  const snapAt = [0, 0.25, 0.5, 0.75].map(f => f * T);
  const rec = () => { const m = S.metrics(); run.series.push({ t: m.t_s, sag: m.max_sag.cm, span_sag: m.max_span_sag.cm, T: m.max_tension.mN, strain: m.max_strain.pct, Ttype: m.max_tension.type, hub: m.hub_xy_cm, KE: m.KE_J, disp: S.supportDisp(0, 0, m.t_s) }); };
  run.snaps.push({ t: 0, th: lite(S.threads()), m: summ(S.metrics()) }); rec();
  for (let i = 1; i <= 160; i++) { S.advance(dt, false); rec(); for (const ts of snapAt) if (ts > 0 && Math.abs(i * dt - ts) < 1e-9) run.snaps.push({ t: i * dt, th: lite(S.threads()), m: summ(S.metrics()) }); }
  out.runs.push(run);
}
return out;
