"""Direct comparison of assets on text (Charter 5): news archive rows, typing scope, text dossiers, pairwise
comparison with consensus, comparison score, the gate statistic and the drivers.

Synthetic fixtures only; no market data, no network. The fixtures of the extraction side are shared with
``test_reader_extract.py``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import threading

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts import cmp_common, cmp_dossiers, cmp_duels, cmp_probe, cmp_read  # noqa: E402
from test_reader_extract import COST, DAY, DECISION, FRIDAY, FakeClient, _doc, _item, _record_row, store_frames  # noqa: E402
from tradingagents.agents_v2.evaluate import CONTROLS  # noqa: E402
from tradingagents.compare import archive, charter5 as c5, dossier, duel, scope  # noqa: E402
from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.anonymizer import Masker  # noqa: E402
from tradingagents.dossier.builder import CANONICAL_SEED  # noqa: E402
from tradingagents.dossier.entities import Dictionary, Linker  # noqa: E402
from tradingagents.dossier.or_client import ORError, SpendCapError  # noqa: E402
from tradingagents.reader import charter2 as c2, items as reader_items  # noqa: E402
from tradingagents.reader.extract import CallCache, CallFailed, call_key  # noqa: E402

HOUR, MINUTE = pd.Timedelta(hours=1), pd.Timedelta(minutes=1)
DICTIONARY = Dictionary(assets={"AAA": ["Alphacoin", "AAA"], "BBB": ["Betacoin", "BBB"], "CCC": ["Gammacoin", "CCC"]})


# ---------------------------------------------------------------- archive rows
def test_feed_times_are_iran_local_time():
    got = archive.to_utc(pd.Series(["2023-01-10 12:00:00", "2022-07-01 12:00:00", "not a time", None]))
    assert got[0] == pd.Timestamp("2023-01-10 08:30", tz="UTC")          # +03:30
    assert got[1] == pd.Timestamp("2022-07-01 07:30", tz="UTC")          # +04:30, daylight time until 2022
    assert got[2:].isna().all()


def test_clean_resolves_entities_and_cuts_the_feed_boilerplate():
    assert archive.clean("Alpha &amp; Beta   rise.\n The post Alpha &amp; Beta rise appeared first on Outlet .") == "Alpha & Beta rise."
    assert archive.clean("The post office reopened.") == "The post office reopened."
    assert archive.clean(None) == "" and archive.clean(float("nan")) == "" and archive.clean("  a\tb ") == "a b"


def _feed(t0: pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """Sixty live articles one minute apart, one article of an old date ingested after them, one more live article."""
    times = [t0 + i * MINUTE for i in range(60)] + [t0 - 30 * DAY, t0 + 61 * MINUTE]
    return pd.Series(times), pd.Series(range(1, 63))


def test_availability_live_articles_and_a_backfilled_one():
    t0 = pd.Timestamp("2023-02-01 10:00", tz="UTC")
    event_ts, feed_id = _feed(t0)
    seen = archive.availability(event_ts, feed_id)
    assert (seen[:60] == event_ts[:60] + HOUR).all()                     # live, also while the clock is still missing
    clock = t0 + pd.Timedelta(minutes=34.5)                              # median of the 50 articles before the late one
    assert seen[60] == clock + archive.LATE_MARGIN                       # not observable at its old publication time
    assert seen[61] == event_ts[61] + HOUR                               # the feed is live again
    assert archive.feed_clock(event_ts, feed_id)[:archive.AVAIL_MIN_HISTORY].isna().all()
    assert archive.feed_clock(event_ts, feed_id).dropna().is_monotonic_increasing


def test_availability_follows_the_feed_order_not_the_row_order():
    event_ts, feed_id = _feed(pd.Timestamp("2023-02-01 10:00", tz="UTC"))
    order = np.random.default_rng(0).permutation(len(event_ts))
    shuffled = archive.availability(event_ts.iloc[order], feed_id.iloc[order])
    assert shuffled.sort_index().equals(archive.availability(event_ts, feed_id))


def _raw(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=archive.RAW_COLUMNS)


def test_store_rows_exclusions_and_counts():
    raw = _raw([
        (1, "2023-03-01 12:00:00", "Alphacoin &amp; partners", "A body. The post Alphacoin appeared first on Outlet.", "u/1", "ALT|NEWS", "newoutlet"),
        (2, "2023-03-01 12:05:00", "Kept elsewhere", "Body", "u/2", "BTC", "coindesk"),          # outlet of the present store
        (3, "2023-03-01 12:10:00", "Alphacoin again", "Body", "u/1", "ALT", "newoutlet"),        # same address as feed id 1
        (4, "2023-03-01 12:15:00", " ", None, "u/4", None, "newoutlet"),                         # nothing to read
        (5, "never", "No time", "Body", "u/5", None, "newoutlet"),
        (6, "2021-06-01 12:00:00", "Before the window", "Body", "u/6", None, "newoutlet")])
    rows, counts = archive.store_rows(raw)
    assert counts == {"rows": 6, "no_time": 1, "in_window": 4, "present_outlets": 1, "duplicate_url": 1, "empty": 1,
                      "stored": 1, "late": 0}
    row = rows.iloc[0]
    assert list(rows.columns) == store.COLUMNS and len(rows) == 1
    assert row["doc_id"] == store.doc_id(archive.SOURCE, "1") and (row["source"], row["outlet"]) == ("ccnews", "newoutlet")
    assert (row["title"], row["body"], row["url"]) == ("Alphacoin & partners", "A body.", "u/1")
    assert row["event_ts"] == pd.Timestamp("2023-03-01 08:30", tz="UTC") and row["as_of_ts"] == row["event_ts"] + HOUR
    assert json.loads(row["extra"]) == {"categories": "ALT|NEWS", "feed_id": 1}
    with pytest.raises(ValueError, match="missing columns"):
        archive.store_rows(raw.drop(columns="source"))


def test_store_rows_marks_a_backfilled_article_late():
    t0 = pd.Timestamp("2023-03-01 12:00:00")
    live = [(i + 1, str(t0 + i * MINUTE), f"Title {i}", "Body", f"u/{i}", None, "newoutlet") for i in range(60)]
    rows, counts = archive.store_rows(_raw(live + [(61, "2023-01-15 09:00:00", "Old article", "Body", "u/old", None, "newoutlet")]))
    assert (counts["stored"], counts["late"]) == (61, 1)
    old = rows[rows["doc_id"] == store.doc_id(archive.SOURCE, "61")].iloc[0]
    assert old["event_ts"] == pd.Timestamp("2023-01-15 05:30", tz="UTC")
    assert old["as_of_ts"] > pd.Timestamp("2023-03-02", tz="UTC")                # observable a day after the feed clock


# ---------------------------------------------------------------- typing scope and pilot weeks
def _top(bases_by_week: dict) -> pd.DataFrame:
    rows = [(friday, f"{b}USDT", b) for friday, bases in bases_by_week.items() for b in bases]
    return pd.DataFrame(rows, columns=["date", "symbol", "base"])


def test_typing_scope_rule():
    nxt = FRIDAY + 7 * DAY
    top = _top({FRIDAY: ["AAA", "BBB", "BTC"], nxt: ["BBB"]})
    items = pd.DataFrame([
        _item("in", "AAA"),
        _item("btc", "BTC"),                                               # main subject BTC: left out
        _item("mention", "AAA", salience="mentioned"),
        _item("old", "AAA", event_ts=DECISION - 8 * DAY),
        _item("late", "AAA", as_of_ts=DECISION + HOUR),                     # not observable at the decision
        _item("outside", "ZZZ"),                                           # not in the universe of the week
        _item("both", "BBB"), _item("both", "AAA"),                        # two primary links, one document
        _item("next", "BBB", event_ts=DECISION + 3 * DAY),
        _item("gone", "AAA", event_ts=DECISION + 3 * DAY)])                # AAA left the universe the week after
    got = scope.typing_scope(items, top)
    assert list(got["doc_id"]) == ["both", "in", "next"] and list(got.columns) == ["doc_id", "event_ts"]
    assert list(scope.typing_scope(items, top, [FRIDAY])["doc_id"]) == ["both", "in"]
    assert list(scope.typing_scope(items.iloc[::-1], top)["doc_id"]) == ["both", "in", "next"]


def test_typing_text_is_the_text_the_link_table_looks_up():
    title, body = "Alphacoin lists a new pair", "Alphacoin said on 3 March 2023 that Betacoin holders can move funds. " * 3
    ts = pd.Timestamp("2023-03-05 10:00", tz="UTC")
    masked = scope.typing_text(title, body, ts, DICTIONARY)
    assert "Alphacoin" not in masked and "Betacoin" not in masked and "2023" not in masked and "Asset_" in masked
    assert masked == scope.typing_text(title, body, ts, DICTIONARY)
    assert masked == Masker(DICTIONARY, ts, CANONICAL_SEED).mask_text(f"{title}\n{body}".strip())
    assert scope.typing_text("Alphacoin", "short", ts, DICTIONARY) is None and scope.typing_text(None, None, ts, DICTIONARY) is None
    # the rebuilt link table finds a typing stored under the key of that text
    typed = {"type": "event", "novelty": "new", "summary": "Asset_A lists a new pair.", "affected_aliases": []}
    rows = pd.DataFrame([("d1", ts, ts + HOUR, "ccnews", "newoutlet", title, body)],
                        columns=["doc_id", "event_ts", "as_of_ts", "source", "outlet", "title", "body"])
    cache = {reader_items.typing_key(masked): typed}
    linked, docs = reader_items.month_rows(rows, DICTIONARY, Linker(DICTIONARY), cache)
    assert list(docs["doc_id"]) == ["d1"] and linked["typed"].all() and set(linked["base"]) == {"AAA", "BBB"}


def test_pilot_weeks_are_a_fixed_seeded_draw():
    fridays = list(pd.date_range("2023-01-06", periods=104, freq="7D", tz="UTC"))
    got = scope.pilot_weeks(fridays)
    assert [str(d.date()) for d in got] == ["2023-01-27", "2023-09-29", "2024-03-01"]
    assert got == scope.pilot_weeks(fridays[::-1]) and got == sorted(got)
    assert scope.pilot_weeks(fridays, seed=1) != got and len(scope.pilot_weeks(fridays, n=5)) == 5


# ---------------------------------------------------------------- text dossiers
LISTING = dict(event_class="exchange_listing", status="occurred", direction="favourable")


def _world():
    """One week, three universe assets. AAA has two reports of one matter, one report of another matter, a side
    mention, a report whose summary still carries a name, an unresolved report and a report without a record;
    BBB has one community post; the report on CCC is older than the window."""
    top = _top({FRIDAY: ["AAA", "BBB", "CCC"]})
    both = {"Asset_A": "asset:AAA", "Asset_B": "asset:BBB", "Exchange_1": "exchange:binance"}
    own = {"Asset_A": "asset:AAA"}
    items = pd.DataFrame([
        _item("d1", "AAA", event_ts=DECISION - 2 * HOUR), _item("d2", "AAA", event_ts=DECISION - 2 * DAY, source="ccnews"),
        _item("d3", "AAA", event_ts=DECISION - 3 * DAY), _item("d4", "AAA"), _item("d5", "AAA"), _item("d7", "AAA"),
        _item("d8", "AAA"), _item("d6", "BBB", source="reddit", event_ts=DECISION, as_of_ts=DECISION),
        _item("d9", "CCC", event_ts=DECISION - 8 * DAY)])
    docs = pd.DataFrame([
        dict(_doc("d1", both), summary="Asset_A was listed on Exchange_1 ahead of Asset_B."),
        dict(_doc("d2", own), summary="Asset_A is to be listed, a venue said."),
        dict(_doc("d3", own), summary="Asset_A lost funds in an exploit."),
        _doc("d4", own), dict(_doc("d5", own), leaky=True), _doc("d7", own), _doc("d8", own),
        dict(_doc("d6", {"Asset_A": "asset:BBB"}), summary="Holders of Asset_A report an outage."),
        _doc("d9", {"Asset_A": "asset:CCC"})])
    records = pd.DataFrame([
        _record_row("d1", materiality=2, **LISTING), _record_row("d2", materiality=2, **LISTING),
        _record_row("d3", event_class="other", direction="unfavourable", materiality=3),
        _record_row("d4", relevance="side_mention"), _record_row("d5", materiality=3, **LISTING),
        _record_row("d7", resolution="unresolved"), _record_row("d6", base="BBB", direction="unfavourable"),
        _record_row("d9", base="CCC")])
    return top, items, docs, records


def _lines():
    top, items, docs, records = _world()
    cands, counts = dossier.candidates(dossier.weekly_sets(items, docs, top), records, docs)
    return dossier.line_table(cands), cands, counts, docs


def test_week_seed_is_fixed_per_week():
    assert dossier.week_seed(FRIDAY) == dossier.week_seed(pd.Timestamp("2023-03-10")) != dossier.week_seed(FRIDAY + 7 * DAY)


def test_weekly_sets_and_work_rows():
    top, items, docs, _ = _world()
    sets = dossier.weekly_sets(items, docs, top)
    assert set(sets["doc_id"]) == {"d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8"}            # d9 is older than seven days
    assert (sets["friday"] == FRIDAY).all() and (sets["decision"] == DECISION).all()
    work = dossier.work_rows(sets)
    assert list(work["doc_id"]) == sorted(set(sets["doc_id"])) and list(work.columns) == ["doc_id", "base", "focus_only"]
    assert dossier.weekly_sets(items, docs, _top({FRIDAY: ["AAA"], FRIDAY + 7 * DAY: ["CCC"]}), [FRIDAY])["base"].eq("AAA").all()


def test_candidates_keep_subject_rows_of_clean_documents():
    lines, cands, counts, docs = _lines()
    assert counts == {"read_rows": 8, "without_record": 1, "unresolved": 1, "subject_rows": 5, "leaky_rows": 1}
    assert sorted(cands["doc_id"]) == ["d1", "d2", "d3", "d6"]
    top, items, _, records = _world()
    with pytest.raises(ValueError, match="duplicate"):
        dossier.candidates(dossier.weekly_sets(items, docs, top), pd.concat([records, records.iloc[:1]]), docs)


def test_line_table_groups_reports_of_one_matter():
    lines, cands, _, _ = _lines()
    assert list(lines.columns) == dossier.LINE_COLUMNS
    got = [(r.base, r.rank, r.doc_id, r.n_reports) for r in lines.itertuples()]
    assert got == [("AAA", 1, "d3", 1), ("AAA", 2, "d1", 2), ("BBB", 1, "d6", 1)]   # most material first; lead = most recent
    assert list(dossier.line_table(cands, max_lines=1)["doc_id"]) == ["d3", "d6"]
    assert dossier.line_table(cands.sample(frac=1.0, random_state=1)).equals(lines)
    assert dossier.line_table(cands.iloc[:0]).empty and list(dossier.line_table(cands.iloc[:0]).columns) == dossier.LINE_COLUMNS


def test_dossier_text_and_the_shared_alias_space():
    lines, _, _, docs = _lines()
    built = dossier.build(lines, docs, DICTIONARY)
    assert list(built.columns) == dossier.DOSSIER_COLUMNS and list(built["base"]) == ["AAA", "BBB"]
    a, b = built.iloc[0], built.iloc[1]
    assert re.fullmatch(r"Asset_[A-Z]", a["alias"]) and re.fullmatch(r"Asset_[A-Z]", b["alias"]) and a["alias"] != b["alias"]
    assert a["text"] == (f"- [3 days ago; news] {a['alias']} lost funds in an exploit.\n"
                         f"- [1 day ago; news; 2 reports] {a['alias']} was listed on Exchange_1 ahead of {b['alias']}.")
    assert b["text"] == f"- [today; community post] Holders of {b['alias']} report an outage."
    assert (a["n_lines"], a["n_reports"], a["leaks"]) == (2, 3, 0) and (b["n_lines"], b["n_reports"], b["leaks"]) == (1, 1, 0)
    assert a["sha256"] == hashlib.sha256(f"{a['alias']}\n{a['text']}".encode()).hexdigest()
    assert dossier.build(lines.sample(frac=1.0, random_state=2), docs, DICTIONARY).equals(built)
    assert dossier.build(lines.iloc[:0], docs, DICTIONARY).empty
    # no class, direction or materiality of the reader is shown
    for word in ("exchange_listing", "favourable", "unfavourable", "materiality"):
        assert word not in a["text"] + b["text"]


def test_alias_letters_change_with_the_week():
    lines, _, _, docs = _lines()
    letters = set()
    for k in range(8):
        week = lines.assign(friday=FRIDAY + 7 * k * DAY)
        letters.add(tuple(dossier.build(week, docs, DICTIONARY)["alias"]))
    assert len(letters) > 1


def test_driver_drops_a_dossier_that_still_carries_a_name():
    top, items, docs, records = _world()
    docs.loc[docs["doc_id"] == "d6", "summary"] = "Holders of Betacoin report an outage."      # a name the typing left in
    lines, dossiers, report = cmp_dossiers.build(items, docs, records, top, [FRIDAY], DICTIONARY)
    assert list(dossiers["base"]) == ["AAA"] and set(lines["base"]) == {"AAA"}
    assert report["dossiers_dropped_for_a_name"] == 1 and report["dossiers"] == 1 and report["lines"] == 2
    assert report["universe_rows"] == 3 and report["dossier_share"] == pytest.approx(1 / 3) and report["weeks_below_minimum"] == 1
    assert report["lead_report_source"] == {"wayback": 2} and report["dossiers_with_an_archive_line"] == 0
    assert report["read_rows"] == 8 and report["dossiers_per_week"] == {"min": 1, "median": 1.0, "max": 1}
    clean = cmp_dossiers.build(*_world()[1:], _world()[0], [FRIDAY], DICTIONARY)[2]
    assert clean["dossiers"] == 2 and clean["dossiers_dropped_for_a_name"] == 0


# ---------------------------------------------------------------- comparison: schedule
@pytest.mark.parametrize("n", [2, 3, 4, 9, 13, 26, 31])
def test_schedule_is_a_partial_round_robin(n):
    syms = [f"S{i:02d}" for i in range(n)]
    pairs = duel.schedule(syms, seed=7)
    rounds = min(duel.K_ROUNDS, n - 1 if n % 2 == 0 else n)
    assert len(set(pairs)) == len(pairs) == rounds * (n // 2)                     # no pair twice
    assert all(a < b and a in syms and b in syms for a, b in pairs)
    met = pd.Series([s for pair in pairs for s in pair]).value_counts()
    if n % 2 == 0:
        assert set(met) == {rounds} and len(met) == n
    else:
        assert set(met) <= {rounds - 1, rounds} and len(met) == n               # one asset rests in every round
    assert duel.schedule(syms[::-1], seed=7) == pairs
    if n > 4:
        assert duel.schedule(syms, seed=8) != pairs


def test_schedule_edge_cases():
    assert duel.schedule(["A"], seed=1) == [] and duel.schedule([], seed=1) == []
    assert len(duel.schedule([f"S{i}" for i in range(6)], seed=1, k=2)) == 6
    assert len(duel.schedule([f"S{i}" for i in range(6)], seed=1, k=50)) == 15  # the full round-robin at most


def _week_dossiers(n: int, friday=FRIDAY) -> pd.DataFrame:
    rows = [(friday, f"S{i:02d}", f"Asset_{chr(65 + i)}", f"- [1 day ago; news] Asset_{chr(65 + i)} report {i} of {friday:%Y-%m-%d}.")
            for i in range(n)]
    return pd.DataFrame(rows, columns=["friday", "base", "alias", "text"])


def test_week_duels_fix_the_orders():
    dossiers = _week_dossiers(12)
    duels = duel.week_duels(FRIDAY, dossiers)
    assert [(d["a"], d["b"]) for d in duels] == duel.schedule(list(dossiers["base"]), dossier.week_seed(FRIDAY))
    for d in duels:
        assert set(d["shown"]) == set(d["judge"]) == {d["a"], d["b"]} == set(d["dossier"])
        for base in (d["a"], d["b"]):
            row = dossiers[dossiers["base"] == base].iloc[0]
            assert d["dossier"][base] == (row["alias"], row["text"])
    assert len({d["shown"] == (d["a"], d["b"]) for d in duels}) == 2 and len({d["judge"] == d["shown"] for d in duels}) == 2
    again = duel.week_duels(FRIDAY, dossiers.iloc[::-1])
    assert [(d["shown"], d["judge"]) for d in again] == [(d["shown"], d["judge"]) for d in duels]
    other = duel.week_duels(FRIDAY + 7 * DAY, dossiers)
    assert [(d["a"], d["b"]) for d in other] != [(d["a"], d["b"]) for d in duels]


# ---------------------------------------------------------------- comparison: stand-in client
class DuelClient:
    """Stand-in comparison client. ``answer(role, first, second, prompt)`` gives the parsed answer, where
    ``first`` and ``second`` are the asset tokens of the prompt; ``fail`` with the same arguments makes the call
    raise ``ORError``; after ``cap_calls`` answered calls every call raises ``SpendCapError``."""
    model = "fake/duel"

    def __init__(self, answer, fail=None, cap_calls=None, cost=COST):
        self.answer, self.fail, self.cap_calls, self.cost = answer, fail, cap_calls, cost
        self.calls, self.attempts, self.log = 0, 0, []
        self._lock = threading.Lock()

    def call(self, prompt, schema_, schema_name="answer", system=None, max_tokens=None):
        role = "J" if duel.ADJUDICATOR in system else "B" if duel.REVIEWER in system else "A"
        first = re.search(r"^FIRST asset: (\S+)$", prompt, flags=re.M).group(1)
        second = re.search(r"^SECOND asset: (\S+)$", prompt, flags=re.M).group(1)
        with self._lock:
            self.attempts += 1
            if self.cap_calls is not None and self.calls >= self.cap_calls:
                raise SpendCapError("spend cap reached")
            if self.fail is not None and self.fail(role, first, second, prompt):
                raise ORError("provider unavailable")
            self.calls += 1
            self.log.append((role, first, second, prompt, schema_, schema_name, max_tokens))
        return (self.answer(role, first, second, prompt),
                {"provider": "Fake", "cost": self.cost, "prompt_tokens": 300, "completion_tokens": 20, "latency_s": 0.5})


def naming(**by_role):
    """An answer function: every role names the given token (or ``no_basis``); any other value is returned as it is."""
    def answer(role, first, second, prompt):
        want = by_role[role]
        if not isinstance(want, str):
            return want
        choice = duel.NO_BASIS if want == duel.NO_BASIS else {first: "first", second: "second"}[want]
        return {"choice": choice, "reason": f"{role} points to the report on {want}"}
    return answer


def by_strength(role, first, second, prompt):
    """Analysts prefer the later letter; the reviewer has no basis in a third of the comparisons and names the
    other asset in a tenth; the adjudicator follows the letter and has no basis in a quarter."""
    h = hashed_pair(first, second)
    if role == "B" and h % 3 == 0:
        return {"choice": duel.NO_BASIS, "reason": "routine items only"}
    if role == "J" and h % 4 == 0:
        return {"choice": duel.NO_BASIS, "reason": "nothing to weigh"}
    better = "first" if first > second else "second"
    if role == "B" and h % 10 == 1:
        better = "second" if better == "first" else "first"
    return {"choice": better, "reason": f"{role} reads a concrete fact"}


def hashed_pair(first: str, second: str) -> int:
    return int(hashlib.sha256("|".join(sorted((first, second))).encode()).hexdigest()[:8], 16)


Q, R = ("Asset_Q", "- [1 day ago; news] Asset_Q was listed."), ("Asset_R", "- [2 days ago; news] Asset_R lost funds.")


def _duel(shown=("AAA", "BBB"), judge=("BBB", "AAA"), friday=FRIDAY) -> dict:
    return {"friday": friday, "a": "AAA", "b": "BBB", "shown": shown, "judge": judge, "dossier": {"AAA": Q, "BBB": R}}


def _resolve(tmp_path, answer, **kwargs):
    client = DuelClient(answer)
    judge = duel.Judge(client, CallCache(tmp_path / "calls.jsonl"))
    return duel.resolve(judge, _duel(**kwargs)), client, judge


# ---------------------------------------------------------------- comparison: prompts and consensus
def test_system_prompts_and_prompt_identity(monkeypatch):
    assert duel.system_prompt("A") == duel.INSTRUCTION
    assert duel.system_prompt("B") == duel.INSTRUCTION + "\n\n" + duel.REVIEWER
    assert duel.system_prompt("J") == duel.INSTRUCTION + "\n\n" + duel.ADJUDICATOR
    with pytest.raises(ValueError):
        duel.system_prompt("C")
    for word in duel.CHOICES:
        assert word in duel.INSTRUCTION
    assert duel.SCHEMA["properties"]["choice"]["enum"] == list(duel.CHOICES) and duel.SCHEMA["required"] == ["choice", "reason"]
    before = duel.prompt_sha256()
    monkeypatch.setattr(duel, "REVIEWER", duel.REVIEWER + " Be strict.")
    assert duel.prompt_sha256() != before


def test_prompt_layout():
    text = duel.duel_prompt(Q, R)
    assert text == ("FIRST asset: Asset_Q\nReports of the last seven days:\n- [1 day ago; news] Asset_Q was listed.\n\n"
                    "SECOND asset: Asset_R\nReports of the last seven days:\n- [2 days ago; news] Asset_R lost funds.")
    assert duel.adjudication_prompt(Q, R, "one", "two") == text + "\n\nAnalyst 1 answered: one\nAnalyst 2 answered: two"


def test_valid_answers():
    assert duel.valid({"choice": "first", "reason": "a  b\nc"}) == {"choice": "first", "reason": "a b c"}
    assert len(duel.valid({"choice": "no_basis", "reason": "w " * 100})["reason"].split()) == 60
    for bad in (None, "first", {"choice": "third", "reason": "x"}, {"choice": "first"}, {"choice": "first", "reason": 3}):
        assert duel.valid(bad) is None
    alias = {"AAA": "Asset_Q", "BBB": "Asset_R"}
    assert duel.said({"choice": "second", "reason": "why"}, ("AAA", "BBB"), alias) == "Asset_R. Reason: why"
    assert duel.said({"choice": "no_basis", "reason": "why"}, ("AAA", "BBB"), alias) == "no_basis. Reason: why"
    assert duel.said(None, ("AAA", "BBB"), alias) == "no valid answer"


def test_agreement_needs_no_adjudicator_and_the_reviewer_sees_the_other_order(tmp_path):
    row, client, judge = _resolve(tmp_path, naming(A="Asset_Q", B="Asset_Q"))
    assert (row["winner"], row["resolution"], row["a_named"], row["b_named"], row["j_named"]) == ("AAA", "agreed", "AAA", "AAA", None)
    assert row["shown_first"] == "AAA" and row["a_reason"] == "A points to the report on Asset_Q" and row["j_reason"] is None
    assert [(c[0], c[1], c[2]) for c in client.log] == [("A", "Asset_Q", "Asset_R"), ("B", "Asset_R", "Asset_Q")]
    assert client.log[0][3] == duel.duel_prompt(Q, R) and client.log[1][3] == duel.duel_prompt(R, Q)
    assert client.log[0][4:] == (duel.SCHEMA, "comparison", duel.MAX_TOKENS)
    assert judge.stats["calls"] == 2 and judge.stats["cost"] == pytest.approx(2 * COST) and len(judge.used) == 2
    flipped, client, _ = _resolve(tmp_path / "x", naming(A="Asset_R", B="Asset_R"), shown=("BBB", "AAA"))
    assert (flipped["winner"], flipped["shown_first"]) == ("BBB", "BBB") and client.log[0][1] == "Asset_R"


def test_two_no_basis_answers_give_no_result(tmp_path):
    row, client, _ = _resolve(tmp_path, naming(A="no_basis", B="no_basis"))
    assert (row["winner"], row["resolution"], row["a_named"], row["b_named"]) == (None, "agreed", "no_basis", "no_basis")
    assert client.calls == 2


def test_disagreement_goes_to_the_adjudicator(tmp_path):
    row, client, _ = _resolve(tmp_path, naming(A="Asset_Q", B="Asset_R", J="Asset_R"))
    assert (row["winner"], row["resolution"], row["j_named"]) == ("BBB", "adjudicated", "BBB")
    role, first, second, prompt = client.log[2][:4]
    assert (role, first, second) == ("J", "Asset_R", "Asset_Q") and prompt.startswith(duel.duel_prompt(R, Q) + "\n\nAnalyst 1 answered: ")
    said = {line.split(" answered: ", 1)[1] for line in prompt.splitlines() if line.startswith("Analyst ")}
    assert said == {"Asset_Q. Reason: A points to the report on Asset_Q", "Asset_R. Reason: B points to the report on Asset_R"}
    # an analyst with an asset against a reviewer without a basis is a disagreement too
    row, client, _ = _resolve(tmp_path / "x", naming(A="Asset_Q", B="no_basis", J="no_basis"))
    assert (row["winner"], row["resolution"], row["j_named"], client.calls) == (None, "adjudicated", "no_basis", 3)
    row, _, _ = _resolve(tmp_path / "y", naming(A="no_basis", B="Asset_R", J="Asset_Q"))
    assert (row["winner"], row["resolution"]) == ("AAA", "adjudicated")


def test_the_adjudicator_sees_the_analysts_in_a_drawn_order(tmp_path):
    first_lines = set()
    for k in range(12):
        _, client, _ = _resolve(tmp_path / str(k), naming(A="Asset_Q", B="Asset_R", J="Asset_Q"), friday=FRIDAY + 7 * k * DAY)
        first_lines.add(re.search(r"^Analyst 1 answered: (\S+)\.", client.log[2][3], flags=re.M).group(1))
    assert first_lines == {"Asset_Q", "Asset_R"}


def test_an_invalid_answer_leaves_the_comparison_unresolved(tmp_path):
    bad = {"choice": "third", "reason": "x"}
    row, client, judge = _resolve(tmp_path, naming(A=bad, B="Asset_Q"))
    assert (row["winner"], row["resolution"], row["a_named"], row["b_named"]) == (None, "unresolved", None, "AAA")
    assert client.calls == 2 and judge.stats["invalid"] == {"A": 1, "B": 0, "J": 0}
    again = DuelClient(naming(A="Asset_Q", B="Asset_Q"))                      # the stored answer is not asked again
    assert duel.resolve(duel.Judge(again, CallCache(tmp_path / "calls.jsonl"), model=client.model), _duel())["resolution"] == "unresolved"
    assert again.attempts == 0
    row, _, judge = _resolve(tmp_path / "x", naming(A="Asset_Q", B="Asset_R", J={"choice": "neither", "reason": "x"}))
    assert (row["winner"], row["resolution"], row["j_named"]) == (None, "unresolved", None) and judge.stats["invalid"]["J"] == 1


def test_a_failed_call_raises_and_a_cached_call_is_free(tmp_path):
    cache = CallCache(tmp_path / "calls.jsonl")
    failing = DuelClient(naming(A="Asset_Q", B="Asset_Q"), fail=lambda role, *_: role == "B")
    with pytest.raises(CallFailed):
        duel.resolve(duel.Judge(failing, cache), _duel())
    assert len(cache) == 1                                                     # analyst A is stored
    client = DuelClient(naming(A="Asset_Q", B="Asset_Q"))
    judge = duel.Judge(client, cache)
    assert duel.resolve(judge, _duel())["winner"] == "AAA" and client.calls == 1 and judge.stats["cached"] == 1
    with pytest.raises(SpendCapError):
        duel.resolve(duel.Judge(DuelClient(naming(A="Asset_Q", B="Asset_Q"), cap_calls=0), CallCache(None)), _duel())
    with pytest.raises(CallFailed, match="no client"):
        duel.Judge(None, CallCache(None), model="m").ask("A", "FIRST asset: x")


# ---------------------------------------------------------------- comparison: rebuild, score, quality
def _filled(tmp_path, n=8, answer=by_strength):
    dossiers = _week_dossiers(n)
    duels = duel.week_duels(FRIDAY, dossiers)
    cache, client = CallCache(tmp_path / "duels.jsonl"), DuelClient(answer)
    judge = duel.Judge(client, cache)
    live = pd.DataFrame([duel.resolve(judge, d) for d in duels], columns=duel.RESULT_COLUMNS)
    return dossiers, duels, cache, client, judge, live


def test_rebuild_from_the_cache_equals_the_live_results(tmp_path):
    dossiers, duels, cache, client, judge, live = _filled(tmp_path)
    assert set(live["resolution"]) == {"agreed", "adjudicated"} and live["winner"].isna().any() and live["winner"].notna().any()
    again, offline, missing = duel.rebuild(duels, CallCache(tmp_path / "duels.jsonl"), client.model)
    assert missing == 0
    pd.testing.assert_frame_equal(again, live)
    assert offline.used == judge.used and offline.stats["calls"] == 0 and offline.stats["cached"] == len(judge.used) == client.calls
    assert duel.rebuild(duels, CallCache(None), client.model)[2] == len(duels)
    empty, _, missing = duel.rebuild(duels, cache, "other/model")
    assert missing == len(duels) and list(empty.columns) == duel.RESULT_COLUMNS and empty.empty


def _results(rows) -> pd.DataFrame:
    """Result rows from (friday, a, b, winner) with the other columns empty."""
    out = pd.DataFrame(rows, columns=["friday", "a", "b", "winner"])
    for col in duel.RESULT_COLUMNS:
        if col not in out:
            out[col] = None
    return out.assign(shown_first=out["a"], resolution="agreed")[duel.RESULT_COLUMNS]


def test_scores_follow_the_decided_comparisons():
    later = FRIDAY + 7 * DAY
    dossiers = pd.concat([_week_dossiers(4), _week_dossiers(3, later)], ignore_index=True)
    results = _results([(FRIDAY, "S00", "S01", "S00"), (FRIDAY, "S00", "S02", "S00"), (FRIDAY, "S01", "S02", "S01"),
                        (FRIDAY, "S02", "S03", None), (later, "S00", "S01", None), (later, "S01", "S02", None)])
    out = duel.scores(results, dossiers)
    assert list(out.columns) == ["friday", "base", "cmp_score", "n_duels", "n_decided"] and len(out) == 7
    week = out[out["friday"] == FRIDAY].set_index("base")
    assert week.loc["S00", "cmp_score"] > week.loc["S01", "cmp_score"] > week.loc["S02", "cmp_score"]
    assert week.loc["S00", "cmp_score"] > week.loc["S03", "cmp_score"] > week.loc["S02", "cmp_score"]
    assert abs(week["cmp_score"].sum()) < 1e-9                                   # log strengths have mean zero within the week
    assert list(week["n_duels"]) == [2, 2, 3, 1] and list(week["n_decided"]) == [2, 2, 2, 0]
    quiet = out[out["friday"] == later]
    assert np.allclose(quiet["cmp_score"], 0.0) and list(quiet["n_duels"]) == [1, 2, 1] and list(quiet["n_decided"]) == [0, 0, 0]


def test_scores_of_the_stand_in_follow_the_letters(tmp_path):
    dossiers, _, _, _, _, live = _filled(tmp_path, n=12)
    out = duel.scores(live, dossiers).set_index("base")
    assert np.corrcoef(out["cmp_score"], np.arange(12))[0, 1] > 0.8
    decided = live[live["winner"].notna()]
    assert (decided["winner"] == decided[["a", "b"]].max(axis=1)).all()


def test_quality_shares():
    nb = duel.NO_BASIS
    rows = [("AAA", "AAA", "AAA", None, "AAA", "agreed"), ("BBB", "AAA", "BBB", "BBB", "BBB", "adjudicated"),
            ("AAA", nb, nb, None, None, "agreed"), ("AAA", "AAA", nb, nb, None, "adjudicated"),
            ("AAA", None, "BBB", None, None, "unresolved")]
    results = pd.DataFrame([{"friday": FRIDAY, "a": "AAA", "b": "BBB", "shown_first": s, "a_named": an, "b_named": bn, "j_named": jn,
                             "winner": w, "resolution": r, "a_reason": None, "b_reason": None, "j_reason": None}
                            for s, an, bn, jn, w, r in rows], columns=duel.RESULT_COLUMNS)
    q = duel.quality(results)
    assert q["comparisons"] == 5 and q["resolution"] == {"agreed": 2, "adjudicated": 2, "unresolved": 1}
    assert q["decided"] == pytest.approx(0.4) and q["adjudicated"] == pytest.approx(0.4)
    assert q["a_no_basis"] == pytest.approx(0.2) and q["b_no_basis"] == pytest.approx(0.4)
    assert q["first_shown"] == pytest.approx(2 / 3) and q["b_first_shown"] == pytest.approx(1 / 3)
    assert q["both_named"] == 2 and q["same_asset"] == pytest.approx(0.5)
    assert duel.quality(results.iloc[:0]) == {"comparisons": 0}
    only_none = duel.quality(results.iloc[[2]])
    assert only_none["first_shown"] is None and only_none["same_asset"] is None and only_none["decided"] == 0.0
    json.dumps(q)


def test_an_order_blind_stand_in_shows_no_position_preference(tmp_path):
    _, _, _, _, _, live = _filled(tmp_path, n=26)
    q = duel.quality(live)
    assert 0.3 < q["first_shown"] < 0.7 and 0.3 < q["b_first_shown"] < 0.7 and q["same_asset"] > 0.8
    always_first = _filled(tmp_path / "x", n=26, answer=lambda role, first, second, prompt: {"choice": "first", "reason": "position"})[5]
    q = duel.quality(always_first)
    assert q["first_shown"] == 1.0 and q["b_first_shown"] == 1.0 and q["same_asset"] == 0.0 and q["adjudicated"] == 1.0


# ---------------------------------------------------------------- gate: synthetic tables
def _tables(weeks=90, n=24, n_dossier=16, signal=0.0, seed=0, start=c5.TEST_START) -> dict:
    """Decision-time tables and forward returns of a synthetic test window. ``signal`` is the loading of the
    return on the comparison score among the dossier assets."""
    rng = np.random.default_rng(seed)
    fridays = pd.date_range(start, periods=weeks, freq="7D")
    bases = [f"S{i:02d}" for i in range(n)]
    top, att, dos, lines, score, results, quant, fwd, flags = ([] for _ in range(9))
    for f in fridays:
        have = set(rng.choice(bases, n_dossier, replace=False))
        strength = dict(zip(bases, rng.normal(size=n)))
        for i, b in enumerate(bases):
            sym = f"{b}USDT"
            top.append((f, sym, b, rng.random(), rng.normal() if rng.random() > 0.1 else np.nan, rng.random()))
            att.append((f, b, float(np.log1p(rng.integers(0, 40)))))
            if rng.random() > 0.05:
                quant.append((f, sym, rng.random()))
            x = strength[b] if b in have else 0.0
            fwd.append((f, sym, 0.05 * (signal * x + np.sqrt(1 - signal ** 2) * rng.normal()), False))
            if b in have:
                k = int(rng.integers(1, 5))
                dos.append((f, b, f"Asset_{chr(65 + i)}", "- text", k))
                lines += [(f, b, j + 1, rng.choice(["favourable", "unfavourable", "neutral", "mixed"]), int(rng.integers(1, 4))) for j in range(k)]
                score.append((f, b, strength[b], 10, int(rng.integers(0, 10))))
                flags.append((f, b, bool(rng.random() < 0.3)))
        order = sorted(have)
        results += [(f, a, b, None if rng.random() < 0.4 else (a if strength[a] > strength[b] else b)) for a, b in zip(order, order[1:])]
    return {"top": pd.DataFrame(top, columns=["date", "symbol", "base", *CONTROLS]),
            "attention": pd.DataFrame(att, columns=["date", "base", "attn_7d"]),
            "dossiers": pd.DataFrame(dos, columns=["friday", "base", "alias", "text", "n_lines"]),
            "lines": pd.DataFrame(lines, columns=["friday", "base", "line", "direction", "materiality"]),
            "scores": pd.DataFrame(score, columns=["friday", "base", c5.SCORE, "n_duels", "n_decided"]),
            "results": _results(results),
            "quant": pd.DataFrame(quant, columns=["date", "symbol", "pred_rank_pct"]),
            "fwd": pd.DataFrame(fwd, columns=["date", "symbol", c5.RET, "delisted"]),
            "flags": pd.DataFrame(flags, columns=["friday", "base", "identified"])}


def _panel(**kwargs) -> pd.DataFrame:
    return c5.assemble_panel(**_tables(**kwargs))


# ---------------------------------------------------------------- gate: panel
def test_panel_rows_and_the_neutral_score():
    t = _tables(weeks=4)
    early = _tables(weeks=2, start=c5.TEST_START - 14 * DAY)["top"]               # universe weeks before the test window
    panel = c5.assemble_panel(**{**t, "top": pd.concat([early, t["top"]], ignore_index=True)})
    assert list(panel.columns) == c5.PANEL_COLUMNS and len(panel) == 4 * 24 and panel["date"].min() == c5.TEST_START
    assert not panel.duplicated(["date", "symbol"]).any()
    have = panel["has_dossier"] == 1.0
    assert have.sum() == len(t["dossiers"]) and set(panel["has_dossier"]) == {0.0, 1.0}
    without = panel[~have]
    for col in ("n_lines", c5.SCORE, "cmp_net", "tone_code", "n_duels", "n_decided"):
        assert (without[col] == 0.0).all() and panel[col].notna().all()
    assert without["identified"].isna().all() and panel.loc[have, "identified"].notna().all()
    row = t["scores"].iloc[5]
    hit = panel[(panel["date"] == row["friday"]) & (panel["base"] == row["base"])].iloc[0]
    assert hit[c5.SCORE] == row[c5.SCORE] and hit["n_decided"] == row["n_decided"]
    lines = t["lines"][(t["lines"]["friday"] == row["friday"]) & (t["lines"]["base"] == row["base"])]
    sign = lines["direction"].map({"favourable": 1, "unfavourable": -1, "neutral": 0, "mixed": 0})
    assert hit["tone_code"] == float((sign * lines["materiality"]).sum()) and hit["n_lines"] == len(lines)
    assert panel[c5.QUANT].isna().any() and panel[c5.RET].notna().all()
    assert c5.assemble_panel(**{**t, "flags": None})["identified"].isna().all()


def test_panel_refuses_inconsistent_tables():
    t = _tables(weeks=3)
    with pytest.raises(ValueError, match="not unique"):
        c5.assemble_panel(**{**t, "top": pd.concat([t["top"], t["top"].iloc[:1]], ignore_index=True)})
    with pytest.raises(ValueError, match="attention count"):
        c5.assemble_panel(**{**t, "attention": t["attention"].iloc[1:]})
    stray = t["dossiers"].iloc[:1].assign(base="ZZZ")
    with pytest.raises(ValueError, match="outside the test universe"):
        c5.assemble_panel(**{**t, "dossiers": pd.concat([t["dossiers"], stray], ignore_index=True)})
    with pytest.raises(ValueError, match="cover different assets"):
        c5.assemble_panel(**{**t, "scores": t["scores"].iloc[1:]})
    with pytest.raises(Exception):                                               # a forward return per universe row at most
        c5.assemble_panel(**{**t, "fwd": pd.concat([t["fwd"], t["fwd"].iloc[:1]], ignore_index=True)})


def test_universe_and_attention_count():
    top = pd.DataFrame({"date": [c5.TEST_START - 7 * DAY, c5.TEST_START, FRIDAY, FRIDAY], "symbol": ["AAAUSDT"] * 3 + ["BBBUSDT"],
                        "base": ["AAA"] * 3 + ["BBB"]})
    assert list(c5.test_universe(top)["date"]) == [c5.TEST_START, FRIDAY, FRIDAY]
    items = pd.DataFrame([_item("d1", "AAA"), _item("d2", "AAA", source="ccnews", event_ts=DECISION - 6 * DAY),
                          _item("d2", "AAA", salience="mention", event_ts=DECISION - 6 * DAY),          # one document, one count
                          _item("d3", "AAA", event_ts=DECISION - 8 * DAY),                               # older than seven days
                          _item("d4", "AAA", event_ts=DECISION - HOUR, as_of_ts=DECISION + HOUR),         # observed after the decision
                          _item("d5", "CCC")])
    out = c5.attention_7d(items, top[top["date"] == FRIDAY])
    assert list(out.columns) == ["date", "base", "attn_7d"] and list(out["base"]) == ["AAA", "BBB"]
    assert out["attn_7d"].tolist() == pytest.approx([np.log(3), 0.0])


def test_net_wins_and_code_tone():
    results = _results([(FRIDAY, "AAA", "BBB", "AAA"), (FRIDAY, "AAA", "CCC", None), (FRIDAY, "BBB", "CCC", "CCC"),
                        (FRIDAY + 7 * DAY, "AAA", "BBB", "BBB")])
    net = c5.net_wins(results).set_index(["friday", "base"])["cmp_net"]
    assert net[(FRIDAY, "AAA")] == 0.5 and net[(FRIDAY, "BBB")] == -1.0 and net[(FRIDAY, "CCC")] == 0.5
    assert net[(FRIDAY + 7 * DAY, "AAA")] == -1.0 and len(net) == 5
    lines = pd.DataFrame([(FRIDAY, "AAA", "favourable", 3), (FRIDAY, "AAA", "unfavourable", 1), (FRIDAY, "AAA", "neutral", 2),
                          (FRIDAY, "BBB", "mixed", 3)], columns=["friday", "base", "direction", "materiality"])
    tone = c5.code_tone(lines).set_index("base")["tone_code"]
    assert tone["AAA"] == 2.0 and tone["BBB"] == 0.0


def test_within_asset_removes_the_standing_level():
    panel = _panel(weeks=6)
    out = c5.within_asset(panel)
    have = out["has_dossier"] > 0
    assert (out.loc[~have, "cmp_within"] == 0.0).all()
    assert np.allclose(out[have].groupby("base")["cmp_within"].mean(), 0.0)
    one = out[have & (out["base"] == "S03")]
    assert np.allclose(one["cmp_within"], one[c5.SCORE] - one[c5.SCORE].mean())


# ---------------------------------------------------------------- gate: statistic
def test_coefficient_equals_the_encompassing_coefficient_of_the_earlier_charters():
    panel = _panel(weeks=12, signal=0.3)
    ours = c5.partial_series(panel, c5.SCORE, [c5.QUANT, *CONTROLS], min_dossiers=0)
    theirs = c2.encompassing_series(panel, c5.SCORE)[1]["beta_llm"]
    assert len(ours) == 12 and list(ours.index) == list(theirs.index)
    assert np.allclose(ours.to_numpy(), theirs.to_numpy(), atol=1e-10)


def test_gate_coefficient_is_the_coefficient_of_the_full_regression():
    panel = _panel(weeks=5, signal=0.3)
    weekly = c5.gate_statistics(panel)[1]
    assert len(weekly) == 5
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[c5.SCORE, c5.RET, c5.QUANT])
        rank = lambda col: day[col].astype(float).rank(pct=True).fillna(0.5).to_numpy()                     # noqa: E731
        x = np.column_stack([np.ones(len(day)), rank(c5.SCORE)] + [rank(c) for c in c5.GATE_CONTROLS])
        beta, *_ = np.linalg.lstsq(x, day[c5.RET].rank(pct=True).to_numpy(), rcond=None)
        assert weekly[d] == pytest.approx(beta[1], abs=1e-10)
    assert c5.GATE_CONTROLS == ["p_quant", "vol_ewma20", "ret_4w", "dvol_30d", "attn_7d", "n_lines", "has_dossier"]


def test_weeks_that_do_not_enter_the_statistic():
    panel = _panel(weeks=6, n=24, n_dossier=16)
    dates = sorted(panel["date"].unique())
    thin = panel[~((panel["date"] == dates[0]) & (panel["symbol"] > "S13USDT"))]                # 14 rows left in one week
    assert dates[0] not in c5.partial_series(thin).index and len(c5.partial_series(thin)) == 5
    few = panel.copy()
    week = few["date"] == dates[1]
    keep = few[week & (few["has_dossier"] > 0)].index[:9]
    drop = few[week & (few["has_dossier"] > 0)].index[9:]
    few.loc[drop, ["has_dossier", "n_lines", c5.SCORE]] = 0.0                                    # nine dossiers left in one week
    assert len(keep) == 9 and dates[1] not in c5.partial_series(few).index
    assert dates[1] in c5.partial_series(few, min_dossiers=9).index
    flat = panel.copy()
    flat.loc[flat["date"] == dates[2], c5.SCORE] = 0.0                                           # no variation of the score
    assert dates[2] not in c5.partial_series(flat).index
    no_quant = panel.copy()
    no_quant.loc[no_quant["date"] == dates[3], c5.QUANT] = np.nan
    assert dates[3] not in c5.partial_series(no_quant).index
    assert dates[3] in c5.partial_series(no_quant, controls=[*CONTROLS, *c5.ATTENTION]).index     # the quant forecast is not needed there
    assert c5.partial_series(panel.iloc[:0]).empty and c5.residual_pairs(panel.iloc[:0]).empty


def test_summary_of_a_weekly_series():
    idx = pd.DatetimeIndex(["2023-06-02", "2023-06-09", "2024-01-05", "2024-01-12", "2025-01-03"], tz="UTC")
    out = c5.summarize(pd.Series([0.02, -0.01, 0.03, 0.01, -0.05], index=idx))
    assert out["weeks"] == 5 and out["mean"] == pytest.approx(0.0) and out["share_positive"] == pytest.approx(0.6)
    assert out["by_year"] == {"2023": {"weeks": 2, "mean": pytest.approx(0.005)}, "2024": {"weeks": 2, "mean": pytest.approx(0.02)}}
    assert out["nw_t"] is not None
    short = c5.summarize(pd.Series([0.02, 0.01], index=idx[:2]))
    assert short["nw_t"] is None and short["by_year"]["2024"] == {"weeks": 0, "mean": None}
    empty = c5.summarize(pd.Series(dtype=float))
    assert empty == {"weeks": 0, "mean": None, "nw_t": None, "share_positive": None,
                     "by_year": {"2023": {"weeks": 0, "mean": None}, "2024": {"weeks": 0, "mean": None}}}


def _stat(t=2.0, mean=0.01, weeks=104, y23=0.01, y24=0.01) -> dict:
    return {"weeks": weeks, "mean": mean, "nw_t": t, "share_positive": 0.6,
            "by_year": {"2023": {"weeks": 52, "mean": y23}, "2024": {"weeks": 52, "mean": y24}}}


@pytest.mark.parametrize("stat, g1, g2", [
    (_stat(), True, True), (_stat(t=1.99), False, True), (_stat(weeks=78), True, True), (_stat(weeks=77), False, False),
    (_stat(y23=-0.001), True, False), (_stat(y24=0.0), True, False), (_stat(y24=None), True, False),
    (_stat(t=None, mean=None, weeks=2), False, False), (_stat(t=-3.0, mean=-0.02, y23=-0.02, y24=-0.02), False, False),
])
def test_gate_thresholds(stat, g1, g2):
    out = c5.gates(stat)
    assert out["G1_coefficient_t"]["pass"] is g1 and out["G2_both_years_positive"]["pass"] is g2
    assert out["G1_coefficient_t"]["threshold"] == 2.0 and out["G1_coefficient_t"]["weeks_needed"] == 78
    assert (c5.GATE_T, c5.GATE_YEARS, c5.MIN_WEEK_ROWS, c5.MIN_WEEK_DOSSIERS, c5.MIN_GATE_WEEKS) == (2.0, (2023, 2024), 15, 10, 78)


# ---------------------------------------------------------------- gate: evaluation and outputs
def test_a_planted_signal_passes_and_noise_fails():
    strong, _ = c5.evaluate(_panel(weeks=100, signal=0.4, seed=1), n_boot=20)
    assert all(g["pass"] for g in strong["gates"].values()) and strong["gate"]["statistic"]["nw_t"] > 4
    assert strong["descriptive"]["spread_score"]["mean"] > 0 and strong["descriptive"]["net_wins"]["mean"] > 0
    assert strong["descriptive"]["score_within_asset"]["nw_t"] > 3                # the planted signal is a weekly one
    noise, errors = c5.evaluate(_panel(weeks=100, signal=0.0, seed=1), n_boot=20)
    assert not noise["gates"]["G1_coefficient_t"]["pass"] and abs(noise["gate"]["statistic"]["nw_t"]) < 2 and errors == {}
    assert set(noise["descriptive"]) == {*c5.DESCRIPTIVE, "score_outside_most_covered", "score_within_asset", "spread_score",
                                         "spread_code_tone", "identified_split", "coverage"}
    assert len(noise["gate"]["weekly"]["dates"]) == len(noise["gate"]["weekly"]["coefficient"]) == 100
    split = noise["descriptive"]["identified_split"]
    assert split["rows"] == split["identified_rows"] + round(split["rows"] * (1 - split["identified_rows"] / split["rows"]))
    assert len(split["difference_ci90"]) == 2 and 0.2 < split["identified_rows"] / split["rows"] < 0.4
    cover = noise["descriptive"]["coverage"]
    assert cover["rows"] == 2400 and cover["dossier_rows"] == 1600 and cover["dossiers_per_week"] == {"min": 16.0, "median": 16.0, "max": 16.0}
    short, _ = c5.evaluate(_panel(weeks=77, signal=0.4, seed=1), n_boot=5)
    assert short["gate"]["statistic"]["nw_t"] > 2 and not any(g["pass"] for g in short["gates"].values())


def test_a_failing_descriptive_panel_is_recorded_and_changes_nothing(monkeypatch):
    panel = _panel(weeks=80, signal=0.4, seed=2)
    clean, _ = c5.evaluate(panel, n_boot=5)
    def broken(_):
        raise RuntimeError("no coverage")
    monkeypatch.setattr(c5, "coverage", broken)
    monkeypatch.setattr(c5, "identified_split", lambda *a, **k: 1 / 0)
    out, errors = c5.evaluate(panel, n_boot=5)
    assert errors == {"coverage": "RuntimeError: no coverage", "identified_split": "ZeroDivisionError: division by zero"}
    assert out["gates"] == clean["gates"] and out["gate"] == clean["gate"] and "coverage" not in out["descriptive"]
    verdict = c5.build_verdict(out, errors, {"comparisons": 3})
    assert verdict["verdict"] == "PASS" and verdict["descriptive_errors"] == errors and verdict["test_weeks"] == 80


def test_registered_outputs():
    t = _tables(weeks=80, signal=0.0, seed=4)
    out = c5.finalize(**t, comparison={"comparisons": 7}, n_boot=5)
    assert set(out) == {"scores.json", "evaluation.json", "comparison.json", "verdict.json"}
    json.dumps(out)
    cols = out["scores.json"]["columns"]
    assert c5.RET not in cols and "delisted" not in cols and cols == [c for c in c5.PANEL_COLUMNS if c not in (c5.RET, "delisted")]
    assert len(out["scores.json"]["rows"]) == 80 * 24 and out["scores.json"]["rows"][0][0] == "2023-01-06"
    assert out["verdict.json"]["verdict"] == "FAIL" and out["verdict.json"]["comparison"] == {"comparisons": 7}
    assert "licenses a single registered run on a sealed window" in out["verdict.json"]["note"]
    assert c5.finalize(**{**t, "flags": None}, comparison={}, n_boot=5)["evaluation.json"]["descriptive"]["identified_split"] == {"rows": 0}
    planted = c5.finalize(**_tables(weeks=80, signal=0.4, seed=4), comparison={}, n_boot=5)
    assert planted["verdict.json"]["verdict"] == "PASS"


# ---------------------------------------------------------------- drivers: shared pieces
def _freeze(root) -> None:
    path = root / cmp_common.CHARTER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Charter\n\nStatus: FROZEN\n")


def test_a_run_on_every_week_needs_the_frozen_charter(tmp_path):
    with pytest.raises(SystemExit, match="draft"):
        cmp_common.require_frozen(tmp_path)
    _freeze(tmp_path)
    cmp_common.require_frozen(tmp_path)
    (tmp_path / cmp_common.CHARTER).write_text(f"# Charter\n\nStatus: {cmp_common.DRAFT_MARK}\n")
    with pytest.raises(SystemExit, match="draft"):
        cmp_common.require_frozen(tmp_path)


def _write(root, path: str, rows) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(root / path, index=False)


def test_joined_tables_put_the_archive_under_the_present_columns(tmp_path):
    _write(tmp_path, cmp_common.PRESENT["items"], [_item("p1", "AAA")])
    _write(tmp_path, cmp_common.PRESENT["docs"], [_doc("p1", {"Asset_A": "asset:AAA"})])
    _write(tmp_path, cmp_common.PRESENT["records"], [_record_row("p1")])
    archive_item = _item("a1", "BBB", source="ccnews")
    _write(tmp_path, cmp_common.ARCHIVE["items"], [{"extra": 1, **dict(reversed(list(archive_item.items())))}])
    _write(tmp_path, cmp_common.ARCHIVE["docs"], [_doc("a1", {"Asset_A": "asset:BBB"})])
    _write(tmp_path, cmp_common.ARCHIVE["records"], [_record_row("a1", base="BBB")])
    _write(tmp_path, "data/compare/pilot_records.parquet", [_record_row("a1", base="BBB"), _record_row("a2", base="CCC")])
    items, docs, records = cmp_common.joined_tables(tmp_path)
    assert list(items.columns) == list(archive_item) and list(items["doc_id"]) == ["p1", "a1"] and list(items["source"]) == ["wayback", "ccnews"]
    assert list(docs["doc_id"]) == ["p1", "a1"] and list(records["doc_id"]) == ["p1", "a1"]
    assert list(cmp_common.joined_tables(tmp_path, records="data/compare/pilot_records.parquet")[2]["doc_id"]) == ["p1", "a1", "a2"]
    _write(tmp_path, cmp_common.ARCHIVE["docs"], [_doc("p1", {"Asset_A": "asset:BBB"})])
    with pytest.raises(SystemExit, match="both stores"):
        cmp_common.joined_tables(tmp_path)


# ---------------------------------------------------------------- drivers: comparison
def _week_list(n=26):
    return duel.week_duels(FRIDAY, _week_dossiers(n))


def test_fill_answers_every_comparison_and_resumes_after_the_spend_limit(tmp_path):
    duels = _week_list()
    assert len(duels) == 130
    whole = DuelClient(by_strength)
    done = cmp_duels.fill(duel.Judge(whole, CallCache(tmp_path / "whole.jsonl")), duels, workers=4)
    assert (done["unfinished"], done["stopped"], done["new_calls"]) == (0, None, whole.calls) and done["new_cost_usd"] == pytest.approx(whole.calls * COST)
    cache = CallCache(tmp_path / "part.jsonl")
    capped = DuelClient(by_strength, cap_calls=100)
    part = cmp_duels.fill(duel.Judge(capped, cache), duels, workers=4)
    assert part["stopped"] == "spend_cap" and part["unfinished"] > 0 and capped.calls == 100
    rest = DuelClient(by_strength)
    again = cmp_duels.fill(duel.Judge(rest, CallCache(tmp_path / "part.jsonl")), duels, workers=4)
    assert (again["unfinished"], again["stopped"]) == (0, None) and rest.calls == whole.calls - 100
    a = duel.rebuild(duels, CallCache(tmp_path / "part.jsonl"), whole.model)[0]
    pd.testing.assert_frame_equal(a, duel.rebuild(duels, CallCache(tmp_path / "whole.jsonl"), whole.model)[0])


def test_fill_retries_failed_comparisons_and_stops_on_a_failing_provider(tmp_path):
    duels, seen = _week_list(), set()

    def first_attempt_fails(role, first, second, prompt):
        new = (role, prompt) not in seen
        seen.add((role, prompt))
        return new and role == "B" and hashed_pair(first, second) % 3 == 0

    flaky = DuelClient(by_strength, fail=first_attempt_fails)
    done = cmp_duels.fill(duel.Judge(flaky, CallCache(tmp_path / "flaky.jsonl")), duels, workers=1, passes=3)
    assert (done["unfinished"], done["stopped"]) == (0, None) and flaky.attempts > flaky.calls
    once = cmp_duels.fill(duel.Judge(DuelClient(by_strength, fail=lambda role, *_: role == "B"), CallCache(tmp_path / "b.jsonl")),
                          duels[:20], workers=1, passes=2)
    assert (once["unfinished"], once["stopped"]) == (20, None)
    down = DuelClient(by_strength, fail=lambda *_: True)
    out = cmp_duels.fill(duel.Judge(down, CallCache(tmp_path / "down.jsonl")), duels, workers=1, passes=3)
    assert out["stopped"] == "consecutive_failures" and out["new_calls"] == 0 and down.attempts == cmp_duels.MAX_CONSECUTIVE_FAILURES


def test_pilot_stop_rule_of_the_comparison():
    good = {"first_shown": 0.5, "same_asset": 0.8, "decided": 0.5}
    assert cmp_duels.PILOT_RULE == {"first_shown": (0.40, 0.60), "same_asset_min": 0.70, "decided_min": 0.30}
    assert cmp_duels.stop_rule(good)["passed"] and cmp_duels.stop_rule({**good, "first_shown": 0.40, "same_asset": 0.70, "decided": 0.30})["passed"]
    for change, check in (({"first_shown": 0.61}, "first_shown_in_band"), ({"first_shown": 0.39}, "first_shown_in_band"),
                          ({"first_shown": None}, "first_shown_in_band"), ({"same_asset": 0.69}, "same_asset"),
                          ({"same_asset": None}, "same_asset"), ({"decided": 0.29}, "decided")):
        out = cmp_duels.stop_rule({**good, **change})
        assert not out["passed"] and [k for k, ok in out["checks"].items() if not ok] == [check]
    assert not cmp_duels.stop_rule({"comparisons": 0})["passed"]


def _duel_root(tmp_path, monkeypatch, n=12):
    """Dossier files of two pilot weeks and three test weeks, and the week selection of the drivers."""
    weeks = [FRIDAY, FRIDAY + 7 * DAY, FRIDAY + 14 * DAY]
    out = tmp_path / "data/compare"
    out.mkdir(parents=True)
    pd.concat([_week_dossiers(n, f) for f in weeks[:2]], ignore_index=True).to_parquet(out / "pilot_dossiers.parquet", index=False)
    pd.concat([_week_dossiers(n, f) for f in weeks], ignore_index=True).to_parquet(out / "dossiers.parquet", index=False)
    top = pd.DataFrame([(f, f"S{i:02d}USDT", f"S{i:02d}") for f in weeks for i in range(n + 2)], columns=["date", "symbol", "base"])
    monkeypatch.setattr(cmp_common, "universe_weeks", lambda args: (top, weeks[:2] if args.pilot else weeks, bool(args.pilot)))
    return weeks, out


def test_comparison_pilot_runs_on_a_draft(tmp_path, monkeypatch, capsys):
    weeks, out = _duel_root(tmp_path, monkeypatch)
    client = DuelClient(by_strength)
    report = cmp_duels.main(["--pilot", "--cap", "1"], root=tmp_path, client=client)
    results, scores = pd.read_parquet(out / "pilot_duels.parquet"), pd.read_parquet(out / "pilot_scores.parquet")
    assert report["pilot"] and report["comparisons"] == len(results) == 2 * 10 * 6 and report["comparisons_call_missing"] == 0
    assert set(results["friday"]) == set(weeks[:2]) and len(scores) == 24 and not (out / "duels.parquet").exists()
    assert (report["model"], report["k_rounds"], report["prompt_sha256"]) == ("fake/duel", 10, duel.prompt_sha256())
    assert sum(r["calls"] for r in report["calls"]["by_role"].values()) == client.calls == report["phase_1"]["new_calls"]
    assert report["cost"]["per_comparison_usd"] == pytest.approx(client.calls * COST / 120)
    assert report["stop_rule"]["passed"] and report["quality"] == duel.quality(results)
    assert json.loads((out / "pilot_duel_report.json").read_text())["stop_rule"] == json.loads(json.dumps(report["stop_rule"]))
    silent = DuelClient(by_strength)
    cmp_duels.main(["--pilot", "--offline"], root=tmp_path, client=silent)
    assert silent.attempts == 0 and '"offline_rebuild_equals_stored_results": true' in capsys.readouterr().out
    results.assign(winner=None).to_parquet(out / "pilot_duels.parquet", index=False)
    with pytest.raises(SystemExit, match="differs"):
        cmp_duels.main(["--pilot", "--offline"], root=tmp_path, client=silent)


def test_comparison_pilot_stop_rule_fails_on_a_position_preference(tmp_path, monkeypatch):
    _, out = _duel_root(tmp_path, monkeypatch)
    report = cmp_duels.main(["--pilot", "--cap", "1"], root=tmp_path,
                            client=DuelClient(lambda role, first, second, prompt: {"choice": "first", "reason": "position"}))
    assert not report["stop_rule"]["passed"]
    assert report["stop_rule"]["checks"] == {"first_shown_in_band": False, "same_asset": False, "decided": True}
    assert (out / "pilot_duels.parquet").exists()                                # the pilot always writes what it saw


def test_full_comparison_needs_the_freeze_and_writes_nothing_when_incomplete(tmp_path, monkeypatch):
    weeks, out = _duel_root(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="draft"):
        cmp_duels.main(["--cap", "1"], root=tmp_path, client=DuelClient(by_strength))
    pilot = DuelClient(by_strength)
    cmp_duels.main(["--pilot", "--cap", "1"], root=tmp_path, client=pilot)
    _freeze(tmp_path)
    with pytest.raises(SystemExit, match="--cap is required"):
        cmp_duels.main([], root=tmp_path, client=DuelClient(by_strength))
    with pytest.raises(SystemExit, match="spend limit reached"):
        cmp_duels.main(["--cap", str(pilot.calls * COST / 2)], root=tmp_path, client=DuelClient(by_strength))
    capped = DuelClient(by_strength, cap_calls=40)
    with pytest.raises(SystemExit, match="incomplete"):
        cmp_duels.main(["--cap", "1"], root=tmp_path, client=capped)
    assert capped.calls == 40 and not (out / "duels.parquet").exists() and not (out / "duel_report.json").exists()
    rest = DuelClient(by_strength)
    report = cmp_duels.main(["--cap", "1"], root=tmp_path, client=rest)
    results = pd.read_parquet(out / "duels.parquet")
    assert not report["pilot"] and "stop_rule" not in report and len(results) == 3 * 60 == report["comparisons"]
    assert set(results["friday"]) == set(weeks) and len(pd.read_parquet(out / "scores.parquet")) == 36
    whole = DuelClient(by_strength)                                              # the pilot weeks came from the cache
    cmp_duels.fill(duel.Judge(whole, CallCache(None)), [d for f in weeks for d in duel.week_duels(f, _week_dossiers(12, f))], workers=1)
    assert pilot.calls + capped.calls + rest.calls == whole.calls
    pd.testing.assert_frame_equal(results[results["friday"].isin(weeks[:2])].reset_index(drop=True), pd.read_parquet(out / "pilot_duels.parquet"))
    again = DuelClient(by_strength)
    cmp_duels.main(["--cap", "1"], root=tmp_path, client=again)
    assert again.attempts == 0


# ---------------------------------------------------------------- drivers: identification probe
class ProbeClient:
    """Stand-in probe client: ``answer(alias)`` gives the parsed answer for the asset token of the prompt;
    ``fail(alias)`` makes the call raise ``ORError``; after ``cap_calls`` answered calls every call raises
    ``SpendCapError``."""
    model = "fake/probe"

    def __init__(self, answer, fail=None, cap_calls=None, cost=COST):
        self.answer, self.fail, self.cap_calls, self.cost = answer, fail, cap_calls, cost
        self.calls, self.attempts, self.log = 0, 0, []
        self._lock = threading.Lock()

    def call(self, prompt, schema_, schema_name="answer", system=None, max_tokens=None):
        alias = re.search(r"^Asset token: (\S+)$", prompt, flags=re.M).group(1)
        with self._lock:
            self.attempts += 1
            if self.cap_calls is not None and self.calls >= self.cap_calls:
                raise SpendCapError("spend cap reached")
            if self.fail is not None and self.fail(alias):
                raise ORError("provider unavailable")
            self.calls += 1
            self.log.append((alias, prompt, schema_, schema_name, system, max_tokens))
        return self.answer(alias), {"provider": "Fake", "cost": self.cost, "prompt_tokens": 200, "completion_tokens": 15, "latency_s": 0.3}


def guesses(alias: str):
    """Asset_A: right asset in lower case, right month. Asset_B: wrong asset, far month. Asset_C: right asset,
    no month. Asset_D: not an object. Every other token: wrong asset, a month six months away."""
    return {"Asset_A": {"asset": "s00", "year_month": "2023-03", "confidence": 0.9},
            "Asset_B": {"asset": "S05", "year_month": "2021-01", "confidence": 0.4},
            "Asset_C": {"asset": " S02 ", "year_month": "soon", "confidence": 0.7},
            "Asset_D": "no idea"}.get(alias, {"asset": "ZZZ", "year_month": "2023-09", "confidence": 0.1})


@pytest.mark.parametrize("year_month, gap", [("2023-03", 0), ("2022-09", 6), ("2024-01", 10), ("2023-03-15", 0), (" 2023-04 ", 1),
                                             ("garbage", None), ("", None), ("2023", None), (None, None)])
def test_month_gap_of_a_guess(year_month, gap):
    assert cmp_probe.month_gap(year_month, FRIDAY) == gap


def test_probe_prompt_and_its_identity(monkeypatch):
    assert cmp_probe.probe_prompt("Asset_A", "- [1 day ago; news] Asset_A report.", ["AAA", "BBB"]) == (
        "Candidate tickers: AAA, BBB\n\nAsset token: Asset_A\nReports of the last seven days:\n- [1 day ago; news] Asset_A report.")
    before = cmp_probe.prompt_sha256()
    assert before == cmp_probe.prompt_sha256() and len(before) == 64
    monkeypatch.setattr(cmp_probe, "SYSTEM", cmp_probe.SYSTEM + " Changed.")
    assert cmp_probe.prompt_sha256() != before


def test_flags_come_from_the_cache_alone(tmp_path):
    dossiers, tickers = _week_dossiers(5), ["S00", "S01", "S02", "S03", "S04", "S05"]
    cache = CallCache(tmp_path / "probe.jsonl")
    for r in dossiers.iloc[:4].itertuples(index=False):
        key = call_key("fake/probe", cmp_probe.SYSTEM, cmp_probe.probe_prompt(r.alias, r.text, tickers))
        cache.put(key, {"parsed": guesses(r.alias), "meta": {"cost": COST}, "role": "probe"})
    table, missing, used = cmp_probe.flags(dossiers, cache, "fake/probe", tickers)
    assert list(table.columns) == cmp_probe.FLAG_COLUMNS and (missing, len(used)) == (1, 4)
    assert list(table["base"]) == ["S00", "S01", "S02", "S03"]
    assert list(table["identified"]) == [True, False, True, False] and list(table["month_within_6"]) == [True, False, False, False]
    assert list(table["guess"]) == ["S00", "S05", "S02", ""] and list(table["year_month"]) == ["2023-03", "2021-01", "soon", ""]
    assert cmp_probe.flags(dossiers, cache, "other/model", tickers)[1] == 5       # another model has no answers
    assert cmp_probe.flags(dossiers, cache, "fake/probe", tickers[:5])[1] == 5    # another candidate list is another prompt


def test_probe_pilot_runs_on_a_draft(tmp_path, monkeypatch):
    weeks, out = _duel_root(tmp_path, monkeypatch)
    client = ProbeClient(guesses)
    report = cmp_probe.main(["--pilot", "--cap", "1"], root=tmp_path, client=client)
    table = pd.read_parquet(out / "pilot_flags.parquet")
    assert report["pilot"] and (report["dossiers"], report["answered"], report["without_answer"], report["new_calls"]) == (24, 24, 0, 24)
    assert (report["model"], report["prompt_sha256"], report["candidate_tickers"]) == ("fake/probe", cmp_probe.prompt_sha256(), 14)
    assert report["chance"] == pytest.approx(1 / 14) and report["identified_share"] == pytest.approx(4 / 24)
    assert report["month_within_6_share"] == pytest.approx(18 / 24)
    assert report["cost_usd"] == pytest.approx(24 * COST) == report["cache_paid_usd"] and report["per_dossier_usd"] == pytest.approx(COST)
    assert list(table.columns) == cmp_probe.FLAG_COLUMNS and set(table["friday"]) == set(weeks[:2]) and not (out / "flags.parquet").exists()
    assert json.loads((out / "pilot_probe_report.json").read_text())["identified_share"] == pytest.approx(4 / 24)
    alias, prompt, schema_, schema_name, system, max_tokens = client.log[0]
    assert (schema_, schema_name, system, max_tokens) == (cmp_probe.SCHEMA, "identification", cmp_probe.SYSTEM, cmp_probe.MAX_TOKENS)
    assert prompt.startswith("Candidate tickers: S00, S01,") and f"Asset token: {alias}\n" in prompt
    silent = ProbeClient(guesses)                                                # the answers are cached
    assert cmp_probe.main(["--pilot", "--cap", "1"], root=tmp_path, client=silent)["new_calls"] == 0 and silent.attempts == 0
    offline = cmp_probe.main(["--pilot", "--offline"], root=tmp_path, client=silent)
    assert silent.attempts == 0 and offline["answered"] == 24
    pd.testing.assert_frame_equal(pd.read_parquet(out / "pilot_flags.parquet"), table)


def test_probe_pilot_records_failed_calls(tmp_path, monkeypatch):
    _, out = _duel_root(tmp_path, monkeypatch)
    report = cmp_probe.main(["--pilot", "--cap", "1"], root=tmp_path, client=ProbeClient(guesses, fail=lambda alias: alias == "Asset_L"))
    assert (report["failed_calls"], report["without_answer"], report["answered"], report["stopped"]) == (2, 2, 22, None)
    assert len(pd.read_parquet(out / "pilot_flags.parquet")) == 22
    capped = cmp_probe.main(["--pilot", "--cap", "1"], root=tmp_path, client=ProbeClient(guesses, cap_calls=0))
    assert capped["stopped"] == "spend_cap" and capped["new_calls"] == 0


def test_full_probe_needs_the_freeze_and_writes_nothing_when_incomplete(tmp_path, monkeypatch):
    weeks, out = _duel_root(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="draft"):
        cmp_probe.main(["--cap", "1"], root=tmp_path, client=ProbeClient(guesses))
    cmp_probe.main(["--pilot", "--cap", "1"], root=tmp_path, client=ProbeClient(guesses))
    _freeze(tmp_path)
    with pytest.raises(SystemExit, match="--cap is required"):
        cmp_probe.main([], root=tmp_path, client=ProbeClient(guesses))
    with pytest.raises(SystemExit, match="spend limit reached"):
        cmp_probe.main(["--cap", str(12 * COST)], root=tmp_path, client=ProbeClient(guesses))
    capped = ProbeClient(guesses, cap_calls=5)
    with pytest.raises(SystemExit, match="incomplete"):
        cmp_probe.main(["--cap", "1"], root=tmp_path, client=capped)
    assert capped.calls == 5 and not (out / "flags.parquet").exists() and not (out / "probe_report.json").exists()
    rest = ProbeClient(guesses)
    report = cmp_probe.main(["--cap", "1"], root=tmp_path, client=rest)
    table = pd.read_parquet(out / "flags.parquet")
    assert rest.calls == 36 - 24 - 5 and not report["pilot"] and (report["answered"], report["without_answer"]) == (36, 0)
    assert set(table["friday"]) == set(weeks) and report["identified_share"] == pytest.approx(6 / 36)
    pd.testing.assert_frame_equal(table[table["friday"].isin(weeks[:2])].reset_index(drop=True), pd.read_parquet(out / "pilot_flags.parquet"))


# ---------------------------------------------------------------- drivers: archive reading
def _read_root(root, monkeypatch):
    """Archive tables of eight weeks under ``root`` and the week selection of the drivers (three pilot weeks)."""
    items, docs, cards = store_frames(weeks=8, n_syms=8, docs_per_week=12)
    _write(root, cmp_common.ARCHIVE["items"], items.assign(source="ccnews"))
    _write(root, cmp_common.ARCHIVE["docs"], docs)
    top = c2.universe(cards)
    fridays = sorted(top["date"].unique())
    monkeypatch.setattr(cmp_common, "universe_weeks", lambda args: (top, fridays[:3] if args.pilot else fridays, bool(args.pilot)))
    return top, fridays


def test_archive_units_are_the_read_rows_of_the_weekly_sets(tmp_path, monkeypatch):
    top, fridays = _read_root(tmp_path, monkeypatch)
    items, docs = (pd.read_parquet(tmp_path / cmp_common.ARCHIVE[k]) for k in ("items", "docs"))
    work, unit_list = cmp_read.archive_units(items, docs, top, fridays[:3])
    assert len(unit_list) == 3 * 8 == work["doc_id"].nunique()                   # four of the six document kinds are read
    assert {u.doc_id[:6] for u in unit_list} == {"doc000", "doc001", "doc002"} and {u.source for u in unit_list} == {"ccnews"}
    assert len(cmp_read.archive_units(items, docs, top, fridays)[1]) == 8 * 8


def test_archive_reading_pilot_runs_on_a_draft(tmp_path, monkeypatch, capsys):
    _, fridays = _read_root(tmp_path, monkeypatch)
    client = FakeClient()
    report = cmp_read.main(["--pilot", "--cap", "1"], root=tmp_path, client=client)
    records = pd.read_parquet(tmp_path / cmp_read.PILOT_RECORDS)
    assert report["pilot"] and report["units"] == 24 and report["weeks"] == [str(f.date()) for f in fridays[:3]]
    assert (report["model"], report["phase_1"]["stopped"]) == ("fake/model", None)
    assert report["calls"]["cost_usd"] == pytest.approx(client.calls * COST) == report["cost"]["cache_paid_usd"]
    assert report["cost"]["per_unit_usd"] == pytest.approx(client.calls * COST / 24)
    assert len(records) and {d[:6] for d in records["doc_id"]} == {"doc000", "doc001", "doc002"}
    assert not (tmp_path / cmp_read.RECORDS).exists() and not (tmp_path / cmp_read.REPORT).exists()
    assert json.loads((tmp_path / cmp_read.PILOT_REPORT).read_text())["units"] == 24
    silent = FakeClient()
    cmp_read.main(["--pilot", "--offline"], root=tmp_path, client=silent)
    assert silent.attempts == 0 and '"offline_rebuild_equals_stored_records": true' in capsys.readouterr().out
    records.iloc[1:].to_parquet(tmp_path / cmp_read.PILOT_RECORDS, index=False)
    with pytest.raises(SystemExit, match="differs"):
        cmp_read.main(["--pilot", "--offline"], root=tmp_path, client=silent)


def test_full_archive_reading_needs_the_freeze_and_writes_nothing_when_incomplete(tmp_path, monkeypatch):
    _read_root(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="draft"):
        cmp_read.main(["--cap", "1"], root=tmp_path, client=FakeClient())
    pilot = FakeClient()
    cmp_read.main(["--pilot", "--cap", "1"], root=tmp_path, client=pilot)
    _freeze(tmp_path)
    with pytest.raises(SystemExit, match="--cap is required"):
        cmp_read.main([], root=tmp_path, client=FakeClient())
    with pytest.raises(SystemExit, match="spend limit reached"):
        cmp_read.main(["--cap", str(pilot.calls * COST / 2)], root=tmp_path, client=FakeClient())
    capped = FakeClient(cap_calls=20)
    with pytest.raises(SystemExit, match="incomplete"):
        cmp_read.main(["--cap", "1"], root=tmp_path, client=capped)
    assert capped.calls == 20 and not (tmp_path / cmp_read.RECORDS).exists() and not (tmp_path / cmp_read.REPORT).exists()
    rest = FakeClient()
    report = cmp_read.main(["--cap", "1"], root=tmp_path, client=rest)
    records = pd.read_parquet(tmp_path / cmp_read.RECORDS)
    assert not report["pilot"] and (report["weeks"], report["units"]) == (8, 64)
    assert {d[:6] for d in records["doc_id"]} == {f"doc{w:03d}" for w in range(8)}
    _freeze(tmp_path / "whole")                                                  # one run without a pilot pays the same calls
    _read_root(tmp_path / "whole", monkeypatch)
    whole = FakeClient()
    cmp_read.main(["--cap", "1"], root=tmp_path / "whole", client=whole)
    assert pilot.calls + capped.calls + rest.calls == whole.calls
    pd.testing.assert_frame_equal(records, pd.read_parquet(tmp_path / "whole" / cmp_read.RECORDS))
    kept = records[records["doc_id"].str[:6].isin({"doc000", "doc001", "doc002"})].reset_index(drop=True)
    pd.testing.assert_frame_equal(kept, pd.read_parquet(tmp_path / cmp_read.PILOT_RECORDS))
    again = FakeClient()
    cmp_read.main(["--cap", "1"], root=tmp_path, client=again)
    assert again.attempts == 0


# ---------------------------------------------------------------- registration and runner
import cmp_charter5_register as reg  # noqa: E402
import cmp_charter5_run as run_script  # noqa: E402


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


CLOSURE = """
import json, sys
from pathlib import Path
root = Path.cwd().resolve()
import cmp_charter5_register, cmp_charter5_run  # noqa: F401,E401
out = set()
for module in list(sys.modules.values()):
    name = getattr(module, "__file__", None)
    path = Path(name).resolve() if name else None
    if path and path.is_relative_to(root) and ".venv" not in path.parts:
        out.add(path.relative_to(root).as_posix())
