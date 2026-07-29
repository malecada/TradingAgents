# liq_fade_r1 forensics — NEGATIVE-at-probe verified

Replication of `liq_fade_i1` (THESIS section 49) on the monthly-PIT 51-150 rank band (304 symbols), frozen config `thr=3.5, H=48, w_per=0.1, cap=1.0`, cost raised to 20bps for the thinner band. The pre-registered P3 control ran first and closed: primary net SR does not clear the 1.0 floor, so the verdict is plain NEGATIVE, not NEGATIVE-confounded. Task 7 (the gated primary run) was correctly skipped per the plan's decision point — no `results.json` was produced, no gate was evaluated, and no trial-ledger row exists for this experiment. The holdout window (2025-04-01 onward) was never touched.

## Power

1892 masked triggers across 304 band symbols over 4.24 years of dev window (446 events/year, 6.22 events/symbol) — comparable order of magnitude to `liq_fade_i1`'s 710 events over 88 symbols (8.07 events/symbol there). 1884 events have a full H=48 forward window and enter the mean below.

Mean gross forward return per event: **-0.4178%**, sd 18.1486%, standard error of the mean 0.4181% → t = -1.00. This does **not** clear the conventional |t| > 1.96 threshold for distinguishing the mean from zero: individual event returns are extremely dispersed relative to the mean (sd ≈ 43× the mean magnitude), and 1884 events is not enough to average that dispersion down to significance. The events are also not strictly independent draws — market-wide crash days trigger many band symbols simultaneously — so the true standard error (clustered by day) is if anything larger than the naive one reported here, meaning the non-significance is a conservative finding, not an artifact that a better test would resolve in the negative's favor.

The honest characterization is therefore **a well-powered null**, not a well-powered, confidently-signed negative: the sample size is large (more events, more symbols, than `liq_fade_i1`), but the per-event effect size is small relative to per-event noise, and a naive test cannot rule out that the population mean is exactly zero. This does not change the P2 outcome — P2 is a pre-registered **absolute floor** (mean gross return must exceed +25bp), not a significance test, and −0.418% fails that floor decisively in point-estimate terms regardless of whether it is significantly different from zero on the downside. But it matters for how the result should be read: the band shows no detectable *positive* timing edge, which is itself sufficient to fail the pre-registered gate — there is no need to additionally claim the band actively punishes crash-fading, and the data does not clearly support that stronger claim.

Events by calendar year: 2020: 0, 2021: 226, 2022: 360, 2023: 751, 2024: 530, 2025: 25.

## P3 control detail (the check `liq_fade_i1`'s own forensics left open)

`liq_fade_i1`'s forensics (THESIS 49.5, item 9) flagged an open item: a generic long-bias-on-high-volatility-days drift could produce the same inversion signature as genuine crash-timing, and the discriminating control was never run on that universe. `liq_fade_r1` pre-registered and ran it, and this section independently re-derives it from the frozen panel (not read back from `probes.json`) as a verification pass.

- Primary (crash condition, `z_ret ≤ −3.5 AND z_vol ≥ 3.5`): **1892 events**, net SR **-0.0476**

- Control (vol-only, `z_vol ≥ 3.5`, crash condition removed): **18778 events**, net SR **-0.5323**

- Separation (primary − control): **+0.4848**

Recomputation matches `probes.json` exactly (primary, control, and both event counts reproduced to floating-point precision). What this establishes and what it does not: the crash condition beats vol-only exposure by +0.485 SR, so the crash timing is not simply relabeled high-volatility drift — **but both numbers are negative**, and the primary (−0.048) sits below the 1.0 floor the confounded label requires. Per the pre-registered scope rule, this makes the result plain NEGATIVE rather than NEGATIVE-confounded: the separation is informative about the mechanism (crash timing ≠ vol drift) but is not itself evidence of a profitable effect, since it separates two losing strategies rather than lifting a winning one clear of a confound.

## Liquidity gradient (new analysis)

