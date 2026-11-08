"""OpenRouter chat-completions client pinned to one DeepSeek endpoint (Charter 0 §4).

Never logs or returns the API key. Fails loudly on model or provider drift,
truncated or schema-invalid answers, exhausted retries, missing credits or the
spend cap. Counters are thread-safe so the labeler may run a small pool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import threading
import time

import requests

from llm_v2c0_prompt import SCHEMA, SCHEMA_NAME, user_prompt, validate_output

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-pro"
PROVIDER = "Baidu"
QUANTIZATION = "fp8"
REASONING = {"effort": "medium"}
TEMPERATURE = 0
MAX_TOKENS = 4000
TIMEOUT_S = 180
KEY_NAMES = ("OPENROUTER_API_KEY", "OPENROUTER_API")
KEY_FILES = (Path.home() / ".secrets" / "openrouter.env",)
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 529})


class ExtractError(RuntimeError):
    """Any condition that must stop a registered run."""


def load_api_key(extra_files: tuple[Path, ...] = ()) -> str:
    for name in KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name].strip()
    from dotenv import dotenv_values
    for path in (*KEY_FILES, *extra_files):
        if Path(path).is_file():
            values = dotenv_values(path)
            for name in KEY_NAMES:
                if values.get(name):
                    return values[name].strip()
    raise ExtractError(f"no OpenRouter key in environment or {KEY_FILES}")


def request_body(text: str, *, model: str = MODEL, provider: str = PROVIDER) -> dict:
    return {
        "model": model,
        "messages": [{"role": "user", "content": user_prompt(text)}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "reasoning": dict(REASONING),
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": SCHEMA_NAME, "strict": True, "schema": SCHEMA}},
        "provider": {"order": [provider], "allow_fallbacks": False,
                     "quantizations": [QUANTIZATION]},
        "usage": {"include": True},
    }


@dataclass
class OpenRouterClient:
    api_key: str = field(repr=False)
    model: str = MODEL
    provider: str = PROVIDER
    cost_cap_usd: float = 5.0
    max_attempts: int = 5
    session: object = None
    sleep: object = time.sleep
    spent_usd: float = 0.0
    calls: int = 0
    max_call_usd: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def extract(self, text: str) -> dict:
        with self._lock:
            if self.spent_usd + self.max_call_usd > self.cost_cap_usd:
                raise ExtractError(f"spend cap reached: {self.spent_usd:.6f} USD of {self.cost_cap_usd}")
        body = request_body(text, model=self.model, provider=self.provider)
        session = self.session or requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                response = session.post(ENDPOINT, json=body, timeout=TIMEOUT_S, headers=headers)
            except requests.RequestException as exc:
                if attempt == self.max_attempts:
                    raise ExtractError(f"network failure after {attempt} attempts: "
                                       f"{type(exc).__name__}") from None
                self.sleep(min(10 * 2 ** (attempt - 1), 120))
                continue
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    raise ExtractError("malformed JSON in 200 response") from None
                if isinstance(data, dict) and "error" in data and "choices" not in data:
                    code = (data.get("error") or {}).get("code")
                    if code in RETRY_STATUS and attempt < self.max_attempts:
                        self.sleep(min(10 * 2 ** (attempt - 1), 120))
                        continue
                    message = str((data.get("error") or {}).get("message"))[:300]
                    raise ExtractError(f"provider error {code}: {message}")
                result = self._check(data)
                result["raw"]["_latency_s"] = time.monotonic() - started
                with self._lock:
                    cost = result["raw"]["usage"]["cost"]
                    self.spent_usd += cost
                    self.calls += 1
                    self.max_call_usd = max(self.max_call_usd, cost)
                return result
            if response.status_code == 402:
                raise ExtractError("OpenRouter reports insufficient credits (HTTP 402)")
            if response.status_code in RETRY_STATUS and attempt < self.max_attempts:
                retry_after = str(response.headers.get("retry-after") or "")
                is_number = retry_after.replace(".", "", 1).isdigit()
                self.sleep(min(float(retry_after), 120.0) if is_number
                           else min(10 * 2 ** (attempt - 1), 120))
                continue
            text_out = str(response.text).replace(self.api_key, "[redacted]")[:300]
            raise ExtractError(f"HTTP {response.status_code}: {text_out}")
        raise ExtractError("retry loop exited without a response")

    def _check(self, data: dict) -> dict:
        if data.get("model") != self.model:
            raise ExtractError(f"model drift: got {data.get('model')!r}, pinned {self.model!r}")
        if data.get("provider") != self.provider:
            raise ExtractError(f"provider drift: got {data.get('provider')!r}, pinned {self.provider!r}")
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) != 1:
            raise ExtractError("response must carry exactly one choice")
        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            raise ExtractError(f"answer not complete: finish_reason={choice.get('finish_reason')!r}")
        message = choice.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ExtractError("empty answer content")
        try:
            parsed = json.loads(content)
        except ValueError:
            raise ExtractError("answer content is not JSON") from None
        try:
            validate_output(parsed)
        except ValueError as exc:
            raise ExtractError(f"schema violation: {exc}") from None
        usage = data.get("usage") or {}
        cost = usage.get("cost")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost):
            raise ExtractError("usage.cost missing or not numeric")
        details = usage.get("completion_tokens_details") or {}
        raw = {"id": data.get("id"), "model": data["model"], "provider": data["provider"],
               "finish_reason": choice["finish_reason"],
               "usage": {"prompt_tokens": usage.get("prompt_tokens"),
                         "completion_tokens": usage.get("completion_tokens"),
                         "reasoning_tokens": details.get("reasoning_tokens"),
                         "cost": float(cost)}}
        return {"events": parsed["events"], "ambiguous": parsed["ambiguous"], "raw": raw}
