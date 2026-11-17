#!/bin/sh
# Convert the repo's own Mulder SVG figures to PDF+PNG with the shared headless-Chrome helper.
# Usage: sh capture_repo_svgs.sh   (W is derived from this script's location)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
W="$(cd "$HERE/../../.." && pwd)"
R="$W/repo/htn-biology"
O="$W/report/figures/mulder"
mkdir -p "$O"
shot() { node "$W/tools/shot.mjs" "$1" "$2.pdf" $3; node "$W/tools/shot.mjs" "$1" "$2.png" $3; }
# 1. Manuscript figures exactly as committed in docs/manuscript/figures
shot "$R/docs/manuscript/figures/mulder_v3_completion.svg"     "$O/repo_v3_completion"
shot "$R/docs/manuscript/figures/mulder_v3_paired_effects.svg" "$O/repo_v3_paired_effects"
# 2. The controller-audit timeline/error SVGs are captured (with enlarged text) by build_galleries.py.
