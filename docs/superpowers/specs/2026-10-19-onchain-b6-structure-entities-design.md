# Branch B6 — hourly graph structure, entity detail and minute-level events

Status: design approved in conversation 2026-10-19 ("go ahead, I need to go afk so go
forward with whole b6"): the user granted autonomy for spec, plan, build, data pass and
analyses. Branch `research/onchain-replication-b-2026-10-12`. B4 confirmed that hourly
exchange-flow intensity forecasts next-6-hour ETH volatility against price history; B5
showed the option market already prices it. B6 is the final on-chain graph test of this
programme: structure and entity detail at hourly resolution, and the minute-level
reaction to very large deposits.

## 1. Decisions

1. Exploratory with a pre-declared plan (`PLAN.md`), as B5: the ETH and BTC 2025–26
   windows are spent. Confirmation is a later forward study.
2. Labels-only exchange entities (B4: deposit inference added nothing for stablecoins),
   expanded with eth-labels' exchange addresses and activated at first observation.
3. Items run in the recommended order: hourly structure (1), entity detail (2),
   minute-level event study (3); Tron USDT as a side block (4) only if its stream
   finishes before the forecast stage.
4. Targets: realised volatility only (next 6 h and 24 h). No direction or return targets.

## 2. Questions

- **Q1 structure.** Do hourly structural statistics of the transfer graph add volatility
  information beyond price history, option-market information and B4's flow intensity?
- **Q2 entity detail.** Do flows split by stablecoin, flows of DEX, bridge, MEV and fund
  addresses, and stablecoin issuance add beyond B4's flows?
- **Q3 minutes.** Do very large exchange deposits or withdrawals move realised volatility
  or price within 5–60 minutes of their block, and does the market move before the block?
- **Q4 Tron (side).** Does Tron USDT exchange flow add beyond Ethereum flows?

## 3. Labels (frozen before the pass, `research_artifacts/onchain-b6/labels/labels6.json`)

| Set | Source | Rule |
|---|---|---|
| Exchange | B2 `labels.json` (4,961) ∪ eth-labels v1 `data/csv/accounts.csv`, chainId 1, rows whose `label` matches a B2 exchange entity stem (109 labels, ≈ 31,000 addresses) | entity name = B2 name or the eth-labels label |
| DEX | eth-labels rows with `label == 'dex'` or `nameTag` containing "router" (case-insensitive) | ≈ 400 |
| Bridge | eth-labels `label == 'bridge'` or `nameTag` containing "bridge" ∪ Spellbook `labels_bridges_ethereum.sql` | ≈ 500 |
| MEV | eth-labels `label` in {mev-bot, mev-builder} | ≈ 3,800 |
| Funds | Spellbook `labels_funds_ethereum.sql` ∪ eth-labels `nameTag` containing any of Wintermute, Jump Trading, Cumberland, Galaxy Digital, Amber Group, B2C2, DWF Labs, GSR, Flow Traders, Genesis Trading, FalconX | ≈ 150 |
| Issuer | Tether Treasury `0x5754284f345afc66a98fbb0a0afe71e0f007b949`; USDC and DAI mint/burn = transfers from/to the zero address | fixed |

An address in the exchange set is removed from every class. Source commit SHAs and
counts are stored with the file. **Activation:** a labelled address counts as labelled
from the day after its first observed transfer (as sender or receiver, any asset) in
the pass; before that it is unlabelled. The identity look-ahead of a 2026 label set is
disclosed.

## 4. Data pass (2017-01-01 … 2026-10-11, sequential, one process)

Reads per day as B4 (`transactions`, `token_transfers`, `blocks`) with a B6 admission
that also keeps stablecoin transfers from or to the zero address, flagged as mint or
burn, and carries the token (ETH, USDT, USDC, DAI) per transfer. Entity state: the
frozen label sets, an activation table (first-seen day per labelled address), and a
Bloom filter (2³³ bits, 5 hashes) of every address seen in earlier hours. Snapshots
every 30 days; resumable; read watchdog and disk guards as B4.

Per hour h, three outputs:

### 4.1 Structure block `gs_` (11)

On the hour's non-self transfers of ETH and stablecoins; U = undirected simple graph.

| Feature | Definition |
|---|---|
| gs_active | distinct addresses (senders ∪ receivers) |
| gs_new_share | share of gs_active not in the Bloom filter before the hour |
| gs_edges | distinct ordered (src, dst) pairs |
| gs_edges_per_node | gs_edges / gs_active |
| gs_value_gini | Gini of per-address outgoing stablecoin USD among addresses with any |
| gs_top10_share | top-10 senders' share of outgoing stablecoin USD |
| gs_core2_share | share of nodes in the 2-core of U (B3 frontier peeling) |
| gs_giant_share | largest connected component of U / gs_active |
| gs_ex_cp | distinct non-exchange addresses with a transfer to or from an active exchange address |
| gs_ex_cp_new_share | share of gs_ex_cp not in the Bloom filter before the hour |
| gs_cex_cex_usd | stablecoin USD between exchange addresses of different entities |

The Bloom filter is updated with the hour's addresses after the hour's features.

### 4.2 Entity block `tk_`, `cl_`, `is_` (28)

- `tk_{usdt,usdc,dai}_{in,out}` (6): USD to / from active exchange addresses from /
  to non-exchange addresses, per token.
- `cl_{dex,bridge,mev,funds}_{stable_in,stable_out,eth_in,eth_out}` (16): value to
  (from) class addresses from (to) addresses outside the class.
- `is_{usdc,dai}_{mint,burn}` (4) and `is_usdt_treasury_{out,in}` (2): USD.

### 4.3 Large-transfer records

Every transfer to or from an active exchange address of ≥ $1M stablecoin or ≥ 500 ETH:
block timestamp, token, amount, direction (deposit / withdrawal), entity name, whether
the counterparty is new. Parquet per day.

## 5. Hourly features and forecast comparison

- B6 raw series enter as B4's causal transforms: `__h1z` (168-hour window, min 120) and
  `__d24z` (log1p of the 24-hour sum, 720-hour window, min 480), clip ±10 → 78 columns.
- Blocks: **F** = B4's 22 flow columns (`eth_`, `stable_` from
  `research_artifacts/onchain-b4/features/hourly.parquet`); **S** = `gs_`; **E** =
  `tk_`, `cl_`, `is_`; **T** = Tron (§7).
