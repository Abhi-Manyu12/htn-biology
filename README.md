# Zschokke 1996 — Orb Web Construction HTN Planner

A Hierarchical Task Network (HTN) planner built with [GTPyhop](https://github.com/dananau/GTPyhop) that models the orb web construction behaviour of *Araneus diadematus* (European garden spider) as documented in:

> **Zschokke, S. (1996).** Early stages of orb web construction in *Araneus diadematus* Clerck. *Revue Suisse de Zoologie*, vol. hors série, 709–720.

## Key Concepts

The model captures Zschokke's central finding: **early construction stages are variable and opportunistic**, while **later stages follow a rigid, stereotyped programme**.

| Phase | Behaviour | HTN Approach |
|---|---|---|
| Exploration & bridging | Spider walks detour to bridge gap between sticks | Sequential method |
| Proto-hub establishment | Highly variable — multiple proto-radius construction variants | **Multiple alternative methods with backtracking** |
| Frame construction | "Quite a rigid pattern" — top frame first | Single procedural method |
| Radii construction | Circle hub, fill gaps | Single procedural method |
| Auxiliary & capture spirals | Seamless transition from circling | Single procedural method |

## Project Structure

```
btp/
├── run.py                    # Entry point — run this
├── requirements.txt          # Python dependencies
├── .gitignore
├── README.md
│
├── spider_web_htn/           # Main package
│   ├── __init__.py
│   ├── state.py              # WebState + initial state factory
│   ├── operators.py          # Primitive actions (walk, anchor, etc.)
│   ├── methods.py            # HTN methods (early + late stages)
│   ├── main.py               # Domain setup + plan execution
│   └── utils.py              # Distance calculations, node geometry
│
├── HTN Coding Plan.pdf       # Implementation guide
└── zschokke1996rsz.pdf       # Original research paper
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the planner
python run.py
```

## How It Works

1. **State** (`state.py`): Tracks spider position, thread network (as a graph), proto-hub status, and cumulative energy expenditure (Zschokke's distance-as-cost metric).

2. **Operators** (`operators.py`): Nine primitive actions — `walk`, `anchor`, `lay_thread`, `drop_down`, `swing_tarzan` (Tarzan method), `reel_up`, `insert_radius`, plus frame/spiral/marking operators.

3. **Methods** (`methods.py`):
   - **Variable early stages**: `establish_proto_hub` has three alternative methods (`via_walk`, `via_drop`, `via_tarzan`), mirroring the three ways Zschokke observed spiders reaching the supporting structure. GTPyhop backtracks among them.
   - **Stereotyped later stages**: `build_remaining_web` → `build_frame` → `build_radii` → `build_auxiliary_spiral` → `build_capture_spiral` in a fixed sequence.

4. **Planner** (`main.py`): Creates the GTPyhop domain, registers all operators and methods, runs `find_plan()`, and prints a categorised action summary with energy cost.
