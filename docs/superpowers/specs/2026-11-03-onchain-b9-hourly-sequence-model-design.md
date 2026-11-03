# Branch B9 — small neural sequence models on the hourly on-chain tables

Status: **DRAFT 2026-11-03, awaiting approval.** Branch
`research/onchain-replication-b-2026-10-12`. No new chain data: B9 reads the hourly series
B4 and B6 produced and the B7 tables (price, range, option-market columns and targets).
Decisions still open are listed in §12.

## 1. Motivation and prior

Every hourly study (B4–B8) used ridge regression and gradient-boosted trees on hand-built
features. The only learned representation in the programme was M2's motif-GAT →
attention-LSTM on weekly graphs, which ended at chance for a diagnosed pooling reason
(near-constant graph vector), not because sequence models were tested on informative
inputs. Whether a learned temporal representation of the hourly series finds information
that hand engineering missed is therefore untested.

The prior is low. B7 showed that more flexible trees (early-stopped, 15 leaves) lose to
B4's small fixed trees, and that re-engineering the same series at five time scales adds
nothing. The coherent signal is small: B4's flow block improves next-6-hour volatility (V6)
and largest-5-minute-move (M6) forecasts by 1.4–3.3 % of squared error in 2022–26 against a
baseline with option-market information, and nothing in 2020–24 once 1-minute ranges are
known. B9 is designed to close the model-class question for the thesis with one bounded
study, not to start a neural search: architectures, sizes and training rules are fixed
here, and no further neural variant follows B9 regardless of the outcome.

## 2. Questions

- **Q1 representation.** Does a sequence model fed the raw hourly flow series beat B4's
  fixed trees fed B4's hand-built flow columns, on the same rows (N1 vs T1)?
- **Q2 flows inside the network.** Do the flow sequences add to a network that already
  sees price, range and option-market sequences (N1 vs N0)? In track A′ this asks whether
  a learned representation recovers flow information that the trees did not find.
- **Q3 complementarity.** Does an equal-weight average of the network and the trees beat
  the trees alone (E1 vs T1)?
- **Q4 B6 series.** Do B6's 39 structure and entity series help a network (N2 vs N1),
  where they hurt both linear models and trees in B6 and B7?

Reference row: N0 vs T0 (network vs trees with price information only), reported so that
any Q1 result can be read against how the network handles the baseline alone.

## 3. Inputs (all produced by B4, B6 and B7)

| Input | Source |
|---|---|
| 15 B4 raw hourly series (`eth_*`, `stable_*`, `act_*`) | `research_artifacts/onchain-b4/features/hourly_raw.parquet` |
| 39 B6 raw hourly series (`gs_*`, `tk_*`, `cl_*`, `is_*`) | `research_artifacts/onchain-b6/features/hourly_raw.parquet` |
| B7 feature table (`h0_`, `px_`, `rg_`, `mk_`, B4 transforms) and targets | `research_artifacts/onchain-b7/features/{table,targets}.parquet` |
| ETH hourly bars | B4 `market/hourly_dev.json` + `sealed/hourly_sealed.json` |

**Data location.** None of these files is on the devbox (77 MB of on-chain artifacts
there). They are on the laptop or the Storage Box. The hourly tables are small (≈ 86k rows;
a few hundred MB in total), so they can be copied as they are; no chain pass is needed.

## 4. Sequence inputs

Per hour t, channels are standardised with the mean and standard deviation of the training
part of each fold (never the test part), then clipped to ±10; missing values are set to 0
and flagged by one missing-indicator channel.

