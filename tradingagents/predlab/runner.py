"""Cell runner: walk a registered cell's series through rolling origins.

For every model: collect one forecast per origin, score the registered loss,
and test against the cell's strong baseline (DM-HLN primary, Clark-West and
Giacomini-White companions, Pesaran-Timmermann where signs are scoreable).
Writes forecasts parquet + result card + one ledger row per model unless
dry=True.
"""

from __future__ import annotations

import json
import time as _time
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.predlab import dm as dmod
from tradingagents.predlab import direction, losses, registry
from tradingagents.predlab.splits import rolling_origin

_SUBPERIODS = [
    ("2021-2022", "2021-01-01", "2022-12-31"),
    ("2023-2024", "2023-01-01", "2024-12-31"),
    ("2025Q1", "2025-01-01", "2025-03-31"),
]


def _loss_vector(loss_name: str, y: np.ndarray, pred: np.ndarray, cell: dict) -> np.ndarray:
    if loss_name == "se":
        return losses.se(y, pred)
    if loss_name == "qlike":
        return losses.qlike(pred, y)  # pred = variance forecast, y = realized variance
    if loss_name == "brier":
        return losses.brier(pred, (y > 0).astype(np.float64))
    if loss_name == "mase":
        scale = cell["_mase_scale"]
        return losses.mase(y, pred, scale)
    raise ValueError(f"unknown loss {loss_name!r}")


def _pt_inputs(target: str, y: np.ndarray, pred: np.ndarray) -> "tuple[np.ndarray, np.ndarray]":
    if target.startswith("T2"):
        return y > 0, pred > 0.5
    return y > 0, pred > 0


