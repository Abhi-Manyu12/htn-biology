"""Import biological observations and calibrate ONLY against rigid controls.

No reference values are invented. Fits are conditional on the rectangular
envelope and prescribed-count model; moving observations remain held out.
"""

import csv
from dataclasses import replace
import math
import statistics

from .experiment import run_trial


REFERENCE_COLUMNS = ["spider_id", "trial_id", "condition", "elapsed_s", "travel_cm",
                     "radials_time_pct", "auxiliary_time_pct", "capture_time_pct",
                     "radials_travel_pct", "auxiliary_travel_pct", "capture_travel_pct",
                     "web_area_cm2", "capture_spiral_area_cm2", "eccentricity",
                     "mean_capture_spiral_count", "mean_mesh_space_cm", "radial_count_measured"]


def load_reference(path):
    with open(path, newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"spider_id", "trial_id", "condition"}.issubset(reader.fieldnames or []):
            raise ValueError("Reference CSV requires spider_id, trial_id and condition")
        result = []
        identifiers = set()
        for source in reader:
            row = {k: source.get(k, "").strip() for k in REFERENCE_COLUMNS[:3]}
            if row["condition"] not in ("rigid", "moving") or not row["spider_id"] or not row["trial_id"]:
                raise ValueError("Every row needs an ID and condition rigid or moving")
            identity = (row["spider_id"], row["trial_id"])
            if identity in identifiers:
                raise ValueError("Duplicate biological observation")
            identifiers.add(identity)
            for key in REFERENCE_COLUMNS[3:]:
                raw = source.get(key, "") or ""
                value = float(raw) if raw.strip() else None
                if value is not None and (not math.isfinite(value) or value < 0):
                    raise ValueError(f"Invalid reference measurement: {key}")
                row[key] = value
            result.append(row)
    if not result:
        raise ValueError("Reference file contains no observations")
    return result


def individual_means(rows, condition, metric):
    groups = {}
    for row in rows:
        if row["condition"] == condition and row.get(metric) is not None:
            groups.setdefault(row["spider_id"], []).append(row[metric])
    return {identity: statistics.mean(values) for identity, values in groups.items()}


def reference_effects(rows):
    import numpy as np
    rng = np.random.default_rng(20261020)
    effects = {}
    for key in REFERENCE_COLUMNS[3:]:
        rigid = individual_means(rows, "rigid", key)
        moving = individual_means(rows, "moving", key)
        paired = sorted(set(rigid) & set(moving))
        differences = [moving[i]-rigid[i] for i in paired]
        ci = [float(x) for x in np.quantile(rng.choice(differences,size=(2000,len(differences)),replace=True).mean(axis=1),[.025,.975])] if differences else None
        effects[key] = dict(paired_spiders=len(paired),ci95_difference=ci,
                            rigid_mean=statistics.mean(rigid[i] for i in paired) if paired else None,
                            moving_mean=statistics.mean(moving[i] for i in paired) if paired else None,
                            mean_paired_difference=statistics.mean(differences) if paired else None)
    return effects


def calibrate_rigid(settings, reference):
    def control_mean(key):
        by_spider = individual_means(reference, "rigid", key)
        return statistics.mean(by_spider.values()) if by_spider else None
    area, eccentricity = control_mean("web_area_cm2"), control_mean("eccentricity")
    fitted = {}
    if area is not None:
        ratio = 1-eccentricity if eccentricity is not None else 1.0
        if ratio <= 0:
            raise ValueError("Rectangular tall-web fit requires eccentricity < 1")
        height = math.sqrt(area/ratio)
        width = area/height
        fitted.update(web_width_fraction=width/settings.width_cm, web_height_fraction=height/settings.height_cm)
    count = control_mean("radial_count_measured")
    if count is not None:
        fitted["radial_count"] = max(4, round(count))
    capture = control_mean("mean_capture_spiral_count")
    if capture is not None:
        # The continuous spiral can cross one cardinal ray an extra time.
        fitted["capture_turns"] = max(1, round(capture-0.5))
    calibrated = replace(settings, **fitted, execution_mode="tracking", amplitude_cm=0, method_policy="direct")
    static, _ = run_trial(calibrated, "local")
    duration = control_mean("elapsed_s")
    if duration is not None:
        dwell = static["total_actions"]*calibrated.attachment_time_s
        if duration <= dwell:
            raise ValueError("Observed duration is shorter than configured total contact dwell")
        fitted["speed_cm_s"] = static["travel_cm"]/(duration-dwell)
        calibrated = replace(calibrated, speed_cm_s=fitted["speed_cm_s"])
    check, _ = run_trial(calibrated, "local",record_path=True)
    def prediction(key):
        if key == "travel_cm":
            return check["sampled_travel_10s_cm"]
        if key.endswith("_travel_pct"):
            return check.get("sampled_"+key)
        return check.get(key)
    residuals = {key: dict(observed=control_mean(key), predicted=prediction(key))
                 for key in REFERENCE_COLUMNS[3:] if control_mean(key) is not None}
    return replace(settings, **fitted), dict(fitted_parameters=fitted, control_residuals=residuals,
                                           source="rigid observations only, equal weight per spider",
                                           assumptions="rectangular envelope, tall-web eccentricity branch; contact dwell held fixed",
                                           moving_observations_used_for_fitting=False)
