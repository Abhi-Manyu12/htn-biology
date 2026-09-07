"""
test_planner.py — End-to-end regression tests.

1. Confirms the full planner still produces the known-good baseline plan
   (71 actions, 600.1 cm energy) after the config-decoupling refactor.
2. Confirms that swapping SPIDER_WEB_CONFIG to a different environment
   changes the outcome (energy scales with frame size) WITHOUT touching
   any Python code — proving the decoupling actually works.

The config-swap test runs in a subprocess because config.yaml is loaded
once into a module-level singleton (CONFIG) at import time; module-level
constants derived from it (e.g. NODE_COORDS, _DOMAIN in methods.py) are
bound at import time too. A fresh process is the simplest way to guarantee
a completely independent config for each run, and it also mirrors how a
real sensitivity-analysis sweep would invoke the planner per-environment.
"""

import json
import os
import subprocess
import sys
import tempfile

import pytest
import yaml

PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BASELINE_ACTIONS = 71
BASELINE_ENERGY = 600.1


def _run_planner_subprocess(config_path=None, env_overrides=None):
    """Run the planner in a fresh subprocess and return (plan_len, energy)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if config_path:
        env["SPIDER_WEB_CONFIG"] = config_path
    if env_overrides:
        env.update(env_overrides)

    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from spider_web_htn_updated.main import run_planner\n"
        "plan = run_planner(verbose_level=0)\n"
        "energy = None\n"
        "if plan:\n"
        "    from spider_web_htn_updated.utils import calculate_distance\n"
        "    from spider_web_htn_updated.state import create_initial_state\n"
        "    state = create_initial_state()\n"
        "    total = 0.0\n"
        "    for action in plan:\n"
        "        name = action[0]\n"
        "        if name in ('walk','lay_thread','lay_frame_thread','lay_radius',\n"
        "                    'drop_down','swing_tarzan','reel_up','build_spiral_segment'):\n"
        "            if len(action) >= 3:\n"
        "                total += calculate_distance(action[1], action[2])\n"
        "    energy = total\n"
        "import json\n"
        "print('RESULT_JSON:' + json.dumps({'plan_len': len(plan) if plan else None, 'energy': energy}))\n"
    ) % PACKAGE_ROOT

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Subprocess failed:\n{result.stdout}\n{result.stderr}"

    for line in result.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            return json.loads(line[len("RESULT_JSON:"):])

    raise AssertionError(f"No RESULT_JSON found in output:\n{result.stdout}\n{result.stderr}")


def test_baseline_plan_matches_known_good_output():
    result = _run_planner_subprocess()
    assert result["plan_len"] == BASELINE_ACTIONS
    assert result["energy"] == pytest.approx(BASELINE_ENERGY, abs=0.05)


def test_scaled_environment_changes_energy_proportionally(tmp_path):
    # Load the real config.yaml and scale every node coordinate by 1.5x —
    # this simulates a bigger supporting structure / wider anchor spacing.
    with open(os.path.join(PACKAGE_ROOT, "config.yaml")) as f:
        cfg = yaml.safe_load(f)

    scale = 1.5
    for name, (x, y) in cfg["environment"]["nodes"].items():
        cfg["environment"]["nodes"][name] = [round(x * scale, 4), round(y * scale, 4)]

    scaled_path = tmp_path / "config_scaled.yaml"
    with open(scaled_path, "w") as f:
        yaml.safe_dump(cfg, f)

    baseline = _run_planner_subprocess()
    scaled = _run_planner_subprocess(config_path=str(scaled_path))

    # Same plan shape (topology/order unaffected by uniform scaling)...
    assert scaled["plan_len"] == baseline["plan_len"]
    # ...but energy scales proportionally, proving geometry came from config.
    assert scaled["energy"] == pytest.approx(baseline["energy"] * scale, rel=0.01)


def test_missing_config_file_fails_fast():
    with pytest.raises(AssertionError):
        _run_planner_subprocess(config_path="/tmp/does_not_exist_config.yaml")
