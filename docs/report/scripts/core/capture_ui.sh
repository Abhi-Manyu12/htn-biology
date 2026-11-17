#!/usr/bin/env bash
# Screenshots of the repo's interactive plan visualisers in their final state (headless Chrome via shot.mjs).
set -euo pipefail
W="<WORKSPACE>"
V="$W/repo/htn-biology/visualization"; S="$W/report/scripts/core"; F="$W/report/figures/core"
mkdir -p "$F"
for pair in "index.html:ui_original_final:ui_goto_last.js" \
            "index_updated.html:ui_updated_final:ui_goto_last.js" \
            "index_updated.html:ui_updated_precomplete:ui_goto_before_complete.js"; do
  IFS=: read -r page stem js <<< "$pair"
  node "$W/tools/shot.mjs" "$V/$page" "$F/$stem.png" --width 1280 --height 860 --wait-for "#webCanvas" \
       --eval-file "$S/$js" --wait 1200
  "$W/.venv/bin/python" "$S/png_to_pdf.py" "$F/$stem.png" "$F/$stem.pdf"
done
