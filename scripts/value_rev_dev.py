"""value_rev dev runner (gates.json["value_rev"], charter 2026-09-04).

  python scripts/value_rev_dev.py p0 --snap1 2026-09-04 --snap2 2026-09-18   # restatement probe (needs snapshot 2 >= 14 d later)
  python scripts/value_rev_dev.py probes --snap1 2026-09-04                    # P1 breadth, P2 lag (requires passing p0 file)
  python scripts/value_rev_dev.py grid --snap1 2026-09-04                      # 4 cells + controls + placebos; refuses without passing probes

Signal: log(mcap / trailing-90d sum of fees|revenue), cross-sectional z per
day, lag 2 d; weekly Monday dollar-neutral L/S via the section-46 engine
(`carry_xs.run_ls_portfolio`, simple returns), 10 bp/side, realized funding,
rf 4.5 %/yr on full capital. Controls C1 (30-d vol) / C2 (reversal) through the
identical pipeline. mcap = CoinMetrics community CapMrktCurUSD.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL  # noqa: E402
from scripts.value_xs_dev import (  # noqa: E402
    circular_shift_columns, dsr_or_nan, rank_shuffle_columns, unique_config_hashes,
)
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.xsect.carry_xs import RF_DAILY, run_ls_portfolio  # noqa: E402
from tradingagents.xsect.ls_common import ls_weights, sharpe_365  # noqa: E402
from tradingagents.xsect.portfolio import maxdd, rank_placebo_pvalue  # noqa: E402
from tradingagents.xsect.universe import load_klines, weekly_rebalance_dates  # noqa: E402
from tradingagents.xsect.value_xs import control_signal, load_fundamentals, simple_returns  # noqa: E402

FEES = ROOT / "data/xsect/fees"
FUND_DIR = ROOT / "data/xsect/fundamentals"
FUNDING_DIR = ROOT / "data/xsect/funding"
KL = ROOT / "data/xsect/klines"
OUT = ROOT / "data/rebuild/value_rev"
GATES = ROOT / "data/rebuild/gates.json"
DEV = ("2021-01-01", "2025-03-31")
WINDOW = 90
LAG = 2
COST_BPS = 10.0
LEG_FRAC = {"tercile": 1 / 3, "decile": 0.1}
GRID = [("fees", "tercile"), ("fees", "decile"), ("revenue", "tercile"), ("revenue", "decile")]
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "dsr_min": 0.9, "delta_min": 0.0}
N_PLACEBO = 500
P0 = {"min_gap_days": 14, "stale_days": 30, "tol_change": 0.10, "max_share": 0.05}


def load_fees(snap: str) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_parquet(p) for p in (FEES / snap).glob("*.parquet")}


def main_p0(a) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d1, d2 = pd.Timestamp(a.snap1), pd.Timestamp(a.snap2)
    assert (d2 - d1).days >= P0["min_gap_days"], "snapshot 2 must be >= 14 days after snapshot 1"
    f1, f2 = load_fees(a.snap1), load_fees(a.snap2)
    cut = pd.Timestamp(a.snap1, tz="UTC") - pd.Timedelta(days=P0["stale_days"])
    n, changed = 0, 0
    per = {}
    for s in sorted(set(f1) & set(f2)):
        j = f1[s][["fees_usd"]].join(f2[s][["fees_usd"]], lsuffix="_1", rsuffix="_2", how="inner")
        j = j[(j.index <= cut) & (j["fees_usd_1"] > 0)]
        if j.empty:
            continue
        rel = (j["fees_usd_2"] - j["fees_usd_1"]).abs() / j["fees_usd_1"]
        c = int((rel > P0["tol_change"]).sum())
        per[s] = {"n": int(len(j)), "changed": c}
        n += len(j)
        changed += c
    share = changed / n if n else float("nan")
    res = {"snap1": a.snap1, "snap2": a.snap2, "n_protocol_days": n, "n_changed_gt_10pct": changed, "share_changed": share,
           "n_symbols_common": len(per), "symbols_only_in_1": sorted(set(f1) - set(f2)), "symbols_only_in_2": sorted(set(f2) - set(f1)),
           "per_symbol": per, "pass": bool(n > 0 and share <= P0["max_share"])}
    (OUT / "p0_restatement.json").write_text(json.dumps(res, indent=1))
    print(f"P0 share changed {share:.4f} over {n} symbol-days -> pass={res['pass']}")


def build_inputs(snap: str) -> dict:
    klines = load_klines(KL)
    fund = load_fundamentals(FUND_DIR, ASSET_TO_SYMBOL)
    fees = load_fees(snap)
    syms = sorted(set(fund) & set(fees) & set(klines))
    days = pd.date_range("2020-06-01", DEV[1], freq="D", tz="UTC")
    mcap = pd.DataFrame({s: fund[s]["CapMrktCurUSD"].reindex(days) for s in syms}, index=days)
    ratios = {}
    for metric in ("fees", "revenue"):
        col = f"{metric}_usd"
        den = pd.DataFrame({s: fees[s][col].reindex(days).fillna(0.0).rolling(WINDOW, min_periods=WINDOW).sum() for s in syms}, index=days)
        ratios[metric] = mcap / den.where(den > 0)
    return {"klines": klines, "syms": syms, "days": days, "ratios": ratios, "mcap": mcap, "fees": fees}


def zsig(ratio: pd.DataFrame) -> pd.DataFrame:
    lg = np.log(ratio.where(ratio > 0))
    z = lg.sub(lg.mean(axis=1), axis=0).div(lg.std(axis=1, ddof=1).where(lg.std(axis=1, ddof=1) > 0), axis=0)
    return z.shift(LAG)


def funding_matrix(syms, days) -> pd.DataFrame:
    cols = {}
    for s in syms:
        p = FUNDING_DIR / f"{s}.parquet"
        if p.exists():
            f = pd.read_parquet(p)["fundingRate"]
            cols[s] = f.groupby(f.index.tz_convert("UTC").normalize()).sum().reindex(days)
        else:
            cols[s] = pd.Series(np.nan, index=days)
    return pd.DataFrame(cols, index=days)


def main_probes(a) -> None:
    p0 = json.loads((OUT / "p0_restatement.json").read_text())
    if not p0["pass"]:
        raise SystemExit("P0 restatement FAIL -- STOP")
    b = build_inputs(a.snap1)
    dev = b["days"][(b["days"] >= DEV[0]) & (b["days"] <= DEV[1])]
    rb = weekly_rebalance_dates(DEV[0], DEV[1])
    breadth = {}
    for metric in ("fees", "revenue"):
        S = zsig(b["ratios"][metric]).loc[dev]
        wk = S.reindex(rb).notna().sum(axis=1)
        breadth[metric] = {"median": float(wk.median()), "min": float(wk.min()), "n_weeks": int(len(wk))}
    p1_pass = any(v["median"] >= 20 for v in breadth.values())
    snap_ts = pd.Timestamp(a.snap1, tz="UTC")
    lags = [(snap_ts - b["fees"][s].index.max()).days for s in b["syms"]]
    p2 = {"median_lag_days": float(np.median(lags)), "max_lag_days": int(max(lags)), "pass": bool(np.median(lags) <= 2)}
    res = {"n_symbols": len(b["syms"]), "symbols": b["syms"], "P1_breadth": breadth, "P1_pass": bool(p1_pass), "P2_lag": p2,
           "stop": not (p1_pass and p2["pass"])}
    (OUT / "probes.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "symbols"}, indent=1))


def main_grid(a) -> None:
    probes = json.loads((OUT / "probes.json").read_text())
    if probes["stop"]:
        raise SystemExit("probes STOP")
    if (OUT / "grid.json").exists():
        raise SystemExit("grid.json exists -- one-shot")
    b = build_inputs(a.snap1)
    days, syms = b["days"], b["syms"]
    dev = days[(days >= DEV[0]) & (days <= DEV[1])]
    R = simple_returns(b["klines"], days, syms).loc[dev]
    F = funding_matrix(syms, days).loc[dev]
    M = b["mcap"].notna().loc[dev]
    rb = weekly_rebalance_dates(DEV[0], DEV[1])

    def port(S, valid, leg):
        W = ls_weights(S.index, S, valid, rb, leg)
        return run_ls_portfolio(W, R.reindex_like(W), F.reindex_like(W), cost_bps=COST_BPS, rf_daily=RF_DAILY)

    controls = {}
    for kind in ("vol", "reversal"):
        C = control_signal(b["klines"], days, syms, kind).loc[dev]
        controls[kind] = sharpe_365(port(C, M & C.notna(), LEG_FRAC["decile"]))
    n_before = unique_config_hashes()
    rng = np.random.default_rng(20260904)
    results = []
    for metric, breadth in GRID:
        S = zsig(b["ratios"][metric]).loc[dev]
        valid = M & S.notna()
        leg = LEG_FRAC[breadth]
        p = port(S, valid, leg)
        sr = sharpe_365(p)
        srA = [sharpe_365(port(circular_shift_columns(S, rng), valid, leg)) for _ in range(N_PLACEBO)]
        srB = [sharpe_365(port(rank_shuffle_columns(S, rng), valid, leg)) for _ in range(N_PLACEBO)]
        pA, pB = rank_placebo_pvalue(sr, srA), rank_placebo_pvalue(sr, srB)
        d = dsr_or_nan(p, len(GRID))
        cfg = {"metric": f"mcap_over_{metric}_{WINDOW}d", "breadth": breadth, "leg_frac": leg, "lag": LAG, "cost_bps": COST_BPS}
        m = {"net_sr": sr, "maxdd": float(maxdd(p)), "placebo_pA": pA, "placebo_pB": pB, "placebo_p_worse": max(pA, pB), "dsr_n4": d,
             "dsr_cumulative": dsr_or_nan(p, n_before + len(GRID)), "delta_c1": sr - controls["vol"], "delta_c2": sr - controls["reversal"],
             "n_days": int(len(p))}
        checks = {"net_sr": sr >= GATE["net_sr_min"], "placebo": max(pA, pB) <= GATE["placebo_p_max"], "dsr": bool(d >= GATE["dsr_min"]),
                  "delta_c1": m["delta_c1"] > GATE["delta_min"], "delta_c2": m["delta_c2"] > GATE["delta_min"]}
        log_trial("value_rev", cfg, DEV, m)
        results.append({"config": cfg, "metrics": m, "checks": checks, "pass": all(checks.values())})
        print(f"{metric}/{breadth}: SR {sr:+.3f} p {max(pA,pB):.3f} dsr {d:.3f} dC1 {m['delta_c1']:+.2f} dC2 {m['delta_c2']:+.2f} pass={all(checks.values())}", flush=True)
    payload = {"controls": controls, "results": results, "n_pass": sum(r["pass"] for r in results), "n_trials_before": n_before}
    (OUT / "grid.json").write_text(json.dumps(payload, indent=1, default=str))
    print(f"value_rev grid: {payload['n_pass']}/4 pass; controls {controls}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["p0", "probes", "grid"])
    ap.add_argument("--snap1", default="2026-09-04")
    ap.add_argument("--snap2", default=None)
    a = ap.parse_args()
    {"p0": main_p0, "probes": main_probes, "grid": main_grid}[a.cmd](a)
