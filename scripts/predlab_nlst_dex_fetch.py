"""nlst_dex data fetch — Uniswap v2 (ETH) pool-creation event panel via dRPC free.

Charter: docs/superpowers/specs/2026-08-26-newlist-charter.md (frozen).
Phases (all idempotent + chunk-cached under data/predlab/nlst/dex_raw/):
  A. enumerate PairCreated logs, dev window, 10k-block chunks
  B. per-quarter seeded screening: candidates in seeded random order,
     fetch first-24h Sync+Swap, apply F1-F5, keep 60/quarter
  C. kept pools: fetch Sync+Swap to creation+16d + entry/exit block headers
Run:  nohup python scripts/predlab_nlst_dex_fetch.py > data/predlab/nlst/dex_fetch.log 2>&1 &
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "predlab" / "nlst" / "dex_raw"
RPC = "https://eth.drpc.org"

FACTORY = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
PAIR_CREATED = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"

# F4 frozen exclusion list (major/derivative tokens; lowercase)
EXCLUDE_TOKENS = {
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    "0x853d955acef822db058eb8505911ed77f175b99e",  # FRAX
    "0x0000000000085d4780b73119b644ae5ecd22b376",  # TUSD
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0",  # LUSD
    "0x4fabb145d64652a948d72533023f6e7a623c7c53",  # BUSD
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # stETH
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",  # wstETH
    "0xae78736cd615f374d3085123a210448e74fc6393",  # rETH
    "0xbe9895146f7af43049ca1c1ae358b0541ea49704",  # cbETH
}

SEED = 7
KEEP_PER_Q = 60
QUARTERS = [f"{y}Q{q}" for y in range(2021, 2025) for q in range(1, 5)] + ["2025Q1"]
BLOCKS_24H = 7200          # ~12s blocks
BLOCKS_16D = 16 * 7200     # event window incl. 14d horizon + buffer
F2_MIN_WETH = 10.0         # ETH
F3_MIN_SWAPS = 20
CHUNK = 10_000
THROTTLE = 0.22            # s between calls


def rpc(method: str, params: list, tries: int = 6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    for a in range(tries):
        try:
            req = urllib.request.Request(RPC, body, {
                "Content-Type": "application/json", "User-Agent": "curl/8.5.0"})
            r = json.loads(urllib.request.urlopen(req, timeout=60).read())
            if "error" in r:
                raise RuntimeError(r["error"].get("message", str(r["error"])))
            time.sleep(THROTTLE)
            return r["result"]
        except Exception as e:  # noqa: BLE001 — backoff on any transport error
            msg = str(e)
            if "ranges over" in msg or "response size" in msg.lower():
                raise  # caller bisects
            time.sleep(min(60, 2.0 * 2 ** a))
    raise RuntimeError(f"rpc gave up: {method}")


def get_logs(addr, topics, lo: int, hi: int) -> list:
    """getLogs with recursive bisection on range/size errors."""
    if hi < lo:
        return []
    try:
        return rpc("eth_getLogs", [{
            "fromBlock": hex(lo), "toBlock": hex(hi),
            "address": addr, "topics": topics}])
    except RuntimeError:
        if hi - lo < 256:
            raise
        mid = (lo + hi) // 2
        return get_logs(addr, topics, lo, mid) + get_logs(addr, topics, mid + 1, hi)


def block_ts(n: int) -> int:
    return int(rpc("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)


def block_at_ts(ts: int, lo: int = 10_000_000, hi: int = 23_500_000) -> int:
    """First block with timestamp >= ts (binary search)."""
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def jload(p: Path, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def jdump(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.rename(p)


# ------------------------------------------------------------------ phase A


def phase_a() -> list[dict]:
    import calendar
    from datetime import datetime, timezone

    meta_p = RAW / "meta.json"
    meta = jload(meta_p, {})
    if "b0" not in meta:
        t0 = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
        t1 = int(datetime(2025, 4, 1, tzinfo=timezone.utc).timestamp())
        meta["b0"] = block_at_ts(t0)
        meta["b1"] = block_at_ts(t1) - 1
        # quarter boundary blocks for stratification
        qb = {}
        for q in QUARTERS:
            y, qn = int(q[:4]), int(q[-1])
            ts = int(datetime(y, 3 * qn - 2, 1, tzinfo=timezone.utc).timestamp())
            qb[q] = block_at_ts(ts)
        qb["end"] = meta["b1"] + 1
        meta["qblocks"] = qb
        jdump(meta_p, meta)
        print("meta:", meta["b0"], "->", meta["b1"], flush=True)

    pairs_p = RAW / "paircreated.jsonl"
    done_p = RAW / "paircreated_done.json"
    done = set(jload(done_p, []))
    with pairs_p.open("a") as fh:
        for lo in range(meta["b0"], meta["b1"] + 1, CHUNK):
            if lo in done:
                continue
            hi = min(lo + CHUNK - 1, meta["b1"])
            logs = get_logs(FACTORY, [PAIR_CREATED], lo, hi)
            for lg in logs:
                fh.write(json.dumps({
                    "block": int(lg["blockNumber"], 16),
                    "token0": "0x" + lg["topics"][1][-40:],
                    "token1": "0x" + lg["topics"][2][-40:],
                    "pair": "0x" + lg["data"][26:66],
                }) + "\n")
            fh.flush()
            done.add(lo)
            if len(done) % 50 == 0:
                jdump(done_p, sorted(done))
                print(f"A: {len(done)} chunks, block {hi}", flush=True)
    jdump(done_p, sorted(done))
    return [json.loads(l) for l in pairs_p.read_text().splitlines()]


# ------------------------------------------------------------------ phase B


def parse_sync(lg):
    d = lg["data"]
    return {"block": int(lg["blockNumber"], 16), "kind": "sync",
            "r0": int(d[2:66], 16), "r1": int(d[66:130], 16)}


def parse_swap(lg):
    d = lg["data"]
    return {"block": int(lg["blockNumber"], 16), "kind": "swap",
            "a0in": int(d[2:66], 16), "a1in": int(d[66:130], 16),
            "a0out": int(d[130:194], 16), "a1out": int(d[194:258], 16)}


def fetch_pool_logs(pair: str, lo: int, hi: int) -> list[dict]:
    logs = get_logs(pair, [[SYNC, SWAP]], lo, hi)
    out = []
    for lg in logs:
        t = lg["topics"][0]
        if t == SYNC:
            out.append(parse_sync(lg))
        elif t == SWAP:
            out.append(parse_swap(lg))
    out.sort(key=lambda r: r["block"])
    return out


def screen_pool(cand: dict) -> dict:
    """Fetch first-24h logs, apply F2/F3/F5. Returns dict with verdict."""
    pair, blk = cand["pair"], cand["block"]
    weth_is_0 = cand["token0"] == WETH
    logs = fetch_pool_logs(pair, blk, blk + BLOCKS_24H)
    syncs = [r for r in logs if r["kind"] == "sync"]
    swaps = [r for r in logs if r["kind"] == "swap"]
    res = dict(cand, weth_is_0=weth_is_0, n_sync24=len(syncs),
               n_swap24=len(swaps))
    if not syncs:
        res["verdict"] = "F2_no_sync"
        return res
    first = syncs[0]
    weth_res = (first["r0"] if weth_is_0 else first["r1"]) / 1e18
    res["first_weth_reserve"] = weth_res
    if weth_res < F2_MIN_WETH:
        res["verdict"] = "F2_thin"
        return res
    if len(swaps) < F3_MIN_SWAPS:
        res["verdict"] = "F3_inactive"
        return res
    if weth_is_0:
        sells = [s for s in swaps if s["a1in"] > 0 and s["a0out"] > 0]
    else:
        sells = [s for s in swaps if s["a0in"] > 0 and s["a1out"] > 0]
    res["n_sell24"] = len(sells)
    if not sells:
        res["verdict"] = "F5_honeypot"
        return res
    res["verdict"] = "KEEP"
    return res


def phase_b(pairs: list[dict]) -> list[dict]:
    meta = jload(RAW / "meta.json")
    qb = meta["qblocks"]
    # candidate filter: F1 WETH side + F4 exclusion
    cands = [p for p in pairs
             if (p["token0"] == WETH) != (p["token1"] == WETH)
             and p["token0"] not in EXCLUDE_TOKENS
             and p["token1"] not in EXCLUDE_TOKENS]
    screened_p = RAW / "screened.jsonl"
    seen = {json.loads(l)["pair"] for l in screened_p.read_text().splitlines()} \
        if screened_p.exists() else set()
    kept_by_q = {}
    if screened_p.exists():
        for l in screened_p.read_text().splitlines():
            r = json.loads(l)
            if r["verdict"] == "KEEP":
                kept_by_q.setdefault(r["quarter"], []).append(r)
    rng = np.random.default_rng(SEED)
    q_starts = [qb[q] for q in QUARTERS] + [qb["end"]]
    with screened_p.open("a") as fh:
        for qi, q in enumerate(QUARTERS):
            lo, hi = q_starts[qi], q_starts[qi + 1]
            qc = [c for c in cands if lo <= c["block"] < hi]
            order = rng.permutation(len(qc))  # consumed deterministically per quarter
            kept = len(kept_by_q.get(q, []))
            for oi in order:
                if kept >= KEEP_PER_Q:
                    break
                c = qc[oi]
                if c["pair"] in seen:
                    continue
                res = screen_pool(c)
                res["quarter"] = q
                fh.write(json.dumps(res) + "\n")
                fh.flush()
                seen.add(c["pair"])
                if res["verdict"] == "KEEP":
                    kept += 1
                    kept_by_q.setdefault(q, []).append(res)
            print(f"B: {q} kept {kept} (candidates {len(qc)})", flush=True)
    return [r for rs in kept_by_q.values() for r in rs]


# ------------------------------------------------------------------ phase C


ANCHOR_STEP = 5_000


def phase_c(kept: list[dict]) -> None:
    """Per-pool event logs + a global block->timestamp anchor grid.

    Exact headers (ts + basefee) for the specific entry/exit blocks are
    fetched on demand by the analysis script via `header()` below (cached to
    headers.jsonl); the anchor grid only locates those blocks in time."""
    meta = jload(RAW / "meta.json")
    anch_p = RAW / "anchors.jsonl"
    have = {json.loads(l)["block"] for l in anch_p.read_text().splitlines()} \
        if anch_p.exists() else set()
    grid = list(range(meta["b0"], meta["b1"] + BLOCKS_16D + ANCHOR_STEP,
                      ANCHOR_STEP))
    todo = [b for b in grid if b not in have]
    print(f"C: fetching {len(todo)} ts anchors", flush=True)
    with anch_p.open("a") as fh:
        for j, b in enumerate(todo):
            fh.write(json.dumps({"block": b, "ts": block_ts(b)}) + "\n")
            if j % 100 == 0:
                fh.flush()
                print(f"C: anchors {j}/{len(todo)}", flush=True)
    pools_dir = RAW / "pools"
    for i, k in enumerate(kept):
        out = pools_dir / f"{k['pair']}.json"
        if not out.exists():
            logs = fetch_pool_logs(k["pair"], k["block"],
                                   k["block"] + BLOCKS_16D)
            jdump(out, {"meta": k, "logs": logs})
        if i % 25 == 0:
            print(f"C: {i}/{len(kept)} pools", flush=True)


def header(block: int) -> dict:
    """Exact header (ts, basefee) with jsonl cache — used by analysis."""
    hdr_p = RAW / "headers.jsonl"
    if hdr_p.exists():
        for l in hdr_p.read_text().splitlines():
            r = json.loads(l)
            if r["block"] == block:
                return r
    blk = rpc("eth_getBlockByNumber", [hex(block), False])
    row = {"block": block, "ts": int(blk["timestamp"], 16),
           "basefee": int(blk.get("baseFeePerGas", "0x0"), 16)}
    with hdr_p.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    pairs = phase_a()
    print(f"A done: {len(pairs)} PairCreated events", flush=True)
    kept = phase_b(pairs)
    print(f"B done: {len(kept)} kept pools", flush=True)
    phase_c(kept)
    print("C done", flush=True)