print(json.dumps(sorted(out)))
"""


def test_registration_pins_every_project_file_the_run_imports():
    import os
    import subprocess

    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(ROOT / "scripts")])}
    done = subprocess.run([sys.executable, "-c", CLOSURE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    imported = set(json.loads(done.stdout.strip().splitlines()[-1]))
    helper = {p for p in imported if p.startswith("tradingagents/research/")}       # pinned by the runtime hashes, if loaded
    assert {"scripts/cmp_charter5_run.py", "tradingagents/compare/charter5.py", "tradingagents/xsect/pair_xs.py"} <= imported
    assert imported - helper <= set(reg.SOURCE_FILES), sorted(imported - helper - set(reg.SOURCE_FILES))
    assert len(set(reg.SOURCE_FILES)) == len(reg.SOURCE_FILES) and all((ROOT / p).is_file() for p in reg.SOURCE_FILES)
    drivers = {f"scripts/{p.name}" for p in (ROOT / "scripts").glob("cmp_*.py")}
    modules = {f"tradingagents/compare/{p.name}" for p in (ROOT / "tradingagents/compare").glob("*.py")}
    assert drivers | modules <= set(reg.SOURCE_FILES)                              # also the drivers that made the tables
    assert {"uv.lock", reg.PARENT_CHARTER} <= set(reg.SOURCE_FILES) and reg.CHARTER not in reg.SOURCE_FILES


def test_registration_continues_the_charter_4_registration():
    parent_spec = json.loads((ROOT / reg.PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][reg.PARENT]
    assert set(parent["source_files"]) <= set(reg.SOURCE_FILES)                     # nothing of the parent run is unpinned
    assert {p: _sha_file(ROOT / p) for p in parent["source_files"]} == parent["source_files"]      # and nothing changed since
    assert reg.PARENT_CHARTER == parent["charter"]["path"] and _sha_file(ROOT / reg.PARENT_CHARTER) == parent["charter"]["sha256"]
    assert reg.DRAFT_MARK not in (ROOT / reg.PARENT_CHARTER).read_text(encoding="utf-8")
    assert {name: parent["inputs"][name]["path"] for name in reg.SAME_AS_PARENT} == {n: reg.INPUTS[n] for n in reg.SAME_AS_PARENT}
    quant = parent_spec["experiments"][reg.QUANT_SOURCE]["inputs"]["quant_forecasts"]
    assert quant["path"] == reg.INPUTS["quant_forecasts"] and _sha_file(ROOT / quant["path"]) == quant["sha256"]
    assert reg.FAMILY_KEY == parent["family"] == "llm-multiagent-v2" and parent_spec["families"][reg.FAMILY_KEY]["attempt_budget"] == 6
    assert len(parent_spec["experiments"]) == 5                                     # the five attempts so far
    assert reg.DATASET not in parent_spec["datasets"] and reg.experiment_id("20261116") not in parent_spec["experiments"]
    assert reg.WINDOW == {"start": "2022-01-01T00:00:00Z", "end": "2025-01-08T00:00:00Z"}
    weekly = parent_spec["experiments"][reg.QUANT_SOURCE]["windows"][0]
    assert (weekly["start"], weekly["end"]) == (reg.WINDOW["start"], reg.WINDOW["end"])     # the weekly window of Charter 2
    last = pd.Timestamp("2024-12-27", tz="UTC")                                     # the last test Friday
    assert pd.Timestamp(reg.WINDOW["end"]) >= last + 8 * DAY and pd.Timestamp(reg.WINDOW["end"]) <= pd.Timestamp("2025-01-08", tz="UTC")


def test_registered_inputs_are_the_inputs_the_runner_reads():
    read = set(re.findall(r'read\("(\w+)"\)', (ROOT / "scripts/cmp_charter5_run.py").read_text()))
    assert read == set(reg.INPUTS)
    assert reg.INPUTS["archive_calls"] == cmp_read.CACHE and reg.INPUTS["duel_calls"] == cmp_duels.CACHE
    assert reg.INPUTS["probe_calls"] == cmp_probe.CACHE and reg.INPUTS["archive_records"] == cmp_read.RECORDS
    assert reg.CHARTER == cmp_common.CHARTER and reg.DRAFT_MARK == cmp_common.DRAFT_MARK


def test_registration_builds_an_exploratory_sixth_attempt_on_the_exposed_window(monkeypatch):
    real = reg._sha
    monkeypatch.setattr(reg, "_sha", lambda p: real(p) if (ROOT / p).is_file() else "0" * 64)    # tables of the full run
    target, spec = reg.build("20991231")
    parent_spec = json.loads((ROOT / reg.PARENT_REGISTRATION).read_text())
    name = reg.experiment_id("20991231")
    assert target == "research/llm-v2-charter5-20991231/gates.json" and not (ROOT / target).exists()
    assert spec["families"] == {reg.FAMILY_KEY: parent_spec["families"][reg.FAMILY_KEY]}
    assert {k: spec["datasets"][k] for k in parent_spec["datasets"]} == parent_spec["datasets"]
    assert {k: spec["experiments"][k] for k in parent_spec["experiments"]} == parent_spec["experiments"]
    assert list(spec["experiments"]) == [*parent_spec["experiments"], name]
    assert spec["datasets"][reg.DATASET]["exposures"] == [{**reg.WINDOW, "state": "exposed"}]
    exp = spec["experiments"][name]
    assert exp["parent"] == reg.PARENT and exp["stage"] == "development" and exp["reuse"] == "exploratory" and exp["selection"] is None
    assert exp["charter"]["path"] == reg.CHARTER and exp["windows"] == [{"dataset": reg.DATASET, **reg.WINDOW, "availability": "existing"}]
    assert exp["cells"] == list(run_script.CELLS) and exp["outputs"] == list(run_script.OUTPUTS)
    parent = parent_spec["experiments"][reg.PARENT]
    assert {k: exp["inputs"][k]["sha256"] for k in reg.SAME_AS_PARENT} == {k: parent["inputs"][k]["sha256"] for k in reg.SAME_AS_PARENT}
    assert all(v["dataset"] == reg.DATASET for v in exp["inputs"].values()) and set(exp["inputs"]) == set(reg.INPUTS)
    assert set(exp["source_files"]) == set(reg.SOURCE_FILES) and exp["source_files"][reg.PARENT_CHARTER] == parent["charter"]["sha256"]
    for word in ("Bradley-Terry", "104 test weeks", f"at least {c5.GATE_T}", f"at least {c5.MIN_GATE_WEEKS} weeks", "lag 4", "2023", "2024"):
        assert word in exp["question"], word
    history = spec["datasets"][reg.DATASET]["history_reference"]
    assert "FAIL" in history and "synthetic" in history and "pilot" in history and "CC-BY-NC-4.0" in history


def test_registration_refuses_a_draft_and_writes_the_store_digest_once(monkeypatch, tmp_path):
    monkeypatch.setattr(reg, "ROOT", tmp_path)
    (tmp_path / reg.CHARTER).parent.mkdir(parents=True)
    (tmp_path / reg.CHARTER).write_text(f"# Charter 5, {reg.DRAFT_MARK}\n")
    with pytest.raises(SystemExit, match="DRAFT"):
        reg.main(["--date", "20991231"])
    (tmp_path / "data/compare/text/ccnews/2023").mkdir(parents=True)
    monkeypatch.setattr(run_script, "TEXT_STORE", "data/compare/text/ccnews")
    with pytest.raises(SystemExit, match="empty"):
        reg.store_digest()
    (tmp_path / "data/compare/text/ccnews/2023/01.parquet").write_bytes(b"a")
    first = reg.store_digest()
    assert json.loads((tmp_path / reg.TEXT_DIGEST).read_text()) == first == {"data/compare/text/ccnews/2023/01.parquet": hashlib.sha256(b"a").hexdigest()}
    assert reg.store_digest() == first
    (tmp_path / "data/compare/text/ccnews/2023/02.parquet").write_bytes(b"b")
    with pytest.raises(SystemExit, match="differs from its written digest"):
        reg.store_digest()


def test_tables_are_compared_by_value_after_a_parquet_round_trip():
    a = pd.DataFrame({"doc_id": ["d1", "d2"], "type": [None, None], "n": [1, 2]})
    stored = pd.DataFrame({"doc_id": ["d1", "d2"], "type": pd.Series([np.nan, np.nan], dtype="string"), "n": [1, 2]})
    assert not a.equals(stored) and run_script.same_table(a, stored)              # a column of only missing values
    assert not run_script.same_table(a, stored.assign(type=pd.Series(["event", None], dtype="string")))
    assert not run_script.same_table(a, stored[["n", "doc_id", "type"]]) and not run_script.same_table(a, stored.iloc[:1])
    assert not run_script.same_table(a, stored.assign(n=[1, 3]))
    t = pd.DataFrame({"ts": pd.to_datetime(["2023-01-01", "2023-01-02"], utc=True)})
    assert run_script.same_table(t, t.assign(ts=t["ts"].astype("datetime64[ns, UTC]")))


def test_store_digest_and_input_check(tmp_path):
    store = tmp_path / run_script.TEXT_STORE / "2023"
    store.mkdir(parents=True)
    (store / "01.parquet").write_bytes(b"x")
    (store / "notes.txt").write_text("not a month file")
    assert run_script.text_digest(tmp_path) == {f"{run_script.TEXT_STORE}/2023/01.parquet": hashlib.sha256(b"x").hexdigest()}
    (tmp_path / "a.bin").write_bytes(b"a")
    experiment = {"inputs": {"a": {"path": "a.bin", "sha256": hashlib.sha256(b"a").hexdigest()}}}
    run_script.check_inputs(tmp_path, experiment)
    (tmp_path / "a.bin").write_bytes(b"b")
    with pytest.raises(SystemExit, match="input a differs"):
        run_script.check_inputs(tmp_path, experiment)
    (tmp_path / "a.bin").unlink()
    with pytest.raises(SystemExit, match="input a differs"):
        run_script.check_inputs(tmp_path, experiment)


def test_typing_cache_from_bytes_matches_the_file_reader(tmp_path):
    lines = [json.dumps({"key": "k1", "value": {"type": "event"}, "cost": 0.1}), "", json.dumps({"key": "k2", "value": {"type": None}})]
    (tmp_path / "t.jsonl").write_text("\n".join(lines) + "\n")
    assert run_script.typing_cache((tmp_path / "t.jsonl").read_bytes()) == reader_items.load_typing_cache(tmp_path / "t.jsonl")


def test_rehearsal_returns_are_seeded_noise_of_the_registered_shape():
    tables = _tables(weeks=6, n=20)
    fwd = run_script.synthetic_returns(tables["top"])
    assert list(fwd.columns) == ["date", "symbol", "fwd_ret", "delisted"] and not fwd["delisted"].any()
    assert fwd["date"].min() >= c5.TEST_START and set(fwd["symbol"]) <= set(tables["top"]["symbol"])
    assert 0.95 < len(fwd) / len(c5.test_universe(tables["top"])) < 1.0 and abs(fwd["fwd_ret"].std() - 0.08) < 0.02
    pd.testing.assert_frame_equal(fwd, run_script.synthetic_returns(tables["top"]))


def test_rehearsal_stops_on_any_error_and_on_a_missing_verdict(monkeypatch):
    tables = _tables(weeks=90)
    ctx = {k: tables[k] for k in ("top", "attention", "dossiers", "lines", "scores", "results", "quant", "flags")}
    ctx["comparison"] = {"quality": {}}
    run_script.rehearse(ctx)
    real = c5.finalize

    def fake(change):
        def finalize(*args, **kwargs):
            out = real(*args, **kwargs)
            change(out)
            return out
        monkeypatch.setattr(c5, "finalize", finalize)

    fake(lambda out: out.update({"extra.json": {}}))
    with pytest.raises(SystemExit, match="output names differ"):
        run_script.rehearse(ctx)
    fake(lambda out: out["verdict.json"].update(descriptive_errors={"coverage": "ValueError: x"}))
    with pytest.raises(SystemExit, match="rehearsal: errors"):
        run_script.rehearse(ctx)
    fake(lambda out: out["verdict.json"].update(verdict="ERROR"))
    with pytest.raises(SystemExit, match="no verdict"):
        run_script.rehearse(ctx)
    fake(lambda out: out["verdict.json"].update(test_weeks=0))
    with pytest.raises(SystemExit, match="no verdict"):
        run_script.rehearse(ctx)
    fake(lambda out: out["evaluation.json"].update(bad=float("nan")))
    with pytest.raises(ValueError):
        run_script.rehearse(ctx)


# ---------------------------------------------------------------- registered run on a synthetic checkout
from test_reader_extract import commit, script_root  # noqa: E402
from test_reader_extract import rx  # noqa: E402

from scripts import cmp_items_build  # noqa: E402
from tradingagents.dossier.entities import build_dictionary  # noqa: E402

RUN_WEEKS, RUN_SYMS, RUN_DOCS, RUN_ARCHIVE_DOCS = 30, 24, 60, 24
RUN_TEST_START = pd.Timestamp("2022-03-04", tz="UTC")                            # 22 test weeks to 2022-07-29
PLANTED = 0.02                                                                   # drift per bar of the week after a decision, per unit of score


@pytest.fixture
def cmp_window(monkeypatch):
    """The registered window moved onto the synthetic store, one model name for every stand-in."""
    monkeypatch.setattr(c5, "TEST_START", RUN_TEST_START)
    monkeypatch.setattr(c5, "GATE_YEARS", (2022,))
    monkeypatch.setattr(c5, "MIN_GATE_WEEKS", 10)
    monkeypatch.setattr(cmp_common, "MODEL", FakeClient.model)
    monkeypatch.setattr(run_script, "REHEARSAL_BOOT", 5)


def _bars_with(days: pd.DatetimeIndex, seed: int, drift: np.ndarray) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(0.03 * rng.normal(size=len(days)) + drift))
    return pd.DataFrame({"open": np.concatenate([[100.0], close[:-1]]), "close": close}, index=pd.Index(days, name="ts"))


def _register(root: Path, manifest: dict) -> None:
    spec = {"schema_version": 1, "program_id": "synthetic-c5",
            "families": {"fam": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3, "prior_attempts": 0,
                                 "history_reference": "synthetic"}},
            "datasets": {"sample": {"identity": "synthetic-sample", "history_reference": "synthetic", "exposures": []}},
            "experiments": {"c5": {
                "family": "fam", "parent": None, "question": "synthetic",
                "charter": {"path": "charter5.md", "sha256": _sha_file(root / "charter5.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {**manifest["source_files"], "charter.md": _sha_file(root / "charter.md")},
                "runtime_hashes": __import__("tradingagents.research", fromlist=["runtime_hashes"]).runtime_hashes(),
                "windows": [{"dataset": "sample", "start": "2022-01-01T00:00:00Z", "end": "2022-12-31T00:00:00Z",
                             "availability": "existing"}],
                "inputs": {name: {"path": path, "sha256": _sha_file(root / path), "dataset": "sample"} for name, path in reg.INPUTS.items()},
                "cells": list(run_script.CELLS), "outputs": list(run_script.OUTPUTS)}}}
    (root / "registration.json").write_text(json.dumps(spec))
    commit(root, "synthetic registration", "registration.json", "charter5.md")


def _cmp_run_root(root: Path, monkeypatch) -> dict:
    """A synthetic checkout before the registered run: the present extraction complete (stand-in reader), archive
    tables and their stand-in rebuild (the synthetic assets have no names for the linker), the archive reading,
    dossiers, comparisons and probe made by the drivers, bars in which the return of the week after a decision
    rises with the comparison score, and a committed registration."""
    items, docs, cards = script_root(root, frozen=True, weeks=RUN_WEEKS, n_syms=RUN_SYMS, docs_per_week=RUN_DOCS)
    docs = docs.assign(alias_map=docs["alias_map"].str.replace("org:venue", "exchange:venue"))      # a role of the masker
    docs.to_parquet(root / rx.INPUTS["docs"], index=False)
    manifest = rx.main(["--charter", "charter.md", "--cost-cap", "5"], root=root, client=FakeClient())
    monkeypatch.setattr(cmp_common, "load_cards", lambda: pd.read_parquet(root / rx.INPUTS["cards"]).assign(
        date=lambda c: pd.to_datetime(c["date"], utc=True)))
    _freeze(root)                                                                # the frozen Charter 5 text of the drivers
    a_items, a_docs, _ = store_frames(weeks=RUN_WEEKS, n_syms=RUN_SYMS, docs_per_week=RUN_ARCHIVE_DOCS, seed=11)
    a_items = a_items.assign(doc_id="cc" + a_items["doc_id"], source="ccnews")
    a_docs = a_docs.assign(doc_id="cc" + a_docs["doc_id"], alias_map=a_docs["alias_map"].str.replace("org:venue", "exchange:venue"))
    _write(root, cmp_common.ARCHIVE["items"], a_items)
    _write(root, cmp_common.ARCHIVE["docs"], a_docs)
    for month in ("01", "02", "03"):
        _write(root, f"{run_script.TEXT_STORE}/2022/{month}.parquet", [{"month": month}])
    (root / reg.INPUTS["typing_cache"]).write_text(json.dumps({"key": "k1", "value": {"type": "event"}}) + "\n")
    (root / reg.TEXT_DIGEST).write_text(json.dumps(run_script.text_digest(root)))
    built = (pd.read_parquet(root / cmp_common.ARCHIVE["items"]), pd.read_parquet(root / cmp_common.ARCHIVE["docs"]))
    rebuilds = []

    def stand_in(paths, cache, bases, workers=4, log=print):
        rebuilds.append((sorted(Path(p).relative_to(root).as_posix() for p in paths), cache, list(bases)))
        return built[0].copy(), built[1].copy()

    monkeypatch.setattr(cmp_items_build, "build_tables", stand_in)
    cmp_read.main(["--cap", "1"], root=root, client=FakeClient())
    top, fridays, _ = cmp_common.universe_weeks(type("Args", (), {"pilot": False, "weeks": ""})())
    bases = cmp_items_build.card_bases(cards)
    lines, dossiers, _ = cmp_dossiers.build(*cmp_common.joined_tables(root), top, fridays, build_dictionary(bases))
    lines.to_parquet(root / reg.INPUTS["lines"], index=False)
    dossiers.to_parquet(root / reg.INPUTS["dossiers"], index=False)
    duel_client, probe_client = DuelClient(by_strength), ProbeClient(guesses)
    duel_client.model = probe_client.model = FakeClient.model
    cmp_duels.main(["--cap", "1"], root=root, client=duel_client)
    cmp_probe.main(["--cap", "1"], root=root, client=probe_client)
    scores = pd.read_parquet(root / reg.INPUTS["scores"])
    rng = np.random.default_rng(5)
    _write(root, reg.INPUTS["quant_forecasts"], top[["date", "symbol"]].assign(pred_rank_pct=rng.uniform(size=len(top))))
    days = pd.date_range(pd.Timestamp("2022-01-01", tz="UTC"), pd.Timestamp(max(fridays)).tz_convert("UTC") + 10 * DAY, freq="D")
    (root / "klines").mkdir()
    for i, base in enumerate(sorted(top["base"].unique())):
        drift = np.zeros(len(days))
        for r in scores[scores["base"] == base].itertuples(index=False):
            week = (days > r.friday) & (days <= r.friday + 7 * DAY)
            drift[week] += PLANTED * r.cmp_score
        _bars_with(days, 100 + i, drift).to_parquet(root / "klines" / f"{base}USDT.parquet")
    digest = {f"klines/{p.name}": _sha_file(p) for p in sorted((root / "klines").glob("*.parquet"))}
    (root / reg.INPUTS["klines_digest"]).parent.mkdir(parents=True, exist_ok=True)
    (root / reg.INPUTS["klines_digest"]).write_text(json.dumps(digest))
    (root / "charter5.md").write_text("synthetic charter of the direct comparison\n")
    _register(root, manifest)
    return {"manifest": manifest, "top": top, "fridays": fridays, "dossiers": dossiers, "scores": scores,
            "rebuilds": rebuilds, "bases": bases}


def _cmp_run(root: Path, *extra: str) -> int:
    return run_script.main(["--registration", "registration.json", "--experiment", "c5", "--workers", "1", *extra], root=root)


def _cmp_output(root: Path, name: str):
    return json.loads((root / "research_runs" / "c5" / "outputs" / name).read_text())


def test_registered_run_checks_everything_before_the_claim_and_joins_outcomes_once(tmp_path, monkeypatch, capsys, cmp_window):
    from tradingagents.research.verify import verify_run
    ctx = _cmp_run_root(tmp_path, monkeypatch)
    weeks = len(ctx["fridays"])
    assert weeks == 22 and ctx["dossiers"].groupby("friday").size().min() >= c5.MIN_WEEK_DOSSIERS
    assert ctx["rebuilds"] == []                                                 # the drivers did not rebuild the link tables
    joins, real_join, rehearsals, real_rehearse = [], run_script.forward_returns, [], run_script.rehearse

    def counted_join(symbols, fridays, klines_dir):
        joins.append(len(fridays))
        return real_join(symbols, fridays, klines_dir=klines_dir)

    def counted_rehearse(context):
        rehearsals.append(len(context["dossiers"]))
        return real_rehearse(context)

    real_finalize = c5.finalize
    monkeypatch.setattr(c5, "finalize", lambda *a, **k: real_finalize(*a, **{**k, "n_boot": 5}))
    monkeypatch.setattr(run_script, "forward_returns", counted_join)
    monkeypatch.setattr(run_script, "rehearse", counted_rehearse)
    claimed = tmp_path / "research_runs"

    def refused(match, exc=SystemExit):
        with pytest.raises(exc, match=match):
            _cmp_run(tmp_path)
        assert not claimed.exists() and joins == [] and rehearsals == []

    # a registered table edited after the registration: its hash differs
    path = tmp_path / reg.INPUTS["scores"]
    original = path.read_bytes()
    pd.read_parquet(path).assign(cmp_score=lambda f: -f["cmp_score"]).to_parquet(path, index=False)
    refused("input scores differs")
    # a registration made with an edited table: the rebuild from the caches differs
    _register(tmp_path, ctx["manifest"])
    refused("comparison score table differs from the rebuild")
    path.write_bytes(original)
    _register(tmp_path, ctx["manifest"])
    # an archive link table that the store and the typing cache do not give
    path = tmp_path / reg.INPUTS["archive_items"]
    original = path.read_bytes()
    pd.read_parquet(path).iloc[1:].to_parquet(path, index=False)
    _register(tmp_path, ctx["manifest"])
    refused("archive link table differs from the rebuild")
    path.write_bytes(original)
    _register(tmp_path, ctx["manifest"])
    # a month file of the archive store changed after its digest
    month = tmp_path / run_script.TEXT_STORE / "2022" / "02.parquet"
    original = month.read_bytes()
    pd.DataFrame([{"month": "changed"}]).to_parquet(month, index=False)
    refused("archive store differs from the registered digest")
    month.write_bytes(original)
    ctx["rebuilds"].clear()

    # pre-flight alone: every table rebuilt, rehearsal on synthetic returns, no claim
    assert _cmp_run(tmp_path, "--preflight-only") == 0
    assert "pre-flight passed" in capsys.readouterr().out
    assert not claimed.exists() and joins == [] and rehearsals == [len(ctx["dossiers"])]
    paths, cache, bases = ctx["rebuilds"][0]
    assert paths == sorted(json.loads((tmp_path / reg.TEXT_DIGEST).read_text())) and len(paths) == 3
    assert cache == {"k1": {"type": "event"}} and bases == ctx["bases"]

    # the registered run
    assert _cmp_run(tmp_path) == 0
    directory = claimed / "c5"
    assert (directory / "claim.json").is_file() and (directory / "complete.json").is_file()
    assert not (directory / "failed.json").exists() and verify_run(directory)["status"] == "complete"
    assert sorted(p.name for p in (directory / "outputs").iterdir()) == sorted(run_script.OUTPUTS)
    assert joins == [weeks] and rehearsals == [len(ctx["dossiers"])] * 2         # one join; one rehearsal per process, before the claim
    verdict, evaluation = _cmp_output(tmp_path, "verdict.json"), _cmp_output(tmp_path, "evaluation.json")
    assert verdict["verdict"] == "PASS" and verdict["descriptive_errors"] == {} and verdict["test_weeks"] == weeks
    assert verdict["gates"]["G1_coefficient_t"]["t"] > 3.0 and verdict["gates"]["G2_both_years_positive"]["pass"]
    assert evaluation["descriptive"]["coverage"]["rows_without_return"] == 0
    comparison = _cmp_output(tmp_path, "comparison.json")
    assert comparison["model"] == FakeClient.model and comparison["k_rounds"] == duel.K_ROUNDS
    assert comparison["prompt_sha256"] == {"comparison": duel.prompt_sha256(), "reader": rx.schema.prompt_sha256(),
                                           "probe": cmp_probe.prompt_sha256()}
    assert comparison["quality"]["comparisons"] == len(pd.read_parquet(tmp_path / reg.INPUTS["duels"]))
    assert comparison["archive"]["units_call_missing"] == 0 and comparison["archive"]["store_files"] == 3
    assert comparison["probe"]["dossiers"] == len(ctx["dossiers"]) and set(comparison["present_extraction"]) == set(run_script.EXTRACTION_KEYS)
    scores = _cmp_output(tmp_path, "scores.json")
    table = pd.DataFrame(scores["rows"], columns=scores["columns"])
    assert len(table) == len(c5.test_universe(ctx["top"])) and "fwd_ret" not in table.columns

    # one registered run per registration
    with pytest.raises(ValueError, match="repeat run prohibited"):
        _cmp_run(tmp_path)
    assert joins == [weeks] and verify_run(directory)["status"] == "complete"


def test_charter_states_the_registered_constants():
    text = " ".join((ROOT / reg.CHARTER).read_text(encoding="utf-8").split())
    lines = (ROOT / reg.CHARTER).read_text(encoding="utf-8").splitlines()
    assert text.count(reg.DRAFT_MARK) == int(lines[0].endswith(reg.DRAFT_MARK))     # in the title or nowhere
    assert (c5.GATE_T, c5.GATE_YEARS, c5.MIN_WEEK_ROWS, c5.MIN_WEEK_DOSSIERS, c5.MIN_GATE_WEEKS) == (2.0, (2023, 2024), 15, 10, 78)
    assert (dossier.WINDOW_DAYS, dossier.MAX_LINES, duel.K_ROUNDS, duel.BT_ALPHA, duel.MAX_TOKENS, cmp_probe.MAX_TOKENS) == (7, 10, 10, 0.5, 200, 100)
    assert (c5.BOOTSTRAP_DRAWS, c5.BOOTSTRAP_SEED, scope.PILOT_SEED, scope.PILOT_WEEKS) == (500, 20261115, 20261115, 3)
    assert (archive.AVAIL_WINDOW, archive.LIVE_TOLERANCE, archive.LIVE_MARGIN, archive.LATE_MARGIN) == (50, HOUR, HOUR, 24 * HOUR)
    assert c5.GATE_CONTROLS == ["p_quant", "vol_ewma20", "ret_4w", "dvol_30d", "attn_7d", "n_lines", "has_dossier"]
    assert cmp_duels.PILOT_RULE == {"first_shown": (0.40, 0.60), "same_asset_min": 0.70, "decided_min": 0.30}
    from tradingagents.agents_v2.evaluate import newey_west_t
    import inspect
    assert inspect.signature(newey_west_t).parameters["lag"].default == 4
    for stated in ("Newey-West t (lag 4)", f"at least {c5.GATE_T}", f"at least {c5.MIN_GATE_WEEKS} weeks", "positive in 2023 and in 2024",
                   f"at least {c5.MIN_WEEK_ROWS} complete rows", f"at least {c5.MIN_WEEK_DOSSIERS} of them with a dossier",
                   f"first {duel.K_ROUNDS} rounds", f"at most {dossier.MAX_LINES} lines", f"{duel.BT_ALPHA} pseudo-wins",
                   f"at most {duel.MAX_TOKENS} output tokens", f"at most {cmp_probe.MAX_TOKENS} output tokens",
                   f"{c5.BOOTSTRAP_DRAWS} draws, seed {c5.BOOTSTRAP_SEED}", f"seed {scope.PILOT_SEED}", "0.40 to 0.60", "at least 70 %",
                   "at least 30 %", f"the {archive.AVAIL_WINDOW} articles", "one hour after its publication", "24 hours after the clock",
                   "`p_quant`, `vol_ewma20`, `ret_4w`, `dvol_30d`, `attn_7d`, `n_lines`, `has_dossier`",
                   duel.prompt_sha256(), cmp_probe.prompt_sha256(), reader_items.prompt_sha256(), rx.schema.prompt_sha256(),
                   cmp_common.MODEL, " or ".join(cmp_common.PROVIDER_ORDER), reg.PARENT, "typing $4.00", "reading $3.00",
                   "comparisons $3.00", "probe $0.30"):
        assert stated in text, stated
    for line in duel.INSTRUCTION.splitlines() + [duel.REVIEWER, duel.ADJUDICATOR, cmp_probe.SYSTEM]:
        assert line.strip() in text, line[:40]                                   # Appendix A carries the code texts
    for week in ("2023-01-27", "2023-09-29", "2024-03-01"):
        assert week in text
    fridays = list(pd.date_range(c5.TEST_START, periods=104, freq="7D"))
    assert str(fridays[-1].date()) == "2024-12-27" and [str(d.date()) for d in scope.pilot_weeks(fridays)] == ["2023-01-27", "2023-09-29", "2024-03-01"]
    for flag in ("--cap 4.00", "--cap 3.00", "--cap 0.30"):
        assert flag in text
