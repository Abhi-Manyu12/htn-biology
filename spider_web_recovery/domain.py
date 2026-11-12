"""Shared domain for fresh DFS and retained-tree IPyHOP recovery.

Sector construction is an abstraction, not the Mulder geometry generator.
Scaffold links exist initially; newly built radii become traversable links.
"""
from copy import deepcopy
from dataclasses import dataclass
import heapq
import math
import gtpyhop


@dataclass(frozen=True)
class Config:
    sectors: int = 4
    depth: int = 1
    silk_cm: float = 500.0
    speed_cm_s: float = 1.0
    amplitude_cm: float = 10.0
    frequency_hz: float = 0.05
    max_repairs: int = 20
    max_attempts: int = 500
    transient_retries: int = 2
    max_elapsed_s: float = 20000.0

    def __post_init__(self):
        for name in ("sectors","depth","max_repairs","max_attempts","transient_retries"):
            value = getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,int):
                raise ValueError(f"{name} must be an integer")
        if self.sectors < 2 or not 0 <= self.depth <= 8:
            raise ValueError("Require sectors >= 2 and depth between 0 and 8")
        if self.max_repairs < 0 or self.max_attempts < 1 or self.transient_retries < 0:
            raise ValueError("Invalid execution budgets")
        for name in ("silk_cm","speed_cm_s","amplitude_cm","frequency_hz","max_elapsed_s"):
            value = getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {name}")
        if self.speed_cm_s == 0 or self.max_elapsed_s == 0:
            raise ValueError("Speed and elapsed budget must be positive")


def edge(a,b):
    return tuple(sorted((a,b)))


class World(gtpyhop.State):
    """Observed symbolic/physical state compatible with both planner APIs."""
    def __init__(self,config):
        self.__name__ = "recovery_world"
        self.config = config
        self.coords = {"hub":(15.,15.),"left":(5.,15.),"right":(25.,15.)}
        self.scaffold = {edge("hub","left"),edge("hub","right"),edge("left","right")}
        self.available = {}
        self.radii = {}
        self.captures = {}
        self.restore_captures = set()
        self.blocked = set()
        self.position = "hub"
        self.position_material = self.coords["hub"]
        self.silk_remaining = config.silk_cm
        self.silk_used = 0.0
        self.silk_lost = 0.0
        self.clock_s = 0.0
        for i in range(config.sectors):
            angle = math.pi/2+2*math.pi*i/config.sectors
            for prefix,offset in (("A",0.),("B",0.12)):
                theta = angle+offset
                point = (15+14*math.cos(theta),15+14*math.sin(theta))
                anchor = f"{prefix}{i}"
                self.coords[anchor] = point
                self.available[anchor] = True
                junction = "left" if point[0] < 15 else "right"
                self.scaffold.add(edge(anchor,junction))

    def copy(self):
        return deepcopy(self)

    def update(self,other):
        self.__dict__.update(other.__dict__)
        return self


def valid_radius(state,i):
    return i in state.radii and state.available.get(state.radii[i],False)


def valid_capture(state,i):
    previous = (i-1)%state.config.sectors
    return (valid_radius(state,i) and valid_radius(state,previous) and
            state.captures.get(i)==(state.radii[i],state.radii[previous]))


def achieved(state):
    return all(valid_radius(state,i) and valid_capture(state,i) for i in range(state.config.sectors))


def resource_lower_bound(state):
    required = 0.
    for i in range(state.config.sectors):
        if not valid_radius(state,i):
            choices = [math.dist(state.coords["hub"],state.coords[f"{prefix}{i}"])
                       for prefix in ("A","B") if state.available[f"{prefix}{i}"]]
            if not choices:
                return math.inf
            required += min(choices)
        if not valid_capture(state,i):
            required += 5
    return required


def links(state):
    radii = {edge("hub",anchor) for i,anchor in state.radii.items() if valid_radius(state,i)}
    return (state.scaffold|radii)-state.blocked


def route(state,target):
    queue = [(0.,(state.position,))]
    visited = set()
    graph = links(state)
    while queue:
        cost,path = heapq.heappop(queue)
        current = path[-1]
        if current == target:
            return path
        if current in visited:
            continue
        visited.add(current)
        for a,b in sorted(graph):
            neighbor = b if a==current else a if b==current else None
            if neighbor is not None and neighbor not in visited:
                length = math.dist(state.coords[current],state.coords[neighbor])
                heapq.heappush(queue,(cost+length,path+(neighbor,)))
    return None


