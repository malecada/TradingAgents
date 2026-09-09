# Forecast and causal-data corrections — 2026-09-09

Implementation is confined to the integrated audit checkout. The original worktrees, source stores, forecasts, result artifacts, and gates were not modified by this task. No API was called and no empirical model fit, strategy run, or holdout evaluation was performed. Tests use synthetic inputs and temporary stores.

## Implemented contracts

- ENet returns NaN when unavailable or when a selected feature is nonfinite. Unfitted LightGBM also returns NaN; its native missing-feature treatment is unchanged. ProbClip preserves unavailable predictions and unknown training/history labels.
- `runner.forecast_frame` implements `declared_baseline_fallback_v1`. Missing/nonfinite predictions, nonpositive variance forecasts, out-of-range probabilities, and nonfinite model losses receive the originally declared baseline whenever that baseline is scoreable. Raw predictions, effective predictions, fallback reason/status, target validity, baseline validity, and common-clock scoring status are retained. Every model is compared on the same target/baseline-valid clock. Coverage and exclusion denominators are explicit. There is no replacement baseline if the declared baseline is unavailable.
- `run_cell(..., return_forecasts=True)` preserves the existing `(rows, predictions)` interface with effective predictions. `return_diagnostics=True` returns `(rows, predictions, diagnostic_frames)`. Per-origin diagnostics are also written into new forecast Parquets; result DataFrame attributes do not carry nested DataFrames.
- Non-dry runs preflight registration before fitting, refuse existing forecast files or an existing card tier, and record the full input-series SHA256 (values, index and schema), constructor settings captured before fitting (including nested wrappers), cell configuration, registration provenance, and `hac-selection-v2` policy metadata. Root owns the statistical implementation and evidence registry.
- nlst2/3/4 normalization now uses strictly earlier decisions with feature availability strictly before the current decision, within the same calendar quarter. Rows sharing a decision timestamp cannot inform one another. At least two prior finite observations are required to standardize a feature; known constant history produces zero only for a known current feature. Missing raw values remain NaN. The builders expose UTC epoch-second decision/feature-window availability timestamps; historical block-time interpolation remains an existing timing approximation, not a new assertion of exact publication availability.
- DEX ETH conversion requires explicitly open-labeled five-minute quotes. At time `t`, the quote is exactly the candle opening at `floor_5min(t)-5min`. Missing/nonpositive prices fail with an actionable error; daily prices and stale substitutes are refused. Corrected feature/event cache names end in `_causal_v2.parquet`; legacy event/feature caches remain separate. No corrected event book or score table was generated.
- Failed ownership retrieval returns NaN and is not cached as `False`. Legacy ownership caches without explicit successful retrieval status are treated as unknown and are not overwritten.
- Alpaca, HF, and CoinMetrics normalization timestamps the returned version at actual retrieval time and records availability basis/retrieval time; Alpaca also records source update time. Legacy ingest-lag arguments cannot backdate a retrieved CoinMetrics version. Known availability cannot precede the source update.
- News and on-chain upserts reject conflicting same-key vintages. Exact repeats are idempotent. Before an existing monthly materialized shard changes, its bytes are preserved under the month's `_vintages/<month>/<sha256>.parquet` directory, outside ordinary query globs. Ordinary queries select the latest eligible vintage per article or event/coin/metric/source; `all_vintages=True` explicitly exposes revision history. Strict PIT is the default; legacy/unverified availability raises an actionable error. `strict_pit=False` is only a qualified diagnostic escape hatch. The news wrapper no longer hides that error as “no signals.” On-chain feature loading also enforces the provenance requirement, and late revisions of older events cannot displace already available newer events.
- Monthly 5m and daily OI coverage checks require every expected timestamp, not one row. The 5m tail revisits the last cached candle and excludes candles not yet completed at the retrieval cutoff.
- RV aggregation retains missing calendar buckets, never differences closes across a missing 5m boundary, exposes bar/return coverage, and marks incomplete target aggregates unavailable. This is a prospective completeness policy: the old 80% RV-only threshold does not silently govern the corrected implementation.
- LightGBM directional accuracy uses the same transformed row's already-lagged reference price. The extra shift is removed. Agent-facing reports and the prediction analyst prompt withdraw old 85%/76% accuracy claims and unsupported model-superiority instructions; agreement and magnitude are described as unvalidated heuristics.

