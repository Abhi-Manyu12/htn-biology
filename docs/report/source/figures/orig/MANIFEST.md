# figures/orig — the three figures of the Checkpoint 2 report, extracted unchanged

All produced by `report/scripts/orig/extract_figures.py <W>` from `report_src/BTP_Checkpoint2.pdf`
(the compiled original, 2026-09-18). No data were re-plotted; these are the original figures.

| Stem | Source | What it shows | n |
|---|---|---|---|
| `fig1_web_ui` (.png) | raster image embedded on p. 8 of the PDF (`report_src/images/p08_img1.png`, 1919x956) | Final state of the interactive plan visualiser after the 70-action default-configuration plan (original Figure 1) | 1 plan |
| `fig2_cumulative_energy` (.pdf vector, .png 300 dpi) | pgfplots drawing on p. 9, cropped losslessly with pymupdf (clip x 81.5–530.0, y 261.0–441.5 pt; content outside the clip redacted) | Cumulative locomotory energy vs action index, shaded by phase (original Figure 2) | 1 plan, 70 actions |
| `fig3_success_vs_removal` (.png) | raster image embedded on p. 12 (`report_src/images/p12_img1.png`, 960x648) | HTN vs baseline success rate vs anchor-removal probability (original Figure 3; a dark-theme chart screenshot) | 1,000 trials/condition (as stated in the original caption) |

Original placement widths (for reproducing the look): Fig. 1 0.72\linewidth, Fig. 2 0.958\linewidth, Fig. 3 0.85\linewidth.
