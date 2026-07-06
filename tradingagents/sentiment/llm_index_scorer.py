"""LLM relevance filter + 0-4 sentiment index (supervisor-template contract).

Prompt structure and the "Relevant. [summary], Index: N" output contract are
adapted verbatim from News_fulltext/sentiment_index_tariff.py so the parser
carries over. Scale: 0 very negative ... 4 very positive for the coin's price.

Error contract: if the LLM call fails after all retries, ``score_article``
returns ``{"relevant": False, "idx": None, "raw": "__error__: <exc>"}`` and
does NOT write to the cache. Downstream (the corpus scoring runner) uses the
``__error__:`` prefix on ``raw`` to skip-and-count failed articles.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import time
from pathlib import Path

CACHE_PATH = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")) / "sentiment" / "llm_score_cache.sqlite"
MAX_CHARS = 12_000
_MAX_ATTEMPTS = 3
_RETRY_DELAYS = (2, 8, 30)  # backoff schedule; slept between attempts

SCORING_PROMPT = """You are a cryptocurrency market analyst evaluating news articles for their relevance to {coin_name} ({symbol}) market conditions. Additionally, you will assess the sentiment of relevant articles based on their potential impact on {coin_name} price over the next days to weeks. Follow these steps:
STEP 1:

Examine the article and determine if it is relevant to understanding or predicting {coin_name} price, adoption, regulation, security incidents, exchange flows, macro conditions affecting crypto markets, or major protocol/network developments.
The article is relevant if it is about {coin_name} directly, or about the broader crypto market in a way that clearly affects {coin_name}.
The article is for example not relevant if it is about an unrelated small-cap token, general stock-market news without crypto linkage, or product advertising.

STEP 2:

    If the article is relevant:
        Respond with: "Relevant" and provide a concise summary of the content, ensuring the summary does not exceed 500 tokens.
        Proceed to Step 3 to create the sentiment index.
    If the article is not relevant:
        Respond with: "Not relevant" and provide reasons why.

STEP 3:

For relevant articles, create a sentiment index using the following scale based on how the article impacts {coin_name} price expectations:

    0 (Very Negative): The article highlights factors or events that severely worsen the price outlook (e.g. exchange collapse, hack, ban).
    1 (Negative): The article discusses elements that negatively impact the outlook, but not to an extreme degree.
    2 (Neutral): The article is balanced, with no strong positive or negative impact.
    3 (Positive): The article emphasizes factors that improve the outlook.
    4 (Very Positive): The article discusses elements that greatly enhance the outlook (e.g. ETF approval, major adoption).

Format your responses as follows:

    For relevant articles: "Relevant. [Your summary], Index: [sentiment_index]"
    For non-relevant articles: "Not relevant. [Your explanation]"

Ensure your evaluations are clear, concise, and consistent.
article text: {article}"""

_IDX_RE = re.compile(r"Index:\s*(\d+)")


def parse_index(answer: str) -> int | None:
    low = answer.lower()
    if "not relevant" in low or "relevant" not in low:
        return None
    m = _IDX_RE.search(answer)
    if m:
        m_val = int(m.group(1))
    else:
        # Fallback only when "Index" IS present but the regex missed
        # (e.g. "Index = 3"). Never scavenge stray digits from the answer.
        if "Index" not in answer:
            return None
        tail = answer.split("Index")[-1]
        m_tail = re.search(r"\d+", tail)
        if not m_tail:
            return None
        m_val = int(m_tail.group(0))
    return m_val if 0 <= m_val <= 4 else None


def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


class LlmIndexScorer:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(CACHE_PATH)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS llm_scores ("
            "model_id TEXT, content_sha TEXT, coin TEXT, relevant INT, idx INT, raw TEXT,"
            " PRIMARY KEY (model_id, content_sha, coin))")
        self._client = None

    def _chat(self, prompt: str) -> str:
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        resp = self._client.chat.completions.create(
            model=self.model, temperature=0,
            messages=[{"role": "user", "content": prompt}])
        if not resp.choices:
            raise RuntimeError("empty choices in LLM response")
        return resp.choices[0].message.content or ""

    def score_article(self, text: str, coin: str, coin_name: str, symbol: str) -> dict:
        sha = _sha(text[:MAX_CHARS])
        row = self._conn.execute(
            "SELECT relevant, idx, raw FROM llm_scores WHERE model_id=? AND content_sha=? AND coin=?",
            (self.model, sha, coin)).fetchone()
        if row:
            return {"relevant": bool(row[0]), "idx": row[1], "raw": row[2]}
        prompt = SCORING_PROMPT.format(
            coin_name=coin_name, symbol=symbol, article=text[:MAX_CHARS])
        answer: str | None = None
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                answer = self._chat(prompt)
                break
            except Exception as exc:  # noqa: BLE001 — graceful degradation
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(_RETRY_DELAYS[attempt])
        if answer is None:
            # Errors are never cached — the corpus runner skips-and-counts these.
            return {"relevant": False, "idx": None, "raw": f"__error__: {last_exc}"}
        idx = parse_index(answer)
        rec = {"relevant": idx is not None, "idx": idx, "raw": answer}
        self._conn.execute(
            "INSERT OR REPLACE INTO llm_scores VALUES (?,?,?,?,?,?)",
            (self.model, sha, coin, int(rec["relevant"]), idx, answer))
        self._conn.commit()
        return rec
