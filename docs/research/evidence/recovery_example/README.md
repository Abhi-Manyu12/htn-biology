# Actual retained-tree recovery example

Source: recovery_v1_verified, four sectors, depth 0, 10 cm moving supports,
seed 0, permanent_anchor, backend ipyhop.

`events.json` records actual attempts, observed states, failure and re-entry.
`trees.json` contains the initial upstream solution tree and the tree after
replanning. Nodes include IDs, task/action arguments, selected methods and
old/new tags. The failed node ID is in the replan record.

Manuscript SVGs: [initial tree](../../../manuscript/figures/recovery_v1_tree_initial.svg)
and [replanned tree](../../../manuscript/figures/recovery_v1_tree_replanned.svg).
Blue nodes retain old refinements; orange nodes are new. A tree's retained
planning context must not be mistaken for proof that old physical effects
remain valid: this example updates the observed state explicitly.

The upstream author source/license and experiment hashes are recorded in
../recovery_v1_summary.json. These are actual IPyHOP tree snapshots, not a tree
drawn retrospectively from a flat action list.
