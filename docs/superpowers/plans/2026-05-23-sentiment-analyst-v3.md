# Sentiment Analyst v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the noisy free-text crypto_sentiment_analyst with a structured `SentimentSnapshot` pipeline (CryptoBERT + FinBERT-Crypto polarity, Liu-Tsyvinski Google-Trends attention, F&G regime gate, GDELT event taxonomy) plus a narrow ticker-anonymized LLM event extractor, feeding both the agent-chain `sentiment_report` and the modulator LLM agent's prompt context.

**Architecture:** New `tradingagents/sentiment/` module owns the Pydantic snapshot, BERT scorers, event classifier, and attention features. A new `dataflows/gtrends_store.py` adds bitemporal Google Trends. The existing `crypto_sentiment_analyst.py` is rewritten under a `sentiment_mode={legacy,v3}` flag. The modulator LLM agent prompt is extended with a sentiment block when v3 is active. Validation runs a 4-variant 90-bar A/B on BTC+ETH.

**Tech Stack:** Python 3.10, Pydantic v2, HuggingFace `transformers` (CryptoBERT + FinBERT), pytrends, pandas, parquet, LangGraph, pytest.

**Spec:** `docs/superpowers/specs/2026-05-23-sentiment-analyst-v3-design.md`

---

## File Structure

NEW:
- `tradingagents/sentiment/__init__.py`
- `tradingagents/sentiment/snapshot.py` — Pydantic models + `build_snapshot()`
- `tradingagents/sentiment/scorers.py` — CryptoBERT + FinBERT-Crypto CPU scorers
- `tradingagents/sentiment/events.py` — GDELT theme → event taxonomy
- `tradingagents/sentiment/attention.py` — Liu-Tsyvinski features
- `tradingagents/sentiment/anonymize.py` — case-insensitive ticker masking
- `tradingagents/dataflows/gtrends_store.py` — bitemporal Google Trends store
- `tests/sentiment/__init__.py`
- `tests/sentiment/test_snapshot.py`
- `tests/sentiment/test_scorers.py`
- `tests/sentiment/test_events.py`
- `tests/sentiment/test_attention.py`
- `tests/sentiment/test_anonymize.py`
- `tests/dataflows/test_gtrends_store.py`
- `scripts/ingest_gtrends.py` — one-off pytrends ingestion driver
- `scripts/run_sentiment_v3_ab.py` — validation harness

REWRITE:
- `tradingagents/agents/analysts/crypto_sentiment_analyst.py`

TOUCH:
- `tradingagents/default_config.py` — `sentiment_mode`, `sentiment_anonymize`
- `tradingagents/agents/modulator.py` — append sentiment block to prompt when `sentiment_mode == "v3"`
- `pyproject.toml` — add `transformers`, `torch` (CPU), `pytrends`
- `scripts/backtest_hybrid.py` — pass-through `--sentiment-mode`

---

### Task 1: Add Python dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read current dependencies**

Run: `grep -nE 'transformers|torch|pytrends' pyproject.toml`
Expected: no matches (deps absent)

- [ ] **Step 2: Add the three deps**

In `pyproject.toml`, find the `[project] dependencies = [` array and append (preserving alphabetical order where present):

```toml
    "pytrends>=4.9.2",
    "torch>=2.2.0",
    "transformers>=4.42.0",
```

- [ ] **Step 3: Install**

