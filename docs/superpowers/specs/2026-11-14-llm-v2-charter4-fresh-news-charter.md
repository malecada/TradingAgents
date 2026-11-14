# Charter 4 — Fresher information: daily decision, next-day return (`llm-v2-charter4`) — DRAFT, NOT FROZEN

**Status:** draft. Stage V0 (code, tests, capture-time audit, synthetic dry run, pass rate and power of the
gates on synthetic targets, calibration on bars before the window) is complete. Two design choices were made
in V0 by rules written before their draws (§4.1). The open decisions are listed in §10, each with the option
that is implemented. Nothing is registered, no attempt is claimed and no feature built from the reader records
has been joined with a return or any other price quantity dated at or after its decision. The freeze needs
approval.
**Family:** `llm-multiagent-v2`, attempts used 4 of 6 (Charter 1 interrupted with a failed receipt, Charter 1b
FAIL, Charter 2 FAIL, Charter 3 FAIL). This charter is attempt 5.
**Predecessor:** `docs/superpowers/specs/2026-11-13-llm-v2-charter3-volatility-charter.md`, run
`llm-v2c3-volatility-dev-run-20261113`, verdict FAIL.

## 1. Why fresher information

Charters 2 and 3 decided once a week, on Saturday 00:00 UTC. An article published on a Monday reached the
forecast five days later. Both charters failed. For the direction of next week's relative return the text
score reached t 1.39 against a threshold of 2.0 (Charter 2). For next week's relative volatility the reader
block reached t −0.72 (Charter 3). In both runs the relation that did exist sat in the number of linked items,
which code counts without a reader agent. The judgements of the reader agents added nothing to it.

One reading of those results is that the judgements are sound and arrive too late: a liquid market has
absorbed a week-old article long before the weekly decision. This charter tests that reading. It keeps the
records and moves the decision to the news. There is one decision per day at 00:00 UTC, the reader features
are built from the items that became usable during the last day, and the target is the return of the next day
relative to the other assets of the day.

How fresh the information is depends on the stores, and the capture-time audit sets the limit (§3.1). A news
item carries its publication date without a time of day, and the time at which the store captured it. An item
enters a feature at the first midnight after its capture, and only when it was captured on its publication
date or on the day after. At the decision a fresh article has therefore been public for hours: the median time
from capture to decision is 9.9 hours, and publication came before capture. The charter does not test the
reaction to the news. It tests whether the direction judged by the reader agents continues over the day
after the news day. A finer timing cannot be built from the stores: the publication time of day is unknown
and the kline store holds daily bars.

The earlier programmes of the ledger speak against the hypothesis (table below). Liquid perpetual contracts
absorb public news within minutes to hours, and the effect that this design can detect is large against any
drift that is plausible on the day after a news day (§5, Power). A FAIL is the expected outcome. The run is
made because the order of the four changes names it (§9), because it costs no model call, and because it
closes the question whether the weekly horizon alone explains the two earlier failures.

No model call is made under this charter. The 53,330 records of Charter 2 are an input.

### Earlier programmes that bear on this (closed-programmes ledger)

| Programme | What was tested | Outcome | Bearing here |
|---|---|---|---|
| Charter 2, `llm-v2c2-reader-dev-run-20261112` | Reader records as features for weekly relative returns | FAIL, t 1.39. Attention counts carried the weak relation, reader judgements none (weekly IC 0.012, t 0.93). | Records, typing and the reading rule are reused. The decision moves from weekly to daily. Attention is a control here, not part of the tested block. |
| Charter 3, `llm-v2c3-volatility-dev-run-20261113` | Unsigned reader features for next-week relative volatility beyond price history and attention | FAIL, t −0.72. Attention counts beyond history t 3.00, carried by 2023 alone. | The two-step removal of the controls and the gate form are reused. Volatility of the next day is a descriptive variant here, not the gate. |
| `llm-c1-event-xs` (THESIS §63) | Typed-event extraction as cross-sectional features | Stopped before any outcome: pooled extraction precision 0.75 below 0.80, prefilter recall 0.70 below 0.85. | Extraction quality limits any event feature. The record quality of Charter 2 is reported again in `reader.json`. |
| `llm-c2-veto` (THESIS §62) | News-based veto of tail days | Failed: news recall 54 % below 60 %. Tail days were squeeze days, not news days. | Large daily moves are often not led by public news. A null on the next-day return is the likely outcome. |
| Sentiment index as quant feature (THESIS §33) | Daily sentiment features for BTC and ETH | All 6 registered gates failed. | A daily text signal on the two largest assets was tested and failed. Here 44.7 % of the fresh-tone rows are BTC and ETH (§3.1). |
| `sentiment-early-warning` research (July 2026) | Sentiment as a primary directional signal, headline classifiers | Judged not viable. Event-driven news trading with a language model judged no-go. | Agrees with the prior stated above. That judgement came from a review of published results (reaction at minute scale, later drift refuted). This charter is the one registered test on own records at a daily horizon. |
| On-chain B6 minute events (October 2026) | Price and volatility reaction to 100,000 large exchange deposits and withdrawals at minute scale | No reaction found. | Public event information of another kind showed no short-horizon reaction either. |
| `llm-c3p-pairwise` (THESIS §65) | Agents compare assets pairwise on numeric cards | IC +0.0079, t 1.01 on 222 weeks. | Bears on the last change (§9), not on this one. |

## 2. Question, target, universe

Universe: the contracts of a day are the 50 perpetual contracts of the last Friday card before that day, by
the rule of Charter 2 (highest trailing 30-day dollar volume each Friday; 7,800 rows, 156 Fridays, 222
contracts). A Saturday uses the card of the day before, a Friday the card of seven days before. The daily
panel has 54,300 rows on 1,086 decision days from 2022-01-08 to 2024-12-28.

Decision time: 00:00 UTC of every day D. The daily bar dated D − 1 closes at the decision. Zero latency is
assumed: the features are complete at the decision and the position is taken at the close of that bar.

Windows: development 2022-01-08 → 2024-12-28. The first 364 days are training only. The last 722 days, from
2023-01-07, are the test days (359 in 2023 and 363 in 2024, 36,100 rows). Sealed-A (2025-01 → 2026-04) and
Sealed-B (2026-05 → 2026-12-11) are untouched and their text is not built.

Target: `fwd_ret_1d`, the simple return from the close of the bar dated D − 1 to the close of the bar dated D,
taken as a percentile rank within the day minus 0.5. The rank is relative on purpose: the market moves all 50
assets together, and the framework ranks assets against each other, as in the earlier charters.

Question: does the net tone of the events that the reader agents judged for an asset, built by code from the
de-identified fact records and limited to news that became usable in the last day and in the six days before
it, carry information on the return of the next day, relative to the other assets of the day, beyond price
history up to the decision and beyond attention counts?

Three other targets of the same decision are reported as descriptive variants (§5): `fwd_absret_1d` and
`fwd_rv_1d` (size of the move of the next day) and `fwd_ret_3d` (return over three days). No bar later than
two days after the decision day is read.

## 3. Design

```
record table of Charter 2 (53,330 records) ─► block R: signed asset-day sums of fresh news (code) ─┐
item store ─► item timing rule ─► block A: attention counts (code) ───────────────┐                │
daily bars up to the decision, Friday card ─► HIST: 11 price-history controls ────┤                │
                                                                                  ▼                ▼
daily bar after the decision ─► target rank ─► controls removed              controls removed
                                               (two steps, §3.2)             (two steps, §3.2)
                                                    │                              │
                                                    └───► walk-forward ridge ◄─────┘
                                                                  │
                                                                  ▼
                                               daily partial correlation ─► gates (code)
```

