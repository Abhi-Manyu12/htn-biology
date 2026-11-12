"""Create the E1 resource figure from saved trial JSON, without rerunning trials."""
import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"mulder-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from spider_web_mulder.validation import wilson


def load_trials(path):
    """Read full run JSON or its curated CSV representation."""
    if path.suffix.lower() != ".csv":
        return json.loads(path.read_text())
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row["success"] not in ("True", "False"):
            raise ValueError("CSV success value must be True or False")
        row["success"] = row["success"] == "True"
        row["seed"] = int(row["seed"])
        row["config"] = json.loads(row["config"])
        row["margin_cm"] = int(row["margin_cm"]) if row["margin_cm"] else None
    return rows


def make_resource_figure(rows, output):
    margins = (-1, 0, 20, 60)
    sizes = (8, 16, 32)
    scenarios = (("damage_single", "Single damage"), ("damage_multi", "Multiple damage"))
    capable = ("state_rules", "fresh_htn", "retained_htn")
    fig, axes = plt.subplots(2, 3, figsize=(9.5, 6), sharex=True, sharey=True, layout="constrained")
    for row_index, (scenario, label) in enumerate(scenarios):
        for column, sectors in enumerate(sizes):
            ax = axes[row_index, column]
            successes, denominators, lower, upper = [], [], [], []
            for margin in margins:
                groups = {controller: [r for r in rows if r["suite"] == "resource" and
                          r["scenario"] == scenario and r["config"]["sectors"] == sectors and
                          r["margin_cm"] == margin and r["controller"] == controller]
                          for controller in capable}
                # Plot the three as one curve only when their outcomes agree seed by seed.
                outcomes = [tuple(sorted((r["seed"], r["success"]) for r in groups[c])) for c in capable]
                if not outcomes[0] or any(o != outcomes[0] for o in outcomes[1:]):
                    raise ValueError("Capable-controller outcomes do not agree; plot them separately")
                n = len(outcomes[0])
                count = sum(success for _, success in outcomes[0])
                low, high = wilson(count, n)
                successes.append(count/n)
                denominators.append(n)
                lower.append(max(0., count/n-low))
                upper.append(max(0., high-count/n))
            ax.errorbar(np.arange(len(margins)), successes, yerr=[lower, upper],
                        color="#0072B2", marker="o", linestyle="none", capsize=3, linewidth=1.5)
            for index, (rate, n) in enumerate(zip(successes, denominators)):
                ax.annotate(f"{round(rate*n)}/{n}", (index, rate), xytext=(0, 7),
                            textcoords="offset points", ha="center", fontsize=8)
            if row_index == 0:
                ax.set_title(f"{sectors} sectors")
            if column == 0:
                ax.set_ylabel(f"{label}\nCompletion fraction")
            if row_index == 1:
                ax.set_xlabel("Stock margin (cm)")
            ax.set_xticks(range(len(margins)), ["−1", "0", "+20", "+60"])
            ax.set_ylim(-.12, 1.25)
    for ext in ("png", "svg"):
        fig.savefig(output.with_suffix("."+ext), dpi=200)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--output-stem", type=Path, required=True)
    args = parser.parse_args(argv)
    make_resource_figure(load_trials(args.trials), args.output_stem)


if __name__ == "__main__":
    main()
