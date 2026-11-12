"""Preserve curated recovery results without rerunning or pooling studies."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new snapshot path")
    rows = json.loads((args.source/"trials.json").read_text())
    comparisons = json.loads((args.source/"paired.json").read_text())
    groups = defaultdict(list)
    for row in rows:
        groups[(row["scenario"],row["backend"])].append(row)
    pooled = []
    for (scenario,backend),group in groups.items():
        pooled.append(dict(scenario=scenario,backend=backend,trials=len(group),successes=sum(r["success"] for r in group),
                           events_fired=sum(r["event_fired"] for r in group),
                           mean_method_calls=statistics.mean(r["method_calls"] for r in group),
                           mean_repairs=statistics.mean(r["repairs"] for r in group),
                           mean_stale_preconditions=statistics.mean(r["stale_preconditions"] for r in group)))
    primary = [r for r in comparisons if r["sectors"]==8 and r["depth"]==2 and r["amplitude_cm"]==10]
    result = dict(snapshot_date="2026-10-20",recovery_model_version=1,total_trials=len(rows),
                  pooled_descriptive_outcomes=pooled,primary_paired_comparisons=primary,
                  unnecessary_repeats_total=sum(r["unnecessary_repeats"] for r in rows),
                  maximum_silk_conservation_error=max(abs(r["silk_used_cm"]+r["silk_remaining_cm"]+r["silk_lost_cm"]-r["config"]["silk_cm"]) for r in rows),
                  original_provenance=json.loads((args.source/"provenance.json").read_text()),
                  input_directory=str(args.source),
                  input_sha256={name:hashlib.sha256((args.source/name).read_bytes()).hexdigest()
                                for name in ("trials.json","paired.json","summary.json","provenance.json")},
                  snapshot_generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope="Authored sector-construction recovery benchmark; not the Mulder v3 geometry/biological study.")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(f"Curated {len(rows)} recovery trials into {args.output}")


if __name__ == "__main__":
    main()
