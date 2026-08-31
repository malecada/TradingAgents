"""nlst2 — PIT feature construction for the DEX legitimacy classifier.

Charter: docs/superpowers/specs/2026-08-31-nlst2-dexlegit-charter.md (frozen).
Gates key: predlab_nlst2 (registered 2026-08-31, pre-result).

Eight pre-named features, all PIT at the hour-24 entry (b24 = block at
pool-creation ts + 24h). Pre-signed legit directions FROZEN here, before any
feature-outcome statistic is computed:

    F1 lp_secured            +   LP burned/locked share by h24
    F2 deployer_age          +   nonce of first-LP-mint recipient at creation
    F3 deployer_supply_share -   deployer token balance / totalSupply at h24
    F4 pool_supply_share     +   pair token balance / totalSupply at h24
    F5 buyer_breadth         +   unique buyer addresses in first 24h
    F6 sell_ratio            +   sells / swaps in first 24h
    F7 sell_tax_proxy        -   median sell-output shortfall vs AMM expectation
    F8 depth_growth          +   WETH reserve at h24 / first-Sync reserve

Composite legit-score = mean over available features of sign * per-quarter
z-score; pools with <5 available features are excluded (count reported).
NO fitting, NO weight tuning, NO threshold search.

Phases (resumable): fetch -> data/predlab/nlst/nlst2_raw/{pair}.json,
build -> data/predlab/nlst/nlst2_features.parquet.
Run: nohup python scripts/predlab_nlst2_features.py > data/predlab/nlst/nlst2_features.log 2>&1 &
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_dex_fetch import (  # noqa: E402
    RAW, SWAP, WETH, get_logs, jdump, jload, rpc,
)

RAW2 = ROOT / "data" / "predlab" / "nlst" / "nlst2_raw"
OUT = ROOT / "data" / "predlab" / "nlst" / "nlst2_features.parquet"
DAY = 86_400

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
DEAD = "0x000000000000000000000000000000000000dead"
LOCKERS = {  # frozen list: Unicrypt v2, Team.Finance, Pinklock v1/v2
    "0x663a5c229c09b049e36dcc11a9b0d4a8eb9db214",
    "0x17e00383a843a9922bca3b280c0ade9f8ba48449",
    "0x71b5759d73262fbb223956913ecf4ecc51057641",
    "0x7ee058420e5937496f5a2096f04caa7721cf70cc",
}
SIGNS = {"lp_secured": 1, "deployer_age": 1, "deployer_supply_share": -1,
         "pool_supply_share": 1, "buyer_breadth": 1, "sell_ratio": 1,
         "sell_tax_proxy": -1, "depth_growth": 1}
MIN_FEATS = 5
SEL_BALANCE_OF = "0x70a08231"
SEL_TOTAL_SUPPLY = "0x18160ddd"


# ------------------------------------------------------------------ anchors


def anchor_maps():
    rows = [json.loads(l) for l in (RAW / "anchors.jsonl").read_text().splitlines()]
    rows.sort(key=lambda r: r["block"])
    b = np.array([r["block"] for r in rows], dtype=np.float64)
    t = np.array([r["ts"] for r in rows], dtype=np.float64)
    return (lambda blk: float(np.interp(blk, b, t)),
            lambda ts: int(np.interp(ts, t, b)))


# ------------------------------------------------------------------ pure fns


def parse_transfer(lg) -> dict:
    return {"block": int(lg["blockNumber"], 16),
            "from": "0x" + lg["topics"][1][-40:],
            "to": "0x" + lg["topics"][2][-40:],
            "value": int(lg["data"], 16)}


def deployer_of(transfers: list[dict]) -> "str | None":
    """Recipient of the first LP mint (Transfer from 0x0), skipping the
    MINIMUM_LIQUIDITY dust burn to 0x0 itself."""
    for t in transfers:
        if t["from"] == ZERO and t["to"] not in (ZERO, DEAD):
            return t["to"]
    return None


def lp_secured(transfers: list[dict]) -> float:
    """Share of minted LP tokens burned (0x0/0xdead) or in lockers by h24."""
    minted = sum(t["value"] for t in transfers if t["from"] == ZERO)
    if minted == 0:
        return np.nan
    secured = sum(t["value"] for t in transfers
                  if t["from"] != ZERO
                  and (t["to"] in (ZERO, DEAD) or t["to"] in LOCKERS))
    return min(1.0, secured / minted)


def sell_tax_proxy(logs: list[dict], weth_is_0: bool) -> float:
    """Median shortfall of realized sell output vs constant-product
    expectation (0.3% fee) from pre-swap reserves. Uses the cached
    amounts-only logs (Sync follows its Swap; stable block order)."""
    from predlab_nlst_lib import v2_sell

    rw = rt = None
    shortfalls = []
    for r in logs:
        if r["kind"] == "sync":
            rw = (r["r0"] if weth_is_0 else r["r1"])
            rt = (r["r1"] if weth_is_0 else r["r0"])
            continue
        if rw is None or r["kind"] != "swap":
            continue
        tok_in = r["a1in"] if weth_is_0 else r["a0in"]
        weth_out = r["a0out"] if weth_is_0 else r["a1out"]
        if tok_in > 0 and weth_out > 0:  # sell
            exp = v2_sell(tok_in, rw, rt)
            if exp > 0:
                shortfalls.append(1.0 - weth_out / exp)
    return float(np.median(shortfalls)) if shortfalls else np.nan


def buyer_breadth(swap_logs: list[dict], weth_is_0: bool) -> float:
    """Unique recipient addresses of buy swaps (WETH in) from topic'd logs."""
    buyers = set()
    for lg in swap_logs:
        d = lg["data"]
        a0in, a1in = int(d[2:66], 16), int(d[66:130], 16)
        weth_in = a0in if weth_is_0 else a1in
        if weth_in > 0:
            buyers.add("0x" + lg["topics"][2][-40:])
    return float(len(buyers))


