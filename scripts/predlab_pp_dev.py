"""PP-02: dev-gate evaluation on the strategy-dev window (2021-01 -> 2025-03).

Evaluates the registered predlab_pp configs (6 S1 + 3 S2 + 4 S3 = 13),
logs one ledger row per config, applies the frozen dev gates, and freezes
ONE config per surviving candidate for the holdout one-shot (PP-03).
Placebos (dual-family) run on the selected config per candidate.
Uses STORED forecasts only — no model refitting.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import pp, registry  # noqa: E402
from tradingagents.predlab.meanstats import stationary_bootstrap_means  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
FC = DATA_ROOT / "predlab" / "forecasts"
DEV = ("2021-01-01", "2025-03-31")
SUBS = [("2021-2022", "2021-01-01", "2022-12-31"),
        ("2023-2024", "2023-01-01", "2024-12-31"),
        ("2025Q1", "2025-01-01", "2025-03-31")]
OUT = DATA_ROOT / "predlab" / "pp_dev_results.json"


def _load_fc(cell_dir: str, model: str) -> pd.DataFrame:
    df = pd.read_parquet(FC / cell_dir / f"{model}.parquet")
    return df.set_index(pd.DatetimeIndex(df["ts"]))[["y_true", "pred"]]


def _subperiods(rets: pd.Series) -> dict:
    out = {}
    for label, lo, hi in SUBS:
        seg = rets[(rets.index >= lo) & (rets.index <= hi)]
        if len(seg) >= 30:
            out[label] = float(seg.mean())
    return out


# ------------------------------------------------------------------ S1

def s1_inputs():
    from predlab_t7 import build_panels, monthly_universe

    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    hi = pd.Timestamp(DEV[1], tz="UTC")
    close = close[close.index <= hi]
    qv, park = qv.loc[close.index], park.loc[close.index]
    ret = np.log(close).diff()
    uni = monthly_universe(qv, top_n=200)
    sig = park.rolling(5).mean().shift(1)
    cache = DATA_ROOT / "predlab" / "pp_funding_daily.parquet"
    if cache.exists():
        fund = pd.read_parquet(cache).reindex(ret.index)
    else:
        used = sorted(uni.columns[uni.any(axis=0)])
        fund = pp.build_funding_daily(used, DATA_ROOT / "xsect" / "funding", ret.index)
        fund.to_parquet(cache)
    return sig, ret, uni, fund


def run_s1_dev():
    sig, ret, uni, fund = s1_inputs()
    rows = {}
    for weighting in ("eq", "rank"):
        for smooth in (1, 3, 5):
            key = f"s1_{weighting}_h{smooth}"
            r = pp.run_s1(sig, ret, uni, fund, weighting, smooth, *DEV)
            rows[key] = r
            registry.log_trial("predlab_pp", "S1_t7_lowvol_ls", key,
                               {"weighting": weighting, "smooth": smooth,
                                "costs": "5bp+funding"}, DEV,
                               {"sr_net": r["sr_net"], "sr_gross": r["sr_gross"],
                                "maxdd": r["maxdd"], "turnover": r["avg_turnover"]})
            print(f"{key}: net SR {r['sr_net']:+.2f} (gross {r['sr_gross']:+.2f}) "
                  f"turn {r['avg_turnover']:.2f} dd {r['maxdd']:.1%}", flush=True)
    return rows, (sig, ret, uni, fund)


def s1_placebos(best_key: str, inputs) -> dict:
    sig, ret, uni, fund = inputs
    _, weighting, smooth = best_key.split("_")
    smooth = int(smooth[1:])

    def sr_of(s):
        return pp.run_s1(s, ret, uni, fund, weighting, smooth, *DEV)["sr_net"]

    real = sr_of(sig)
    rng = np.random.default_rng(7)
    fam_a = []
    n = len(sig)
    for _ in range(200):
        k = int(rng.integers(30, n - 30))
        fam_a.append(sr_of(pd.DataFrame(np.roll(sig.to_numpy(), k, axis=0),
                                        index=sig.index, columns=sig.columns)))
    fam_b = []
    for d in range(200):
        rngb = np.random.default_rng(1000 + d)
        vals = sig.to_numpy().copy()
        for i in range(vals.shape[0]):
            row = vals[i]
            ok = ~np.isnan(row)
            row[ok] = rngb.permutation(row[ok])
        fam_b.append(sr_of(pd.DataFrame(vals, index=sig.index, columns=sig.columns)))
    return {"real_sr": real,
            "p_shift": pp.placebo_pvalue(real, fam_a),
            "p_xshuffle": pp.placebo_pvalue(real, fam_b)}


# ------------------------------------------------------------------ S2

def run_s2_dev():
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1d" / "BTCUSDT.parquet")
    harq = _load_fc("predlab_p2_ml/BTCUSDT_24h_T3_rv", "harq")["pred"]
    har = _load_fc("predlab_p2_ml/BTCUSDT_24h_T3_rv", "har_levels")["pred"]
    naive = store["rv"].rolling(20).mean().shift(1)
    ret = store["ret"]
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    rows = {}
    for name, fc in (("harq", harq), ("har_levels", har), ("naive20", naive)):
        f = fc[(fc.index >= lo) & (fc.index <= hi)].dropna()
        r = pp.run_s2(f, ret)
        rows[name] = r
        registry.log_trial("predlab_pp", "S2_harq_voltarget", name,
                           {"sigma_source": name, "target": 0.20, "cap": 3.0},
                           DEV, {"sr_net": r["sr_net"], "maxdd": r["maxdd"],
                                 "tracking_err": r["tracking_err"]})
        print(f"s2_{name}: TE {r['tracking_err']:.4f} SR {r['sr_net']:+.2f} "
              f"dd {r['maxdd']:.1%} avg_pos {r['avg_pos']:.2f}", flush=True)
    # bootstrap TE-difference gate: harq vs each baseline
    boot = {}
    for base in ("har_levels", "naive20"):
        a = (rows["harq"]["roll_vol"] - 0.20) ** 2
        b = (rows[base]["roll_vol"] - 0.20) ** 2
        common = a.index.intersection(b.index)
        d = (b.loc[common] - a.loc[common]).dropna().to_numpy()  # >0 = harq better
        means = stationary_bootstrap_means(d, n_boot=2000, mean_block=21)
        boot[base] = {"p_harq_better": float(np.mean(means <= 0)),
                      "te_reduction_pct": float(
                          100 * (rows[base]["tracking_err"] - rows["harq"]["tracking_err"])
                          / rows[base]["tracking_err"])}
        print(f"s2 harq vs {base}: TE reduction {boot[base]['te_reduction_pct']:+.1f}% "
              f"p={boot[base]['p_harq_better']:.4f}", flush=True)
    return rows, boot


# ------------------------------------------------------------------ S3

def run_s3_dev():
    fc = _load_fc("predlab_p2_ml/BTCUSDT_1h_T2_dir", "logit_lags5")
    store = pd.read_parquet(DATA_ROOT / "predlab" / "rv_1h" / "BTCUSDT.parquet")
    ret = store["ret"]
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    prob = fc["pred"][(fc.index >= lo) & (fc.index <= hi)]
    rows = {}
    for thresh in (0.50, 0.52):
        for smooth in (1, 24):
            key = f"s3_t{thresh}_h{smooth}"
            r = pp.run_s3(prob, ret, thresh, smooth)
            rows[key] = r
            registry.log_trial("predlab_pp", "S3_sign_filter_exploratory", key,
                               {"thresh": thresh, "smooth": smooth}, DEV,
                               {"sr_net": r["sr_net"], "maxdd": r["maxdd"],
                                "time_in_mkt": r["time_in_mkt"]})
            print(f"{key}: net SR {r['sr_net']:+.2f} tim {r['time_in_mkt']:.2f} "
                  f"dd {r['maxdd']:.1%}", flush=True)
    return rows, prob, ret


def main() -> None:
    if OUT.exists():
        print(f"dev results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    res = {"registered_utc": "2026-07-31"}

    print("== S1 T7 low-vol long-short ==", flush=True)
    s1, s1_in = run_s1_dev()
    best_s1 = max(s1, key=lambda k: s1[k]["sr_net"])
    res["S1"] = {k: {kk: v[kk] for kk in ("sr_net", "sr_gross", "maxdd",
                                          "avg_turnover", "n_days")}
                 for k, v in s1.items()}
    res["S1_best"] = best_s1
    res["S1_subperiods"] = _subperiods(s1[best_s1]["rets"]["net"])
    if s1[best_s1]["sr_net"] > 0:
        print(f"placebos on {best_s1} (2x200 draws)...", flush=True)
        res["S1_placebos"] = s1_placebos(best_s1, s1_in)
        print(res["S1_placebos"], flush=True)

    print("== S2 HARQ vol-target ==", flush=True)
    s2, boot = run_s2_dev()
    res["S2"] = {k: {"sr_net": v["sr_net"], "maxdd": v["maxdd"],
                     "tracking_err": v["tracking_err"], "avg_pos": v["avg_pos"]}
                 for k, v in s2.items()}
    res["S2_bootstrap"] = boot
    res["S2_subperiods"] = _subperiods(s2["harq"]["rets"])

    print("== S3 sign filter (exploratory) ==", flush=True)
    s3, prob, ret = run_s3_dev()
    best_s3 = max(s3, key=lambda k: s3[k]["sr_net"])
    res["S3"] = {k: {"sr_net": v["sr_net"], "maxdd": v["maxdd"],
                     "time_in_mkt": v["time_in_mkt"]}
                 for k, v in s3.items()}
    res["S3_best"] = best_s3

    # DSR at n_trials=13 for the two graduating candidates
    all_srs = ([v["sr_net"] for v in s1.values()]
               + [v["sr_net"] for v in s2.values()]
               + [v["sr_net"] for v in s3.values()])
    res["DSR"] = {
        "S1": pp.dsr(s1[best_s1]["sr_net"], all_srs, s1[best_s1]["n_days"],
                     s1[best_s1]["rets"]["net"].to_numpy()),
        "S3": pp.dsr(s3[best_s3]["sr_net"], all_srs, s3[best_s3]["n_hours"],
                     s3[best_s3]["rets"].to_numpy()),
    }
    print("DSR:", res["DSR"], flush=True)

    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwritten {OUT}", flush=True)


if __name__ == "__main__":
    main()
