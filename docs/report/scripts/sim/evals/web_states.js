// Fig 1 + Fig 4(tension) : straight plan, gravity, gravity + wind; default parameters
const out = { params: DEF, rig: S.rig() };
S.set({ g: 0 }); S.buildTo("final"); out.plan_settle = S.settle(400); out.plan = { m: summ(S.metrics()), th: lite(S.threads()) };
S.set({ g: 9.81 }); S.buildTo("final"); S.settle(400); { const m = S.metrics(); out.gravity = { m: summ(m), th: lite(S.threads()), per: perThread(m) }; }
S.set({ spider: 0 }); S.buildTo("final"); S.settle(400); { const m = S.metrics(); out.gravity_nospider = { m: summ(m), th: lite(S.threads()), per: perThread(m) }; }
S.set({ spider: DEF.spider, wind: 4, dir: 0 }); S.buildTo("final"); S.settle(400); { const m = S.metrics(); out.wind4 = { m: summ(m), th: lite(S.threads()), per: perThread(m) }; }
S.set({ wind: 0 }); S.buildQuasiStatic("final", 400); { const m = S.metrics(); out.quasistatic = { m: summ(m), th: lite(S.threads()), per: perThread(m) }; }
return out;
