"""smw_xs step 4 — fetch Uniswap v2/v3 Swap logs for the in-universe pools.

Charter: docs/superpowers/specs/2026-09-04-smw-xs-charter.md (frozen).
Per month m and segment ("main" = [m_start, m_end); "lb" = the 7-day lookback
[m_start - LB, m_start) for pools whose token was not in the universe in
m-1), the active pools (token in universe, pool depth >= $10k at m_start)
are fetched in 10k-block chunks with address lists of <= ADDR_PER_CALL pools
per call; a refused call (every endpoint) is bisected. Each (month, segment,
chunk) is one parquet under data/predlab/smw/raw/<month>/ — file present =
done, so re-run = resume. Rows: pool, block, log_index, recipient,
token_amt (token units, + = wallet received token), quote_amt (quote units,
+ = wallet paid quote), version.

Block-time anchors every ANCHOR_STEP blocks (eth_getBlockByNumber) are
cached in anchors.parquet for the feature step's interpolation.

  python scripts/predlab_smw_fetch.py --probe      # feasibility (2024-03, 10 deepest)
  nohup python scripts/predlab_smw_fetch.py > data/predlab/smw/fetch.log 2>&1 &
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import rpc_pool  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
RAW = SMW / "raw"
SWAP2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
SWAP3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
CHUNK = 10_000
ADDR_PER_CALL = 8
LOOKBACK_BLOCKS = 50_400          # ~7 days at 12 s
POOL_DEPTH_MIN_USD = 10_000.0
ANCHOR_STEP = 2_000
ANCHOR_LO, ANCHOR_HI = 11_500_000, 22_400_000
QUOTE_DEC = {"WETH": 18, "USDC": 6, "USDT": 6}
MONTHS_DEV = [d.strftime("%Y-%m-%d") for d in pd.date_range("2021-01-01", "2025-03-01", freq="MS")]


# ------------------------------------------------------------ pure decoders

def _u(word: str) -> int:
    return int(word, 16)


def _i256(word: str) -> int:
    v = int(word, 16)
    return v - (1 << 256) if v >= (1 << 255) else v


def decode_swap(lg: dict, meta: dict) -> "dict | None":
    """meta: {pool, version, token_is_0, token_dec, quote_dec}. Returns a row
    or None for a foreign topic. Sign convention: token_amt > 0 wallet
    received token; quote_amt > 0 wallet paid quote (i.e. bought the token)."""
    t0 = lg["topics"][0]
    d = lg["data"][2:]
    words = [d[i:i + 64] for i in range(0, len(d), 64)]
    tok0 = meta["token_is_0"]
    if meta["version"] == 2:
        if t0 != SWAP2 or len(words) < 4:
            return None
        a0in, a1in, a0out, a1out = (_u(w) for w in words[:4])
        tin, tout = (a0in, a0out) if tok0 else (a1in, a1out)
        qin, qout = (a1in, a1out) if tok0 else (a0in, a0out)
        token_amt, quote_amt = tout - tin, qin - qout
    else:
        if t0 != SWAP3 or len(words) < 2:
            return None
        a0, a1 = _i256(words[0]), _i256(words[1])       # + = pool received
        at, aq = (a0, a1) if tok0 else (a1, a0)
        token_amt, quote_amt = -at, aq
    return {"pool": meta["pool"], "block": int(lg["blockNumber"], 16),
            "log_index": int(lg["logIndex"], 16),
            "recipient": "0x" + lg["topics"][2][-40:].lower(),
            "token_amt": token_amt / 10 ** meta["token_dec"],
            "quote_amt": quote_amt / 10 ** meta["quote_dec"],
            "version": meta["version"]}


# ------------------------------------------------------------ plan

def load_plan():
    pools = json.loads((SMW / "pools.json").read_text())["by_symbol"]
    tmap = json.loads((SMW / "token_map.json").read_text())["map"]
    universe = json.loads((SMW / "universe.json").read_text())
    mb = json.loads((SMW / "month_blocks.json").read_text())
    depth = pd.read_parquet(SMW / "depth.parquet")
    dep = depth.set_index(["month", "pool"])["depth_usd"].to_dict()
    metas = {}
    for sym, plist in pools.items():
        for p in plist:
            metas[p["pool"]] = {"pool": p["pool"], "sym": sym, "version": p["version"],
                                "token_is_0": p["token_is_0"], "quote": p["quote"],
                                "token_dec": tmap[sym]["decimals"], "quote_dec": QUOTE_DEC[p["quote"]]}
    return pools, universe, mb, dep, metas


def active_pools(month: str, pools: dict, universe: dict, dep: dict) -> list[str]:
    out = []
    for sym in universe.get(month, []):
        for p in pools.get(sym, []):
            if dep.get((month, p["pool"]), 0.0) >= POOL_DEPTH_MIN_USD:
                out.append(p["pool"])
    return sorted(set(out))


def month_segments(month: str, months: list[str], pools, universe, mb, dep) -> list[tuple]:
    """[(segment, lo, hi, [pool...])] for one month."""
    i = months.index(month)
    m_lo = mb[month]
    m_hi = mb[months[i + 1]] - 1 if i + 1 < len(months) else mb[month] + 220_000
    act = active_pools(month, pools, universe, dep)
    segs = [("main", m_lo, m_hi, act)]
    if i > 0:
        prev = set(active_pools(months[i - 1], pools, universe, dep))
        lb = [p for p in act if p not in prev]
    else:
        lb = act
    if lb:
        segs.append(("lb", m_lo - LOOKBACK_BLOCKS, m_lo - 1, lb))
    return segs


# ------------------------------------------------------------ fetch

def get_logs_multi(addrs: list[str], lo: int, hi: int) -> list[dict]:
    try:
        return rpc_pool.rpc("eth_getLogs", [{"fromBlock": hex(lo), "toBlock": hex(hi),
                                             "address": addrs, "topics": [[SWAP2, SWAP3]]}])
    except RuntimeError:
        if hi - lo < 64:
            if len(addrs) > 1:      # last resort: split the address list
                mid = len(addrs) // 2
                return get_logs_multi(addrs[:mid], lo, hi) + get_logs_multi(addrs[mid:], lo, hi)
            raise
        mid = (lo + hi) // 2
        return get_logs_multi(addrs, lo, mid) + get_logs_multi(addrs, mid + 1, hi)


def fetch_chunk(month: str, seg: str, lo: int, hi: int, addrs: list[str], metas: dict) -> dict:
    out = RAW / month / f"{seg}_{lo}.parquet"
    if out.exists():
        return {"cached": True}
    t = time.time()
    rows, nlogs = [], 0
    for i in range(0, len(addrs), ADDR_PER_CALL):
        logs = get_logs_multi(addrs[i:i + ADDR_PER_CALL], lo, hi)
        nlogs += len(logs)
        for lg in logs:
            r = decode_swap(lg, metas[lg["address"].lower()])
            if r is not None:
                rows.append(r)
    df = pd.DataFrame(rows, columns=["pool", "block", "log_index", "recipient",
                                     "token_amt", "quote_amt", "version"])
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.parquet")
    df.to_parquet(tmp, index=False)
    tmp.rename(out)
    return {"cached": False, "logs": nlogs, "rows": len(df), "secs": time.time() - t}


def fetch_anchors(workers: int = 4) -> None:
    p = SMW / "anchors.parquet"
    have = pd.read_parquet(p) if p.exists() else pd.DataFrame(columns=["block", "ts"])
    done = set(have["block"].tolist())
    todo = [b for b in range(ANCHOR_LO, ANCHOR_HI + 1, ANCHOR_STEP) if b not in done]
    print(f"anchors: {len(done)} cached, {len(todo)} to fetch", flush=True)
    rows = have.to_dict("records")

    def one(b):
        return {"block": b, "ts": int(rpc_pool.rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)}
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, r in enumerate(ex.map(one, todo)):
            rows.append(r)
            if i % 200 == 0:
                pd.DataFrame(rows).sort_values("block").to_parquet(p, index=False)
                print(f"anchors {i}/{len(todo)} {rpc_pool.get_pool().stats()}", flush=True)
    pd.DataFrame(rows).sort_values("block").drop_duplicates("block").to_parquet(p, index=False)


def run(months: list[str], workers: int, probe_pools: "list[str] | None" = None) -> dict:
    pools, universe, mb, dep, metas = load_plan()
    jobs = []
    for m in months:
        for seg, lo, hi, addrs in month_segments(m, MONTHS_DEV, pools, universe, mb, dep):
            if probe_pools is not None:
                addrs = [a for a in addrs if a in probe_pools]
                if seg == "lb":
                    continue
            if not addrs:
                continue
            for c_lo in range(lo, hi + 1, CHUNK):
                jobs.append((m, seg, c_lo, min(c_lo + CHUNK - 1, hi), addrs))
    print(f"jobs: {len(jobs)} chunks over {len(months)} months", flush=True)
    tot = {"logs": 0, "rows": 0, "secs": 0.0, "chunks": 0, "cached": 0}
    t0 = time.time()
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(fetch_chunk, *j, metas) for j in jobs]
        for i, f in enumerate(cf.as_completed(futs)):
            r = f.result()
            if r.get("cached"):
                tot["cached"] += 1
            else:
                for k in ("logs", "rows", "secs"):
                    tot[k] += r[k]
                tot["chunks"] += 1
            if i % 50 == 0 or i == len(jobs) - 1:
                print(f"{i + 1}/{len(jobs)} logs={tot['logs']} wall={time.time() - t0:.0f}s "
                      f"{rpc_pool.get_pool().stats()}", flush=True)
    tot["wall"] = time.time() - t0
    return tot


def probe() -> None:
    """Charter feasibility probe: 2024-03, ten deepest tokens, main segment."""
    pools, universe, mb, dep, metas = load_plan()
    month = "2024-03-01"
    depth = pd.read_parquet(SMW / "depth.parquet")
    tok = depth[depth["month"] == month].groupby("sym")["depth_usd"].sum().sort_values(ascending=False)
    top = [s for s in tok.index if s in universe[month]][:10]
    addrs = set()
    for s in top:
        addrs |= {p["pool"] for p in pools[s] if dep.get((month, p["pool"]), 0) >= POOL_DEPTH_MIN_USD}
    print(f"probe tokens {top}; pools {len(addrs)}", flush=True)
    res = run([month], workers=4, probe_pools=sorted(addrs))
    n_cells = sum(len(active_pools(m, pools, universe, dep)) for m in MONTHS_DEV)
    logs_per_pool_month = res["logs"] / max(len(addrs), 1)
    proj_logs = logs_per_pool_month * n_cells
    proj_bytes = proj_logs * 45                      # compact parquet row estimate
    rate = res["logs"] / max(res["wall"], 1)
    proj_hours = proj_logs / max(rate, 1) / 3600
    out = {"month": month, "tokens": top, "n_pools": len(addrs), **res,
           "pool_months_total": n_cells, "logs_per_pool_month_probe": logs_per_pool_month,
           "projected_logs": proj_logs, "projected_store_gb": proj_bytes / 1e9,
           "logs_per_sec": rate, "projected_hours": proj_hours,
           "verdict": "ABORT" if (proj_bytes > 20e9 or proj_hours > 240) else "GO",
           "note": "ten deepest tokens = densest pools; projection is an upper bound"}
    (SMW / "probe_feasibility.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--anchors-only", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--months", nargs="*", default=None)
    a = ap.parse_args()
    if a.probe:
        probe()
        return
    fetch_anchors(a.workers)
    if a.anchors_only:
        return
    res = run(a.months or MONTHS_DEV, a.workers)
    print("FETCH DONE", json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
