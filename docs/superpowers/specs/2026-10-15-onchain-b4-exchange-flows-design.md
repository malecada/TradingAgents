# Branch B4 — exchange flows, daily (Coin Metrics) and hourly (own chain pass)

Status: design approved in conversation 2026-10-15, written before any B4 data read or
outcome. Branch `research/onchain-replication-b-2026-10-12`. M2 (paper-scale
replication, direction accuracy 0.490), B2 (weekly activity and motifs, 0 of 40) and B3
(whole-graph structure and 20k motifs, 0 of 42) were negative; their shared sealed ETH
window 2025-01-01 → 2026-10-12 was never opened. B4 changes the data layer (stablecoin
transfers, exchange entities), the frequency (hourly) and the source (Coin Metrics
daily metrics), and spends that window at most once.

## 1. Decisions taken with the user (2026-10-15)

1. Stage 1 (daily Coin Metrics metrics) and stage 2 (hourly own exchange flows) run as
   one study: one screen, one committed selection of at most 3, one holdout.
2. Stage 3 (ETH moved inside contracts, `traces`) and graph representation learning
   are out of scope.
3. Exchange entities: the 4,961 B2 labels plus deposit addresses inferred causally by a
   first-send and count-share rule (§4.2). Labels-only flows are computed for
   exploratory comparison but are not a registered feature set.
4. Every day is read from the public S3 dataset (the retained 2022–24 copies lack the
   gas-price column).

## 2. Question

Do exchange flows — ETH and stablecoins moving into and out of exchange entities —
measured daily by Coin Metrics or hourly from the chain, add out-of-sample information
to price/volume history for next-day to next-week ETH direction, return and volatility
(daily), or next 1–24 h return and volatility (hourly)?

Motivating claim (unverified, used only to choose the design): an arXiv study
(2411.06327) reports that hourly ETH exchange net inflows predict lower ETH returns and
volatility and that USDT exchange net inflows predict higher BTC and ETH returns.

## 3. Windows and sealing

Development 2017-10-02 → 2024-12-31; sealed holdout 2025-01-01 → 2026-10-12 (B2
windows). Walk-forward test years 2019–2024, expanding training, purge = target
horizon. A sample enters a target only if that target's whole label window lies inside
its window. All price-derived data after 2024-12-31 — hourly Binance bars, Coin Metrics
metrics (MVRV and the stablecoin ratio depend on price) — is written only to
`research_artifacts/onchain-b4/sealed/` and read only by the holdout command. Chain-only
hourly flows are not sealed (they contain no price).

## 4. Stage 2 — hourly chain pass

### 4.1 Reads per UTC day (2017-01-01 … 2026-10-11, 3,571 days)

| Table | Columns | Admission |
|---|---|---|
| `transactions` | from, to, value, receipt_status, gas_price, receipt_effective_gas_price, block_number, block_timestamp | ETH transfer: status 1, value > 0, to not null, from ≠ to |
| `token_transfers` | token_address, from, to, value, block_number, block_timestamp | token ∈ {USDT `0xdac17f958d2ee523a2206206994597c13d831ec7`, USDC `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`, DAI `0x6b175474e89094c44da98b954eedeac495271d0f`}, value > 0, from ≠ to, neither end the zero address |
| `blocks` | timestamp, gas_used, transaction_count | all |

Token addresses arrive left-padded to 32 bytes and are cut to the last 20. Values:
ETH = wei / 1e18; USDT, USDC = raw / 1e6; DAI = raw / 1e18; the three stablecoins are
summed as USD ("stable"). Addresses are keyed by the first 16 hex digits after `0x` as
uint64 (B3 rule). A day that fails after B2's retry schedule gets an
`.unavailable.json` marker; its 24 hours are missing, and the exchange state continues
without it.

Days are processed strictly in date order (the state of §4.2 is sequential); reads may
be prefetched in parallel threads.

### 4.2 Exchange entities (causal, updated at day boundaries)

