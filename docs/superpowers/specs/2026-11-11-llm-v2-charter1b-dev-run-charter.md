# Charter 1b — Multi-agent v2 development run, replacement registration (`llm-v2-charter1b`) — DRAFT, NOT FROZEN

**Status:** drafted 2026-11-11 after the first registered attempt of Charter 1 was interrupted. Not frozen, not
registered, not run. Three items await a decision and are marked **OPEN** (§9).
**Parent charter:** `docs/superpowers/specs/2026-11-09-llm-v2-charter1-dev-run-charter.md` (frozen 2026-11-11).
**Parent attempt:** `llm-v2c1-dev-run-20261111`, registration `research/llm-v2-charter1-20261111/gates.json`,
receipt `research_runs/llm-v2c1-dev-run-20261111/failed.json`.
**Review:** `docs/superpowers/specs/2026-11-11-multiagent-v2-system-review.md` (finding numbers A1–A14, B1–B18
below refer to it).

Charter 1 §7 states that any change after the first dev call is a new charter. This document is that charter.
It replaces the evaluation tail of Charter 1 and nothing else: the agents, prompts, dossiers, model pins, gate
families and gate thresholds are those of Charter 1, and the calls already paid for are reused.

## 1. What happened in the first attempt
- Started 2026-11-10 23:01 UTC at source `dff3aaebe`, newest week first.
- The system review of 2026-11-11, made while the run was in progress, established that the attempt could not
  end as a completed run. The results writer rejects non-finite numbers, and the identified-subset block of the
  evaluation always produces them (ten flagged assets per week, never ten in one subset, so both subsets have
  zero evaluable weeks). The run would have spent the whole cap and then failed while writing
  `evaluation.json`, one line after writing `forecasts.json` with realized returns (B1).
- The review found further defects in the evaluation tail (B6, B8, B9, B10, B11, B13) and a failure path of the
  run loop (A14). None can be patched in a running attempt, because the run script and the evaluation module are
  hash-checked at every write.
- The run was interrupted with SIGINT on 2026-11-11 12:14 UTC. The lifecycle recorded `failed.json` (reason
  `KeyboardInterrupt`), no output file was written, and no forecast was joined with a forward return.
- State of the call cache at the interrupt: 61 complete weeks (2024-12-27 back to 2023-11-03, 3,050 asset-weeks,
  3,111 files) and part of week 2023-10-27 (all 50 assets without debate, 2 of 12 debates).

## 2. Question, target, universe
Unchanged (Charter 1 §1 and §2). The dev window, the newest-first execution order and the truncation rule of
Charter 1 §6a are unchanged: the gates are evaluated on the completed contiguous block of weeks.

## 3. Unchanged
| Item | Value |
|---|---|
| Agent config | `agents-v2.4`, sha `a97972476be6f5b1…`; every agent source file equals the hash in the parent registration (enforced by `scripts/llm_v2c1b_register.py`) |
| Dossiers | builder `dossier-v2.8`, the parent's manifest, identical hash |
| Model pins, provider order, reasoning map, debate count and random debate selection | as registered in Charter 1 |
| Forecast panels and the hybrid formula | Charter 1 §5 |
| Gate families and thresholds | Charter 1 §5 (restated in §5 below) |
| Book | rule twin of Charter 1 §5, taker cost 5 bp per side, realized funding |
| Kline store, cards, quant forecasts, identification flags | the parent's inputs, identical hashes |
| Family | `llm-multiagent-v2`, attempt budget 6; this is attempt 2 |
| Spend cap | $140 cumulative over both attempts (§7) |

## 4. Changes (all fixed before any outcome is opened)
Corrections of the evaluation tail:

1. **Publication cannot fail on a non-finite statistic (B1).** Outputs pass through `json_safe` (NaN and
   infinity become null). Descriptive blocks are guarded: an exception is recorded in place of the value and
   listed in `verdict.json`. The four gate statistics are not guarded. If one of them raises, the run fails
   before any output is written and nothing is unblinded.
