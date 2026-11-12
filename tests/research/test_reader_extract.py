"""Reader configuration (Charter 2), extraction side: record schema and prompts, validation, call cache, reader
calls with one re-read, consensus and adjudication, reading sets, asset-week text features and the extraction
script. Synthetic fixtures only; no market data, no network."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import reader_extract as rx  # noqa: E402
from tradingagents.dossier.or_client import ORError, SpendCapError  # noqa: E402
from tradingagents.reader import charter2 as c2, consensus, features, reading, schema  # noqa: E402
from tradingagents.reader.extract import (CallCache, CallFailed, Reader, call_key, clean, evidence_ok, normalize,  # noqa: E402
                                          validate, well_formed)
from tradingagents.reader.reading import Unit  # noqa: E402

COST = 0.0001
DECISION = pd.Timestamp("2023-03-11", tz="UTC")           # Saturday 00:00 UTC after the Friday card of 2023-03-10
FRIDAY = DECISION - pd.Timedelta(days=1)
DAY, WEEK = pd.Timedelta(days=1), pd.Timedelta(days=7)


# ---------------------------------------------------------------- stand-in client
def hashed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest(), 16)


def careful_record(summary: str, alias: str) -> dict:
    """A well-formed record with evidence from the text: a fixed function of the summary and the asset token."""
    h = hashed(summary, alias)
    relevance = ("subject",) * 7 + ("side_mention",) * 2 + ("not_about",)
    return {"asset": alias, "relevance": relevance[h % 10], "event_class": schema.EVENT_CLASSES[(h >> 8) % len(schema.EVENT_CLASSES)],
            "status": schema.STATUSES[(h >> 16) % 3], "direction": schema.DIRECTIONS[(h >> 24) % 4],
            "materiality": 1 + (h >> 32) % 3, "evidence": " ".join(summary.split()[:3])}


def default_answer(role: str, summary: str, aliases: list[str], retry: bool) -> list[dict]:
    """Reader A and the adjudicator give the careful record; reader B falls back to neutral and materiality 1
    on a quarter of the assets, which creates disagreements."""
    out = []
    for alias in aliases:
        record = careful_record(summary, alias)
        if role == "B" and (hashed(summary, alias) >> 40) % 4 == 0:
            record.update(direction="neutral", materiality=1)
        out.append(record)
    return out


class FakeClient:
    """Stand-in for ``StructuredClient``: answers from the prompt alone, deterministic and thread-safe.
    ``answer(role, summary, aliases, retry)`` gives the records; ``fail`` with the same arguments makes the call
    raise ``ORError``; after ``cap_calls`` answered calls every call raises ``SpendCapError``."""
    model = "fake/model"

    def __init__(self, answer=None, fail=None, cap_calls=None, cost=COST):
        self.answer, self.fail, self.cap_calls, self.cost = answer or default_answer, fail, cap_calls, cost
        self.calls, self.attempts, self.spent_usd, self.log, self.prompts = 0, 0, 0.0, [], []
        self._lock = threading.Lock()

    def call(self, prompt, schema_, schema_name="answer", system=None, max_tokens=None):
        role = "J" if schema.ADJUDICATOR in system else "B" if schema.REVIEWER in system else "A"
        summary = re.search(r"^Summary: (.*)$", prompt, flags=re.M).group(1)
        aliases = re.findall(r"^- (\S+)", prompt, flags=re.M)
        retry = schema.RETRY_LINE in prompt
        with self._lock:
            self.attempts += 1
            if self.cap_calls is not None and self.calls >= self.cap_calls:
                raise SpendCapError("spend cap reached")
            if self.fail is not None and self.fail(role, summary, aliases, retry):
                raise ORError("provider unavailable")
            self.calls += 1
            self.spent_usd += self.cost
            self.log.append((role, tuple(aliases), retry))
            self.prompts.append(prompt)
            n = self.calls
        return ({"records": self.answer(role, summary, aliases, retry)},
                {"model": self.model, "provider": "Fake", "cost": self.cost, "prompt_tokens": 400, "completion_tokens": 60,
                 "reasoning_tokens": 0, "latency_s": 0.5, "id": f"gen-{n}"})


def scripted(table: dict):
    """An answer function from {(role, retry): records}; only requested assets are returned."""
    def answer(role, summary, aliases, retry):
        return [r for r in table.get((role, retry), []) if r["asset"] in aliases]
    return answer


SUMMARY = "Asset_A was listed on Exchange_1 after a security review, while Asset_B lost a tenth of its supply."


def _unit(doc_id="d1", summary=SUMMARY, assets=(("Asset_A", "AAA"), ("Asset_B", "BBB")), type_="event", source="wayback") -> Unit:
    return Unit(doc_id=doc_id, type=type_, source=source, summary=summary, assets=tuple(assets))


def _rec(asset="Asset_A", relevance="subject", event_class="exchange_listing", status="occurred", direction="favourable",
         materiality=2, evidence="was listed on Exchange_1") -> dict:
    return {"asset": asset, "relevance": relevance, "event_class": event_class, "status": status, "direction": direction,
            "materiality": materiality, "evidence": evidence}


def _fields(record: dict) -> dict:
    return {f: record[f] for f in schema.FIELDS}


# ---------------------------------------------------------------- synthetic reader store
def store_frames(weeks: int = 20, n_syms: int = 12, docs_per_week: int = 10, seed: int = 3):
    """(items, docs, cards) in the shape of the reader store. Six document kinds in rotation: news event on two
    assets, news opinion, community post, news event filed under an asset without a token in the summary, price
    recap (typed, not read) and an untyped document (no row in the document table)."""
    rng = np.random.default_rng(seed)
    fridays = pd.date_range(c2.PANEL_START, periods=weeks, freq="7D", tz="UTC")
    syms = [f"S{i:02d}USDT" for i in range(n_syms)]
    bases = [s[:-4] for s in syms]
    cards = pd.DataFrame([(d, s) for d in fridays for s in syms], columns=["date", "symbol"])
    for col in dict.fromkeys([*c2.QUANT, *c2.CONTROLS]):
        cards[col] = rng.normal(size=len(cards))
    cards["vol_ewma20"] = rng.uniform(0.3, 1.5, len(cards))
    cards["dvol_30d"] = rng.uniform(1.0, 100.0, len(cards))
    items, docs = [], []
    for w, friday in enumerate(fridays):
        for j in range(docs_per_week):
            doc_id, kind = f"doc{w:03d}{j:02d}", j % 6
            first, second = (bases[i] for i in rng.choice(n_syms, size=2, replace=False))
            ts = friday + DAY - pd.Timedelta(hours=float(rng.uniform(1, 167)))
            source = "reddit" if kind == 2 else "wayback"
            type_ = {0: "event", 1: "analysis_opinion", 2: "event", 3: "event", 4: "price_recap", 5: None}[kind]
            linked = [(first, "primary"), (second, "mentioned")] if kind == 0 else [(first, "primary")]
            for base, salience in linked:
                items.append({"doc_id": doc_id, "base": base, "source": source, "outlet": "outlet", "event_ts": ts,
                              "as_of_ts": ts + pd.Timedelta(hours=1), "salience": salience, "typed": type_ is not None,
                              "type": type_, "novelty": None, "affected": None})
            if type_ is None:
                continue
            alias_map = {0: {"Asset_A": f"asset:{first}", "Asset_B": f"asset:{second}", "Exchange_1": "org:venue"},
                         3: {}}.get(kind, {"Asset_A": f"asset:{first}"})
            summary = {0: f"Report {doc_id}: Asset_A completed step {w} on Exchange_1 while Asset_B announced a response.",
                       1: f"Note {doc_id}: the author expects Asset_A to gain users after release {j}.",
                       2: f"Post {doc_id}: holders of Asset_A report an outage of the main client.",
                       3: f"Report {doc_id}: the project disclosed a treasury decision without naming a token.",
                       4: f"Recap {doc_id}: Asset_A rose during the session."}[kind]
            docs.append({"doc_id": doc_id, "type": type_, "novelty": "new", "summary": summary,
                         "alias_map": json.dumps(alias_map), "leaky": False})
    return pd.DataFrame(items), pd.DataFrame(docs), cards


def write_store(root: Path, items: pd.DataFrame, docs: pd.DataFrame, cards: pd.DataFrame) -> None:
    for name, frame in (("items", items), ("docs", docs), ("cards", cards)):
        path = root / rx.INPUTS[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root: Path, message: str, *paths: str) -> None:
    git(root, "add", *paths)
    git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def script_root(root: Path, frozen: bool = True, **shape):
    """A synthetic checkout for the extraction script: its hashed source files, a charter text and the store."""
    git(root, "init", "-q")
    for path in rx.SOURCES:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, root / path)
    (root / "charter.md").write_text("synthetic charter\n" + ("" if frozen else f"Status: {rx.DRAFT_MARK}\n"))
    frames = store_frames(**shape)
    write_store(root, *frames)
    commit(root, "synthetic sources", "charter.md", *rx.SOURCES)
    return frames


def extract(root: Path, *args: str, client=None):
    return rx.main(["--charter", "charter.md", *args], root=root, client=client)


# ---------------------------------------------------------------- schema and prompts
def test_schema_enumerations_and_instruction_are_consistent():
    props = schema.RECORD_SCHEMA["properties"]["records"]["items"]
    assert props["required"] == ["asset", *schema.FIELDS] and props["additionalProperties"] is False
    assert props["properties"]["relevance"]["enum"] == list(schema.RELEVANCE)
    assert props["properties"]["event_class"]["enum"] == list(schema.EVENT_CLASSES)
    assert props["properties"]["status"]["enum"] == list(schema.STATUSES)
    assert props["properties"]["direction"]["enum"] == list(schema.DIRECTIONS)
    assert props["properties"]["materiality"]["enum"] == [1, 2, 3]
    for name in (*schema.RELEVANCE, *schema.EVENT_CLASSES, *schema.STATUSES, *schema.DIRECTIONS):
        assert name in schema.INSTRUCTION, name                      # every label an agent may return is explained
    assert set(features.CLASS_SIGN) == set(schema.EVENT_CLASSES) and set(features.DIRECTION_SIGN) == set(schema.DIRECTIONS)
    assert well_formed({k: v for k, v in schema.NOT_ABOUT.items()}) and schema.NOT_ABOUT["relevance"] == "not_about"


def test_system_prompts_by_role():
    assert schema.system_prompt("A") == schema.INSTRUCTION
    assert schema.system_prompt("B") == schema.INSTRUCTION + "\n\n" + schema.REVIEWER
    assert schema.system_prompt("J") == schema.INSTRUCTION + "\n\n" + schema.ADJUDICATOR
    with pytest.raises(ValueError):
        schema.system_prompt("C")


def test_unit_prompt_text():
    unit = _unit()
    text = schema.unit_prompt(unit, unit.aliases)
    assert text == f"Item type: event\nSource: news\nSummary: {SUMMARY}\nAssets:\n- Asset_A\n- Asset_B"
    assert schema.unit_prompt(unit, ["Asset_B"], retry=True) == (
        f"Item type: event\nSource: news\nSummary: {SUMMARY}\nAssets:\n- Asset_B\n\n{schema.RETRY_LINE}")
    filed = _unit(type_="analysis_opinion", source="reddit", assets=((schema.FILED_ALIAS, "AAA"),))
    assert schema.unit_prompt(filed, filed.aliases) == (
        f"Item type: opinion or analysis\nSource: community post\nSummary: {SUMMARY}\nAssets:\n"
        "- Filed_asset (the item is filed under this asset; the summary describes it without a token)")


def test_adjudication_prompt_shows_both_records_in_the_given_order():
    unit = _unit()
    first, second = {"Asset_A": _fields(_rec()), "Asset_B": None}, {"Asset_A": _fields(_rec(direction="neutral", materiality=1))}
    text = schema.adjudication_prompt(unit, ["Asset_A", "Asset_B"], first, second)
    assert text == (f"Item type: event\nSource: news\nSummary: {SUMMARY}\nAssets and the two records:\n"
                    f"- Asset_A\n  reader 1: {json.dumps(first['Asset_A'])}\n  reader 2: {json.dumps(second['Asset_A'])}\n"
                    "- Asset_B\n  reader 1: no valid record\n  reader 2: no valid record")
    assert list(json.loads(json.dumps(first["Asset_A"]))) == list(schema.FIELDS)
    assert schema.adjudication_prompt(unit, ["Asset_A"], first, second, retry=True).endswith("\n\n" + schema.RETRY_LINE)


def test_prompt_identity_follows_the_instructions(monkeypatch):
    before = schema.prompt_sha256()
    assert before == schema.prompt_sha256() and len(before) == 64
    monkeypatch.setattr(schema, "REVIEWER", schema.REVIEWER + " ")
    assert schema.prompt_sha256() != before


# ---------------------------------------------------------------- validation
def test_evidence_check_ignores_case_and_spacing():
    assert normalize("  Was   LISTED\non ") == "was listed on"
    assert evidence_ok({"evidence": "WAS listed  on exchange_1", "relevance": "subject"}, SUMMARY)
    assert not evidence_ok({"evidence": "was delisted", "relevance": "subject"}, SUMMARY)
    assert not evidence_ok({"evidence": "  ", "relevance": "subject"}, SUMMARY)        # an empty phrase supports nothing
    assert evidence_ok({"evidence": "", "relevance": "not_about"}, SUMMARY)


def test_validate_reasons_and_cleaning():
    parsed = {"records": [
        _rec("Asset_A"),
        _rec("Asset_A", direction="unfavourable"),                             # second record of an asset: ignored
        _rec("Asset_B", evidence="words that are not in the text"),
        _rec("Asset_C", materiality=4),
        _rec("Asset_D", relevance="not_about", event_class="legal_regulatory", direction="unfavourable", materiality=3, evidence=""),
        _rec("Asset_X"),                                                       # not requested: ignored
        "not a record"]}
    out, why = validate(parsed, ["Asset_A", "Asset_B", "Asset_C", "Asset_D", "Asset_E"], SUMMARY)
    assert why == {"Asset_A": "ok", "Asset_B": "evidence", "Asset_C": "malformed", "Asset_D": "ok", "Asset_E": "absent"}
    assert out["Asset_A"] == _fields(_rec()) and "asset" not in out["Asset_A"]
    assert out["Asset_B"] is None and out["Asset_C"] is None and out["Asset_E"] is None
    assert out["Asset_D"] == schema.NOT_ABOUT                                  # fixed neutral fields
    assert clean(_rec(relevance="not_about")) == schema.NOT_ABOUT
    for broken in (None, [], "text", {"records": None}, {"other": 1}):
        out, why = validate(broken, ["Asset_A"], SUMMARY)
        assert out == {"Asset_A": None} and why == {"Asset_A": "absent"}


@pytest.mark.parametrize("change", [{"relevance": "about"}, {"event_class": "merger"}, {"status": "done"}, {"direction": "up"},
                                    {"materiality": 0}, {"materiality": True}, {"materiality": "2"}, {"evidence": None}])
def test_malformed_records_are_rejected(change):
    assert well_formed(_rec()) and not well_formed({**_rec(), **change})


# ---------------------------------------------------------------- call cache
def test_call_cache_is_append_only_and_counts_every_payment(tmp_path):
    path = tmp_path / "cache" / "calls.jsonl"
    cache = CallCache(path)
    assert len(cache) == 0 and cache.get("k") is None and cache.paid_usd == 0.0
    cache.put("k", {"parsed": {"records": []}, "meta": {"cost": 0.25}, "role": "A"})
    cache.put("k", {"parsed": {"records": [1]}, "meta": {"cost": 0.5}, "role": "A"})       # a later line replaces
    cache.put("m", {"parsed": {}, "meta": None, "role": "B"})
    again = CallCache(path)
    assert len(again) == 2 and again.get("k")["parsed"] == {"records": [1]}
    assert again.paid_usd == cache.paid_usd == 0.75                              # replaced lines stay paid
    assert len(path.read_text().splitlines()) == 3
    frozen = CallCache.from_bytes(path.read_bytes())
    assert len(frozen) == 2 and frozen.paid_usd == 0.75 and sorted(map(json.dumps, frozen.values())) == sorted(map(json.dumps, again.values()))
    frozen.put("n", {"parsed": {}, "meta": {"cost": 1.0}})                       # nothing is written back
    assert len(path.read_text().splitlines()) == 3


def test_call_key_separates_model_role_and_prompt():
    keys = {call_key("m", "s", "p"), call_key("m2", "s", "p"), call_key("m", "s2", "p"), call_key("m", "s", "p2"),
            call_key("ms", "", "p"), call_key("m", "sp", "")}
    assert len(keys) == 6 and call_key("m", "s", "p") == call_key("m", "s", "p")


# ---------------------------------------------------------------- reader calls
def test_reader_rereads_only_assets_without_a_valid_record(tmp_path):
    table = {("A", False): [_rec("Asset_A"), _rec("Asset_B", evidence="invented words")],
             ("A", True): [_rec("Asset_B", event_class="token_supply_reduction", evidence="lost a tenth of its supply")]}
    client = FakeClient(scripted(table))
    reader = Reader(client, CallCache(tmp_path / "calls.jsonl"))
    out = reader.read("A", _unit())
    assert out["Asset_A"] == _fields(_rec()) and out["Asset_B"]["event_class"] == "token_supply_reduction"
    assert client.log == [("A", ("Asset_A", "Asset_B"), False), ("A", ("Asset_B",), True)]
    stats = reader.stats
    assert stats["first_read"]["A"] == {"ok": 1, "absent": 0, "malformed": 0, "evidence": 1}
    assert stats["reread"]["A"] == {"ok": 1, "absent": 0, "malformed": 0, "evidence": 0}
    assert stats["grounding"]["A"] == {"needed": 2, "found": 1}                 # first reads only
    assert stats["calls"] == 2 and stats["cached"] == 0 and stats["cost"] == pytest.approx(2 * COST)
    assert stats["providers"] == {"Fake": 2} and stats["prompt_tokens"] == 800 and stats["completion_tokens"] == 120


def test_reader_leaves_a_reading_missing_after_the_second_failure(tmp_path):
    table = {("B", False): [_rec("Asset_A", relevance="not_about", evidence="")], ("B", True): [_rec("Asset_B", materiality=7)]}
    client = FakeClient(scripted(table))
    reader = Reader(client, CallCache(tmp_path / "calls.jsonl"))
    out = reader.read("B", _unit())
    assert out == {"Asset_A": schema.NOT_ABOUT, "Asset_B": None} and client.calls == 2      # no third call
    assert reader.stats["first_read"]["B"] == {"ok": 1, "absent": 1, "malformed": 0, "evidence": 0}
    assert reader.stats["reread"]["B"] == {"ok": 0, "absent": 0, "malformed": 1, "evidence": 0}
    assert reader.stats["grounding"]["B"] == {"needed": 0, "found": 0}          # a clean not_about needs no phrase


def test_reader_answers_from_the_cache_without_a_client(tmp_path):
    path = tmp_path / "calls.jsonl"
    client = FakeClient()
    first = Reader(client, CallCache(path)).read("A", _unit())
    offline = Reader(None, CallCache(path), model=client.model)
    assert offline.read("A", _unit()) == first
    assert offline.stats["calls"] == 0 and offline.stats["cached"] == client.calls == len(offline.used)
    with pytest.raises(CallFailed):
        offline.read("B", _unit())                                               # never asked: not in the cache
    with pytest.raises(CallFailed):
        Reader(None, CallCache(path), model="other/model").read("A", _unit())    # another model: other keys


def test_failed_calls_are_not_cached_and_the_spend_limit_propagates(tmp_path):
    cache = CallCache(tmp_path / "calls.jsonl")
    with pytest.raises(CallFailed, match="provider unavailable"):
        Reader(FakeClient(fail=lambda *a: True), cache).read("A", _unit())
    assert len(cache) == 0 and not (tmp_path / "calls.jsonl").exists()
    with pytest.raises(SpendCapError):
        Reader(FakeClient(cap_calls=0), cache).read("A", _unit())
    assert len(cache) == 0


# ---------------------------------------------------------------- consensus
def test_agreement_rule():
    a = _fields(_rec())
    assert consensus.agree(a, dict(a))
    assert consensus.agree(a, {**a, "materiality": 3}) and consensus.agree(a, {**a, "materiality": 1, "evidence": "other"})
    assert not consensus.agree({**a, "materiality": 1}, {**a, "materiality": 3})
    for field, value in (("relevance", "side_mention"), ("event_class", "other"), ("status", "scheduled"), ("direction", "mixed")):
        assert not consensus.agree(a, {**a, field: value}), field
    assert consensus.agree(dict(schema.NOT_ABOUT), dict(schema.NOT_ABOUT))
    assert not consensus.agree(a, dict(schema.NOT_ABOUT)) and not consensus.agree(a, None) and not consensus.agree(None, None)
    assert consensus.merged({**a, "materiality": 3}, {**a, "materiality": 2, "evidence": "b"}) == {**a, "materiality": 2}


def test_resolve_agreement_needs_no_adjudicator(tmp_path):
    table = {("A", False): [_rec("Asset_A", materiality=3), _rec("Asset_B", relevance="not_about", evidence="")],
             ("B", False): [_rec("Asset_A", materiality=2, evidence="after a security review"),
                            _rec("Asset_B", relevance="not_about", event_class="other", evidence="")]}
    client = FakeClient(scripted(table))
    rows = consensus.resolve(Reader(client, CallCache(tmp_path / "calls.jsonl")), _unit())
    assert [role for role, *_ in client.log] == ["A", "B"]
    assert [list(row) for row in rows] == [consensus.RECORD_COLUMNS] * 2
    first, second = rows
    assert (first["doc_id"], first["base"], first["alias"], first["focus_only"], first["resolution"]) == ("d1", "AAA", "Asset_A", False, "agreed")
    assert first["materiality"] == 2 and first["evidence"] == "was listed on Exchange_1"          # reader A's fields, lower materiality
    assert (first["a_materiality"], first["b_materiality"]) == (3, 2)
    assert second["resolution"] == "agreed" and _fields(second) == schema.NOT_ABOUT and second["base"] == "BBB"


def test_resolve_sends_only_disputed_assets_to_the_adjudicator(tmp_path):
    ids = [f"d{i}" for i in range(20)]
    for doc_id in (next(d for d in ids if consensus.a_first(d)), next(d for d in ids if not consensus.a_first(d))):
        a_b = _rec("Asset_B", event_class="token_supply_reduction", direction="unfavourable", materiality=3, evidence="lost a tenth of its supply")
        b_b = {**a_b, "direction": "neutral", "materiality": 1}
        j_b = {**a_b, "direction": "mixed", "materiality": 2}
        table = {("A", False): [_rec("Asset_A"), a_b], ("B", False): [_rec("Asset_A"), b_b], ("J", False): [_rec("Asset_A", direction="mixed"), j_b]}
        client = FakeClient(scripted(table))
        rows = consensus.resolve(Reader(client, CallCache(tmp_path / f"{doc_id}.jsonl")), _unit(doc_id=doc_id))
        assert client.log == [("A", ("Asset_A", "Asset_B"), False), ("B", ("Asset_A", "Asset_B"), False), ("J", ("Asset_B",), False)]
        shown_first, shown_second = (a_b, b_b) if consensus.a_first(doc_id) else (b_b, a_b)
        assert f"- Asset_B\n  reader 1: {json.dumps(_fields(shown_first))}\n  reader 2: {json.dumps(_fields(shown_second))}" in client.prompts[-1]
        assert "- Asset_A" not in client.prompts[-1]
        assert rows[0]["resolution"] == "agreed" and rows[0]["direction"] == "favourable"
        assert rows[1]["resolution"] == "adjudicated" and (rows[1]["direction"], rows[1]["materiality"]) == ("mixed", 2)
        assert (rows[1]["a_direction"], rows[1]["b_direction"], rows[1]["a_materiality"], rows[1]["b_materiality"]) == ("unfavourable", "neutral", 3, 1)
    assert consensus.a_first("d1") == consensus.a_first("d1")


def test_resolve_missing_readings(tmp_path):
    good = _rec("Asset_A")
    # one reading missing: the adjudicator decides, seeing "no valid record" for the missing one
    client = FakeClient(scripted({("B", False): [good], ("J", False): [good]}))
    rows = consensus.resolve(Reader(client, CallCache(tmp_path / "one.jsonl")), _unit(assets=(("Asset_A", "AAA"),)))
    assert [role for role, *_ in client.log] == ["A", "A", "B", "J"] and "no valid record" in client.prompts[-1]
    assert rows[0]["resolution"] == "adjudicated" and rows[0]["a_relevance"] is None and rows[0]["b_relevance"] == "subject"
    # both readings missing: unresolved without an adjudication
    client = FakeClient(scripted({}))
    rows = consensus.resolve(Reader(client, CallCache(tmp_path / "none.jsonl")), _unit(assets=(("Asset_A", "AAA"),)))
    assert [role for role, *_ in client.log] == ["A", "A", "B", "B"]
    assert rows[0]["resolution"] == "unresolved" and all(rows[0][f] is None for f in schema.FIELDS)
    # the adjudicator gives no valid record: unresolved, both readings stay in the row
    table = {("A", False): [good], ("B", False): [_rec("Asset_A", direction="unfavourable")], ("J", False): [_rec("Asset_A", evidence="invented")],
             ("J", True): [_rec("Asset_A", evidence="invented again")]}
    client = FakeClient(scripted(table))
    rows = consensus.resolve(Reader(client, CallCache(tmp_path / "judge.jsonl")), _unit(assets=(("Asset_A", "AAA"),)))
    assert [role for role, *_ in client.log] == ["A", "B", "J", "J"]
    assert rows[0]["resolution"] == "unresolved" and rows[0]["direction"] is None
    assert (rows[0]["a_direction"], rows[0]["b_direction"]) == ("favourable", "unfavourable")


def test_filed_asset_rows_are_marked(tmp_path):
    unit = _unit(assets=((schema.FILED_ALIAS, "AAA"),))
    rows = consensus.resolve(Reader(FakeClient(), CallCache(tmp_path / "calls.jsonl")), unit)
    assert rows[0]["focus_only"] is True and rows[0]["alias"] == schema.FILED_ALIAS and rows[0]["base"] == "AAA"
    blank = consensus.unresolved_rows(unit)
    assert blank == [{**dict.fromkeys(consensus.RECORD_COLUMNS), "doc_id": "d1", "base": "AAA", "alias": schema.FILED_ALIAS,
                      "focus_only": True, "resolution": "unresolved"}]


def test_rebuild_from_the_cache_alone(tmp_path):
    items, docs, cards = store_frames(weeks=6, n_syms=8, docs_per_week=12)
    work, unit_list = rx.build_units(items, docs, cards)
    path = tmp_path / "calls.jsonl"
    live = Reader(FakeClient(), CallCache(path))
    rows = [row for unit in unit_list for row in consensus.resolve(live, unit)]
    assert len(rows) == len(work) and {r["resolution"] for r in rows} == {"agreed", "adjudicated"}
    again, reader, missing = consensus.rebuild(unit_list, CallCache.from_bytes(path.read_bytes()), "fake/model")
    assert again == rows and missing == []
    assert reader.stats["calls"] == 0 and reader.stats["cached"] == live.stats["calls"] == len(reader.used)
    assert reader.stats["first_read"] == live.stats["first_read"] and reader.stats["grounding"] == live.stats["grounding"]
    # a cache without the calls of one unit: that unit is unresolved and reported
    partial = Reader(FakeClient(), CallCache(tmp_path / "partial.jsonl"))
    for unit in unit_list[1:]:
        consensus.resolve(partial, unit)
    part, _, missing = consensus.rebuild(unit_list, partial.cache, "fake/model")
    assert missing == [unit_list[0].doc_id] and len(part) == len(rows)
    n_first = len(unit_list[0].assets)
    assert part[:n_first] == consensus.unresolved_rows(unit_list[0]) and part[n_first:] == rows[n_first:]


def test_record_table_round_trip(tmp_path):
    unit_a, unit_b = _unit(), _unit(doc_id="d2", assets=((schema.FILED_ALIAS, "CCC"),))
    reader = Reader(FakeClient(), CallCache(tmp_path / "calls.jsonl"))
    rows = consensus.resolve(reader, unit_a) + consensus.unresolved_rows(unit_b)
    frame = consensus.record_frame(rows)
    assert list(frame.columns) == consensus.RECORD_COLUMNS and frame["focus_only"].dtype == bool
    assert all(str(frame[c].dtype) == "Int64" for c in ("materiality", "a_materiality", "b_materiality"))
    frame.to_parquet(tmp_path / "records.parquet", index=False)
    stored = pd.read_parquet(tmp_path / "records.parquet")
    assert consensus.same_records(stored, frame) and consensus.same_records(frame, stored)
    assert consensus.record_rows(stored) == rows                                 # None for every missing cell
    changed = stored.copy()
    changed.loc[0, "direction"] = "mixed" if stored.loc[0, "direction"] != "mixed" else "neutral"
    assert not consensus.same_records(changed, frame) and not consensus.same_records(stored.iloc[:-1], frame)
    filled = stored.copy()
    filled.loc[len(filled) - 1, "relevance"] = "subject"                          # a value where the other table has none
    assert not consensus.same_records(filled, frame)


def _row(doc_id, resolution, final, a, b) -> dict:
    """A record row from (relevance, event_class, status, direction, materiality) tuples or None."""
    keys = schema.FIELDS[:-1]
    row = dict.fromkeys(consensus.RECORD_COLUMNS)
    row.update(doc_id=doc_id, base="AAA", alias="Asset_A", focus_only=False, resolution=resolution)
    for prefix, value in (("", final), ("a_", a), ("b_", b)):
        if value is not None:
            row.update({prefix + k: v for k, v in zip(keys, value)})
    return row


def test_quality_summary():
    listing = ("subject", "exchange_listing", "occurred", "favourable", 2)
    nothing = ("not_about", "other", "occurred", "neutral", 1)
    rows = [
        _row("d1", "agreed", listing, ("subject", "exchange_listing", "occurred", "favourable", 3), listing),
        _row("d1", "adjudicated", ("subject", "legal_regulatory", "scheduled", "unfavourable", 3),
             ("subject", "legal_regulatory", "scheduled", "unfavourable", 3), ("subject", "other", "occurred", "neutral", 1)),
        _row("d2", "adjudicated", ("side_mention", "other", "occurred", "neutral", 1), listing, ("side_mention", "other", "occurred", "neutral", 1)),
        _row("d2", "agreed", nothing, nothing, nothing),
        _row("d3", "unresolved", None, None, listing),
    ]
    q = consensus.quality(rows)
    assert (q["records"], q["documents"]) == (5, 3)
    assert q["valid_reading_a"] == 4 / 5 and q["valid_reading_b"] == 1.0
    agreement = q["agreement"]
    assert (agreement["rows_both_valid"], agreement["rows_both_about"]) == (4, 3)
    assert agreement["relevance"] == 3 / 4                                        # over rows with both readings
    assert agreement["event_class"] == 1 / 3 and agreement["status"] == 2 / 3 and agreement["direction"] == 1 / 3
    assert agreement["materiality_exact"] == 0.0 and agreement["materiality_within_one"] == 2 / 3
    assert q["resolution"] == {"agreed": 2 / 5, "adjudicated": 2 / 5, "unresolved": 1 / 5}
    assert q["documents_adjudicated"] == 1.0                                      # every document has a row that is not agreed
    assert q["final"]["relevance"] == {"subject": 2, "side_mention": 1, "not_about": 1}
    assert q["final"]["direction"] == {"favourable": 1, "unfavourable": 1} and q["final"]["materiality"] == {"2": 1, "3": 1}
    assert consensus.quality([]) == {"records": 0}
    only_missing = consensus.quality([_row("d9", "unresolved", None, None, None)])
    assert only_missing["agreement"]["direction"] is None and only_missing["resolution"]["unresolved"] == 1.0
    json.dumps(q, allow_nan=False)


# ---------------------------------------------------------------- reading sets
def _item(doc_id, base, salience="primary", source="wayback", type_="event", event_ts=DECISION - DAY, as_of_ts=None) -> dict:
    return {"doc_id": doc_id, "base": base, "source": source, "outlet": "outlet", "event_ts": event_ts,
            "as_of_ts": event_ts + pd.Timedelta(hours=1) if as_of_ts is None else as_of_ts, "salience": salience,
            "typed": type_ is not None, "type": type_, "novelty": None, "affected": None}


def _doc(doc_id, alias_map, type_="event") -> dict:
    return {"doc_id": doc_id, "type": type_, "novelty": "new", "summary": f"Summary of {doc_id}.",
            "alias_map": json.dumps(alias_map), "leaky": False}


def test_summary_assets_takes_the_first_alias_of_a_base():
    alias_map = json.dumps({"Asset_B": "asset:XRP", "Asset_A": "asset:BTC", "Exchange_1": "org:binance", "Asset_C": "asset:BTC"})
    assert reading.summary_assets(alias_map) == {"BTC": "Asset_A", "XRP": "Asset_B"}
    assert reading.summary_assets("{}") == {} and reading.summary_assets(json.dumps({"Exchange_1": "org:venue"})) == {}


def test_flag_items_marks_what_yields_a_record():
    items = pd.DataFrame([
        _item("token", "AAA"), _item("token", "BBB", salience="mentioned"),       # BBB linked but not in the summary
        _item("filed", "AAA"), _item("filed", "BBB", salience="mentioned"),       # no token, one primary link
        _item("two", "AAA"), _item("two", "BBB"),                                 # no token, two primary links
        _item("org", "CCC"),                                                      # only a non-asset token
        _item("recap", "AAA", type_="price_recap"),
        _item("opinion", "AAA", type_="analysis_opinion"),
        _item("untyped", "AAA", type_=None)])
    docs = pd.DataFrame([_doc("token", {"Asset_A": "asset:AAA"}), _doc("filed", {}), _doc("two", {}),
                         _doc("org", {"Exchange_1": "org:venue"}), _doc("recap", {"Asset_A": "asset:AAA"}, "price_recap"),
                         _doc("opinion", {"Asset_A": "asset:AAA"}, "analysis_opinion")])
    out = reading.flag_items(items, docs)
    assert list(out.columns) == [*items.columns, "in_summary", "focus_only", "read"] and len(out) == len(items)
    got = {(r.doc_id, r.base): (r.in_summary, r.focus_only, r.read) for r in out.itertuples()}
    assert got == {("token", "AAA"): (True, False, True), ("token", "BBB"): (False, False, False),
                   ("filed", "AAA"): (False, True, True), ("filed", "BBB"): (False, False, False),
                   ("two", "AAA"): (False, False, False), ("two", "BBB"): (False, False, False),
                   ("org", "CCC"): (False, True, True), ("recap", "AAA"): (True, False, False),
                   ("opinion", "AAA"): (True, False, True), ("untyped", "AAA"): (False, False, False)}


def test_reading_set_window_and_community_cap():
    hour = pd.Timedelta(hours=1)
    rows = [
        _item("edge", "AAA", event_ts=DECISION - 30 * DAY),                               # exactly 30 days old: inside
        _item("old", "AAA", event_ts=DECISION - 30 * DAY - pd.Timedelta(seconds=1)),
        _item("now", "AAA", event_ts=DECISION, as_of_ts=DECISION),                        # at the decision: inside
        _item("late", "AAA", event_ts=DECISION - hour, as_of_ts=DECISION + pd.Timedelta(seconds=1)),   # seen after the decision
        _item("future", "AAA", event_ts=DECISION + pd.Timedelta(seconds=1)),
        _item("outside", "ZZZ"),                                                          # not a member
        _item("side", "AAA", salience="mentioned"),                                       # news counts with any salience
        _item("post_side", "AAA", salience="mentioned", source="reddit"),                 # community posts only as primary
        _item("tie_b", "AAA", source="reddit", event_ts=DECISION - 25 * hour),
        _item("tie_a", "AAA", source="reddit", event_ts=DECISION - 25 * hour),
    ]
    rows += [_item(f"post{i:02d}", "AAA", source="reddit", event_ts=DECISION - i * hour) for i in (*range(1, 25), *range(26, 31))]
    rows += [_item(f"other{i}", "BBB", source="reddit", event_ts=DECISION - i * DAY) for i in range(1, 4)]
    items = pd.DataFrame(rows).sample(frac=1.0, random_state=0).reset_index(drop=True)
    got = reading.reading_set(items, ["AAA", "BBB"], DECISION)
    assert not got.duplicated(["doc_id", "base"]).any()
    expected = {"edge", "now", "side", "tie_a", *(f"post{i:02d}" for i in range(1, 25)), "other1", "other2", "other3"}
    assert set(got["doc_id"]) == expected                                               # 25 newest posts, tie by doc_id
    assert set(reading.reading_set(items, ["AAA"], DECISION, reddit_cap=2).query("source == 'reddit'")["doc_id"]) == {"post01", "post02"}
    assert set(reading.reading_set(items, ["AAA"], DECISION, lookback_days=1)["doc_id"]) >= {"now", "side"}
    assert "edge" not in set(reading.reading_set(items, ["AAA"], DECISION, lookback_days=1)["doc_id"])


def test_reading_sets_per_week_and_work_list():
    top = pd.DataFrame({"date": [FRIDAY - WEEK, FRIDAY - WEEK, FRIDAY, FRIDAY], "symbol": ["AAAUSDT", "BBBUSDT", "AAAUSDT", "CCCUSDT"],
                        "base": ["AAA", "BBB", "AAA", "CCC"]})
    items = pd.DataFrame([
        _item("both", "AAA", event_ts=DECISION - 8 * DAY), _item("both", "BBB", salience="mentioned", event_ts=DECISION - 8 * DAY),
        _item("recent", "AAA", event_ts=DECISION - DAY), _item("filed", "CCC", event_ts=DECISION - 2 * DAY),
        _item("recap", "AAA", type_="price_recap", event_ts=DECISION - 9 * DAY)])
    docs = pd.DataFrame([_doc("both", {"Asset_B": "asset:AAA", "Asset_A": "asset:BBB"}), _doc("recent", {"Asset_A": "asset:AAA"}),
                         _doc("filed", {}), _doc("recap", {"Asset_A": "asset:AAA"}, "price_recap")])
    sets = reading.reading_sets(reading.flag_items(items, docs), top)
    assert set(sets["decision"] - sets["friday"]) == {DAY}
    got = {(r.friday, r.doc_id, r.base) for r in sets.itertuples()}
    assert got == {(FRIDAY - WEEK, "both", "AAA"), (FRIDAY - WEEK, "both", "BBB"), (FRIDAY - WEEK, "recap", "AAA"),
                   (FRIDAY, "both", "AAA"), (FRIDAY, "recent", "AAA"), (FRIDAY, "recap", "AAA"), (FRIDAY, "filed", "CCC")}
    work = reading.work_list(sets)
    assert work.to_dict("records") == [{"doc_id": "both", "base": "AAA", "focus_only": False}, {"doc_id": "both", "base": "BBB", "focus_only": False},
                                       {"doc_id": "filed", "base": "CCC", "focus_only": True}, {"doc_id": "recent", "base": "AAA", "focus_only": False}]
    unit_list = reading.units(work, docs, items)
    assert unit_list == [Unit("both", "event", "wayback", "Summary of both.", (("Asset_A", "BBB"), ("Asset_B", "AAA"))),
                         Unit("filed", "event", "wayback", "Summary of filed.", ((schema.FILED_ALIAS, "CCC"),)),
                         Unit("recent", "event", "wayback", "Summary of recent.", (("Asset_A", "AAA"),))]
    assert unit_list[0].aliases == ["Asset_A", "Asset_B"]
    clash = pd.DataFrame({"doc_id": ["filed", "filed"], "base": ["CCC", "DDD"], "focus_only": [True, True]})
    with pytest.raises(ValueError, match="alias collision in filed"):
        reading.units(clash, docs, items)


def test_units_of_the_synthetic_store():
    items, docs, cards = store_frames(weeks=6, n_syms=8, docs_per_week=12)
    work, unit_list = rx.build_units(items, docs, cards)
    kind = {u.doc_id: int(u.doc_id[-2:]) % 6 for u in unit_list}
    assert len(unit_list) == 6 * 8 and set(kind.values()) == {0, 1, 2, 3}          # recaps and untyped documents are not read
    assert [u.doc_id for u in unit_list] == sorted(kind) and len(work) == sum(len(u.assets) for u in unit_list)
    for unit in unit_list:
        expected = {0: ["Asset_A", "Asset_B"], 3: [schema.FILED_ALIAS]}.get(kind[unit.doc_id], ["Asset_A"])
        assert unit.aliases == expected and unit.source == ("reddit" if kind[unit.doc_id] == 2 else "wayback")
        assert unit.type == ("analysis_opinion" if kind[unit.doc_id] == 1 else "event") and unit.doc_id in unit.summary


# ---------------------------------------------------------------- asset-week features
def _reading_row(doc_id, age, type_="event", base="AAA", read=True) -> dict:
    return {"friday": FRIDAY, "decision": DECISION, "doc_id": doc_id, "base": base, "event_ts": DECISION - age, "type": type_, "read": read}


def _record_row(doc_id, event_class="other", status="occurred", direction="neutral", materiality=1, relevance="subject",
                resolution="agreed", base="AAA") -> dict:
    if resolution == "unresolved":
        relevance = event_class = status = direction = materiality = None
    return {"doc_id": doc_id, "base": base, "resolution": resolution, "relevance": relevance, "event_class": event_class,
            "status": status, "direction": direction, "materiality": materiality}


def _block_b_case():
    reading_rows = [
        _reading_row("e1", DAY), _reading_row("e2", 2 * DAY), _reading_row("e3", 6 * DAY), _reading_row("e6", 3 * DAY),
        _reading_row("o1", 3 * DAY, "analysis_opinion"), _reading_row("e5", 7 * DAY), _reading_row("e4", 15 * DAY),
        _reading_row("o2", 10 * DAY, "analysis_opinion"), _reading_row("u1", DAY), _reading_row("s1", DAY), _reading_row("n1", DAY),
        _reading_row("x1", DAY, base="BBB"), _reading_row("z1", DAY, read=False)]
    records = [
        _record_row("e1", "security_incident", "occurred", "unfavourable", 2),
        _record_row("e2", "security_incident", "occurred", "unfavourable", 3),           # same event as e1: counted once at 3
        _record_row("e6", "security_incident", "occurred", "mixed", 1),                  # same class, another direction
        _record_row("e3", "governance_or_team", "occurred", "favourable", 1, resolution="adjudicated"),
        _record_row("o1", "opinion_or_forecast", "occurred", "favourable", 2),
        _record_row("e5", "token_supply_increase", "occurred", "unfavourable", 2),       # exactly 7 days old: days 8 to 30
        _record_row("e4", "protocol_upgrade_or_launch", "scheduled", "favourable", 2),
        _record_row("o2", "token_supply_reduction", "proposed_or_rumoured", "unfavourable", 1),
        _record_row("u1", resolution="unresolved"),
        _record_row("s1", "legal_regulatory", "occurred", "unfavourable", 3, relevance="side_mention"),
        _record_row("n1", relevance="not_about"),
        _record_row("x1", "exchange_listing", "occurred", "favourable", 3, base="BBB"),
        _record_row("z1", "exchange_delisting", "occurred", "unfavourable", 3),
        _record_row("unused", "exchange_delisting", "occurred", "unfavourable", 3)]      # not in any reading set
    return pd.DataFrame(reading_rows), consensus.record_frame([{**dict.fromkeys(consensus.RECORD_COLUMNS), **r} for r in records])


def test_block_b_sums_and_deduplication():
    sets, records = _block_b_case()
    out = features.block_b(sets, records).set_index(["date", "base"])
    assert set(out.columns) == set(features.BLOCK_B) | set(features.BLOCK_B_CLASS) | set(features.COUNTS)
    assert out.loc[(FRIDAY, "AAA")].to_dict() == {
        "tone_7d": -2.0,          # -3 (e1 and e2 once, at the higher materiality) + 1 (e3) + 0 (e6, mixed)
        "tone_30d": 0.0,          # -2 (e5) + 2 (e4)
        "unfav_7d": 3.0,
        "sched_fwd": 2.0,
        "stance_7d": 1.0,         # o1 only; o2 is older than 7 days
        "supply_30d": 1.0,        # +2 (increase, e5) - 1 (reduction, o2); events and opinions
        "tone_7d_c": -3.0,        # e1, e2 and e6 are one group by class; governance has sign 0
        "tone_30d_c": 0.0,
        "unfav_7d_c": 3.0,
        "sched_fwd_c": 2.0,
        "n_subject_7d": 5.0, "n_subject_30d": 8.0, "n_unresolved_30d": 1.0}
    other = out.loc[(FRIDAY, "BBB")]
    assert other["tone_7d"] == 3.0 and other["tone_7d_c"] == 3.0 and other["n_subject_7d"] == 1.0
    assert other.drop(["tone_7d", "tone_7d_c", "n_subject_7d", "n_subject_30d"]).eq(0.0).all()


def test_block_b_is_additive_over_event_groups():
    sets, records = _block_b_case()
    base = features.block_b(sets, records).set_index(["date", "base"]).loc[(FRIDAY, "AAA")]
    more = pd.concat([sets, pd.DataFrame([_reading_row("e7", 20 * DAY)])], ignore_index=True)
    extra = consensus.record_frame([{**dict.fromkeys(consensus.RECORD_COLUMNS), **_record_row("e7", "protocol_upgrade_or_launch", "scheduled", "favourable", 3)}])
    out = features.block_b(more, pd.concat([records, extra], ignore_index=True)).set_index(["date", "base"]).loc[(FRIDAY, "AAA")]
    # e7 repeats e4 (same class, status, direction and week bucket) at materiality 3: the group counts 3, not 2 + 3
    assert out["tone_30d"] == base["tone_30d"] + 1 and out["sched_fwd"] == base["sched_fwd"] + 1
    assert out["n_subject_30d"] == base["n_subject_30d"] + 1 and out["tone_7d"] == base["tone_7d"]


def _attention_items() -> pd.DataFrame:
    hour = pd.Timedelta(hours=1)
    return pd.DataFrame([
        _item("a1", "AAA", event_ts=DECISION, as_of_ts=DECISION),
        _item("a2", "AAA", event_ts=DECISION - DAY, type_=None),                           # untyped documents count
        _item("a3", "AAA", event_ts=DECISION - WEEK + hour, source="reddit", salience="mentioned"),
        _item("a3", "AAA", event_ts=DECISION - WEEK + hour, source="reddit", salience="mentioned"),   # one document, two rows
        _item("a4", "AAA", event_ts=DECISION - WEEK),                                      # exactly 7 days old: the week before
        _item("a5", "AAA", event_ts=DECISION - 2 * DAY, as_of_ts=DECISION + hour),         # seen after the decision
        _item("a6", "AAA", event_ts=DECISION - 9 * WEEK),                                  # older than the history
        _item("a7", "AAA", event_ts=DECISION - 9 * WEEK + hour),                           # oldest history week
        _item("a8", "ZZZ", event_ts=DECISION - DAY)])


def test_attention_counts_and_own_history():
    items = _attention_items()
    out = features.attention(items, [FRIDAY], ["BBB", "AAA", "AAA"], pd.Timestamp("2022-01-01", tz="UTC"))
    assert list(out.columns) == ["date", "base", "attn_7d", "attn_abn"] and list(out["base"]) == ["AAA", "BBB"]
    row = out.set_index("base").loc["AAA"]
    assert row["attn_7d"] == pytest.approx(math.log(4))                                    # a1, a2, a3
    assert row["attn_abn"] == pytest.approx(math.log(4) - 2 * math.log(2) / 8)             # a4 and a7 in two of eight weeks
    assert out.set_index("base").loc["BBB"].tolist()[1:] == [0.0, 0.0] and (out["date"] == FRIDAY).all()


def test_attention_history_must_lie_inside_the_store():
    items = _attention_items()
    short = features.attention(items, [FRIDAY], ["AAA"], DECISION - 4 * WEEK)              # three history weeks inside
    assert short["attn_7d"].iloc[0] == pytest.approx(math.log(4)) and math.isnan(short["attn_abn"].iloc[0])
    enough = features.attention(items, [FRIDAY], ["AAA"], DECISION - 5 * WEEK)             # four: the minimum
    assert enough["attn_abn"].iloc[0] == pytest.approx(math.log(4) - math.log(2) / 4)
    assert (features.ATTN_HISTORY, features.ATTN_MIN_HISTORY) == (8, 4)


def test_asset_week_features_fill_assets_without_records():
    sets, records = _block_b_case()
    top = pd.DataFrame({"date": [FRIDAY] * 3, "symbol": ["AAAUSDT", "BBBUSDT", "CCCUSDT"], "base": ["AAA", "BBB", "CCC"], "dvol_30d": 1.0})
    out = features.asset_week_features(_attention_items(), sets, records, top, DECISION - 4 * WEEK)
    assert list(out[["date", "symbol", "base"]].itertuples(index=False, name=None)) == [(FRIDAY, s, s[:3]) for s in top["symbol"]]
    assert set(out.columns) == {"date", "symbol", "base", *features.TEXT_FEATURES, *features.BLOCK_B_CLASS, *features.COUNTS}
    quiet = out.set_index("base").loc["CCC"]
    assert quiet[[*features.BLOCK_B, *features.BLOCK_B_CLASS, *features.COUNTS, "attn_7d"]].eq(0.0).all()
    assert out["attn_abn"].isna().all() and out.drop(columns="attn_abn").notna().all().all()
    assert out.set_index("base").loc["AAA", "tone_7d"] == -2.0


# ---------------------------------------------------------------- extraction script
SHAPE = {"weeks": 8, "n_syms": 8, "docs_per_week": 12}        # 64 units
UNITS = 64


def rebuild_offline(root: Path) -> dict:
    """The offline mode under the stand-in model name; the client is never called."""
    idle = FakeClient()
    try:
        return extract(root, "--offline", client=idle)
    finally:
        assert idle.attempts == 0


def agreeing(role, summary, aliases, retry):
    return [careful_record(summary, alias) for alias in aliases]


def test_pilot_sample_is_fixed_and_ordered():
    unit_list = [_unit(doc_id=f"d{i:03d}") for i in range(200)]
    first, second = rx.pilot_sample(unit_list, 30), rx.pilot_sample(unit_list, 30)
    assert first == second and len({u.doc_id for u in first}) == 30
    assert [u.doc_id for u in first] == sorted(u.doc_id for u in first)
    assert rx.pilot_sample(unit_list, 30, seed=1) != first and rx.pilot_sample(unit_list, 500) == unit_list


def test_pilot_runs_on_a_draft_and_writes_only_a_report(tmp_path):
    script_root(tmp_path, frozen=False, **SHAPE)
    client = FakeClient(agreeing)
    report = extract(tmp_path, "--pilot", "20", "--cost-cap", "1.0", "--workers", "4", client=client)
    assert (report["stage"], report["units"], report["model"], report["seed"]) == ("R1 pilot", 20, "fake/model", rx.PILOT_SEED)
    assert report["prompt_sha256"] == schema.prompt_sha256() and report["units_call_missing"] == []
    assert report["phase_1"]["stopped"] is None and report["phase_1"]["unfinished_units"] == 0
    assert client.calls == 40 == report["phase_1"]["new_calls"] == report["calls"]["calls"] == len(CallCache(tmp_path / rx.CACHE))
    assert report["calls"]["by_role"]["A"]["calls"] == report["calls"]["by_role"]["B"]["calls"] == 20 and "J" not in report["calls"]["by_role"]
    assert report["calls"]["providers"] == {"Fake": 40} and report["calls"]["latency_s"] == {"median": 0.5, "q90": 0.5}
    assert report["cost"]["work_list_units"] == UNITS and report["cost"]["per_unit_usd"] == pytest.approx(2 * COST)
    assert report["cost"]["projected_full_usd"] == pytest.approx(UNITS * 2 * COST) and report["cost"]["cache_paid_usd"] == pytest.approx(40 * COST)
    assert report["stop_rule"] == {"evidence_grounding": 1.0, "minimum_grounding": 0.95, "direction_agreement": 1.0,
                                   "minimum_direction_agreement": 0.70, "passed": True}
    assert report["quality"]["resolution"] == {"agreed": 1.0, "adjudicated": 0.0, "unresolved": 0.0}
    assert json.loads((tmp_path / rx.PILOT_REPORT).read_text()) == report
    assert len(pd.read_parquet(tmp_path / rx.PILOT_RECORDS)) == report["records"]
    assert not (tmp_path / rx.RECORDS).exists() and not (tmp_path / rx.MANIFEST).exists()
    # the same pilot again: every call is in the cache
    again = FakeClient(agreeing)
    second = extract(tmp_path, "--pilot", "20", "--cost-cap", "1.0", client=again)
    assert again.attempts == 0 and second["phase_1"]["new_calls"] == 0
    assert {k: second[k] for k in ("units", "records", "quality", "evidence_grounding", "calls", "stop_rule", "cost")} == \
           {k: report[k] for k in ("units", "records", "quality", "evidence_grounding", "calls", "stop_rule", "cost")}
    # a larger pilot pays only for the new units
    third = FakeClient(agreeing)
    extract(tmp_path, "--pilot", "30", "--cost-cap", "1.0", client=third)
    assert 0 < third.calls <= 2 * 30 - 2 * 0 and len(CallCache(tmp_path / rx.CACHE)) == 40 + third.calls


def test_pilot_stop_rule_fails_on_ungrounded_evidence(tmp_path):
    script_root(tmp_path, frozen=False, **SHAPE)

    def careless(role, summary, aliases, retry):
        records = agreeing(role, summary, aliases, retry)
        if role == "A" and not retry and hashed(summary) % 3 == 0:
            records = [{**r, "relevance": "subject", "evidence": "a phrase the text does not contain"} for r in records]
        return records

    client = FakeClient(careless)
    report = extract(tmp_path, "--pilot", "40", "--cost-cap", "1.0", "--workers", "4", client=client)
    first, again = report["readings"]["first_read"]["A"], report["readings"]["reread"]["A"]
    assert first["evidence"] > 0 and again["ok"] == first["evidence"] and again["evidence"] == 0      # one re-read repairs them
    assert report["quality"]["resolution"]["unresolved"] == 0.0 and report["quality"]["valid_reading_a"] == 1.0
    grounded = report["evidence_grounding"]
    assert grounded["B"] == 1.0 and grounded["A"] < 0.95 and grounded["A"] < grounded["readers"] < 1.0
    assert report["stop_rule"]["evidence_grounding"] == grounded["readers"]
    assert report["stop_rule"]["passed"] is (grounded["readers"] >= 0.95) and grounded["readers"] < 0.95


def test_pilot_stop_rule_fails_on_direction_disagreement(tmp_path):
    script_root(tmp_path, frozen=False, **SHAPE)

    def contrary(role, summary, aliases, retry):
        records = agreeing(role, summary, aliases, retry)
        if role == "B":
            records = [{**r, "direction": "mixed" if r["direction"] != "mixed" else "neutral"} for r in records]
        return records

    report = extract(tmp_path, "--pilot", "20", "--cost-cap", "1.0", client=FakeClient(contrary))
    assert report["stop_rule"]["evidence_grounding"] == 1.0 and report["stop_rule"]["direction_agreement"] == 0.0
    assert report["stop_rule"]["passed"] is False and report["quality"]["resolution"]["adjudicated"] > 0.5
    assert report["calls"]["by_role"]["J"]["calls"] > 0


def test_full_extraction_refuses_a_draft_charter(tmp_path):
    script_root(tmp_path, frozen=False, weeks=4, n_syms=6, docs_per_week=6)
    client = FakeClient()
    with pytest.raises(SystemExit, match="draft"):
        extract(tmp_path, "--cost-cap", "1.0", client=client)
    with pytest.raises(SystemExit, match="draft"):
        extract(tmp_path, "--offline")
    assert client.attempts == 0 and not (tmp_path / rx.CACHE).exists() and not (tmp_path / rx.RECORDS).exists()


def test_full_extraction_resumes_and_writes_records_and_manifest(tmp_path, capsys):
    frames = script_root(tmp_path, **SHAPE)
    work, unit_list = rx.build_units(*frames)
    flaky = FakeClient(fail=lambda role, summary, aliases, retry: role == "B" and hashed(summary) % 5 == 0)
    with pytest.raises(SystemExit, match="extraction incomplete"):
        extract(tmp_path, "--cost-cap", "1.0", "--workers", "4", client=flaky)
    assert not (tmp_path / rx.RECORDS).exists() and not (tmp_path / rx.MANIFEST).exists()
    assert flaky.attempts > flaky.calls > 0 and flaky.calls == len(CallCache(tmp_path / rx.CACHE))

    client = FakeClient()
    manifest = extract(tmp_path, "--cost-cap", "1.0", "--workers", "4", client=client)
    cache = CallCache(tmp_path / rx.CACHE)
    assert client.calls > 0 and flaky.calls + client.calls == len(cache) == manifest["cache"]["calls"] == manifest["calls"]["calls"]
    assert manifest["cache"] == {"path": rx.CACHE, "sha256": sha(tmp_path / rx.CACHE), "calls": len(cache), "paid_usd": cache.paid_usd}
    assert cache.paid_usd == pytest.approx(len(cache) * COST) and manifest["calls"]["cost_usd"] == pytest.approx(len(cache) * COST)
    assert manifest["charter"] == {"path": "charter.md", "sha256": sha(tmp_path / "charter.md")}
    assert manifest["prompt_sha256"] == schema.prompt_sha256()
    assert manifest["model"] == {"id": "fake/model", "providers": list(rx.PINS[rx.PIN][1]), "quantization": rx.PINS[rx.PIN][2],
                                 "reasoning": "disabled", "temperature": 0, "max_tokens": rx.MAX_TOKENS}
    assert manifest["universe"] == {"n": c2.UNIVERSE_N, "start": c2.PANEL_START, "end": c2.PANEL_END}
    assert manifest["inputs"] == {name: {"path": path, "sha256": sha(tmp_path / path)} for name, path in rx.INPUTS.items()}
    assert manifest["records_file"] == {"path": rx.RECORDS, "sha256": sha(tmp_path / rx.RECORDS)}
    assert manifest["source_files"] == {path: sha(ROOT / path) for path in rx.SOURCES}
    assert manifest["head"] == git(tmp_path, "rev-parse", "HEAD")
    assert (manifest["units"], manifest["records"], manifest["units_call_missing"]) == (UNITS, len(work), [])
    assert manifest["quality"]["resolution"]["unresolved"] == 0.0 and 0.0 < manifest["quality"]["resolution"]["adjudicated"] < 1.0
    assert manifest["evidence_grounding"]["readers"] == 1.0
    assert json.loads((tmp_path / rx.MANIFEST).read_text()) == manifest
    records = pd.read_parquet(tmp_path / rx.RECORDS)
    assert list(records.columns) == consensus.RECORD_COLUMNS
    by_asset = records.sort_values(["doc_id", "base"])                          # one row per work-list entry
    assert by_asset[["doc_id", "base", "focus_only"]].reset_index(drop=True).equals(work[["doc_id", "base", "focus_only"]])
    order = list(records[["doc_id", "alias"]].itertuples(index=False, name=None))
    assert order == sorted(order)                                                # document order, assets in alias order

    # no call: the cache alone reproduces the stored table
    offline = rebuild_offline(tmp_path)
    assert offline["equal"] is True and offline["records"] == len(work) and offline["calls"] == manifest["calls"]
    # another online run finds every call in the cache
    idle = FakeClient()
    repeat = extract(tmp_path, "--cost-cap", "1.0", client=idle)
    assert idle.attempts == 0 and repeat["cache"] == manifest["cache"] and repeat["quality"] == manifest["quality"]
    assert consensus.same_records(pd.read_parquet(tmp_path / rx.RECORDS), records)
    # without the stored table the offline mode writes it from the cache
    (tmp_path / rx.RECORDS).unlink()
    rebuilt = rebuild_offline(tmp_path)
    assert rebuilt["cache"] == manifest["cache"] and consensus.same_records(pd.read_parquet(tmp_path / rx.RECORDS), records)
    # a cache that lost a call no longer reproduces it
    lines = (tmp_path / rx.CACHE).read_text().splitlines(keepends=True)
    (tmp_path / rx.CACHE).write_text("".join(lines[1:]))
    with pytest.raises(SystemExit, match="differs from the stored records"):
        rebuild_offline(tmp_path)
    capsys.readouterr()


def test_spend_limit_stops_the_extraction(tmp_path):
    script_root(tmp_path, **SHAPE)
    capped = FakeClient(cap_calls=30)
    with pytest.raises(SystemExit, match="extraction incomplete"):
        extract(tmp_path, "--cost-cap", "1.0", "--workers", "2", client=capped)
    assert capped.calls == 30 == len(CallCache(tmp_path / rx.CACHE)) and not (tmp_path / rx.RECORDS).exists()
    untouched = FakeClient()
    with pytest.raises(SystemExit, match="spend limit reached"):
        extract(tmp_path, "--cost-cap", str(10 * COST), client=untouched)          # the cache already cost more than the limit
    with pytest.raises(SystemExit, match="--cost-cap is required"):
        extract(tmp_path, client=untouched)
    assert untouched.attempts == 0 and len(CallCache(tmp_path / rx.CACHE)) == 30


def test_accepted_missing_units_are_written_as_unresolved(tmp_path):
    frames = script_root(tmp_path, **SHAPE)
    _, unit_list = rx.build_units(*frames)
    lost = unit_list[3]

    def broken():
        return FakeClient(fail=lambda role, summary, aliases, retry: role == "B" and summary == lost.summary)

    with pytest.raises(SystemExit, match="extraction incomplete"):
        extract(tmp_path, "--cost-cap", "1.0", client=broken())
    assert not (tmp_path / rx.RECORDS).exists()
    manifest = extract(tmp_path, "--cost-cap", "1.0", "--accept-missing", "1", client=broken())
    assert manifest["units_call_missing"] == [lost.doc_id] and manifest["units"] == UNITS
    records = pd.read_parquet(tmp_path / rx.RECORDS)
    mine = records["doc_id"] == lost.doc_id
    assert mine.sum() == len(lost.assets) and set(records.loc[mine, "resolution"]) == {"unresolved"}
    assert records.loc[mine, list(schema.FIELDS)].isna().all().all()
    assert set(records.loc[~mine, "resolution"]) == {"agreed", "adjudicated"}
    assert manifest["quality"]["resolution"]["unresolved"] == pytest.approx(len(lost.assets) / len(records))
    assert rebuild_offline(tmp_path)["equal"] is True


def test_fill_stops_after_consecutive_failures_or_at_the_spend_limit(tmp_path):
    items, docs, cards = store_frames(weeks=16, n_syms=8, docs_per_week=12)
    _, unit_list = rx.build_units(items, docs, cards)
    assert len(unit_list) > 2 * rx.MAX_CONSECUTIVE_FAILURES
    quiet = {"log": lambda line: None}
    dead = FakeClient(fail=lambda *a: True)
    out = rx.fill(Reader(dead, CallCache(tmp_path / "dead.jsonl")), unit_list, workers=1, **quiet)
    assert out["stopped"] == "consecutive_failures" and dead.attempts == rx.MAX_CONSECUTIVE_FAILURES and dead.calls == 0
    assert out["unfinished_units"] == len(unit_list) and out["new_calls"] == 0 and out["new_cost_usd"] == 0.0
    # failures between successes do not add up
    half = FakeClient(fail=lambda role, summary, aliases, retry: hashed(summary) % 2 == 0)
    out = rx.fill(Reader(half, CallCache(tmp_path / "half.jsonl")), unit_list, workers=1, passes=1, **quiet)
    failing = sum(hashed(u.summary) % 2 == 0 for u in unit_list)
    assert out["stopped"] is None and out["unfinished_units"] == failing and 0 < failing < len(unit_list)
    # the spend limit
    capped = FakeClient(cap_calls=25)
    out = rx.fill(Reader(capped, CallCache(tmp_path / "capped.jsonl")), unit_list, workers=1, **quiet)
    assert out["stopped"] == "spend_cap" and out["new_calls"] == 25 and out["new_cost_usd"] == pytest.approx(25 * COST)
    assert out["unfinished_units"] > 0 and capped.attempts == 26                   # one refused call, then nothing


def test_grounding_shares():
    stats = Reader(None, CallCache.from_bytes(b""), model="any/model").stats
    assert rx.grounding(stats) == {"A": None, "B": None, "J": None, "readers": None}
    stats["grounding"]["A"].update(needed=8, found=6)
    stats["grounding"]["B"].update(needed=2, found=2)
    stats["grounding"]["J"].update(needed=4, found=1)
    assert rx.grounding(stats) == {"A": 0.75, "B": 1.0, "J": 0.25, "readers": 0.8}
