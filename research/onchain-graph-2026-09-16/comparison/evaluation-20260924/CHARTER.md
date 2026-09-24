# Fixed incremental Ethereum direction screen

The user authorized the matched M0/M1/M2 comparison and its completion on
September 23–24, 2026. This charter operationalizes the unchanged September 16
[protocol](../PROTOCOL.md) and [configuration](../config.json). Neither scientific
rules nor prior results are replaced. Execution requires this charter and the
exact gate, input/source/runtime bindings, full offline verification and
independent release approval committed and remotely verified before outcomes.

## Question and cumulative history

The single exploratory question is whether the declared temporal-motif
summaries improve next-day ETHUSDT spot direction prediction beyond the same
market information and ordinary activity controls. It is not a replication of
the paper's neural architecture, a fresh confirmation test or a trading study.
M0 has seven market features; M1 adds six activity features; M2 adds seven motif
features. No extra feature, alternative lag, model, seed, target or baseline is
introduced. The existing training-majority baseline remains descriptive.

Experiment `eth-matched-direction-20260924` has graph-source predecessor
`eth-full-history-feature-panel-resume2-20260922`, enforced as graph_parent.
Lifecycle parent is null because the helper restricts parent links to the same
fitted family; this first comparison retains the complete upstream history. The additive allowance is one
claim with 16 prior lineage claims and a cumulative cap of 17. These counts
include source and engineering attempts, not 17 independent financial
hypotheses. The explicit amendment and independent review preserve all old
limits, failed/incomplete attempts and receipts; another family name cannot
reset them. A failed comparison consumes this allowance and cannot be replayed.

The sixteen graph claims are hash-bound in history.json, including the failed
initial motif attempt and pilot, reboot-interrupted full panel and oomd-stopped
first continuation.
Earlier ETH forecasting/factor/risk-policy studies exposed the historical
sample, as recorded in SOURCE_INVENTORY.md and the cited dated charters. Both
graph and spot dataset identities retain their original canonical names. This
run is development/exploratory; inspected 2022–2024 data is not fresh validation.

## Input and clock admission

The reviewed graph source is fixed at
`87b6ac39d12a4f9a2ac1832f34f68647c52c53c8`. Its completed panel, terminal,
passing full-panel independent report, exact successful review guard and full
preservation/backup records are bound before claim. There are exactly 1,096
ordered source dates 2022-01-01 through 2024-12-31 and 1,094 admitted graph
dates. The only graph exclusions are the two registered endpoints. Independent
review verified all 1,221,389,903 full transaction identities with zero duplicates.
Neither graph computation nor its final review is rerun for this comparison.

All 38 retained Binance spot monthly archives, December 2021 through January
2025, are included with their original monthly metadata and stored zstd
ZIP/checksum bytes. Committed inputs bind stored and raw sizes/hashes, original
capture review and complete spot manifest. No new network requests or futures
substitution are permitted. All archived dates stay in the capture denominator,
but only 2021-12-01 through 2025-01-01 prices/volumes are decoded. The 2025
timestamp unit is microseconds; earlier archives use milliseconds. OHLC must be
finite, positive and internally ordered, volumes finite and nonnegative, and
the selected market field is quote volume. A malformed source fails admission;
it cannot be repaired by imputation or replacement acquisition.

Decision D is UTC midnight; label one means open(D+1) exceeds open(D), otherwise
zero, including ties. Prices at D or D+1 are labels only. Features use D−2 or
older. Graph availability is assumed source day +2 days; market availability
is assumed bar end +5 minutes. Later supplied clocks take precedence. Each
trailing feature uses the maximum clock of every required input. Missing or
late inputs exclude the same decision across all arms. The unavailable first
graph day makes January 9, 2022 a warmup exclusion; January 10 is the first
potentially complete training row. This disclosed consequence does not change
the registered decision calendar or omit a test day.

Original historical graph availability remains null and unverified. Derived
clocks explicitly carry the protocol-assumption qualification. The rewritten
archive vintage and retrospective price series do not establish historical
publication or achievable midnight fills.

## Fitting, metrics and the one decision

