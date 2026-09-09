# Bounded correction artifact verification — September 9, 2026

**PASS: 108 of 108 read-only integrity checks; no discrepancy found.** The completed correction was inspected without running its generator, refitting a model, recomputing a backtest or bootstrap, accessing an API, or modifying original data/results.

Verified result: `data/predlab/audit_correction_2026_09_09/result.json`.

**Result SHA-256:** `21be37f6c53d9827a150309fdf722953846bf88a87d72c1a2f07b38872115a3c`

## Provenance and immutable inputs

- All **23 Parquet outputs** exist under exactly the declared names, with no missing or extra Parquet file. Every byte checksum matches `output_sha256`.
- All **46 referenced original inputs** under `/home/malecada/master_thesis/TradingAgents-predlab/data/predlab` still match their recorded SHA-256 values, both before and after this inspection. The four original artifacts pinned by the gate—development results, holdout verdict file, original gates and original ledger—also match their frozen hashes. The holdout verdict file was hashed only; its contents were not parsed or evaluated.
- The embedded registration equals the gate at source commit **`cc6801e81e25f05cdfbae77d560b59fa43e16dd9`** and the current gate. Its canonical SHA-256 is `611d12466b06865e38cb6fce51f9ce30713d7ac472a0effe02686c26b9b82bd5`. The correction-policy hash also matches the policy bytes at that source commit.
- The integrated trial ledger preserves its complete prefix from the source commit and contains exactly one correction record. That record names the same source commit, gate/config hash, completed status, 7 strategy cells, 16 forecast cells and development window. The registration timestamp precedes the result ledger timestamp. The original predlab ledger remains byte-identical to its frozen hash.

## Cell coverage and conclusions

| Artifact group | Required and observed coverage |
|---|---|
| S2 | `harq`, `har_levels`, `naive20`; 1,551 daily rows each |
| S3 | Thresholds 0.50/0.52 × smoothing 1/24; 37,201 hourly rows each |
| ENet | BTC/ETH × 1h/24h × T1/T2/T3/T4; all 16 declared cells |

All seven strategy frames retain the original inclusive endpoint convention, from January 1, 2021 through **March 31, 2025 at 00:00 UTC**. Their paired original metrics equal the preserved development JSON exactly. No shortened or extra strategy clock was found.

S2 checks both registered baselines with 1,532 paired 20-day volatility windows each. The recorded tracking-error reductions exceed 15%, but HARQ's corrected Sharpe is worse than both baselines and its drawdown is worse than HAR-levels. The recorded comparison flags and failed overall S2 gate agree with those values and the original rule. Every S3 corrected Sharpe remains below the frozen floor of 1.0; all four cells retain the original exploratory exclusion from graduation. The uncomputed legacy 13-cell DSR and absence of candidate promotion are expressly disclosed. Bootstrap p-values were checked as recorded inputs to the gate flags; the bootstrap was not rerun.

The 16 forecast frames contain **276,614 saved origins**, **276,612 scoreable origins** and **65,104 recorded fallback origins**. Their row counts, scoring/availability flags and coverage ratios agree with the result JSON. Original forecast timestamps, targets and saved predictions match the preserved development forecasts; fallback predictions equal the originally declared baseline at the same timestamp. Reconstructed unavailable rows retain raw NaNs. All 16 records remain diagnostic-only, without a significance, adoption or validation verdict.

## Evidence and boundary

Detailed checks, counts and failures list: `docs/audit/verification/bounded-correction-integrity.json` (108 passed, empty failures list). Verification used SHA-256 byte reads, Parquet metadata and development-filtered forecast reads, exact comparisons with the source-commit gate/ledger, and arithmetic consistency checks on already recorded metrics and flags. No strategy return, feature, model forecast or inferential statistic was regenerated.

This verifies artifact integrity, recorded provenance and conclusion consistency. It does not independently reproduce the numerical correction, validate a strategy, establish genuine historical feature vintages, or certify files outside the 46 referenced inputs. Original artifacts were not changed by this inspection.
