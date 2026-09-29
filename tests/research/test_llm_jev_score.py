"""Gate arithmetic and diagnostics on hand-built cases."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import RoundData  # noqa: E402
from llm_jev_questions import CLASSES  # noqa: E402
from llm_jev_score import (  # noqa: E402
    anon_agreement, asset_link, diagnostics, evaluate, gate_rows, wilson,
)


def ev(cls, asset):
    return {"class": cls, "asset": asset}


def lab(events, probs=None, cands=("X",)):
    probs = probs or {c: (0.9 if any(e["class"] == c for e in events) else 0.1) for c in CLASSES}
    raw = {"answers": {f"ev_{c}": {"type": "noul", "noul": probs[c]} for c in CLASSES},
           "usage": {"cost": 0.0002}, "_latency_s": 0.3}
    return {"events": events, "probs": probs, "delta": {c: 0.0 for c in CLASSES},
            "flip": False, "candidates": list(cands),
            "asset": events[0]["asset"] if events else None, "raw": [raw, raw]}


def test_wilson_known_value():
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-3) and hi == pytest.approx(0.9433, abs=1e-3)
    assert wilson(0, 0) is None


def test_gate_rows_pooling():
    rows = gate_rows({"hack": {"tp": 9, "fp": 1, "fn": 1},
                      "regulatory": {"tp": 3, "fp": 2, "fn": 1},
                      "unlock_emission": {"tp": 1, "fp": 0, "fn": 1}})
    assert set(rows) == {"hack", "pooled_small"}
    assert rows["hack"]["precision"] == pytest.approx(0.9)
    assert rows["pooled_small"]["tp"] == 4 and rows["pooled_small"]["fp"] == 2
    assert rows["pooled_small"]["precision"] == pytest.approx(4 / 6)
    assert rows["pooled_small"]["recall"] == pytest.approx(4 / 6)


def test_asset_link_uses_review_and_rejects_none():
    truth = {1: [ev("hack", "Poly Network")], 2: [ev("hack", "Bitcoin")]}
    pred = {1: [ev("hack", "Ronin")], 2: [ev("hack", None)]}
    assert asset_link(truth, pred, {"1|hack": True, "2|hack": True})["value"] == 0.5
    assert asset_link(truth, pred, {})["value"] == 0.0


def test_anon_agreement():
    named = {"1": {"events": [ev("hack", "X")]}, "2": {"events": []}}
    anon = {"1": {"events": [ev("hack", None)]}, "2": {"events": [ev("regulatory", None)]}}
    assert anon_agreement(named, anon) == {"agree": 1, "n": 2, "value": 0.5}


def test_evaluate_pass_and_fail():
    truth = {i: [ev("hack", "Bitcoin")] for i in range(12)}
    named = {str(i): {"events": [ev("hack", "BTC")]} for i in range(12)}
    events = {i: named[str(i)]["events"] for i in range(12)}
    result = evaluate(truth, events, {}, named, dict(named))
    assert result["verdict"] == "PASS"
    assert result["gates"]["prefilter_recall"]["status"] == "not_applicable"
    worse = {i: events[i] + [ev("regulatory", "BTC")] for i in range(12)}
    assert evaluate(truth, worse, {}, named, dict(named))["verdict"] == "FAIL"


def test_diagnostics_shape():
    frame = pd.DataFrame({"sample_idx": [1, 2], "prefilter": [True, False],
                          "store": "gdelt", "headline": "h", "summary": "", "content": ""})
    frame.index = frame["sample_idx"].to_numpy()
    truth = {1: [ev("hack", "X")], 2: []}
    rounds = {"v1": RoundData("v1", frame, dict(truth), dict(truth), frozenset(), (), {})}
    named = {"1": lab([ev("hack", "X")]), "2": lab([])}
    meta = {"spent_usd": 0.0008, "calls": 4}
    out = diagnostics(rounds, truth, named, meta)
    assert out["asset_candidate_coverage"]["value"] == 1.0
    assert out["stability"]["flip_rate"] == 0.0
    assert out["threshold_sweep"]["0.5"]["hack"]["tp"] == 1
    assert out["cost"]["per_article_usd"] == pytest.approx(0.0004)
    assert out["prefilter_negative_recall"]["value"] is None
    assert len(out["reliability"]["hack"]) == 10
