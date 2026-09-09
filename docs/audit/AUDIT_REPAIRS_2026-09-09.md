# September 9, 2026 — system repairs and evidence reconciliation

The confirmed defects from the [system audit](/home/malecada/master_thesis/AUDIT_SYSTEM_2026-09-09.md) have been repaired, independently reviewed and exercised by 779 passing offline tests. A single preregistered correction completed all seven original S2/S3 development cells and sixteen saved ENet diagnostics. Software errors materially affected the historical comparisons, but the corrected S2/S3 evidence still provides no strategy eligible for promotion. The thesis withdraws invalidated positive claims and bounds the negative conclusions to the tested configurations.

Current engineering checkout: `/home/malecada/master_thesis/TradingAgents-audit-fixes`, branch `fix/system-audit-2026-09-09`. Source repairs used by the bounded run are committed as `cc6801e81e25f05cdfbae77d560b59fa43e16dd9`. Original worktrees and raw evidence remain preserved. Live deployment is a separate outstanding operational step; the VPS was not changed or inspected by these repairs.

## Repairs implemented

| Area | Resulting behavior | Evidence |
|---|---|---|
| Accounting | Simple-return PnL, initial-capital drawdown, drifted holdings, fees on actual turnover, signed funding, complete clocks, compounded hourly NAV and explicit failure on missing held prices. Cost stress and exact overlays replay the book. | [Accounting repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/accounting-repair.md) |
| Forecast scoring | Missing fits/features remain unavailable, with the declared baseline applied on the same origin. Raw/effective forecasts, fallback reasons, coverage and exclusions are retained. | [Data repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/data-repair.md) |
| Causal data | DEX normalization uses prior available observations and completed five-minute FX quotes. Versioned news/on-chain records preserve actual retrieval times; unverifiable historical vintages cannot be silently treated as point-in-time data. Fetch coverage revisits incomplete tails. | [Data repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/data-repair.md) |
| Execution and paper | Persisted intents and stable order IDs, query-only recovery from unknown submissions, actual position reconciliation, cumulative partial-fill/fee accounting, stale-data refusal, isolated dry state, and versioned funded paper measurement. | [Execution repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/execution-repair.md) |
| Evidence and inference | Committed gate/source/data/policy provenance, full trial identity, append-only corrections, complete comparison denominators, explicit dependence and nested-model inference, corrected cointegration and reversal tests. Historical gate thresholds remain unchanged. | [Evidence repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/evidence-repair.md) |
| Manuscript | Unsupported strategy/venue/capacity claims withdrawn in both languages; included tables and figures reconciled; engineering contribution and assignment mapping retained. | [Thesis repair](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/thesis-repair.md) |

## The bounded correction

Only the original development interval and fixed cells were evaluated. No holdout data were evaluated, no model was refitted, and no new search was conducted. The existing holdout verdict file was hashed for provenance; no holdout returns or verdicts were recomputed.

| Cell | Original net SR | Corrected net SR | Corrected maximum drawdown | Observations |
|---|---:|---:|---:|---:|
| S2 harq | +0.2037 | +0.4909 | 35.58% | 1,551 |
| S2 har_levels | +0.3423 | +0.6400 | 31.00% | 1,551 |
| S2 naive20 | +0.4505 | +0.7348 | 39.62% | 1,551 |
| S3 s3_t0.5_h1 | -2.1391 | -1.8877 | 99.14% | 37,201 |
| S3 s3_t0.5_h24 | -0.0804 | +0.2056 | 72.75% | 37,201 |
| S3 s3_t0.52_h1 | -2.6926 | -2.4834 | 99.30% | 37,201 |
| S3 s3_t0.52_h24 | -0.1603 | +0.0359 | 69.14% | 37,201 |