### 3.1 Regressor blocks (decision-time data only)

**Item timing.** Every item row has a publication date (`event_ts`, midnight of the date) and a capture time
(`as_of_ts`). For a community post the two are equal.

- An item becomes usable at the first midnight after its capture. An item captured exactly at midnight waits
  one more day. The feature day of an item is that midnight.
- A news item is timely when its feature day is at most 2 days after its publication date, which means it was
  captured on the publication date or on the day after. A news item captured later enters no feature. A
  community post is always timely.
- "Last day" of a decision at day D means the items whose feature day is D. "Last seven days" means the
  feature days D − 6 to D.

**HIST, 11 price-history controls.** All bar features use bars dated up to D − 1, the bar that closes at the
decision. A row without that bar has every bar feature missing.

| Feature | Definition |
|---|---|
| `ret_1d`, `ret_7d`, `ret_30d` | log return of the close over the last 1, 7 and 30 days (the earlier bar must exist) |
| `rv_1d` | Garman-Klass variance of the last bar |
| `rv_7d` | mean Garman-Klass variance of the last 7 days, at least 4 bars |
| `rv_30d` | mean Garman-Klass variance of the last 30 days, at least 10 bars |
| `vsurge_1d` | log of the dollar volume of the last bar over its mean of the last 30 days |
| `dvol_30d` | mean dollar volume of the last 30 days |
| `beta_60d` | covariance of the daily log return with that of BTCUSDT over its variance, last 60 days, at least 30 pairs |
| `age_weeks`, `funding_3d` | card columns of the last Friday card before the day |

**Block A, 4 attention controls.** Counts of distinct documents linked to the asset at any salience.

| Feature | Definition |
|---|---|
| `news_1d` | log(1 + timely news documents of the last day) |
| `posts_1d` | log(1 + community posts of the last day) |
| `attn_7d` | log(1 + timely news documents and community posts of the last seven days) |
| `attn_abn_1d` | log(1 + documents of the last day) minus the asset's mean of the same daily value over the 28 preceding days inside the store. With fewer than 14 such days the value is missing. |

**Block R, 6 reader features.** Built from timely news item rows joined with their record, restricted to
resolved records about the asset as the subject. Community posts enter the counts of block A only. Events
(item type `event`) that are equal on class, status and direction within an asset-day count once, at their
highest materiality. Opinion items are those of type `analysis_opinion`.

| Feature | Definition |
|---|---|
| `tone_1d` | sum over the events of the last day of direction sign (favourable +1, unfavourable −1, else 0) times materiality |
| `unfav_1d` | materiality of the unfavourable events of the last day |
| `evt_1d` | materiality of all events of the last day |
| `stance_1d` | favourable minus unfavourable opinion items of the last day |
| `tone_prev6` | sum of the daily tone over the six days before the last day |
| `unfav_prev6` | sum of the daily unfavourable materiality over the six days before the last day |

The gate uses two of them: `tone_1d` and `tone_prev6` (§3.3, §4.1). The other four enter descriptive scores.

**Counts, not regressors.** `n_subject_1d` and `n_subject_7d` count the subject records behind block R.
`gap_1d` and `gap_7d` count timely news item rows of the asset that have no judgement although the reading
rule of Charter 2 would have asked for one: rows without a type, and rows that the rule reads and that have
no record. Charter 2 typed and read an item for the assets that were members on one of the Fridays of the 30
days after its publication. An asset that was a member on the last Friday before the decision and on none of
those later Fridays can therefore have an unread item. Such a row counts as no record. The gate is reported a
second time without the rows that have `gap_7d` above zero (§5).

**Missing values.** Every regressor enters as a percentile rank within the day minus 0.5. A missing value
takes the neutral rank 0.

**Decision-time facts (no price outcome is used; `research/multiagent-v2/charter4_design/decision_facts.json`).**

Timing of the 138,428 news item rows of the store:

| | all | 2022 | 2023 | 2024 |
|---|---|---|---|---|
| news item rows | 138,428 | 48,017 | 41,634 | 48,699 |
| timely | 88.0 % | 80.4 % | 92.5 % | 91.6 % |
| usable one day after the publication date | 81.0 % | 76.8 % | 84.9 % | 81.9 % |
| usable two days after | 6.9 % | 3.6 % | 7.6 % | 9.7 % |
| later (enters no feature) | 12.0 % | 19.6 % | 7.5 % | 8.4 % |
| median hours from capture to decision | 9.9 | 9.6 | 9.9 | 10.3 |

The quartiles of the time from capture to decision are 5.3 and 15.0 hours. The store holds 382,006 community
item rows.

Coverage of the text features (share of the rows that are not zero, and the mean number of such assets per
day):

| Feature | all 54,300 rows | per day | 36,100 test rows | per test day |
|---|---|---|---|---|
| `tone_1d` | 5.5 % | 2.8 | 5.8 % | 2.9 |
| `unfav_1d` | 3.1 % | 1.5 | 3.2 % | 1.6 |
| `evt_1d` | 7.2 % | 3.6 | 7.4 % | 3.7 |
| `stance_1d` | 3.0 % | 1.5 | 3.0 % | 1.5 |
| `tone_prev6` | 17.0 % | 8.5 | 17.7 % | 8.9 |
| `unfav_prev6` | 9.1 % | 4.5 | 9.5 % | 4.8 |
| `n_subject_1d` | 8.8 % | 4.4 | 8.8 % | 4.4 |
| `n_subject_7d` | 26.3 % | 13.1 | 26.1 % | 13.0 |
| `news_1d` | 33.5 % | 16.7 | 32.8 % | 16.4 |
| `posts_1d` | 41.4 % | 20.7 | 36.6 % | 18.3 |
| `attn_7d` | 77.9 % | 38.9 | 76.1 % | 38.1 |
| `gap_7d` | 0.34 % | | 0.23 % | |

- The fresh tone is sparse. `tone_1d` is not zero on 3,006 rows, of which 2,080 lie on test days: 912 rows in
  2022, 1,072 in 2023 and 1,022 in 2024. Between 85 % and 91 % of the days of a year have at least one such
  row. The tone of the whole week (`tone_1d` plus `tone_prev6`) is not zero on 10,119 rows, of which 7,006 lie
  on test days.
- Favourable tone is more frequent than unfavourable: `tone_1d` is positive on 1,814 rows and negative on
  1,192 (test days 1,309 and 771).
- The fresh tone is concentrated. 77 of the 222 assets ever have a non-zero `tone_1d`. BTC has 724 such rows,
  ETH 620, SOL 307, XRP 138, MATIC 137, AVAX 121, BNB 116. BTC and ETH hold 44.7 % of them, and 1,662 rows lie
  outside the two. The gate is reported a second time without BTC and ETH (§5).
- Gaps are rare. Of 87,574 timely news item rows of members, 101 rows (88 documents) have no judgement that
  the reading rule would have asked for: 66 rows without a type and 35 read rows without a record. 183 panel
  rows (0.34 %) have `gap_7d` above zero, and 61 of them carry a tone.
- Bar features are missing on 3 rows. `ret_30d` and `beta_60d` are missing on 0.43 % of the rows and
  `attn_abn_1d` on 0.74 % (none on test days).
- After both steps of §3.2 the residual of `tone_1d` keeps 0.668 of its rank variance (0.681 on test days)
  and that of `tone_prev6` 0.647 (0.665). A within-day regression of 50 rows on 15 ranks and an intercept
  leaves 34/49 = 0.694 of a feature that is pure noise, so the controls take little of the tone beyond the
  degrees of freedom. On the rows with a tone the residual correlates with the rank at 0.951 (`tone_1d`) and
  0.914 (`tone_prev6`).

