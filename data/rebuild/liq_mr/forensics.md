# liq_mr_t1 forensic verification — dev-gate NEGATIVE (2026-07-28)

Verdict: **NEGATIVE VERIFIED**. 0/6 configs pass the pre-registered dev gate
(`data/rebuild/gates.json["liq_mr_t1"]`, registered 7856d17 before any run).
Best net SR −0.119 (thr=2.5, H=1) vs floor +1.0; worse-of-families placebo
p ≥ 0.136 everywhere; DSR ≤ 0.003 at ledger n_trials=93.

## Pre-run data-validity probe (spec-mandated)

Stamp-convention contemporaneity probe (BTC/ETH, thr=2.5 events, dev window):
mean |return| on event day 6.5%/7.6% vs next day 3.0%/5.0% vs baseline
2.2%/2.9%. Liquidation spikes are contemporaneous with same-day moves, not
next-day — confirms Coinglass 1d rows are stamped at UTC day open and the
day-t aggregate is complete at close t. Decision close t → weights bar t+1 is
causal. PASS (run before the grid; result trusted).

## Probes on the negative

**P1 — honest denominators / signal density.** All 8 coins: z live on
1492/1551 dev days, first signal 2021-03-01 — exactly the registered 90d/60
warmup from the 2020-12-23 liquidation-history start. No silent data holes;
the negative is measured on the full registered window.

**P2 — inversion kill test.** Negated weights (momentum-follow instead of
fade): thr=2.5 H=1 real −0.119 vs inverted −0.835 — the fade side is the
better direction at 1 day, so a weak reversal effect exists but is far below
the floor. H=5: real −0.764 vs inverted +0.150 — at 5 days the direction
content is momentum-side (cascade continuation), the fade is fighting it.
Engine transmits direction; the negative is signal-level, not plumbing.

**P3 — drag decomposition (best config thr=2.5 H=1).** Gross price-leg SR
+0.359 → after 10 bps/side costs +0.166 → after rf on full capital −0.119.
Unlike carry_xs_t1 (gross 1.005 killed by drag), the raw effect here is only
~1/3 of the gate floor even before any cost — intrinsically weak signal, not
a cost/rf artifact.

**P4 — event validity.** All five benchmark cascade dates flagged at thr=2.5
(2021-05-19, 2022-06-13, 2022-11-09 FTX, 2024-08-05, 2025-02-03). Event
counts 349L/393S (thr=2.5) and 722L/789S (thr=1.5) — well-powered (§44
lesson: ≥30 events needed; we have hundreds). "Underpowered" label does NOT
apply; this is a genuine no-signal result.

**P5 — placebo machinery.** Planted-reversal kill test in the unit suite:
synthetic next-day rebound survives both placebo families (real SR >
95th percentile of both), pure noise does not. p-values on real data
(0.136–0.824) are mid-distribution — real weights are statistically
indistinguishable from calendar-shifted weights.

**P6 — per-coin long-fade decomposition (thr=2.5, H=1, costs, no rf).**
7/8 coins positive but small: DOGE +0.66, BNB +0.52, SOL +0.45, BTC +0.42,
ADA +0.29, XRP +0.27, ETH +0.03, TRX −0.17. Broad but shallow — no single
coin drives or hides the result.

## Mechanism reading (diagnostics, non-gating)

- Post-event signed fade profile (thr=2.5, gross): +25 bp at 1 day, −29 bp at
  3 days, −91 bp at 5 days. The exploitable reversal, if any, completes
  within the event day itself (the probe shows a 6.5% same-day move); at
  daily granularity only a faint next-day echo remains, and beyond one day
  cascades **continue** rather than revert.
- Direction asymmetry: long-fade (buy after long-liquidation cascades) is the
  entire weak edge (+0.19..+0.55 net SR alone); short-fade (short after
  short-liquidation squeezes) loses consistently (−0.68..−1.41) — squeeze
  continuation. Both directions were frozen at registration; no post-hoc
  long-only variant is claimed (that would be exactly the selection the house
  methodology forbids). Recorded as a mechanism observation only.
- Event-day vol percentile ≈ 0.51–0.52 → events are not merely a high-vol
  regime proxy (§43 mechanism absent).

## Conclusion

The liquidation-cascade fade hypothesis fails at daily frequency on the 8
majors: the reversal is intraday, the daily residue is ~1/3 of the gate floor
gross and negative net, and multi-day holds fight continuation. Holdout
stays sealed. Any revival would need intraday bars (lead #4, currently
disk-blocked) — recorded as the natural follow-on, not as a promise.
