# Market Analyst v2 — Asset-Agnostic "Do No Harm" Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current free-text market analyst with a structured-snapshot + narrow-LLM analyst that emits a Pydantic-typed signal whose effective weight collapses to ~0 when the analyst is uncertain on a given coin, so the analyst either helps a coin or contributes ~0 to it (no per-coin disable required).

**Architecture:** Mirror the existing sentiment-v3 pattern in `tradingagents/sentiment/` and `crypto_sentiment_analyst.py`. A deterministic module (`tradingagents/market/`) computes a 12-indicator whitelist, a regime tag (ADX/ATR-percentile), a category vote across {Trend, Momentum, Volatility, Volume}, a `conflict_score`, and an asymmetric default direction (FLAT under conflict; SHORT requires ≥3 confirming categories, LONG ≥2). The analyst LLM receives this anonymized snapshot in a third-person ("Andrew") persona and emits a Pydantic-validated `{direction, conviction, conflict_score, indicators_used, dissenting_indicators}`. The modulator multiplies that conviction by a per-coin isotonic calibrator (re-using `tradingagents/strategies/calibration.py`) so endogenous per-coin weight emerges from data, not code. The modulator integrates the result as `market_features` exactly the way it already consumes `sentiment_features`. Validated via a 4-variant A/B harness over BTC/ETH/BNB/SOL.

**Tech Stack:** Python 3.10 (runtime tolerant of 3.9 via `from __future__ import annotations`), pydantic v1/v2 compatible BaseModel, langchain-core ChatPromptTemplate, scikit-learn IsotonicRegression, stockstats (existing indicator backend), pytest with `tests/conftest.py` patterns, the existing `scripts/run_sentiment_v3_ab.py` harness as a template.

---

## Branching & Working Directory

All work happens in the existing worktree at
`/home/malecada/master_thesis/TradingAgents/.worktrees/hybrid-modulator`
on a new branch `feature/market-analyst-v2`, forked off
`feature/sentiment-analyst-v3` (commit `f910855` at plan-write time).

```bash
cd /home/malecada/master_thesis/TradingAgents/.worktrees/hybrid-modulator
git checkout -b feature/market-analyst-v2
```

## File Structure

**New files**

- `tradingagents/market/__init__.py` — re-exports `build_market_snapshot` and `MarketSnapshot`
- `tradingagents/market/snapshot.py` — `MarketSnapshot` Pydantic schema + `MarketAnalystOutput` schema
- `tradingagents/market/indicators.py` — deterministic computation of the 12-name whitelist
- `tradingagents/market/regime_tag.py` — cheap deterministic ADX/ATR-percentile/30-day-return regime tag
- `tradingagents/market/category_vote.py` — pure-function category aggregation + conflict_score + asymmetric direction default
- `tradingagents/market/build_snapshot.py` — orchestrator: indicators + regime + category vote → `MarketSnapshot`
- `tests/market/__init__.py` — empty
- `tests/market/test_snapshot.py`
- `tests/market/test_indicators.py`
- `tests/market/test_regime_tag.py`
- `tests/market/test_category_vote.py`
- `tests/market/test_build_snapshot.py`
- `tests/agents/test_market_analyst_v2.py`
- `tests/strategies/test_market_calibration.py`
- `tests/agents/test_modulator_market_features.py`
- `scripts/run_market_v2_ab.py` — 4-variant A/B validator (analog of `run_sentiment_v3_ab.py`)
- `scripts/fit_market_calibrator.py` — fits `IsotonicCalibrator` per coin from logged conviction-vs-realised pairs
- `docs/superpowers/specs/2026-05-26-market-analyst-v2-design.md` — mirror of this plan's spec section for the thesis record

**Modified files**

- `tradingagents/agents/analysts/market_analyst.py` — add v2 branch under `market_mode == "v2"`, preserve legacy as default
- `tradingagents/agents/utils/agent_states.py` — add `market_features: Annotated[dict, ...]`
- `tradingagents/agents/modulator.py` — include `market_features` in prompt (mirror `sentiment_features`)
- `tradingagents/graph/propagation.py` — initialize `market_features: {}` in state
- `tradingagents/default_config.py` — add `market_mode`, `market_anonymize`, `market_skip_llm`, `market_horizon_days`, plus env-var hooks
- `scripts/generate_hybrid_signals.py` — add `--market-mode`, `--market-skip-llm`, `--market-anonymize` CLI flags

**Boundary discipline**: `tradingagents/market/*` must NOT import from `agents/`, `strategies/`, or `graph/`. It is a pure deterministic module that the analyst node calls. The analyst node owns LLM and config concerns.

---

## Task 1: Pydantic Schemas for the v2 Snapshot

