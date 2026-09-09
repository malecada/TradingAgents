# stress_ews2 — Positioning stress index on the full funding history (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `stress_ews2` in `data/rebuild/gates.json`
is written in the same commit as this file, before any composite value on the
extended window exists. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 8;
parent §42 (`stress_ews`, registered 2026-07-14, dev-gate NEGATIVE 0/9,
holdout unspent). §42.7 named this cycle as the "cheap falsification path":
the parent's funding series began 2021-11-01, so the composite was never
evaluated against its own motivating regime (the 2021 leverage tops). The
799-symbol funding store built 2026-07-28 (`data/xsect/funding`, BTC from
2019-09-10, ETH from 2019-11-27, three 8-hour settlements per day) unblocks it.
Decisions taken under the user's afk autonomy grant (2026-09-04): (a) the
9-config grid verbatim — a re-test, not a re-search; (b) dev start 2020-08-01.

## Goal (falsifiable)

The §42 composite, verbatim, detects the registered crash episodes of an
extended dev window that contains the May-2021 and Nov-2021 tops at a hit rate
≥ 0.5 with ≤ 6 false-alarm clusters per year and a block-shuffle placebo
p ≤ 0.05, and a flatten-while-WARN overlay does not worsen EW BTC+ETH
buy-and-hold drawdown or Sharpe beyond the registered tolerances. Null: the
composite is a euphoria detector (§42.5) and stays below every threshold in
the 20 days before each crash even when its target regime is inside the window.

## Protocol (as §42, unchanged except where stated)

- **Components** (per coin, EW BTC+ETH, all inputs `shift(1)`, z365 with
  min_periods 180): `z_fund` = z(funding_rate_ma7), `z_oi` = z(oi_close /
  oi_close.shift(30) − 1), `z_liq` = z(liq_total_usd / oi_close), `z_fg` =
  z(|F&G − 50|) portfolio-level.
- **Funding source (stated change):** `funding_rate` = daily MEAN of the
  store's 8-hour settlements (`data/xsect/funding/{BTCUSDT,ETHUSDT}.parquet`);
  `funding_rate_ma7` = 7-day rolling mean. Probe P0 verifies that this
  reproduces the parent's Coinglass `funding_rate_ma7` on the 2021-11 →
  2025-03 overlap (corr ≥ 0.999). OI, liquidations and F&G come from the
  parent stores (`data/derivatives`, `data/sentiment/fng`) unchanged.
- **Grid (frozen, 9):** component sets {[z_fund, z_oi], [z_fund, z_oi, z_liq],
  [z_fund, z_oi, z_liq, z_fg]} × k ∈ {1.0, 1.5, 2.0}; hysteresis 0.25;
  cooldown 5; detection window 20 days.
- **Episodes:** crash day = 10-day forward log return of the EW BTC+ETH close
  ≤ log(0.85); maximal runs; merge gaps < 10 days; start = first crash day;
  computed on the dev window 2020-08-01 → 2025-03-31.
- **Honest denominator:** an episode counts only if the composite of the
  config under test is non-NaN on every day of its 20-day pre-window (the
  registered "≥ 180 d component history" rule made mechanical); the excluded
  episodes are listed. The OI series starts 2020-02-27, so the first
  detectable date is ≈ 2020-09-24 for every set (all sets contain `z_oi`).
- **Overlay base:** EW BTC+ETH buy-and-hold **simple** daily returns (the
  parent used log; log reported as the convention swap).
- **Placebo:** block-shuffle of the WARN series (geometric blocks, mean 21 d),
  500 draws, seed 0, p = (1 + #{placebo hit rate ≥ real}) / 501.

## Gates (dev-select, ALL required, per config; selection = lowest p, then most negative ΔmaxDD)

hit rate ≥ 0.5; false-alarm clusters ≤ 6/yr; placebo p ≤ 0.05; overlay
ΔmaxDD ≤ 0; overlay ΔSR ≥ −0.10.

## Holdout

2025-04-01 → 2026-07-01 is **H1 virgin** for this index (never spent by §42).
One-shot only on a dev PASS, via a separate script that refuses to run without
`dev_results.json["selected"]` and refuses a second run. Data caveat recorded
now: the derivatives store ends 2026-05-26 and F&G 2026-05-24, so a holdout
evaluation would cover 2025-04-01 → 2026-05-24 unless the stores are extended
first (the extension is a fetch, not a design change).

## Probes (blocking)

- **P0 funding parity:** store-derived `funding_rate_ma7` vs the parent's
  Coinglass series, corr ≥ 0.999 and median ratio within [0.98, 1.02] on the
  overlap; else STOP (data).
- **P1 parent parity:** the extended pipeline restricted to the parent's dev
  window 2021-11-01 → 2025-03-31 with the parent's funding source reproduces
  the parent's 9 hit rates and false-alarm rates exactly and the same
  11-episode catalog; else STOP (harness).
- **P2 target-regime coverage:** the episode catalog on 2020-08-01 →
  2025-03-31 contains ≥ 1 detectable episode starting in 2021-04 → 2021-06 and
  ≥ 1 in 2021-11 → 2022-01; else the cycle cannot test its hypothesis ⇒ STOP
  (scope), recorded as such.

## Multiplicity

9 registered configs, n_trials = 9 (own grid) with cumulative reported. Ledger
experiment `stress_ews2`.

## Stop rule

0/9 PASS ⇒ family closed at the mechanism level ("euphoria detector even on
its target regime"); no threshold, lag, aggregation or window changes. Any
PASS ⇒ holdout one-shot on the selected config, then stop-and-decide.

## Mechanics / write-fence

`tradingagents/stress/index.py::store_funding_components` (+ test),
`scripts/stress_ews2_register.py`, `scripts/stress_ews2_dev.py`,
`data/rebuild/stress_ews2/`, THESIS §78. Effort 1 day; cost $0.

## Amendment A1 (2026-09-04, pre-grid, afk grant)

P0 as registered returned corr 0.969 because the parent store fills
`funding_rate_ma7` with 0.0 on its first six days (2021-11-01..06, fewer than
seven observations); on every other overlap day the store-derived series
equals the parent's to 5e-20 and daily `funding_rate` matches exactly. P0 is
computed on rows where the parent's own 7-day window is complete; the raw
figure is reported. Recorded in `gates.json["stress_ews2"]["amendments"]`
before any extended-window grid number existed.

## Status (2026-09-04, executed): 0/9 FAIL — family closed at the mechanism level. THESIS §78.
