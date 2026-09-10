# Factor sizing and stop re-entry comparison — September 10, 2026

Registered key: `risk_policy_2026_09_10`. The user's instruction to proceed authorizes this bounded retrospective comparison and its engineering implementation. The research program retains zero validated strategies. Base source is `3202d7982c47bb1472a8f3eb43a0851fd37b1480`. Registration must be committed before implementation or new performance calculations; reviewed source must then be committed before one empirical execution.

## Question and prior record

The completed risk diagnostic found stale entry sizes and repeated same-target re-entry after price stops. Test the effects of refreshing size daily and waiting for a new saved target episode after a price stop. Keep all eighteen original factor configurations; do not select only previously favorable cases. The scoped history review found prior lower-Kelly, no-vol-target and stop-threshold tests, but no exact instance of this two-axis comparison. See the three pre-result design reviews in this directory. Their historical qualifications remain; this charter resolves their proposed choices.

## Frozen grid and clocks

Cross all eighteen configurations, in the gate's original order, with these four arms in this order:

| Arm | Sizing | Price-stop re-entry |
|---|---|---|
| A00 | Saved entry/flip target magnitude | Immediate saved target |
| A10 | Daily causal volatility resize | Immediate saved target |
| A01 | Saved entry/flip target magnitude | Wait for new saved target episode |
| A11 | Daily causal volatility resize | Wait for new saved target episode |

This is 72 primary identities: eighteen repeated controls and 54 changed policies. Every identity includes independently simulated bitcoin and ethereum sleeves. The index is the daily mean of those two complete simple-return streams; it is not a pooled executable account. Four independently simulated cost scenarios per identity give 288 index evaluations and 576 sleeve books. Retain all identities, including identical, flat, halted, failed and unavailable cases.

Only pinned saved targets/OHLC and corrected control traces/returns from `data/factor-correction/2026-09-10/results/` may enter. Pin the original result (SHA-256 a6886a55966f78d8e9bb36f694212fa626484a3088104bd53c48589a27b4309d), all 36 targets, 144 traces and 72 return files, plus source references. Its original execution commit is `27640882822d812c6d0478340495e033a11d3915`. Preserve all 1,241 target/valuation dates, 2021-11-07 through 2025-03-31, and all 1,240 return dates beginning 2021-11-08. Normalize the naive daily timestamps explicitly as UTC midnight. Reject duplicates, gaps, nonpositive/nonfinite or incoherent OHLC, malformed targets, mismatched sleeve clocks or input hash changes. Do not fetch data, rebuild signals, inspect later observations or open a holdout.

## Policy contract

The saved raw target is authoritative. Its embedded original signal decisions, min-hold7, early-exit0.015, entry volatility gate and development-reset warmup remain fixed. The underlying raw factor signal cannot release a stop block. No subsequent trend filter is added.

For daily sizing, derive sigma from the original lagged visible close sequence `[Close[0], Close[:-1]]`, twenty log-return sample standard deviation times sqrt252. Log returns are used only for this estimator. A permitted nonzero raw target becomes `sign(raw_target) * min(3, 0.15 / sigma)`, retaining targetvol0.10, Kelly0.5 and confidence-one leverage3. The original strictly-prior 95th-percentile gate remains embedded in raw target entry/flip decisions; no daily gate-induced exit is added. Flat, blocked and permanently halted decisions request zero without requiring positive sigma. An admitted nonzero daily target with missing/nonfinite/nonpositive sigma makes that sleeve evaluation explicitly unavailable with date/reason. Never pass NaN as a policy output or manufacture zero exposure from missing data.

Each sleeve/arm/cost variant gets a fresh controller. Initially its blocked direction is zero. After an actually executed price-stop exit, remember the direction that stopped; this can affect only later decisions. On a later bar, a zero saved raw target clears the block and remains flat. An opposite saved raw direction clears the block and may enter that direction on that date. A same-sign target remains blocked irrespective of magnitude changes or elapsed time. Suppressed/executed zero, resizing and changes of the underlying raw signal do not clear the block. An opposite entry stopped on its own entry bar establishes a new block in its direction. A long-only target can consequently remain flat indefinitely; this is an intended retained outcome.

The permanent 15% portfolio drawdown halt takes precedence and is never reset. Preserve the original 3% threshold price stop, gap/fill-envelope convention, initial NAV10000 per sleeve, and trade-equity stop_loss1.0/take_profit0. The latter channel remains inactive. Same-sign daily resizing must not reset the price-stop entry anchor; only an actual new entry/sign flip does. Keep all original pre-exit peak updates, signed funding, charges and post-exit halt checks. The controller supplies targets and receives executed-stop notifications; it does not replace `accounting_step` or calculate PnL.

## Costs and control parity

Primary assumptions: fee0.0004, slippage0.0005, spread0.0001, quadratic impact coefficient0.00005 and signed assumed funding0.0003 per day on opening exposure. Positive funding charges longs and credits shorts, including the original stopped-day approximation. The saved daily price proxies and threshold fills cannot substantiate executable venue performance.

Run `primary`, `zero_execution`, `double_execution`, `zero_funding`, in that order. Execution scaling applies to fee, spread, slippage and impact; zero funding changes only funding. Each path independently determines its stops and permanent halt. Never derive a sensitivity merely by subtracting primary costs.

