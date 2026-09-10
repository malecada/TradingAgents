# Independent accounting readiness review — September 10, 2026

Scope: review of the minute coverage repair, the saved timestamp inventory, exposure charter `c11527b5ca6d14b5a1d2d84785e1fedccad2bfbd` with pre-execution ledger clarification `0349f0403e49a69030dfbd09cde2be73f8c22459`, and the original-book lifecycle exposure diagnostic. Review uses source, registered documents, saved metadata and synthetic fixtures only. No strategy replay, original market-value read, price substitution, source edit or commit is performed by this reviewer.

## Minute coverage repair

No blocking defect was found in the reviewed change to `scripts/fetch_vision_1m.py`. The new predicate requires every expected UTC minute exactly once and in order; one observed row cannot certify a month. Duplicates, off-grid timestamps and interior/tail holes fail coverage. A partially observed month remains retryable despite its legacy archive-absence marker. Manifest wording correctly distinguishes an HTTP 404 from proof of non-listing. Legitimately partial listing/termination months remain incomplete until lifecycle evidence establishes the available period; this is conservative and does not fabricate observations.

Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/xsect/test_vision_1m_coverage.py -q -p no:cacheprovider`.

Result: **3 passed in 0.32s**. The fixtures cover complete, singleton, 72-hour tail gap, interior gap, duplicate, off-grid and wrong-month clocks, and retry with a legacy marker. No download was made. The legacy downloader is not the authorized immutable recovery writer; this review does not authorize running it against original stores.

## Timestamp inventory

The saved `data/recovery/2026-09-10/clock-inventory.json` hash is `2a71e5bcbe63e0b6820e2a08111763f8e1f1fff3895d03411262b396d1c4bc0d`, matching the exposure gate. Its recorded gate hash matches `data/predlab/gates.json` at its transform commit `264b865e0b33a1d0c498b27c90b64795e86cd781`; current inventory source bytes also match that commit. The inventory source projects only the timestamp field with a UTC filter `[2020-06-01, 2025-04-01)`. Full-file hashing supplies provenance without materializing price observations. Output uses exclusive creation.

All saved file counts, unique path/symbol counts, gap totals and contiguous range lengths were independently reconciled. There are 217 nonempty hourly files, 49 with internal gaps totaling 6,832 symbol-hours, and 799 daily files of which 442 have development observations and none have internal clock gaps. All recorded clocks are unique, monotone and cadence-aligned. Leading/trailing unobserved periods are separately qualified; the inventory does not certify listing, termination, price quality or instrument continuity.

A temporary synthetic Parquet probe verified that the April 1 holdout row is excluded, one missing interior March 31 hour is reported exactly, and the last development hour does not create a trailing gap. Naive clocks fail closed in PyArrow before the later explicit clock check; the first review probe expected a different exception class, then the corrected harness confirmed rejection. This is an error-message limitation, not evidence admission. No inventory was rerun against original market stores. All metadata assertions and corrected synthetic probes passed.

## Exposure contract and implementation

The committed contract freezes all six original cells, all five specified terminations, 217 original hourly inputs, the universe hash, feature/holding constants, and original missing-input construction. It correctly distinguishes incoming allocation at an exact closure boundary from the new target, and allocation during a bar containing an intrabar termination. No observed conflict is explicitly qualified and cannot certify valid settlement, executable quantity changes or readiness. The gate prohibits PnL, SR, DSR, probes, fitting, new prices, ticker substitutions, holdout and selection; six forensic rows do not change financial trial counts.

The source reconstructs only the original sorted-symbol membership/cascade/event-weight schedule. Reused constructor files are checked byte-for-byte against the original frozen commit `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`; the original result hash is also pinned and verified. The 217 input hashes and original universe/symbol-list hashes are checked before use and again before finalization. Only close and quote volume are projected within warmup/development bounds. No portfolio, funding, PnL, performance-probe or model-fitting function is called. All six cells and five events are retained, including construction failure statuses.

The exact-boundary check independently considers the prior requested allocation, so a zero target at settlement cannot silently dispose of an incoming position. Intrabar events inspect the target on the containing `[t,t+1h)` interval. Post-closure nonzero targets are retained, while quantity changes caused by NAV/price drift remain explicitly unknown. Conflict evidence is retained even when other allocations are unavailable. The surrounding input lookback is descriptive and does not certify complete competing-slot history.

Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_lifecycle_exposure_audit.py tests/xsect/test_vision_1m_coverage.py -q -p no:cacheprovider`.

Initial result: **16 passed in 0.99s**. Additional temporary synthetic probes confirmed incoming short exposure at exact closure and preservation of a known conflict alongside later unknown allocation. A temporary counter fixture demonstrated the integration finding below; it did not append a real ledger row.

### Actionable integration finding and disposition

Initial exposure writer lines 330–332 called `registry.log_trial` for six nonfinancial forensic records. `registry.trial_count` counts all ledger identities without interpreting `financial_candidate_evaluated=False`: a synthetic ledger containing one blocked financial row and one forensic row returned 2. This conflicts with the gate's unchanged financial trial denominator, although the separately frozen accounting denominator 150 was unaffected.

The parent accepted the finding and chose a dedicated append-only `forensic-ledger.jsonl` inside the registered exposure output namespace, leaving the central financial trial ledger and counter semantics untouched. The correction is now reviewed and verified. `write_forensic_artifact` makes no financial registry call, validates six unique cells and five unique events per cell, requires an explicit false financial-candidate flag, serializes both complete outputs before opening either, and uses exclusive creation. It records the dedicated ledger hash in the result and refuses repeat writes. The runtime hashes the central ledger before and after reconstruction and refuses a changed ledger. The gate clarification was committed before execution at `0349f0403e49a69030dfbd09cde2be73f8c22459`.