### 3.2 Partial design (the gate)

The gate asks for the part of the reader tone that the controls cannot explain, set against the part of the
next-day return that the controls cannot explain. The controls are the 15 ranks of HIST and block A. They are
removed from both sides in two steps, as in Charter 3, with days in place of weeks.

1. **Flexible step, target.** The target rank minus a quadratic surface of the control ranks: an intercept,
   the ranks, their centred squares and their pairwise products (136 columns). The surface is a ridge
   regression with penalty 1.0, intercept not penalised. The surface of a day is fitted on the rows of all
   earlier days, whose outcome has closed by the decision, and is fitted again every day. The first 182 days
   are fitted on themselves. They lie inside the training-only days and are never scored.
2. **Flexible step, features.** Every feature rank minus the prediction of boosted trees from the control
   ranks (LightGBM, 300 rounds, Appendix A). The trees are fitted at day 183 and again every 91 days after
   it, each time on all earlier days. The first 182 days are fitted on themselves. This step uses no outcome.
3. **Within-day step.** What is left of the target and of every feature is regressed, within the day, on an
   intercept and the 15 control ranks (ordinary least squares, a day needs at least 30 rows). The residuals
   are `e_reader` (target) and the residual features.
4. **Model.** A ridge regression without intercept of `e_reader` on the residual features, penalty 10. The
   score of a day uses coefficients fitted on all earlier days and needs 364 days of them. The first scored
   day is 2023-01-07. The score is `s_reader`.
5. **Statistic.** The correlation of `s_reader` with `e_reader` within the day, on every test day with at
   least 30 rows and variation on both sides. The gate statistic is the Newey-West t (lag 7) of the mean of
   that daily series.

Why this form:
- The two steps answer the finding of Charter 3 stage V0: a within-period regression alone leaves curved and
  time-varying relations between controls and target in the residual, and a fitted score can pick them up
  through features that are correlated with the controls. Here the first design is kept as the descriptive
  score `s_reader_lin`.
- The return of the next day reverses the return of the last day to some degree, and the news follows the
  price: an asset that fell has unfavourable news. `ret_1d`, `rv_1d` and `vsurge_1d` are controls for that
  reason. A tone that only repeats the last return earns nothing (tests in §4).
- Attention is a control, not part of the tested block. The count of items needs no reader agent, and both
  earlier charters found their relation there.
- The sign of the relation is fitted on earlier days, not fixed. The reader tone may continue (drift) or
  reverse (over-reaction). The gate asks whether a stable relation of either sign exists and can be used out
  of sample. A score with a fixed direction was drawn next to it in stage V0 (§4.1) and is a decision of §10.

### 3.3 Scores

Partial scores. Each is built by the steps of §3.2 from its own features and controls and is read with the
same daily statistic. Only `s_reader` enters the verdict.

| Score | Features | Controls | Flexible step | Role |
|---|---|---|---|---|
| `s_reader` | `tone_1d`, `tone_prev6` | HIST + block A | yes | **the gate** |
| `s_reader_lin` | `tone_1d`, `tone_prev6` | HIST + block A | no | first design, descriptive |
| `s_reader_hist` | `tone_1d`, `tone_prev6` | HIST | yes | tone beyond price history, attention not removed |
| `s_block_r` | the six features of block R | HIST + block A | yes | whole reader block |
| `s_fresh` | the four features of the last day | HIST + block A | yes | last day only |
| `s_text` | block A + block R | HIST | yes | all text beyond price history |
| `s_attn` | block A | HIST | yes | attention counts beyond price history, no reader agent |

Forecasts. Each is a walk-forward fit of the target rank on feature ranks, without removal of controls, read
by rank IC, mean squared error and the loss difference of nested pairs.

| Forecast | Features | Model |
|---|---|---|
| `v_hist` | HIST | ridge |
| `v_hist_attn` | HIST + block A | ridge |
| `v_full` | HIST + block A + block R | ridge |
| `g_hist_attn` | HIST + block A | boosted trees, fitted again every 28 days |
| `g_full` | HIST + block A + block R | boosted trees, fitted again every 28 days |

- The gate score is fitted without a guard: an error there stops the run. An error in any other fit leaves
  its column missing and is recorded.
- The boosted trees stay in the run as the second model class that was decided for the four changes with
  Charter 2. They do not enter the verdict.

### 3.4 Score book (size reading) and no decision layer

A partial correlation states whether a relation exists. It does not state whether the relation is large
enough to pay for the trades that use it. The run therefore books `s_reader` as a portfolio, for description
and for the size reading of §5:

- Each test day the weights are proportional to the score minus its mean of the day, scaled to a gross
  exposure of 2 (long 1, short 1). The book is held one day and booked with the simple return of every asset.
- Turnover is the sum of the absolute weight changes from one day to the next. The first day builds the book.
- Cost is 5 bp per unit of turnover (taker fee per side, the rate of the earlier portfolio evaluations).
- Reported: gross and net mean daily return in basis points, Newey-West t, annual Sharpe ratio at 365 days and
  mean turnover.

The turnover of this book follows from decision-time features alone and was measured before the freeze
(`decision_facts.json`, no outcome): a book on the residual of `tone_1d` alone turns over 2.76 times its
exposure of one side per day, a book on the residual of `tone_prev6` alone 1.67 times, and mixes of the two
between 1.64 and 2.02 times. The book therefore costs about 8 to 14 bp per day on the basis of its return,
and a relation has to earn more than that per day to be read as "above cost".

There is no agent debate and no consensus layer under this charter. A decision layer is only worth building
on a forecast that passes.

## 4. Stages

| Stage | Content | Cost | Opens outcomes |
|---|---|---|---|
| V0 | Capture-time audit, evaluation code, runner, registration script, tests, synthetic dry run, calibration on bars before the window, pass rate and power of the gates on synthetic targets, the two design rules (§4.1) | 0 | no |
| V1 | Freeze of this document (needs approval) | 0 | no |
| V2 | Registration, pre-flight, registered run with the single outcome join and the verdict | 0 | yes, once |

**V0 (complete).** The code of §7 with 85 offline tests, among them a whole registered run on a synthetic
checkout (defects stop before the claim, one counted outcome join, a repeat run is refused), the capture-time
audit and the decision-time facts of §3.1, the calibration of Appendix C, the simulations of Appendix B and
the two design rules of §4.1.

**V1 freeze.** The draft mark in the title is removed, the status line is changed and the document is
committed. From then on it stays byte-identical: the registration records its hash and the run requires it.

**V2 registered run.** `scripts/reader_charter4_register.py` writes the registration
(`research/llm-v2-charter4-<date>/gates.json`, experiment `llm-v2c4-fresh-news-dev-run-<date>`, dataset
`dev-reader-daily-2022-2024`, parent `llm-v2c3-volatility-dev-run-20261113`) with the hashes of this document,
of 45 source files and of 7 inputs: items, typed documents, cards, call cache, record table, extraction
manifest and kline digest. Every input must have the bytes registered for the Charter 3 run. The frozen
documents of Charter 2 (`docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md`, under which
the records were extracted) and of Charter 3 are among the source files, and every source file of the Charter
3 run must be unchanged. `scripts/reader_charter4_run.py` then runs in this order.
1. Before the claim: the manifest is checked against the registration, the records are rebuilt from the
   registered cache and must equal the record table, the kline store is verified against its digest (799
   files), the decision-time features are built, and the whole evaluation is rehearsed on seeded synthetic
   targets. `--preflight-only` stops here.
2. The claim (attempt 5 of 6).
3. The same preparation through the registered inputs, then the forward targets as the single outcome join.
4. Evaluation and the four outputs: `forecasts.json`, `evaluation.json`, `reader.json`, `verdict.json`. The
   run makes no model call.

