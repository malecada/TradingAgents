from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_funding_rates,
    get_tvl_metrics,
    get_stablecoin_metrics,
    get_gas_metrics,
    get_stablecoin_supply,
    get_language_instruction,
)
from tradingagents.dataflows.config import get_config


def create_onchain_analyst(llm):

    def onchain_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])
        config = get_config()

        # Core tools (always available — Binance Futures + DeFiLlama)
        tools = [
            get_funding_rates,
            get_tvl_metrics,
            get_stablecoin_metrics,
        ]

        # Only include Web3 tools when a provider is actually configured
        has_web3 = bool(
            config.get("web3_provider_eth") or config.get("web3_provider_bsc")
        )
        if has_web3:
            tools.extend([get_gas_metrics, get_stablecoin_supply])

        web3_section = ""
        if has_web3:
            web3_section = """
**Network Metrics (Web3):**
- Gas prices: Network demand and congestion. High gas = heavy usage.
- Transaction counts: Network activity and adoption trends.
- Stablecoin supply on-chain: Capital availability on specific chains.
You MUST call get_gas_metrics and get_stablecoin_supply for both 'ethereum' and 'bsc' chains.
"""
        else:
            web3_section = """
**Network Metrics:** Web3 RPC endpoints are not configured, so gas and on-chain stablecoin supply data are unavailable for this run.
"""

        system_message = (
            f"""You are a blockchain and on-chain data analyst specializing in cryptocurrency markets. Your role is to analyze on-chain metrics that reveal the underlying health and activity of blockchain networks and derivatives markets.

Use the available tools to gather and analyze the following categories of on-chain data:

**Derivatives Metrics (Binance Futures):**
- Funding rates: Indicate market leverage and directional bias. Positive = longs pay shorts (bullish bias). Extreme rates (>0.1% or <-0.1%) signal overleveraged positions and potential liquidation cascades.

**DeFi Metrics (DeFiLlama):**
- Total Value Locked (TVL): Measures capital deposited in DeFi protocols. Rising TVL = growing confidence and capital inflow. Falling TVL = capital flight.
- Stablecoin market cap: Indicates available liquidity. Growing supply = more dry powder for crypto purchases.
{web3_section}
**Analysis Framework:**
1. Start by fetching funding rates for the asset of interest
2. Get TVL metrics (both total and chain-specific if relevant)
3. Check stablecoin market cap for liquidity assessment
{"4. Get gas metrics and on-chain stablecoin supply for ethereum and bsc" if has_web3 else ""}
{"5" if has_web3 else "4"}. Synthesize findings into a coherent on-chain health assessment

You MUST call ALL available tools. Do not skip any tool.

Write a comprehensive report covering:
- Current market leverage conditions (funding rate analysis)
- DeFi capital flow trends (TVL momentum)
- Liquidity environment (stablecoin metrics)
{"- Network activity indicators (gas prices, tx counts)" if has_web3 else ""}
- Key risk signals from on-chain data
- How on-chain metrics support or contradict price action"""
            + """ Append a Markdown summary table at the end with columns: Metric | Current Value | Trend | Signal (Bullish/Bearish/Neutral)."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "onchain_report": report,
        }

    return onchain_analyst_node
