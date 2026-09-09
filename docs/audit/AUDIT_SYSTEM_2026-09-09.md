# Independent audit of the crypto trading research system — 2026-09-09

**The available evidence still supports zero validated strategies. It does not support the stronger conclusion that every rejection was measured correctly, or that useful predictive structure has been exhausted.** Active accounting defects, a material missing-feature scoring failure, causal data problems, incomplete provenance, and operational failure handling were reproduced. The thesis still asserts positive strategy results invalidated in August.

The immediate priority is to make measurement and reporting trustworthy before spending more research trials. No profitable strategy was discovered or reinstated by this audit. No historical strategy was rerun and no unspent holdout was opened.

## Scope and evidence

The audit combined four independent reviews: trading/accounting and timing; statistical gates and research records; data availability and integrity; and paper/live execution plus manuscript claims. Important findings were reproduced using synthetic inputs or checked against already saved development forecasts. Source versions, pre-existing worktree changes and evidence hashes are recorded in [workspace_inventory.json](/home/malecada/master_thesis/data/audit_2026-09-09/workspace_inventory.json); the audit contract is in [SCOPE.md](/home/malecada/master_thesis/data/audit_2026-09-09/SCOPE.md).

| Review | Detailed report | Fresh existing-test results |
|---|---|---:|
| Engines, PnL, timing, accounting contracts | [Engine report](/home/malecada/master_thesis/data/audit_2026-09-09/engine_report.md) | 122 passed; two historical-data tests excluded |
| Gates, statistical calibration, provenance | [Gates report](/home/malecada/master_thesis/data/audit_2026-09-09/gates_report.md) | 58 passed |
| Data, causal availability, missing features | [Data report](/home/malecada/master_thesis/data/audit_2026-09-09/data_audit_report.md) | 51 passed |
| Paper/live behavior and parity | [Execution report](/home/malecada/master_thesis/data/audit_2026-09-09/execution_report.md) | 95 passed |
| Thesis claims and assignment | [Thesis report](/home/malecada/master_thesis/data/audit_2026-09-09/thesis_report.md) | Source and artifact checks |

Test sets overlap; these are per-review run counts, not a count of unique tests. The accounting, statistical and execution counterexamples passed alongside those suites. The six execution reproductions were independently rerun by the engine reviewer with identical results. Passing the existing suites therefore does not resolve the demonstrated failures.

Current source is split across checkouts: predlab at `c5f1a445`, xsect research and current findings in TradingAgents at `01798677`, monitoring/main at `ed5e22f6`, thesis at `7dfa296d`. Predlab and xsect are separate capability sets; neither research package is present in monitoring/main. A correction on one branch cannot be assumed to exist in every runnable checkout. The current VPS contents and account state were not inspected.

## Findings that most directly affect the research conclusions

### 1. Two strategy tests still book log returns as trading PnL — high; plausible false-rejection mechanism

The August correction repaired S1 but missed Phase-P S2 and S3. Their actual callers still pass the realized-measure store's logarithmic `ret` into an arithmetic position-return engine: [S2 caller](/home/malecada/master_thesis/TradingAgents-predlab/scripts/predlab_pp_dev.py:128), [S3 caller](/home/malecada/master_thesis/TradingAgents-predlab/scripts/predlab_pp_dev.py:163), [return definition](/home/malecada/master_thesis/TradingAgents-predlab/tradingagents/predlab/rv.py:72).

For a long position, `log(1+r) <= r`: this subtracts from every bar's gross PnL. A synthetic fixed-position fixture flips S2 Sharpe from the correctly booked +0.484 to -0.436, and S3 from +2.358 to -2.148. These deliberately illustrative numbers demonstrate the software error; they are not estimates of a market edge.

The saved unrepaired S3 smooth-24 dev results are near zero (-0.080 and -0.160). A corrected historical result could therefore matter, but **a real gate reversal has not been established**. S2's benchmarks share the accounting defect, so its relative tracking-error/do-no-harm result cannot be inferred from the absolute long bias. Neither S2 nor S3 spent a strategy holdout; S3 was exploratory.

The existing source-text regression test accepts a file containing `pct_change` anywhere. It passes because the S1 portion was repaired. Caller-level checks are needed for each actual PnL input. This is a concrete counterexample to treating a file-level convention check as an engine-wide accounting guarantee.

### 2. Missing data are scored as strong forecasts against Elastic Net — high; actual saved-score contamination

