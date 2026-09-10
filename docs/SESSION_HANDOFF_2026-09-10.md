# Session handoff — September 10, 2026

The user requested a memory update and will resume in another session. This is a completed research checkpoint, not authorization for background work, a scheduler or another experiment.

## Objective and preferences

- Find positive net returns with little exposure to overall crypto prices.
- Capital: approximately $1,000 initially; potentially $10,000 if the approach works.
- Available venue according to the user: Binance; possibly Bitrue. Exact account product access has not been verified.
- Historical settlement recovery and paid data for the 22 blocked cases are explicitly deferred. The earlier support request was not sent; no further provider contact is pending.
- The approved sequence was economic feasibility, full hedge accounting example, a separately registered strategy evaluation only if justified, then paper execution after prerequisites. The first two stages are complete. The conditional later stages have not been admitted.

## Where to resume

Use `/home/malecada/master_thesis/TradingAgents-audit-fixes`, branch `research/dated-carry-feasibility-2026-09-10`. The last research-results commit is `52508eaf8b72a7952e18ba3ec99ee30541d023e9`; it was pushed and verified equal to remote HEAD with a clean working tree before this memory-only checkpoint. Use `git status` and `git log` to identify the subsequent handoff commit rather than treating the research-results hash as the current HEAD forever.

Root `/home/malecada/master_thesis/AGENTS.md` and the canonical audits govern. Original `TradingAgents` and `TradingAgents-predlab` worktrees/data remain provenance. The consolidated checkout's `THESIS_FINDINGS.md`, gates and ledgers contain current corrections. Older memory files and earlier state summaries are historical where they conflict with the September 9–10 audits and Sections 88–98.

## Latest completed result: dated BTC/ETH cash-and-carry

- Registration: `57149c6bfeefe3a1a76e5103d21dbd598d10080c`; reviewed execution source: `62bcf8bf4bdb2c57e8b78d4443427863e287d692`. Both preceded the single public capture and were pushed before execution.
- The earliest eligible conventional linear USDT expiry rule selected BTCUSDT_260925 and ETHUSDT_260925, expiring September 25, 2026 at 08:00 UTC. Sixteen public requests retained metadata/clocks and three scheduled quote batches on September 10 at 16:11–16:12 UTC.
- All 48 entry cases and 432 terminal sensitivities are retained and calculable. **All 432 modeled cash profits are negative; all four necessary asset/capital screens fail.** These are correlated arithmetic scenarios, not independent strategy trials or historical returns.
- At base assumed fees, full futures-notional reserve, unchanged terminal index and aligned spot exit, profit through expiry is BTC −0.58 to −0.55 / ETH −0.90 to −0.80 USDT at 1,000 capital; BTC −6.49 to −6.05 / ETH −9.90 to −8.26 at 10,000. Budgets assume USDT already on venue, not verified fiat conversion proceeds.
- In those reference cases, the matched entry premium is roughly 10–18bp versus approximately 30bp modeled four-fee drag. Larger capital does not repair proportional negative economics. All 48 entries are budget-limited; larger future sales consume deeper bids.
- All 72 one-third-reserve scenarios with doubled terminal index have insufficient terminal futures reserve. Full-reserve cases stay terminal-positive within the grid, without proving maintenance-margin compliance or survival throughout the holding period.
- Actual commissions/fee assets/rounding, legal settlement-fee treatment, contract/entity applicability, account product access, spot freshness and margin survival remain unverified. Public depth is not proof of fills. Bitrue's eligible dated-product availability remains unverified; perpetuals were not substituted.
- The pure cash/base-unit calculator and synthetic hedge example are complete; the combined pre-result suite passed 127 tests. Exact-fraction reconstruction independently verified 48 entries and 432 cashflows without importing the calculator. Source, saved accounting and final prose reviews passed. Synthetic positive example profits use invented prices and are not market evidence.

Canonical [decision report](carry-feasibility-2026-09-10/INTERPRETATION.md), [generated results](carry-feasibility-2026-09-10/RESULTS.md), [sources](carry-feasibility-2026-09-10/SOURCES.md), [synthetic accounting](carry-feasibility-2026-09-10/verification/accounting-example.md) and [delivery checks](carry-feasibility-2026-09-10/verification/delivery-verification.json). Findings: Section 98.

The separate measurement ledger is `data/carry-feasibility/2026-09-10/measurement_ledger.jsonl`, SHA-256 `7624f2809c604e51c72726fc375c3d27785675cc2992f031a913c2df813aa985`. Capture manifest SHA-256: `67d85e098dc181b09d0f42cf95c03aceced79cd63dd1f8237959641f592c77ff`.

## Earlier work that must not be lost

- The system audit and local corrections repaired accounting, missing-data, causal-data, provenance and execution defects. Engineering completion is separate from strategy validation; corrected measurements retain remaining source assumptions.
- Of 24 momentum/carry/liquidation configurations, **two H6 liquidation-fade cases are conditional measured failures and 22 remain unavailable**: 12 momentum, six carry, four liquidation-fade. Unavailable is not a confirmed kill. Authentic recovery supplied 5,568 internal hourly observations across 47 symbols; unknown terminal cashflows still prevent the deferred cases. PRX remains a qualified failure; NLST4 retains a descriptive ranking association but fails economics. See findings Sections 89–91.
- The fixed factor correction retained 18 configurations: seven positive primary Sharpes, all 36 BTC/ETH sleeves eventually halted, with proxy prices and assumed funding. Saved volume forecasts show qualified error improvements but no standalone trading edge. See Sections 95–96.
- The fixed sizing/stop comparison retained 72 policy identities and 576 sleeve books. Daily sizing fixes the nominal risk-budget drift but improves returns in only 7/18 configurations. Waiting improves 14/18, including seven smaller losses caused by almost no long-only exposure. Four previously negative long/short configurations become positive under four cost assumptions, but no winner, adoption gate or fresh validation was established. These exposed directional comparisons are not automatically suitable for the user's market-neutral objective. See Section 97 and `docs/risk-policy-2026-09-10/INTERPRETATION.md`.
- **The original financial ledger currently has 820 rows**, SHA-256 `4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927`. Dated-carry work appended no financial trials and preserved all 40 earlier gate objects. Never delete superseded outcomes, adjust gates after results or treat a spent holdout as fresh.
- Earlier spot/perpetual carry was already tested and failed; it is not an untouched lead. The combo-C1 April 2025–July 2026 holdout remains spent for liquidation, carry, momentum and value.
- Local event accounting, operational integration and funding-capture improvements are implemented. No new VPS deployment, paper start or scheduler was made in the recent research cycles. The last read-only VPS inspection found legacy code and no v2 journals/funding store; do not infer current deployment from local readiness.
- Existing value-reversal snapshot timing is no earlier than September 18, 2026; the deferred LLM cycle is approximately January 2027. These retain their own registrations and need readiness checks before execution. This handoff creates no automatic continuation for either.

## First action next session

Read this handoff and the latest decision report, check the current branch/status, and review the closed-program ledger before proposing any lead. **No next strategy has been selected and no evaluation, paper start or automatic quote refresh is pending.** The next substantive decision is one affordable, distinct research question consistent with the user's market-neutral objective; do not present the rejected September 25 setup as ready to trade or rerun its collector to search for a better quote. A new empirical question requires a new committed charter/gate before outcomes, with exact costs, account applicability, margin/liquidity behavior, validation dates and adoption criteria where relevant.

Stop after saving this checkpoint. Zero validated strategies remain. The negative current measurement does not establish permanent absence of every possible dated-carry opportunity.
