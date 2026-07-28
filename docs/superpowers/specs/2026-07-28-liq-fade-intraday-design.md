# liq_fade_i1 — Intraday Liquidation-Cascade Fade (Lead #4, revival of Lead #6)

**Date:** 2026-07-28
**Registration key:** `liq_fade_i1`
**Branch:** `feature/xs-momentum`
**Thesis section:** §48 (either verdict)
**Status:** DESIGN — pre-registered before any backtest, per house methodology
(trial ledger + gates.json + locked holdout + one-shot).

## 1. Hypothesis

§47 (`liq_mr_t1`) established that liquidation-cascade reversals are an
*intraday* phenomenon: the daily fade shows only a +25bp 1-day echo that decays
and inverts by day 3, with gross SR +0.36 far below the gate floor. The
follow-on hypothesis tested here: **entering the fade within hours of the
cascade — at 1h resolution — captures the reversal that daily bars miss.**

Direction is **long-fade only** (buy after downside cascades). §47 direction
decomposition showed short-fade (shorting squeezes) actively harmful
(per-config SR −0.68..−1.41; squeezes continue) while long-fade was weakly
positive on 7/8 coins. This asymmetry is carried forward as a pre-registered
design choice, not searched over.

## 2. Data

Sub-daily liquidation data is paywalled (Coinglass Hobbyist returns
`401 Upgrade plan` for every interval below 1d on all liq/OI endpoints —
probed 2026-07-28). The strategy therefore uses a **free proxy detector**
built from Binance USD-M futures 1h klines, with the existing *daily*
Coinglass liquidation store used for ground-truth validation only (never as a
live input).

- **1h klines**: Binance UM futures, top-50 universe, from each symbol's
  listing date (REST pagination or Binance Vision bulk zips — implementation
  choice). Columns: open, high, low, close, volume, quote_volume,
  taker_buy_quote_volume. ~150–250MB parquet under `data/xsect/klines_1h/`.
  Disk OK (17G free after 2026-07-28 cleanup).
- **Universe (PIT)**: top-50 by trailing 30d median daily dollar volume,
  re-selected monthly, drawn from the 799-symbol survivorship-safe store
  (§43 infrastructure). Listing dates respected; no symbol enters before it
  has 60d of history.
- **Ground truth (validation only)**: existing daily Coinglass aggregated liq
  parquets (`data/derivatives/*.parquet`, 8 coins).

## 3. Signal (exact, pre-registered)

All rolling statistics: window 2160 hourly bars (90d), `min_periods` 1440
(60d), `ddof=1`, computed per symbol on data ≤ t only.

- `r_t` = 1h log return of close.
- `z_ret_t` = (r_t − rollmean(r)) / rollstd(r)
- `z_vol_t` = (log1p(quote_volume_t) − rollmean(log1p(qv))) / rollstd(log1p(qv))
- **Trigger** (downside cascade proxy): `z_ret_t ≤ −thr AND z_vol_t ≥ thr`.
- **Position**: long the symbol for bars t+1 … t+H (decision at close of the
  completed bar t; position held from bar t+1 — same causal convention as the
  daily engine). Re-trigger during an open hold resets the timer. No shorts.
- **Sizing**: fixed weight 1/10 of capital per active event, total gross
  exposure capped at 1.0 (max 10 concurrent events; excess triggers beyond
  the cap are ignored in arrival order). No vol sizing (§43 lesson).

## 4. Grid (6 configs, all pre-registered)

`thr ∈ {2.5, 3.5}` × `H ∈ {6, 24, 48}` hours. Nothing else is searched.
H range brackets the §47 reversal window (completes intraday to ~1 day;
inverts by day 3 — H=48 is included as the upper edge, H=6 the fast fade).

## 5. P&L and evaluation conventions

- Costs: 10 bps per side on every entry and exit (turnover-based).
- Funding: EXCLUDED (as in `liq_mr_t1` — avoids entanglement with the closed
  carry family).
- rf: flat 4.5%/yr accrued daily on FULL capital (harshest convention, §41
  mandate).
- Portfolio P&L computed on the hourly grid, then **aggregated to daily (UTC)
  returns; SR annualized ×√365** — comparable to the house floor.
- Dev window: 2021-01-01 → 2025-03-31. Holdout 2025-04-01 → 2026-07-01
  remains SEALED and is spent only if the dev gate passes (one-shot).
- Turnover constraint check (Bysik/Ślepaczuk risk): event-driven design is
  sparse by construction; report events/coin/month and total annual turnover
  in dev results.

## 6. Pre-backtest probes (gating; run before any strategy P&L)

- **P0 — stamp convention**: verify 1h kline bars are open-stamped and the
  decision-close-t → hold-t+1 mapping introduces no same-bar leakage
  (spot-check against exchange-documented bar semantics + one manual event).
- **P1 — proxy concordance**: aggregate proxy triggers (thr=2.5) to daily per
  coin on the 8 Coinglass coins; the 5 §47 benchmark cascade dates
  (2021-05-19, 2022-06-13, 2022-11-09, 2024-08-05, 2025-02-03) must be
  flagged on ≥4 of 5 dates by at least one coin. FAIL → STOP, document
  proxy-invalid, holdout untouched.
- **P2 — event-study**: mean cumulative GROSS forward return over bars
  t+1…t+H across all dev-window triggers, per grid cell. If no grid cell
  shows mean per-event return > +25 bps (≈ round-trip cost + margin), STOP:
  intraday reversal absent, record NEGATIVE-at-probe in §48, holdout
  untouched. This is the cheap kill switch.

## 7. Dev gate (all three required; registered in gates.json before runs)

1. Best-config net SR ≥ 1.0 (daily-aggregated, net of costs and rf).
2. Dual-family placebo p ≤ 0.05 in BOTH families, 500 draws each:
   - Family A: per-symbol circular time-shift of the trigger series
     (preserves event clustering and count).
   - Family B: uniform random event timestamps, count-matched per symbol.
3. DSR ≥ 0.9 with `n_trials` = cumulative ledger count at evaluation time
   (grid adds 6 trials to the ledger).

Forensic negative-verification discipline applies to any 0/6 result
(probes, inversion test, direction decomposition, per-coin table — §47
pattern).

## 8. Components

- `tradingagents/xsect/liq_fade.py` — proxy trigger + event bookkeeping +
  hourly P&L (new; the daily xsect engine is not reused since holds are
  sub-daily). TDD.
- `scripts/fetch_xsect_klines_1h.py` — 1h kline fetch, idempotent tail-append
  (pattern of `fetch_xsect_klines.py`; canonical filenames, no dates in names).
- `scripts/liq_fade_dev.py` — probes P0–P2, dev grid, placebos, DSR,
  forensics output under `data/rebuild/liq_fade/`.
- `gates.json` — `liq_fade_i1` entry committed before first dev run.

## 9. Known limitations (declared at registration)

- Proxy ≠ liquidations: volume+return spikes include non-liquidation flow
  (news bars). P1 concordance bounds this only on 8 coins.
- Top-50 monthly re-selection uses trailing volume — PIT-safe but the 799
  store's listing metadata is the survivorship guarantee, not exchange
  delisting reconstructions.
- Binance-only 1h data; cascades on other venues are visible only via the
  Binance price echo.
- 10bps/side may understate taker cost in cascade conditions (slippage);
  a +10bps stress row is reported (not gated).
