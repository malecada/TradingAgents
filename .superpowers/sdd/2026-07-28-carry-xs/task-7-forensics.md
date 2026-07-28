# carry_xs_t1 — Forensic Verification of Dev-Gate NEGATIVE

Date: 2026-07-28. Branch: feature/xs-momentum. Scope: dev window only
(2021-01-01..2025-03-31). Holdout (2025-04-01+) NOT touched — no metric computed
past 2025-03-31 anywhere in this report.

Result under scrutiny: 0/6 configs pass carry_xs_t1 gates
(net_sr_min=1.0, placebo_p_max=0.05, dsr_min=0.9). Best config L=30/leg_frac=0.2:
net_sr=+0.695, placebo_p=0.094 (max of indep 0.066 / shared 0.094), DSR=0.123.

All probe scripts are throwaway, in
`/tmp/claude-1000/-home-malecada-master-thesis/04d02b03-5d90-4e14-8e89-d597c8eeb64f/scratchpad/`
(`build_common.py`, `probe1_density.py` .. `probe6_repro.py`,
`probe_dsr_check.py`), not committed.

## 1. Signal density — book was NOT starved

Universe membership is a clean top-50 every refresh (min/med/max members =
50/50/50 across all 51 monthly refreshes). Restricting to the executed dev
window (post first-refresh, ≤2025-03-31, 1547 days × up to 50 members =
77,350 universe-member-days):

| L | non-NaN signal | 30-gapless funding OK | fully valid (member & signal & fundok) |
|---|---|---|---|
| 1 | 77327/77350 = 99.97% | 99.97% | 99.97% |
| 7 | 99.97% | 99.97% | 99.97% |
| 30 | 99.97% | 99.97% | 99.97% |

Per-day `n_valid` distribution: min=49, median=50, max=50 for every L. Zero
days across the whole dev window fall below `MIN_VALID=5` (which would force
a flat day) — `n_active_days=1547/1547` in the ledger is real, not an
artifact of a degenerate mostly-flat book. **This rules out the §45-style
sparsity mechanism** (wide-trend's negative was partly an under-populated
book; carry_xs is not).

## 2. Mutation kill-test — engine IS wired to the signal

Best config (L=30, leg_frac=0.2), negating the signal (`carry_weights` fed
`-S`):

- real SR = **+0.6948**
- negated-signal SR = **−1.3155**

Sign flips as expected (kill test **PASSES** — a no-op/mis-wired engine
would leave SR unchanged or move it only slightly). The sum (+0.695 − 1.316
= −0.621) is not exactly zero because cost and rf drag are *constant*
burdens applied on both the real and negated book (they don't flip sign with
the signal) — this asymmetry is explained quantitatively in §3/§4 below, not
a red flag.

## 3. P&L decomposition (best config, L=30/leg_frac=0.2)

| variant | net_sr | total_logret | ann. simple return |
|---|---|---|---|
| (a) full engine as registered | +0.695 | +0.796 | +20.67% |
| (b) cost=0, rf=0 | +1.005 | +1.152 | +31.24% |
| (c) funding zeroed (price leg only), no cost/rf | +0.408 | +0.468 | +11.68% |
| (d) price zeroed (funding leg only), no cost/rf | +15.49 | +0.684 | +17.51% |

Row (a) vs (b) is the *combined* cost+rf drag (−0.356 logret). Decomposed
analytically into its two additive components: isolated cost-only drag =
−0.169 logret, scaling with the scored-window turnover (0.1087/day × 10bps ×
1547 days ≈ 0.169); isolated rf-only drag = −0.187 logret, a deterministic
daily charge on full capital independent of turnover (1547 days × rf_daily
1.2060e-4 ≈ 0.187) — over the 4.2-yr window (≈4.0%/yr and ≈4.4%/yr
respectively, consistent with `RF_DAILY` house convention and ~8.5% mean
gross turnover/day). rf's deterministic, turnover-independent value is the
basis for distinguishing the two components: 0.169 + 0.187 = 0.356 matches
the (a)-vs-(b) combined drag exactly.

**Key finding, contradicts the pre-registered hypothesis stated in the
task**: at the best config, the funding leg is *not* thin cross-sectionally —
it is strongly positive and low-variance (SR +15.5, near-cash-like, because
funding differentials are a slow-moving, low-noise signal). The price leg is
*also* positive (SR +0.41), not destructive. Combined gross (cost/rf-free)
SR is a healthy +1.005 — comfortably above the 1.0 floor. **What kills the
gate is cost+rf drag alone**, pulling the *registered* net SR down to 0.695,
below the 1.0 floor. Both legs contributing positively cross-sectionally
(unlike the time-series funding-carry finding in §41) but the combined edge
is thin relative to the house's harsh-honest cost+rf convention.

## 4. Turnover/cost share, all 6 configs

| L | leg_frac | net_sr | no-cost SR (rf kept) | gross ann. return | cost drag (ann. logret) | mean gross turnover/day |
|---|---|---|---|---|---|---|
| 1 | 0.10 | −0.269 | +0.493 | 23.86% | 0.331 | 0.716 |
| 1 | 0.20 | −0.464 | +0.623 | 18.49% | 0.296 | 0.663 |
| 7 | 0.10 | −0.202 | +0.067 | 2.94% | 0.116 | 0.236 |
| 7 | 0.20 | +0.463 | +0.820 | 24.88% | 0.097 | 0.210 |
| 30 | 0.10 | +0.185 | +0.302 | 13.74% | 0.050 | 0.099 |
| 30 | 0.20 | +0.695 | +0.842 | 25.59% | 0.040 | 0.085 |