[ElasticNetForecaster.predict](/home/malecada/master_thesis/TradingAgents-predlab/tradingagents/predlab/tier2.py:64) returns literal zero when a feature is missing or no fitted model exists. [ProbClip](/home/malecada/master_thesis/TradingAgents-predlab/tradingagents/predlab/tier2.py:93) then turns this into a 2% up probability. Data unavailability is thus scored as a confident directional forecast.

Alignment with saved development predictions shows missing registered inputs at approximately 27.49% of BTC hourly origins and 31.88% of ETH hourly origins. On those same labelled origins, the fallback's Brier losses are about 0.484 and 0.480, compared with 0.25 for a neutral forecast. This adds approximately 0.064 and 0.073 to the entire cell's mean Brier score relative to that neutral diagnostic. No model was refitted to obtain these measurements.

For variance forecasts, nonpositive outputs instead become missing QLIKE losses. Thousands of saved ENet forecasts are excluded. Baseline and candidate losses are paired on the retained origins, but the retained sample varies by model and failed forecasts are not represented in headline coverage. This is a selection and reliability problem, not evidence of a measured counterfactual improvement.

The resulting comparisons cannot cleanly support a general conclusion that the model class lacks useful signal. A target-appropriate missing-feature/failure policy, explicit valid-forecast coverage and a common evaluation population must be fixed in advance. Correcting this issue would not validate Elastic Net or any trading strategy by itself.

### 3. Some DEX and historical features use data unavailable at the claimed timestamp — high; economic effect unmeasured

The new-pool composite is normalized using all pools in the same calendar quarter. A synthetic change to a later pool changes earlier pools' scores and ordering. That preprocessing is unavailable for an entry decision before the quarter finishes. Cohort-relative descriptive rankings can be defined this way, but they cannot be represented as an executable score at the registered entry time.

The DEX simulator also converts an intraday USD entry into WETH using that date's end-of-day ETH close. In the checked NLST3 development entries, this reaches forward a median of 11.32 hours. Across 1,203 entries, the daily FX price differs from the last completed five-minute price by median 1.28%, 95th percentile 7.00%, and maximum 18.73%. This affects position sizing, gas conversion and execution economics. It is a price comparison, not a rerun of the strategy.

These findings qualify the point-in-time ranking/economics claims. They do not demonstrate that the substantial observed losses disappear after correction. Exact code paths and affected cycles are in the data report.

Historical backfills have a related provenance limitation. Alpaca normalization assigns the latest returned article a publication-plus-one-minute availability timestamp and ignores its update timestamp. CoinMetrics values receive fixed event-plus-one-day or seven-day timestamps, and repeated fetches can overwrite values at those same keys. The inspected 257,617-row historical CoinMetrics slice contains no preserved multiple-as-of versions. Synthetic probes demonstrate that revised content can be assigned an earlier availability time; the incidence of actual revisions and their effect on research results remain unmeasured. A correctly filtered timestamp cannot establish point-in-time correctness if the content version was backdated.

### 4. Portfolio holding, fees, and return aggregation lack a single executable contract — medium; effects can run in either direction

Several engines reuse unchanged target weights while accruing daily returns, yet charge turnover only when targets change. A purported weekly 50/50 holding of assets priced `100→110→121` and `100→100→100` ends at 1.1025 in the engine; actual held units end at 1.105. The engine's daily constant-weight strategy is a valid gross construction, but keeping those weights requires maintenance trades omitted from its cost calculation.

The hourly liquidation-fade engine sums hourly simple returns into daily returns. A fully invested instrument doubling then halving produces a reported +50% day, although compounded wealth returns to its starting value. Additive PnL against fixed day-start capital is possible under a different quantity/capital contract, but that bridge and its required trades are absent. Smaller registered exposures reduce the synthetic discrepancy without resolving the definition.

Other reproduced problems include maximum drawdown omitting initial NAV (a first-period 20% loss can be reported as 0% drawdown), and an existing overlay charging the already-net base fee a second time. Empty-target dates can disappear from the return clock while the previous book remains held. The latter two were already described in August and remain reachable.

Free maintenance turnover and omitted drawdown tend to flatter results; duplicated fees depress them; holding/aggregation differences can move relative outcomes in either direction. Their historical magnitudes were not recomputed. A blanket claim that all accounting errors can only flatter a failed strategy is unsupported.

### 5. Gate failures are being interpreted more strongly than the tests allow — high interpretation issue

The basic Newey–West and Benjamini–Hochberg arithmetic was independently verified. Representative recent stored decisions (CAL2, final OFLOW, SMW, LIQ_FADE_V1 and NLST4) match their numerical thresholds. That supports those procedural decisions, conditional on the inputs; it does not prove there is no economically useful population effect.