2. **Identified-subset estimator (B1, B14).** Charter 1 §4 asked for the forecast gates "computed separately for
   identified and non-identified dossiers". That cannot be computed: the flag sample holds ten assets per week.
   Replacement, descriptive as before: residual ranks of forecast and return are computed within the week on
   the full cross-section; inside each subset the pooled correlation of the two is the subset IC; the reported
   quantity is the gap identified minus not identified, per panel (`p_hybrid`, `p_judge`, `p_quant`), with the
   Brier skill gap alongside. Intervals and two-sided p-values come from a week-block bootstrap (2,000 draws,
   seed 20261111). The memorization estimate is the difference-in-differences, gap of `p_judge` minus gap of
   `p_quant`. Because identification is confounded with text availability (identified 0.4 % without text items,
   56.5 % with), the same estimator is also reported on rows with at least one text item.
3. **Sharpe net of funding (B9).** The headline Sharpe of every book is net of taker costs and realized funding.
   The variant without funding is reported separately. Placebo books pay the same costs and funding as the real
   book, and placebo p-values are (1 + count) / (n + 1) with 500 draws.
4. **Funding window (B13).** Funding is summed over the holding period. For a Friday stamped f (00:00 UTC) that
   is the interval from f + 1 day (exclusive) to f + 8 days (inclusive): the settlement at entry is excluded
   and the settlement at exit is included. The Charter 1 code summed from f to f + 7 days.
   Settlement stamps carry millisecond jitter and are rounded to the minute. Coverage is the share of
   asset-weeks with a funding row.
5. **Sub-period gate evaluated by code (B6).** The rule of Charter 1 §5 and §6a is applied literally to the years
   present: the mean weekly IC must have the same sign in at least min(2, years present) years. See §5.
6. **Verdict by code (B8).** `verdict.json` holds each gate value, its rule, pass or fail, and the overall verdict.
   A statistic that cannot be computed fails its gate. Portfolio gates are evaluated only when every forecast
   gate passes; otherwise their values are marked descriptive. Charter 1 named a deflated Sharpe ratio at trial
   count 1 without a threshold; it is reported as the probabilistic Sharpe ratio against zero, without threshold.
7. **Registered outputs and inputs (B10).** New output `books.json`: weights and the weekly decomposition (gross,
   cost, funding, net, turnover, gross exposure, missing returns) of every book. New registered inputs: the
   funding store digest (347 files) and the call-cache manifest.
8. **Declared sensitivities (A2, B11), descriptive.** The four gate statistics are recomputed (a) without
   abstaining rows and (b) on rows served entirely by the primary provider.

Changes of the run mechanics:

9. **Cache admission.** The 61 completed weeks are loaded from the cache only. No call and no retry is made
   for them. Every cached file is pinned by sha256 in `data/agents_v2/charter1b/cache_manifest.json`; the cache
   may hold nothing else; each file must carry the registered config sha and dossier sha; the stored weekly
   book must equal the book recomputed from the cached forecasts.
10. **Stop rules for newly run weeks (A14).** Execution continues newest first with 2023-10-27 (its cached
    stages are reused) and then older weeks. A week is excluded and the run ends when the spend cap is reached
    inside it, when it raises, or when more than 5 of its 50 assets fail. Under Charter 1 a credit shortfall
    would have produced weeks of failed assets counted as complete.
11. **Pre-flight.** Every verification of inputs, stores and cache runs before the attempt is claimed, so a
    defect found there does not consume an attempt.

Not changed, disclosed as limitations. Each of these alters the forecasts or the gates and belongs to a new
design, not to a correction:

- The quant percentile shown to the forecast interpreter and used in the hybrid is ranked over all card symbols,
  not over the top-50 (A1). Residual identifiers in 13 dossiers (A5). Card labelling issues (A7). Near-duplicate
  text items (A8). The judge without debate is told to read a debate that is empty (A11).
