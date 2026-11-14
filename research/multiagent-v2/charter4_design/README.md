# Charter 4 design folder (fresher information: daily decision, next-day return)

Stage V0 work for the Charter 4 draft. Nothing here joins a text feature with a real return or any other
price quantity dated at or after its decision.

## Rule for the form of the daily gate statistic (written before the power draws)

The module carries two forms of the daily statistic of the reader score against the target residual: the
within-day correlation (`corr`) and the within-day covariance (`cov`). One of them is registered as the gate,
the other stays descriptive. The choice is made on synthetic targets only:

1. A form is excluded when its pass rate on a noise cell (400 draws) has a 95 % interval wholly above 5 %.
2. Among the remaining forms the one with more passes in the `factor` cell with the `fresh` plant, summed
   over the planted sizes 0.05, 0.10, 0.15 and 0.20 (200 draws each), is chosen.
3. A difference below 5 % of those 800 draws (fewer than 40 passes) leaves `corr`, the form of Charters 2 and 3.

### Outcome of the rule (3,400 draws, `null_gate_summary.json`)

No form is excluded: the noise pass rates lie between 1.8 % and 2.8 % (`corr`) and between 1.3 % and 2.0 % (`cov`)
in all five noise cells. Passes in the `factor` cell with the `fresh` plant over the four planted sizes:
`corr` 28 + 125 + 191 + 200 = 544, `cov` 28 + 131 + 195 + 200 = 554. The difference is 10 passes, below 40.
The gate form stays `corr`.

## Rule for the feature set of the fitted gate score (written before its draws)

The first power draws show that a fitted score pays for the estimation of six weights on sparse features. The
feature set of the fitted gate score is therefore chosen on synthetic targets, with the gate form fixed at `corr`:

1. Candidates: `BLOCK_R` (six features, the drafted set), `FRESH` (the four features of the last day) and
   `TONE` (`tone_1d` and `tone_prev6`).
2. Draws in the `factor` cell with one set of seeds for all candidates: 400 noise draws and 200 draws for each
   of the plants `fresh` 0.05, `fresh` 0.10, `week` 0.03 and `week` 0.06.
3. A candidate is excluded when the 95 % interval of its noise pass rate lies wholly above 5 %.
4. Among the remaining candidates the one with the most passes summed over the four planted cells (800 draws)
   is chosen. A lead of fewer than 40 passes over `BLOCK_R` leaves `BLOCK_R`.
5. A score with a fixed direction (the residual of `tone_1d`, no fitted weight) is reported next to the
   candidates. It is not a candidate under this rule: taking it as the gate fixes the sign of the hypothesis and
   is a decision for the charter approval.

### Outcome of the rule (1,200 draws, `gate_score_power.json`)

Noise pass rates: `BLOCK_R` 1.8 %, `FRESH` 1.5 %, `TONE` 3.0 % (400 draws each). No candidate is excluded.

| plant | size | `BLOCK_R` | `FRESH` | `TONE` | fixed direction, test days | fixed direction, all days |
|---|---|---|---|---|---|---|
| fresh | 0.05 | 10.5 % | 16.5 % | 20.0 % | 29.5 % | 39.0 % |
| fresh | 0.10 | 57.5 % | 71.5 % | 75.5 % | 81.5 % | 92.0 % |
| week | 0.03 | 15.5 % | 3.0 % | 28.0 % | 7.0 % | 10.5 % |
| week | 0.06 | 79.0 % | 7.5 % | 87.0 % | 16.5 % | 24.5 % |
| passes of 800 | | 325 | 197 | 421 | 269 | 332 |

`TONE` leads `BLOCK_R` by 96 passes, more than 40. The fitted gate score uses `tone_1d` and `tone_prev6`. The
six-feature score stays in the run as a descriptive score. Both plants are defined on the tone features, so the
rule favours them by construction: an effect that lives only in the unfavourable-event, event-count or stance
features is not what the gate is built to detect.

The pass rates and the power of the registered gate were drawn again with this score (`null_gate.jsonl`,
`null_gate_summary.json`). The draws of the first round with the six-feature score are kept as
`null_gate_block_r.jsonl` and `null_gate_block_r_summary.json`.

## Pass rate and power of the registered gate score (3,800 draws, `null_gate_summary.json`)

Every draw keeps the 54,300 rows of real decision-time regressors and replaces the next-day return by a
synthetic one. The gate runs by the registered functions. Seeds 0 to 399 in the cells without a planted effect,
0 to 199 in the planted cells. A planted size is given in units of the asset's own daily volatility and, in
brackets, in basis points per directed asset-day (2,080 asset-days with a fresh direction on the test days,
7,006 with a direction over the week).