An independent illustrative simulation using the earlier audit's broad design reproduces a compound acceptance probability of only **18–31% for true annual Sharpe 1**, versus roughly **82–84% for Sharpe 2**. Assumptions include iid Gaussian daily returns, fixed DSR benchmarks, and no additional holdout hurdle; this is not a measured power estimate for every family. The stack is deliberately difficult to pass and can miss modest real effects.

The latest NLST4 economic mean has a standard error of 26.15 percentage points implied by the implemented Newey–West statistic, around 2.48 times its preregistration projection. This is conditional on the implemented dependence specification; the adequacy of event-overlap handling was not independently established. Its approximate normal 95% interval spans -44.75% to +57.74%. The registered economic claim fails, including separate ex-top and stress criteria, while the unconditional mean remains imprecisely estimated. Closure should preserve this distinction.

Some significance claims also require stronger calibration checks: one-step forecast losses may remain serially correlated even with non-overlapping targets; selecting a winner before applying BH requires handling within-cell selection; and invalid observations must not silently reduce the family denominator. Synthetic counterexamples demonstrate these risks. They do not establish the actual error rate or reverse any specific holdout result.

### 6. Failed oracle heuristics do not prove every forecasting approach is exhausted — high logical issue

The [O6 code](/home/malecada/master_thesis/TradingAgents-predlab/scripts/predlab_opt_o6.py:5) treats exact future volume fed into a proportional-weight heuristic as an upper bound on any volume forecaster's attainable performance. That implication is false. Better information can improve the optimum over feasible policies; it need not improve a fixed heuristic.

A deterministic counterexample makes exact-volume weighting lose while a constant forecast through the same heuristic earns a positive mean. The valid conclusion is that the registered weighting constructions failed. A whole-axis impossibility claim requires an actual objective upper bound. This is a correction to the inference, not a proposal to reopen that axis.

### 7. The evidence register cannot currently enforce its own reproducibility claims — high provenance issue

The available ledger/Git records contain ten evaluated rows across five cycles whose first committed gates postdate recorded results. This does not establish that criteria were invented after seeing results; they may have existed uncommitted. It does fail the stated **committed-before-results** standard.

The recorded HEAD SHA is not a hash of executed working-tree source. The logger does not require a clean tree or verify a matching frozen gate/data manifest. At the audited snapshot, the final eleven ledger rows are uncommitted. The ledger's config-only hashes also merge different cells/families, and multiple hash encodings coexist. A raw row count, distinct configuration count and effective independent trial count are different quantities.

The hash-count defect was traced to descriptive or unreached/report-only consumers, so it is not evidence of an existing DSR gate reversal. A more direct consistency example is OFLOW: its original P0 sign check wrongly killed an admissible reversal; that was corrected and the survivor subsequently failed P1, but the old false P0 remains in its ledger row. Original Bybit PASS and some early `sealed` flags also survive separately from correction/spending records.

The committed ledger is append-only, which is useful. Corrections need explicit supersession links and one authoritative resolver, so reports cannot accidentally treat preserved historical claims as current facts.

## Operational and thesis findings

### 8. Live execution can report completion without having achieved it — high operational issue

Six offline fake-client scenarios were reproduced and independently confirmed:

- Two rejected orders are journaled as “done”; the next wake skips the day with no actual positions.
- A rejected emergency close reports “flattened” while the position remains open.
- A dry run consumes the date's live idempotency key.
- A desired leg with a missing mark is closed as though it left the strategy.
- An 18-day-old champion row can generate orders.
- An unknown-status HTTP 503 triggers another identical order submission without reconciliation.

The last scenario proves duplicate submission, not actual duplicate fills. Binance explicitly requires checking unknown execution status before resubmitting. [Official error-handling documentation](https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info).

These defects affect the trustworthiness of paper/live measurement and execution reports. They do not explain historical backtest failures. The current server deployment was not checked; local source capability must not be confused with evidence of a real account incident.

### 9. The paper trader is not a strict replica of the backtest — medium operational/evidence issue

The paper universe uses a 35-day liquidity interval and the signal as-of month; the backtest uses the prior calendar month relative to the trading day. At month-end, a synthetic panel causes each book to contain five names absent from the other. A separate fixture changes a candidate's liquidity median from 1 to 100 solely because the paper window contains four extra days.

Paper returns omit funding and estimate fees separately; overlay volatility is calculated from a different return basis. These quantities can support descriptive monitoring, but require a shared holdings, timing, funding, cost and scaling contract before they can establish research/live parity.

### 10. The thesis still claims the invalidated champion is validated — critical reporting issue

