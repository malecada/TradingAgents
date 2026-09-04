"""smw_xs P0 — T7 IC battery on the smart-money features (one-shot, registered).

Charter: docs/superpowers/specs/2026-09-04-smw-xs-charter.md; gates key
predlab_smw_xs. Refuses to run if p0_result.json exists. Every (signal,
target) row goes to the trial ledger. Declared forensics run afterwards in
the same script regardless of verdict.

Run: python scripts/predlab_smw_p0.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from tradingagents.predlab import registry, xsec  # noqa: E402
from predlab_t7 import SUBPERIODS  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
PANELS = ROOT / "data" / "predlab" / "t7_panels"
EXP = "predlab_smw_xs"
SIGNS = {"f1": 1, "f2": 1, "f3": -1, "f4": 1}
MIN_BREADTH = 20
MIN_QUALIFIED = 100
IC_FLOOR, T_FLOOR, Q_MAX = 0.02, 3.0, 0.05
FDR_Q = 0.10
DAY = 86_400


# ------------------------------------------------------------ pure helpers

def zrow(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean(axis=1)
    sd = df.std(axis=1, ddof=1).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0)


def composite(panels: dict, min_feats: int = 3) -> pd.DataFrame:
    zs = [zrow(panels[k]) * SIGNS[k] for k in SIGNS]
    stack = pd.concat(zs, keys=list(SIGNS))
    n = stack.groupby(level=1).count()
    comp = stack.groupby(level=1).mean()
    return comp.where(n >= min_feats)


def bh_qvalues(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def universe_mask(universe: dict, index: pd.DatetimeIndex, columns) -> pd.DataFrame:
    mask = pd.DataFrame(False, index=index, columns=columns)
    months = sorted(universe)
    for i, m in enumerate(months):
        lo = pd.Timestamp(m, tz="UTC")
        hi = pd.Timestamp(months[i + 1], tz="UTC") if i + 1 < len(months) else lo + pd.offsets.MonthBegin(1)
        rows = (index >= lo) & (index < hi)
        cols = [s for s in universe[m] if s in mask.columns]
        mask.loc[rows, cols] = True
    return mask


def residualize(sig: pd.DataFrame, controls: list[pd.DataFrame]) -> pd.DataFrame:
    """Per-day OLS residual of sig on controls (cross-sectional, with intercept)."""
    out = sig.copy() * np.nan
    for d in sig.index:
        y = sig.loc[d]
        X = pd.concat([c.loc[d] for c in controls], axis=1)
        ok = y.notna() & X.notna().all(axis=1)
        if ok.sum() < MIN_BREADTH:
            continue
        A = np.column_stack([np.ones(ok.sum()), X[ok].to_numpy()])
        beta, *_ = np.linalg.lstsq(A, y[ok].to_numpy(), rcond=None)
        out.loc[d, ok[ok].index] = y[ok].to_numpy() - A @ beta
    return out


def score(sig: pd.DataFrame, y: pd.DataFrame, lag: int) -> dict:
    ics = xsec.daily_ic(sig, y, min_breadth=MIN_BREADTH)
    s = xsec.ic_summary(ics, nw_lag=lag)
    subs = {}
    for label, lo, hi in SUBPERIODS:
        sub = ics[(ics.index >= lo) & (ics.index <= hi)].dropna()
        subs[label] = float(sub.mean()) if len(sub) > 20 else float("nan")
    s["sub_periods"] = subs
    s["p_two_sided"] = float(2 * (1 - stats.norm.cdf(abs(s["nw_t"])))) if np.isfinite(s["nw_t"]) else float("nan")
    s["ic_se"] = float(s["ic_std"] / np.sqrt(s["n_days"])) if s["n_days"] > 1 else float("nan")
    s["subs_positive"] = int(sum(1 for v in subs.values() if np.isfinite(v) and v > 0))
    return s


# ------------------------------------------------------------ main

def main() -> None:
    out_p = SMW / "p0_result.json"
    if out_p.exists():
        raise SystemExit("p0_result.json exists — one-shot already spent")
    entry = registry.get_experiment(EXP)
    dev_start, dev_end = entry["universe"]["dev_window"]
    registry.assert_dev_window(dev_end)

    F = pd.read_parquet(SMW / "features.parquet")
    Q = pd.read_parquet(SMW / "qualified_daily.parquet")
    universe = json.loads((SMW / "universe.json").read_text())
    close = pd.read_parquet(PANELS / "close.parquet")
    close = close[(close.index >= "2020-12-01") & (close.index <= dev_end)]
    syms = sorted(set(F["sym"]) & set(close.columns))
    close = close[syms]
    uni = universe_mask(universe, close.index, syms)

    panels = {k: F.pivot(index="date", columns="sym", values=k).reindex(index=close.index, columns=syms)
              for k in SIGNS}
    # information through close d -> T7 row d+1
    panels = {k: v.shift(1) for k, v in panels.items()}
    comp = composite(panels)
    eval_start = pd.Timestamp(Q.loc[Q["n_qualified"] >= MIN_QUALIFIED, "date"].min()) + pd.Timedelta(days=1)
    eval_start = max(eval_start, pd.Timestamp(dev_start, tz="UTC"))
    ret = np.log(close).diff()
    targets = {"ret_24h": (ret, 5), "ret_7d": (ret.rolling(7).sum().shift(-6), 10)}
    window = (eval_start.strftime("%Y-%m-%d"), dev_end)

    signals = {**{k: v * SIGNS[k] for k, v in panels.items()}, "composite": comp}
    results, tests = {}, []
    for tname, (y, lag) in targets.items():
        y_dev = y[y.index >= eval_start].where(uni)
        for sname, sig in signals.items():
            s_dev = sig[sig.index >= eval_start].where(uni)
            s = score(s_dev, y_dev, lag)
            key = f"{tname}|{sname}"
            results[key] = s
            tests.append((key, s["p_two_sided"]))
            registry.log_trial(EXP, key, sname, {"target": tname, "signal": sname, "universe": "smw"},
                               window, {k: v for k, v in s.items() if k != "sub_periods"})
            print(f"{key}: ic={s['mean_ic']:+.4f} nw_t={s['nw_t']:+.2f} n={s['n_days']} "
                  f"subs={ {k: round(v, 4) for k, v in s['sub_periods'].items()} }", flush=True)
    q = bh_qvalues([p if np.isfinite(p) else 1.0 for _, p in tests])
    for (key, _), qv in zip(tests, q):
        results[key]["bh_q"] = float(qv)

    verdict = {}
    for tname in targets:
        r = results[f"{tname}|composite"]
        ok = (r["mean_ic"] >= IC_FLOOR and r["nw_t"] >= T_FLOOR and r["bh_q"] < Q_MAX and r["subs_positive"] >= 2)
        verdict[tname] = {"pass": bool(ok), "mean_ic": r["mean_ic"], "nw_t": r["nw_t"], "bh_q": r["bh_q"],
                          "subs_positive": r["subs_positive"]}
    t1 = "PASS" if any(v["pass"] for v in verdict.values()) else "FAIL"

    # ---------------------------------------------------------- forensics
    fx = {}
    mom7 = ret.rolling(7).sum().shift(1)
    mom30 = ret.rolling(30).sum().shift(1)
    comp_dev = comp[comp.index >= eval_start].where(uni)
    resid = residualize(comp_dev, [mom7.where(uni), mom30.where(uni)])
    fx["momentum_control"] = {t: score(resid, y[y.index >= eval_start].where(uni), lag)
                              for t, (y, lag) in targets.items()}
    fx["timing_canary"] = {}
    for t, (y, lag) in targets.items():
        y_dev = y[y.index >= eval_start].where(uni)
        contemporaneous = comp.shift(-1)[comp.index >= eval_start].where(uni)   # swap day d vs return over day d
        extra_lag = comp.shift(1)[comp.index >= eval_start].where(uni)
        fx["timing_canary"][t] = {"contemporaneous": score(contemporaneous, y_dev, lag),
                                  "extra_lag_1d": score(extra_lag, y_dev, lag)}
    build = json.loads((SMW / "feature_build.json").read_text())
    fx["contract_share"] = {k: build[k] for k in ("n_checked", "n_contracts", "contract_gross_share")}
    cov = comp_dev.notna().sum(axis=1)
    fx["coverage_per_month"] = {k.strftime("%Y-%m"): float(v) for k, v in cov.resample("MS").mean().items()}
    fx["breadth_per_month"] = {k.strftime("%Y-%m"): float(v) for k, v in uni[uni.index >= eval_start].sum(axis=1).resample("MS").mean().items()}
    rc = results["ret_24h|composite"]
    fx["power"] = {"ic_se_24h": rc["ic_se"], "floor_in_se": IC_FLOOR / rc["ic_se"] if rc["ic_se"] else None,
                   "n_days": rc["n_days"]}
    per_feature_cov = {k: float(panels[k][panels[k].index >= eval_start].where(uni).notna().mean().mean()) for k in SIGNS}
    fx["feature_coverage"] = per_feature_cov
    deep = universe_mask(json.loads((SMW / "universe_1m_slice.json").read_text()), close.index, syms) & uni
    band = uni & ~deep
    fx["depth_slice"] = {}
    for label, mask in (("ge_1m", deep), ("250k_1m", band)):
        fx["depth_slice"][label] = {t: score(comp[comp.index >= eval_start].where(mask),
                                             y[y.index >= eval_start].where(mask), lag)
                                    for t, (y, lag) in targets.items()}

    out = {"experiment": EXP, "eval_window": window, "eval_start_rule": f"first day with >= {MIN_QUALIFIED} qualified + 1",
           "n_symbols": len(syms), "T1": t1, "verdict_by_horizon": verdict, "results": results,
           "forensics": fx, "n_trials_this_experiment": registry.trial_count(EXP),
           "n_trials_program": registry.trial_count()}
    out_p.write_text(json.dumps(out, indent=1, default=float))
    print(f"\nT1 {t1}  {json.dumps(verdict, indent=1)}", flush=True)
    print(f"momentum control: { {t: round(v['mean_ic'], 4) for t, v in fx['momentum_control'].items()} }", flush=True)


if __name__ == "__main__":
    main()
