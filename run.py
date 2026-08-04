#!/usr/bin/env python3
"""
run.py — Top-level entry point to run the Zschokke 1996 orb web HTN planner.

Usage:
    python run.py
"""

from spider_web_htn.main import run_planner

if __name__ == "__main__":
    run_planner(verbose_level=1)
