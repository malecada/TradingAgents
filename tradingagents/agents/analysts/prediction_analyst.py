from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from typing import Annotated
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.dataflows.config import get_config


# Module-level trade_date used by prediction tools to prevent look-ahead
# bias during backtesting.  Set via set_prediction_trade_date() before
# each propagate() call; defaults to None (= use datetime.now()).
_prediction_trade_date: str | None = None


def set_prediction_trade_date(trade_date: str | None) -> None:
    """Set the trade_date that prediction tools will use as their data boundary."""
    global _prediction_trade_date
    _prediction_trade_date = trade_date


@tool
def get_rf_forecast(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')"],
    lookback_days: Annotated[int, "Number of historical days to use for training (default: 300)"] = 300,
) -> str:
    """Run Random Forest price prediction with 95% confidence interval.

    Returns the predicted next-day price, confidence interval bounds,
    and the direction (up/down) relative to the current price.
    """
    try:
        from tradingagents.models.rf_model import forecast_next
        result = forecast_next(symbol, lookback_days, trade_date=_prediction_trade_date)
        return result
    except ImportError:
        return "Random Forest model not available. Run 'python scripts/train_models.py' to train models first."
    except Exception as e:
        return f"RF forecast error: {e}"


@tool
def get_lgb_forecast(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum', 'binancecoin')"],
    lookback_days: Annotated[int, "Number of historical days to use for training (default: 730)"] = 730,
) -> str:
    """Run LightGBM multi-horizon pooled prediction for h=7 and h=14.

    Selects the configured training pool based on the target coin:
    - For BTC/ETH: trains on 2-coin pool (BTC+ETH)
    - For altcoins: trains on 2+1 pool (BTC+ETH+target)

    Returns h=7 and h=14 price predictions with directional consensus and
    a qualitative agreement label. Forecast skill remains unvalidated;
    historical directional-accuracy claims were withdrawn after the timing audit.
    """
    try:
        from tradingagents.models.lgb_model import forecast_next
        result = forecast_next(
            symbol, horizons=[7, 14], lookback_days=lookback_days,
            trade_date=_prediction_trade_date,
        )
        return result
    except ImportError:
        return "LightGBM model not available. Install lightgbm: pip install lightgbm"
    except Exception as e:
        return f"LGB forecast error: {e}"


@tool
def get_onchain_model_forecast(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')"],
    lookback_days: Annotated[int, "Number of historical days for training (default: 300)"] = 300,
) -> str:
    """Run Gradient Boosting prediction using ONLY on-chain features.

    This model provides context about the predictive power of on-chain
    metrics alone. It does NOT drive trading decisions — use it to
    understand how on-chain signals relate to price movement.
    """
    try:
        from tradingagents.models.onchain_model import forecast_next
        result = forecast_next(symbol, lookback_days, trade_date=_prediction_trade_date)
        return result
    except ImportError:
        return "On-chain model not available. Run 'python scripts/train_models.py' to train models first."
    except Exception as e:
        return f"On-chain model forecast error: {e}"


def create_prediction_analyst(llm):

    def prediction_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_lgb_forecast,
            get_rf_forecast,
            get_onchain_model_forecast,
        ]

        system_message = (
            """You are a quantitative prediction model analyst. Your role is to run and interpret machine learning price forecasts for cryptocurrencies.

**Available Models:**

1. **LightGBM Multi-Horizon**: Pooled gradient boosting trained on BTC+ETH (or BTC+ETH+target for altcoins). Produces h=7 and h=14 price forecasts. Historical directional-accuracy claims were withdrawn after a timing audit; corrected historical skill has not been validated.
2. **Random Forest**: Single-coin ensemble producing a next-day forecast and model-generated interval. Its relative superiority and interval calibration are unvalidated.
3. **On-Chain Gradient Boosting**: Uses on-chain features for descriptive context. Strict historical availability must be established by preserved vintages; a retrieval or availability error means the input is unavailable.

**Analysis Framework:**
1. Use the forecast tools relevant to the requested horizons and report their data boundary.
2. Describe agreement, disagreement, and predicted magnitude across horizons as model outputs. Agreement or a large predicted move does not establish measured accuracy or profitable trading performance.
3. Treat any HIGH/MEDIUM/LOW label returned by a tool as a qualitative heuristic, not a calibrated probability or demonstrated forecast skill.
4. Preserve missing-data, stale-input, and availability errors in the report. Never turn unavailable forecasts into directional evidence.
5. Do not cite withdrawn historical accuracy percentages or rank model reliability without valid supporting evaluation.

**Key Considerations:**
- The research program remains closed with zero validated strategies.
- A prediction deviating >50% from current price may indicate data/model issues.
- Software corrections alone do not validate these forecasts or justify a trading recommendation.

Write a detailed prediction report including:
- LGB h=7 and h=14 predictions with directional consensus
- Qualitative agreement label with its unvalidated status
- RF cross-check (if called)
- On-chain context (if called) — observational only
- Data availability and evaluation limitations"""
            + """ Append a Markdown table: Model | Horizon | Prediction | Direction | Confidence | Notes"""
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
                    "\n\n{instrument_context}"
                    "\n\nFor your reference, the current date is {current_date}.",
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
            "prediction_report": report,
        }

    return prediction_analyst_node
