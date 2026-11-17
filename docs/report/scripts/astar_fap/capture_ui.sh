#!/bin/sh
# Capture the repo's A* plan viewer (visualization/index_astar.html, data plan_data_astar.js)
# in its final state (last plan step) as PNG and PDF.  Reads the repo, writes only figures/.
W="<WORKSPACE>"
IN="$W/repo/htn-biology/visualization/index_astar.html"
OUT="$W/report/figures/astar_fap/ui_astar_final"
JS='var st=document.createElement("style"); st.textContent="*{outline:none!important}"; document.head.appendChild(st); if(document.activeElement) document.activeElement.blur(); pause(); goToStep(PLAN_DATA.total_steps - 1, true); draw(); updateUI(); "ok"'
node "$W/tools/shot.mjs" "$IN" "$OUT.png" --width 1400 --height 900 --full --wait 1500 --eval "$JS"
node "$W/tools/shot.mjs" "$IN" "$OUT.pdf" --width 1400 --height 900 --wait 1500 --eval "$JS"
