// Fig 3: single span validation
const P = S.params(), base = { L: 16, mu: P.mu_radius, EA: P.EA_radius, exag: P.exag, g: P.g };
const out = { base, conv: [], slack: [], shape: null };
for (const slack of [0, 1, 5]) for (const N of [4, 8, 16, 32, 64, 128, 256]) {
  const r = S.validate(Object.assign({}, base, { slack, N }));
  out.conv.push({ slack, N, err_cm: r.err_sim_max_cm, rel: r.err_sim_rel_sag, sag_sim: r.sag_sim_cm, sag_exact: r.sag_exact_cm, H_sim: r.H_sim_mN, H_exact: r.H_exact_mN, res: r.settle.residual, conv: r.settle.converged, it: r.settle.iters });
}
for (const slack of [-0.5, -0.25, 0, 0.25, 0.5, 1, 2, 3, 5, 7.5, 10, 15, 20]) {
  const r = S.validate(Object.assign({}, base, { slack, N: 40 }));
  out.slack.push({ slack, err_sim_cm: r.err_sim_max_cm, err_par_cm: r.err_parabola_max_cm, err_rigid_cm: r.err_rigid_max_cm, sag_exact: r.sag_exact_cm, sag_sim: r.sag_sim_cm, sag_par: r.sag_parabola_formula_cm, sag_rigid: r.sag_rigid_catenary_cm, H_exact: r.H_exact_mN, H_sim: r.H_sim_mN, Tmax_exact: r.Tmax_exact_mN, Tmax_sim: r.Tmax_sim_mN, res: r.settle.residual });
}
for (const [slack, N] of [[3, 16], [3, 40], [0, 40], [10, 40]]) { const r = S.validate(Object.assign({}, base, { slack, N })); out["shape_" + slack + "_" + N] = { sim: r.sim_cm, curves: r.curves, resid_um: r.resid_um, err_cm: r.err_sim_max_cm, rel: r.err_sim_rel_sag, sag: r.sag_exact_cm, a_cm: r.a_cm, w: r.w_N_per_m, H: r.H_exact_mN }; }
// X = 1 for reference: real-weight sag of a 16 cm zero-slack radius
{ const r = S.validate(Object.assign({}, base, { slack: 0, N: 40, exag: 1 })); out.x1 = { sag_exact: r.sag_exact_cm, sag_sim: r.sag_sim_cm, err: r.err_sim_max_cm }; }
return out;