**Files:**
- Create: `tradingagents/market/snapshot.py`
- Test: `tests/market/test_snapshot.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/market/test_snapshot.py
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tradingagents.market.snapshot import (
    CategoryDirection,
    DirectionLabel,
    IndicatorReading,
    MarketAnalystOutput,
    MarketCategory,
    MarketSnapshot,
    RegimeLabel,
)


def _now():
    return datetime(2026, 1, 15, tzinfo=timezone.utc)


def test_market_snapshot_minimum_valid():
    snap = MarketSnapshot(
        asset="BTC",
        as_of_ts=_now(),
        trade_date=_now(),
        horizon_days=7,
        regime="TREND_UP",
        regime_confidence=0.7,
        adx=28.0,
        atr_percentile=0.6,
        return_30d=0.05,
        indicators=[
            IndicatorReading(name="close_30_sma", value=20000.0,
                             category="trend", direction=1),
            IndicatorReading(name="rsi", value=62.0,
                             category="momentum", direction=1),
            IndicatorReading(name="atr", value=900.0,
                             category="volatility", direction=0),
            IndicatorReading(name="vwma", value=20100.0,
                             category="volume", direction=1),
        ],
        category_votes={
            "trend": 1, "momentum": 1, "volatility": 0, "volume": 1,
        },
        conflict_score=0.25,
        default_direction="LONG",
    )
    assert snap.asset == "BTC"
    assert snap.conflict_score == 0.25
    assert snap.default_direction == "LONG"


def test_market_snapshot_horizon_bounds_enforced():
    with pytest.raises(ValidationError):
        MarketSnapshot(
            asset="BTC", as_of_ts=_now(), trade_date=_now(),
            horizon_days=0,  # < 1
            regime="RANGE", regime_confidence=0.5,
            adx=10.0, atr_percentile=0.5, return_30d=0.0,
            indicators=[], category_votes={},
            conflict_score=0.0, default_direction="FLAT",
        )


def test_market_snapshot_conflict_score_bounds_enforced():
    with pytest.raises(ValidationError):
        MarketSnapshot(
            asset="BTC", as_of_ts=_now(), trade_date=_now(),
            horizon_days=7,
            regime="RANGE", regime_confidence=0.5,
            adx=10.0, atr_percentile=0.5, return_30d=0.0,
            indicators=[], category_votes={},
            conflict_score=1.5,  # > 1
            default_direction="FLAT",
        )


def test_market_analyst_output_min_valid():
    out = MarketAnalystOutput(
        direction="LONG",
        conviction=0.6,
        conflict_score=0.2,
        indicators_used=["close_30_sma", "rsi", "atr"],
        dissenting_indicators=[],
        rationale="Trend aligned with momentum; volatility neutral.",
    )
    assert out.direction == "LONG"
    assert 0.0 <= out.conviction <= 1.0


def test_market_analyst_output_dissenting_must_be_subset_of_used():
    with pytest.raises(ValidationError):
        MarketAnalystOutput(
            direction="LONG", conviction=0.5, conflict_score=0.4,
            indicators_used=["rsi", "macd"],
            dissenting_indicators=["macd", "boll"],  # boll not in used
            rationale="x",
        )


def test_market_snapshot_to_prompt_table_includes_all_blocks():
    snap = MarketSnapshot(
        asset="ASSET_A", as_of_ts=_now(), trade_date=_now(),
        horizon_days=7,
        regime="TREND_UP", regime_confidence=0.7,
        adx=28.0, atr_percentile=0.6, return_30d=0.05,
        indicators=[
            IndicatorReading(name="close_30_sma", value=20000.0,
                             category="trend", direction=1),
        ],
        category_votes={"trend": 1, "momentum": 0, "volatility": 0, "volume": 0},
        conflict_score=0.25, default_direction="LONG",
    )
    md = snap.to_prompt_table()
    assert "Regime: TREND_UP" in md
    assert "conflict_score" in md.lower()
    assert "category" in md.lower() or "Trend:" in md
    assert "ASSET_A" in md


def test_market_snapshot_to_modulator_features_keys():
    snap = MarketSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(),
        horizon_days=7,
        regime="RANGE", regime_confidence=0.6,
        adx=15.0, atr_percentile=0.4, return_30d=0.01,
        indicators=[],
        category_votes={"trend": 0, "momentum": 1, "volatility": 0, "volume": -1},
        conflict_score=0.5, default_direction="FLAT",
    )
    feats = snap.to_modulator_features()
    assert set(feats.keys()) >= {
        "market_regime", "market_regime_confidence",
        "market_adx", "market_atr_percentile", "market_return_30d",
        "market_conflict_score", "market_default_direction",
        "market_cat_trend", "market_cat_momentum",
        "market_cat_volatility", "market_cat_volume",
    }
    assert feats["market_default_direction"] == "FLAT"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/market/test_snapshot.py -x -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.market'`

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/market/snapshot.py
"""Pydantic schemas for the v2 market analyst pipeline.

Mirrors the v3 sentiment pipeline at tradingagents/sentiment/snapshot.py:
a deterministic structured snapshot is the LLM's only input on indicator
content, and the LLM emits a structured directional output. The modulator
consumes ``to_modulator_features()`` exactly the way it consumes the
sentiment features dict today.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field, conint, confloat, validator

RegimeLabel = Literal["TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOL"]
DirectionLabel = Literal["LONG", "SHORT", "FLAT"]
MarketCategory = Literal["trend", "momentum", "volatility", "volume"]
CategoryDirection = conint(ge=-1, le=1)


class IndicatorReading(BaseModel):
    name: str
    value: float
    category: MarketCategory
    direction: CategoryDirection  # -1 bearish, 0 neutral, +1 bullish


class MarketSnapshot(BaseModel):
    asset: str = Field(min_length=1)
    as_of_ts: datetime
    trade_date: datetime
    horizon_days: conint(ge=1, le=30)

    regime: RegimeLabel
    regime_confidence: confloat(ge=0.0, le=1.0)
    adx: float
    atr_percentile: confloat(ge=0.0, le=1.0)
    return_30d: float

    indicators: List[IndicatorReading]
    category_votes: dict  # {"trend": -1|0|+1, ...}
    conflict_score: confloat(ge=0.0, le=1.0)
    default_direction: DirectionLabel

    def to_prompt_table(self) -> str:
        cv = self.category_votes
        ind_rows = "\n".join(
            f"| {r.name} | {r.category} | {r.value:.6g} | {r.direction:+d} |"
            for r in self.indicators
        ) or "| (none) | | | |"
        return (
            f"### MarketSnapshot for {self.asset} @ {self.trade_date.date()}\n\n"
            f"Regime: {self.regime} (confidence {self.regime_confidence:.2f})\n"
            f"ADX: {self.adx:.2f} | ATR pct: {self.atr_percentile:.2f} | "
            f"30d return: {self.return_30d:+.2%}\n\n"
            f"Category votes — Trend: {cv.get('trend', 0):+d}, "
            f"Momentum: {cv.get('momentum', 0):+d}, "
            f"Volatility: {cv.get('volatility', 0):+d}, "
            f"Volume: {cv.get('volume', 0):+d}\n"
            f"conflict_score: {self.conflict_score:.2f} | "
            f"default_direction: {self.default_direction}\n\n"
            f"| indicator | category | value | direction |\n"
            f"|---|---|---|---|\n{ind_rows}\n"
        )

    def to_modulator_features(self) -> dict:
        cv = self.category_votes
        return {
            "market_regime": self.regime,
            "market_regime_confidence": self.regime_confidence,
            "market_adx": self.adx,
            "market_atr_percentile": self.atr_percentile,
            "market_return_30d": self.return_30d,
            "market_conflict_score": self.conflict_score,
            "market_default_direction": self.default_direction,
            "market_cat_trend": int(cv.get("trend", 0)),
            "market_cat_momentum": int(cv.get("momentum", 0)),
            "market_cat_volatility": int(cv.get("volatility", 0)),
            "market_cat_volume": int(cv.get("volume", 0)),
        }


class MarketAnalystOutput(BaseModel):
    direction: DirectionLabel
    conviction: confloat(ge=0.0, le=1.0)
    conflict_score: confloat(ge=0.0, le=1.0)
    indicators_used: List[str]
    dissenting_indicators: List[str]
    rationale: str = Field(min_length=1)

    @validator("dissenting_indicators")
    def dissent_subset_of_used(cls, v, values):  # noqa: N805
        used = set(values.get("indicators_used") or [])
        bad = [x for x in v if x not in used]
        if bad:
            raise ValueError(
                f"dissenting_indicators must be subset of indicators_used; "
                f"unknown: {bad}"
            )
        return v
```

```python
# tradingagents/market/__init__.py
from tradingagents.market.snapshot import (
    DirectionLabel,
    IndicatorReading,
    MarketAnalystOutput,
    MarketCategory,
    MarketSnapshot,
    RegimeLabel,
)

__all__ = [
    "DirectionLabel",
    "IndicatorReading",
    "MarketAnalystOutput",
    "MarketCategory",
    "MarketSnapshot",
    "RegimeLabel",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/market/test_snapshot.py -x -q`
Expected: PASS, 7 tests passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/market/__init__.py tradingagents/market/snapshot.py \
        tests/market/__init__.py tests/market/test_snapshot.py
git commit -m "feat(market-v2): Pydantic schemas for MarketSnapshot + MarketAnalystOutput"
```

---

## Task 2: Deterministic Indicator Computation (12-name whitelist)

**Files:**
- Create: `tradingagents/market/indicators.py`
- Test: `tests/market/test_indicators.py`

The 12-name whitelist comes verbatim from upstream TradingAgents `market_analyst.py`:
`close_30_sma`, `close_50_sma`, `close_200_sma`, `close_10_ema`, `macd`, `macds`, `macdh`, `rsi`, `boll`, `boll_ub`, `boll_lb`, `atr`, `vwma`. (The current fork adds `close_30_sma` and `macdh`; we keep both for parity with the existing prompt.)

Per-indicator direction rules (deterministic, no LLM):

| Indicator | Direction +1 if | Direction -1 if | Category |
|---|---|---|---|
| close_30_sma | close > sma | close < sma | trend |
| close_50_sma | close > sma | close < sma | trend |
| close_200_sma | close > sma | close < sma | trend |
| close_10_ema | close > ema | close < ema | trend |
| macd | macd > 0 | macd < 0 | momentum |
| macds | macd > macds | macd < macds | momentum |
| macdh | macdh > 0 | macdh < 0 | momentum |
| rsi | rsi > 55 | rsi < 45 | momentum |
| boll | close > boll | close < boll | volatility |
| boll_ub | close > boll_ub | close < boll_lb | volatility |
| boll_lb | close < boll_lb | close > boll_ub | volatility |
| atr | atr_pct < 0.4 | atr_pct > 0.8 | volatility (risk-on/off) |
| vwma | close > vwma | close < vwma | volume |

Where `atr_pct` is the 90-day rolling percentile of ATR. The 55/45 RSI thresholds are deliberately tighter than 70/30 to avoid no-signal during normal regimes — this matches the "asymmetric default" philosophy (we want most readings to register a direction so conflict_score is informative).

- [ ] **Step 1: Write the failing tests**

```python
# tests/market/test_indicators.py
import numpy as np
import pandas as pd

from tradingagents.market.indicators import (
    INDICATOR_CATEGORY,
    INDICATOR_WHITELIST,
    compute_indicator_directions,
    compute_indicator_values,
)


def _make_ohlcv(n: int = 250, trend: float = 0.001, vol: float = 0.01,
                seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(loc=trend, scale=vol, size=n)
    close = 20000.0 * np.exp(np.cumsum(rets))
    high = close * (1.0 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.005, n)))
    openp = close * (1.0 + rng.normal(0, 0.002, n))
    vol_arr = rng.lognormal(mean=10, sigma=0.3, size=n)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {"Date": dates, "Open": openp, "High": high, "Low": low,
         "Close": close, "Volume": vol_arr}
    )


def test_whitelist_size_is_13():
    # 12 upstream + close_30_sma already in the fork's prompt = 13 names.
    assert len(INDICATOR_WHITELIST) == 13
    assert "close_30_sma" in INDICATOR_WHITELIST
    assert "vwma" in INDICATOR_WHITELIST


def test_indicator_category_covers_whitelist():
    assert set(INDICATOR_CATEGORY.keys()) == set(INDICATOR_WHITELIST)
    for cat in INDICATOR_CATEGORY.values():
        assert cat in {"trend", "momentum", "volatility", "volume"}


def test_compute_indicator_values_uptrending_series():
    df = _make_ohlcv(n=250, trend=0.003, vol=0.01, seed=42)
    vals = compute_indicator_values(df)
    # All whitelist names present and finite.
    assert set(vals.keys()) == set(INDICATOR_WHITELIST)
    for k, v in vals.items():
        assert np.isfinite(v), f"{k} non-finite: {v}"


def test_directions_uptrend_majority_bullish():
    df = _make_ohlcv(n=250, trend=0.005, vol=0.005, seed=1)
    vals = compute_indicator_values(df)
    directions = compute_indicator_directions(df, vals)
    # In a strong uptrend, ≥ 3 of 4 trend indicators must be +1.
    trend_names = [n for n, c in INDICATOR_CATEGORY.items() if c == "trend"]
    trend_dirs = [directions[n] for n in trend_names]
    assert sum(1 for d in trend_dirs if d == 1) >= 3


def test_directions_downtrend_majority_bearish():
    df = _make_ohlcv(n=250, trend=-0.005, vol=0.005, seed=2)
    vals = compute_indicator_values(df)
    directions = compute_indicator_directions(df, vals)
    trend_names = [n for n, c in INDICATOR_CATEGORY.items() if c == "trend"]
    trend_dirs = [directions[n] for n in trend_names]
    assert sum(1 for d in trend_dirs if d == -1) >= 3


def test_compute_indicator_values_returns_float_scalars():
    df = _make_ohlcv(n=250)
    vals = compute_indicator_values(df)
    for k, v in vals.items():
        assert isinstance(v, float), f"{k}={v!r} not float"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/market/test_indicators.py -x -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/market/indicators.py
"""Deterministic 13-name indicator whitelist + direction rules.

Indicator values are computed via stockstats (the same backend used by
``tradingagents.dataflows.stockstats_utils``). Direction rules are
asymmetric-default-friendly: a typical RSI in the 45-55 band registers
0 (neutral) so it does NOT amplify a one-sided category vote. This is
the key to making ``conflict_score`` informative across coins.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from stockstats import StockDataFrame

INDICATOR_WHITELIST = [
    "close_30_sma", "close_50_sma", "close_200_sma", "close_10_ema",
    "macd", "macds", "macdh", "rsi",
    "boll", "boll_ub", "boll_lb", "atr",
    "vwma",
]

INDICATOR_CATEGORY: Dict[str, str] = {
    "close_30_sma":  "trend",
    "close_50_sma":  "trend",
    "close_200_sma": "trend",
    "close_10_ema":  "trend",
    "macd":          "momentum",
    "macds":         "momentum",
    "macdh":         "momentum",
    "rsi":           "momentum",
    "boll":          "volatility",
    "boll_ub":       "volatility",
    "boll_lb":       "volatility",
    "atr":           "volatility",
    "vwma":          "volume",
}

# ATR percentile rolling window
_ATR_PCT_WINDOW = 90
# RSI thresholds — tighter than the 70/30 textbook so most bars register a
# direction; this is what makes conflict_score informative.
_RSI_HIGH = 55.0
_RSI_LOW = 45.0


def _ohlcv_to_stockstats(df: pd.DataFrame) -> StockDataFrame:
    cols = {c.lower(): c for c in df.columns}
    rename = {
        cols.get("open", "Open"):   "open",
        cols.get("high", "High"):   "high",
        cols.get("low",  "Low"):    "low",
        cols.get("close","Close"):  "close",
        cols.get("volume","Volume"):"volume",
    }
    sdf = df.rename(columns=rename).copy()
    return StockDataFrame.retype(sdf)


def compute_indicator_values(df: pd.DataFrame) -> Dict[str, float]:
    """Compute the 13 whitelist indicator values at the most recent bar.

    Caller is responsible for filtering ``df`` to ``Date <= trade_date``
    upstream (the existing OHLCV loaders already do this).
    """
    sdf = _ohlcv_to_stockstats(df)
    out: Dict[str, float] = {}
    for name in INDICATOR_WHITELIST:
        try:
            series = sdf[name]
            val = float(series.iloc[-1])
        except Exception:
            val = float("nan")
        out[name] = val
    return out


def _atr_percentile(df: pd.DataFrame, window: int = _ATR_PCT_WINDOW) -> float:
    sdf = _ohlcv_to_stockstats(df)
    atr_series = sdf["atr"]
    tail = atr_series.tail(window).dropna()
    if len(tail) < 10 or not np.isfinite(atr_series.iloc[-1]):
        return 0.5
    rank = (tail < atr_series.iloc[-1]).mean()
    return float(np.clip(rank, 0.0, 1.0))


