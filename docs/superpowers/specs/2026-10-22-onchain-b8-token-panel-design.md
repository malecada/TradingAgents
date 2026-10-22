# Branch B8 — hourly per-token on-chain panel for perp-listed ERC-20 tokens

Status: design under the 2026-10-22 autonomy grant ("go with the recommended order … keep
working autonomously"; item 3 of the feature-generation review). Branch
`research/onchain-replication-b-2026-10-12`. B4–B7 studied one asset (ETH). B8 asks whether
the one surviving on-chain content — exchange-flow and activity intensity → short-horizon
volatility — holds across a panel of tokens, where cross-sectional breadth gives power and
no option market prices the information.

## 1. Decisions

1. Exploratory with a pre-declared plan (`PLAN.md`); no sealed window.
2. Universe: perp-listed symbols with a mainnet ERC-20 contract in the smw token map
   (`TradingAgents-predlab/data/predlab/smw/token_map.json`, `address` present) and at
   least two years of hourly bars in the 1-hour kline store
   (`TradingAgents/data/xsect/klines_1h`): 148 tokens, delisted ones included. The list is
   frozen in `config/universe.json` before the pass; it is a 2026 listing (disclosed).
3. Exchange addresses and their activation days are B6's (`labels6.json`, `state.npz`
   first-seen table): an address counts as an exchange from the day after its first
   observed transfer in the B6 pass.
4. Targets are volatility only: per-token next-6-hour and next-24-hour log realised
   volatility, and the 24-hour value relative to the hour's cross-sectional mean.
5. Features are B7's engineering (`features7.multiscale`) applied per token, plus
   cross-sectional z-scores per hour.

## 2. Questions

- **Q1 pooled.** Across tokens, do hourly exchange-flow and transfer-activity features
  improve next-6/24-hour volatility forecasts beyond the token's own price and volume
  history?
- **Q2 cross-section.** Do they forecast which tokens will be more volatile than the
  others over the next 24 hours (V24 relative to the hour's panel mean)?
- **Q3 (reading).** Is the per-token effect, if any, of the same kind as ETH's (an
  activity proxy that fades once intraday price features are present)?

## 3. Data pass (2020-06-01 … 2026-07-29, sequential, resumable per day)

`token_transfers` of the public ETH tables (B4's S3 reader, one table), rows whose
`token_address` is in the universe; amounts in token units via the map's `decimals`, USD
via the token's hourly close (bar-open hour of the block timestamp). Per token and hour:

| Series | Definition |
|---|---|
| dep_usd, wd_usd | USD to / from active exchange addresses from / to non-exchange addresses |
| dep_cnt, wd_cnt | counts of those transfers |
| tx_cnt | all transfers of the token |
| active | distinct addresses (senders ∪ receivers) |
| big_cnt | transfers ≥ $100k |

Output: one parquet per day with rows (hour, token, 7 series); days without the table are
marked unavailable (as B4/B6). Watchdog, stall exit and snapshots as B4 (no state beyond
the day files, so a snapshot is the set of written days).

## 4. Panel

- Per token: the 7 series → B7 `multiscale` (6 transforms each, 42 columns, prefix `n_`);
  price features from the token's hourly bars: B4 `price_features` (`h0_`, 8) and B5
  `px_features` (`px_`, 5) with quote volume as volume.
- Cross-sectional per hour over tokens with complete rows: z-scores of the 7 `__s24z` and
  7 `__ex1` columns (`xs_`, 14) and of `h0_rv24`, `h0_lvol24` (`xs_`, 2).
- Targets per token (B4 `hourly_targets`): V6, V24; XV24 = V24 minus the hour's mean V24
  over tokens with V24 (requires ≥ 20 tokens in the hour).
- Rows: token-hours with all features finite; a token enters 30 days after its first bar.

## 5. Comparisons

Pooled walk-forward, one model across tokens; test years 2022–2026 (window 2020-06 →
2026-07-29), purge = horizon, min_train 50,000 rows, expanding training. Families ridge
and trees_es (B7 `models7`; inner window for the alpha search 8,760 × 20 rows). Sets:
P0 = `h0_` + `px_` + `xs_h0_`; P1 = P0 + `n_`; P2 = P1 + `xs_n_`. Comparisons P1 vs P0,
P2 vs P1, P2 vs P0 per target and family (3 × 3 × 2 = 18 rows).

Statistics: per-row loss differences averaged per hour across tokens (rows of the same
hour are not independent), then the mean over hours with a circular block bootstrap over
hours (block 168, 2,000 draws, seed 20261023), per-year means, the constant-forecast
loss. Criterion: upper end < 0 and better in ≥ 3 of 5 years. Post hoc (labelled): per-token
mean differences, by liquidity tercile.

## 6. Compute

Pass: one table per day, ≈ 2,250 days at ≈ 10–20 s → 6–12 h (after the B7 forecast
finishes; memory cap 6 GiB). Panel: ≈ 5M rows × 75 columns ≈ 3 GB; forecasts: 5 folds ×
(3 sets × 2 families) × 3 targets = 90 fits, trees ≤ 600 iterations on ≤ 4M rows → ≈ 2–3 h.

## 7. Layout

```
tradingagents/research/onchain_b8/
  config.py, universe8.py (token list + decimals + bars), reader8.py (token_transfers day
  read filtered to the universe), hourly8.py (token-hour series with exchange activation),
  panel8.py (features, cross-sectional z, targets, rows), forecast8.py (pooled folds,
  hour-block bootstrap, criteria, report), cli.py (universe, pass, panel, forecast, report)
tests/research/onchain_b8/
research/onchain-b8-2026-10-22/   # CHARTER.md, PLAN.md, config/{b8.json,universe.json}, STATE.md, RESULTS.md
research_artifacts/onchain-b8/     # gitignored: days/, panel/, forecast/, logs/
```

## 8. Disclosures

- The universe and the token map are 2026 snapshots; delisted tokens are included where
  the kline store kept them, but tokens never listed on Binance perps are absent.
- Exchange labels: B6's disclosures carry over (identity look-ahead; activation causal).
- USD values use the perp close of the block's hour (price known within the hour; the
  value feature is therefore "known at the end of hour h" like the count features).
- §82 (smw_xs) tested DEX-swap smart-money features for next-day *returns* on the same
  kind of universe and closed; B8 uses exchange transfers and volatility targets only and
  makes no return claim.

## 9. Checkpoints

B8-CP1 universe frozen + PLAN committed; B8-CP2 pass complete; B8-CP3 panel; B8-CP4
comparisons and `RESULTS.md`.
