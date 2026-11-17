# Figures: `sim` (2D cable simulation of the planned web)

All numbers come from runs of the simulation page `W/simulation/orb_web_sim.html`, performed for this report (17 Nov 2026,
repo commit `61d18d8`). The page embeds the HTN plan from `visualization/plan_data_updated.js` and the rig and stochastic settings
from `spider_web_htn_updated/config.yaml`, `spider_web_mulder/config.yaml` and `spider_web_htn_updated/perturbations.py`.
It is built by `report/scripts/sim/build_sim_page.py` from `report/scripts/sim/page_src/{template.html,core.js,ui.js}`.

Pipeline (regenerates everything):

    .venv/bin/python report/scripts/sim/build_sim_page.py      # page
    .venv/bin/python report/scripts/sim/collect_sim_data.py    # runs evals/*.js inside the page -> work/sim/data/*.json
    .venv/bin/python report/scripts/sim/fig_sim_*.py           # matplotlib figures
    sh report/scripts/sim/capture_sim_page.sh                  # page captures

Default parameters (all material values illustrative; there are no silk-mechanics numbers in the repo): sag exaggeration
X = 2000, g = 9.81 m/s^2, segment length 0.5 cm, mu / EA / slack per type as in Table `tab:sim-params` of `sim.tex`,
drag c_n = 6e-5 N s m^-2, spider 30 mg. "n" below counts simulated threads or simulation runs. Runs are deterministic, so
there are no replicates and no error bars.

| Stem | Script | Data (all in `W/work/sim/data/`, produced by `collect_sim_data.py` with the named eval) | What it shows | n |
|---|---|---|---|---|
| `sim_web_states` | `fig_sim_web_states.py` | `web_states.json` (`evals/web_states.js`) | Finished web, same scale: (a) g = 0, identical to the straight-line plan; (b) gravity, X = 2000; (c) gravity + steady 4 m/s wind towards +x. Static equilibria. | 66 threads per panel; 3 runs |
| `sim_construction_phases` | `fig_sim_phases.py` | `phases.json` (`evals/phases.js`) | Quasi-static sequential construction (each of the 105 actions executed on the settled web left by the previous one). Snapshots after the last action of each macro phase (steps 10, 25, 36, 52, 74, 104). | 1 run, 105 settles (all converged, worst rel. residual 9.4e-7) |
| `sim_validation` | `fig_sim_validation.py` | `validation.json` (`evals/validation.js`) | Single 16 cm span, radius material (mu 0.10 ug/cm, EA 60 mN), X = 2000. (a) shape at 3 % slack, N = 16, against the elastic catenary, the rigid catenary a cosh(x/a) and the parabola; (b) deviations from the elastic catenary; (c) max error against N (slack 0, 1, 5 %); (d) error against slack at N = 40. | 21 runs (c) + 13 runs (d) |
| `sim_sag_sweeps` | `fig_sim_sweeps.py` | `sweeps.json` (`evals/sweeps.js`) | Finished web, spider load off, static equilibria. (a) max node displacement and max thread sag against steady wind speed (towards +x and towards -y); (b) sag against slack applied to every thread type (negative = pretension), with max tension; (c) sag against weight factor X g / 9.81, from an X sweep and a g sweep. | 20 + 11 + 12 + 7 runs |
| `sim_tension` | `fig_sim_sweeps.py` | `web_states.json` (`gravity_nospider`) | (a) per-thread maximum tension by thread type (bar = median); (b) web coloured by segment tension (log scale). | 66 threads (2 bridge, 4 proto-radius, 4 frame, 8 radius, 20 auxiliary, 28 capture); 944 segments |
| `sim_moving_supports` | `fig_sim_supports.py` | `supports.json` (`evals/supports.js`) | Affine shear of `spider_web_mulder/model.py` on the 16 x 18 cm rig, A = 10 cm, f = 0.05 Hz: (a-d) web at phases 0, 90, 180, 270 deg; (e) max tension over two periods for (10 cm, 0.05 Hz), (5 cm, 0.05 Hz), (10 cm, 0.1 Hz); (f) bottom-bar shift, hub displacement, max sag, max strain. | 3 runs, 161 samples each |
| `sim_anchor_removal` | `fig_sim_anchors.py` | `anchors.json` (`evals/anchors.js`) | Anchors removed with the same draws as `stochastic.select_available_anchors` (Python MT19937, sorted candidates) for seeds 7107 (config seed) and 4 at p = 0.1, 0.2, 0.35, 0.5. Threads ending on a removed anchor or on a waypoint of its radius are not built; there is no replanning. | 8 runs |
| `sim_detach` | `fig_sim_anchors.py` | `anchors.json` | Structural failure after construction (cf. `perturbations.py`): the bottom-left (a) or right-lower (b) anchor lets go; new static equilibrium, original web in light grey. | 2 runs |
| `sim_page` | `capture_sim_page.sh` | the page itself (`?run=0&wind=3&dir=0&gust=0.3&seed=7&t=6`) | Full-window capture of the tool at 1400 x 900 CSS px with the controls visible: finished web after 6 s of gusty wind. The PDF wraps the PNG. | 1 |
| `sim_page_validation` | `capture_sim_page.sh` | the page itself (`?run=0&panel=validate&vslack=3&vN=16`) | The page's validation panel: single span against the analytic curves, with residuals and numerical readouts. The PDF wraps the PNG. | 1 |
