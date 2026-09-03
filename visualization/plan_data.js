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
      "cumulative_energy": 110.7
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
      "cumulative_energy": 119.3
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
      "cumulative_energy": 119.3
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "anchor_right_upper",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "anchor_right_upper",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 8.5,
      "cumulative_energy": 127.8
    },
    {
      "action": [
        "reel_up",
        "anchor_right_upper",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "anchor_right_upper",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 8.5,
      "cumulative_energy": 136.4
    },
    {
      "action": [
        "insert_radius",
        "anchor_right_upper",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_right_upper",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 136.4
    },
    {
      "action": [
        "lay_thread",
        "proto_hub",
        "anchor_left_lower",
        "dragline"
      ],
      "name": "lay_thread",
      "args": [
        "proto_hub",
        "anchor_left_lower",
        "dragline"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 146.4
    },
    {
      "action": [
        "reel_up",
        "anchor_left_lower",
        "proto_hub"
      ],
      "name": "reel_up",
      "args": [
        "anchor_left_lower",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 156.4
    },
    {
      "action": [
        "insert_radius",
        "anchor_left_lower",
        "proto_hub"
      ],
      "name": "insert_radius",
      "args": [
        "anchor_left_lower",
        "proto_hub"
      ],
      "phase": "proto_hub",
      "energy": 0.0,
      "cumulative_energy": 156.4
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
      "cumulative_energy": 166.4
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
      "cumulative_energy": 176.4
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
      "cumulative_energy": 176.4
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
      "cumulative_energy": 176.4
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
      "phase": "proto_hub",
      "energy": 10.0,
      "cumulative_energy": 186.4
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
      "phase": "frame",
      "energy": 16.0,
      "cumulative_energy": 202.4
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
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 212.4
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
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 222.4
    },
    {
      "action": [
        "lay_frame_thread",
        "left_stick_top",
        "anchor_left_lower"
      ],
      "name": "lay_frame_thread",
      "args": [
        "left_stick_top",
        "anchor_left_lower"
      ],
      "phase": "frame",
      "energy": 12.0,
      "cumulative_energy": 234.4
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
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 244.4
    },
    {
      "action": [
        "walk",
        "proto_hub",
        "anchor_left_lower"
      ],
      "name": "walk",
      "args": [
        "proto_hub",
        "anchor_left_lower"
      ],
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 254.4
    },
    {
      "action": [
        "lay_frame_thread",
        "anchor_left_lower",
        "anchor_right_lower"
      ],
      "name": "lay_frame_thread",
      "args": [
        "anchor_left_lower",
        "anchor_right_lower"
      ],
      "phase": "frame",
      "energy": 16.0,
      "cumulative_energy": 270.4
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
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 280.4
    },
    {
      "action": [
        "walk",
        "proto_hub",
        "anchor_right_lower"
      ],
      "name": "walk",
      "args": [
        "proto_hub",
        "anchor_right_lower"
      ],
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 290.4
    },
    {
      "action": [
        "lay_frame_thread",
        "anchor_right_lower",
        "right_stick_top"
      ],
      "name": "lay_frame_thread",
      "args": [
        "anchor_right_lower",
        "right_stick_top"
      ],
      "phase": "frame",
      "energy": 12.0,
      "cumulative_energy": 302.4
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
      "phase": "frame",
      "energy": 10.0,
      "cumulative_energy": 312.4
    },
    {
      "action": [
        "lay_radius",
        "proto_hub",
        "anchor_top_center"
      ],
      "name": "lay_radius",
      "args": [
        "proto_hub",
        "anchor_top_center"
      ],
      "phase": "radii",
      "energy": 6.0,
      "cumulative_energy": 318.4
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
      "phase": "radii",
      "energy": 6.0,
      "cumulative_energy": 324.4
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
      "cumulative_energy": 332.9
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
      "cumulative_energy": 341.4
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
      "cumulative_energy": 351.4
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
      "cumulative_energy": 361.4
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
      "cumulative_energy": 374.4
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
      "cumulative_energy": 387.4
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
      "cumulative_energy": 399.4
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
      "cumulative_energy": 411.4
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
      "cumulative_energy": 424.4
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
      "cumulative_energy": 437.4
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
      "cumulative_energy": 447.4
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
      "cumulative_energy": 457.4
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
      "cumulative_energy": 466.0
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
      "cumulative_energy": 474.5
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
      "cumulative_energy": 480.5
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
      "cumulative_energy": 489.1
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
      "cumulative_energy": 498.1
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_right_lower",
        "anchor_bottom_center",
        "auxiliary_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_right_lower",
        "anchor_bottom_center",
        "auxiliary_spiral"
      ],
      "phase": "auxiliary_spiral",
      "energy": 10.0,
      "cumulative_energy": 508.1
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
      "cumulative_energy": 513.1
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
      "cumulative_energy": 519.8
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
      "cumulative_energy": 528.8
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
      "cumulative_energy": 537.3
    },
    {
      "action": [
        "mark_auxiliary_spiral_done"
      ],
      "name": "mark_auxiliary_spiral_done",
      "args": [],
      "phase": "auxiliary_spiral",
      "energy": 0.0,
      "cumulative_energy": 537.3
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
      "cumulative_energy": 545.9
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
      "cumulative_energy": 554.9
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
      "cumulative_energy": 561.6
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
      "cumulative_energy": 566.6
    },
    {
      "action": [
        "build_spiral_segment",
        "anchor_bottom_center",
        "anchor_right_lower",
        "capture_spiral"
      ],
      "name": "build_spiral_segment",
      "args": [
        "anchor_bottom_center",
        "anchor_right_lower",
        "capture_spiral"
      ],
      "phase": "capture_spiral",
      "energy": 10.0,
      "cumulative_energy": 576.6
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
      "cumulative_energy": 585.6
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
      "cumulative_energy": 594.1
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
      "cumulative_energy": 600.1
    },
    {
      "action": [
        "mark_capture_spiral_done"
      ],
      "name": "mark_capture_spiral_done",
      "args": [],
      "phase": "capture_spiral",
      "energy": 0.0,
      "cumulative_energy": 600.1
    },
    {
      "action": [
        "mark_web_complete"
      ],
      "name": "mark_web_complete",
      "args": [],
      "phase": "complete",
      "energy": 0.0,
      "cumulative_energy": 600.1
    }
  ],
  "total_steps": 70,
  "total_energy": 600.1
};
