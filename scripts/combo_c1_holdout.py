"""combo_c1 ONE-SHOT holdout spend (charter docs/superpowers/specs/2026-09-02-combo-c1-charter.md).

Refuses to run if data/rebuild/combo_c1/holdout_verdict.json exists (the
sealed 2025-04-01 -> 2026-07-01 window is spent for S1-S4 the moment this
script writes it). Requires probes.json with blocking_pass = true.

Evaluates the frozen book (weights from gates.json["combo_c1"]["registered_dev"])
on the holdout, scores the seven registered gates, the dual-family
weight-path placebos (500 draws each), the convention swap, the 2x cost
stress, the W2 sensitivity and the DSR denominators; writes the verdict file,
holdout_series.parquet, and one ledger row per variant (allow_holdout=True).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.combo_c1_probes import CM_FUND_H1, LIQ_SYMS_H1, LIQ_UNIV_H1, VAL_UNIV_H1, WARMUP_VAL_H1  # noqa: E402
from scripts.combo_c1_register import CM_UNIV, FUND, GATES, HOLDOUT, KL, KL1H, OUT  # noqa: E402
from tradingagents.rebuild.ledger import DEFAULT_LEDGER, log_trial  # noqa: E402
from tradingagents.strategies.v3.backtest.dsr import (  # noqa: E402
    deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr,
)
from tradingagents.xsect.combo import (  # noqa: E402
    align_sleeves, assert_holdout_unspent, combine, draw_shared_offset, gate_verdict,
    indep_shift, maxdd_simple, rank_placebo_pvalue, shared_shift, sharpe,
    sleeve_contributions, top_name_share,
)
from tradingagents.xsect.combo_sleeves import (  # noqa: E402
    CFG, SLEEVE_IDS, build_carry, build_liq_fade, build_momentum, build_value,
    load_cm_mapping, load_hourly_panel, sleeve_name_pnl, sleeve_net,
)
from tradingagents.xsect.universe import load_klines  # noqa: E402

VERDICT = OUT / "holdout_verdict.json"
N_PLACEBO = 500
MIN_SHIFT_DAYS = 30
WARMUP_1H_H1 = "2024-09-01"
FAMILY_N = 28          # 6 liq_fade + 6 carry + 12 momentum + 4 value parent configs


def _dsr(series: pd.Series, n_trials: int) -> float:
    x = series.to_numpy()
    var_sr = variance_of_sr(x)
    sd = x.std(ddof=1)
    sr_pb = float(x.mean() / sd) if sd > 0 else 0.0
    return float(deflated_sharpe_ratio(sr_pb, expected_max_sharpe(n_trials, var_sr), float(np.sqrt(var_sr))))


def _unique_hashes() -> int:
    seen = set()
    with open(DEFAULT_LEDGER) as f:
        for line in f:
            if line.strip():
                seen.add(json.loads(line)["config_hash"])
    return len(seen)


def build_holdout_sleeves(t0: float) -> dict:
    lo, hi = pd.Timestamp(HOLDOUT[0], tz="UTC"), pd.Timestamp(HOLDOUT[1], tz="UTC")
    klines = load_klines(KL)
    klines = {s: d.loc[:hi] for s, d in klines.items()}
    sl = {}
    sl["momentum"] = build_momentum(klines, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] momentum: {sl['momentum'].meta['rebalances']} rebalances", flush=True)
    sl["carry"] = build_carry(klines, FUND, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] carry: {sl['carry'].meta['refreshes']} refreshes", flush=True)
    sl["value"] = build_value(klines, CM_FUND_H1, load_cm_mapping(CM_UNIV),
                              json.loads(VAL_UNIV_H1.read_text()), WARMUP_VAL_H1, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] value: breadth median {sl['value'].meta['breadth_median']}", flush=True)
    syms = [s for s in LIQ_SYMS_H1.read_text().split() if s]
    close, qvol = load_hourly_panel(KL1H, syms, pd.Timestamp(WARMUP_1H_H1, tz="UTC"), hi + pd.Timedelta(hours=23))
    sl["liq_fade"] = build_liq_fade(close, qvol, json.loads(LIQ_UNIV_H1.read_text()), lo, hi)
    print(f"[{time.time()-t0:6.1f}s] liq_fade: {sl['liq_fade'].meta}", flush=True)
    return sl


def _book(series: dict, idx: pd.DatetimeIndex, weights: dict) -> tuple:
    df = align_sleeves(series, idx)
    return df, combine(df, weights)


def main() -> None:
    t0 = time.time()
    assert_holdout_unspent(VERDICT)
    probes = json.loads((OUT / "probes.json").read_text())
    if not probes.get("blocking_pass"):
        raise SystemExit("blocking probes did not pass — no spend")
    gates = json.loads(GATES.read_text())["combo_c1"]
    reg = gates["registered_dev"]
    G = gates["gates_holdout"]
    w1, w2 = reg["weights_W1"], reg["weights_W2"]
    idx = pd.date_range(HOLDOUT[0], HOLDOUT[1], freq="D", tz="UTC")
    n_days = len(idx)

    sl = build_holdout_sleeves(t0)
    real = {sid: sleeve_net(sl[sid]) for sid in SLEEVE_IDS}
    df, c1 = _book(real, idx, w1)
    _, c2 = _book(real, idx, w2)
    print(f"[{time.time()-t0:6.1f}s] holdout W1 SR {sharpe(c1):+.4f}  W2 SR {sharpe(c2):+.4f}", flush=True)

    # ── placebos on weight paths (costs/rf re-applied by the sleeve engines) ──
    plA = {"W1": [], "W2": []}
    plB = {"W1": [], "W2": []}
    for p in range(N_PLACEBO):
        rng = np.random.default_rng(seed=p)
        shifted = {}
        for sid in SLEEVE_IDS:
            s = sl[sid]
            ms = MIN_SHIFT_DAYS * (24 if s.engine == "hourly" else 1)
            shifted[sid] = sleeve_net(s, W=indep_shift(s.W, rng, ms))
        dA = align_sleeves(shifted, idx)
        plA["W1"].append(sharpe(combine(dA, w1))); plA["W2"].append(sharpe(combine(dA, w2)))
        rngB = np.random.default_rng(seed=p)
        k = draw_shared_offset(rngB, n_days, MIN_SHIFT_DAYS)
        shB = {sid: sleeve_net(sl[sid], W=shared_shift(sl[sid].W, k)) for sid in SLEEVE_IDS}
        dB = align_sleeves(shB, idx)
        plB["W1"].append(sharpe(combine(dB, w1))); plB["W2"].append(sharpe(combine(dB, w2)))
        if p % 50 == 49:
            print(f"[{time.time()-t0:6.1f}s] placebo {p+1}/{N_PLACEBO}", flush=True)

    # ── convention swap + cost stress ──
    swap = {sid: sleeve_net(sl[sid], convention="log") for sid in SLEEVE_IDS}
    _, c1_log = _book(swap, idx, w1)
    stress = {sid: sleeve_net(sl[sid], cost_bps=2 * sl[sid].cost_bps) for sid in SLEEVE_IDS}
    _, c1_stress = _book(stress, idx, w1)
    _, c2_stress = _book(stress, idx, w2)

    name_pnl = {sid: sleeve_name_pnl(sl[sid]) for sid in SLEEVE_IDS}
    pooled = {sid: {k: v * w1[sid] for k, v in d.items()} for sid, d in name_pnl.items()}
    top_name, top_share = top_name_share(pooled)
    n_cum = _unique_hashes() + 1

    def _variant(name, c, w, pA, pB, c_log, c_stress):
        contrib = sleeve_contributions(df, w)
        halves = np.array_split(np.arange(n_days), 2)
        pa, pb = rank_placebo_pvalue(sharpe(c), pA), rank_placebo_pvalue(sharpe(c), pB)
        sr_dev = reg[f"dev_sr_{name}"]
        sr_h, sr_log = sharpe(c), sharpe(c_log)
        flips = not (sr_log >= G["sr_ratio_min"] * sr_dev and sr_log >= G["sr_abs_min"]
                     and np.sign(sr_log) == np.sign(sr_dev))
        m = {"sr_h": sr_h, "sr_dev": sr_dev, "sr_floor": max(G["sr_ratio_min"] * sr_dev, G["sr_abs_min"]),
             "placebo_p_indep": pa, "placebo_p_shared": pb, "placebo_p_worse": max(pa, pb),
             "placebo_sr_indep_q95": float(np.quantile(pA, 0.95)), "placebo_sr_shared_q95": float(np.quantile(pB, 0.95)),
             "contrib": contrib, "min_contrib": min(contrib.values()),
             "maxdd": maxdd_simple(c), "top_name": top_name, "top_name_share": top_share,
             "sr_log_convention": sr_log, "convention_swap_flips": bool(flips),
             "sr_cost_2x": sharpe(c_stress), "sr_halves": [sharpe(c.iloc[h]) for h in halves],
             "mean_bp_day": float(c.mean() * 1e4), "total_return": float((1 + c).prod() - 1),
             "n_days": n_days,
             "dsr_n1": _dsr(c, 1), "dsr_family28": _dsr(c, FAMILY_N), "dsr_cumulative": _dsr(c, n_cum),
             "n_cumulative": n_cum}
        m["gate"] = gate_verdict(m, G)
        return m

    W1 = _variant("W1", c1, w1, plA["W1"], plB["W1"], c1_log, c1_stress)
    _, c2_log = _book(swap, idx, w2)
    W2 = _variant("W2", c2, w2, plA["W2"], plB["W2"], c2_log, c2_stress)
    per_sleeve = {sid: {"sr_h": sharpe(df[sid]), "sr_h_native": sharpe(real[sid]), "n_days_native": int(len(real[sid])),
                        "maxdd": maxdd_simple(df[sid]), "mean_bp_day": float(df[sid].mean() * 1e4),
                        "sr_log_convention": sharpe(align_sleeves(swap, idx)[sid]),
                        "sr_cost_2x": sharpe(align_sleeves(stress, idx)[sid]),
                        "meta": {k: v for k, v in (sl[sid].meta or {}).items()
                                 if k not in ("n_members", "breadth_weekly")}}
                  for sid in SLEEVE_IDS}
    corr_h = df.corr()
    verdict = "PASS" if W1["gate"]["pass"] else "FAIL"
    out = {"verdict": verdict, "gated_variant": "W1", "spent": pd.Timestamp.utcnow().isoformat(),
           "holdout_window": list(HOLDOUT), "weights_W1": w1, "weights_W2": w2,
           "W1": W1, "W2": W2, "per_sleeve": per_sleeve,
           "corr_holdout": {a: {b: float(corr_h.loc[a, b]) for b in corr_h.columns} for a in corr_h.index},
           "n_placebo": N_PLACEBO, "runtime_sec": time.time() - t0,
           "sleeve_configs": {k: CFG[k] for k in SLEEVE_IDS}}
    for name, m, w in (("W1", W1, w1), ("W2", W2, w2)):
        log_trial("combo_c1", {"variant": name, "weights": w, "sleeves": {k: CFG[k] for k in SLEEVE_IDS},
                               "window_role": "holdout-one-shot"}, HOLDOUT,
                  {k: m[k] for k in ("sr_h", "placebo_p_worse", "maxdd", "top_name_share", "min_contrib",
                                     "sr_log_convention", "sr_cost_2x", "dsr_n1", "n_days")}
                  | {"gate_pass": m["gate"]["pass"]}, allow_holdout=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df.assign(combined_W1=c1, combined_W2=c2).to_parquet(OUT / "holdout_series.parquet")
    pd.DataFrame({"A_W1": plA["W1"], "A_W2": plA["W2"], "B_W1": plB["W1"], "B_W2": plB["W2"]}).to_parquet(
        OUT / "holdout_placebo_srs.parquet")

    def _san(o):
        if isinstance(o, float):
            return None if (np.isnan(o) or np.isinf(o)) else o
        if isinstance(o, dict):
            return {str(k): _san(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_san(v) for v in o]
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return o
    VERDICT.write_text(json.dumps(_san(out), indent=1, default=str))
    print(json.dumps({"verdict": verdict, "W1": {k: W1[k] for k in ("sr_h", "sr_floor", "placebo_p_worse", "min_contrib",
                                                                       "maxdd", "top_name_share", "sr_log_convention",
                                                                       "sr_cost_2x", "sr_halves")},
                      "checks": W1["gate"]["checks"], "W2_sr": W2["sr_h"],
                      "per_sleeve_sr": {k: v["sr_h"] for k, v in per_sleeve.items()}}, indent=1, default=str))


if __name__ == "__main__":
    main()
