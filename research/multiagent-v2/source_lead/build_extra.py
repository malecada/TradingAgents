"""Asset and time tables of two public X datasets for `lead_probe.py`. No text is hydrated; no price is read.

Inputs (downloaded by hand, outside version control, read as untrusted data: run with `python -I`):
  <raw>/tweets_hf/train.parquet           Hugging Face StephanAkkerman/financial-tweets-crypto (MIT)
  <raw>/x_cashtag/tweets_YYYY-MM.parquet  Hugging Face twitterapi-io/x-cashtag-mentions-2024-2026 (CC BY 4.0, IDs only)
Outputs: <extra>/x_trader_accounts_hf.parquet, x_cashtag_ids_2024.parquet, x_cashtag_ids_2024_original.parquet
Usage: python -I build_extra.py <events.parquet> <raw dir> <extra dir>
"""
import re
import sys
from pathlib import Path

import pandas as pd

SNOWFLAKE_EPOCH_MS = 1288834974657          # post time in milliseconds = (id >> 22) + epoch


def main(events_path: str, raw: str, extra: str) -> int:
    bases = set(pd.read_parquet(events_path, columns=["base"])["base"])
    raw_dir, out = Path(raw), Path(extra)
    out.mkdir(parents=True, exist_ok=True)

    d = pd.read_parquet(raw_dir / "tweets_hf/train.parquet", columns=["created_at", "tickers"])
    d["ts"] = pd.to_datetime(d["created_at"], utc=True)

    def to_bases(tickers) -> list[str]:
        found = set()
        for x in ([] if tickers is None else tickers):
            x = re.sub(r"^1000+", "", re.sub(r"(USDT|USD|BUSD|PERP|/.*)$", "", str(x).upper().lstrip("$")))
            if x in bases:
                found.add(x)
        return sorted(found)

    d["base"] = d["tickers"].map(to_bases)
    x = d.explode("base").dropna(subset=["base"])[["base", "ts"]]
    x = x[(x["ts"] >= "2022-06-01") & (x["ts"] < "2025-03-01")]
    x.to_parquet(out / "x_trader_accounts_hf.parquet", index=False)
    print("x_trader_accounts_hf", len(x))

    frames = []
    for path in sorted((raw_dir / "x_cashtag").glob("tweets_*.parquet")):
        c = pd.read_parquet(path, columns=["tweet_id", "cashtags", "type", "collection"])
        c = c[c["collection"].map(lambda v: "cashtag_search" in list(v))]      # the query family that ran all period
        c = c.explode("cashtags").rename(columns={"cashtags": "base", "tweet_id": "doc_id"})
        c = c[c["base"].isin(bases)]
        c["ts"] = pd.to_datetime((c["doc_id"].astype("int64") // (1 << 22)) + SNOWFLAKE_EPOCH_MS, unit="ms", utc=True)
        frames.append(c[["doc_id", "base", "ts", "type"]])
    ids = pd.concat(frames, ignore_index=True)
    ids[["doc_id", "base", "ts"]].to_parquet(out / "x_cashtag_ids_2024.parquet", index=False)
    ids[ids["type"] == "original"][["doc_id", "base", "ts"]].to_parquet(out / "x_cashtag_ids_2024_original.parquet", index=False)
    print("x_cashtag_ids_2024", len(ids), "original", int((ids["type"] == "original").sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
