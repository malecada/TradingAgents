# Phase-1 Tier-1 report — volatility (T3), volume (T4), funding (T6) daily cells (2026-07-30)

Battery `predlab_p1_classical`, tier t1, dev origins 2021-01-01 → 2025-03-31
(n = 1,551 daily; 4,651 8h funding prints). DM one-sided vs baseline
(positive = model better). Forensics: `data/predlab/forensics_t3*.json`,
`forensics_t4.json`, `forensics_shuffled_null.json`.

## T3 realized volatility (QLIKE, vs registered baseline har_levels)

| Cell | Model | QLIKE | DM p vs har_levels |
|---|---|---:|---:|
| BTC 24h | ewma_0.94 | 0.4387 | 0.832 |
| BTC 24h | har_levels | 0.3983 | — |
| BTC 24h | log_har | 0.4278 | 0.665 |
| BTC 24h | **harq** | **0.3521** | **1.0e-3** |
| BTC 24h | garch11 / egarch11 / gjr11 | 0.4139 / 0.4279 / 0.4314 | 0.94 / 0.97 / 1.00 |
| ETH 24h | ewma_0.94 | 0.4568 | 0.392 |
| ETH 24h | har_levels | 0.4759 | — |
| ETH 24h | log_har | 0.4198 | 0.277 |
| ETH 24h | **harq** | **0.4025** | **4.8e-12** |
| ETH 24h | garch11 / egarch11 / gjr11 | 0.4031 / 0.4525 / 0.4215 | 0.015 / 0.40 / 0.037 |

Strongest-baseline pairwise (forensics v2 K3, real data):

| Cell | HARQ vs log_har | HARQ vs EWMA |
|---|---|---|
| BTC 24h | Δ17.6%, p 0.095 | Δ19.8%, **p 0.006** |
| ETH 24h | Δ3.9%, p 0.427 | Δ12.0%, p 0.205 |

**Verdicts.**
- **BTC 24h T3: SKILL-CANDIDATE (HARQ).** Best of 7 models; beats the
  registered baseline (p 1.0e-3, ΔQLIKE 11.6% ≥ 2% floor) and EWMA (p 0.006);
  vs log_har the margin is large (17.6%) but noisy (p 0.095). Phase-5 MCS
  (registered within-cell multiplicity tool) + holdout will formalize.
- **ETH 24h T3: PREDICTABLE-VS-WEAK-ONLY.** HARQ is the best point estimate,
  but no significant edge over the strongest alternatives (log_har p 0.43,
  EWMA p 0.21). The battery's p = 4.8e-12 vs har_levels reflects the levels-OLS
  baseline's fragility under ETH's RV outliers — established by shuffled-data
  forensics — and is therefore NOT read as model skill (charter A1).
- GARCH family never beats HAR-class. HAR > EWMA on BTC (lit-consistency
  check PASS); on ETH levels-HAR is outlier-fragile (EWMA nominally better,
  ns) — motivates robust-loss/log-space variants in later tiers.

## T4 volume (MASE, log dollar volume, vs seasonal_naive_m7)

| Cell | Model | MASE | DM p vs baseline | DM p vs best-t0 alt |
|---|---|---:|---:|---|
| BTC 24h | seasonal_naive_m7 | 0.9036 | — | — |
| BTC 24h | persistence | 0.9712 | 0.996 | — |
| BTC 24h | **seasonal_ar_m7** | **0.7549** | **7.5e-18** | (baseline = best t0) |
| ETH 24h | seasonal_naive_m7 | 0.7419 | — | — |
| ETH 24h | persistence | 0.6960 | 0.0095 | — |
| ETH 24h | **seasonal_ar_m7** | **0.5832** | **5.8e-25** | vs persistence: Δ16.2%, **p 5.9e-41** |

**Verdict: SKILL-CANDIDATE (both cells).** Seasonal-AR (3 short lags + weekly
lag) beats the registered baseline by ΔMASE 16.5% (BTC) / 21.4% (ETH), far
above the 5% floor, and on ETH also beats persistence — the strongest Tier-0
alternative — at p 5.9e-41. Mundane mechanism (persistence + weekly
seasonality combined), exactly the literature prior; survives the corrected
shuffled-null (equality vs hist_mean: p 0.45 / 0.58).

## T6 funding (MSE, vs AR(1))

| Cell | Model | MSE | DM p vs ar1 |
|---|---|---:|---:|
| BTC 8h | persistence / **ar1** / dar1 | 1.573e-8 / **1.478e-8** / 1.561e-8 | 0.90 / — / 0.87 |
| BTC 24h | persistence / **ar1** / dar1 | 1.014e-7 / **9.779e-8** / 9.962e-8 | 0.72 / — / 0.63 |
| ETH 8h | persistence / **ar1** / dar1 | 3.504e-8 / **3.173e-8** / 3.494e-8 | 0.96 / — / 0.96 |
| ETH 24h | persistence / **ar1** / dar1 | 2.306e-7 / **2.142e-7** / 2.300e-7 | 0.83 / — / 0.82 |

**Verdict: BASELINE-WINS (all 4 cells).** Funding is predictable (AR(1)
clearly better than persistence/history), but nothing in Tier 1 beats the
registered strong baseline — DAR(1) adds nothing at these frequencies. Note:
CW columns are not interpretable for these non-nested pairs and are ignored.

## Forensic method lessons (recorded for the house pattern)

1. **Shuffled-target kill-tests are only fair between models that collapse to
   the same unconditional forecast.** Regression models collapse to the
   arithmetic mean; (seasonal-)naive stays a 2×-variance random draw;
   log-space models collapse to the geometric mean (systematic QLIKE
   under-forecast on heavy tails). Cross-class shuffled comparisons are
   structurally biased — v1 K1/K2 and v2 K4 "failures" were probe-design
   artifacts, not leakage. The honest shuffled check is model-vs-hist_mean
   EQUALITY, which passes for 3 of 4 cells.
2. The single remaining anomaly (ETH T3 HARQ vs mean on shuffled, p 0.0034,
   one seed) is a chance allocation of heavy-tail outliers between burn-in
   and eval window (eval-window target mean 11% below full-sample mean;
   HARQ median forecast −11% vs hist_mean while its mean is +1.2%). Leak
   channels are excluded independently (rq alignment audit exact;
   truncation-equivalence; train-on-future canary p 5.6e-15). Lesson:
   **multi-seed shuffled nulls for heavy-tailed targets** — adopted for any
   Phase-5 confirmation forensics.
3. Baseline fragility is itself a finding: gates registered against a fragile
   baseline overstate significance. The registered gate stays as written
   (stop rule), but skill VERDICTS here apply the charter-A1
   strongest-baseline principle, and Phase-5 champion evaluation will gate
   against the MCS surviving set, not a single named baseline.
