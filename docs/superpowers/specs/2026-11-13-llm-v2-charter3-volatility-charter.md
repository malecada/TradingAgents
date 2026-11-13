# Charter 3 — Target change: next-week volatility (`llm-v2-charter3`)

**Status:** frozen on 2026-11-13 (V1), with approval given on the draft. Stage V0 (code, tests, synthetic dry
run, pass rate and power of the gates on synthetic targets) is complete. It changed the gate: the first
design passed too often on targets that hold no reader information and was hardened before any outcome was
opened (§3.2, §4.1). The decisions on the draft are recorded in §10. At the freeze nothing is registered, no
attempt is claimed and no feature built from the reader records has been joined with a volatility outcome.
From this commit the document stays byte-identical (§4).
**Family:** `llm-multiagent-v2`, attempts used 3 of 6 (Charter 1 interrupted with a failed receipt, Charter 1b
FAIL, Charter 2 FAIL). This charter is attempt 4.
**Predecessor:** `docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md`, run
`llm-v2c2-reader-dev-run-20261112`, verdict FAIL.

## 1. Why this target

Charter 2 let the agents read and a fitted model forecast. On 104 test weeks the text score next to the quant
forecast reached t 1.39 against a threshold of 2.0. What relation there was sat in the attention counts, which
code builds from the number of linked items. The judgements of the reader agents carried none (weekly IC 0.012,
t 0.93). The target was the direction of next week's relative return.

This charter keeps the records and changes the question from "which way" to "how much". A security incident, a
court ruling, a listing, a token unlock or an unconfirmed report states that something is happening to an
asset. Whether the price then rises or falls is hard to read from public text. That it moves more than usual is
a weaker and more plausible statement, and it is the statement a risk layer needs: position limits and sizing
depend on expected volatility, not on expected direction.

The difficulty is the baseline. Volatility is persistent and is forecast well from its own history, and the
number of items about an asset rises whenever its price is active. A text feature therefore passes a naive
volatility test easily and adds nothing. The registered question is the increment: do the judgements of the
reader agents carry information on next week's relative volatility beyond price history up to the decision
and beyond the attention counts?

No model call is made under this charter. The 53,330 records of Charter 2 are an input.

### Earlier programmes that bear on this (closed-programmes ledger)

| Programme | What was tested | Outcome | Bearing here |
|---|---|---|---|
| Charter 2, `llm-v2c2-reader-dev-run-20261112` | Reader records as features for weekly relative returns | FAIL, t 1.39. Attention counts carried the weak relation, reader judgements none. | Records, reading sets and attention counts are reused. Signed features are dropped. Attention is a control here, not part of the tested block. |
| `exec_fcst` (Sep 2026, THESIS §85) | Volatility forecasts from own history as execution inputs | HARQ on BTC 14.7 % better than a naive 20-day forecast (QLIKE, p 0.002), EGARCH on ETH failed its floor | Own history at several horizons is a strong baseline. The history block of §3.1 follows that shape (1, 7, 30 and 90 days). |
| `rviv-p0` | Realised-volatility forecasters against option-implied volatility, BTC and ETH | The debiased option-implied index beat every history-based forecaster (p < 0.01) | For the two assets with a liquid option market the market's own forecast is the better baseline. It does not exist for a cross-section of 50 perpetual contracts. The baseline here is price history, and this limit is stated in §6. |
| On-chain Branch B, B4 to B8 (Oct 2026) | Exchange flows and on-chain structure as volatility predictors, hourly | B4: holdout passed 2 of 3, the gain was mostly a proxy of last-hour activity. B5: nothing beyond option-implied volatility. B8 (146 tokens): own volatility null, relative volatility a thin pass (0.5 to 1.1 % of MSE), fading in 2026. | An activity proxy passes a volatility gate without adding information. The gate here controls for price activity and for attention, and the size of a pass is read against a fixed value (§5). |
| `llm-c2-veto` (THESIS §62) | News veto overlay for tail days | Stopped at P1: news recall 54 % against a floor of 60 %. The tail days were squeeze days, not news days. | Tail events in this market are often not led by news. Tail targets are descriptive here and the gate is on realised variance. |
| Sentiment index as model feature (THESIS §33) | Tone index as a return feature, BTC and ETH daily | All gates failed | Return target. Not repeated. |
| News → volatility (lead list Aug 2026) | Not run | Open | This charter. |

## 2. Question, target, universe

Universe, decision time and windows are those of Charter 2. Universe: the 50 perpetual contracts with the
highest trailing 30-day dollar volume each Friday (7,800 rows, 156 weeks, 222 contracts). Decision time:
Saturday 00:00 UTC after the Friday card. The daily bar dated Friday closes at the decision. Windows:
development 2022-01-07 → 2024-12-27 (156 weeks, of which the first 52 weeks are training only and the last 104,
from 2023-01-06, are the test weeks), Sealed-A 2025-01 → 2026-04, Sealed-B 2026-05 → 2026-12-11. Both sealed
windows are untouched and their text is not built.

Target: `fwd_rv`, the mean Garman-Klass variance of the seven daily bars after the decision (bars dated
Friday + 1 to Friday + 7, Appendix A), taken as a percentile rank within the week minus 0.5. The rank is
relative on purpose. The level of market volatility moves all 50 assets together and is known from history;
the framework ranks assets against each other, as in the earlier charters.

Question: do unsigned asset-week features, built by code from the de-identified fact records of the reader
agents, carry information on the realised variance of the next seven days, relative to the other assets of
the week, beyond price history up to the decision and beyond attention counts?

Tail risk is the second target named for this change. Three tail measures of the same forward week are
reported as descriptive variants (§5): `fwd_absret`, `fwd_drawdown` and `fwd_maxday`. They are noisier than
the variance, and the one earlier tail programme (`llm-c2-veto`) found the tail days not led by news.

## 3. Design

```
record table of Charter 2 (53,330 records) ─► block V: unsigned asset-week sums (code) ──────┐
reading list ─► block A: attention counts (code) ─────────────────────────────┐              │
daily bars up to the decision, Friday card ─► HIST: 12 price-history controls ┤              │
                                                                              ▼              ▼
daily bars after the decision ─► target rank ─► controls removed          controls removed
                                                (two steps, §3.2)         (two steps, §3.2)
                                                     │                          │
                                                     └──► walk-forward ridge ◄──┘
                                                                 │
                                                                 ▼
                                             weekly partial correlation ─► gates (code)
```

### 3.1 Regressor blocks (decision-time data only)

Code: `tradingagents/reader/charter3.py`. Every block uses only what is observable at the decision. Each
feature is turned into a within-week percentile rank minus 0.5 over the 50 universe members (ties share the
average rank, a missing value takes 0).

**HIST, 12 controls.** Eight from the daily bars up to and including the Friday bar, four from the Friday
card. A window "of the last n days" holds the bars dated within n days up to the Friday bar.

