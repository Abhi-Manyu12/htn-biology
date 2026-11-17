# Experiment demos

Open [experiments.html](experiments.html) directly in a browser, or follow
**Experiment tabs & video demos** from any existing construction viewer.
No server, build step or new application dependencies are required.

1. Select a study, scenario and recorded configuration.
2. Choose the controllers to compare, or disable **Side by side**.
3. Play, pause, seek or jump to a recorded disturbance. Both sides share the
   same simulated-time clock; a finished run holds its final state.
4. Choose a playback speed, then **Export video**. Recording starts at the
   beginning. Keep the tab visible; **Stop & save** creates a partial clip.
   Use **Download video** when recording finishes. The browser selects a
   supported WebM or MP4 format. Study, settings, seed and speed are burned
   into the clip. Unsupported browsers still support replay.

## What is shown

| Tab | Saved replay coverage | Full study |
| --- | --- | ---: |
| Construction | Original, updated HTN and A* plan viewers | Historical plan demonstrations, not matched experiments |
| Moving supports | 4 matched configured-size cases; local repair/full policies; normal movement/synthetic miss; 12 seed-0 runs | 2,160 trials |
| Recovery | 14 matched cases; 4 sectors, depth 0, stationary/10 cm motion, every failure scenario; 56 seed-0 runs | 2,240 trials |
| E1 observed state | All 24 first-seed cases; 96 seed-0 runs | 1,920 trials |
| E1 expanded | 17 cases; 68 seed-20 runs, covering scaling at 4–32 sectors, 8-sector resource margins, 32-sector transfer, and 30 cm/0.10 Hz movement | 5,280 trials |

The 232 replay runs are a curated subset, not additional experiment evidence.
Across-seed summaries use all recorded seeds in exactly the selected stratum;
physical means condition on success and planning means include failures.
An empty successful stratum is unavailable, not a zero physical cost.

The sector model renders capture effects as schematic links; their drawn
length is not the model's fixed silk cost. Mulder silk is deposited chord
length, while E1/recovery silk is actor expenditure. Donor silk is separate.
Paths interpolate recorded endpoints; support shear follows the original
affine transform. Construction geometry and disturbances are imposed model
assumptions, not animal observations. Ties and negative results are retained.
Decision/planning wall timings include the original controller/adapter work;
they are separate from simulated construction time.

The Construction tab embeds the existing viewers without replacing their
renderers or generators. Their animation is unloaded when leaving that tab.
Video capture applies to the four trace-based study tabs.

## Regenerating replay assets

```sh
python3 -m visualization.export_experiments
```

This reads the original saved directories under `mulder_results/` (see
`STUDIES` in `export_experiments.py`) and writes `experiments/*.js` plus
`manifest.json`. It does **not** run models or modify historical artifacts.
Missing source ledgers fail explicitly. The committed bundles work without
the ignored raw output directories. Full research evidence remains under
`docs/research/evidence/`.

The exporter reuses the sector domain's nodes/scaffold and checks recorded
final state, elapsed time and travel against trial outcomes. The manifest
records input SHA-256 hashes and output bundle hashes. Labels use text nodes;
generated script data escapes markup and JavaScript separator characters.

Video export reuses the browser's
[Canvas captureStream](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream)
and [MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
instead of adding a codec dependency. Captures remain local, and streams and
download URLs are released after use.

## Verification

```sh
python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests visualization/tests
```

Optional browser checks use an installed Chrome and locally available
`aiohttp` tooling; they are separate from application dependencies:

```sh
python3 -m visualization.browser_check --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --screenshot /private/tmp/spider-demo-desktop.png
python3 -m visualization.browser_check --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --width 390 --screenshot /private/tmp/spider-demo-mobile.png
```

The browser harness tests the real page in a temporary copy, using a fresh
Chrome profile and a loopback-only debugging connection. It checks tabs,
case matching, damage timestamps, failed/unexposed outcomes, donor labeling,
recording failure/unsupported states and a real downloaded video decoded at
the expected dimensions. It does not modify the normal browser profile.
