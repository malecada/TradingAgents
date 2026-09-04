# liq_fade_v1 — Liquidation-cascade fade, second venue (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `predlab_liq_fade_v1` in
`data/predlab/gates.json` written before any Bybit 1 h bar is evaluated (the
1 h store fetch runs in parallel; fetching is data, not a result). Source:
`master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 5; parents §49 (liq_fade_i1,
dev 2/3 DSR-bound), §50 (rank 51–150 replication FAIL), §76 (sleeve −0.79 on
the sealed Binance window), §77 (passive execution no gain). Decisions under
the afk autonomy grant: (a) Bybit (store + delisting sweep exist); (b) cost
10 bp/side for comparability (Bybit VIP0 taker 5.5 bp reported as a
sensitivity).

## Goal (falsifiable)

The frozen liq_fade_i1 configuration (thr 3.5, H 48, w_per 0.1, cap 1.0,
long-fade only, 10 bp, rf 4.5 %), executed on an independent venue's prices
and universe (Bybit linear USDT perps, monthly top-50 PIT by trailing-30-day
median turnover, 1 h bars), survives its own probe ladder with the vol-drift
control run FIRST and the registered gates. Interpretation boundary (stated
now): venues trade the same market; this is execution/universe robustness
evidence, not an independent statistical sample. Null: the §49 dev result was
a Binance-universe artifact, or a generic long-on-high-volume-hours drift.

## Data

Bybit v5 `market/kline` interval 60, all 735 symbols of the daily store, to
2025-03-31 23:00 (dev cap; `predlab_bybit_fetch_1h.py`); quote volume =
`turnover`. Universe from the Bybit daily store (`data/predlab/bybit/klines`,
turnover), min age 60 days; the delisting-truncation caveat of the daily store
applies (store first bar ≠ launch) — membership uses the store as-is, as the
parent did on Binance. Warm-up from 2020-10-01 (z-window 2,160 bars).

## Probes (blocking, in order)

- **P0 stamp reconciliation:** Bybit 1 h BTC/ETH simple returns vs Binance 1 h
  returns on the overlap, corr > 0.99; else STOP (data).
- **P3 FIRST — vol-drift control:** long-only 1/10 for 48 bars after every
  hour with z_vol ≥ 3.5 and NO crash condition (z_ret > −3.5), same engine and
  costs. Control net SR < 0.5 AND separation (primary − control) ≥ 0.75; else
  the verdict is NEGATIVE-confounded (if the primary ≥ 1.0) or NEGATIVE.
- **P1 detector concordance:** thr 2.5 on the 8 majors flags ≥ 4/5 benchmark
  cascade dates (2021-05-19, 2022-06-13, 2022-11-09, 2024-08-05, 2025-02-03).
- **P2 gross event floor:** mean gross forward return t+1..t+48 over dev
  triggers ≥ +0.25 % with ≥ 300 events; else STOP.

## Gates (dev, H3; one frozen config)

net SR ≥ 1.0; dual-family placebo (A per-symbol circular trigger shift ≥ 24
bars, B count-matched uniform redraw within membership) 500 draws each, worse
p ≤ 0.05; 20 bp cost-stress keeps sign; top-symbol share of pooled gross
|PnL| ≤ 25 %; convention swap (log booking) keeps sign; DSR at confirmatory
n = 1 (frozen config, new venue) with the cumulative ledger denominator
reported. Reported: 5.5 bp venue-actual cost; per-year SR; events per year.

## Holdout

None this cycle (H3). The Binance sealed window is spent for this signal
(§76); any Bybit holdout claim would use the F window (≥ 2027-01), registered
then.

## Stop rule

FAIL on any gate or probe ⇒ "liq_fade does not replicate on Bybit" (or
NEGATIVE-confounded per P3); no re-tuning. PASS ⇒ recorded as venue-robust on
dev only, stop-and-decide.

## Mechanics

Predlab worktree; engine = `tradingagents/xsect/liq_fade.py` of the main
worktree (simple returns; imported by path) + the parent's placebo functions
(`scripts/liq_fade_dev.py`); `scripts/predlab_liq_fade_v1.py` (register /
probes / run); results `data/predlab/liq_fade_v1_*.json`; ledger
`predlab_liq_fade_v1`; THESIS §80 (oflow takes §80 → this cycle takes §87).
Effort 1 day after the fetch; cost $0.