| Control | Definition |
|---|---|
| `rv_1d` | Garman-Klass variance of the Friday bar |
| `rv_7d` | mean Garman-Klass variance of the bars of the last 7 days, at least 4 bars |
| `rv_30d` | the same over the last 30 days, at least 10 bars |
| `rv_90d` | the same over the last 90 days, at least 10 bars |
| `rv_max_7d` | largest Garman-Klass variance of a bar of the last 7 days, at least 4 bars |
| `ret_7d` | log return of the close over the last 7 days (the bar dated seven days earlier must exist) |
| `absret_7d` | absolute value of `ret_7d` |
| `vsurge_7d` | log of the mean dollar volume of the last 7 days over that of the last 30 days |
| `vol_ewma20` | card column: volatility of daily returns, exponentially weighted (20 days) |
| `dvol_30d` | card column: trailing 30-day dollar volume |
| `age_weeks` | card column: weeks since the contract was listed |
| `abs_funding_3d` | absolute value of the card column `funding_3d` |

**Block A, 2 controls.** `attn_7d` and `attn_abn`, the attention counts of Charter 2 with unchanged
definitions: log(1 + distinct linked documents of the last 7 days), and that value minus its mean over the 8
preceding 7-day windows of the asset.

**Block V, 6 features (the tested block).** Built from the resolved records with relevance `subject` of the
reading sets of Charter 2. Rows, time buckets and the removal of near-duplicates are those of block B of
Charter 2: within an asset-week, event records equal on class, status, direction and 7-day age bucket count
once with their highest materiality. No feature carries a sign.

| Feature | Definition | Reader judgement used |
|---|---|---|
| `evt_7d` | sum of materiality over events of the last 7 days | relevance, type, materiality |
| `evt_30d` | sum of materiality over events of days 8 to 30 | relevance, type, materiality |
| `unfav_7d` | sum of materiality over unfavourable events of the last 7 days (the Charter 2 feature of the same name; the code requires equality) | direction, materiality |
| `sched_30d` | sum of materiality over events with status scheduled, last 30 days | status, materiality |
| `rumour_30d` | sum of materiality over events with status proposed or rumoured, last 30 days | status, materiality |
| `split_7d` | the smaller of the number of favourable and the number of unfavourable opinion items of the last 7 days | direction of opinion items |

Counts reported with the features and used in no model: `n_subject_7d`, `n_subject_30d`.

The list is fixed here and is not revised after any outcome is opened. It was written after the result of
Charter 2 was known and before any volatility outcome was joined (§6).

Facts of the built features on the 7,800 universe rows (decision-time data, no outcome involved). The last
column gives the share of the rank variance of a block-V feature that is left after the controls are
removed: by the within-week step on HIST alone, by the within-week step on HIST and block A, and by both
steps of §3.2.

| Feature | Asset-weeks with a non-zero value | Assets per week, mean | Share of the rank variance left: within-week on HIST; within-week on HIST and block A; both steps |
|---|---|---|---|
| `attn_7d` | 78.1 % | 39.0 | |
| `attn_abn` | 90.1 % (missing in 2.6 %, the first four weeks) | 45.0 | |
| `evt_7d` | 39.5 % | 19.7 | 0.489; 0.322; 0.274 |
| `evt_30d` | 56.4 % | 28.2 | 0.488; 0.342; 0.302 |
| `unfav_7d` | 17.2 % | 8.6 | 0.598; 0.518; 0.387 |
| `sched_30d` | 32.1 % | 16.0 | 0.564; 0.464; 0.401 |
| `rumour_30d` | 14.8 % | 7.4 | 0.677; 0.621; 0.494 |
| `split_7d` | 9.6 % | 4.8 | 0.596; 0.545; 0.324 |

- No HIST control is missing in any of the 7,800 rows.
- On the 104 test weeks the non-zero shares of block V are 37.1 %, 55.9 %, 16.9 %, 31.9 %, 14.2 % and 8.2 %,
  and both steps leave 0.304, 0.317, 0.391, 0.428, 0.473 and 0.337 of the rank variance.
- Block V is sparse and far from independent of the controls. Its ranks correlate at 0.40 to 0.74 with
  `attn_7d`, at 0.26 to 0.43 with `dvol_30d` and at −0.24 to −0.41 with `rv_7d` and `rv_30d`: assets with many
  typed events are the large, liquid, less volatile ones. A raw correlation of block V with next week's
  volatility would mostly restate that. This is the reason for the partial design of §3.2.
- The dependence is not linear. The flexible step of §3.2 removes a further part of the rank variance that
  the within-week linear step leaves, most for `split_7d` (0.545 to 0.324) and `unfav_7d` (0.518 to 0.387).
  This is the reason for the two steps of §3.2.
- The table is reproduced by `research/multiagent-v2/charter3_design/decision_time_facts.py` (output
  `decision_time_facts.json`).

### 3.2 Partial design (the gate)

The 14 controls (HIST and block A) are removed from the target and from every block-V feature in two steps.
A model is then fitted on what is left.

1. **Flexible step, target.** A quadratic surface of the 14 control ranks is subtracted from the target rank:
   intercept, the ranks, their centred squares and all pairwise products, 120 columns. It is fitted by ridge
   (penalty 1.0, intercept not penalised) on the pooled rows of all earlier weeks, whose forward week has
   closed by the decision, and is refitted every week. The first 26 weeks are fitted on themselves. They lie
   inside the training-only period and are never scored.
2. **Flexible step, features.** From the rank of every block-V feature the prediction of boosted trees on the
   14 control ranks is subtracted. The trees are refitted every 13 weeks on all weeks before the refit week
   and serve the weeks up to the next refit. The first 26 weeks are fitted on themselves. LightGBM with
   300 rounds, learning rate 0.05, 8 leaves, depth 3 and at least 50 rows per leaf; the other settings are
   those of Charter 2 (§3.3). This step uses decision-time data only and no outcome.
3. **Within-week step.** In every week, what the flexible step leaves of the target rank and of every
   feature rank is regressed by OLS with intercept on the 14 control ranks. A week needs at least 30 rows
   with the target. The residual of the target is `e_reader`. The residuals of the features are the
   regressors of the model.
4. **Model.** A ridge regression without intercept (penalty 10) of `e_reader` on the six residual features
   is fitted walk-forward on the pooled earlier weeks. A week is forecast from the weeks whose forward week
   has closed by its decision. The first 52 weeks are training only. The fitted value is the score
   `s_reader`, on 104 test weeks.
5. **Statistic.** The weekly Pearson correlation of `s_reader` with `e_reader` across the assets of the week
   (at least 30 rows): the weekly partial correlation of the reader score with the target.

- **Why two steps.** The first design of this draft had the within-week step only. On simulated targets
  that hold no reader information it passed in 4.8 % to 14.7 % of the draws, where an unbiased gate of this
  form passes in about 3 % (§4.1). The within-week step removes what is linear in the control ranks. Block V
  depends on the controls in a curved way (§3.1), and so can the target. What is left on the two sides then
  correlates without any reader information. The flexible step removes curved dependence on each side. A
  spurious relation needs a leftover on both sides: its size is the product of the two fitting errors.
