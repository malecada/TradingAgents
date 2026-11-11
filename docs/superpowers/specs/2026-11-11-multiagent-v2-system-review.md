# Multi-agent v2: whole-system review, 11 November 2026

Scope: dossier pipeline (builder v2.8), agent framework (agents v2.4), evaluation code, registration and run
mechanics of the running Charter 1 attempt `llm-v2c1-dev-run-20261111`.
Method: three independent read-only reviews (data pipeline, agent framework, evaluation and run mechanics),
followed by re-verification of the main claims against code and cached outputs. Nothing in the checkout was
changed. No registered gate statistic was computed on real returns of the LLM forecasts. Simulations used
synthetic returns.

Classes: **A** = affects the forecasts being generated, **B** = affects evaluation or reporting only,
**C** = improvement for a later cycle. "Verified" = reproduced independently in the main review.
"Reported" = found by one reviewer, mechanism plausible, not reproduced.

## 1. Decision needed first

**The running attempt cannot end as a completed registered run.** It will spend the rest of the cap and then
fail while writing `evaluation.json`.

| Item | Value (03:25 UTC) |
|---|---|
| Weeks completed | 23 (2024-12-27 back to 2024-07-26) |
| Run tally | $41.66 of $140 |
| OpenRouter balance | $108.77 |
| Rate | about $9.5 per hour, 12 to 13 minutes per week |
| Left alone | about 68 weeks by about 12:30 UTC, then failure |

Cause (verified by a structure-only dry run of the evaluation tail):
- `scripts/llm_v2c1_run.py:144-146` computes the identified and not-identified subsets with `evaluate_panel`.
- The re-identification sample has exactly 10 assets per week. No week has 10 in one subset (maximum 9), and
  `weekly_ic` drops weeks with fewer than 10 rows. Both subsets therefore have zero weeks.
- `newey_west_t` returns NaN for fewer than 3 weeks. `ResearchRun.write_json` serialises with
  `allow_nan=False` and raises.
- `forecasts.json` is written one line earlier, so realised returns reach the disk before the crash.
- The same NaN path fires in `by_year` if a calendar year ends with fewer than 3 completed weeks.
- No in-flight patch is possible. The run script and `evaluate.py` are hash-checked at every write.

Consequences:
- The attempt is consumed either way. A replacement registration is needed either way.
- Stopping now loses nothing that continuing would keep. The per-asset cache survives a stop.
- Continuing has two costs. It spends about $9.5 per hour on a provider mix that is itself a finding (section 2).
  It also writes `forecasts.json` with outcomes before the replacement registration exists, which weakens the
  claim that the amended evaluation was fixed before any outcome was visible.

**Recommendation: stop now** (clean interrupt, `failed.json` recorded), then decide the replacement design.
The run was not touched. An attempted reversible pause was blocked by the permission system and not retried.

## 2. Provider mix: price and behaviour (class A, verified)

The pin is DeepSeek V4-Pro fp8 with provider order Baidu then StreamLake. Both endpoints are admitted by the
charter as "same weights". They are not equivalent in price or behaviour.

| Measure (cached calls) | Baidu | StreamLake |
|---|---|---|
| Share of calls | 91 % | 9 % (up to 72 % in one week) |
| Judge call, reasoning tokens | 2,744 | 1,444 |
| Judge call, completion tokens | 3,045 | 1,703 |
| Judge call, cost | $0.0141 | $0.0039 |
| Market analyst call, cost | $0.0028 | $0.0012 |
| Week at this provider only (role-weighted) | about $2.01 | about $0.60 |

Within-week output differences, StreamLake minus Baidu (22 weeks):

| Output | Difference | t |
|---|---|---|
| Market analyst probability | −0.042 | −3.3 |
| Judge confidence | +0.029 | +2.7 |
| Judge probability | +0.002 | +0.3 |
| Judge abstention rate | 4.9 % vs 8.6 % | −1.2 |

