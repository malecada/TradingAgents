from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.llm_text import MODEL, PROVIDER, PROVIDERS, CreditError, TextLLM, TextLLMError, request_body  # noqa: E402


class R:
    def __init__(self, status, payload=None):
        self.status_code, self._p, self.headers, self.text = status, payload, {}, ""

    def json(self):
        return self._p


class S:
    def __init__(self, responses):
        self.responses, self.n = list(responses), 0

    def post(self, url, json=None, timeout=None, headers=None):
        self.n += 1
        return self.responses.pop(0)


def payload(value, model=MODEL, provider=PROVIDER, finish="stop"):
    return {"model": model, "provider": provider, "usage": {"cost": 0.0001},
            "choices": [{"finish_reason": finish, "message": {"content": json.dumps(value)}}]}


GOOD = {"type": "event", "summary": "Exchange_1 halted withdrawals.", "novelty": "new_information", "affected_aliases": ["Asset_A"]}


def test_classify_caches_and_validates(tmp_path):
    s = S([R(200, payload(GOOD))])
    llm = TextLLM(api_key="k", session=s, cache_path=tmp_path / "c.jsonl", sleep=lambda x: None)
    assert llm.classify("t")["type"] == "event" and llm.calls == 1
    assert llm.classify("t")["type"] == "event" and llm.calls == 1 and llm.cache_hits == 1
    llm2 = TextLLM(api_key="k", session=S([]), cache_path=tmp_path / "c.jsonl")
    assert llm2.classify("t")["summary"].startswith("Exchange_1") and llm2.calls == 0
    body = request_body("x")
    assert body["provider"]["order"] == PROVIDERS and body["response_format"]["json_schema"]["strict"]


@pytest.mark.parametrize("resp,needle", [
    (R(200, payload(GOOD, model="deepseek/deepseek-v4-pro")), "drift"),
    (R(200, payload({"type": "weird", "summary": "", "novelty": "none", "affected_aliases": []})), "invalid"),
    (R(200, payload(GOOD, finish="content_filter")), "finish_reason"),
])


def test_failures(tmp_path, resp, needle):
    llm = TextLLM(api_key="k", session=S([resp]), cache_path=tmp_path / "c.jsonl", sleep=lambda x: None)
    with pytest.raises(TextLLMError, match=needle):
        llm.classify("t")


def test_retry_then_success(tmp_path):
    llm = TextLLM(api_key="k", session=S([R(429), R(200, payload(GOOD))]), cache_path=tmp_path / "c.jsonl", sleep=lambda x: None)
    assert llm.classify("t")["novelty"] == "new_information"


def test_truncated_answer_retries_with_headroom(tmp_path):
    s = S([R(200, payload(GOOD, finish="length")), R(200, payload(GOOD))])
    llm = TextLLM(api_key="k", session=s, cache_path=tmp_path / "c.jsonl", sleep=lambda x: None)
    assert llm.classify("t")["type"] == "event" and s.n == 2


def test_scrub_proper_nouns_keeps_tokens_and_sentence_starts():
    from tradingagents.dossier.llm_text import scrub_proper_nouns
    text = "Asset_K partnered with WonderFi and Sun Hung Kai Properties. The deal, led by Exchange_1, is worth about $100 million in US dollars."
    out, n = scrub_proper_nouns(text)
    assert "WonderFi" not in out and "Sun Hung Kai" not in out and n == 2
    assert "Asset_K" in out and "Exchange_1" in out and out.startswith("Asset_K") and "The deal" in out and "US dollars" in out


def test_402_is_a_credit_error(tmp_path):
    llm = TextLLM(api_key="k", session=S([R(402)]), cache_path=tmp_path / "c.jsonl", sleep=lambda x: None)
    with pytest.raises(CreditError):
        llm.classify("t")
    llm = TextLLM(api_key="k", session=S([R(200, payload(GOOD, provider="DeepInfra"))]), cache_path=tmp_path / "d.jsonl")
    assert llm.classify("u")["type"] == "event"          # second pinned provider accepted
