"""OpenRouter Decisions client with a fake session (no network)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_client import ENDPOINT, JevClient, JevError, load_api_key  # noqa: E402

QUESTIONS = {"ev_hack": {"type": "noul", "instructions": "x"},
             "asset": {"type": "choice", "instructions": "y",
                       "criteria": {"c00": "A", "none": "n"}}}


def ok_payload(model="typesafe/jev-1.13-20260917", provider="TypeSafe", cost=0.0004, answers=None):
    return {"id": "gen-dec-1", "model": model, "provider": provider,
            "answers": answers if answers is not None else {
                "ev_hack": {"type": "noul", "noul": 0.9},
                "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                          "probabilities": {"c00": 0.8, "none": 0.2}}},
            "usage": {"input_tokens": 400, "output_tokens": 20, "cost": cost}}


class FakeResponse:
    def __init__(self, status, payload=None, headers=None, text=""):
        self.status_code, self._payload = status, payload
        self.headers, self.text = headers or {}, text

    def json(self):
        return self._payload


class BadJsonResponse(FakeResponse):
    """FakeResponse that raises ValueError on json()."""
    def json(self):
        raise ValueError("invalid JSON")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.bodies, self.headers = list(responses), [], []

    def post(self, url, json=None, timeout=None, headers=None):
        assert url == ENDPOINT
        self.bodies.append(json)
        self.headers.append(headers)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(responses, **kw):
    sleeps = []
    c = JevClient(api_key="sk-test", model="typesafe/jev-1.13-20260917",
                  expected_model="typesafe/jev-1.13-20260917",
                  session=FakeSession(responses), sleep=sleeps.append, **kw)
    return c, sleeps


def test_success_body_and_cost_tracking():
    c, _ = client([FakeResponse(200, ok_payload())])
    data = c.decide({"headline": "h"}, QUESTIONS)
    body = c.session.bodies[0]
    assert body["model"] == "typesafe/jev-1.13-20260917"
    assert body["provider"] == {"only": ["typesafe"], "allow_fallbacks": False}
    assert body["questions"] == QUESTIONS and body["state"] == {"headline": "h"}
    assert c.session.headers[0]["Authorization"] == "Bearer sk-test"
    assert c.calls == 1 and c.spent_usd == pytest.approx(0.0004)
    assert data["_latency_s"] >= 0


def test_retry_after_honoured_then_success():
    c, sleeps = client([FakeResponse(429, headers={"retry-after": "2"}),
                        FakeResponse(200, ok_payload())])
    c.decide({}, QUESTIONS)
    assert sleeps == [2.0] and c.calls == 1


def test_network_error_retried_then_exhausted():
    c, sleeps = client([requests.ConnectionError("boom")] * 5)
    with pytest.raises(JevError, match="network failure"):
        c.decide({}, QUESTIONS)
    assert len(sleeps) == 4


def test_retry_status_exhausted():
    c, _ = client([FakeResponse(503)] * 5)
    with pytest.raises(JevError, match="HTTP 503"):
        c.decide({}, QUESTIONS)


def test_insufficient_credits_fails_immediately():
    c, sleeps = client([FakeResponse(402)])
    with pytest.raises(JevError, match="402"):
        c.decide({}, QUESTIONS)
    assert sleeps == []


def test_model_drift_fails():
    c, _ = client([FakeResponse(200, ok_payload(model="typesafe/jev-1.14-20261001"))])
    with pytest.raises(JevError, match="model drift"):
        c.decide({}, QUESTIONS)


def test_provider_drift_fails():
    c, _ = client([FakeResponse(200, ok_payload(provider="Other"))])
    with pytest.raises(JevError, match="provider drift"):
        c.decide({}, QUESTIONS)


def test_missing_answer_fails():
    answers = {"ev_hack": {"type": "noul", "noul": 0.9}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="answers"):
        c.decide({}, QUESTIONS)


def test_incomplete_choice_probabilities_fail():
    answers = {"ev_hack": {"type": "noul", "noul": 0.9},
               "asset": {"type": "choice", "choice": "c00", "probabilities": {"c00": 1.0}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="probabilities"):
        c.decide({}, QUESTIONS)


def test_cost_cap_blocks_before_posting():
    c, _ = client([FakeResponse(200, ok_payload(cost=0.0008)),
                   FakeResponse(200, ok_payload(cost=0.0008))], cost_cap_usd=0.001)
    c.decide({}, QUESTIONS)
    with pytest.raises(JevError, match="spend cap"):
        c.decide({}, QUESTIONS)
    assert len(c.session.bodies) == 1


def test_key_loading_and_repr(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTHER=1\nOPENROUTER_API=sk-abc\n")
    assert load_api_key(env) == "sk-abc"
    env.write_text("OPENROUTER_API_KEY=sk-def\n")
    assert load_api_key(env) == "sk-def"
    env.write_text("NOTHING=1\n")
    with pytest.raises(JevError, match="no OpenRouter key"):
        load_api_key(env)
    assert "sk-test" not in repr(client([])[0])


def test_504_retried_then_success():
    c, sleeps = client([FakeResponse(504), FakeResponse(200, ok_payload())])
    c.decide({}, QUESTIONS)
    assert len(sleeps) == 1 and c.calls == 1


def test_408_retried_then_success():
    c, sleeps = client([FakeResponse(408), FakeResponse(200, ok_payload())])
    c.decide({}, QUESTIONS)
    assert len(sleeps) == 1 and c.calls == 1


def test_backoff_schedule():
    c, sleeps = client([FakeResponse(503)] * 5)
    with pytest.raises(JevError, match="HTTP 503"):
        c.decide({}, QUESTIONS)
    assert sleeps == [10, 20, 40, 80]


def test_malformed_json_in_200_response():
    c, _ = client([BadJsonResponse(200)])
    with pytest.raises(JevError, match="malformed JSON"):
        c.decide({}, QUESTIONS)


def test_usage_cost_none():
    payload = ok_payload()
    payload["usage"]["cost"] = None
    c, _ = client([FakeResponse(200, payload)])
    with pytest.raises(JevError, match="usage.cost"):
        c.decide({}, QUESTIONS)


def test_answer_value_not_dict():
    answers = {"ev_hack": "not a dict",
               "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                         "probabilities": {"c00": 0.8, "none": 0.2}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="not an object"):
        c.decide({}, QUESTIONS)


def test_noul_value_is_bool():
    answers = {"ev_hack": {"type": "noul", "noul": True},
               "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                         "probabilities": {"c00": 0.8, "none": 0.2}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="noul probability"):
        c.decide({}, QUESTIONS)


def test_noul_value_nan():
    answers = {"ev_hack": {"type": "noul", "noul": float("nan")},
               "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                         "probabilities": {"c00": 0.8, "none": 0.2}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="noul probability"):
        c.decide({}, QUESTIONS)


def test_noul_value_out_of_range():
    answers = {"ev_hack": {"type": "noul", "noul": 1.5},
               "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                         "probabilities": {"c00": 0.8, "none": 0.2}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="noul probability"):
        c.decide({}, QUESTIONS)


def test_choice_probability_not_numeric():
    answers = {"ev_hack": {"type": "noul", "noul": 0.9},
               "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                         "probabilities": {"c00": "x", "none": 0.2}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="choice probabilities"):
        c.decide({}, QUESTIONS)


def test_api_key_scrubbed_in_error_message():
    c, _ = client([FakeResponse(401, text="bad key sk-test here")])
    with pytest.raises(JevError) as exc_info:
        c.decide({}, QUESTIONS)
    msg = str(exc_info.value)
    assert "401" in msg
    assert "[redacted]" in msg
    assert "sk-test" not in msg
