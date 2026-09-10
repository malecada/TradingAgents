# Lifecycle readiness and original-allocation audit review — September 10, 2026

## Scope and present disposition

Recovery of hourly rows alone does not establish liquidation-fade replay readiness. Official notices identify five terminations inside the frozen monthly universe: LUNAUSDT in May 2022, TOMOUSDT in November 2023, RNDRUSDT in July 2024, MATICUSDT in September 2024 and BNXUSDT in March 2025. The original monthly universe SHA256 is `0b9e931f7eae01d6d5f85aa6ef48fc63b2fd7453b5a7990e460b8eb0874d4e96`. BZRXUSDT was absent in December 2021 and BNXUSDT absent in February 2023; this membership check is not an exposure calculation.

The event schedules and remaining settlement evidence are documented in [PRX identities](prx-identities.md) and [settlements](settlements.md). Nonmissing frozen bars, continuing public funding records and successor tokens do not establish executable old-contract prices or a final settlement cashflow. The PRX six-outcome problem is structural under the original 25-observation and fixed-beta rules; no successor splice can complete those measurements.

The registered exposure audit is an independent diagnostic of historical allocation assumptions, not a performance replay. At this review stage, **only synthetic tests have run**. No original signal panel, allocation book, PnL, SR, P0/P1/P2 statistic or revised strategy outcome has been computed by the new audit.

## Required lifecycle semantics

The existing accounting core checks returns for desired nonzero notionals. An explicit flat target assumes that the prior opening mark was already valid. Consequently, replacing post-closure returns with missing values would still allow an incoming position to disappear at an unverified opening mark. A lifecycle check must precede target application.

The committed exposure charter fixes the clock: an hourly close with open label `t−1h` becomes available at `t`; allocation `W[t]` is requested then and valued at `t+1h`. A bar's millisecond close label cannot establish that an order was executable before information availability.

- At an exact closure boundary `t`, incoming prior-row allocation remains unresolved even when `W[t]` is zero. No pre-event exit is invented at `t−1ms`.
- A nonzero allocation over an interval containing an intrahour closure requires the unestablished terminal event cashflow. LUNA's 15:30 closure lies inside the 15:00 bar.
- A subsequent nonzero request is recorded as a post-closure assumption. The original weights are retained, including natural later timer expiry; the audit does not synthetically flatten them.
- New targets and increases in target allocation on or after the announced entry restriction are counted, including those after closure. Pre-closure counts are supplied separately. Unchanged target weights do not establish unchanged contract quantities: NAV and price drift are not reconstructed in this audit.
- An allocation flattened at a genuinely earlier decision time is distinct from flattening at the event boundary. The absence of a lifecycle flag still does not prove fill quality, full coverage or settlement readiness.

Any future executable guard needs actual incoming position state, admissible opening/valuation marks and contract-event ordering. If an unreconciled position crosses a closure, it must remain unavailable even if a later target is flat. The present diagnostic supplies evidence about requested allocations only; it does not implement a settlement extension or prove actual holdings.

## Source and output controls

The recovery-only registration at `78b4fe9` and timestamp scope addendum at `6f84e4b` were reviewed independently. The committed gate, addendum SHA256 and inventory SHA256 agree. All 49 symbols and 6,832 declared internal symbol-hours match the timestamp inventory, and the September 9 gate is unchanged. The recovery registration authorizes no strategy metrics. The 250 MB download budget applies across documentary and market-data receipts, rather than separately to each downloader.

The separate exposure registration was committed at `c11527b`. Its implementation is [audit_lifecycle_exposure_2026_09_10.py](../../scripts/audit_lifecycle_exposure_2026_09_10.py), with [synthetic tests](../../tests/predlab/test_lifecycle_exposure_audit.py). It:

- defaults to a dry run that reads no original input and creates no output state;
- requires the committed exposure gate and clean executable sources before an exclusive start marker;
- verifies all 217 original hourly hashes before reading and again before publication, together with the frozen symbol list, universe, inventory and official event receipts;
- pins the original liquidation-fade result SHA256 `30a8629fa9214ac031d8a642f719bccdff60c6f1a0b473b365e699dd79f6837a` and reused construction source at `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`;
- reads only close and quote-volume inputs, with the development cutoff applied in the Parquet read; uses log differences only inside the unchanged cascade signal;
- retains the original six cells, five events per cell, sorting, membership mask, warmup, rolling feature settings, timer resets and slot cap;
- preserves missing-input behavior for reproduction while separately reporting original input coverage and allocation uncertainty;
- writes six nonfinancial records to the exclusive `forensic-ledger.jsonl` inside the exposure output namespace, with a hashed result; the central financial trial ledger is neither appended nor counted, and its before/after hash is checked.

No broad public-price or strategy run is invoked by this wrapper. Global reconstruction failure retains all six cells and all five event records as unavailable. Complete serialization precedes either forensic-output write. A low-level interrupted disk write still needs manual provenance review; an existing start/output namespace prevents blind re-execution.

## Verification and remaining limits

The initial 13 tests failed because the audit was absent. An additional restriction regression showed that post-closure new requests were omitted from the restriction count; this was corrected without changing original weights. Six further failing regressions required the dedicated forensic ledger, denominator retention, pre-serialization and repeat refusal. **27 focused tests pass in 1.09 seconds.** Red and green logs are preserved under [verification](verification/).

The tests cover exact-boundary incoming exposure, intrabar closure, pre-event flattening, post-closure requests, restriction reporting, nonfinite allocations, incomplete clocks, frozen event timing, original-input hash/path controls, registration refusals, dry-run behavior, filtered development reads and immutable forensic writing. No empirical result is claimed from them.

The audit is bounded to five registered events. Earlier same-ticker incarnations, other terminations, unknown funding/settlement cashflows, original internal gaps and price/NAV-driven order-quantity changes remain limitations. An absent flag is never a readiness certificate. Source freeze and the explicit execution instruction remain required before the single original-input reconstruction.
