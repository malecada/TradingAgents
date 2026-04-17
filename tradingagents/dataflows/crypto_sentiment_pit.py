"""PIT-enforced crypto sentiment tool implementations.

Registered as vendor 'crypto_sentiment_pit' in dataflows.interface.
When data_vendors['crypto_sentiment'] = 'crypto_sentiment_pit', agent tool
calls route here instead of the today-relative live implementations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import pandas as pd

from tradingagents.dataflows import sentiment_store


def get_crypto_news_pit(
    coin_name: Annotated[str, "Cryptocurrency name (e.g., 'Bitcoin', 'Ethereum')"],
    trade_date: Annotated[str, "Point-in-time date in yyyy-mm-dd format; no data after this date is returned"],
    lookback_days: Annotated[int, "How many days back from trade_date to fetch"] = 7,
) -> str:
    """Fetch Alpaca News articles with strict PIT enforcement.

    trade_date is treated as end-of-day UTC (consistent with the OHLCV
    ``Date <= curr_date`` convention in ``coingecko_binance.py``, where the
    midnight-keyed row for trade_date contains that day's close). Articles
    published on trade_date itself are therefore visible; articles published
    after 23:59:59.999999 UTC on trade_date are not.

    Returns raw headlines and article content for the LLM analyst to
    interpret sentiment. Every row satisfies as_of_ts <= end-of-day(trade_date),
    so there is no look-ahead.
    """
    coin = coin_name.lower()
    try:
        trade_dt = datetime.strptime(trade_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return f"Invalid trade_date format: {trade_date!r} (expected yyyy-mm-dd)."

    # End-of-day UTC: trade_date is inclusive of its own 23:59:59.999999.
    ts_end = trade_dt + timedelta(days=1) - timedelta(microseconds=1)
    ts_start = trade_dt - timedelta(days=lookback_days)

    try:
        df = sentiment_store.query_news(
            coin=coin,
            ts_start=ts_start,
            ts_end=ts_end,
            as_of=ts_end,
            limit=50,
            root=sentiment_store.DEFAULT_ROOT,
        )
    except ValueError as e:
        return f"Sentiment store error: {e}"

    if df.empty:
        return (
            f"No Alpaca articles found for {coin_name} in the "
            f"{lookback_days}-day window before {trade_date}. "
            f"(Ensure backfill_alpaca_news.py ran for this range.)"
        )

    lines: list[str] = [
        f"# Alpaca News (Benzinga): {coin_name}",
        f"# Window: {ts_start.date()} → {trade_date}",
        f"# Articles: {len(df)}",
        "",
    ]
    for i, row in enumerate(df.itertuples(index=False), 1):
        event_ts_str = pd.Timestamp(row.event_ts).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"### Article {i} — {row.source}")
        lines.append(f"**Date:** {event_ts_str}")
        lines.append(f"**Headline:** {row.headline}")
        if row.summary:
            lines.append(f"**Summary:** {row.summary}")
        elif row.content:
            body = row.content[:800]
            lines.append(f"**Content:** {body}")
        if row.url:
            lines.append(f"**URL:** {row.url}")
        lines.append("")
    return "\n".join(lines)


def get_reddit_posts_pit_stub(
    coin_name: Annotated[str, "Cryptocurrency name"],
    start_date: Annotated[str, "Start date yyyy-mm-dd"],
    end_date: Annotated[str, "End date yyyy-mm-dd"],
) -> str:
    """P1 stub: Reddit PIT data is not available (Phase 3).

    Returning an explicit message (instead of no impl) prevents the vendor
    router from silently falling back to the today-relative live Reddit tool.
    """
    return (
        f"Reddit PIT data is not available in P1 (no Arctic Shift/Pushshift ingest yet). "
        f"Sentiment analysis should rely on Alpaca News for {coin_name}."
    )
