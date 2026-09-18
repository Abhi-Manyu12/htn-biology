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
        "lay_thread",
        "right_stick_top",
        "anchor_right_upper",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "right_stick_top",
        "anchor_right_upper",
        "dragline"
      ],
      "phase": "exploration",
      "energy": 3.0,
      "cumulative_energy": 3.0
    },
    {
      "action": [
        "swing_tarzan",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "swing_tarzan",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "exploration",
      "energy": 3.0,
      "cumulative_energy": 6.0
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 6.0
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 6.0
    },
    {
      "action": [
        "drop_down",
        "right_stick_top",
        "anchor_right_upper"
      ],
      "name": "drop_down",
      "args": [
        "right_stick_top",
        "anchor_right_upper"
      ],
      "phase": "proto_hub",
      "energy": 3.0,
      "cumulative_energy": 9.0
    },
    {
      "action": [
        "swing_tarzan",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "swing_tarzan",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 3.0,
      "cumulative_energy": 12.0
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 12.0
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 12.0
    },
    {
      "action": [
        "mark_proto_hub",
        "right_stick_top"
      ],
      "name": "mark_proto_hub",
      "args": [
        "right_stick_top"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 12.0
    },
    {
      "action": [
        "lay_radius",
        "right_stick_top",
        "anchor_right_upper"
      ],
      "name": "lay_radius",
      "args": [
        "right_stick_top",
        "anchor_right_upper"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 15.0
    },
    {
      "action": [
        "lay_frame_thread",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "lay_frame_thread",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "frame",
      "energy": 3.0,
      "cumulative_energy": 18.0
    },
    {
      "action": [
        "lay_radius",
        "right_stick_top",
        "anchor_right_upper"
      ],
      "name": "lay_radius",
      "args": [
        "right_stick_top",
        "anchor_right_upper"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 21.0
    },
    {
      "action": [
        "walk",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "walk",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 24.0
    },
    {
      "action": [
        "lay_radius",
        "right_stick_top",
        "anchor_right_upper"
      ],
      "name": "lay_radius",
      "args": [
        "right_stick_top",
        "anchor_right_upper"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 27.0
    },
    {
      "action": [
        "walk",
        "anchor_right_upper",
        "right_stick_top"
      ],
      "name": "walk",
      "args": [
        "anchor_right_upper",
        "right_stick_top"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 30.0
    },
    {
      "action": [
        "lay_radius",
        "right_stick_top",
        "anchor_right_upper"
      ],
      "name": "lay_radius",
      "args": [
        "right_stick_top",
        "anchor_right_upper"
      ],
      "phase": "radii",
      "energy": 3.0,
      "cumulative_energy": 33.0
    },
    {
      "action": [
        "lay_frame_thread",
        "anchor_right_upper",
        "anchor_top_center"
      ],
      "name": "lay_frame_thread",
      "args": [
        "anchor_right_upper",
        "anchor_top_center"
      ],
      "phase": "frame",
      "energy": 8.5,
      "cumulative_energy": 41.5
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_top_center",
        "left_stick_top",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_top_center",
        "left_stick_top",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 8.0,
      "cumulative_energy": 49.5
    },
    {
      "action": [
        "build_spiral_segment",
        "left_stick_top",
        "anchor_left_upper",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "left_stick_top",
        "anchor_left_upper",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 3.0,
      "cumulative_energy": 52.5
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_left_upper",
        "left_stick_mid",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_left_upper",
        "left_stick_mid",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 3.0,
      "cumulative_energy": 55.5
    },
    {
      "action": [
        "build_spiral_segment",
        "left_stick_mid",
        "crossbar_left",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "left_stick_mid",
        "crossbar_left",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 3.0,
      "cumulative_energy": 58.5
    },
    {
      "action": [
        "build_spiral_segment",
        "crossbar_left",
        "anchor_left_lower",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "crossbar_left",
        "anchor_left_lower",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 3.0,
      "cumulative_energy": 61.5
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_left_lower",
        "left_stick_bottom",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_left_lower",
        "left_stick_bottom",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 6.0,
      "cumulative_energy": 67.5
    },
    {
      "action": [
        "build_spiral_segment",
        "left_stick_bottom",
        "anchor_bottom_left",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "left_stick_bottom",
        "anchor_bottom_left",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 3.0,
      "cumulative_energy": 70.5
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
      "cumulative_energy": 75.5
    },
    {
      "action": [
        "mark_web_complete"
      ],
      "name": "mark_web_complete",
      "args": [],
      "phase": "complete",
      "energy": 0.0,
      "cumulative_energy": 75.5
    }
  ],
  "total_steps": 26,
  "total_energy": 75.5
};
