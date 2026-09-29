"""C1 truth rebuild from committed artifacts (read-only; no network)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import (  # noqa: E402
    check_reproduction, class_counts, dir_reader, load_rounds, match_events,
    parse_labels, parse_sheet, published_counts,
)


def test_parse_labels_single_multi_and_empty():
    assert parse_labels("regulatory/Republic/sev1") == [
        {"class": "regulatory", "asset": "Republic", "severity": 1}]
    assert parse_labels("regulatory/Binance/sev3; regulatory/Coinbase/sev3") == [
        {"class": "regulatory", "asset": "Binance", "severity": 3},
        {"class": "regulatory", "asset": "Coinbase", "severity": 3}]
    assert parse_labels("NO EVENTS") == []
    assert parse_labels("\\NO EVENTS") == []
    assert parse_labels("hack/Poly Network") == [{"class": "hack", "asset": "Poly Network"}]
    assert parse_labels("hack/A/B/sev2") == [{"class": "hack", "asset": "A/B", "severity": 2}]


def test_parse_labels_rejects_garbage():
    with pytest.raises(ValueError):
        parse_labels("just words")


def test_parse_sheet_reads_blocks():
    text = ("### row 4 (gdelt, 2024-12-19, disagreement)\n\n**H**\n\n"
            "- A: regulatory/Republic/sev1\n- B: NO EVENTS\n- VERDICT: \\_\\_\\_\\_B\n\n"
            "### row 9 (gdelt, 2022-08-08, agreement-check)\n\n"
            "- A: hack/X/sev2\n- B: hack/X/sev2\n- VERDICT: BOTH\n")
    rows = parse_sheet(text)
    assert rows[4] == ([{"class": "regulatory", "asset": "Republic", "severity": 1}], [], "B")
    assert rows[9][2] == "BOTH"


def test_match_and_counts_hand_example():
    truth = {1: [{"class": "hack", "asset": "X"}, {"class": "regulatory", "asset": "Y"}],
             2: [],
             3: [{"class": "listing_delisting", "asset": "Z"}]}
    pred = {1: [{"class": "hack", "asset": "X2"}],
            2: [{"class": "hack", "asset": "Q"}],
            3: [{"class": "listing_delisting", "asset": "Z"},
                {"class": "listing_delisting", "asset": "Z"}]}
    assert class_counts(truth, pred) == {
        "hack": {"tp": 1, "fp": 1, "fn": 0},
        "regulatory": {"tp": 0, "fp": 0, "fn": 1},
        "listing_delisting": {"tp": 1, "fp": 1, "fn": 0}}
    pairs, false_pos, false_neg = match_events(truth[1], pred[1])
    assert pairs == [({"class": "hack", "asset": "X2"}, {"class": "hack", "asset": "X"})]
    assert false_pos == [] and false_neg == [{"class": "regulatory", "asset": "Y"}]


def test_rebuild_reproduces_published_c1_counts():
    rounds = load_rounds(dir_reader(ROOT))
    for name, data in rounds.items():
        assert class_counts(data.truth, data.extractor) == published_counts(data), name
    check_reproduction(rounds)


def test_round_shapes():
    rounds = load_rounds(dir_reader(ROOT))
    v1, v2 = rounds["v1"], rounds["v2"]
    assert len(v1.sample) == 300 and len(v2.sample) == 100
    assert len(v1.audited) == 115 and len(v2.audited) == 39
    assert len(v1.anon_ids) == 50 and len(v2.anon_ids) == 50
    assert not set(v1.truth) & set(v2.truth)


def test_reproduction_guard_detects_tampering():
    v1 = load_rounds(dir_reader(ROOT))["v1"]
    idx = next(i for i, events in v1.truth.items() if events)
    tampered = dict(v1.truth)
    tampered[idx] = []
    with pytest.raises(ValueError, match="v1"):
        check_reproduction({"v1": replace(v1, truth=tampered)})