- **Why earlier weeks only.** Next week's `rv_7d` is this week's target. A flexible fit that includes later
  weeks can see the target of a week through the controls of the following week. Both flexible fits use
  earlier weeks only, and the surface of the target uses only weeks whose outcome has closed by the decision.
- **Why trees on one side and a surface on the other.** The surface is linear in its parameters. It is
  refitted every week from running sums, which matters on the target side, where every week adds outcomes.
  The feature side uses no outcome, so trees that are refitted once a quarter suffice there. Among the
  four variants that use earlier weeks only, none had a lower pass rate on noise than this pair in any
  noise cell of the comparison (§4.1, Appendix B). Trees on the target side were not tried.
- In step 3 the controls are fitted inside the week of the outcome, which gives them the best linear fit
  that week allows. The reader block is fitted on earlier weeks only. The asymmetry works against the reader
  block and is intended.
- A comparison of two forecasts with and without block V is reported as a descriptive panel (§3.3, §5). It is
  not the gate: both forecasts are dominated by the history part, and the difference of two large correlated
  numbers is a noisier statistic than the partial correlation.

### 3.3 Scores

Partial scores. Each is the ridge score of steps 4 and 5 of §3.2 for its own features and controls.

| Score | Tested features | Controls | Removal of the controls | Role |
|---|---|---|---|---|
| `s_reader` | block V (6) | HIST and block A (14) | both steps | gate score (§5) |
| `s_reader_lin` | block V | HIST and block A | within-week step only | descriptive: the first design of this draft (§4.1) |
| `s_reader_sq` | block V | HIST and block A, and the squares of the 8 bar-history ranks | within-week step only | descriptive: a simpler correction for a curved relation to price history |
| `s_reader_hist` | block V | HIST (12) | both steps | descriptive: reader features beyond price history only |
| `s_text` | block A and block V (8) | HIST | both steps | descriptive: all text beyond price history |
| `s_attn` | block A (2) | HIST | both steps | descriptive: attention counts beyond price history |

Forecasts of the target rank from feature ranks, walk-forward, no control removed.

| Score | Model | Features | Role |
|---|---|---|---|
| `v_hist` | ridge | HIST (12) | descriptive forecast |
| `v_hist_attn` | ridge | HIST and block A (14) | descriptive forecast |
| `v_full` | ridge | HIST, block A and block V (20) | descriptive forecast |
| `g_hist_attn`, `g_full` | boosted trees | as the ridge forecasts with 14 and 20 features | descriptive forecast |

- Ridge: without intercept, penalty 10, refitted every week, burn-in 52 weeks, as in Charter 2.
- Boosted-tree forecasts: LightGBM with the parameters of Charter 2, fixed in advance and not tuned on any
  outcome: 200 rounds, learning rate 0.03, 4 leaves, depth 2, at least 100 rows per leaf, feature and row
  sampling 0.8, L2 penalty 10, fixed seed, one thread, deterministic mode. No gate depends on them.
- With 12 controls the surface of the flexible step has 91 columns. Every other setting of the two steps is
  that of §3.2.
- The gate score is fitted without a guard. A failure of any other fit leaves its column empty, is recorded in
  the output and cannot change the verdict.
- Only `s_reader` enters the verdict. A pass of `s_reader_lin` or `s_reader_sq` next to a fail of `s_reader`
  is a FAIL.

### 3.4 No decision layer

A volatility rank is not a position, so no book is built and no profit is computed. In the framework the
forecast would enter the risk side: sizing and limits. A PASS states that the reader records improve a risk
forecast. It states nothing on returns.

## 4. Stages

| Stage | Content | Cost | Opens outcomes |
|---|---|---|---|
| V0 | Evaluation code, runner, registration script, tests, synthetic dry run, calibration on bars before the window, pass rate and power of the gates on synthetic targets, hardening of the gate (§4.1) | 0 | no |
| V1 | Freeze of this document (needs approval) | 0 | no |
| V2 | Registration, pre-flight, registered run with the single outcome join and the verdict | 0 | yes, once |

**V0 (complete).** The code of §7 with 79 offline tests, among them a whole registered run on a synthetic
checkout (defects stop before the claim, one counted outcome join, a repeat run is refused), the calibration
of Appendix C, the simulations of Appendix B and the design checks of §4.1.

**V1 freeze.** The draft mark in the title is removed, the status line is changed and the document is
committed. From then on it stays byte-identical: the registration records its hash and the run requires it.

**V2 registered run.** `scripts/reader_charter3_register.py` writes the registration
(`research/llm-v2-charter3-<date>/gates.json`, experiment `llm-v2c3-volatility-dev-run-<date>`, dataset
`dev-reader-volatility-2022-2024`, parent `llm-v2c2-reader-dev-run-20261112`) with the hashes of this document,
of 41 source files and of 7 inputs: items, typed documents, cards, call cache, record table, extraction
manifest and kline digest. Every input must have the bytes registered for the Charter 2 run. The frozen
Charter 2 document is one of the source files, because the records were extracted under it and the extraction
manifest names its hash. `scripts/reader_charter3_run.py` then runs in this order.
1. Before the claim: the manifest is checked against the registration, the records are rebuilt from the
   registered cache and must equal the record table, the text features and the price-history features are
   built, the kline store is verified against its digest (799 files), and the whole evaluation is rehearsed on
   seeded synthetic targets. `--preflight-only` stops here.
2. The claim (attempt 4 of 6).
3. The same preparation through the registered inputs, then the forward targets as the single outcome join.
4. Evaluation and the four outputs: `forecasts.json`, `evaluation.json`, `reader.json`, `verdict.json`. The
   run makes no model call.

The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
window under this charter.

No block is evaluated on its own before the run. Attention counts and price history exist at no cost, and
opening them first against the volatility outcome would condition the reading of block V on an outcome of
the same window.

### 4.1 Finding of stage V0: the first gate passed on noise

The first design of this draft removed the controls in the within-week step only. It is now the descriptive
score `s_reader_lin`. Its pass rate was measured on synthetic targets that hold no reader information, built
on the real decision-time regressors (Appendix B). An unbiased gate of this form passes on noise in about
3 % of the draws: 2.3 % for a normal statistic at a one-sided threshold of 2.0, somewhat more because a t
statistic of 104 weekly values has heavier tails, somewhat less because G2 fails some of those draws. On a
synthetic panel whose text features are independent of everything else the first design passed in 3.15 % and
2.85 % of 2,000 draws. On the real regressors it passed more often.