def move(state,source,target,owner):
    if state.position != source or edge(source,target) not in links(state):
        return None
    state.clock_s += math.dist(state.coords[source],state.coords[target])/state.config.speed_cm_s
    state.position = target
    state.position_material = state.coords[target]
    return state


def attach(state,sector,anchor,owner):
    cost = math.dist(state.coords["hub"],state.coords[anchor])
    if state.position != anchor or not state.available[anchor] or state.silk_remaining+1e-9 < cost:
        return None
    state.radii[sector] = anchor
    state.silk_remaining -= cost
    state.silk_used += cost
    state.clock_s += 0.5
    return state


def capture(state,sector,anchor,previous_anchor,owner):
    previous = (sector-1)%state.config.sectors
    if (state.position != "hub" or not valid_radius(state,sector) or not valid_radius(state,previous) or
        state.radii[sector]!=anchor or state.radii[previous]!=previous_anchor or state.silk_remaining+1e-9 < 5):
        return None
    state.captures[sector] = (anchor,previous_anchor)
    state.restore_captures.discard(sector)
    state.silk_remaining -= 5
    state.silk_used += 5
    state.clock_s += 0.5
    return state


def build_web(state):
    return [("radial_phase",),("capture_phase",)]


def radial_phase(state):
    return [("layer",state.config.depth,("build_radius",i,("radius",i))) for i in range(state.config.sectors)]


def capture_phase(state):
    return [("layer",state.config.depth,("build_capture",i,("capture",i))) for i in range(state.config.sectors)]


def layer(state,depth,task):
    return [("layer",depth-1,task)] if depth else [task]


def radius_done(state,i,owner):
    return [] if valid_radius(state,i) else None


def radius_primary(state,i,owner):
    anchor = f"A{i}"
    if valid_radius(state,i) or not state.available[anchor]:
        return None
    return [("travel",anchor,owner),("attach",i,anchor,owner),("travel","hub",owner)]


def radius_backup(state,i,owner):
    anchor = f"B{i}"
    if valid_radius(state,i) or not state.available[anchor]:
        return None
    return [("travel",anchor,owner),("attach",i,anchor,owner),("travel","hub",owner)]


def travel_done(state,target,owner):
    return [] if state.position==target else None


def travel_path(state,target,owner):
    path = route(state,target)
    return [("move",a,b,owner) for a,b in zip(path,path[1:])] if path and len(path)>1 else None


def travel_recompute(state,target,owner):
    # Same routing knowledge on re-entry, evaluated against newly observed edges.
    # Separate method instance permits an untried refinement after execution failure.
    return travel_path(state,target,owner)


def capture_done(state,i,owner):
    return [] if valid_capture(state,i) else None


def capture_direct(state,i,owner):
    previous = (i-1)%state.config.sectors
    if valid_capture(state,i) or not valid_radius(state,i) or not valid_radius(state,previous):
        return None
    return [("travel","hub",owner),("capture",i,state.radii[i],state.radii[previous],owner)]


def capture_repair(state,i,owner):
    if valid_capture(state,i):
        return None
    # Structural damage can invalidate already executed effects. Restore them
    # explicitly; an execution-history entry is not a permanent truth assertion.
    needed = any(not valid_radius(state,j) for j in range(state.config.sectors)) or bool(state.restore_captures)
    return [("restore_structure",owner),("build_capture",i,owner)] if needed else None


def restore_structure(state,owner):
    return [("build_radius",j,owner) for j in range(state.config.sectors) if not valid_radius(state,j)] + [
        ("build_capture",j,owner) for j in sorted(state.restore_captures)]


ACTIONS = (move,attach,capture)
METHODS = {"build_web":(build_web,),"radial_phase":(radial_phase,),"capture_phase":(capture_phase,),
           "layer":(layer,),"build_radius":(radius_done,radius_primary,radius_backup),
           "travel":(travel_done,travel_path,travel_recompute),
           "build_capture":(capture_done,capture_direct,capture_repair),"restore_structure":(restore_structure,)}


def observe_anchor_loss(state,anchor):
    state.available[anchor] = False
    invalid = [i for i in state.captures if anchor in state.captures[i]]
    for i in invalid:
        del state.captures[i]
        state.restore_captures.add(i)
    for i in [i for i,a in state.radii.items() if a==anchor]:
        del state.radii[i]
    return invalid
