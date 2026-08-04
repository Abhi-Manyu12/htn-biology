const PLAN_DATA = {
  "node_coords": {
    "right_stick_top": [
      16.0,
      18.0
    ],
    "right_stick_mid": [
      16.0,
      12.0
    ],
    "right_stick_bottom": [
      16.0,
      0.0
    ],
    "left_stick_top": [
      0.0,
      18.0
    ],
    "left_stick_mid": [
      0.0,
      12.0
    ],
    "left_stick_bottom": [
      0.0,
      0.0
    ],
    "crossbar_right": [
      16.0,
      9.0
    ],
    "crossbar_left": [
      0.0,
      9.0
    ],
    "bottom_path": [
      8.0,
      0.0
    ],
    "proto_hub": [
      8.0,
      12.0
    ],
    "anchor_top_center": [
      8.0,
      18.0
    ],
    "anchor_left_upper": [
      0.0,
      15.0
    ],
    "anchor_left_lower": [
      0.0,
      6.0
    ],
    "anchor_right_upper": [
      16.0,
      15.0
    ],
    "anchor_right_lower": [
      16.0,
      6.0
    ],
    "anchor_bottom_left": [
      3.0,
      0.0
    ],
    "anchor_bottom_center": [
      8.0,
      0.0
    ],
    "anchor_bottom_right": [
      13.0,
      0.0
    ]
  },
  "steps": [
    {
      "action": [
        "walk",
        "right_stick_top",
        "right_stick_bottom"
      ],
      "name": "walk",
      "args": [
        "right_stick_top",
        "right_stick_bottom"
      ],
      "phase": "exploration",
      "energy": 18.0,
      "cumulative_energy": 18.0
    },
    {
      "action": [
        "walk",
        "right_stick_bottom",
        "bottom_path"
      ],
      "name": "walk",
      "args": [
        "right_stick_bottom",
        "bottom_path"
      ],
      "phase": "exploration",
      "energy": 8.0,
      "cumulative_energy": 26.0
    },
    {
      "action": [
        "walk",
        "bottom_path",
        "left_stick_bottom"
      ],
      "name": "walk",
      "args": [
        "bottom_path",
        "left_stick_bottom"
      ],
      "phase": "exploration",
      "energy": 8.0,
      "cumulative_energy": 34.0
    },
    {
      "action": [
        "walk",
        "left_stick_bottom",
        "left_stick_mid"
      ],
      "name": "walk",
      "args": [
        "left_stick_bottom",
        "left_stick_mid"
      ],
      "phase": "exploration",
      "energy": 12.0,
      "cumulative_energy": 46.0
    },
    {
      "action": [
        "lay_thread",
        "left_stick_mid",
        "right_stick_top",
        "bridge"
      ],
      "name": "lay_thread",
      "args": [
        "left_stick_mid",
        "right_stick_top",
        "bridge"
      ],
      "phase": "exploration",
      "energy": 17.1,
      "cumulative_energy": 63.1
    },
    {
      "action": [
        "walk",
        "right_stick_top",
        "left_stick_mid"
      ],
      "name": "walk",
      "args": [
        "right_stick_top",
        "left_stick_mid"
      ],
      "phase": "exploration",
      "energy": 17.1,
      "cumulative_energy": 80.2
    },
    {
      "action": [
        "walk",
        "left_stick_mid",
        "left_stick_top"
      ],
      "name": "walk",
      "args": [
        "left_stick_mid",
        "left_stick_top"
      ],
      "phase": "exploration",
      "energy": 6.0,
      "cumulative_energy": 86.2
    },
    {
      "action": [
        "lay_thread",
        "left_stick_top",
        "right_stick_top",
        "bridge"
      ],
      "name": "lay_thread",
      "args": [
        "left_stick_top",
        "right_stick_top",
        "bridge"
      ],
      "phase": "exploration",
      "energy": 16.0,
      "cumulative_energy": 102.2
    },
    {
      "action": [
        "mark_high_thread_done"
      ],
      "name": "mark_high_thread_done",
      "args": [],
      "phase": "exploration",
      "energy": 0.0,
      "cumulative_energy": 102.2
    },
    {
      "action": [
        "anchor",
        "proto_hub"
      ],
      "name": "anchor",
      "args": [
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 102.2
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "left_stick_top",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "left_stick_top",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 112.2
    },
    {
      "action": [
        "reel_up",
        "left_stick_top",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "left_stick_top",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 122.2
    },
    {
      "action": [
        "insert_radius",
        "left_stick_top",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "left_stick_top",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 122.2
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "anchor_left_upper",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "anchor_left_upper",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 8.5,
      "cumulative_energy": 130.7
    },
    {
      "action": [
        "reel_up",
        "anchor_left_upper",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "anchor_left_upper",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 8.5,
      "cumulative_energy": 139.3
    },
    {
      "action": [
        "insert_radius",
        "anchor_left_upper",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_left_upper",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 139.3
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "anchor_right_lower",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "anchor_right_lower",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 149.3
    },
    {
      "action": [
        "reel_up",
        "anchor_right_lower",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "anchor_right_lower",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 159.3
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_lower",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_lower",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 159.3
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "right_stick_top",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "right_stick_top",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 169.3
    },
    {
      "action": [
        "reel_up",
        "right_stick_top",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "right_stick_top",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 179.3
    },
    {
      "action": [
        "insert_radius",
        "right_stick_top",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "right_stick_top",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 179.3
    },
    {
      "action": [
        "mark_proto_hub",
        "proto_hub"
      ],
      "name": "mark_proto_hub",
      "args": [
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 179.3
    },
    {
      "action": [
        "relocate_hub",
        "proto_hub",
        "proto_hub"
      ],
      "name": "relocate_hub",
      "args": [
        "proto_hub",
        "proto_hub"
      ],
      "phase": "hub_relocate",
      "energy": 6.0,
      "cumulative_energy": 185.3
    },
    {
      "action": [
        "walk",
        "proto_hub",
        "left_stick_top"
      ],
      "name": "walk",
      "args": [
        "proto_hub",
        "left_stick_top"
      ],
      "phase": "hub_relocate",
      "energy": 10.0,
      "cumulative_energy": 195.3
    },
    {
      "action": [
        "lay_frame_thread",
        "left_stick_top",
        "right_stick_top"
      ],
      "name": "lay_frame_thread",
      "args": [
        "left_stick_top",
        "right_stick_top"
      ],
      "phase": "hub_relocate",
      "energy": 16.0,
      "cumulative_energy": 211.3
    },
    {
      "action": [
        "walk",
        "right_stick_top",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "right_stick_top",
        "proto_hub"
      ],
      "phase": "hub_relocate",
      "energy": 10.0,
      "cumulative_energy": 221.3
    },
    {
      "action": [
        "mark_top_frame_done"
      ],
      "name": "mark_top_frame_done",
      "args": [],
      "phase": "hub_relocate",
      "energy": 0.0,
      "cumulative_energy": 221.3
    },
    {
      "action": [
        "construct_frame_with_radius",
        "proto_hub",
        "anchor_left_upper",
        "anchor_left_lower",
        null
      ],
      "name": "construct_frame_with_radius",
      "args": [
        "proto_hub",
        "anchor_left_upper",
        "anchor_left_lower",
        null
      ],
      "phase": "frame",
      "energy": 27.5,
      "cumulative_energy": 248.8
    },
    {
      "action": [
        "construct_frame_with_radius",
        "proto_hub",
        "anchor_left_lower",
        "anchor_right_lower",
        null
      ],
      "name": "construct_frame_with_radius",
      "args": [
        "proto_hub",
        "anchor_left_lower",
        "anchor_right_lower",
        null
      ],
      "phase": "frame",
      "energy": 36.0,
      "cumulative_energy": 284.8
    },
    {
      "action": [
        "construct_frame_with_radius",
        "proto_hub",
        "anchor_right_lower",
        "right_stick_top",
        null
      ],
      "name": "construct_frame_with_radius",
      "args": [
        "proto_hub",
        "anchor_right_lower",
        "right_stick_top",
        null
      ],
      "phase": "frame",
      "energy": 32.0,
      "cumulative_energy": 316.8
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_left_upper"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_left_upper"
      ],
      "phase": "radii",
      "energy": 8.5,
      "cumulative_energy": 325.4
    },
    {
      "action": [
        "walk",
        "anchor_left_upper",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_left_upper",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 8.5,
      "cumulative_energy": 333.9
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_bottom_right"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_bottom_right"
      ],
      "phase": "radii",
      "energy": 13.0,
      "cumulative_energy": 346.9
    },
    {
      "action": [
        "walk",
        "anchor_bottom_right",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_bottom_right",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 13.0,
      "cumulative_energy": 359.9
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_right_upper"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_right_upper"
      ],
      "phase": "radii",
      "energy": 8.5,
      "cumulative_energy": 368.4
    },
    {
      "action": [
        "walk",
        "anchor_right_upper",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_right_upper",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 8.5,
      "cumulative_energy": 377.0
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_left_lower"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_left_lower"
      ],
      "phase": "radii",
      "energy": 10.0,
      "cumulative_energy": 387.0
    },
    {
      "action": [
        "walk",
        "anchor_left_lower",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_left_lower",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 10.0,
      "cumulative_energy": 397.0
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_right_lower"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_right_lower"
      ],
      "phase": "radii",
      "energy": 10.0,
      "cumulative_energy": 407.0
    },
    {
      "action": [
        "walk",
        "anchor_right_lower",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_right_lower",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 10.0,
      "cumulative_energy": 417.0
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_bottom_left"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_bottom_left"
      ],
      "phase": "radii",
      "energy": 13.0,
      "cumulative_energy": 430.0
    },
    {
      "action": [
        "walk",
        "anchor_bottom_left",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_bottom_left",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 13.0,
      "cumulative_energy": 443.0
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_bottom_center"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_bottom_center"
      ],
      "phase": "radii",
      "energy": 12.0,
      "cumulative_energy": 455.0
    },
    {
      "action": [
        "walk",
        "anchor_bottom_center",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_bottom_center",
        "proto_hub"
      ],
      "phase": "radii",
      "energy": 12.0,
      "cumulative_energy": 467.0
    },
    {
      "action": [
        "build_spiral_segment",
        "proto_hub",
        "anchor_top_center",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "proto_hub",
        "anchor_top_center",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 6.0,
      "cumulative_energy": 473.0
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_top_center",
        "anchor_right_upper",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_top_center",
        "anchor_right_upper",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 8.5,
      "cumulative_energy": 481.5
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_right_upper",
        "anchor_right_lower",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_right_upper",
        "anchor_right_lower",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 9.0,
      "cumulative_energy": 490.5
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_right_lower",
        "anchor_bottom_right",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_right_lower",
        "anchor_bottom_right",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 6.7,
      "cumulative_energy": 497.2
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_right",
        "anchor_bottom_center",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_right",
        "anchor_bottom_center",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 5.0,
      "cumulative_energy": 502.2
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_center",
        "anchor_bottom_left",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_center",
        "anchor_bottom_left",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 5.0,
      "cumulative_energy": 507.2
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_left",
        "anchor_left_lower",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_left",
        "anchor_left_lower",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 6.7,
      "cumulative_energy": 513.9
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_left_lower",
        "anchor_left_upper",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_left_lower",
        "anchor_left_upper",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 9.0,
      "cumulative_energy": 522.9
    },
    {
      "action": [
        "walk",
        "anchor_left_upper",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_left_upper",
        "proto_hub"
      ],
      "phase": "auxiliary_spiral",
      "energy": 8.5,
      "cumulative_energy": 531.5
    },
    {
      "action": [
        "mark_auxiliary_spiral_done"
      ],
      "name": "mark_auxiliary_spiral_done",
      "args": [],
      "phase": "auxiliary_spiral",
      "energy": 0.0,
      "cumulative_energy": 531.5
    },
    {
      "action": [
        "build_spiral_segment",
        "proto_hub",
        "anchor_left_upper",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "proto_hub",
        "anchor_left_upper",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 8.5,
      "cumulative_energy": 540.0
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_left_upper",
        "anchor_left_lower"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_left_upper",
        "anchor_left_lower"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 540.0
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_left_upper",
        "anchor_left_lower",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_left_upper",
        "anchor_left_lower",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 9.0,
      "cumulative_energy": 549.0
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_left_lower",
        "anchor_bottom_left"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_left_lower",
        "anchor_bottom_left"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 549.0
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_left_lower",
        "anchor_bottom_left",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_left_lower",
        "anchor_bottom_left",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 6.7,
      "cumulative_energy": 555.7
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_bottom_left",
        "anchor_bottom_center"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_bottom_left",
        "anchor_bottom_center"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 555.7
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_left",
        "anchor_bottom_center",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_left",
        "anchor_bottom_center",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 5.0,
      "cumulative_energy": 560.7
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_bottom_center",
        "anchor_bottom_right"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_bottom_center",
        "anchor_bottom_right"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 560.7
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_center",
        "anchor_bottom_right",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_center",
        "anchor_bottom_right",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 5.0,
      "cumulative_energy": 565.7
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_bottom_right",
        "anchor_right_lower"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_bottom_right",
        "anchor_right_lower"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 565.7
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_right",
        "anchor_right_lower",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_right",
        "anchor_right_lower",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 6.7,
      "cumulative_energy": 572.4
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_right_lower",
        "anchor_right_upper"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_right_lower",
        "anchor_right_upper"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 572.4
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_right_lower",
        "anchor_right_upper",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_right_lower",
        "anchor_right_upper",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 9.0,
      "cumulative_energy": 581.4
    },
    {
      "action": [
        "remove_auxiliary_spiral_segment",
        "anchor_right_upper",
        "anchor_top_center"
      ],
      "name": "remove_auxiliary_spiral_segment",
      "args": [
        "anchor_right_upper",
        "anchor_top_center"
      ],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 581.4
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_right_upper",
        "anchor_top_center",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_right_upper",
        "anchor_top_center",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 8.5,
      "cumulative_energy": 590.0
    },
    {
      "action": [
        "walk",
        "anchor_top_center",
        "proto_hub"
      ],
      "name": "walk",
      "args": [
        "anchor_top_center",
        "proto_hub"
      ],
      "phase": "capture_spiral",
      "energy": 6.0,
      "cumulative_energy": 596.0
    },
    {
      "action": [
        "mark_capture_spiral_done"
      ],
      "name": "mark_capture_spiral_done",
      "args": [],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 596.0
    },
    {
      "action": [
        "mark_web_complete"
      ],
      "name": "mark_web_complete",
      "args": [],
      "phase": "complete",
      "energy": 0.0,
      "cumulative_energy": 596.0
    }
  ],
  "total_steps": 73,
  "total_energy": 596.0
};