| Synthetic target, 2,000 draws per cell | First design: pass rate, mean weekly partial correlation | Registered design: pass rate, mean weekly partial correlation |
|---|---|---|
| linear in the history ranks, no persistence | 4.80 %, +0.0025 | 2.60 %, −0.0002 |
| curved in the history ranks, no persistence | 11.00 %, +0.0097 | 2.75 %, +0.0000 |
| linear, persistence 0.3 | 6.70 %, +0.0060 | 4.30 %, +0.0034 |
| curved, persistence 0.3 | 12.20 %, +0.0122 | 4.95 %, +0.0038 |
| curved, persistence 0.6 | 14.65 %, +0.0165 | 7.50 %, +0.0088 |

Two channels.
- **Curvature.** Block V is a curved function of the controls (§3.1). A target that is a curved function of
  price history leaves a part of that function in a linear residual, and the leftovers of the two sides
  correlate. The first design was biased upward even for a target that is linear in the history ranks
  (+0.0025, 4.80 %). The likely cause is the rank of the target, which bends a linear relation.
- **Persistence.** When the part of an asset's volatility that no control sees persists from week to week
  and the text features of the asset persist as well, a chance relation of the training weeks carries over
  into the test week. The score learns the asset, the weekly values are positive on average and the gates
  pass too often.

Nine ways of removing the controls were compared on 300 common seeds in four cells (Appendix B, evidence in
`research/multiagent-v2/charter3_design/`): squares in the within-week step, and trees or a quadratic surface
subtracted from the features, from the target or from both, fitted across blocks of weeks or on earlier
weeks only. The registered design (§3.2) was chosen for three reasons.
- It uses earlier weeks only on both sides. No argument is needed about what a later week reveals.
- Among the four variants of that kind none had a lower pass rate on noise in any noise cell of the
  comparison.
- On 2,000 draws per cell its mean on noise without persistence is zero (−0.0002 and +0.0000) and its pass
  rate is 2.60 % for the linear and 2.75 % for the curved shape.

The registered design does not remove the persistence channel (4.30 % to 7.50 % in the table). §5 states how
the run shows which row applies, and Appendix C why no persistence is expected.

The cost is power at a given planted strength. A planted effect of strength 0.075 passed in 76.8 % of the
draws under the first design and passes in 48.4 % under the registered one. Most of the difference is scale:
the flexible step credits to the controls the part of a planted effect that a curved function of the
controls can represent, so the same planted strength gives a smaller partial correlation (0.031 against
0.045). At an equal partial correlation of 0.045 the two designs pass about equally often (77 % and 78 %).

Every choice of this section was made on synthetic targets. No realised variance of the window was joined
with a text feature and no gate statistic was computed on real outcomes. The first design stays in the
outputs as `s_reader_lin`, so that the effect of the hardening on the real result is visible. It has no
weight in the verdict.

## 5. Gates

One primary statistic and one stability condition, as in Charter 2.

- **G1 (primary).** The weekly partial correlation of `s_reader` with `e_reader` (§3.2) on the test weeks.
  Statistic: Newey-West t (lag 4) of its mean. Rule: t at least 2.0 and mean positive.
- **G2 (stability).** The mean weekly partial correlation is positive in 2023 and in 2024 (calendar year of
  the Friday).
- **Verdict.** PASS when G1 and G2 hold. Otherwise FAIL. A statistic that cannot be computed fails its gate.
  No descriptive score enters the verdict.
- **Size reading (no gate).** With a PASS, the mean weekly partial correlation is read as "visible" when it
  is at least 0.07 and as "thin" below. The value is written into `verdict.json` by code. A partial correlation
  of 0.07 removes about half a percent of the variance that the controls leave unexplained (0.07 squared),
  which is the scale of the thin pass of the per-token on-chain panel (B8). Below it a pass is statistically
  present and of no practical use for a risk forecast.

Descriptive, no gate (`evaluation.json`, `reader.json`):
- Every partial score of §3.3: weekly partial correlation with Newey-West t at lag 4 and at lag 12, by year,
  the share of the residual variance explained out of sample, the share of the target variance that the
  controls leave, the correlation of every single residual feature with the target residual, and the ridge
  coefficient paths.
- The forecasts of §3.3: rank IC and mean squared error on the test weeks, and the weekly loss differences of
  the nested pairs (`v_hist_attn` against `v_full`, `v_hist` against `v_hist_attn`, `v_hist` against `v_full`,
  `g_hist_attn` against `g_full`).
- The gate statistic with another target and unchanged features, controls and steps: the log of the
  variance standardised within the week, `fwd_absret`, `fwd_drawdown` and `fwd_maxday`.
- What each step of §3.2 removes: the share of the rank variance of the target and of every block-V
  feature that is left on the test weeks after the within-week step alone and after both steps.
- Permutation placebo: the gate statistic after the feature rows are permuted across the assets of every
  week, 500 draws, seed 20261113.
- Shift placebo: the gate statistic with every asset's residual features taken from 13, 26 and 52 weeks
  earlier and later. The asset is kept and the timing is broken.
- Autocorrelation of the target residual within an asset at 1, 2, 4 and 8 weeks. It places the result in
  a row of the noise table (below and Appendix B).
- Feature and target coverage, and the quality report of the reader records.
An error in a descriptive part is listed in `verdict.json` and cannot change the verdict.

What each verdict licenses:
- PASS on the development window is not a claim. It licenses building the text of Sealed-A and Sealed-B and
  one confirmation run there under a further charter. The size reading states how the result is described:
  "visible" as a candidate input of the risk layer, "thin" as a statistical relation without practical weight.
- FAIL closes weekly relative volatility from the reader records. The records stay as an input of the two
  remaining changes (§9).
- In both cases the rows `s_attn` and `s_text` show whether counting items, with no reader judgement, carries
  volatility information beyond price history. That result needs no language model. It is reported and
  nothing is claimed from it.

Power. On the real regressors with an effect planted in block V (Appendix B, 1,000 draws per cell), the gates
pass in 20 % of the draws when the mean weekly partial correlation is 0.017, in 48 % at 0.031, in 78 % at
0.045 and in 99 % at 0.074. A relation of the visible size (0.07) is found almost surely. A relation near
0.03 is found about every second time. A FAIL therefore excludes a visible relation and does not exclude a
thin one.

Pass rate on noise. On the real regressors with a synthetic target that holds no reader information
(Appendix B, 2,000 draws per cell), the gates pass in 2.60 % of the draws when the target is linear in the
history ranks and in 2.75 % when it is curved, with a mean weekly partial correlation of zero. These cells
match the calibration on the bars of 2021, which shows neither persistence nor curvature of the residual
(Appendix C). When the part of the target that no control sees persists within an asset, the gates pass more
often: in 4.30 % and 4.95 % of the draws at a weekly persistence of 0.3 and in 7.50 % at 0.6. The run reports
the autocorrelation of the target residual within an asset. In the simulations that value is 0.00 at one
week without persistence, 0.21 to 0.22 at persistence 0.3 and 0.43 at 0.6, so the reported value states
which row of the noise table applies to the result. In real data a persistent part of an asset's volatility
enters the price history of the following weeks and is controlled there. The simulation withholds it from
the controls on purpose, so the persistent rows are stress cases. No noise draw at a persistence of 0 or 0.3
was read as visible (0 of 10,000), and 3 of 2,000 at 0.6.

