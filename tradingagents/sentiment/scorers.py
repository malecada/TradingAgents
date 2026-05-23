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
