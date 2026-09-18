"""
make_index_astar.py — one-off: clone visualization/index.html into
visualization/index_astar.html, repointing it at plan_data_astar.js instead
of plan_data.js.

Run once from anywhere (paths are absolute-relative to this file's location,
matching the htn-biology/{spider_web_htn, spider_web_astr, visualization}/
layout):

    python make_index_astar.py
"""
import os

project_root = os.path.dirname(os.path.abspath(__file__))
# Adjust this if you place this script somewhere other than spider_web_astr/
viz_dir = os.path.join(os.path.dirname(project_root), "visualization")

src = os.path.join(viz_dir, "index.html")
dst = os.path.join(viz_dir, "index_astar.html")

with open(src, "r", encoding="utf-8") as f:
    html = f.read()

if "plan_data.js" not in html:
    print("⚠ Could not find a reference to plan_data.js in index.html.")
    print("  Open index.html manually and check how it loads PLAN_DATA —")
    print("  the <script src=\"...\"> tag name may differ from expected.")
else:
    html_astar = html.replace("plan_data.js", "plan_data_astar.js")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html_astar)
    print(f"✓ Wrote {dst}")