"""Asset-week text features of the reader configuration (Charter 2 §3.3). Code only, no model call, no outcome.

Block A counts every linked document observable at the decision, typed or not, with no cap. Block B sums the
consensus records of the reading set. "Last 7 days" means decision - 7 d < event_ts <= decision; "days 8 to 30"
means decision - 30 d <= event_ts <= decision - 7 d. Values are raw; the model ranks them within the week.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.reader.reading import DECISION_OFFSET

BLOCK_A = ["attn_7d", "attn_abn"]
BLOCK_B = ["tone_7d", "tone_30d", "unfav_7d", "sched_fwd", "stance_7d", "supply_30d"]
TEXT_FEATURES = BLOCK_A + BLOCK_B
BLOCK_B_CLASS = ["tone_7d_c", "tone_30d_c", "unfav_7d_c", "sched_fwd_c", "supply_30d"]   # direction from the class alone
COUNTS = ["n_subject_7d", "n_subject_30d", "n_unresolved_30d"]

DIRECTION_SIGN = {"favourable": 1, "unfavourable": -1, "mixed": 0, "neutral": 0}
CLASS_SIGN = {"security_incident": -1, "legal_regulatory": -1, "exchange_listing": 1, "exchange_delisting": -1,
              "token_supply_increase": -1, "token_supply_reduction": 1, "protocol_upgrade_or_launch": 1,
              "partnership_or_integration": 1, "adoption_or_product": 1, "distress_or_outage": -1,
              "funding_or_treasury": 1, "governance_or_team": 0, "market_wide_or_macro": 0, "opinion_or_forecast": 0,
              "other": 0}
ATTN_HISTORY, ATTN_MIN_HISTORY = 8, 4      # weeks in the own-history mean of attention; fewer than the minimum -> missing
WEEK = pd.Timedelta(days=7)


def attention(items: pd.DataFrame, fridays, bases, store_start: pd.Timestamp) -> pd.DataFrame:
    """(date, base, attn_7d, attn_abn) for every Friday in ``fridays`` and every base in ``bases``.

    ``attn_7d`` is log(1 + distinct linked documents of the last 7 days). ``attn_abn`` subtracts the asset's own
    mean of the same quantity over the ``ATTN_HISTORY`` preceding 7-day windows, all counted from what is
    observable at this decision; a history window counts only when it lies inside the store, and with fewer than
    ``ATTN_MIN_HISTORY`` such windows the value is missing."""
    bases = sorted(set(bases))
    rows = items[items["base"].isin(bases)]
    ev, asof = rows["event_ts"], rows["as_of_ts"]
    out = []
    for friday in sorted(pd.Timestamp(f) for f in fridays):
        dec = friday + DECISION_OFFSET
        seen = rows[(ev > dec - (ATTN_HISTORY + 1) * WEEK) & (ev <= dec) & (asof <= dec)]
        k = ((dec - seen["event_ts"]) // WEEK).astype(int)                     # 0 = last 7 days, 1 = the week before, ...
        n = seen.assign(k=k).groupby(["base", "k"])["doc_id"].nunique().unstack("k")
        n = n.reindex(index=bases, columns=range(ATTN_HISTORY + 1)).fillna(0.0)
        attn = np.log1p(n)
        inside = [j for j in range(1, ATTN_HISTORY + 1) if dec - (j + 1) * WEEK >= store_start]
        own = attn[inside].mean(axis=1) if len(inside) >= ATTN_MIN_HISTORY else np.nan
        out.append(pd.DataFrame({"date": friday, "base": bases, "attn_7d": attn[0].to_numpy(),
                                 "attn_abn": (attn[0] - own).to_numpy()}))
    return pd.concat(out, ignore_index=True)


def _signed(rows: pd.DataFrame, key: list[str], sign: pd.Series) -> pd.DataFrame:
    """Near-duplicates removed: rows equal on ``key`` within an asset-week count once with their highest
    materiality. Returns one row per group with ``value = sign * materiality``."""
    g = rows.assign(sign=sign).groupby(["friday", "base", *key], sort=False, observed=True)
    out = g.agg(materiality=("materiality", "max"), sign=("sign", "first")).reset_index()
    out["value"] = out["sign"] * out["materiality"]
    return out


def _sum(rows: pd.DataFrame, col: str, name: str) -> pd.Series:
    return rows.groupby(["friday", "base"])[col].sum().rename(name)


def block_b(reading: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    """Raw block-B features, the class-only variant and record counts per (friday, base) with any record."""
    rec = records[["doc_id", "base", "resolution", "relevance", "event_class", "status", "direction", "materiality"]]
    rows = reading.loc[reading["read"], ["friday", "decision", "doc_id", "base", "event_ts", "type"]].merge(
        rec, on=["doc_id", "base"], how="inner", validate="m:1")
    age = rows["decision"] - rows["event_ts"]
    rows = rows.assign(bucket=(age // WEEK).astype(int), recent=age < WEEK)
    unresolved = rows[rows["resolution"] == "unresolved"]
    subj = rows[(rows["resolution"] != "unresolved") & (rows["relevance"] == "subject")].copy()
    subj["materiality"] = subj["materiality"].astype(int)
    events, opinions = subj[subj["type"] == "event"], subj[subj["type"] == "analysis_opinion"]

    ev = _signed(events, ["event_class", "status", "direction", "bucket"], events["direction"].map(DIRECTION_SIGN))
    evc = _signed(events, ["event_class", "status", "bucket"], events["event_class"].map(CLASS_SIGN))
    supply = subj[subj["event_class"].isin(["token_supply_increase", "token_supply_reduction"])]
    sup = _signed(supply, ["event_class", "status", "direction", "bucket"],
                  supply["event_class"].map({"token_supply_increase": 1, "token_supply_reduction": -1}))
    stance = opinions[opinions["recent"]].assign(value=opinions["direction"].map(DIRECTION_SIGN))
    parts = [
        _sum(ev[ev["bucket"] == 0], "value", "tone_7d"),
        _sum(ev[ev["bucket"] >= 1], "value", "tone_30d"),
        _sum(ev[(ev["bucket"] == 0) & (ev["sign"] < 0)], "materiality", "unfav_7d"),
        _sum(ev[ev["status"] == "scheduled"], "value", "sched_fwd"),
        _sum(stance, "value", "stance_7d"),
        _sum(sup, "value", "supply_30d"),
        _sum(evc[evc["bucket"] == 0], "value", "tone_7d_c"),
        _sum(evc[evc["bucket"] >= 1], "value", "tone_30d_c"),
        _sum(evc[(evc["bucket"] == 0) & (evc["sign"] < 0)], "materiality", "unfav_7d_c"),
        _sum(evc[evc["status"] == "scheduled"], "value", "sched_fwd_c"),
        subj[subj["recent"]].groupby(["friday", "base"]).size().rename("n_subject_7d"),
        subj.groupby(["friday", "base"]).size().rename("n_subject_30d"),
        unresolved.groupby(["friday", "base"]).size().rename("n_unresolved_30d"),
    ]
    out = pd.concat(parts, axis=1).fillna(0.0).reset_index()
    return out.rename(columns={"friday": "date"})


def asset_week_features(items: pd.DataFrame, reading: pd.DataFrame, records: pd.DataFrame, top: pd.DataFrame,
                        store_start: pd.Timestamp) -> pd.DataFrame:
    """One row per universe row (date, symbol, base) with the raw features of both blocks, the class-only
    variant and the record counts. An asset without records has zero in every block-B column."""
    keys = top[["date", "symbol", "base"]].reset_index(drop=True)
    attn = attention(items, keys["date"].unique(), keys["base"].unique(), store_start)
    out = keys.merge(attn, on=["date", "base"], how="left", validate="m:1")
    out = out.merge(block_b(reading, records), on=["date", "base"], how="left", validate="m:1")
    cols = sorted(set(BLOCK_B) | set(BLOCK_B_CLASS) | set(COUNTS))
    out[cols] = out[cols].fillna(0.0)
    return out