The dense decision calendar is January 9, 2022 through December 31, 2024.
Twelve monthly 2024 test folds share the same admitted rows and expanding
training sample. Training label_end must not exceed fold start minus one day.
No within-month fitting, tuning, early stopping, dictionary learning or feature
selection is permitted. LightGBM 4.6.0 uses exactly 100 trees, max depth3,
7 leaves, learning rate0.05, minimum child samples30, L2 penalty1, seed42,
two threads and deterministic column-wise fitting, as in the unchanged config.
The budget is 36 production fits. Saved Booster strings enable independent
prediction replay without additional fitting or selection.

Retain accuracy, balanced accuracy, Brier score and log loss monthly and pooled,
all dated labels/probabilities, common-row exclusions, fold counts and partial
fits. The primary contrast is M2−M1 mean log loss; M1−M0 is secondary. All 366
2024 predictions are required for primary inference. Any gap makes inference
and screening unavailable while preserving available-row descriptive results.

The paired 95% percentile interval uses 2,000 non-circular overlapping moving
block bootstrap draws, block length14 and seed42. Sample blocks to length n,
truncate the last block, and use identical indices for all contrasts. A neural
follow-up is supported only if the primary interval is entirely below zero and
at least eight of twelve monthly M2−M1 differences are negative. No alternative
metric or post-outcome threshold replaces that criterion. Such support would
justify a separate decision, not automatically authorize a neural experiment.

This single exploratory screen has no PnL, execution, fee, funding, portfolio,
exposure-reduction or adoption claim. Uncertainty is conditional on the fitted
predictions and one historical year, without full retraining uncertainty or
cross-regime confirmation. No accounting convention diagnostic is relevant to
this classification-only experiment; none is claimed as passed.

## Denominators, failure and independent checks

The 77 lifecycle cells are 38 spot months, one graph-panel admission, 36
fold/arm cells, one primary-inference cell and one screening cell. Every cell
is retained as complete or unavailable with a reason. A failed fold leaves all
three arm cells unavailable; any already fitted arm remains in the partial-fit
archive. A top-level failure preserves the claimed identity and partial files
without retry. Input tables and the decision panel are published before fits.
The eight output basenames and exact JSON interfaces are in CONTRACT.md.
Each completed fit is also atomically checkpointed under the lifecycle run's
fit-checkpoints directory before prediction or the next fit. Its immutable
receipt binds the experiment, source, claim hash, sequence and full saved fit.
These supplemental receipts are independently reconciled to fits.json and
preserved even after interruption. A failed checkpoint aborts later fits. An
inference-only exception keeps completed predictions, folds and descriptive
scores and makes only inference/screening unavailable; no retry is permitted.

Independent checking first verifies the structural run and source/input hashes.
It separately decodes source market values, maps graph counts and reconstructs
the label, features, clocks, common mask and train/test purge. It verifies saved
model feature order and predictions by loading Booster strings, then recomputes
classification metrics, paired inference, missing-cell handling and screening.
Replaying a saved model proves internal consistency; it does not independently
prove which historical data trained it. Recorded training membership, source
bindings and deterministic runner checks support that qualified audit. No model
is refitted by the independent checker. Failed/partial comparison verification
is distinct from a complete result with available primary inference.

Synthetic adversarial tests cover wrong timestamps, future clocks, row/target
changes, source or archive hash mismatch, graph conservation, missing dates,
failed folds, purged membership, model replay and inference mutations. They
establish implementation behavior only. The named offline target and independent
release review must pass before observed prices/labels are opened.

## Resources and preservation

Execution and independent review each use one exclusive transient user service
with 6 GiB memory.high=max, 512 MiB swap, two CPUs, 9 GiB startup MemAvailable,
3 GiB running host reserve and a 15-second guard lease. Both partitions retain
20 GiB free. There is no elapsed-time kill. The previously reviewed guard is
hash-bound; the exact local .venv interpreter and existing runtime receipt
checker enforce the locked complete environment before claim and review; no global oomd configuration or production service is changed.
The coordinator checkout is used directly from a fixed committed source; no
large Data clone is created. New serialized output payload, including fit checkpoints and the eight
JSON outputs together, is bounded to 64 MiB for this small panel/model archive. Failure preserves outputs and every consumed claim.

Preserve original raw stores, graph hashes, failed archives, frozen source and
criteria. Bind all comparison evidence and resource receipts with hashes,
commit/push and verify the exact remote head at closure. Raw-data off-device
backup remains unverified. The monitor continues under standing authorization
and is retired after reviewed comparison closure or a terminal decision.
No paid resource, provider contact, new acquisition, neural run, trading or
production mutation follows from this charter.