The S2 HARQ tracking-error reductions are 21.35% against HAR levels and 25.50% against naive20, on 1,532 paired volatility windows. Both pass the 15% tracking-error floor and the frozen bootstrap check (zero adverse draws among 2,000 resamples; not a population probability of zero). HARQ Sharpe remains worse than both comparators, and its drawdown is worse than HAR levels. The original conjunctive S2 gate therefore fails. Every S3 cell is below the original SR1 floor and is ineligible for graduation under the original exploratory restriction. No DSR across the 13 legacy cells is recomputed from the invalidated S1 evidence.

S2 contains 1,551 daily observations. S3 retains the exact 37,201 saved hourly origins, ending at 2025-03-31 00:00 UTC; the last day's later hours are not fabricated. The development-only correction does not validate any strategy.

| Saved ENet cell | Scored / saved | Fallback count | Raw valid coverage | Original loss | Corrected loss | Baseline loss |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT / 1h / T1_ret (se) | 37,201 / 37,201 | 10,395 | 72.06% | 4.54035e-05 | 4.54035e-05 | 4.52378e-05 |
| BTCUSDT / 1h / T2_dir (brier) | 37,201 / 37,201 | 10,395 | 72.06% | 0.315078 | 0.249585 | 0.249991 |
| BTCUSDT / 1h / T3_rv (qlike) | 37,200 / 37,201 | 11,328 | 69.55% | 0.929794 | 0.822537 | 0.606691 |
| BTCUSDT / 1h / T4_vol (mase) | 37,200 / 37,200 | 949 | 97.45% | 1.49266 | 0.669187 | 1.09387 |
| BTCUSDT / 24h / T1_ret (se) | 1,551 / 1,551 | 425 | 72.60% | 0.00107746 | 0.00107746 | 0.00103847 |
| BTCUSDT / 24h / T2_dir (brier) | 1,551 / 1,551 | 425 | 72.60% | 0.312468 | 0.25661 | 0.251395 |
| BTCUSDT / 24h / T3_rv (qlike) | 1,551 / 1,551 | 448 | 71.12% | 0.799607 | 0.673304 | 0.397951 |
| BTCUSDT / 24h / T4_vol (mase) | 1,551 / 1,551 | 93 | 94.00% | 4.16643 | 0.748493 | 0.903588 |
| ETHUSDT / 1h / T1_ret (se) | 29,185 / 29,185 | 9,470 | 67.55% | 5.42511e-05 | 5.42511e-05 | 5.42366e-05 |
| ETHUSDT / 1h / T2_dir (brier) | 29,185 / 29,185 | 9,470 | 67.55% | 0.323876 | 0.249429 | 0.250056 |
| ETHUSDT / 1h / T3_rv (qlike) | 29,184 / 29,185 | 9,558 | 67.25% | 0.711538 | 0.665279 | 0.741546 |
| ETHUSDT / 1h / T4_vol (mase) | 29,184 / 29,184 | 860 | 97.05% | 1.66473 | 0.705945 | 1.12317 |
| ETHUSDT / 24h / T1_ret (se) | 1,217 / 1,217 | 399 | 67.21% | 0.00131669 | 0.00131669 | 0.00130492 |
| ETHUSDT / 24h / T2_dir (brier) | 1,217 / 1,217 | 399 | 67.21% | 0.32717 | 0.25871 | 0.251456 |
| ETHUSDT / 24h / T3_rv (qlike) | 1,217 / 1,217 | 403 | 66.89% | 0.505211 | 0.46323 | 0.492057 |
| ETHUSDT / 24h / T4_vol (mase) | 1,217 / 1,217 | 87 | 92.85% | 3.7398 | 0.589816 | 0.759746 |

Each loss is compared only within its own cell. Lower is better; scales differ across targets. Variance losses in the original implementation omitted some invalid forecasts, so original and corrected QLIKE means have different denominators; the JSON and per-origin artifacts preserve those counts. The corrected comparison retains every origin with a valid target and declared baseline, while reporting model failure and fallback. Missing raw model availability was reconstructed from the original features and fit schedule; a valid zero or clipped boundary forecast was retained unless an independent failure condition was established. No model was refitted, selected or promoted.

