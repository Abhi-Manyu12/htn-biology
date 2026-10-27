"""Curate a small manuscript evidence record from the version-3 saved study.

python3 docs/research/probes/snapshot_mulder_evidence.py \
    --source mulder_results/paper_validation_v3_report \
    --output docs/research/evidence/mulder_v3_summary.json

No simulation is rerun and no estimates are recomputed from rounded prose.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new evidence snapshot path")
    comparisons = json.loads((args.source/"comparisons.json").read_text())
    trials = json.loads((args.source/"trials.json").read_text())
    provenance = json.loads((args.source/"provenance.json").read_text())
    if provenance["model_version"] != 3:
        parser.error("This snapshot schema describes the version-3 study")
    selected = [r for r in comparisons if
                r["amplitude_cm"]==10 and r["frequency_hz"]==0.05 and
                ((r["profile"] in ("endpoint","tracking") and r["metric"] in
                  ("completion","elapsed_s","travel_cm","sampled_travel_10s_cm")) or
                 (r["profile"] not in ("endpoint","tracking") and r["metric"] in ("completion","elapsed_s")))]
    ablations = []
    for alternative,baseline in (("flat_tracking","tracking"),("phase_wait","tracking_slow")):
        matched = {r["seed"]:r for r in trials if r["profile"]==baseline and r["controller"]=="local"
                   and r["amplitude_cm"]==10 and r["frequency_hz"]==0.05}
        differences = [r["elapsed_s"]-matched[r["seed"]]["elapsed_s"] for r in trials
                       if r["profile"]==alternative and r["controller"]=="local" and
                       r["amplitude_cm"]==10 and r["frequency_hz"]==0.05 and r["success"] and
                       r["seed"] in matched and matched[r["seed"]]["success"]]
        ablations.append(dict(alternative=alternative,baseline=baseline,controller="local",
                              paired_n=len(differences),mean_duration_difference_s=sum(differences)/len(differences),
                              maximum_absolute_duration_difference_s=max(abs(x) for x in differences)))
    result = dict(snapshot_date="2026-10-20",model_version=3,total_trials=len(trials),
                  input_directory=str(args.source),
                  input_sha256={name:hashlib.sha256((args.source/name).read_bytes()).hexdigest()
                                for name in ("trials.json","comparisons.json","profiles.json","provenance.json","calibration.json")},
                  original_provenance=provenance,
                  profiles=json.loads((args.source/"profiles.json").read_text()),
                  calibration=json.loads((args.source/"calibration.json").read_text()),
                  selected_comparisons=selected,
                  matched_ablation_checks=ablations,
                  snapshot_generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  historical_search_strategy="Not explicitly pinned or recorded by the original runner; see the separate current-environment audit.",
                  uncertainty_unit="Initial forcing phase, not biological individual",
                  qualifications=["Ideal geometry/true corrected distance partly imposed by target generation",
                                  "Continuous outcomes conditional on both paired runs succeeding",
                                  "No raw biological observations supplied for calibration",
                                  "No IPyHOP or retained-tree recovery implemented"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(f"Curated {len(selected)} comparisons from {len(trials)} trials into {args.output}")


if __name__ == "__main__":
    main()