def run_cell(
    cell: dict,
    series: pd.DataFrame,
    models: list,
    gates_key: str,
    tier: str,
    dry: bool = False,
    return_forecasts: bool = False,
):
    """Run every model over the cell's origins; return one tidy row per model."""
    end_date = str(series.index.max().date())
    registry.assert_dev_window(end_date, allow_holdout=bool(cell.get("allow_holdout", False)))

    y = series["y"].to_numpy(dtype=np.float64)
    exog_cols = [c for c in series.columns if c != "y"]
    X = series[exog_cols].to_numpy(dtype=np.float64) if exog_cols else None

    h = int(cell["horizon_bars"])
    embargo = int(cell.get("embargo", 0))
    refit_every = int(cell.get("refit_every", 1))
    splits = rolling_origin(
        len(y), min_train=int(cell["min_train"]), horizon=h,
        step=int(cell.get("step", 1)), embargo=embargo,
    )
    eval_start = cell.get("eval_start")
    if eval_start is not None:
        start_ts = pd.Timestamp(eval_start, tz="UTC")
        splits = [sp for sp in splits if series.index[sp.origin] >= start_ts]
    if not splits:
        raise ValueError(f"cell {cell['cell']}: no origins (series too short)")

    loss_name = cell["loss"]
    if loss_name == "mase" and "_mase_scale" not in cell:
        m = int(cell.get("mase_m", 1))
        cell["_mase_scale"] = losses.mase_scale(y[: int(cell["min_train"])], m=m)

    origins = np.array([sp.origin for sp in splits])
    y_true = y[origins]
    ts_origin = series.index[origins]

    preds: "dict[str, np.ndarray]" = {}
    for model in models:
        # a model may declare its own refit cadence (e.g. Phase-1 champions
        # keep their registered cadence inside Tier-2 comparison runs)
        model_refit = int(getattr(model, "refit_every", None) or refit_every)
        out = np.empty(len(splits), dtype=np.float64)
        _t_model = _time.time()
        for i, sp in enumerate(splits):
            if i and i % 5000 == 0:
                rate = i / max(_time.time() - _t_model, 1e-9)
                print(f"    [{cell['cell']}] {model.name}: {i}/{len(splits)} "
                      f"({rate:.0f} orig/s)", flush=True)
            if i % model_refit == 0:
                Xt = X[: sp.train_end] if X is not None else None
                model.fit(y[: sp.train_end], Xt)
            n_hist = sp.origin - h + 1  # labels realized at the origin
            y_hist = y[:n_hist] if n_hist > 0 else y[:1]
            x_now = X[sp.origin] if X is not None else None
            if getattr(model, "wants_x_hist", False):
                # period-labeled exog (realized at t+h, e.g. returns for GARCH):
                # only the same realized prefix as y_hist is in the info set
                x_hist = X[:n_hist] if X is not None else None
                out[i] = model.predict(y_hist, x_now, x_hist)
            else:
                out[i] = model.predict(y_hist, x_now)
        preds[model.name] = out

    base_name = cell["strong_baseline"]
    if base_name not in preds:
        raise ValueError(f"strong baseline {base_name!r} not among models {sorted(preds)}")
    base_losses = _loss_vector(loss_name, y_true, preds[base_name], cell)

    rows = []
    for model in models:
        p = preds[model.name]
        lv = _loss_vector(loss_name, y_true, p, cell)
        pair_ok = ~(np.isnan(base_losses) | np.isnan(lv))
        r_dm = dmod.dm_test(base_losses[pair_ok], lv[pair_ok], h=h)
        r_gw = dmod.gw_test(base_losses[pair_ok], lv[pair_ok], h=h)
        e_base = y_true - preds[base_name]
        e_model = y_true - p
        r_cw = dmod.clark_west(
            e_base[pair_ok], e_model[pair_ok],
            preds[base_name][pair_ok], p[pair_ok], h=h,
        )
        ys, xs = _pt_inputs(cell["target"], y_true[pair_ok], p[pair_ok])
        r_pt = direction.pt_test(ys, xs)
        sub = {}
        for label, lo, hi in _SUBPERIODS:
            mask = (ts_origin >= lo) & (ts_origin <= hi) & pair_ok
            if mask.sum() >= 30:
                d = base_losses[mask] - lv[mask]
                sub[label] = float(np.nanmean(d))
        rows.append({
            "model": model.name,
            "loss_mean": float(np.nanmean(lv)),
            "dm_stat": r_dm.stat, "dm_p": r_dm.pvalue,
            "cw_p": r_cw.pvalue, "gw_p": r_gw.pvalue, "pt_p": r_pt.pvalue,
            "degenerate": bool(r_dm.degenerate),
            "n_origins": int(pair_ok.sum()),
            "sub_periods": sub,
        })

    result = pd.DataFrame(rows)

    if not dry:
        data_root = registry.gates_path().parent
        fdir = data_root / "forecasts" / gates_key / cell["cell"].replace("|", "_")
        fdir.mkdir(parents=True, exist_ok=True)
        for name, p in preds.items():
            pd.DataFrame({"ts": ts_origin, "y_true": y_true, "pred": p}).to_parquet(
                fdir / f"{name}.parquet"
            )
        cdir = data_root / "cards" / gates_key
        cdir.mkdir(parents=True, exist_ok=True)
        card = {
            "cell": cell["cell"], "tier": tier, "loss": loss_name,
            "strong_baseline": base_name,
            "n_origins": int(len(origins)),
            "window": [str(ts_origin.min().date()), str(ts_origin.max().date())],
            "per_model": {
                r["model"]: {k: v for k, v in r.items() if k != "model"} for r in rows
            },
        }
        card_path = cdir / f"{cell['cell'].replace('|', '_')}.json"
        existing = json.loads(card_path.read_text()) if card_path.exists() else {}
        existing[tier] = card
        card_path.write_text(json.dumps(existing, indent=1, default=float))
        for r in rows:
            registry.log_trial(
                gates_key, cell["cell"], r["model"],
                {
                    "cell": cell["cell"], "model": r["model"], "tier": tier,
                    "loss": loss_name, "h": h, "min_train": cell["min_train"],
                    "refit_every": refit_every,
                },
                (str(ts_origin.min().date()), str(ts_origin.max().date())),
                {
                    "loss_mean": r["loss_mean"], "dm_p": r["dm_p"],
                    "cw_p": r["cw_p"], "pt_p": r["pt_p"],
                },
            )
    if return_forecasts:
        return result, preds
    return result
