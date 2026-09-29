"""Blind review sheet: construction, blindness, rendering, parsing, application."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import RoundData  # noqa: E402
from llm_jev_review import (  # noqa: E402
    apply_review, auto_asset_match, build_review, parse_filled, render_markdown,
)


def make_round(truth: dict, audited: set, name: str = "v1") -> RoundData:
    idxs = sorted(truth)
    frame = pd.DataFrame({"sample_idx": idxs, "headline": [f"Headline {i}" for i in idxs],
                          "summary": "", "content": "", "store": "gdelt", "symbols": "BTCUSD",
                          "event_ts": pd.Timestamp("2023-01-02", tz="UTC"), "prefilter": True})
    frame.index = frame["sample_idx"].to_numpy()
    return RoundData(name, frame, dict(truth), dict(truth), frozenset(audited), (), {})


def ev(cls, asset):
    return {"class": cls, "asset": asset}


@pytest.fixture()
def scenario():
    truth = {1: [ev("hack", "Poly Network")], 2: [ev("regulatory", "SEC target")]}
    truth.update({i: [] for i in range(3, 40)})
    rounds = {"v1": make_round(truth, audited={1})}
    jev = {"1": {"events": [ev("hack", "Ronin")]}, "2": {"events": []}}
    jev.update({str(i): {"events": []} for i in range(3, 40)})
    return rounds, jev


def test_auto_asset_match_rules():
    assert auto_asset_match("BTC", "Bitcoin")
    assert auto_asset_match("North Korean", "North Korean computer programmers")
    assert auto_asset_match("Poly Network", "poly network")
    assert not auto_asset_match("Binance", "Coinbase")
    assert not auto_asset_match(None, "X") and not auto_asset_match("X", "")


def test_build_review_kinds_blindness_and_determinism(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    kinds = sorted(r["kind"] for r in rows)
    assert kinds.count("entity") == 1 and kinds.count("class") == 1
    assert kinds.count("check") == 20
    entity = next(r for r in rows if r["kind"] == "entity")
    assert {entity["A"], entity["B"]} == {"Ronin", "Poly Network"}
    k = key[str(entity["row"])]
    assert entity[next(s for s in "AB" if k[s] == "jev")] == "Ronin"
    klass = next(r for r in rows if r["kind"] == "class")
    assert {klass["A"], klass["B"]} == {"NO EVENTS", "regulatory/SEC target"}
    blob = json.dumps(rows)
    assert '"jev"' not in blob and '"stored"' not in blob
    assert build_review(rounds, jev) == (rows, key)


def fill(text: str, rows: list[dict], verdicts: dict[str, str], same: str = "Y") -> str:
    kinds = {r["row"]: r["kind"] for r in rows}
    out = []
    for block in re.split(r"(?m)^(?=### row )", text):
        head = re.match(r"### row (\d+)", block)
        if head:
            kind = kinds[int(head.group(1))]
            if kind in verdicts:
                block = block.replace("- VERDICT: \n", f"- VERDICT: {verdicts[kind]}\n")
            block = re.sub(r"(?m)^(- SAME \([a-z_]+\):) $", rf"\1 {same}", block)
        out.append(block)
    return "".join(out)


def test_render_parse_apply_roundtrip(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": "A", "check": "BOTH"})
    filled = parse_filled(text, rows)
    truth, same, stats = apply_review(rounds, jev, rows, key, filled)
    klass = next(r for r in rows if r["kind"] == "class")
    expected = [] if key[str(klass["row"])]["A"] == "jev" else [ev("regulatory", "SEC target")]
    assert truth[2] == expected
    assert same == {"1|hack": True}
    assert stats["check_rows"] == 20 and stats["check_error_rate"] == 0.0
    assert truth[1] == [ev("hack", "Poly Network")]


def test_neither_and_no_events_on_checks(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows,
                {"class": "neither: hack/Poly", "check": "no events"}, same="n")
    filled = parse_filled(text, rows)
    truth, same, stats = apply_review(rounds, jev, rows, key, filled)
    assert truth[2] == [{"class": "hack", "asset": "Poly"}]
    assert same == {"1|hack": False}
    assert stats["check_error_rate"] == 1.0


def test_parse_normalizes_case_and_yes_no(scenario):
    rounds, jev = scenario
    rows, _ = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": " b ", "check": "Both"}, same="yes")
    filled = parse_filled(text, rows)
    assert {f["verdict"] for f in filled.values() if f["verdict"]} <= {"B", "BOTH"}


def test_parse_reports_all_problems(scenario):
    rounds, jev = scenario
    rows, _ = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": "NEITHER", "check": "maybe"}, same="")
    with pytest.raises(ValueError) as err:
        parse_filled(text, rows)
    message = str(err.value)
    assert "NEITHER" in message and "maybe" in message and "SAME" in message
    assert message.count("row ") >= 22
