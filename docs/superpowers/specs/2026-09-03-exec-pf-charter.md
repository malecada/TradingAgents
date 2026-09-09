# exec_pf — Passive-execution model and re-pricing of the hourly stratum (registered 2026-09-03)

Status: **REGISTERED pre-result.** Gates key `exec_pf` in `data/rebuild/gates.json`
is written in the same commit as this file, before any Vision 1-minute, aggTrades
or fill-model number exists. Source charter: `master_thesis/LEADS_SCOPE_2026-09-02.md`
Lead 2; audit basis: `AUDIT_RESEARCH_PROGRAM_2026-09-02.md` §6 item 2
("hourly stratum is cost-bound, not signal-bound"). Holdout class **H3 dev-only**:
no holdout claim this cycle; the sealed 2025-04-01 → 2026-07-01 window is not
loaded (loaders clip at 2025-03-31 23:00; the liq_fade H1 window is in any case
SPENT by combo_c1, §76).

## Goal (falsifiable)

Two closed hourly signals whose only binding kill was taker cost are re-priced
under a conservative, pre-frozen maker-fill model built from free Binance
Vision data. A signal is revived as a *candidate* (not a strategy) only if it
clears the house net-SR floor under the passive model with a realistic fill
rate, re-passes its parent placebos, and survives cost-stress and the
convention swap. Null: passive execution does not lift either signal above the
floor, or does so only with an unrealistic fill rate.

## Signals re-priced (frozen from parents; NO re-tuning)

| id | signal | frozen config | parent | parent net SR (taker) |
|---|---|---|---|---:|
| R1-BTC | 1h long/flat sign filter on stored `logit_lags5` P(up) | thresh 0.50, smooth 24 (`s3_t0.5_h24`, pp dev best) | §58 predlab_pp S3 (exploratory) | −0.080 (hourly SR, log-return engine, 5 bp) |
| R1-ETH | same rule on the ETHUSDT `logit_lags5` store (2021-12 → 2025-03) | same config, never run by the parent | §58 (config transfer, declared) | none |
| R2 | liq_fade_i1 top-50 long-fade | thr 3.5, H 48, w_per 0.1, cap 1.0, rf 4.5 %/yr full capital | §49 | +1.3047 (daily SR, simple returns, 10 bp) |
| R0 | BTC→alt hourly lead-lag follow | slope −0.0340 (xfam_llg P0) | §72 | arithmetic pre-check only |

Facts recorded at registration: the S3 parent numbers in `pp_dev_results.json`
were produced on the pre-Aug-24 engine (rv_1h `ret` = log returns booked as
PnL; verified 2026-09-03: corr 1.0 with Δlog of the 5-minute store). The
registered taker reference for R1 is therefore **re-derived under simple
returns** by the same rule; the log-engine number is reproduced only as the P2
harness check. R2's parent already books simple returns (lead-0 engine).

**R0 arithmetic pre-check (registered rule):** expected gross next-hour
alt-index move per trigger = |slope| × E[|r_BTC,1h| | top decile], computed
from the dev 1h store; R0 is run only if that exceeds 2 × the maker round
trip (2 × 2.0 bp × 2 sides = 8.0 bp). Registration-time estimate from the 1h
store: q90 of |r| = 0.95 %, top-decile mean 1.64 % ⇒ 5.6 bp expected gross
< 8.0 bp. Unless the probe script (which recomputes this from data) disagrees,
R0 stays closed without a run. Reported at q95 and q99 as sensitivities.

## Data (Vision, free; probed 2026-09-03)