| Block | Channels per hour |
|---|---|
| P (price) | hourly log return, absolute log return, `rg_range1` (log max/min of the hour's 1-minute closes), log hourly quote volume |
| K (calendar) | sin/cos of hour-of-day, sin/cos of day-of-week |
| O (options, track B only) | `mk_dvol`, `mk_iv` |
| F (flows, B4) | the 15 B4 raw series, log1p |
| G (B6) | the 39 B6 raw series, log1p |
| M | missing indicator |

The window for decision hour h holds hours h − L + 1 … h, with L = 168. The window aggregates
(the `h0_`, `px_`, `rg_` and `mk_` columns of B7's X0 at hour h) enter the head as a static
vector, so every network sees at least the information of the B7 baseline.

## 5. Models

### 5.1 Networks (two architectures = the two families)

- **GRU:** one layer, hidden size 32, final state.
- **TCN:** causal dilated 1-D convolutions, 4 residual blocks of 32 channels, kernel 3,
  dilations 1, 2, 4, 8 (two convolutions per block, receptive field 61 hours), followed by
  mean and last-step pooling over the window (both concatenated).

Head for both: concat(sequence summary, static X0 vector) → linear 32 → GELU → dropout 0.1 →
linear 3. **Multi-task:** one network outputs V6, V24 and M6 (log scale, each standardised by
its training mean and standard deviation); the loss is the mean squared error over the
targets present in a row (masked), equal weights.

Sets:

| Network | Sequence blocks | Static |
|---|---|---|
| N0 | P, K, M (+ O in track B) | X0 |
| N1 | N0 + F | X0 |
| N2 | N1 + G | X0 |

### 5.2 Training rule (fixed; no tuning on test years)

AdamW, learning rate 1e-3, weight decay 1e-4, batch 256, gradient-norm clip 1.0, at most
40 epochs. Early stopping: the last 10 % of the fold's training hours (time-ordered,
separated from the earlier part by a 24-hour gap) is the validation tail; patience 5 on the
masked validation loss; the best epoch count E is kept (minimum 3). The network is then
refitted on the whole training window for E epochs, as B7 refits trees_es on the whole
window with the chosen iteration count. **Seeds:** 5 per fit; the prediction is the mean of
the 5 seeds; the per-seed spread is reported. `torch.set_num_threads` fixed; deterministic
algorithms on.

### 5.3 Reference models

- **T0, T1:** B4's fixed trees (B7 `trees_fixed`: 100 iterations, 7 leaves, min leaf 30,
  learning rate 0.05, l2 1.0) on B7's X0 and X1, refitted on B9's row set.
- **R1:** B7 ridge on X1, refitted on B9's row set (reported, not compared).
- **E1:** ½ (N1 + T1), equal weights fixed here; no weight is fitted.

## 6. Targets, tracks and folds

Targets V6, V24 and M6 as in B7 (V: log realised volatility of hourly log returns over the
next 6 / 24 h; M6: log of the largest absolute 5-minute log return within the next 6 h).
Tail targets J6/J24 and M24 are dropped (null in B7; rare-class training is a separate
problem for a network).

Tracks and folds are B7's: A′ 2019-04-01 → 2024-12-31 (test years 2020–2024, group
2020–24); B 2021-04-01 → 2026-10-12 (test years 2022–2026, groups 2022–24 and 2025–26);
walk-forward, expanding, purge = horizon, min_train 2,000 rows. The training window of every
fold starts L hours after the track start so that every window is complete.

**Row set.** Per track and target: B7's rows (complete X0/X1 features, target present)
intersected with rows whose 168-hour window has at most 12 missing hours. Every model in a
comparison (networks, trees, ridge, constant) is evaluated on exactly this set, and the
trees are refitted on it rather than taken from B7.

## 7. Blocking probes (run before any comparison is read)

- **P0 alignment and capability (one fold: track B, test year 2022, GRU, one seed).**
  (a) An oracle channel equal to the V6 target at hour t (it contains hours t+1 … t+6) is
  added to N0. Pass if the oracle network cuts validation V6 error by ≥ 50 % — the network
  can read the last position, and the window ends where it should. (b) The same channel
  lagged by 6 hours (known at t) must not improve V6 by more than 2 % — anything larger
  means the window or the target is misaligned. Fail → fix and rerun P0; no comparison
  is built before P0 passes. Neither oracle fit enters any result.
- **P1 training sanity.** N0 must beat the constant forecast (training mean) for V6 in
  ≥ 3 of 5 test years of each track. If not, the networks are reported as failed for that
  track; the comparison rows are still built and labelled so.
- **P2 compute calibration.** One full fold (5 seeds, refit included) is timed for N1 GRU
  and TCN on the devbox. If the projected total exceeds 36 hours, the pre-declared fallback
  is applied in this order until it fits: (i) 3 seeds instead of 5; (ii) L = 72;
  (iii) hidden size and channels 16. The fallback used is recorded in `STATE.md` before
  any comparison is read.

## 8. Comparisons and criteria

Per track, target (V6, V24, M6) and architecture (GRU, TCN):

| ID | Comparison | Question |
|---|---|---|
| C1 | N1 vs T1 | Q1 |
| C2 | N1 vs N0 | Q2 |
| C3 | E1 vs T1 | Q3 |
| C4 | N2 vs N1 | Q4 |
| C5 | N0 vs T0 | reference |

