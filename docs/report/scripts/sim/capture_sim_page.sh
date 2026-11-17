#!/bin/sh
# Figure 7: captures of the simulation page itself (controls visible). Requires Chrome; run from anywhere.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$HERE/../../.." && pwd)"
PAGE="$W/simulation/orb_web_sim.html"; OUT="$W/report/figures/sim"
node "$W/tools/shot.mjs" "$PAGE?run=0&wind=3&dir=0&gust=0.3&seed=7&t=6" "$OUT/sim_page.png" --width 1400 --height 900 --scale 2 --wait 400
node "$W/tools/shot.mjs" "$PAGE?run=0&panel=validate&vslack=3&vN=16" "$OUT/sim_page_validation.png" --width 1400 --height 900 --scale 2 --wait 400
"$W/.venv/bin/python" - "$OUT" <<'PY'
import sys, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.image as mpimg
out = sys.argv[1]
for stem in ["sim_page", "sim_page_validation"]:
    im = mpimg.imread(os.path.join(out, stem + ".png")); h, w = im.shape[:2]
    fig = plt.figure(figsize=(w / 200, h / 200), dpi=200); ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(im, interpolation="none"); ax.axis("off")
    fig.savefig(os.path.join(out, stem + ".pdf"), dpi=200); plt.close(fig); print("wrote", stem + ".pdf")
PY
