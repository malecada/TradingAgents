# PIT Sentiment Pipeline — Phase 1 (Alpaca News)

**Date:** 2026-04-17
**Status:** Design — approved for implementation planning
**Author:** Adam Málek
**Scope:** Phase 1 of a 3-phase PIT sentiment pipeline. Later phases (GDELT, HuggingFace Parquet corpora, Reddit dumps) are out of scope for this spec.

## Problem

The `crypto_sentiment` analyst's existing tools are today-relative, not point-in-time:

- [crypto_sentiment.py:68](../../../tradingagents/dataflows/crypto_sentiment.py#L68) — Reddit search uses `time_filter: "week"|"month"|"year"`, which Reddit resolves as "last N from today" and ignores the `start_date`/`end_date` arguments.
- [crypto_sentiment.py:135](../../../tradingagents/dataflows/crypto_sentiment.py#L135) — Google News uses `when:{days_back}d`, also relative to today.

If the `crypto_sentiment` analyst is enabled in a historical backtest, agents making decisions for a January 2026 trade date receive today's Reddit threads and today's news articles. This is a severe look-ahead bias and is why the analyst was disabled in the 90-day backtest that just completed (2026-01-16 → 2026-04-15). Re-enabling it requires a historically accurate, point-in-time sentiment data layer.

## Constraints

1. **LLM training cutoff bounds the backtest window.** GPT-4o-mini's cutoff is 2023-10. Any backtest earlier than that is contaminated by the LLM's training memory, so the historical backfill only needs to cover **2023-10 → present**. This also applies forward: if the project upgrades to a newer model with a later cutoff, the viable window shifts, not the source data.
2. **Cost: use GPT-4o-mini for both `deep_think_llm` and `quick_think_llm` during development.** Larger models are reserved for final thesis-result runs.
3. **LLM-centric sentiment.** The analyst synthesizes sentiment from raw text (headlines, article content). No pre-computed sentiment scores, no HuggingFace classifier in P1. CryptoBERT-style scoring is deferred to a later prediction-model feature, not the sentiment analyst.
4. **No new heavyweight infrastructure.** Thesis-scale data — DuckDB + Parquet is sufficient; Delta Lake/Databricks is overkill.
5. **Graceful degradation.** Agent must continue if the sentiment store is missing, empty, or errors — same pattern as existing Reddit/Google News tools.

## Architecture

```
Alpaca News API (Benzinga)
  │  backfill script (historical) + daily incremental (future)
  ▼
data/sentiment/alpaca/{year}/{month}.parquet
  schema: [event_ts, as_of_ts, id, headline, content, symbols, source, url]
  │
  ▼
DuckDB view (created on demand via glob pattern)
  │
  ▼
get_alpaca_news_window(coin, trade_date, lookback_days)
  WHERE event_ts BETWEEN (trade_date - lookback) AND trade_date
    AND as_of_ts   <= trade_date
    AND (symbols LIKE '%BTC%'  OR symbols LIKE '%ETH%')   -- per coin
  │
  ▼
crypto_sentiment_analyst (LLM reads headlines/content, writes sentiment_report)
```

## Components

### New modules

- **`tradingagents/dataflows/sentiment_store.py`** — DuckDB wrapper.
  - `connect() -> duckdb.Connection`
  - `upsert_alpaca_rows(df: pd.DataFrame, year: int, month: int) -> None`  (writes/appends a month Parquet file)
  - `query_news(coin: str, ts_start: datetime, ts_end: datetime, as_of: datetime, limit: int = 50) -> pd.DataFrame`
  - Query implementation globs `data/sentiment/alpaca/*/*.parquet`, filters by `event_ts`/`as_of_ts`, uses an explicit coin→symbol map: `{"bitcoin": "BTCUSD", "ethereum": "ETHUSD"}`. Filter predicate: `symbols LIKE '%' || <mapped_symbol> || '%'` (exact substring on `BTCUSD`, avoiding a `BTC`-matches-`BTCUSD,DOGEBTC` collision).

- **`scripts/backfill_alpaca_news.py`** — one-shot CLI.
  - Args: `--start 2023-10-01`, `--end today`, `--symbols BTCUSD ETHUSD`, `--out-dir data/sentiment/alpaca`, `--batch-days 7`, `--force`.
  - Paginates Alpaca `/v1beta1/news` via `next_page_token`; groups by year/month; writes Parquet per month.
  - Sets `as_of_ts = event_ts + 60s` (near-real-time source, small buffer captures ingestion lag).
  - Idempotent: reads existing Parquet for the month, merges by `id`, writes back. `--force` overrides.
  - Rate limit: Alpaca free tier = 200 req/min. Backoff on 429.

- **`tradingagents/dataflows/crypto_sentiment_pit.py`** — PIT tool functions wired into LangChain.
  - `get_crypto_news_pit(coin: str, trade_date: str, lookback_days: int = 7) -> str` — formats `sentiment_store.query_news(...)` output as a markdown block (same shape as existing `get_crypto_google_news` output).
  - Returns a "no data" message if the store is empty or missing.

### Modified modules

- **`tradingagents/default_config.py`** — add `"sentiment_mode": "live"` default. Backtest scripts override to `"pit"`.
- **`tradingagents/dataflows/interface.py`** — in the `crypto_sentiment` vendor category, route `get_crypto_news` based on `config["sentiment_mode"]`:
  - `"live"` → existing `get_crypto_google_news` (today-relative, fine for live trading)
  - `"pit"` → new `get_crypto_news_pit`
- **`tradingagents/agents/analysts/crypto_sentiment_analyst.py`** — no prompt changes; tool list composition picks up the vendor-routed function. Verify the prompt's expectations match the PIT tool's output shape.
- **`scripts/generate_agent_signals.py`** — when callers pass `sentiment_mode="pit"` via config, include `"crypto_sentiment"` in the default analyst list for sentiment-enabled runs.

## Data flow and PIT rule

Every row in the Parquet store has two timestamps:

- **`event_ts`** — original publication time from Alpaca's `created_at` field. PIT-safe (publisher-assigned).
- **`as_of_ts`** — when the row became observable in our store. For Alpaca's near-real-time feed this is `event_ts + 60s`. For future mutable sources (e.g., Google Trends if added later) it would be the daily snapshot time.

Backtest queries **always** filter `as_of_ts <= trade_date`. This is enforced at the `sentiment_store.query_news` level — the agent tool cannot bypass it. Unit tests verify this filter cannot be omitted.

## Schema

Parquet files: `data/sentiment/alpaca/{year}/{month:02d}.parquet`

| column | type | notes |
|---|---|---|
| `event_ts` | timestamp (UTC) | Alpaca `created_at`; row's primary time |
| `as_of_ts` | timestamp (UTC) | `event_ts + 60s` for Alpaca (near-real-time) |
| `id` | int64 | Alpaca article ID; dedup key |
| `headline` | string | title |
| `content` | string | body text (may be empty); Alpaca returns HTML — strip tags on ingest |
| `summary` | string | short blurb if Alpaca provides one |
| `symbols` | string | comma-joined, e.g. `"BTCUSD,ETHUSD"` |
| `source` | string | Alpaca `source` field |
| `author` | string | optional |
| `url` | string | |

Partitioning: physical files per month; logical querying via DuckDB glob `data/sentiment/alpaca/*/*.parquet`.

## Rerun plan (validation at end of P1)

Rerun the 2026-01-16 → 2026-04-15 BTC+ETH backtest with the PIT sentiment analyst enabled:

```bash
# Signals go to a separate dir so the original 3-analyst baseline is preserved for comparison.
python scripts/generate_agent_signals.py \
  --coins bitcoin ethereum \
  --start 2026-01-16 --end 2026-04-15 \
  --analysts market onchain prediction crypto_sentiment \
  --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
  --output-dir data/agent_signals_pit
python scripts/backtest_system_v2.py \
  --coins bitcoin ethereum \
  --start 2026-01-16 --end 2026-04-15 \
  --signals-dir data/agent_signals_pit \
  --output-dir data/agent_backtest_v2_pit
```

Note: `--signals-dir` / `--output-dir` flag names on `backtest_system_v2.py` need verification during implementation; if not present, add them as a first-step refactor. The principle (separate dirs) is non-negotiable.

Compare to the 2026-04-17 baseline:
- Signal distribution shift (was BTC 67 SELL / 18 BUY, ETH 59 SELL / 23 BUY)
- Return / Sharpe / MaxDD / WinRate per coin and portfolio
- Sample inspection: for 3 trading days where the baseline said SELL and sentiment-enabled says BUY (or vice versa), read the sentiment report and confirm it's driven by real Alpaca coverage, not hallucination.

Write results to `THESIS_FINDINGS.md` under a new "PIT Sentiment — Alpaca P1" heading.

## Error handling / graceful degradation

- **Missing Parquet store** → `query_news` returns empty DataFrame → tool returns `"No cached sentiment for this window; ensure backfill_alpaca_news.py ran for the date range."` (same pattern as existing tools)
- **Empty window** → tool returns `"No Alpaca articles found in the {lookback_days}-day window before {trade_date}."`
- **Alpaca rate limit during backfill** → exponential backoff (1s, 2s, 4s, 8s, max 60s); preserve progress across retries.
- **Agent-side** — existing graceful degradation pattern applies: if the tool errors, the analyst's report will note missing sentiment and the debate proceeds.

## Testing

- **Unit — store round-trip**: ingest 100 synthetic rows across 3 months → Parquet on disk → query full window → assert row count and column values match.
- **Unit — PIT enforcement**: ingest rows with `event_ts` both before and after a fixed `as_of`; query with that `as_of`; assert no row with `event_ts > as_of` is returned.
- **Unit — symbol filtering**: ingest rows tagged `BTCUSD`, `ETHUSD`, `BTCUSD,ETHUSD`, `SOLUSD`; query for `bitcoin` and `ethereum` separately; assert correct partitioning.
- **Integration — backfill smoke**: backfill 1 day of real Alpaca data (`--start 2024-01-01 --end 2024-01-02`); assert Parquet exists and has >0 rows.
- **Integration — agent propagate**: force `sentiment_mode="pit"`, run `ta.propagate("bitcoin", "2024-01-02")` against the smoke-backfilled store; assert `final_state["sentiment_report"]` is non-empty and references Alpaca content.
- **Regression — backtest rerun**: the validation run above; compare signal distribution against baseline logged in `THESIS_FINDINGS.md`.

## Out of scope for P1

Explicitly deferred to later phases:
- GDELT 2.0 ingestion (Phase 2)
- HuggingFace `edaschau/bitcoin_news` Parquet corpus (Phase 2)
- alternative.me Fear & Greed daily snapshots (Phase 2)
- Arctic Shift / Pushshift Reddit dumps (Phase 3 — and likely not needed at all since our viable backtest window is post-2023-10 and Arctic Shift's coverage gets patchy there)
- CryptoBERT or any learned classifier (deferred until prediction model gains a sentiment feature)
- Replacing live-mode tools — `"live"` mode keeps existing behavior
- Multi-year 2020–2023 historical validation — dropped entirely due to LLM cutoff constraint
- Twitter/X archives — paywalled for recent data, out of scope

## Open questions

None at design-approval time. Implementation may surface:
- Alpaca's `content` field turns out to be too sparse → may need to fall back to headline-only analysis. Decide during integration test.
- Whether DuckDB glob performance degrades past ~50 Parquet files → if so, partition by year not year/month. Benchmark during validation rerun.

## Approval

- Design approved by Adam: 2026-04-17 (this session).
- Next: spec self-review (inline), then writing-plans skill to produce the implementation plan.
