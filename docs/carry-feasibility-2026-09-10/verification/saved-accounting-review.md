# Saved accounting and interpretation review — September 10, 2026

**PASS; no accounting or reporting blocker identified.** Review used only the retained capture, entry records,432 measurement rows, independent `saved-review.json`, `screen-summary.json` and `RESULTS.md`. No quote was requested, policy rerun, scenario added or measured artifact changed. The prior independent exact-rational checker passed for execution source `62bcf8bf4bdb2c57e8b78d4443427863e287d692`,48 entries,432 scenarios and16 requests, with absolute arithmetic tolerance1e-20 and the original820-row financial ledger unchanged.

All12 reference-table lines in `RESULTS.md` match the corresponding saved net cash/full-budget return/simple-annualization strings at the displayed precision. Each of the four preregistered screen groups retains its exact9 required observations; every group has0/9 positive net cash outcomes and correctly reports that the necessary screen did not pass. More broadly, **all432 fixed modeled outcomes are negative** under the registered fee and terminal scenarios. This is evidence about these observations and assumptions, not a finding that dated carry can never be profitable.

All48 entry cases are budget-limited, not displayed-depth-limited. They respect the combined spot-purchase, cash-entry-fee and total-reserve budget; the remaining cash stays in terminal NAV and the return denominator remains the entire1,000/10,000USDT. No futures entry principal is credited. Spot purchase commission is deducted in base units and the hedge uses the retained net coins. All48 cases have a strictly positive lot-rounding residual and correctly set exact matching/executable admission false; the residual is valued at terminal spot sale rather than deleted.

The terminal cash identity includes spot sale net of its fee, signed fixed-quantity futures settlement, expiry fee, initial spot cost and cash future-entry fee exactly once. Reserve principal is released, not expensed. The futures-reserve flags identify all72 one-third-reserve cases at the doubled terminal index as insufficient without external liquidity. None of the216 full-reserve scenarios has a negative modeled terminal reserve, but this does **not** certify maintenance margin or intrahorizon liquidation survival. The report makes that distinction and does not call lower collateral a risk reduction.

The stated limited neutrality is appropriate. The small excess spot creates residual directional exposure; notional-based terminal fees and the adverse spot/index mismatch also make net cash dependent on the hypothetical terminal level. Neutrality of the ideal pre-fee matched-quantity payoff cannot be substituted for those actual scenario cashflows. The report correctly labels fees as assumptions, settlement/account applicability as unresolved, capital as already-availableUSDT rather than verified fiat conversion, cash benchmarks as illustrative and spot freshness as unproved where timestamps are missing. No scenario is adopted or described as an actual fill.

Observed pair request/receipt spans remain below0.335s in the six retained asset/snapshot pairs, and the saved conservative future-event ages remain below612ms. Every pair retains `spot_event_timestamp_unavailable`. Those timing observations support the declared conditional admission only; they do not establish simultaneous fills or a future sale aligned with the settlement index.

Reviewed evidence hashes:

- Capture manifest: `67d85e098dc181b09d0f42cf95c03aceced79cd63dd1f8237959641f592c77ff`.
- Entry records: `cedaf343c7ec0fd529a4afa5e927344f3218f1a29c2240efc3adee016606d89f`.
- Measurement ledger: `7624f2809c604e51c72726fc375c3d27785675cc2992f031a913c2df813aa985`.
- Screen summary: `3f066628f8accb9fe9bc2de7352fd690336dc17ce293f959ac60b90b3dd74ca3`.
- Initially reviewed report: `ff349ee952c3176c050f10edf320e2c77dcc0f37b6460851c3a6e3bfb10dd31f`.

The root was informed of the432/432 negative outcomes and72 terminal-reserve shortfalls for possible inclusion in the final report. Such a sourced reporting addition does not change the retained measurements. The conditional feasibility stage can close without starting a strategy evaluation, paper account or execution workflow.