def per_quarter_z(df: pd.DataFrame, cols) -> pd.DataFrame:
    z = pd.DataFrame(index=df.index, columns=cols, dtype=float)
    for q, sub in df.groupby("quarter"):
        for c in cols:
            v = sub[c].astype(float)
            sd = v.std()
            z.loc[sub.index, c] = (v - v.mean()) / sd if sd and sd > 0 else 0.0
    return z


def composite(df: pd.DataFrame) -> pd.Series:
    cols = list(SIGNS)
    z = per_quarter_z(df, cols)
    signed = z * pd.Series(SIGNS, dtype=float)
    n_ok = signed.notna().sum(axis=1)
    score = signed.mean(axis=1, skipna=True)
    score[n_ok < MIN_FEATS] = np.nan
    return score


# ------------------------------------------------------------------ fetch


def eth_call(to: str, data: str, block: int):
    try:
        r = rpc("eth_call", [{"to": to, "data": data}, hex(block)])
        return int(r, 16) if r and r != "0x" else None
    except RuntimeError:
        return None


def pad_addr(a: str) -> str:
    return a[2:].lower().rjust(64, "0")


def fetch_pool_features(meta: dict, b24: int) -> dict:
    pair, cblock = meta["pair"], meta["block"]
    token = meta["token1"] if meta["weth_is_0"] else meta["token0"]
    transfers = [parse_transfer(lg) for lg in
                 get_logs(pair, [TRANSFER], cblock, b24)]
    swaps = get_logs(pair, [SWAP], cblock, b24)  # raw, with topics
    dep = deployer_of(transfers)
    nonce = None
    if dep:
        try:
            nonce = int(rpc("eth_getTransactionCount", [dep, hex(cblock)]), 16)
        except RuntimeError:
            nonce = None
    supply = eth_call(token, SEL_TOTAL_SUPPLY, b24)
    bal_dep = eth_call(token, SEL_BALANCE_OF + pad_addr(dep), b24) if dep else None
    bal_pair = eth_call(token, SEL_BALANCE_OF + pad_addr(pair), b24)
    return {"pair": pair, "b24": b24, "deployer": dep, "nonce": nonce,
            "supply": supply, "bal_dep": bal_dep, "bal_pair": bal_pair,
            "transfers": transfers,
            "swaps_topics": [{"topics": lg["topics"], "data": lg["data"]}
                             for lg in swaps]}