Reading:
- The forecast panel mixes two endpoints in week-clustered proportions. That is unmodelled noise in the panel.
- The judge probability itself shows no detectable shift. The market analyst and the confidence do.
- Assignment to StreamLake is a fallback event, not randomised. The differences are indicative, not causal.
- The 3.3-fold price gap is the largest lever in the whole system. At StreamLake prices the full 156-week
  window costs about $94. At Baidu prices the same budget buys about 45 weeks.
- A provider change is a configuration change (new config hash, no cache reuse, new charter). Whether the
  shorter StreamLake reasoning costs forecast quality is unknown. A no-outcome check is possible: re-run 2 to 3
  cached weeks on StreamLake only and on Baidu only, and compare within-week rank agreement of the judge
  against Baidu's own repeat noise. Estimated cost $8 to $9.

Minimum mitigation under any path: record the provider per call (already done), report a Baidu-only
sensitivity, and fix one provider order explicitly in the next charter.

## 3. Class A: findings that affect the forecasts

| # | Finding | Evidence | Status |
|---|---|---|---|
| A1 | Quant percentile uses the wrong reference class. The ridge score is ranked over all 127 to 200 card symbols, while the target is the top-50 median. The same raw percentile is shown to the forecast interpreter as "percentile N of the universe" and enters the hybrid as q. | Weekly median of the shown percentile inside the top-50 averages 0.438 (range 0.245 to 0.663), below 0.40 in 53 of 156 weeks. Wrong side of 50 for 7.1 % of dossiers. | Verified |
| A2 | Provider mix (section 2). | See above. | Verified |
| A3 | Skill record printed from too little history. | "over the last 1 weeks" at 2022-01-07. 26 weeks reached only in mid-2022. Not in the newest-first window of this run. | Verified |
| A4 | Stored quant forecasts before 2022-10-07 are not reproducible from current code. `dossier_build.py:50` reuses a parquet written before a `forward_returns` fix. | Maximum difference 0.022 (2022-06-03). Exact from 2022-10-07. Not in the window of this run. | Verified |
| A5 | Residual identifiers in dossier text. | Own ticker as a token in 13 dossiers (for example "its OP token", 2023-02-10 to 03-03). | Verified |
| A6 | A failed debate leaves a file without a debate stage. A resume would re-run it and change the deployed probability. | RAREUSDT 2024-09-27, HTTP 400, one case. | Verified |
| A7 | Mislabelled or misleading card lines. | Size bucket "unavailable" in 5,292 of 7,800 dossiers. Unwinsorised outliers. Cross-sectional percentile printed after a different lookback than the one it ranks (`funding_xs_pct` ranks 3-day funding, shown after the 30-day value). | Percentile lookback verified in code. Counts reported. |
| A8 | Near-duplicate and stale text items. | 3,528 of 93,023 items near-duplicate. One item repeated for up to five weeks tagged as new information. | Reported |
| A9 | Text availability correlates with size. | Items present for 95 % of the top volume quintile and 73 % of the bottom. | Reported |
| A10 | Last-speaker effect in the debate. | +0.026 toward the last speaker (t 10.9). Both orders are run and averaged, which cancels it in the mean. | Reported |
| A11 | Judge without debate is told to read a debate that is empty. | Prompt assembly. | Reported |
| A12 | Agents reproduce real names that are absent from the dossier. | 73 of 40,176 output strings (for example "Elon Musk" for Person_1, DOGEUSDT 2024-12-06). Evidence that anonymisation is partly reversed from memory. | Reported |
| A13 | Possible look-ahead not ruled out: emissions vintage, Wayback first-capture date as publication date, Reddit post edits. Raw CoinMetrics and DefiLlama inputs are absent from the devbox. | Emissions feature IC −0.040, so no evidence of benefit. | Not verified |
| A14 | Credit exhaustion path. HTTP 402 raises a plain `ORError`. Assets would be marked failed and weeks would still count as complete. | Balance $108.77 against remaining cap $98.34. Margin about $10, positive. Cost of truncated or failed attempts is not added to the tally and erodes it. | Mechanism verified. Not triggered. |