- Provider mix: 91 % of calls at the primary provider, 9 % at the fallback, with measurable differences in
  reasoning length and in some outputs (A2). Sensitivity (b) is the only control.
- `p_hybrid` is nearly rank-equivalent to the quant percentile (within-week Spearman 0.95). The IC gate and the
  Brier gate therefore mostly test the ridge. Only the encompassing gate isolates the LLM (B2, B3).
- The book divides by volatility before demeaning, which leaves a volatility tilt that the asset-shuffle placebo
  removes (B12). The closing trade of the last week is not charged. Positions without a return row earn zero
  and are counted.
- `config_sha` does not cover the prompt-assembly code or the request body (B18). The source-file hashes of the
  registration cover them.

## 5. Gates
Thresholds as in Charter 1. All statistics on the completed contiguous weeks.

| Gate | Statistic | Floor |
|---|---|---|
| Forecast 1 | Newey-West (lag 4) t of the weekly residual rank IC of `p_hybrid`, controls vol_ewma20, ret_4w, dvol_30d | ≥ 2.0 |
| Forecast 2 | Brier skill of `p_hybrid` after walk-forward logistic recalibration, first 52 weeks training only | > 0 |
| Forecast 3 | Encompassing regression, Newey-West t of the mean `p_judge` coefficient next to `p_quant` | ≥ 2.0 |
| Forecast 4 | Sub-periods: mean IC of the same sign in at least min(2, years present) years | pass |
| Portfolio 1 | Rule-twin Sharpe net of costs and funding | ≥ 0.8 |
| Portfolio 2 | Placebo p, shuffled dates and shuffled assets | both ≤ 0.05 |

Portfolio gates count only if all four forecast gates pass. Verdict PASS requires all six.

Known weaknesses of the registered gates, stated before unblinding and not repaired:
- **Sub-periods.** With three years present the rule cannot fail. With the expected window (2023 and 2024
  present, 2023 with about 10 to 14 weeks) it is binding: both yearly means must share a sign. A short year has
  a noisy mean, so this gate can fail by chance. **OPEN (§9):** literal reading as above, or declare the gate
  not evaluable with fewer than three years.
- **Brier gate.** Test weeks are the completed weeks minus 52, about 13, all at the new end of the window. There
  is no significance requirement. Simulated pass probability is 0.39 without skill and 0.59 at hybrid IC 0.05.
- **Power.** At 61 weeks, 80 % power needs a true IC of about 0.054 for the encompassing gate and about 0.090
  for the IC gate. A FAIL says little about an IC between 0.02 and 0.05. The t ≥ 2 rule has a null rejection
  rate of 3.5 % at 61 weeks.
- **Reading.** The question "does the LLM add over the quant model" is answered by the encompassing statistic
  whatever the overall verdict. The overall verdict answers whether the deployed hybrid clears the registered
  bar.

## 6. Exposure before the freeze
- Forecasts joined with outcomes: only the four descriptive preview weeks disclosed in Charter 1 §6a
  (`research/multiagent-v2/preview_4weeks.json`). Two of them, 2024-06-28 and 2024-12-27, lie inside the window
  of this run. Nothing since.
- First attempt: its evaluation tail never ran and `forecasts.json` was never written.
- System review of 2026-11-11: read the cached forecasts for forecast-side statistics only (distributions,
  rank correlations between panels, provider differences, abstentions, citations, debate shifts). On returns it
  computed the missing-cell pattern of the universe, the residual IC of the quant-only ridge over the 91 oldest
  weeks 2022-01-07 to 2023-09-29 (mean 0.007, t 0.48) and the IC of one card feature. No LLM forecast was
  involved. The 91 weeks overlap this run in at most one week (2023-09-29, reached only if the budget allows).