def compute_indicator_directions(
    df: pd.DataFrame, values: Dict[str, float]
) -> Dict[str, int]:
    """Return -1 / 0 / +1 per whitelist indicator using the rules table."""
    close = float(df["Close"].iloc[-1])
    atr_pct = _atr_percentile(df)
    macd = values.get("macd", float("nan"))
    macds = values.get("macds", float("nan"))
    macdh = values.get("macdh", float("nan"))
    rsi = values.get("rsi", float("nan"))
    boll = values.get("boll", float("nan"))
    boll_ub = values.get("boll_ub", float("nan"))
    boll_lb = values.get("boll_lb", float("nan"))
    vwma = values.get("vwma", float("nan"))

    d: Dict[str, int] = {}
    for sma_name in ("close_30_sma", "close_50_sma",
                     "close_200_sma", "close_10_ema"):
        v = values.get(sma_name, float("nan"))
        d[sma_name] = (
            1 if np.isfinite(v) and close > v else
           -1 if np.isfinite(v) and close < v else 0
        )
    d["macd"]  = 1 if macd > 0 else -1 if macd < 0 else 0
    d["macds"] = (
        1 if np.isfinite(macd) and np.isfinite(macds) and macd > macds else
       -1 if np.isfinite(macd) and np.isfinite(macds) and macd < macds else 0
    )
    d["macdh"] = 1 if macdh > 0 else -1 if macdh < 0 else 0
    d["rsi"]   = (
        1 if np.isfinite(rsi) and rsi > _RSI_HIGH else
       -1 if np.isfinite(rsi) and rsi < _RSI_LOW else 0
    )
    d["boll"]  = (
        1 if np.isfinite(boll) and close > boll else
       -1 if np.isfinite(boll) and close < boll else 0
    )
    d["boll_ub"] = (
        1 if np.isfinite(boll_ub) and close > boll_ub else
       -1 if np.isfinite(boll_lb) and close < boll_lb else 0
    )
    d["boll_lb"] = (
        1 if np.isfinite(boll_lb) and close < boll_lb else
       -1 if np.isfinite(boll_ub) and close > boll_ub else 0
    )
    d["atr"]  = 1 if atr_pct < 0.4 else -1 if atr_pct > 0.8 else 0
    d["vwma"] = (
        1 if np.isfinite(vwma) and close > vwma else
       -1 if np.isfinite(vwma) and close < vwma else 0
    )
    return d
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/market/test_indicators.py -x -q`
Expected: PASS, 6 tests passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/market/indicators.py tests/market/test_indicators.py
git commit -m "feat(market-v2): 13-indicator whitelist + deterministic direction rules"
```

---

## Task 3: Regime Tag (deterministic, prompt-conditioning)

**Files:**
- Create: `tradingagents/market/regime_tag.py`
- Test: `tests/market/test_regime_tag.py`

This is intentionally a separate, cheap deterministic regime tag — distinct from `tradingagents/strategies/regime.py` (which is an HMM-3 trained per-coin). The strategies regime label is fitted on smoothed log returns; the v2 market analyst needs a fast, training-free, per-bar tag suitable for prompt conditioning across any coin.

Rules:
- ADX > 25 AND 30-day return > 0  → `TREND_UP`
- ADX > 25 AND 30-day return < 0  → `TREND_DOWN`
- ATR percentile (90-day) > 0.8   → `HIGH_VOL`
- Otherwise                        → `RANGE`

Regime confidence: `0.5 + 0.5 * min(adx/40, 1.0)` for TREND_*; `0.5 + 0.5 * (atr_pct - 0.8) / 0.2` for HIGH_VOL; `0.6 - 0.1 * abs(return_30d) / max(atr_pct, 0.05)` for RANGE (bounded to [0, 1]).

- [ ] **Step 1: Write the failing tests**

```python
# tests/market/test_regime_tag.py
import numpy as np
import pandas as pd

from tradingagents.market.regime_tag import (
    RegimeFeatures,
    compute_regime_features,
    deterministic_regime,
)


def _series(n: int, start: float = 20000.0, drift: float = 0.0,
            vol: float = 0.01, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = start * np.exp(np.cumsum(r))
    high = close * (1.0 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.005, n)))
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n, freq="D"),
        "Open": close, "High": high, "Low": low, "Close": close,
        "Volume": np.ones(n) * 1e6,
    })


def test_compute_regime_features_keys():
    df = _series(250, drift=0.0, vol=0.01)
    feats = compute_regime_features(df)
    assert isinstance(feats, RegimeFeatures)
    for k in ("adx", "atr_percentile", "return_30d"):
        assert hasattr(feats, k)


def test_strong_uptrend_classified_trend_up():
    df = _series(250, drift=0.006, vol=0.005, seed=10)
    label, conf, _feats = deterministic_regime(df)
    assert label == "TREND_UP"
    assert 0.0 <= conf <= 1.0


def test_strong_downtrend_classified_trend_down():
    df = _series(250, drift=-0.006, vol=0.005, seed=11)
    label, conf, _ = deterministic_regime(df)
    assert label == "TREND_DOWN"


def test_high_vol_classified_high_vol():
    rng = np.random.default_rng(7)
    n = 250
    # Spike vol in last 40 bars without a clear trend.
    base = np.full(n, 0.005)
    base[-40:] = 0.05
    rets = rng.normal(0.0, base, n)
    close = 20000.0 * np.exp(np.cumsum(rets))
    df = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n, freq="D"),
        "Open": close,
        "High": close * 1.02, "Low": close * 0.98,
        "Close": close, "Volume": np.ones(n) * 1e6,
    })
    label, _, feats = deterministic_regime(df)
    assert label == "HIGH_VOL"
    assert feats.atr_percentile > 0.8


def test_chop_classified_range():
    df = _series(250, drift=0.0, vol=0.005, seed=3)
    label, _, _ = deterministic_regime(df)
    assert label == "RANGE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/market/test_regime_tag.py -x -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/market/regime_tag.py
"""Deterministic regime tag for prompt conditioning.

NOT the HMM regime in tradingagents/strategies/regime.py — that one is
trained per-coin and used by the modulator. This one is a fast
training-free per-bar tag suitable for inclusion in the market
analyst's prompt. It uses ADX, 30-day return sign, and ATR percentile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from stockstats import StockDataFrame

_ATR_PCT_WINDOW = 90


@dataclass
class RegimeFeatures:
    adx: float
    atr_percentile: float
    return_30d: float


def _stockstats(df: pd.DataFrame) -> StockDataFrame:
    cols = {c.lower(): c for c in df.columns}
    rename = {
        cols.get("open", "Open"):   "open",
        cols.get("high", "High"):   "high",
        cols.get("low",  "Low"):    "low",
        cols.get("close","Close"):  "close",
        cols.get("volume","Volume"):"volume",
    }
    return StockDataFrame.retype(df.rename(columns=rename).copy())


def compute_regime_features(df: pd.DataFrame) -> RegimeFeatures:
    sdf = _stockstats(df)
    adx_series = sdf["adx"]
    adx = float(adx_series.iloc[-1]) if np.isfinite(adx_series.iloc[-1]) else 0.0

    atr_series = sdf["atr"]
    tail = atr_series.tail(_ATR_PCT_WINDOW).dropna()
    if len(tail) >= 10 and np.isfinite(atr_series.iloc[-1]):
        atr_pct = float(np.clip((tail < atr_series.iloc[-1]).mean(), 0.0, 1.0))
    else:
        atr_pct = 0.5

    close = df["Close"].astype(float)
    if len(close) >= 31:
        return_30d = float(close.iloc[-1] / close.iloc[-31] - 1.0)
    else:
        return_30d = 0.0

    return RegimeFeatures(adx=adx, atr_percentile=atr_pct, return_30d=return_30d)


def deterministic_regime(df: pd.DataFrame) -> Tuple[str, float, RegimeFeatures]:
    """Return ``(label, confidence, features)``.

    Precedence: TREND_* dominates if ADX > 25; HIGH_VOL only when no trend
    is detected. This avoids labelling a strong trending market HIGH_VOL
    just because volatility is elevated.
    """
    feats = compute_regime_features(df)
    if feats.adx > 25.0 and feats.return_30d > 0.0:
        return "TREND_UP", float(np.clip(0.5 + 0.5 * min(feats.adx / 40.0, 1.0),
                                         0.0, 1.0)), feats
    if feats.adx > 25.0 and feats.return_30d < 0.0:
        return "TREND_DOWN", float(np.clip(0.5 + 0.5 * min(feats.adx / 40.0, 1.0),
                                            0.0, 1.0)), feats
    if feats.atr_percentile > 0.8:
        return "HIGH_VOL", float(np.clip(0.5 + 0.5 * (feats.atr_percentile - 0.8) / 0.2,
                                          0.0, 1.0)), feats
    denom = max(feats.atr_percentile, 0.05)
    conf = float(np.clip(0.6 - 0.1 * abs(feats.return_30d) / denom, 0.0, 1.0))
    return "RANGE", conf, feats
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/market/test_regime_tag.py -x -q`
Expected: PASS, 5 tests passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/market/regime_tag.py tests/market/test_regime_tag.py
git commit -m "feat(market-v2): deterministic regime tag (ADX/ATR-pct/30d-return)"
```

---

## Task 4: Category Vote, Conflict Score, Asymmetric Default Direction

**Files:**
- Create: `tradingagents/market/category_vote.py`
- Test: `tests/market/test_category_vote.py`

Rules:
- Per category, the category direction is the sign of `sum(direction)` across indicators in that category; ties → 0.
- `conflict_score = (# categories whose direction disagrees with the majority of non-zero categories) / 4`. If all non-zero categories agree → 0; if 2 of 4 disagree → 0.5; if no non-zero categories → 0.0 (no signal, not conflict).
- `default_direction` (asymmetric):
  - `LONG` if ≥2 of 4 category directions are +1 and ≤0 are -1
  - `SHORT` if ≥3 of 4 category directions are -1 and ≤0 are +1
  - `FLAT` otherwise

The 2-vs-3 asymmetry is the FINSABER bear-aggression correction: bear positions require stronger consensus than bull positions.

- [ ] **Step 1: Write the failing tests**

```python
# tests/market/test_category_vote.py
import pytest

from tradingagents.market.category_vote import (
    aggregate_category_votes,
    asymmetric_default_direction,
    conflict_score,
)


def test_aggregate_unanimous_bullish():
    directions = {
        "close_30_sma": 1, "close_50_sma": 1,
        "rsi": 1, "macd": 1, "macds": 1, "macdh": 1,
        "boll": 1, "atr": 0, "boll_ub": 0, "boll_lb": 0, "close_200_sma": 1, "close_10_ema": 1,
        "vwma": 1,
    }
    cats = aggregate_category_votes(directions)
    assert cats["trend"] == 1
    assert cats["momentum"] == 1
    assert cats["volume"] == 1
    # volatility had +1 + 0 + 0 + 0 → +1
    assert cats["volatility"] == 1


def test_aggregate_split_trend_and_momentum():
    directions = {
        "close_30_sma": 1, "close_50_sma": 1, "close_200_sma": -1, "close_10_ema": -1,
        "macd": -1, "macds": -1, "macdh": 1, "rsi": 1,
        "boll": 0, "boll_ub": 0, "boll_lb": 0, "atr": 0,
        "vwma": 0,
    }
    cats = aggregate_category_votes(directions)
    # trend: 1+1-1-1 = 0
    assert cats["trend"] == 0
    # momentum: -1-1+1+1 = 0
    assert cats["momentum"] == 0
    assert cats["volatility"] == 0
    assert cats["volume"] == 0


def test_conflict_score_all_agree_is_zero():
    cats = {"trend": 1, "momentum": 1, "volatility": 1, "volume": 1}
    assert conflict_score(cats) == 0.0


def test_conflict_score_half_disagree_is_half():
    cats = {"trend": 1, "momentum": 1, "volatility": -1, "volume": -1}
    assert conflict_score(cats) == 0.5


def test_conflict_score_no_signal_is_zero():
    cats = {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    assert conflict_score(cats) == 0.0


def test_asymmetric_long_threshold_two_positive_no_negative():
    cats = {"trend": 1, "momentum": 1, "volatility": 0, "volume": 0}
    assert asymmetric_default_direction(cats) == "LONG"


def test_asymmetric_long_blocked_by_any_negative():
    cats = {"trend": 1, "momentum": 1, "volatility": -1, "volume": 0}
    # ≥ 2 positives but a negative exists → FLAT (asymmetric)
    assert asymmetric_default_direction(cats) == "FLAT"


def test_asymmetric_short_requires_three_negatives():
    cats = {"trend": -1, "momentum": -1, "volatility": 0, "volume": 0}
    # Only 2 negatives → not enough for SHORT
    assert asymmetric_default_direction(cats) == "FLAT"
    cats = {"trend": -1, "momentum": -1, "volatility": -1, "volume": 0}
    assert asymmetric_default_direction(cats) == "SHORT"


def test_asymmetric_short_blocked_by_any_positive():
    cats = {"trend": -1, "momentum": -1, "volatility": -1, "volume": 1}
    assert asymmetric_default_direction(cats) == "FLAT"


def test_asymmetric_all_zero_is_flat():
    assert asymmetric_default_direction(
        {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    ) == "FLAT"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/market/test_category_vote.py -x -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/market/category_vote.py
"""Category aggregation, conflict_score, asymmetric default direction.

The 2-vs-3 LONG/SHORT asymmetry implements the FINSABER bear-aggression
correction (arXiv:2505.07078): bear positions require stronger consensus
than bull positions because pretrained LLMs over-allocate on the short
side in down-markets. Asymmetric thresholds also encode the crypto-
specific upward drift.
"""
from __future__ import annotations

from typing import Dict

from tradingagents.market.indicators import INDICATOR_CATEGORY


def aggregate_category_votes(directions: Dict[str, int]) -> Dict[str, int]:
    """Sum per-indicator directions inside each category, return signed votes."""
    sums = {"trend": 0, "momentum": 0, "volatility": 0, "volume": 0}
    for name, d in directions.items():
        cat = INDICATOR_CATEGORY.get(name)
        if cat is None:
            continue
        sums[cat] += int(d)
    return {k: (1 if v > 0 else -1 if v < 0 else 0) for k, v in sums.items()}


def conflict_score(category_votes: Dict[str, int]) -> float:
    """Fraction of non-zero categories disagreeing with the majority sign.

    No non-zero categories ⇒ 0 (absence of signal, not conflict).
    """
    nonzero = [v for v in category_votes.values() if v != 0]
    if not nonzero:
        return 0.0
    sign = 1 if sum(nonzero) > 0 else -1 if sum(nonzero) < 0 else 0
    if sign == 0:
        # Even split — maximum disagreement among non-zero categories.
        return 0.5
    disagree = sum(1 for v in category_votes.values() if v != 0 and v != sign)
    return disagree / 4.0


def asymmetric_default_direction(category_votes: Dict[str, int]) -> str:
    """LONG ≥ 2 pos & 0 neg; SHORT ≥ 3 neg & 0 pos; else FLAT."""
    pos = sum(1 for v in category_votes.values() if v == 1)
    neg = sum(1 for v in category_votes.values() if v == -1)
    if pos >= 2 and neg == 0:
        return "LONG"
    if neg >= 3 and pos == 0:
        return "SHORT"
    return "FLAT"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/market/test_category_vote.py -x -q`
Expected: PASS, 10 tests passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/market/category_vote.py tests/market/test_category_vote.py
git commit -m "feat(market-v2): category vote + conflict_score + asymmetric default"
```

---

## Task 5: Snapshot Builder (Orchestrator)

**Files:**
- Create: `tradingagents/market/build_snapshot.py`
- Test: `tests/market/test_build_snapshot.py`

`build_market_snapshot(coin, trade_date, horizon_days, anonymize)` orchestrates:
1. Load OHLCV via the existing `tradingagents.dataflows.interface.get_OHLCV` family (the same loader the legacy market analyst uses through tools, but called directly here — no LLM tool round-trip).
2. Compute indicator values + directions (Task 2).
3. Compute regime tag (Task 3).
4. Aggregate category votes, conflict_score, default direction (Task 4).
5. Return a populated `MarketSnapshot`.

The exact OHLCV fetch function reused: `tradingagents.dataflows.coingecko_binance.get_coingecko_binance_ohlcv` (verify import path matches current code — if API differs, use the same call site the legacy market analyst's `get_crypto_data` tool delegates to via `route_to_vendor`). The point is to bypass the LangChain tool roundtrip in v2 because we don't need an LLM tool call to get indicator values — they are deterministic.

- [ ] **Step 1: Inspect the existing OHLCV loader to confirm the call signature**

```bash
grep -n "def get_coingecko_binance_ohlcv\|def get_crypto_data\|def _fetch_ohlcv\|coingecko_binance" \
     tradingagents/dataflows/coingecko_binance.py \
     tradingagents/agents/utils/crypto_market_tools.py 2>/dev/null \
     | head -20
```

Expected: locate the function exposed to the rest of the package that returns a DataFrame with `Date, Open, High, Low, Close, Volume` filtered to `<= trade_date`. Use that exact import in the snapshot builder. (If the name differs from the placeholder in Step 3 below, adjust both the snapshot builder and the test mock accordingly before continuing.)

- [ ] **Step 2: Write the failing tests**

```python
# tests/market/test_build_snapshot.py
from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np
import pandas as pd

from tradingagents.market.build_snapshot import build_market_snapshot


def _ohlcv(n=260, drift=0.0, vol=0.01, seed=0):
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = 20000.0 * np.exp(np.cumsum(r))
    return pd.DataFrame({
        "Date": pd.date_range("2025-04-01", periods=n, freq="D"),
        "Open": close, "High": close*1.005, "Low": close*0.995,
        "Close": close, "Volume": np.ones(n) * 1e6,
    })


def test_build_snapshot_returns_market_snapshot(monkeypatch):
    df = _ohlcv(drift=0.003, vol=0.005, seed=99)

    def fake_loader(coin, trade_date, lookback_days=300):
        return df

    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               side_effect=fake_loader):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
        )
    from tradingagents.market.snapshot import MarketSnapshot
    assert isinstance(snap, MarketSnapshot)
    assert snap.horizon_days == 7
    assert 0.0 <= snap.conflict_score <= 1.0
    assert snap.default_direction in {"LONG", "SHORT", "FLAT"}
    assert snap.regime in {"TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOL"}
    assert len(snap.indicators) == 13