## 6. Leakage and exposure

- **The window is exposed.** The 104 test weeks were opened by Charter 2 for the return target, and 66 of
  them before that by Charter 1b. The daily bars of the window were used by earlier programmes of the
  repository, also for volatility forecasts from price, option and on-chain data.
- **What was known when the design was fixed.** The outputs of Charter 2: attention counts carried the weak
  return relation, reader judgements none, and the ridge coefficient of `unfav_7d` was positive in every test
  week. Each of these relates a text feature to the signed return of the next week. None relates a text
  feature to a variance, a range or an absolute move. The decision to control for attention and to test the
  reader block alone follows from that result and from the on-chain programmes of §1.
- **What was not looked at.** Before the registered run no feature built from the records is joined with a
  realised variance, a range or any other price quantity dated after its decision, and no gate statistic of
  this charter is computed on real outcomes. The text features were joined with price history up to the
  decision only: for the facts of §3.1, for the flexible step on the feature side, and for the simulations
  of §4.1 and Appendix B, in which every target is synthetic.
- **The design changed once before the freeze.** The gate was hardened in stage V0 (§4.1). The change was
  decided on synthetic targets alone, it lowers the pass rate on noise, and both designs are reported.
- **Bars before the window.** The persistence of the target residual and the curvature of its relation to
  price history were measured on bars dated before 2022-01-01, from price alone (Appendix C). No card and
  no text exists for that period.
- **News about a price move.** Some items exist because the price moved, and volatility clusters. Such an
  item predicts next week's volatility through the move that it reports. The history block holds the
  variance of the last day, week, month and quarter, the largest daily variance, the weekly return and its
  absolute value, and the volume surge, so that this channel is in the controls.
- **Attention as an activity proxy.** The number of items rises with price activity. Block A is a control of
  the gate, so a reader block that only restates "more items" does not pass. A test plants a signal in the
  attention counts and checks that it appears in `s_attn` and not in `s_reader`.
- **Curved relation to history.** Found in stage V0 (§4.1). With the controls removed linearly inside the
  week, a target that is a curved function of price history passed the gates on noise in 11 % of the draws,
  because block V is itself a curved function of the controls (§3.1). The registered gate removes the
  controls from both sides in a flexible step first (§3.2). On simulated targets its mean is zero for the
  linear and for the curved shape. Limits: the curved shape of the simulation (a square, an interaction and
  a kink of history ranks) lies largely inside what a quadratic surface can represent, and with the trees on
  the feature side alone 4.67 % of 300 curved draws still passed. A dependence that neither the trees nor
  the surface represents could still pass. For that reason `s_reader_lin`, `s_reader_sq` and the table of
  what each step removes are reported next to the gate.
- **Persistence.** If an asset stays more volatile than its controls predict for many weeks, and its text
  features persist as well, the score learns the asset and the Newey-West t at lag 4 is too generous. The
  hardening does not remove this channel: on simulated targets the gates pass in 4.3 % to 5.0 % of the noise
  draws at a weekly persistence of 0.3 and in 7.5 % at 0.6 (§5). Checks: the calibration on earlier bars
  finds no persistence of the residual (Appendix C), the run reports the residual autocorrelation, which
  places the result in a row of the noise table, and the outputs carry the t at lag 12 and the shift placebo.
- **Option-implied volatility is not in the baseline.** For BTC and ETH the option market forecasts
  volatility better than price history (`rviv-p0`). No such series exists for the cross-section. A PASS
  therefore means "beyond price history and attention", not "beyond what the market already prices".
- **Hindsight in the reader.** The reader saw de-identified summaries and recorded what they state. A famous
  episode could still be recognised and colour `materiality`. Controls as in Charter 2: evidence must be
  verbatim, magnitudes come from the text, and the fitted model learns from earlier weeks only. Sealed-B
  stays the arbiter.
- **Timing.** The forward week of a Friday ends with the bar that closes at the next decision. A week is
  trained on only when that bar has closed. The tests check that the forward week of one Friday equals the
  trailing week of the next.
- **Delisted contracts.** The universe comes from the cards of each Friday and the kline store keeps
  delisted contracts. A forward week with fewer than seven bars uses the bars present; `fwd_bars` counts
  them and the target coverage reports the short weeks.
- The registered run rehearses on synthetic targets before the claim and joins the real forward targets
  once, after the claim.

## 7. What is fixed and what is reused

Reused without change: everything of Charter 2 up to the record table (text store, typing, reading sets,
reader agents, adjudicator, call cache, 53,330 records, $5.75 paid), the attention counts, the cards and the
universe, the daily bars, the ridge and boosted-tree fitters (`tradingagents/reader/model.py`) and the run
lifecycle (`tradingagents.research`).

New under this charter:

| File | Content |
|---|---|
| `tradingagents/reader/charter3.py` | bar history, forward targets, block V, panel, removal of the controls in two steps, gates, descriptive panels, verdict |
| `scripts/reader_charter3_register.py`, `scripts/reader_charter3_run.py` | registration and registered run |
| `scripts/reader_charter3_null_gate.py` | calibration, pass rate and power on synthetic targets (not part of the run) |
| `tests/research/test_reader_charter3.py` | tests |
| `research/multiagent-v2/charter3_null_gate.jsonl`, `charter3_null_gate_power.jsonl` | draws of the registered design on synthetic targets: noise, planted effect |
| `research/multiagent-v2/charter3_null_gate_first_design.jsonl`, `charter3_null_gate_first_design_power.jsonl` | the same for the first design |
| `research/multiagent-v2/charter3_design/` | design checks of §4.1, decision-time facts of §3.1, persistence scale, builder of the tables of Appendix B |

Fixed by the freeze and pinned by the registration: this document, the source files, the gates of §5 and
every constant quoted in §3 to §5 and in Appendix A.

## 8. Budget

| Item | Amount |
|---|---|
| Model calls | none |
| Features, model, evaluation, registered run | local, 0 |
| **Cap of this charter** | **$0** |

- The account balance of about $4.86 is not touched.
- Confirmation on the sealed windows is outside this charter and only follows a PASS. Its cost is that of
  Charter 2 §8: news fetch for 2025 and 2026 (free, about a week), cards rebuilt to December 2026, typing
  about $8, extraction about $4. A top-up of about $10 would be needed at that point.
- Calendar: the last Sealed-B outcome (decision 2026-12-11) closes on 2026-12-18, three days before the
  planned results freeze of 2026-12-21.

## 9. Order of the four changes