All six exactly reproduce the ledger's `net_sr` and `mean_gross_turnover`
(cross-checked programmatically, `match_sr=True` for all rows).

**L=1's negativity is purely cost-driven**: gross (no-cost) SR is *positive*
for both L=1 configs (+0.49, +0.62) but daily-refresh turnover (~0.66–0.72
of book/day, because a 1-day funding signal is noisy and flips membership of
the top/bottom legs constantly) drags net SR to −0.27/−0.46. This is
expected, mechanical, and not a defect — a 1-day trailing-mean carry signal
being too noisy/high-turnover to survive 10bps/side costs is a real
economic finding, matching how L=7 (mid-turnover) and L=30 (low-turnover)
progressively recover.

## 5. Tie mass at L=30 — disjointness amendment essentially never binds in-sample

Restricted to dev days with n_valid≥5 (1547/1547 days), best config
(L=30, leg_frac=0.2, n_leg≈10 of ~50 valid names):

- Days where the signal value AT the short-leg or long-leg cut boundary
  recurs elsewhere (i.e., a tie sits exactly on the leg-selection cutoff):
  **4/1547 = 0.26%**.
- Days where a **naive** (no-exclusion) single-sort short/long leg selection
  would actually overlap in membership — the exact bug the amendment was
  written to prevent — **0/1547 = 0.0%**.

The amendment (explicit `shorts_set` exclusion for the long leg) is a
necessary *correctness* guard — the first dev invocation crashed on the
frozen net-exposure assert, per the gates.json `amendment_2026-07-28` note,
zero metrics read at that time — but for the specific window/config
actually scored, ties never materially reassign portfolio weight. The
negative result is not an artifact of the tie-handling rule.

## 6. Sanity repro — bit-exact

Independent fresh script (`probe6_repro.py`), reloading klines/funding from
disk from scratch (not reusing the shared pickle used by probes 1–5), calling
only the registered module functions (`build_funding_matrix`, `carry_signal`,
`carry_weights`, `run_ls_portfolio`) for L=30/leg_frac=0.2:

```
independent net_sr=0.6948016551  ledger net_sr=0.6948016551  diff=0.00e+00
independent maxdd=0.5749418756   ledger maxdd=0.5749418756   diff=0.00e+00
independent total_logret=0.7964110013  ledger total_logret=0.7964110013  diff=0.00e+00
n_days independent=1547  ledger=1547
```

Exact float match — no reproducibility defect.

## Extra check: DSR computation (not in original probe list, done to close the
loop on the most severe-looking number, DSR=0.123 vs 0.9 floor)

Independently recomputed via `variance_of_sr`/`expected_max_sharpe`/
`deflated_sharpe_ratio` on the raw daily-return series for the best config:
`sr_perbar=0.036368`, `se_sr=0.027572`, `expected_max_sharpe(n_trials=87)
=0.068413` → **DSR=0.122572**, exact match to the ledger (`0.122572`,
`n_trials_at_eval=87`).

Sensitivity check — what DSR would be at lower trial counts (same SR/SE):

| n_trials | expected_max_sharpe | DSR |
|---|---|---|
| 1 (no multiplicity penalty) | 0.0143 | 0.788 |
| 5 | 0.0329 | 0.550 |
| 10 | 0.0434 | 0.399 |
| 20 | 0.0524 | 0.280 |
| 87 (actual) | 0.0684 | 0.123 |

Important nuance: even with **zero** multiple-testing correction (n_trials=1),
DSR would be 0.79 — still below the 0.9 floor. The 87-trial ledger-wide
multiplicity penalty makes it much worse (0.79→0.12), but the underlying
signal is intrinsically weak even before that: the daily-SR standard error
(0.0276) is on the same order as the observed daily SR (0.0364), i.e. the
raw estimate is only ~1.3 SE from zero pre-multiplicity. DSR failing this
hard is not solely a multiplicity artifact.

## Verdict

**NEGATIVE VERIFIED.** No engine, wiring, or data defect found. Every probe
came back clean:
- Book fully populated (~50/50 valid names, 99.97% density) — not starved.
- Kill-test flips sign as required — engine is wired to the signal.
- Bit-exact independent reproduction of the ledger numbers.
- Tie-handling amendment doesn't materially bind in-sample (0% naive-overlap
  days, 0.26% boundary-tie days).
- L=1's failure is cleanly cost-driven (gross SR positive, net SR negative
  purely from high turnover × 10bps).
- Best config (L=30/leg_frac=0.2) has genuinely positive gross legs on
  *both* sides (price SR +0.41, funding SR +15.5 in isolation, combined
  gross SR +1.005) — contrary to the pre-registered "funding thin
  cross-sectionally" concern, the funding differential is actually the
  stronger, cleaner leg. What fails the gate is (a) cost+rf drag pulling net
  SR from 1.005 to 0.695 (below the 1.0 floor), and (b) the DSR/placebo
  statistical-rigor gates, where even pre-multiplicity significance is weak
  (SE_sr ≈ SR_sr) and the 87-trial ledger multiplicity penalty then crushes
  DSR to 0.123. This is a real, thin cross-sectional carry premium that
  doesn't clear the house's harsh-honest cost/rf/multiplicity bar — not a
  measurement artifact.
