# TradingAgents (Crypto-Adapted)

Multi-agent LLM framework for cryptocurrency trading decisions. Uses a trading firm hierarchy of specialized AI agents (analysts, researchers, risk managers) built on LangGraph + LangChain. Adapted from the original stock-focused TradingAgents (arxiv.org/abs/2412.20138) with crypto data sources, on-chain analytics, ML price forecasting, and Binance Futures execution.

## Architecture

```
Analysts (parallel data collection)
  → Bull/Bear Researchers (investment debate)
    → Research Manager (synthesis)
      → Trader (decision)
        → Aggressive/Conservative/Neutral Risk Analysts (risk debate)
          → Portfolio Manager (final rating: Buy/Overweight/Hold/Underweight/Sell)
```

### Agent Teams

**Crypto Analysts** (optional, any combination):
- **Market** — crypto OHLCV from Binance/CoinGecko + 150+ technical indicators via stockstats (RSI, MACD, Bollinger, ATR, etc.)
- **On-Chain** — funding rates (Binance Futures), TVL (DeFiLlama), gas prices + stablecoin supply (Web3/EVM)
- **Crypto Sentiment** — multi-source: Alpha Vantage crypto news, Reddit crypto subreddits, Google News, global macro news. LLM-centric analysis (no HuggingFace NLP model)
- **Prediction Model** — Random Forest + ARIMA(2,1,2) price forecasts with 95% confidence intervals, plus on-chain Gradient Boosting (observational)

**Stock Analysts** (legacy, still available when `asset_class="stock"`):
- Market, Social Media, News, Fundamentals

**Debate & Decision** (always active):
- **Researchers**: Bull argues for investment, Bear argues against — configurable rounds
- **Trader**: Synthesizes research into BUY/HOLD/SELL proposal
- **Risk Management**: Three-way debate (aggressive/conservative/neutral)
- **Portfolio Manager**: Final 5-level rating

Each analyst uses LangChain tool-calling to fetch data. BM25-based memory retrieves similar past situations. All debate/decision agents are crypto-aware and reference on-chain + prediction reports.

## Project Structure

```
tradingagents/                    # Core package
  agents/
    analysts/
      market_analyst.py           # Crypto OHLCV + technical indicators (switches tools by asset_class)
      onchain_analyst.py          # On-chain metrics: funding rates, TVL, gas, stablecoin supply
      crypto_sentiment_analyst.py # Multi-source sentiment: Alpha Vantage + Reddit + Google News
      prediction_analyst.py       # RF/ARIMA/GBR forecasts (tools defined inline, not via vendor routing)
      social_media_analyst.py     # Stock social media (legacy)
      news_analyst.py             # Stock news (legacy)
      fundamentals_analyst.py     # Stock fundamentals (legacy)
    researchers/                  # Bull and bear researchers (crypto-adapted prompts)
    managers/                     # Research manager, portfolio manager (crypto-adapted)
    risk_mgmt/                    # Aggressive, conservative, neutral debators (crypto-adapted)
    trader/                       # Trader agent (crypto-adapted)
    utils/
      agent_states.py             # TypedDict state: includes onchain_report, prediction_report
      agent_utils.py              # All tool imports (stock + crypto)
      memory.py                   # BM25-based FinancialSituationMemory
      core_stock_tools.py         # get_stock_data (stock mode)
      technical_indicators_tools.py
      fundamental_data_tools.py
      news_data_tools.py          # get_news, get_global_news, get_insider_transactions
      crypto_market_tools.py      # get_crypto_data, get_crypto_indicators
      onchain_tools.py            # get_funding_rates, get_tvl_metrics, get_stablecoin_metrics, get_gas_metrics, get_stablecoin_supply
      crypto_sentiment_tools.py   # get_reddit_posts, get_crypto_google_news
  graph/
    trading_graph.py              # TradingAgentsGraph orchestrator; clears session cache per propagate()
    setup.py                      # Graph node/edge construction (supports onchain, prediction, crypto_sentiment analysts)
    conditional_logic.py          # Routing: tool loops, debate continuation, analyst sequencing
    propagation.py                # State initialization (includes onchain_report, prediction_report)
    reflection.py                 # Post-trade learning (includes on-chain + prediction in situation memory)
    signal_processing.py          # Extract trading signal from portfolio manager output
  dataflows/
    interface.py                  # Vendor routing with 7 categories: core_stock, technical_indicators, fundamental_data, news_data, crypto_market_data, onchain_data, crypto_sentiment
    config.py                     # Runtime config with env var override on init
    coingecko_binance.py          # CoinGecko + Binance OHLCV with disk + session cache
    onchain.py                    # Web3 (gas, stablecoin supply), Binance Futures (funding rates), DeFiLlama (TVL, stablecoin mcap)
    crypto_sentiment.py           # Reddit scraper + Google News fetcher (raw text for LLM analysis)
    y_finance.py                  # Yahoo Finance (stock mode)
    alpha_vantage*.py             # Alpha Vantage (stock mode + crypto news)
    stockstats_utils.py           # Technical indicator computation (works on any OHLCV data)
  models/
    rf_model.py                   # Random Forest (1000 trees) with 95% CI; forecast_next() returns formatted string
    arima_model.py                # ARIMA(2,1,2) with exogenous features; forecast_next() returns formatted string
    onchain_model.py              # Gradient Boosting on on-chain features (observational only)
    model_utils.py                # data_transform, fetch_ohlcv_for_model, compute_metrics
    prediction.py                 # Prediction dataclass with to_report_string()
  backtesting/
    engine.py                     # run_backtest() with 5-level signal support, realistic costs (fees, slippage, short borrowing)
    strategies.py                 # FiveLevelSignal, ThresholdSignal, ModelConsensus; SignalLevel enum
  execution/
    exchange.py                   # Binance Futures wrapper (testnet default); place_market_order, place_stop_loss
    risk.py                       # 4-tier pre-trade checks: confidence gate, daily loss limit, max positions, position sizing
    runner.py                     # LiveRunner: propagate() → risk check → execute → journal log
    logger.py                     # SQLite trade journal: trades, portfolio_snapshots, daily_summary, analyst_reports
  llm_clients/
    factory.py                    # LLM client factory (OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama)
    base_client.py, openai_client.py, anthropic_client.py, google_client.py
    model_catalog.py, validators.py
  default_config.py               # DEFAULT_CONFIG + apply_env_overrides()
cli/
  main.py                         # Typer CLI with asset class selection (crypto/stock)
  utils.py                        # get_crypto_ticker, select_asset_class, select_analysts(asset_class)
  models.py                       # AnalystType enum (market, social, news, fundamentals, onchain, prediction, crypto_sentiment)
main.py                           # Example: crypto analysis of bitcoin
```

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run the interactive CLI
tradingagents
# or: python -m cli.main

