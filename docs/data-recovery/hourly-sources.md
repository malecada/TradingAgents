# Binance hourly recovery source inventory — September 10, 2026

**All three local interval sources have the same gaps. Official daily archive objects and checksum metadata exist for every missing symbol-day, but their financial contents have not yet been downloaded or validated.** This discovery stage used local timestamp columns, repository source, public documentation, HTTP HEAD responses and small checksum/server-time responses only. Original stores remain unchanged; no price was inferred, substituted or replayed in a backtest.

## Exact local coverage

The scope is Binance USDⓈ-M **symbol klines** for `TRXUSDT`, `FILUSDT` and `LTCUSDT`, open-labelled UTC one-hour bars. It excludes spot, COIN-M, index/mark prices and continuous-contract substitutions.

| Missing interval, UTC | Expected hourly rows per symbol | Observed rows in hourly store | Observed minute rows | Observed aggregate-hour rows |
|---|---:|---:|---:|---:|
| February 26, 2022 00:00 through February 28 23:00 | 72 | 0 | 0 / 4,320 expected | 0 |
| April 1, 2022 00:00 through April 2 23:00 | 48 | 0 | 0 / 2,880 expected | 0 |

These counts hold separately for all three symbols: **120 missing hours each; 360 symbol-hours total**. The last hour/minute before each gap and the first after it are present. Only the two necessary windows plus one hour on each side were loaded, using Parquet timestamp-column filters.

Exact source families, under `/home/malecada/master_thesis/TradingAgents/data/`:

- `xsect/klines_1h/{TRXUSDT,FILUSDT,LTCUSDT}.parquet`
- `xsect/klines_1m/{TRXUSDT,FILUSDT,LTCUSDT}.parquet`
- `rebuild/exec_pf/agg_1h/{TRXUSDT,FILUSDT,LTCUSDT}.parquet`

The minute manifests declare all 52 requested months covered, 2,270,880 rows per symbol; aggregate manifests contain 37,848 hourly rows per symbol. Their shared timestamp gaps establish that these alternatives cannot supply the missing observations. `xsect/klines_1h_missing_months.json` is empty for TRX/LTC and contains only June–September 2020 for FIL. Neither missing 2022 interval is flagged. The hourly manifest records first/last timestamps and row totals, without internal coverage ranges.

## Confirmed fetcher defect and remaining origin uncertainty

`scripts/fetch_xsect_klines_1h.py:90–108` treats a month as covered when **any** existing timestamp falls inside it. The monthly loop skips that month at lines 199–201; API retrieval starts only after the global last stored bar at lines 213–220. Consequently, the surviving February/April observations permanently suppress repair of their missing days. `scripts/fetch_vision_1m.py:101–113` uses the same any-row coverage criterion. Successful ZIP parsing is not checked against an expected clock, companion SHA256 files are not verified, and the manifests do not record partial internal coverage.

The hourly/minute fetchers also equate an archive HTTP 404 with permanent nonlisting. An absent archive object alone does not prove that a contract was unlisted. This is not the current missing-day response: all target daily objects currently return 200.

The **persistence and detection defects are established**. The original cause of the missing rows is still unassigned: current monthly ZIP payloads must be inspected after registration to distinguish incomplete provider archives from earlier import losses. Their shared gaps across independent interval downloads are consistent with a common archive issue, but that remains an inference, not a demonstrated payload finding.

## Primary provider evidence

