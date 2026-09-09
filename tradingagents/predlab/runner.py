"""Cell runner: walk a registered cell's series through rolling origins.

For every model: collect one forecast per origin, score the registered loss,
and test against the cell's strong baseline. DM-HAC is primary for nonnested
comparisons; declared nesting requires a registered matching-loss test.
Clark-West/Giacomini-White remain diagnostics, as does Pesaran-Timmermann
where signs are scoreable.
Writes forecasts parquet + result card + one ledger row per model unless
dry=True.
"""

from __future__ import annotations

import json
import hashlib
import inspect
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


def series_digest(series: pd.DataFrame) -> str:
    """Bind the in-memory values, full origin index, column identities and dtypes."""
    schema = {
        "columns": list(series.columns), "dtypes": [str(t) for t in series.dtypes],
        "index_names": list(series.index.names), "index_dtype": str(series.index.dtype),
    }
    digest = hashlib.sha256(json.dumps(schema, sort_keys=True, default=str).encode())
    digest.update(pd.util.hash_pandas_object(series, index=True).to_numpy().astype("<u8").tobytes())
    return digest.hexdigest()


def model_config(model) -> dict:
    """Capture resolved public constructor settings before fit mutates state."""
    def encode(value):
        if hasattr(value, "fit") and hasattr(value, "predict"):
            return model_config(value)
        if isinstance(value, dict):
            return {str(k): encode(v) for k, v in value.items()}
        if isinstance(value, (tuple, list, np.ndarray)):
            return [encode(v) for v in value]
        if isinstance(value, np.generic):
            return value.item()
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise TypeError(f"model setting {type(value).__name__} needs explicit serializable provenance")
    parameters = {}
    for name, parameter in inspect.signature(type(model).__init__).parameters.items():
        if name == "self" or parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        if hasattr(model, name):
            parameters[name] = encode(getattr(model, name))
        elif parameter.default is not inspect.Parameter.empty:
            parameters[name] = encode(parameter.default)
        else:
            raise ValueError(f"model {type(model).__name__} does not expose constructor setting {name}")
    return {"class": f"{type(model).__module__}.{type(model).__qualname__}", "parameters": parameters}


def forecast_frame(y_true, raw_pred, baseline, loss_name: str, cell: dict) -> pd.DataFrame:
    """Apply declared-baseline fallback without changing the scoring clock.

    Prospective policy v1. Missing targets/baselines are disclosed exclusions;
    model failures never remove an otherwise scoreable origin. Raw predictions
    are preserved so failure coverage can be audited independently of loss.
    """
    y = np.asarray(y_true, dtype=float)
    raw = np.asarray(raw_pred, dtype=float)
    base = np.asarray(baseline, dtype=float)
    target_valid = np.isfinite(y)
    if loss_name == "qlike":
        target_valid &= y > 0
    reason = np.full(raw.shape, "", dtype=object)
    reason[~np.isfinite(raw)] = "missing_or_nonfinite"
    if loss_name == "qlike":
        reason[np.isfinite(raw) & (raw <= 0)] = "nonpositive_variance"
    if loss_name == "brier":
        reason[np.isfinite(raw) & ((raw < 0) | (raw > 1))] = "invalid_probability"
    with np.errstate(all="ignore"):
        base_loss = _loss_vector(loss_name, y, base, cell)
        raw_loss = _loss_vector(loss_name, y, raw, cell)
    baseline_valid = np.isfinite(base) & np.isfinite(base_loss)
    if loss_name == "brier":
        baseline_valid &= (base >= 0) & (base <= 1)
    scoreable = target_valid & baseline_valid
    reason[(reason == "") & scoreable & ~np.isfinite(raw_loss)] = "nonfinite_loss"
    raw_valid = reason == ""
    fallback_used = ~raw_valid & baseline_valid
    effective = np.where(fallback_used, base, raw)
    return pd.DataFrame({
        "y_true": y, "raw_pred": raw, "pred": effective,
        "fallback_used": fallback_used, "fallback_reason": reason,
        "raw_valid": raw_valid, "target_valid": target_valid,
        "baseline_valid": baseline_valid, "scoreable": scoreable,
    })


def _pt_inputs(target: str, y: np.ndarray, pred: np.ndarray) -> "tuple[np.ndarray, np.ndarray]":
    if target.startswith("T2"):
        return y > 0, pred > 0.5
    return y > 0, pred > 0


def _inference_metadata(cell: dict, model_name: str) -> dict:
    """A model family name alone never establishes nesting or test validity."""
    nested = cell.get("nested_models", {}).get(model_name) == cell["strong_baseline"]
    if nested:
        eligible = cell["loss"] == "se" and cell.get("registered_nested_test") == "clark_west"
        primary = "clark_west" if eligible else "unavailable_nested_loss_test"
    else:
        eligible, primary = True, "dm_hac"
    return {"nested": nested, "primary_test": primary, "inference_eligible": eligible}


