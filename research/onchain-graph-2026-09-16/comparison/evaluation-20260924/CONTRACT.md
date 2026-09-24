# Fixed comparison implementation contract

Preparation only until the exact charter/gate, input bindings and independent
release review are committed and admitted. The unchanged parent PROTOCOL.md and
config.json define every scientific choice. No observed price or label may be
decoded during implementation or synthetic verification.

Experiment: `eth-matched-direction-20260924`. Namespace:
`research/onchain-graph-2026-09-16/comparison/evaluation-20260924`.
Execution uses the coordinator checkout and its pinned Python. No new Data
checkout or source acquisition is required. Original extraction source stays
87b6ac39d12a4f9a2ac1832f34f68647c52c53c8 and is never replayed.

## Inputs and admission

Registered input names: `config`, `protocol`, `history`, `approval`, `amendment`,
`graph_panel`, `graph_terminal`, `graph_review`, `graph_review_guard`,
`spot_capture_review`, `spot_manifest`, and for all 38 previously captured
months `spot_YYYY-MM_metadata`, `spot_YYYY-MM_zip`, `spot_YYYY-MM_checksum`.
ZIP/checksum inputs are the exact stored zstd response bytes. Decode only after
the ResearchRun claim and input hash checks. Bind the complete stored/raw size
and SHA256 chain to monthly metadata and original spot capture review/manifest.
Graph review must pass full-panel admission, match source/terminal/panel hashes,
and have a successful guard for that exact checker/root/source/report command.
Require exactly 1,096 graph source dates 2022-01-01 through 2024-12-31, in order,
with only 2022-01-01 and 2024-12-31 graph exclusions. Do not overwrite null
historical availability; normalized clocks are explicitly protocol assumptions.

## Production outputs

All artifacts are JSON inside the single lifecycle run outputs directory.

- `inputs-admission.json`: source identities, graph exclusions and qualifications.
- `market.json`: `{rows: [...]}` for normalized spot dates/open/close/quote_volume/
  available_at; exactly 2021-12-01 through 2025-01-01 inclusive.
- `graph.json`: `{rows: [...], exclusions: [...]}` for normalized admitted graph
  counts/clocks from the adapter, with original exclusions retained.
- `panel.json`: `{rows: [...], feature_sets: {...}}` for the dense fixed decision
  calendar, feature values, per-feature availability, labels and label intervals.
- `fits.json`: `{fits: [...]}`. Each successful fit record has `fold`, `arm`,
  `train_days`, `test_days`, `params` and `model_text` (LightGBM Booster string).
  A minimal optional audit callback in existing model functions may record this
  after fitting, without changing predictions, parameters or scientific rules.
  Preserve fits from a partially failed fold as well as successful folds.
- `predictions.json`: `{rows: [...]}` using the existing evaluator's dated
  prediction table and columns without scientific alteration.
- `evaluation.json`: the existing `model.evaluate` result except `predictions`,
  with DataFrames serialized as record lists, UTC timestamps as ISO strings,
  numpy scalars as native JSON scalars and unavailable numeric values as null.
- `summary.json`: counts, all cells, screening status and explicit retrospective
  qualification. No PnL or strategy claim.

Supplemental immutable fit checkpoints live in
research_runs/eth-matched-direction-20260924/fit-checkpoints/YYYY-MM-Mx.json.
Each envelope has schema_version=1, experiment_id, source, claim_sha256,
zero-based sequence and fit (exactly the corresponding fits.json record).
Publish atomically with no overwrite and fsync before prediction or another fit.
The final checker inventories and hashes all checkpoint members, reconciles
published JSON checkpoints to fits.json, and preserves any incomplete temporary
write as failure evidence. Both checkpoints and the eight JSON outputs share
the 64 MiB new serialized-payload cap. Checkpoint failure stops further fits.
Inference-only failure retains all completed forecasts and descriptive results,
while marking inference and screening unavailable without retry.

Publish admitted input tables and the decision panel before fitting. If fitting
or inference fails, retain already produced evidence and partial fit records;
never erase or retry the experiment. Use the existing evaluator's monthly
failure records and all-row admission mask. Lifecycle cells are 38
`spot-YYYY-MM`, one `graph-panel`, 36 `fold-YYYY-MM-M0/M1/M2`, one `inference`
and one `screening` (77 total). A failed monthly fold makes all its three arm
cells unavailable with an explicit reason; the fit archive preserves any
completed partial fits. Missing test days remain explicit even in a completed
fold; incomplete pooled coverage makes inference/screening unavailable.

## Independent checker

The checker does not import production model, feature or adapter modules and
does not refit models. It reconstructs source numeric spot rows from retained
hash-bound bytes, graph aggregate mappings, targets, lagged features, clocks,
common mask, purged monthly train/test membership and majority baseline.
It loads each saved Booster string, checks feature order and verifies saved
probabilities on independently rebuilt test inputs. Fitted parameters, recorded
train membership and tree input feature names are checked; saved model replay
does not independently prove the historical training operation itself.
It independently recomputes monthly/pooled classification scores and paired
14-day, 2,000-resample bootstrap with the frozen seed and percentile rule, all
missing/failed fold handling and the original screening rule. These checks are
outcome forensics, not another fit or an empirical allowance reset.

CLI: `check_final.py --root ROOT --source SOURCE --report ABSOLUTE_REPORT`.
Report is exclusively published in this namespace after structural lifecycle
verification and independent checks. Export reusable pure checks for synthetic
tests. Report scope and unavailable results explicitly; a failure-only evidence
review cannot be labelled a passing complete prediction comparison.

## Resource and implementation ownership

The parent owns charter/gate/admission/launch, preservation and integration.
The runner worker owns `run.py`, the optional callback in parent `model.py`,
and `tests/research/test_onchain_matched_run.py`. The independent checker worker
owns `check_final.py` and `tests/research/test_onchain_matched_final.py` only.
No agent changes the frozen feature/model configuration or protocol. Synthetic
tests use invented prices/counts only. Dependencies and source hashes must be
complete before admission; no empirical CLI is called during development.