- `futures/um/monthly/klines/{SYM}/1m/` — ≈ 1.5–2.0 MB per symbol-month; header
  row present in newer files, absent in older ones (both handled). Fetched for
  the **88 symbols carrying a dev thr-3.5 trigger** (list frozen in
  `data/xsect/exec_pf_symbols.txt`, produced from the parent detector on the
  parent 1h store, dev window) plus BTCUSDT/ETHUSDT, months 2020-12 → 2025-03
  (only months inside each symbol's 1h coverage; 404 = not listed, recorded).
  Store `data/xsect/klines_1m/{SYM}.parquet` + manifest; loader clips at
  2025-03-31 23:59.
- `futures/um/daily/aggTrades/{SYM}/` — tick prints with `is_buyer_maker`;
  fetched ONLY for the P0 calibration sample (60 symbol-days, below).
- `futures/um/daily/bookDepth/` — **probed: starts 2023-01-01 and carries only
  the ±1 %…±5 % notional bands**, no touch-level quote. It cannot serve as a
  spread or queue proxy; it is NOT used. `bookTicker` is not published on
  Vision for UM futures (404). Deviation from the scoping charter, recorded.
- Tick size per symbol-month is inferred from the 1-minute OHLC prices
  (minimum positive gap between sorted distinct prices in the month) and
  cross-checked against `fapi exchangeInfo` for the last month; a symbol-month
  whose inferred tick disagrees with the neighbouring months by more than a
  factor 10 is flagged in P3.

## Fill model (frozen before any re-pricing)

1. **Order placement.** Every change of the parent's hourly weight path
   ΔW ≠ 0 at the boundary between bar b and bar b+1 (the parent's decision
   time = close of bar b) becomes a passive limit order placed at that close.
   Quote proxy: buy limit L = close_b − ½·spread_b rounded DOWN to the tick;
   sell limit L = close_b + ½·spread_b rounded UP to the tick.
2. **Spread proxy.** spread_b = max(1 tick, s_rel(sym) × close_b). s_rel is a
   per-symbol constant estimated in P0 from the aggTrades sample: per minute,
   median ask-side print (is_buyer_maker = false) minus median bid-side print
   (is_buyer_maker = true), divided by their mid; symbol-day = median over
   minutes with both sides; symbol = median over sampled days; symbols with no
   sampled day take the pooled median over all sampled non-BTC/ETH symbol-days.
   The estimation procedure is frozen here; the numbers are written to
   `data/rebuild/exec_pf/spread_model.json` by the P0 script and never edited.
3. **Latency.** The order is live from minute 1 of bar b+1 (minute 0 is
   excluded — the order cannot be resting during the minute in which it is
   placed).
4. **Fill rule ("trade-through", conservative).** A buy fills iff some
   1-minute low in minutes 1..59 of bar b+1 is ≤ L − 1 tick; a sell fills iff
   some 1-minute high is ≥ L + 1 tick. A touch does not fill. Fill price = L.
   Under price-time priority a print strictly beyond L implies the whole queue
   at L was consumed, so no queue haircut is needed for the through-print
   rule; P0 verifies this against tick prints (a print strictly beyond L, at
   time ≥ placement + 60 s).
5. **PnL booking (exact segment accounting, simple returns).** For a symbol
   whose weight changes from w_old to w_new at boundary b with a fill at L:
   bar b+1 return contribution = w_old·(L/close_b − 1) + w_new·(close_{b+1}/L − 1).
   Unfilled under LTM: w_old·(close_{b+1}/close_b − 1), then a market fill at
   close_{b+1} charged ½·spread_{b+1} + taker fee on |Δw|, and w_new applies
   from bar b+2. Bars without an order use the parent booking
   w·(close_{b+1}/close_b − 1). Adverse selection is therefore *inside* the
   PnL (fill at L, mark at the next close), not an assumed haircut; P1 checks
   its sign on unconditional placements.
6. **Policies (both pre-declared).** **LTM (primary, gated):** limit, then
   market at the end of bar b+1 if unfilled — the parent's intended weight
   path is reached with at most one bar's delay. **LOC (reported):** entries
   and size increases are limit-or-cancel, re-placed at every following
   boundary while the parent still wants the larger position; reductions and
   exits are limit-then-market (a position never lingers past the parent's
   intended exit + 1 bar). **taker:** fill at close_b at the parent's cost —
   the P2 parity mode.
7. **Fees.** Maker 2.0 bp, taker 5.0 bp (VIP0, no BNB discount) on |Δw|;
   parent cost (10 bp R2, 5 bp R1) only in taker/parity mode. rf 4.5 %/yr on
   full capital daily for R2 (parent convention); none for R1 (long/flat,
   parent convention). Daily aggregation of hourly net returns by UTC day;
   SR = mean/sd(ddof 1) × √365 on daily net returns for BOTH signals (house
   convention; R1's parent hourly-SR is reported alongside for parity).
8. **Missing 1-minute data** for an ordered bar ⇒ no fill; LTM market at
   close_{b+1} from the 1h store (parent's fillna(0) return convention kept).

## Blocking probes (in order; each has an abort verdict)

- **P0 fill-model calibration (tick vs 1-minute).** Seeded sample (seed 20260903):
  40 liq_fade entry symbol-days drawn without replacement from the 565 dev
  event symbol-days, + 10 BTCUSDT + 10 ETHUSDT dev days. For every order the
  parent path places on a sampled day (entries and exits, both sides):
  tick-level truth = bid/ask at placement := last bid-side / ask-side print at
  or before the placement time, limit joined there, fill iff a print strictly
  beyond that limit occurs ≥ 60 s after placement within the bar. The
  1-minute rule (spread proxy, item 4) must be *conservative*: its fill rate ≤
  tick-level fill rate + 5 pp on the pooled sample. FAIL ⇒ tighten to a 2-tick
  through requirement and re-check once; second FAIL ⇒ STOP (model not
  trustworthy; nothing re-priced). The spread model (item 2) is estimated on
  the same sample and frozen here. Also reported: mean |L_1m − quote_tick|/mid,
  per-side fill rates, tick-level fill rate with a 0-second latency.
- **P1 adverse-selection sanity (unconditional).** 2,000 seeded random
  (symbol, hour, side) placements on the fetched symbols inside dev; fills by
  the frozen rule; signed 5-minute post-fill drift (buy: close_{m+5}/L − 1;
  sell: −(close_{m+5}/L − 1)) must have mean ≤ 0. If passive fills look
  favourable unconditionally, the model is broken ⇒ STOP. The same drift on the
  R2 event entries is reported as a diagnostic (a fade may legitimately
  differ), not gated.
- **P2 parity.** taker mode reproduces (a) R2's parent daily net series
  element-wise to 1e-9 and SR 1.3047 to 1e-6 (pin
  `data/rebuild/liq_fade/dev_results.json`); (b) R1-BTC's parent hourly SR
  −0.0804 to 1e-6 when fed the parent's log-return series and 5 bp
  (`data/predlab/pp_dev_results.json` S3 `s3_t0.5_h24`; harness check only).
  FAIL ⇒ STOP (harness).
- **P3 data integrity.** For every fetched symbol, the hourly close rebuilt
  from the 1-minute store equals the 1h store's close (|Δ|/close ≤ 1e-6) on
  ≥ 99.5 % of dev bars where both exist; every ordered bar of the real R2/R1
  paths has ≥ 55 of 60 minutes present; inferred tick consistency (above).
  FAIL ⇒ STOP (data); the mismatch list is written either way.

## Gates (per signal, dev-only, ALL required; LTM policy)

1. net SR (daily, √365) ≥ 1.0;
2. fill rate ≥ 60 % — limit-filled |Δw| notional ÷ total ordered |Δw|
   notional over the dev window (LTM market remainders count as unfilled);
3. parent placebos re-pass through the passive overlay: R2 dual family
   (A per-symbol circular trigger shift ≥ 24 bars, B count-matched uniform
   redraw within membership), 500 draws each, seed 48 threaded as in the
   parent, gate on the WORSE family p ≤ 0.05; R1 dual family (A circular
   shift of the probability series, min 30 bars; B 24-hour-block permutation
   of the probability series), 500 draws each, worse p ≤ 0.05;
4. maker 3.0 bp cost-stress keeps the sign of net SR;
5. convention swap: log booking at every PnL step (Δlog in place of simple)
   keeps the sign of net SR; both numbers reported (rail 15, two-sided).

Reported, not gated: LOC policy on every metric; taker reference under simple
returns; fill rate by side and by year; mean adverse-selection cost per fill
(L vs bar-end close); per-year SR; DSR at n_trials = 3 (family) and at the
cumulative ledger count; maxDD; top-name share of pooled gross PnL (R2).

## Multiplicity

Fill model fixed pre-result; one frozen config per signal ⇒ **3 gated rows**
(R1-BTC, R1-ETH, R2) under LTM. Also ledgered and declared non-selectable:
3 LOC rows, 3 taker-reference rows. Family denominator 3 for DSR; cumulative
ledger denominator reported alongside.

## Stop rule

Per signal: any gate FAIL ⇒ closed at the execution layer, recorded as
"real, uneconomic even passive" (R2) or "no edge to price" (R1). No re-tuning
of thresholds, spread, latency or fee; no second fill rule beyond the single
P0-declared tightening. PASS ⇒ stop-and-decide with the user: the R2 holdout
is spent (§76); a passive-execution confirmatory would run on the F window
(2026-07-02 →) after ≥ 6 months' accrual (≥ 2027-01), registered then.

## Decisions (resolved 2026-09-03 on "go ahead with next lead")

(a) LTM primary, LOC reported; (b) maker 2.0 bp; (c) R0 arithmetic pre-check
included; (d) worktree: TradingAgents research trunk (`feature/exec-pf` off
`feature/llm-event-xs`) because the liq_fade engine, the 1h store, the rebuild
ledger and THESIS_FINDINGS live there; the two predlab forecast stores and
rv_1h/BTCUSDT are copied read-only into `data/rebuild/exec_pf/inputs/` with
sha256 stamps. (e) bookDepth dropped (probed unusable) — spread proxy from
aggTrades sample instead, procedure frozen above.

## Mechanics / write-fence

`tradingagents/xsect/fills.py` (+ `tests/test_xsect_fills.py`: trade-through
kill-tests, latency exclusion, rounding direction, segment-booking identity,
taker-parity identity, LOC re-placement, missing-minute handling);
`scripts/fetch_vision_1m.py`, `scripts/fetch_vision_aggtrades.py`
(idempotent, manifest-tracked); `scripts/exec_pf_register.py`,
`scripts/exec_pf_probes.py`, `scripts/exec_pf_run.py`; data under
`data/xsect/klines_1m/`, `data/xsect/aggtrades/`, `data/rebuild/exec_pf/`;
ledger experiment `exec_pf`; THESIS §77. Effort 1–2 weeks; cost $0.

## Amendment (2026-09-03, pre-result, accepted by the user)

Recorded in `gates.json["exec_pf"]["amendments"]`. P3 as registered failed on
technicalities before any P0/P1/re-pricing number existed: two ordered bars
with no 1-minute data are bars absent from the 1h store as well (FILUSDT
2022-04-01 02:00 exchange gap; LUNAUSDT 2022-05-13 16:00 delisting), and the
cross-month tick flags were genuine Binance tick-size changes plus the
minimum-gap inference picking stale finer-grid prints (113 symbol-months).
**A1:** the ≥ 55/60-minute requirement applies to ordered bars where the 1h
store carries a close; bars absent from both stores fall under fill-model
item 8 and are listed. **A2:** tick = modal gap per symbol-month (conservative
direction); cross-month consistency and the exchangeInfo cross-check are
reported, not STOP. Kept as STOP: close agreement ≥ 99.5 % and A1 coverage.

## Status (2026-09-03, executed)

Probes P0–P3 PASS (P3 under amendment A1/A2), R0 closed by arithmetic.
R1-BTC FAIL, R1-ETH FAIL, R2 PASS all gates but LTM +1.265 < taker +1.305
(passive fills condition on continuation). THESIS §77; results in
`data/rebuild/exec_pf/run_{R1_BTC,R1_ETH,R2}.json`, `forensics_R2.json`.
