"""Consensus of the two readers and the adjudication (Charter 2). Code decides agreement; an agent decides
only where the readers differ.

Agreement: equal relevance, and either both say ``not_about`` or class, status and direction are equal and
materiality differs by at most one (the lower value is kept). A missing reading is a disagreement. Where both
readings are missing, or the adjudicator gives no valid record, the record is unresolved and enters no feature.
"""
from __future__ import annotations

import hashlib

from tradingagents.reader import schema
from tradingagents.reader.extract import CallFailed, Reader
from tradingagents.reader.reading import Unit

RECORD_COLUMNS = ["doc_id", "base", "alias", "focus_only", "resolution", *schema.FIELDS,
                  *[f"a_{f}" for f in schema.FIELDS[:-1]], *[f"b_{f}" for f in schema.FIELDS[:-1]]]


def agree(a: dict | None, b: dict | None) -> bool:
    if a is None or b is None or a["relevance"] != b["relevance"]:
        return False
    if a["relevance"] == "not_about":
        return True
    return (a["event_class"] == b["event_class"] and a["status"] == b["status"] and a["direction"] == b["direction"]
            and abs(a["materiality"] - b["materiality"]) <= 1)


def merged(a: dict, b: dict) -> dict:
    """The agreed record: reader A's fields with the lower materiality."""
    return {**a, "materiality": min(a["materiality"], b["materiality"])}


def a_first(doc_id: str) -> bool:
    """Which reader the adjudicator sees first: fixed per document, balanced over documents."""
    return int(hashlib.sha256(doc_id.encode("utf-8")).hexdigest(), 16) % 2 == 0


def resolve(reader: Reader, unit: Unit) -> list[dict]:
    """Rows of the record table for one document: both readings, the adjudication where needed, the final record."""
    a, b = reader.read("A", unit), reader.read("B", unit)
    disputed = [al for al in unit.aliases if not agree(a[al], b[al])]
    to_judge = [al for al in disputed if a[al] is not None or b[al] is not None]
    judged = {}
    if to_judge:
        readings = (a, b) if a_first(unit.doc_id) else (b, a)
        judged = reader.read("J", unit, aliases=to_judge, readings=readings)
    rows = []
    for alias, base in unit.assets:
        if alias not in disputed:
            final, how = merged(a[alias], b[alias]), "agreed"
        elif judged.get(alias) is not None:
            final, how = judged[alias], "adjudicated"
        else:
            final, how = None, "unresolved"
        row = {"doc_id": unit.doc_id, "base": base, "alias": alias, "focus_only": alias == schema.FILED_ALIAS, "resolution": how}
        for f in schema.FIELDS:
            row[f] = final[f] if final else None
        for tag, rec in (("a", a[alias]), ("b", b[alias])):
            for f in schema.FIELDS[:-1]:
                row[f"{tag}_{f}"] = rec[f] if rec else None
        rows.append(row)
    return rows


def unresolved_rows(unit: Unit) -> list[dict]:
    """Rows of a unit without any reading: every asset unresolved."""
    rows = []
    for alias, base in unit.assets:
        row = dict.fromkeys(RECORD_COLUMNS)
        row.update(doc_id=unit.doc_id, base=base, alias=alias, focus_only=alias == schema.FILED_ALIAS, resolution="unresolved")
        rows.append(row)
    return rows


def rebuild(unit_list: list[Unit], cache, model: str) -> tuple[list[dict], Reader, list[str]]:
    """Every record from the cache alone, without a call: (rows, the reader with its counters, documents with a
    call missing from the cache). A unit with a missing call is unresolved."""
    reader, rows, missing = Reader(None, cache, model=model), [], []
    for unit in unit_list:
        try:
            rows += resolve(reader, unit)
        except CallFailed:
            missing.append(unit.doc_id)
            rows += unresolved_rows(unit)
    return rows, reader, missing


def same_records(a, b) -> bool:
    """Two record tables are equal cell by cell (missing values equal each other)."""
    def norm(frame):
        return frame[RECORD_COLUMNS].astype(object).where(frame[RECORD_COLUMNS].notna(), None).reset_index(drop=True)
    return len(a) == len(b) and bool(norm(a).equals(norm(b)))


def record_frame(rows: list[dict]) -> "pd.DataFrame":
    """The record table with integer materiality columns that keep their missing values."""
    import pandas as pd
    frame = pd.DataFrame(rows, columns=RECORD_COLUMNS)
    for col in ("materiality", "a_materiality", "b_materiality"):
        frame[col] = frame[col].astype("Int64")
    frame["focus_only"] = frame["focus_only"].astype(bool)
    return frame


def record_rows(frame) -> list[dict]:
    """Record rows as plain dicts with None for a missing value (the form ``quality`` reads)."""
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


def quality(rows: list[dict]) -> dict:
    """Extraction quality from record rows: validity of single readings, agreement by field, resolution shares."""
    n = len(rows)
    if not n:
        return {"records": 0}
    both = [r for r in rows if r["a_relevance"] is not None and r["b_relevance"] is not None]
    about = [r for r in both if r["a_relevance"] != "not_about" and r["b_relevance"] != "not_about"]

    def share(sub, f):
        return sum(r[f"a_{f}"] == r[f"b_{f}"] for r in sub) / len(sub) if sub else None

    def count(key):
        return sum(r["resolution"] == key for r in rows)

    final = [r for r in rows if r["resolution"] != "unresolved"]
    return {"records": n, "documents": len({r["doc_id"] for r in rows}),
            "valid_reading_a": sum(r["a_relevance"] is not None for r in rows) / n,
            "valid_reading_b": sum(r["b_relevance"] is not None for r in rows) / n,
            "agreement": {"relevance": share(both, "relevance"), "event_class": share(about, "event_class"),
                          "status": share(about, "status"), "direction": share(about, "direction"),
                          "materiality_exact": share(about, "materiality"),
                          "materiality_within_one": (sum(abs(r["a_materiality"] - r["b_materiality"]) <= 1 for r in about) / len(about)) if about else None,
                          "rows_both_valid": len(both), "rows_both_about": len(about)},
            "resolution": {"agreed": count("agreed") / n, "adjudicated": count("adjudicated") / n, "unresolved": count("unresolved") / n},
            "documents_adjudicated": len({r["doc_id"] for r in rows if r["resolution"] != "agreed"}) / len({r["doc_id"] for r in rows}),
            "final": {"relevance": _dist(final, "relevance"), "direction": _dist([r for r in final if r["relevance"] == "subject"], "direction"),
                      "materiality": _dist([r for r in final if r["relevance"] == "subject"], "materiality"),
                      "event_class": _dist([r for r in final if r["relevance"] == "subject"], "event_class")}}


def _dist(rows: list[dict], field: str) -> dict:
    out: dict[str, int] = {}
    for r in rows:
        out[str(r[field])] = out.get(str(r[field]), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


__all__ = ["RECORD_COLUMNS", "agree", "merged", "a_first", "resolve", "unresolved_rows", "rebuild", "same_records",
           "record_frame", "record_rows", "quality", "CallFailed"]