Both abstracts, introduction, post-audit chapter, discussion and conclusion present S1 holdout +2.20 and champion +1.89 as validated strategy results. The canonical stored corrections instead report **S1 holdout -2.202, champion overlay -0.371, and Bybit overlay -0.616**. These correction values are historical saved evidence, not newly rerun results.

The thesis equity figure is **byte-identical** to the explicitly superseded log-PnL chart. The literature comparison also labels the invalidated V5 MIX +3.18 and hybrid +4.68 results as validated. Later tables were updated without reconciling these central claims. Source locations and the figure hash are in the thesis report.

The supplied [assignment text](/home/malecada/master_thesis/topic/thesis_assignment.md) asks for a functioning hybrid architecture, comparison with baselines and component evaluation, including whether performance improves. A rigorous negative answer can address that question. The empirical claims must be corrected and mapped to the assignment; positive alpha is not stated as a requirement. The signed-assignment placeholder remains in the manuscript.

## What was verified and can be retained

- Predlab's corrected S1 return callers and current xsect return constructors use simple returns. Several causal sizing, purging, signal-lag and funding-sign checks pass. The missed S2/S3 paths are specifically localized.
- The inspected BTC/ETH five-minute development series each contain 552,096 rows with no internal gaps or duplicate timestamps. Daily Binance and Bybit stores have no internal timestamp gaps or duplicates within the inspected instrument spans; one nonpositive Bybit price was identified. Cached development close and quote-volume panels match source values exactly. These checks do not prove every historical instrument or provider revision is present.
- The principal deficiencies in the inspected derivatives features are field-level coverage and failure handling; a high headline count of OI rows does not establish usable coverage of every feature.
- Recent gates generally have committed registrations and their sampled final arithmetic decisions match the stored thresholds. Historical ledger commits preserve prior prefixes.
- Forecastability, rank discrimination and tradeability are different questions. Genuine evidence for one cannot be automatically promoted to another, and a faulty strategy-accounting path does not automatically invalidate every forecast result.

## Prioritized correction plan

| Priority | Work | Acceptance evidence |
|---|---|---|
| 1 | Freeze an authoritative claim/result/source/data registry and mark affected claims as requiring correction | Every result resolves to a convention, exact source snapshot, data manifest, gate version, window status and supersession chain; thesis positives are clearly withdrawn |
| 2 | Repair S2/S3 PnL, ENet failure semantics, and causal DEX transformations | Caller-level simple-return checks; missing-feature/failure cases per target; future-data mutation leaves every earlier actionable score and price unchanged |
| 3 | Define a common executable accounting contract | Hand-calculated units/NAV, price drift, rebalance costs, funding, gaps, short round trips, initial-loss drawdown and time-aggregation checks agree with an independent reference calculator |
| 4 | Register a bounded correction of already affected results | Original grids, windows and gates retained; only diagnosed defects corrected; originals preserved; no new winner search or new out-of-sample claim on spent data |
| 5 | Repair order completion/reconciliation and paper parity | Failed/partial/unknown orders cannot become successful completion; emergency closure is verified; dry-run/live states are separate; common-panel book and PnL reconciliation passes |
| 6 | Reconcile the manuscript and qualify inference | One evidence source drives abstracts, tables, figures and conclusions; calibrated uncertainty, tested policy scope and assignment requirements are explicit; compiled PDF inspected |

Operational completion/reconciliation repairs can proceed in parallel with research accounting and are a prerequisite to further execution or operational measurement using this source. Actual deployed exposure remains unverified.

Corrections should classify each affected conclusion as unchanged, invalid measurement, insufficient precision, construction/cost failure, or valid rejection of the specified effect. “Closed by stop rule” should remain distinct from a claim that a whole phenomenon is absent. Existing gates must not be relaxed retrospectively to rescue a result.

## Boundaries of this audit

This is a completed source-and-evidence review of the principal research and execution paths, with reproducible targeted probes. It is not a line-by-line certification of every repository or a re-execution of every historical result. Reference repositories were inventoried; their complete implementations were not re-audited. No strategy search, model refit, market-data refresh, live account inspection, orders, service changes, source repair or manuscript rewrite was performed. Credentials were not inspected. Pre-existing modifications were preserved.

Historical verdict changes remain unresolved until bounded corrections are registered and run. Actual dependence-adjusted significance, final deployment version, fees/fills, full corpus revision histories, complete universe survivorship, and every literature citation were not independently established. The signed assignment and live environment require separate evidence for final submission and operational verification; no additional material was needed to establish the findings above.
