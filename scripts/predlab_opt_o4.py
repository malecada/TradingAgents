"""O-05 / stage O4 — vol-target overlay re-tune on the ewma_20 champion book
(predlab_opt.stages.O4). New claim set, distinct from the frozen pp2 vt10
confirmation on the old S1 book (disclosed).

Overlay: scale_t = clip(target_ann / sigma_hat_t, 0, cap), sigma_hat from
book returns SHIFTED 1 day. Estimators: naive20 (trailing 20d std), ewma20
(span-20 EWMA std), har (rolling-500d OLS HAR on squared book returns).
b100 variant: scale forced to 0 while universe breadth < 100 names (O3
lesson probe). Costs (pp2 formula): 5bp x (scale_t x underlying turnover
+ |d scale| x gross 2).

Gates (frozen pre-run, pp2 precedent): MaxDD reduction >= 25% vs raw AND
net SR >= 0.9 x raw net SR, both on the FULL window; V-consistency
(overlay SR_V >= 0.5 x overlay SR_D); n_trials=12 disclosed. ONE config
adopted at most.

Subcommands: register | run
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

from tradingagents.predlab import opt, registry  # noqa: E402
from tradingagents.predlab.pp import ann_sr, max_drawdown  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT = DATA_ROOT / "predlab" / "opt_o4_results.json"
FULL = ("2021-01-01", "2026-07-01")
ANN = 365.0

GRID: "dict[str, dict]" = {}
for tgt in (0.10, 0.15, 0.20):
    for est in ("naive20", "ewma20", "har"):
        GRID[f"vt{int(tgt*100)}_{est}"] = {"target": tgt, "est": est, "cap": 2.0}
GRID["vt10_naive20_cap15"] = {"target": 0.10, "est": "naive20", "cap": 1.5}
GRID["vt15_naive20_cap15"] = {"target": 0.15, "est": "naive20", "cap": 1.5}
GRID["vt15_naive20_b100"] = {"target": 0.15, "est": "naive20", "cap": 2.0,
                             "breadth_floor": 100}


def register() -> None:
    gates = json.loads(GATES.read_text())
    stages = gates["predlab_opt"]["stages"]
    if "O4" in stages:
        print("stage O4 already frozen — refusing")
        sys.exit(1)
    stages["O4"] = {
        "frozen_utc": "2026-08-03",
        "axis": "vol-target overlay re-tune (new claim set; pp2 vt10 claim untouched)",
        "base_book": "ewma_20 eq-quintile-daily top-200 (chain seq 1)",
        "grid": GRID,
        "n_configs": len(GRID),
        "gates": ("MaxDD reduction >=25% vs raw AND net SR >= 0.9 x raw (full "
                  "window) AND overlay SR_V >= 0.5 x overlay SR_D; one adoption max; "
                  "n_trials=12 disclosed"),
        "cost_model": "5bp x (scale x underlying turnover + |d scale| x gross 2)",
        "window": list(FULL),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"frozen stage O4: {len(GRID)} configs")


def sigma_hat(net: pd.Series, est: str) -> pd.Series:
    """Annualized book-vol forecast, information through t-1 only."""
    if est == "naive20":
        s = net.rolling(20).std()
    elif est == "ewma20":
        s = net.ewm(span=20).std()
    elif est == "har":
        r2 = net ** 2
        x1 = r2.rolling(1).mean()
        x5 = r2.rolling(5).mean()
        x22 = r2.rolling(22).mean()
        X = pd.concat([x1, x5, x22], axis=1).to_numpy()
        y = r2.to_numpy()
        pred = np.full(len(y), np.nan)
        W = 500
        for t in range(W + 22, len(y)):
            Xw = X[t - W:t - 1]
            yw = y[t - W + 1:t]  # y_{i+1} on X_i
            ok = ~np.isnan(Xw).any(axis=1) & ~np.isnan(yw)
            beta, *_ = np.linalg.lstsq(
                np.column_stack([np.ones(ok.sum()), Xw[ok]]), yw[ok], rcond=None)
            xt = X[t - 1]
            if not np.isnan(xt).any():
                pred[t] = max(float(beta[0] + xt @ beta[1:]), 1e-10)
        s = pd.Series(np.sqrt(pred), index=net.index)
        return (s * np.sqrt(ANN)).shift(0)  # pred[t] already uses info <= t-1
    else:
        raise ValueError(est)
    return (s * np.sqrt(ANN)).shift(1)


def run() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_opt"]["stages"].get("O4") is None:
        print("stage O4 not frozen — run `register` first")
        sys.exit(1)
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    sig = opt.build_signal(park, close, "ewma_20")
    raw = opt.run_ls(sig, ret, uni, fund, opt.OptConfig(), *FULL)
    df = raw["rets"]
    net, gross_to = df["net"], df["turnover"]
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(df.index)

    raw_sr, raw_dd = raw["sr_net"], raw["maxdd"]
    D_hi = pd.Timestamp(opt.DESIGN_D[1], tz="UTC")
    res = {"stage": "O4", "raw": {"sr_net": raw_sr, "maxdd": raw_dd},
           "configs": {}}
    print(f"RAW: SR {raw_sr:+.3f} dd {raw_dd:.1%}", flush=True)

    for name, spec in GRID.items():
        sh = sigma_hat(net, spec["est"])
        scale = (spec["target"] / sh).clip(0.0, spec["cap"]).fillna(0.0)
        if "breadth_floor" in spec:
            scale = scale.where(breadth >= spec["breadth_floor"], 0.0)
        o_gross = scale * net
        cost = 5.0 / 1e4 * (scale * gross_to + scale.diff().abs().fillna(0.0) * 2.0)
        o_net = o_gross - cost
        dd = max_drawdown(o_net.to_numpy())
        sr = ann_sr(o_net.to_numpy())
        sr_d = ann_sr(o_net[o_net.index <= D_hi].to_numpy())
        sr_v = ann_sr(o_net[o_net.index > D_hi].to_numpy())
        row = {"sr_net": sr, "sr_D": sr_d, "sr_V": sr_v, "maxdd": dd,
               "avg_scale": float(scale.mean()),
               "dd_reduction": 1 - dd / raw_dd,
               "gate_dd": bool(1 - dd / raw_dd >= 0.25),
               "gate_sr": bool(sr >= 0.9 * raw_sr),
               "gate_v": bool(sr_v >= 0.5 * sr_d)}
        row["pass"] = bool(row["gate_dd"] and row["gate_sr"] and row["gate_v"])
        res["configs"][name] = row
        registry.log_trial("predlab_opt", "O4_overlay", name, spec, FULL,
                           {"sr_net": sr, "maxdd": dd,
                            "dd_reduction": row["dd_reduction"]})
        print(f"{name}: SR {sr:+.3f} (D {sr_d:+.3f}/V {sr_v:+.3f}) dd {dd:.1%} "
              f"(-{row['dd_reduction']:.0%}) scale {row['avg_scale']:.2f} "
              f"{'PASS' if row['pass'] else 'fail'}", flush=True)

    passing = {k: v for k, v in res["configs"].items() if v["pass"]}
    # selection rule: among passers, max net SR; tie-break lower MaxDD
    chosen = max(passing, key=lambda k: (passing[k]["sr_net"], -passing[k]["maxdd"])) \
        if passing else None
    res["passing"] = sorted(passing)
    res["chosen"] = chosen
    print(f"\npassing: {sorted(passing) or 'NONE'}; chosen: {chosen}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    {"register": register, "run": run}[sys.argv[1]]()
