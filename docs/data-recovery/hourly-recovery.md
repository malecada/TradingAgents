# Verified hourly recovery — September 10, 2026

The frozen transform `1375e8a6528ec9e3f07c51ac4415880c056e867b` recovered **5,568 genuine missing hourly bars across 47 symbols**. This includes all 360 primary TRXUSDT/FILUSDT/LTCUSDT hours. The other 1,264 inventoried hours remain explicitly quarantined: BNXUSDT 638 and ICPUSDT 626. All 49 symbols and 6,832 inventoried hours remain in the denominator. No strategy metric or backtest was computed.

| Batch | UTC execution | Inventoried hours | Verified insertions | Requests | Downloaded body bytes |
|---|---|---:|---:|---:|---:|
| Primary, 3 symbols | 07:25:59–07:26:14 | 360 | 360 | 72 | 301,238 |
| Extended, 46 symbols | 07:26:24–07:30:55 | 6,472 | 5,208 | 1,043 | 4,219,819 |
| Total | September 10, 2026 | 6,832 | 5,568 | 1,115 | 4,521,057 |

Both commands exited 0, sequentially, without a source, gate or admission-policy change. All 1,115 requests returned successful receipts; there were no checksum, schema, request, overlap or floating-point conflicts. The source hierarchy and exact-equality policy remained frozen throughout.

## What the recovered evidence establishes

Checksum-valid current monthly archives omit **all 5,568 ordinary missing target hours**. In the primary cases, February contains 600 hourly rows instead of 672 and April contains 672 instead of 720. The corresponding daily archives and public symbol-klines API supply the missing observations and agree exactly. All original/monthly/daily/API overlaps agree: 558 recorded comparisons involving 81,700 rows across repeated comparison pairs. These observations establish incomplete provider monthly archives and a local coverage predicate that concealed their incompleteness. They do not reconstruct the precise original download event or establish that today's archive revision was available at a historical research decision.

The fixed hourly predicate now requires a complete, unique, ordered hourly month and reports internal gaps. A missing archive's legacy `not_listed` status is explicitly qualified as archive absence. The bounded recovery uses daily/API corroboration; repeatedly obtaining the same incomplete monthly ZIP alone would not restore coverage.

## Saved-artifact verification

[Verification evidence](verification/hourly-artifact-checks.json) independently rechecked all 49 original hashes, 94 output Parquets and 2,230 raw body/receipt hashes. Every downloaded archive was rechecked against its saved provider checksum. Every original row in `[2020-06-01T00:00:00Z, 2025-04-01T00:00:00Z)` is preserved exactly in the corresponding snapshot, including registered 2020 warmup. Snapshot additions exactly match the approved missing timestamps and their 12-field insertion artifacts; no recovered snapshot has an internal hourly hole between its first and last observation. This clock check does not certify that every preserved original bar was tradable across a contract closure.

Original files remain unchanged. Values at or after April 1, 2025 were excluded by the Parquet read predicate; only whole-file hashing touched their encoded bytes. No BNX or ICP price request was made. All normalized outputs contain UTC open timestamps and exact one-hour close timestamps (`open_time + 3,599,999 ms`). Raw receipts retain URL, retrieval time, HTTP status/headers, body size and SHA256. Downloaded price bodies total 4.52 MB, below the 250 MB aggregate ceiling with the separately reserved documentary allowance.

The immutable result manifests contain all snapshot hashes:

| Result | SHA256 |
|---|---|
| `data/recovery/2026-09-10/hourly-primary/result.json` | `77174de1dd4afff71b45018b306e50b2295ee84b51563eb51db43fb7898139f2` |
| `data/recovery/2026-09-10/hourly-extended/result.json` | `48673ab5b47836153b7e85809e5766ccc9891773aaf62cce28bc3fc84ab13217` |

## Remaining limits

BNXUSDT includes three 2022 gaps totaling 120 hours and the 518-hour February 2023 lifecycle span. ICPUSDT's 626-hour September 2022 span predates the replacement contract. Official lifecycle evidence distinguishes settled original contracts from reused tickers; neither an ordinary same-ticker fill nor a successor splice is admissible. The intervals remain unavailable pending any separately registered identity-specific recovery, with genuine closure periods requiring lifecycle treatment rather than invented bars. Relevant documentary evidence is retained in [settlements](settlements.md).

Recovery of ordinary bars does not resolve settlement cashflows, previously preserved untradable/padded bars, or the full strategy-family readiness decision. Any subsequent strategy replay still requires a separate committed registration. No earlier research result, gate, original manifest or source Parquet was rewritten.

Offline implementation verification: 36 owned tests passed; the parent's integrated pre-run suite passed 143 tests. Exact test commands and regression logs are recorded in [source investigation](hourly-sources.md). Actual commands:

```text
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python scripts/recover_binance_hourly_2026_09_10.py --execute --batch primary
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python scripts/recover_binance_hourly_2026_09_10.py --execute --batch extended
```

Their complete logs are `verification/hourly-primary-run.log` and `verification/hourly-extended-run.log`. No recovery run or policy was repeated to improve an outcome.
