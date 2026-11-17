// Fig 4: sag and tension against the factors (static equilibrium for each setting)
const out = { params: DEF, wind: [], slack: [], exag: [], g: [] };
const one = () => { S.buildTo("final"); const r = S.settle(600); const m = S.metrics(); return { m: summ(m), per: perThread(m), th: lite(S.threads()), settle: r }; };
S.set({ spider: 0 });
for (const dir of [0, 270]) for (const u of [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8]) { S.set({ wind: u, dir }); const r = one(); out.wind.push({ dir, u, m: r.m, settle: r.settle, th: r.th }); }
S.set({ wind: 0, dir: 0 });
for (const sl of [-1, -0.5, -0.25, 0, 0.25, 0.5, 1, 1.5, 2, 3, 4]) { S.set({ slack: sl }); const r = one(); out.slack.push({ slack: sl, m: r.m, per: r.per, settle: r.settle }); }
S.set({ slack: 0 });
for (const x of [1, 3, 10, 30, 100, 300, 1000, 2000, 3000, 10000, 30000, 100000]) { S.set({ exag: x }); const r = one(); out.exag.push({ exag: x, m: r.m, per: r.per, settle: r.settle }); }
S.set({ exag: DEF.exag });
for (const g of [0, 1, 2.5, 5, 9.81, 15, 20]) { S.set({ g }); const r = one(); out.g.push({ g, m: r.m, per: r.per, settle: r.settle }); }
return out;
