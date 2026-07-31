"""Phase-4 zero-shot foundation-model battery (registered: predlab_p4_fm).

Per cell x model: batched zero-shot forecasts on the model's leakage-safe
window; comparison vs the cell's champion and strong baseline by SUBSETTING
their stored forecasts to the identical origins (matched windows, no
recompute). Ledger row per (cell, model).
"""
from __future__ import annotations

import argparse
import fnmatch
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

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))

# (stored-forecast gates key, champion model name) per cell family
CHAMPIONS = {
    ("T1_ret", "1h"): ("predlab_p1_classical", "rw_zero"),
    ("T1_ret", "24h"): ("predlab_p1_classical", "rw_zero"),
    ("T3_rv", "1h"): {"BTCUSDT": ("predlab_p2_ml", "harq"),
                      "ETHUSDT": ("predlab_p2_ml", "gjr11")},
    ("T3_rv", "24h"): {"BTCUSDT": ("predlab_p2_ml", "harq"),
                       "ETHUSDT": ("predlab_p2_ml", "gjr11")},
    ("T4_vol", "1h"): ("predlab_p2_ml", "lgb"),
    ("T4_vol", "24h"): ("predlab_p2_ml", "lgb"),
}


def _series(sym: str, hz: str, tgt: str) -> pd.Series:
    grid = "rv_1h" if hz == "1h" else "rv_1d"
    st = pd.read_parquet(DATA_ROOT / "predlab" / grid / f"{sym}.parquet")
    st = st[st.index <= pd.Timestamp("2025-03-31", tz="UTC")]
    if tgt == "T1_ret":
        return st["ret"].dropna()
    if tgt == "T3_rv":
        return st["rv"].dropna()
    return np.log(st["quote_volume"].replace(0.0, np.nan)).dropna()


def _stored_preds(gates_key: str, cell_id: str, model: str) -> pd.DataFrame:
    p = (DATA_ROOT / "predlab" / "forecasts" / gates_key /
         cell_id.replace("|", "_") / f"{model}.parquet")
    df = pd.read_parquet(p)
    return df.set_index(pd.DatetimeIndex(df["ts"]))


def _loss(tgt: str, y: np.ndarray, pred: np.ndarray, scale: float) -> np.ndarray:
    if tgt == "T3_rv":
        return L.qlike(pred, y)
    if tgt == "T4_vol":
        return L.mase(y, pred, scale)
    return L.se(y, pred)


class ChronosModel:
    name = "chronos_bolt_small"

    def __init__(self):
        import torch
        from chronos import BaseChronosPipeline

        self._torch = torch
        self.pipe = BaseChronosPipeline.from_pretrained(
            "amazon/chronos-bolt-small", device_map="cpu",
            torch_dtype=torch.float32)

    def forecast(self, contexts: "list[np.ndarray]") -> np.ndarray:
        t = self._torch
        out = np.empty(len(contexts))
        B = 64
        for i in range(0, len(contexts), B):
            batch = [t.tensor(c.astype(np.float32)) for c in contexts[i:i + B]]
            q, _ = self.pipe.predict_quantiles(batch, prediction_length=1,
                                               quantile_levels=[0.5])
            out[i:i + len(batch)] = q[:, 0, 0].numpy()
        return out


class TTMModel:
    name = "ttm_r2"

    def __init__(self, context_length: int):
        import torch
        from tsfm_public.toolkit.get_model import get_model

        self._torch = torch
        self.L = context_length
        self.model = get_model("ibm-granite/granite-timeseries-ttm-r2",
                               context_length=context_length, prediction_length=1)
        self.model.eval()

    def forecast(self, contexts: "list[np.ndarray]") -> np.ndarray:
        t = self._torch
        out = np.empty(len(contexts))
        B = 256
        with t.no_grad():
            for i in range(0, len(contexts), B):
                arr = np.stack(contexts[i:i + B]).astype(np.float32)
                # per-series standardization (TTM expects scaled input)
                mu = arr.mean(axis=1, keepdims=True)
                sd = arr.std(axis=1, keepdims=True)
                sd[sd == 0] = 1.0
                x = t.tensor((arr - mu) / sd).unsqueeze(-1)
                pred = self.model(past_values=x).prediction_outputs[:, 0, 0].numpy()
                out[i:i + len(arr)] = pred * sd[:, 0] + mu[:, 0]
        return out