The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
window under this charter.

No block is evaluated on its own before the run. Attention counts and price history exist at no cost, and
opening them first against the next-day return would condition the reading of the reader tone on an outcome
of the same window.

### 4.1 Findings of stage V0: two choices made by rule on synthetic targets

Every draw of stage V0 keeps the 54,300 rows of real decision-time regressors and replaces the next-day
return by a synthetic one (Appendix B). No draw reads a bar of the window dated at or after a decision. Each
rule below was written into the design folder before its draws were made
(`research/multiagent-v2/charter4_design/README.md`).

**Rule 1: form of the daily statistic.** Two forms were coded: the correlation within the day (`corr`) and
the covariance within the day (`cov`). The covariance weights a day by the spread of its score, so days with
news count more. Rule: a form is excluded when the 95 % interval of its pass rate on a noise cell lies wholly
above 5 %. Of the forms that remain, the one with more passes over four planted sizes (800 draws) is taken. A
difference of fewer than 40 passes leaves `corr`, the form of Charters 2 and 3.
Outcome: no form was excluded. `corr` passed 544 times and `cov` 554 times. The difference is 10. The gate
form stays `corr`, and `cov` is a descriptive value of the run.

**Rule 2: features of the fitted gate score.** The first power draws showed that a fitted score pays for the
estimation of six weights on sparse features. Rule: the candidates are the six features of block R, the four
features of the last day, and the two tone features. One set of seeds serves all candidates: 400 noise draws
and 200 draws for each of four planted cells. A candidate is excluded by the 95 % interval as in rule 1. Of
the candidates that remain, the one with the most passes over the 800 planted draws is taken. A lead of fewer
than 40 passes over the six features leaves the six features.
Outcome: the noise pass rates were 1.8 %, 1.5 % and 3.0 %, and no candidate was excluded.

| Planted effect | size | six features | four of the last day | two tone features | fixed direction |
|---|---|---|---|---|---|
| fresh | 0.05 | 10.5 % | 16.5 % | 20.0 % | 29.5 % |
| fresh | 0.10 | 57.5 % | 71.5 % | 75.5 % | 81.5 % |
| week | 0.03 | 15.5 % | 3.0 % | 28.0 % | 7.0 % |
| week | 0.06 | 79.0 % | 7.5 % | 87.0 % | 16.5 % |
| passes of 800 | | 325 | 197 | 421 | 269 |

The two tone features lead the six features by 96 passes. The gate score uses `tone_1d` and `tone_prev6`. The
six-feature score stays in the run as `s_block_r` and the last-day score as `s_fresh`.

- Limit of rule 2: both planted effects are defined on the tone (the sign of `tone_1d`, or of the tone of the
  week). The rule favours the tone features by construction. An effect that lives only in the unfavourable
  events, the event count or the opinion stance is not what the gate is built to detect. It would show in
  `s_block_r`, which is descriptive.
- The column "fixed direction" is a score without a fitted weight: the residual of `tone_1d`, with the
  hypothesis that favourable tone is followed by a higher return. It was not a candidate of the rule, because
  taking it fixes the sign of the hypothesis. It is stronger for an effect of the last day with that sign
  (29.5 % against 20.0 %, 81.5 % against 75.5 %), weak for an effect that lasts the week (7.0 % and 16.5 %),
  and blind to a reversal. The choice between the two is decision 3 of §10.
- After rule 2 the pass rate and the power of the registered gate were drawn again with the two-feature
  score (3,800 draws, Appendix B). Rule 1 was checked on those draws as well: `corr` 595 passes, `cov` 603, a
  difference of 8.
- The synthetic cells were compared with the real next-day return on bars before the window (Appendix C).
  One cell was added after that comparison, before any outcome was opened: a `stress` cell in which the bar
  history explains as much of the return as it does in 2021 and in which the unexplained part persists more
  than measured. Its pass rate is 2.5 %.

## 5. Gates

One primary statistic and one stability condition, as in Charters 2 and 3.

- **G1 (primary).** The daily partial correlation of `s_reader` with `e_reader` (§3.2) on the 722 test days.
  Statistic: Newey-West t (lag 7) of its mean. Rule: t at least 2.0 and mean positive.
- **G2 (stability).** The mean daily partial correlation is positive in 2023 and in 2024 (calendar year of
  the decision day).
- **Verdict.** PASS when G1 and G2 hold. Otherwise FAIL. A statistic that cannot be computed fails its gate.
  No descriptive score enters the verdict.
- **Size reading (no gate).** With a PASS, the net mean daily return of the score book of §3.4 is read as
  "above cost" when it is above zero and as "below cost" otherwise. The value is written into `verdict.json`
  by code. A relation can be statistically present and still too small to pay a daily turnover of 1.6 to 2.8
  at 5 bp per side. "Below cost" names that case.

Descriptive, no gate (`evaluation.json`, `reader.json`):
- Every partial score of §3.3: daily partial correlation and daily covariance with Newey-West t, by year and
  with the share of positive days, the share of the residual variance explained out of sample, the share of
  the target variance that the controls leave, the correlation of every single residual feature with the
  target residual, and the ridge coefficient paths.
- The forecasts of §3.3: rank IC and mean squared error on the test days, and the daily loss differences of
  the nested pairs (`v_hist_attn` against `v_full`, `v_hist` against `v_hist_attn`, `v_hist` against `v_full`,
  `g_hist_attn` against `g_full`).
- The gate statistic with another target and unchanged features, controls and steps: `fwd_absret_1d`,
  `fwd_rv_1d` and `fwd_ret_3d`. A day is trained on only when its outcome has closed, which is three days for
  the three-day return.
- What each step of §3.2 removes: the share of the rank variance of the target and of every gate feature
  that is left on the test days after the within-day step alone and after both steps.
- Permutation placebo: the gate statistic after the feature rows are permuted across the assets of every
  day, 500 draws, seed 20261114.
- Shift placebo: the gate statistic with every asset's residual features taken from 28, 91 and 182 days
  earlier and later. The asset is kept and the timing is broken.
- Autocorrelation of the target residual within an asset at 1, 2 and 7 days. It is compared with the cells
  of the noise table (Appendix B, Appendix C).
- The gate without the rows of BTC and ETH, in the fit and in the statistic, and the gate without the rows
  that have `gap_7d` above zero.
- The score book of §3.4.
- An event study: the next-day return minus the equal-weight mean of the day, in basis points, for the rows
  with positive tone, negative tone, an event with zero tone, an unfavourable event, a record without event
  and no record. Pooled mean, mean of the day means and Newey-West t.
- Feature and target coverage, the timing facts of §3.1 and the quality report of the reader records.
An error in a descriptive part is listed in `verdict.json` and cannot change the verdict.

What each verdict licenses:
- PASS on the development window is not a claim. It licenses building the text of Sealed-A and Sealed-B and
  one confirmation run there under a further charter. The size reading states how the result is described:
  "above cost" as a candidate input of a daily decision layer, "below cost" as a statistical relation that
  does not pay for its trades.
- FAIL closes the next-day relative return from the reader tone at a daily decision. With Charters 2 and 3
  it shows that the weekly horizon was not the reason for the earlier failures, within what the stores can
  time (§1). The records stay as an input of the last change (§9).
- In both cases the rows `s_attn` and `s_text` show whether counting items, with no reader judgement, carries
  next-day information beyond price history. That result needs no language model. It is reported and
  nothing is claimed from it.