- Baselines: **P0** = B4 `h0_` (8) + B5 intraday `px_` (5); **K0** = P0 + `mk_dvol`,
  `mk_dvol_chg24` (B5 DVOL hourly) + `mk_iv` (log near-expiry near-ATM implied
  volatility per hour from B5's option trades, ≥ 3 trades, forward-filled ≤ 3 hours).
- Targets V6, V24 = log realised volatility of hourly log returns over the next 6 / 24
  hours (B4 definition); decision at the end of hour h; purge = horizon.

| Track | Window | Test years | Groups | Sets |
|---|---|---|---|---|
| A | 2017-10 → 2024-12 | 2019–2024 | 2019–24 | P0, P1 = P0+F, P2 = P1+S, P3 = P1+E, P4 = P1+S+E |
| B | 2021-04 → 2026-10-12 | 2022–2026 | 2022–24, 2025–26 | K0, K1 = K0+F, K2 = K1+S, K3 = K1+E, K4 = K1+S+E |

Comparisons per track: X1 vs X0, X2 vs X1, X3 vs X1, X4 vs X1 → 4 × 2 targets × 2
families (ridge with B4's alpha search; B4's tree settings) × 2 tracks = 32; with Tron,
X5 = X4+T vs X4 adds 8. Bootstrap: circular 168-row blocks, 2,000 draws, seed 20261020.
Pre-declared positive reading: track A — interval upper end < 0 and better in ≥ 4 of 6
years; track B — upper end < 0 in 2022–24 and mean difference < 0 in 2025–26.

## 6. Minute-level event study

- Binance 1-minute ETHUSDT and BTCUSDT closes, 2019-01-01 → 2026-10-12 (public REST).
- Events from §4.3: deposits (non-exchange → exchange) of ≥ $10M stablecoin or ≥ 5,000
  ETH, with a ≥ $50M / ≥ 20,000 ETH tier; withdrawals likewise; the first event per
  30 minutes per direction and tier. Event minute m = the minute containing the block
  timestamp; responses start at m + 1.
- Responses: log realised volatility over the next k ∈ {5, 15, 30, 60} minutes minus
  log realised volatility over the previous 60 minutes; signed log return over the next
  k ∈ {1, 5, 15, 30, 60} minutes; the signed return over the 15 minutes before m
  (anticipation check).
- Placebo: for each event, one random minute from the same year and hour of day, at
  least 60 minutes from any event (seed 20261020).
- Statistics: means with circular block bootstrap over time-ordered events (block 10,
  2,000 draws); groups 2019–24 and 2025–26; ETH primary, BTC as a cross-check.

## 7. Tron side block

SQD portal `tron-mainnet/stream`, USDT contract, Transfer topic0, server-side `topic1` /
`topic2` filters on the 151 Spellbook Tron exchange addresses (frozen with its commit
SHA), 2020-05-23 → 2026-10-12, hourly aggregation on the fly (nothing raw stored),
back-off on HTTP 529 / 429 (30 s, 120 s, 600 s), resumable per day. Series:
`tron_in_val`, `tron_out_val`, `tron_in_cnt`, `tron_out_cnt`, `tron_big_in` (≥ $1M);
transforms as §5. Used only if complete before the forecast stage; otherwise reported
as not run.

## 8. Pre-declared plan and reporting

`research/onchain-b6-2026-10-19/PLAN.md` lists every comparison, event table and
criterion of §§5–7 and is committed before any pass output is read. `RESULTS.md`
reports all of them; post hoc additions are labelled.

## 9. Compute and storage

- Engineering ≈ 1.5 days, ≈ 35 tests; fresh whole-branch review before the pass.
- Pass ≈ 25 h (labels-only, peak ≈ 3 GB, 6 GiB cap); 1-minute bars ≈ 50 min; Tron
  6–20 h in parallel; analyses < 1 h.
- Disk: hourly tables ≈ 100 MB, large transfers ≈ 200 MB, 1-minute bars ≈ 150 MB,
  snapshots ≈ 1.5 GB.

## 10. Package layout

```
tradingagents/research/onchain_b6/
  config.py      # research/onchain-b6-2026-10-19/config/b6.json
  labels6.py     # fetch, classify, freeze label sets; activation table
  reader6.py     # B4 tables with mint/burn kept and token codes
  structure6.py  # §4.1 on one hour
  hourly6.py     # one day -> 24 rows of gs_/tk_/cl_/is_ + large transfers
  minutes.py     # Binance 1-minute fetch; event selection, responses, placebo
  tron.py        # SQD stream, hourly aggregation
  dataset6.py    # transforms, IV series, samples for tracks A and B
  forecast6.py   # comparisons (B5 primitives), criteria, report
  cli.py         # labels, market, pass, tron, features, forecast, events, report
tests/research/onchain_b6/
research/onchain-b6-2026-10-19/   # CHARTER.md, PLAN.md, config/b6.json, STATE.md, RESULTS.md
research_artifacts/onchain-b6/     # gitignored
```

`onchain_b` … `onchain_b5` are imported, not edited.

## 11. Testing

Label classification and precedence; activation causality (an address labelled only
after first observation; day-boundary); structure features on hand-built hourly
graphs (Gini, top-10, 2-core, giant, counterparties, cross-entity value); mint/burn
and token codes in admission; large-transfer thresholds and directions; transforms
causal; IV series forward-fill limit; track windows and purges; event selection
spacing and tiers, response alignment (m + 1), placebo distance; Tron hourly
aggregation from a toy stream and back-off; pass resume equivalence and watchdog.

## 12. Checkpoints

- **B6-CP1:** labels frozen, 1-minute bars stored, `PLAN.md` committed.
- **B6-CP2:** pass complete; hourly tables; large transfers; Tron status.
- **B6-CP3:** forecast comparisons.
- **B6-CP4:** event study, `RESULTS.md`.
