"""
test_planner.py — End-to-end regression tests.

1. Confirms the full planner still produces the known-good baseline plan
   (70 actions, 600.1 cm energy) after the config-decoupling refactor.
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

# tests/ lives inside spider_web_htn_updated/. SYS_PATH_ROOT is the
# package's parent directory (needed on sys.path so subprocesses can
# `import spider_web_htn_updated`); PACKAGE_DIR is the package itself
# (needed to locate config.yaml).
_TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
PACKAGE_DIR = os.path.abspath(os.path.join(_TESTS_DIR, ".."))
SYS_PATH_ROOT = os.path.abspath(os.path.join(_TESTS_DIR, "..", ".."))

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
        "    from spider_web_htn_updated.operators import _movement_cost\n"
        "    from spider_web_htn_updated.state import create_initial_state\n"
        "    state = create_initial_state()\n"
        "    total = 0.0\n"
        "    for action in plan:\n"
        "        name = action[0]\n"
        "        if name in ('walk','lay_thread','lay_frame_thread','lay_radius',\n"
        "                    'drop_down','swing_tarzan','reel_up','build_spiral_segment'):\n"
        "            if len(action) >= 3:\n"
        "                total += _movement_cost(state, action[1], action[2])\n"
        "    energy = total\n"
        "import json\n"
        "print('RESULT_JSON:' + json.dumps({'plan_len': len(plan) if plan else None, 'energy': energy}))\n"
    ) % SYS_PATH_ROOT

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Subprocess failed:\n{result.stdout}\n{result.stderr}"

    for line in result.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            return json.loads(line[len("RESULT_JSON:"):])

    raise AssertionError(f"No RESULT_JSON found in output:\n{result.stdout}\n{result.stderr}")


def _load_packaged_config():
    """Load the real config.yaml shipped with the package, as a dict."""
    with open(os.path.join(PACKAGE_DIR, "config.yaml")) as f:
        return yaml.safe_load(f)


def _write_config(cfg, tmp_path, filename="config_variant.yaml"):
    path = tmp_path / filename
    with open(path, "w") as f:
        yaml.safe_dump(cfg, f)
    return str(path)


def test_baseline_plan_matches_known_good_output(tmp_path):
    """
    The 71-action / 600.1 cm baseline is a DETERMINISTIC-mode contract.
    We don't trust whatever `stochastic.enabled` happens to be set to in
    the ambient config.yaml on disk (that value may legitimately vary
    across machines/branches) — instead we force it off explicitly, so
    this test's meaning doesn't depend on what someone else last left in
    the shared config file.
    """
    cfg = _load_packaged_config()
    cfg["stochastic"]["enabled"] = False
    config_path = _write_config(cfg, tmp_path, "config_deterministic.yaml")

    result = _run_planner_subprocess(config_path=config_path)
    assert result["plan_len"] == BASELINE_ACTIONS
    assert result["energy"] == pytest.approx(BASELINE_ENERGY, abs=0.05)


def test_scaled_environment_changes_energy_proportionally(tmp_path):
    """
    Same "force determinism explicitly" principle as the baseline test above:
    both the reference and scaled runs pin stochastic.enabled=False, so a
    difference in energy can only come from the geometry change we made,
    not from whatever the ambient config's stochastic settings happen to be.
    """
    base_cfg = _load_packaged_config()
    base_cfg["stochastic"]["enabled"] = False
    base_path = _write_config(base_cfg, tmp_path, "config_base.yaml")

    scale = 1.5
    scaled_cfg = _load_packaged_config()
    scaled_cfg["stochastic"]["enabled"] = False
    for name, (x, y) in scaled_cfg["environment"]["nodes"].items():
        scaled_cfg["environment"]["nodes"][name] = [round(x * scale, 4), round(y * scale, 4)]
    scaled_path = _write_config(scaled_cfg, tmp_path, "config_scaled.yaml")

    baseline = _run_planner_subprocess(config_path=base_path)
    scaled = _run_planner_subprocess(config_path=scaled_path)

    # Same plan shape (topology/order unaffected by uniform scaling)...
    assert scaled["plan_len"] == baseline["plan_len"]
    # ...but energy scales proportionally, proving geometry came from config.
    assert scaled["energy"] == pytest.approx(baseline["energy"] * scale, rel=0.01)


def test_missing_config_file_fails_fast():
    with pytest.raises(AssertionError):
        _run_planner_subprocess(config_path="/tmp/does_not_exist_config.yaml")


# ---------------------------------------------------------------------------
# Stochastic reproducibility contract (Way-Forward Step 6, end-to-end).
#
# These deliberately do NOT assert a fixed plan length/energy value — the
# whole point of stochastic mode is that the outcome legitimately varies
# with the environment/seed. What must hold instead:
#   (a) same seed + same config => byte-identical plan, every time
#   (b) turning stochastic on can actually change the outcome vs. the
#       deterministic baseline (i.e. it isn't secretly a no-op)
# ---------------------------------------------------------------------------

def _stochastic_config(tmp_path, seed, wind_noise_std=0.15, filename="config_stochastic.yaml"):
    cfg = _load_packaged_config()
    cfg["stochastic"]["enabled"] = True
    cfg["stochastic"]["seed"] = seed
    cfg["stochastic"]["wind"]["enabled"] = True
    cfg["stochastic"]["wind"]["noise_std"] = wind_noise_std
    return _write_config(cfg, tmp_path, filename)


def test_same_seed_gives_identical_plan_and_energy(tmp_path):
    config_path = _stochastic_config(tmp_path, seed=123)

    run1 = _run_planner_subprocess(config_path=config_path)
    run2 = _run_planner_subprocess(config_path=config_path)

    assert run1["plan_len"] == run2["plan_len"]
    assert run1["energy"] == pytest.approx(run2["energy"], abs=1e-9)


def test_different_seeds_can_change_energy(tmp_path):
    config_a = _stochastic_config(tmp_path, seed=1, filename="config_seed1.yaml")
    config_b = _stochastic_config(tmp_path, seed=2, filename="config_seed2.yaml")

    run_a = _run_planner_subprocess(config_path=config_a)
    run_b = _run_planner_subprocess(config_path=config_b)

    # Wind noise is seed-dependent, so different seeds should (almost
    # certainly) produce different energy totals — this is a sanity check
    # that stochastic mode isn't silently behaving as a no-op.
    assert run_a["energy"] != pytest.approx(run_b["energy"], abs=1e-9)


def test_stochastic_disabled_ignores_seed_and_matches_baseline(tmp_path):
    """
    With stochastic.enabled=False, the seed is irrelevant — every seed
    should reproduce the exact same deterministic baseline.
    """
    cfg = _load_packaged_config()
    cfg["stochastic"]["enabled"] = False
    cfg["stochastic"]["seed"] = 999  # arbitrary — must have no effect
    config_path = _write_config(cfg, tmp_path, "config_seed_irrelevant.yaml")

    result = _run_planner_subprocess(config_path=config_path)
    assert result["plan_len"] == BASELINE_ACTIONS
    assert result["energy"] == pytest.approx(BASELINE_ENERGY, abs=0.05)