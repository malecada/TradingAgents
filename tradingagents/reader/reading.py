"""Reading sets and the extraction work list of the reader configuration (Charter 2).

The reading set of an asset at a decision is the rule under which the typing was bought (``builder.retrieve_text``):
store rows of the last 30 days observable at the decision and linked to the asset; every news row; of the
community posts only those with the asset as primary subject, the newest 25. A row yields a record when its
document is typed ``event`` or ``analysis_opinion`` and either the summary carries the asset's token or the
summary carries no asset token and the asset is the single primary link of the document. No outcome is read.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

import pandas as pd

from tradingagents.dossier.builder import REDDIT_CAP, TEXT_LOOKBACK_DAYS
from tradingagents.reader.schema import FILED_ALIAS

READ_TYPES = ("event", "analysis_opinion")
DECISION_OFFSET = pd.Timedelta(days=1)   # decision = Saturday 00:00 UTC after the Friday card


@dataclass(frozen=True)
class Unit:
    """One document as the agents see it: its summary and the assets to record (alias, base)."""
    doc_id: str
    type: str
    source: str
    summary: str
    assets: tuple[tuple[str, str], ...]

    @property
    def aliases(self) -> list[str]:
        return [a for a, _ in self.assets]


def summary_assets(alias_map: str) -> dict[str, str]:
    """base -> alias for the asset tokens of one summary (the first alias in sort order when two share a base)."""
    out: dict[str, str] = {}
    for alias, key in sorted(json.loads(alias_map).items()):
        if key.startswith("asset:"):
            out.setdefault(key.split(":", 1)[1], alias)
    return out


def flag_items(items: pd.DataFrame, docs: pd.DataFrame) -> pd.DataFrame:
    """Adds ``in_summary``, ``focus_only`` and ``read`` to the item rows."""
    assets = docs.set_index("doc_id")["alias_map"].map(summary_assets)
    pairs = pd.DataFrame([(d, b) for d, m in assets.items() for b in m], columns=["doc_id", "base"]).assign(in_summary=True)
    out = items.merge(pairs, on=["doc_id", "base"], how="left", validate="m:1")
    out["in_summary"] = out["in_summary"].fillna(False).astype(bool)
    n_primary = out[out["salience"] == "primary"].groupby("doc_id")["base"].size().rename("n_primary")
    n_tokens = assets.map(len).rename("n_tokens")
    out = out.join(n_primary, on="doc_id").join(n_tokens, on="doc_id")
    out["focus_only"] = (out["salience"] == "primary") & (out["n_primary"] == 1) & (out["n_tokens"] == 0)
    out["read"] = out["type"].isin(READ_TYPES) & (out["in_summary"] | out["focus_only"])
    return out.drop(columns=["n_primary", "n_tokens"])


def reading_set(items: pd.DataFrame, members, decision: pd.Timestamp, lookback_days: int = TEXT_LOOKBACK_DAYS,
                reddit_cap: int = REDDIT_CAP) -> pd.DataFrame:
    """Item rows in the reading sets of ``members`` at ``decision`` (flagged rows; one row per document and asset)."""
    lo = decision - pd.Timedelta(days=lookback_days)
    win = items[(items["event_ts"] >= lo) & (items["event_ts"] <= decision) & (items["as_of_ts"] <= decision)
                & items["base"].isin(set(members))]
    news = win[win["source"] != "reddit"]
    posts = win[(win["source"] == "reddit") & (win["salience"] == "primary")]
    posts = posts.sort_values(["event_ts", "doc_id"], ascending=[False, True]).groupby("base", sort=False).head(reddit_cap)
    return pd.concat([news, posts], ignore_index=True)


def reading_sets(items: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    """Reading sets of every universe week, with ``friday`` and ``decision`` columns."""
    parts = []
    for friday, week in top.groupby("date"):
        decision = pd.Timestamp(friday) + DECISION_OFFSET
        parts.append(reading_set(items, week["base"], decision).assign(friday=friday, decision=decision))
    return pd.concat(parts, ignore_index=True)


def work_list(reading: pd.DataFrame) -> pd.DataFrame:
    """(doc_id, base, focus_only) of every row that yields a record in some reading set."""
    rows = reading[reading["read"]]
    return (rows[["doc_id", "base", "focus_only"]].drop_duplicates(["doc_id", "base"])
            .sort_values(["doc_id", "base"]).reset_index(drop=True))


def units(work: pd.DataFrame, docs: pd.DataFrame, items: pd.DataFrame) -> list[Unit]:
    """One unit per document of the work list, assets in alias order."""
    meta = docs.set_index("doc_id")
    source = items.drop_duplicates("doc_id").set_index("doc_id")["source"]
    out = []
    for doc_id, rows in work.groupby("doc_id", sort=True):
        d = meta.loc[doc_id]
        alias_of = summary_assets(d["alias_map"])
        assets = []
        for r in rows.itertuples(index=False):
            alias = FILED_ALIAS if r.focus_only else alias_of[r.base]
            assets.append((alias, r.base))
        if len({a for a, _ in assets}) != len(assets):
            raise ValueError(f"alias collision in {doc_id}")
        out.append(Unit(doc_id=doc_id, type=d["type"], source=source.loc[doc_id], summary=d["summary"],
                        assets=tuple(sorted(assets))))
    return out
