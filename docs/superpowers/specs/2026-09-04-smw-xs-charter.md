# smw_xs — Smart-money wallet features on perp-listed ERC-20 tokens (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `predlab_smw_xs` in
`data/predlab/gates.json` is written in the same commit as this file, after
the outcome-free dry enumeration (token map, pool list, monthly depth, breadth)
and the fetch-feasibility probe, and before any swap-derived statistic is
joined to a return. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 4.
Parents: nlst3 §75 (DEX smart-money composite, OOS IC +0.136 on day-old pools,
economics FAIL), T7 §55 (cross-sectional IC battery on the monthly PIT top-200
perp universe). Decisions under the user's afk autonomy grant (2026-09-04):
(a) DEX-swap logs only, ERC-20 Transfer logs excluded; (b) breadth floor 40
(dev-window median); (c) run now, concurrently with nlst4 — the machinery is
shared by import, nlst4's wallet ledger is NOT an input (the track record is
computed PIT inside this cycle's own covered universe); (d) quotes WETH / USDC /
USDT on Uniswap v2 and v3 (fee tiers 100 / 500 / 3000 / 10000); (e) wallet
identity = swap recipient, with contract addresses excluded by `eth_getCode`
on every qualification candidate; (f) the CoinGecko symbol → contract mapping
rule below, survivorship caveat disclosed.

## Goal (falsifiable)

Wallet-intelligence features computed point-in-time from Ethereum-mainnet DEX
swap logs for the perp-listed tokens that live on mainnet carry
cross-sectional next-24h / 7-day rank information (T7-style IC) — i.e. the
program's only out-of-sample-positive predictive channel (nlst3 T1: smart
wallets' buying ranks day-old pools) transfers from day-old pools to a liquid,
shortable universe. Null: no composite IC ≥ 0.02 with NW-t ≥ 3 at either
horizon; the nlst3 signal was specific to the first-hours-of-life regime.

## Universe (frozen, outcome-free)

- Monthly PIT top-200 Binance USDT perps by prior-month median quote volume
  (`predlab_t7.monthly_universe`, T7 rule), 799-symbol kline store.
- ∩ tokens mapped to a mainnet ERC-20 contract. Rule (`predlab_smw_map.py`):
  base symbol = perp symbol minus `USDT` and a leading 1000 / 1000000
  multiplier. (1) Binance-spot rule: CoinGecko's Binance spot ticker list
  (fetched 2026-09-04) gives base → coin id; a listed base is mapped iff that
  coin has a `platforms.ethereum` address, and is otherwise unmapped even if
  a same-symbol ERC-20 exists (TON, CFX, DASH collisions found in the dry
  run). (2) Fallback for bases not on Binance spot today (delisted / dead
  tokens): CoinGecko coins with that symbol and an ethereum address — a single
  candidate is taken; among several, the best market-cap rank in the
  top-2500 snapshot of the same day only if that rank ≤ 500; else unmapped. Caveat: the snapshots are 2026-09, so
  dead multi-candidate tokens drop out and bridged wrappers (e.g. Wormhole
  AVAX) can enter — a universe-selection effect, not a signal look-ahead;
  the mapped list with the rule that fired is stored with the registration.
- ∩ pool depth: Uniswap v2 pair and v3 pools (four fee tiers) against WETH,
  USDC, USDT (`predlab_smw_pools.py`); at each month-start block the quote
  balance held by each pool (archive `balanceOf`) × quote price (ETH close of
  the previous UTC day; stables 1) × 2; token in universe for month m iff the
  sum over its pools ≥ $250k (`predlab_smw_depth.py`); stablecoin perps
  (USDC etc.) excluded. Swap logs are fetched for the pools with ≥ $10k of
  that depth (dust pools carry no flow).
- Breadth floor 40 (dev median); the dry enumeration figure is recorded in
  the gates entry. **Pre-registration re-scope (2026-09-04, outcome-free):**
  the scoping charter's $1M depth cut gave a dev median of 30 names (min 15,
  47/51 months below 40) — the abort condition. The cut was lowered to $250k
  (median 48, min 25, 10/51 months below 40) before any swap log was read;
  the $1M subset is kept as declared forensic slice 6 so the original design
  is still reported. Dev window 2021-01-01 → 2025-03-31; evaluation starts on
  the first day with ≥ 100 qualified wallets (burn-in for the track record;
  the date is disclosed, not chosen).

## Data and timing

Uniswap v2 `Swap` and v3 `Swap` logs of every enumerated pool for each month
the token is in the universe, plus a 7-day pre-month lookback (F4 baseline).
Block → UTC time by linear interpolation between cached block headers every
1,000 blocks (≤ 3.4 h span; error seconds). Swap direction from the event
amounts: v2 `amount{0,1}{In,Out}`, v3 signed `amount0/amount1` (positive =
pool received). Per swap: recipient (topics[2]), signed quote amount
(positive = wallet paid quote = bought the token), gross quote amount; USD
via ETH daily close of the same UTC day (stables 1). Daily aggregation to
(token, UTC day, wallet): net_buy_usd, gross_usd. Features for day d use
swaps in [d 00:00, d+1 00:00) UTC, i.e. information through the daily close
of d; in the T7 harness convention (signal row d uses information through
close d−1, target row d = the return over day d) the feature panel is shifted
by one row before scoring — same-day information only, no overlap. Transport: `tradingagents/predlab/rpc_pool.py` (free archive
endpoints, self-checked); every fetch is chunk-cached and resumable.

