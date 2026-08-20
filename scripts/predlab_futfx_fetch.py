"""Futures/FX daily store builder for xasset_futfx_r1. DATA ONLY.

Frozen universe (registered): ~72 liquid instruments —
  FX: G10 USD pairs + liquid deliverable EM + major crosses (yahoo "=X",
      spot; NO volume; interest-carry caveat registered)
  Futures: CME/CBOT/NYMEX/ICE front-month continuous (yahoo "=F";
      roll-splice caveat registered)
Store: data/xsect_futfx/bars/SYMBOL.parquet + manifest.json. Idempotent.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORE = PROJECT_ROOT / "data" / "xsect_futfx"
START, END = "2016-01-01", "2026-08-14"

FX = [
    "EURUSD=X", "GBPUSD=X", "JPY=X", "CHF=X", "CAD=X", "AUDUSD=X",
    "NZDUSD=X", "SEK=X", "NOK=X", "DKK=X", "PLN=X", "HUF=X", "CZK=X",
    "TRY=X", "ZAR=X", "MXN=X", "SGD=X", "HKD=X", "THB=X", "ILS=X",
    "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURSEK=X", "EURNOK=X",
    "EURPLN=X", "EURHUF=X", "EURCZK=X", "EURAUD=X", "EURCAD=X",
    "GBPJPY=X", "AUDJPY=X", "CHFJPY=X", "CADJPY=X", "NZDJPY=X",
    "GBPCHF=X", "AUDNZD=X",
]
FUT = [
    "ES=F", "NQ=F", "YM=F", "RTY=F",
    "ZB=F", "ZN=F", "ZF=F", "ZT=F",
    "GC=F", "SI=F", "HG=F", "PL=F", "PA=F",
    "CL=F", "BZ=F", "NG=F", "HO=F", "RB=F",
    "ZC=F", "ZS=F", "ZW=F", "ZM=F", "ZL=F", "KE=F", "ZO=F", "ZR=F",
    "CT=F", "KC=F", "SB=F", "CC=F", "OJ=F",
    "LE=F", "HE=F", "GF=F", "DX=F",
]


def fetch(sym: str) -> "pd.DataFrame":
    r = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
        params={"period1": int(pd.Timestamp(START).timestamp()),
                "period2": int(pd.Timestamp(END).timestamp()) + 86400,
                "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({
        "date": pd.to_datetime(res["timestamp"], unit="s", utc=True).normalize()
                  .tz_localize(None),
        "open": q["open"], "high": q["high"], "low": q["low"],
        "close": q["close"], "volume": q["volume"],
    }).dropna(subset=["high", "low", "close"])
    return df.drop_duplicates("date", keep="last").sort_values("date")


def main() -> int:
    bars = STORE / "bars"
    bars.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for sym in FX + FUT:
        safe = sym.replace("=", "_")
        fp = bars / f"{safe}.parquet"
        if fp.exists():
            df = pd.read_parquet(fp)
        else:
            try:
                df = fetch(sym)
            except Exception as e:
                print(sym, "ERROR", e)
                continue
            df.to_parquet(fp, index=False)
            time.sleep(0.5)
        hl_same = float((df["high"] == df["low"]).mean())
        manifest[sym] = {"kind": "fx" if sym.endswith("=X") else "fut",
                         "n_bars": int(len(df)),
                         "first": str(df["date"].iloc[0].date()),
                         "last": str(df["date"].iloc[-1].date()),
                         "frac_h_eq_l": hl_same}
        print(f"{sym}: {len(df)} bars, h==l {hl_same:.1%}")
    (STORE / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("DONE", len(manifest), "instruments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
