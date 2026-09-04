"""Bybit linear USDT-perp 1h kline store for liq_fade_v1 (charter 2026-09-04). DATA ONLY.

  nohup python scripts/predlab_bybit_fetch_1h.py --end 2025-03-31 >> data/predlab/bybit/fetch_1h.log 2>&1 &

Symbols = every symbol in the existing daily store (data/predlab/bybit/klines,
735 files, enumerated 2026-08-06 incl. non-Trading). Idempotent: a symbol whose
parquet already reaches `end` is skipped. Output
data/predlab/bybit/klines_1h/{SYMBOL}.parquet (open/high/low/close/volume/
turnover, UTC open-time index) + klines_1h_manifest.json. End is clipped to
2025-03-31 (dev-only cycle; the sealed window is not fetched).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from predlab_bybit_fetch import PAUSE, STORE, _get  # noqa: E402

OUT = STORE / "klines_1h"
MANIFEST = STORE / "klines_1h_manifest.json"
CAP = pd.Timestamp("2025-03-31 23:00", tz="UTC")


def fetch_klines_1h(symbol: str, end_ms: int) -> "pd.DataFrame | None":
    rows: list[list] = []
    end = end_ms
    while True:
        res = _get("/v5/market/kline", category="linear", symbol=symbol, interval="60", limit=1000, end=end)
        chunk = res["list"]
        if not chunk:
            break
        rows.extend(chunk)
        oldest = int(chunk[-1][0])
        if len(chunk) < 1000:
            break
        end = oldest - 1
        time.sleep(PAUSE)
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume", "turnover"]).astype({"ts": "int64"})
    df.index = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.drop(columns="ts").astype(float).sort_index()
    df.index.name = "ts"
    return df[~df.index.duplicated(keep="last")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--end", default="2025-03-31")
    ap.add_argument("--limit-syms", type=int, default=0)
    args = ap.parse_args()
    end_ts = min(pd.Timestamp(args.end, tz="UTC") + pd.Timedelta(hours=23), CAP)
    end_ms = int(end_ts.timestamp() * 1000)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    syms = sorted(p.stem for p in (STORE / "klines").glob("*.parquet"))
    if args.limit_syms:
        syms = syms[: args.limit_syms]
    t0 = time.time()
    for i, sym in enumerate(syms):
        path = OUT / f"{sym}.parquet"
        if path.exists() and sym in manifest and manifest[sym].get("complete"):
            continue
        try:
            df = fetch_klines_1h(sym, end_ms)
        except Exception as exc:
            print(f"[{i+1}/{len(syms)}] {sym}: ERROR {exc}", flush=True)
            continue
        if df is None or df.empty:
            manifest[sym] = {"rows": 0, "complete": True}
            print(f"[{i+1}/{len(syms)}] {sym}: no data", flush=True)
        else:
            df = df.loc[df.index <= CAP]
            df.to_parquet(path)
            manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()), "rows": int(len(df)), "complete": True}
            print(f"[{i+1}/{len(syms)}] {sym}: {len(df)} bars {df.index.min().date()} -> {df.index.max().date()} t={time.time()-t0:.0f}s", flush=True)
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        time.sleep(PAUSE)
    print(f"done: {len(manifest)} symbols in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
