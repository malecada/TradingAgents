# Matched isolated source-check observation

The same synthetic reserved archive owner-read fixture passed under both source
snapshots. Only admission.py differs; manifests retain source commit/export and
overlay hashes. Runs were sequential, unprofiled, with the same pinned Python and
pytest command, and a240second timeout. Logs and /usr/bin/time output are retained.

| Observation | Pytest seconds | Total wall seconds | Maximum RSS KiB |
|---|---:|---:|---:|
| baseline04 |56.57|57.81|710376|
| candidate05 |24.98|26.33|712008|

Observed wall ratio2.196, reduction54.454%. This is one observation each on a
host with uncontrolled background load, not a randomized statistical benchmark
or a model-training speedup. Both successful fresh fixtures mock the OS guard
and use filesystem transport; neither is a financial/actual-network experiment.
The unchanged independent historical verifier continues running its own checks.
No admission checks were disabled or cached across calls. The earlier cProfile
118.12seconds are excluded from this unprofiled timing comparison.
