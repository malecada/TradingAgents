"""rviv_p0 — RV-forecast vs debiased-DVOL, P0 dev-window probe.

Charter: docs/superpowers/specs/2026-08-25-rviv-p0-charter.md
Gates key: predlab_rviv_p0 (registered 2026-08-25, pre-result).

Claim under test: PIT HAR-30 realized-vol forecast (C2, primary) beats the
debiased-DVOL implied forecast (B1) at next-30d realized vol, QLIKE, DM p<0.05,
rel improvement >=3%, on BOTH BTC and ETH. Everything else is disclosure.

Runs entirely on-disk (rv_1d store + DVOL parquets); no network, no holdout.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RV_DIR = ROOT / "data" / "predlab" / "rv_1d"
DVOL_DIR = ROOT / "data" / "options"
OUT_DIR = ROOT / "data" / "predlab" / "rviv"
LEDGER = ROOT / "data" / "predlab" / "trial_ledger.jsonl"

ASSETS = {"BTCUSDT": "btc", "ETHUSDT": "eth"}
EVAL_START, EVAL_END = "2022-06-01", "2025-03-31"
GAP_DAYS = 30
MIN_TRAIN = 365
PRED_FLOOR = 0.01
ANN = 365.0

# ---------------------------------------------------------------- core math


def rv30_target(r: pd.Series, min_obs: int = 25) -> pd.Series:
    """RV30(t) = sqrt(365 * mean(r^2 over t+1..t+30 calendar days)).

    Uncentered; requires >= min_obs non-NaN daily returns in the window.
    """
    idx = pd.date_range(r.index.min(), r.index.max(), freq="D", tz="UTC")
    s2 = r.pow(2).reindex(idx)
    fwd = s2.shift(-1)[::-1].rolling(GAP_DAYS, min_periods=min_obs).mean()[::-1]
    return np.sqrt(ANN * fwd).reindex(r.index)


def trailing_rv(r: pd.Series, k: int, min_obs: int | None = None) -> pd.Series:
    """Trailing RV_k(t) = sqrt(365 * mean(r^2 over t-k+1..t)), calendar days."""
    if min_obs is None:
        min_obs = int(np.ceil(0.8 * k))
    idx = pd.date_range(r.index.min(), r.index.max(), freq="D", tz="UTC")
    s2 = r.pow(2).reindex(idx)
    m = s2.rolling(k, min_periods=min_obs).mean()
    return np.sqrt(ANN * m).reindex(r.index)


def qlike(true_var: np.ndarray, pred_var: np.ndarray) -> np.ndarray:
    ratio = true_var / pred_var
    return ratio - np.log(ratio) - 1.0


def dm_test(l1: np.ndarray, l2: np.ndarray, lag: int = 30) -> tuple[float, float]:
    """Diebold-Mariano with Newey-West HAC variance (Bartlett weights).

    Returns (stat, two-sided p, normal approx). Negative stat = l1 smaller loss.
    """
    from math import erf, sqrt

    d = np.asarray(l1, dtype=np.float64) - np.asarray(l2, dtype=np.float64)
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    gamma0 = float(dc @ dc) / n
    var = gamma0
    for j in range(1, min(lag, n - 1) + 1):
        w = 1.0 - j / (lag + 1.0)
        var += 2.0 * w * float(dc[j:] @ dc[:-j]) / n
    if var <= 0 or n == 0:
        return 0.0, 1.0
    stat = dbar / np.sqrt(var / n)
    p = 2.0 * (1.0 - 0.5 * (1.0 + erf(abs(stat) / sqrt(2.0))))
    return float(stat), float(p)


def expanding_pit_ols_forecast(
    X: pd.DataFrame,
    y: pd.Series,
    eval_index: pd.DatetimeIndex,
    gap_days: int = GAP_DAYS,
    min_train: int = MIN_TRAIN,
    floor: float | None = None,
    return_last_train: bool = False,
):
    """Daily-refit expanding OLS obeying the PIT training-pair rule.

    A pair (X(s), y(s)) is trainable at eval day t only if s + gap_days <= t,
    i.e. the 30d target window ending at s+30 has completed by t.
    """
    feat = X.dropna()
    yv = y.dropna()
    common = feat.index.intersection(yv.index)
    feat, yv = feat.loc[common], yv.loc[common]
    preds, last_train = {}, {}
    for t in eval_index:
        cutoff = t - pd.Timedelta(days=gap_days)
        train = feat.index[feat.index <= cutoff]
        if len(train) < min_train or t not in X.index or X.loc[t].isna().any():
            preds[t] = np.nan
            continue
        A = np.column_stack([np.ones(len(train)), feat.loc[train].to_numpy()])
        coef, *_ = np.linalg.lstsq(A, yv.loc[train].to_numpy(), rcond=None)
        p = float(coef[0] + coef[1:] @ X.loc[t].to_numpy())
        preds[t] = max(p, floor) if floor is not None else p
        last_train[t] = train.max()
    out = pd.Series(preds).reindex(eval_index)
    if return_last_train:
        return out, last_train
    return out


# ---------------------------------------------------------------- pipeline


def load_asset(sym: str, dvol_name: str, log_returns: bool = False):
    rv = pd.read_parquet(RV_DIR / f"{sym}.parquet")
    r = rv["ret"] if log_returns else np.exp(rv["ret"]) - 1.0
    r = r.dropna()
    dv = pd.read_parquet(DVOL_DIR / f"{dvol_name}_dvol.parquet")
    iv = (dv["dvol_close"] / 100.0).dropna()
    return r, iv


def build_forecasts(r: pd.Series, iv: pd.Series, eval_index: pd.DatetimeIndex):
    tgt = rv30_target(r)
    rv1 = trailing_rv(r, 1, min_obs=1)
    rv5 = trailing_rv(r, 5)
    rv30 = trailing_rv(r, 30)
    rv20 = trailing_rv(r, 20)
    ewma = np.sqrt(ANN * r.pow(2).ewm(span=20).mean())

    har_X = pd.concat({"rv1": rv1, "rv5": rv5, "rv30": rv30}, axis=1)
    hariv_X = har_X.join(iv.rename("iv"), how="left")
    iv_X = iv.to_frame("iv")

    fc = {
        "B0_raw_dvol": iv.reindex(eval_index),
        "B1_debiased_dvol": expanding_pit_ols_forecast(iv_X, tgt, eval_index, floor=PRED_FLOOR),
        "B2_rv20": rv20.reindex(eval_index),
        "C1_ewma20": ewma.reindex(eval_index),
        "C2_har30": expanding_pit_ols_forecast(har_X, tgt, eval_index, floor=PRED_FLOOR),
        "C3_har30_iv": expanding_pit_ols_forecast(hariv_X, tgt, eval_index, floor=PRED_FLOOR),
    }
    return tgt, fc


def evaluate(tgt: pd.Series, fc: dict[str, pd.Series], eval_index: pd.DatetimeIndex):
    frame = pd.DataFrame(fc).reindex(eval_index)
    frame["tgt"] = tgt.reindex(eval_index)
    frame = frame.dropna()
    tv = frame["tgt"].to_numpy() ** 2
    res, losses = {}, {}
    for name in fc:
        pv = frame[name].to_numpy() ** 2
        ql = qlike(tv, pv)
        losses[name] = ql
        res[name] = {
            "qlike": float(ql.mean()),
            "mse_vol": float(((frame[name] - frame["tgt"]) ** 2).mean()),
        }
    for name in fc:
        if name == "B1_debiased_dvol":
            continue
        stat, p = dm_test(losses[name], losses["B1_debiased_dvol"], lag=GAP_DAYS)
        res[name]["dm_stat_vs_B1"] = stat
        res[name]["dm_p_vs_B1"] = p
        res[name]["rel_qlike_impr_vs_B1"] = float(
            1.0 - res[name]["qlike"] / res["B1_debiased_dvol"]["qlike"]
        )
    return res, len(frame), frame


def vrp_descriptive(tgt: pd.Series, iv: pd.Series) -> dict:
    df = pd.concat({"iv": iv, "rv": tgt}, axis=1).dropna()
    out = {}
    for yr, sub in df.groupby(df.index.year):
        out[str(yr)] = {
            "mean_var_premium": float((sub["iv"] ** 2 - sub["rv"] ** 2).mean()),
            "mean_vol_premium": float((sub["iv"] - sub["rv"]).mean()),
            "n_days": int(len(sub)),
        }
    return out


def run_asset(sym: str, dvol_name: str, log_returns: bool = False, iv_shift_days: int = 0):
    r, iv = load_asset(sym, dvol_name, log_returns=log_returns)
    if iv_shift_days:
        iv = pd.Series(np.roll(iv.to_numpy(), iv_shift_days), index=iv.index)
    eval_index = pd.date_range(EVAL_START, EVAL_END, freq="D", tz="UTC")
    tgt, fc = build_forecasts(r, iv, eval_index)
    res, n, frame = evaluate(tgt, fc, eval_index)
    sanity = {
        "mean_rv30": float(frame["tgt"].mean()),
        "mean_iv": float(iv.reindex(frame.index).mean()),
    }
    return res, n, vrp_descriptive(tgt, iv), sanity


def git_commit_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    commit = git_commit_short()
    ts = datetime.now(timezone.utc).isoformat()
    results = {"registered": "predlab_rviv_p0", "git_commit": commit, "ts_utc": ts}

    for sym, dvname in ASSETS.items():
        res, n, vrp, sanity = run_asset(sym, dvname)
        results[sym] = {"models": res, "n_eval_days": n, "vrp_by_year": vrp, "sanity_F4": sanity}
        # F1 convention-swap kill-test: log-return target
        res_log, n_log, _, _ = run_asset(sym, dvname, log_returns=True)
        results[sym]["F1_log_target"] = {
            "C2_rel_impr": res_log["C2_har30"]["rel_qlike_impr_vs_B1"],
            "C2_dm_p": res_log["C2_har30"]["dm_p_vs_B1"],
            "n": n_log,
        }
        # F2 shuffled-IV probe: circular shift 180d
        res_sh, n_sh, _, _ = run_asset(sym, dvname, iv_shift_days=180)
        results[sym]["F2_shifted_iv"] = {
            "B1_qlike": res_sh["B1_debiased_dvol"]["qlike"],
            "B2_qlike": res_sh["B2_rv20"]["qlike"],
            "C2_qlike": res_sh["C2_har30"]["qlike"],
            "C3_qlike": res_sh["C3_har30_iv"]["qlike"],
            "n": n_sh,
        }

    # primary verdict inputs (verdict itself recorded in gates.json by hand)
    primary = {}
    for sym in ASSETS:
        m = results[sym]["models"]["C2_har30"]
        primary[sym] = {
            "rel_qlike_impr_vs_B1": m["rel_qlike_impr_vs_B1"],
            "dm_p_vs_B1": m["dm_p_vs_B1"],
            "passes": bool(m["rel_qlike_impr_vs_B1"] >= 0.03 and m["dm_p_vs_B1"] < 0.05),
        }
    primary["PASS_both_assets"] = all(primary[s]["passes"] for s in ASSETS)
    results["primary_criterion"] = primary

    out_path = OUT_DIR / "p0_results.json"
    out_path.write_text(json.dumps(results, indent=1))

    with LEDGER.open("a") as fh:
        for sym in ASSETS:
            for model, m in results[sym]["models"].items():
                cfg = {"model": model, "eval": [EVAL_START, EVAL_END], "loss": "qlike_var"}
                row = {
                    "ts_utc": ts,
                    "experiment": "predlab_rviv_p0",
                    "cell": f"{sym}|1d|RV30",
                    "model": model,
                    "config": cfg,
                    "config_hash": hashlib.sha1(
                        json.dumps(cfg, sort_keys=True).encode()
                    ).hexdigest()[:12],
                    "git_commit": commit,
                    "window": [EVAL_START, EVAL_END],
                    "metrics": m,
                }
                fh.write(json.dumps(row) + "\n")

    print(json.dumps(results["primary_criterion"], indent=1))
    for sym in ASSETS:
        print(f"\n{sym} (n={results[sym]['n_eval_days']}):")
        for model, m in sorted(results[sym]["models"].items()):
            extra = (
                f" impr={m['rel_qlike_impr_vs_B1']:+.3f} p={m['dm_p_vs_B1']:.4f}"
                if "dm_p_vs_B1" in m
                else " (bar)"
            )
            print(f"  {model:18s} qlike={m['qlike']:.4f}{extra}")
        print(f"  F1 log-target: {results[sym]['F1_log_target']}")
        print(f"  F2 shifted-IV: {results[sym]['F2_shifted_iv']}")
        print(f"  F4 sanity: {results[sym]['sanity_F4']}")
    print(f"\nresults -> {out_path}")


if __name__ == "__main__":
    main()
