#!/bin/sh
# Regenerate every `record` figure and the integrity checks. Read-only on the repo; writes to W/work/record
# and W/report/figures/record. Requires the private clone W/work/record/repo (git clone of W/repo/htn-biology).
set -e
W="<WORKSPACE>"
PY="$W/.venv/bin/python"
S="$W/report/scripts/record"
[ -d "$W/work/record/repo" ] || git clone -q "$W/repo/htn-biology" "$W/work/record/repo"
"$PY" "$S/repo_history.py" "$W/work/record/repo" "$W/work/record/history"      # per-commit LOC + tests
"$PY" "$S/verify_record.py" "$W/repo/htn-biology" "$W/work/record/verify.json"  # hash checks
(cd "$W/work/record/repo" && "$PY" -m pytest -q -p no:cacheprovider \
    spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests | tail -1)
"$PY" "$S/make_figures.py"
