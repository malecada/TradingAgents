# Decision 14 — positive WBETH cash, insufficient relevance

The frozen wbeth-book-20260911 completed once from
04e1fa48336bdb10e6a9795a91e24a72526c9ef7 after verified remote freeze.
Eight complete cells, zero unavailable, two immutable outputs total931,662bytes.
The structural receipt verifier passes. Independent raw Decimal cashflow and
manual HAC reconstruction passes19,428 comparisons, maximum absolute difference
5.05e-12, including728daily NAV rows,32price stresses and12raw receipts.
The checker and reports are retained in reviews/wbeth-book-review.{json,md}.
The guard records9.339seconds,436,752,384bytes sampled aggregate RSS and no
limit reason under512MiB/120seconds.

| Initial USDT | Base cash PnL | Stressed cash PnL | Base simple annualized | Stressed simple annualized |
|---|---:|---:|---:|---:|
| 1,000 | +2.02025468 | +0.86674884 | 0.8103% | 0.3477% |
| 10,000 | +23.01003374 | +9.80235778 | 0.9229% | 0.3932% |

All four primary books earn positive conditional cash over91days. None reaches
the frozen3% full-capital relevance screen, and annualization is descriptive,
not a prediction that this episode repeats. The positive-cash component and
failed relevance component are distinct. No investment preference was lowered.
The four same-quantity zero-funding books also earn small positive cash:
1.23054780/0.07704195 at1,000 and15.08789481/1.89275388 at10,000 (base/stress).
They remove funding only; they do not identify pure validator yield.

## Diagnosis and uncertainty

At1,000 base, same-quantity frictionless price PnL2.557006 plus observed short
funding0.78970689 is reduced by slippage0.27897099 and fees1.04748722. The
resulting2.02025468 cash profit includes the offsetting WBETH spot loss and
ETH perpetual gain, principal and collateral release. No opportunity-cost
charge is included. Even that frictionless same-quantity price-plus-funding
scalar is below the separate3%91-day cash benchmark7.47945205. The corresponding
10,000 base scalar36.29344993 is below74.79452055. Thus removing modeled fees
alone cannot meet the frozen relevance condition at these fixed quantities.
There is no newly optimized financing/allocation counterfactual.

Measured joint BTC/ETH betas and their HAC7 intervals are small and satisfy the
conditional descriptive bounds. Observed primary drawdown is at most about0.257%.
True contractual WBETH ETH delta is unverified; market-value mismatch is not
substituted for the net-base-delta gate. Actual fills, historical lots/fees,
account applicability and liquidation remain unavailable. Chosen depeg and
common-price stresses are illustrations, not loss bounds. The isolated10%
WBETH markdown loses about4.1–4.3% of all capital; the50% markdown loses about
20.1–20.2%, despite a nearly matched market-value hedge initially. That visible
linked-asset tail risk is separate from the small historical beta. Expected-return
confidence and power remain unavailable for a single holding episode;91daily
marks are not91independent repeat trades.

The result weakens the claim that ordinary assumed round-trip costs alone
explain every neutral carry failure: this distinct linked-asset book remains
cash-positive even under stressed costs. It does not establish durable expected
profit, pure staking attribution, the frozen relevance level or graduation.

## Decision and next action

Close this fixed episode's3% relevance claim while retaining its small positive
cash finding. Do not increase allocation, lower fees, refit the hedge or select
another date to rescue it. Contract-ratio provenance could refine risk attribution,
but does not change the recorded cash and currently does not outrank the saved
news availability gap. WBETH has consumed two new questions, also charged to
MAProws3/8. The third initial row8 question is the separately proposed seven-path
metadata-only news inventory; its one-claim technical family is not a fresh
three-trial alpha allowance. Freeze and execute it only after synthetic and
independent source/privacy review. A parallel map coverage review will identify
remaining affordable distinct questions. Zero strategies validated; research
remains active/incomplete, not exhausted.
