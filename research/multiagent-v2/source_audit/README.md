# Source audit for the text material (2026-11-14)

Question: which point-in-time text sources could be added for 2022 to 2024, what they cost, and whether an
earlier closed programme already covers them. No outcome column is read and no model call is made. The result
is recorded in `../STATE.md`, section "Source audit".

All probes ran from the devbox with a generic user agent. Downloaded third-party data is kept outside the
repository and is not committed.

| File | Content |
|---|---|
| `bn_probe.py`, `bn_list.py`, `bn_catalogs.json` | Binance announcement catalogues (public content endpoint): totals and the list download |
| `bn_coverage.py`, `bn_coverage.json` | Coverage of the Charter 4 universe by Binance announcement titles |
| `cdx_feeds.py`, `cdx_feeds.json` | Wayback captures of outlet RSS feeds, March 2023 |
| `cdx_outlets.py`, `cdx_outlets.json` | Wayback captures of further outlets, week of 2023-03-13 |
| `gdelt_probe.json` | GDELT DOC API, two name queries for one week |
| `pubtime_probe.py`, `pubtime_probe.json`, `pubtime_summary.py`, `pubtime_summary.json` | Publication time of 90 stored articles read from the first capture, against the capture time |
| `agg_news_audit.py`, `agg_news_audit.json` | Public news archive of 70 outlets: volume, time stamps, coverage against the present store |
| `agg_news_tz.py`, `agg_news_tz.json` | Month by month check of the archive's time zone against the first captures |
| `agg_news_titles.py`, `agg_news_titles.json` | Share of price-commentary titles, keyword rule |
| `tweets_audit.py`, `tweets_audit.json`, `tweets_gaps.py` | Public tweet dataset: volume, accounts, coverage, collection gaps |

Probes without a script (single requests, results in `../STATE.md`): OKX and Bybit announcement endpoints,
Upbit notices, CryptoCompare and CoinDesk Data news endpoints, Snapshot GraphQL (proposal counts of nine
spaces), Arctic Shift yearly post counts of project subreddits, Hugging Face dataset search.

Third-party data (not in the repository):

| Dataset | File | Bytes | sha256 |
|---|---|---|---|
| Hugging Face `maryamfakhari/crypto-news-coindesk-2020-2025` (CC-BY-NC-4.0, attribution required) | `news.csv` | 240,403,139 | `d17b24d672c6e343ce43e267c2ab5c37438edbb88004d8548e626ba28bd2339c` |
| Hugging Face `StephanAkkerman/financial-tweets-crypto` (MIT) | `train.parquet` | 20,735,701 | `81b2f7563a44c1a103e9468a83d52319dfeae0fc616422b4a4df90d8d684b960` |
| Binance announcement lists (catalogues 48, 49, 128, 157, 161) | `data/source_audit/binance/*.jsonl` | 1,384,825 | local, ignored by git |

Only the columns `date` and `base` of the Charter 4 decision panel are read. The panel has 728 decision days
from 2023-01-01: the 722 test days of Charter 4 and the six days before them.
