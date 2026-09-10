# Independent saved-result review

**PASS.** Both completed packages were checked against registration `38d9a67e6ff042cb1fd870877b3e0222f40fdc08` and execution source `cd8d9e3f064bb40273ba493e597e371e6f199b66`. The only identified discrepancy is an earlier prose count of halted cash rows, corrected below. No diagnostic runner, bootstrap resampling, strategy replay or network request was executed during verification.

The new checker was run once:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -B docs/diagnostics-2026-09-10/verification/check_results.py
```

It exited zero in 5.40 seconds and wrote `result-review.json`, containing 11,891 assertions and per-cell denominator records. Its SHA-256 is `f7c04b64026cbf1b8c339f31b940fba77cabbf5ffe7460799301ee6149463180`.

| Package | Verified scope | Result SHA-256 |
|---|---|---|
| Forecast | 16 cells and forensic identities; 35 listed output artifacts | `acbe21b51a346211a8c13c9c04ca82844c6fe90b12f9ac5a604b1dca15ef9cdc` |
| Factor risk | 36 sleeves and forensic identities; 75 listed output artifacts | `d37d6f7ab18b307aa12f4b5f57212ee0dbffd7611358ba3a1beaf8638982f9fa` |

All 113 registered input references, representing 112 distinct files, matched their pins. Output inventories contain precisely their declared artifacts plus each result file. Current reviewed sources match the execution commit, and the recorded correction-policy hashes match that commit's policy bytes. Later documentary appends are not confused with the policy active during execution.

Forecast verification covered all 276,616 clock rows, including 276,612 scoreable observations, and all 32,000 saved bootstrap draws. Paired targets, predictions and masks were compared with the pinned corrected vectors and declared baselines. Original baseline values were filtered to their registered development bounds before materialization. Loss formulas, fallback-zero differences, means, original-correction reconciliation, saved percentile intervals, centered p-values, stability counts and sixteen-slot Holm arithmetic agree. The twelve unresolved nested comparisons retain null primary p-values and adjustment inputs of one. Only the four volume comparisons are eligible for conditional inference; their rejection flags do not constitute fresh model-class or strategy validation.

Risk verification covered 44,676 target dates, 44,640 trace dates and all 852 saved price-stop events. Original trace fields and latent targets match the derived records. Component totals and halt dates reconcile with the original result. Direct checks cover drifted weights, opening turnover decomposition and netting, staged NAV/drawdown identities, successor classifications and unique re-entry charges. Every exposure series—latent, incoming, applied and closing—has matching proxy values, reference ratios, distribution summaries and finite/active/unavailable threshold denominators.

The central financial ledger remains exactly 748 rows and 569,325 bytes, SHA-256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. Preservation verification also passed for 7,217 baseline tracked files under the declared three-path policy, all 62 prior gate objects and all 270 original external input receipts. No old artifact was rewritten.

## Documentary count correction

The correct already-halted cash-row range is **238–1,158**, rather than the earlier prose range ending at 1,157. The original immutable `tsmom_k180_ls-primary-ethereum-trace.parquet` has its first halt on January 28, 2022. Its `halted_before` mask is true on 1,158 dates, January 29, 2022 through March 31, 2025 inclusive. `halted_after` is true on 1,159 dates because it also includes the halt date. The original result records the correct January 28 halt date and does not contain the erroneous cash-row count. The new diagnostic agrees with the original trace. This is a prose addendum; historical artifacts remain unchanged.

The review certifies saved identities and arithmetic, not stationarity, missing-target recovery, executable perpetual-market provenance or causal effects of alternative risk/stop policies. Final Git retention is verified separately.