def test_build_snapshot_uptrend_default_long(monkeypatch):
    df = _ohlcv(drift=0.006, vol=0.004, seed=1)
    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               return_value=df):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
        )
    assert snap.regime == "TREND_UP"
    # In a clean uptrend with low vol, all 4 categories should agree → LONG.
    assert snap.default_direction == "LONG"
    assert snap.conflict_score == 0.0


def test_build_snapshot_anonymize_asset_alias(monkeypatch):
    from tradingagents.agents.utils import anonymizer
    df = _ohlcv(drift=0.002, vol=0.005, seed=2)
    anonymizer.configure(enabled=True)
    try:
        with patch("tradingagents.market.build_snapshot._load_ohlcv",
                   return_value=df):
            snap = build_market_snapshot(
                coin="bitcoin",
                trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
                horizon_days=7,
                anonymize=True,
            )
        assert snap.asset.startswith("Asset_")
    finally:
        anonymizer.configure(enabled=False)


def test_build_snapshot_no_anonymize_uses_coin_label(monkeypatch):
    df = _ohlcv(drift=0.001, vol=0.005, seed=3)
    from tradingagents.agents.utils import anonymizer
    anonymizer.configure(enabled=False)
    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               return_value=df):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
            anonymize=False,
        )
    assert snap.asset == "bitcoin"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/market/test_build_snapshot.py -x -q`
Expected: FAIL — `build_market_snapshot` does not exist.

- [ ] **Step 4: Write minimal implementation**

```python
# tradingagents/market/build_snapshot.py
"""Build a MarketSnapshot for one (coin, trade_date) pair.

This is the deterministic, training-free, LLM-free half of the v2 market
analyst. The analyst node passes the snapshot to a narrow LLM via
``snapshot.to_prompt_table()``; the modulator consumes
``snapshot.to_modulator_features()``.

OHLCV is fetched via the same path the legacy analyst's tool delegates
to. We call it directly here to skip the LangChain tool round-trip.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from tradingagents.market.category_vote import (
    aggregate_category_votes,
    asymmetric_default_direction,
    conflict_score,
)
from tradingagents.market.indicators import (
    INDICATOR_CATEGORY,
    INDICATOR_WHITELIST,
    compute_indicator_directions,
    compute_indicator_values,
)
from tradingagents.market.regime_tag import deterministic_regime
from tradingagents.market.snapshot import IndicatorReading, MarketSnapshot


def _load_ohlcv(coin: str, trade_date: datetime, lookback_days: int = 300) -> pd.DataFrame:
    """Defer to the package's OHLCV loader. Mocked in tests."""
    # IMPORTANT: confirm in Task 5 step 1 that this import path is correct
    # for the current branch. If it differs, update here AND in tests.
    from tradingagents.dataflows.coingecko_binance import (
        get_coingecko_binance_ohlcv,
    )

    df = get_coingecko_binance_ohlcv(
        coin=coin,
        as_of_date=trade_date,
        lookback_days=lookback_days,
    )
    df = df[df["Date"] <= pd.Timestamp(trade_date).tz_localize(None)]
    return df


