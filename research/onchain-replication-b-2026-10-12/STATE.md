# Branch B state

2026-10-13 — CP1 nearly complete, CP2 running. No fit has been run; the sealed
2024 holdout is untouched.

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

Next safe action: independent whole-branch review → fix pass → launch the fit grid
(full × 5 seeds × 2 tasks; LSTM/GRU/HLSTM × 5 × 2; SVM × 2; diagnostics
constant_graph and label_permutation × 5) → `cli report` (CP3, CP4).