# Run example crypto analysis
python main.py

# Run tests
python -m pytest tests/

# Train prediction models (required before prediction analyst can run)
python scripts/train_models.py --coin bitcoin --days 300

# Docker
docker compose run --rm tradingagents
```

## Python API Usage

### Crypto Analysis (primary use case)
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["asset_class"] = "crypto"
config["llm_provider"] = "openai"
config["deep_think_llm"] = "gpt-4o"
config["quick_think_llm"] = "gpt-4o-mini"

ta = TradingAgentsGraph(
    selected_analysts=["market", "onchain", "crypto_sentiment", "prediction"],
    debug=True,
    config=config,
)
final_state, signal = ta.propagate("bitcoin", "2025-01-15")
# signal: "BUY" | "OVERWEIGHT" | "HOLD" | "UNDERWEIGHT" | "SELL"

ta.reflect_and_remember(returns_losses=1000)
```

### Live Execution
```python
from tradingagents.execution.runner import LiveRunner

runner = LiveRunner(config={
    "asset_class": "crypto",
    "execution": {"live_mode": False, "dry_run": True},  # testnet + dry run
})
signal, result = runner.run_single("bitcoin")
```

### Backtesting
```python
from tradingagents.backtesting.engine import run_backtest
from tradingagents.backtesting.strategies import FiveLevelSignal

# signals: list of ("BUY"/"SELL"/etc.) strings per day
# prices: corresponding price series
result = run_backtest(signals, prices, strategy=FiveLevelSignal())
print(f"Sharpe: {result.metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result.metrics['max_drawdown']:.1%}")
```

### Stock Analysis (legacy)
```python
config["asset_class"] = "stock"
ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    config=config,
)
final_state, signal = ta.propagate("NVDA", "2025-01-15")
```

## Configuration

