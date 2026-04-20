import functools

from tradingagents.agents.utils.agent_utils import build_instrument_context


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        onchain_report = state.get("onchain_report", "")
        prediction_report = state.get("prediction_report", "")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{onchain_report}\n\n{prediction_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. {instrument_context} This plan incorporates insights from current technical market trends, macroeconomic indicators, social media sentiment, on-chain analytics, and prediction model forecasts. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nOn-chain analysis report: {onchain_report}\n\nPrediction model report: {prediction_report}\n\nLeverage these insights, including prediction model outputs and confidence intervals, to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are a cryptocurrency trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold.

When evaluating the prediction and market reports, prioritize these signals (in order):

1. **LightGBM horizon consensus (PRIMARY SIGNAL)**: The prediction report includes h=7 and h=14 LGB forecasts.
   - If h=7 AND h=14 agree on direction AND the h=14 predicted move is ≥ 2% → HIGH confidence.
   - If only h=14 has a clear directional signal → MEDIUM confidence. Trust h=14 (85% historical DirAcc for BTC) over short-term signals.
   - If h=7 and h=14 disagree → LOW confidence, prefer HOLD.

2. **SMA30 trend alignment (POSITION SIZING CONTEXT)**: The market report's "Trend Filter" section tells you whether price is above or below the 30-day SMA.
   - Longs aligned with the bullish regime (price > SMA30) carry higher expected return.
   - Shorts aligned with the bearish regime (price < SMA30) carry higher expected return.
   - A trade AGAINST the SMA30 trend needs a stronger justification (e.g., extreme LGB consensus, clear reversal pattern).

3. **Cross-signal confirmation**: When LGB and Random Forest agree on direction, confidence rises. On-chain Gradient Boosting is observational only — do NOT use it as primary evidence.

**Confidence reporting**: State your confidence level explicitly as HIGH, MEDIUM, or LOW alongside your decision. Map confidence to recommendation strength:
- HIGH + trend-aligned → strong BUY or SELL
- MEDIUM → cautious BUY or SELL (or HOLD if risk is elevated)
- LOW → HOLD

End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Apply lessons from past decisions to strengthen your analysis. Here are reflections from similar situations you traded in and the lessons learned: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