| cell | draws | pass rate `corr` (95 % interval) | pass rate `cov` | t mean / sd (`corr`) |
|---|---|---|---|---|
| noise | 400 | 2.5 % (1.0 to 4.0) | 1.8 % | +0.05 / 1.05 |
| factor | 400 | 1.5 % (0.3 to 2.7) | 0.8 % | +0.05 / 1.01 |
| drift | 400 | 2.5 % (1.0 to 4.0) | 1.5 % | +0.06 / 1.00 |
| curved | 400 | 1.8 % (0.5 to 3.0) | 1.0 % | +0.06 / 1.01 |
| attention | 400 | 2.0 % (0.6 to 3.4) | 1.0 % | +0.06 / 1.00 |
| stress | 400 | 2.5 % (1.0 to 4.0) | 1.5 % | +0.05 / 1.00 |
| fresh 0.05 (18.4 bp) | 200 | 22.0 % | 21.0 % | +1.12 / 1.11 |
| fresh 0.10 (36.7 bp) | 200 | 77.0 % | 81.5 % | +2.77 / 1.06 |
| fresh 0.15 (55.1 bp) | 200 | 98.5 % | 99.0 % | +4.32 / 1.06 |
| fresh 0.20 (73.5 bp) | 200 | 100 % | 100 % | +5.84 / 1.09 |
| week 0.03 (13.5 bp) | 200 | 29.5 % | 24.5 % | +1.34 / 1.27 |
| week 0.06 (27.0 bp) | 200 | 87.0 % | 81.5 % | +3.28 / 1.11 |
| week 0.10 (45.0 bp) | 200 | 100 % | 100 % | +5.64 / 1.10 |

No cell without a planted effect has an interval wholly above 5 %. The gate needs a positive mean, so a pass
rate near 2.5 % is the nominal rate of a one-sided test at t 2.0. The t statistic of the `corr` form has a
standard deviation of 1.00 to 1.05 under no effect. Even odds of a pass need about 30 bp per fresh directed
asset-day, or about 20 bp per asset-day when the effect lasts the week.

The rule for the form of the statistic was written for the first round (six-feature score) and its outcome
stands. With the registered score the `factor` cell with the `fresh` plant gives `corr` 44 + 154 + 197 + 200 =
595 passes and `cov` 42 + 163 + 198 + 200 = 603: a difference of 8, again below 40.

## Are the synthetic cells as hard as the real target? (`history_calibration.json`, `shape_cells.json`)

The false-pass rate above is only as good as the synthetic targets. The `history` kind measures, on bars dated
before 2022-01-01 only (364 decision days of 2021, 18,200 rows, 109 assets, no card and no text), how the real
next-day return rank relates to the nine bar-history ranks. The `shapes` kind takes the same measures on the
synthetic cells (three seeds each).

| | share of the target rank variance left by the within-day regression | residual autocorrelation lag 1 / 2 / 7 | one-day reversal | curved share |
|---|---|---|---|---|
| bars of 2021 | 0.680 | −0.005 / −0.004 / +0.010 | −0.024 | −0.003 |
| noise | 0.820 | −0.000 / −0.001 / −0.002 | −0.001 | −0.003 |
| factor | 0.784 | +0.001 / −0.000 / −0.001 | −0.042 | −0.003 |
| drift | 0.785 | +0.009 / +0.007 / +0.004 | −0.042 | −0.003 |
| curved | 0.783 | +0.005 / +0.002 / +0.001 | −0.002 | +0.008 |
| attention | 0.784 | +0.002 / +0.000 / +0.000 | −0.040 | −0.003 |
| stress | 0.690 | +0.031 / +0.027 / +0.020 | −0.039 | −0.003 |

Reading:

- A regression of 50 rows on nine ranks and an intercept leaves 40/49 = 0.816 of pure noise. The bars of 2021
  leave 0.680: the bar history explains about 17 % of the rank variance beyond that baseline.
- Reversal (−0.024, Newey-West t −2.26) and curvature (−0.003) of the real target lie inside the range of the
  first five cells.
- The first five cells did not cover two measures: none explains as much of the target by the bar history
  (0.78 against 0.68), and none has the lag-7 persistence of the residual (+0.010, standard error about 0.008).
- The `stress` cell was added for that reason, before any outcome was opened. Its explained share about equals
  the measured one (0.690 against 0.680: it matches, it does not exceed it), and its residual persistence is
  two to three times the largest measured value. Its pass rate is 2.5 % (10 of 400, first gate alone 11).
- The constants of the `stress` cell (`STRESS_MARKET` 3.0, `STRESS_DRIFT` 2.0) were set once and not tuned
  further.

The measures use 2021 only. The panel window itself (2022 to 2024) is not measured, since its next-day returns
are the outcome of the registered run.

## Panel rebuild check

The `panel` kind was run a second time after the last change to the builders. The rebuilt decision-time panel
equals the stored one that fed every draw above: 54,300 rows, 29 columns, no forward column.

## Files

- `capture_time_audit.py`, `capture_time_audit.json`: first capture-time audit (item timing only).
- `null_gate.jsonl`: one line per synthetic draw of the registered gate score (`scripts/reader_charter4_null_gate.py real`).
- `null_gate_summary.json`: pass rates per cell and form.
- `null_gate_block_r.jsonl`, `null_gate_block_r_summary.json`: the first round, six-feature score.
- `gate_score_power.py`, `gate_score_power.jsonl`, `gate_score_power.json`: draws and outcome of the feature-set rule.
- `history_calibration.json`: the `history` kind (bars before 2022-01-01 only).
- `shape_cells.json`: the `shapes` kind on the six synthetic cells.
- `decision_facts.py`, `decision_facts.json`: facts of the daily panel on the registered builders (no price outcome).
- `post_run_history_diagnostic.py`, `post_run_history_diagnostic.json`: written after the registered run, not a
  registered output. Daily rank correlation of every price-history feature with the next-day return on the
  722 test days, from the outcome column of the registered `forecasts.json` and the decision-time panel. No
  gate and no re-estimation (STATE.md, "Charter 4 run").
