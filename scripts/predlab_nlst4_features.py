"""nlst4 feature stage (charter 2026-09-04): events + nlst2/nlst3 feature caches
for every pool in dex_raw/pools (old and new), frozen nlst3 composite.

  nohup python scripts/predlab_nlst4_features.py >> data/predlab/nlst/nlst4_features.log 2>&1 &

Outputs (own files; closed-family artifacts untouched):
  data/predlab/nlst/nlst4_events.parquet     event table (pool_event, all pools)
  data/predlab/nlst/nlst4_features.parquet   ten features + legit3-composite + new_set flag
RPC caches are shared with the closed cycles (nlst2_raw/, nlst3_raw/,
headers.jsonl) -- append-only, existing entries reused. new_set = KEEP #181+
per quarter in screened.jsonl order (the P0 evaluation set).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import predlab_nlst2_features as f2  # noqa: E402
import predlab_nlst3_features as f3  # noqa: E402
from predlab_nlst_dex_fetch import RAW, jdump, jload  # noqa: E402
from predlab_nlst_dex_p0 import eth_usd_series, load_anchors, pool_event  # noqa: E402

NL = ROOT / "data" / "predlab" / "nlst"
EVENTS4 = NL / "nlst4_events.parquet"
FEATS4 = NL / "nlst4_features.parquet"
DAY = 86_400
NEW_FROM = 180   # KEEP index (0-based) at which the nlst4 evaluation set starts


def build_events4() -> pd.DataFrame:
    if EVENTS4.exists():
        return pd.read_parquet(EVENTS4)
    ts_of = load_anchors()
    ethusd = eth_usd_series()
    rows = []
    pools = sorted((RAW / "pools").glob("*.json"))
    t0 = time.time()
    for i, pp in enumerate(pools):
        r = pool_event(json.loads(pp.read_text()), ts_of, ethusd)
        if r is not None and not r.get("dead_before_entry"):
            rows.append(r)
        if i % 200 == 0:
            print(f"events4: {i}/{len(pools)} t={time.time()-t0:.0f}s", flush=True)
    tab = pd.DataFrame(rows).set_index("pair").sort_values("list_date")
    tab.to_parquet(EVENTS4)
    return tab


def new_set_pairs() -> set[str]:
    counts: dict[str, int] = {}
    out = set()
    for line in (RAW / "screened.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["verdict"] != "KEEP":
            continue
        k = counts.get(r["quarter"], 0)
        counts[r["quarter"]] = k + 1
        if k >= NEW_FROM:
            out.add(r["pair"])
    return out


def main() -> None:
    f2.RAW2.mkdir(parents=True, exist_ok=True)
    f3.RAW3.mkdir(parents=True, exist_ok=True)
    ts_of, blk_at = f2.anchor_maps()
    ev = build_events4()
    print(f"events: {len(ev)} entered pools", flush=True)
    pools = {p.stem: p for p in (RAW / "pools").glob("*.json")}
    rows2, sm_entries, dep_entries, rows3 = [], [], [], []
    t0 = time.time()
    for i, (pair, e) in enumerate(ev.iterrows()):
        d = json.loads(pools[pair].read_text())
        meta, logs = d["meta"], d["logs"]
        t_create = ts_of(meta["block"])
        b24 = blk_at(t_create + DAY)
        cache2 = f2.RAW2 / f"{pair}.json"
        raw2 = jload(cache2)
        if raw2 is None:
            raw2 = f2.fetch_pool_features(meta, b24)
            jdump(cache2, raw2)
        rows2.append(f2.build_row(meta, logs, raw2, ts_of))
        b12 = blk_at(t_create + DAY / 2)
        buyers = f3.pool_buyers(raw2["swaps_topics"], meta["weth_is_0"])
        base = {"pair": pair, "create_ts": t_create, "complete_ts": e["entry_ts"] + 7 * DAY, "ret7": e["ret7"]}
        sm_entries.append({**base, "buyers": buyers})
        dep_entries.append({**base, "deployer": raw2.get("deployer")})
        rows3.append({"pair": pair, "quarter": meta["quarter"],
                      "ownership_renounced": float(f3.fetch_ownership(meta, raw2["b24"])),
                      **f3.flow_features(logs, meta["weth_is_0"], meta.get("first_weth_reserve"), b12, raw2["b24"])})
        if i % 100 == 0:
            print(f"features: {i}/{len(ev)} t={time.time()-t0:.0f}s", flush=True)
    d2 = pd.DataFrame(rows2).set_index("pair")
    df = pd.DataFrame(rows3).set_index("pair")
    df = df.join(f3.smart_money(sm_entries)).join(f3.serial_deployer(dep_entries))
    df = df.join(d2[["deployer_supply_share", "deployer_age", "depth_growth"]])
    df["legit3_score"] = f3.composite(df)
    new = new_set_pairs()
    df["new_set"] = df.index.isin(new)
    df.to_parquet(FEATS4)
    print(f"built {len(df)} rows ({int(df['new_set'].sum())} new-set) -> {FEATS4}")
    print(df[list(f3.SIGNS)].notna().mean().round(3).to_string())


if __name__ == "__main__":
    main()
