# Branch B state

2026-10-13 — CP1 in progress. Protocol frozen 2026-10-12. Package implemented
through training (tasks 1–13 of the plan; evaluation/report pending). Density
calibration complete: **K = 5,000** frozen in `config/graph.json`
(`CALIBRATION.md` §1; the paper's density lies below the grid — recorded as a
fidelity qualification, rule applied as written). `fidelity-b.json` written.
Full 156-week graph build launched (`research_artifacts/onchain-replication-b/logs/build-graphs.jsonl`).

Measured so far: one real day (1.15M rows) reads and admits in 1.0 s, 377 MB RSS;
one week aggregates in ~18 s at 2.9 GB RSS.

Next safe action: finish evaluation/report module; when graphs exist, run the
N_max / GAT compute calibration (`CALIBRATION.md` §2), freeze `n_max`, then
dictionaries and MCM for the five seeds (CP2).
