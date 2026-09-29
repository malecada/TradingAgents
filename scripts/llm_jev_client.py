"""Minimal OpenRouter Decisions API client for Jev (charter §4.1).

Never logs or returns the API key. Fails loudly on model/provider drift,
malformed answers, exhausted retries, missing credits or the spend cap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

import requests

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
PROVIDER_SLUG = "typesafe"
PROVIDER_NAME = "TypeSafe"
KEY_NAMES = ("OPENROUTER_API_KEY", "OPENROUTER_API")
RETRY_STATUS = frozenset({429, 500, 502, 503, 524, 529})


class JevError(RuntimeError):
    """Any condition that must stop a registered run."""


def load_api_key(env_file: Path) -> str:
    from dotenv import dotenv_values
    values = dotenv_values(env_file)
    for name in KEY_NAMES:
        if values.get(name):
            return values[name].strip()
    raise JevError(f"no OpenRouter key in {env_file} (expected one of {KEY_NAMES})")


@dataclass
class JevClient:
    api_key: str = field(repr=False)
    model: str
    cost_cap_usd: float = 5.0
    max_attempts: int = 5
    expected_model: str | None = None
    expected_provider: str | None = PROVIDER_NAME
    session: object = None
    sleep: object = time.sleep
    spent_usd: float = 0.0
    calls: int = 0
    max_call_usd: float = 0.0

    def decide(self, state, questions: dict) -> dict:
        if self.spent_usd + self.max_call_usd > self.cost_cap_usd:
            raise JevError(f"spend cap reached: {self.spent_usd:.6f} USD of {self.cost_cap_usd}")
        body = {"model": self.model, "state": state, "questions": questions,
                "provider": {"only": [PROVIDER_SLUG], "allow_fallbacks": False}}
        session = self.session or requests
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                response = session.post(ENDPOINT, json=body, timeout=60,
                                        headers={"Authorization": f"Bearer {self.api_key}"})
            except requests.RequestException as exc:
                if attempt == self.max_attempts:
                    raise JevError(f"network failure after {attempt} attempts: "
                                   f"{type(exc).__name__}") from None
                self.sleep(min(2 ** attempt, 30))
                continue
            if response.status_code == 200:
                data = response.json()
                self._check(data, questions)
                cost = float(data["usage"]["cost"])
                self.spent_usd += cost
                self.calls += 1
                self.max_call_usd = max(self.max_call_usd, cost)
                data["_latency_s"] = time.monotonic() - started
                return data
            if response.status_code == 402:
                raise JevError("OpenRouter reports insufficient credits (HTTP 402)")
            if response.status_code in RETRY_STATUS and attempt < self.max_attempts:
                retry_after = str(response.headers.get("retry-after") or "")
                is_number = retry_after.replace(".", "", 1).isdigit()
                self.sleep(float(retry_after) if is_number else min(2 ** attempt, 30))
                continue
            raise JevError(f"HTTP {response.status_code}: {str(response.text)[:300]}")
        raise JevError("retry loop exited without a response")

    def _check(self, data: dict, questions: dict) -> None:
        if self.expected_model is not None and data.get("model") != self.expected_model:
            raise JevError(f"model drift: got {data.get('model')!r}, "
                           f"pinned {self.expected_model!r}")
        if self.expected_provider is not None and data.get("provider") != self.expected_provider:
            raise JevError(f"provider drift: got {data.get('provider')!r}")
        answers = data.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise JevError("answers do not cover exactly the asked questions")
        for name, question in questions.items():
            answer = answers[name]
            if answer.get("type") != question["type"]:
                raise JevError(f"answer type mismatch for {name}")
            if question["type"] == "noul" and not isinstance(answer.get("noul"), (int, float)):
                raise JevError(f"noul probability missing for {name}")
            if question["type"] == "choice":
                probs = answer.get("probabilities")
                if not isinstance(probs, dict) or set(probs) != set(question["criteria"]):
                    raise JevError(f"choice probabilities incomplete for {name}")
        if "cost" not in (data.get("usage") or {}):
            raise JevError("usage.cost missing from response")