def run_cell(
    cell: dict,
    series: pd.DataFrame,
    models: list,
    gates_key: str,
    tier: str,
    dry: bool = False,
    return_forecasts: bool = False,
    return_diagnostics: bool = False,
):
    """Run a registered cell. Optional diagnostics returns (rows, preds, frames)."""
    end_date = str(series.index.max().date())
    registry.assert_dev_window(end_date, allow_holdout=bool(cell.get("allow_holdout", False)))

    if not dry:
        start_date = str(pd.Timestamp(cell["eval_start"]).date()) if cell.get("eval_start") else str(series.index.min().date())
        provenance = registry.preflight(gates_key, (start_date, end_date))
        data_root = registry.gates_path().parent
        fdir = data_root / "forecasts" / gates_key / cell["cell"].replace("|", "_")
        cdir = data_root / "cards" / gates_key
        card_path = cdir / f"{cell['cell'].replace('|', '_')}.json"
        if any((fdir / f"{model.name}.parquet").exists() for model in models):
            raise FileExistsError("existing forecast files are immutable; use a registered correction key")
        if card_path.exists() and tier in json.loads(card_path.read_text()):
            raise FileExistsError("existing card tier is immutable; use a registered correction key")
        if cell.get("nested_models"):
            # Empirical callers cannot assert a test registration absent from
            # the gate just verified by preflight. Dry fixtures supply it explicitly.
            registered_test = registry.get_experiment(gates_key).get("tests", {}).get("nested")
            cell = dict(cell, registered_nested_test=registered_test)

    input_sha256 = series_digest(series)
    declared_models = {model.name: model_config(model) for model in models}

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
    raw_preds = preds
    diagnostics = {
        name: forecast_frame(y_true, raw, raw_preds[base_name], loss_name, cell)
        for name, raw in raw_preds.items()
    }
    preds = {name: frame["pred"].to_numpy() for name, frame in diagnostics.items()}
    pair_ok = diagnostics[base_name]["scoreable"].to_numpy()
    base_losses = _loss_vector(loss_name, y_true, preds[base_name], cell)

    rows = []
    for model in models:
        p = preds[model.name]
        lv = _loss_vector(loss_name, y_true, p, cell)
        diag = diagnostics[model.name]
        if not np.isfinite(lv[pair_ok]).all():
            raise ValueError("nonfinite effective forecast loss on common scoring clock")
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
            **_inference_metadata(cell, model.name),
            "loss_mean": float(np.mean(lv[pair_ok])) if pair_ok.any() else float("nan"),
            "forecast_policy": "declared_baseline_fallback_v1",
            "inference_policy": "hac-selection-v2",
            "n_requested_origins": int(len(origins)),
            "n_scoreable_origins": int(pair_ok.sum()),
            "n_excluded_target": int((~diag["target_valid"]).sum()),
            "n_excluded_baseline": int((diag["target_valid"] & ~diag["baseline_valid"]).sum()),
            "n_fallback": int((diag["fallback_used"] & pair_ok).sum()),
            "n_raw_valid": int((diag["raw_valid"] & pair_ok).sum()),
            "model_coverage": float(diag.loc[pair_ok, "raw_valid"].mean()) if pair_ok.any() else float("nan"),
            "dm_stat": r_dm.stat, "dm_p": r_dm.pvalue,
            "cw_p": r_cw.pvalue, "gw_p": r_gw.pvalue, "pt_p": r_pt.pvalue,
            "degenerate": bool(r_dm.degenerate),
            "n_origins": int(pair_ok.sum()),
            "sub_periods": sub,
        })

    result = pd.DataFrame(rows)
    for frame in diagnostics.values():
        frame.insert(0, "ts", ts_origin)

    if not dry:
        data_root = registry.gates_path().parent
        fdir = data_root / "forecasts" / gates_key / cell["cell"].replace("|", "_")
        fdir.mkdir(parents=True, exist_ok=True)
        for name, p in preds.items():
            diagnostics[name].to_parquet(
                fdir / f"{name}.parquet"
            )
        cdir = data_root / "cards" / gates_key
        cdir.mkdir(parents=True, exist_ok=True)
        card = {
            "cell": cell["cell"], "tier": tier, "loss": loss_name,
            "inference_policy": "hac-selection-v2",
            "forecast_policy": "declared_baseline_fallback_v1",
            "strong_baseline": base_name,
            "nested_models": dict(cell.get("nested_models", {})),
            "registered_nested_test": cell.get("registered_nested_test"),
            "provenance": provenance,
            "input_series_sha256": input_sha256,
            "model_configs": declared_models,
            "cell_config": dict(cell),
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
                    "input_series_sha256": input_sha256,
                    "model_config": declared_models[r["model"]],
                    "forecast_policy": "declared_baseline_fallback_v1",
                    "inference_policy": "hac-selection-v2",
                    "nested_models": dict(cell.get("nested_models", {})),
                    "registered_nested_test": cell.get("registered_nested_test"),
                    **_inference_metadata(cell, r["model"]),
                },
                (str(ts_origin.min().date()), str(ts_origin.max().date())),
                {
                    "loss_mean": r["loss_mean"], "dm_p": r["dm_p"],
                    "cw_p": r["cw_p"], "pt_p": r["pt_p"],
                },
            )
    if return_diagnostics:
        return result, preds, diagnostics
    if return_forecasts:
        return result, preds
    return result
