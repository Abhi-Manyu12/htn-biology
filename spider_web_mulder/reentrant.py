"""IPyHOP adapters for the actual Mulder construction HTN and actor.

Both modes share the domain. Fresh starts at the root; retained re-enters at
an actual failed action leaf. The finite refresh alternatives let a stale
command be regenerated without declaring a transient miss permanently invalid.
"""
from copy import deepcopy
import time

import os
from pathlib import Path
import sys
import tempfile

VENDOR = Path(__file__).resolve().parents[1] / 'third_party' / 'IPyHOP'
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'mulder-matplotlib'))
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))
import ipyhop
if not Path(ipyhop.__file__).resolve().is_relative_to(VENDOR.resolve()):
    raise RuntimeError('A different IPyHOP import shadows the pinned implementation')
from networkx import dfs_preorder_nodes

from .model import (build_web, build_component, build_component_with_wait,
                    place_segment, wait_for_support)


class ObservedState:
    def __init__(self, state):
        self.__dict__.update(state.__dict__)

    def copy(self):
        return deepcopy(self)

    def update(self, other):
        self.__dict__.update(other.__dict__)
        return self


class MulderPlanner:
    def __init__(self, mode, counter, record_trees=False):
        if mode not in ('ipyhop_fresh', 'ipyhop_retained'):
            raise ValueError(mode)
        self.record_trees = record_trees
        self.mode = mode
        self.counter = counter
        self.node_queue = []
        self.snapshots = []
        self.reentries = 0
        self.wall_s = 0.
        self.initialized = False
        methods, actions = ipyhop.Methods(), ipyhop.Actions()

        def action(fn):
            def adapted(*args):
                result = fn(*args)
                return None if result is False else result
            adapted.__name__ = fn.__name__
            return adapted

        actions.declare_actions([action(place_segment), action(wait_for_support)])

        def counted(fn):
            def adapted(*args):
                counter[0] += 1
                result = fn(*args)
                return None if result is False else result
            adapted.__name__ = fn.__name__
            return adapted

        def component(fn):
            def adapted(state, task):
                result = fn(state, task)
                if result is False:
                    return None
                return [('perform_segment', a[1]) if a[0] == 'place_segment' else a
                        for a in result]
            adapted.__name__ = fn.__name__
            return adapted

        def perform_segment(state, index):
            if index in state.done:
                return []
            return [('place_segment', index,
                     state.motion.world(state.segments[index].end, state.snapshot_time))]

        methods.declare_task_methods('build_web', [counted(build_web)])
        methods.declare_task_methods('build_component', [counted(component(fn)) for fn in
                                     (build_component, build_component_with_wait)])
        # Register a finite family of equivalent refresh methods. IPyHOP tries
        # the next method on failure; these regenerate the command from the
        # observed clock. Actor budgets still limit actual retry attempts.
        self.methods = methods
        self.actions = actions
        self.perform = perform_segment
        self.counted = counted
        self.planner = None

    def plan(self, state):
        started = time.perf_counter()
        try:
            observed = ObservedState(state)
            resume = self.mode == 'ipyhop_retained' and self.initialized
            if not self.initialized:
                alternatives = []
                for k in range(state.motion.settings.max_repairs_per_action + 2):
                    def refresh(s, i, fn=self.perform):
                        return fn(s, i)
                    refresh.__name__ = f'current_target_{k}'
                    alternatives.append(self.counted(refresh))
                self.methods.declare_task_methods('perform_segment', alternatives)
                self.planner = ipyhop.IPyHOP(self.methods, self.actions)
            failed = self.node_queue[0] if resume and self.node_queue else None
            if resume:
                if failed is None:
                    raise RuntimeError('Missing failed leaf for retained-tree recovery')
                result = self.planner.replan(observed, failed)
                self.reentries += 1
            else:
                result = self.planner.plan(observed, [('build_web',)])
            self.initialized = True
            ids = [i for i in dfs_preorder_nodes(self.planner.sol_tree, source=0)
                   if self.planner.sol_tree.nodes[i]['type'] == 'A' and
                   (not resume or self.planner.sol_tree.nodes[i]['tag'] == 'new')]
            if len(ids) != len(result):
                raise RuntimeError('Mulder IPyHOP leaf/command mismatch')
            if not result and len(state.done) != len(state.segments):
                raise RuntimeError('IPyHOP exhausted search before construction finished')
            # Symbolic search must produce exactly the remaining ordered indices.
            indices = [a[1] for a in result if a[0] == 'place_segment']
            expected = [s.index for s in state.segments if s.index not in state.done]
            if indices != expected:
                raise RuntimeError('Recovery omitted or repeated a construction segment')
            self.node_queue = ids
            if self.record_trees:
                self.snapshots.append(dict(event='planner_tree', mode=self.mode,
                reentry=resume, failed_node=failed, done=sorted(state.done),
                nodes=[dict(id=i, info=a['info'], kind=a['type'], tag=a.get('tag'),
                            method=getattr(a.get('selected_method'), '__name__', None))
                       for i,a in self.planner.sol_tree.nodes.items()],
                edges=list(self.planner.sol_tree.edges)))
            return result
        finally:
            self.wall_s += time.perf_counter() - started

    def completed(self):
        self.node_queue.pop(0)