Binance documents daily/monthly public archives, USD-M symbol klines sourced from `/fapi/v1/klines`, a 12-field OHLCV schema and companion SHA256 files. It also states that archived objects can be revised. A new recovery must therefore preserve the downloaded bytes, checksum response, retrieval time and content hashes rather than assert an unavailable historic vintage. [Official Binance public-data documentation](https://github.com/binance/binance-public-data).

Metadata was checked at **2026-09-10 07:02:48–07:02:55 UTC**. All six monthly ZIP HEAD requests, fifteen target-day ZIP HEAD requests, and their 21 checksum GET requests returned **HTTP 200**. ZIP bodies were not requested. Daily objects are 1,269–1,380 bytes; their Last-Modified timestamps are March 1–3 or April 4–5, 2022. Monthly objects are 27,239–31,807 bytes and were last modified January 8, 2024. Object size, presence and Last-Modified do not establish row coverage or the original availability of each observation.

Exact endpoint templates:

```text
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY-MM}.zip
https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY-MM-DD}.zip
```

Each checksum endpoint is the exact ZIP endpoint plus `.CHECKSUM`. `{SYMBOL}` is one of the three named contracts. The complete verified filenames and reported SHA256 values follow; each filename resolves through the matching template above.

| Monthly filename | Provider checksum |
|---|---|
| TRXUSDT-1h-2022-02.zip | `e960c9147b5c0ca10439ce2c9572015ba408d7f2c0ce6b4854878eee49c708cc` |
| TRXUSDT-1h-2022-04.zip | `783ac2ccb4609fc86765deef2a763628f0d73c8cfc306d2490b5d5f2b3546a84` |
| FILUSDT-1h-2022-02.zip | `9ca29f200fcbbf89f4375ba028ce4485de1b56a20f430c582ab4f9ca9a854696` |
| FILUSDT-1h-2022-04.zip | `184435f695d58ce5325a0eb7c2ffd6f8d7160a8a0c48a46acee10c053a5ea511` |
| LTCUSDT-1h-2022-02.zip | `530edd9825fbaa53389576163d0e8954738def451398b5f5bba4f98182c50699` |
| LTCUSDT-1h-2022-04.zip | `6c556dcf847b48ca020b56ab6c3e375a8e940b9c916d9f55c5b213488e5c9df8` |

| Daily filename | Provider checksum |
|---|---|
| TRXUSDT-1h-2022-02-26.zip | `759a23741ae937d6f7918ee7372173cb97f2e16a397f0a1e1477d44eab1fa876` |
| TRXUSDT-1h-2022-02-27.zip | `bdc5369cebe7a63a432a9a16e4a8a43300eed198dd343f1121ba6793c18572ed` |
| TRXUSDT-1h-2022-02-28.zip | `5febb713808bca3f504d479715ccb364c014784561f4235aa28a38ec4816797b` |
| TRXUSDT-1h-2022-04-01.zip | `85fa3f5e3e95b478928da74b59d70ea4ed0448c9bfbfa1e46e6769f23cce5df2` |
| TRXUSDT-1h-2022-04-02.zip | `c4687e5079493323757930738f1b36f959610174d20f4a18b9db3997bf2f483d` |
| FILUSDT-1h-2022-02-26.zip | `1421a586738f7d15673c2ee83797f834ca795200a45328ef937d797bfaabe580` |
| FILUSDT-1h-2022-02-27.zip | `9f7e28d9aceb0cfb017c75c40432a47d8f0224e06f4727f64f63c50420b074c6` |
| FILUSDT-1h-2022-02-28.zip | `b17338e294bd2e9fa2f3b92deaebe32864b52b1b253e243044ee84ecc0e7a8a1` |
| FILUSDT-1h-2022-04-01.zip | `ef02f51e11cadbcc052085f203a460c1a162e16dbfbb4745ec13d4245a8cdac5` |
| FILUSDT-1h-2022-04-02.zip | `cff602492027b2d5d21d916016e2bbfecfa39213e04916190b97d9f45cdeb5e8` |
| LTCUSDT-1h-2022-02-26.zip | `426ccd90cb2b9c17da9fc1ad4e7eb07067764a332066a8e7ec75c88e6ffcce18` |
| LTCUSDT-1h-2022-02-27.zip | `5234c4c09c5347651c50813a2070111e920b261807ad6d3554946b9ae4a7f367` |
| LTCUSDT-1h-2022-02-28.zip | `2516ad0fd306c2754ca3b341508b9a5df3beb607d8d25114359ba80a4d3beca1` |
| LTCUSDT-1h-2022-04-01.zip | `b1dd41d59f59a6ebe3d625de71db3bb2f88717f526ba5d2e0fb04ba7aa8da9fa` |
| LTCUSDT-1h-2022-04-02.zip | `3c9631ea621728f3ae38885dec7ac8276956fd8a4f45e8b71de0c6016e84559b` |

For example, the exact [TRX February 26 daily checksum](https://data.binance.vision/data/futures/um/daily/klines/TRXUSDT/1h/TRXUSDT-1h-2022-02-26.zip.CHECKSUM) and [TRX February monthly checksum](https://data.binance.vision/data/futures/um/monthly/klines/TRXUSDT/1h/TRXUSDT-1h-2022-02.zip.CHECKSUM) are both accessible. Listed values are the provider's assertions, pending verification against downloaded ZIP bytes.

## Public API fallback and frozen recovery requirements

The official connector identifies symbol bars with open timestamps and exposes `symbol`, `interval`, `startTime` and `endTime` on `GET /fapi/v1/klines`. [Official Binance USD-M connector](https://github.com/binance/binance-futures-connector-python/blob/main/binance/um_futures/market.py#L118-L134). The public server-time endpoint `https://fapi.binance.com/fapi/v1/time` returned 200 at 07:03:51 UTC, establishing connectivity only; no historical kline API response has been requested.

For each named symbol, the planned API endpoint is:

```text
https://fapi.binance.com/fapi/v1/klines
interval=1h
February window: startTime=1645833600000, endTime=1646092799999
April window:    startTime=1648771200000, endTime=1648943999999
```

A limit of 500 is sufficient for either bounded window without relying on an uncertain maximum-limit claim. Exact timestamp/schema validation remains necessary even if an API call returns 200.

The proposed registered implementation should archive the six monthly objects and fifteen exact missing-day daily objects with their checksum responses, then validate actual coverage. It should retain the 12 raw kline fields; verify unique, ordered hourly open timestamps, exact close-time convention, finite positive OHLC, valid high/low bounds and nonnegative volumes/counts; and require all 360 requested symbol-hours. The daily/monthly/API hierarchy and conflict policy must be fixed before inspection of price values. Suggested overlap controls are February 25, March 1, March 31 and April 3 for each symbol, compared with the existing original bars. Any conflicting observation must be quarantined rather than overwritten.

Only a new versioned raw/normalized snapshot may be written after the committed recovery charter and source are ready. Original Parquets, manifests, research results and gates remain untouched. A verified recovery would repair input availability for the already blocked cases; it would not itself change their research verdicts or authorize a backtest.

## Frozen implementation and offline verification

`scripts/recover_binance_hourly_2026_09_10.py` reads the committed scope addendum and emits independent per-interval admissions. The primary batch has 72 fixed requests: six monthly ZIPs, 27 daily ZIPs (15 missing dates plus 12 adjacent control dates), their 33 checksums, and six API windows containing the missing intervals plus one day on each side. Extended requests are generated from the hash-pinned inventory ranges, with API pages bounded to 500 hours. All BNX and ICP requests are excluded pending a separately registered original-contract alias mapping; every BNX/ICP interval remains explicitly quarantined. The separate lifecycle evidence establishes that the same ticker cannot identify a continuous contract.

The admission hierarchy is checksum-verified daily bars, corroborated by the public symbol-klines API; all available original/monthly/daily/API overlaps must agree exactly, without a numerical tolerance. A failed interval does not erase verified recoveries elsewhere. Each source attempt retains its body (including partial bytes), URL, UTC retrieval time, HTTP status/headers and local SHA256. An HTTP response, matching ticker or provider checksum alone does not establish historical publication vintage. The current provider bytes are retained as a later retrieval.

Original Parquets remain byte-for-byte untouched. Parquet predicates restrict original value materialization and normalized snapshots to `[2020-06-01T00:00:00Z, 2025-04-01T00:00:00Z)`. The registered 2020 warmup is retained. Every original row within that declared window must survive serialization exactly. Whole-file original SHA256 checks occur before reading, immediately before each artifact write and before completion; hashing outside-window bytes does not load their prices. The 12-field insertion artifact contains only approved recovered timestamps. The download budget subtracts prior hourly raw bodies and reserves at least 5 MB for documentary receipts, or their larger existing size.

The hourly legacy fetcher's coverage decision now requires the complete hourly calendar grid, rather than any row in a month. Partial observations override stale archive-absence markers. Its manifest reports exact internal missing ranges; listing/delisting edge months still require separate lifecycle evidence. No legacy fetcher or strategy execution has been run.

Offline command:

```text
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_recover_binance_hourly.py tests/xsect/test_klines_1h_merge.py -q
```

Initial regression evidence: 15 failures and 8 passes before implementation (`verification/hourly-red.txt`). Final review regressions: 7 failures and 24 passes before the corresponding fixes (`verification/hourly-review-red.txt`); 32 tests then passed (`verification/hourly-review-green.txt`). Coverage includes immutable insertions, invalid/checksum-corrupt inputs, empty/non-CSV archives, bounded requests, partial-byte retention, provider backoff, BNX quarantine, exact overlap admission/conflict, independent successful intervals, unavailable original isolation and a filtered development-only read. No market ZIP body or historical price API response has been consumed at this source-ready checkpoint.

Final pre-commit regressions also established that duplicate, off-grid or unsorted observations cannot count as a complete hourly month, and that registered June 2020 warmup rows survive the filtered snapshot read. These each failed before the corresponding fix (`verification/hourly-clock-red.txt`, `verification/hourly-warmup-red.txt`). The final owned suite passes 36 tests (`verification/hourly-final-green.txt`). The legacy HTTP 404 status label now explicitly describes archive absence without claiming proof of non-listing.

The original ICP contract was also settled before a distinct September 27, 2022 relaunch. All ICP requests and its 626-hour September interval are quarantined, with no successor or settled-contract alias lookup. Two synthetic ICP cases failed before this exclusion and passed after it (`verification/hourly-icp-red.txt`, final green log).
