# nlst — new-listing / low-cap discovery events, multi-venue

Drafted 2026-08-26 BEFORE any results; **user-approved 2026-08-26** with
defaults confirmed (DEX $1k P0 size, 60 pools/quarter sample, holdout
stop-and-decide). Gates key `predlab_nlst` registered at approval, pre-result.

Program context: last unattacked event family ([[predlab-xfam-hunt-negative]],
[[predlab-rviv-p0-negative]]; THESIS_FINDINGS §70-72 = current state, this cycle
targets §73+).

## Goal (falsifiable)

Do newly listed / newly discovered low-cap coins have an exploitable
post-listing return pattern (drift or fade), net of honest venue-specific
costs, on any of: Binance perps, Bybit perps, Uniswap v2 (ETH)?
Both directions pre-named; 0/4 cells is a publishable outcome.

## Data inventory (2026-08-26, pre-registration)

| Source | Events in dev window | Notes |
|---|---|---|
| Binance perp daily (`data/xsect/klines`, 799 sym) | 363 listings | 150 delisted syms present (survivorship-safe); funding starts at listing day (TRUMP/MEW/BIGTIME verified); store ends 2026-07-02 |
| Bybit perp daily (`data/predlab/bybit`, 735 sym) | 445 listings | funding parquets present; ends 2026-07-01 |
| Cross-venue overlap | 79 events | Binance listing in dev window where symbol already on Bybit ≥30d |
| Uniswap v2 via dRPC free (`eth.drpc.org`) | ~100 PairCreated / 5k blocks (Jun-2022 probe) | `eth_getLogs` archive OK, ≤10k-block chunks; Sync events give price AND exact reserves; `baseFeePerGas` per block OK. GeckoTerminal REJECTED (180-day OHLCV cap); publicnode/ankr/1rpc/llamarpc REJECTED (auth/range/dead) |

DEX feasibility pre-gate: **PASSED at inventory** — all three legs (enumeration,
price+depth path, gas model) probed green on the free tier.

## Cells and P0 tests (11 tests total, frozen)

| Cell | Events | P0 tests |
|---|---|---|
| nlst_bin | ~363 | cum funding-adj return, horizons 5d/10d/20d (3) |
| nlst_byb | ~445 | same (3) |
| nlst_x | ~79 | Bybit return after Binance listing, 5d/10d (2) |
| nlst_dex | ~1,020 sampled | net-of-cost return @ $1k, 3d/7d/14d (3) |

**P0 gate (one-shot, per test)**: survivor = BH-FDR q < 0.10 across all 11
tests (two-sided NW p-values). Cell survives if ≥1 of its tests survives.
FAIL ⇒ cell CLOSED, no re-tuning, no window changes, no horizon additions.

## Shared protocol (house rules)

- **Windows**: dev 2021-01-01 → 2025-03-31; last event clipped so the longest
  horizon completes ≤ 2025-03-31. Holdout 2025-04-01 → 2026-07-01,
  CONTAMINATION-DISCLOSED (observed by prior programs, virgin for nlst
  signals). F window 2026-07-02+ untouched.
- **Returns**: simple `pct_change` of closes, NEVER log
  ([[feedback-never-log-returns-as-pnl]]). Convention-swap kill-test mandatory
  on every P1.
- **Listing date = PIT**: entry keys ONLY on information available at entry
  time — first tradeable bar, never announcement date. Announcement run-ups
  reported descriptively only.
- **Listing-date verification (data-quality gate, pre-results)**: 15 random
  events (10 Binance + 5 Bybit) cross-checked against exchange announcement
  pages. >2 mismatches by >1 day ⇒ stop, revisit design BEFORE any P0 run.
- **Funding**: new perp listings often carry extreme negative funding — daily
  funding (sum of 3 settlements) booked into every perp path; longs pay
  positive funding. Funding-vs-price decomposition reported per cell
  (descriptive, regardless of verdict).
- **Concentration (FTT lesson, §50)**: top-1 event |contribution| to pooled
  mean ≤ 50%; every P0/P1 stat reported with and without top event.
- **Stats**: cross-event NW t (events ordered by listing date, lag 5) — proxy
  for calendar-overlap correction; plus binomial sign test (median) reported;
  `year_sign_consistency` reported (2021-2024, 2025Q1 descriptive).
- **Engine/lib**: reuse `scripts/predlab_xfam_lib.py` (`nw_tstat`, `bh_fdr`,
  `ann_sr`, placebos, `ledger_append`); new event-study code in
  `scripts/predlab_nlst_lib.py` + unit tests `tests/predlab/test_nlst_lib.py`
  BEFORE first registered use.
- **Ledger**: every evaluated config = one row, experiment
  `predlab_nlst_<cell>`.
- **Multiplicity**: BH-FDR within P0 (11 tests); any champion claim needs
  DSR > 0.5 with house denominator (all nlst ledger rows + prior program
  trials).
- **Long-run resilience**: DEX fetch idempotent + resumable
  (per-chunk cache under `data/predlab/nlst/dex_raw/`), nohup, ledger =
  recovery map.

## Perp cells (nlst_bin, nlst_byb)

