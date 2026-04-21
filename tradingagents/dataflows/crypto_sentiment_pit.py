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
    start_date: Annotated[str, "Start date yyyy-mm-dd (inclusive)"],
    end_date: Annotated[str, "End date yyyy-mm-dd (inclusive); acts as PIT cutoff"],
) -> str:
    """Fetch Alpaca News articles with strict PIT enforcement.

    Signature matches the live ``get_crypto_google_news`` tool so the vendor
    router can dispatch positionally. ``end_date`` is treated as end-of-day
    UTC (inclusive of its own 23:59:59.999999) and is also used as the
    ``as_of`` cutoff — no article with ``as_of_ts`` beyond end-of-day(end_date)
    is returned. This is consistent with the OHLCV ``Date <= curr_date``
    convention in ``coingecko_binance.py``.

    Returns raw headlines and article content for the LLM analyst to
    interpret sentiment. Every row satisfies as_of_ts <= end-of-day(end_date),
    so there is no look-ahead.
    """
    coin = coin_name.lower()
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return f"Invalid date format: start={start_date!r} end={end_date!r} (expected yyyy-mm-dd)."

    # End-of-day UTC: end_date is inclusive of its own 23:59:59.999999.
    ts_end = end_dt + timedelta(days=1) - timedelta(microseconds=1)
    ts_start = start_dt

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
            f"No Alpaca articles found for {coin_name} in the window "
            f"{start_date} → {end_date}. "
            f"(Ensure backfill_alpaca_news.py ran for this range.)"
        )

    lines: list[str] = [
        f"# Alpaca News (Benzinga): {coin_name}",
        f"# Window: {start_date} → {end_date}",
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
