"""US-equity daily store builder for the champion cross-asset replication
(xasset_equity_r1). DATA ONLY — no strategy computation lives here; the
replication itself is gated behind the frozen registration (house rule).

Universe pool (survivorship-safe, composite — pre-result amendment
2026-08-18 declared in gates.json): Alpaca /v2/assets alone PURGES major
delistings (BBBY/SIVB/FRC/TWTR/ATVI absent; recycled tickers like FB now
resolve to unrelated ETFs), so enumeration is the union of
  (1) Alpaca /v2/assets us_equity active+inactive (no exchange filter —
      16K inactive carry OTC as their *last* exchange; top-200 dollar-
      volume membership self-selects the listed liquid phase anyway),
      with `_DELISTED`-suffixed records mapped back to their base symbol;
  (2) S&P 500 ever-members 2016+ (fja05680/sp500 ticker_start_end);
  (3) SEC company_tickers.json.
Warrant/right/unit symbol shapes and ETF/fund name-heuristic matches are
excluded (frozen lists below). The bars API is then probed for every
candidate; empties recorded. Residual caveat (disclosed): pre-2023
delistings outside S&P500/SEC-current enumeration may be missing;
coverage is gated by feasibility_P1.deaths.

Bars: Alpaca SIP daily klines, adjustment=all (split+dividend adjusted;
Parkinson ln(high/low) is invariant to multiplicative adjustment). Window
2016-01-01 .. 2026-08-14; 2016 is burn-in only per registration.

Store: data/xsect_equity/bars/SYMBOL.parquet + manifest.json.
Idempotent: symbols with an existing parquet (or recorded empty) are
skipped, so the script can be re-run after interruptions.

Usage: python scripts/predlab_xasset_fetch.py [--limit-syms N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
STORE = DATA_ROOT / "xsect_equity"
KEYS = Path("/home/malecada/master_thesis/keys")

DATA_API = "https://data.alpaca.markets"
ASSET_API = "https://paper-api.alpaca.markets"  # live api 401s on assets for this key
START, END = "2016-01-01", "2026-08-14"

# Frozen ETF/fund name heuristic (case-insensitive substring):
FUND_NAME_PAT = re.compile(
    r"\bETF\b|\bETN\b|iShares|SPDR|ProShares|Direxion|WisdomTree|Vanguard|"
    r"Invesco|Xtrackers|VanEck|Global X|First Trust| Fund\b|Index Trust|"
    r"Ultra(Pro|Short)|2x |3x |1\.5x ",
    re.IGNORECASE,
)
# Symbol shape: 1-5 letters, optional ".X" share class; 5-letter roots ending
# W/R/U (warrant/right/unit) excluded.
SYM_OK = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


def _headers() -> dict:
    return {
        "APCA-API-KEY-ID": (KEYS / "alpaca_key.txt").read_text().strip(),
        "APCA-API-SECRET-KEY": (KEYS / "alpaca_secret.txt").read_text().strip(),
    }


def sym_eligible(sym: str, name: str = "") -> bool:
    root = sym.split(".")[0]
    if not SYM_OK.match(sym):
        return False
    if len(root) == 5 and root[-1] in "WRU":
        return False
    if name and FUND_NAME_PAT.search(name):
        return False
    return True


def enumerate_assets(sess: requests.Session) -> "list[dict]":
    """Composite candidate pool; see module docstring. Dedup by symbol."""
    pool: "dict[str, dict]" = {}

    def add(sym: str, status: str, exchange: "str|None", name: str, src: str):
        if not sym_eligible(sym, name):
            return
        if sym not in pool:
            pool[sym] = {"symbol": sym, "_status": status,
                         "exchange": exchange, "name": name, "_src": src}

    for status in ("active", "inactive"):
        r = sess.get(f"{ASSET_API}/v2/assets",
                     params={"status": status, "asset_class": "us_equity"},
                     headers=_headers(), timeout=60)
        r.raise_for_status()
        for a in r.json():
            sym = a["symbol"]
            if sym.endswith("_DELISTED"):
                sym = sym[: -len("_DELISTED")]
            add(sym, status, a.get("exchange"), a.get("name") or "", "alpaca")

    sp = pd.read_csv(STORE / "sp500_ticker_start_end.csv")
    sp["end_date"] = sp["end_date"].fillna("9999-12-31")
    for _, row in sp[sp["end_date"] >= "2016-01-01"].iterrows():
        add(str(row["ticker"]).replace("-", "."), "sp500_ever", None, "", "sp500")

    sec = json.loads((STORE / "sec_company_tickers.json").read_text())
    for rec in sec.values():
        add(str(rec["ticker"]).replace("-", "."), "sec", None,
            rec.get("title") or "", "sec")

    return list(pool.values())


def fetch_bars(sess: requests.Session, symbol: str) -> "pd.DataFrame":
    rows, token = [], None
    while True:
        params = {"timeframe": "1Day", "start": START, "end": END,
                  "limit": 10000, "adjustment": "all", "feed": "sip"}
        if token:
            params["page_token"] = token
        for attempt in range(6):
            r = sess.get(f"{DATA_API}/v2/stocks/{symbol}/bars",
                         params=params, headers=_headers(), timeout=60)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            break
        if r.status_code == 404:  # symbol unknown to data api
            return pd.DataFrame()
        r.raise_for_status()
        out = r.json()
        rows.extend(out.get("bars") or [])
        token = out.get("next_page_token")
        if not token:
            break
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).rename(columns={
        "t": "date", "o": "open", "h": "high", "l": "low", "c": "close",
        "v": "volume", "vw": "vwap", "n": "trades"})
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["dollar_volume"] = df["vwap"] * df["volume"]
    return df[["date", "open", "high", "low", "close", "volume", "vwap",
               "trades", "dollar_volume"]].sort_values("date")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-syms", type=int, default=0)
    args = ap.parse_args()

    bars_dir = STORE / "bars"
    bars_dir.mkdir(parents=True, exist_ok=True)
    empty_path = STORE / "empty_symbols.json"
    empties = set(json.loads(empty_path.read_text())) if empty_path.exists() else set()

    sess = requests.Session()
    assets = enumerate_assets(sess)
    pool = assets  # enumerate_assets() already applies the frozen filters
    from collections import Counter
    print(f"candidates={len(pool)} by_src={Counter(a['_src'] for a in pool)} "
          f"by_status={Counter(a['_status'] for a in pool)}", flush=True)
    if args.limit_syms:
        pool = pool[: args.limit_syms]

    manifest_path = STORE / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    done = skipped = empty = 0
    t0 = time.time()
    for i, a in enumerate(pool):
        sym = a["symbol"]
        fp = bars_dir / f"{sym.replace('.', '_')}.parquet"
        if fp.exists() or sym in empties:
            skipped += 1
            continue
        try:
            df = fetch_bars(sess, sym)
        except Exception as e:  # record and continue; rerun picks it up
            print(f"[{i}] {sym}: ERROR {e}", flush=True)
            time.sleep(2)
            continue
        if df.empty:
            empties.add(sym)
            empty += 1
        else:
            df.to_parquet(fp, index=False)
            manifest[sym] = {
                "status": a["_status"], "exchange": a.get("exchange"),
                "name": a.get("name"), "n_bars": int(len(df)),
                "first": str(df["date"].iloc[0].date()),
                "last": str(df["date"].iloc[-1].date()),
            }
            done += 1
        if (done + empty) % 200 == 0:
            manifest_path.write_text(json.dumps(manifest, sort_keys=True))
            empty_path.write_text(json.dumps(sorted(empties)))
            rate = (done + empty) / max(time.time() - t0, 1)
            left = (len(pool) - i) / max(rate, 0.01) / 60
            print(f"[{i}/{len(pool)}] fetched={done} empty={empty} "
                  f"skipped={skipped} ~{left:.0f}min left", flush=True)
        time.sleep(0.31)  # ~190 req/min, under the 200/min cap

    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    empty_path.write_text(json.dumps(sorted(empties)))
    print(f"DONE fetched={done} empty={empty} skipped={skipped} "
          f"store_symbols={len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