def run(models_sel: "list[str]", pattern: str) -> None:
    entry = registry.get_experiment("predlab_p4_fm")
    proto = entry["protocol"]
    loaded = {}
    for cell_id in entry["cells"]:
        if not fnmatch.fnmatch(cell_id, pattern):
            continue
        sym, hz, tgt = cell_id.split("|")
        y = _series(sym, hz, tgt)
        ctx_len = proto["context_length"][hz]
        step = proto["step"][hz]
        for mname, mcfg in entry["models"].items():
            if mname not in models_sel:
                continue
            lo, hi = mcfg["eval_window"]
            idx_all = np.arange(ctx_len, len(y))
            ts_all = y.index[idx_all]
            in_win = (ts_all >= pd.Timestamp(lo, tz="UTC")) & (ts_all <= pd.Timestamp(hi, tz="UTC"))
            origins = idx_all[in_win][::step]
            if len(origins) < 30:
                print(f"{cell_id} {mname}: <30 origins, skip", flush=True)
                continue
            if mname not in loaded:
                if mname == "chronos_bolt_small":
                    loaded[mname] = ChronosModel()
                elif mname == "ttm_r2":
                    loaded[mname] = {"1h": TTMModel(proto["context_length"]["1h"]),
                                     "24h": TTMModel(proto["context_length"]["24h"])}
                else:
                    print(f"{mname}: not implemented in this runner", flush=True)
                    continue
            model = loaded[mname][hz] if isinstance(loaded[mname], dict) else loaded[mname]
            yv = y.to_numpy()
            contexts = [yv[o - ctx_len:o] for o in origins]
            preds = model.forecast(contexts)
            if tgt == "T3_rv":
                preds = np.maximum(preds, 1e-12)  # variance floor for QLIKE validity
            y_true = yv[origins]
            ts_o = y.index[origins]
            scale = L.mase_scale(yv[:max(origins[0], 400)],
                                 m=(24 if hz == "1h" else 7)) if tgt == "T4_vol" else 1.0
            lf = _loss(tgt, y_true, preds, scale)
            # matched champion + strong baseline from stored forecasts
            champ_spec = CHAMPIONS[(tgt, hz)]
            if isinstance(champ_spec, dict):
                champ_spec = champ_spec[sym]
            gkey, champ_name = champ_spec
            row = {"model": mname, "cell": cell_id, "n": int(len(origins)),
                   "loss": float(np.nanmean(lf))}
            if champ_name == "rw_zero":
                lc = _loss(tgt, y_true, np.zeros_like(y_true), scale)
            else:
                stored = _stored_preds(gkey, cell_id, champ_name)
                sub = stored.reindex(ts_o).dropna()
                keep = np.isin(ts_o, sub.index)
                lf = lf[keep]
                lc = _loss(tgt, sub["y_true"].to_numpy(), sub["pred"].to_numpy(), scale)
            ok = ~(np.isnan(lf) | np.isnan(lc))
            r = dmod.dm_test(lc[ok], lf[ok], h=1)
            imp = 100 * (np.nanmean(lc) - np.nanmean(lf)) / np.nanmean(lc)
            row.update({"champion": champ_name, "champ_loss": float(np.nanmean(lc)),
                        "impr_vs_champ_pct": float(imp), "dm_p": float(r.pvalue)})
            registry.log_trial("predlab_p4_fm", cell_id, mname,
                               {"cell": cell_id, "model": mname, "window": mcfg["eval_window"],
                                "step": step, "ctx": ctx_len},
                               tuple(mcfg["eval_window"]), row)
            print(f"{cell_id} {mname}: loss={row['loss']:.6g} vs {champ_name} "
                  f"{row['champ_loss']:.6g} (impr {imp:+.1f}%) dm_p={r.pvalue:.3g} "
                  f"n={row['n']}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+",
                    default=["chronos_bolt_small", "ttm_r2"])
    ap.add_argument("--cells", default="*")
    args = ap.parse_args()
    run(args.models, args.cells)


if __name__ == "__main__":
    main()
