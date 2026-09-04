"""smw_xs step 3 — monthly PIT pool depth and the dry universe enumeration.

For every month start m in the dev window (2021-01 .. 2025-03, plus 2025-04
as the first holdout month for the H2 count only), find the first block at
or after m 00:00 UTC (binary search on block timestamps, cached), then for
every enumerated pool of a token that is in that month's PIT top-200 perp
universe (T7 rule: month m membership from month m-1 median quote volume),
read the quote-token balance held by the pool at that block
(ERC-20 balanceOf(pool), archive eth_call). Depth USD := 2 x quote-side
balance x quote price (ETH close of the previous UTC day for WETH; 1 for
USDC/USDT). Universe rule (frozen): token is in the smw universe in month m
iff sum of depth over its pools >= $1M at the month-start block.

Outputs: data/predlab/smw/month_blocks.json, depth.parquet
(month, sym, pool, version, quote, balance, depth_usd), universe.json
(month -> [sym]) and a breadth table printed for the charter.

Run: python scripts/predlab_smw_depth.py
"""
from __future__ import annotations

import json
import sys
import concurrent.futures as cf
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from tradingagents.predlab import rpc_pool  # noqa: E402
from predlab_t7 import monthly_universe  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
PANELS = ROOT / "data" / "predlab" / "t7_panels"
MONTHS = pd.date_range("2021-01-01", "2025-04-01", freq="MS", tz="UTC")
DEPTH_FLOOR_USD = 1_000_000.0
DEC = {"WETH": 18, "USDC": 6, "USDT": 6}


def block_ts(n: int) -> int:
    return int(rpc_pool.rpc("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)


def block_at_ts(ts: int, lo: int = 11_000_000, hi: int = 22_400_000) -> int:
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def month_blocks() -> dict:
    p = SMW / "month_blocks.json"
    mb = json.loads(p.read_text()) if p.exists() else {}
    for m in MONTHS:
        k = m.strftime("%Y-%m-%d")
        if k not in mb:
            mb[k] = block_at_ts(int(m.timestamp()))
            p.write_text(json.dumps(mb, indent=1))
            print(f"month block {k} -> {mb[k]}", flush=True)
    return mb


def balance_of(token_addr: str, holder: str, block: int) -> int:
    data = "0x70a08231" + holder[2:].lower().rjust(64, "0")
    r = rpc_pool.rpc("eth_call", [{"to": token_addr, "data": data}, hex(block)])
    return int(r, 16) if r and r != "0x" else 0


def main() -> None:
    pools = json.loads((SMW / "pools.json").read_text())["by_symbol"]
    qv = pd.read_parquet(PANELS / "qv.parquet")
    close = pd.read_parquet(PANELS / "close.parquet")
    eth = close["ETHUSDT"].dropna()
    uni = monthly_universe(qv, top_n=200)
    mb = month_blocks()
    out_p = SMW / "depth.parquet"
    rows = pd.read_parquet(out_p).to_dict("records") if out_p.exists() else []
    have = {(r["month"], r["pool"]) for r in rows}
    tasks = []
    for m in MONTHS:
        k = m.strftime("%Y-%m-%d")
        members = set(uni.columns[uni.loc[m]]) if m in uni.index else set()
        for sym, plist in pools.items():
            if sym not in members:
                continue
            for pl in plist:
                if (k, pl["pool"]) not in have:
                    tasks.append((k, mb[k], sym, pl))
    print(f"balance calls to do: {len(tasks)} (cached {len(rows)})", flush=True)

    def work(t):
        k, blk, sym, pl = t
        bal = balance_of(pl["quote_addr"], pl["pool"], blk) / 10 ** DEC[pl["quote"]]
        d = pd.Timestamp(k, tz="UTC") - pd.Timedelta(days=1)
        px = float(eth.asof(d)) if pl["quote"] == "WETH" else 1.0
        return {"month": k, "sym": sym, "pool": pl["pool"], "version": pl["version"], "fee": pl["fee"],
                "quote": pl["quote"], "balance": bal, "depth_usd": 2.0 * bal * px}

    with cf.ThreadPoolExecutor(4) as ex:
        for i, r in enumerate(ex.map(work, tasks)):
            rows.append(r)
            if i % 200 == 0:
                pd.DataFrame(rows).to_parquet(out_p)
                print(f"{i}/{len(tasks)}  {rpc_pool.get_pool().stats()}", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(out_p)
    tok = df.groupby(["month", "sym"])["depth_usd"].sum().reset_index()
    universe = {m: sorted(g.loc[g["depth_usd"] >= DEPTH_FLOOR_USD, "sym"].tolist())
                for m, g in tok.groupby("month")}
    (SMW / "universe.json").write_text(json.dumps(universe, indent=1))
    breadth = pd.Series({m: len(v) for m, v in universe.items()}).sort_index()
    dev = breadth[breadth.index < "2025-04-01"]
    print("breadth per month:\n" + breadth.to_string(), flush=True)
    print(f"DEV breadth median {dev.median():.0f} min {dev.min()} max {dev.max()} "
          f"(floor 40: {'PASS' if dev.median() >= 40 else 'ABORT'})", flush=True)


if __name__ == "__main__":
    main()
