"""Independent integrity checks of the repository's research record (record domain).

Read-only on the repo. Re-hashes committed files and compares them with the hashes the
repository itself records, then writes a JSON summary used in the report text.

Checks:
  1. research_snapshots manifest: archive SHA-256 and every per-file SHA-256 against the
     committed mulder_results/ tree (3,046 files).
  2. Curated evidence JSONs: input_sha256 / artifact_sha256 against mulder_results/.
  3. Vendored IPyHOP: per-file SHA-256 against third_party/IPyHOP/UPSTREAM.json.
  4. docs/manuscript/figures/provenance.json: curated figure copies and their sources.
  5. perturbation_trials.csv against the SHA-256 quoted in WORK_LOG.md (2026-11-12 entry).

Usage: python verify_record.py <repo> <out.json>
"""
import hashlib
import json
import os
import sys

repo, out = sys.argv[1], sys.argv[2]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rp(*p):
    return os.path.join(repo, *p)


res = {}

# 1. snapshot manifest
m = json.load(open(rp("research_snapshots", "mulder_results_2026-10-27.manifest.json")))
arch = rp(m["archive"]) if not os.path.isabs(m["archive"]) else m["archive"]
if not os.path.exists(arch):
    arch = rp("research_snapshots", os.path.basename(m["archive"]))
ok = bad = missing = 0
bytes_total = 0
for rel, info in m["files"].items():
    p = rp(rel)
    if not os.path.exists(p):
        missing += 1
        continue
    bytes_total += os.path.getsize(p)
    if sha(p) == info["sha256"]:
        ok += 1
    else:
        bad += 1
res["snapshot"] = {
    "archive_bytes": os.path.getsize(arch),
    "archive_sha256_match": sha(arch) == m["archive_sha256"],
    "manifest_files": len(m["files"]),
    "committed_match": ok,
    "committed_mismatch": bad,
    "committed_missing": missing,
    "committed_bytes": bytes_total,
}

# 2. evidence JSON input hashes
ev = {}
for name, key, dirkey in [
    ("mulder_v3_summary.json", "input_sha256", "input_directory"),
    ("recovery_v1_summary.json", "input_sha256", "input_directory"),
    ("mulder_reentrant_v4_summary.json", "artifact_sha256", "bulk_output"),
]:
    d = json.load(open(rp("docs", "research", "evidence", name)))
    base = d[dirkey]
    r = {"match": 0, "mismatch": [], "missing": []}
    for fn, h in d[key].items():
        p = rp(base, fn)
        if not os.path.exists(p):
            r["missing"].append(fn)
        elif sha(p) == h:
            r["match"] += 1
        else:
            r["mismatch"].append(fn)
    r["directory"] = base
    ev[name] = r
res["evidence"] = ev

# 3. vendored IPyHOP
u = json.load(open(rp("third_party", "IPyHOP", "UPSTREAM.json")))
r = {"revision": u["revision"], "modifications": u["modifications"], "match": 0, "mismatch": []}
for fn, h in u["sha256"].items():
    if sha(rp("third_party", "IPyHOP", fn)) == h:
        r["match"] += 1
    else:
        r["mismatch"].append(fn)
r["files"] = len(u["sha256"])
res["ipyhop"] = r

# 4. figure provenance
prov = json.load(open(rp("docs", "manuscript", "figures", "provenance.json")))
r = {"entries": len(prov), "copy_match": 0, "source_match": 0, "notes": []}
for fn, info in prov.items():
    if sha(rp("docs", "manuscript", "figures", fn)) == info["sha256"]:
        r["copy_match"] += 1
    else:
        r["notes"].append("copy differs: " + fn)
    src = rp(info["source"])
    if os.path.exists(src) and sha(src) == info["sha256"]:
        r["source_match"] += 1
    else:
        r["notes"].append("source differs/missing: " + info["source"])
res["figure_provenance"] = r

# 5. perturbation_trials.csv
quoted = "c9d30b18118b930c1bf3b8a9ad3c86364193e3ec6d4fb1afc3a4fb22cdc9e2f8"
res["perturbation_csv_sha256_match"] = sha(rp("perturbation_trials.csv")) == quoted

json.dump(res, open(out, "w"), indent=2)
print(json.dumps(res, indent=2))
