"""nlst3 — smart-money / deployer-history feature construction (charter-frozen).

Charter: docs/superpowers/specs/2026-09-01-nlst3-moonshot-charter.md.
Gates: predlab_nlst3 (registered 2026-09-01, pre-result).

Signs FROZEN (G blind; C carried with disclosed in-sample direction):
    G1 smart_money_volshare  +    G2 smart_money_breadth   +
    G3 serial_deployer_perf  +    G4 serial_deployer_count -
    G5 early_net_inflow      +    G6 buy_acceleration      +
    G7 ownership_renounced   -
    C1 deployer_supply_share +    C2 deployer_age          -
    C3 depth_growth          +

Track record (PIT, frozen): wallet's record at pool P = mean net ret7 over
prior pools it bought in h24 whose completion (entry_ts + 7d) precedes
create_ts(P); qualified = >=3 such priors; smart = top quintile of qualified
wallets' records at that time. Composite: equal-weight signed per-quarter z,
>=6 features. No fitting.

Run: nohup python scripts/predlab_nlst3_features.py > data/predlab/nlst/nlst3_features.log 2>&1 &
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_dex_fetch import RAW, get_logs, jdump, jload  # noqa: E402
from predlab_nlst2_features import anchor_maps  # noqa: E402
from predlab_nlst_dex_p0 import (  # noqa: E402
    eth_usd_series, load_anchors, pool_event,
)


def build_events3() -> "pd.DataFrame":
    """Own event table over the FULL 3,060-pool sample (cached at EVENTS3);
    never touches the closed nlst2 cycle's nlst2_events.parquet artifact."""
    if EVENTS3.exists():
        return pd.read_parquet(EVENTS3)
    ts_of = load_anchors()
    ethusd = eth_usd_series()
    rows = []
    pools = sorted((RAW / "pools").glob("*.json"))
    for i, pp in enumerate(pools):
        r = pool_event(json.loads(pp.read_text()), ts_of, ethusd)
        if r is not None and not r.get("dead_before_entry"):
            rows.append(r)
        if i % 100 == 0:
            print(f"events3: {i}/{len(pools)}", flush=True)
    tab = pd.DataFrame(rows).set_index("pair").sort_values("list_date")
    tab.to_parquet(EVENTS3)
    return tab

RAW2 = ROOT / "data" / "predlab" / "nlst" / "nlst2_raw"
RAW3 = ROOT / "data" / "predlab" / "nlst" / "nlst3_raw"
OUT = ROOT / "data" / "predlab" / "nlst" / "nlst3_features.parquet"
NLST2_FEATS = ROOT / "data" / "predlab" / "nlst" / "nlst2_features.parquet"
EVENTS3 = ROOT / "data" / "predlab" / "nlst" / "nlst3_events.parquet"

OWN_XFER = "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0"
ZERO_PAD = "0x" + "0" * 64
DAY = 86_400
SIGNS = {"smart_money_volshare": 1, "smart_money_breadth": 1,
         "serial_deployer_perf": 1, "serial_deployer_count": -1,
         "early_net_inflow": 1, "buy_acceleration": 1,
         "ownership_renounced": -1,
         "deployer_supply_share": 1, "deployer_age": -1, "depth_growth": 1}
MIN_FEATS = 6
SMART_Q = 0.8   # top quintile of qualified wallets
MIN_PRIORS = 3


# ------------------------------------------------------------ pure functions


def pool_buyers(swaps_topics: list[dict], weth_is_0: bool) -> dict[str, float]:
    """h24 buyers -> WETH volume (in ETH units) from cached topic'd swaps."""
    out: dict[str, float] = {}
    for lg in swaps_topics:
        d = lg["data"]
        a0in, a1in = int(d[2:66], 16), int(d[66:130], 16)
        weth_in = (a0in if weth_is_0 else a1in) / 1e18
        if weth_in > 0:
            to = "0x" + lg["topics"][2][-40:]
            out[to] = out.get(to, 0.0) + weth_in
    return out


def smart_money(entries: list[dict]) -> pd.DataFrame:
    """entries: [{pair, create_ts, complete_ts, ret7, buyers:{addr:vol}}]
    sorted ascending by create_ts. Returns G1/G2 per pair (expanding PIT)."""
    hist: dict[str, list[tuple[float, float]]] = {}  # addr -> [(complete_ts, ret7)]
    rows = []
    for e in sorted(entries, key=lambda x: x["create_ts"]):
        t0 = e["create_ts"]
        records = {}
        for addr, past in hist.items():
            done = [r for ct, r in past if ct < t0]
            if len(done) >= MIN_PRIORS:
                records[addr] = float(np.mean(done))
        g1 = g2 = np.nan
        if records:
            cut = np.quantile(list(records.values()), SMART_Q)
            smart = {a for a, r in records.items() if r >= cut}
            vols = e["buyers"]
            tot = sum(vols.values())
            hit = {a for a in vols if a in smart}
            g1 = sum(vols[a] for a in hit) / tot if tot > 0 else np.nan
            g2 = float(len(hit))
        rows.append({"pair": e["pair"], "smart_money_volshare": g1,
                     "smart_money_breadth": g2,
                     "n_qualified_wallets": len(records)})
        for addr, vol in e["buyers"].items():
            hist.setdefault(addr, []).append((e["complete_ts"], e["ret7"]))
    return pd.DataFrame(rows).set_index("pair")


