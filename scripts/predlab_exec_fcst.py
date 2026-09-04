"""predlab_exec_fcst — forecasts as execution inputs (charter 2026-09-04).

  python scripts/predlab_exec_fcst.py register
  python scripts/predlab_exec_fcst.py run      # one-shot (refuses if verdicts exist)
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

from predlab_xfam_lib import DEV, clip_dev, ledger_append, load_1h_panels, load_daily_panels  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402
from tradingagents.predlab.meanstats import nw_tstat, p_pos  # noqa: E402
from tradingagents.predlab.opt import monthly_universe  # noqa: E402

KEY = "predlab_exec_fcst"
OUT = ROOT / "data" / "predlab" / "exec_fcst_result.json"
FC = ROOT / "data" / "predlab" / "forecasts" / "predlab_p1_classical"
AUM_GRID = [1e7, 3e7, 1e8]
AUM_HEAD = 3e7
K = 1.0
PROFILE_DAYS = 28
DEV_LO, DEV_HI = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)

ENTRY = {
    "registered_utc": "2026-09-04", "charter": "docs/superpowers/specs/2026-09-04-exec-fcst-charter.md",
    "purpose": "measurement, dev-only H3: (a) causal hour-of-day volume profile vs uniform participation schedule under sqrt impact; (b) RV champions vs naive-20 in the impact model's cost prediction (trade-invariant, = QLIKE of sigma forecast)",
    "book": "EW monthly top-200 PIT, weights 1/n set on the first trading day of each month, held; AUM grid 1e7/3e7/1e8, headline 3e7",
    "impact": "k*sigma_h*x_h*sqrt(x_h/V_h), k=1, sigma_h = trailing-20d std of hourly returns lagged, V_h realized hourly quote volume; fees dropped (identical)",
    "schedules": {"S_uni": "T/24", "S_prof": "T * trailing-28-day mean hour-of-day share of daily volume (days strictly before)", "S_oracle": "realized V_h shares (lower bound, reported)"},
    "gate_a": "mean daily cost reduction >= 5% at AUM 3e7 AND stationary-bootstrap p_pos >= 0.90 (mean block 21, 2000 draws) on paired daily cost_uni - cost_prof",
    "gate_b": "QLIKE(sigma_hat, sigma_real) improvement vs naive-20 >= 5% AND DM (HAC lag 5) p < 0.05, BTC (harq) and ETH (egarch11), 24h forecasts from predlab_p1_classical",
    "dev_window": list(DEV), "stop_rule": "report-grade; all numbers recorded; no schedule/window/k changes; one-shot", "thesis_section": "85",
}


def main_register() -> None:
    gates = registry.load_gates()
    if KEY in gates:
        raise SystemExit("already registered")
    gates[KEY] = ENTRY
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"gates.json['{KEY}'] written")


def cell_a() -> dict:
    t0 = time.time()
    daily = load_daily_panels()
    qv_d = clip_dev(daily["qv"])
    uni = monthly_universe(qv_d, 200)
    uni = uni[(uni.index >= DEV_LO) & (uni.index <= DEV_HI)]
    # weights: 1/n on the first trading day of each month, held
    W = pd.DataFrame(0.0, index=uni.index, columns=uni.columns)
    month = uni.index.to_period("M")
    for m in month.unique():
        rows = uni.index[month == m]
        members = uni.loc[rows[0]]
        n = int(members.sum())
        if n:
            W.loc[rows, members[members].index] = 1.0 / n
    dW = W.diff().abs()
    dW.iloc[0] = W.iloc[0]
    h1 = load_1h_panels()
    close, qv = clip_dev(h1["close"]), clip_dev(h1["qv"])
    cols = [c for c in W.columns if c in qv.columns]
    r1 = close[cols].pct_change(fill_method=None)
    sig_h = r1.rolling(480, min_periods=240).std(ddof=1).shift(1)          # 20 days of hourly bars, lagged
    day = qv.index.tz_convert("UTC").normalize()
    daily_vol = qv[cols].groupby(day).sum()
    share = qv[cols].div(daily_vol.reindex(day).set_axis(qv.index), axis=0)   # hourly share of the day's volume
    hour = qv.index.hour
    # trailing-28-day mean share by hour-of-day, causal (days strictly before the trade day)
    prof_by_hour = {}
    for h in range(24):
        s = share[hour == h]
        s.index = s.index.normalize()
        prof_by_hour[h] = s.rolling(PROFILE_DAYS, min_periods=14).mean().shift(1)
    print(f"cell a: panels ready ({time.time()-t0:.0f}s)", flush=True)
    trades = dW[cols]
    trade_days = trades.index[(trades > 0).any(axis=1)]
    costs = {f"{aum:.0e}": {"uni": [], "prof": [], "oracle": [], "day": []} for aum in AUM_GRID}
    n_name_days = 0
    for d in trade_days:
        bars = qv.index[day == d]
        if len(bars) < 20:
            continue
        names = trades.columns[trades.loc[d] > 0]
        V = qv.loc[bars, names]                                     # hours x names
        S = sig_h.loc[bars, names]
        ok = V.notna().all(axis=0) & S.notna().all(axis=0) & (V > 0).all(axis=0)
        names = names[ok.to_numpy()]
        if len(names) == 0:
            continue
        V, S = V[names], S[names]
        hrs = bars.hour
        P = pd.DataFrame({nm: [prof_by_hour[h].at[d, nm] if (d in prof_by_hour[h].index and nm in prof_by_hour[h].columns) else np.nan for h in hrs] for nm in names}, index=bars)
        ok2 = P.notna().all(axis=0) & (P.sum(axis=0) > 0)
        names = names[ok2.to_numpy()]
        if len(names) == 0:
            continue
        V, S, P = V[names], S[names], P[names]
        P = P / P.sum(axis=0)
        O = V / V.sum(axis=0)
        n_name_days += len(names)
        frac = trades.loc[d, names]                                  # weight fraction traded
        for aum in AUM_GRID:
            T = frac * aum
            for label, sched in (("uni", pd.DataFrame(1.0 / len(bars), index=bars, columns=names)), ("prof", P), ("oracle", O)):
                x = sched.mul(T, axis=1)
                c = (K * S * x * np.sqrt(x / V)).sum().sum() / aum
                costs[f"{aum:.0e}"][label].append(float(c))
            costs[f"{aum:.0e}"]["day"].append(d)
    res = {"n_trade_days": int(len(trade_days)), "n_name_days_used": n_name_days, "aum": {}}
    for key, c in costs.items():
        u, p, o = np.array(c["uni"]), np.array(c["prof"]), np.array(c["oracle"])
        diff = u - p
        res["aum"][key] = {"n_days": int(len(u)), "cost_uni_ann_pct": float(u.sum() / len(u) * 365 * 100) if len(u) else None,
                           "reduction_prof_pct": float((1 - p.sum() / u.sum()) * 100) if u.sum() > 0 else None,
                           "reduction_oracle_pct": float((1 - o.sum() / u.sum()) * 100) if u.sum() > 0 else None,
                           "p_pos_paired": float(p_pos(diff, n_boot=2000, mean_block=21, seed=0)) if len(diff) > 30 else None,
                           "share_days_prof_cheaper": float(np.mean(diff > 0)) if len(diff) else None}
    head = res["aum"][f"{AUM_HEAD:.0e}"]
    res["gate_a"] = {"reduction_pct": head["reduction_prof_pct"], "p_pos": head["p_pos_paired"],
                     "pass": bool(head["reduction_prof_pct"] is not None and head["reduction_prof_pct"] >= 5.0 and head["p_pos_paired"] >= 0.90)}
    print(f"cell a done ({time.time()-t0:.0f}s): {json.dumps(res['aum'][f'{AUM_HEAD:.0e}'])}", flush=True)
    return res


def qlike(pred: np.ndarray, real: np.ndarray) -> np.ndarray:
    r = real / pred
    return r - np.log(r) - 1.0


def cell_b() -> dict:
    out = {}
    for sym, model in (("BTCUSDT", "harq"), ("ETHUSDT", "egarch11")):
        df = pd.read_parquet(FC / f"{sym}_24h_T3_rv" / f"{model}.parquet").set_index("ts").sort_index()
        df = df[(df.index >= DEV_LO) & (df.index <= DEV_HI)]
        naive = df["y_true"].rolling(20, min_periods=20).mean().shift(1)
        d = pd.DataFrame({"real": np.sqrt(df["y_true"]), "champ": np.sqrt(df["pred"].clip(lower=1e-12)), "naive": np.sqrt(naive)}).dropna()
        l_c, l_n = qlike(d["champ"].to_numpy(), d["real"].to_numpy()), qlike(d["naive"].to_numpy(), d["real"].to_numpy())
        diff = l_n - l_c
        t = float(nw_tstat(diff, lag=5))   # meanstats.nw_tstat returns the HAC t only
        from scipy.stats import norm
        p = float(2 * (1 - norm.cdf(abs(t))))
        impr = float((1 - l_c.mean() / l_n.mean()) * 100)
        out[sym] = {"model": model, "n_days": int(len(d)), "qlike_champ": float(l_c.mean()), "qlike_naive20": float(l_n.mean()),
                    "improvement_pct": impr, "dm_t": t, "dm_p": p, "pass": bool(impr >= 5.0 and p < 0.05)}
        print(f"cell b {sym}/{model}: QLIKE {l_c.mean():.4f} vs naive {l_n.mean():.4f} impr {impr:+.1f}% DM t {t:+.2f} p {p:.4f}", flush=True)
    out["gate_b"] = {"pass": bool(all(out[s]["pass"] for s in ("BTCUSDT", "ETHUSDT")))}
    out["note"] = "impact = k*sigma*T*sqrt(T/ADV): predicted/realized impact ratio = sigma_hat/sigma_real, so QLIKE of impact == QLIKE of the sigma forecast (trade-invariant)"
    return out


def main_run() -> None:
    gates = registry.load_gates()
    if gates[KEY].get("verdicts"):
        raise SystemExit("REFUSED: verdicts already recorded (one-shot)")
    a = cell_a()
    b = cell_b()
    verdict = {"a": "PASS" if a["gate_a"]["pass"] else "FAIL", "b": "PASS" if b["gate_b"]["pass"] else "FAIL"}
    payload = {"ts_utc": pd.Timestamp.utcnow().isoformat(), "cell_a": a, "cell_b": b, "verdict": verdict}
    OUT.write_text(json.dumps(payload, indent=1, default=str))
    ledger_append(KEY, "a_profile_schedule", "sqrt_impact", {"aum": AUM_HEAD, "k": K, "profile_days": PROFILE_DAYS},
                  {k: v for k, v in a["aum"][f"{AUM_HEAD:.0e}"].items() if v is not None})
    for s in ("BTCUSDT", "ETHUSDT"):
        ledger_append(KEY, f"b_rv_{s}", b[s]["model"], {"symbol": s}, {k: v for k, v in b[s].items() if isinstance(v, (int, float))})
    gates = registry.load_gates()
    gates[KEY]["verdicts"] = {"a": f"{verdict['a']}: reduction {a['gate_a']['reduction_pct']:.2f}% p_pos {a['gate_a']['p_pos']:.3f} (oracle {a['aum'][f'{AUM_HEAD:.0e}']['reduction_oracle_pct']:.1f}%)",
                              "b": f"{verdict['b']}: BTC {b['BTCUSDT']['improvement_pct']:+.1f}% p {b['BTCUSDT']['dm_p']:.4f}; ETH {b['ETHUSDT']['improvement_pct']:+.1f}% p {b['ETHUSDT']['dm_p']:.4f}"}
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(json.dumps(gates[KEY]["verdicts"], indent=1))


if __name__ == "__main__":
    {"register": main_register, "run": main_run}[sys.argv[1]]()
