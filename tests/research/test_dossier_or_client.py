from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.or_client import ORError, StructuredClient  # noqa: E402


class R:
    def __init__(self, status, payload=None):
        self.status_code, self._p, self.headers, self.text = status, payload, {}, ""

    def json(self):
        return self._p


class S:
    def __init__(self, responses):
        self.responses, self.bodies = list(responses), []

    def post(self, url, json=None, timeout=None, headers=None):
        self.bodies.append(json)
        return self.responses.pop(0)


def ok(value, model="deepseek/deepseek-v4-pro", provider="Baidu"):
    return {"model": model, "provider": provider, "usage": {"cost": 0.001, "completion_tokens_details": {"reasoning_tokens": 5}},
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}]}


def test_pinned_call_and_meta():
    s = S([R(200, ok({"a": 1}))])
    c = StructuredClient.pinned("pro", "k", session=s, sleep=lambda x: None)
    parsed, meta = c.call("p", {"type": "object"}, "t", system="sys")
    assert parsed == {"a": 1} and meta["reasoning_tokens"] == 5 and c.spent_usd == pytest.approx(0.001)
    body = s.bodies[0]
    assert body["messages"][0]["role"] == "system" and body["provider"]["order"] == ["Baidu"]
    assert body["reasoning"] == {"effort": "medium"} and body["response_format"]["json_schema"]["strict"]


def test_drift_and_retry():
    c = StructuredClient.pinned("flash", "k", session=S([R(200, ok({}, provider="Nebius"))]), sleep=lambda x: None)
    with pytest.raises(ORError, match="drift"):
        c.call("p", {"type": "object"})
    c = StructuredClient.pinned("flash", "k", session=S([R(503), R(200, ok({"z": 2}, model="deepseek/deepseek-v4.1-flash"))]), sleep=lambda x: None)
    assert c.call("p", {"type": "object"})[0] == {"z": 2}


def test_reasoning_cap_overrides_effort():
    c = StructuredClient.pinned("pro", "k", reasoning_max_tokens=1500)
    assert c.body("p", {"type": "object"}, "t")["reasoning"] == {"max_tokens": 1500}
