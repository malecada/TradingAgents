"""Frozen Jev wording, state and candidate generator (no network)."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_questions import (  # noqa: E402
    CLASS_DEFINITIONS, CLASSES, GENERAL_RULES, V2_RULES, build_questions, build_state,
    candidates, noul_instruction,
)


def test_class_definitions_are_verbatim_c1_prompt_text():
    from llm_event_xs_extract import PROMPT, PROMPT_V2
    flat = " ".join(PROMPT.split())
    flat_v2 = " ".join(PROMPT_V2.split())
    for cls, definition in CLASS_DEFINITIONS.items():
        assert f"- {cls}: {definition}" in flat, cls
    for cls, rule in V2_RULES.items():
        assert f"- {cls}: {rule}" in flat_v2, cls
    assert ("Only report events the article itself asserts as fact or formal action "
            "(not speculation, price commentary, or opinion).") in flat
    assert "No knowledge of later events; judge only the given text." in flat
    assert set(CLASS_DEFINITIONS) == set(CLASSES)


def test_noul_instruction_composition():
    text = noul_instruction("regulatory")
    assert text.startswith("The article reports a 'regulatory' event. Definition: government/agency action")
    assert "Additional rule: the target must be a crypto asset" in text
    assert text.endswith(GENERAL_RULES)
    assert "Additional rule" not in noul_instruction("hack")


def test_candidates_title_case_headline():
    row = {"store": "gdelt", "symbols": "BTCUSD", "summary": "",
           "headline": "Bitcoin Miner Greenidge Faces Setback as Regulator Denies Permit Application"}
    assert candidates(row) == [
        "Bitcoin", "Bitcoin Miner Greenidge", "Bitcoin Miner", "Miner Greenidge", "Miner",
        "Greenidge", "Setback", "Regulator", "Permit Application", "Permit", "Application"]


def test_candidates_alpaca_symbols_first():
    row = {"store": "alpaca", "symbols": "AVAXUSD,ETHUSD", "summary": "",
           "headline": "Kraken lists AVAX"}
    assert candidates(row) == ["AVAX", "ETH", "Kraken"]


def test_candidates_none_found():
    assert candidates({"store": "gdelt", "headline": "prices slide 5% as traders wait",
                       "summary": ""}) == []


def test_candidates_capped_at_30():
    headline = " and ".join(f"Name{i}" for i in range(40))
    assert len(candidates({"store": "gdelt", "headline": headline, "summary": ""})) == 30


def test_build_state_fields():
    row = {"headline": "Héadline 한국", "summary": float("nan"), "content": "x" * 5000}
    assert build_state(row) == {"headline": "Héadline 한국", "content": "x" * 4000}
    upper = build_state(row, str.upper)
    assert upper == {"headline": "HÉADLINE 한국", "content": "X" * 4000}
    assert build_state({"headline": None, "summary": "S"}) == {"headline": "", "summary": "S"}
    doubled = build_state({"headline": "h", "content": "x" * 5000}, lambda s: s.replace("x", "xx"))
    assert doubled["content"] == "xx" * 4000  # truncate to 4,000 first, then transform


def test_build_questions_shape():
    q = build_questions(["Kraken", "AVAX"], reverse=False)
    assert list(q) == [f"ev_{c}" for c in CLASSES] + ["asset"]
    assert all(q[f"ev_{c}"] == {"type": "noul", "instructions": noul_instruction(c)} for c in CLASSES)
    assert list(q["asset"]["criteria"]) == ["c00", "c01", "none"]
    assert q["asset"]["criteria"]["c01"] == "AVAX"
    assert q["asset"]["type"] == "choice"
    r = build_questions(["Kraken", "AVAX"], reverse=True)
    assert list(r["asset"]["criteria"]) == ["c01", "c00", "none"]
    assert "asset" not in build_questions([], reverse=False)
    assert "asset" not in build_questions(["X"], reverse=False, with_asset=False)


QUESTIONS_SHA256 = "5204286177c37570653da49d476129533474db67143e8d7c613986cf01c784a0"


def test_questions_hash_pinned():
    from llm_jev_questions import questions_sha256
    assert questions_sha256() == QUESTIONS_SHA256
