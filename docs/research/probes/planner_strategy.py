"""Audit GTPyhop in an isolated process; does not modify application code.

python3 docs/research/probes/planner_strategy.py --output /tmp/strategy.json
The toy task's first applicable method has an impossible descendant; its
second method succeeds. This distinguishes deep search backtracking from
merely trying another immediately inapplicable method.
"""

import argparse
import contextlib
import hashlib
import importlib
import io
import json
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()):
    import gtpyhop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    engine = importlib.import_module("gtpyhop.main")
    original_strategy = engine._current_seek_plan
    original_verbose = gtpyhop.get_verbose_level()
    source = Path(engine.__file__)
    observations = []
    calls = []

    def impossible(state):
        return False

    def finish(state):
        state.finished = True
        return state

    def first_method(state):
        calls.append("first_method")
        return [("impossible",)]

    def second_method(state):
        calls.append("second_method")
        return [("finish",)]

    with contextlib.redirect_stdout(io.StringIO()):
        gtpyhop.Domain("documentation_strategy_probe")
        gtpyhop.declare_actions(impossible,finish)
        gtpyhop.declare_task_methods("complete",first_method,second_method)
        gtpyhop.set_verbose_level(0)
        try:
            for label in ("installed_default","iterative_dfs_backtracking"):
                if label != "installed_default":
                    gtpyhop.set_recursive_planning(label)
                calls.clear()
                state = gtpyhop.State("probe")
                state.finished = False
                result = gtpyhop.find_plan(state,[("complete",)])
                observations.append(dict(configuration=label,strategy_function=engine._current_seek_plan.__name__,
                                         plan=result,methods_called=list(calls),live_state_mutated=state.finished))
        finally:
            # This private assignment restores the exact observed function in
            # this audit process; no application strategy is changed on disk.
            engine._current_seek_plan = original_strategy
            gtpyhop.set_verbose_level(original_verbose)
    record = dict(audit_date="2026-10-20",gtpyhop_version=getattr(gtpyhop,"__version__","unknown"),
                  installed_default_strategy=original_strategy.__name__,
                  engine_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  probe_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  observations=observations,
                  qualification="Standalone toy audit, not an IPyHOP implementation or a rerun of the Mulder study.")
    if args.output:
        if args.output.exists():
            parser.error("Choose a new audit output path")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))


if __name__ == "__main__":
    main()