304 band symbols split by whether they were ever a `liq_fade_i1` top-50 member in some OTHER PIT month: **188 "near-top50"** symbols (rotate in and out of the top-50 across the 5-year PIT history) vs **116 "never-top50"** symbols (never top-50 at any point).

- Near-top50: 1678 events, mean fwd ret **+0.4936%** (se 0.3884%, t=1.27). Top single-symbol contributor: **MANAUSDT**, 51% of the partition's total pp-sum; excluding it, mean = +0.2450% (t=0.65) over 1653 events.

- Never-top50: 206 events, mean fwd ret **-7.8419%** (se 2.0812%, t=-3.77). Top single-symbol contributor: **FTTUSDT**, 78% of the partition's total pp-sum; excluding it, mean = -1.9799% (t=-2.18) over 179 events.

The headline never-top50 number (**-7.84%**) is substantially a single-symbol artifact: **FTTUSDT** — the FTX exchange token, which collapsed to near-zero in November 2022 and never recovered — alone accounts for 78% of the partition's total loss from just 27 events. "Fading" a cascade in a token headed to a permanent delisting is a fundamentally different bet than fading a liquidity-driven overreaction, and this single collapse should not be read as representative of the never-top50 population. Excluding it, the partition's mean shrinks roughly fourfold (to -1.98%) but remains negative and nominally significant at conventional levels (t=-2.18).

The near-top50 partition, by contrast, shows a small **positive** point estimate (+0.49%), though it does not clear conventional significance (t=1.27) and is itself moderately concentrated (one symbol, MANAUSDT, contributes 51% of the total; excluding it the mean is smaller but still positive, +0.24%).

**Honest reading**: there is a directional split consistent with a liquidity gradient — proximity to the top-50 tilts positive, distance from it tilts negative — but neither side is a statistically robust, broad-based finding once single-symbol concentration is accounted for. This sharpens the section-49 story modestly (the effect does not invert sign as cleanly as "both partitions negative" would suggest, and there is a real, order-of-magnitude decay from i1's own +2.77% down toward the near-top50 group's small positive tilt) without licensing a claim that the underlying effect is real and merely attenuated by liquidity — the pooled, whole-band result (Power, above) remains a statistically indistinguishable-from-zero null that fails the pre-registered gate on its own terms.

## Per-symbol distribution

219 of 304 band symbols registered at least one event. **110/219 (50.2%)** have a positive mean forward event return — essentially a coin flip, not a lopsided majority in either direction. That is itself informative and consistent with the Power section's finding above: the aggregate negative mean does **not** come from most symbols individually leaning negative (which would show as a small minority positive, well under 50%). It comes from the *magnitude* of losses among the losing names exceeding the magnitude of gains among the winning ones — a fat left tail sitting on top of an otherwise roughly symmetric distribution, which is exactly what the worst/best tables below show.

Worst 5 by mean forward return:

- FTTUSDT: -46.7043% (27 events)
- BANUSDT: -28.2157% (2 events)
- 1000SATSUSDT: -26.2526% (1 events)
- RAYUSDT: -24.4746% (4 events)
- PERPUSDT: -15.7494% (8 events)

Best 5 by mean forward return:

- NEARUSDT: +65.9437% (1 events)
- SSVUSDT: +26.3595% (1 events)
- KEEPUSDT: +19.5964% (2 events)
- TAOUSDT: +18.4672% (4 events)
- MANAUSDT: +16.9328% (25 events)

The worst name is FTTUSDT at −46.7% mean forward return (27 events) — the FTX token collapse discussed in the liquidity-gradient section above — an order of magnitude larger in magnitude than any other name in either tail. This is the single-symbol tail-risk mechanism that drags the pooled mean negative despite an even sign split: a small number of names undergoing a genuine, permanent collapse (not a liquidity-driven overreaction that mean-reverts) generate losses large enough to outweigh many smaller, roughly-offsetting gains and losses elsewhere in the band.

## Horizon check

- H=1h: mean gross forward return **-0.0840%** (t=-0.88, 1892 events with a full forward window)
- H=6h: mean gross forward return **-0.3612%** (t=-1.82, 1891 events with a full forward window)
- H=24h: mean gross forward return **-0.4478%** (t=-1.27, 1886 events with a full forward window)
- H=48h: mean gross forward return **-0.4178%** (t=-1.00, 1884 events with a full forward window)