Power. On the real regressors with an effect planted on the tone (Appendix B, 200 draws per cell), a planted
size is a share of the asset's own daily volatility, added to the return of every asset-day with a direction.
For an effect of the last day (2,080 such asset-days on the test days) the gates pass in 22 % of the draws at
about 18 bp, in 77 % at about 37 bp and in 98.5 % at about 55 bp. For an effect that lasts the week (7,006
asset-days) they pass in 29.5 % at about 13 bp, in 87 % at 27 bp and in all draws at 45 bp. Even odds of a
pass need about 30 bp per asset-day with a fresh direction, or about 20 bp when the effect lasts the week.
The effect was planted with a positive sign. The score is fitted, so a reversal of the same size has the
same power. These sizes are large for a liquid market one day after public news. A FAIL therefore speaks
against a drift or reversal of about 40 bp and more per directed asset-day, firmly from about 55 bp, and
does not exclude a smaller one.

Pass rate on noise. On the real regressors with a synthetic return that holds no reader information
(Appendix B, 400 draws per cell, six cells), the gates pass in 1.5 % to 2.5 % of the draws, 51 of 2,400 in
all. No cell has a 95 % interval wholly above 5 %. The t statistic has a mean of +0.05 to +0.06 and a
standard deviation of 1.00 to 1.05. The gate needs a positive mean, so these rates are those of a one-sided
test at t 2.0. The cells cover a market factor with one-day reversal, a persistent drift that no control
sees, a curved relation to the history, an unsigned drift after attention, and a `stress` cell that explains
as much of the return by the bar history as the bars of 2021 show and persists more (Appendix C). The run
reports the autocorrelation of the target residual, which states whether the real target lies inside the
range of these cells.

## 6. Leakage and exposure

- **The window is exposed.** The test days lie in the weeks that Charter 2 opened for the weekly return and
  Charter 3 for the weekly volatility. The daily bars of the window were used by earlier programmes of the
  repository, also for daily return forecasts from price, funding and on-chain data. The registration states
  the reuse as exploratory.
- **What was known when the design was fixed.** The outputs of Charters 2 and 3. Each relates a weekly text
  feature to an outcome of the next week. The weekly return relation of the text was weak and positive and
  sat in the attention counts (t 1.39). None of these outputs relates a daily text feature to a return of
  the next day. The decision to control for attention follows from those results.
- **What was not looked at.** Before the registered run no feature built from the records or from the item
  counts is joined with a return or any other price quantity dated at or after its decision, and no gate
  statistic of this charter is computed on real outcomes. The text features were joined with price history
  up to the decision only: for the facts of §3.1, for the flexible step on the feature side, for the
  turnover of §3.4, and for the simulations of §4.1 and Appendix B, in which every target is synthetic.
- **Design choices before the freeze.** Two, each by a rule written before its draws and on synthetic
  targets alone (§4.1). Both alternatives stay in the run as descriptive values. The `stress` cell was added
  after the calibration and before any outcome was opened.
- **Bars before the window.** The persistence of the target residual, its one-day reversal and the curvature
  of its relation to the history were measured on bars dated before 2022-01-01, from price alone (Appendix
  C). No card and no text exists for that period.
- **News follows price.** An article about a price move is written after the move, and its tone repeats the
  last return. The return of the next day partly reverses the last one. `ret_1d`, `rv_1d` and `vsurge_1d`
  are controls in both steps so that this channel is removed. Tests plant a tone that is a linear and a
  curved function of the history and check that it earns nothing, and plant a signal in the attention counts
  and check that it appears in `s_attn` and not in `s_reader`.
- **Timing of the items.** No item enters a feature before the first midnight after the store captured it.
  The capture time is the stamp of the store. For a community post the stamp is the publication date, so a
  post enters at the midnight after its date. The publication time of day of a news item is unknown, which
  limits how fresh a feature can be (§1) and cannot place an item before its capture.
- **Zero latency.** The position is taken at the close of the bar that closes at the decision, and the last
  items were captured a median of 9.9 hours earlier. A real system needs seconds to minutes after midnight.
  The assumption favours the result slightly and is the same for every score.
- **Records depend on later membership.** An item was read for an asset when the asset was a member on a
  Friday within 30 days after the item (§3.1). Whether a record exists on a decision day therefore depends,
  for 0.34 % of the panel rows, on a membership that was fixed after the decision. Those rows count as no
  record, and the gate is reported without them.
- **Concentration.** BTC and ETH hold 44.7 % of the rows with a fresh tone. A result could rest on two
  assets. The gate is reported without them. With 2.9 assets per day carrying a fresh tone, the daily
  correlation rests on few rows and is noisy. The t is taken over the 722 daily values, so that noise is in
  its denominator, and the permutation placebo checks it.
- **Persistence.** The tone of an asset persists and `tone_prev6` overlaps from day to day, so the daily
  statistic is autocorrelated. The t uses lag 7. The cells with an unseen persistent drift pass in 2.5 % of
  the draws (§5). The outputs carry the residual autocorrelation and the shift placebo.
- **Hindsight in the reader.** The reader saw de-identified summaries and recorded what they state. A famous
  episode could still be recognised and colour the direction of a record. Controls as in Charter 2: evidence
  must be verbatim, and the fitted model learns from earlier days only. Hindsight would raise the statistic.
  It bears on a PASS, not on a FAIL, and the sealed windows stay the arbiter.
- **Delisted contracts.** The universe comes from the card of each Friday and the kline store keeps delisted
  contracts. A row without the bar of the next day has no target and the target coverage reports it.
- The registered run rehearses on synthetic targets before the claim and joins the real forward targets
  once, after the claim.

## 7. What is fixed and what is reused

Reused without change: everything of Charter 2 up to the record table (text store, typing, reading rule,
reader agents, adjudicator, call cache, 53,330 records, $5.75 paid), the cards and the universe, the daily
bars, the ridge and boosted-tree fitters (`tradingagents/reader/model.py`), the rank, basis and tree settings
of Charter 3 (`tradingagents/reader/charter3.py`) and the run lifecycle (`tradingagents.research`).

New under this charter:

| File | Content |
|---|---|
| `tradingagents/reader/charter4.py` | daily universe, item timing, bar history, forward targets, block A and block R per day, panel, removal of the controls in two steps, gates, descriptive panels, score book, event study, verdict |
| `scripts/reader_charter4_register.py`, `scripts/reader_charter4_run.py` | registration and registered run |
| `scripts/reader_charter4_null_gate.py` | panel builder, calibration, pass rate and power on synthetic targets (not part of the run) |
| `tests/research/test_reader_charter4.py` | tests |
| `research/multiagent-v2/charter4_design/` | the two rules of §4.1 with their draws, the draws of the registered gate, the capture-time audit, the decision-time facts of §3.1 and §3.4, the calibration of Appendix C |

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
- Calendar: the submission date is 2027-01-08 and the planned results freeze is 2026-12-21. The registered
  run of this charter is expected to take hours, not days, after the freeze approval.

## 9. Order of the four changes

| # | Change | Status | Planned as |
|---|---|---|---|
| 1 | Language model reads, fitted model forecasts | Charter 2, FAIL (t 1.39) | done |
| 2 | Different target (next-week volatility, tail risk descriptive) | Charter 3, FAIL (t −0.72) | done |
| 3 | Fresher information (decision close to the news, not once a week) | Untried on own records. Earlier no-go at minute scale. | This charter. Daily decision, next-day return. No model call. |
| 4 | Agents compare assets directly | Tested on numeric cards (t 1.01 on 222 weeks) | Last. Only the text-based variant is new. It needs model calls and its own charter. |

Two attempts remain in the family and each change consumes one. After this charter one remains.

## 10. Decisions