The previous blanket interpretation of ENet failure is not supported by these corrected diagnostics. For example, hourly direction Brier losses become 0.249585 for BTC and 0.249429 for ETH, close to their declared baselines, while all four volume-loss comparisons materially improve. This warrants accurate reporting of the historical evidence, not a new profitability or significance claim.

## Verification and provenance

- Final integrated offline suite: **779 passed, 2 deselected**, 3,502 known warnings, 223.37 seconds. The three-test physical raw-store coverage file was excluded in the isolated checkout; two legacy parity/marker tests were deselected. Online/slow tests and live exchange behavior were not exercised.
- Hand-derived regressions cover initial loss/drawdown, held-unit drift, round-trip returns, fees, missing observations and unavailable forecasts. Mutation tests cover causal availability. Fake-exchange tests cover unknown, rejected and partial orders, reconciliation, dry/live isolation and emergency residuals.
- Independent reviews and preservation checks: [accounting/execution](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/independent-accounting-execution-review.md), [evidence](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/independent-evidence-review.md), [bounded artifact verification](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/bounded-correction-verification.md), [final preservation verification](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/final-preservation-verification.md).
- Source commit: `cc6801e81e25f05cdfbae77d560b59fa43e16dd9`. Registration preceded results in `6436f28`, with the pre-result maintenance-turnover clarification in `9aee7a9`.
- Gate SHA256: `611d12466b06865e38cb6fce51f9ce30713d7ac472a0effe02686c26b9b82bd5`. Pre-run correction-policy SHA256: `23cdf85b45138a5a0429e19bf20fd195402bbc9aec4e03cdb28e8eb2ed8d8350`.
- [Immutable result](/home/malecada/master_thesis/TradingAgents-audit-fixes/data/predlab/audit_correction_2026_09_09/result.json), SHA256 `21be37f6c53d9827a150309fdf722953846bf88a87d72c1a2f07b38872115a3c`. It contains all source and 23 output checksums, original/corrected values and denominator counts. Original input files were unchanged after the run. Completion is appended in the ledger and correction register; the frozen gate's pre-run status is retained as history.
- [Correction register](/home/malecada/master_thesis/TradingAgents-audit-fixes/docs/audit/corrections.jsonl) resolves superseded claims without deleting the original evidence. [Findings §88](/home/malecada/master_thesis/TradingAgents-audit-fixes/THESIS_FINDINGS.md) records the complete correction.

## Versioned deliverables

The correction branch `fix/system-audit-2026-09-09` contains the integrated source, append-only evidence records, all 23 correction outputs and review reports. The source used by the empirical correction remains pinned to `cc6801e81e25f05cdfbae77d560b59fa43e16dd9`; subsequent commits add outcomes and documentation.

The revised thesis is committed and pushed to its private remote at `8ab5828acb261413bae333fc3ff1d090a7d4e15c`. Its [92-page PDF](/home/malecada/master_thesis/thesis-latex/main.pdf) has SHA256 `8a78f19b9a52ec2c384ab29b2fdd9b24ebfb2d29354094c8de6f1895216fc7eb`; the final build has zero overfull boxes, undefined references/citations or duplicate labels. Existing nonfatal font/microtype/bookmark warnings remain.

## Remaining limits and operational work

The repaired source has not been deployed to the VPS, and legacy live journals have not been reconciled against actual exchange positions/fills. Historical point-in-time vintages cannot be recreated from latest-only stores. S1/champion/Bybit and other changed-engine families were not repriced under the September contract; those claims stay invalidated or qualified. Any additional empirical correction requires a separate committed registration, with prior holdout spending preserved.

The thesis has been reconciled to the corrected evidence. The signed assignment attachment remains unavailable and must be supplied before submission. Academic acceptance and production behavior are not established by local compilation or offline tests.

No validated trading strategy is claimed. The engineering repairs and preserved negative evidence provide a more reliable basis for a separately authorized research decision; they do not prove that every possible strategy lacks an edge.
