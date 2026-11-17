"""Count how often the drop / Tarzan proto-hub variants appear in HTN plans under anchor removal.
Run inside a private checkout (cwd = repo root):  "$PY" rerun_protohub_variants.py [n]"""
import contextlib, io, os, sys, collections
sys.path.insert(0, os.getcwd())
import gtpyhop
from spider_web_htn_updated import sensitivity as sens
from spider_web_htn_updated.config_loader import CONFIG
from spider_web_htn_updated.state import create_initial_state
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
CONFIG["stochastic"]["enabled"] = True
CONFIG["stochastic"]["anchor_availability"]["enabled"] = True
for p in (0.0, 0.2, 0.5, 0.8):
    CONFIG["stochastic"]["anchor_availability"]["removal_prob"] = p
    c = collections.Counter()
    for t in range(n):
        sens._setup_domain()
        with contextlib.redirect_stdout(io.StringIO()):
            gtpyhop.set_verbose_level(0)
            plan = gtpyhop.find_plan(create_initial_state(seed=1000 + t), [("build_web",)])
        if plan:
            names = {a[0] for a in plan}
            c["plans"] += 1
            c["drop_down"] += "drop_down" in names
            c["swing_tarzan"] += "swing_tarzan" in names
    print(p, dict(c), flush=True)
