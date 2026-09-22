"""
instrumentation.py — Lightweight counters for metrics GTPyhop doesn't expose
natively, used to fill in the Way-Forward "Formal Evaluation Protocol"
metrics table (future plan.pdf, Part 1, Section 3):

    Decomposition Depth (D): "Tree nodes visited during planning" — a count
    of method-decomposition attempts, not a max-recursion-depth value (per
    the table's own definition). We get this by wrapping each registered
    HTN method function so every *attempt* to apply it (successful or not —
    GTPyhop tries a method and backtracks on failure, and every such try is
    a node in the search tree) increments a counter.

Usage: wrap method functions with `count_calls(...)` when registering them
with gtpyhop.declare_task_methods, call `reset_decomposition_counter()`
immediately before find_plan, and read `get_decomposition_counter()` after.
"""

import functools

_counter = {"value": 0}


def reset_decomposition_counter():
    _counter["value"] = 0


def get_decomposition_counter():
    return _counter["value"]


def count_calls(func):
    """Wrap a method function so every call increments the shared counter."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _counter["value"] += 1
        return func(*args, **kwargs)
    return wrapper


def count_calls_all(*funcs):
    """Apply count_calls to each of several method functions at once."""
    return [count_calls(f) for f in funcs]