The points below are open at the draft. The column "Implemented" holds the option that the code and this
document carry and that is recommended. An approval of the freeze without remark takes that option in every
row. Any row can be changed before the freeze. A change of row 1, 2, 3 or 4 needs new draws on synthetic
targets before the freeze.

| # | Point | Implemented (recommended) | Alternative |
|---|---|---|---|
| 1 | Gate target | Relative return of the next day (`fwd_ret_1d`). The reader records carry a direction, and the weekly volatility target has failed. | Size of the move of the next day, or the three-day return. Both are descriptive variants here. A volatility gate would repeat Charter 3 at a shorter horizon, where own history is again the baseline to beat. |
| 2 | What the gate tests | The reader tone beyond price history and attention counts (`s_reader`, two features, chosen by rule 2 of §4.1). | The whole reader block (`s_block_r`): covers unfavourable events and opinion stance, with less power on a tone effect (325 against 421 passes of 800). Or all text beyond price history (`s_text`): easier to pass, but a pass could rest on item counts alone and would say nothing on the agents. |
| 3 | Sign of the hypothesis | Fitted: the score learns on earlier days whether tone continues or reverses. Detects either sign and an effect that lasts the week. | Fixed: favourable tone of the last day is followed by a higher return. More power for exactly that case (81.5 % against 75.5 % at 37 bp), little for an effect over the week (16.5 % against 87 % at 27 bp), none for a reversal. |
| 4 | Threshold of G1 | t at least 2.0, as in Charters 1b, 2 and 3. Pass rate on noise 1.5 % to 2.5 %. | t at least 2.3. Pass rate on noise 0.8 % to 1.2 %. Power falls from 77 % to 67 % at 37 bp of the last day and from 87 % to 80.5 % at 27 bp over the week (Appendix B). |
| 5 | Form of the daily statistic | Correlation within the day, by rule 1 of §4.1. | Covariance within the day. Equal power within 10 passes of 800. Descriptive here. |
| 6 | Size of a pass | Reading rule on the net return of the score book ("above cost" or "below cost"), written by code, no gate. | A third gate that requires a positive net return. A PASS would then be a tradable relation by definition. Its pass rate and power were not drawn, and a relation below cost is still a finding on the agents. |
| 7 | Items without a judgement | Count as no record (183 panel rows, 0.34 %). The gate is reported without them. No model call, and every input keeps the bytes of the Charter 3 run. | Type and read the 88 documents now (a few cents). The record table would change, and with it the registered inputs and the claim "no model call". |
| 8 | Community posts | Counts in block A only. | Signed features from posts. Charter 2 read only the most recent posts before each weekly decision, so whether a post has a record depends on posts that came after it. Not possible without that look-ahead. |
| 9 | Decision frequency | Daily at 00:00 UTC. | Several decisions per day. Not built: it needs an hourly bar store for 222 contracts, and the publication time of day stays unknown. |
| 10 | Attempt accounting | Attempt 5 of 6 in the family `llm-multiagent-v2`. One attempt remains for the last change. | Skip this change and keep two attempts for the last one. |

## Appendix A. Definitions

- **Decision day D:** the decision is taken at 00:00 UTC of day D. The daily bar dated D − 1 covers the day
  before the decision and closes at it. The bar dated D opens at the decision and closes at the next one.
- **Feature day of an item:** the first midnight after its capture time. An item captured exactly at midnight
  waits one more day. A news item enters a feature only when its feature day is at most 2 days after its
  publication date.
- **Garman-Klass variance of a daily bar:** 0.5 · ln(high / low)² − (2 ln 2 − 1) · ln(close / open)², not
  below 0. A bar without four positive prices is missing.
- **`fwd_ret_1d`:** close of the bar dated D over the close of the bar dated D − 1, minus 1. It is the simple
  return of the bar that opens at the decision.
- **`fwd_absret_1d`:** absolute value of `fwd_ret_1d`.
- **`fwd_rv_1d`:** Garman-Klass variance of the bar dated D.
- **`fwd_ret_3d`:** close of the bar dated D + 2 over the close of the bar dated D − 1, minus 1.
- **Missing target:** a row without the bars a target needs has that target missing. It enters no fit and no
  statistic of that target. No bar later than D + 2 is read.
- **Target rank:** percentile rank within the day over the rows that have the target, minus 0.5.
- **Feature rank:** percentile rank within the day minus 0.5. A missing value takes the neutral rank 0.
- **History windows:** a window of n days ending at the bar dated D − 1 holds the bars dated later than
  D − 1 − n days and not later than D − 1. A 7-day window needs at least 4 bars, a 30-day window needs
  at least 10 bars and the 60-day beta needs at least 30 pairs of returns. Otherwise the value is missing.
- **Training days of a decision:** the days whose outcome has closed by the decision. For a one-day target
  these are all earlier days. For `fwd_ret_3d` these are the days at least three days before the decision day.
- **Daily statistics:** a within-day regression or correlation needs at least 30 rows with the target. A day
  without variation on either side has no statistic.
- **Newey-West t:** of the mean of a daily series, with Bartlett weights and lag 7.
- **Quadratic surface (flexible step, target):** ridge regression of the target rank on an intercept, the
  control ranks, their squares minus 1/12 and their pairwise products (136 columns with 15 controls, 78 with
  11), penalty 1.0, intercept not penalised. From day 183 on, a day is served by the surface fitted on the
  rows of its training days, and the surface is fitted again every day. One surface fitted on the first 182
  days serves those days.
- **Trees (flexible step, features):** LightGBM regression of a feature rank on the control ranks, with
  300 rounds, learning rate 0.05, 8 leaves, depth 3, at least 50 rows per leaf, feature and row sampling
  0.8, L2 penalty 10, fixed seed, one thread and deterministic mode. Fitted at day 183 and every 91 days
  after it on all earlier days. One fit on the first 182 days serves those days.
- **Walk-forward ridge (every partial score and ridge forecast):** ridge regression without intercept,
  penalty 10, fitted again every day on the training days of the decision. A day is scored when it has
  364 days of training days. The first scored day is 2023-01-07.
- **Boosted-tree forecasts (`g_hist_attn`, `g_full`):** the boosted trees of Charter 2 on the feature ranks,
  target `fwd_ret_1d` as a rank, fitted from the first scored day and again every 28 days on all earlier days.
- **Loss difference of two forecasts:** daily mean squared error of the smaller model minus that of the
  larger one on the test rows. A positive value means the larger model has the smaller error.
- **Score book:** every asset is held for one day in proportion to its score minus the mean score of the
  day, scaled to gross exposure 2. The return of a day is the weighted sum of `fwd_ret_1d`. Turnover is the
  sum of absolute weight changes against the book of the day before. The cost is 5 bp per unit of turnover.
  Reported are the gross and net mean daily return in basis points, their Newey-West t, the annualised
  Sharpe ratio on 365 days and the mean turnover.
- **Event study:** mean of `fwd_ret_1d` minus the equal-weight mean of the day's panel rows, in basis points,
  on the test days, for six groups of asset-days by their records of the last day: positive tone, negative
  tone, an event with zero tone, an unfavourable event, a record without an event, no record.
- **Permutation placebo:** the residual features are permuted across the assets of every day, the model is
  fitted again and the gate statistic is computed. With seed 20261114 and 500 draws. Reported are the share
  of draws with a t at or above the observed one, and the mean, spread and 97.5 % point of the drawn t.
- **Shift placebo:** every asset takes its own residual features of 28, 91 and 182 days earlier and later.
  The asset is kept and the timing is broken. A row whose shifted day is outside the asset's panel days is
  neutral.
- **Residual autocorrelation:** correlation of an asset's `e_reader` with its own value 1, 2 and 7 days
  earlier, pooled over the panel.
