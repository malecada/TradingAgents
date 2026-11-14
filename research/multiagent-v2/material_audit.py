"""Facts about the text material of the reader agents (Charters 2 to 4). No outcome, no model call.

Inputs: the text store (``data/dossier/text``), the reading list (``data/reader/items.parquet``,
``docs.parquet``) and the decision-time panel of Charter 4 (``scripts/reader_charter4_null_gate.py panel``).

Usage: python material_audit.py <panel.parquet> <out.json>
"""
import glob
import json
import sys

import pandas as pd


def main(panel_path: str, out_path: str) -> None:
    out = {}
    items = pd.read_parquet("data/reader/items.parquet")
    docs = pd.read_parquet("data/reader/docs.parquet")
    one = items.drop_duplicates("doc_id")
    out["documents_by_outlet"] = {f"{s}/{o}": int(n) for (s, o), n in one.groupby(["source", "outlet"]).size().items()}
    out["typed_share_by_source"] = one.groupby("source")["typed"].mean().round(4).to_dict()
    news_rows = items[items["source"] == "wayback"].groupby("base").size().sort_values(ascending=False)
    out["news_item_rows"] = {"assets": int(len(news_rows)), "share_btc_eth": float(news_rows.head(2).sum() / news_rows.sum()),
                             "share_top10": float(news_rows.head(10).sum() / news_rows.sum())}
    words = docs["summary"].fillna("").str.split().str.len()
    out["summary_words"] = {str(q): float(words.quantile(q)) for q in (0.1, 0.5, 0.9)}

    news = pd.concat([pd.read_parquet(p, columns=["event_ts", "as_of_ts", "body"]) for p in sorted(glob.glob("data/dossier/text/wayback/202[234]/*.parquet"))])
    body = news["body"].fillna("").str.len()
    lag = (pd.to_datetime(news["as_of_ts"], utc=True) - pd.to_datetime(news["event_ts"], utc=True)).dt.total_seconds() / 3600
    out["news"] = {"articles": int(len(news)), "per_day": float(len(news) / 1096),
                   "body_chars": {str(q): float(body.quantile(q)) for q in (0.1, 0.5, 0.9)},
                   "hours_publication_to_capture": {str(q): float(lag.quantile(q)) for q in (0.25, 0.5, 0.75, 0.9)}}
    posts = pd.concat([pd.read_parquet(p, columns=["body"]) for p in sorted(glob.glob("data/dossier/text/reddit/202[234]/*.parquet"))])
    out["posts"] = {"rows": int(len(posts)), "title_only_share": float((posts["body"].fillna("").str.len() == 0).mean())}

    panel = pd.read_parquet(panel_path)
    panel["date"] = pd.to_datetime(panel["date"], utc=True)
    test = panel[panel["date"] >= "2023-01-07"]
    per = test.groupby("base").agg(days=("news_1d", "size"), news=("news_1d", lambda x: (x > 0).mean()),
                                   subject=("n_subject_1d", lambda x: (x > 0).mean()), tone=("tone_1d", lambda x: (x != 0).mean()))
    rest = per.drop(["BTC", "ETH"])
    toned = test[test["tone_1d"] != 0]
    out["test_days"] = {
        "assets": int(len(per)),
        "assets_without_any_fresh_subject_record": int((per["subject"] == 0).sum()),
        "assets_with_fresh_subject_record_on_5pct_of_days": int((per["subject"] >= 0.05).sum()),
        "btc": per.loc["BTC", ["news", "subject", "tone"]].round(4).to_dict(),
        "eth": per.loc["ETH", ["news", "subject", "tone"]].round(4).to_dict(),
        "other_assets_median": rest[["news", "subject", "tone"]].median().round(4).to_dict(),
        "other_assets_q90": rest[["news", "subject", "tone"]].quantile(0.9).round(4).to_dict(),
        "assets_of_50_with_tone_per_day": {"mean": float(test.groupby("date")["tone_1d"].apply(lambda x: (x != 0).sum()).mean()),
                                            "median": float(test.groupby("date")["tone_1d"].apply(lambda x: (x != 0).sum()).median())},
        "share_of_toned_rows_btc_eth": float(toned["base"].isin(["BTC", "ETH"]).mean()),
        "toned_rows": int(len(toned)),
    }
    json.dump(out, open(out_path, "w"), indent=1, sort_keys=True)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:3])