def build_market_snapshot(
    coin: str,
    trade_date: datetime,
    horizon_days: int = 7,
    anonymize: bool = False,
    lookback_days: int = 300,
    df: Optional[pd.DataFrame] = None,
) -> MarketSnapshot:
    from tradingagents.agents.utils.anonymizer import mask

    df = df if df is not None else _load_ohlcv(coin, trade_date, lookback_days)
    if len(df) < 60:
        raise ValueError(
            f"build_market_snapshot: only {len(df)} bars for {coin} "
            f"<= {trade_date}; need ≥ 60"
        )

    values = compute_indicator_values(df)
    directions = compute_indicator_directions(df, values)
    regime, regime_conf, feats = deterministic_regime(df)
    cat_votes = aggregate_category_votes(directions)
    cs = conflict_score(cat_votes)
    direction = asymmetric_default_direction(cat_votes)

    indicators = [
        IndicatorReading(
            name=name,
            value=float(values.get(name, float("nan"))),
            category=INDICATOR_CATEGORY[name],
            direction=int(directions.get(name, 0)),
        )
        for name in INDICATOR_WHITELIST
    ]

    asset_label = mask(coin) if anonymize else coin

    return MarketSnapshot(
        asset=asset_label,
        as_of_ts=pd.Timestamp(df["Date"].iloc[-1]).to_pydatetime().replace(
            tzinfo=trade_date.tzinfo
        ),
        trade_date=trade_date,
        horizon_days=int(horizon_days),
        regime=regime,
        regime_confidence=float(regime_conf),
        adx=float(feats.adx),
        atr_percentile=float(feats.atr_percentile),
        return_30d=float(feats.return_30d),
        indicators=indicators,
        category_votes=cat_votes,
        conflict_score=float(cs),
        default_direction=direction,
    )
```

Also update `tradingagents/market/__init__.py`:

```python
# tradingagents/market/__init__.py
from tradingagents.market.build_snapshot import build_market_snapshot
from tradingagents.market.snapshot import (
    DirectionLabel,
    IndicatorReading,
    MarketAnalystOutput,
    MarketCategory,
    MarketSnapshot,
    RegimeLabel,
)