- **Exclusions:** the gate fit and statistic without the rows of BTC and ETH, and without the rows that have
  an item without a judgement in the last seven days (`gap_7d` above 0). The excluded rows enter neither the
  fit nor the daily statistic.
- **Control removal:** share of the rank variance of each gate feature and of the target that is left on the
  test days after the within-day step alone and after both steps.

## Appendix B. Pass rate and power of the gates on synthetic targets

`scripts/reader_charter4_null_gate.py`. No real outcome of the window is involved in any draw. The draws and
their summaries are stored in `research/multiagent-v2/charter4_design/`.

| Draws | Number | Files |
|---|---|---|
| Registered score (`tone_1d`, `tone_prev6`) | 3,800 | `null_gate.jsonl`, `null_gate_summary.json` |
| First round, six-feature score | 3,400 | `null_gate_block_r.jsonl`, `null_gate_block_r_summary.json` |
| Rule 2, feature set of the gate score | 1,200 | `gate_score_power.jsonl`, `gate_score_power.json` |

**How a draw is made.** The 54,300 panel rows keep their real decision-time regressors: price history,
attention counts and reader features. The return of the next day is replaced by a synthetic one. The gate
then runs by the registered functions: both flexible steps, the within-day step, the walk-forward ridge, the
daily statistic and the two gates. The feature side is the same in every draw. Seeds 0 to 399 are used in
the cells without a planted effect and seeds 0 to 199 in the planted cells.

**Cells of the synthetic return.** All parts are in units of the asset's own daily volatility.

| Cell | Synthetic return of the next day |
|---|---|
| `noise` | independent standard normal returns on one scale |
| `factor` | a market return (daily volatility 0.03) times the real `beta_60d`, plus the asset's own volatility (root of the real `rv_30d`) times noise, minus 0.05 times the standardised real `ret_1d` (a one-day reversal) |
| `drift` | `factor` plus a drift per asset that no regressor sees (scale 0.10, daily persistence 0.95) |
| `curved` | `factor` plus a curved function of the history ranks (scale 0.30) |
| `attention` | `factor` plus an unsigned drift after news and posts, a function of the attention counts only |
| `stress` | `drift` with 3.0 times the market volatility and 2.0 times the unseen drift |

**Planted effects.** Both are placed in the `factor` cell.
- `fresh` adds kappa times the sign of `tone_1d`. The test days hold 2,080 asset-days with such a sign.
- `week` adds kappa times the sign of `tone_1d + tone_prev6`. The test days hold 7,006 such asset-days.
- The size is stated as kappa and in basis points per directed asset-day, which is kappa times the median
  daily volatility of those asset-days.

### B.1 Registered score (`s_reader`)

"PASS" applies both gates as registered. "G1 alone" counts the draws with t at least 2.0 and a positive mean.
The last column applies the gates to the covariance form.

| Cell | Planted size | Draws | PASS | Pass rate (95 % interval) | G1 alone | Mean daily correlation | t: mean, sd, 97.5 % point | Pass rate, covariance form |
|---|---|---|---|---|---|---|---|---|
| `noise` | none | 400 | 10 | 2.5 % (1.0 % to 4.0 %) | 11 | +0.0003 | +0.05, 1.05, 2.13 | 1.8 % |
| `factor` | none | 400 | 6 | 1.5 % (0.3 % to 2.7 %) | 7 | +0.0003 | +0.05, 1.01, 1.88 | 0.8 % |
| `drift` | none | 400 | 10 | 2.5 % (1.0 % to 4.0 %) | 11 | +0.0003 | +0.06, 1.00, 2.04 | 1.5 % |
| `curved` | none | 400 | 7 | 1.8 % (0.5 % to 3.0 %) | 8 | +0.0003 | +0.06, 1.01, 1.89 | 1.0 % |
| `attention` | none | 400 | 8 | 2.0 % (0.6 % to 3.4 %) | 9 | +0.0003 | +0.06, 1.00, 1.93 | 1.0 % |
| `stress` | none | 400 | 10 | 2.5 % (1.0 % to 4.0 %) | 11 | +0.0003 | +0.05, 1.00, 2.04 | 1.5 % |
| `factor` | `fresh` 0.05, 18.4 bp | 200 | 44 | 22.0 % | 44 | +0.0062 | +1.12, 1.11, 3.35 | 21.0 % |
| `factor` | `fresh` 0.10, 36.7 bp | 200 | 154 | 77.0 % | 155 | +0.0152 | +2.77, 1.06, 5.01 | 81.5 % |
| `factor` | `fresh` 0.15, 55.1 bp | 200 | 197 | 98.5 % | 197 | +0.0236 | +4.32, 1.06, 6.60 | 99.0 % |
| `factor` | `fresh` 0.20, 73.5 bp | 200 | 200 | 100 % | 200 | +0.0317 | +5.84, 1.09, 8.06 | 100 % |
| `factor` | `week` 0.03, 13.5 bp | 200 | 59 | 29.5 % | 60 | +0.0076 | +1.34, 1.27, 3.63 | 24.5 % |
| `factor` | `week` 0.06, 27.0 bp | 200 | 174 | 87.0 % | 174 | +0.0186 | +3.28, 1.11, 5.56 | 81.5 % |
| `factor` | `week` 0.10, 45.0 bp | 200 | 200 | 100 % | 200 | +0.0321 | +5.64, 1.10, 7.92 | 100 % |

- No cell without a planted effect has an interval wholly above 5 %. Pooled over the six cells, 51 of 2,400
  draws pass (2.1 %). The six cells share their seeds and their regressors, so they are not six independent
  samples.
- The gate needs a positive mean. A pass rate near 2.5 % is the nominal rate of a one-sided test at t 2.0.
- The second gate removes almost nothing on noise: one draw per cell passes G1 and fails G2.
- A pass rate on 200 draws has a standard error of about 3 points near 25 % and 75 %.
- The mean daily correlation that the gate sees is small even at full power: 0.015 at 37 bp of the last day.
  The gate detects a relation of this size because it has 722 days.
- The covariance form has a mean t of −0.19 to −0.25 without a planted effect. That is why its pass rate on
  noise is lower. With a planted effect neither form leads throughout: the covariance form passes more often
  for the `fresh` plant (603 against 595 of 800) and less often for the `week` plant (412 against 433 of 600).

### B.2 Other thresholds on the draws of the registered score

Passes when G1 asks for another t and G2 stays as it is (§10, row 4):

| Cell | Planted size | Draws | t at least 2.0 | t at least 2.3 | t at least 2.6 |
|---|---|---|---|---|---|
| `noise` | none | 400 | 10 (2.5 %) | 4 (1.0 %) | 3 (0.8 %) |
| `factor` | none | 400 | 6 (1.5 %) | 3 (0.8 %) | 1 (0.2 %) |
| `drift` | none | 400 | 10 (2.5 %) | 4 (1.0 %) | 1 (0.2 %) |
| `curved` | none | 400 | 7 (1.8 %) | 3 (0.8 %) | 2 (0.5 %) |
| `attention` | none | 400 | 8 (2.0 %) | 4 (1.0 %) | 1 (0.2 %) |
| `stress` | none | 400 | 10 (2.5 %) | 5 (1.2 %) | 2 (0.5 %) |
| `factor` | `fresh` 0.05, 18.4 bp | 200 | 44 (22.0 %) | 29 (14.5 %) | 19 (9.5 %) |
| `factor` | `fresh` 0.10, 36.7 bp | 200 | 154 (77.0 %) | 134 (67.0 %) | 117 (58.5 %) |
| `factor` | `fresh` 0.15, 55.1 bp | 200 | 197 (98.5 %) | 194 (97.0 %) | 191 (95.5 %) |
| `factor` | `fresh` 0.20, 73.5 bp | 200 | 200 (100 %) | 200 (100 %) | 200 (100 %) |
| `factor` | `week` 0.03, 13.5 bp | 200 | 59 (29.5 %) | 44 (22.0 %) | 34 (17.0 %) |
| `factor` | `week` 0.06, 27.0 bp | 200 | 174 (87.0 %) | 161 (80.5 %) | 145 (72.5 %) |
| `factor` | `week` 0.10, 45.0 bp | 200 | 200 (100 %) | 200 (100 %) | 200 (100 %) |