Checked and clean:
- Bar timing, forward returns (simple, close to close), ridge labels realised before each fit.
- All 93,023 text items have `as_of` at or before the decision time. Leak grep clean.
- 7,800 dossiers equal the manifest. Universe is 156 weeks of exactly 50 assets, no missing forward return.
- Cache integrity of all files. Quant wording appears in no role except the forecast interpreter.
- Book weights satisfy the constraints and reproduce. Newey-West weights, funding sign and Sharpe scaling are correct.
- Encompassing regression has no collinearity problem. Simulated size 0.05.

## 4. Class B: evaluation and reporting

| # | Finding | Evidence | Status |
|---|---|---|---|
| B1 | Results writing fails on NaN (section 1). The charter's identified versus non-identified gates cannot be computed by this code at all. | Dry run. | Verified |
| B2 | Gates 1 and 2 test the ridge, not the LLM. `p_hybrid` is rank-equivalent to the quant percentile. | Within-week Spearman with q: mean 0.95, minimum 0.83. With the judge: 0.09. Judge versus quant: −0.11. Only the encompassing gate isolates the LLM. | Verified |
| B3 | A pass through LLM skill is nearly unreachable under the three-gate rule. | Simulation: judge partial IC 0.05 with a skill-less ridge gives P(encompassing t ≥ 2) 0.78 and P(all three gates) 0.05. Ridge residual IC in the 91 weeks before the run window: mean 0.007, t 0.48. | Reported |
| B4 | Power is lower than the charter states. | Charter: detectable IC 0.036 at 52 weeks, which assumes weekly IC sd 0.13. Measured sd 0.204 for a quant-like panel with autocorrelation factor 1.22, 0.143 to 0.149 for a noise-like panel. At 61 weeks, 80 % power needs IC 0.090 (hybrid gate) or 0.054 (encompassing). At 156 weeks the encompassing figure is about 0.034. A fail at 60 to 70 weeks says little about IC 0.02 to 0.05. | sd reported. Arithmetic verified. |
| B5 | Recalibrated Brier gate barely discriminates. | Test weeks equal completed weeks minus 52: about 15 at 68 weeks, newest weeks only. No significance requirement. Simulated P(pass, no skill) 0.39 and P(pass, hybrid IC 0.05) 0.59. | Week count verified. Simulation reported. |
| B6 | Sub-period gate is vacuous. | "Same sign of mean IC in ≥ 2 of 3" holds for any three non-zero numbers. Undefined with two years present. No code evaluates it. | Verified |
| B7 | The t ≥ 2 rule is oversized on short slices. | P(t ≥ 2) under the null: 3.5 % at 61 weeks, 8.7 % at 13, 11.7 % at 9, 17.5 % at 5 (nominal 2.3 %). | Verified |
| B8 | No verdict object. Cells are marked complete unconditionally. DSR is named in the charter without threshold and exists nowhere in code. The verdict would be assembled by hand after outcomes are visible. | Code and charter line 72. | Verified |
| B9 | Headline book Sharpe excludes funding. The placebo dictionary's no-funding `sharpe` key overwrites the funded one. Placebos ignore funding. | Funded and unfunded variants report the identical value. | Verified |
| B10 | Book weights, weekly book returns and funding are not in the registered outputs. Funding store and call cache are unhashed. | Registration file. | Reported |
| B11 | Abstention handling is inconsistent. In the deployed panel an abstaining judge yields a quant-driven probability (0.11 to 0.85 in 62 of 71 cases) that enters the IC gate, while the book holds the asset flat. In the judge-only panel abstention maps to 0.5 while the judge mean is 0.473, so "no view" ranks as mildly bullish. | Cached outputs. | Verified |
| B12 | Volatility tilt in the book. The score (p − 0.5)/vol is demeaned after dividing by vol, and p has a level bias (A1). The asset-shuffle placebo removes the tilt, so its p-value can reflect the tilt. Placebo p has no +1 correction. | Mechanism in `rule_weights`. Magnitude not quantified. | Mechanism verified |
| B13 | Funding window is shifted one day before the holding period. `funding_coverage` evaluates to 2.76 instead of 1. | Window (Fri 00:00, +7 d] against a Saturday 00:00 position. 3 of 21 prints differ. Correlation with the correct window 0.989. | Verified |
| B14 | Identification is confounded with text availability. | Identified rate 0.4 % without items (n 237), 56.5 % with items (n 1,323). | Verified |
| B15 | Judge is close to a re-weighting of the analysts. | R² 0.789 on analyst probabilities (market 0.58, fundamental 0.31, news 0.15). 87 % of judge values inside the analyst range. | Verified |
| B16 | Debate contrast is weak as designed. | 12 assets per week, unresidualised IC, two-judge mean against one judge. Debate moves p by 0.024 for 35.5 % of spend. | Reported |
| B17 | Multiplicity. | 7 panels, 2 encompassing tests, 5 books, 2 subsets, by-year. Three registered gates. Fine if the rest is labelled descriptive. | Reported |
| B18 | `config_sha` omits prompt-assembly code, the hybrid formula, the selection seed and the request body. Temperature is hashed but never sent. `number_grounded_rate` understates grounding. Spend cap is per process. | Code. | Reported, spend cap verified |