# ------------------------------------------------------------------ build


def build_row(meta: dict, logs: list[dict], raw2: dict, ts_of) -> dict:
    weth_is_0 = meta["weth_is_0"]
    syncs = [r for r in logs if r["kind"] == "sync"]
    syncs24 = [s for s in syncs if s["block"] <= raw2["b24"]]
    row = {"pair": meta["pair"], "quarter": meta["quarter"]}
    row["lp_secured"] = lp_secured(raw2["transfers"])
    row["deployer_age"] = float(raw2["nonce"]) if raw2["nonce"] is not None else np.nan
    sup = raw2["supply"]
    row["deployer_supply_share"] = (raw2["bal_dep"] / sup
                                    if sup and raw2["bal_dep"] is not None else np.nan)
    row["pool_supply_share"] = (raw2["bal_pair"] / sup
                                if sup and raw2["bal_pair"] is not None else np.nan)
    row["buyer_breadth"] = buyer_breadth(raw2["swaps_topics"], weth_is_0)
    n_swaps24 = sum(1 for r in logs
                    if r["kind"] == "swap" and r["block"] <= raw2["b24"])
    n_sells24 = 0
    for r in logs:
        if r["kind"] == "swap" and r["block"] <= raw2["b24"]:
            tok_in = r["a1in"] if weth_is_0 else r["a0in"]
            w_out = r["a0out"] if weth_is_0 else r["a1out"]
            if tok_in > 0 and w_out > 0:
                n_sells24 += 1
    row["sell_ratio"] = n_sells24 / n_swaps24 if n_swaps24 else np.nan
    row["sell_tax_proxy"] = sell_tax_proxy(
        [r for r in logs if r["block"] <= raw2["b24"]], weth_is_0)
    if syncs24:
        first_w = (syncs24[0]["r0"] if weth_is_0 else syncs24[0]["r1"])
        last_w = (syncs24[-1]["r0"] if weth_is_0 else syncs24[-1]["r1"])
        row["depth_growth"] = last_w / first_w if first_w else np.nan
    else:
        row["depth_growth"] = np.nan
    return row


def main() -> None:
    ts_of, blk_at = anchor_maps()
    RAW2.mkdir(parents=True, exist_ok=True)
    pools = sorted((RAW / "pools").glob("*.json"))
    rows = []
    for i, p in enumerate(pools):
        d = json.loads(p.read_text())
        meta, logs = d["meta"], d["logs"]
        syncs = [r for r in logs if r["kind"] == "sync"]
        if not syncs:
            continue
        t_create = ts_of(meta["block"])
        # entered pools only (same entry rule as nlst_dex)
        if not any(ts_of(s["block"]) >= t_create + DAY for s in syncs):
            continue
        b24 = blk_at(t_create + DAY)
        cache = RAW2 / f"{meta['pair']}.json"
        if cache.exists():
            raw2 = jload(cache)
        else:
            raw2 = fetch_pool_features(meta, b24)
            jdump(cache, raw2)
        rows.append(build_row(meta, logs, raw2, ts_of))
        if i % 50 == 0:
            print(f"features: {i}/{len(pools)}", flush=True)
    df = pd.DataFrame(rows).set_index("pair")
    df["legit_score"] = composite(df)
    df.to_parquet(OUT)
    n_excl = int(df["legit_score"].isna().sum())
    print(f"built {len(df)} rows -> {OUT}; excluded <{MIN_FEATS} feats: {n_excl}")
    print("feature availability:")
    print(df[list(SIGNS)].notna().mean().round(3).to_string())


if __name__ == "__main__":
    main()
