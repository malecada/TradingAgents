"""smw_xs step 5 — wallet-day aggregation, PIT track record, F1–F4 features.

Charter: docs/superpowers/specs/2026-09-04-smw-xs-charter.md (frozen).
  1. raw swap parquet -> (sym, day, wallet) net_usd / gross_usd (block time by
     interpolation on anchors.parquet; USD = quote x ETH close of the same UTC
     day for WETH, 1 for stables). Totals per (sym, day) are taken over ALL
     recipients before any exclusion (denominators).
  2. contract exclusion: eth_getCode (batched) for every wallet with >= 5
     net-buy days in the universe plus the 2,000 largest by gross volume;
     non-empty code -> excluded from every wallet-level quantity.
  3. episodes: (wallet, sym, day) with net_usd > 0 while sym is in the
     universe; ret7 = close[d+7]/close[d] - 1; completion day d+7.
  4. daily loop: record = expanding mean over episodes with completion < t;
     qualified >= 5; smart = record >= 80th percentile of qualified records.
  5. F1 smart net-buy share, F2 smart buyer breadth, F3 smart net-sell
     share, F4 log buyer-breadth acceleration (7-day baseline).
Outputs data/predlab/smw/features.parquet (long, in-universe days only),
qualified_daily.parquet, contracts.json, feature_build.json (diagnostics).
Nothing here touches a next-day return.

Run: nohup python scripts/predlab_smw_features.py > data/predlab/smw/features.log 2>&1 &
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import rpc_pool  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
RAW = SMW / "raw"
PANELS = ROOT / "data" / "predlab" / "t7_panels"
MIN_EPISODES = 5
SMART_Q = 0.80
EP_HORIZON = 7
F4_LOOKBACK = 7
TOP_GROSS_CHECK = 2000
DAY = 86_400
DEV_END = "2025-03-31"


# ------------------------------------------------------------ pure functions

def smart_sets(episodes: pd.DataFrame, days: np.ndarray, n_wallets: int,
               min_ep: int = MIN_EPISODES, q: float = SMART_Q):
    """episodes: columns wallet (int), complete_day (int day number), ret.
    days: sorted int day numbers to evaluate. Yields (day, smart_mask(bool[n_wallets]),
    n_qualified, cut) with the record built from episodes whose completion
    day < day (strictly before)."""
    ep = episodes.sort_values("complete_day")
    ew, ec, er = ep["wallet"].to_numpy(), ep["complete_day"].to_numpy(), ep["ret"].to_numpy()
    sums = np.zeros(n_wallets)
    cnts = np.zeros(n_wallets, dtype=np.int64)
    ptr = 0
    for d in days:
        while ptr < len(ec) and ec[ptr] < d:
            sums[ew[ptr]] += er[ptr]
            cnts[ew[ptr]] += 1
            ptr += 1
        qual = cnts >= min_ep
        nq = int(qual.sum())
        if nq == 0:
            yield d, np.zeros(n_wallets, dtype=bool), 0, np.nan
            continue
        rec = np.full(n_wallets, np.nan)
        rec[qual] = sums[qual] / cnts[qual]
        cut = float(np.quantile(rec[qual], q))
        yield d, qual & (rec >= cut), nq, cut


def day_features(sym: np.ndarray, wallet: np.ndarray, net: np.ndarray,
                 smart: np.ndarray, gross_total: dict) -> dict:
    """One day's F1/F2/F3 per sym from that day's (sym, wallet, net) rows
    (contracts already removed). gross_total: sym -> total gross over ALL
    recipients. Returns sym -> (f1, f2, f3)."""
    is_smart = smart[wallet]
    out = {}
    for s in np.unique(sym):
        m = sym == s
        g = gross_total.get(s, 0.0)
        ms = m & is_smart
        buy = ms & (net > 0)
        sell = ms & (net < 0)
        f1 = float(net[buy].sum() / g) if g > 0 else np.nan
        f3 = float(-net[sell].sum() / g) if g > 0 else np.nan
        out[s] = (f1, float(buy.sum()), f3)
    return out


def f4_acceleration(n_buyers: pd.Series, lookback: int = F4_LOOKBACK) -> pd.Series:
    """n_buyers: daily series on a complete calendar (missing days = 0).
    log(n_d / mean(n_{d-7..d-1})); NaN where the baseline is 0."""
    base = n_buyers.shift(1).rolling(lookback, min_periods=lookback).mean()
    out = np.log(n_buyers.replace(0, np.nan) / base.replace(0, np.nan))
    return out.where((base > 0) & (n_buyers > 0))


# ------------------------------------------------------------ pipeline

def load_meta():
    pools = json.loads((SMW / "pools.json").read_text())["by_symbol"]
    universe = json.loads((SMW / "universe.json").read_text())
    pool_sym = {p["pool"]: (sym, p["quote"]) for sym, plist in pools.items() for p in plist}
    anchors = pd.read_parquet(SMW / "anchors.parquet").sort_values("block")
    close = pd.read_parquet(PANELS / "close.parquet")
    close = close[close.index <= DEV_END]
    return pool_sym, universe, anchors, close


def aggregate_raw(pool_sym, anchors, eth_close_by_day: dict, wallet_ids: dict):
    """Stream every raw chunk into (sym, day, wallet) rows + (sym, day) totals."""
    ab, at = anchors["block"].to_numpy(dtype=float), anchors["ts"].to_numpy(dtype=float)
    parts, totals = [], []
    files = sorted(RAW.glob("*/*.parquet"))
    t0 = time.time()
    n_swaps = 0
    for i, f in enumerate(files):
        df = pd.read_parquet(f)
        if df.empty:
            continue
        df = df.drop_duplicates(["pool", "block", "log_index"])
        n_swaps += len(df)
        ts = np.interp(df["block"].to_numpy(dtype=float), ab, at)
        day = (ts // DAY).astype(np.int64)
        sym = df["pool"].map(lambda p: pool_sym[p][0])
        quote = df["pool"].map(lambda p: pool_sym[p][1])
        px = np.where(quote.to_numpy() == "WETH",
                      pd.Series(day).map(eth_close_by_day).fillna(np.nan).to_numpy(), 1.0)
        usd = df["quote_amt"].to_numpy() * px
        w = df["recipient"].map(lambda a: wallet_ids.setdefault(a, len(wallet_ids))).to_numpy()
        g = pd.DataFrame({"sym": sym.to_numpy(), "day": day, "wallet": w,
                          "net": usd, "gross": np.abs(usd)})
        g = g.dropna(subset=["net"])
        agg = g.groupby(["sym", "day", "wallet"], sort=False).agg(net=("net", "sum"), gross=("gross", "sum"),
                                                                   n=("gross", "size")).reset_index()
        parts.append(agg)
        totals.append(g.groupby(["sym", "day"], sort=False)["gross"].sum().reset_index())
        if i % 200 == 0:
            print(f"aggregate {i}/{len(files)} swaps={n_swaps} wallets={len(wallet_ids)} "
                  f"{time.time() - t0:.0f}s", flush=True)
    W = pd.concat(parts, ignore_index=True)
    W = W.groupby(["sym", "day", "wallet"], sort=False).agg(net=("net", "sum"), gross=("gross", "sum"),
                                                           n=("n", "sum")).reset_index()
    T = pd.concat(totals, ignore_index=True).groupby(["sym", "day"], sort=False)["gross"].sum().reset_index()
    return W, T, n_swaps


def contract_flags(addresses: list[str]) -> dict:
    cache_p = SMW / "code_cache.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    todo = [a for a in addresses if a not in cache]
    print(f"getCode: {len(todo)} to check ({len(cache)} cached)", flush=True)
    for i in range(0, len(todo), 100):
        batch = todo[i:i + 100]
        res = rpc_pool.rpc_batch("eth_getCode", [[a, "latest"] for a in batch])
        for a, r in zip(batch, res):
            cache[a] = bool(r and r != "0x")
        if (i // 100) % 50 == 0:
            cache_p.write_text(json.dumps(cache))
            print(f"getCode {i}/{len(todo)} {rpc_pool.get_pool().stats()}", flush=True)
    cache_p.write_text(json.dumps(cache))
    return {a: cache[a] for a in addresses}


def main() -> None:
    pool_sym, universe, anchors, close = load_meta()
    days_idx = close.index
    eth = close["ETHUSDT"]
    eth_by_day = {int(d.timestamp() // DAY): float(v) for d, v in eth.dropna().items()}
    wallet_ids: dict[str, int] = {}
    W, T, n_swaps = aggregate_raw(pool_sym, anchors, eth_by_day, wallet_ids)
    print(f"W rows {len(W)}  totals {len(T)}  wallets {len(wallet_ids)}  swaps {n_swaps}", flush=True)

    # in-universe (sym, day) membership from the monthly universe
    uni_days = set()
    months = sorted(universe)
    for i, m in enumerate(months):
        lo = pd.Timestamp(m, tz="UTC")
        hi = pd.Timestamp(months[i + 1], tz="UTC") if i + 1 < len(months) else lo + pd.offsets.MonthBegin(1)
        d0, d1 = int(lo.timestamp() // DAY), int(hi.timestamp() // DAY)
        for s in universe[m]:
            for d in range(d0, d1):
                uni_days.add((s, d))
    W["in_uni"] = [(s, d) in uni_days for s, d in zip(W["sym"], W["day"])]

    # contract exclusion
    buy_days = W[W["in_uni"] & (W["net"] > 0)].groupby("wallet").size()
    cand = set(buy_days[buy_days >= MIN_EPISODES].index)
    top = W.groupby("wallet")["gross"].sum().nlargest(TOP_GROSS_CHECK).index
    cand |= set(top)
    id_to_addr = {v: k for k, v in wallet_ids.items()}
    flags = contract_flags([id_to_addr[w] for w in sorted(cand)])
    is_contract = np.zeros(len(wallet_ids), dtype=bool)
    for w in cand:
        is_contract[w] = flags[id_to_addr[w]]
    contract_gross = float(W.loc[is_contract[W["wallet"].to_numpy()], "gross"].sum())
    print(f"contracts: {int(is_contract.sum())} of {len(cand)} checked; "
          f"gross share {contract_gross / W['gross'].sum():.3f}", flush=True)
    Wc = W[~is_contract[W["wallet"].to_numpy()]].reset_index(drop=True)

    # episodes
    close_by = {s: close[s] for s in close.columns}
    ep = Wc[Wc["in_uni"] & (Wc["net"] > 0)][["sym", "day", "wallet"]].copy()
    d_ts = pd.to_datetime(ep["day"] * DAY, unit="s", utc=True)
    r7 = np.full(len(ep), np.nan)
    for s, idx in ep.groupby("sym").indices.items():
        c = close_by.get(s)
        if c is None:
            continue
        c0 = c.reindex(d_ts.iloc[idx]).to_numpy()
        c7 = c.reindex(d_ts.iloc[idx] + pd.Timedelta(days=EP_HORIZON)).to_numpy()
        r7[idx] = c7 / c0 - 1.0
    ep["ret"] = r7
    ep["complete_day"] = ep["day"] + EP_HORIZON
    ep = ep.dropna(subset=["ret"])
    print(f"episodes {len(ep)} over {ep['wallet'].nunique()} wallets", flush=True)

    # daily loop: smart sets + F1-F3
    gross_total = {(s, d): g for s, d, g in zip(T["sym"], T["day"], T["gross"])}
    Wu = Wc[Wc["in_uni"]]
    by_day = {d: g for d, g in Wu.groupby("day")}
    all_days = np.array(sorted(by_day))
    n_w = len(wallet_ids)
    feat_rows, qual_rows = [], []
    for d, smart, nq, cut in smart_sets(ep[["wallet", "complete_day", "ret"]], all_days, n_w):
        g = by_day[d]
        gt = {s: gross_total.get((s, d), 0.0) for s in g["sym"].unique()}
        if nq > 0:
            f = day_features(g["sym"].to_numpy(), g["wallet"].to_numpy(), g["net"].to_numpy(), smart, gt)
        else:
            f = {s: (np.nan, np.nan, np.nan) for s in gt}
        for s, (f1, f2, f3) in f.items():
            feat_rows.append({"sym": s, "day": d, "f1": f1, "f2": f2, "f3": f3, "gross_total": gt[s]})
        qual_rows.append({"day": d, "n_qualified": nq, "cut": cut, "n_smart": int(smart.sum())})
    F = pd.DataFrame(feat_rows)
    Q = pd.DataFrame(qual_rows)

    # F4 on the full calendar per sym (lookback days included; missing = 0 buyers)
    nb = Wc[Wc["net"] > 0].groupby(["sym", "day"])["wallet"].nunique().rename("n_buyers").reset_index()
    f4_parts = []
    for s, g in nb.groupby("sym"):
        ser = g.set_index("day")["n_buyers"]
        full = pd.Series(0.0, index=np.arange(ser.index.min(), ser.index.max() + 1))
        full.loc[ser.index] = ser.to_numpy()
        f4 = f4_acceleration(full)
        f4_parts.append(pd.DataFrame({"sym": s, "day": full.index, "n_buyers": full.to_numpy(), "f4": f4.to_numpy()}))
    F4 = pd.concat(f4_parts, ignore_index=True)
    F = F.merge(F4, on=["sym", "day"], how="left")
    F["date"] = pd.to_datetime(F["day"] * DAY, unit="s", utc=True)
    Q["date"] = pd.to_datetime(Q["day"] * DAY, unit="s", utc=True)
    F.to_parquet(SMW / "features.parquet", index=False)
    Q.to_parquet(SMW / "qualified_daily.parquet", index=False)
    diag = {"n_swaps": int(n_swaps), "n_wallets": int(n_w), "n_wallet_days": int(len(W)),
            "n_checked": int(len(cand)), "n_contracts": int(is_contract.sum()),
            "contract_gross_share": contract_gross / float(W["gross"].sum()),
            "n_episodes": int(len(ep)), "n_feature_rows": int(len(F)),
            "first_day_100_qualified": (Q.loc[Q["n_qualified"] >= 100, "date"].min().strftime("%Y-%m-%d")
                                        if (Q["n_qualified"] >= 100).any() else None),
            "days_with_smart_set": int((Q["n_qualified"] > 0).sum()),
            "coverage_f1_share": float(F["f1"].notna().mean()), "coverage_f4_share": float(F["f4"].notna().mean())}
    (SMW / "feature_build.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps(diag, indent=1), flush=True)


if __name__ == "__main__":
    main()