## 5. Class C: improvements for a later cycle

1. Rank q inside the top-50 and calibrate it to a probability before mixing. Fixes A1, B12 and part of B2.
2. Make the judge coefficient in the encompassing regression the primary LLM gate, with stated power. Keep the
   hybrid gates as system-level gates.
3. Replace the Brier and sub-period gates with tested statistics (for example a block-bootstrap interval for
   the Brier skill, sign consistency against a stated null).
4. Have the code write the verdict object, weights, weekly returns and funding. Hash the funding store and a
   cache manifest. Compute DSR or drop it from the charter.
5. One abstention rule across panel and book. Either exclude abstentions from the judge panel or map them to
   the weekly judge mean.
6. Deterministic weekly interpreter weight (saves about 7.5 % of spend). Debate share (35.5 % of spend) is the
   next cost lever, but the debate is the assignment's core and should stay.
7. Dossier rebuild v2.9: label fixes, de-duplication, stale-item tagging, ticker-token scrub, minimum history
   for the skill record, quant forecasts regenerated from current code.
8. Attempt log with the cost of failed and truncated calls. Treat HTTP 402 as a spend-cap stop.
9. Named-versus-anonymised ablation and a flag probe on all 50 assets if the memorisation estimate matters for
   the thesis argument. A12 suggests it does.

## 6. Paths after a stop

| | Path A: minimal amendment | Path B: rebuild and full window |
|---|---|---|
| Change | Same dossiers, same agent config, Baidu first. Fixed evaluation tail only (B1, B6, B8, B9, B11, B13 as pre-registered corrections). | Dossier v2.9 and agent fixes (A1, A5 to A8, B11), one provider order, evaluation fixes, new charter. |
| Cache | Reused (23 weeks). | Not reused. The 23 Baidu weeks become a sensitivity sample. |
| Sample | About 68 weeks for the remaining $98. | 156 weeks for about $94 if StreamLake pricing holds. |
| Power (encompassing, 80 %) | IC about 0.054 | IC about 0.034 |
| Effort | Hours. | One to two days plus a mechanics preview. |
| Risk | Known class A limitations stay and are disclosed. | StreamLake throughput and quality unverified. Needs the balance to stay near $108, so each further hour of the current run removes about $9.5 from it. |

Both paths start with the same step. Path B stays affordable without a top-up only if the run stops within
about an hour.

## 7. Housekeeping

- A stray `uv` build process (PID 48318) has used a full core for 18.6 days. Not touched.
- Scratch material of the review: `/tmp/review_main`, `/tmp/review_data`, `/tmp/review_agents`, `/tmp/review_eval`.