Run: `pip install -e .`
Expected: success; verify with `python -c "import transformers, torch, pytrends; print(transformers.__version__, torch.__version__, pytrends.__version__)"`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build(deps): add transformers, torch, pytrends for sentiment v3"
```

---

### Task 2: Add config keys

**Files:**
- Modify: `tradingagents/default_config.py`
- Test: `tests/test_default_config.py` (add to existing or create)

- [ ] **Step 1: Locate DEFAULT_CONFIG**

Run: `grep -n 'DEFAULT_CONFIG\s*=' tradingagents/default_config.py`
Expected: a line like `DEFAULT_CONFIG = {`

- [ ] **Step 2: Write the failing test**

Append to `tests/test_default_config.py` (create if needed):

```python
from tradingagents.default_config import DEFAULT_CONFIG


def test_sentiment_mode_default_is_legacy():
    assert DEFAULT_CONFIG["sentiment_mode"] == "legacy"


def test_sentiment_anonymize_default_true():
    assert DEFAULT_CONFIG["sentiment_anonymize"] is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_default_config.py -v -k sentiment`
Expected: FAIL with KeyError

- [ ] **Step 4: Add the keys**

In `tradingagents/default_config.py`, inside the `DEFAULT_CONFIG = {...}` dict, add (near other top-level keys):

```python
    "sentiment_mode": "legacy",  # "legacy" | "v3" — selects sentiment analyst pipeline
    "sentiment_anonymize": True,  # mask BTC/ETH names in LLM prompts during backtest
```

If `apply_env_overrides()` exists in the same file, also add env mapping (search for similar patterns):

```python
    "TRADINGAGENTS_SENTIMENT_MODE": ("sentiment_mode", str),
    "TRADINGAGENTS_SENTIMENT_ANONYMIZE": ("sentiment_anonymize", lambda v: v.lower() in ("1", "true", "yes")),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_default_config.py -v -k sentiment`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tradingagents/default_config.py tests/test_default_config.py
git commit -m "feat(config): add sentiment_mode and sentiment_anonymize keys"
```

---

### Task 3: Pydantic schemas (CryptoEventType, EventFlag, SentimentSnapshot)

**Files:**
- Create: `tradingagents/sentiment/__init__.py`
- Create: `tradingagents/sentiment/snapshot.py`
- Test: `tests/sentiment/__init__.py`
- Test: `tests/sentiment/test_snapshot.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sentiment/__init__.py` (empty).

Create `tests/sentiment/test_snapshot.py`:

```python
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tradingagents.sentiment.snapshot import (
    CryptoEventType,
    EventFlag,
    SentimentSnapshot,
)


def _now():
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_event_type_enum_has_required_members():
    assert CryptoEventType.EXCHANGE_HACK.value == "exchange_hack"
    assert CryptoEventType.ETF_APPROVAL_DENIAL.value == "etf_approval_denial"
    assert CryptoEventType.NONE.value == "none"


def test_event_flag_round_trip():
    flag = EventFlag(
        event_type=CryptoEventType.EXCHANGE_HACK,
        asset="BTC",
        direction_hint=-1,
        severity=0.7,
        event_ts=_now(),
        as_of_ts=_now(),
        half_life_days=3.0,
        confidence=0.8,
    )
    assert flag.event_type == CryptoEventType.EXCHANGE_HACK
    assert flag.direction_hint == -1
    dumped = flag.model_dump_json()
    EventFlag.model_validate_json(dumped)


def test_event_flag_rejects_out_of_range_direction():
    with pytest.raises(ValidationError):
        EventFlag(
            event_type=CryptoEventType.NONE,
            asset="BTC",
            direction_hint=2,
            severity=0.0,
            event_ts=_now(),
            as_of_ts=_now(),
            confidence=0.0,
        )


def test_event_flag_rejects_bad_asset():
    with pytest.raises(ValidationError):
        EventFlag(
            event_type=CryptoEventType.NONE,
            asset="DOGE",
            direction_hint=0,
            severity=0.0,
            event_ts=_now(),
            as_of_ts=_now(),
            confidence=0.0,
        )


def test_snapshot_minimal_construction():
    snap = SentimentSnapshot(
        asset="BTC",
        as_of_ts=_now(),
        trade_date=_now(),
        horizon_days=14,
        polarity_news=0.1,
        polarity_social=0.0,
        polarity_news_n=10,
        polarity_social_n=0,
        google_search_z=0.5,
        google_neg_attention_ratio=0.02,
        twitter_volume_z=0.0,
        fng_level=55.0,
        fng_ema24w=50.0,
        fng_extreme_flag=0,
        agg_signal=0.2,
        agg_signal_lo95=-0.1,
        agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    assert snap.events == []


def test_snapshot_to_modulator_features_returns_dict():
    snap = SentimentSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(), horizon_days=14,
        polarity_news=0.1, polarity_social=0.0,
        polarity_news_n=10, polarity_social_n=0,
        google_search_z=0.5, google_neg_attention_ratio=0.02, twitter_volume_z=0.0,
        fng_level=55.0, fng_ema24w=50.0, fng_extreme_flag=0,
        agg_signal=0.2, agg_signal_lo95=-0.1, agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    feats = snap.to_modulator_features()
    assert isinstance(feats, dict)
    for key in ("polarity_news", "polarity_event", "attention_search_z",
                "fng_level", "fng_ema24w", "fng_extreme_flag",
                "n_events_regulatory_3d", "n_events_security_3d",
                "n_events_etf_3d", "agg_signal"):
        assert key in feats


def test_snapshot_to_prompt_table_returns_markdown():
    snap = SentimentSnapshot(
        asset="BTC", as_of_ts=_now(), trade_date=_now(), horizon_days=14,
        polarity_news=0.1, polarity_social=0.0,
        polarity_news_n=10, polarity_social_n=0,
        google_search_z=0.5, google_neg_attention_ratio=0.02, twitter_volume_z=0.0,
        fng_level=55.0, fng_ema24w=50.0, fng_extreme_flag=0,
        agg_signal=0.2, agg_signal_lo95=-0.1, agg_signal_hi95=0.5,
        model_version="v3-2026-05",
    )
    md = snap.to_prompt_table()
    assert "|" in md
    assert "Polarity" in md or "polarity" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_snapshot.py -v`
Expected: FAIL (ModuleNotFoundError: tradingagents.sentiment)

- [ ] **Step 3: Create the module**

Create `tradingagents/sentiment/__init__.py`:

```python
"""Structured sentiment pipeline (v3).

See docs/superpowers/specs/2026-05-23-sentiment-analyst-v3-design.md.
"""
from tradingagents.sentiment.snapshot import (
    CryptoEventType,
    EventFlag,
    SentimentSnapshot,
)

__all__ = ["CryptoEventType", "EventFlag", "SentimentSnapshot"]
```

Create `tradingagents/sentiment/snapshot.py`:

```python
"""Pydantic schemas for the v3 sentiment pipeline."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint


class CryptoEventType(str, Enum):
    # Regulatory
    SEC_ENFORCEMENT = "sec_enforcement"
    SEC_RULEMAKING = "sec_rulemaking"
    CFTC_ACTION = "cftc_action"
    MICA_EU = "mica_eu"
    NATIONAL_REG = "national_reg"
    # Market structure
    ETF_FLOW = "etf_flow"
    ETF_APPROVAL_DENIAL = "etf_approval_denial"
    EXCHANGE_LISTING = "exchange_listing"
    EXCHANGE_DELISTING = "exchange_delisting"
    PROOF_OF_RESERVES = "proof_of_reserves"
    # Security
    EXCHANGE_HACK = "exchange_hack"
    PROTOCOL_EXPLOIT = "protocol_exploit"
    BRIDGE_EXPLOIT = "bridge_exploit"
    # Network
    NETWORK_UPGRADE = "network_upgrade"
    HALVING = "halving"
    HARD_FORK = "hard_fork"
    # On-chain
    WHALE_MOVEMENT = "whale_movement"
    EXCHANGE_NETFLOW_EXTREME = "exchange_netflow_extreme"
    # Macro
    FED_FOMC = "fed_fomc"
    CPI_PRINT = "cpi_print"
    DXY_EXTREME = "dxy_extreme"
    NONE = "none"


_REGULATORY = {
    CryptoEventType.SEC_ENFORCEMENT, CryptoEventType.SEC_RULEMAKING,
    CryptoEventType.CFTC_ACTION, CryptoEventType.MICA_EU,
    CryptoEventType.NATIONAL_REG,
}
_SECURITY = {
    CryptoEventType.EXCHANGE_HACK, CryptoEventType.PROTOCOL_EXPLOIT,
    CryptoEventType.BRIDGE_EXPLOIT,
}
_ETF = {CryptoEventType.ETF_FLOW, CryptoEventType.ETF_APPROVAL_DENIAL}


class EventFlag(BaseModel):
    event_type: CryptoEventType
    asset: str = Field(pattern="^(BTC|ETH|MULTI|MACRO)$")
    direction_hint: conint(ge=-1, le=1)
    severity: confloat(ge=0.0, le=1.0)
    event_ts: datetime
    as_of_ts: datetime
    half_life_days: confloat(ge=0.0) = 3.0
    source_url: Optional[str] = None
    confidence: confloat(ge=0.0, le=1.0)


class SentimentSnapshot(BaseModel):
    asset: str = Field(pattern="^(BTC|ETH|MULTI)$")
    as_of_ts: datetime
    trade_date: datetime
    horizon_days: conint(ge=1, le=30)
    # Polarity
    polarity_news: confloat(ge=-1.0, le=1.0)
    polarity_social: confloat(ge=-1.0, le=1.0)
    polarity_news_n: conint(ge=0)
    polarity_social_n: conint(ge=0)
    # Attention
    google_search_z: float
    google_neg_attention_ratio: float
    twitter_volume_z: float
    # Regime
    fng_level: confloat(ge=0.0, le=100.0)
    fng_ema24w: confloat(ge=0.0, le=100.0)
    fng_extreme_flag: conint(ge=0, le=1)
    # Events
    events: List[EventFlag] = []
    # LLM analyst (optional)
    llm_event_summary: Optional[str] = None
    llm_event_conf: confloat(ge=0.0, le=1.0) = 0.0
    # Aggregate
    agg_signal: float
    agg_signal_lo95: float
    agg_signal_hi95: float
    model_version: str

    def _count_events(self, group: set[CryptoEventType], within_days: int = 3) -> int:
        from datetime import timedelta
        cutoff = self.trade_date - timedelta(days=within_days)
        return sum(
            1 for e in self.events
            if e.event_type in group and e.event_ts >= cutoff
        )

    def to_modulator_features(self) -> dict:
        """Numeric feature dict for the modulator LLM agent's prompt context."""
        polarity_event = (
            sum(e.direction_hint * e.severity * e.confidence for e in self.events)
            / max(len(self.events), 1)
        )
        return {
            "polarity_news": float(self.polarity_news),
            "polarity_event": float(polarity_event),
            "polarity_news_n": int(self.polarity_news_n),
            "attention_search_z": float(self.google_search_z),
            "attention_neg_ratio_z": float(self.google_neg_attention_ratio),
            "fng_level": float(self.fng_level),
            "fng_ema24w": float(self.fng_ema24w),
            "fng_extreme_flag": int(self.fng_extreme_flag),
            "n_events_regulatory_3d": self._count_events(_REGULATORY, 3),
            "n_events_security_3d": self._count_events(_SECURITY, 3),
            "n_events_etf_3d": self._count_events(_ETF, 3),
            "agg_signal": float(self.agg_signal),
        }

    def to_prompt_table(self) -> str:
        """Compact Markdown for the narrow LLM analyst prompt (≤ ~1500 tokens)."""
        feats = self.to_modulator_features()
        lines = [
            f"# SentimentSnapshot — {self.asset} @ {self.trade_date.date()}",
            "",
            "| Feature | Value |",
            "|---|---|",
        ]
        lines.extend(f"| {k} | {v} |" for k, v in feats.items())
        lines.append("")
        if self.events:
            lines.append("## Recent Event Flags")
            lines.append("| Type | Direction | Severity | Event Date | Confidence |")
            lines.append("|---|---|---|---|---|")
            for e in self.events[-10:]:
                lines.append(
                    f"| {e.event_type.value} | {e.direction_hint:+d} | "
                    f"{e.severity:.2f} | {e.event_ts.date()} | {e.confidence:.2f} |"
                )
        lines.append("")
        lines.append(
            f"**Aggregate signal:** {self.agg_signal:+.3f} "
            f"(95% CI [{self.agg_signal_lo95:+.3f}, {self.agg_signal_hi95:+.3f}])"
        )
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_snapshot.py -v`
Expected: PASS (all 7 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/__init__.py tradingagents/sentiment/snapshot.py tests/sentiment/
git commit -m "feat(sentiment): pydantic schemas for SentimentSnapshot v3"
```

---

### Task 4: Ticker anonymizer

**Files:**
- Create: `tradingagents/sentiment/anonymize.py`
- Test: `tests/sentiment/test_anonymize.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sentiment/test_anonymize.py`:

```python
from tradingagents.sentiment.anonymize import (
    anonymize_text,
    build_substitution_table,
)


def test_anonymizes_btc_case_insensitive():
    out = anonymize_text("Bitcoin hits ATH; BTC up. bitcoin etf.", coin="BTC")
    assert "Asset-A" in out
    assert "Bitcoin" not in out
    assert "BTC" not in out
    assert "bitcoin" not in out


def test_anonymizes_eth():
    out = anonymize_text("Ethereum upgrade ships; ETH rises.", coin="ETH")
    assert "Asset-B" in out
    assert "Ethereum" not in out
    assert "ETH" not in out


def test_anonymizes_exchanges():
    out = anonymize_text("Binance and Coinbase pause withdrawals.", coin="BTC")
    assert "Binance" not in out
    assert "Coinbase" not in out
    assert "Exchange-" in out


def test_does_not_corrupt_unrelated_words():
    out = anonymize_text("Bitcoiners are happy", coin="BTC")
    # Whole-word match: 'Bitcoiners' should NOT be replaced.
    assert "Bitcoiners" in out


def test_table_is_reversible_for_inspection():
    table = build_substitution_table("BTC")
    assert any(orig.lower() == "bitcoin" for orig in table)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_anonymize.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

Create `tradingagents/sentiment/anonymize.py`:

```python
"""Case-insensitive whole-word ticker/exchange anonymization."""
from __future__ import annotations

import re
from typing import Dict


_COIN_TO_ALIAS = {"BTC": "Asset-A", "ETH": "Asset-B"}

_COIN_NAMES = {
    "BTC": ["Bitcoin", "BTC"],
    "ETH": ["Ethereum", "ETH", "Ether"],
}

_EXCHANGES = [
    "Binance", "Coinbase", "Kraken", "Bitfinex", "Bitstamp",
    "OKX", "Bybit", "KuCoin", "Gate.io", "Huobi", "Bittrex",
    "Gemini", "FTX",
]


def build_substitution_table(coin: str) -> Dict[str, str]:
    """Return {original_token: replacement} for a coin. Used for debugging."""
    coin = coin.upper()
    alias = _COIN_TO_ALIAS[coin]
    table: Dict[str, str] = {}
    for name in _COIN_NAMES.get(coin, []):
        table[name] = alias
    for i, ex in enumerate(_EXCHANGES, 1):
        table[ex] = f"Exchange-{i}"
    return table


def anonymize_text(text: str, coin: str) -> str:
    """Case-insensitive whole-word replacement of coin + exchange names."""
    coin = coin.upper()
    if coin not in _COIN_TO_ALIAS:
        return text
    alias = _COIN_TO_ALIAS[coin]
    result = text
    # Coin tokens: whole-word, case-insensitive
    for name in _COIN_NAMES[coin]:
        result = re.sub(
            rf"\b{re.escape(name)}\b",
            alias,
            result,
            flags=re.IGNORECASE,
        )
    # Exchanges: whole-word, case-insensitive, stable index
    for i, ex in enumerate(_EXCHANGES, 1):
        result = re.sub(
            rf"\b{re.escape(ex)}\b",
            f"Exchange-{i}",
            result,
            flags=re.IGNORECASE,
        )
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_anonymize.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/anonymize.py tests/sentiment/test_anonymize.py
git commit -m "feat(sentiment): case-insensitive ticker and exchange anonymizer"
```

---

### Task 5: BERT scorers (CryptoBERT + FinBERT)

**Files:**
- Create: `tradingagents/sentiment/scorers.py`
- Test: `tests/sentiment/test_scorers.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sentiment/test_scorers.py`:

```python
import numpy as np
import pytest

from tradingagents.sentiment.scorers import (
    CryptoBertScorer,
    FinBertCryptoScorer,
    score_polarity_mean,
)


# These tests touch HuggingFace model download — skip in CI without HF cache.
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("transformers", reason="transformers not installed"),
    reason="needs transformers",
)


def test_cryptobert_scores_have_shape_n_by_3():
    scorer = CryptoBertScorer()
    out = scorer.score(["Bitcoin to the moon!", "Crypto crash imminent."])
    assert out.shape == (2, 3)
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-3)


def test_cryptobert_deterministic():
    scorer = CryptoBertScorer()
    a = scorer.score(["Ethereum upgrade is a success."])
    b = scorer.score(["Ethereum upgrade is a success."])
    np.testing.assert_allclose(a, b, atol=1e-6)


def test_score_polarity_mean_collapses_to_scalar():
    scorer = CryptoBertScorer()
    probs = scorer.score(["bullish", "bearish", "neutral"])
    mean = score_polarity_mean(probs)
    assert -1.0 <= mean <= 1.0


def test_finbert_scores_have_shape_n_by_3():
    scorer = FinBertCryptoScorer()
    out = scorer.score(["The exchange was hacked."])
    assert out.shape == (1, 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_scorers.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

Create `tradingagents/sentiment/scorers.py`:

```python
"""HuggingFace CryptoBERT and FinBERT-Crypto scorers with disk cache."""
from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

CACHE_PATH = Path(os.environ.get(
    "SENTIMENT_SCORER_CACHE",
    "data/sentiment/scorer_cache.sqlite",
))


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def _ensure_cache():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS scores ("
        "model_id TEXT, content_sha TEXT, p_bear REAL, p_neutral REAL, p_bull REAL,"
        " PRIMARY KEY (model_id, content_sha))"
    )
    conn.commit()
    return conn


class _BertScorer:
    MODEL_ID: str = ""

    def __init__(self, model_id: Optional[str] = None, max_length: int = 256):
        self.model_id = model_id or self.MODEL_ID
        self.max_length = max_length
        self._tok = None
        self._mdl = None
        self._conn = _ensure_cache()

    def _load(self):
        if self._mdl is not None:
            return
        import torch  # noqa: F401
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self._tok = AutoTokenizer.from_pretrained(self.model_id)
        self._mdl = AutoModelForSequenceClassification.from_pretrained(self.model_id)
        self._mdl.eval()

    def _cached(self, texts: List[str]) -> tuple[list[Optional[np.ndarray]], list[int]]:
        cached: list[Optional[np.ndarray]] = []
        misses: list[int] = []
        for i, t in enumerate(texts):
            sha = _sha1(t)
            row = self._conn.execute(
                "SELECT p_bear, p_neutral, p_bull FROM scores WHERE model_id=? AND content_sha=?",
                (self.model_id, sha),
            ).fetchone()
            if row is None:
                cached.append(None)
                misses.append(i)
            else:
                cached.append(np.array(row, dtype=np.float32))
        return cached, misses

    def _store(self, text: str, probs: np.ndarray):
        sha = _sha1(text)
        self._conn.execute(
            "INSERT OR REPLACE INTO scores (model_id, content_sha, p_bear, p_neutral, p_bull) "
            "VALUES (?, ?, ?, ?, ?)",
            (self.model_id, sha, float(probs[0]), float(probs[1]), float(probs[2])),
        )
        self._conn.commit()

    def score(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 3), dtype=np.float32)
        cached, misses = self._cached(texts)
        if misses:
            self._load()
            import torch
            miss_texts = [texts[i] for i in misses]
            enc = self._tok(
                miss_texts,
                padding=True, truncation=True, max_length=self.max_length,
                return_tensors="pt",
            )
            with torch.no_grad():
                logits = self._mdl(**enc).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy().astype(np.float32)
            for j, i in enumerate(misses):
                cached[i] = probs[j]
                self._store(texts[i], probs[j])
        return np.vstack(cached)


class CryptoBertScorer(_BertScorer):
    """Social-media polarity (3.2M StockTwits + Telegram posts)."""
    MODEL_ID = "ElKulako/cryptobert"


class FinBertCryptoScorer(_BertScorer):
    """Generic financial news polarity. Document gap: no public retrained
    FinBERT-Crypto checkpoint; vanilla FinBERT used as best available."""
    MODEL_ID = "ProsusAI/finbert"


@lru_cache(maxsize=1)
def get_cryptobert() -> CryptoBertScorer:
    return CryptoBertScorer()


@lru_cache(maxsize=1)
def get_finbert_crypto() -> FinBertCryptoScorer:
    return FinBertCryptoScorer()


def score_polarity_mean(probs: np.ndarray) -> float:
    """Collapse (n, 3) softmax probabilities to a scalar polarity in [-1, +1]."""
    if probs.shape[0] == 0:
        return 0.0
    # Direction: p_bull - p_bear
    direction = probs[:, 2] - probs[:, 0]
    return float(direction.mean())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_scorers.py -v`
Expected: PASS (4 tests; first run downloads models ~500 MB)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/scorers.py tests/sentiment/test_scorers.py
git commit -m "feat(sentiment): CryptoBERT and FinBERT scorers with sqlite cache"
```

---

### Task 6: GDELT event classifier

**Files:**
- Create: `tradingagents/sentiment/events.py`
- Test: `tests/sentiment/test_events.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sentiment/test_events.py`:

```python
from datetime import datetime, timezone

import pandas as pd

from tradingagents.sentiment.events import (
    classify_event_rule,
    extract_events,
    THEME_TO_EVENT,
)
from tradingagents.sentiment.snapshot import CryptoEventType


def test_theme_to_event_known_mappings():
    assert CryptoEventType.SEC_ENFORCEMENT in THEME_TO_EVENT.values()
    assert CryptoEventType.EXCHANGE_HACK in THEME_TO_EVENT.values()


def test_classify_rule_picks_security_for_hack_theme():
    et, conf = classify_event_rule(
        themes="ECON_CRYPTO;CYBER_ATTACK;EXCHANGE",
        headline="Major exchange hacked, funds drained",
    )
    assert et == CryptoEventType.EXCHANGE_HACK
    assert conf > 0.5


def test_classify_rule_picks_regulatory_for_legislation_theme():
    et, conf = classify_event_rule(
        themes="ECON_CRYPTO;LEGISLATION;ECON_GOVCRYPTO",
        headline="SEC files enforcement action against issuer",
    )
    assert et in {
        CryptoEventType.SEC_ENFORCEMENT,
        CryptoEventType.SEC_RULEMAKING,
        CryptoEventType.NATIONAL_REG,
    }


def test_classify_rule_returns_none_for_irrelevant():
    et, conf = classify_event_rule(
        themes="ENV_CLIMATECHANGE",
        headline="Weather report",
    )
    assert et == CryptoEventType.NONE


def test_extract_events_filters_by_as_of():
    now = datetime(2026, 1, 5, tzinfo=timezone.utc)
    df = pd.DataFrame([
        {"headline": "SEC charges exchange", "themes": "LEGISLATION",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 3, 12, tzinfo=timezone.utc),
         "url": ""},
        {"headline": "Future leak", "themes": "LEGISLATION",
         "event_ts": datetime(2026, 1, 5, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 5, 23, tzinfo=timezone.utc),
         "url": ""},
    ])
    flags = extract_events(df, coin="BTC", as_of=now)
    assert all(f.as_of_ts < now for f in flags)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_events.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

Create `tradingagents/sentiment/events.py`:

```python
"""GDELT V2Themes → CryptoEventType taxonomy + extractor."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd

from tradingagents.sentiment.snapshot import CryptoEventType, EventFlag


THEME_TO_EVENT: dict[str, CryptoEventType] = {
    # Regulatory
    "LEGISLATION": CryptoEventType.SEC_RULEMAKING,
    "ECON_GOVCRYPTO": CryptoEventType.NATIONAL_REG,
    "TAX_FNCACT_REGULATOR": CryptoEventType.SEC_RULEMAKING,
    # Security
    "CYBER_ATTACK": CryptoEventType.EXCHANGE_HACK,
    "TERROR_HACK": CryptoEventType.PROTOCOL_EXPLOIT,
    # Market structure
    "ECON_STOCKMARKET": CryptoEventType.ETF_FLOW,
    "ECON_BUSINESS_LISTING": CryptoEventType.EXCHANGE_LISTING,
    # Macro
    "ECON_INTEREST_RATES": CryptoEventType.FED_FOMC,
    "ECON_INFLATION": CryptoEventType.CPI_PRINT,
    "WB_2459_FOREIGN_EXCHANGE_RATES": CryptoEventType.DXY_EXTREME,
}


_KEYWORD_OVERRIDES: list[tuple[str, CryptoEventType, int]] = [
    ("hack", CryptoEventType.EXCHANGE_HACK, -1),
    ("exploit", CryptoEventType.PROTOCOL_EXPLOIT, -1),
    ("bridge", CryptoEventType.BRIDGE_EXPLOIT, -1),
    ("etf approval", CryptoEventType.ETF_APPROVAL_DENIAL, +1),
    ("etf denial", CryptoEventType.ETF_APPROVAL_DENIAL, -1),
    ("halving", CryptoEventType.HALVING, +1),
    ("fork", CryptoEventType.HARD_FORK, 0),
    ("upgrade", CryptoEventType.NETWORK_UPGRADE, +1),
    ("sec ", CryptoEventType.SEC_ENFORCEMENT, -1),
    ("cftc", CryptoEventType.CFTC_ACTION, -1),
    ("mica", CryptoEventType.MICA_EU, 0),
    ("fomc", CryptoEventType.FED_FOMC, 0),
    ("cpi", CryptoEventType.CPI_PRINT, 0),
]


def classify_event_rule(themes: str, headline: str) -> Tuple[CryptoEventType, float]:
    """Rule-based event classifier. Returns (event_type, confidence)."""
    hl_lower = (headline or "").lower()
    for kw, et, _ in _KEYWORD_OVERRIDES:
        if kw in hl_lower:
            return et, 0.85
    theme_tokens = (themes or "").split(";")
    for tok in theme_tokens:
        tok = tok.strip().split(",", 1)[0]
        if tok in THEME_TO_EVENT:
            return THEME_TO_EVENT[tok], 0.6
    return CryptoEventType.NONE, 0.0


def _direction_hint(et: CryptoEventType, headline: str) -> int:
    hl = (headline or "").lower()
    for kw, kw_et, direction in _KEYWORD_OVERRIDES:
        if kw_et == et and kw in hl:
            return direction
    if et in {CryptoEventType.EXCHANGE_HACK, CryptoEventType.PROTOCOL_EXPLOIT,
              CryptoEventType.BRIDGE_EXPLOIT, CryptoEventType.SEC_ENFORCEMENT}:
        return -1
    if et in {CryptoEventType.ETF_APPROVAL_DENIAL, CryptoEventType.NETWORK_UPGRADE,
              CryptoEventType.HALVING}:
        return +1
    return 0


def extract_events(
    gdelt_rows: pd.DataFrame,
    coin: str,
    as_of: datetime,
    *,
    max_events: int = 50,
) -> List[EventFlag]:
    """Build EventFlag list from a GDELT rows dataframe, PIT-enforced."""
    if gdelt_rows.empty:
        return []
    coin_upper = coin.upper() if coin.upper() in {"BTC", "ETH"} else "MULTI"
    flags: List[EventFlag] = []
    df = gdelt_rows.copy()
    # PIT filter
    if "as_of_ts" in df.columns:
        df = df[pd.to_datetime(df["as_of_ts"], utc=True) < as_of]
    df = df.head(max_events)
    for row in df.itertuples(index=False):
        themes = getattr(row, "themes", "") or ""
        headline = getattr(row, "headline", "") or ""
        et, conf = classify_event_rule(themes, headline)
        if et == CryptoEventType.NONE:
            continue
        flags.append(EventFlag(
            event_type=et,
            asset=coin_upper,
            direction_hint=_direction_hint(et, headline),
            severity=0.5,
            event_ts=pd.to_datetime(getattr(row, "event_ts"), utc=True).to_pydatetime(),
            as_of_ts=pd.to_datetime(getattr(row, "as_of_ts"), utc=True).to_pydatetime(),
            half_life_days=3.0,
            source_url=getattr(row, "url", None) or None,
            confidence=conf,
        ))
    return flags
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_events.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/events.py tests/sentiment/test_events.py
git commit -m "feat(sentiment): GDELT theme to CryptoEventType classifier"
```

---

### Task 7: Bitemporal Google Trends store

**Files:**
- Create: `tradingagents/dataflows/gtrends_store.py`
- Test: `tests/dataflows/test_gtrends_store.py`

- [ ] **Step 1: Write the failing test**

Create `tests/dataflows/test_gtrends_store.py`:

```python
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import pytest

from tradingagents.dataflows import gtrends_store


def _utc(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc)


def test_write_then_query_returns_rows(tmp_path):
    root = tmp_path / "gtrends"
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 1), "as_of_ts": _utc(2026, 1, 2),
         "value": 70.0, "value_z90": 0.5, "value_z365": 0.3},
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 2), "as_of_ts": _utc(2026, 1, 3),
         "value": 80.0, "value_z90": 0.8, "value_z365": 0.6},
    ])
    gtrends_store.write_rows(df, root=root)
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=root,
    )
    assert len(out) == 2


def test_query_enforces_24h_embargo(tmp_path):
    root = tmp_path / "gtrends"
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 1), "as_of_ts": _utc(2026, 1, 4, 12),
         "value": 70.0, "value_z90": 0.5, "value_z365": 0.3},
    ])
    gtrends_store.write_rows(df, root=root)
    # trade_date = Jan 5, embargo = 24h, cutoff = Jan 4 00:00.
    # Row's as_of = Jan 4 12:00 → AFTER cutoff → must be excluded.
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=root,
    )
    assert out.empty


def test_query_returns_empty_when_path_missing(tmp_path):
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=tmp_path / "missing",
    )
    assert out.empty
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/dataflows/test_gtrends_store.py -v`
Expected: FAIL (ModuleNotFoundError or missing function)

- [ ] **Step 3: Implement**

Create `tradingagents/dataflows/gtrends_store.py`:

```python
"""Bitemporal Google Trends store.

Schema (parquet, one file per (coin, as_of_date)):
    coin: str
    query: str
    event_ts: datetime64[ns, UTC]
    as_of_ts: datetime64[ns, UTC]
    value: float
    value_z90: float
    value_z365: float

PIT discipline: queries enforce as_of_ts < trade_date - embargo (default 24h)
to defend against Google Trends mid-window renormalization.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

DEFAULT_ROOT = Path("data/sentiment/gtrends")
SCHEMA_COLS = ["coin", "query", "event_ts", "as_of_ts",
               "value", "value_z90", "value_z365"]
EMBARGO_HOURS = 24


def _file_for(root: Path, coin: str, as_of_date: pd.Timestamp) -> Path:
    return Path(root) / coin / f"as_of={as_of_date.strftime('%Y-%m-%d')}.parquet"


def write_rows(df: pd.DataFrame, *, root: Path = DEFAULT_ROOT) -> None:
    """Append rows to the store, partitioned by (coin, as_of_date)."""
    if df.empty:
        return
    missing = set(SCHEMA_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df = df.copy()
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
    for (coin, as_of_date), group in df.groupby(
        ["coin", df["as_of_ts"].dt.floor("D")]
    ):
        target = _file_for(Path(root), coin, as_of_date)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = pd.read_parquet(target)
            combined = pd.concat([existing, group], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["coin", "query", "event_ts", "as_of_ts"],
                keep="last",
            )
        else:
            combined = group
        combined.to_parquet(target, index=False)


def query_attention(
    coin: str,
    trade_date: datetime,
    lookback_days: int,
    *,
    root: Path = DEFAULT_ROOT,
    embargo_hours: int = EMBARGO_HOURS,
) -> pd.DataFrame:
    """Return rows for `coin` with event_ts in [trade_date - lookback, trade_date)
    and as_of_ts < trade_date - embargo_hours."""
    root = Path(root)
    coin_dir = root / coin
    if not coin_dir.exists():
        return pd.DataFrame(columns=SCHEMA_COLS)
    cutoff = pd.Timestamp(trade_date).tz_convert("UTC") - pd.Timedelta(hours=embargo_hours)
    start = pd.Timestamp(trade_date).tz_convert("UTC") - pd.Timedelta(days=lookback_days)
    parts = []
    for f in coin_dir.glob("as_of=*.parquet"):
        df = pd.read_parquet(f)
        df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
        df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
        df = df[
            (df["as_of_ts"] < cutoff)
            & (df["event_ts"] >= start)
            & (df["event_ts"] < pd.Timestamp(trade_date).tz_convert("UTC"))
        ]
        if not df.empty:
            parts.append(df)
    if not parts:
        return pd.DataFrame(columns=SCHEMA_COLS)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("event_ts").drop_duplicates(
        subset=["coin", "query", "event_ts"], keep="last"
    )
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/dataflows/test_gtrends_store.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/dataflows/gtrends_store.py tests/dataflows/test_gtrends_store.py
git commit -m "feat(dataflows): bitemporal Google Trends parquet store"
```

---

### Task 8: Liu-Tsyvinski attention features

**Files:**
- Create: `tradingagents/sentiment/attention.py`
- Test: `tests/sentiment/test_attention.py`

- [ ] **Step 1: Write the failing test**

Create `tests/sentiment/test_attention.py`:

```python
from datetime import datetime, timezone

import pandas as pd

from tradingagents.sentiment.attention import compute_attention_features


def test_returns_default_when_empty():
    df = pd.DataFrame(columns=["coin", "query", "event_ts", "as_of_ts",
                                "value", "value_z90", "value_z365"])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_search_z"] == 0.0
    assert feats["google_neg_attention_ratio"] == 0.0
    assert feats["twitter_volume_z"] == 0.0


def test_uses_latest_value_z90_for_search():
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 70.0, "value_z90": 1.2, "value_z365": 0.8},
    ])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_search_z"] == 1.2


