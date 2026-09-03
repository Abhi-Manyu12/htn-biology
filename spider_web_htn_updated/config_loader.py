"""
config_loader.py — Loads config.yaml and exposes a validated, importable
CONFIG object used throughout the package.

This is the seam that decouples the domain (operators/methods logic) from
the environment (geometry, thresholds, construction ordering). Swapping in
a different config.yaml (or pointing SPIDER_WEB_CONFIG at another file) lets
the exact same planner code run against a different environment, with no
changes to utils.py / state.py / methods.py.
"""

import os
import yaml

_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

# Allow overriding the config file via environment variable — useful for
# running batches of experiments against different environments without
# editing code (see sensitivity-analysis / comparison experiments).
CONFIG_PATH = os.environ.get("SPIDER_WEB_CONFIG", _DEFAULT_CONFIG_PATH)


class ConfigError(Exception):
    """Raised when config.yaml is missing required keys or malformed."""


def _require(d, key, context):
    if key not in d:
        raise ConfigError(f"Missing required key '{key}' in {context} section of config")
    return d[key]


# ---------------------------------------------------------------------------
# Stochastic section — OPTIONAL. Any key/sub-key a config file omits is
# filled in from these defaults, so:
#   (a) old configs written before Step 6 keep working unchanged, and
#   (b) "enabled: false" (the default) reproduces the original fully
#       deterministic behaviour exactly.
# ---------------------------------------------------------------------------

_STOCHASTIC_DEFAULTS = {
    "enabled": False,
    "seed": 42,
    "wind": {
        "enabled": False,
        "noise_std": 0.08,
    },
    "anchor_availability": {
        "enabled": False,
        "removal_prob": 0.2,
        "removable_nodes": [],
    },
}


def _merge_defaults(user_dict, defaults):
    """Recursively fill in missing keys from `defaults` into `user_dict`."""
    merged = dict(defaults)
    for key, value in (user_dict or {}).items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            merged[key] = _merge_defaults(value, defaults[key])
        else:
            merged[key] = value
    return merged


def load_config(path=None):
    """
    Load and validate the YAML config file.

    Parameters
    ----------
    path : str, optional
        Path to a config YAML file. Defaults to CONFIG_PATH.

    Returns
    -------
    dict
        Parsed and lightly validated config dictionary.
    """
    path = path or CONFIG_PATH
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    if not cfg:
        raise ConfigError(f"Config file at {path} is empty or invalid")

    env = _require(cfg, "environment", "top-level")
    dom = _require(cfg, "domain", "top-level")

    for key in ("nodes", "walkable_edges", "spider_start_pos", "structure_nodes"):
        _require(env, key, "environment")

    for key in ("min_proto_radii", "target_radii_count", "target_frame_count",
                "frame_pairs", "radii_anchor_order", "proto_hub_anchors",
                "spiral_nodes", "default_hub_name"):
        _require(dom, key, "domain")

    # Normalise node coordinates to tuples of floats
    env["nodes"] = {name: tuple(float(c) for c in coord)
                     for name, coord in env["nodes"].items()}

    # Normalise walkable edges to tuples
    env["walkable_edges"] = [tuple(edge) for edge in env["walkable_edges"]]

    # Normalise frame pairs to tuples
    dom["frame_pairs"] = [tuple(pair) for pair in dom["frame_pairs"]]

    env.setdefault("default_distance", 2.0)

    # Stochastic section is optional; merge with defaults either way so
    # downstream code can always do CONFIG["stochastic"][...] safely.
    cfg["stochastic"] = _merge_defaults(cfg.get("stochastic"), _STOCHASTIC_DEFAULTS)

    return cfg


# Module-level singleton — imported everywhere else as:
#   from .config_loader import CONFIG
CONFIG = load_config()


def reload_config(path=None):
    """
    Reload CONFIG in place from a (possibly different) file.

    Useful for scripts that iterate over multiple environment configs in a
    single process (e.g. the sensitivity-analysis sweep) without needing to
    reimport the whole package between runs.
    """
    global CONFIG
    new_cfg = load_config(path)
    CONFIG.clear()
    CONFIG.update(new_cfg)
    return CONFIG
