# Metadata-only market source inventory

September 16, 2026. Footer schemas, row counts, timestamp statistics, manifests
and fetcher lineage were inspected; no price rows or forecasting outcomes were
materialized. These endpoints do not prove interior completeness.

| Source under /home/malecada/master_thesis | Coverage | Bytes | Instrument |
|---|---|---:|---|
| TradingAgents/data/xsect/klines/ETHUSDT.parquet | 2019-11-27–2026-07-02 daily, 2,410 rows | 109,556 | USDT-M perpetual |
| TradingAgents/data/xsect/klines_1h/ETHUSDT.parquet | 2020-06-01–2026-07-28 18:00, 53,971 rows | 3,299,527 | USDT-M perpetual |
| TradingAgents-predlab/data/predlab/klines_5m/ETHUSDT.parquet | 2020-01-01–2026-07-30 12:20, 691,925 rows | 34,672,901 | USDT-M perpetual |
| TradingAgents/data/derivatives_raw/ETHUSDT_basis.parquet | 2021-11-01–2026-05-26 daily, 1,663 rows | 54,507 | Joined spot/perpetual closes only |

Current SHA256, in the same order:

```
711fd5f6ad252bada78f9bad4b082777ac98a9b666108bf439f372183077549f
d178f72396566330317074be1e7e39087d610207f1e2ceec5b59253488e694e6
3b5cf031059ba5b0c0228ccc4b9220f964c3762d3e4bf5a4702dbb7c968f066d
8b0ddfa435920c67a2e178f5bc649a261c4d0e60f5ced225dc0e143a9f11c828
```

Daily/hourly/5m fetchers specify fapi and futures/um archives. All timestamps
are bar openings. The basis builder uses Binance spot klines but preserves only
close after a completeness join with perpetual prices; spot volume/open are
absent, and an original capture receipt binding these bytes was not located.
No existing candidate qualifies for the full spot-open/close/volume protocol.
This is a bounded inventory finding, not proof no other copy exists.

Prior docs/diagnostics-2026-09-10/forecast-charter.md includes ETH direction
origins December 2021–March 2025 and spent P1/P2/P5 holdouts. The factor-risk
charter covers November 2021–March 2025; the risk-policy charter also marks
historical windows spent. Thus 2022–2024 cannot be fresh confirmation. Existing
raw-store backup certification is incomplete; local hashes are not remote backup.

Storage observation at preparation: /dev/nvme0n1p6 had 82,027,532,288 available
bytes (76.4 GiB), shared by workspace, /mnt and /media paths examined. Existing
graph projection estimate is 130.75 GiB before recompression; one-day ratio
.743960122 suggests approximately 97.3 GiB payload, without derived artifacts or
backups. User subsequently authorized bounded pulls on this filesystem while
freeing space. Per-request free-space guards protect the fixed first tranche.

Subsequent user addition: /home/malecada/Data, ext4 Data label, /dev/nvme0n1p3,
176,155,725,824 bytes available (164.1 GiB). New preserved execution checkouts and
captures use /home/malecada/Data/onchain-research/. This is a different partition
on the same physical NVMe device, not an independent backup. Full-history raw,
derived and external backup layouts still need separate capacity accounting;
the first bounded tranche fits without relying on the projection as a hard bound.
