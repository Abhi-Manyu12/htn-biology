#!/usr/bin/env bash
# Re-runs used by the core section (all in PRIVATE checkouts, never in the read-only repo).
#   repo_39b89f3 : git worktree at 39b89f3 (2026-09-09, the commit that produced the committed sweep CSVs)
#   repo         : clone at 61d18d8 (current main)
# Outputs go to $W/work/core/derived/.
set -euo pipefail
W="<WORKSPACE>"
PY="$W/.venv/bin/python"
D="$W/work/core/derived"
mkdir -p "$D"

what="${1:-all}"

if [[ "$what" == sens || "$what" == all ]]; then
  # Reproduction check of three anchor-removal rows and one wind row of the committed CSVs (n=1000 each).
  cd "$W/work/core/repo_39b89f3"
  "$PY" -m spider_web_htn_updated.sensitivity --n-runs 1000 --removal-probs 0.0 0.5 0.8 \
      --out "$D/rerun39_sens_p0_05_08.csv" > "$D/rerun39_sens.log" 2>&1
  "$PY" -m spider_web_htn_updated.sensitivity --n-runs 1000 --removal-probs 0.0 --wind-stds 0.0 0.5 \
      --out "$D/rerun39_wind_0_05.csv" > "$D/rerun39_wind.log" 2>&1
fi

if [[ "$what" == compare || "$what" == all ]]; then
  # compare.py re-runs. The baseline's candidate list is built from list(state.nodes) (a Python set of str),
  # so its trajectory depends on PYTHONHASHSEED; we therefore pin it and also sweep it.
  S="$W/report/scripts/core/rerun_compare.py"
  cd "$W/work/core/repo_39b89f3"      # Checkpoint-2-era code + shipped config (anchor removal p=0.2 ON)
  for h in 0 1 2 3 4 5 6 7 8 9; do
    PYTHONHASHSEED=$h "$PY" "$S" 30 5000 "$D/rerun39_compare_n30_hash$h.json" > /dev/null 2>&1
  done
  cd "$W/work/core/repo"              # current code + shipped config (deterministic)
  for h in 0 1 2 3 4 5 6 7 8 9; do
    PYTHONHASHSEED=$h "$PY" "$S" 30 5000 "$D/rerun61_compare_n30_hash$h.json" > /dev/null 2>&1
  done
  PYTHONHASHSEED=0 "$PY" "$S" 300 5000 "$D/rerun61_compare_n300_hash0.json" > /dev/null 2>&1
fi

if [[ "$what" == pert || "$what" == all ]]; then
  # Reproduction check of the restored perturbation_trials.csv with the code at 61d18d8 (default settings).
  cd "$W/work/core/repo"
  "$PY" -m spider_web_htn_updated.perturbations --n-runs 200 --out "$D/rerun61_perturbation_trials.csv" \
      > "$D/rerun61_pert.log" 2>&1
fi
