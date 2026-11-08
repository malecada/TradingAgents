# multiagent-v2 — Phase 1 state (dossier builder)

Plan: `docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md`. Branch `feature/multiagent-v2-dossier`.
Runtime: minimal `.venv` (pandas, pyarrow, requests, python-dotenv, trafilatura, warcio, datasketch, pytest);
run scripts with `PYTHONPATH=. .venv/bin/python scripts/<name>.py`. Key: `OPENROUTER_API_KEY` in `~/.secrets/openrouter.env`.

## Components (all unit-tested, `tests/research/test_dossier_*.py`)
- `tradingagents/dossier/universe.py` — weekly top-N by `dvol_30d` from `data/llm_rank_xs/cards.parquet` (2021-01 → 2026-06-26; top-50 over 2022-01→2024-12 = 7,800 asset-weeks, 222 symbols).
- `store.py` — bitemporal Parquet text store `data/dossier/text/<source>/<yyyy>/<mm>.parquet`; earliest capture wins; PIT query.
- `wayback.py` + `scripts/dossier_news_discover.py` / `dossier_news_fetch.py` — CoinDesk, Cointelegraph, The Block via Wayback CDX (first capture = as_of) and raw capture fetch at 1 req/3.5 s; trafilatura text + publication date. Common Crawl index found too sparse (0–668 records per crawl).
- `reddit.py` + `scripts/dossier_reddit_fetch.py` — Arctic Shift posts (r/CryptoCurrency, r/Bitcoin, r/ethereum); as_of = created; 87% of bodies empty (link posts).
- `entities.py` — dictionary from CoinGecko top-1000 + curated aliases/synonym groups; linker with salience.
- `anonymizer.py` — Masker v2: role tokens per channel, relative dates, year-less dates resolved to nearest occurrence, price levels masked, verification pass.
- `numeric_card.py` — relative-only numeric block + indexed weekly price path.
- `llm_text.py` — DeepSeek V4.1-Flash (Baidu fp8) typing {price_recap, event, analysis_opinion, promotional, unrelated} + anonymized 2-sentence summary + novelty; disk cache; smoke 3 items $0.0003.
- `quant_forecast.py` — walk-forward cross-sectional ridge (52-week burn-in) with trailing 26-week calibration record.
- `builder.py` + `scripts/dossier_build.py` — assembles dossier text (numeric → text → linking → masking → typing → selection within ~9K tokens → verify → hash) to `data/dossier/dossiers/<friday>/<symbol>.json`.
- `or_client.py` — generic pinned structured-output client (roles pro/flash/chrono); `scripts/dossier_reid_probe.py` — re-identification probe.

## Jobs
- 2026-11-08 discovery (`/tmp/dossier_discover.log`) and Reddit ingest (`/tmp/dossier_reddit.log`) started in background.
- Fetch worker to start after discovery completes: `scripts/dossier_news_fetch.py --start 2022-01 --end 2024-12` first (dev window), then later months.

## Open
- Macro calendar block (FOMC/CPI) not yet in the dossier.
- Cards end 2026-06-26: Sealed-B / forward need card rebuild from Binance public funding + klines (week 5).
- Alpaca/Benzinga store lives on the laptop; sync when available (`data/sentiment/alpaca`).

## Phase 2 scaffolding (written 2026-11-08, ahead of schedule; awaits dossiers)
- `tradingagents/agents_v2/{schemas,roles,graph,runner,evaluate}.py` + `scripts/agents_run.py`: three analysts
  (market, fundamental, news) + forecast interpreter; debate in both orders with one rebuttal each; judge per
  order, probabilities averaged; debate only for the 20 most contested/convinced aliases per week, analysts' mean
  probability for the rest; weekly PM with constraint validation and a deterministic rule twin as fallback and
  baseline; results cached per (dossier sha, config sha) in `data/agents_v2/runs/<friday>/`.
- Evaluation: residualized weekly rank IC (controls vol, 4w momentum, size), Newey-West t, Brier skill vs 0.5,
  calibration slope (`agents_v2/evaluate.py`).
- Target definition: P(asset 7-day return > universe median return), decision Saturday 00:00 UTC after the Friday card.

## 2026-11-08 evening — pilot findings on Q1-2022 dossiers (builder v2.3)
- Audit (145 dossiers): 93% with shown items, median 9 items, noise share 27%, 0 leaks by dictionary verification.
- **Re-identification probe FAIL**: DeepSeek V4-Pro (non-thinking, StreamLake route because Baidu returned 502s)
  names the asset in 81/100 anonymized dossiers (chance 1.9%) and the month within ±6 months in 81/100.
  Name masking is insufficient: content (project-specific events, partners, products, price-path shape)
  identifies the asset. Per-section probes (numeric-only, text-only) running to locate the channel.
- Consequence for the plan: §5 anonymization must be hardened (generic rewriting of news summaries,
  removal of non-dictionary proper nouns, coarser numeric rendering) and re-probed; otherwise pre-release
  windows cannot be claimed leakage-controlled and Sealed-B carries the whole evidential weight.