## Wallet track record (PIT, frozen)

Episode = (wallet, token, day d) with net_buy_usd > 0 while the token is in
the universe; episode return = close[d+7] / close[d] − 1 (perp panel);
completion day = d+7. Record at day t = mean episode return over episodes
with completion day < t; qualified = ≥ 5 completed episodes; smart set at
day t = qualified wallets with record ≥ the 80th percentile of qualified
records at t (daily re-rank, expanding, no fitting). Contract addresses
(non-empty `eth_getCode` at latest) among wallets with ≥ 5 net-buy days are
excluded from every wallet-level quantity (routers, aggregators, bots,
vaults); the 2,000 largest recipients by gross volume are checked as well;
addresses below both thresholds are treated as EOAs undisturbed.

## Features (frozen, four, per token-day; signs fixed at registration)

- F1 smart net-buy share (+): Σ over smart wallets with net_buy_usd > 0 of
  net_buy_usd ÷ Σ over all recipients of gross_usd.
- F2 smart buyer breadth (+): number of distinct smart wallets with
  net_buy_usd > 0.
- F3 smart net-sell share (−): Σ over smart wallets with net_buy_usd < 0 of
  |net_buy_usd| ÷ Σ gross_usd.
- F4 buyer-breadth acceleration (+): log of distinct (non-contract) buyers on
  day d ÷ mean distinct buyers over days d−7 … d−1 (NaN if the mean is 0).
- Composite: equal-weight mean of the pre-signed daily cross-sectional
  z-scores of the available features, requiring ≥ 3 of 4. Days before the
  smart set exists have F1–F3 NaN.

## Protocol (T7 battery, verbatim)

Daily Spearman IC of each feature and the composite versus the next-24h and
the 7-day forward return rank inside the smw universe (min joint breadth 20
per day; `xsec.daily_ic`), Newey–West t on the daily IC series (lag 5 for
24h, lag 10 for 7d), three sub-periods (2021–2022, 2023–2024, 2025Q1),
BH-FDR at q = 0.10 across the 10 tests (4 features × 2 horizons + composite ×
2), every row logged to the trial ledger under `predlab_smw_xs`.

## Gates

- **T1 (existence):** composite mean IC ≥ +0.02 AND NW-t ≥ 3 AND BH-adjusted
  p < 0.05 AND positive mean IC in ≥ 2 of 3 sub-periods, at the 24h or the
  7d horizon (both reported). Per-feature ICs are descriptive.
- FAIL ⇒ family CLOSED for the perp universe (no re-signing, no new features,
  no re-weighting, no universe re-cut).
- **P1 (only on T1 PASS; two pre-declared constructions, both run, DSR at
  n = 2 plus the cumulative program denominator):** (a) long-only composite
  top quintile, equal weight, daily rebalance, versus the equal-weight smw
  basket; (b) quintile long/short. Costs 5 bp per side plus funding
  (`opt_funding_daily`); house gates: net SR ≥ 1.0, dual placebo (time-shift
  and cross-sectional shuffle, 500 draws) p ≤ 0.05, ΔSR versus the basket > 0
  for (a), 2× cost stress keeps the sign, convention swap (simple PnL booked;
  the log-return column disclosed). Then STOP-AND-DECIDE before the holdout.
- **Holdout H2:** 2025-04-01 → 2026-07-01 (price panel observed by prior
  programs; on-chain features virgin). Universe enumeration for H2 months
  happens only after a user decision; one-shot; `assert_dev_window` guards
  every dev evaluation.

## Declared forensics (run regardless of verdict, not gates)

1. Momentum control: partial IC of the composite after cross-sectional
   regression on the token's trailing 7-day and 30-day returns (the smart
   set is selected on past token returns; the control shows whether the
   feature is more than repackaged momentum).
2. Timing canary: composite built from day d+1 swaps versus the d→d+1 target
   (must be large if the engine's alignment were off) and a one-day extra
   lag (decay).
3. Recipient-vs-contract share of gross volume over time and the number of
   excluded contract addresses (how much flow is attributable to wallets).
4. Coverage: breadth of the smw universe and of non-NaN composite per month;
   share of smart-set days per token.
5. Power: IC standard error from the realised breadth and day count; the
   0.02 floor sits at ≈ 6 SE on the dev sample.
6. Depth slice: composite IC restricted to the ≥ $1M-depth names (the
   scoping charter's universe) versus the $250k–$1M band.

## Feasibility probe (pre-registration, outcome-free)

One month (2024-03) of swap logs for the 10 deepest tokens; project calls,
bytes and hours for the full store from the observed per-pool log density and
the pool's throughput; ABORT the cycle if the projection exceeds 20 GB or
10 days of fetch. Result recorded in the gates entry.

## Mechanics

Worktree `TradingAgents-predlab` (branch `research/prediction-lab`), gates
key `predlab_smw_xs`, ledger experiment `predlab_smw_xs`, scripts
`scripts/predlab_smw_{map,pools,depth,fetch,features,p0}.py`, tests
`tests/predlab/test_smw.py`, data `data/predlab/smw/` (raw swap parquet per
pool-chunk, features parquet, results JSON), logs/pids beside the data.
THESIS §82. Effort: fetch background (days), 1–2 days analysis. Cost $0.
Prior: moderate-low, novel; no PIT academic replication known.
