from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from typing import Annotated
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.dataflows.config import get_config


# Prediction tools are defined inline here because they call the model
# code directly rather than routing through the vendor system.

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
        result = forecast_next(symbol, lookback_days)
        return result
    except ImportError:
        return "Random Forest model not available. Run 'python scripts/train_models.py' to train models first."
    except Exception as e:
        return f"RF forecast error: {e}"


@tool
def get_arima_forecast(
    symbol: Annotated[str, "CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')"],
    lookback_days: Annotated[int, "Number of historical days to use for training (default: 300)"] = 300,
) -> str:
    """Run ARIMA(2,1,2) time series prediction with confidence interval.

    Returns the predicted next-day price and confidence bounds.
    ARIMA captures linear time-series patterns and trend momentum.
    """
    try:
        from tradingagents.models.arima_model import forecast_next
        result = forecast_next(symbol, lookback_days)
        return result
    except ImportError:
        return "ARIMA model not available. Run 'python scripts/train_models.py' to train models first."
    except Exception as e:
        return f"ARIMA forecast error: {e}"


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
        result = forecast_next(symbol, lookback_days)
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
            get_rf_forecast,
            get_arima_forecast,
            get_onchain_model_forecast,
        ]

        system_message = (
            """You are a quantitative prediction model analyst. Your role is to run and interpret machine learning price forecasts for cryptocurrencies.

**Available Models:**

1. **Random Forest (RF)**: An ensemble of 1000 decision trees. Uses price lags, macro indicators, and on-chain features. Provides 95% confidence intervals from individual tree predictions.

2. **ARIMA(2,1,2)**: Autoregressive Integrated Moving Average time series model. Captures linear trend and momentum with exogenous variables. Good at detecting mean-reversion and trend continuation.

3. **On-Chain Gradient Boosting**: Uses ONLY on-chain features (funding rate, TVL, stablecoin supply). Provides context about on-chain signal strength — does NOT drive trading decisions.

**Analysis Framework:**
1. Run ALL three models for the asset
2. Compare predictions between RF and ARIMA:
   - Do they agree on direction (up/down)? Agreement = higher confidence
   - How wide are the confidence intervals? Narrow = more certain
   - Where do the confidence intervals overlap?
3. Note the on-chain model prediction for context
4. Assess overall model confidence:
   - HIGH: Both RF and ARIMA agree on direction, confidence intervals overlap
   - MEDIUM: Same direction but different confidence intervals
   - LOW: Models disagree on direction

**Key Considerations:**
- Models use pre-trained checkpoints — note when they were last trained
- A prediction deviating >50% from current price may indicate model staleness
- Confidence interval width reflects prediction uncertainty
- On-chain model is observational only — never recommend trades based on it alone

Write a detailed prediction report including:
- Individual model predictions with confidence intervals
- Model agreement/disagreement analysis
- Overall prediction confidence assessment
- Key features driving each model's prediction (if available)
- Any caveats about model reliability"""
            + """ Append a Markdown table: Model | Prediction | Lower CI | Upper CI | Direction | Notes"""
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
            "prediction_report": report,
        }

    return prediction_analyst_node
