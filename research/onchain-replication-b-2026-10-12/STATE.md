# Branch B state

2026-10-13 08:30 — CP2 running, fit grid launched. Price-only baseline cells are
being fitted; full-model cells start as each seed's MCM completes.

Done:
- Protocol frozen 2026-10-12 (`PROTOCOL.md`, `config/*.json`, `gates.json`).
- Package and tests (63 passing at `6afb0a14d`).
- K = 5,000 frozen by label-free density calibration (`CALIBRATION.md` §1).
- n_max = 32 and 2 torch threads frozen from measured throughput (`CALIBRATION.md` §2).
- Five dictionaries (seeds 11/23/37/51/71) built from training weeks only, ~25 s
  each, ≤ 1.1 GB RSS. Motif sizes 1–32 nodes, 0–474 edges
  (`research_artifacts/onchain-replication-b/logs/dictionary-seed*.jsonl`).

Running (systemd user units):
- `onchain-b-graphs`: remaining 2024 weeks (112/156 built at 08:12). One crash
  on 2024-01-01 fixed in `771f50e5b` (untracked prototype-day captures).
- `onchain-b-mcm{11,23,37}a`: MCM on the built weeks; measured 7,010 cells/s,
  22.8 s per week (160,000 cells), ~1.0 GB RSS.
- `onchain-b-mcm-all`: waits for the above, then completes MCM for all five
  seeds over 156 weeks, three in parallel.

Measured comparison with Branch A for CP2: Branch A pilot39 exclusive numeric
rate 59.31 cells/s on whole-graph neighborhoods; Branch B 7,010 cells/s on
paper-scale neighborhoods (different workloads; not a like-for-like speedup).

Independent whole-branch review (fresh reviewer, range 312460acd..6afb0a14d):
0 Critical; science path verified (batched solver ≡ reference to 5.6e-17 at real
sizes; no leakage). Fix pass `4470ffbfb` before any fit: GAT self entry once,
smoke runs isolated in `fits-smoke/`, atomic fit outputs, circular bootstrap,
report computes every registered gate and lists excluded cells, dictionary-week
leakage test. 69 tests pass.

Fit grid (`onchain-b-fits`, 3 cells in parallel, 52 cells,
`research_artifacts/onchain-replication-b/scratch/fit_jobs.txt`):
LSTM/GRU/HLSTM × 5 seeds × 2 tasks; SVM × 2 tasks (deterministic, seed 11);
full × 5 seeds × 2 tasks; full classification diagnostics constant_graph and
label_permutation × 5 seeds. Every cell runs once; status in
`logs/fit_status.log`. Measured: price-only LSTM 100 epochs in ~20 s.

CP3 (2026-10-13 10:13): first genuine joint MCM-MLP → GAT → attention-LSTM fit
completed — `fits/classification/full/seed11`, 100 epochs in 3,364 s (≈ 34 s per
epoch with three cells in parallel), peak RSS 1.14 GB, exit 0. Final training
cross-entropy 0.6913 (ln 2 = 0.6931): the model barely fits even the training
days. No test metric has been read; the 2024 evaluation is reported only by
`cli report` after all 52 cells finish.

Next safe action: when all 52 cells have exit=0, run `cli report` → RESULT.md
(CP4), record CP3 timing from the first full-model `fit.jsonl`, update the
audit artifact's checkpoint section.
