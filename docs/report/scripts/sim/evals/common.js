// shared helpers prepended to every eval (simAPI is defined by the page)
const S = window.simAPI;
const summ = m => ({ t_s: m.t_s, step: m.step, max_sag: m.max_sag, max_span_sag: m.max_span_sag, max_above_chord: m.max_above_chord,
  max_tension: m.max_tension, max_strain: m.max_strain, hub_xy_cm: m.hub_xy_cm, KE_J: m.KE_J, wind_now_ms: m.wind_now_ms,
  settle: m.settle, silk_by_type: m.silk_by_type, removed_anchors: m.removed_anchors, detached: m.detached, energy_cm: m.energy_cm,
  phase: m.phase, nodes_free: m.nodes_free, segments_on: m.segments_on, spider_xy_cm: m.spider_xy_cm });
const lite = th => th.map(t => ({ id: t.id, type: t.type, a: t.a, b: t.b, pts: t.pts.map(p => [+p[0].toFixed(5), +p[1].toFixed(5)]), T_mN: t.T_mN.map(v => +v.toPrecision(5)) }));
const perThread = m => m.threads.map(t => ({ id: t.id, type: t.type, a: t.a, b: t.b, sag_cm: t.sag_cm, span_sag_cm: t.span_sag_cm, chord_cm: t.chord_cm, T_max_mN: t.T_max_mN, T_mean_mN: t.T_mean_mN, strain_max_pct: t.strain_max_pct, rest_cm: t.rest_cm }));
const DEF = S.params();