5 × 3 × 2 × 2 = 60 comparisons (track B reported per group).

Statistics and criteria are B7's: mean per-row loss difference, 95 % circular block-bootstrap
interval (block 168 rows, 2,000 draws, seed 20261103), per-year differences, loss of a
constant forecast for every row. Positive reading: A′ — upper end < 0 and better in ≥ 3 of
5 years; B — upper end < 0 in 2022–24 and mean difference < 0 in 2025–26 (sign-only,
labelled). A result counts as a finding only if it holds for **both architectures** (and,
for Q2/Q3, in the target where B7 found the flow signal, V6 or M6). About 3 interval passes
are expected by chance among the 60 rows.

Pre-declared readings:

- C1 and C3 fail in both tracks → a learned temporal representation of the hourly series
  adds nothing to hand-built features; the hourly line stays closed with the model-class
  question answered.
- C3 passes, C1 does not → the network carries some information complementary to the trees;
  reported as a small forecasting effect, no trading claim.
- C2 passes in track A′ → the network recovers flow information that B7's trees did not
  find before 2025; this would be the only new result and would need the confirmation in §9.

## 9. Confirmation (optional, decided before the run — §12)

Both sealed windows are spent, so B9 is exploratory. A confirmatory window can only come from
hours after 2026-10-12. B4's V6 flow effect (about −0.008 in squared log-vol error, interval
width ≈ ±0.003 over three years) would need roughly 12 months of new hours for a comparable
interval; a 6-month window (≈ 4,300 hours) is underpowered for effects of 1–3 %. If a finding
in the sense of §8 appears, the frozen configuration (architecture, set, seed rule, training
rule) is registered with a window 2026-10-13 → 2027-10-12, evaluated once.

## 10. Compute

Per track: 5 folds × 3 network sets × 2 architectures × 5 seeds × (early-stopped fit + refit)
≈ 300 network fits; 600 for both tracks, multi-task over the three targets. Training data
≤ 48k windows × 168 hours × ≤ 65 channels; the hourly arrays (≈ 86k × 65 float32 ≈ 22 MB)
stay in memory and windows are sliced per batch, so memory stays under 2 GB per process.
Rough estimate 1–3 minutes per fit on 2 CPU threads → about 10–30 hours with two processes on
the 4-vCPU devbox; P2 replaces this estimate with a measurement. Trees and ridge refits:
minutes. Run as systemd user units with a memory cap, resumable per (track, set,
architecture, fold, seed) unit file, as B6–B8.

## 11. Layout

```
tradingagents/research/onchain_b9/
  config.py, windows.py (channel assembly, causal standardisation, window slicing),
  nets.py (GRU, TCN, head), train.py (early stopping, refit, seeds), forecast9.py
  (runner, reference refits, comparisons, criteria, report), cli.py (inputs, probes,
  forecast, report)
tests/research/onchain_b9/
research/onchain-b9-2026-11-03/   # CHARTER.md, PLAN.md, config/b9.json, STATE.md, RESULTS.md
research_artifacts/onchain-b9/     # gitignored
```

Testing: window for row h ends at h and never includes h+1; standardisation statistics come
from training rows only; masked multi-task loss on toy rows; early stopping and refit epoch
count on a toy series; seed averaging; GRU and TCN causality (output at t unchanged when
inputs after t change); the row set is identical across all models in a comparison; the
runner, criteria and report on toy predictions. A fresh whole-branch review before P0.

Checkpoints: B9-CP0 inputs restored and verified (row counts match B7-CP1); B9-CP1 probes
P0–P2; B9-CP2 comparisons; B9-CP3 `RESULTS.md` and closure.

## 12. Open decisions

1. **Where to run.** Devbox (needs the hourly tables copied from the laptop or the Storage
   Box; 4 vCPU, 8 GB) or the laptop (data already there, 12 cores, 16 GB). Recommended:
   devbox, after copying the B4/B6/B7 feature files.
2. **Confirmation.** Register the 12-month forward window now (§9) or decide only if a
   finding appears. Recommended: decide only if a finding appears; nothing is spent either
   way, since the window lies in the future.
3. **Scope.** Keep Q4 (N2, B6 series), or drop it to save about a third of the compute.
   Recommended: keep — B6's series failed in linear models and trees partly through
   extrapolation, which a standardised, clipped network input handles differently.