| # | Change | Status | Planned as |
|---|---|---|---|
| 1 | Language model reads, fitted model forecasts | Charter 2, FAIL (t 1.39) | done |
| 2 | Different target (next-week volatility, tail risk descriptive) | Untried | This charter. No model call. |
| 3 | Fresher information (decision close to the news, not once a week) | Earlier no-go at minute scale | Charter 4. Needs an audit of capture times first. Feasible at a daily horizon only. Which target it uses is decided in its own draft, with the result of this charter known. |
| 4 | Agents compare assets directly | Tested on numeric cards (t 1.01 on 222 weeks) | Last. Only the text-based variant is new. |

Three attempts remain in the family and each change consumes one. After this charter two remain.

## 10. Decisions

The six points were open at the draft. All were decided on 2026-11-13 together with the freeze approval:
the option of the column "Implemented" stands in every row. The alternatives are recorded as considered.

| # | Point | Implemented | Alternative |
|---|---|---|---|
| 1 | What the gate tests | The reader block beyond price history and attention counts (`s_reader`). Attention counts need no reader agent, and Charter 2 found the return relation there. | All text beyond price history (`s_text`). Easier to pass, but a pass could rest on item counts alone and would say nothing on the agents. In this charter it is a descriptive row. |
| 2 | Removal of the controls (changed in stage V0) | Two steps on both sides: a flexible fit on earlier weeks, then the linear step within the week (§3.2). Pass rate on noise 2.60 % and 2.75 % without persistence. | The first design, the within-week step alone. It passes on noise in 4.8 % to 14.7 % of the draws (§4.1). In this charter it is the descriptive row `s_reader_lin`. |
| 3 | Threshold of G1 | t at least 2.0, as in Charter 1b and Charter 2. Pass rate on noise 2.60 % and 2.75 % without persistence, 4.30 % and 4.95 % at a persistence of 0.3. | t at least 2.3. Pass rate on noise 1.1 % to 1.5 % without persistence and 2.3 % at a persistence of 0.3. Power falls from 78 % to 69 % at a partial correlation of 0.045 and from 48 % to 37 % at 0.031 (Appendix B). |
| 4 | Size of a pass | Reading rule at 0.07, written by code, no gate. | A third gate with that floor. No noise draw at a persistence of 0 or 0.3 would pass (0 of 10,000). Power would fall from 99 % to 61 % at a partial correlation of 0.074 and from 78 % to 7 % at 0.045, because the estimate of a visible effect scatters around the floor. |
| 5 | Gate target | Realised variance of the next seven days. Tail measures are descriptive variants. | A tail measure as the gate target. Noisier, and the one earlier tail programme found tail days not led by news. |
| 6 | Attempt accounting | Attempt 4 of 6 in the family `llm-multiagent-v2`. | |

## Appendix A. Definitions

- **Garman-Klass variance of a daily bar:** 0.5 · ln(high / low)² − (2 ln 2 − 1) · ln(close / open)², not
  below 0. A bar without four positive prices is missing.
- **Forward week of a Friday:** the bars dated after the Friday and not later than Friday + 7 days. The bar
  dated Friday closes at the decision, so the forward week starts at the decision and ends at the next one.
- **`fwd_rv`:** mean Garman-Klass variance of the usable bars of the forward week. A row with no usable bar
  has no target. The number of bars used is stored as `fwd_bars`.
- **`fwd_maxday`:** largest Garman-Klass variance of a bar of the forward week.
- **`fwd_absret`:** absolute log return from the Friday close to the close of the last bar of the forward week.
- **`fwd_drawdown`:** the fall of the lowest daily low of the forward week below the Friday close, as a log
  return with the sign turned (a larger value is a deeper fall).
- **Target rank:** percentile rank within the week over the rows that have the target, minus 0.5.
- **Log variant:** ln(max(`fwd_rv`, 1e-10)), standardised within the week.
- **History windows:** a window of n days ending at the Friday bar holds the bars dated later than Friday − n
  days and not later than the Friday. A 7-day window needs at least 4 bars, a 30-day or 90-day window at
  least 10 bars; otherwise the value is missing and the asset takes the neutral rank.
- **Training weeks of a decision:** the weeks whose Friday is at least seven days before the Friday of the
  decision.
- **Weekly statistics:** a within-week regression or correlation needs at least 30 rows with the target.
- **Newey-West t:** of the mean of the weekly series, lag 4 for the gate and lag 12 as a descriptive value.
- **Quadratic surface (flexible step, target):** ridge regression of the target rank on an intercept, the
  control ranks, their squares minus 1/12 and their pairwise products (120 columns with 14 controls, 91 with
  12), penalty 1.0, intercept not penalised. From the 27th week on, a week is served by the surface fitted
  on the rows of all earlier weeks. One surface fitted on the first 26 weeks serves those weeks.
- **Trees (flexible step, features):** LightGBM regression of a feature rank on the control ranks, with
  300 rounds, learning rate 0.05, 8 leaves, depth 3, at least 50 rows per leaf, feature and row sampling
  0.8, L2 penalty 10, fixed seed, one thread and deterministic mode. Fitted at the 27th week and every 13
  weeks after it on all earlier weeks. One fit on the first 26 weeks serves those weeks.

## Appendix B. Pass rate and power of the gates on synthetic targets

`scripts/reader_charter3_null_gate.py`. No real outcome of the window is involved in any draw. The tables
are built from the stored draws by `research/multiagent-v2/charter3_design/tables.py`.

| Draws | File under `research/multiagent-v2/` |
|---|---|
| Registered design, noise | `charter3_null_gate.jsonl` |
| Registered design, planted effect | `charter3_null_gate_power.jsonl` |
| First design, noise | `charter3_null_gate_first_design.jsonl` |
| First design, planted effect | `charter3_null_gate_first_design_power.jsonl` |
| Nine variants on common seeds | `charter3_design/check1.jsonl`, `charter3_design/check2.jsonl` |

Two kinds of draw.
- **Real regressors, synthetic target.** The decision-time regressors of the 7,800 universe rows are kept as
  they are (price history, attention counts, block V). The target is replaced by the within-week rank of a
  synthetic log variance: a function of the price-history ranks, plus a component per asset that no regressor
  sees (weekly persistence `rho`, scale `noise`), plus, for power, a planted effect on the ranks of `evt_7d`,
  `unfav_7d`, `sched_30d` and `rumour_30d`. The "curved" shape adds a square, an interaction and a kink of
  history ranks. With scale 1.0 the controls leave about 0.33 of the target-rank variance (0.30 with the
  curved shape), with 1.3 they leave 0.43. On the bars of 2021 the 8 bar-history controls leave 0.39
  (Appendix C).
- **Synthetic panel.** A panel of the registered shape made by the fixture of the tests (156 weeks, 50 assets,
  a persistent latent volatility per asset, noisy history columns, sparse text features), with a target that
  is independent of the text features. `rho` is the weekly persistence of the part of the target that no
  regressor sees. This kind was run for the first design only. The registered design fits trees in every
  such draw (about 40 seconds), and the excess pass rate came from the real regressors, not from this panel.

