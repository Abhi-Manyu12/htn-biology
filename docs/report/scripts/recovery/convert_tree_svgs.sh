#!/usr/bin/env bash
# Convert the repository's recorded IPyHOP solution-tree SVGs to PDF (vector) and PNG.
#  1. The two manuscript SVGs (docs/manuscript/figures/recovery_v1_tree_{initial,replanned}.svg)
#     -> report/figures/recovery/tree_manuscript_{initial,replanned}.{pdf,png}
#  2. tree_0.svg / tree_1.svg of case 1 (4 sectors, depth 0, 10 cm), seed 0, backend ipyhop, for every
#     scenario in mulder_results/recovery_v1_verified/traces -> work/recovery/raw_trees/<scenario>_tree_<k>.png
#     (intermediate rasters, composed into a gallery by fig_tree_gallery_raw.py).
# The SVGs are 2800 x 720 user units. PNGs are rendered at 2800 px width, device scale 1.5.
set -euo pipefail
W="<WORKSPACE>"
R="$W/repo/htn-biology"
OUT="$W/report/figures/recovery"
RAW="$W/work/recovery/raw_trees"
mkdir -p "$OUT" "$RAW"
for k in initial replanned; do
  src="$R/docs/manuscript/figures/recovery_v1_tree_$k.svg"
  node "$W/tools/shot.mjs" "$src" "$OUT/tree_manuscript_$k.pdf" --max-width 2800
  node "$W/tools/shot.mjs" "$src" "$OUT/tree_manuscript_$k.png" --max-width 2800 --scale 1.5
done
for sc in clean transient_attachment permanent_anchor route_block prefix_damage silk_depletion unreachable; do
  d="$R/mulder_results/recovery_v1_verified/traces/case1_${sc}_ipyhop"
  for i in 0 1; do
    if [ -f "$d/tree_$i.svg" ]; then
      node "$W/tools/shot.mjs" "$d/tree_$i.svg" "$RAW/${sc}_tree_$i.png" --max-width 2800 --scale 1
    fi
  done
done
