"""Phase-5: combinations, per-cell MCS, champion freeze (registered: predlab_p5).

Modes:
  combos    build lgb_cal (C1) + ttm_ens (C2) forecast files
  mcs       run HLN MCS per registered cell on stored dev forecasts -> champions
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import dm as dmod  # noqa: E402
from tradingagents.predlab import losses as L  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402
from tradingagents.predlab.meanstats import nw_tstat  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
FC = DATA_ROOT / "predlab" / "forecasts"

# which gates key holds each stored model's forecasts, per cell family
SOURCE = {
    "harq": "predlab_p2_ml", "gjr11": "predlab_p2_ml", "lgb": "predlab_p2_ml",
    "enet": "predlab_p2_ml", "har_levels": "predlab_p2_ml",
    "seasonal_ar_m24": "predlab_p2_ml", "seasonal_ar_m7": "predlab_p2_ml",
    "seasonal_naive_m24": "predlab_p2_ml", "seasonal_naive_m7": "predlab_p2_ml",
    "garch11": "predlab_p1_classical", "egarch11": "predlab_p1_classical",
    "ewma_0.94": "predlab_p1_classical", "log_har": "predlab_p1_classical",
    "logit_lags5": "predlab_p2_ml", "base_rate": "predlab_p2_ml",
    "lgb_cal": "predlab_p5", "ttm_ens": "predlab_p5",
}


def _load(cell_id: str, model: str) -> pd.DataFrame:
    keys = [SOURCE[model], "predlab_p2_ml", "predlab_p1_classical", "predlab_p5"]
    for key in dict.fromkeys(keys):  # ordered dedup
        p = FC / key / cell_id.replace("|", "_") / f"{model}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            return df.set_index(pd.DatetimeIndex(df["ts"]))[["y_true", "pred"]]
    raise FileNotFoundError(f"no stored forecasts for {cell_id}/{model}")


def build_lgb_cal() -> None:
    """C1: isotonic recalibration of stored ProbClip(LGB) T2 probabilities."""
    from sklearn.isotonic import IsotonicRegression

    for sym in ("BTCUSDT", "ETHUSDT"):
        cell_id = f"{sym}|1h|T2_dir"
        base = _load(cell_id, "lgb")
        p = base["pred"].to_numpy()
        y_up = (base["y_true"].to_numpy() > 0).astype(float)
        out = np.full(len(p), np.nan)
        window, refit = 4320, 168
        for start in range(window, len(p), refit):
            iso = IsotonicRegression(y_min=0.02, y_max=0.98, out_of_bounds="clip")
            iso.fit(p[start - window:start], y_up[start - window:start])
            end = min(start + refit, len(p))
            out[start:end] = iso.predict(p[start:end])
        keep = ~np.isnan(out)
        df = pd.DataFrame({"ts": base.index[keep], "y_true": base["y_true"].to_numpy()[keep],
                           "pred": out[keep]})
        d = FC / "predlab_p5" / cell_id.replace("|", "_")
        d.mkdir(parents=True, exist_ok=True)
        df.to_parquet(d / "lgb_cal.parquet")
        bl = L.brier(out[keep], y_up[keep]).mean()
        raw = L.brier(p[keep], y_up[keep]).mean()
        print(f"{cell_id} lgb_cal: brier {bl:.6f} (raw lgb {raw:.6f}) n={keep.sum()}",
              flush=True)


def build_ttm_ens() -> None:
    """C2: 0.5*TTM + 0.5*gjr11 on TTM's valid window (matched comparison)."""
    # regenerate TTM forecasts for ETH 1h T3 on its window, aligned to gjr ts
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from predlab_p4 import TTMModel, _series

    cell_id = "ETHUSDT|1h|T3_rv"
    gjr = _load(cell_id, "gjr11")
    y = _series("ETHUSDT", "1h", "T3_rv")
    ctx_len = 2048
    win = (pd.Timestamp("2024-11-01", tz="UTC"), pd.Timestamp("2025-03-31", tz="UTC"))
    ts_sel = gjr.index[(gjr.index >= win[0]) & (gjr.index <= win[1])]
    pos = y.index.get_indexer(ts_sel)
    ok = pos >= ctx_len
    ts_sel, pos = ts_sel[ok], pos[ok]
    model = TTMModel(ctx_len, freq="h")
    yv = y.to_numpy()
    contexts = [yv[p - ctx_len:p] for p in pos]
    ttm = np.maximum(model.forecast(contexts), 1e-12)
    ens = 0.5 * ttm + 0.5 * gjr.loc[ts_sel, "pred"].to_numpy()
    df = pd.DataFrame({"ts": ts_sel, "y_true": gjr.loc[ts_sel, "y_true"].to_numpy(),
                       "pred": ens})
    d = FC / "predlab_p5" / cell_id.replace("|", "_")
    d.mkdir(parents=True, exist_ok=True)
    df.to_parquet(d / "ttm_ens.parquet")
    yq = gjr.loc[ts_sel, "y_true"].to_numpy()
    ql_e = np.nanmean(L.qlike(ens, yq))
    ql_g = np.nanmean(L.qlike(gjr.loc[ts_sel, "pred"].to_numpy(), yq))
    lf, lg = L.qlike(ens, yq), L.qlike(gjr.loc[ts_sel, "pred"].to_numpy(), yq)
    okp = ~(np.isnan(lf) | np.isnan(lg))
    r = dmod.dm_test(lg[okp], lf[okp], h=1)
    print(f"{cell_id} ttm_ens: qlike {ql_e:.6f} vs gjr {ql_g:.6f} "
          f"(impr {100*(ql_g-ql_e)/ql_g:+.1f}%) dm_p={r.pvalue:.3g} n={okp.sum()}",
          flush=True)