- Dry run of the new evaluation tail (`scripts/llm_v2c1b_dryrun.py`, record
  `research/multiagent-v2/charter1b_dryrun.json`): the real forecast panel of the 61 weeks with seeded synthetic
  outcomes. The return and funding stores were read for the pattern of missing and delisted cells and for
  settlement counts only. Every path produced a verdict: noise FAIL with descriptive portfolio values, planted
  signal PASS with portfolio gates evaluated, all-zero returns FAIL, a three-week panel FAIL. No descriptive
  block raised. The tail takes about 80 seconds.
- No prompt, schema, weight, threshold or estimator was chosen on the basis of an outcome.

## 7. Budget
| Item | USD |
|---|---|
| Cumulative cap (Charter 1 §7) | 140.00 |
| First attempt, client tally at the last complete week | 127.49 |
| First attempt, cached calls of the interrupted week (262 calls) | 1.58 |
| First attempt, recorded | 129.07 |
| Allowance for calls in flight at the interrupt and not saved | 0.35 |
| Allowance for overshoot (the cap is checked before each of 12 concurrent calls) | 0.15 |
| **Process cap of this run** | **10.43** |

- The account balance gives an independent figure for the first attempt of about $129.27, inside the allowance.
  If all ten debates in flight at the interrupt had been billed in full, the cumulative total could reach about
  $140.6.
- Expected use: about $0.70 for the ten missing debates of 2023-10-27, then about $2.35 per week. That is three
  to four further weeks, 65 to 66 weeks in total, ending at 2023-10-06 or 2023-09-29. Account balance $21.16.
- **OPEN (§9):** spend the remainder as above, or evaluate the 61 cached weeks at zero spend
  (`--cost-cap 0 --no-new-weeks`).

## 8. Registration and execution
- Program `llm-v2-charter1b-<date>`, experiment `llm-v2c1b-dev-run-<date>`, parent `llm-v2c1-dev-run-20261111`
  (copied verbatim, failed receipt), stage development, reuse exploratory, same window and dataset as the parent
  with the first attempt added to the dataset history.
- Source files: the parent's agent and dossier files with identical hashes, plus `agents_v2/evaluate.py`,
  `agents_v2/portfolio_eval.py`, `agents_v2/charter1b.py`, `scripts/llm_v2c1b_run.py`,
  `scripts/llm_v2c1b_manifest.py`, `scripts/llm_v2c1b_register.py`.
- Outputs: `forecasts.json`, `evaluation.json`, `portfolio.json`, `books.json`, `cost.json`, `verdict.json`.
  Cells: agent-run, forecast-gates, portfolio-gates, identified-subsets.
- Command: `scripts/llm_v2c1b_run.py --registration research/llm-v2-charter1b-<date>/gates.json --experiment
  llm-v2c1b-dev-run-<date> --cost-cap 10.43`.
- Tests: `tests/research/test_agents_v2_charter1b.py` (cache tamper detection, store verification, verdict
  rules, the evaluation tail on synthetic panels, the lifecycle run end to end in a temporary repository with a
  stub client: resumed week, cap inside a week, failing provider, zero-spend variant, defects caught before the
  claim), `test_agents_v2_portfolio.py` (funding window boundaries with jitter, funded headline, placebo
  basis), `test_agents_v2_eval.py` (sub-period rule, subset estimator).

## 9. Open decisions before the freeze
1. Spend the remaining $10.43 for three to four more weeks (recommended), or evaluate 61 weeks at zero spend.
2. Sub-period gate: literal reading, binding with two years present (recommended, it is what Charter 1 §6a
   says), or not evaluable below three years.
3. Whether a rebuilt design (dossier v2.9, corrected quant reference class, one provider, full 156 weeks) will
   be attempted later on the same window. If so, its charter has to be frozen before the outputs of this run
   are opened, otherwise it is conditioned on them.

## 10. After the run
- The verdict is the one in `verdict.json`. No re-run, no re-estimation and no change of estimator on this
  window under this charter.
- PASS or FAIL, the dev window stays exposed for this mechanism. A FAIL closes the configuration, not the
  family: four attempts remain and each needs its own charter.
- Sealed-A and Sealed-B stay untouched.