Final focused command (same two files as above): **30 passed in 1.12s** (27 exposure, 3 minute). New fixtures cover frozen registration guards, dirty-source rejection before market/output access, dedicated six-row logging, central-ledger preservation, output hash, repeat refusal, and malformed/unserializable payloads without partial writes. Restriction counts include post-closure new requests and separately identify pre-closure requests. No empirical execution was performed by this reviewer.

**Disposition: the finding is resolved; no remaining blocker was identified for the registered exposure-only diagnostic.** This is not approval for a financial replay. Low-level interrupted disk writes can still leave a consumed output directory requiring manual provenance review; the writer fails closed and does not silently overwrite or resume it.

## Factual documentation check

The draft `docs/data-recovery/DATA_RECOVERY_2026-09-10.md` agrees with the saved inventory and separately archived official settlement evidence. In particular, LUNA's closure is May 12, 2022 at 15:30 UTC; BNX's February 2023 old/new contract distinction is preserved; and neither archived general rules nor minute candles are presented as proven terminal cashflows. No factual correction was requested.


## Reviewed source identities

Final SHA-256 values at focused verification:

| File | SHA-256 |
|---|---|
| `scripts/fetch_vision_1m.py` | `8b0ba8ecf89f4ca21e7d319c6db23f301239c25050101050fcef189ba22772f7` |
| `tests/xsect/test_vision_1m_coverage.py` | `f10c3dc79d7816e200ece65f4b30ca4ad0ffff6a9a5d387abb776d0ad5273b18` |
| `scripts/inventory_recovery_clocks_2026_09_10.py` | `8255f255f364233afc47ec1ae4ba0a9e9607351b6df1056e03564969c752b9d8` |
| `scripts/audit_lifecycle_exposure_2026_09_10.py` | `a1dee1dbb2c9aa77ffb1d20add466d43dff55e948f19f2e6f9e8b6b7b0393edc` |
| `tests/predlab/test_lifecycle_exposure_audit.py` | `a719b55ab6181db109ae06c2eee7e68b95aa536a4581bb25ec424e7c05178ee7` |

## Completed exposure artifact verification

The registered diagnostic completed once on frozen source `1375e8a6528ec9e3f07c51ac4415880c056e867b`, from `2026-09-10T07:26:13.335452Z` to `2026-09-10T07:26:21.430891Z`. This follow-up inspected the completed JSON and hashed its referenced files; it did not reconstruct allocations, read original price values, rerun a strategy, calculate performance, or change any source, gate, input or result.

**Verification passed:** all 229 recorded input hashes; both recorded output hashes; the committed gate and correction-policy hashes; all six original cells in registered order; all five events per cell in registered order; and all six dedicated ledger records, whose identities, configurations and metrics exactly match the result. The central trial ledger's current bytes match both the artifact and committed `HEAD`. It contains no new exposure records, so financial trial counts remain unchanged.

| Preserved object | SHA-256 |
|---|---|
| Exposure `result.json` | `9657ac0113c024b682a08c6b6c2a7c2e7a4ec83481ad78cd5a94a4e1a10ddd46` |
| Dedicated `forensic-ledger.jsonl` | `cb9fff2c5d6e196030460582d54efe182dbd64ab43face38511b6ef32e40415b` |
| Central `data/predlab/trial_ledger.jsonl` | `0b9ab125e64e9c808ccd398d703092e344b6f8772de9e6ec6e223a1e2b9f9a09` |

Saved allocation rows independently reproduce the boundary incoming/requested allocations, event-straddling counts, post-closure counts and last-request timestamps, restriction request counts, per-event flags and per-cell conflict totals. Row timestamps are unique and ordered. The four observed conflicts are all LUNA at its May 12, 2022 15:30 UTC closure. Each requests weight 0.1 during the `15:00–16:00` bar that contains closure:

| Cell | Straddling allocated bars | Post-closure allocated bars | Last post-closure requested bar open (UTC) |
|---|---:|---:|---|
| `thr2.5_H24` | 1 | 12 | 2022-05-13 03:00 |
| `thr2.5_H48` | 1 | 36 | 2022-05-14 03:00 |
| `thr3.5_H24` | 1 | 0 | None |
| `thr3.5_H48` | 1 | 24 | 2022-05-13 15:00 |

The zero post-closure count for `thr3.5_H24` does not remove its intrabar closure conflict. Its September 9 measured FAIL therefore acquires an additional execution/lifecycle qualification; the preserved numerical artifact is not rewritten, and this audit does not calculate a revised return or gate verdict. The other three affected cells were already unavailable in the September 9 accounting run.

Both H6 LUNA checks and the other 24 symbol/cell checks report `no_observed_conflict_qualified`, giving 4 observed conflicts and 26 qualified absences across all 30 records. No record certifies readiness. The saved LUNA local lookbacks contain 120 missing close/volume hours in every flagged cell. Original missing-signal behavior and missing competing-slot history limit these diagnostic conclusions; recovered inputs could change allocations. Earlier BNX incarnations and all other unregistered lifecycle events remain outside this five-event audit. Exact settlement prices, fees and terminal cashflows remain unproven.

No artifact integrity or denominator defect was found. The observed lifecycle conflicts remain a substantive barrier to executable financial replay for those cells, rather than a reason to invent settlement or alter the original signal.
