# Proposed investment contract

**Draft numerical assumptions, not accepted user preferences or an executable gate.**
The September 15 request authorizes design and state recovery. Before financial
experiments, record the user's investment choices and resolve this contract.
Changing a draft now is legitimate; changing a frozen gate after outcomes is not.

## Capital, horizon and tolerances

| Item | Proposed primary assumption | Meaning / unresolved detail |
| --- | --- | --- |
| Capital | $1,000; independent $10,000 scenario | All initial capital available on day zero; no later contributions or borrowing. Recompute lots, fixed charges and depth separately. |
| Spending currency | USD provisionally | Confirm USD/EUR/CZK; translate cashflows and FX costs into the chosen currency. USDT is not automatically a dollar. |
| Investment horizon | 365 days | No required interim withdrawal; this is distinct from the length of evidence needed to estimate performance. |
| Useful absolute net cash profit | $50 at $1,000; $500 at $10,000 per 365 days | 5% of initial capital, measured after modeled implementation costs. Confirm that these are useful cash amounts. |
| Useful incremental cash benefit | $20 / $200 per 365 days | Proposed 2% benefit over each eligible simple benchmark; a separate preference from absolute profit. |
| Maximum drawdown | 20% of prior liquidation NAV peak | Include initial NAV, fees, gaps and terminal conversion; not a guaranteed stop-loss fill. |
| Maximum stress loss | 35% of total capital at each stress origin | Apply the scenarios below throughout the path; separately report drawdown from original capital. |
| Instruments | Unlevered BTC and ETH spot; accessible cash | No short, perpetual, option, lending or staking book in the initial four tests. Those require a later explicit scope choice and inherited-budget review. |
| Venue | Binance only if product/account applicability is established | Public API reachability is insufficient. No credentials/private endpoints needed for this design. |
| Operational burden | At most one scheduled decision per month, two assets, no intraday discretionary response | Continuous prices may be needed for honest risk measurement; this does not imply frequent trading. |
| Cash location | Majority outside exchange/crypto credit risk, if accessible | Model transfer time/fees and prefunding explicitly. Keeping everything in exchange USDT cannot be called safe cash. |
| Taxes and labor | Net of implementation costs, pre-personal-tax; labor shown separately | Confirm whether useful profit must instead be after tax and time cost before freezing. No tax assumptions silently treated as zero. |

The capital boundary includes bank cash assigned to the strategy, idle money,
prefunded venue wallets, fee assets, transfer balances and unusable dust. A phased
entry strategy starts with the full capital committed; it cannot divide profit
by only the money already invested. No annualization of a short favorable episode
can establish the annual cash target.

## Stress contract proposed for every candidate and benchmark

Evaluate the entire account at every daily state and every trade/transfer event.
Revalue quantities, cash, fees and access under: (a) simultaneous BTC/ETH -50%;
(b) simultaneous -80%; (c) BTC -50%, ETH -90%; (d) +100% crypto followed by -60%,
including any intervening monthly rebalance; (e) a seven-day trading/transfer
outage during -50% crypto, with spread/impact five times primary on reopening;
(f) stablecoin -20% with redemption unavailable for 30 days; and (g) complete loss
of assets at one exchange/custodian. Include a combined -50% crypto/-20%
stablecoin/outage scenario, avoiding double-counting already lost balances.
Specify the within-scenario clocks and recovery prices in the experiment contract.
No assumed emergency stop execution or instant cash transfer.

These are deterministic adverse scenarios, not probabilities or worst possible
loss bounds. Report maximum drawdown, worst rolling 30-day loss, terminal loss,
exposure drift, custody concentration and liquidity lockup. The 35% proposal may
make an all-on-exchange implementation unacceptable even if its market exposure
is small. Such a result is implementation/risk infeasibility, not absence of a
return mechanism. No strategy can guarantee the proposed drawdown limit.

## Benchmarks: same money, clocks, costs and available instruments

Freeze these ten identities, with identical start/end dates and terminal exit:

| ID | Recipe | Role |
| --- | --- | --- |
| B0 | Cash with zero nominal yield | Transparent floor; not an assertion about inflation or deposit safety. |
| B1 | Cash in the user's accessible low-risk vehicle, net of its charges | Primary opportunity set; if no vehicle is established, the implementable comparison is unavailable. |
| B2 | 100% BTC buy-and-hold | Full directional exposure context. |
| B3 | 100% ETH buy-and-hold | Full directional exposure context. |
| B4 | Initially 50% BTC / 50% ETH, buy-and-hold | Simple crypto basket context. |
| B5 | 25% BTC / 75% cash, reset monthly | Primary simple allocation. |
| B6 | 50% BTC / 50% cash, reset monthly | Higher-risk context; eligible only if frozen risk tests pass. |
| B7 | 12.5% BTC / 12.5% ETH / 75% cash, reset monthly | Primary diversified allocation. |
| B8 | 25% BTC / 25% ETH / 50% cash, reset monthly | Higher-risk diversified context. |
| B9 | Initially 25% BTC / 75% cash, buy-and-hold | Primary minimal-trading allocation; drift stays visible. |

