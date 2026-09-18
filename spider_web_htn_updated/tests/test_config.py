"""
test_config.py — Verifies config.yaml loading, validation, and the
override mechanism (SPIDER_WEB_CONFIG) used for running alternate
environments.
"""

import os
import tempfile

import pytest
import yaml

from spider_web_htn_updated.config_loader import load_config, ConfigError, CONFIG


def test_default_config_loads_successfully():
    cfg = load_config()
    assert "environment" in cfg
    assert "domain" in cfg


def test_default_config_has_required_keys():
    env = CONFIG["environment"]
    dom = CONFIG["domain"]
    for key in ("nodes", "walkable_edges", "spider_start_pos", "structure_nodes"):
        assert key in env
    for key in ("min_proto_radii", "target_radii_count", "target_frame_count",
                "frame_pairs", "radii_anchor_order", "proto_hub_anchors",
                "spiral_nodes", "default_hub_name"):
        assert key in dom


def test_missing_domain_section_raises_config_error(tmp_path):
    bad_cfg = {"environment": {
        "nodes": {"a": [0, 0]},
        "walkable_edges": [],
        "spider_start_pos": "a",
        "structure_nodes": ["a"],
    }}
    path = tmp_path / "bad_config.yaml"
    path.write_text(yaml.safe_dump(bad_cfg))

    with pytest.raises(ConfigError):
        load_config(str(path))


def test_missing_required_domain_key_raises_config_error(tmp_path):
    bad_cfg = {
        "environment": {
            "nodes": {"a": [0, 0]},
            "walkable_edges": [],
            "spider_start_pos": "a",
            "structure_nodes": ["a"],
        },
        "domain": {
            # missing min_proto_radii and others on purpose
            "target_radii_count": 8,
        },
    }
    path = tmp_path / "bad_domain.yaml"
    path.write_text(yaml.safe_dump(bad_cfg))

    with pytest.raises(ConfigError):
        load_config(str(path))


def test_empty_config_file_raises_config_error(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("")
    with pytest.raises(ConfigError):
        load_config(str(path))


def test_node_coords_normalised_to_float_tuples():
    cfg = load_config()
    for name, coord in cfg["environment"]["nodes"].items():
        assert isinstance(coord, tuple)
        assert len(coord) == 2
        assert all(isinstance(c, float) for c in coord)
