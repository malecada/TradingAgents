"""smw_xs step 1 — map Binance USDT-perp symbols to Ethereum-mainnet ERC-20 contracts.

Rule (frozen, outcome-free): base symbol = perp symbol minus 'USDT' and a
leading 1000 / 1000000 multiplier.
  1. Binance-spot rule: CoinGecko's Binance spot ticker list
     (cg/binance_tickers_p*.json, /exchanges/binance/tickers, 2026-09-04)
     gives base -> coin_id (most frequent coin_id per base). If the base is
     listed: mapped iff that coin has a platforms.ethereum address
     ('binance_spot'), else unmapped ('binance_spot_no_eth') even when a
     same-symbol ERC-20 exists (TON, CFX, DASH collisions).
  2. Fallback (base not on Binance spot today, i.e. delisted / dead tokens):
     candidates = CoinGecko coins with that symbol and an ethereum address
     (cg/coins_list_platforms.json); a single candidate is taken; with
     several, the best market_cap_rank in the top-2500 snapshot
     (cg/markets_p*.json) is taken only if rank <= 500 (guards against
     same-symbol ERC-20 collisions such as TON -> Tokamak); else unmapped.
Decimals via eth_call decimals(). The mapping is a universe definition, not
a signal; the stored file lists every symbol with the rule that fired.

Run: python scripts/predlab_smw_map.py   -> data/predlab/smw/token_map.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import rpc_pool  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
KLINES = ROOT / "data" / "xsect" / "klines"
OUT = SMW / "token_map.json"
FALLBACK_MAX_RANK = 500


def base_symbol(sym: str) -> str:
    s = sym[:-4] if sym.endswith("USDT") else sym
    m = re.match(r"^(1000000|1000)(.+)$", s)
    return m.group(2) if m else s


def load_cg():
    coins = json.loads((SMW / "cg" / "coins_list_platforms.json").read_text())
    rank = {}
    for p in sorted((SMW / "cg").glob("markets_p*.json")):
        for c in json.loads(p.read_text()):
            if c.get("market_cap_rank") is not None:
                rank[c["id"]] = int(c["market_cap_rank"])
    return coins, rank


def load_binance_spot() -> dict:
    """base symbol (lower) -> most frequent CoinGecko coin_id on Binance spot."""
    counts: dict[str, dict[str, int]] = {}
    for p in sorted((SMW / "cg").glob("binance_tickers_p*.json")):
        for t in json.loads(p.read_text()).get("tickers", []):
            if t.get("coin_id"):
                d = counts.setdefault(t["base"].lower(), {})
                d[t["coin_id"]] = d.get(t["coin_id"], 0) + 1
    return {b: max(d.items(), key=lambda kv: kv[1])[0] for b, d in counts.items()}


def map_symbols(syms: list[str], coins: list[dict], rank: dict,
                spot: "dict | None" = None) -> dict:
    spot = spot or {}
    by_id = {c["id"]: c for c in coins}
    by_sym: dict[str, list] = {}
    for c in coins:
        addr = (c.get("platforms") or {}).get("ethereum")
        if addr and re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
            by_sym.setdefault(c["symbol"].lower(), []).append(
                {"id": c["id"], "name": c["name"], "address": addr.lower(), "rank": rank.get(c["id"])})
    out = {}
    for sym in syms:
        b = base_symbol(sym).lower()
        cands = by_sym.get(b, [])
        if b in spot:
            c = by_id.get(spot[b])
            addr = ((c or {}).get("platforms") or {}).get("ethereum")
            if c and addr and re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
                pick, how = {"id": c["id"], "name": c["name"], "address": addr.lower(),
                             "rank": rank.get(c["id"])}, "binance_spot"
            else:
                pick, how = None, "binance_spot_no_eth"
            out[sym] = {"base": base_symbol(sym), "how": how, "n_candidates": len(cands),
                        "spot_coin_id": spot[b],
                        **({"cg_id": pick["id"], "name": pick["name"], "address": pick["address"],
                            "rank": pick["rank"]} if pick else {})}
            continue
        ranked = sorted([c for c in cands if c["rank"] is not None], key=lambda c: c["rank"])
        if len(cands) == 1:
            pick, how = cands[0], ("fallback_single_ranked" if ranked else "fallback_single_unranked")
        elif ranked and ranked[0]["rank"] <= FALLBACK_MAX_RANK:
            pick, how = ranked[0], "fallback_ranked"
        else:
            pick, how = None, ("fallback_no_candidate" if not cands else "fallback_ambiguous")
        out[sym] = {"base": base_symbol(sym), "how": how, "n_candidates": len(cands),
                    **({"cg_id": pick["id"], "name": pick["name"], "address": pick["address"],
                        "rank": pick["rank"]} if pick else {})}
    return out


def main() -> None:
    syms = sorted(p.stem for p in KLINES.glob("*.parquet"))
    coins, rank = load_cg()
    spot = load_binance_spot()
    assert len(spot) > 300, f"binance spot ticker list incomplete ({len(spot)} bases)"
    m = map_symbols(syms, coins, rank, spot)
    mapped = {s: v for s, v in m.items() if v.get("address")}
    prev = json.loads(OUT.read_text())["map"] if OUT.exists() else {}
    # decimals (latest state; ERC-20 decimals are immutable in practice)
    for i, (s, v) in enumerate(mapped.items()):
        pv = prev.get(s, {})
        if pv.get("address") == v["address"] and pv.get("decimals") is not None:
            v["decimals"] = pv["decimals"]
            continue
        try:
            r = rpc_pool.rpc("eth_call", [{"to": v["address"], "data": "0x313ce567"}, "latest"])
            v["decimals"] = int(r, 16) if r and r != "0x" else None
        except RuntimeError as e:
            v["decimals"] = None
            v["decimals_error"] = str(e)[:80]
        if i % 50 == 0:
            print(f"decimals {i}/{len(mapped)}", flush=True)
    hows = {}
    for v in m.values():
        hows[v["how"]] = hows.get(v["how"], 0) + 1
    OUT.write_text(json.dumps({"n_perp_symbols": len(syms), "how_counts": hows, "map": m}, indent=1))
    print(f"wrote {OUT}: {hows}; decimals missing "
          f"{sum(1 for v in mapped.values() if v.get('decimals') is None)}", flush=True)
    print(rpc_pool.get_pool().stats())


if __name__ == "__main__":
    main()
