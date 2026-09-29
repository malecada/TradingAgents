"""Aggregation of two Jev calls and article labeling with a scripted client."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_labels import aggregate, label_article  # noqa: E402
from llm_jev_questions import CLASSES  # noqa: E402


def response(nouls: dict, asset: dict | None = None) -> dict:
    answers = {f"ev_{c}": {"type": "noul", "noul": nouls.get(c, 0.0)} for c in CLASSES}
    if asset is not None:
        answers["asset"] = {"type": "choice", "choice": max(asset, key=asset.get),
                            "confidence": 0.9, "probabilities": asset}
    return {"id": "gen-x", "model": "m", "provider": "TypeSafe", "answers": answers,
            "usage": {"cost": 1e-5}, "_latency_s": 0.2}


class ScriptedClient:
    def __init__(self, responses):
        self.responses, self.calls, self.spent_usd = list(responses), [], 0.0

    def decide(self, state, questions):
        self.calls.append((state, questions))
        return self.responses.pop(0)


def test_threshold_is_inclusive():
    out = aggregate(response({"hack": 0.5, "regulatory": 0.49}),
                    response({"hack": 0.5, "regulatory": 0.49}), [])
    assert [e["class"] for e in out["events"]] == ["hack"]
    assert out["flip"] is False


def test_mean_and_flip():
    out = aggregate(response({"hack": 0.7}), response({"hack": 0.2}), [])
    assert out["probs"]["hack"] == pytest.approx(0.45)
    assert out["delta"]["hack"] == pytest.approx(0.5)
    assert out["events"] == [] and out["flip"] is True


def test_asset_argmax_over_mean():
    first = response({"hack": 0.9}, {"c00": 0.6, "c01": 0.3, "none": 0.1})
    second = response({"hack": 0.9}, {"c00": 0.2, "c01": 0.7, "none": 0.1})
    out = aggregate(first, second, ["Poly", "Ronin"])
    assert out["asset"] == "Ronin"
    assert out["events"] == [{"class": "hack", "asset": "Ronin"}]
    assert out["asset_probs"]["c01"] == pytest.approx(0.5)


def test_none_asset_wins():
    probs = {"c00": 0.1, "none": 0.9}
    out = aggregate(response({"hack": 0.8}, probs), response({"hack": 0.8}, probs), ["X"])
    assert out["asset"] is None and out["events"] == [{"class": "hack", "asset": None}]


def test_no_asset_question():
    out = aggregate(response({"regulatory": 0.9}), response({"regulatory": 0.9}), [])
    assert out["asset"] is None and out["asset_probs"] == {}
    assert out["raw"][0]["_latency_s"] == 0.2 and "answers" in out["raw"][0]


def test_label_article_named_reverses_candidates():
    row = {"store": "alpaca", "symbols": "AVAXUSD", "headline": "Kraken lists AVAX", "summary": ""}
    probs = {"c00": 0.8, "c01": 0.1, "none": 0.1}
    client = ScriptedClient([response({"listing_delisting": 0.9}, probs)] * 2)
    out = label_article(client, row, anon=False)
    first_q, second_q = client.calls[0][1], client.calls[1][1]
    assert list(first_q["asset"]["criteria"]) == ["c00", "c01", "none"]
    assert list(second_q["asset"]["criteria"]) == ["c01", "c00", "none"]
    assert out["candidates"] == ["AVAX", "Kraken"] and out["asset"] == "AVAX"


def test_label_article_anon_masks_and_skips_asset():
    row = {"store": "alpaca", "symbols": "BNBUSD", "headline": "Binance halts withdrawals",
           "summary": ""}
    client = ScriptedClient([response({"insolvency_halt": 0.9})] * 2)
    out = label_article(client, row, anon=True)
    for state, questions in client.calls:
        assert "Binance" not in state["headline"] and "ENTITY_12" in state["headline"]
        assert "asset" not in questions
    assert out["candidates"] == [] and out["asset"] is None
