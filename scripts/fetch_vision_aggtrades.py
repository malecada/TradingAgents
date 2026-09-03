"""Daily aggTrades from Binance Vision for an explicit (symbol, day) list (exec_pf P0 sample).

Idempotent: a (symbol, day) already on disk is skipped. Output
data/xsect/aggtrades/{SYM}-{YYYY-MM-DD}.parquet with columns
price (float64), qty (float64), ts (UTC), is_buyer_maker (bool); manifest
data/xsect/aggtrades_manifest.json.

Usage: python scripts/fetch_vision_aggtrades.py --sample data/rebuild/exec_pf/p0_sample.json
The sample file is {"days": [["BTCUSDT", "2023-03-15"], ...]}.
"""
from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/xsect/aggtrades"
MANIFEST = ROOT / "data/xsect/aggtrades_manifest.json"
URL = "https://data.binance.vision/data/futures/um/daily/aggTrades/{sym}/{sym}-aggTrades-{d}.zip"
COLS = ["agg_id", "price", "qty", "first_id", "last_id", "ts", "is_buyer_maker"]
HOLDOUT_START = pd.Timestamp("2025-04-01", tz="UTC")


def parse_zip(content: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        raw = z.read(z.namelist()[0])
    header = 0 if raw[:10].startswith(b"agg_trade") else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    df.columns = COLS[: df.shape[1]]
    ts = pd.to_numeric(df["ts"])
    if ts.max() > 1e14:
        ts = ts // 1000
    out = pd.DataFrame({
        "price": df["price"].astype("float64"),
        "qty": df["qty"].astype("float64"),
        "ts": pd.to_datetime(ts, unit="ms", utc=True),
        "is_buyer_maker": df["is_buyer_maker"].astype(str).str.lower().isin(["true", "1"]),
    })
    return out.sort_values("ts", kind="stable").reset_index(drop=True)


def fetch_day(sym: str, day: str) -> tuple[str, str, str]:
    path = OUT_DIR / f"{sym}-{day}.parquet"
    if path.exists():
        return sym, day, "cached"
    if pd.Timestamp(day, tz="UTC") >= HOLDOUT_START:
        return sym, day, "refused_holdout"
    for i in range(4):
        try:
            r = requests.get(URL.format(sym=sym, d=day), timeout=120)
        except requests.RequestException:
            time.sleep(2.0 * (i + 1))
            continue
        if r.status_code == 404:
            return sym, day, "not_found"
        if r.status_code == 200:
            df = parse_zip(r.content)
            df.to_parquet(path)
            return sym, day, f"ok:{len(df)}"
        time.sleep(2.0 * (i + 1))
    return sym, day, "failed"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    days = json.loads(Path(args.sample).read_text())["days"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(fetch_day, s, d) for s, d in days]
        for fut in as_completed(futs):
            sym, day, status = fut.result()
            manifest[f"{sym}-{day}"] = status
            print(f"{sym} {day}: {status} t={time.time()-t0:.0f}s", flush=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    n_ok = sum(1 for v in manifest.values() if v.startswith("ok") or v == "cached")
    print(f"done: {n_ok}/{len(days)} days on disk")


if __name__ == "__main__":
    main()