**Environment variables** (`.env` file, auto-loaded via python-dotenv):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`
- `ALPHA_VANTAGE_API_KEY` (optional, for Alpha Vantage crypto news)
- `WEB3_PROVIDER_URI_ETH`, `WEB3_PROVIDER_URI_BSC` (optional, for on-chain gas/stablecoin supply)
- `BINANCE_API_KEY`, `BINANCE_API_SECRET` (for live trading only, in `.env.trading`)

**Execution env var overrides** (for container/cloud deployment):
- `LIVE_MODE`, `DRY_RUN`, `MAX_POSITION_PCT`, `STOP_LOSS_PCT`, `MAX_DAILY_LOSS_PCT`, `MAX_OPEN_POSITIONS`, `MIN_CONFIDENCE`, `POSITION_SIZING`, `LEVERAGE`
- `TRADINGAGENTS_LLM_PROVIDER`, `TRADINGAGENTS_ASSET_CLASS`, `TRADINGAGENTS_DEEP_THINK_LLM`, `TRADINGAGENTS_QUICK_THINK_LLM`

**Config dict** (`tradingagents/default_config.py`):
- `asset_class`: `"crypto"` (default) or `"stock"`
- `llm_provider`: openai | anthropic | google | xai | openrouter | ollama
- `deep_think_llm` / `quick_think_llm`: Model IDs
- `max_debate_rounds` / `max_risk_discuss_rounds`: Debate iteration count (default: 1)
- `data_vendors`: Category-level vendor selection (7 categories)
- `web3_provider_eth`, `web3_provider_bsc`: Ethereum/BSC RPC URLs
- `use_onchain`: Enable on-chain data (default True, degrades gracefully)
- `prediction_models`: RF/ARIMA/GBR hyperparameters, checkpoint paths, lookback days
- `execution`: live_mode, dry_run, max_position_pct, stop_loss_pct, position_sizing, leverage

## Code Conventions

- Python 3.10+ with type hints; `Annotated[type, "description"]` for tool parameters
- `TypedDict` for LangGraph state schemas (see `agent_states.py`)
- snake_case for functions/variables, CamelCase for classes
- Google-style docstrings
- `@tool` decorator from `langchain_core.tools` for all tool functions
- Tools route through `route_to_vendor()` in `dataflows/interface.py` (except prediction tools which call model code directly)

## Key Patterns

- **Vendor routing**: `dataflows/interface.py` routes tool calls to vendor implementations with automatic fallback on rate limits
- **Asset class switching**: `config["asset_class"]` controls which tools Market Analyst binds (crypto vs stock) and which data vendors are used
- **Session cache**: `coingecko_binance.py` has in-memory `_session_cache` cleared per `propagate()` call to avoid redundant fetches within a single analysis run. Disk cache (CSV per symbol) persists across sessions.
- **Factory pattern**: `llm_clients/factory.py` creates provider-specific LLM clients
- **BM25 memory**: Lexical similarity retrieval of past trading situations; 5 separate memory instances
- **Tool-calling loops**: Analysts call tools via `bind_tools`, graph loops until no more tool calls
- **Env var overrides**: `apply_env_overrides()` in `default_config.py` overlays env vars on config at initialization
- **Prediction tools bypass vendor routing**: Defined inline in `prediction_analyst.py`, call model code directly (documented exception to the vendor pattern)
- **Graceful degradation**: On-chain data, Web3 metrics, Reddit all optional — system continues if any source is unavailable

## Gotchas

- **`asset_class` defaults to `"crypto"`** — set to `"stock"` explicitly for equity analysis
- **Prediction models require training** — run `scripts/train_models.py` before using the prediction analyst, or models will train on the fly (slow)
- **`LIVE_MODE` defaults to `False`** — testnet only; must be explicitly `True` for real money
- **`social` and `crypto_sentiment` analysts both write to `sentiment_report`** — they are mutually exclusive (don't select both)
- **On-chain Web3 metrics require RPC endpoints** — set `WEB3_PROVIDER_URI_ETH` / `WEB3_PROVIDER_URI_BSC` env vars; without them, gas/stablecoin supply tools return helpful error messages
- **On-chain model uses fallback features** — when called via prediction analyst, the GBR model receives OHLCV-derived features (not actual on-chain data), since the data pipeline doesn't merge on-chain metrics into the model DataFrame
- **CoinGecko free tier rate limits** — disk caching + backoff mitigates this; consider Pro API key for heavy usage
- **Reddit rate limiting** — exponential backoff + 30s delay on 429; Reddit data is additive, not required
- **Confidence parsed from LLM output** — regex-based extraction of confidence level from portfolio manager text; can be brittle if output format drifts
- **Max recursion limit** — with 4 crypto analysts + debates, the graph has many nodes; default `max_recur_limit=100` should suffice but increase if hitting limits

## Results Output

- **State logs**: `results/{ticker}/TradingAgentsStrategy_logs/full_states_log_{date}.json` (includes all analyst reports, debate state, final decision)
- **Trade journal**: `data/trade_journal.db` (SQLite — trades, portfolio snapshots, daily summaries, full analyst reports)
- **Model checkpoints**: `data/checkpoints/` (RF, ARIMA, GBR joblib/pkl files)