def serial_deployer(entries: list[dict]) -> pd.DataFrame:
    """entries: [{pair, create_ts, complete_ts, ret7, deployer}] sorted by
    create_ts. G3 = mean ret7 of deployer's COMPLETED priors, G4 = count of
    priors CREATED before (completed or not)."""
    hist: dict[str, list[tuple[float, float, float]]] = {}
    rows = []
    for e in sorted(entries, key=lambda x: x["create_ts"]):
        dep, t0 = e.get("deployer"), e["create_ts"]
        g3, g4 = np.nan, np.nan
        if dep:
            past = hist.get(dep, [])
            created = [x for x in past if x[0] < t0]
            done = [r for ct_c, ct_f, r in created if ct_f < t0]
            g4 = float(len(created))
            g3 = float(np.mean(done)) if done else np.nan
            hist.setdefault(dep, []).append((t0, e["complete_ts"], e["ret7"]))
        rows.append({"pair": e["pair"], "serial_deployer_perf": g3,
                     "serial_deployer_count": g4})
    return pd.DataFrame(rows).set_index("pair")


def flow_features(logs: list[dict], weth_is_0: bool, first_w: float,
                  b12: int, b24: int) -> dict:
    """G5 net inflow / initial depth and G6 buy acceleration from
    amounts-only cached pool logs."""
    win = wout = 0.0
    n_early = n_late = 0
    for r in logs:
        if r["kind"] != "swap" or r["block"] > b24:
            continue
        a_in = (r["a0in"] if weth_is_0 else r["a1in"]) / 1e18
        a_out = (r["a0out"] if weth_is_0 else r["a1out"]) / 1e18
        win += a_in
        wout += a_out
        if r["block"] <= b12:
            n_early += 1
        else:
            n_late += 1
    g5 = (win - wout) / first_w if first_w else np.nan
    g6 = n_late / n_early if n_early else np.nan
    return {"early_net_inflow": g5, "buy_acceleration": g6}


def eval_set_pairs() -> set[str]:
    """Fresh-extension eval set: per-quarter KEEPs #121-180 in file order."""
    counts: dict[str, int] = {}
    out = set()
    for l in (RAW / "screened.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r["verdict"] != "KEEP":
            continue
        k = counts.get(r["quarter"], 0)
        counts[r["quarter"]] = k + 1
        if k >= 120:
            out.add(r["pair"])
    return out


def composite(df: pd.DataFrame) -> pd.Series:
    from predlab_nlst2_features import per_quarter_z

    cols = list(SIGNS)
    z = per_quarter_z(df, cols)
    signed = z * pd.Series(SIGNS, dtype=float)
    n_ok = signed.notna().sum(axis=1)
    score = signed.mean(axis=1, skipna=True)
    score[n_ok < MIN_FEATS] = np.nan
    return score


# ------------------------------------------------------------ fetch + build


def fetch_ownership(meta: dict, b24: int) -> bool:
    token = meta["token1"] if meta["weth_is_0"] else meta["token0"]
    cache = RAW3 / f"{meta['pair']}.json"
    if cache.exists():
        return jload(cache)["renounced"]
    ren = False
    try:
        for lg in get_logs(token, [OWN_XFER], meta["block"], b24):
            if len(lg["topics"]) >= 3 and int(lg["topics"][2], 16) == 0:
                ren = True
                break
    except RuntimeError:
        pass
    jdump(cache, {"renounced": ren})
    return ren


def main() -> None:
    RAW3.mkdir(parents=True, exist_ok=True)
    ts_of, blk_at = anchor_maps()
    ev = build_events3()  # full-sample events (fetches new headers on demand)
    f2 = pd.read_parquet(NLST2_FEATS)
    sm_entries, dep_entries, rows = [], [], []
    pools = {p.stem: p for p in (RAW / "pools").glob("*.json")}
    for i, (pair, e) in enumerate(ev.iterrows()):
        d = json.loads(pools[pair].read_text())
        meta, logs = d["meta"], d["logs"]
        raw2 = jload(RAW2 / f"{pair}.json")
        if raw2 is None:
            continue
        t_create = ts_of(meta["block"])
        b12, b24 = blk_at(t_create + DAY / 2), raw2["b24"]
        buyers = pool_buyers(raw2["swaps_topics"], meta["weth_is_0"])
        base = {"pair": pair, "create_ts": t_create,
                "complete_ts": e["entry_ts"] + 7 * DAY, "ret7": e["ret7"]}
        sm_entries.append({**base, "buyers": buyers})
        dep_entries.append({**base, "deployer": raw2.get("deployer")})
        row = {"pair": pair, "quarter": meta["quarter"],
               "ownership_renounced": float(fetch_ownership(meta, b24)),
               **flow_features(logs, meta["weth_is_0"],
                               meta.get("first_weth_reserve"), b12, b24)}
        rows.append(row)
        if i % 100 == 0:
            print(f"nlst3: {i}/{len(ev)}", flush=True)
    df = pd.DataFrame(rows).set_index("pair")
    df = df.join(smart_money(sm_entries)).join(serial_deployer(dep_entries))
    df = df.join(f2[["deployer_supply_share", "deployer_age", "depth_growth"]])
    df["legit3_score"] = composite(df)
    ev_pairs = eval_set_pairs()
    df["eval_set"] = df.index.isin(ev_pairs)
    df.to_parquet(OUT)
    print(f"built {len(df)} rows ({int(df['eval_set'].sum())} eval) -> {OUT}")
    print("availability:")
    print(df[list(SIGNS)].notna().mean().round(3).to_string())
    print("qualified-wallet coverage:",
          float((df.join(pd.DataFrame(sm_entries).set_index('pair')[[]])
                 ["smart_money_volshare"].notna()).mean()).__round__(3))


if __name__ == "__main__":
    main()