All four horizons are negative (confirmed), though none individually clears conventional significance (all |t| < 2). The failure is not an artifact of the H=48 choice specifically — shortening the hold to 1h, 6h, or 24h does not turn the crash-fade gross return positive at any horizon tested; there is no shorter exit that would have rescued the primary config.

## Contrast: liq_fade_i1 vs liq_fade_r1 (thr=3.5, H=48)

| | liq_fade_i1 (§49) | liq_fade_r1 |
|---|---|---|
| Universe | top-50 PIT monthly (799-symbol survivorship-safe store) | monthly PIT ranks 51-150 band (304 symbols) |
| Cost (bps/side) | 10 | 20 |
| Events (masked, full window) | 710 (710) | 1892 (1884) |
| Symbols active | 88 | 219 |
| Gross return / event | +2.772% | -0.418% |
| Net SR (primary config) | +1.305 | -0.048 |
| Gate outcome | 2/3 -- DSR 0.479 < 0.9 (0.881 at own n_trials=6); NEGATIVE, DSR-bound | primary SR -0.048 below the 1.0 floor; confounded label not applicable |

## Sections skipped (named per the anti-silent-omission rule)

The plan's Task 8 template lists eleven forensic sections (F1-F11) written for a PASS or a DSR-bound gate-failure outcome. Six sections above cover what this NEGATIVE-at-probe outcome calls for (power, P3 control detail, liquidity gradient, per-symbol distribution, horizon check, i1-vs-r1 contrast). The remaining six are skipped, not silently omitted:

- **F1_inversion**: no gated result to invert -- P2 already failed gross, before any gate
- **F3_yearly_stability**: no realized net-return series exists (Task 7 skipped); power section's events-per-year table covers the adjacent question from raw trigger data alone
- **F5_dsr_decomposition**: no gate was evaluated (Task 7 skipped, no results.json, no ledger row) -- nothing to deflate
- **F6_cost_curve**: signal loses gross before any cost bps is applied -- cost sensitivity cannot rescue or further sink that verdict
- **F7_p2_reconciliation**: no realized, compounded portfolio series exists to reconcile against the P2 event-study mean
- **F8_placebo_audit**: no placebo was run -- P3 failure routes straight to write-up per gates.json's pass_rule, so there is no p-value to re-derive

## Verdict

`liq_fade_r1` closes as plain **NEGATIVE**, decided at probes P2/P3 before any gate (G1-G3) was ever evaluated. The universe move (top-50 → ranks 51-150, same frozen signal and holding rule) does not merely shrink the section-49 effect — the point estimate flips sign (+2.77%/event on the original universe vs -0.418%/event on the band). That said, the pooled per-event negative is not itself statistically distinguishable from zero at conventional levels (Power section, t≈−1.0) — the honest characterization is a **well-powered null**, not a confidently-signed harm, and it fails the pre-registered P2 floor (which requires the mean to clear +25bp, a bar a null result also fails) rather than because the band actively punishes crash-fading. The per-symbol distribution shows a roughly even sign split (50.2% positive) with the pooled negative driven by a small number of fat-tailed losers (worst: FTTUSDT −46.7%, the FTX collapse), not a broad-based majority-negative pattern. The liquidity-gradient partition shows a directional split consistent with a gradient — near-top50 symbols tilt positive (+0.49%, not significant), never-top50 symbols tilt negative (−7.84%, but 78% of that is one symbol's permanent collapse; ex-that-symbol the negative shrinks to −1.98%) — real but partial and not robust enough on its own to overturn the pooled null. Every horizon tested (1h/6h/24h/48h) has a negative point estimate, none individually significant, so H=48 was not an unlucky choice of hold. No trial-ledger row exists for this experiment and the declared n_trials=1 amendment was registered but never exercised, since the gates were never reached. The holdout (2025-04-01 onward) remains sealed and unspent.

