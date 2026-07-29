# liq_fade_i1 forensic verification — dev-gate NEGATIVE, DSR-bound (2026-07-29)

Verdict: **NEGATIVE at dev gate, 2/3** (`data/rebuild/gates.json["liq_fade_i1"]`,
registered 2026-07-28 before any run). Best config thr=3.5 H=48: net SR
+1.305 (≥1.0 PASS), dual-family placebo p=0.002 both families (≤0.05 PASS —
the minimum possible with 500 draws), DSR 0.479 at ledger-cumulative
n_trials=100 (<0.9 FAIL). Unlike every prior post-rebuild lead (§45-§47, all
0/6 with placebo p in the 0.14-0.82 range), this is the **first genuine
timing signal** to survive the dual-family placebo — the failure mode here is
multiplicity/effect-size, not absence of effect. Holdout stays sealed and
unspent. All numbers below reproduced with `scripts/liq_fade_forensics.py`
(read-only re-derivation from the registered engine, `tradingagents/xsect/
liq_fade.py`, and loaders in `scripts/liq_fade_dev.py` — no registered script
modified). Full grid: `data/rebuild/liq_fade/dev_results.json`. Machine-
readable forensics output: `data/rebuild/liq_fade/forensics.json`.

**Recomputation sanity check.** The forensics script independently reloads
the 1h panel and recomputes the best-config engine path from scratch: net
SR = 1.3047 (dev_results.json: 1.3047415) and sr_stress_20bps = 1.2290
(dev_results.json: 1.2290419) — exact match to 4 decimal places. The
forensic numbers below are not vulnerable to a stale/edited copy of the
engine.

## F1 — Inversion test (sign sanity)

Best config, same 710 trigger events, weights negated (short instead of
long-fade), same costs/rf: **long-fade SR +1.305 vs short-inverted SR
−1.795**. The registered direction beats its inversion by 3.1 SR — far
stronger separation than §47's liq_mr_t1 H=1 case (−0.119 vs −0.835, a
~0.7 gap). Sign matters cleanly here; the engine is not transmitting noise
that happens to net positive under either direction.

## F2 — Per-symbol concentration (best config, gross P&L, pre-cost)

