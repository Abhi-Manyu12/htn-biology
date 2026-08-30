"""
astar.py — flat-state A* search over WebState.

A* uses:
    f(s) = g(s) + h(s)

The heuristic is deliberately conservative.  A separate progress tie-breaker
prefers states with more completed mandatory construction work without
changing the f-ordering of A*.
"""

import heapq
import time

from .operators import get_successors, is_goal
from .state import state_key
from .heuristic import heuristic, progress_score


class SearchResult:
    """Container for A* output and experimental search statistics."""

    def __init__(
        self,
        success,
        plan,
        energy,
        nodes_expanded,
        wall_time,
        max_depth,
        final_state=None,
        max_open_size=0,
        generated_nodes=0,
        lower_bound=None,
        lower_bound_valid=False,
    ):
        self.success = success
        self.plan = plan or []
        self.energy = energy
        self.nodes_expanded = nodes_expanded
        self.wall_time = wall_time
        self.max_depth = max_depth
        self.final_state = final_state
        self.max_open_size = max_open_size
        self.generated_nodes = generated_nodes
        # Lower bound on the true optimal solution cost, extracted from the
        # open list at the moment of a time/node-limit cutoff (see find_plan
        # docstring). Only a SOUND admissible lower bound when the run used
        # weight == 1.0 — weighted A* (weight > 1.0) does not guarantee
        # non-decreasing f-expansion order, so this number is reported but
        # flagged invalid in that case.
        self.lower_bound = lower_bound
        self.lower_bound_valid = lower_bound_valid

    def to_dict(self):
        return {
            "success": self.success,
            "plan_length": len(self.plan),
            "energy": round(self.energy, 2),
            "nodes_expanded": self.nodes_expanded,
            "generated_nodes": self.generated_nodes,
            "max_open_size": self.max_open_size,
            "wall_time_s": round(self.wall_time, 4),
            "max_depth": self.max_depth,
            "lower_bound": (
                round(self.lower_bound, 2) if self.lower_bound is not None else None
            ),
            "lower_bound_valid": self.lower_bound_valid,
        }


def _reconstruct_plan(parent, action_from_parent, goal_key):
    """Reconstruct a plan without copying the whole list at every successor."""
    actions = []
    key = goal_key

    while parent[key] is not None:
        actions.append(action_from_parent[key])
        key = parent[key]

    actions.reverse()
    return actions


def _extract_lower_bound(open_heap, weight):
    """
    Extract a lower bound on the true optimal solution cost from the current
    open list.

    For an admissible heuristic h, standard A* theory guarantees: as long as
    the goal has not yet been found, min(f) over all nodes still in OPEN is
    <= the true optimal solution cost. (If a cheaper solution existed, some
    node on that solution path would already be in OPEN with a smaller f,
    by admissibility — contradiction.) This holds even with lazy deletion
    (stale duplicate heap entries only ever have f >= the fresh entry for
    the same state, since h depends only on the state's key fields, not on
    the accumulated g), so scanning the raw heap (rather than a de-duplicated
    frontier) is safe.

    IMPORTANT: this guarantee requires weight == 1.0 (standard admissible
    A*). Weighted A* (weight > 1.0) does not guarantee non-decreasing f
    across expansions, so a node on the optimal path can be closed with a
    suboptimal g before ever appearing in OPEN with its true optimal g —
    breaking the argument above. We still return the number for weighted
    runs (it's informative), but flag it as unsound via `valid`.
    """
    if not open_heap:
        return None, False
    return open_heap[0][0], (weight <= 1.0)


