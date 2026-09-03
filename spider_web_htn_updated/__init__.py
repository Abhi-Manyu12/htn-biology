"""
spider_web_htn — GTPyhop HTN planner for Zschokke 1996 orb web construction.

Models the web construction behavior of Araneus diadematus using
Hierarchical Task Network planning with GTPyhop.
"""

from .state import create_initial_state, rigid
from .utils import calculate_distance, NODE_COORDS
