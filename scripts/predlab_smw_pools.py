"""smw_xs step 2 — enumerate Uniswap v2/v3 pools (token x quote) for mapped tokens.

Frozen, outcome-free: quotes = WETH, USDC, USDT; Uniswap v2 factory getPair
and v3 factory getPool at fee tiers 100 / 500 / 3000 / 10000 (latest state —
pool addresses are deterministic CREATE2 and immutable once created; a pool
that did not exist yet at a month start simply has zero balance there).

Run: python scripts/predlab_smw_pools.py   -> data/predlab/smw/pools.json
"""
from __future__ import annotations

import json
import sys
import concurrent.futures as cf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import rpc_pool  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
OUT = SMW / "pools.json"

V2_FACTORY = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
V3_FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"
QUOTES = {"WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
          "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
          "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7"}
V3_FEES = (100, 500, 3000, 10000)
ZERO = "0x" + "0" * 40


def _pad(addr: str) -> str:
    return addr[2:].lower().rjust(64, "0")


def _addr(word: str) -> str:
    return "0x" + word[-40:].lower()


def v2_pair(token: str, quote: str) -> str:
    data = "0xe6a43905" + _pad(token) + _pad(quote)
    r = rpc_pool.rpc("eth_call", [{"to": V2_FACTORY, "data": data}, "latest"])
    return _addr(r) if r and len(r) >= 66 else ZERO


def v3_pool(token: str, quote: str, fee: int) -> str:
    data = "0x1698ee82" + _pad(token) + _pad(quote) + hex(fee)[2:].rjust(64, "0")
    r = rpc_pool.rpc("eth_call", [{"to": V3_FACTORY, "data": data}, "latest"])
    return _addr(r) if r and len(r) >= 66 else ZERO


def enumerate_token(sym: str, token: str) -> list[dict]:
    """All 15 factory lookups for one token in ONE batched JSON-RPC request."""
    specs, params = [], []
    for qname, q in QUOTES.items():
        specs.append((qname, q, 2, 3000))
        params.append([{"to": V2_FACTORY, "data": "0xe6a43905" + _pad(token) + _pad(q)}, "latest"])
        for fee in V3_FEES:
            specs.append((qname, q, 3, fee))
            params.append([{"to": V3_FACTORY, "data": "0x1698ee82" + _pad(token) + _pad(q)
                            + hex(fee)[2:].rjust(64, "0")}, "latest"])
    res = rpc_pool.rpc_batch("eth_call", params)
    out = []
    for (qname, q, ver, fee), r in zip(specs, res):
        p = _addr(r) if r and len(r) >= 66 else ZERO
        if p != ZERO:
            out.append({"sym": sym, "token": token, "quote": qname, "quote_addr": q,
                        "version": ver, "fee": fee, "pool": p, "token_is_0": token.lower() < q.lower()})
    return out


def main() -> None:
    tm = json.loads((SMW / "token_map.json").read_text())["map"]
    want = {s: v["address"] for s, v in tm.items() if v.get("address") and v.get("decimals") is not None}
    cache = json.loads((SMW / "pools_by_token.json").read_text()) if (SMW / "pools_by_token.json").exists() else {}
    todo = {a for a in want.values() if a not in cache}
    print(f"tokens to enumerate: {len(todo)} (cached {len(cache)})", flush=True)
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {ex.submit(enumerate_token, "", a): a for a in sorted(todo)}
        for i, f in enumerate(cf.as_completed(futs)):
            a = futs[f]
            cache[a] = [{k: v for k, v in p.items() if k != "sym"} for p in f.result()]
            if i % 20 == 0:
                (SMW / "pools_by_token.json").write_text(json.dumps(cache, indent=0))
                print(f"{i}/{len(todo)} {a}: {len(cache[a])} pools  {rpc_pool.get_pool().stats()}", flush=True)
    (SMW / "pools_by_token.json").write_text(json.dumps(cache, indent=0))
    by_symbol = {s: [{"sym": s, **p} for p in cache[a]] for s, a in want.items()}
    OUT.write_text(json.dumps({"by_symbol": by_symbol}, indent=0))
    n = sum(len(v) for v in by_symbol.values())
    print(f"wrote {OUT}: {len(by_symbol)} tokens, {n} pools", flush=True)


if __name__ == "__main__":
    main()
