"""Run a registered Phase-1 battery tier over cells.

Usage:
  python scripts/predlab_run_battery.py --tier t0 --cells all
  python scripts/predlab_run_battery.py --tier t0 --cells 'BTCUSDT|24h*'

Loads each cell's series from the predlab stores (clipped at MAX_LOAD_END —
the sealed holdout is never read), builds the tier's model set, and delegates
to runner.run_cell (cards + forecasts + ledger rows).

Series convention (matches the stores' labeling): row ts = period START t,
y[t] realized over (t, t+h] — rv/ret/volume rows already carry it; funding is
re-labeled accordingly (8h: next print; 24h: UTC-day sum).

Tier-0 comparison base per cell (baselines are the null; the REGISTERED
strong baseline arrives with its tier): T1 rw_zero, T2 base_rate,
T3 ewma_0.94, T4 seasonal_naive, T6 persistence.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import baselines, registry, runner  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
FUND_DIR = DATA_ROOT / "predlab" / "funding"  # copied from the 799-sym xsect store

SEASONAL_M = {"1h": 24, "24h": 7, "7d": 1}
HORIZON_BARS = {"1h": 1, "24h": 1, "7d": 7, "8h": 1}


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.index <= pd.Timestamp(registry.MAX_LOAD_END, tz="UTC")]


def _rv_store(symbol: str, horizon: str) -> pd.DataFrame:
    sub = "rv_1h" if horizon == "1h" else "rv_1d"
    return _clip(pd.read_parquet(DATA_ROOT / "predlab" / sub / f"{symbol}.parquet"))


def _season_bin(idx: pd.DatetimeIndex, horizon: str) -> np.ndarray:
    if horizon == "1h":
        return idx.hour.to_numpy(dtype=float)
    return idx.dayofweek.to_numpy(dtype=float)


def _agg7(s: pd.Series) -> pd.Series:
    # y7[t] = value over (t, t+7d] on the daily grid (overlapping, step 1)
    return s.rolling(7).sum().shift(-6)


def load_series(symbol: str, horizon: str, target: str) -> pd.DataFrame:
    if target == "T6_funding":
        raw = pd.read_parquet(FUND_DIR / f"{symbol}.parquet")
        rate = raw["fundingRate"].astype(float).sort_index()  # DatetimeIndex fundingTime (UTC)
        if horizon == "8h":
            y = rate.shift(-1)  # target = next print, realized (t, t+8h]
        else:  # 24h: UTC-day sum, row = day start, realized at day end
            y = rate.groupby(rate.index.floor("D")).sum()
        y = _clip(y.to_frame("y")).dropna()
        return y

    store = _rv_store(symbol, horizon)
    if target in ("T1_ret", "T2_dir"):
        base = store["ret"]
    elif target == "T3_rv":
        base = store["rv"]
    elif target == "T4_vol":
        base = np.log(store["quote_volume"].replace(0.0, np.nan))
    else:
        raise ValueError(target)

    if horizon == "7d":
        base = _agg7(base)
    df = base.to_frame("y").dropna()
    df["bin"] = _season_bin(df.index, horizon)
    return df


def tier0_models(target: str, horizon: str) -> "tuple[list, str]":
    m = SEASONAL_M[horizon] if horizon in SEASONAL_M else 1
    if target == "T1_ret":
        return [baselines.RWZero(), baselines.HistMean(), baselines.Persistence()], "rw_zero"
    if target == "T2_dir":
        return [baselines.BaseRate()], "base_rate"
    if target == "T3_rv":
        return [baselines.EWMA(lam=0.94), baselines.Persistence(), baselines.HistMean()], "ewma_0.94"
    if target == "T4_vol":
        sn = baselines.SeasonalNaive(m=m)
        return [sn, baselines.Persistence(), baselines.HistMean(),
                baselines.Climatology(bin_col=0)], sn.name
    if target == "T6_funding":
        return [baselines.Persistence(), baselines.HistMean()], "persistence"
    raise ValueError(target)


def run_tier0(gates_key: str, pattern: str) -> None:
    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    cells = [c for c in entry["cells"] if fnmatch.fnmatch(c["cell"], pattern)]
    print(f"tier t0: {len(cells)} cells matching {pattern!r}")
    for c in cells:
        sym, hz, tgt = c["symbol"], c["horizon"], c["target"]
        series = load_series(sym, hz, tgt)
        models, base = tier0_models(tgt, hz)
        loss = proto["loss"][tgt.split("_")[0]]
        cell = {
            "cell": c["cell"],
            "target": tgt,
            "horizon_bars": HORIZON_BARS[hz],
            "strong_baseline": base,
            "loss": loss,
            "min_train": proto["min_train"].get(hz, 365),
            "step": 1,
            "refit_every": 1,
            "embargo": 0,
            "mase_m": SEASONAL_M.get(hz, 1),
            "eval_start": entry["dev_window"][0],  # earlier bars = burn-in only
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t0")
        best = out.sort_values("loss_mean").iloc[0]
        print(f"  {c['cell']}: n={int(out['n_origins'].max())} base={base} "
              f"best={best['model']} loss={best['loss_mean']:.6g}")


def run_tier1_t1t2_24h(gates_key: str) -> None:
    from tradingagents.predlab import tier1

    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    refit = proto["refit_every"]["arima_ets_garch"]["24h"]
    cells = [c for c in entry["cells"]
             if c["horizon"] == "24h" and c["target"] in ("T1_ret", "T2_dir")]
    print(f"tier t1_t1t2_24h: {len(cells)} cells, refit_every={refit}")
    for c in cells:
        series = load_series(c["symbol"], c["horizon"], c["target"])
        if c["target"] == "T1_ret":
            models = [baselines.RWZero(), tier1.ArimaForecaster(),
                      tier1.EtsForecaster("ANN"), tier1.EtsForecaster("AAN")]
        else:
            models = [baselines.BaseRate(), tier1.LogitLags()]
        cell = {
            "cell": c["cell"], "target": c["target"], "horizon_bars": 1,
            "strong_baseline": c["strong_baseline"],
            "loss": proto["loss"][c["target"].split("_")[0]],
            "min_train": proto["min_train"]["24h"], "step": 1,
            "refit_every": refit, "embargo": 0,
            "eval_start": entry["dev_window"][0],
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t1")
        for _, r in out.iterrows():
            print(f"  {c['cell']} {r['model']}: loss={r['loss_mean']:.6g} "
                  f"dm_p={r['dm_p']:.4g} cw_p={r['cw_p']:.4g} pt_p={r['pt_p']:.4g}")


def run_tier1_t3_24h(gates_key: str) -> None:
    from tradingagents.predlab import har, tier1

    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    refit = proto["refit_every"]["arima_ets_garch"]["24h"]
    cells = [c for c in entry["cells"] if c["horizon"] == "24h" and c["target"] == "T3_rv"]
    print(f"tier t1_t3_24h: {len(cells)} cells, refit_every(garch)={refit}")
    for c in cells:
        store = _rv_store(c["symbol"], "24h")
        series = pd.DataFrame({
            "y": store["rv"],           # target: variance of period (t, t+1d]
            "ret": store["ret"],        # period-labeled: GARCH conditioning series
            "rq_lag": store["rq"].shift(1),  # pre-lagged quarticity for HARQ
        }).dropna(subset=["y", "ret"])
        models = [
            baselines.EWMA(lam=0.94),                        # weak ref (reported)
            har.HarForecaster("har_levels"),                 # registered strong baseline
            har.HarForecaster("log_har"),
            har.HarForecaster("harq", rq_col=1),
            tier1.GarchForecaster("garch11", ret_col=0, refit_every=refit),
            tier1.GarchForecaster("egarch11", ret_col=0, refit_every=refit),
            tier1.GarchForecaster("gjr11", ret_col=0, refit_every=refit),
        ]
        cell = {
            "cell": c["cell"], "target": "T3_rv", "horizon_bars": 1,
            "strong_baseline": "har_levels", "loss": "qlike",
            "min_train": proto["min_train"]["24h"], "step": 1,
            "refit_every": refit, "embargo": 0,
            "eval_start": entry["dev_window"][0],
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t1")
        for _, r in out.iterrows():
            print(f"  {c['cell']} {r['model']}: qlike={r['loss_mean']:.6g} "
                  f"dm_p={r['dm_p']:.4g} gw_p={r['gw_p']:.4g}")


def run_tier1_t4t6(gates_key: str) -> None:
    from tradingagents.predlab import tier1

    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    cells = [c for c in entry["cells"]
             if (c["target"] == "T4_vol" and c["horizon"] == "24h")
             or c["target"] == "T6_funding"]
    print(f"tier t1_t4t6: {len(cells)} cells")
    for c in cells:
        series = load_series(c["symbol"], c["horizon"], c["target"])
        if c["target"] == "T4_vol":
            m = SEASONAL_M[c["horizon"]]
            models = [baselines.SeasonalNaive(m=m), baselines.Persistence(),
                      tier1.SeasonalAR(m=m)]
            base = f"seasonal_naive_m{m}"
            loss, mase_m = "mase", m
        else:
            models = [baselines.Persistence(), tier1.Ar1(), tier1.Dar1()]
            base = "ar1"  # registered strong baseline (Tier-1 asks: does richer beat AR1?)
            loss, mase_m = "se", 1
        cell = {
            "cell": c["cell"], "target": c["target"], "horizon_bars": 1,
            "strong_baseline": base, "loss": loss, "mase_m": mase_m,
            "min_train": proto["min_train"].get(c["horizon"], 365), "step": 1,
            "refit_every": 1, "embargo": 0,
            "eval_start": entry["dev_window"][0],
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t1")
        for _, r in out.iterrows():
            print(f"  {c['cell']} {r['model']}: loss={r['loss_mean']:.6g} "
                  f"dm_p={r['dm_p']:.4g} cw_p={r['cw_p']:.4g}")


CAP_1H = 4320  # declared amendment: arima/ets/garch conditioning cap at 1h


def run_tier1_1h(gates_key: str) -> None:
    from tradingagents.predlab import har, tier1

    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    refit = proto["refit_every"]["arima_ets_garch"]["1h"]
    cells = [c for c in entry["cells"] if c["horizon"] == "1h"]
    print(f"tier t1_1h: {len(cells)} cells, refit(arima/ets/garch)={refit}, cap={CAP_1H}")
    for c in cells:
        sym, tgt = c["symbol"], c["target"]
        store = _rv_store(sym, "1h")
        if tgt in ("T1_ret", "T2_dir"):
            series = store["ret"].to_frame("y").dropna()
            if tgt == "T1_ret":
                models = [baselines.RWZero(),
                          tier1.ArimaForecaster(refit_every=refit, window_cap=CAP_1H,
                                                select_once=True,
                                                use_extend_cache=True),
                          tier1.EtsForecaster("ANN", window_cap=CAP_1H),
                          tier1.EtsForecaster("AAN", window_cap=CAP_1H)]
            else:
                models = [baselines.BaseRate(), tier1.LogitLags()]
            refit_cell = refit if tgt == "T1_ret" else 24
        elif tgt == "T3_rv":
            series = pd.DataFrame({
                "y": store["rv"], "ret": store["ret"], "rq_lag": store["rq"].shift(1),
            }).dropna(subset=["y", "ret"])
            hl = (1, 24, 168)
            models = [baselines.EWMA(lam=0.94),
                      har.HarForecaster("har_levels", lags=hl),
                      har.HarForecaster("log_har", lags=hl),
                      har.HarForecaster("harq", rq_col=1, lags=hl),
                      tier1.GarchForecaster("garch11", ret_col=0, refit_every=refit,
                                            window_cap=CAP_1H),
                      tier1.GarchForecaster("egarch11", ret_col=0, refit_every=refit,
                                            window_cap=CAP_1H),
                      tier1.GarchForecaster("gjr11", ret_col=0, refit_every=refit,
                                            window_cap=CAP_1H)]
            refit_cell = refit
        else:  # T4_vol
            series = np.log(store["quote_volume"].replace(0.0, np.nan)).to_frame("y").dropna()
            models = [baselines.SeasonalNaive(m=24), baselines.Persistence(),
                      tier1.SeasonalAR(m=24)]
            refit_cell = 24
        cell = {
            "cell": c["cell"], "target": tgt, "horizon_bars": 1,
            "strong_baseline": c["strong_baseline"] if tgt not in ("T3_rv", "T4_vol")
            else ("har_levels" if tgt == "T3_rv" else "seasonal_naive_m24"),
            "loss": proto["loss"][tgt.split("_")[0]],
            "min_train": proto["min_train"]["1h"], "step": 1,
            "refit_every": refit_cell, "embargo": 0, "mase_m": 24,
            "eval_start": entry["dev_window"][0],
        }
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t1")
        for _, r in out.iterrows():
            print(f"  {c['cell']} {r['model']}: loss={r['loss_mean']:.6g} "
                  f"dm_p={r['dm_p']:.4g}", flush=True)


def run_tier1_7d(gates_key: str) -> None:
    from tradingagents.predlab import har, tier1

    entry = registry.get_experiment(gates_key)
    proto = entry["protocol"]
    cells = [c for c in entry["cells"] if c["horizon"] == "7d"]
    print(f"tier t1_7d: {len(cells)} cells (direct aggregation)")
    for c in cells:
        sym, tgt = c["symbol"], c["target"]
        store = _rv_store(sym, "24h")
        if tgt in ("T1_ret", "T2_dir"):
            series = _agg7(store["ret"]).to_frame("y").dropna()
            models = ([baselines.RWZero(),
                       tier1.ArimaForecaster(refit_every=5, select_once=True),
                       tier1.EtsForecaster("ANN"), tier1.EtsForecaster("AAN")]
                      if tgt == "T1_ret" else
                      [baselines.BaseRate(), tier1.LogitLags()])
        elif tgt == "T3_rv":
            series = pd.DataFrame({
                "y": _agg7(store["rv"]), "ret": store["ret"],
                "rq_lag": store["rq"].shift(1),
            }).dropna(subset=["y", "ret"])
            models = [baselines.EWMA(lam=0.94),
                      har.HarForecaster("har_levels"), har.HarForecaster("log_har"),
                      har.HarForecaster("harq", rq_col=1),
                      tier1.GarchForecaster("garch11", ret_col=0, horizon=7, refit_every=5)]
        else:  # T4_vol: log of 7-day dollar-volume sum
            qv7 = store["quote_volume"].rolling(7).sum().shift(-6)
            series = np.log(qv7.replace(0.0, np.nan)).to_frame("y").dropna()
            models = [baselines.SeasonalNaive(m=1), baselines.Persistence(),
                      baselines.HistMean(), tier1.SeasonalAR(m=1)]
        cell = {
            "cell": c["cell"], "target": tgt, "horizon_bars": 7,
            "strong_baseline": c["strong_baseline"] if tgt not in ("T3_rv",)
            else "har_levels",
            "loss": proto["loss"][tgt.split("_")[0]],
            "min_train": proto["min_train"]["7d"], "step": 1,
            "refit_every": 5, "embargo": 0, "mase_m": 1,
            "eval_start": entry["dev_window"][0],
        }
        if tgt == "T4_vol":
            cell["strong_baseline"] = "seasonal_naive_m1"
        out = runner.run_cell(cell, series, models, gates_key=gates_key, tier="t1")
        for _, r in out.iterrows():
            print(f"  {c['cell']} {r['model']}: loss={r['loss_mean']:.6g} "
                  f"dm_p={r['dm_p']:.4g}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates-key", default="predlab_p1_classical")
    ap.add_argument("--tier", required=True,
                    choices=["t0", "t1_t1t2_24h", "t1_t3_24h", "t1_t4t6",
                             "t1_1h", "t1_7d"])
    ap.add_argument("--cells", default="all")
    args = ap.parse_args()
    pattern = "*" if args.cells == "all" else args.cells
    if args.tier == "t0":
        run_tier0(args.gates_key, pattern)
    elif args.tier == "t1_t1t2_24h":
        run_tier1_t1t2_24h(args.gates_key)
    elif args.tier == "t1_t3_24h":
        run_tier1_t3_24h(args.gates_key)
    elif args.tier == "t1_t4t6":
        run_tier1_t4t6(args.gates_key)
    elif args.tier == "t1_1h":
        run_tier1_1h(args.gates_key)
    elif args.tier == "t1_7d":
        run_tier1_7d(args.gates_key)


if __name__ == "__main__":
    main()
