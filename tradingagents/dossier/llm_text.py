"""Article typing and anonymized summaries with DeepSeek V4.1-Flash via OpenRouter (plan §6.2 step 3).

Input text is anonymized BEFORE the call so the summary inherits the masking; the
verification pass then rejects any summary that re-introduces an identity term.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
import re
from pathlib import Path
import threading
import time

import requests

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4.1-flash"
PROVIDERS = ["Morph", "CoreWeave", "DeepInfra"]   # same fp8 weights, fastest first (Baidu rate-limits at 8 workers)
PROVIDER = PROVIDERS[0]
LOG = os.environ.get("LLM_TEXT_LOG")
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
PROMPT = """You classify and de-identify one crypto-market news item. Entities are already replaced by role tokens such as Asset_K, Exchange_1, Person_2; dates are relative; keep those tokens verbatim and never guess real names.

Types:
- price_recap: the item mainly describes price moves, market caps or technical levels without a new underlying event.
- event: a concrete occurrence (exploit, regulatory action, listing/delisting, unlock, upgrade, partnership, insolvency, funding round, major holder move, product launch, outage).
- analysis_opinion: commentary, forecasts, interviews, explainers.
- promotional: sponsored content, press releases without a verifiable event, giveaways.
- unrelated: not about crypto assets or markets.

Write a de-identified summary of at most two sentences that states only facts the item asserts. De-identification rules, all mandatory:
- No proper nouns of any kind except the role tokens: replace every project, protocol, company, product, person, place, fund, bank, regulator, blockchain network or media outlet that is not already a role token with a generic description of its role (for example "a lending protocol", "a hardware-wallet maker", "a Hong Kong real-estate group", "a national central bank", "a metaverse game", "a sports-fan token platform").
- No ticker symbols, token names, brand names, product names or event names (write "a planned network upgrade", not its codename).
- Round every figure to one significant digit with a magnitude word ("about $100 million", "roughly 10%", "several thousand users"); no exact counts, prices or dates.
- Keep the generic nature of the event precise: what happened, to which role token, with what magnitude and direction.

Set novelty to new_information if the item reports something that happened or was announced within the last few days relative to the item, follow_up if it mainly updates an earlier story, otherwise none. List the Asset_ tokens the item is materially about in affected_aliases (empty if none).

Return only JSON matching the schema.

Item:
{text}"""
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 529})
CACHE = Path("data/dossier/llm_text_cache.jsonl")


class TextLLMError(RuntimeError):
    pass


class CreditError(TextLLMError):
    """Account credit exhausted: the whole build must stop, not degrade dossier by dossier."""


def _log(**fields):
    if LOG:
        with open(LOG, "a") as fh:
            fh.write(json.dumps({"ts": time.time(), **fields}) + "\n")


_SENTENCE_START = re.compile(r"(?:^|[.!?]\s+)([A-Z][a-z]+)")
_PROPER = re.compile(r"\b(?!(?:Asset|Exchange|Person|Regulator|Network)_[A-Za-z0-9]+\b)[A-Z][A-Za-z0-9&'-]*(?: [A-Z][A-Za-z0-9&'-]*)*")
_ALLOWED_CAPS = {"I", "US", "U.S.", "UK", "EU", "ETF", "ETFs", "NFT", "NFTs", "DeFi", "CeFi", "DAO", "DAOs", "DEX", "DEXs", "CEX",
                 "APY", "APR", "TVL", "USD", "DApp", "DApps", "AI", "CEO", "CFO", "CTO", "IPO", "SEC", "L1", "L2", "The", "A", "An",
                 "In", "On", "At", "It", "Its", "This", "That", "These", "Those", "After", "Before", "During", "Over", "Under",
                 "About", "Roughly", "Several", "Many", "Some", "No", "Not", "Users", "Traders", "Investors", "Holders"}


def scrub_proper_nouns(text: str) -> tuple[str, int]:
    """Replace residual capitalized names (not role tokens, not sentence-initial common words) with [entity]."""
    starts = {m.start(1) for m in _SENTENCE_START.finditer(text)}
    out, n, last = [], 0, 0
    for m in _PROPER.finditer(text):
        token = m.group(0)
        if m.start() in starts and " " not in token:
            continue
        if token in _ALLOWED_CAPS or token.replace(".", "") in _ALLOWED_CAPS or token.isupper() and len(token) <= 2:
            continue
        if re.fullmatch(r"(?:Asset|Exchange|Person|Regulator|Network)_[A-Za-z0-9]+", token):
            continue
        out.append(text[last:m.start()]); out.append("[entity]"); last = m.end(); n += 1
    out.append(text[last:])
    return "".join(out), n


def validate(obj) -> dict:
    if not isinstance(obj, dict) or set(obj) != {"type", "summary", "novelty", "affected_aliases"}:
        raise ValueError("bad keys")
    if obj["type"] not in TYPES or obj["novelty"] not in ("new_information", "follow_up", "none"):
        raise ValueError("bad enum")
    if not isinstance(obj["summary"], str) or not isinstance(obj["affected_aliases"], list) \
            or not all(isinstance(a, str) for a in obj["affected_aliases"]):
        raise ValueError("bad types")
    return obj


def request_body(text: str, max_tokens: int = 3000) -> dict:
    return {"model": MODEL, "messages": [{"role": "user", "content": PROMPT.format(text=text)}],
            "temperature": 0, "max_tokens": max_tokens, "reasoning": {"effort": "low"},
            "response_format": {"type": "json_schema", "json_schema": {"name": "news_item", "strict": True, "schema": SCHEMA}},
            "provider": {"order": PROVIDERS, "allow_fallbacks": False, "quantizations": [QUANTIZATION]},
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
            if attempt == 2 and body["max_tokens"] < 8000:
                body = request_body(text, max_tokens=8000)   # one retry with headroom after a truncated answer
            try:
                r = session.post(ENDPOINT, json=body, timeout=120, headers=headers)
            except requests.RequestException as exc:
                _log(attempt=attempt, outcome=f"network:{type(exc).__name__}")
                if attempt == self.max_attempts:
                    raise TextLLMError("network failure") from None
                self.sleep(min(5 * 2 ** (attempt - 1), 60))
                continue
            if r.status_code == 200:
                data = r.json()
                if "error" in data and "choices" not in data:
                    code = (data.get("error") or {}).get("code")
                    _log(attempt=attempt, outcome="provider_error", code=code, detail=str(data["error"])[:160])
                    if code == 402:
                        raise CreditError("insufficient credits (402 in body)")
                    if attempt < self.max_attempts:
                        self.sleep(min(5 * 2 ** (attempt - 1), 60))
                        continue
                    raise TextLLMError(f"provider error: {str(data['error'])[:200]}")
                if data.get("model") != MODEL or data.get("provider") not in PROVIDERS:
                    raise TextLLMError(f"drift: {data.get('model')} / {data.get('provider')}")
                _log(attempt=attempt, outcome="ok", provider=data.get("provider"))
                choice = data["choices"][0]
                if choice.get("finish_reason") == "length" and attempt < self.max_attempts:
                    continue
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
            _log(attempt=attempt, outcome=f"http_{r.status_code}", detail=str(r.text)[:160])
            if r.status_code == 402:
                raise CreditError("insufficient credits (402)")
            if r.status_code in RETRY_STATUS and attempt < self.max_attempts:
                self.sleep(min(5 * 2 ** (attempt - 1), 60))
                continue
            raise TextLLMError(f"HTTP {r.status_code}")
        raise TextLLMError("retries exhausted")
