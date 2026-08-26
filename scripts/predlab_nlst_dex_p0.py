"""nlst_dex P0 — event study on sampled Uniswap v2 pools (charter-frozen).

Entry: first Sync >= 24h after pool creation (execute against its reserves).
Exit per horizon H in {3,7,14}d: first Sync >= entry_ts + H days; if none
(dead pool), last Sync (rug booking, ~-100%).
Cost model: 0.30% LP fee/side + exact constant-product execution of the full
notional ($1k P0, $5k stress) + gas 2 x 150k x (basefee + 2 gwei) x ETH/USD.
Simple returns. No other fudge factors. MEV sandwich not modeled (disclosed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_lib import (  # noqa: E402
    DEV, HORIZONS_DEX, OUT_DIR, ledger_append, p0_stats, v2_buy, v2_sell,
    write_result,
)
from predlab_nlst_dex_fetch import RAW, header  # noqa: E402

GAS_SWAP = 150_000
TIP_WEI = 2e9
DAY = 86_400
NOTIONALS = (1_000.0, 5_000.0)


def load_anchors():
    rows = [json.loads(l) for l in (RAW / "anchors.jsonl").read_text().splitlines()]
    rows.sort(key=lambda r: r["block"])
    b = np.array([r["block"] for r in rows], dtype=np.float64)
    t = np.array([r["ts"] for r in rows], dtype=np.float64)
    return lambda blk: float(np.interp(blk, b, t))


def eth_usd_series() -> pd.Series:
    c = pd.read_parquet(ROOT / "data" / "xsect" / "klines" / "ETHUSDT.parquet",
                        columns=["close"])["close"]
    return c


def eth_usd_at(ts: float, ser: pd.Series) -> float:
    d = pd.Timestamp(int(ts), unit="s", tz="UTC").floor("D")
    s = ser.reindex([d]).iloc[0]
    if np.isnan(s):
        s = ser[ser.index <= d].iloc[-1]
    return float(s)


def pool_event(pool: dict, ts_of, ethusd: pd.Series) -> "dict | None":
    meta, logs = pool["meta"], pool["logs"]
    weth_is_0 = meta["weth_is_0"]
    syncs = [r for r in logs if r["kind"] == "sync"]
    if not syncs:
        return None
    t_create = ts_of(meta["block"])
    entry = next((s for s in syncs if ts_of(s["block"]) >= t_create + DAY), None)
    if entry is None:
        return {"pair": meta["pair"], "quarter": meta["quarter"],
                "dead_before_entry": True}
    t_entry = ts_of(entry["block"])
    hdr_e = header(entry["block"])
    eth_e = eth_usd_at(hdr_e["ts"], ethusd)
    row = {"pair": meta["pair"], "quarter": meta["quarter"],
           "dead_before_entry": False,
           "entry_ts": hdr_e["ts"],
           "list_date": pd.Timestamp(hdr_e["ts"], unit="s", tz="UTC")}
    rw_e = (entry["r0"] if weth_is_0 else entry["r1"]) / 1e18
    rt_e = (entry["r1"] if weth_is_0 else entry["r0"])
    peak_weth = rw_e
    for h in HORIZONS_DEX:
        exit_s = next((s for s in syncs
                       if ts_of(s["block"]) >= t_entry + h * DAY), None)
        rug_fallback = exit_s is None
        if rug_fallback:
            exit_s = syncs[-1]
        hdr_x = header(exit_s["block"])
        eth_x = eth_usd_at(hdr_x["ts"], ethusd)
        rw_x = (exit_s["r0"] if weth_is_0 else exit_s["r1"]) / 1e18
        rt_x = (exit_s["r1"] if weth_is_0 else exit_s["r0"])
        for notional in NOTIONALS:
            weth_in = notional / eth_e
            # raw token units throughout — v2 math is decimals-invariant
            tok = v2_buy(weth_in, rw_e, rt_e)
            weth_out = v2_sell(tok, rw_x, rt_x) if rt_x > 0 else 0.0
            gas_usd = (GAS_SWAP * (hdr_e["basefee"] + TIP_WEI) / 1e18 * eth_e
                       + GAS_SWAP * (hdr_x["basefee"] + TIP_WEI) / 1e18 * eth_x)
            ret = (weth_out * eth_x - gas_usd) / notional - 1.0
            key = f"ret{h}" if notional == NOTIONALS[0] else f"ret{h}_s{int(notional)}"
            row[key] = float(ret)
        row[f"rug{h}"] = bool(rug_fallback or rw_x < 0.1 * peak_weth)
    return row


def main() -> None:
    ts_of = load_anchors()
    ethusd = eth_usd_series()
    pools = sorted((RAW / "pools").glob("*.json"))
    rows, dead = [], 0
    for p in pools:
        r = pool_event(json.loads(p.read_text()), ts_of, ethusd)
        if r is None:
            continue
        if r.get("dead_before_entry"):
            dead += 1
            continue
        rows.append(r)
    tab = pd.DataFrame(rows).set_index("pair").sort_values("list_date")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_parquet(OUT_DIR / "dex_events.parquet")
    stats = {}
    for h in HORIZONS_DEX:
        st = p0_stats(tab, f"ret{h}")
        st["stress_5k_mean"] = float(tab[f"ret{h}_s5000"].mean())
        st["rug_rate"] = float(tab[f"rug{h}"].mean())
        stats[f"dex_{h}d"] = st
        ledger_append("predlab_nlst_dex", cell=f"{h}d", model="event_study",
                      config={"horizon": h, "notional_usd": 1000,
                              "fee": 0.003, "gas_model": "150k*(basefee+2gwei)*2",
                              "window": list(DEV)},
                      metrics={k: v for k, v in st.items()
                               if not isinstance(v, dict)})
    per_q = tab.groupby("quarter")["ret7"].agg(["count", "mean", "median"])
    payload = {"n_events": int(len(tab)), "dead_before_entry": dead,
               "stats": stats,
               "per_quarter_descriptive": per_q.round(4).to_dict("index")}
    p = write_result("dex_p0", payload)
    print(f"dex: n={len(tab)} dead_before_entry={dead} -> {p}")
    for name, st in stats.items():
        print(f"  {name}: n={st['n']} mean={st['mean']:+.4f} t={st['nw_t']:+.2f} "
              f"p={st['nw_p']:.4f} med={st['median']:+.4f} "
              f"rug={st['rug_rate']:.2f} stress5k={st['stress_5k_mean']:+.4f}")


if __name__ == "__main__":
    main()
