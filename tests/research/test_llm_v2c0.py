"""Charter 0 (DeepSeek V4-Pro extraction probe): prompt freeze, client, labels, review, score."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_extract import PROMPT_V2  # noqa: E402
from llm_event_xs_truth import RoundData  # noqa: E402
from llm_v2c0_client import (  # noqa: E402
    ENDPOINT, MODEL, PROVIDER, ExtractError, OpenRouterClient, request_body,
)
from llm_v2c0_labels import N_REPEAT, label_article, label_rounds, repeat_ids  # noqa: E402
from llm_v2c0_prompt import SCHEMA, article_text, prompt_sha256, validate_output  # noqa: E402
from llm_v2c0_review import build, header, parse_filled, render_markdown  # noqa: E402
from llm_v2c0_score import diagnostics, evaluate  # noqa: E402

PROMPT_SHA = "4bf1e5ef146a4c85a55ae1ae674b1012baab4009be06ea235f73a3fd3c5df1c1"


def ok_payload(events=None, model=MODEL, provider=PROVIDER, finish="stop", cost=0.0005,
               content=None):
    body = {"events": events if events is not None else [], "ambiguous": False}
    return {"id": "gen-1", "model": model, "provider": provider,
            "choices": [{"finish_reason": finish,
                         "message": {"role": "assistant",
                                     "content": json.dumps(body) if content is None else content}}],
            "usage": {"prompt_tokens": 300, "completion_tokens": 200, "cost": cost,
                      "completion_tokens_details": {"reasoning_tokens": 150}}}


class FakeResponse:
    def __init__(self, status, payload=None, headers=None, text=""):
        self.status_code, self._payload, self.headers, self.text = status, payload, headers or {}, text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses, self.bodies = list(responses), []

    def post(self, url, json=None, timeout=None, headers=None):
        assert url == ENDPOINT
        assert headers["Authorization"].startswith("Bearer ")
        self.bodies.append(json)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(responses, **kw):
    sleeps = []
    c = OpenRouterClient(api_key="sk-test", session=FakeSession(responses),
                         sleep=sleeps.append, **kw)
    return c, sleeps


def test_prompt_is_c1_v2_verbatim_and_pinned():
    assert "Additional rules (v2)" in PROMPT_V2
    body = request_body("some text")
    assert body["messages"][0]["content"] == PROMPT_V2.format(text="some text")
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["response_format"]["json_schema"]["schema"] == SCHEMA
    assert body["provider"] == {"order": [PROVIDER], "allow_fallbacks": False, "quantizations": ["fp8"]}
    assert body["temperature"] == 0 and body["usage"] == {"include": True}
    assert len(prompt_sha256()) == 64
    if PROMPT_SHA != "PINNED_AT_REGISTRATION":
        assert prompt_sha256() == PROMPT_SHA


def test_article_text_omits_nan_and_truncates():
    row = {"headline": "Head ✓", "summary": float("nan"), "content": "x" * 5000}
    text = article_text(row)
    assert text.startswith("Head ✓\n") and "nan" not in text and len(text) == len("Head ✓\n") + 4000


def test_validate_output_rejects_bad_shapes():
    validate_output({"events": [], "ambiguous": False})
    for bad in ({"events": []}, {"events": [], "ambiguous": "no"},
                {"events": [{"asset": "a", "class": "hack", "severity": 4, "evidence": "e"}], "ambiguous": False},
                {"events": [{"asset": "a", "class": "rumor", "severity": 1, "evidence": "e"}], "ambiguous": False},
                {"events": [{"asset": "a", "class": "hack", "severity": True, "evidence": "e"}], "ambiguous": False},
                {"events": [{"asset": "a", "class": "hack", "severity": 1}], "ambiguous": False}):
        with pytest.raises(ValueError):
            validate_output(bad)


def test_client_success_records_usage():
    c, _ = client([FakeResponse(200, ok_payload(
        events=[{"asset": "Zetrix", "class": "hack", "severity": 2, "evidence": "drained"}]))])
    out = c.extract("t")
    assert out["events"][0]["class"] == "hack" and out["ambiguous"] is False
    assert out["raw"]["usage"]["reasoning_tokens"] == 150 and out["raw"]["provider"] == PROVIDER
    assert c.calls == 1 and c.spent_usd == pytest.approx(0.0005)


@pytest.mark.parametrize("payload,needle", [
    (ok_payload(model="deepseek/deepseek-v4-flash"), "model drift"),
    (ok_payload(provider="StreamLake"), "provider drift"),
    (ok_payload(finish="length"), "not complete"),
    (ok_payload(content="not json"), "not JSON"),
    (ok_payload(content=json.dumps({"events": [{"asset": "a", "class": "hack", "severity": 9,
                                                 "evidence": "e"}], "ambiguous": False})), "schema"),
    (ok_payload(cost=None), "usage.cost"),
])
def test_client_fails_loudly(payload, needle):
    c, _ = client([FakeResponse(200, payload)])
    with pytest.raises(ExtractError, match=needle):
        c.extract("t")


def test_client_retries_then_succeeds_and_402_is_fatal():
    c, sleeps = client([FakeResponse(429, headers={"retry-after": "3"}),
                        requests.ConnectionError(), FakeResponse(200, ok_payload())])
    assert c.extract("t")["events"] == [] and sleeps == [3.0, 20]
    c, _ = client([FakeResponse(402, text="no credits")])
    with pytest.raises(ExtractError, match="402"):
        c.extract("t")


def test_client_spend_cap():
    c, _ = client([FakeResponse(200, ok_payload(cost=0.6)), FakeResponse(200, ok_payload(cost=0.6))],
                  cost_cap_usd=1.0)
    c.extract("t")
    with pytest.raises(ExtractError, match="spend cap"):
        c.extract("t")


class StubClient:
    def __init__(self, events, ambiguous=False):
        self.events, self.ambiguous, self.texts, self.spent_usd, self.calls = events, ambiguous, [], 0.0, 0

    def extract(self, text):
        self.texts.append(text)
        self.calls += 1
        return {"events": [dict(e) for e in self.events], "ambiguous": self.ambiguous,
                "raw": {"id": "x", "model": MODEL, "provider": PROVIDER, "finish_reason": "stop",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": 0,
                                  "cost": 0.001}, "_latency_s": 0.1}}


def test_label_article_drops_hallucinated_spans_and_anonymizes():
    row = {"headline": "Binance halts withdrawals after exploit", "summary": "", "content": ""}
    stub = StubClient([{"asset": "Binance", "class": "hack", "severity": 2, "evidence": "after exploit"},
                       {"asset": "Binance", "class": "insolvency_halt", "severity": 2,
                        "evidence": "withdrawals suspended indefinitely"}])
    label = label_article(stub, row, anon=False)
    assert [e["class"] for e in label["events"]] == ["hack"]
    assert label["spans_dropped"] == 1 and label["raw_events"] == 2
    label_article(stub, row, anon=True)
    assert "Binance" not in stub.texts[-1] and "ENTITY_" in stub.texts[-1]


def make_round(n, name="v1", anon_ids=()):
    idxs = list(range(n))
    frame = pd.DataFrame({"sample_idx": idxs, "headline": [f"Headline {i}" for i in idxs],
                          "summary": "", "content": "", "store": "gdelt", "symbols": "",
                          "event_ts": pd.Timestamp("2023-01-02", tz="UTC"), "prefilter": [i % 2 == 0 for i in idxs]})
    frame.index = frame["sample_idx"].to_numpy()
    truth = {i: [] for i in idxs}
    truth[0] = [{"class": "hack", "asset": "Poly Network"}]
    return RoundData(name, frame, dict(truth), dict(truth), frozenset({0}), tuple(anon_ids), {})


def test_label_rounds_covers_named_anon_and_repeat():
    rounds = {"v1": make_round(60, anon_ids=(1, 2)), "v2": make_round(10, name="v2", anon_ids=(3,))}
    stub = StubClient([])
    named, anon, repeat = label_rounds(rounds, stub, progress=lambda s: None)
    assert len(named) == 60 and set(anon) == {"1", "2", "3"} and len(repeat) == N_REPEAT
    assert set(repeat) == {str(i) for i in repeat_ids(rounds)} and stub.calls == 60 + 10 + 3 + N_REPEAT
    assert repeat_ids(rounds) == repeat_ids(rounds)


def test_review_header_and_render_parse_roundtrip():
    text = header()
    assert "llm-v2c0-p0-label-20261109" in text and "data/llm_event_xs/" in text
    rounds = {"v1": make_round(40)}
    labels = {str(i): {"events": []} for i in range(40)}
    labels["5"] = {"events": [{"class": "regulatory", "asset": "SEC target"}]}
    rows, key = build(rounds, labels)
    md = render_markdown(rows)
    assert md.startswith("# DeepSeek V4-Pro P0 blind review")
    assert sum(r["kind"] == "class" for r in rows) == 1 and sum(r["kind"] == "check" for r in rows) == 20
    filled = md
    for row in rows:
        verdict = "NO EVENTS" if row["kind"] == "class" else "BOTH"
        filled = filled.replace(f"### row {row['row']} ", f"### row {row['row']} ", 1)
    filled = filled.replace("- VERDICT: \n", "- VERDICT: BOTH\n")
    class_row = next(r for r in rows if r["kind"] == "class")
    block_start = filled.index(f"### row {class_row['row']} ")
    block_end = filled.index("### row", block_start + 1) if "### row" in filled[block_start + 1:] else len(filled)
    block = filled[block_start:block_end].replace("- VERDICT: BOTH", "- VERDICT: NO EVENTS")
    filled = filled[:block_start] + block + filled[block_end:]
    parsed = parse_filled(filled, rows)
    assert parsed[class_row["row"]]["verdict"] == "NO EVENTS"


def test_evaluate_and_diagnostics_shapes():
    rounds = {"v1": make_round(12)}
    truth = {i: [] for i in range(12)}
    truth[0] = [{"class": "hack", "asset": "Poly Network"}]
    raw = {"usage": {"cost": 0.001, "reasoning_tokens": 10}, "_latency_s": 0.2}
    named = {str(i): {"events": [], "ambiguous": False, "spans_dropped": 0, "raw_events": 0, "raw": raw}
             for i in range(12)}
    named["0"] = {"events": [{"class": "hack", "asset": "Poly", "severity": 3, "evidence": "e"}],
                  "ambiguous": False, "spans_dropped": 0, "raw_events": 1, "raw": raw}
    anon = {"0": named["0"], "1": named["1"]}
    repeat = {"0": named["0"], "1": named["1"]}
    events = {int(k): v["events"] for k, v in named.items()}
    verdict = evaluate(truth, events, {}, named, anon)
    assert verdict["primary"]["verdict"] in {"PASS", "FAIL"} and "gate_rows" in verdict
    diag = diagnostics(rounds, truth, named, anon, repeat, {"spent_usd": 0.01, "calls": 12})
    assert diag["stability"]["class_set_flip_rate"] == 0.0
    assert diag["severity_distribution"]["hack"]["3"] == 1 and diag["cost"]["calls"] == 12
