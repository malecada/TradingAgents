# Bitcoin version of the B2 screen — what it would take (draft for review)

Status: planning draft, 2026-10-14. Nothing has been captured, built or registered
for Bitcoin. Measurements below come from read-only probes of the public dataset
(one footer read and two single-day reads). Approval of this draft is needed before
a spec, plan or capture.

## 1. Why, and what to expect

The ETH B2 screen (`research/onchain-b2-2026-10-13/`) was negative: 0 of 40
comparisons passed; on-chain activity, exchange/whale flows and motif features
added nothing to price/volume history for next-day or next-week direction, return,
volatility or volume (2019–2024 walk-forward). The paper reports a stronger Bitcoin
result for its own model (76.5 % direction accuracy, Table 2). A Bitcoin run would
(a) cover the paper's second asset and (b) test whether the ETH null generalises.
Prior expectation, given the ETH null and the price-only baselines at chance:
a negative result is the most likely outcome; the value is the answer itself.

## 2. Data — measured

| Item | Finding |
|---|---|
| Source | AWS public blockchain `v1.0/btc/transactions/date=D/` (same bucket as ETH), one parquet part per day, 2017-01 → 2026-10-11 available |
| Day size | 490–620 MB per file; needed columns ≈ 25 % of it |
| Transactions per day | 291k (2017-01-02), 769k (2024-06-03) |
| Inputs | already resolved: each input carries `address` and `value` (no previous-output lookup needed); coinbase inputs are null |
| Outputs | nested list with `address`, `value`; 2024 day: 508k of 1.89M outputs have no address (OP_RETURN / inscription era), 2017 day: 4.5k |
| Values | BTC as float64 (not satoshis) |
| Read time | 30–61 s per day from S3 (column-projected), the dominant cost |
| Projection | proportional input×output rule on 2024-06-03: 3.76M projected rows → 2.87M distinct address pairs, 3 s, peak 2.5 GB (mostly the nested read) |
| Heavy tail | in×out pairs per transaction p99 32–68, max 37k–71k; transactions with > 10k pairs carry 7–14 % of all pairs |
| Exchange labels | Dune Spellbook `cex_bitcoin_addresses`: ≈ 760 addresses (vs 4,961 for ETH); eth-labels has none |
| Prices / volume | Coin Metrics BTC `PriceUSD` (same API); Binance BTCUSDT 1d from 2017-08-17 |

## 3. What changes from the ETH pipeline

Reusable unchanged: periods/windows, market (asset parameter), weekly pair
aggregation, address table, F1 core, role flows, top-K graph, dictionary, MCM,
motif features, transforms, samples, screen, holdout guard, CLI stages.

New or changed:

1. **Day reader `btcsource`** — read `txid, is_coinbase, block_timestamp, fee,
   inputs.{address,value}, outputs.{address,value}`; stream by row group (5 per
   day) to keep the peak under ~1 GB, so three days can download in parallel.
2. **Projection `btcproject`** — the rule already written in Branch A's protocol:
   merge repeated input addresses; edge value `in_i × out_j / Σ in`; fee not
   allocated; change outputs kept (they become self-edges or input→own-address
   edges); coinbase excluded and counted. **Decision needed:** outputs without an
   address — Branch A excluded the whole transaction, which in 2023–24 would drop a
   large share of activity; recommendation: drop only those outputs (almost all are
   zero-value OP_RETURN) and count them.
3. **Counters / F1 differences** — ETH's failed / zero-value / null-recipient shares
   become coinbase share, no-address-output share, mean inputs and outputs per
   transaction, fee median; the rest of F1 is unchanged.
4. **Labels** — Bitcoin addresses are case-sensitive (base58) or lowercase (bech32):
   no lowercasing. Fewer labels make the deposit-like rule matter more; it is
   unchanged.
5. **Asset parameter** — `config/b2.json` gains per-asset sections; artifacts under
   `research_artifacts/onchain-b2-btc/`; a separate registered study directory
   `research/onchain-b2-btc-<date>/` with the same gates, windows and selection rule.
   BTC's 2025–26 window is its own sealed, one-shot holdout.

## 4. Effort and time

| Part | Estimate |
|---|---|
| Engineering (reader, projection, counters, asset parameter, labels, ≈ 25 tests, review) | ≈ 1 working day of agent time |
| Capture, 3,570 days | ≈ 50 h single stream; ≈ 15–20 h with row-group streaming and 3 parallel downloads (memory ≈ 3 × 1 GB + one week build ≤ ≈ 6 GB) |
| Week builds | 2.9M distinct pairs/day → ≈ 15–20M per week; ≈ 4–6 GB peak, 1 builder |
| Dictionary + MCM | ≈ 2 h (same K = 5,000) |
| Features + screen | minutes |
| Disk | ≈ 0.7 GB graphs + MCM; no raw kept |
| **Total wall-clock** | **≈ 2 days**, mostly unattended download |

## 5. Decisions for the user

1. Go / no-go for a Bitcoin B2 run given the ETH null (recommended: go only if the
   thesis needs the second asset or a generality check; otherwise the ETH null plus
   this assessment is a sufficient negative).
2. No-address outputs: drop the outputs (recommended) vs Branch A's whole-transaction
   exclusion.
3. Same windows, targets, feature sets, gates and selection rule as ETH (recommended,
   for comparability) vs a narrowed BTC hypothesis (e.g. only exchange flows and
   volatility, which would also use fewer comparisons).
4. Optional cheaper variant: skip motifs (F2/F3b) — saves only ≈ 2 h; the download
   is the cost, so not recommended.

## 6. Risks

- S3 throughput varies 2–5× between hours; the estimate assumes current speeds.
- 2023–24 inscription traffic inflates transactions and no-address outputs; the
  projection rule decides how much of it enters the graph.
- Sparse exchange labels weaken F3a/F3b; the deposit-like rule partly compensates.
- One-shot holdout: as for ETH, it opens only for a committed, non-empty selection.
