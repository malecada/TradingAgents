# value_rev — Revenue-based value factor (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `value_rev` in `data/rebuild/gates.json`
is written in the same commit as this file; the first DefiLlama snapshot
(vintage 2026-09-04) is being taken at registration and no ratio, breadth or
return number has been computed. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md`
Lead 6; parent §51 (`value_xs_t1`, activity-ratio value, dev 0/4). Decisions
under the user's afk autonomy grant: (a) revenue included as the second metric
(4 cells); (b) 90-day trailing window.

## Goal (falsifiable)

Coins cheap on market cap per unit of protocol fees (or revenue) outperform
expensive ones cross-sectionally at a weekly cadence, net of costs, and beat
the vol-sorted and reversal-sorted control books. Null: as §51 — the cheap
tercile is the fallen tercile and the reversal control absorbs it.

## Data

- DefiLlama `overview/fees` + `/protocols` (slug → symbol) + per-protocol
  `summary/fees/{slug}?dataType=dailyFees|dailyRevenue`; protocols mapped to
  the perp base `{SYMBOL}USDT` / `1000{SYMBOL}USDT` in the 799-symbol daily
  store, stablecoins and wrapped assets excluded, several protocols per token
  summed. Snapshot 1 = vintage 2026-09-04 (`data/xsect/fees/2026-09-04/`, raw
  responses with sha256 under `data/xsect/fees_raw/2026-09-04/`). At
  registration the mapping covers ≈ 220 perp symbols.
- Market cap: CoinMetrics community `CapMrktCurUSD` (`data/xsect/fundamentals`,
  63 mapped assets) where available, else price × circulating supply is NOT
  used — names without a market-cap series are dropped (breadth reported).
  Prices/returns: 799-symbol daily store, simple returns.

## Probes (blocking, in order)

- **P0 restatement (PIT safety):** a second snapshot ≥ 14 days after the
  first (≥ 2026-09-18); on the common protocol-days ending ≥ 30 days before
  the first snapshot, ≤ 5 % of protocol-days change by > 10 %; else STOP (the
  series is not PIT-safe). Nothing after P0 runs before P0 exists.
- **P1 breadth:** median weekly signal-valid names ≥ 20 on the dev window
  (2021-01-01 → 2025-03-31); else STOP (as §51).
- **P2 publication lag:** the fee series is available with ≤ 2-day lag at the
  snapshot date (last point vs snapshot date); the registered feature lag is
  2 days, widened pre-grid if P2 measures more (logged amendment).

## Grid (frozen, 4 cells) and engine

metric ∈ {mcap / fees_90d, mcap / revenue_90d} × breadth ∈ {tercile, decile};
signal = log ratio, cross-sectional z per rebalance, low ratio = cheap = long;
weekly Monday dollar-neutral L/S, 10 bp/side, realized funding, rf 4.5 %/yr on
full capital once; engine `tradingagents/xsect/value_xs.py` machinery with a
fees/revenue denominator (simple returns). Controls C1 (30-day vol sort) and
C2 (reversal sort) through the identical pipeline; value must beat both
(ΔSR > 0).

## Gates (dev-select, ALL required)

net SR ≥ 1.0; dual-family placebo (A per-symbol circular shift of the signal,
B count-matched random rank re-assignment) 500 draws each, worse p ≤ 0.05;
ΔSR vs C1 > 0 and vs C2 > 0; DSR ≥ 0.9 at n = 4 (own grid) with the
cumulative ledger denominator reported.

## Holdout

2025-04-01 → 2026-07-01 is **H1 virgin** for this signal; one-shot only on a
dev PASS, stop-and-decide.

## Multiplicity / stop rule

4 registered cells, n_trials = 4. 0/4 ⇒ family closed ("value capture does not
price cross-sectionally net of costs"); no metric, window or breadth changes.

## Mechanics

TradingAgents worktree; `scripts/fetch_defillama_fees.py` (snapshot, never
overwrites), `scripts/value_rev_register.py`, `scripts/value_rev_dev.py`
(probes + grid; refuses the grid without a passing P0 file), data under
`data/xsect/fees*`, results `data/rebuild/value_rev/`, ledger `value_rev`,
THESIS §81. Effort 3–4 days spread over the 14-day restatement clock; cost $0.

## Coverage fact recorded at snapshot 1 (2026-09-04, before any P0/P1 number)

Snapshot 1: 220 perp symbols with fee panels (704 raw responses; revenue on
all 220; median first fee date 2024-07-16, 10th percentile 2021-04-22).
Intersection with the CoinMetrics community market-cap set is **24 symbols**
(AAVE, ADA, ALPHA, BAL, BNB, BTC, COMP, CRV, EOS, FLOW, FUN, KNC, LDO, LEND,
LINK, LPT, LTC, PERP, SNX, SUSHI, TRX, UNI, XTZ, YFI). The P1 breadth floor
(median weekly signal-valid ≥ 20) is therefore expected to bind; no
market-cap source is added post hoc (the charter states names without a
market-cap series are dropped). If P1 STOPs on 2026-09-18 the cycle closes as
NEGATIVE-at-probe (data), and a future cycle would need a registered
market-cap source for the ~200 uncovered names.