## Historical limits and unsupported effects

Software acceptance does not establish forecast skill or a profitable strategy. No prior verdict was recalculated by this task.

1. Historical ENet zeros and clipped 0.02 probabilities are not individually sufficient to identify every failed forecast. The authorized saved-forecast correction must reconstruct selected-feature availability and the minimum complete-training-row condition, retain unexplained boundary forecasts, use each cell's original baseline, and preserve every denominator. T3 invalid nonpositive forecasts additionally require baseline substitution. No refitting is implied.
2. Causal DEX normalization and contemporaneous ETH conversion can change scores, ranks, sizing, gas valuation, and returns. The historical magnitude and any economics-verdict change remain unmeasured. Old P0 rankings are retrospective and cannot be represented as executable h24 scores.
3. Missing historical news text/value versions cannot be recreated from final revised downloads. Existing assumed publication-plus-lag timestamps remain unverified, even when their as-of filter was mechanically correct. Prospective retrieval vintages do not retroactively repair them. The number of actual historical revisions and their forecast effect remain unknown.
4. Existing ownership `False` values cannot establish whether RPC retrieval succeeded. No incidence estimate can be recovered from those booleans alone.
5. The audit found no development gaps in the examined BTC/ETH 5m/RV data. The RV repair therefore fixes a latent robustness defect; no claim is made that it explains classical-model development results. OI timestamp and field completeness remain distinct. The per-field OI aggregation policy and vendor recoverability of historical gaps were not changed here.
6. Bybit manifest reconstruction, existing-file end-date skip handling, universe/delisting incompleteness, and broad fetch-manifest provenance are not repaired by this task. No vendor reconciliation or historical refetch occurred.
7. The corrected LightGBM directional-accuracy formula does not supply replacement historical accuracy. Prior accuracy percentages remain withdrawn pending a separately authorized corrected evaluation.

## Regression evidence and verification

The new regressions were executed against the defective behavior before their corresponding fixes. Observed failures included zero instead of NaN; missing QLIKE origins; late/same-time score mutation; invented known feature counts; daily/stale ETH conversion; cached failed ownership negatives; backdated normalization and vintage overwrite; duplicate revised articles; late old-event revisions replacing newer metrics; one-row coverage; gap-bridging RV; shifted directional reference; unsupported report percentages; absent series/config provenance; and fitting before existing-artifact refusal.

Final combined offline command (run from this checkout):

```bash
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -m pytest -q \
  tests/predlab/test_audit_forecast_availability.py tests/predlab/test_runner.py \
  tests/predlab/test_losses.py tests/predlab/test_tier2.py \
  tests/predlab/test_audit_causal_dex.py tests/predlab/test_nlst2.py tests/predlab/test_nlst3.py \
  tests/predlab/test_audit_fetch_rv.py tests/predlab/test_rv.py \
  tests/predlab/test_fetch_5m.py tests/predlab/test_fetch_oi.py \
  tests/dataflows/test_audit_vintages.py tests/dataflows/test_sentiment_store.py \
  tests/dataflows/test_onchain_store.py tests/dataflows/test_crypto_sentiment_pit.py \
  tests/dataflows/test_onchain_features.py tests/models/test_audit_direction_reference.py \
  tests/models/test_target_mode_logret.py tests/models/test_data_transform_target_nan.py \
  tests/predlab/test_features.py tests/predlab/test_splits.py tests/predlab/test_har.py \
  tests/predlab/test_tier1.py tests/predlab/test_tier1_vol_funding.py
```

Result: **154 passed** in 64.39 seconds; 3,500 existing LightGBM/sklearn feature-name warnings.

Output: `docs/audit/verification/data-repair-pytest.txt`. Existing LightGBM/sklearn feature-name warnings are disclosed in that log; no warning suppression was added. `git diff --check` is also run before handoff. Commits and cross-owner review remain root-coordinated.
