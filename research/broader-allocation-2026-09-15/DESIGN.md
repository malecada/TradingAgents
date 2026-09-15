# Proposed investment contract

**Capital baseline confirmed at $10,000; larger capital may be considered if needed.
The annual net-return target is at least 10%; 30% maximum drawdown and 50%
stress loss are accepted research limits. Other contract details remain open.**
The September 15 request authorizes design and state recovery. Before financial
experiments, record the user's investment choices and resolve this contract.
Changing a draft now is legitimate; changing a frozen gate after outcomes is not.

## Capital, horizon and tolerances

| Item | Accepted choice or proposed assumption | Meaning / unresolved detail |
| --- | --- | --- |
| Capital | $10,000 baseline; larger amount if capital is the demonstrated blocker | Determine and report the required amount under the capital policy below. All capital is committed on day zero; no leverage or later top-up is implied. |
| Spending currency | USD provisionally | Confirm USD/EUR/CZK; translate cashflows and FX costs into the chosen currency. USDT is not automatically a dollar. |
| Investment horizon | 365 days | No required interim withdrawal; this is distinct from the length of evidence needed to estimate performance. |
| Annual net-return target | At least 10% of C per 365 days ($1,000 at $10,000) | User-requested target after modeled implementation costs; neither a forecast nor a guaranteed minimum each year. Tax basis remains to be settled. |
| Useful incremental cash benefit | 2% of C per 365 days ($200 at $10,000) | Proposed 2% benefit over each eligible simple benchmark; a separate preference from absolute profit. |
| Maximum drawdown | 30% of prior liquidation NAV peak; accepted by the user | Include initial NAV, fees, gaps and terminal conversion; not a guaranteed stop-loss fill. The earlier 20% proposal was not accepted. |
| Maximum stress loss | 50% of total capital at each stress origin; accepted by the user | Apply the scenarios below throughout the path; separately report drawdown from original capital. The earlier 35% proposal was not accepted. |
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

## Accepted return target and risk limits

The user requested 10% or more annually and then accepted the proposed
30% maximum drawdown / 50% stress-loss pair with “lets go with that”. These
are the research acceptance limits for this broader program. The alternative
40% / 60% pair and earlier 20% / 35% proposal are not selected or additional
backtest cells. No leverage permission or guaranteed return follows.
Record this single accepted pair in each committed experiment contract before
outcomes; acceptance does not by itself complete source or run admission.

At a $10,000 reference value, the accepted 30% drawdown is $3,000 from a
$10,000 peak; 50% stress loss is $5,000 from a $10,000 scenario origin. These
dollar limits scale with the relevant peak/origin and with larger committed
capital. Drawdown and deterministic stress loss are distinct measurements.

The 10% hurdle concerns total net profit, not 10% excess return over benchmarks.
The separate proposed benchmark-improvement floor remains 2% of C ($200 at
baseline). Report positive net returns below 10% as target shortfalls, separately
from losses, benchmark underperformance and inadequate evidence. Raising the
target does not justify changing an outcome window, discarding a failed case
or weakening confirmation. The investment horizon and personal-tax basis
remain unresolved; a stated annual target is not a guarantee for every year.

[Investor.gov’s risk/return explanation](https://www.investor.gov/introduction-investing/investing-basics/investment-products)
supports the distinction between higher potential returns and greater chances
of loss; it does not establish that this target is achievable by these recipes.

## Capital policy: baseline plus justified larger capital

The user clarified that $10,000 should not itself eliminate a useful strategy.
First distinguish a capital constraint from negative unit economics, missing
data, lack of access, unacceptable percentage risk or inadequate evidence.
Minimum quantities, fixed execution/transfer charges, required prefunding or
collateral, and feasible diversification can justify a larger-capital question.
More capital does not by itself establish a better percentage return–risk tradeoff.

For a capital-blocked candidate, report the specific constraint, minimum
implementable capital, reserves and uncertainty, and the least larger amount
that clears it under frozen conservative assumptions. Derive the amount from
constraints before inspecting new returns; do not sweep capital until a favorable
backtest appears. Unknown terms remain unknown rather than guessed break-even
capital. Retain the $10,000 outcome as capital-constrained when appropriate.

The initial finite design permits one additional capital scenario, C_plus,
selected before outcomes for the highest-ranked candidate with a demonstrated
capital blocker. Freeze the numerical amount and justification in registration.
Apply all benchmarks at the same capital, recomputing costs, rounding, depth,
reserves, cash opportunity cost and dollar losses. Other required amounts remain
reported leads; additional financial capital scenarios need a recorded budget
amendment. Researching a required amount does not commit that investment, and
no unlimited available balance or personal maximum is assumed.

The 10% absolute target and proposed 2% incremental annual cash-profit floor
remain proportional to larger capital, with both dollar amounts shown. Accepted
30% drawdown and 50% stress-loss limits also apply at larger capital.
Thus larger capital cannot pass merely by increasing dollar profit while diluting
return on total committed capital. Confirmation selects at most one recipe and
one capital amount, with the capital choice included in the selection history.

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
exposure drift, custody concentration and liquidity lockup. The accepted 50% stress limit may
make an all-on-exchange implementation unacceptable even if its market exposure
is small. Such a result is implementation/risk infeasibility, not absence of a
return mechanism. No strategy can guarantee the accepted drawdown limit.

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
same capital/access, 30% drawdown and 50% stress-loss limits to be a feasible
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
2. Candidate satisfies the accepted 30% drawdown / 50% stress-loss limits and
   the frozen operational constraints.
3. Absolute profitability: observed 365-day P >= 0.10*C ($1,000 at baseline) and the simultaneous
   one-sided 95% lower bound on expected 365-day net profit is above zero.
4. Benchmark value: observed D >= 0.02*C ($200 at baseline) against **every feasible member of
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
development data. Rank within each capital scenario first; select the baseline
if any baseline recipe qualifies, otherwise consider the justified C_plus panel.
Within a capital scenario, differences below 0.01*C ($100 at baseline) are ties: prefer lower annual
turnover, then fewer policy rules, then fixed map rank. Select at most one recipe
and one capital amount; all tested candidates remain in the selection history. Development
selection itself never validates a strategy. If none qualifies, cash/simple
allocation can remain the practical reference without being advertised as a
newly validated profitable strategy. H1's simple allocations receive full
implementation, risk and absolute cash-profit reporting as benchmarks. They
need not demonstrate superiority to themselves. The initial four-candidate
program makes no confirmatory superiority claim for a benchmark; promoting a
benchmark as a new selected strategy would require a separately registered
claim and budget decision, not silently adding a fifth candidate.
