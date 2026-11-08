"""Generic pinned OpenRouter structured-output call used by probes and agents.

One model, one provider, strict JSON schema, retries on transient failures, cost
accounting, drift check. Thread-safe counters. Never logs the key.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import threading
import time

import requests

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 529})
PINS = {  # role -> (model, provider, quantization)
    "pro": ("deepseek/deepseek-v4-pro", "Baidu", "fp8"),
    "flash": ("deepseek/deepseek-v4.1-flash", "Baidu", "fp8"),
    "chrono": ("deepseek/deepseek-v3.2", "Baidu", "fp8"),
}


class ORError(RuntimeError):
    pass


@dataclass
class StructuredClient:
    api_key: str = field(repr=False)
    model: str
    provider: str
    quantization: str = "fp8"
    cost_cap_usd: float = 10.0
    reasoning_effort: str | None = "medium"
    max_tokens: int = 4000
    max_attempts: int = 5
    session: object = None
    sleep: object = time.sleep
    spent_usd: float = 0.0
    calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def pinned(cls, role: str, api_key: str, **kw) -> "StructuredClient":
        model, provider, quant = PINS[role]
        return cls(api_key=api_key, model=model, provider=provider, quantization=quant, **kw)

    def body(self, prompt: str, schema: dict, schema_name: str, system: str | None = None) -> dict:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        b = {"model": self.model, "messages": messages, "temperature": 0, "max_tokens": self.max_tokens,
             "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
             "provider": {"order": [self.provider], "allow_fallbacks": False, "quantizations": [self.quantization]},
             "usage": {"include": True}}
        if self.reasoning_effort:
            b["reasoning"] = {"effort": self.reasoning_effort}
        return b

    def call(self, prompt: str, schema: dict, schema_name: str = "answer", system: str | None = None) -> tuple[dict, dict]:
        """Returns (parsed_json, meta) where meta has usage, cost, latency, model, provider."""
        with self._lock:
            if self.spent_usd > self.cost_cap_usd:
                raise ORError(f"spend cap reached: {self.spent_usd:.4f} of {self.cost_cap_usd}")
        session = self.session or requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = self.body(prompt, schema, schema_name, system)
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                r = session.post(ENDPOINT, json=body, timeout=240, headers=headers)
            except requests.RequestException:
                if attempt == self.max_attempts:
                    raise ORError("network failure") from None
                self.sleep(min(10 * 2 ** (attempt - 1), 120))
                continue
            if r.status_code == 200:
                data = r.json()
                if "error" in data and "choices" not in data:
                    if attempt < self.max_attempts:
                        self.sleep(min(10 * 2 ** (attempt - 1), 120))
                        continue
                    raise ORError(f"provider error: {str(data['error'])[:200]}")
                if data.get("model") != self.model or data.get("provider") != self.provider:
                    raise ORError(f"drift: {data.get('model')} / {data.get('provider')}")
                choice = data["choices"][0]
                if choice.get("finish_reason") != "stop":
                    raise ORError(f"finish_reason {choice.get('finish_reason')}")
                try:
                    parsed = json.loads(choice["message"]["content"])
                except (ValueError, TypeError, KeyError):
                    raise ORError("answer is not JSON") from None
                usage = data.get("usage") or {}
                cost = float(usage.get("cost") or 0.0)
                if not math.isfinite(cost):
                    raise ORError("non-finite cost")
                with self._lock:
                    self.spent_usd += cost
                    self.calls += 1
                meta = {"model": data["model"], "provider": data["provider"], "cost": cost,
                        "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                        "latency_s": time.monotonic() - started, "id": data.get("id")}
                return parsed, meta
            if r.status_code == 402:
                raise ORError("insufficient credits (402)")
            if r.status_code in RETRY_STATUS and attempt < self.max_attempts:
                self.sleep(min(10 * 2 ** (attempt - 1), 120))
                continue
            raise ORError(f"HTTP {r.status_code}")
        raise ORError("retries exhausted")
