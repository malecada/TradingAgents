"""Generic pinned OpenRouter structured-output call used by probes and agents.

One model, one provider, strict JSON schema, retries on transient failures, cost
accounting, drift check. Thread-safe counters. Never logs the key.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import os
import threading
import time

import requests

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 529})
PINS = {  # role -> (model, ordered providers, quantization); every listed provider serves the same fp8 weights
    "pro": ("deepseek/deepseek-v4-pro", ["Baidu", "StreamLake"], "fp8"),
    "flash": ("deepseek/deepseek-v4.1-flash", ["Baidu", "DeepInfra"], "fp8"),
    "chrono": ("deepseek/deepseek-v3.2", ["Baidu", "AtlasCloud"], "fp8"),
}
LOG = os.environ.get("OR_CLIENT_LOG")   # path; when set, one JSON line per attempt


class ORError(RuntimeError):
    pass


@dataclass
class StructuredClient:
    api_key: str = field(repr=False)
    model: str
    provider: str | list[str]
    quantization: str = "fp8"
    cost_cap_usd: float = 10.0
    reasoning_effort: str | None = "medium"
    reasoning_max_tokens: int | None = None      # hard cap on reasoning tokens (OpenRouter unified param)
    reasoning_enabled: bool = True               # False = non-thinking mode
    max_tokens: int = 4000
    max_attempts: int = 5
    session: object = None
    sleep: object = time.sleep
    spent_usd: float = 0.0
    calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def pinned(cls, role: str, api_key: str, **kw) -> "StructuredClient":
        model, providers, quant = PINS[role]
        return cls(api_key=api_key, model=model, provider=list(providers), quantization=quant, **kw)

    @property
    def providers(self) -> list[str]:
        return [self.provider] if isinstance(self.provider, str) else list(self.provider)

    def _log(self, **fields):
        if LOG:
            with open(LOG, "a") as fh:
                fh.write(json.dumps({"ts": time.time(), **fields}) + "\n")

    def body(self, prompt: str, schema: dict, schema_name: str, system: str | None = None,
             reasoning_effort: str | None = None, reasoning: dict | None = None) -> dict:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        b = {"model": self.model, "messages": messages, "temperature": 0, "max_tokens": self.max_tokens,
             "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
             "provider": {"order": self.providers, "allow_fallbacks": False, "quantizations": [self.quantization]},
             "usage": {"include": True}}
        if reasoning is not None:                       # explicit per-call override (e.g. {"enabled": False})
            b["reasoning"] = dict(reasoning)
        elif not self.reasoning_enabled:
            b["reasoning"] = {"enabled": False}
        elif self.reasoning_max_tokens:
            b["reasoning"] = {"max_tokens": int(self.reasoning_max_tokens)}
        elif reasoning_effort or self.reasoning_effort:
            b["reasoning"] = {"effort": reasoning_effort or self.reasoning_effort}
        return b

    def call(self, prompt: str, schema: dict, schema_name: str = "answer", system: str | None = None,
             reasoning_effort: str | None = None, reasoning: dict | None = None) -> tuple[dict, dict]:
        """Returns (parsed_json, meta) where meta has usage, cost, latency, model, provider."""
        with self._lock:
            if self.spent_usd > self.cost_cap_usd:
                raise ORError(f"spend cap reached: {self.spent_usd:.4f} of {self.cost_cap_usd}")
        session = self.session or requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = self.body(prompt, schema, schema_name, system, reasoning_effort, reasoning)
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                r = session.post(ENDPOINT, json=body, timeout=240, headers=headers)
            except requests.RequestException as exc:
                self._log(schema=schema_name, attempt=attempt, outcome=f"network:{type(exc).__name__}")
                if attempt == self.max_attempts:
                    raise ORError("network failure") from None
                self.sleep(min(10 * 2 ** (attempt - 1), 120))
                continue
            if r.status_code == 200:
                data = r.json()
                if "error" in data and "choices" not in data:
                    self._log(schema=schema_name, attempt=attempt, outcome="provider_error",
                              detail=str(data["error"])[:160], latency_s=round(time.monotonic() - started, 1))
                    if attempt < self.max_attempts:
                        self.sleep(min(5 * 2 ** (attempt - 1), 60))
                        continue
                    raise ORError(f"provider error: {str(data['error'])[:200]}")
                if data.get("model") != self.model or data.get("provider") not in self.providers:
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
                self._log(schema=schema_name, attempt=attempt, outcome="ok", provider=data["provider"],
                          latency_s=round(meta["latency_s"], 1), cost=cost, reasoning_tokens=meta["reasoning_tokens"])
                return parsed, meta
            if r.status_code == 402:
                raise ORError("insufficient credits (402)")
            self._log(schema=schema_name, attempt=attempt, outcome=f"http_{r.status_code}")
            if r.status_code in RETRY_STATUS and attempt < self.max_attempts:
                self.sleep(min(5 * 2 ** (attempt - 1), 60))
                continue
            raise ORError(f"HTTP {r.status_code}")
        raise ORError("retries exhausted")
