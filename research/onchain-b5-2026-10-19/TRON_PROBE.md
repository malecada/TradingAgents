# Q5 — Tron USDT feasibility probe (2026-10-19)

**Verdict: go — feasible at no cost, labels-only.** No Tron analysis is part of B5; this
note sizes a later study.

## Source

SQD Network portal, keyless HTTP:
`POST https://portal.sqd.dev/datasets/tron-mainnet/stream` with a JSON body
(`type: tron`, block range, log filters, field selection); newline-delimited JSON, one
block per line; long ranges arrive in parts and are continued from the last block.

- USDT TRC-20 contract (hex, no 0x41 prefix): `a614f803b6fd780986a42c78ec9c7f77e6ded13c`;
  Transfer topic0 `ddf252ad…b3ef`.
- History reaches at least block 20,000,000 (2020-05-23). A request at block
  10,000,000 (2019) returned HTTP 529 (overloaded), so the free tier is rate-limited
  and early 2019 coverage is unconfirmed.

## Labels

Dune Spellbook `dbt_subprojects/hourly_spellbook/models/_sector/cex/addresses/chains/tron/cex_tron_addresses.sql`:
151 Tron addresses across 30 exchanges (MaskEX 19, HTX 18, Binance 16, OKX 15,
CoinDCX 13, Bitget 11, Bybit 8, Lemon Cash 6, KuCoin 5, Bitfinex 4, …). Base58check
addresses convert to the 32-byte topic form by stripping the 0x41 version byte and the
4-byte checksum. B4 found labels-only stablecoin flows as informative as
deposit-expanded flows, so no deposit inference is needed.

## Measured volume (blocks 84,000,000–84,001,200 ≈ 1 hour, 2026-06-28)

| Request | Transfers | Bytes | Time |
|---|---|---|---|
| All USDT transfers | 81,479 | 23.6 MB | 4.2 s |
| To labelled exchanges (server-side topic2 filter) | 3,540 | 1.0 MB | 0.5 s |
| From labelled exchanges (topic1 filter) | 7,073 | 2.1 MB | 0.8 s |

## Cost estimate

- **Filtered (recommended):** about 3 MB and 1–2 s per hour of blocks in 2026, less in
  earlier years. Full history from 2020 is about 50–150 GB streamed, 6–20 h at the
  observed rates, with hourly aggregation on the fly (nothing raw stored).
- **Unfiltered:** about 0.6 GB per day in 2026, roughly 0.5–1 TB in total, multi-day.
- **Risks:** free-tier rate limits (HTTP 529) need back-off; a 151-address label set
  misses unlabelled exchange wallets, and its 2026 snapshot is applied to all years.