Columns. "G1 alone" counts the draws with t at least 2.0 and a positive mean. "PASS with t at lag 12" applies
the gates with a Newey-West lag of 12 in place of 4. "Read as visible / thin" splits the passes at a mean of
0.07. The planted strength is a coefficient of the synthetic log variance on feature ranks; the gates see the
mean weekly partial correlation that it produces, which is the column to read.

### B.1 Registered design (`s_reader`)

Noise (no planted effect), registered gates applied by the registered code:

| Regressors | `rho` | Shape | `noise` | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | t: mean, sd, 97.5 % point | G1 alone | PASS with t at lag 12 | Read as visible / thin | Target-rank variance left by the controls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 0.0 | linear | 1.0 | 2,000 | 52 | 2.60 % (1.90 % to 3.30 %) | −0.0002 | −0.02, 1.06, 2.04 | 53 | 76 | 0 / 52 | 0.327 |
| real | 0.0 | linear | 1.3 | 2,000 | 52 | 2.60 % (1.90 % to 3.30 %) | −0.0002 | −0.02, 1.06, 2.04 | 56 | 69 | 0 / 52 | 0.425 |
| real | 0.0 | curved | 1.0 | 2,000 | 55 | 2.75 % (2.03 % to 3.47 %) | +0.0000 | −0.00, 1.06, 2.04 | 57 | 85 | 0 / 55 | 0.296 |
| real | 0.3 | linear | 1.0 | 2,000 | 86 | 4.30 % (3.41 % to 5.19 %) | +0.0034 | +0.20, 1.05, 2.25 | 88 | 120 | 0 / 86 | 0.327 |
| real | 0.3 | curved | 1.0 | 2,000 | 99 | 4.95 % (4.00 % to 5.90 %) | +0.0038 | +0.22, 1.03, 2.28 | 99 | 116 | 0 / 99 | 0.296 |
| real | 0.6 | curved | 1.0 | 2,000 | 150 | 7.50 % (6.35 % to 8.65 %) | +0.0088 | +0.46, 1.03, 2.57 | 150 | 167 | 3 / 147 | 0.296 |

- The rows with `noise` 1.0 and 1.3 share their seeds. They are close to the same draws and are not
  independent evidence.
- Scale of `rho` (`charter3_design/check3.json`, 20 seeds): the autocorrelation of the target residual
  within an asset is 0.00 at every lag for `rho` 0; 0.21 to 0.22, 0.06 and 0.01 at 1, 2 and 4 weeks for
  `rho` 0.3; 0.43, 0.25, 0.08 and 0.01 at 1, 2, 4 and 8 weeks for `rho` 0.6. The run reports the same
  quantity.

Power (planted effect of the given strength):

| Planted strength | `rho` | Shape | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | Mean t | Read as visible / thin |
|---|---|---|---|---|---|---|---|---|
| 0.025 | 0.0 | linear | 1,000 | 63 | 6.3 % (4.8 % to 7.8 %) | +0.0049 | 0.31 | 0 / 63 |
| 0.05 | 0.0 | linear | 1,000 | 199 | 19.9 % (17.4 % to 22.4 %) | +0.0165 | 1.06 | 1 / 198 |
| 0.075 | 0.0 | linear | 1,000 | 484 | 48.4 % (45.3 % to 51.5 %) | +0.0306 | 1.95 | 11 / 473 |
| 0.1 | 0.0 | linear | 1,000 | 779 | 77.9 % (75.3 % to 80.5 %) | +0.0454 | 2.90 | 67 / 712 |
| 0.15 | 0.0 | linear | 1,000 | 994 | 99.4 % (98.9 % to 99.9 %) | +0.0742 | 4.77 | 613 / 381 |
| 0.075 | 0.3 | curved | 1,000 | 407 | 40.7 % (37.7 % to 43.7 %) | +0.0312 | 1.80 | 22 / 385 |

### B.2 First design (`s_reader_lin`)

Noise:

| Regressors | `rho` | Shape | `noise` | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | t: mean, sd, 97.5 % point | G1 alone | PASS with t at lag 12 | Read as visible / thin | Target-rank variance left by the controls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 0.0 | linear | 1.0 | 2,000 | 96 | 4.80 % (3.86 % to 5.74 %) | +0.0025 | +0.16, 1.11, 2.34 | 98 | 133 | 1 / 95 | 0.323 |
| real | 0.0 | linear | 1.3 | 2,000 | 66 | 3.30 % (2.52 % to 4.08 %) | +0.0007 | +0.05, 1.08, 2.10 | 67 | 97 | 0 / 66 | 0.420 |
| real | 0.0 | curved | 1.0 | 2,000 | 220 | 11.00 % (9.63 % to 12.37 %) | +0.0097 | +0.60, 1.13, 2.76 | 223 | 259 | 2 / 218 | 0.320 |
| real | 0.3 | linear | 1.0 | 2,000 | 134 | 6.70 % (5.60 % to 7.80 %) | +0.0060 | +0.36, 1.09, 2.57 | 135 | 166 | 1 / 133 | 0.323 |
| real | 0.3 | curved | 1.0 | 2,000 | 244 | 12.20 % (10.77 % to 13.63 %) | +0.0122 | +0.68, 1.14, 3.04 | 247 | 272 | 3 / 241 | 0.320 |
| real | 0.6 | curved | 1.0 | 2,000 | 293 | 14.65 % (13.10 % to 16.20 %) | +0.0165 | +0.83, 1.15, 3.30 | 302 | 307 | 26 / 267 | 0.321 |
| synthetic panel | 0.0 | | | 2,000 | 63 | 3.15 % (2.38 % to 3.92 %) | +0.0003 | +0.01, 1.07, 2.19 | 65 | 89 | 0 / 63 |  |
| synthetic panel | 0.3 | | | 2,000 | 57 | 2.85 % (2.12 % to 3.58 %) | +0.0002 | +0.01, 1.07, 2.09 | 57 | 81 | 0 / 57 |  |

Power:

| Planted strength | `rho` | Shape | Draws | PASS | Pass rate (95 % interval) | Mean weekly partial correlation | Mean t | Read as visible / thin |
|---|---|---|---|---|---|---|---|---|
| 0.025 | 0.0 | linear | 1,000 | 155 | 15.5 % (13.3 % to 17.7 %) | +0.0123 | 0.80 | 1 / 154 |
| 0.05 | 0.0 | linear | 1,000 | 418 | 41.8 % (38.7 % to 44.9 %) | +0.0278 | 1.81 | 8 / 410 |
| 0.075 | 0.0 | linear | 1,000 | 768 | 76.8 % (74.2 % to 79.4 %) | +0.0446 | 2.91 | 69 / 699 |
| 0.1 | 0.0 | linear | 1,000 | 957 | 95.7 % (94.4 % to 97.0 %) | +0.0616 | 4.02 | 314 / 643 |
| 0.15 | 0.0 | linear | 1,000 | 1000 | 100.0 % (100.0 % to 100.0 %) | +0.0944 | 6.18 | 944 / 56 |
| 0.075 | 0.3 | curved | 1,000 | 675 | 67.5 % (64.6 % to 70.4 %) | +0.0465 | 2.55 | 124 / 551 |

