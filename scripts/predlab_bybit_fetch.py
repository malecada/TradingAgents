"""Bybit USDT-perp daily store builder for the champion venue replication
(predlab_bybit_r1). DATA ONLY — no strategy computation lives here; the
replication itself is gated behind a frozen registration (house rule).

Fetches, for every linear USDT perpetual Bybit will enumerate (including
non-Trading statuses where the API still serves history):
  - daily klines (open/high/low/close/volume/turnover) from listing
  - full 8-hourly funding-rate history
into data/predlab/bybit/{klines,funding}/SYMBOL.parquet + manifest.json.

Idempotent: symbols with an up-to-date parquet are skipped, so the script
can be re-run after interruptions. Survivorship note: whether Bybit serves
klines for delisted contracts is probed and recorded in the manifest —
this feeds the P1 coverage probe of the registration.

Usage:  python scripts/predlab_bybit_fetch.py [--end 2026-07-01] [--limit-syms N]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
STORE = DATA_ROOT / "predlab" / "bybit"
API = "https://api.bybit.com"
PAUSE = 0.15  # ~6-7 req/s, well under Bybit public limits


def _get(path: str, **params) -> dict:
    import urllib.parse
    import urllib.request

    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                out = json.load(r)
            if out.get("retCode") == 0:
                return out["result"]
            if out.get("retCode") in (10006, 10018):  # rate limited
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"{path}: retCode {out.get('retCode')} {out.get('retMsg')}")
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def enumerate_symbols() -> "list[dict]":
    """All linear USDT perps, any status, paginated."""
    out, cursor = [], ""
    while True:
        res = _get("/v5/market/instruments-info", category="linear",
                   limit=1000, cursor=cursor)
        for s in res["list"]:
            if (s["quoteCoin"] == "USDT"
                    and s.get("contractType") == "LinearPerpetual"):
                out.append({"symbol": s["symbol"], "status": s["status"],
                            "launchTime": int(s.get("launchTime") or 0)})
        cursor = res.get("nextPageCursor") or ""
        if not cursor:
            break
        time.sleep(PAUSE)
    return out


def fetch_klines(symbol: str, end_ms: int) -> "pd.DataFrame | None":
    """Daily klines from listing to end, paginating backwards (1000/page)."""
    rows: "list[list]" = []
    end = end_ms
    while True:
        res = _get("/v5/market/kline", category="linear", symbol=symbol,
                   interval="D", limit=1000, end=end)
        chunk = res["list"]  # newest-first: [start, o, h, l, c, vol, turnover]
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
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close",
                                     "volume", "turnover"])
    df = df.astype({"ts": "int64"})
    df.index = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.drop(columns="ts").astype(float).sort_index()
    return df[~df.index.duplicated(keep="last")]


def fetch_funding(symbol: str, end_ms: int) -> "pd.DataFrame | None":
    rows: "list[dict]" = []
    end = end_ms
    while True:
        res = _get("/v5/market/funding/history", category="linear",
                   symbol=symbol, limit=200, endTime=end)
        chunk = res["list"]  # newest-first
        if not chunk:
            break
        rows.extend(chunk)
        oldest = int(chunk[-1]["fundingRateTimestamp"])
        if len(chunk) < 200:
            break
        end = oldest - 1
        time.sleep(PAUSE)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["fundingRateTimestamp"].astype("int64"),
                              unit="ms", utc=True)
    df = df[["fundingRate"]].astype(float).sort_index()
    return df[~df.index.duplicated(keep="last")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--end", default="2026-07-01",
                    help="panel end date (matches sealed Binance panels)")
    ap.add_argument("--limit-syms", type=int, default=0)
    args = ap.parse_args()
    end_ms = int(pd.Timestamp(args.end, tz="UTC").timestamp() * 1000)

    (STORE / "klines").mkdir(parents=True, exist_ok=True)
    (STORE / "funding").mkdir(parents=True, exist_ok=True)

    syms = enumerate_symbols()
    print(f"enumerated {len(syms)} linear USDT perps "
          f"({sum(1 for s in syms if s['status'] != 'Trading')} non-Trading)",
          flush=True)
    # Bybit only enumerates LIVE contracts; its kline API still serves some
    # delisted symbols by name. Probe every symbol known from the Binance
    # survivorship-safe store as a partial delisting recovery (disclosed as
    # a P1 survivorship caveat — Bybit-only delistings remain unrecoverable).
    listed = {s["symbol"] for s in syms}
    binance_store = DATA_ROOT / "xsect" / "klines"
    extra = sorted(p.stem for p in binance_store.glob("*.parquet")
                   if p.stem not in listed) if binance_store.exists() else []
    syms += [{"symbol": x, "status": "probe-delisted", "launchTime": 0}
             for x in extra]
    print(f"+{len(extra)} Binance-known symbols probed for delisted history",
          flush=True)
    if args.limit_syms:
        syms = syms[:args.limit_syms]

    manifest = {"fetched_utc": datetime.now(timezone.utc).isoformat(),
                "end": args.end, "n_enumerated": len(syms),
                "symbols": {}}
    for i, s in enumerate(syms):
        sym = s["symbol"]
        kp = STORE / "klines" / f"{sym}.parquet"
        fp = STORE / "funding" / f"{sym}.parquet"
        if kp.exists() and fp.exists():
            manifest["symbols"][sym] = {"status": s["status"], "skipped": True}
            continue
        try:
            kl = fetch_klines(sym, end_ms)
            if kl is not None and len(kl):
                kl.to_parquet(kp)
            fu = fetch_funding(sym, end_ms)
            if fu is not None and len(fu):
                fu.to_parquet(fp)
            manifest["symbols"][sym] = {
                "status": s["status"],
                "kline_days": 0 if kl is None else int(len(kl)),
                "kline_start": None if kl is None or not len(kl)
                else str(kl.index[0].date()),
                "funding_prints": 0 if fu is None else int(len(fu)),
            }
        except Exception as e:  # record and continue — coverage probe will judge
            manifest["symbols"][sym] = {"status": s["status"], "error": str(e)}
        if i % 20 == 0:
            print(f"[{i}/{len(syms)}] {sym}", flush=True)
            (STORE / "manifest.json").write_text(json.dumps(manifest, indent=1))
        time.sleep(PAUSE)

    (STORE / "manifest.json").write_text(json.dumps(manifest, indent=1))
    ok = sum(1 for v in manifest["symbols"].values() if v.get("kline_days"))
    print(f"done: {ok} symbols with klines; manifest written", flush=True)


if __name__ == "__main__":
    main()
