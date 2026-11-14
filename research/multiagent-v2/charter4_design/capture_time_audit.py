"""Capture-time audit for a daily decision (Charter 4 preparation). No price bar and no outcome is read.

Inputs: the item, document and record tables of the reader store and the weekly universe of the card panel.
A decision is taken at 00:00 UTC of day D; the universe of D is the top 50 of the last Friday before D. An item is
admissible at D when its as_of_ts lies before D, and "fresh" when it became observable in the 24 hours before D.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tradingagents.reader import charter2, reading  # noqa: E402

DAY = pd.Timedelta(days=1)
OUT = Path(__file__).with_name("capture_time_audit.json")


def q(series: pd.Series, qs=(0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99)) -> dict:
    return {f"q{int(p * 100):02d}": round(float(series.quantile(p)), 2) for p in qs}


def main() -> None:
    items = pd.read_parquet(ROOT / "data/reader/items.parquet")
    docs = pd.read_parquet(ROOT / "data/reader/docs.parquet")
    records = pd.read_parquet(ROOT / "data/reader/records.parquet")
    top = charter2.universe(pd.read_parquet(ROOT / "data/llm_rank_xs/cards.parquet"))
    items = reading.flag_items(items, docs)
    out: dict = {"items": int(len(items)), "documents": int(items["doc_id"].nunique())}

    # 1. time stamps per source
    res = {}
    for source, g in items.drop_duplicates("doc_id").groupby("source"):
        ev, asof = g["event_ts"], g["as_of_ts"]
        res[source] = {
            "documents": int(len(g)),
            "event_at_midnight": round(float(((ev.dt.hour == 0) & (ev.dt.minute == 0) & (ev.dt.second == 0)).mean()), 4),
            "as_of_equals_event": round(float((asof == ev).mean()), 4),
            "as_of_before_event": round(float((asof < ev).mean()), 4),
        }
    out["timestamps"] = res

    # 2. capture lag of the news articles: first capture minus 00:00 UTC of the publication date
    news = items[items["source"] == "wayback"].drop_duplicates("doc_id").copy()
    news["lag_h"] = (news["as_of_ts"] - news["event_ts"]).dt.total_seconds() / 3600.0
    news["year"] = news["event_ts"].dt.year
    lag = {"all": {**q(news["lag_h"]), "n": int(len(news))}}
    for key, g in news.groupby("outlet"):
        lag[f"outlet:{key}"] = {**q(g["lag_h"]), "n": int(len(g))}
    for key, g in news.groupby("year"):
        lag[f"year:{key}"] = {**q(g["lag_h"]), "n": int(len(g))}
    for key, g in news.groupby(["outlet", "year"]):
        lag[f"{key[0]}:{key[1]}"] = {"q50": round(float(g["lag_h"].median()), 2), "within_24h": round(float((g["lag_h"] <= 24).mean()), 3),
                                     "within_48h": round(float((g["lag_h"] <= 48).mean()), 3), "n": int(len(g))}
    out["news_capture_lag_hours"] = lag
    out["news_capture_within"] = {f"{h}h": round(float((news["lag_h"] <= h).mean()), 4) for h in (0, 12, 24, 36, 48, 72, 168, 720)}
    out["news_capture_hour_utc"] = {int(h): int(n) for h, n in news["as_of_ts"].dt.hour.value_counts().sort_index().items()}
    reddit = items[items["source"] == "reddit"].drop_duplicates("doc_id")
    out["reddit_created_hour_utc"] = {int(h): int(n) for h, n in reddit["event_ts"].dt.hour.value_counts().sort_index().items()}

    # 3. the daily panel: decision at 00:00 UTC of D, universe of the last Friday before D
    fridays = pd.DatetimeIndex(sorted(pd.to_datetime(top["date"].unique(), utc=True)))
    members = {f: set(top.loc[pd.to_datetime(top["date"], utc=True) == f, "base"]) for f in fridays}
    days = pd.date_range(fridays[0] + DAY, pd.Timestamp("2024-12-31", tz="UTC"), freq="D")
    friday_of = {d: fridays[fridays < d][-1] for d in days}
    later = {f: [g for g in fridays if f < g] for f in fridays}

    rec = records[(records["resolution"] != "unresolved")][["doc_id", "base", "relevance", "event_class", "direction", "materiality"]]
    it = items.merge(rec, on=["doc_id", "base"], how="left")
    it["has_record"] = it["relevance"].notna()
    it["subject"] = it["relevance"] == "subject"
    it["day"] = it["as_of_ts"].dt.floor("D") + DAY          # the first decision that may use the item
    it["pub_lag_d"] = (it["day"] - it["event_ts"].dt.floor("D")).dt.days   # 1 = captured on the publication date
    it = it[(it["day"] >= days[0]) & (it["day"] <= days[-1])]
    it["friday"] = it["day"].map(friday_of)
    it["member"] = [b in members[f] for b, f in zip(it["base"], it["friday"])]
    fresh = it[it["member"]].copy()
    fresh["year"] = fresh["day"].dt.year
    fresh["dow"] = fresh["day"].dt.dayofweek            # 5 = Saturday decision (the weekly decision time)
    out["days"] = {"first": str(days[0].date()), "last": str(days[-1].date()), "n": int(len(days)), "asset_days": int(len(days) * 50)}

    def coverage(g: pd.DataFrame) -> dict:
        keys = ["day", "base"]
        n_days = g["day"].nunique()
        return {"item_rows": int(len(g)), "asset_days_with_item": int(g.drop_duplicates(keys).shape[0]),
                "typed": round(float(g["typed"].mean()), 4), "read_rule": round(float(g["read"].mean()), 4),
                "has_record": round(float(g["has_record"].mean()), 4),
                "asset_days_with_subject_record": int(g[g["subject"]].drop_duplicates(keys).shape[0]),
                "days_with_item": int(n_days)}

    cov = {}
    for source, g in fresh.groupby("source"):
        cov[source] = {"all": coverage(g)}
        for year, gy in g.groupby("year"):
            cov[source][f"year:{year}"] = coverage(gy)
        for dow, gd in g.groupby("dow"):
            cov[source][f"dow:{dow}"] = coverage(gd)
    out["fresh_items_of_members"] = cov

    # 4. news: why a fresh item of a member has no typing
    fn = fresh[fresh["source"] == "wayback"].copy()
    fn["member_later"] = [any(b in members[g] for g in later[f][:5]) for b, f in zip(fn["base"], fn["friday"])]
    fn["member_next"] = [bool(later[f]) and b in members[later[f][0]] for b, f in zip(fn["base"], fn["friday"])]
    out["news_untyped"] = {
        "fresh_rows": int(len(fn)), "untyped": int((~fn["typed"]).sum()),
        "untyped_member_at_a_later_friday": int((~fn["typed"] & fn["member_later"]).sum()),
        "untyped_not_member_at_the_next_five_fridays": int((~fn["typed"] & ~fn["member_later"]).sum()),
        "typed_share_when_member_next_friday": round(float(fn.loc[fn["member_next"], "typed"].mean()), 4),
        "typed_share_when_not_member_next_friday": round(float(fn.loc[~fn["member_next"], "typed"].mean()), 4),
        "rows_not_member_next_friday": int((~fn["member_next"]).sum()),
        "by_publication_lag_days": {int(k): {"rows": int(len(g)), "typed": round(float(g["typed"].mean()), 4)}
                                    for k, g in fn.assign(k=fn["pub_lag_d"].clip(upper=8)).groupby("k")},
    }
    # the last days of the window have no later Friday inside the store: typed share by week of the window end
    tail = fn[fn["day"] >= pd.Timestamp("2024-12-01", tz="UTC")]
    out["news_untyped"]["december_2024_by_week"] = {str(k.date()): {"rows": int(len(g)), "typed": round(float(g["typed"].mean()), 4)}
                                                    for k, g in tail.groupby("friday")}

    # 5. fresh news per asset-day and per day
    def per_day(g: pd.DataFrame, name: str) -> dict:
        n = g.drop_duplicates(["day", "base"]).groupby("day").size().reindex(days, fill_value=0)
        return {f"{name}_assets_per_day": {**q(n, (0.05, 0.25, 0.5, 0.75, 0.95)), "mean": round(float(n.mean()), 2),
                                           "days_with_none": int((n == 0).sum()), "days_with_fewer_than_3": int((n < 3).sum())},
                f"{name}_asset_day_share": round(float(n.sum() / (len(days) * 50)), 4)}

    dens = {}
    dens.update(per_day(fresh, "any_item"))
    dens.update(per_day(fresh[fresh["source"] == "reddit"], "community_item"))
    dens.update(per_day(fn, "news_item"))
    dens.update(per_day(fn[fn["pub_lag_d"] <= 2], "news_item_published_within_2d"))
    dens.update(per_day(fn[fn["has_record"]], "news_record"))
    dens.update(per_day(fn[fn["subject"]], "news_subject_record"))
    ev = fn[fn["subject"] & (fn["type"] == "event")]
    dens.update(per_day(ev, "news_subject_event"))
    dens.update(per_day(ev[ev["direction"].isin(["favourable", "unfavourable"])], "news_subject_event_directed"))
    dens.update(per_day(ev[ev["pub_lag_d"] <= 2], "news_subject_event_published_within_2d"))
    for year, g in ev.groupby("year"):
        dens.update(per_day(g, f"news_subject_event_{year}"))
    out["density"] = dens
    by_base = ev.drop_duplicates(["day", "base"]).groupby("base").size().sort_values(ascending=False)
    out["news_subject_event_asset_days_by_base"] = {"top10": {k: int(v) for k, v in by_base.head(10).items()},
                                                    "assets": int(len(by_base)),
                                                    "share_of_top2": round(float(by_base.head(2).sum() / by_base.sum()), 4),
                                                    "share_of_top10": round(float(by_base.head(10).sum() / by_base.sum()), 4)}
    out["news_subject_event_direction"] = {k: int(v) for k, v in ev["direction"].value_counts().items()}
    out["news_subject_event_class"] = {k: int(v) for k, v in ev["event_class"].value_counts().items()}
    out["news_subject_event_materiality"] = {int(k): int(v) for k, v in ev["materiality"].value_counts().items()}

    # 6. community posts: does a record exist for a fresh post, by weekday of the decision and by post flow
    fr = fresh[(fresh["source"] == "reddit") & (fresh["salience"] == "primary")].copy()
    flow = fr.groupby(["friday", "base"]).size().rename("posts_in_week")
    fr = fr.join(flow, on=["friday", "base"])
    fr["flow"] = pd.cut(fr["posts_in_week"], [0, 5, 25, 100, 10**6], labels=["1-5", "6-25", "26-100", "over 100"])
    out["community_typed_by_weekday_and_flow"] = {
        str(k): {int(d): {"rows": int(len(g)), "typed": round(float(g["typed"].mean()), 3)} for d, g in gk.groupby("dow")}
        for k, gk in fr.groupby("flow", observed=True)}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