- Event: symbol's first daily bar in store (bar 0, possibly partial day).
- Entry: close of bar 1 (first full day). Horizons: cum funding-adj simple
  return over bars 2..6 (5d), 2..11 (10d), 2..21 (20d).
- Raw returns are the TESTED series (tradeable); BTC-adjusted reported
  descriptively.
- Both hypotheses pre-named: post-listing drift (mean > 0) vs fade
  (mean < 0); two-sided test covers both, direction recorded at P0.

## Cross-venue cell (nlst_x)

- Event: Binance perp listing (dev window) of symbol already trading on Bybit
  ≥ 30 days (79 events).
- Entry: close of Binance-listing day 0 on Bybit bars (listing public
  intraday ⇒ day-0 close is PIT-valid). Horizons: 5d, 10d cum funding-adj
  Bybit return.
- Descriptive only: pre-window −5..0 path (announcement run-up, not
  tradeable).

## DEX cell (nlst_dex) — Uniswap v2, Ethereum

- **Enumeration** (survivorship-complete by construction): factory
  `0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f` PairCreated logs,
  2021-01-01 → 2025-03-31, 10k-block chunks via dRPC free.
- **Sampling (pre-registered, seed=7)**: stratified uniform 60 pairs/quarter
  (17 quarters ⇒ ~1,020) among pairs passing PIT filters:
  - F1: quote side = WETH (USD via own Binance ETHUSDT closes).
  - F2: WETH reserve ≥ 10 ETH at first Sync within 24h of creation.
  - F3: activity — ≥ 20 swaps in first 24h (else untradeable).
  - F4: base token not in pre-named major/derivative exclusion list
    (WBTC, stables, staked-ETH derivatives; frozen in script header).
  - F5 honeypot proxy: ≥ 1 successful sell (token→WETH) before entry time;
    no-sell pools excluded, count reported.
- **Post-entry deaths NOT excluded**: rugs/dead pools ride to horizon; exit
  against last-Sync reserves with exact slippage (≈ −100% when rugged).
  Rug flag (reserve drop > 90%) reported.
- **Entry**: price at first Sync ≥ 24h after pool creation. **Exit**: first
  Sync ≥ horizon end (3d/7d/14d after entry).
- **Cost model (pre-registered, NOT flat bps)**:
  - LP fee 0.30% per side;
  - exact constant-product execution of the full trade notional against
    actual entry/exit reserves ($1k P0, $5k stress);
  - gas: 2 swaps × 150k gas × (block basefee + 2 gwei tip) × ETH/USD at
    trade block;
  - stated limitation: sandwich/MEV extraction not modeled; mitigant =
    2× cost-stress gate at P1. No other slippage fudge factors.
- Both hypotheses pre-named: discovery drift vs post-launch dump; two-sided.

## P1 (per surviving cell — ONE frozen config, no sweeps)

- nlst_bin / nlst_byb: enter close bar 1, hold 10 bars, direction = P0 sign
  (10d test; conflict across surviving horizons ⇒ 10d rules), equal weight
  1/K over max K=10 concurrent events, gross ≤ 1.0, costs 5bp/side ×
  turnover + funding.
- nlst_x: enter close day 0 on Bybit, hold 5 bars, direction = P0 sign,
  same weighting/costs.
- nlst_dex: $1k per sampled event, direction = P0 sign, hold = surviving P0
  horizon (conflict ⇒ 7d), full pre-registered cost model.
- **Promotion gates (house standard, all required)**: dev net SR ≥ 1.0 AND
  circular-shift placebo (≥200 draws) p < 0.10 AND exposure-pattern placebo
  (same symbol, same hold length, random entry ≥ 60d post listing) reported
  and separating AND cost-stress 2× keeps sign AND top-1 event |PnL| share
  ≤ 50% AND convention-swap no verdict flip.

## Holdout rule (STRICTER than xfam)

Any P1 survivor ⇒ **STOP AND DECIDE WITH USER** before any holdout spend or
deployment discussion. No autonomous holdout. One-shot per cell on
2025-04-01 → 2026-07-01 with contamination disclosure; spend script refuses
to run twice.

## Stop rules

- Per-cell P0 FAIL ⇒ cell CLOSED this program; revival needs a new registered
  cycle with a new mechanism argument.
- All four cells fail ⇒ family closes negative; THESIS_FINDINGS §73 records
  the sweep + memory file written either way.
- Descriptive per-year event tables + funding/price decomposition written
  regardless of verdict (thesis content).

## Mechanics

Branch `research/prediction-lab` (worktree TradingAgents-predlab). Scripts
`scripts/predlab_nlst_lib.py` + `scripts/predlab_nlst_{bin,byb,x,dex}.py`;
tests `tests/predlab/test_nlst_lib.py`; outputs `data/predlab/nlst/`; gates
key `predlab_nlst` (registered on approval, before any results); ledger rows
per config. Read-only externals: 1h store + any main-worktree stores; dRPC
free endpoint (rate-limited, chunked, cached).

## Approved decisions (2026-08-26)

1. DEX P0 trade size $1k (capacity deliberately tiny).
2. DEX sample 60 pools/quarter (~1,020; est. 6-12h nohup fetch on free RPC).
3. Holdout stop-and-decide checkpoint confirmed as written.