__all__ = [
    "DirectionLabel",
    "IndicatorReading",
    "MarketAnalystOutput",
    "MarketCategory",
    "MarketSnapshot",
    "RegimeLabel",
    "build_market_snapshot",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/market/test_build_snapshot.py -x -q`
Expected: PASS, 4 tests passed

- [ ] **Step 6: Commit**

```bash
git add tradingagents/market/build_snapshot.py tradingagents/market/__init__.py \
        tests/market/test_build_snapshot.py
git commit -m "feat(market-v2): build_market_snapshot orchestrator"
```

---

## Task 6: Per-Coin Calibration Wrapper (reuse IsotonicCalibrator)

**Files:**
- Create: `tradingagents/strategies/market_calibration.py`
- Test: `tests/strategies/test_market_calibration.py`

Reuse `tradingagents/strategies/calibration.IsotonicCalibrator` and add a thin wrapper that stores per-coin checkpoints at `data/checkpoints/market_isotonic_{coin}.pkl` and supports an `apply()` convenience that returns the calibrated conviction. This keeps the sentiment isotonic store (`isotonic_{coin}.pkl`) and the market one in separate files.

- [ ] **Step 1: Write the failing tests**

```python
# tests/strategies/test_market_calibration.py
import os
import tempfile

import numpy as np
import pytest

from tradingagents.strategies.market_calibration import (
    MARKET_CALIBRATOR_FILENAME,
    fit_market_calibrator,
    load_market_calibrator,
)


def test_filename_template_includes_coin():
    assert "{coin}" in MARKET_CALIBRATOR_FILENAME


def test_fit_then_load_roundtrip(tmp_path):
    rng = np.random.default_rng(0)
    raw = rng.uniform(0.0, 1.0, 200)
    realised = (raw > 0.55).astype(int)
    fit_market_calibrator(raw, realised, coin="bitcoin", root=str(tmp_path))
    c = load_market_calibrator("bitcoin", root=str(tmp_path))
    # Calibrator should reduce extreme convictions toward realised hit rate.
    assert 0.0 <= c.transform(0.9) <= 1.0
    assert 0.0 <= c.transform(0.1) <= 1.0


def test_load_unfit_coin_returns_identity(tmp_path):
    c = load_market_calibrator("nonexistent", root=str(tmp_path))
    assert c.transform(0.42) == pytest.approx(0.42)


def test_fit_rejects_too_few_samples(tmp_path):
    with pytest.raises(ValueError):
        fit_market_calibrator(
            np.array([0.1, 0.5, 0.9]),
            np.array([0, 1, 1]),
            coin="bitcoin",
            root=str(tmp_path),
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/strategies/test_market_calibration.py -x -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/strategies/market_calibration.py
"""Per-coin isotonic calibration of the v2 market analyst's conviction.

Same algorithm as tradingagents.strategies.calibration but stored under a
separate filename so the sentiment and market calibrators do not collide.

The modulator multiplies the analyst's verbalized conviction by the
calibrator's output, so the effective per-coin weight is endogenous: a
coin where the analyst has no edge ends up with a calibrator that maps
all convictions toward ~0.5 → effective contribution ≈ 0.
"""
from __future__ import annotations

import os
from typing import Union

import numpy as np

from tradingagents.strategies.calibration import IsotonicCalibrator

MARKET_CALIBRATOR_FILENAME = "market_isotonic_{coin}.pkl"


def fit_market_calibrator(
    raw_confidences: Union[np.ndarray, list],
    realised_outcomes: Union[np.ndarray, list],
    coin: str,
    root: str = "data/checkpoints",
) -> IsotonicCalibrator:
    c = IsotonicCalibrator().fit(
        np.asarray(raw_confidences, dtype=float),
        np.asarray(realised_outcomes, dtype=float),
        coin=coin,
    )
    os.makedirs(root, exist_ok=True)
    c.to_pkl(os.path.join(root, MARKET_CALIBRATOR_FILENAME.format(coin=coin)))
    return c


def load_market_calibrator(
    coin: str, root: str = "data/checkpoints"
) -> IsotonicCalibrator:
    path = os.path.join(root, MARKET_CALIBRATOR_FILENAME.format(coin=coin))
    if not os.path.exists(path):
        identity = IsotonicCalibrator()
        identity.coin = coin
        return identity
    return IsotonicCalibrator.from_pkl(path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/strategies/test_market_calibration.py -x -q`
Expected: PASS, 4 tests passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/strategies/market_calibration.py \
        tests/strategies/test_market_calibration.py
git commit -m "feat(market-v2): per-coin isotonic calibrator wrapper"
```

---

## Task 7: State + Config Wiring

**Files:**
- Modify: `tradingagents/agents/utils/agent_states.py`
- Modify: `tradingagents/graph/propagation.py:53` (initial state dict)
- Modify: `tradingagents/default_config.py`
- Test: extend `tests/agents/test_modulator_market_features.py` (created in Task 9)

- [ ] **Step 1: Add `market_features` to AgentState**

Modify [tradingagents/agents/utils/agent_states.py](tradingagents/agents/utils/agent_states.py) by adding a new annotated field directly after `sentiment_features`:

```python
    market_features: Annotated[dict, "Deterministic market-analyst-v2 snapshot features (regime, conflict_score, category votes)"]
```

- [ ] **Step 2: Initialize `market_features: {}` in propagation**

Modify [tradingagents/graph/propagation.py](tradingagents/graph/propagation.py) — in the initial-state dict construction (around line 53 where `"sentiment_features": {}` is set), add a sibling line:

```python
            "market_features": {},
```

- [ ] **Step 3: Add config flags to DEFAULT_CONFIG**

Modify [tradingagents/default_config.py](tradingagents/default_config.py). Insert after the `sentiment_anonymize` block (around line 117):

```python
    # Market analyst pipeline mode (asset-agnostic v2 implementation).
    # "legacy"  = free-text market_analyst (current default; 150+ indicators)
    # "v2"      = structured-snapshot market analyst with Pydantic-typed
    #             output, conflict_score gating, asymmetric default direction,
    #             and per-coin isotonic calibration.
    "market_mode": "legacy",
    # Anonymize coin name in the market analyst prompt (Glasserman & Lin).
    # Independent of sentiment_anonymize so they can be toggled separately.
    "market_anonymize": True,
    # Variant C of the A/B harness: structured-only mode that skips the
    # narrow LLM call and emits the snapshot table as the report. Used in
    # ablation to isolate the contribution of the LLM interpretation.
    "market_skip_llm": False,
    # Horizon used in the market analyst's reasoning prompt (days).
    "market_horizon_days": 7,
```

And add env-var hooks in `apply_env_overrides`:

```python
    # Market analyst overrides
    _env_str(config, "market_mode", "TRADINGAGENTS_MARKET_MODE")
    _env_bool(config, "market_anonymize", "TRADINGAGENTS_MARKET_ANONYMIZE")
    _env_bool(config, "market_skip_llm", "TRADINGAGENTS_MARKET_SKIP_LLM")
    _env_int(config, "market_horizon_days", "TRADINGAGENTS_MARKET_HORIZON_DAYS")
```

(Place these immediately after the existing sentiment overrides, around line 170.)

- [ ] **Step 4: Run regression tests to confirm nothing broke**

```bash
pytest tests/agents tests/graph tests/strategies -x -q
```

Expected: existing tests still pass; no new test added in this task — the wiring is covered by Tasks 8 and 9.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/utils/agent_states.py \
        tradingagents/graph/propagation.py \
        tradingagents/default_config.py
git commit -m "feat(market-v2): wire market_features into state + market_* config flags"
```

---

## Task 8: Market Analyst v2 Branch in Analyst Node

**Files:**
- Modify: `tradingagents/agents/analysts/market_analyst.py`
- Test: `tests/agents/test_market_analyst_v2.py`

The legacy path stays the default. Under `cfg["market_mode"] == "v2"` the node:
1. Builds the snapshot via `build_market_snapshot`.
2. If `cfg["market_skip_llm"]` is True → returns the structured-only report (Variant C).
3. Else → builds a third-person ("Andrew") prompt that asks the LLM to refine `direction` (only allowed to disagree with `default_direction` if it can name ≥ 1 dissenting indicator), emit conviction ∈ [0,1], and a rationale. The LLM response is parsed into `MarketAnalystOutput`. On parse failure → fall back to the snapshot's `default_direction` with conviction 0.0 (zero contribution).
4. Loads `load_market_calibrator(coin)` and multiplies the verbalized conviction by the calibrator.
5. Returns `{"messages": [...], "market_report": "...", "market_features": {...analyst features merged with snapshot features...}}`.

The merged feature dict adds three analyst-side keys to the snapshot features so the modulator sees both:

| key | type | source |
|---|---|---|
| `market_llm_direction` | "LONG" / "SHORT" / "FLAT" | analyst LLM output |
| `market_llm_conviction_raw` | float ∈ [0,1] | analyst LLM output |
| `market_llm_conviction_calibrated` | float ∈ [0,1] | `IsotonicCalibrator.transform(raw)` |

- [ ] **Step 1: Write the failing tests**

```python
# tests/agents/test_market_analyst_v2.py
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.analysts.market_analyst import create_market_analyst


def _state():
    return {
        "trade_date": "2026-01-15",
        "company_of_interest": "bitcoin",
        "messages": [],
    }


def _fake_snapshot(direction="LONG", conflict=0.25):
    from tradingagents.market.snapshot import (
        IndicatorReading, MarketSnapshot,
    )
    now = datetime(2026, 1, 15, tzinfo=timezone.utc)
    return MarketSnapshot(
        asset="Asset_A", as_of_ts=now, trade_date=now,
        horizon_days=7,
        regime="TREND_UP", regime_confidence=0.7,
        adx=28.0, atr_percentile=0.6, return_30d=0.05,
        indicators=[IndicatorReading(
            name="rsi", value=60.0, category="momentum", direction=1,
        )],
        category_votes={"trend": 1, "momentum": 1, "volatility": 0, "volume": 1},
        conflict_score=conflict, default_direction=direction,
    )


def test_legacy_mode_unchanged():
    fake_llm = MagicMock()
    fake_response = MagicMock(content="legacy text", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response
    with patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={"market_mode": "legacy", "asset_class": "crypto"}):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    assert "market_report" in out
    assert out.get("market_features", {}) == {}


def test_v2_skip_llm_emits_snapshot_only():
    fake_llm = MagicMock()
    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot()), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": True,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    assert "MarketSnapshot" in out["market_report"]
    feats = out["market_features"]
    assert "market_conflict_score" in feats
    assert feats["market_default_direction"] == "LONG"
    # No LLM-side keys when skip_llm.
    assert "market_llm_direction" not in feats


def test_v2_full_parses_llm_output_and_calibrates():
    fake_llm = MagicMock()
    llm_response = MagicMock(
        content=(
            '{"direction": "LONG", "conviction": 0.8, '
            '"conflict_score": 0.25, '
            '"indicators_used": ["rsi"], '
            '"dissenting_indicators": [], '
            '"rationale": "Trend and momentum aligned."}'
        ),
        tool_calls=[],
    )
    fake_llm.invoke.return_value = llm_response

    def fake_calibrator(coin, root="data/checkpoints"):
        from tradingagents.strategies.calibration import IsotonicCalibrator
        import numpy as np
        return IsotonicCalibrator().fit(
            np.linspace(0.0, 1.0, 50),
            np.where(np.linspace(0.0, 1.0, 50) > 0.5, 1, 0),
            coin=coin,
        )

    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot()), \
         patch("tradingagents.agents.analysts.market_analyst.load_market_calibrator",
               side_effect=fake_calibrator), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": False,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())

    feats = out["market_features"]
    assert feats["market_llm_direction"] == "LONG"
    assert feats["market_llm_conviction_raw"] == pytest.approx(0.8)
    assert 0.0 <= feats["market_llm_conviction_calibrated"] <= 1.0


def test_v2_unparseable_llm_falls_back_to_default():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(
        content="this is not JSON at all", tool_calls=[],
    )
    with patch("tradingagents.agents.analysts.market_analyst.build_market_snapshot",
               return_value=_fake_snapshot(direction="FLAT", conflict=0.5)), \
         patch("tradingagents.agents.analysts.market_analyst.load_market_calibrator",
               return_value=MagicMock(transform=lambda x: x)), \
         patch("tradingagents.agents.analysts.market_analyst.get_config",
               return_value={
                   "market_mode": "v2", "market_skip_llm": False,
                   "market_anonymize": False, "market_horizon_days": 7,
                   "asset_class": "crypto",
               }):
        node = create_market_analyst(fake_llm)
        out = node(_state())
    feats = out["market_features"]
    assert feats["market_llm_direction"] == "FLAT"
    assert feats["market_llm_conviction_raw"] == 0.0
    assert feats["market_llm_conviction_calibrated"] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_market_analyst_v2.py -x -q`
Expected: FAIL — `build_market_snapshot` / `load_market_calibrator` not imported in `market_analyst.py`.

- [ ] **Step 3: Rewrite `market_analyst.py` to support both modes**

Replace [tradingagents/agents/analysts/market_analyst.py](tradingagents/agents/analysts/market_analyst.py) with:

```python
"""Market analyst — legacy free-text path + asset-agnostic v2 structured path.

v2 design (asset-agnostic "do no harm"):
  - 13-indicator whitelist, deterministic category vote, asymmetric default
  - Pydantic-typed LLM output: direction + conviction + dissenting indicators
  - Per-coin isotonic calibration of conviction (effective per-coin weight
    is endogenous; no coin-specific code path).
  - Anonymized asset name in the prompt (Glasserman & Lin) by default in v2.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_indicators,
    get_language_instruction,
    get_stock_data,
    get_crypto_data,
    get_crypto_indicators,
    get_crypto_indicators_batch,
)
from tradingagents.dataflows.config import get_config
from tradingagents.market.build_snapshot import build_market_snapshot
from tradingagents.market.snapshot import MarketAnalystOutput, MarketSnapshot
from tradingagents.strategies.market_calibration import load_market_calibrator

logger = logging.getLogger(__name__)


_LEGACY_SYSTEM_MESSAGE = (
    # Unchanged legacy prompt — moved here to keep the v2 branch readable.
    # See git history (commit prior to market-v2 work) for the original.
    """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. ..."""
)


_V2_SYSTEM_MESSAGE = (
    "You are Andrew, a conservative technical analyst. The MarketSnapshot "
    "below was computed deterministically — do NOT recompute indicators or "
    "values. Your job is to either confirm or refine the snapshot's "
    "`default_direction` and emit a structured JSON object.\n\n"
    "Rules:\n"
    "1. The asset is intentionally referred to by an alias to neutralise "
    "training-corpus priors. Do not speculate about its identity.\n"
    "2. You may disagree with `default_direction` ONLY if you can name ≥ 1 "
    "specific indicator from the snapshot that contradicts it AND the "
    "snapshot's `conflict_score` is < 0.5. Otherwise emit FLAT.\n"
    "3. Asymmetric thresholds: prefer LONG over SHORT when uncertain. "
    "If you would emit SHORT but conflict_score ≥ 0.4, emit FLAT instead.\n"
    "4. Conviction ∈ [0,1] expresses how much you trust your own call. If "
    "you emit FLAT, conviction MUST be ≤ 0.2.\n"
    "5. Output ONLY a single JSON object matching this schema (no prose, "
    "no markdown fence):\n"
    "  {{\n"
    '    "direction": "LONG" | "SHORT" | "FLAT",\n'
    '    "conviction": <float 0..1>,\n'
    '    "conflict_score": <float 0..1>,\n'
    '    "indicators_used": [<indicator names from the snapshot>],\n'
    '    "dissenting_indicators": [<subset of indicators_used>],\n'
    '    "rationale": "<1-3 sentences>"\n'
    "  }}\n"
)


def _parse_trade_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    body = fence.group(1) if fence else text
    m = re.search(r"\{.*\}", body, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _fallback_output(snap: MarketSnapshot) -> MarketAnalystOutput:
    return MarketAnalystOutput(
        direction=snap.default_direction,
        conviction=0.0,
        conflict_score=snap.conflict_score,
        indicators_used=[],
        dissenting_indicators=[],
        rationale="LLM output unparseable; reverted to deterministic default.",
    )


def _compose_features(snap: MarketSnapshot,
                      llm_out: Optional[MarketAnalystOutput],
                      calibrated: Optional[float]) -> Dict[str, Any]:
    feats = snap.to_modulator_features()
    if llm_out is not None:
        feats["market_llm_direction"] = llm_out.direction
        feats["market_llm_conviction_raw"] = float(llm_out.conviction)
        feats["market_llm_conviction_calibrated"] = (
            float(calibrated) if calibrated is not None
            else float(llm_out.conviction)
        )
    return feats


def create_market_analyst(llm):

    def market_analyst_node(state):
        cfg = get_config()
        mode = cfg.get("market_mode", "legacy")
        if mode == "v2":
            return _run_v2(state, llm, cfg)
        return _run_legacy(state, llm, cfg)

    return market_analyst_node


def _run_v2(state, llm, cfg) -> Dict[str, Any]:
    coin = state["company_of_interest"]
    trade_date = _parse_trade_date(state["trade_date"])
    horizon = int(cfg.get("market_horizon_days", 7))
    anonymize = bool(cfg.get("market_anonymize", True))
    skip_llm = bool(cfg.get("market_skip_llm", False))

    snap = build_market_snapshot(
        coin=coin, trade_date=trade_date,
        horizon_days=horizon, anonymize=anonymize,
    )

    if skip_llm:
        report = (
            f"# Market v2 (structured-only) — {snap.asset} "
            f"{state['trade_date']}\n\n{snap.to_prompt_table()}\n"
        )
        feats = snap.to_modulator_features()
        return {
            "messages": [AIMessage(content=report)],
            "market_report": report,
            "market_features": feats,
        }

    instrument_context = build_instrument_context(coin)
    system_message = _V2_SYSTEM_MESSAGE + get_language_instruction()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are Andrew, an experienced technical analyst. {system_message}\n\n"
         "MarketSnapshot:\n\n{snapshot_md}\n\n"
         "{instrument_context}\n\nCurrent date: {current_date}"),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(
        system_message=system_message,
        snapshot_md=snap.to_prompt_table(),
        instrument_context=instrument_context,
        current_date=state["trade_date"],
    )

    result = llm.invoke(prompt.format(messages=state.get("messages", [])))
    raw = getattr(result, "content", "") or ""
    parsed = _extract_json_object(raw)
    if parsed is not None:
        try:
            llm_out = MarketAnalystOutput(**parsed)
        except ValidationError as exc:
            logger.warning(f"market-v2: schema validation failed: {exc}")
            llm_out = _fallback_output(snap)
    else:
        llm_out = _fallback_output(snap)

    calibrator = load_market_calibrator(coin)
    calibrated = float(calibrator.transform(llm_out.conviction))

    report = (
        f"# Market v2 — {snap.asset} {state['trade_date']}\n\n"
        f"{snap.to_prompt_table()}\n\n"
        f"## Andrew's structured assessment\n"
        f"Direction: {llm_out.direction} | "
        f"Raw conviction: {llm_out.conviction:.2f} | "
        f"Calibrated: {calibrated:.2f}\n\n"
        f"Rationale: {llm_out.rationale}\n"
    )
    if llm_out.dissenting_indicators:
        report += (
            f"\nDissenting indicators: "
            f"{', '.join(llm_out.dissenting_indicators)}\n"
        )

    return {
        "messages": [result],
        "market_report": report,
        "market_features": _compose_features(snap, llm_out, calibrated),
    }


def _run_legacy(state, llm, cfg) -> Dict[str, Any]:
    current_date = state["trade_date"]
    instrument_context = build_instrument_context(state["company_of_interest"])
    asset_class = cfg.get("asset_class", "stock")
    if asset_class == "crypto":
        tools = [get_crypto_data, get_crypto_indicators_batch, get_crypto_indicators]
    else:
        tools = [get_stock_data, get_indicators]

    system_message = _LEGACY_SYSTEM_MESSAGE + get_language_instruction()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful AI assistant, collaborating with other assistants."
         " Use the provided tools to progress towards answering the question."
         " You have access to the following tools: {tool_names}.\n{system_message}"
         "\n\n{instrument_context}\n\nFor your reference, the current date is {current_date}."),
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
        "market_report": report,
        "market_features": {},
    }
```

**Note**: the `_LEGACY_SYSTEM_MESSAGE` placeholder above uses `...` for brevity. **Do not** check in `...`. Paste the existing legacy prompt verbatim from the pre-edit file (the multi-paragraph string starting `"""You are a trading assistant tasked with analyzing financial markets...` through `"""` ending at line 75, plus the trailing markdown-table instruction). The diff should preserve the legacy prompt byte-for-byte.

- [ ] **Step 4: Run the new tests + the full agents suite**

```bash
pytest tests/agents/test_market_analyst_v2.py -x -q
pytest tests/agents -x -q
```

Expected: PASS for the new file (4 tests), and the existing agents suite stays green.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/analysts/market_analyst.py \
        tests/agents/test_market_analyst_v2.py
git commit -m "feat(market-v2): v2 structured-snapshot + narrow-LLM market analyst"
```

---

## Task 9: Modulator Consumes market_features

**Files:**
- Modify: `tradingagents/agents/modulator.py`
- Test: `tests/agents/test_modulator_market_features.py`

Mirror the existing sentiment_features integration. The modulator's `_build_prompt` already accepts kwargs and produces a `sentiment_block` — add a sibling `market_block`. The node passes `market_features=state.get("market_features") or None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/agents/test_modulator_market_features.py
from unittest.mock import MagicMock

from tradingagents.agents.modulator import _build_prompt
from tradingagents.strategies.contracts import QuantSignal


def _qs():
    return QuantSignal(
        coin="bitcoin",
        direction="long",
        magnitude=0.4,
        regime="bull",
        regime_confidence=0.7,
        hurst=0.55,
        deterministic_signals={"lgb_h7": 0.6, "lgb_h14": 0.55},
        as_of_date="2026-01-15",
    )


def test_build_prompt_includes_market_block_when_features_present():
    market_feats = {
        "market_regime": "TREND_UP",
        "market_conflict_score": 0.25,
        "market_default_direction": "LONG",
        "market_llm_direction": "LONG",
        "market_llm_conviction_calibrated": 0.62,
    }
    msgs = _build_prompt(
        coin_alias="Asset_A",
        quant_signal=_qs(),
        trader_plan="",
        factual_report="",
        subjective_report="",
        regime_note="",
        sentiment_features=None,
        market_features=market_feats,
    )
    sys = msgs[0]["content"]
    assert "MarketSnapshot features" in sys
    assert "market_llm_conviction_calibrated" in sys
    assert "0.62" in sys


def test_build_prompt_omits_market_block_when_no_features():
    msgs = _build_prompt(
        coin_alias="Asset_A",
        quant_signal=_qs(),
        trader_plan="", factual_report="",
        subjective_report="", regime_note="",
        sentiment_features=None,
        market_features=None,
    )
    sys = msgs[0]["content"]
    assert "MarketSnapshot features" not in sys
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agents/test_modulator_market_features.py -x -q`
Expected: FAIL — `_build_prompt` does not accept `market_features`.

- [ ] **Step 3: Modify `_build_prompt` and `modulator_node` to forward `market_features`**

Edit [tradingagents/agents/modulator.py](tradingagents/agents/modulator.py):

In `_build_prompt`, after the `sentiment_block` block, add:

```python
    market_block = ""
    if market_features:
        lines = "\n".join(f"- {k}: {v}" for k, v in market_features.items())
        market_block = (
            "\n\nLayer-2 MarketSnapshot features (deterministic):\n" + lines
        )
```

Extend the `sys = (... + sentiment_block)` concatenation to include `+ market_block`. Add a `market_features: Optional[dict] = None` keyword argument (matching the existing `sentiment_features` signature).

In `modulator_node` near the existing `sentiment_features=state.get("sentiment_features") or None` call, add a sibling line:

```python
            market_features=state.get("market_features") or None,
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/agents/test_modulator_market_features.py -x -q
pytest tests/agents -x -q
```

Expected: PASS for the new file (2 tests), and the existing agents suite stays green.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/modulator.py \
        tests/agents/test_modulator_market_features.py
git commit -m "feat(market-v2): modulator consumes market_features mirroring sentiment_features"
```

---

## Task 10: CLI Flags in generate_hybrid_signals.py

**Files:**
- Modify: `scripts/generate_hybrid_signals.py`

Mirror the existing `--sentiment-mode` / `--sentiment-skip-llm` / `--sentiment-anonymize` triplet.

- [ ] **Step 1: Inspect the existing flag block**

```bash
sed -n '40,80p' scripts/generate_hybrid_signals.py
```

- [ ] **Step 2: Add `--market-mode`, `--market-skip-llm`, `--market-anonymize`, `--market-horizon-days`**

Replace the argparse block (in the same `add_argument` style as the sentiment flags):

```python
    p.add_argument("--market-mode", choices=["legacy", "v2"], default="legacy",
                   help="Market analyst pipeline mode (default: legacy).")
    p.add_argument("--market-skip-llm", action="store_true",
                   help="Variant C: structured snapshot only, no narrow LLM call.")
    p.add_argument("--market-anonymize", action="store_true",
                   help="Mask coin name in the market analyst prompt (default on under v2).")
    p.add_argument("--market-horizon-days", type=int, default=7,
                   help="Horizon used in the market analyst's reasoning prompt.")
```

In the section where the config dict is assembled (around the existing `cfg["sentiment_mode"] = args.sentiment_mode` line, ~ line 295), add:

```python
    cfg["market_mode"] = args.market_mode
    cfg["market_anonymize"] = args.market_anonymize or (args.market_mode == "v2")
    cfg["market_skip_llm"] = bool(args.market_skip_llm)
    cfg["market_horizon_days"] = int(args.market_horizon_days)
```

- [ ] **Step 3: Smoke-check the CLI parses**

```bash
python scripts/generate_hybrid_signals.py --help | grep -E "market-mode|market-skip|market-anonymize|market-horizon"
```

Expected: all four lines present in the help output.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_hybrid_signals.py
git commit -m "feat(market-v2): CLI flags --market-mode / --market-skip-llm / --market-anonymize"
```

---

## Task 11: A/B Validation Harness (`run_market_v2_ab.py`)

**Files:**
- Create: `scripts/run_market_v2_ab.py`

Adapt `scripts/run_sentiment_v3_ab.py`. Four variants, coins BTC + ETH + BNB + SOL, 90-bar OOS slice (default `2026-01-16 → 2026-04-15` to match the sentiment-v3 A/B), all-gpt-4o-mini, sequential. Variants:

| ID | analysts | market_mode | market_skip_llm |
|---|---|---|---|
| A_pure_quant | onchain, prediction (no market) | legacy | False |
| B_legacy_market | market, onchain, prediction | legacy | False |
| C_v2_struct_only | market, onchain, prediction | v2 | True |
| D_v2_full | market, onchain, prediction | v2 | False |

- [ ] **Step 1: Copy and adapt the sentiment A/B harness**

```bash
cp scripts/run_sentiment_v3_ab.py scripts/run_market_v2_ab.py
```

Then edit `scripts/run_market_v2_ab.py`:
1. Update the module docstring to describe market-v2 variants A/B/C/D as in the table above.
2. Replace the `VARIANTS` dict with:

```python
VARIANTS: dict[str, dict] = {
    "A_pure_quant": {
        # No market analyst in chain.
        "analysts": ["onchain", "prediction"],
        "market_mode": "legacy",
        "market_skip_llm": False,
    },
    "B_legacy_market": {
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "legacy",
        "market_skip_llm": False,
    },
    "C_v2_struct_only": {
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "v2",
        "market_skip_llm": True,
    },
    "D_v2_full": {
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "v2",
        "market_skip_llm": False,
    },
}
```

3. In the subprocess invocation of `generate_hybrid_signals.py`, replace the sentiment-mode/skip flags with their market-mode equivalents:

```python
    subprocess.run([
        "python", "scripts/generate_hybrid_signals.py",
        "--coin", coin,
        "--start", start, "--end", end,
        "--analysts", *variant["analysts"],
        "--market-mode", variant["market_mode"],
        *(["--market-skip-llm"] if variant["market_skip_llm"] else []),
        "--output-dir", str(out_dir),
    ], check=True)
```

4. Update the default output path from `data/sentiment_v3_ab` to `data/market_v2_ab`.
5. Replace `BTC + ETH` coin list with `bitcoin, ethereum, binancecoin, solana` to match the 4-coin V5 universe ([project_v5_mix_per_coin_routing.md](../../../memory/project_v5_mix_per_coin_routing.md)).
6. Keep the existing paired-bootstrap Sharpe-CI machinery; just regenerate `summary.json` keyed by the new variant names.

- [ ] **Step 2: Dry-run the harness with `--smoke` (≤ 5 bars)**

If the script has a `--smoke` / `--dry-run` toggle in the sentiment original, keep it; otherwise add a flag that caps the date range to 5 bars and short-circuits the bootstrap. Verify the four subprocess invocations launch without crashing:

```bash
python scripts/run_market_v2_ab.py --smoke --coins bitcoin --output-dir /tmp/market_v2_ab_smoke
```

Expected: four directories created under `/tmp/market_v2_ab_smoke/{A_pure_quant,B_legacy_market,C_v2_struct_only,D_v2_full}/`, each containing a signals CSV. No tracebacks.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_market_v2_ab.py
git commit -m "feat(market-v2): 4-variant A/B harness over BTC/ETH/BNB/SOL"
```

---

## Task 12: Calibrator Fitting Script

**Files:**
- Create: `scripts/fit_market_calibrator.py`

Reads logged conviction-vs-realised-direction pairs from `data/market_v2_ab/D_v2_full/{coin}_*.csv` (or from the trade journal if available — pick whichever has the conviction column populated), fits one `IsotonicCalibrator` per coin, writes to `data/checkpoints/market_isotonic_{coin}.pkl`.

The realised outcome is the sign of the next-bar return at the snapshot's `horizon_days`. The script must use the same OHLCV loader as `build_market_snapshot` to avoid look-ahead.

- [ ] **Step 1: Write the script**

```python
# scripts/fit_market_calibrator.py
"""Fit per-coin isotonic calibrators from logged market-v2 convictions.

Reads CSVs produced by ``generate_hybrid_signals.py`` under
``--market-mode v2`` (which writes the ``market_llm_conviction_raw`` and
the realised forward return per bar), groups by coin, fits one
``IsotonicCalibrator`` per coin, and pickles to
``data/checkpoints/market_isotonic_{coin}.pkl``.
"""
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.strategies.market_calibration import fit_market_calibrator


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--signals-glob", required=True,
                   help="Glob of CSVs containing market_llm_conviction_raw "
                        "and forward_return columns, e.g. "
                        "'data/market_v2_ab/D_v2_full/*.csv'")
    p.add_argument("--horizon-days", type=int, default=7)
    p.add_argument("--output-dir", default="data/checkpoints")
    args = p.parse_args()

    paths = sorted(glob.glob(args.signals_glob))
    if not paths:
        raise SystemExit(f"No CSVs matched {args.signals_glob}")

    per_coin: dict[str, list[tuple[float, int]]] = {}
    for path in paths:
        coin = Path(path).stem.split("_")[0]
        df = pd.read_csv(path)
        if "market_llm_conviction_raw" not in df.columns:
            print(f"skip {path}: no conviction column")
            continue
        if "forward_return" not in df.columns:
            print(f"skip {path}: no forward_return column")
            continue
        df = df.dropna(subset=["market_llm_conviction_raw", "forward_return"])
        for _, row in df.iterrows():
            outcome = 1 if row["forward_return"] > 0 else 0
            per_coin.setdefault(coin, []).append(
                (float(row["market_llm_conviction_raw"]), int(outcome))
            )

    os.makedirs(args.output_dir, exist_ok=True)
    for coin, pairs in per_coin.items():
        if len(pairs) < 30:
            print(f"{coin}: only {len(pairs)} samples; skipping (need ≥ 30)")
            continue
        raw = np.array([p[0] for p in pairs], dtype=float)
        outc = np.array([p[1] for p in pairs], dtype=float)
        fit_market_calibrator(raw, outc, coin=coin, root=args.output_dir)
        print(f"fit calibrator for {coin}: n={len(pairs)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it imports clean**

```bash
python -c "import scripts.fit_market_calibrator"
```

Expected: no traceback.

- [ ] **Step 3: Commit**

```bash
git add scripts/fit_market_calibrator.py
git commit -m "feat(market-v2): per-coin calibrator fitter from D_v2_full signals"
```

---

## Task 13: Persistence of `market_llm_conviction_raw` in Generated Signals

**Files:**
- Modify: `scripts/generate_hybrid_signals.py`

The calibrator fitter (Task 12) and the A/B harness (Task 11) both rely on the per-bar CSV containing two extra columns:

- `market_llm_conviction_raw` — sourced from `state["market_features"]["market_llm_conviction_raw"]`
- `market_conflict_score` — sourced from `state["market_features"]["market_conflict_score"]`

Find the row-construction site in `generate_hybrid_signals.py` (the loop that writes one CSV row per `propagate()` call) and add these columns alongside any existing `sentiment_*` columns. If `market_features` is empty (legacy mode), write `NaN`.

- [ ] **Step 1: Locate the row-emission code**

```bash
grep -n "sentiment_features\|to_csv\|row.append\|writer.writerow" \
     scripts/generate_hybrid_signals.py | head
```

- [ ] **Step 2: Add the two new columns at the emission site**

Around the existing pattern that reads `state.get("sentiment_features", {}).get("polarity_news")` (or whatever the active columns are), add sibling reads for `market_features`. Example shape (adjust to whatever the existing dict-construction looks like):

```python
        mfeat = final_state.get("market_features") or {}
        row["market_llm_conviction_raw"] = mfeat.get("market_llm_conviction_raw")
        row["market_conflict_score"] = mfeat.get("market_conflict_score")
        row["market_default_direction"] = mfeat.get("market_default_direction")
```

- [ ] **Step 3: Smoke-test with 1 bar**

```bash
python scripts/generate_hybrid_signals.py --coin bitcoin \
    --start 2026-04-10 --end 2026-04-11 \
    --analysts market onchain prediction \
    --market-mode v2 \
    --output-dir /tmp/market_v2_smoke
head -1 /tmp/market_v2_smoke/bitcoin_2026-04-10_2026-04-11.csv
```

Expected: header includes `market_llm_conviction_raw`, `market_conflict_score`, `market_default_direction`.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_hybrid_signals.py
git commit -m "feat(market-v2): persist conviction + conflict_score in signal CSVs"
```

---

## Task 14: Spec Document for Thesis Record

**Files:**
- Create: `docs/superpowers/specs/2026-05-26-market-analyst-v2-design.md`

Mirror the brief stored in the conversation: the failure mode (P=0.997 ETH harm in the LOO study; reproduces FS-ReasoningAgent's "stronger-LLM-worse" finding), the design principles (asset-agnostic conviction-gated analyst; FLAT-by-default under conflict; endogenous per-coin weight via calibration), the mechanism stack M1-M6 from the brainstorming output, and the do-no-harm theorem with its informal proof sketch.

This is the document the thesis writeup will cite — keep it self-contained.

- [ ] **Step 1: Write the spec document**

Use the structure from `docs/superpowers/specs/2026-05-08-quant-v3-design.md` as a template (briefly skim it first to copy section headings: Background → Failure Mode → Design Principles → Mechanism Stack → Pseudocode → Validation Plan → Acceptance Criteria → Open Questions). Lift the M1-M6 content from the conversation's brainstorming output verbatim. Cite arXiv IDs inline (2410.12464, 2505.07078, 2509.25532, 2309.17322, 2506.16123).

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-05-26-market-analyst-v2-design.md
git commit -m "docs(market-v2): design spec for thesis record"
```

---

## Task 15: Run the Full A/B Validation

**Files:**
- Generated: `data/market_v2_ab/{variant}/{coin}_*.csv` and `data/market_v2_ab/summary.json`

Cost note: 4 variants × 4 coins × 90 bars × ~$0.02/bar ≈ **$30** on gpt-4o-mini. Cache reuse from the existing replay cache (`data/llm_replay_cache.db`) will absorb most of variants B/C/D once one of them has run.

- [ ] **Step 1: Pre-warm the replay cache by running B_legacy_market first on BTC**

```bash
python scripts/run_market_v2_ab.py \
    --variants B_legacy_market \
    --coins bitcoin \
    --start 2026-01-16 --end 2026-04-15 \
    --output-dir data/market_v2_ab
```

Expected: ~ 90 cached propagate calls, runtime ~ 20-30 min.

- [ ] **Step 2: Run the full 4-variant × 4-coin grid**

```bash
python scripts/run_market_v2_ab.py \
    --coins bitcoin ethereum binancecoin solana \
    --start 2026-01-16 --end 2026-04-15 \
    --output-dir data/market_v2_ab
```

Expected: `data/market_v2_ab/summary.json` populated with per-(variant, coin) Sharpe + paired-bootstrap CI vs `A_pure_quant`.

- [ ] **Step 3: Fit per-coin calibrators from `D_v2_full` output**

```bash
python scripts/fit_market_calibrator.py \
    --signals-glob 'data/market_v2_ab/D_v2_full/*.csv' \
    --horizon-days 7 \
    --output-dir data/checkpoints
```

Expected: `data/checkpoints/market_isotonic_bitcoin.pkl` (and ethereum / binancecoin / solana) all written.

- [ ] **Step 4: Re-run D_v2_full only, with the new calibrators in place**

```bash
python scripts/run_market_v2_ab.py \
    --variants D_v2_full \
    --coins bitcoin ethereum binancecoin solana \
    --start 2026-01-16 --end 2026-04-15 \
    --output-dir data/market_v2_ab_calibrated
```

This is the calibrated-D measurement that gets compared against A_pure_quant for the do-no-harm test.

- [ ] **Step 5: Inspect the do-no-harm verdict**

```bash
python -c "
import json, pathlib
for p in sorted(pathlib.Path('data/market_v2_ab_calibrated').glob('summary.json')):
    print(p)
    print(json.dumps(json.loads(p.read_text()), indent=2))
"
```

Acceptance criteria:
- **Per-coin** Δ Sharpe (D_v2_full − A_pure_quant) ≥ 0 on every coin in {bitcoin, ethereum, binancecoin, solana}.
- Paired-bootstrap 95% CI for ΔSharpe on the **worst-coin** has upper bound > 0 (no statistically significant harm) **AND** lower bound ≥ −0.15 (practically negligible if not net positive).
- At least one coin shows ΔSharpe > 0.3 with paired-t p < 0.1 (proof of upside).

If any of those fail, do NOT merge. Iterate on the prompt or the asymmetric thresholds, not on per-coin overrides.

- [ ] **Step 6: Commit the result artefacts**

```bash
git add data/market_v2_ab/summary.json \
        data/market_v2_ab_calibrated/summary.json \
        data/checkpoints/market_isotonic_*.pkl
git commit -m "validate(market-v2): 4-variant × 4-coin A/B + calibrators"
```

---

## Task 16: Finishing the Branch

- [ ] **Step 1: Full test suite green**

```bash
pytest tests/ -x -q
```

Expected: all green; no skips related to market-v2.

- [ ] **Step 2: Update CLAUDE.md and THESIS_FINDINGS.md**

In [TradingAgents/CLAUDE.md](TradingAgents/CLAUDE.md) — add a one-line entry under "Key Patterns" describing `market_mode == "v2"` and reference the spec doc.

In `THESIS_FINDINGS.md` (project root) — add a new section "§13 Market Analyst v2 (Asset-Agnostic Refactor)" summarising the A/B results from Task 15, the per-coin Δ Sharpe, and the conclusion (kept / rejected / iterate).

- [ ] **Step 3: Commit + integration**

```bash
git add TradingAgents/CLAUDE.md THESIS_FINDINGS.md
git commit -m "docs(market-v2): record A/B verdict in CLAUDE.md + THESIS_FINDINGS"
```

Then invoke the `superpowers:finishing-a-development-branch` skill to decide between merge / PR / further work.

---

## Validation Checklist (end-of-plan summary)

| Item | Where covered |
|---|---|
| Pydantic schema for MarketSnapshot + MarketAnalystOutput | Task 1 |
| 13-indicator whitelist with deterministic direction rules | Task 2 |
| Deterministic regime tag (ADX / ATR-pct / 30d return) | Task 3 |
| Category vote + conflict_score + asymmetric default direction | Task 4 |
| Snapshot orchestrator | Task 5 |
| Per-coin isotonic calibrator | Task 6 |
| State + config + propagation wiring | Task 7 |
| Analyst node v2 path with Pydantic-validated LLM output | Task 8 |
| Modulator consumes market_features | Task 9 |
| CLI flags `--market-mode` / `--market-skip-llm` / `--market-anonymize` | Task 10 |
| 4-variant A/B harness | Task 11 |
| Per-coin calibrator fitting script | Task 12 |
| Signal CSV persistence of conviction + conflict_score | Task 13 |
| Spec doc for thesis citation | Task 14 |
| A/B run + do-no-harm acceptance | Task 15 |
| Branch finishing + thesis docs | Task 16 |

Three mechanisms enforce "do no harm":
1. **Conflict-gated FLAT** (Task 4 + Task 8): the analyst's hard-coded asymmetric rule defaults to FLAT under conflict.
2. **Calibrated conviction** (Task 6 + Task 8): a coin where the LLM has no edge sees its calibrator collapse all convictions toward ~0.5 (or below), and the modulator multiplies through that, so the analyst's effective contribution → 0 endogenously.
3. **Anonymization** (Task 5 + Task 8): coin name is masked in the prompt, neutralising pretrained narrative priors that the LOO study identified as the dominant ETH-harm channel.