### B.3 Nine ways of removing the controls

300 common seeds per cell, real regressors. Every cell gives the pass rate and the mean weekly partial
correlation. The standard error of a pass rate near 4 % on 300 draws is 1.1 points, so differences of one
or two points between variants are not established. The paired standard error of a difference of the mean
partial correlation to the first design is 0.0004 to 0.0012.

| Removal of the controls before the walk-forward fit | linear, noise (300 seeds) | curved, noise (300 seeds) | curved, `rho` 0.3, noise (300 seeds) | linear, planted 0.075 (300 seeds) |
|---|---|---|---|---|
| first design: within-week linear step only (`s_reader_lin`) | 4.67 %, +0.0033 | 10.67 %, +0.0104 | 10.33 %, +0.0129 | 77.67 %, +0.0449 |
| squares of the 8 bar-history ranks added to the within-week step (`s_reader_sq`) | 5.00 %, +0.0015 | 3.00 %, −0.0003 | 3.33 %, +0.0039 | 60.00 %, +0.0415 |
| features: trees cross-fitted over 6 blocks of weeks (parameters of Charter 2) | 4.00 %, +0.0005 | 3.67 %, +0.0031 | 4.00 %, +0.0058 | 55.00 %, +0.0336 |
| features: trees cross-fitted over 6 blocks of weeks (parameters of §3.2) | 3.67 %, +0.0003 | 2.33 %, +0.0009 | 2.67 %, +0.0038 | 50.00 %, +0.0314 |
| the same, and the squares in the within-week step | 3.67 %, −0.0002 | 2.33 %, −0.0009 | 2.33 %, +0.0027 | 36.67 %, +0.0298 |
| features: quadratic surface fitted on earlier weeks | 5.67 %, +0.0017 | 6.00 %, +0.0034 | 6.00 %, +0.0062 | 65.67 %, +0.0378 |
| features: trees fitted on earlier weeks | 3.67 %, +0.0003 | 4.67 %, +0.0044 | 4.67 %, +0.0069 | 52.00 %, +0.0330 |
| features and target: quadratic surface fitted on earlier weeks | 5.67 %, +0.0014 | 5.00 %, +0.0019 | 6.00 %, +0.0054 | 60.33 %, +0.0355 |
| **registered:** features: trees on earlier weeks; target: quadratic surface on earlier weeks | 3.67 %, −0.0002 | 3.00 %, −0.0000 | 3.33 %, +0.0037 | 48.00 %, +0.0310 |

- The variants fitted across blocks of weeks use weeks after the scored week. They hold the pass rate on
  noise as well as the registered design. They were set aside only because they use later weeks.
- The variant with squares in the within-week step is favoured by the simulated curved shape, whose largest
  curved term is the square of a history rank. For the linear shape it keeps a positive mean (+0.0015).
- The registered design was then run on 2,000 draws per noise cell and 1,000 per power cell (B.1). The 300
  seeds of the comparison are the first 300 of those draws. On the 1,700 noise seeds that had no part in the
  choice it passes in 2.41 % (linear), 2.47 % (linear, `noise` 1.3) and 2.71 % (curved) of the draws without
  persistence, in 4.35 % and 5.24 % at `rho` 0.3 and in 7.82 % at `rho` 0.6.

### B.4 Other thresholds on the draws of the registered design

Pass rate when G1 asks for another t, G2 unchanged, and when a third gate asks for a mean of at least 0.07
(§10, points 3 and 4):

| Draws | t at least 2 | t at least 2.3 | t at least 2.5 | t at least 2 and mean at least 0.07 |
|---|---|---|---|---|
| linear, `rho` 0.0, noise, scale 1.0 | 2.60 % | 1.10 % | 0.85 % | 0.00 % |
| linear, `rho` 0.0, noise, scale 1.3 | 2.60 % | 1.15 % | 0.70 % | 0.00 % |
| curved, `rho` 0.0, noise, scale 1.0 | 2.75 % | 1.45 % | 0.95 % | 0.00 % |
| linear, `rho` 0.3, noise, scale 1.0 | 4.30 % | 2.25 % | 1.35 % | 0.00 % |
| curved, `rho` 0.3, noise, scale 1.0 | 4.95 % | 2.30 % | 1.65 % | 0.00 % |
| curved, `rho` 0.6, noise, scale 1.0 | 7.50 % | 4.35 % | 2.85 % | 0.15 % |
| linear, `rho` 0.0, planted 0.025 | 6.30 % | 3.20 % | 2.20 % | 0.00 % |
| linear, `rho` 0.0, planted 0.05 | 19.90 % | 12.40 % | 9.30 % | 0.10 % |
| linear, `rho` 0.0, planted 0.075 | 48.40 % | 36.60 % | 29.60 % | 1.10 % |
| linear, `rho` 0.0, planted 0.1 | 77.90 % | 69.40 % | 63.50 % | 6.70 % |
| linear, `rho` 0.0, planted 0.15 | 99.40 % | 98.80 % | 98.10 % | 61.30 % |
| curved, `rho` 0.3, planted 0.075 | 40.70 % | 32.10 % | 26.20 % | 2.20 % |

## Appendix C. Calibration on bars before the window

`scripts/reader_charter3_null_gate.py history`. Bars dated before 2022-01-01 only, price alone. Every Friday
of 2021 (52 weeks), the 50 contracts with the highest trailing 30-day dollar volume (2,600 rows, 107
contracts), target and bar-history ranks as registered, the 8 bar-history controls only, removed by the
within-week step.

| Quantity | Value |
|---|---|
| Share of the target-rank variance left by the bar-history controls | 0.391 |
| Autocorrelation of the target residual within an asset, 1 week | −0.039 (2,388 pairs) |
| 2 weeks | +0.019 (2,219 pairs) |
| 4 weeks | −0.000 (1,947 pairs) |
| 8 weeks | +0.047 (1,640 pairs) |
| Share left when the squares of the 8 controls are added | 0.306, against 0.315 expected from the added columns alone |
| Share of the linear residual that trees on the control ranks explain out of sample, tree settings of Charter 2 | −0.001 |
| The same, tree settings of §3.2 | −0.040 |

For scale, the last two rows on the simulated targets of Appendix B (`shapes` mode, 5 seeds): −0.001 and
−0.013 for the linear shape, +0.051 and +0.046 for the curved shape.

Once the price history of an asset is controlled linearly, what is left of next week's relative volatility
showed in 2021 neither persistence from week to week nor a curved dependence on that history. The curved and
the persistent variants of Appendix B are therefore stress cases and not the expected state. The flexible
step is registered all the same. The calibration covers one year, 8 of the 14 controls and no text, and the
first design was biased on the real regressors even for a target that is linear in the history ranks (§4.1).
