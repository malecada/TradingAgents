# Operational integration and read-only VPS audit — September 10, 2026

The missing BZRX/LUNA/BNX historical settlement records are deferred at the user's instruction. No alternative price or fee is manufactured and no further Binance support contact is attempted. The research request text was never sent; a contact address was entered in a visitor form before security verification. No case number or provider response was obtained. **Two conditional measured failures and 22 unavailable accounting cases remain; zero validated strategies.** No financial trial, ledger append, model fit or holdout evaluation occurred in this stage.

## Verified operational gap

A read-only SSH probe at 2026-09-10 10:23:56 UTC collected checkout hashes, selected source hashes, service states and journal/funding metadata. It did not read credentials, environment-file contents, account balances, full cron bodies or private account records, and did not call an exchange account API. No remote source, service, journal or order was changed. The exact collector and output are retained in `verification/collect_runtime.py` and `verification/runtime-2026-09-10.json`.

| Component | Observed state | Implication |
|---|---|---|
| `/opt/tradingagents/predlab` | HEAD `558ffe7456dbfa95e89f960df713a4e3d8125ea0`; old paper/live code; shared accounting modules absent | The repaired writer and execution reconciliation are not deployed |
| `/opt/tradingagents/repo` | HEAD `ed5e22f63d9e2d8ab4bf163103f40b0029eb0e7b` | Current main monitor still reads legacy S1 journals |
| Paper journals | 39 VT10 and 38 champion legacy rows; latest as-of September 9; no v2 journals | Fresh file dates do not establish corrected net performance |
| Testnet journal | 17 legacy rows; no v2 execution journal | Completion dates do not establish actual reconciled positions |
| Funding | `/opt/tradingagents/predlab-data/xsect/funding` absent | Corrected funded paper measurement cannot be assumed available |
| Services | Monitor, Caddy and cron running; quant and hybrid cycle timers inactive | Service activity proves neither accounting completeness nor strategy validity |

The actual S1 scheduler commands, interpreter paths, account positions and dependency versions were not inspected. An absent halt flag does not establish a flat account. Previously documented schedule times are not a new verification of the current cron contents.

## Local compatibility repair

The integration branch `fix/operational-integration-2026-09-10` merges the repaired source at `fb40355a31193639b6301361e293f608f5e769cb` with current main at `ed5e22f63d9e2d8ab4bf163103f40b0029eb0e7b`. Merge commit `e9e62d9` preserves both histories and the newer monitoring functionality. Original dirty worktrees remain untouched; neither production main nor the VPS is changed by this local merge.

The monitor prefers v2 journals and never falls back to old gross results when a v2 file exists but is empty, corrupt or incomplete. Legacy composition and freshness remain available as diagnostics. Base performance reads saved base net measurements; overlay performance reads already-net overlay measurements without applying scale again. Version, state/return consistency, expected dates, missing observations and reconciliation status are explicit. Missing intervals remain in chart calendars with unavailable values; a broken measured chain cannot reconnect as complete performance. Legitimate initial state and observed flat overlay warmup remain distinct from missing data. The volatility target requires 20 contiguous corrected base net observations.

The frontend withholds legacy API performance, shows measurement and reconciliation reasons, and preserves null values through range slicing and chart conversion. Account equity is labelled an unadjusted change, not a strategy return. The invalidated S1 development references, yearly comparisons and derived 0.946 gate are withdrawn from the served S1 views; the original gate records are unchanged. This is an operational compatibility correction, not a fresh S1 validation. Other legacy quant/hybrid panes and their historical anchors are outside this S1 change and must not be cited as validated evidence.

The backup keeps all four legacy/v2 paper journals in the dedicated backup branch, refuses source truncation or rewriting, handles partial rollout, and retries an unpushed local commit even when no new bytes arrive. Git failures stop explicitly. Operational logs are excluded from new backup updates. `BACKUP_SYNCED` describes delivery; `V2_FRESH` describes latest expected dates and journal versions. Neither establishes funding coverage, daily continuity, economic completeness, execution reconciliation or a valid strategy. Executor fills, order intents, day-equity state and halt flags are not covered by this four-file backup.

## Verification and remaining boundary

**489 integrated Python tests and 25 frontend tests passed**, with a successful frontend build and lint. Synthetic tests and independent reviews cover incomplete/legacy/v2 payloads, hand-calculated net/state consistency, warmup, dates, reconciliation and real local Git remotes with push/pull failure. Frontend render tests verify that old references and false warmup claims disappear, while unavailable values remain unavailable. Test counts and exact source hashes are recorded in `verification/final-manifest.json`; no result is produced from a market replay.

Preservation checks verify 2,476 previous local recovery/replay/settlement artifacts and 222 original input hashes. Original market stores, research gates, results, accounting engines and paper/live writers remain unchanged. The financial ledger retains its 428,150 bytes and SHA-256 `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791`, with no new rows.

A manual monitor rollout can show the present unavailability honestly while execution stays unchanged. A funded v2 paper chain is a later prerequisite: missing active funding produces an incomplete state that subsequent rows cannot automatically repair. Funding admission must precede accumulation; any restart after a broken chain requires an explicit, preserved version boundary. The standalone event-accounting module is still not integrated into S1, whose funding measurement retains its documented daily approximation. No production readiness, venue margin correctness, deployment or strategy-validation claim is made.

The concrete staging and rollback sequence is in `MANUAL_ROLLOUT.md`. Generic deployment is unsuitable here: it enables unrelated stopped trading timers; Docker's broad copy includes research artifacts; package defaults install large research frameworks and do not explicitly package the built monitor frontend. A committed source allowlist avoids those paths while preserving the existing runtime and external data roots.
