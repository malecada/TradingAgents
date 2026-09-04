"""predlab_oflow P1 — one frozen config per P0 survivor (charter 2026-09-04).

  python scripts/predlab_oflow_p1.py

XS survivor: quintile long-short daily book via opt.run_ls (q 0.2, equal
weight, 5 bp taker + realized funding), signal = daily flow z with the dev sign
(P0 IC < 0 => reversal: long low-z / short high-z; run_ls longs the BOTTOM
quantile, so sig = z directly). Gates: net SR >= 1.0, circular-shift placebo
(500 draws, min shift 30 days, per-column independent shifts of the signal
panel) p < 0.10, 2x cost-stress keeps sign, max single-name |PnL| share <= 50 %,
convention swap (log booking) keeps sign. One-shot: refuses if a P1 verdict
exists. TS survivors: none at P0 (hourly cells failed), so the TS branch is
not exercised this cycle.
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
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_oflow_p0 import DEV_HI, DEV_LO, MIN_BREADTH, imbalance, load_1h, zscore  # noqa: E402
from predlab_xfam_lib import DEV, clip_dev, ledger_append, load_daily_panels  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402
from tradingagents.predlab.opt import OptConfig, cost_stress, monthly_universe, run_ls  # noqa: E402
from tradingagents.predlab.pp import build_funding_daily  # noqa: E402

OUT = ROOT / "data" / "predlab" / "oflow"
KEY = "predlab_oflow"
N_PLACEBO = 500
MIN_SHIFT = 30
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.10, "name_share_max": 0.5}
FUND_DIR = ROOT / "data" / "xsect" / "funding"


def sr(x: pd.Series) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd * np.sqrt(365)) if sd > 0 else 0.0


def build_inputs():
    p1h = load_1h()
    daily = load_daily_panels()
    close_d, qv_d = clip_dev(daily["close"]), clip_dev(daily["qv"])
    uni = monthly_universe(qv_d, 200)
    c, q, tb = p1h["close"], p1h["qv"], p1h["tb"]
    day = c.index.tz_convert("UTC").normalize()
    imb_d = imbalance(tb.groupby(day).sum(), q.groupby(day).sum())
    z_d = zscore(imb_d, 30)
    common = uni.columns.intersection(z_d.columns)
    idx = uni.index.intersection(z_d.index)
    idx = idx[(idx >= DEV_LO) & (idx <= DEV_HI)]
    sig = z_d.reindex(index=idx, columns=common).shift(1)        # row d uses z through d-1 (trades day-d return)
    ret = close_d.reindex(index=idx, columns=common).pct_change(fill_method=None)
    uni_c = uni.reindex(index=idx, columns=common).fillna(False)
    fund = build_funding_daily(list(common), FUND_DIR, idx)
    return sig, ret, uni_c, fund, idx


def book(sig, ret, uni, fund, cfg, log_booking=False) -> dict:
    r = ret if not log_booking else np.log1p(ret)
    return run_ls(sig, r, uni, fund, cfg, DEV[0], DEV[1])


def main() -> None:
    gates = registry.load_gates()
    if gates[KEY]["verdicts"].get("P1"):
        raise SystemExit("REFUSED: P1 verdict already recorded (one-shot)")
    res0 = json.loads((OUT / "p0_result.json").read_text())
    survivors = res0["survivors"]
    assert survivors == ["XS_24h_IC"], survivors
    t0 = time.time()
    sig, ret, uni, fund, idx = build_inputs()
    cfg = OptConfig(signal="flow_z30", top_n=200, adv_floor=0.0, q_frac=0.2, weighting="eq", smooth=1, cadence=1, buffer=0.0, taker_bp=5.0)
    real = book(sig, ret, uni, fund, cfg)
    net = real["rets"]["net"]
    sr_net = sr(net)
    stress = cost_stress(real, 2.0)
    sr_stress = sr(stress)
    logbook = book(sig, ret, uni, fund, cfg, log_booking=True)
    sr_log = sr(logbook["rets"]["net"])
    name_share = float(real["name_pnl"].abs().max() / real["name_pnl"].abs().sum()) if real["name_pnl"].abs().sum() > 0 else float("nan")
    print(f"real: net SR {sr_net:+.3f} gross SR {real['sr_gross']:+.3f} maxdd {real['maxdd']:.3f} turnover {real['avg_turnover']:.3f} "
          f"n_days {real['n_days']} stress2x {sr_stress:+.3f} log {sr_log:+.3f} name_share {name_share:.3f} ({time.time()-t0:.0f}s)", flush=True)
    # placebo: per-column independent circular shifts of the signal panel (min 30 days)
    rng = np.random.default_rng(7)
    null = []
    S = sig.to_numpy()
    n = len(sig)
    for i in range(N_PLACEBO):
        Sp = np.empty_like(S)
        for j in range(S.shape[1]):
            k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT))
            Sp[:, j] = np.roll(S[:, j], k)
        pb = run_ls(pd.DataFrame(Sp, index=sig.index, columns=sig.columns), ret, uni, fund, cfg, DEV[0], DEV[1])
        null.append(sr(pb["rets"]["net"]))
        if i % 100 == 0:
            print(f"  placebo {i}/{N_PLACEBO} t={time.time()-t0:.0f}s", flush=True)
    p = float((np.sum(np.asarray(null) >= sr_net) + 1) / (len(null) + 1))
    yearly = {str(y): sr(g) for y, g in net.groupby(net.index.year)}
    gates_res = {"net_sr": bool(sr_net >= GATE["net_sr_min"]), "placebo": bool(p < GATE["placebo_p_max"]),
                 "cost_stress_sign": bool(np.sign(sr_stress) == np.sign(sr_net) and sr_net != 0),
                 "name_share": bool(name_share <= GATE["name_share_max"]),
                 "convention_swap_sign": bool(np.sign(sr_log) == np.sign(sr_net) and sr_net != 0)}
    verdict = "PASS" if all(gates_res.values()) else "FAIL"
    metrics = {"sr_net": sr_net, "sr_gross": real["sr_gross"], "maxdd": real["maxdd"], "avg_turnover": real["avg_turnover"],
               "n_days": real["n_days"], "sr_stress_2x": sr_stress, "sr_logbooking": sr_log, "name_share": name_share,
               "placebo_p": p, "placebo_null_mean": float(np.mean(null)), "placebo_null_sd": float(np.std(null, ddof=1))}
    ledger_append(KEY, "XS_24h_IC", "P1_quintile_ls", {"cfg": cfg.__dict__, "sign": "reversal (dev IC<0): long low-z / short high-z"}, metrics)
    payload = {"ts_utc": pd.Timestamp.utcnow().isoformat(), "survivor": "XS_24h_IC", "config": cfg.__dict__, "metrics": metrics,
               "yearly_sr": yearly, "gates": gates_res, "verdict": verdict, "n_placebo": N_PLACEBO,
               "top_names": real["name_pnl"].abs().sort_values(ascending=False).head(10).to_dict(), "runtime_sec": time.time() - t0}
    (OUT / "p1_result.json").write_text(json.dumps(payload, indent=1, default=str))
    real["rets"].to_parquet(OUT / "p1_daily.parquet")
    gates = registry.load_gates()
    gates[KEY]["verdicts"]["P1"] = f"XS_24h_IC quintile L/S: net SR {sr_net:+.3f}, placebo p {p:.3f}, stress {sr_stress:+.3f}, log {sr_log:+.3f}, name share {name_share:.2f} -> {verdict}"
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"P1 {verdict} gates {gates_res} placebo p {p:.3f} (null mean {np.mean(null):+.2f} sd {np.std(null):.2f}) yearly {yearly}")


if __name__ == "__main__":
    main()
