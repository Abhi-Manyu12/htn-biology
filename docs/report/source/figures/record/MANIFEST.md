# Figures: `record` domain

All figures regenerate with `report/scripts/record/run_all.sh` (order: `repo_history.py` on the private clone
`work/record/repo` -> `work/record/history/history.csv`; then `make_figures.py`). Repository state: commit
`61d18d8`. No figure uses estimated or invented values.

| Stem | Script | Source data (repo paths) | What it shows | n |
|---|---|---|---|---|
| `record_timeline` | `make_figures.py:fig_timeline` (data from `repo_history.py`) | `git log` of the repo (20 commits); each commit's tracked `*.py` files; `pytest --collect-only` on each commit's `*/tests` | Top: commits by author with milestones, Checkpoint 2 line (c9144e6) and the 19-24 Oct work-log band (dates from `docs/research/WORK_LOG.md`). Middle/bottom: Python lines (excl. `third_party/`) and collected tests per commit tree, drawn along the commit graph | 20 commits |
| `record_composition` | `make_figures.py:fig_composition` | HEAD (`61d18d8`) tracked `*.py` per package; pytest collection per package; c9144e6 totals for the Checkpoint-2 tick | Source + test lines per package, vendored IPyHOP separately; tests collected per package (56 / 77 / 44 = 177) | 9 packages/groups |
| `record_claims` | `make_figures.py:fig_claims` | `docs/research/CLAIMS.md` (C01-C28) | Claims per status category (S 11, N 10, U 6, X 1) and a per-claim strip with the evidence study named in each row. Category rule is in the script (`ASSIGN`, asserted against the status wording) and in the LaTeX caption | 28 claims |
| `record_evidence_volume` | `make_figures.py:fig_evidence` | `mulder_results/*/trials.csv` row counts; `docs/research/evidence/mulder_suffix_control.json` (`trials`); `sensitivity_comparison.csv`, `wind_sensitivity.csv`, `perturbation_trials.csv` (`n_runs` sums); file counts under `mulder_results/` | Simulated trials per study (log scale) coloured by how each result is held (curated/hash-verified, raw cited, raw uncited, aggregate-only, historical C28); committed files per result directory | 14 study rows; 3,046 files |

Supporting check (no figure): `verify_record.py` -> `work/record/verify.json` (snapshot manifest, evidence input
hashes, IPyHOP hashes, figure provenance, perturbation CSV hash; all match).
