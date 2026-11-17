// Fig 6: anchor removal (stochastic.select_available_anchors draws) and post-build detachment
const out = { params: DEF, rig: S.rig(), drops: [], detach: [] };
for (const seed of [7107, 4]) for (const p of [0.1, 0.2, 0.35, 0.5]) {
  S.set({ seed, drop: p }); S.buildTo("final"); const r = S.settle(600); const m = S.metrics();
  out.drops.push({ seed, p, removed: m.removed_anchors, settle: r, m: summ(m), th: lite(S.threads()) });
}
S.set({ seed: DEF.seed, drop: 0 });
for (const nm of ["anchor_bottom_left", "anchor_right_lower"]) {
  S.restore(); S.buildTo("final"); S.settle(400); const before = { th: lite(S.threads()), m: summ(S.metrics()) };
  S.detach(nm); const tr = []; for (let i = 0; i < 6; i++) { S.advance(0.05, false); const m = S.metrics(); tr.push({ t: m.t_s, KE: m.KE_J, hub: m.hub_xy_cm }); }
  const mid = { th: lite(S.threads()), t: S.metrics().t_s };
  const r = S.settle(800); const after = { th: lite(S.threads()), m: summ(S.metrics()), settle: r };
  out.detach.push({ anchor: nm, before, mid, after, transient: tr });
}
return out;
