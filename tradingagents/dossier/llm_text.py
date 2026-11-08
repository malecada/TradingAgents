"""Article typing and anonymized summaries with DeepSeek V4.1-Flash via OpenRouter (plan §6.2 step 3).

Input text is anonymized BEFORE the call so the summary inherits the masking; the
verification pass then rejects any summary that re-introduces an identity term.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import threading
import time

import requests

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4.1-flash"
PROVIDER = "Baidu"
QUANTIZATION = "fp8"
TYPES = ["price_recap", "event", "analysis_opinion", "promotional", "unrelated"]
SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": TYPES},
        "summary": {"type": "string"},
        "novelty": {"type": "string", "enum": ["new_information", "follow_up", "none"]},
        "affected_aliases": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["type", "summary", "novelty", "affected_aliases"],
    "additionalProperties": False,
}
PROMPT = """You classify and summarize one crypto-market news item. Entities are already replaced by role tokens such as Asset_K, Exchange_1, Person_2; dates are relative; keep those tokens verbatim and never guess real names.

Types:
- price_recap: the item mainly describes price moves, market caps or technical levels without a new underlying event.
- event: a concrete occurrence (exploit, regulatory action, listing/delisting, unlock, upgrade, partnership, insolvency, funding round, major holder move, product launch, outage).
- analysis_opinion: commentary, forecasts, interviews, explainers.
- promotional: sponsored content, press releases without a verifiable event, giveaways.
- unrelated: not about crypto assets or markets.

Write a summary of at most two sentences stating only facts the item asserts (no price commentary unless the type is price_recap). Set novelty to new_information if the item reports something that happened or was announced within the last few days relative to the item, follow_up if it mainly updates an earlier story, otherwise none. List the Asset_ tokens the item is materially about in affected_aliases (empty if none).

Return only JSON matching the schema.

Item:
{text}"""
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 529})
CACHE = Path("data/dossier/llm_text_cache.jsonl")


class TextLLMError(RuntimeError):
    pass


def validate(obj) -> dict:
    if not isinstance(obj, dict) or set(obj) != {"type", "summary", "novelty", "affected_aliases"}:
        raise ValueError("bad keys")
    if obj["type"] not in TYPES or obj["novelty"] not in ("new_information", "follow_up", "none"):
        raise ValueError("bad enum")
    if not isinstance(obj["summary"], str) or not isinstance(obj["affected_aliases"], list) \
            or not all(isinstance(a, str) for a in obj["affected_aliases"]):
        raise ValueError("bad types")
    return obj


def request_body(text: str) -> dict:
    return {"model": MODEL, "messages": [{"role": "user", "content": PROMPT.format(text=text)}],
            "temperature": 0, "max_tokens": 1200, "reasoning": {"effort": "low"},
            "response_format": {"type": "json_schema", "json_schema": {"name": "news_item", "strict": True, "schema": SCHEMA}},
            "provider": {"order": [PROVIDER], "allow_fallbacks": False, "quantizations": [QUANTIZATION]},
            "usage": {"include": True}}


def prompt_sha256() -> str:
    return hashlib.sha256(json.dumps({"prompt": PROMPT, "schema": SCHEMA, "model": MODEL}, sort_keys=True).encode()).hexdigest()


@dataclass
class TextLLM:
    api_key: str = field(repr=False)
    cost_cap_usd: float = 50.0
    max_attempts: int = 5
    session: object = None
    sleep: object = time.sleep
    cache_path: Path = CACHE
    spent_usd: float = 0.0
    calls: int = 0
    cache_hits: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _cache: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.cache_path and Path(self.cache_path).exists():
            for line in Path(self.cache_path).read_text().splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._cache[rec["key"]] = rec["value"]

    def classify(self, text: str) -> dict:
        key = hashlib.sha256((prompt_sha256() + "|" + text).encode("utf-8")).hexdigest()
        with self._lock:
            if key in self._cache:
                self.cache_hits += 1
                return dict(self._cache[key])
            if self.spent_usd > self.cost_cap_usd:
                raise TextLLMError(f"spend cap reached: {self.spent_usd:.4f}")
        session = self.session or requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = request_body(text)
        for attempt in range(1, self.max_attempts + 1):
            try:
                r = session.post(ENDPOINT, json=body, timeout=120, headers=headers)
            except requests.RequestException:
                if attempt == self.max_attempts:
                    raise TextLLMError("network failure") from None
                self.sleep(min(5 * 2 ** (attempt - 1), 60))
                continue
            if r.status_code == 200:
                data = r.json()
                if "error" in data and "choices" not in data:
                    if attempt < self.max_attempts:
                        self.sleep(min(5 * 2 ** (attempt - 1), 60))
                        continue
                    raise TextLLMError(f"provider error: {str(data['error'])[:200]}")
                if data.get("model") != MODEL or data.get("provider") != PROVIDER:
                    raise TextLLMError(f"drift: {data.get('model')} / {data.get('provider')}")
                choice = data["choices"][0]
                if choice.get("finish_reason") != "stop":
                    raise TextLLMError(f"finish_reason {choice.get('finish_reason')}")
                try:
                    value = validate(json.loads(choice["message"]["content"]))
                except (ValueError, TypeError, KeyError) as exc:
                    raise TextLLMError(f"invalid answer: {exc}") from None
                cost = float((data.get("usage") or {}).get("cost") or 0.0)
                if not math.isfinite(cost):
                    raise TextLLMError("non-finite cost")
                with self._lock:
                    self.spent_usd += cost
                    self.calls += 1
                    self._cache[key] = value
                    if self.cache_path:
                        Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
                        with Path(self.cache_path).open("a") as fh:
                            fh.write(json.dumps({"key": key, "value": value, "cost": cost}) + "\n")
                return dict(value)
            if r.status_code == 402:
                raise TextLLMError("insufficient credits (402)")
            if r.status_code in RETRY_STATUS and attempt < self.max_attempts:
                self.sleep(min(5 * 2 ** (attempt - 1), 60))
                continue
            raise TextLLMError(f"HTTP {r.status_code}")
        raise TextLLMError("retries exhausted")
