# Independent practical-episode review: superseding engineering disposition

September 11, 2026. **PASS for the finite offline accounting and batch prototype, including the measured full-length invented episode.** This report supersedes the practical-readiness inference in `options-policy-implementation-review.md`. That earlier source-bound report and both subsequent failure proofs remain unchanged. No market input, network call, empirical claim, registration or research ledger was created or modified by this review.

Reviewed source SHA256 values:

- `options_policy_engine.py`: `255892184fa302687f43ac22195840dc050491f7d520b063e851dc1941826168`.
- `options_policy_batch.py`: `6daad0e65e1806b9389ee5ed871997c0f80dd4d4b4879c1cbf50696e5fb29e23`.

## Preserved failures and correction

The initial arithmetic bound prevented uncontrolled integer serialization but rejected all eight ordinary 1,057-record paths. The first size proof consequently contained no complete books. Its byte-only success flag did not establish practical eight-book feasibility. That failure remains in `options-policy-size-proof.json` and its guard report.

Replacing weighted-average basis removed one source of rational denominator growth. The next version still failed all eight ordinary paths when summing exact simple NAV returns for a noncash diagnostic. The second failed proof remains in `options-policy-size-proof-v2.json` and its guard report. Neither failure was a financial experiment or evidence about option profitability.

Current monetary accounting remains exact. The linear perpetual valuation offset is `A=-sum(change_in_quantity*execution_price)`, accumulated across flat periods and re-entry. Marked trading PnL is `A+held_quantity*mark`; when flat, cumulative trading PnL is `A`. Perpetual equity includes the initial reserve, signed funding, fees and this trading PnL. The offset is explicitly uncredited and is never presented as short-sale proceeds or withdrawable wallet cash. The reserve/funding/fee component alone is likewise not claimed to be actual cash available while the position is open. Actual realized-cash decomposition while open is unavailable. Terminal cash includes the full cumulative offset after the hedge is closed.

The arithmetic-return sum now uses an explicitly labeled 60-significant-digit, ROUND_HALF_EVEN approximation solely for the convention diagnostic. Monetary quantities, executions, fees, funding, wallets, NAV and terminal cash retain exact rational arithmetic. The 4,096-bit scope guard remains; no integer safety limit or monetary precision was relaxed.

## Independent full-length reconstruction

`check_options_policy_direct_independent.py` and `options-policy-direct-independent-review.json` verify eight invented asset/capital/cost cases, each with 1,057 hourly points and 132 credited funding events. The checker uses incremental PnL from previously held inventory times the mark change, plus execution-price slippage, independently of the engine's cumulative offset. It performs **35,952 exact cash comparisons across 8,456 NAV points**, including funding-before-action inventory, signed hedge changes, option fees and liabilities, separate perpetual equity and final cash. Every comparison passes.

An independent Decimal100 calculation agrees with each Decimal60 arithmetic-return diagnostic within `1e-55` on these paths. The log-return sum agrees with the terminal NAV ratio's logarithm within `1e-11`. These are convention checks, not trading PnL or economic inference. Earlier independently checked timing, partial field availability, tri-state deficits and separate-wallet valuation corrections remain applicable to the unchanged batch and retained engine logic.

## Measured resource evidence

`options-policy-size-proof-v3.json` binds the reviewed source hashes and retains all eight complete cases. Each case has 1,057 records and 1,057 trades. The compact serialized books total **6,845,005 bytes**. The fixture includes sixteen raw bodies of 8,192 bytes per batch; its projected 1,057 batches of receipts and assemblies plus the eight books total **206,969,986 bytes**. The report separately records the byte bound, eight-case completeness and combined practical-fixture verdict, all passing.

`options-policy-size-guard-v3.json` records exit zero, no limit reason, **1.02653 seconds** and **46,088,192 bytes sampled aggregate RSS**, under 120 seconds and 512 MiB. Its 20 ms sampling qualification and separate individual-child `ru_maxrss` remain explicit. This is an observed engineering resource envelope for the invented fixture.

This proof does not cover every admissible numeric path or actual API payload, whole historical admission cost, metadata/funding retention, transport, durable storage or a full empirical lifecycle. It does not prove a universal 512 MiB episode bound. A future runner must enforce total serialized bytes incrementally, handle arithmetic-scope errors as retained unavailable cases and preserve exact attempted denominators. A future collector also needs monotonic clock/timeout proof, durable raw retention, restart and duplicate handling, rule/selection admission and a concrete missed-decision policy.

## Disposition

The finite offline ledger and batch preparation is accepted. Both ordinary full-episode failures were diagnosed and corrected without market observations or weakened monetary accounting. The superseded failures and earlier source hashes remain part of the engineering evidence.

The next action is a concrete prospective capture and lifecycle design decision. This review admits no new quote probe, options budget extension, unattended collector, account operation or financial episode. Future data and durable collection requirements remain explicit dependencies; this acceptance does not characterize the entire research program as exhausted or establish positive expected returns, low realized beta, actual margin safety or account affordability.
