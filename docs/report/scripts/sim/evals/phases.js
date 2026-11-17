// Fig 2: quasi-static sequential construction, snapshot at the end of each macro phase
const out = { params: DEF, rig: S.rig(), snaps: [] };
S.buildTo(0); S.settle(400);
const n = S.metrics().total_steps; let worst = 0, unconv = 0;
const phaseAt = []; // phase of each step, from metrics after each action
let prevPhase = null;
for (let k = 0; k < n; k++) {
  S.stepAction(); const r = S.settle(400); worst = Math.max(worst, r.residual); if (!r.converged) unconv++;
  const m = S.metrics(); phaseAt.push(m.phase);
}
// second pass with snapshots at phase boundaries (deterministic replay)
const ends = []; for (let k = 0; k < n; k++) if (k === n - 1 || phaseAt[k] !== phaseAt[k + 1]) ends.push(k + 1);
S.buildTo(0); S.settle(400);
for (let k = 0; k < n; k++) { S.stepAction(); S.settle(400); if (ends.includes(k + 1)) { const m = S.metrics(); out.snaps.push({ k: k + 1, phase: phaseAt[k], m: summ(m), th: lite(S.threads()) }); } }
out.worst_residual = worst; out.unconverged = unconv; out.ends = ends;
return out;
