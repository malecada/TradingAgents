# Fixed Ethereum direction comparison — verified negative screen

The fixed temporal-motif summaries did not demonstrate incremental prediction
value beyond ordinary graph activity under the registered retrospective protocol.
The run is complete and independently verified; its statistical screen is
negative. This is a result for the fixed summaries and learner, not a replication
or rejection of the paper's full neural architecture.

## Results

All 366 daily 2024 predictions, 12 monthly folds, 36 fits and 77 lifecycle cells are
complete; no cell is unavailable. The 1,088-row decision panel has one common
training warmup exclusion (January 9, 2022), caused by the unavailable January 1
graph day in three trailing activity features. The first fold has 720 included
training rows. All arms use identical admitted rows and purged training dates.
The source inputs contain 1,128 market rows and 1,094 admitted graph rows.

| Model | Accuracy | Balanced accuracy | Brier score | Log loss |
|---|---:|---:|---:|---:|
| M0: Market | 53.01% | 53.25% | 0.249682 | 0.692672 |
| M1: Market + ordinary activity | 55.19% | 55.61% | 0.250320 | 0.694183 |
| M2: Market + activity + motifs | 50.27% | 50.56% | 0.253969 | 0.701571 |
| majority: Training-majority baseline | 44.81% | 45.16% | 0.551913 | 19.062564 |

Lower Brier and log loss are better. The majority baseline emits degenerate
probabilities and is retained transparently as an accuracy reference. The
ordinary-activity model has higher descriptive accuracy than the market model,
but slightly worse log loss; accuracy alone is not the frozen decision criterion.

Primary M2−M1 mean log loss is **+0.007387**, with paired 95% interval
**[-0.009289, +0.019717]**. The mean favors M1,
while the interval includes zero; this does not establish that motifs are
systematically harmful. Motifs improve monthly log loss in **6 of 12 months**.
The frozen rule required the entire interval below zero and at least 8 negative
months. Both conditions fail. Secondary M1−M0 mean log loss is
+0.001511, interval [-0.010793, +0.017100].
Intervals use the single registered 14-day moving-block bootstrap, 2,000 resamples,
seed 42. No post-result threshold, fit, feature or alternate seed was introduced.

| Month | Matched test days | M2−M1 mean log loss |
|---|---:|---:|
| 2024-01 | 31 | -0.000338 |
| 2024-02 | 29 | -0.009883 |
| 2024-03 | 31 | +0.021284 |
| 2024-04 | 30 | +0.048817 |
| 2024-05 | 31 | -0.001472 |
| 2024-06 | 30 | +0.010038 |
| 2024-07 | 31 | -0.000696 |
| 2024-08 | 31 | -0.002186 |
| 2024-09 | 30 | -0.004484 |
| 2024-10 | 31 | +0.008607 |
| 2024-11 | 30 | +0.013987 |
| 2024-12 | 31 | +0.005109 |

## Verification and resources

Execution source is `baa8129ed58096a202f5b909777eacc736c8631c`, committed and
remotely verified before claim. Experiment eth-matched-direction-20260924
consumes cumulative 17/17, retaining all 16 predecessors including four failures.
The independent checker separately decoded retained source inputs, reconstructed
features/clocks/labels/common masks and purged membership, replayed saved models,
and recomputed metrics, paired inference and the screening rule. All 36 immutable
fit checkpoints match the final fit archive. It performed no independent refit.
Saved-model consistency does not independently prove historical training provenance.

Compute guard elapsed 478.23 seconds, peak 206,622,720 bytes; review guard elapsed
5.54 seconds, peak 199,421,952 bytes. Both exited zero with verified cleanup and
zero memory-high/max/OOM events. Named offline engineering verification passed
2,746 tests and 97 subtests before outcomes. Six cleanup warnings concerned an
existing pytest temporary directory. They did not fail a test or resource guard.

## Interpretation and closure

The original large graph reconstruction was computationally feasible under its
bounded run, but the current comparison provides no empirical basis under its
predeclared screen for advancing these summaries into a neural experiment.
This conclusion is specific to ETHUSDT, the 2024 test year, the declared features,
LightGBM settings and retrospective input clocks. It does not reproduce the
paper's architecture, exact split or any reported high-accuracy claim.

The 2022–2024 sample was previously inspected and remains exploratory, not fresh
confirmation. Historical graph publication and midnight tradability remain
unverified; feature clocks are explicit protocol assumptions. No PnL, financial
validation, strategy deployment or causal economic claim is made. A neural or
other changed experiment requires a separate decision and registration.

All source inputs, prior attempts, 36 fit checkpoints, eight outputs, independent
report and guard receipts are retained. The evidence manifest records their
hashes. Original graph raw/hash stores remain intact; off-device full raw-data
backup remains unverified. The remote-backup receipt, written after push verification, records
compact-evidence closure. The monitor is retired after
reviewed preservation closure; no automatic rerun or follow-up remains.
