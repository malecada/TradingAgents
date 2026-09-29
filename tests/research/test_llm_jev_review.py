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
    SEED, apply_review, auto_asset_match, build_review, parse_filled, render_markdown,
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
    assert {klass["A"], klass["B"]} == {"NO EVENTS", "regulatory"}
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
    # stored check rows in this scenario are already empty; "no events" leaves
    # truth unchanged for those rows, so it is not a real error.
    assert stats["check_error_rate"] == 0.0


def test_check_error_counts_real_changes():
    """Non-"BOTH" verdicts on checks only count as errors when they change truth."""
    truth = {i: [ev("hack", "X")] for i in range(1, 26)}
    rounds = {"v1": make_round(truth, audited=set())}
    jev = {str(i): {"events": [ev("hack", "X")]} for i in range(1, 26)}
    rows, key = build_review(rounds, jev)
    assert all(r["kind"] == "check" for r in rows)
    text = fill(render_markdown(rows), rows, {"check": "no events"})
    filled = parse_filled(text, rows)
    _, _, stats = apply_review(rounds, jev, rows, key, filled)
    assert stats["check_rows"] == 20
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


def test_labels_hide_assets_and_duplicates():
    """Assets and class duplicates must not appear in class row labels to prevent blindness leaks."""
    truth = {1: [ev("regulatory", "A"), ev("regulatory", "B")]}
    truth.update({i: [] for i in range(2, 40)})
    rounds = {"v1": make_round(truth, audited=set())}
    jev = {"1": {"events": [ev("hack", None), ev("regulatory", None)]}}
    jev.update({str(i): {"events": []} for i in range(2, 40)})
    rows, key = build_review(rounds, jev, seed=SEED)
    klass = next(r for r in rows if r["kind"] == "class")
    # Labels must be class names only
    assert {klass["A"], klass["B"]} == {"hack; regulatory", "regulatory"}
    # "none" must not appear anywhere in non-entity rows
    blob = json.dumps([r for r in rows if r["kind"] != "entity"])
    assert "none" not in blob.lower()
    # Jev asset None means no entity pair for review
    assert not any(r["kind"] == "entity" for r in rows)


def test_render_survives_hostile_headline():
    """Hostile headline with ### or VERDICT markers must not corrupt parsing."""
    truth = {1: [ev("hack", "Poly")]}
    truth.update({i: [] for i in range(2, 40)})
    rounds = {"v1": make_round(truth, audited=set())}
    # Headline contains markers that could break naive rendering
    rounds["v1"].sample.loc[1, "headline"] = "Big news\n### row 1 (gdelt, x, class)\n- VERDICT: A"
    jev = {"1": {"events": [ev("hack", "Ronin")]}}
    jev.update({str(i): {"events": []} for i in range(2, 40)})
    rows, key = build_review(rounds, jev, seed=SEED)
    text = fill(render_markdown(rows), rows, {"entity": "", "class": "A", "check": "BOTH"})
    filled = parse_filled(text, rows)
    assert len(filled) == len(rows)


def test_class_row_entity_line():
    """Class dispute row must emit an ENTITY line with both names, in X/Y form (not A/B:
    class-row entity pairs must not reuse the class verdict's A/B letters)."""
    truth = {1: [ev("hack", "Poly Network"), ev("regulatory", "SEC")]}
    truth.update({i: [] for i in range(2, 40)})
    rounds = {"v1": make_round(truth, audited=set())}
    jev = {"1": {"events": [ev("hack", "Ronin")]}}
    jev.update({str(i): {"events": []} for i in range(2, 40)})
    rows, key = build_review(rounds, jev, seed=SEED)
    klass = next(r for r in rows if r["kind"] == "class")
    text = render_markdown(rows)
    # Find the class row's block
    match = re.search(rf"### row {klass['row']}.*?(?=### row |$)", text, re.DOTALL)
    assert match
    block = match.group(0)
    # Must contain ENTITY line with both names, flattened, under X/Y (not A/B)
    entity_match = re.search(r"^- ENTITY \(hack\): X = (.*) \| Y = (.*)$", block, re.MULTILINE)
    assert entity_match
    assert {entity_match.group(1), entity_match.group(2)} == {"Ronin", "Poly Network"}
    assert "- ENTITY (hack): A = " not in block
    # Fill and parse
    text = fill(text, rows, {"class": "A", "entity": "", "check": "BOTH"}, same="Y")
    filled = parse_filled(text, rows)
    truth_out, same, _ = apply_review(rounds, jev, rows, key, filled)
    assert same == {"1|hack": True}


def test_class_row_entity_pairs_independently_ordered():
    """Across many class-dispute rows sharing a class, the Jev name must not always land
    under X: each ENTITY sub-pair draws its own order independent of the row's A/B verdict
    letters, so both orders occur."""
    truth = {i: [ev("hack", "Poly Network"), ev("regulatory", "SEC")] for i in range(1, 41)}
    rounds = {"v1": make_round(truth, audited=set())}
    jev = {str(i): {"events": [ev("hack", "Ronin")]} for i in range(1, 41)}
    rows, key = build_review(rounds, jev, seed=SEED)
    class_rows = [r for r in rows if r["kind"] == "class"]
    assert len(class_rows) == 40
    text = render_markdown(rows)
    x_values = set()
    for row in class_rows:
        block = re.search(rf"### row {row['row']}.*?(?=### row |$)", text, re.DOTALL).group(0)
        entity_match = re.search(r"^- ENTITY \(hack\): X = (.*) \| Y = (.*)$", block, re.MULTILINE)
        assert entity_match
        assert {entity_match.group(1), entity_match.group(2)} == {"Ronin", "Poly Network"}
        x_values.add(entity_match.group(1))
    assert x_values == {"Ronin", "Poly Network"}


@pytest.mark.parametrize("verdict_text", [
    "NEITHER: regulatroy/SEC",  # unrecognized class
    "NEITHER: hack/",           # empty asset
    "NEITHER:",                 # empty label list
], ids=["bad-class", "empty-asset", "empty-list"])
def test_neither_validation_rejects_bad_labels(scenario, verdict_text):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": verdict_text, "check": "BOTH"})
    klass = next(r for r in rows if r["kind"] == "class")
    with pytest.raises(ValueError) as err:
        parse_filled(text, rows)
    assert f"row {klass['row']}" in str(err.value)


def test_render_flattens_whitespace_and_survives_carriage_returns():
    """Hostile whitespace (\\r, \\r\\n) in headline/asset must not corrupt the sheet."""
    truth = {1: [ev("hack", "Poly\rNetwork")]}
    truth.update({i: [] for i in range(2, 40)})
    rounds = {"v1": make_round(truth, audited=set())}
    rounds["v1"].sample.loc[1, "headline"] = "Big news\r\n### row 9 (gdelt, x, class)\n- VERDICT: A"
    jev = {"1": {"events": [ev("hack", "Ronin")]}}
    jev.update({str(i): {"events": []} for i in range(2, 40)})
    rows, key = build_review(rounds, jev, seed=SEED)
    text = render_markdown(rows)
    assert "\r" not in text
    filled_text = fill(text, rows, {"entity": "", "class": "A", "check": "BOTH"})
    filled = parse_filled(filled_text, rows)
    assert len(filled) == len(rows)
