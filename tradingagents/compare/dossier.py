"""Text dossiers of the direct-comparison configuration (Charter 5).

One dossier per asset and week: the reports of the last seven days whose reader record names the asset as
the subject. Reports with the same event class, status and direction count as reports of one matter; a
matter is shown once, by its most material and then most recent report, with the number of reports. The
reader's class, direction and materiality select and order the lines and are not shown: the agents compare
on the text. All dossiers of a week share one alias space, so an entity carries the same token in both
dossiers of a comparison. No outcome is read and no model is called.
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd

from tradingagents.dossier.anonymizer import Masker
from tradingagents.dossier.builder import translate_aliases
from tradingagents.dossier.entities import Dictionary
from tradingagents.reader.reading import DECISION_OFFSET, flag_items, reading_set

WINDOW_DAYS = 7
MAX_LINES = 10
SUBJECT = "subject"
MATTER = ["event_class", "status", "direction"]
SOURCE_LABEL = {"reddit": "community post"}
RECORD_COLUMNS = ["doc_id", "base", "resolution", "relevance", *MATTER, "materiality"]
LINE_COLUMNS = ["friday", "decision", "base", "rank", "doc_id", "source", "event_ts", "n_reports", *MATTER, "materiality"]
DOSSIER_COLUMNS = ["friday", "base", "alias", "n_lines", "n_reports", "leaks", "sha256", "text"]


def week_seed(friday) -> int:
    """Seed of everything drawn for one week (alias letters, pairing, shown order)."""
    day = pd.Timestamp(friday).strftime("%Y-%m-%d")
    return int(hashlib.sha256(f"compare|{day}".encode("utf-8")).hexdigest()[:12], 16)


def weekly_sets(items: pd.DataFrame, docs: pd.DataFrame, top: pd.DataFrame, fridays=None) -> pd.DataFrame:
    """Seven-day reading sets of the universe weeks (the rule of ``reading.reading_set``), flagged rows with
    ``friday`` and ``decision``. ``fridays`` restricts the weeks."""
    flagged = flag_items(items, docs)
    weeks = top if fridays is None else top[top["date"].isin(set(fridays))]
    lo = weeks["date"].min() - pd.Timedelta(days=WINDOW_DAYS)
    flagged = flagged[flagged["event_ts"] >= lo]
    parts = []
    for friday, week in weeks.groupby("date"):
        decision = pd.Timestamp(friday) + DECISION_OFFSET
        part = reading_set(flagged, week["base"], decision, lookback_days=WINDOW_DAYS)
        parts.append(part.assign(friday=friday, decision=decision))
    return pd.concat(parts, ignore_index=True)


def work_rows(sets: pd.DataFrame) -> pd.DataFrame:
    """(doc_id, base, focus_only) of every row of the weekly sets that needs a reader record."""
    rows = sets[sets["read"]]
    return (rows[["doc_id", "base", "focus_only"]].drop_duplicates(["doc_id", "base"])
            .sort_values(["doc_id", "base"]).reset_index(drop=True))


def candidates(sets: pd.DataFrame, records: pd.DataFrame, docs: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Rows of the weekly sets whose record names the asset as the subject, and the counts of what was left out.
    A document whose summary still carries a name (``leaky``) is never shown."""
    rows = sets[sets["read"]]
    have = records[RECORD_COLUMNS]
    if have.duplicated(["doc_id", "base"]).any():
        raise ValueError("record table: duplicate (doc_id, base)")
    out = rows.merge(have, on=["doc_id", "base"], how="left", validate="m:1", indicator=True)
    counts = {"read_rows": len(out), "without_record": int((out["_merge"] != "both").sum()),
              "unresolved": int((out["resolution"] == "unresolved").sum())}
    out = out[out["relevance"] == SUBJECT].drop(columns="_merge")
    counts["subject_rows"] = len(out)
    leaky = set(docs.loc[docs["leaky"].astype(bool), "doc_id"])
    drop = out["doc_id"].isin(leaky)
    counts["leaky_rows"] = int(drop.sum())
    return out[~drop].reset_index(drop=True), counts


def line_table(cands: pd.DataFrame, max_lines: int = MAX_LINES) -> pd.DataFrame:
    """One row per dossier line, ``rank`` 1 first. Matters are ordered by materiality, number of reports and
    recency; ties by document id, so the table is a function of its input."""
    if cands.empty:
        return pd.DataFrame(columns=LINE_COLUMNS)
    key = ["friday", "base", *MATTER]
    rows = cands.sort_values([*key, "materiality", "event_ts", "doc_id"], ascending=[True] * len(key) + [False, False, True])
    lead = rows.drop_duplicates(key, keep="first").copy()
    lead["n_reports"] = lead[key].merge(rows.groupby(key)["doc_id"].nunique().rename("n").reset_index(), on=key, how="left")["n"].to_numpy()
    lead = lead.sort_values(["friday", "base", "materiality", "n_reports", "event_ts", "doc_id"],
                            ascending=[True, True, False, False, False, True])
    lead["rank"] = lead.groupby(["friday", "base"]).cumcount() + 1
    return lead[lead["rank"] <= max_lines][LINE_COLUMNS].reset_index(drop=True)


def _age(decision: pd.Timestamp, event_ts: pd.Timestamp) -> str:
    days = (decision.normalize() - event_ts.normalize()).days
    return "today" if days <= 0 else ("1 day ago" if days == 1 else f"{days} days ago")


def _line(row, summary: str, decision: pd.Timestamp) -> str:
    head = [_age(decision, row.event_ts), SOURCE_LABEL.get(row.source, "news")]
    if row.n_reports > 1:
        head.append(f"{int(row.n_reports)} reports")
    return f"- [{'; '.join(head)}] {summary}"


def render_week(lines: pd.DataFrame, docs: pd.DataFrame, dictionary: Dictionary, friday) -> pd.DataFrame:
    """Dossiers of one week in one alias space. Aliases are issued to the assets with a dossier in ticker
    order, then to every other entity in the order of the lines, so the result is a function of the input."""
    decision = pd.Timestamp(friday) + DECISION_OFFSET
    masker = Masker(dictionary, decision, week_seed(friday))
    meta = docs.set_index("doc_id")
    bases = sorted(lines["base"].unique())
    alias = {b: masker.alias("asset", b) for b in bases}
    out = []
    for base in bases:
        rows = lines[lines["base"] == base].sort_values("rank")
        text = []
        for r in rows.itertuples(index=False):
            d = meta.loc[r.doc_id]
            text.append(_line(r, translate_aliases(d["summary"], json.loads(d["alias_map"]), masker), decision))
        body = "\n".join(text)
        out.append((friday, base, alias[base], len(rows), int(rows["n_reports"].sum()), len(masker.verify(body)),
                    hashlib.sha256(f"{alias[base]}\n{body}".encode("utf-8")).hexdigest(), body))
    return pd.DataFrame(out, columns=DOSSIER_COLUMNS)


def build(lines: pd.DataFrame, docs: pd.DataFrame, dictionary: Dictionary) -> pd.DataFrame:
    """Dossiers of every week of the line table."""
    parts = [render_week(week, docs, dictionary, friday) for friday, week in lines.groupby("friday")]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=DOSSIER_COLUMNS)