def find_plan(
    initial_state,
    time_limit_s=None,
    max_nodes=None,
    energy_limit=None,
    weight=1.0,
):
    """
    Run flat-state A* from initial_state.

    Parameters
    ----------
    initial_state : WebState
    time_limit_s : float or None
        Wall-clock budget.
    max_nodes : int or None
        Maximum number of states actually expanded.
    energy_limit : float or None
        Do not expand states whose accumulated g exceeds this value.
    weight : float
        Weight on the heuristic: f = g + weight * h. weight=1.0 is standard
        admissible A* (optimal plans, guaranteed). weight>1.0 is "weighted
        A*" — trades optimality guarantees for much faster convergence when
        the heuristic is weak relative to the branching factor. Useful for
        just getting ANY plan when standard A* stalls.

    Notes
    -----
    The node limit is deliberately checked against *expanded* states, making
    it suitable for the experimental "search budget" metric.
    """
    start_time = time.perf_counter()

    start_key = state_key(initial_state)
    start_g = float(initial_state.energy_expended)
    start_h = heuristic(initial_state)

    # Heap tuple:
    #   (f, -progress, g, counter, key, state)
    #
    # -progress is only a tie-breaker.  f remains the first priority, so
    # admissible-A* cost ordering is preserved (when weight == 1.0).
    counter = 0
    open_heap = [
        (
            start_g + weight * start_h,
            -progress_score(initial_state),
            start_g,
            counter,
            start_key,
            initial_state,
        )
    ]

    closed = set()
    best_g = {start_key: start_g}

    parent = {start_key: None}
    action_from_parent = {}
    depths = {start_key: 0}

    nodes_expanded = 0
    generated_nodes = 1
    max_open_size = 1
    max_depth = 0
    best_progress = progress_score(initial_state)
    best_state = initial_state
    best_state_g = start_g

    while open_heap:
        elapsed = time.perf_counter() - start_time

        if time_limit_s is not None and elapsed >= time_limit_s:
            lb, lb_valid = _extract_lower_bound(open_heap, weight)
            return SearchResult(
                False,
                None,
                best_state_g,
                nodes_expanded,
                elapsed,
                max_depth,
                final_state=best_state,
                max_open_size=max_open_size,
                generated_nodes=generated_nodes,
                lower_bound=lb,
                lower_bound_valid=lb_valid,
            )

        if max_nodes is not None and nodes_expanded >= max_nodes:
            lb, lb_valid = _extract_lower_bound(open_heap, weight)
            return SearchResult(
                False,
                None,
                best_state_g,
                nodes_expanded,
                elapsed,
                max_depth,
                final_state=best_state,
                max_open_size=max_open_size,
                generated_nodes=generated_nodes,
                lower_bound=lb,
                lower_bound_valid=lb_valid,
            )

        f, _, g, _, key, state = heapq.heappop(open_heap)

        # Ignore stale heap entries.
        if g > best_g.get(key, float("inf")):
            continue

        if key in closed:
            continue

        # Apply the resource constraint BEFORE closing/expanding the state.
        if energy_limit is not None and g > energy_limit:
            continue

        closed.add(key)
        nodes_expanded += 1

        current_progress = progress_score(state)

        if (
            current_progress > best_progress
            or (
                current_progress == best_progress
                and state.proto_hub_exists
                and not best_state.proto_hub_exists
            )
        ):
            best_progress = current_progress
            best_state = state
            best_state_g = g

        # Depth is stored when the node is generated, so this is O(1).
        depth = depths[key]
        max_depth = max(max_depth, depth)

        if is_goal(state):
            plan = _reconstruct_plan(parent, action_from_parent, key)
            return SearchResult(
                True,
                plan,
                state.energy_expended,
                nodes_expanded,
                time.perf_counter() - start_time,
                max_depth,
                final_state=state,
                max_open_size=max_open_size,
                generated_nodes=generated_nodes,
            )

        successors = list(get_successors(state))

        for action, cost, new_state in successors:
            # Defensive check: operators should never return negative costs.
            if cost < 0:
                continue

            new_g = g + cost

            if energy_limit is not None and new_g > energy_limit:
                continue

            new_key = state_key(new_state)

            if new_key in closed:
                continue

            old_g = best_g.get(new_key)
            if old_g is not None and old_g <= new_g:
                continue

            best_g[new_key] = new_g
            parent[new_key] = key
            action_from_parent[new_key] = action
            depths[new_key] = depth + 1

            counter += 1
            generated_nodes += 1

            new_h = heuristic(new_state)
            heapq.heappush(
                open_heap,
                (
                    new_g + weight * new_h,
                    -progress_score(new_state),
                    new_g,
                    counter,
                    new_key,
                    new_state,
                ),
            )

        max_open_size = max(max_open_size, len(open_heap))

    return SearchResult(
            False,
            None,
            best_state_g,
            nodes_expanded,
            time.perf_counter() - start_time,
            max_depth,
            final_state=best_state,
            max_open_size=max_open_size,
            generated_nodes=generated_nodes,
        )