def test_neg_attention_ratio_uses_hack_query():
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 100.0, "value_z90": 0.0, "value_z365": 0.0},
        {"coin": "bitcoin", "query": "bitcoin hack",
         "event_ts": datetime(2026, 1, 3, tzinfo=timezone.utc),
         "as_of_ts": datetime(2026, 1, 4, tzinfo=timezone.utc),
         "value": 5.0, "value_z90": 1.8, "value_z365": 1.0},
    ])
    feats = compute_attention_features(
        df, coin="bitcoin",
        trade_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )
    assert feats["google_neg_attention_ratio"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_attention.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Create `tradingagents/sentiment/attention.py`:

```python
"""Liu-Tsyvinski-style Google Trends attention features."""
from __future__ import annotations

from datetime import datetime
from typing import Dict

import pandas as pd

_COIN_TO_QUERY = {"bitcoin": "bitcoin", "ethereum": "ethereum",
                  "btc": "bitcoin", "eth": "ethereum"}
_COIN_TO_NEG = {"bitcoin": "bitcoin hack", "ethereum": "ethereum hack",
                "btc": "bitcoin hack", "eth": "ethereum hack"}


def compute_attention_features(
    gtrends_df: pd.DataFrame,
    coin: str,
    trade_date: datetime,
) -> Dict[str, float]:
    """Compute Liu-Tsyvinski attention features from gtrends rows."""
    out = {
        "google_search_z": 0.0,
        "google_neg_attention_ratio": 0.0,
        "twitter_volume_z": 0.0,
    }
    if gtrends_df.empty:
        return out
    coin_l = coin.lower()
    pos_q = _COIN_TO_QUERY.get(coin_l, coin_l)
    neg_q = _COIN_TO_NEG.get(coin_l, f"{coin_l} hack")
    df = gtrends_df.copy()
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df = df.sort_values("event_ts")
    pos = df[df["query"] == pos_q]
    if not pos.empty:
        out["google_search_z"] = float(pos["value_z90"].iloc[-1])
    neg = df[df["query"] == neg_q]
    if not neg.empty and not pos.empty:
        # Liu-Tsyvinski ratio: neg / pos, then z-score-flavoured via stored z90.
        pos_val = float(pos["value"].iloc[-1]) or 1.0
        neg_val = float(neg["value"].iloc[-1])
        out["google_neg_attention_ratio"] = neg_val / pos_val
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_attention.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/attention.py tests/sentiment/test_attention.py
git commit -m "feat(sentiment): Liu-Tsyvinski Google Trends attention features"
```

---

### Task 9: build_snapshot orchestrator

**Files:**
- Modify: `tradingagents/sentiment/snapshot.py`
- Test: `tests/sentiment/test_snapshot.py` (add)

- [ ] **Step 1: Add the failing test**

Append to `tests/sentiment/test_snapshot.py`:

```python
from unittest.mock import patch

import numpy as np
import pandas as pd


def test_build_snapshot_with_empty_stores(tmp_path, monkeypatch):
    from tradingagents.sentiment import snapshot as snap_mod

    monkeypatch.setenv("SENTIMENT_SCORER_CACHE", str(tmp_path / "scorer.sqlite"))

    with patch.object(snap_mod, "_query_alpaca_headlines", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "_query_gdelt_rows", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "_query_fng_series", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "_query_gtrends_rows", return_value=pd.DataFrame()):
        out = snap_mod.build_snapshot(
            coin="bitcoin",
            trade_date=_now(),
            horizon_days=14,
        )
    assert out.asset == "BTC"
    assert out.polarity_news == 0.0
    assert out.polarity_news_n == 0
    assert out.events == []
    assert out.fng_level == 50.0


def test_build_snapshot_scores_alpaca_news(tmp_path, monkeypatch):
    from tradingagents.sentiment import snapshot as snap_mod

    monkeypatch.setenv("SENTIMENT_SCORER_CACHE", str(tmp_path / "scorer.sqlite"))

    alpaca = pd.DataFrame([
        {"headline": "Bitcoin surges 10%",
         "summary": "BTC reaches new high",
         "event_ts": _now(), "as_of_ts": _now(), "source": "alpaca"},
        {"headline": "Crypto regulation tightens",
         "summary": "SEC issues new rules",
         "event_ts": _now(), "as_of_ts": _now(), "source": "alpaca"},
    ])
    fake_probs = np.array([[0.1, 0.2, 0.7], [0.6, 0.3, 0.1]], dtype=np.float32)

    class FakeScorer:
        def score(self, texts):
            return fake_probs[: len(texts)]

    with patch.object(snap_mod, "_query_alpaca_headlines", return_value=alpaca), \
         patch.object(snap_mod, "_query_gdelt_rows", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "_query_fng_series", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "_query_gtrends_rows", return_value=pd.DataFrame()), \
         patch.object(snap_mod, "get_cryptobert", return_value=FakeScorer()):
        out = snap_mod.build_snapshot(
            coin="bitcoin",
            trade_date=_now(),
            horizon_days=14,
        )
    # polarity_news = mean(p_bull - p_bear) = mean(0.7-0.1, 0.1-0.6) = mean(0.6, -0.5) = 0.05
    assert abs(out.polarity_news - 0.05) < 0.01
    assert out.polarity_news_n == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/sentiment/test_snapshot.py -v -k build_snapshot`
Expected: FAIL (no build_snapshot)

- [ ] **Step 3: Implement**

Append to `tradingagents/sentiment/snapshot.py`:

```python
# --- Orchestrator -----------------------------------------------------------

import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

MODEL_VERSION = "v3-2026-05"


def _coin_to_asset(coin: str) -> str:
    c = coin.upper()
    if c in {"BTC", "BITCOIN"}: return "BTC"
    if c in {"ETH", "ETHEREUM"}: return "ETH"
    return "MULTI"


def _query_alpaca_headlines(coin: str, trade_date: datetime,
                             lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import sentiment_store
    start = trade_date - timedelta(days=lookback_days)
    ts_end = trade_date + timedelta(days=1) - timedelta(microseconds=1)
    coin_l = coin.lower()
    if coin_l not in sentiment_store.COIN_TO_SYMBOL:
        return pd.DataFrame()
    try:
        return sentiment_store.query_news(
            coin=coin_l, ts_start=start, ts_end=ts_end, as_of=trade_date,
            limit=100, root=sentiment_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("Alpaca query failed: %s", e)
        return pd.DataFrame()


def _query_gdelt_rows(coin: str, trade_date: datetime,
                      lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import sentiment_store
    from tradingagents.dataflows.crypto_sentiment_pit import GDELT_ROOT
    start = trade_date - timedelta(days=lookback_days)
    ts_end = trade_date + timedelta(days=1) - timedelta(microseconds=1)
    coin_l = coin.lower()
    if not Path(GDELT_ROOT).exists():
        return pd.DataFrame()
    try:
        df = sentiment_store.query_news(
            coin=coin_l, ts_start=start, ts_end=ts_end, as_of=trade_date,
            limit=200, root=GDELT_ROOT,
        )
        # The GDELT store also carries themes if it was ingested with them.
        return df
    except Exception as e:
        logger.warning("GDELT query failed: %s", e)
        return pd.DataFrame()


def _query_fng_series(trade_date: datetime, lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import fng_store
    try:
        return fng_store.query_fng(
            trade_date=trade_date, lookback_days=lookback_days,
            root=fng_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("F&G query failed: %s", e)
        return pd.DataFrame()


def _query_gtrends_rows(coin: str, trade_date: datetime,
                        lookback_days: int) -> pd.DataFrame:
    from tradingagents.dataflows import gtrends_store
    try:
        return gtrends_store.query_attention(
            coin=coin.lower(), trade_date=trade_date,
            lookback_days=lookback_days, root=gtrends_store.DEFAULT_ROOT,
        )
    except Exception as e:
        logger.warning("gtrends query failed: %s", e)
        return pd.DataFrame()


def _score_polarity(texts: list[str], scorer) -> tuple[float, int]:
    if not texts:
        return 0.0, 0
    probs = scorer.score(texts)
    if probs.shape[0] == 0:
        return 0.0, 0
    direction = probs[:, 2] - probs[:, 0]
    return float(direction.mean()), int(probs.shape[0])


def _fng_extreme_flag(level: float) -> int:
    return int(level < 25 or level > 75)


def _bootstrap_ci(values: list[float], n_boot: int = 200,
                  alpha: float = 0.05) -> tuple[float, float]:
    import numpy as np
    if not values:
        return -0.5, 0.5
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(42)
    boots = [arr[rng.integers(0, len(arr), len(arr))].mean()
             for _ in range(n_boot)]
    lo = float(np.quantile(boots, alpha / 2))
    hi = float(np.quantile(boots, 1 - alpha / 2))
    return lo, hi


def build_snapshot(
    coin: str,
    trade_date: datetime,
    horizon_days: int = 14,
) -> SentimentSnapshot:
    """Assemble a SentimentSnapshot for one (coin, trade_date) tuple.

    All queries are PIT-locked. Returns a zero-default snapshot if every
    upstream source is empty.
    """
    from tradingagents.sentiment.attention import compute_attention_features
    from tradingagents.sentiment.events import extract_events
    from tradingagents.sentiment.scorers import (
        get_cryptobert, get_finbert_crypto,
    )

    lookback = max(horizon_days * 4, 30)

    alpaca_df = _query_alpaca_headlines(coin, trade_date, lookback)
    gdelt_df = _query_gdelt_rows(coin, trade_date, lookback)
    fng_df = _query_fng_series(trade_date, lookback_days=24 * 7)  # 24 weeks for EMA
    gtrends_df = _query_gtrends_rows(coin, trade_date, lookback)

    # Polarity — news (Alpaca via FinBERT, GDELT via FinBERT)
    finbert = get_finbert_crypto()
    news_texts: list[str] = []
    if not alpaca_df.empty:
        news_texts.extend(
            f"{h} {s or ''}".strip()
            for h, s in zip(alpaca_df["headline"], alpaca_df.get("summary", [""] * len(alpaca_df)))
        )
    if not gdelt_df.empty:
        news_texts.extend(gdelt_df["headline"].tolist())
    pol_news, pol_news_n = _score_polarity(news_texts, finbert)

    # Polarity — social (placeholder; Reddit PIT not built in P3)
    pol_social, pol_social_n = 0.0, 0

    # Attention
    att = compute_attention_features(gtrends_df, coin, trade_date)

    # Regime — F&G
    if not fng_df.empty:
        fng_level = float(fng_df["value"].iloc[-1])
        # 24w EMA
        fng_ema24w = float(fng_df["value"].ewm(span=24 * 7, adjust=False).mean().iloc[-1])
    else:
        fng_level, fng_ema24w = 50.0, 50.0
    fng_extreme = _fng_extreme_flag(fng_level)

    # Events
    events = extract_events(gdelt_df, coin=coin, as_of=trade_date)

    # Aggregate signal — simple weighted combination
    polarity_event = (
        sum(e.direction_hint * e.severity * e.confidence for e in events)
        / max(len(events), 1)
    )
    agg = (
        0.30 * pol_news
        + 0.20 * polarity_event
        + 0.20 * att["google_search_z"]
        - 0.20 * att["google_neg_attention_ratio"]
        + 0.10 * (fng_level - 50.0) / 50.0
    )
    component_values = [
        pol_news,
        polarity_event,
        att["google_search_z"],
        -att["google_neg_attention_ratio"],
        (fng_level - 50.0) / 50.0,
    ]
    lo, hi = _bootstrap_ci(component_values)

    return SentimentSnapshot(
        asset=_coin_to_asset(coin),
        as_of_ts=trade_date,
        trade_date=trade_date,
        horizon_days=horizon_days,
        polarity_news=pol_news,
        polarity_social=pol_social,
        polarity_news_n=pol_news_n,
        polarity_social_n=pol_social_n,
        google_search_z=att["google_search_z"],
        google_neg_attention_ratio=att["google_neg_attention_ratio"],
        twitter_volume_z=att["twitter_volume_z"],
        fng_level=fng_level,
        fng_ema24w=fng_ema24w,
        fng_extreme_flag=fng_extreme,
        events=events,
        agg_signal=agg,
        agg_signal_lo95=lo,
        agg_signal_hi95=hi,
        model_version=MODEL_VERSION,
    )
```

Also add to `tradingagents/sentiment/__init__.py`:

```python
from tradingagents.sentiment.snapshot import build_snapshot  # noqa: E402
__all__.append("build_snapshot")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/sentiment/test_snapshot.py -v`
Expected: PASS (all snapshot tests including the new build_snapshot ones)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/sentiment/snapshot.py tradingagents/sentiment/__init__.py tests/sentiment/test_snapshot.py
git commit -m "feat(sentiment): build_snapshot orchestrator with PIT-locked queries"
```

---

### Task 10: Google Trends ingestion script (one-off)

**Files:**
- Create: `scripts/ingest_gtrends.py`

(No new tests — this is a one-off ingestion script; correctness is verified via the gtrends_store tests in Task 7.)

- [ ] **Step 1: Implement**

Create `scripts/ingest_gtrends.py`:

```python
"""One-off pytrends ingestion driver.

Pulls daily Google Trends interest-over-time for BTC and ETH (plus the
'<coin> hack' negative-attention query) in rolling 90-day windows,
stores into the bitemporal store with the pull timestamp as as_of_ts.

Usage:
    python scripts/ingest_gtrends.py --coins bitcoin ethereum \
        --start 2024-01-01 --end 2026-05-23
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from tradingagents.dataflows import gtrends_store

logger = logging.getLogger(__name__)

QUERIES = {
    "bitcoin": ["bitcoin", "bitcoin hack"],
    "ethereum": ["ethereum", "ethereum hack"],
}


def _zscore(series: pd.Series, window: int) -> pd.Series:
    roll = series.rolling(window=window, min_periods=window // 2)
    return (series - roll.mean()) / roll.std(ddof=0).replace(0, 1)


def fetch_window(coin: str, query: str, start: datetime, end: datetime) -> pd.DataFrame:
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    tf = f"{start.strftime('%Y-%m-%d')} {end.strftime('%Y-%m-%d')}"
    pytrends.build_payload([query], cat=0, timeframe=tf, geo="", gprop="")
    df = pytrends.interest_over_time()
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index().rename(columns={"date": "event_ts", query: "value"})
    df["coin"] = coin
    df["query"] = query
    return df[["coin", "query", "event_ts", "value"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--window-days", type=int, default=90)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    as_of = datetime.now(timezone.utc)

    cursor = start
    accum = []
    while cursor < end:
        nxt = min(cursor + timedelta(days=args.window_days), end)
        for coin in args.coins:
            for q in QUERIES.get(coin, [coin]):
                logger.info("Fetch %s '%s' %s → %s", coin, q, cursor.date(), nxt.date())
                df = fetch_window(coin, q, cursor, nxt)
                if df.empty:
                    continue
                df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
                df["as_of_ts"] = as_of
                df["value_z90"] = _zscore(df["value"], 90)
                df["value_z365"] = _zscore(df["value"], 365)
                df = df.fillna({"value_z90": 0.0, "value_z365": 0.0})
                accum.append(df)
        cursor = nxt

    if accum:
        big = pd.concat(accum, ignore_index=True)
        gtrends_store.write_rows(big)
        logger.info("Wrote %d rows to gtrends store", len(big))
    else:
        logger.warning("No rows ingested")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke run (dry — single-day window, may fail without network)**

Run: `python scripts/ingest_gtrends.py --coins bitcoin --start 2026-05-20 --end 2026-05-23 --window-days 90`
Expected: completes without error and writes ≥1 row OR logs "No rows ingested" if pytrends rate-limits. Either is acceptable for the smoke check.

- [ ] **Step 3: Commit**

```bash
git add scripts/ingest_gtrends.py
git commit -m "feat(scripts): pytrends ingestion driver for sentiment v3"
```

---

### Task 11: Rewrite crypto_sentiment_analyst.py with v3 path under flag

**Files:**
- Modify: `tradingagents/agents/analysts/crypto_sentiment_analyst.py`
- Test: `tests/agents/test_crypto_sentiment_analyst_v3.py`

- [ ] **Step 1: Write the failing test**

Create `tests/agents/test_crypto_sentiment_analyst_v3.py`:

```python
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.analysts.crypto_sentiment_analyst import (
    create_crypto_sentiment_analyst,
)


def _state():
    return {
        "trade_date": "2026-01-15",
        "company_of_interest": "bitcoin",
        "messages": [],
    }


def test_v3_mode_calls_build_snapshot(monkeypatch):
    fake_snap = MagicMock()
    fake_snap.to_prompt_table.return_value = "## Snapshot table"
    fake_snap.to_modulator_features.return_value = {
        "polarity_news": 0.1, "agg_signal": 0.2,
    }

    fake_llm = MagicMock()
    fake_response = MagicMock(content="bullish events", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response
    fake_llm.invoke.return_value = fake_response

    with patch("tradingagents.agents.analysts.crypto_sentiment_analyst.build_snapshot",
               return_value=fake_snap), \
         patch("tradingagents.agents.analysts.crypto_sentiment_analyst.get_config",
               return_value={"sentiment_mode": "v3", "sentiment_anonymize": False,
                             "deep_think_llm": "gpt-4o-mini",
                             "quick_think_llm": "gpt-4o-mini"}):
        node = create_crypto_sentiment_analyst(fake_llm)
        out = node(_state())

    assert "sentiment_report" in out
    assert "## Snapshot table" in out["sentiment_report"] or "Snapshot" in out["sentiment_report"]
    assert "sentiment_features" in out
    assert out["sentiment_features"]["agg_signal"] == 0.2


def test_legacy_mode_unchanged(monkeypatch):
    fake_llm = MagicMock()
    fake_response = MagicMock(content="legacy text", tool_calls=[])
    fake_llm.bind_tools.return_value.invoke.return_value = fake_response

    with patch("tradingagents.agents.analysts.crypto_sentiment_analyst.get_config",
               return_value={"sentiment_mode": "legacy"}):
        node = create_crypto_sentiment_analyst(fake_llm)
        out = node(_state())

    assert "sentiment_report" in out
    # Legacy returns features as empty dict (or absent).
    assert out.get("sentiment_features", {}) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agents/test_crypto_sentiment_analyst_v3.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Replace `tradingagents/agents/analysts/crypto_sentiment_analyst.py` entirely:

```python
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
        # Variant C: structured-only — no narrative LLM call.
        sentiment_report = (
            f"# Sentiment v3 (structured-only) — {snap.asset} {state['trade_date']}\n\n"
            f"{snapshot_md}\n"
        )
        return {
            "messages": [],
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agents/test_crypto_sentiment_analyst_v3.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Smoke: legacy regression**

Run: `pytest tests/ -k "sentiment and not v3" -v`
Expected: PASS (any pre-existing sentiment analyst tests still green under legacy mode)

- [ ] **Step 6: Commit**

```bash
git add tradingagents/agents/analysts/crypto_sentiment_analyst.py tests/agents/test_crypto_sentiment_analyst_v3.py
git commit -m "feat(agents): crypto_sentiment_analyst v3 with structured snapshot + narrow LLM"
```

---

### Task 12: Add sentiment_features to agent state schema

**Files:**
- Modify: `tradingagents/agents/utils/agent_states.py`

- [ ] **Step 1: Locate the state TypedDict**

Run: `grep -nE "class.*State.*TypedDict|sentiment_report" tradingagents/agents/utils/agent_states.py`
Expected: a TypedDict with `sentiment_report` already declared.

- [ ] **Step 2: Add field**

In `tradingagents/agents/utils/agent_states.py`, add to the same TypedDict that holds `sentiment_report`:

```python
    sentiment_features: dict  # numeric features from SentimentSnapshot.to_modulator_features (v3)
```

- [ ] **Step 3: Initialise in propagation**

Open `tradingagents/graph/propagation.py`, find where the initial state dict is built (search for `sentiment_report=`). Add:

```python
        sentiment_features={},
```

- [ ] **Step 4: Quick regression**

Run: `pytest tests/ -k "propagation or graph" -v --maxfail=3`
Expected: PASS or no relevant tests existing — failures unrelated to this field are fine, but no NameError on sentiment_features.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/utils/agent_states.py tradingagents/graph/propagation.py
git commit -m "feat(state): add sentiment_features to AgentState"
```

---

### Task 13: Wire sentiment features into the modulator LLM agent

**Files:**
- Modify: `tradingagents/agents/modulator.py`
- Test: `tests/agents/test_modulator_v3_features.py`

- [ ] **Step 1: Write the failing test**

Create `tests/agents/test_modulator_v3_features.py`:

```python
from tradingagents.agents.modulator import _build_prompt
from tradingagents.strategies.contracts import QuantSignal


def _quant_signal():
    return QuantSignal(
        coin="bitcoin",
        as_of_date="2026-01-15",
        direction=1,
        magnitude=1.0,
        regime="trend_bull",
        deterministic_signals={"lgb_h7": 0.55, "unlock_flag": False},
    )


def test_prompt_includes_sentiment_block_when_features_provided():
    feats = {
        "polarity_news": 0.12, "polarity_event": -0.05,
        "attention_search_z": 1.4, "fng_level": 65.0,
        "fng_ema24w": 50.0, "fng_extreme_flag": 0,
        "n_events_regulatory_3d": 1, "n_events_security_3d": 0,
        "n_events_etf_3d": 0, "agg_signal": 0.18,
    }
    msgs = _build_prompt(
        coin_alias="Asset-A",
        quant_signal=_quant_signal(),
        trader_plan="hold",
        factual_report="",
        subjective_report="",
        regime_note="trend bull",
        belief="",
        sentiment_features=feats,
    )
    full = "\n".join(m["content"] for m in msgs)
    assert "polarity_news" in full
    assert "65.0" in full or "65" in full


def test_prompt_omits_sentiment_block_when_features_absent():
    msgs = _build_prompt(
        coin_alias="Asset-A",
        quant_signal=_quant_signal(),
        trader_plan="hold",
        factual_report="",
        subjective_report="",
        regime_note="trend bull",
        belief="",
    )
    full = "\n".join(m["content"] for m in msgs)
    assert "polarity_news" not in full
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agents/test_modulator_v3_features.py -v`
Expected: FAIL (unexpected kwarg `sentiment_features` OR no sentiment block)

- [ ] **Step 3: Modify `_build_prompt` to accept optional `sentiment_features`**

In `tradingagents/agents/modulator.py`:

Find the existing `_build_prompt(...)` signature and append a keyword-only param at the end:

```python
def _build_prompt(
    coin_alias: str,
    quant_signal: QuantSignal,
    trader_plan: str,
    factual_report: str,
    subjective_report: str,
    regime_note: str,
    belief: str = "",
    sentiment_features: Optional[dict] = None,
) -> list[dict]:
```

Inside the function, after the existing `det_block` line, add:

```python
    sentiment_block = ""
    if sentiment_features:
        sent_lines = "\n".join(f"- {k}: {v}" for k, v in sentiment_features.items())
        sentiment_block = (
            "\n\nLayer-2 SentimentSnapshot features (deterministic):\n"
            f"{sent_lines}\n"
        )
```

Then find where the system prompt string is assembled and append `+ sentiment_block` so the block is included when present. Search for `sys = (` and append `+ sentiment_block` at the appropriate concatenation point — keep the search of "Multiplier semantics" intact.

Then find the call site within the same file (the node function that calls `_build_prompt(...)`) and pull `sentiment_features` from the agent state:

```python
        sentiment_features=state.get("sentiment_features") or None,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/agents/test_modulator_v3_features.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/modulator.py tests/agents/test_modulator_v3_features.py
git commit -m "feat(modulator): inject sentiment_features into LLM modulator prompt"
```

---

### Task 14: Backtest harness CLI flag

**Files:**
- Modify: `scripts/backtest_hybrid.py`

- [ ] **Step 1: Locate argparse setup**

Run: `grep -n "add_argument\|argparse" scripts/backtest_hybrid.py | head -20`
Expected: an `argparse.ArgumentParser()` instance.

- [ ] **Step 2: Add flags**

In `scripts/backtest_hybrid.py`, in the argparse section, add (preserving file style):

```python
    p.add_argument(
        "--sentiment-mode",
        choices=["legacy", "v3"],
        default="legacy",
        help="Sentiment analyst pipeline: 'legacy' free-text or 'v3' structured snapshot",
    )
    p.add_argument(
        "--sentiment-anonymize",
        action="store_true",
        help="Mask coin/exchange names in LLM prompts (default True in v3 mode)",
    )
    p.add_argument(
        "--sentiment-skip-llm",
        action="store_true",
        help="In v3 mode, skip the narrow LLM event analyst — emit only the structured snapshot table. Used to distinguish C (structured-only) from D (full v3) in the A/B harness.",
    )
```

After the args are parsed, find where the `config` dict is assembled (or where TradingAgentsGraph receives config) and add:

```python
    config["sentiment_mode"] = args.sentiment_mode
    config["sentiment_anonymize"] = args.sentiment_anonymize or (args.sentiment_mode == "v3")
    config["sentiment_v3_skip_llm"] = args.sentiment_skip_llm
```

- [ ] **Step 3: Smoke-run with --help**

Run: `python scripts/backtest_hybrid.py --help | grep sentiment`
Expected: shows `--sentiment-mode` and `--sentiment-anonymize` lines.

- [ ] **Step 4: Commit**

```bash
git add scripts/backtest_hybrid.py
git commit -m "feat(harness): --sentiment-mode flag for backtest_hybrid"
```

---

### Task 15: Validation harness script

**Files:**
- Create: `scripts/run_sentiment_v3_ab.py`

- [ ] **Step 1: Implement**

Create `scripts/run_sentiment_v3_ab.py`:

```python
"""Sentiment v3 A/B validation harness.

Runs 4 variants over BTC + ETH, 2026-01-16 → 2026-04-15 (90 bars),
all-gpt-4o-mini, sequential. Variants:
    A — pure V5 quant (no sentiment analyst)
    B — legacy sentiment analyst (current production)
    C — v3 structured-only (modulator features only)
    D — v3 full (modulator features + narrow LLM)

Each variant invokes `scripts/backtest_hybrid.py` with the right
combination of --analysts, --sentiment-mode, and --modulator-features
flags, and outputs signals to data/sentiment_v3_ab/{variant}/.

After all 4 runs complete, computes paired bootstrap 10k CI for
Sharpe ratio per (coin, variant) vs (coin, A) and (coin, B) and writes
data/sentiment_v3_ab/summary.json.
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

VARIANTS = {
    "A_pure_quant": {
        "analysts": ["market", "onchain", "prediction"],
        "sentiment_mode": "legacy",
        "sentiment_skip_llm": False,
    },
    "B_legacy_sentiment": {
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "legacy",
        "sentiment_skip_llm": False,
    },
    "C_v3_features_only": {
        # crypto_sentiment analyst still in chain to populate sentiment_features,
        # but its narrow LLM step is bypassed via --sentiment-skip-llm.
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "v3",
        "sentiment_skip_llm": True,
    },
    "D_v3_full": {
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "v3",
        "sentiment_skip_llm": False,
    },
}


def run_variant(variant: str, coin: str, start: str, end: str,
                out_root: Path) -> Path:
    cfg = VARIANTS[variant]
    out = out_root / variant
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python", "scripts/backtest_hybrid.py",
        "--coin", coin,
        "--start", start,
        "--end", end,
        "--analysts", *cfg["analysts"],
        "--sentiment-mode", cfg["sentiment_mode"],
        "--output-dir", str(out),
        "--baseline-preset", "v5_2coin",
    ]
    if cfg["sentiment_skip_llm"]:
        cmd.append("--sentiment-skip-llm")
    logger.info("Running %s for %s: %s", variant, coin, " ".join(cmd))
    subprocess.run(cmd, check=True)
    return out / f"signals_{coin}.csv"