Cash legs use B1 economics when admitted. Fixed 0%, 3%, 5% annual cash-yield
scenarios may additionally describe opportunity-cost sensitivity; they are not
quotes or selectable primary rates. There is no best-cash-rate choice after
results. Use each date's admitted information/terms, not today's yield backfilled.
If B1 is unavailable, show conditional results but withhold an implementable pass.

Primary comparator set is B0, B1, B5, B7, B9. Each must independently satisfy the
same capital/access, 20% drawdown and 35% stress limits to be a feasible
alternative; retain the others with reasons. Report every contrast even when a
benchmark is infeasible. B2/B3/B4/B6/B8 remain compulsory context: outperforming
their returns at substantially lower exposure is not required, and reduced loss
from merely holding more cash is not evidence of timing skill.

Candidate and simple controls start from equal capital, use identical cash
economics, fees, custody and transfer models, and have the same information
clock. No ex-post volatility scaling. For timing rules, add a predeclared 25%
static exposure control (B5/B9) and causal exposure/risk attribution; average
realized exposure matching is diagnostic only. Report mean/max crypto exposure,
BTC/ETH beta, turnover, active/cash days and cash profit by source.

## One primary decision rule, two separate claims

For capital C, define P = liquidation wealth at day 365 minus C. Define
D(b) = P(candidate) - P(benchmark b), both including every committed dollar.
Opportunity cost is represented by D, not subtracted a second time from P.

The proposed adoption rule is conjunctive:

1. Accounting, point-in-time data, access, all capital, execution and independent
   review pass; no material unknown held value or cash term remains.
2. Candidate satisfies the fixed drawdown/stress constraints and operational limits.
3. Absolute profitability: observed 365-day P >= $50/$500 and the simultaneous
   one-sided 95% lower bound on expected 365-day net profit is above zero.
4. Benchmark value: observed D >= $20/$200 against **every feasible member of
   the frozen primary comparator set**, and simultaneous one-sided 95% lower
   bounds on their expected D are above zero. Missing feasibility evidence cannot
   be used to exclude an inconvenient comparator.
5. Doubled execution-cost sensitivity preserves positive P and positive D for
   those comparators and still satisfies risk limits. This is robustness, not
   a substitute primary scenario.

Report the absolute and incremental verdicts separately even if only one passes.
If annual evidence includes several non-overlapping 365-day episodes, use their
mean cash outcome for the effect thresholds, show each episode and loss
frequency, and apply risk constraints to the complete path. Exact estimator,
dependence treatment and error allocation must be frozen before any scoring.
Annualized Sharpe, CAGR, Sortino and win rate are descriptive only. They cannot
rescue a failed primary gate. A riskier passive benchmark can earn more without
meeting this mandate; that opportunity cost must be visible.

Development promotion is descriptive: complete and independently checked
cash/source evidence, observed absolute/incremental effect floors, risk limits
and doubled-cost robustness must pass on the predeclared development panel.
Confidence-bound adoption is not required or claimed on those spent windows.
Treat each fixed window as a separate reported cohort; development ranks use
the mean of complete, predeclared 365-day episodes, without dropping a bad or
unavailable cohort. If that full comparison is unavailable, promotion is blocked.
Independent prospective power/feasibility admission must then pass before a
selected candidate enters confirmation.

If several development candidates meet that promotion screen, select the largest
minimum D across the feasible primary benchmarks, using only predeclared
development data. Differences below $10/$100 are ties: prefer lower annual
turnover, then fewer policy rules, then fixed map rank. Select at most one per
capital; all tested candidates remain in the selection history. Development
selection itself never validates a strategy. If none qualifies, cash/simple
allocation can remain the practical reference without being advertised as a
newly validated profitable strategy. H1's simple allocations receive full
implementation, risk and absolute cash-profit reporting as benchmarks. They
need not demonstrate superiority to themselves. The initial four-candidate
program makes no confirmatory superiority claim for a benchmark; promoting a
benchmark as a new selected strategy would require a separately registered
claim and budget decision, not silently adding a fifth candidate.