710 events across 88 symbols with any trigger; 85 symbols carry nonzero
gross P&L. HHI (Herfindahl over each symbol's share of total gross P&L) =
**0.099** — for reference, an evenly-split contribution across 85 symbols
gives HHI ≈ 0.012 and a 10-symbol-only book gives HHI = 0.10, so the
realized concentration is roughly "as broad as 10 equal contributors," not
one or two dominant names. Top-5 share of total gross P&L = **45.2%**:

| rank | symbol | gross P&L | share |
|------|--------|-----------|-------|
| 1 | DOGEUSDT | 0.289 | 17.0% |
| 2 | BCHUSDT | 0.135 | 7.9% |
| 3 | 1000PEPEUSDT | 0.123 | 7.2% |
| 4 | SANDUSDT | 0.118 | 6.9% |
| 5 | 1000SHIBUSDT | 0.105 | 6.2% |
| 6 | DOTUSDT | 0.095 | 5.6% |
| 7 | CRVUSDT | 0.083 | 4.9% |
| 8 | XRPUSDT | 0.082 | 4.8% |
| 9 | FTMUSDT | 0.081 | 4.8% |
| 10 | KSMUSDT | 0.074 | 4.4% |

Three of the top five are meme/high-beta retail names (DOGE, PEPE, SHIB —
30.4% of total gross P&L combined), consistent with the mechanism
(forced-liquidation cascades are more violent in thin, high-leverage retail
books) rather than an artifact of one anomalous symbol. No single symbol
exceeds 17% — the result is not a DOGE-only or memecoin-only fluke, but the
top-heavy tilt toward meme names is a real feature of the edge, not
incidental.

## F3 — Yearly net SR stability (best config)

| year | net SR | n days | mean daily net |
|------|--------|--------|------------------|
| 2021 | +2.663 | 365 | +0.00408 |
| 2022 | −0.347 | 365 | −0.00046 |
| 2023 | +1.307 | 365 | +0.00147 |
| 2024 | +2.353 | 366 | +0.00251 |
| 2025 (Q1 only, 90d) | −0.203 | 90 | −0.00019 |

3 of 5 calendar periods strongly positive (2021, 2023, 2024), one roughly
flat-negative in the 2022 bear/FTX year, and a small negative in the
partial 2025 Q1 slice (only 16 events — see F4, thin sample). Not a
single-regime artifact: the effect survives across a bull year (2021), a
bear year (2023 recovery), and a strong 2024 bull run. 2022 (crypto's worst
drawdown year, including FTX) is the weakest period, plausibly because
liquidation cascades during a structural deleveraging regime behave
differently than cascades during range-bound or trending markets — recorded
as a mechanism observation, not further tested (would be post-hoc).

## F4 — Event-count honesty (best config, thr=3.5)

| year | n events |
|------|----------|
| 2021 | 206 |
| 2022 | 130 |
| 2023 | 181 |
| 2024 | 177 |
| 2025 (Q1 only) | 16 |
| **total** | **710** |

All full calendar years clear the ≥30-events/config bar comfortably
(130-206/year); only the partial 2025 Q1 slice (3 months) is thin at 16,
consistent pro-rata with the full-year rate (~130-180/yr → ~35-45/quarter
expected, 16 observed — event rate itself was lower in Q1 2025, a quieter
period for the majors). The registered 710-event/4.25-year total is not
concentrated in a single year; no year is silently driving the aggregate
count.

## F5 — DSR sensitivity: multiplicity burden vs intrinsic signal (diagnostic only)

Same recomputed daily net-return series (`cand`, from F0), same variance-of-SR
and per-bar SR — only `n_trials` (which sets the expected-max-SR-under-null
term) changes:

| n_trials | expected max SR under null | DSR | passes 0.9 floor? |
|----------|------------------------------|-----|--------------------|
| 6 (this experiment alone — the 6-config grid) | lower | **0.881** | no, but 0.019 short |
| 100 (ledger-cumulative, registered) | higher | **0.479** (matches dev_results.json exactly) | no |

At the scale of this experiment alone, DSR would very nearly clear the 0.9
bar (0.881 — 2 percentage points short). The registered gate correctly uses
the ledger-cumulative count (100 unique configs tried across all
post-rebuild leads to date, per the house pre-registration methodology —
every prior grid's trials count against every later one), and at that
honest denominator DSR collapses to 0.479. **This is not a reason to
override the gate** — the house standard is deliberately punitive about
multiplicity because that is exactly the mechanism that makes uncorrected
backtests unreliable, and relaxing it here for "the first one that looks
real" would be the same post-hoc rationalization the methodology exists to
prevent. It is, however, the most direct evidence the experiment has
produced that the failure here is a **multiplicity/power problem**, not an
**absence-of-effect problem**: an in-sample SR of +1.3 with p=0.002 placebo
separation is a genuinely unusual result for this pipeline (§45-§47 never
got closer than p=0.136), and the DSR verdict would flip on n_trials alone,
holding the signal fixed.

## F6 — Cost sensitivity (best config)

| cost (bps/side) | net SR |
|-------------------|--------|
| 10 (registered) | +1.305 |
| 20 (registered stress row) | +1.229 |
| 30 (new, this pass) | +1.153 |

Roughly linear decay, ~0.08 SR per +10bps. Low sensitivity is consistent
with the config's low turnover (H=48 hold, thr=3.5 selects only 710 events
vs 5064 at thr=2.5; mean_gross_turnover 0.0023/bar). Even at 3x the
registered cost assumption the SR would still clear the 1.0 floor — the
result is not a cost-fragile artifact the way carry_xs_t1 (§46) was.

## F7 — P2-vs-grid order-of-magnitude reconciliation

Probe P2 measured mean GROSS forward return of +2.77%/event (t+1..t+H,
uncapped, no netting, no costs) for thr=3.5/H=48. A naive linear
extrapolation — 710 events × 2.77% × w_per (0.10 notional/event) — gives an
undiscounted sum of **+196.8%**. The realized portfolio's actual compounded
gross cumulative return over the 4.24-year dev window is **+311.7%**
(compounded net of costs: +261.5%). The realized figure exceeds the naive
linear extrapolation, which is expected and NOT a red flag: (a) compounding
over 4.24 years pushes a sum of period returns above the linear total, and
(b) the portfolio can hold up to 10 concurrent 10%-notional slots (cap=1.0),
so overlapping cascades compound gains from concurrent positions that the
per-event P2 average — which measures each event in isolation — does not
capture. Both numbers land in the same order of magnitude (a factor of
~1.6x apart, not 10x or 100x), which is the check this forensic step is
for: the grid result is not decoupled from the P2 event-study number that
justified running the grid in the first place.

## Conclusion

The liquidation-cascade intraday fade hypothesis clears net SR and placebo
at dev gate (best config +1.305 SR, p=0.002 both placebo families — the
strongest placebo separation any post-rebuild lead has produced) but fails
the DSR multiplicity gate (0.479 < 0.9 at n_trials=100) by a wide margin at
the honest ledger-cumulative trial count, even though the same signal would
narrowly pass DSR (0.881) if evaluated in isolation (n_trials=6). The
inversion test (F1), concentration check (F2), yearly stability (F3), and
event-count table (F4) all rule out plumbing bugs, single-symbol artifacts,
single-regime luck, and underpowered sampling as alternative explanations
for the SR — this reads as a real, broad, temporally-stable timing effect
that the house's multiplicity discipline correctly refuses to certify on
100 prior trials of runway. Holdout stays sealed; the correct next step is
a fresh pre-registered replication (new data window or new instrument
family) as its OWN experiment with its OWN trial count, not a holdout spend
on this one.

## Addendum (2026-07-29): placebo kill-test, vol percentile, per-symbol SR

Reviewer follow-up per the §47 P5/P6 pattern, run to completion synchronously
(not backgrounded) via the extended `scripts/liq_fade_forensics.py`; verdict
and gate unchanged. Best config (thr=3.5, H=48) throughout.

### F8 — Placebo machinery: distribution sanity + planted-uplift kill-test

**F8a (distribution sanity).** An independent, ad-hoc re-derivation of the
placebo SR distribution (150 draws/family, fresh RNG streams distinct from
the registered 500-draw run) — not a re-citation of the ledger's p=0.002:

| family | mean | sd | q05 | q50 | q95 | q99 | max |
|--------|------|----|----|----|----|-----|-----|
| shift (A) | −0.174 | 0.445 | −0.856 | −0.205 | 0.565 | 0.917 | 1.046 |
| redraw (B) | −0.091 | 0.410 | −0.689 | −0.076 | 0.542 | 0.807 | 1.105 |

Both distributions are non-degenerate (sd ≈ 0.41-0.45, clearly nonzero) and
centered near/below zero, as expected for placebo trigger sets with no
genuine timing information. **Real SR 1.305 exceeds the maximum of both
150-draw distributions** (1.046 and 1.105) — 0/150 draws in either family
reach the real SR, giving p = 1/151 = 0.0066 (the minimum resolution at this
draw count; consistent with, and independently corroborating, the
registered p=0.002 at 500 draws).

**F8b (positive control — planted uplift at real timing).** +50bp planted at
each of the 710 real trigger events' own entry bar (t+1, the bar the
position first earns): real SR **1.305 → 1.583** (+0.28 SR from the
injection alone). A fresh 150-draw placebo cloud built against this SAME
boosted return series (using placebo-shifted, i.e. **misaligned**, trigger
sets) stays centered near baseline (mean −0.118, essentially unchanged from
F8a's −0.174) — misaligned candidates mostly miss the planted bump. Real SR
vs this cloud: p = 0.0066 (0/150, same floor as F8a). **The mechanism
correctly flags a genuinely-timed planted effect as significant, and stays
significant (does not get diluted) even after admixing extra alpha into the
series.**

**F8c (negative control — same uplift, wrong timing).** The converse check:
the +50bp uplift stays exactly where it was in F8b (i.e. genuinely present
in the data, at the real trigger locations), but the candidate asked to
detect it is deliberately **mistimed** — one fixed circular-shift draw of
the real trigger set (same event count and per-symbol clustering structure,
wrong calendar alignment). This mistimed candidate's own SR against the
boosted series is **−0.234** (vs the aligned F8b reference of +1.583), and
a placebo cloud built by further shifting that SAME mistimed candidate
(150 draws) gives **p = 0.589** (mean −0.161, sd 0.433 — indistinguishable
in shape from F8a's baseline cloud). **A trigger set that is mistimed
relative to a genuine, present effect looks statistically ordinary against
further mistimed draws — the low p-values in F8a/F8b are not an artifact of
"some alpha exists somewhere in this return series"; they require the
candidate's own timing to actually land on it.** This directly answers the
reviewer's concern: the placebo machinery distinguishes **timing**, not
**bookkeeping**.

### F9 — Event-day realized-vol percentile

Per-event percentile of that symbol-day's realized hourly-return volatility
against the pooled all-symbol-day background distribution (all 710 events
scored): **median 0.966, mean 0.915** (IQR 0.881–0.991) — event days sit at
the extreme high end of the volatility distribution, unlike §47's liq_mr_t1
finding (~0.51-0.52, i.e. no regime-proxy signature). **This is expected
and not independently diagnostic here**, for a reason specific to this
detector: unlike §47 (whose liquidation z-score is an independent Coinglass
data source, orthogonal to price-return volatility), `cascade_triggers`
*is itself* defined as `z_ret ≤ −thr AND z_vol ≥ thr` on the same close/
quote-volume series used to compute realized vol — so a triggering bar is
mechanically one of the 24 hourly observations that make up an
elevated-volatility calendar day. A high vol percentile on event days is
close to tautological given the trigger definition, not an independent
finding that the edge is secretly a disguised high-vol-regime exposure. The
relevant test for that concern is F1 (inversion): if the edge were pure
vol-regime exposure (just "hold a high-vol coin"), long and short exposure
to the same events should perform similarly — instead they diverge by 3.1
SR (+1.305 vs −1.795), which is inconsistent with a pure-exposure story and
consistent with genuine reversal timing.

### F10 — Per-symbol SR table (top-15 by event count)

Costs, no rf (isolates the price/cost effect per symbol from the constant
full-capital rf drag — §47 P6 convention), alongside the F2 HHI/gross-P&L-
share table (P&L share was used there because it directly measures
concentration of the *dollar* result driving the aggregate SR; this table
adds the complementary per-symbol *risk-adjusted* view):

| symbol | n events | SR (costs, no rf) | gross P&L share |
|--------|---------:|-------------------:|------------------:|
| DOGEUSDT | 44 | +0.799 | 17.0% |
| XRPUSDT | 38 | +0.803 | 4.8% |
| BNBUSDT | 37 | +0.491 | 3.7% |
| BCHUSDT | 28 | +1.121 | 7.9% |
| ADAUSDT | 27 | +0.437 | 1.9% |
| TRXUSDT | 27 | +0.325 | 1.6% |
| FILUSDT | 26 | +0.025 | 0.3% |
| LTCUSDT | 25 | +0.447 | 2.1% |
| SOLUSDT | 23 | +0.108 | 1.4% |
| LINKUSDT | 23 | +0.485 | 3.1% |
| 1000SHIBUSDT | 22 | +0.679 | 6.2% |
| EOSUSDT | 21 | +0.500 | 2.7% |
| DOTUSDT | 21 | +0.786 | 5.6% |
| BTCUSDT | 18 | +0.187 | 0.8% |
| LUNAUSDT | 16 | **−0.514** | **−14.5%** |

**14/15** of the top event-count symbols are individually SR-positive. The
one exception, LUNAUSDT (16 events, SR −0.514, −14.5% gross P&L share), is
the Terra/Luna collapse (May 2022) — a genuine tail case where "fade the
cascade" is exactly wrong, because the underlying asset went to zero rather
than reverting. This is a useful honest data point, not a hidden problem:
the strategy has real tail risk on true de-pegging/collapse events, and the
aggregate result (+1.305 SR, HHI 0.099, 14/15 symbols positive) already
prices that loss in — LUNA's −14.5% share is fully reflected in the F2
concentration table, not excluded or smoothed over.

### Addendum conclusion

None of the three additional checks changes the verdict. The placebo
machinery is independently confirmed non-degenerate and timing-sensitive
(F8a-c); the high event-day vol percentile (F9) is a mechanical property of
the trigger definition, not new evidence of a disguised regime-exposure
artifact (the inversion test in F1 remains the relevant check, and it
already rules that story out); and the per-symbol SR table (F10) shows
broad positive contribution (14/15) with one honestly-reported tail loss
(LUNA) rather than a hidden concentration problem. Gate verdict (2/3, DSR
FAIL at n_trials=100) and holdout-sealed status are unchanged.
