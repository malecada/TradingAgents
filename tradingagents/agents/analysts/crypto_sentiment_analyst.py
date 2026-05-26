"""Crypto sentiment analyst — v3 structured snapshot + narrow LLM, with
backwards-compatible legacy free-text path under a config flag."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_news,
    get_global_news,
    get_reddit_posts,
    get_crypto_google_news,
    get_language_instruction,
)
from tradingagents.dataflows.config import get_config
from tradingagents.sentiment import build_snapshot
from tradingagents.sentiment.anonymize import anonymize_text

logger = logging.getLogger(__name__)


_LEGACY_SYSTEM_MESSAGE = (
    """You are a cryptocurrency sentiment analyst tasked with analyzing market sentiment from multiple sources. Your role is to synthesize information from news outlets, social media, and community discussions to gauge the overall sentiment around a specific cryptocurrency.

**Available Data Sources (use all of them):**

1. **Alpha Vantage / Financial News** (get_news): Professional financial news with sentiment scores. Supports crypto tickers. Use this for institutional-grade news coverage.
2. **Global/Macro News** (get_global_news): Broader macroeconomic and regulatory news.
3. **Reddit Crypto Communities** (get_reddit_posts): Raw posts from crypto subreddits.
4. **Google News** (get_crypto_google_news): Mainstream news coverage.

Write a comprehensive sentiment report with: overall sentiment, confidence, key drivers, risks, and a Markdown summary table: Source | Dominant Sentiment | Key Theme | Confidence"""
)


_V3_SYSTEM_MESSAGE = (
    "You are a narrow cryptocurrency EVENT analyst. The polarity, attention, "
    "and regime fields in the SentimentSnapshot have already been computed "
    "deterministically — do NOT re-derive them. Your job is to:\n\n"
    "1. Summarize material EVENTS (regulatory, security, ETF, network) in "
    "≤120 words.\n"
    "2. Identify the dominant RISK and CATALYST for the next "
    "{horizon_days}-day horizon.\n"
    "3. Output a structured assessment:\n\n"
    "**Overall:** Strongly Bullish | Bullish | Neutral | Bearish | Strongly Bearish\n"
    "**Confidence:** Low | Medium | High\n"
    "**Key events:** ... (use snapshot events list)\n"
    "**Dominant risk:** ... \n"
    "**Dominant catalyst:** ...\n\n"
    "Stay factual. Do not interpret price action or polarity tone — that is "
    "handled upstream."
)


def _parse_trade_date(s: str) -> datetime:
    from datetime import timezone
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def create_crypto_sentiment_analyst(llm):

    def crypto_sentiment_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = get_config()
        mode = cfg.get("sentiment_mode", "legacy")

        if mode == "v3":
            return _run_v3(state, llm, cfg)
        return _run_legacy(state, llm, cfg)

    return crypto_sentiment_analyst_node


def _run_v3(state, llm, cfg) -> Dict[str, Any]:
    coin = state["company_of_interest"]
    trade_date = _parse_trade_date(state["trade_date"])
    horizon = int(cfg.get("sentiment_horizon_days", 14))
    anonymize = bool(cfg.get("sentiment_anonymize", True))
    skip_llm = bool(cfg.get("sentiment_v3_skip_llm", False))

    snap = build_snapshot(coin=coin, trade_date=trade_date, horizon_days=horizon)
    snapshot_md = snap.to_prompt_table()
    if anonymize:
        snapshot_md = anonymize_text(snapshot_md, coin=snap.asset)

    features = snap.to_modulator_features()

    if skip_llm:
        # Variant C: structured-only — no narrative LLM call. Emit an empty-content
        # AIMessage stub so downstream routing (which inspects last message's
        # tool_calls) doesn't trip on the human message left in state.
        from langchain_core.messages import AIMessage
        sentiment_report = (
            f"# Sentiment v3 (structured-only) — {snap.asset} {state['trade_date']}\n\n"
            f"{snapshot_md}\n"
        )
        stub = AIMessage(content=sentiment_report)
        return {
            "messages": [stub],
            "sentiment_report": sentiment_report,
            "sentiment_features": features,
        }

    instrument_context = build_instrument_context(
        coin if not anonymize else snap.asset
    )

    system_message = _V3_SYSTEM_MESSAGE.format(horizon_days=horizon)
    system_message = system_message + get_language_instruction()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an event analyst. {system_message}\n\n"
         "**SentimentSnapshot for {asset_label}:**\n\n{snapshot_md}\n\n"
         "{instrument_context}\n\nCurrent date: {current_date}"),
        MessagesPlaceholder(variable_name="messages"),
    ])
    asset_label = snap.asset if anonymize else coin
    prompt = prompt.partial(
        system_message=system_message,
        snapshot_md=snapshot_md,
        asset_label=asset_label,
        instrument_context=instrument_context,
        current_date=state["trade_date"],
    )

    result = llm.invoke(prompt.format(messages=state.get("messages", [])))
    body = getattr(result, "content", "") or ""

    sentiment_report = (
        f"# Sentiment v3 — {snap.asset} {state['trade_date']}\n\n"
        f"{snapshot_md}\n\n"
        f"## Narrow event analyst\n{body}"
    )

    return {
        "messages": [result],
        "sentiment_report": sentiment_report,
        "sentiment_features": features,
    }


def _run_legacy(state, llm, cfg) -> Dict[str, Any]:
    current_date = state["trade_date"]
    instrument_context = build_instrument_context(state["company_of_interest"])
    tools = [get_news, get_global_news, get_reddit_posts, get_crypto_google_news]
    system_message = _LEGACY_SYSTEM_MESSAGE + get_language_instruction()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful AI assistant collaborating with other assistants."
         " Use the provided tools to progress towards answering."
         " You have access to: {tool_names}.\n{system_message}\n\n"
         "{instrument_context}\n\nCurrent date: {current_date}."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(
        system_message=system_message,
        tool_names=", ".join([t.name for t in tools]),
        current_date=current_date,
        instrument_context=instrument_context,
    )
    chain = prompt | llm.bind_tools(tools)
    result = chain.invoke(state["messages"])
    report = "" if result.tool_calls else result.content
    return {
        "messages": [result],
        "sentiment_report": report,
        "sentiment_features": {},
    }
