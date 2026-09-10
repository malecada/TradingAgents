# Settlement and funding accounting extension — September 10, 2026

**The event accounting engine is implemented and verified with synthetic inputs.** It tracks signed contract quantities, funding payments at their own timestamps, final valuation, settlement fees and permanent closure of the original contract. Verification passed **234 tests: 61 new synthetic cases and 173 existing accounting, lifecycle and recovery regressions**. This is engineering validation; no historical strategy result was recomputed or admitted.

Source: `tradingagents/event_accounting.py`; tests: `tests/test_event_accounting.py`. The pre-implementation design was committed at `3ef9f3b`. Baseline `d9d6a3ede6d80f4c46024ea27b296860e51cd7db` and the frozen legacy engine remain preserved. Branch: `feature/terminal-event-accounting`.

## Implemented behavior

- Quantities remain fixed between declared target trades. Linear mark PnL uses price differences and the explicit contract multiplier. Terminal valuation applies to incoming quantity before a same-time flat target; settlement commission is charged once, and the old identity cannot reopen.
- Funding uses the quantity held at the event and the event's own mark/rate. Its valuation basis does not overwrite the portfolio mark. A payment after closure has no held quantity to charge. Simultaneous external events require an explicit unique sequence.
- `events_before_targets` is the supported boundary policy and must be supplied. The full regular UTC boundary clock is retained. Final-boundary events enter the last period; no final-boundary target is accepted. Initial entry and later maintenance fees belong to their opening periods.
- Missing terminal price, fee, source or expected funding inputs fail when the book requires them. An explicit independent funding calendar is required whenever funding is included. `funding=None` records intentional exclusion; a daily summed funding panel is not an event input.
- Contract identity, lifetime, reduce-only restriction, multiplier, sizing step, collateral, fee basis, cash rounding and price/source references are explicit. Successor contracts have separate quantities. Reductions during a restriction are checked in units after NAV and price drift.
- The output contains period returns, quantities at every boundary and a ledger with incoming/outgoing quantities, price/cashflow basis, multiplier, event order, PnL, funding and fees. Provenance references are retained in metadata; their presence does not authenticate a source.

## Numerical verification and review

Hand-derived examples include symmetric long/short settlement, zero terminal/intermediate marks, funding before/at/after closure, final-boundary settlement, missing inputs, complete calendars, separate successors and position restrictions. An initial NAV of 100 with prices 100→110→110 and a 1% fee ends its first period at 109 and its second at 108.99, preserving the initial entry fee and charging only actual maintenance turnover.

Independent accounting and execution reviews reproduced three related numerical defects during implementation: flooring an already rounded floating-point target could lose a valid lot; floating-point NAV drift could trigger an unnecessary one-lot reduction; and the same drift could falsely reject unchanged continuous quantity during reduce-only maintenance. Each has a retained failing regression and a verified fix.

Sizing now multiplies/divides original inputs using Decimal before lot flooring. Because preceding NAV remains floating point, lot ratios within `8 * machine_epsilon` relative tolerance of an integer are snapped to it before flooring. The same narrow relative equality policy preserves unchanged continuous quantity during restrictions. Real undersized targets still floor, and real quantity increases/sign reversals remain rejected. This tolerance is exposed in result metadata. Cash rounding is independently declared as unrounded model arithmetic, toward zero, half-up or half-even; no historical venue rounding rule is inferred.

The final independent numeric review passed four targeted regressions and six additional signed-sizing checks, with no unresolved prior finding. The complete 234-test parent run is retained in `verification/final-green.log`; earlier failure/fix logs and review scope are retained alongside it. The supplementary settlement-report review received after the earlier cycle is preserved as `verification/late-settlement-report-review.md`; it does not alter that completed cycle's manifest.

## Preservation and limits

The offline preservation check verified all 2,476 prior local recovery/replay/settlement artifacts and all 222 referenced original input hashes. Prior scripts, shared bar accounting, xsect engines, gates, results and evidence reports are unchanged. The financial ledger remains 428,150 bytes with SHA-256 `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791`. Verification details are recorded in `verification/preservation.json`.

This API supports USDT-linear arithmetic with absolute-notional fees. Inverse products, other fee bases, alternative boundary orderings, actual fill reconstruction, margin/liquidation, slippage and capital-charge conventions are not implemented here. An intrabar ledger balance contains the most recently marked value of each contract; it is not a fully synchronized margin observation. Positivity is checked at fully valued boundaries and after target fees.

Legacy carry still uses its documented daily opening-notional funding approximation. Momentum and liquidation-fade retain their registered funding exclusions. No existing wrapper is silently redirected. A future empirical adapter must explicitly choose this API, preserve the original cohort/clock/decision convention, admit the necessary event data and capital-charge/execution treatment, and use a fresh committed registration before any replay. Existing overlay helpers consume the legacy input contract and are not an event-accounting replay interface.

**Current research status remains two conditional measured failures and 22 unavailable accounting cases; zero validated strategies.** No model fit, spent holdout reuse, manuscript change, canonical-main merge, VPS verification or deployment occurred.

## Provider request

The prepared request remains at `docs/settlement-evidence/provider-request-draft.md`. The official actionable route is [Binance Support Chat](https://www.binance.com/en/chat?sourceEntry=33). The current [visitor-support guide](https://www.binance.com/en/support/faq/detail/4ec71332039d4b45ab30e660895423c3) allows contact without login, using an email address or phone number and transfer to customer service.

Submission could not be performed in this session: CUA reported no available browser, the chat requires JavaScript, and no callable Binance support connector exists. No contact identifier was supplied or entered, no public support email was verified, and no message was sent. This is a tooling/contact-data limitation, not a requirement to reapprove the prepared request. The verified support links are route discovery only, outside the completed settlement-data acquisition gate; no market data was fetched.

The next evidence requirement is a provider response or relevant retained account export establishing the original BZRX/LUNA/BNX settlement prices, fees, event ordering and funding cashflows. These inputs remain unknown; passing synthetic tests does not supply them. Operational consolidation and read-only paper/VPS verification remain separate pending work.
