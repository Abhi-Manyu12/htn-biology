"""Pinned upstream IPyHOP and explicitly selected GTPyhop DFS adapters."""
import contextlib
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import time

import gtpyhop

from .domain import ACTIONS,METHODS,achieved,resource_lower_bound

VENDOR = Path(__file__).resolve().parents[1]/"third_party"/"IPyHOP"
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"mulder-matplotlib"))
if str(VENDOR) not in sys.path:
    sys.path.insert(0,str(VENDOR))
import ipyhop
if not Path(ipyhop.__file__).resolve().is_relative_to(VENDOR.resolve()):
    raise RuntimeError("A different IPyHOP import shadows the pinned implementation")
from networkx import dfs_preorder_nodes


class Backend:
    def __init__(self,name):
        if name not in ("fresh_root","component","ipyhop_fresh","ipyhop"):
            raise ValueError(name)
        self.name = name
        self.method_calls = 0
        self.planning_calls = 0
        self.planning_wall_s = 0.0
        self.iterations = 0
        self.tree_snapshots = []
        if name in ("ipyhop","ipyhop_fresh"):
            methods = ipyhop.Methods()
            actions = ipyhop.Actions()
            actions.declare_actions(list(ACTIONS))
            for task,functions in METHODS.items():
                methods.declare_task_methods(task,[self.counted(fn) for fn in functions])
            self.planner = ipyhop.IPyHOP(methods,actions)
        else:
            self.planner = None

    def counted(self,function,gtp=False):
        def wrapped(*args):
            self.method_calls += 1
            result = function(*args) if args[0].silk_remaining+1e-9 >= resource_lower_bound(args[0]) else None
            return False if gtp and result is None else result
        wrapped.__name__ = function.__name__
        return wrapped

    def snapshot(self,label,failed_node=None):
        if self.planner is None:
            return
        nodes = []
        for identity,attrs in self.planner.sol_tree.nodes.items():
            nodes.append(dict(id=identity,info=attrs["info"],kind=attrs["type"],status=attrs["status"],
                              tag=attrs.get("tag"),selected_method=getattr(attrs.get("selected_method"),"__name__",None)))
        self.tree_snapshots.append(dict(label=label,failed_node=failed_node,nodes=nodes,
                                        edges=list(self.planner.sol_tree.edges)))

    def plan(self,state,failed_node=None,owner=None):
        started = time.perf_counter()
        self.planning_calls += 1
        try:
            if self.planner is not None:
                resume = self.name=="ipyhop" and failed_node is not None
                result = self.planner.replan(state,failed_node) if resume else self.planner.plan(state,[("build_web",)])
                self.iterations += self.planner.iterations
                self.snapshot("replan" if resume else "fresh_plan",failed_node if resume else None)
                nodes = [i for i in dfs_preorder_nodes(self.planner.sol_tree,source=0)
                         if self.planner.sol_tree.nodes[i]["type"]=="A" and
                         (not resume or self.planner.sol_tree.nodes[i]["tag"]=="new")]
                if len(nodes)!=len(result):
                    raise RuntimeError("IPyHOP leaf-to-command mapping is inconsistent")
                # Upstream can return [] on exhausted search. Empty is only
                # success when the actual observed construction goal holds.
                return list(zip(nodes,result)) if result or achieved(state) else None
            engine = importlib.import_module("gtpyhop.main")
            old_strategy = engine._current_seek_plan
            old_verbose = gtpyhop.get_verbose_level()
            old_domain = gtpyhop.get_current_domain()
            try:
                gtpyhop.Domain("recovery_fresh_dfs")
                def adapted(action):
                    def wrapped(*args):
                        result = action(*args)
                        return False if result is None else result
                    wrapped.__name__ = action.__name__
                    return wrapped
                gtpyhop.declare_actions(*(adapted(a) for a in ACTIONS))
                for task,functions in METHODS.items():
                    gtpyhop.declare_task_methods(task,*(self.counted(fn,gtp=True) for fn in functions))
                gtpyhop.set_recursive_planning("iterative_dfs_backtracking")
                todo = [("build_radius" if owner[0]=="radius" else "build_capture",owner[1],owner)] if owner else [("build_web",)]
                with contextlib.redirect_stdout(io.StringIO()):
                    gtpyhop.set_verbose_level(0)
                    result = gtpyhop.find_plan(state,todo)
            finally:
                engine._current_seek_plan = old_strategy
                with contextlib.redirect_stdout(io.StringIO()):
                    gtpyhop.set_verbose_level(old_verbose)
                if old_domain is not None:
                    gtpyhop.set_current_domain(old_domain)
            return None if result is False or result is None else [(None,a) for a in result]
        finally:
            self.planning_wall_s += time.perf_counter()-started