Pooled over the six cells without a planted effect (2,400 draws): 51, 23 and 10 passes. A threshold of 2.3
halves the pass rate on noise and costs 10 points of power at 37 bp of the last day.

### B.3 First round: the six-feature score (`s_block_r`)

The first draws used the six features of block R as the gate score. Rule 1 (form of the statistic) was
decided on them. The `stress` cell did not exist yet.

| Cell | Planted size | Draws | PASS | Pass rate | Mean daily correlation | t: mean, sd, 97.5 % point | Pass rate, covariance form |
|---|---|---|---|---|---|---|---|
| `noise` | none | 400 | 11 | 2.8 % | +0.0001 | +0.02, 1.05, 2.06 | 2.0 % |
| `factor` | none | 400 | 9 | 2.2 % | +0.0001 | +0.01, 1.02, 1.96 | 1.2 % |
| `drift` | none | 400 | 7 | 1.8 % | +0.0002 | +0.04, 1.00, 1.87 | 1.5 % |
| `curved` | none | 400 | 10 | 2.5 % | +0.0001 | +0.02, 1.02, 2.00 | 2.0 % |
| `attention` | none | 400 | 10 | 2.5 % | +0.0001 | +0.01, 1.03, 2.01 | 1.5 % |
| `factor` | `fresh` 0.05, 18.4 bp | 200 | 28 | 14.0 % | +0.0048 | +0.85, 1.10, 2.80 | 14.0 % |
| `factor` | `fresh` 0.10, 36.7 bp | 200 | 125 | 62.5 % | +0.0133 | +2.40, 1.12, 4.56 | 65.5 % |
| `factor` | `fresh` 0.15, 55.1 bp | 200 | 191 | 95.5 % | +0.0221 | +4.02, 1.10, 6.28 | 97.5 % |
| `factor` | `fresh` 0.20, 73.5 bp | 200 | 200 | 100 % | +0.0306 | +5.59, 1.10, 7.85 | 100 % |
| `factor` | `week` 0.03, 13.5 bp | 200 | 48 | 24.0 % | +0.0062 | +1.09, 1.19, 3.21 | 20.0 % |
| `factor` | `week` 0.06, 27.0 bp | 200 | 156 | 78.0 % | +0.0167 | +2.93, 1.15, 5.18 | 75.5 % |
| `factor` | `week` 0.10, 45.0 bp | 200 | 200 | 100 % | +0.0307 | +5.38, 1.12, 7.79 | 100 % |

- Rule 1 on these draws: 544 passes of 800 with the correlation form against 554 with the covariance form
  in the `fresh` cells. The difference of 10 is below 40, so the correlation form stays (§4.1).
- The six-feature score needs a larger effect for the same power than the two-feature score of B.1: 62.5 %
  against 77.0 % at 37 bp of the last day. The fit of six weights on sparse features costs power. This led
  to rule 2.

### B.4 Rule 2: feature set of the gate score

The table of rule 2 is in §4.1. Its draws use seeds from 5000 on, one set for the three candidate sets and
for the score with a fixed direction: 400 draws without a planted effect and 200 for each of four planted
cells, all in the `factor` cell.

- The draws of B.1 use seeds 0 to 399 and had no part in the choice. On them the chosen set passes in 22.0 %,
  77.0 %, 29.5 % and 87.0 % of the draws of the four planted cells of the rule, against 20.0 %, 75.5 %, 28.0 %
  and 87.0 % on the draws of the rule. Without a planted effect it passes in 1.5 % of the `factor` draws of
  B.1, against 3.0 % on the draws of the rule.
- Both plants are defined on the tone features. The rule therefore favours the tone set by construction, and
  the registered gate is built to detect a tone effect and no other.

## Appendix C. Calibration on bars before the window

`scripts/reader_charter4_null_gate.py history` and `shapes`. Outputs: `history_calibration.json` and
`shape_cells.json` in the design folder. The false-pass rate of Appendix B is only as good as the synthetic
targets. The calibration asks whether those targets are as hard as the real one.

The `history` kind uses bars dated before 2022-01-01 only, price alone, no card and no text. Every day from
2021-01-02 to 2021-12-31 (364 decision days), the 50 contracts with the highest trailing 30-day dollar volume
(18,200 rows, 109 contracts), the next-day return rank and the nine bar-history ranks as registered. The last
outcome bar closes at 2022-01-01. The `shapes` kind takes the same measures on the synthetic cells of
Appendix B, with the nine bar-history ranks of the panel and three seeds per cell.

Measures:
- **Share left:** share of the target-rank variance left by the within-day regression on the nine ranks.
- **Residual autocorrelation:** correlation of an asset's residual with its own value 1, 2 and 7 days earlier.
- **Reversal:** mean daily correlation of the target rank with the rank of `ret_1d`.
- **Curved share:** share of the residual that boosted trees of the control ranks explain out of sample,
  fitted across four blocks of consecutive days with the tree settings of Appendix A. Near zero means no
  curvature that the trees can find.

| Target | Share left | Residual autocorrelation, 1 / 2 / 7 days | Reversal | Curved share |
|---|---|---|---|---|
| bars of 2021 | 0.680 | −0.005 / −0.004 / +0.010 | −0.024 | −0.003 |
| `noise` | 0.820 | −0.000 / −0.001 / −0.002 | −0.001 | −0.003 |
| `factor` | 0.784 | +0.001 / −0.000 / −0.001 | −0.042 | −0.003 |
| `drift` | 0.785 | +0.009 / +0.007 / +0.004 | −0.042 | −0.003 |
| `curved` | 0.783 | +0.005 / +0.002 / +0.001 | −0.002 | +0.008 |
| `attention` | 0.784 | +0.002 / +0.000 / +0.000 | −0.040 | −0.003 |
| `stress` | 0.690 | +0.031 / +0.027 / +0.020 | −0.039 | −0.003 |

Reading:
- A regression of 50 rows on nine ranks and an intercept leaves 40/49 = 0.816 of pure noise. The bars of
  2021 leave 0.680. The bar history therefore explains about 17 % of the rank variance beyond that baseline.
- The reversal of the real target (−0.024, Newey-West t −2.26) and its curvature (−0.003) lie inside the
  range of the first five cells.
- The first five cells did not cover two measures. None explains as much of the target by the bar history
  (0.78 against 0.68). None has the persistence of the residual at 7 days (+0.010, standard error about
  0.008, on 16,696 pairs).
- The `stress` cell was added for that reason, before any outcome was opened. Its share left about equals
  the measured one (0.690 against 0.680). Its residual persistence is two to three times the largest measured
  value. Its pass rate is 2.5 % (10 of 400).
- The constants of the `stress` cell were set once and were not tuned further.

Limits:
- The measures use one year, 2021, and the nine bar-history controls. The card columns, the attention counts
  and the reader features have no part in them.
- The panel window itself is not measured. Its next-day returns are the outcome of the registered run.
- The `stress` cell matches the share left and exceeds the persistence. It does not exceed the share left. A
  real target with a stronger dependence on the history than in 2021 is outside the cells drawn.
