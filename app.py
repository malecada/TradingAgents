"""Streamlit UI for TradingAgents crypto analysis.

Run with: `streamlit run app.py`
"""

from __future__ import annotations

import datetime as _dt
import re
import traceback

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from tradingagents.default_config import DEFAULT_CONFIG, apply_env_overrides
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.llm_clients.factory import create_llm_client

load_dotenv()

ANALYST_OPTIONS = ["market", "onchain", "crypto_sentiment", "prediction"]
PROVIDER_OPTIONS = ["openai", "anthropic", "google", "xai", "openrouter", "ollama"]

SIGNAL_COLORS = {
    "BUY": "#1b9e4b",
    "OVERWEIGHT": "#5fa85f",
    "HOLD": "#d9822b",
    "UNDERWEIGHT": "#c0504d",
    "SELL": "#b02a25",
}


def resolve_coingecko_id(raw: str, provider: str, model: str, base_url: str | None) -> str:
    """Map a free-text coin name/ticker to a CoinGecko coin ID via a one-shot LLM call.

    Results are cached in `st.session_state` so repeated runs on the same
    input don't re-hit the LLM.
    """
    raw = raw.strip()
    if not raw:
        return raw

    cache = st.session_state.setdefault("_coin_id_cache", {})
    key = raw.lower()
    if key in cache:
        return cache[key]

    # Fast path: already looks like a lowercase coingecko id (hyphen + alpha)
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", raw) and raw == key:
        cache[key] = raw
        return raw

    client = create_llm_client(provider=provider, model=model, base_url=base_url)
    llm = client.get_llm()
    prompt = (
        "Return ONLY the CoinGecko coin id for the following cryptocurrency. "
        "Respond with the id in lowercase, no quotes, no extra text. "
        "Examples: Bitcoin -> bitcoin, BTC -> bitcoin, Ether -> ethereum, "
        "Solana -> solana, DOGE -> dogecoin.\n\n"
        f"Input: {raw}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    coin_id = content.strip().splitlines()[0].strip().strip("`'\"").lower()
    coin_id = re.sub(r"[^a-z0-9-]", "", coin_id)
    if not coin_id:
        coin_id = key
    cache[key] = coin_id
    return coin_id


def build_config(provider: str, deep_model: str, quick_model: str, debate_rounds: int) -> dict:
    config = DEFAULT_CONFIG.copy()
    apply_env_overrides(config)
    config["asset_class"] = "crypto"
    config["llm_provider"] = provider
    config["deep_think_llm"] = deep_model
    config["quick_think_llm"] = quick_model
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds
    return config


def run_analysis(coin_id: str, trade_date: str, analysts: list[str], config: dict):
    ta = TradingAgentsGraph(
        selected_analysts=analysts,
        debug=False,
        config=config,
    )
    return ta.propagate(coin_id, trade_date)


def signal_badge(signal: str) -> str:
    color = SIGNAL_COLORS.get(signal.upper(), "#555")
    return (
        f'<div style="background:{color};color:white;padding:18px 24px;'
        f'border-radius:12px;text-align:center;font-size:42px;'
        f'font-weight:700;letter-spacing:2px;">{signal.upper()}</div>'
    )


def extract_price(market_report: str) -> str | None:
    """Best-effort extraction of a current price from the market analyst report."""
    if not market_report:
        return None
    match = re.search(
        r"(?:current\s+price|price\s+is|latest\s+close)[^\d$]*\$?\s*([\d,]+(?:\.\d+)?)",
        market_report,
        re.IGNORECASE,
    )
    if match:
        return f"${match.group(1)}"
    return None


def extract_confidence(decision_text: str) -> str | None:
    if not decision_text:
        return None
    match = re.search(r"confidence[^a-z]*?(high|medium|low)", decision_text, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    return None


def render_header(signal: str, final_state: dict) -> None:
    st.markdown(signal_badge(signal), unsafe_allow_html=True)
    st.write("")
    cols = st.columns(3)
    cols[0].metric("Asset", final_state.get("company_of_interest", "—"))
    cols[1].metric("Trade date", final_state.get("trade_date", "—"))
    confidence = extract_confidence(final_state.get("final_trade_decision", "")) or "—"
    cols[2].metric("Confidence", confidence)
    price = extract_price(final_state.get("market_report", ""))
    if price:
        st.caption(f"Reported current price: **{price}**")


def _markdown_or_empty(text: str, empty_msg: str = "_Not generated in this run._") -> None:
    st.markdown(text if text else empty_msg)


def render_tabs(final_state: dict) -> None:
    tabs = st.tabs(
        [
            "Final Decision",
            "Trader Plan",
            "Analyst Reports",
            "Investment Debate",
            "Risk Debate",
            "Raw State",
        ]
    )

    with tabs[0]:
        st.subheader("Portfolio Manager — final call")
        _markdown_or_empty(final_state.get("final_trade_decision", ""))

    with tabs[1]:
        st.subheader("Trader Investment Plan")
        _markdown_or_empty(final_state.get("trader_investment_plan", ""))
        research_plan = final_state.get("investment_plan", "")
        if research_plan:
            with st.expander("Research Manager synthesis"):
                st.markdown(research_plan)

    with tabs[2]:
        st.subheader("Analyst Reports")
        report_map = [
            ("Market Analyst", "market_report"),
            ("On-Chain Analyst", "onchain_report"),
            ("Sentiment Analyst", "sentiment_report"),
            ("Prediction Models (RF / ARIMA / On-chain GBR)", "prediction_report"),
            ("News Analyst", "news_report"),
            ("Fundamentals", "fundamentals_report"),
        ]
        any_rendered = False
        for title, key in report_map:
            content = final_state.get(key, "")
            if content:
                any_rendered = True
                with st.expander(title, expanded=(key == "prediction_report")):
                    st.markdown(content)
        if not any_rendered:
            st.info("No analyst reports in the final state.")

    with tabs[3]:
        st.subheader("Bull vs Bear — Investment Debate")
        debate = final_state.get("investment_debate_state", {}) or {}
        col_bull, col_bear = st.columns(2)
        with col_bull:
            st.markdown("#### 🐂 Bull")
            _markdown_or_empty(debate.get("bull_history", ""))
        with col_bear:
            st.markdown("#### 🐻 Bear")
            _markdown_or_empty(debate.get("bear_history", ""))
        judge = debate.get("judge_decision", "")
        if judge:
            st.markdown("#### Research Manager verdict")
            st.markdown(judge)

    with tabs[4]:
        st.subheader("Risk Management Debate")
        risk = final_state.get("risk_debate_state", {}) or {}
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🔥 Aggressive")
            _markdown_or_empty(risk.get("aggressive_history", ""))
        with c2:
            st.markdown("#### 🛡 Conservative")
            _markdown_or_empty(risk.get("conservative_history", ""))
        with c3:
            st.markdown("#### ⚖️ Neutral")
            _markdown_or_empty(risk.get("neutral_history", ""))
        judge = risk.get("judge_decision", "")
        if judge:
            st.markdown("#### Judge verdict")
            st.markdown(judge)

    with tabs[5]:
        st.subheader("Raw final state (debug)")
        # Messages can be large LangChain objects — drop them from the JSON view.
        view = {k: v for k, v in final_state.items() if k != "messages"}
        st.json(view, expanded=False)


def main() -> None:
    st.set_page_config(page_title="TradingAgents — Crypto", layout="wide")
    st.title("TradingAgents — Crypto Analysis")
    st.caption("Multi-agent LLM analysis: analysts → bull/bear debate → trader → risk debate → final rating.")

    with st.sidebar:
        st.header("Run configuration")
        coin_input = st.text_input("Coin name or ticker", value="bitcoin")
        trade_date = st.date_input("Trade date", value=_dt.date.today())
        analysts = st.multiselect(
            "Analysts",
            options=ANALYST_OPTIONS,
            default=ANALYST_OPTIONS,
            help="Choose which analyst teams run in parallel. 'crypto_sentiment' and stock 'social' are mutually exclusive.",
        )
        st.divider()
        provider = st.selectbox(
            "LLM provider",
            options=PROVIDER_OPTIONS,
            index=PROVIDER_OPTIONS.index(DEFAULT_CONFIG["llm_provider"])
            if DEFAULT_CONFIG["llm_provider"] in PROVIDER_OPTIONS
            else 0,
        )
        deep_model = st.text_input("Deep-think model", value=DEFAULT_CONFIG["deep_think_llm"])
        quick_model = st.text_input("Quick-think model", value=DEFAULT_CONFIG["quick_think_llm"])
        debate_rounds = st.number_input("Debate rounds", min_value=1, max_value=5, value=1, step=1)
        run_clicked = st.button("Analyze", type="primary", use_container_width=True)

    if run_clicked:
        if not coin_input.strip():
            st.error("Please enter a coin name or ticker.")
            return
        if not analysts:
            st.error("Select at least one analyst.")
            return

        config = build_config(provider, deep_model, quick_model, int(debate_rounds))
        base_url = config.get("backend_url")

        try:
            with st.spinner("Resolving coin id…"):
                coin_id = resolve_coingecko_id(coin_input, provider, quick_model, base_url)
            st.info(f"Resolved **{coin_input}** → CoinGecko id `{coin_id}`")

            with st.spinner("Running multi-agent analysis — this may take several minutes…"):
                final_state, signal = run_analysis(
                    coin_id, trade_date.strftime("%Y-%m-%d"), analysts, config
                )
            st.session_state["last_run"] = {
                "final_state": final_state,
                "signal": signal,
                "coin_id": coin_id,
            }
        except Exception as exc:  # noqa: BLE001 — boundary
            st.error(f"Analysis failed: {exc}")
            with st.expander("Traceback"):
                st.code(traceback.format_exc())
            return

    last_run = st.session_state.get("last_run")
    if last_run:
        render_header(last_run["signal"], last_run["final_state"])
        st.divider()
        render_tabs(last_run["final_state"])
    else:
        st.info("Configure a run in the sidebar and click **Analyze** to start.")


if __name__ == "__main__":
    main()