def sharpe(returns: np.ndarray, ann: int = 365) -> float:
    if returns.size == 0 or returns.std(ddof=0) == 0:
        return 0.0
    return float(returns.mean() / returns.std(ddof=0) * np.sqrt(ann))


def paired_bootstrap_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 10_000,
                        alpha: float = 0.05) -> tuple[float, float, float]:
    rng = np.random.default_rng(2026)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(a), len(a))
        diffs.append(sharpe(a[idx]) - sharpe(b[idx]))
    arr = np.asarray(diffs)
    return float(arr.mean()), float(np.quantile(arr, alpha / 2)), float(np.quantile(arr, 1 - alpha / 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    ap.add_argument("--start", default="2026-01-16")
    ap.add_argument("--end", default="2026-04-15")
    ap.add_argument("--out", default="data/sentiment_v3_ab")
    ap.add_argument("--skip-runs", action="store_true",
                    help="Skip variant runs and only compute summary from existing CSVs")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    signals: dict[str, dict[str, pd.DataFrame]] = {}
    for v in VARIANTS:
        signals[v] = {}
        for c in args.coins:
            f = out_root / v / f"signals_{c}.csv"
            if not args.skip_runs:
                run_variant(v, c, args.start, args.end, out_root)
            if f.exists():
                signals[v][c] = pd.read_csv(f)

    summary = {"runs": {}, "comparisons": {}}
    for v in VARIANTS:
        summary["runs"][v] = {}
        for c, df in signals[v].items():
            if "ret" in df.columns:
                rets = df["ret"].values
            elif "return" in df.columns:
                rets = df["return"].values
            else:
                rets = np.diff(df["equity"].values) / df["equity"].values[:-1] if "equity" in df.columns else np.array([])
            summary["runs"][v][c] = {
                "sharpe": sharpe(rets),
                "n_bars": int(len(rets)),
            }

    for v in ["C_v3_features_only", "D_v3_full"]:
        summary["comparisons"][v] = {}
        for c in args.coins:
            for baseline in ["A_pure_quant", "B_legacy_sentiment"]:
                if c not in signals[v] or c not in signals[baseline]:
                    continue
                a = signals[v][c]
                b = signals[baseline][c]
                if "ret" not in a.columns or "ret" not in b.columns:
                    continue
                mean, lo, hi = paired_bootstrap_ci(a["ret"].values, b["ret"].values)
                summary["comparisons"][v][f"{c}_vs_{baseline}"] = {
                    "delta_sharpe_mean": mean,
                    "ci_lo": lo, "ci_hi": hi,
                    "p_positive": float((np.array([mean]) > 0).mean()),
                }

    with open(out_root / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info("Summary written to %s", out_root / "summary.json")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke (--help only)**

Run: `python scripts/run_sentiment_v3_ab.py --help`
Expected: argparse help text printed without error.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_sentiment_v3_ab.py
git commit -m "feat(scripts): 4-variant sentiment v3 A/B validation harness"
```

---

### Task 16: Final test sweep and branch push

**Files:** none (verification only)

- [ ] **Step 1: Run the full sentiment test suite**

Run: `pytest tests/sentiment/ tests/dataflows/test_gtrends_store.py tests/agents/test_crypto_sentiment_analyst_v3.py tests/agents/test_modulator_v3_features.py -v`
Expected: ALL PASS (or test_scorers.py SKIPs if transformers download is blocked — that's acceptable).

- [ ] **Step 2: Run V2 baseline regression**

Run: `python -c "from tradingagents.default_config import DEFAULT_CONFIG; assert DEFAULT_CONFIG['sentiment_mode'] == 'legacy'; print('legacy default confirmed')"`
Expected: prints "legacy default confirmed". The legacy path is the default, so V2 backtests are unaffected.

- [ ] **Step 3: Push branch**

Run: `git push -u origin feature/sentiment-analyst-v3`
Expected: success.

- [ ] **Step 4: Final commit if there are any docs changes**

Run: `git status` and review.
If clean: nothing to commit.

---

## Validation kickoff (out of plan; surfaced to user)

After Task 16 the architecture ships. The 50h Hetzner CX22 4-variant A/B validation is left to the user to kick off — it's expensive infra-touching work, not local code, and requires manual cost + cluster authorization. The plan's `scripts/run_sentiment_v3_ab.py` is the entry point. Suggested command:

```bash
# On Hetzner CX22 isolated worktree
python scripts/run_sentiment_v3_ab.py \
    --coins bitcoin ethereum \
    --start 2026-01-16 --end 2026-04-15 \
    --out data/sentiment_v3_ab
```

Once results land, update `THESIS_FINDINGS.md` §23.12 with the bootstrap CIs and flip `DEFAULT_CONFIG["sentiment_mode"] = "v3"` in a follow-up PR if acceptance criteria pass.
