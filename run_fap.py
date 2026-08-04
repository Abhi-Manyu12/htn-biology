#!/usr/bin/env python3
"""
run_fap.py — Entry point to run the 5 Fixed Action Patterns (FAPs) Orb Web HTN Planner.

Models the 5 Macro-Stages:
1. Proto-Web & Frame FAP (Y-Shape core creation)
2. Radial Spoke Construction FAP (Leg angle measurement & tension balance)
3. Auxiliary (Scaffolding) Spiral FAP
4. Capture (Sticky) Spiral FAP (Silk chemistry switch & destructive recycling)
5. Stabilimentum Construction FAP

Usage:
    python3 run_fap.py
"""

from spider_web_fap.main import run_fap_planner

if __name__ == "__main__":
    run_fap_planner(verbose_level=1)