def _loss_frame(cell_id: str, spec: dict) -> pd.DataFrame:
    frames = {}
    for m in spec["set"]:
        if m == "ttm_ens":
            continue  # matched-window only, per registration note
        df = _load(cell_id, m)
        frames[m] = df
    common = None
    for df in frames.values():
        common = df.index if common is None else common.intersection(df.index)
    cols = {}
    for m, df in frames.items():
        sub = df.loc[common]
        y = sub["y_true"].to_numpy()
        p = sub["pred"].to_numpy()
        if spec["loss"] == "qlike":
            cols[m] = L.qlike(np.maximum(p, 1e-12), y)
        elif spec["loss"] == "mase":
            cols[m] = L.ae(y, p)  # scale-free comparison: constant scale cancels
        else:
            cols[m] = L.brier(p, (y > 0).astype(float))
    out = pd.DataFrame(cols, index=common).dropna()
    return out


def run_mcs() -> None:
    from arch.bootstrap import MCS

    entry = registry.get_experiment("predlab_p5")
    champions = {}
    for cell_id, spec in entry["cells"].items():
        if cell_id.startswith("T7"):
            champions[cell_id] = run_t7_rule(spec)
            continue
        lf = _loss_frame(cell_id, spec)
        block = 24 if "|1h|" in cell_id else 5
        mcs = MCS(lf, size=0.10, block_size=block, method="R", seed=0)
        mcs.compute()
        included = list(mcs.included)
        means = lf.mean()
        champ = means[included].idxmin()
        champions[cell_id] = {
            "included": included, "excluded": list(mcs.excluded),
            "champion": champ, "dev_loss": float(means[champ]),
            "baseline": spec.get("baseline"),
            "baseline_loss": float(means.get(spec.get("baseline"), np.nan)),
            "n": int(len(lf)),
        }
        print(f"{cell_id}: MCS included={included} -> champion={champ} "
              f"(loss {means[champ]:.6g}, n={len(lf)})", flush=True)
    out = DATA_ROOT / "predlab" / "p5_champions.json"
    out.write_text(json.dumps(champions, indent=1))
    print(f"written {out}")


def run_t7_rule(spec: dict) -> dict:
    ics = {}
    raw = json.loads((DATA_ROOT / "predlab" / "t7_raw_ics.json").read_text())
    ics["park_5"] = raw["ret_24h|park_5"]["mean_ic"]
    # combos ICs from ledger prints (stored in ledger); recompute quickly is
    # heavy — use ledger metrics
    for row in (DATA_ROOT / "predlab" / "trial_ledger.jsonl").read_text().splitlines():
        rec = json.loads(row)
        if rec.get("experiment") == "predlab_p2_t7" and rec.get("model") in (
                "ridge_combo", "lgb_combo"):
            ics[rec["model"]] = rec["metrics"]["mean_ic"]
    champ = max(ics, key=lambda k: abs(ics[k]))
    print(f"T7|ret_24h: ICs={ {k: round(v,4) for k,v in ics.items()} } -> "
          f"champion={champ}", flush=True)
    return {"ics": ics, "champion": champ,
            "note": "highest |IC|; pairwise-DM equivalence documented in "
                    "p2_t7_xs.md (combos not significantly better)"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True, choices=["combos", "mcs"])
    args = ap.parse_args()
    if args.mode == "combos":
        build_lgb_cal()
        build_ttm_ens()
    else:
        run_mcs()


if __name__ == "__main__":
    main()