- L = the 4,961 labelled exchange addresses (B2 `labels.json`, frozen).
- Seen-sender filter S: a Bloom filter (2³² bits, 5 hashes, B3's multiply-shift) of
  every from-address in admitted transfers already processed (false-positive rate
  ≈ 0.2 % at 3 × 10⁸ senders).
- Candidate table C (sorted uint64 keys, outgoing-transfer count n_out, count to L
  n_L): an address X ∉ L enters C on the day of its first observed outgoing transfer
  if X ∉ S before that day and at least one of X's outgoing transfers in the earliest
  block in which X sends that day goes to L. Once in C, every later outgoing admitted
  transfer of X updates n_out and n_L.
- Deposit set for day d+1: D = {X ∈ C : n_L ≥ 1 and n_L / n_out ≥ 0.9}, computed after
  day d. Exchange set E(d) = L ∪ D(d).

Flows on day d use E(d) only (state before the day): inflow = admitted transfer with
from ∉ E(d), to ∈ E(d); outflow = from ∈ E(d), to ∉ E(d); transfers inside E (sweeps,
gas top-ups) are excluded. A new deposit address's first deposits are counted once, at
sweep time (its sweep to L is a non-E → E transfer); later deposits count at deposit
time.

Labels-only flows (E = L) are computed alongside for exploration.

### 4.3 Hourly raw series (15, plus 10 labels-only)

Per hour h (block timestamp in [h, h + 1 h)):

| Block | Series |
|---|---|
| ETH flows (5) | inflow ETH, outflow ETH, inflow count, outflow count, large-inflow count (≥ 100 ETH) |
| Stable flows (5) | inflow USD, outflow USD, inflow count, outflow count, large-inflow count (≥ $1M) |
| Gas and activity (5) | median paid gas price (receipt_effective_gas_price, else gas_price; all successful transactions), gas used and transaction count (blocks), admitted ETH transfer count, ETH transferred |

The 10 flow series are also computed with E = L (`lab_` prefix, exploration only).
Output: one parquet of 24 rows per day; empty hours are zeros, missing days are absent.

### 4.4 State persistence

Every 30 processed days and at the end: Bloom bits, C and the last processed day are
written atomically (new file, then rename) to `state/`; a restart resumes from the last
snapshot and recomputes later days (outputs are deterministic and overwritten). Peak
memory ≈ 3–4 GB (Bloom 0.5 GiB, C ≤ ≈ 1.3 GB, up to three days in flight); unit cap
6 GiB. Disk: snapshot ≤ ≈ 2 GB, two during a swap ≤ ≈ 4 GB; hourly outputs ≈ 40 MB.
The pass requires ≥ 5 GB free at launch.

### 4.5 Hourly market data

Binance ETHUSDT 1-hour klines from 2017-08-17 (public REST, as B2's daily volume):
close and quote volume per hour; ≤ 2024-12-31 23:00 to `market/hourly_dev.json`,
later to `sealed/`. A missing bar makes every sample that needs it ineligible.

### 4.6 Hourly features

Values x ≥ 0 are taken as log1p(x). For each of the 15 registered series:

- `__h1z`: the hour's value z-scored against the previous 168 hours (minimum 120,
  ddof 0, zero std → 0, clip ±10);
- `__d24z`: log1p of the 24-hour sum ending at h, z-scored against the previous 720
  hourly values of that sum (minimum 480; same rules).

Plus `eth_net24__z` and `stable_net24__z`: log1p(in24) − log1p(out24), z-scored
against the previous 720 hours. Total 32 flow/gas/activity features. A feature uses
data up to the end of hour h only.

H0 price/volume (8): log returns over 1, 4, 24 and 168 h; realised volatility √Σr² of
hourly log returns over 24 and 168 h; log quote volume over 24 h; log(volume 24 h /
(volume 168 h / 7)).

### 4.7 Hourly targets (decision at the end of hour h)

| ID | Definition | Loss | Purge / bootstrap block |
|---|---|---|---|
| R1 | log(c[h+1] / c[h]) | MSE | 1 h / 168 rows |
| R6 | log(c[h+6] / c[h]) | MSE | 6 h / 168 rows |
| R24 | log(c[h+24] / c[h]) | MSE | 24 h / 168 rows |
| V6 | log √Σ r², hourly log returns h+1 … h+6 | MSE | 6 h / 168 rows |
| V24 | log √Σ r², hourly log returns h+1 … h+24 | MSE | 24 h / 168 rows |

### 4.8 Hourly feature sets

| Set | Contents |
|---|---|
| H0 | price/volume (8) |
| HE | H0 + ETH flows (5 × 2) + `eth_net24__z` |
| HS | H0 + stable flows (5 × 2) + `stable_net24__z` |
| HA | H0 + all 32 |

Comparisons: HE vs H0, HS vs H0, HA vs H0 → 5 targets × 2 families × 3 = 30.

## 5. Stage 1 — daily Coin Metrics metrics

### 5.1 Data

Coin Metrics community API, daily, fetched once over 2017-01-01 → 2026-10-12: ETH
`FlowInExNtv`, `FlowOutExNtv`, `SplyExNtv`, `SplyCur`, `CapMVRVCur`, `AdrActCnt`,
`FeeTotNtv`; `SplyCur` for USDT, USDC and DAI (missing early values of USDC/DAI count as
0). Dates ≤ 2024-12-31 go to `market/cm_dev.json`, later dates to `sealed/`. Coin
Metrics revises its exchange history as it adds labels; the fetched history reflects
its current labels (disclosed look-ahead, like the static exchange labels).

### 5.2 Daily raw values (lagged one day: the decision at the end of day d uses day d−1)

| Block | Values |
|---|---|
| Flow (5) | log1p inflow, log1p outflow, (inflow − outflow) / exchange supply, log(exchange supply d / d−7), exchange supply / current supply |
| Other (5) | log MVRV, log active addresses, log fees, log(stable supply d / d−7), log(stable supply USD / (B2 PriceUSD × ETH supply)) |

Each value enters as a 28-day z-score (previous 28 days, minimum 21, ddof 0, zero std
→ 0, clip ±10) and a one-day change: 20 columns.

### 5.3 Daily samples, targets and sets

Decision at the end of day d (B2 convention, B2 F0 price/volume with 7 columns, from
B2's `market/dev.json`).

| ID | Definition | Loss | Purge / block |
|---|---|---|---|
| T1 | 1 if close[d+1] > close[d] | log loss | 1 day / 14 |
| R7 | log(close[d+7] / close[d]) | MSE | 7 days / 28 |
| V7 | log √Σ r², daily log returns d+1 … d+7 | MSE | 7 days / 28 |

Sets: D0 = F0 (7); DF = D0 + flow block (10); DA = D0 + flow + other (20).
Comparisons: DF vs D0, DA vs D0 → 3 targets × 2 families × 2 = 12.

## 6. Screen, selection, holdout

- 42 comparisons (12 daily + 30 hourly), one screen run.
- Models as B3: linear (logistic/ridge, alpha grid {0.1, 1, 10, 100, 1e3, 1e4, 1e5},
  inner validation on the last 365 days or 8,760 hours of training when the training
  window holds ≥ 2× that, else alpha 100) and trees (HistGradientBoosting, max_iter
  100, learning_rate 0.05, max_leaf_nodes 7, min_samples_leaf 30, l2 1.0,
  random_state 11).
- Bootstrap: circular moving blocks, 2,000 draws, seed 20261015.
- Gate: 95 % interval upper end < 0 and better in ≥ 4 of 6 test years.
- Selection: ≤ 3 by relative upper bound (hi / comparator loss), ties prefer the larger
  on-chain set; `selection.json` and `SCREEN.md` are committed before the holdout
  command; the screen refuses to overwrite `selection.json`.
- Report: B3's columns plus, for every row, R² against a training-mean constant
  (regression) or log-loss gain against the training base rate (classification) for
  both arms.
- Holdout: runs only for a committed non-empty selection; writes a one-shot lock with
  commit and blob before any sealed read; refits each selected model on all
  development samples; Holm at α = 0.05. An empty selection leaves the window unread.
  B4 is the fourth study on this window; once opened it is spent for later ETH studies.

## 7. Post-screen forensics (registered as exploratory)

Harness check against a constant forecast for every target; feature counts; labels-only
against deposit-expanded flows on the same models; the sign of the hourly ETH and
stable net-inflow coefficients against the motivating claim; per-year detail for any
near miss.

## 8. Compute and storage

- Engineering ≈ 1 working day; 30–40 tests.
- Coin Metrics and Binance fetches: minutes.
- Chain pass ≈ 15–25 h on the laptop (≈ 27 s per heavy 2025 day measured for
  transactions + token transfers; 2017–19 days are smaller; two-day prefetch).
- Screen: minutes to an hour (≈ 63,000 hourly development rows).
- Storage kept: hourly outputs ≈ 40 MB, final state snapshot ≈ 2 GB (deletable after
  the screen), JSON.

## 9. Package layout

```
tradingagents/research/onchain_b4/
  config.py        # research/onchain-b4-2026-10-15/config/b4.json
  cmdaily.py       # Coin Metrics fetch, dev/sealed split
  hourmarket.py    # Binance 1 h klines, dev/sealed split
  reader.py        # one S3 day of three tables, unpadding, admission, retries
  entities.py      # Bloom S, candidate table C, deposit set D, snapshots
  flows.py         # one day -> 24 hourly rows (E and labels-only)
  dataset4.py      # hourly and daily transforms, samples, targets, windows
  screen4.py       # B3 screen with hourly kind, constant-forecast columns, report
  cli.py           # market, cm, pass, features, screen, holdout
tests/research/onchain_b4/
research/onchain-b4-2026-10-15/   # CHARTER.md, config/b4.json, gates.json, STATE.md
research_artifacts/onchain-b4/     # gitignored
```

`onchain_b`, `onchain_b2` and `onchain_b3` are imported, not edited.

## 10. Testing

Address unpadding and keys; token decimals and admission; hourly binning at day and
hour boundaries; deposit rule on toy day sequences (fresh first send to L joins C and
becomes D the next day; a previously seen sender never joins; share falling below 0.9
leaves D; sweeps and top-ups inside E are excluded; a first deposit is counted once at
sweep time); snapshot round trip and resume equivalence; causality of hourly
transforms (changing data after h leaves features at h unchanged); target windows and
dev/sealed separation (no development label beyond 2024-12-31 23:00); Coin Metrics
one-day lag; screen comparisons, purges and blocks from config; holdout guards reused
from B2.

## 11. Checkpoints

- **B4-CP1:** Coin Metrics and hourly market data stored (dev and sealed); charter and
  gates committed.
- **B4-CP2:** chain pass complete (days built, unavailable), hourly and daily feature
  tables.
- **B4-CP3:** screen and committed selection.
- **B4-CP4:** holdout result, or the recorded decision not to open it; forensics.
