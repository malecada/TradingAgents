"""Coverage of the Charter 4 universe by Binance announcement titles (no outcome column is read).

Usage: python bn_coverage.py <panel.parquet> <out.json> <list.jsonl> [<list.jsonl> ...]
Only the columns `date` and `base` of the panel are read.
"""
import collections, json, re, sys
import pandas as pd

QUOTES = {"USDT", "BUSD", "USDC", "FDUSD", "TUSD", "BTC", "ETH", "BNB", "TRY", "EUR", "BRL", "DAI", "USD", "GBP", "AUD", "RUB", "UAH", "BIDR", "JPY", "ARS", "MXN", "PLN", "RON", "ZAR", "IDRT", "NGN", "VAI", "AEUR", "USDP", "UST"}
NAMES = {48: "new listing", 161: "delisting", 128: "airdrop", 157: "maintenance", 49: "latest news"}

panel = pd.read_parquet(sys.argv[1], columns=["date", "base"])
panel["date"] = pd.to_datetime(panel["date"], utc=True)
bases = sorted(panel["base"].unique())
norm = {b: re.sub(r"^1000+", "", b) for b in bases}          # 1000SHIB -> SHIB
by_token = collections.defaultdict(list)
for b, t in norm.items():
    by_token[t].append(b)

rows = []
for path in sys.argv[3:]:
    rows += [json.loads(line) for line in open(path)]
ann = pd.DataFrame(rows).drop_duplicates("id")
ann["ts"] = pd.to_datetime(ann["release_ms"], unit="ms", utc=True)
ann = ann[(ann["ts"] >= "2022-01-01") & (ann["ts"] < "2025-01-01")].copy()

def tickers(title: str) -> set[str]:
    found = set()
    for tok in re.findall(r"[A-Z0-9]{2,12}", title):
        cands = [tok]
        for q in QUOTES:                                       # ABCUSDT -> ABC
            if tok.endswith(q) and len(tok) > len(q) + 1:
                cands.append(tok[: -len(q)])
        for c in cands:
            c = re.sub(r"^1000+", "", c)
            if c in by_token and c not in QUOTES:
                found.update(by_token[c])
    for m in re.findall(r"\b(BTC|ETH|BNB)\b(?!\s*/)(?!-)", title):   # majors only when not a quote leg
        if not re.search(r"/\s*" + m, title) and m in by_token:
            found.update(by_token[m])
    return found

ann["bases"] = ann["title"].map(tickers)
ann["n_bases"] = ann["bases"].map(len)
out = {"window": "2022-01-01..2024-12-31", "universe_bases": len(bases), "catalogs": {}}
for cid, g in ann.groupby("catalog"):
    out["catalogs"][NAMES.get(cid, str(cid))] = {
        "announcements": int(len(g)), "per_day": round(len(g) / 1096, 2),
        "title_names_universe_asset": int((g["n_bases"] > 0).sum()),
        "share": round(float((g["n_bases"] > 0).mean()), 3)}

ex = ann[ann["n_bases"] > 0].explode("bases").rename(columns={"bases": "base"})[["base", "ts", "catalog"]]
test = panel[panel["date"] >= "2023-01-01"].copy()
days = sorted(test["date"].unique())
ex["date"] = (ex["ts"] + pd.Timedelta(days=1)).dt.normalize()   # released on the day before the 00:00 UTC decision
def coverage(sub, label):
    key = set(zip(sub["base"], sub["date"]))
    test["hit"] = [(b, d) in key for b, d in zip(test["base"], test["date"])]
    per_asset = test.groupby("base")["hit"].mean()
    per_day = test.groupby("date")["hit"].sum()
    majors = {b: round(float(per_asset.get(b, 0)), 3) for b in ("BTC", "ETH")}
    others = per_asset.drop(labels=[b for b in ("BTC", "ETH") if b in per_asset.index])
    return {"label": label, "asset_days": int(len(test)), "asset_days_with_announcement": int(test["hit"].sum()),
            "share_asset_days": round(float(test["hit"].mean()), 4), "majors": majors,
            "other_assets_median_share": round(float(others.median()), 4), "other_assets_q90_share": round(float(others.quantile(0.9)), 4),
            "assets_total": int(per_asset.size), "assets_with_any": int((per_asset > 0).sum()),
            "assets_on_5pct_of_days": int((per_asset >= 0.05).sum()),
            "median_assets_per_day": float(per_day.median()), "days_with_any": round(float((per_day > 0).mean()), 3)}
out["test_days"] = len(days)
out["coverage_prev_day"] = [coverage(ex, "all catalogs"), coverage(ex[ex["catalog"].isin([48, 161, 128, 157])], "listing, delisting, airdrop, maintenance")]
ex7 = pd.concat([ex.assign(date=ex["date"] + pd.Timedelta(days=k)) for k in range(7)])
out["coverage_prev_7_days"] = [coverage(ex7, "all catalogs")]
out["examples"] = ann[ann["n_bases"] > 0].sample(12, random_state=7)[["catalog", "ts", "title"]].assign(ts=lambda d: d["ts"].dt.strftime("%Y-%m-%d %H:%M")).values.tolist()
hours = ann["ts"].dt.hour.value_counts(normalize=True).sort_index()
out["release_hour_utc_share"] = {"00-07": round(float(hours.loc[0:7].sum()), 3), "08-15": round(float(hours.loc[8:15].sum()), 3), "16-23": round(float(hours.loc[16:23].sum()), 3)}
json.dump(out, open(sys.argv[2], "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != "examples"}, indent=1, default=str))
for e in out["examples"]:
    print(e)
