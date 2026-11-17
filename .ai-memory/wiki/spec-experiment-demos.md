# Experiment demo and comparison UI

- Purpose: demonstrate saved simulated spider construction and compare measured controller performance in the existing local visualization.
- Confirmed 2026-11-17: user requests simulated videos from experiment traces, experiment tabs and relevant side-by-side comparisons.

## Acceptance criteria

- AC-1 WHEN an experiment tab is selected THE SYSTEM SHALL show that study's saved trace cases, settings and evidence context.
- AC-2 WHEN a case is selected THE SYSTEM SHALL replay its recorded construction, damage/transfer and failure states with play, pause, seek, restart and speed controls.
- AC-3 WHEN controllers are compared THE SYSTEM SHALL select runs from the same study, configuration, scenario and seed and advance both with one simulated-time clock.
- AC-4 THE SYSTEM SHALL show recorded completion, simulated duration, travel, silk and planning wall time separately, and distinguish representative runs from aggregate study results.
- AC-5 WHEN recording is supported THE SYSTEM SHALL export a labeled video of the selected single or paired replay; IF unsupported or recording fails THEN THE SYSTEM SHALL explain the limitation and restore playback controls.
- AC-6 THE SYSTEM SHALL identify these as model simulations, preserve ties/negative outcomes and link source provenance; missing traces SHALL be explicit and SHALL NOT be invented or rerun as historical evidence.
- AC-7 THE SYSTEM SHALL preserve existing construction pages and entry commands, provide keyboard-operable tabs/controls and a usable narrow-screen layout.
- AC-8 WHEN replay assets are rebuilt THE SYSTEM SHALL derive them from saved runs with source hashes and verify trace endpoints against recorded outcomes without changing original experiments.

## Scope

- Local static UI, existing construction viewers, saved moving-support/recovery/E1/expanded E1 runs, native browser video capture; no new dependencies.
- No new scientific experiments, changes to models, biological footage, hosting or publication guarantees.

## Evolution

- 2026-11-17 — created after user confirmed simulation replays.
