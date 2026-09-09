"""exec_pf dev re-pricing (gates.json["exec_pf"]["gates_dev_LTM"]).

  python scripts/exec_pf_run.py R2        # liq_fade_i1 thr3.5/H48 through the passive overlay
  python scripts/exec_pf_run.py R1_BTC
  python scripts/exec_pf_run.py R1_ETH

Refuses to run unless data/rebuild/exec_pf/probes.json exists with stop=false
and refuses to overwrite an existing per-signal result (no second look).
Per signal: LTM (gated), LOC (reported), taker reference under simple returns
(reported), maker 3 bp stress, log-booking swap, dual-family placebos through
the LTM overlay (500 draws each), per-year SR, fill statistics, DSR at
n_trials 3 and cumulative. One ledger row per policy (3 per signal).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exec_pf_common as X  # noqa: E402
from liq_fade_dev import _redraw_random_triggers, _shift_triggers, _unique_config_hashes  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.fills import passive_overlay  # noqa: E402
from tradingagents.xsect.liq_fade import event_weights_hourly  # noqa: E402
from tradingagents.xsect.portfolio import rank_placebo_pvalue  # noqa: E402

N_PLACEBO = 500
GATE = {"net_sr_min": 1.0, "fill_rate_min": 0.60, "placebo_p_max": 0.05}
FAMILY_N = 3


def _dsr(daily: np.ndarray, n_trials: int) -> float:
    if len(daily) < 2 or daily.std(ddof=1) <= 0:
        return float("nan")
    var_sr = variance_of_sr(daily)
    se = float(np.sqrt(var_sr))
    if se <= 0:
        return float("nan")
    try:
        return float(deflated_sharpe_ratio(float(daily.mean() / daily.std(ddof=1)),
                                           expected_max_sharpe(n_trials, var_sr), se))
    except ValueError:
        return float("nan")


def _fill_stats(orders: pd.DataFrame, W: pd.DataFrame) -> dict:
    o = orders.copy()
    if o.empty:
        return {}
    o["year"] = pd.to_datetime(o["ts_bar"]).dt.year
    o["adw"] = o["dw"].abs()
    f = o[o["filled"]]
    sgn = np.where(f["side"] == "buy", 1.0, -1.0)
    adverse = sgn * (f["close_n"] / f["fill_price"] - 1)
    ok = np.isfinite(adverse)
    return {
        "n_orders": int(len(o)), "n_filled": int(len(f)),
        "fill_rate_count": float(o["filled"].mean()),
        "fill_rate_by_side": {s: float(g["adw"][g["filled"]].sum() / g["adw"].sum()) for s, g in o.groupby("side")},
        "fill_rate_by_year": {str(y): float(g["adw"][g["filled"]].sum() / g["adw"].sum()) for y, g in o.groupby("year")},
        "adverse_selection_mean_bp": float(np.mean(adverse[ok]) * 1e4) if ok.any() else None,
        "adverse_selection_median_bp": float(np.median(adverse[ok]) * 1e4) if ok.any() else None,
        "limit_vs_close_mean_bp": float(np.mean(np.abs(f["fill_price"] / f["close_b"] - 1)) * 1e4) if len(f) else None,
    }


def _metrics(out: dict, W: pd.DataFrame) -> dict:
    d = out["daily_net"]
    gp = out["gross_panel"].sum(axis=0)
    top = float(gp.abs().max() / gp.abs().sum()) if gp.abs().sum() > 0 else None
    return {"net_sr": X.sharpe(d), "maxdd": X.maxdd_simple(d), "mean_bp_day": float(d.mean() * 1e4),
            "fill_rate": out["fill_rate"], "n_days": int(len(d)), "yearly_sr": X.yearly_sr(d),
            "gross_total": float(out["gross"].sum()), "cost_total": float(out["cost"].sum()),
            "top_name_share": top, "fills": _fill_stats(out["orders"], W)}


def _panels(W: pd.DataFrame) -> dict:
    return X.load_agg_panel(list(W.columns), W.index)


def run_signal(sig: str) -> dict:
    t0 = time.time()
    probes = json.loads((X.OUT / "probes.json").read_text())
    if probes["stop"]:
        raise SystemExit("probes STOP -- refusing to run")
    res_path = X.OUT / f"run_{sig}.json"
    if res_path.exists():
        raise SystemExit(f"{res_path} exists -- no second look (stop rule)")
    spread = X.spread_model()
    through = json.loads((X.OUT / "p0_calibration.json").read_text())["through_ticks_selected"]
    srel = {s: spread["per_symbol_s_rel"].get(s, spread["pooled_alt_s_rel"]) for s in X.symbols()}

    if sig == "R2":
        par = X.r2_parent()
        W, C = par["W"], par["close"]
        rf, parent_cost = X.R2["rf_annual"], X.R2["cost_bps"]
        cfg_base = {"signal": "R2", "parent": "liq_fade_i1", **X.R2}
    else:
        sym = sig.split("_")[1] + "USDT"
        par = X.r1_parent(sym)
        W, C = par["W"], par["close"]
        rf, parent_cost = 0.0, X.R1["cost_bps"]
        cfg_base = {"signal": sig, "parent": "predlab_pp S3", "symbol": sym, **X.R1}
    P = _panels(W)
    ML, MH, T = P["minlow_ex0"], P["maxhigh_ex0"], P["tick"]
    fill = {"s_rel": srel, "through_ticks": through, "maker_bp": X.FEES["maker_bp"], "taker_bp": X.FEES["taker_bp"]}
    window = (X.DEV[0], X.DEV[1]) if sig == "R2" else (par["window"][0][:10], par["window"][1][:10])
    print(f"[{sig}] W {W.shape}, orders intended {int((W.diff().fillna(W.iloc[0]) != 0).to_numpy().sum())}, "
          f"through={through} t={time.time()-t0:.0f}s", flush=True)

    def run(policy, **kw):
        base = dict(fill)
        base.update(kw)
        return passive_overlay(W, C, ML, MH, T, policy=policy, rf_annual=rf,
                               parent_cost_bp=parent_cost, **base)

    ltm = run("LTM")
    m_ltm = _metrics(ltm, W)
    m_stress = _metrics(run("LTM", maker_bp=X.FEES["stress_maker_bp"]), W)
    m_log = _metrics(run("LTM", log_booking=True), W)
    loc = run("LOC")
    m_loc = _metrics(loc, W)
    tak = run("taker")
    m_tak = _metrics(tak, W)
    print(f"[{sig}] LTM SR {m_ltm['net_sr']:+.4f} fill {m_ltm['fill_rate']:.3f} | LOC SR {m_loc['net_sr']:+.4f} "
          f"fill {m_loc['fill_rate']:.3f} | taker SR {m_tak['net_sr']:+.4f} | stress {m_stress['net_sr']:+.4f} "
          f"| log {m_log['net_sr']:+.4f} t={time.time()-t0:.0f}s", flush=True)

    # ── placebos through the LTM overlay ──────────────────────────────────────
    real_sr = m_ltm["net_sr"]
    srA, srB = [], []
    if sig == "R2":
        rng = np.random.default_rng(48)
        trig, mask = par["trig"], par["mask"]
        for i in range(N_PLACEBO):
            Wp = event_weights_hourly(_shift_triggers(trig, rng), X.R2["H"], w_per=X.R2["w_per"], cap=X.R2["cap"])
            srA.append(X.sharpe(passive_overlay(Wp, C, ML, MH, T, policy="LTM", rf_annual=rf, parent_cost_bp=parent_cost, **fill)["daily_net"]))
            if i % 50 == 0:
                print(f"  placebo A {i}/{N_PLACEBO} t={time.time()-t0:.0f}s", flush=True)
        for i in range(N_PLACEBO):
            Wp = event_weights_hourly(_redraw_random_triggers(trig, mask, rng), X.R2["H"], w_per=X.R2["w_per"], cap=X.R2["cap"])
            srB.append(X.sharpe(passive_overlay(Wp, C, ML, MH, T, policy="LTM", rf_annual=rf, parent_cost_bp=parent_cost, **fill)["daily_net"]))
            if i % 50 == 0:
                print(f"  placebo B {i}/{N_PLACEBO} t={time.time()-t0:.0f}s", flush=True)
    else:
        rng = np.random.default_rng(48)
        prob = par["prob"]
        n = len(prob)

        def pos_from(p: pd.Series) -> pd.DataFrame:
            q = p.rolling(X.R1["smooth"], min_periods=1).mean() if X.R1["smooth"] > 1 else p
            return pd.DataFrame({W.columns[0]: (q > X.R1["thresh"]).astype(float).to_numpy()}, index=W.index)

        for _ in range(N_PLACEBO):
            k = int(rng.integers(30, n - 30))
            Wp = pos_from(pd.Series(np.roll(prob.to_numpy(), k), index=prob.index))
            srA.append(X.sharpe(passive_overlay(Wp, C, ML, MH, T, policy="LTM", rf_annual=rf, parent_cost_bp=parent_cost, **fill)["daily_net"]))
        for _ in range(N_PLACEBO):
            blocks = [prob.to_numpy()[i:i + 24] for i in range(0, n, 24)]
            perm = rng.permutation(len(blocks))
            Wp = pos_from(pd.Series(np.concatenate([blocks[j] for j in perm])[:n], index=prob.index))
            srB.append(X.sharpe(passive_overlay(Wp, C, ML, MH, T, policy="LTM", rf_annual=rf, parent_cost_bp=parent_cost, **fill)["daily_net"]))
    pA, pB = rank_placebo_pvalue(real_sr, srA), rank_placebo_pvalue(real_sr, srB)
    p_worse = max(pA, pB)
    print(f"[{sig}] placebo pA {pA:.3f} pB {pB:.3f} (null A mean {np.mean(srA):+.2f} sd {np.std(srA):.2f}; "
          f"B mean {np.mean(srB):+.2f} sd {np.std(srB):.2f}) t={time.time()-t0:.0f}s", flush=True)

    # ── ledger + DSR ─────────────────────────────────────────────────────────
    n_before = _unique_config_hashes()
    rows = {}
    for policy, m in (("LTM", m_ltm), ("LOC", m_loc), ("taker_simple", m_tak)):
        cfg = {**cfg_base, "policy": policy, "fill_model": {k: v for k, v in fill.items() if k != "s_rel"},
               "spread_model": "data/rebuild/exec_pf/spread_model.json", "selectable": policy == "LTM"}
        rows[policy] = log_trial("exec_pf", cfg, window, {"net_sr": m["net_sr"], "maxdd": m["maxdd"],
                                                            "fill_rate": m["fill_rate"], "n_days": m["n_days"]})
    daily = ltm["daily_net"].to_numpy()
    dsr = {"n_trials_family": FAMILY_N, "dsr_family": _dsr(daily, FAMILY_N),
           "n_trials_cumulative": n_before + 3, "dsr_cumulative": _dsr(daily, n_before + 3)}

    gates = {"net_sr": bool(m_ltm["net_sr"] >= GATE["net_sr_min"]),
             "fill_rate": bool(m_ltm["fill_rate"] >= GATE["fill_rate_min"]),
             "placebo": bool(p_worse <= GATE["placebo_p_max"]),
             "cost_stress_sign": bool(np.sign(m_stress["net_sr"]) == np.sign(m_ltm["net_sr"]) and m_ltm["net_sr"] != 0),
             "convention_swap_sign": bool(np.sign(m_log["net_sr"]) == np.sign(m_ltm["net_sr"]) and m_ltm["net_sr"] != 0)}
    verdict = "PASS" if all(gates.values()) else "FAIL"
    out = {"signal": sig, "generated_utc": pd.Timestamp.utcnow().isoformat(), "window": list(window),
           "fill_model": {k: v for k, v in fill.items() if k != "s_rel"}, "gate": GATE, "gates": gates, "verdict": verdict,
           "LTM": m_ltm, "LTM_maker3bp": m_stress, "LTM_logbooking": m_log, "LOC": m_loc, "taker_simple": m_tak,
           "placebo": {"n_draws": N_PLACEBO, "p_A": pA, "p_B": pB, "p_worse": p_worse,
                       "null_A": {"mean": float(np.mean(srA)), "sd": float(np.std(srA, ddof=1)), "max": float(np.max(srA))},
                       "null_B": {"mean": float(np.mean(srB)), "sd": float(np.std(srB, ddof=1)), "max": float(np.max(srB))}},
           "dsr": dsr, "ledger_rows": {k: v["config_hash"] for k, v in rows.items()},
           "parent_reference": {"parent_sr": par.get("parent_sr"), "pin_sr": par.get("pin_sr")} if sig == "R2" else
           {"parent_hourly_sr_log": json.loads((X.INPUTS / "pp_dev_results.json").read_text())["S3"]["s3_t0.5_h24"]["sr_net"] if sig == "R1_BTC" else None},
           "runtime_sec": time.time() - t0}
    res_path.write_text(json.dumps(out, indent=1, default=str))
    ltm["daily_net"].rename("ltm_daily_net").to_frame().to_parquet(X.OUT / f"run_{sig}_ltm_daily.parquet")
    ltm["orders"].to_parquet(X.OUT / f"run_{sig}_ltm_orders.parquet")
    loc["orders"].to_parquet(X.OUT / f"run_{sig}_loc_orders.parquet")
    print(f"[{sig}] VERDICT {verdict} gates {gates} -> {res_path} ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    run_signal(sys.argv[1])