Execute A00 controls first across all eighteen configurations and four cost cases. Compare all original trace columns against all 144 saved traces, and both sleeve plus index streams against all 72 saved return files. Clocks, flags and categories must match exactly; dollar absolute tolerance1e-9, weights/returns1e-12, relative tolerance1e-10 are fixed. Default-None engine parity against the exact archived pre-change engine is also required on synthetic fixtures before source freeze. Any global input/admission or A00 parity failure halts alternative execution, preserves attempted outputs and publishes all 72 identities as unavailable for comparison. No tolerance changes or blind repeat are permitted after seeing that failure.

Only `scripts/baseline_strategy_v2.py` may change among existing executable files, through a minimal optional policy hook whose default remains unchanged. Archive its exact original bytes under `docs/risk-policy-2026-09-10/original/`. Preserve all previous artifacts and gate objects. New independent modules/runners/tests and append-only findings/evidence are allowed.

## Fixed analysis

Report every primary identity and sleeve in original order. Headline metrics use the full 1,240-day clock and initial NAV: mean simple return, arithmetic annual mean, realized volatility, sqrt365 zero-hurdle Sharpe with ddof1, compound return and maximum drawdown. Undefined zero-variance ratios are null with a reason, never an attractive substituted value. Keep full-clock cash tails; active-only metrics cannot replace the headline. Also report complete period metrics for 2021-11-08–2022-12-31, 2023-01-01–2024-12-31 and 2025-01-01–2025-03-31.

Per sleeve report active, blocked/waiting, permanently halted and flat counts, first halt and post-halt cash count; applied/incoming/closing exposures and integrated absolute/signed exposure; nominal risk proxy quantiles (50th,90th,99th,max), finite/active/unavailable denominators, counts above0.15 and original-entry risk references; raw sizing age, price stops, successor classes, blocked re-entry opportunities, and stop fill-envelope exceptions. Reconcile gross PnL, signed funding, linear execution charges, impact, turnover and NAV, keeping sleeve dollars separate. Opening/maintenance/flip/resize/close categories are exclusive; stopped exits are separate, and re-entry is a subset rather than an additional charge. Use the registered numerical tolerances. A daily admitted resize must respect its algebraic current-risk cap; a waiting arm must have zero entries within a blocked old episode. Those are engineering checks, not economic success gates.

Report all 54 within-configuration primary contrasts A10−A00, A01−A00 and A11−A00, pairing complete identical calendars. Include metric, exposure, risk and cost differences, plus the three descriptive factorial contrasts: sizing `[(A10−A00)+(A11−A01)]/2`, waiting `[(A01−A00)+(A11−A10)]/2`, interaction `A11−A10−A01+A00`. Preserve nulls and identify the metric orientation, including negative-valued maximum drawdown. Report all cost sensitivities; no best-cost selection. Reductions in exposure, active days or long cash tails must accompany apparent improvements. No bootstrap, p-value, DSR, winner ranking, champion selection or adoption PASS is part of this spent-history experiment.

Produce 72 primary invalid-log shadows using frozen primary exposures, stop schedules and fee/funding fractions: replace only the gross exposure-times-simple-mark-return term with exposure-times-log1p(mark return), per sleeve, then average the two complete streams. Save undefined cases explicitly. Report sign/order changes versus simple accounting. These shadows are invalid accounting diagnostics, never alternative executable strategies. No additional variants, fill models, thresholds, cooldown lengths, halt restarts or new statistical methods enter this grid.

## Tests, one execution and evidence

Before source freeze, synthetic tests cover original/default/A00 parity; causal lag/future perturbation; long and short stop anchors through resize; raw-target block transitions including zero/opposite/same-sign changes; stop chronology and permanent-halt precedence; marked holdings, maintenance netting, both funding signs and every charged leg; exact cash tails, clipping, invalid targets/sigma/clocks; a planted resizing/re-entry trade-off; all identities and failure preservation. Independent code review checks engine and evaluation boundaries.

Reserve `data/risk-policy/2026-09-10/results/` exclusively with an attempted-run marker and all 72 pending identities before input admission. Record committed source/gate/correction policy, inputs and runtime. Save all successful traces/return frames/shadows and explicit failures. Recheck source and input hashes at completion. Serialize all 72 central financial rows to an immutable receipt before append; validate the exact original 748-row,569325-byte ledger prefix (SHA-2564d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601). Append once, retaining each identity and all four nested scenarios plus the shadow; final count820. Preserve durable partial-failure metadata and require a recovery review rather than rerunning books. Independent result checks reconstruct saved arithmetic and denominators without rerunning policies.

Original gate objects, existing results, the original external270 provenance receipts, and undeclared source stay unchanged. Findings and correction policy can be appended at completion to close this cycle against accidental rerun. Commit and retain reports and all new empirical artifacts on the dedicated research branch.

## Fresh validation route

The old factor holdout and other historical windows are spent. This cycle selects no champion and cannot promote a strategy. `fresh-validation-plan.md` defines the required prospective path; it is a planning document, not permission to backdate eligibility or an already executable validation registration. No future data collection, scheduler, provider contact or VPS change is part of this run.
