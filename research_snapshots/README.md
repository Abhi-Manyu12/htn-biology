# Research result backup

The 2026-10-27 snapshot preserves all 3,046 generated files in `mulder_results/`,
including reports, traces, trial tables and provenance. Source code, tests and
manuscript documents are committed separately in their ordinary locations.
The manifest records archive and individual-file SHA-256 hashes. Every archived
file was verified against its original before committing.

To restore from the repository root into a checkout without existing results:

```sh
tar -xzf research_snapshots/mulder_results_2026-10-27.tar.gz
```

The archive contains the `mulder_results/` directory. Extracting over existing
results replaces matching paths, so use a fresh checkout or preserve newer
local outputs first. Generated working outputs remain ignored by Git; this is
an explicit backup snapshot, not an automatic record of future runs.
