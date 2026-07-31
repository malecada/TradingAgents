"""P5-02: sealed-holdout one-shots for the frozen champions (predlab_p5).

ONE evaluation per cell, verdicts recorded PASS or FAIL, no re-tuning, no
second look. The spend rule is enforced in code: if the verdicts file exists,
this script refuses to run. Criteria (registered): DM p<0.05 vs the cell's
strong baseline recomputed causally on holdout AND effect >= 0.5 x dev effect
AND same sign; T2 additionally accuracy edge >= 1.0pp; T7: |IC| >= 0.02 with
NW-t >= 2 (dev sign).

Champion configs are the EXACT dev-battery configs (verified against
predlab_run_battery.py + registered protocols before the spend). Dev effects
come from the frozen p5_champions.json losses (the MCS common-origin frame).
Feature frames for T4 are rebuilt here without the battery's MAX_LOAD_END
dev clip (loaders clip at holdout end instead).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import baselines, har, registry, runner, tier1, tier2, xsec  # noqa: E402
from tradingagents.predlab import features as F  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
VERDICTS = DATA_ROOT / "predlab" / "p5_holdout_verdicts.json"
HOLDOUT = ("2025-04-01", "2026-07-01")
RUN_KEY = "predlab_p5_holdout"  # forecasts/cards/ledger namespace for the spend


def _store(sym: str, hz: str) -> pd.DataFrame:
    grid = "rv_1h" if hz == "1h" else "rv_1d"
    st = pd.read_parquet(DATA_ROOT / "predlab" / grid / f"{sym}.parquet")
    return st[st.index <= pd.Timestamp(HOLDOUT[1], tz="UTC")]


def _t4_series(sym: str, hz: str, entry_ml: dict) -> "tuple[pd.DataFrame, list]":
    """Replicates the battery's Tier-2 T4 frame WITHOUT the dev-end clip."""
    from predlab_run_battery import _resolve_names

    store = _store(sym, hz)
    base = F.build_features(store, grid=hz)
    oi5 = pd.read_parquet(DATA_ROOT / "predlab" / "oi_5m" / f"{sym}.parquet")
    oi = F.oi_features(oi5, grid=hz)
    rate = pd.read_parquet(DATA_ROOT / "predlab" / "funding" / f"{sym}.parquet")["fundingRate"]
    fund = F.funding_features(rate, base.index)
    feats = base.join(oi, how="left").join(fund, how="left")
    cols = _resolve_names(entry_ml["feature_sets"]["T4_vol"], hz)
    missing = [c for c in cols if c not in feats.columns]
    assert not missing, missing
    y = np.log(store["quote_volume"].replace(0.0, np.nan))
    series = feats[cols].copy()
    series.insert(0, "y", y)
    return series.dropna(subset=["y"]), cols


def _cell_run(cell_id: str, champ_name: str, loss_name: str) -> dict:
    sym, hz, tgt = cell_id.split("|")
    st = _store(sym, hz)
    entry_ml = registry.get_experiment("predlab_p2_ml")
    mase_m = 1
    if tgt == "T3_rv":
        series = pd.DataFrame({"y": st["rv"], "ret": st["ret"],
                               "rq_lag": st["rq"].shift(1)}).dropna(subset=["y", "ret"])
        hl = (1, 24, 168) if hz == "1h" else (1, 5, 22)
        base = har.HarForecaster("har_levels", lags=hl, refit_every=1)
        if champ_name == "harq":
            champ = har.HarForecaster("harq", rq_col=1, lags=hl, refit_every=1)
        else:  # egarch11, dev tier-1 1h config
            champ = tier1.GarchForecaster("egarch11", ret_col=0,
                                          refit_every=24 if hz == "1h" else 5,
                                          window_cap=4320 if hz == "1h" else None)
        cell_refit = 24 if hz == "1h" else 5
    elif tgt == "T4_vol":
        series, cols = _t4_series(sym, hz, entry_ml)
        m = 24 if hz == "1h" else 7
        mase_m = m
        base = baselines.SeasonalNaive(m=m)
        cell_refit = int(entry_ml["protocol"]["refit_every"][hz])
        champ = tier2.LGBForecaster(refit_every=cell_refit, n_features=len(cols))
    else:  # T2_dir — dev config: LogitLags() defaults (n_lags 5, refit 5)
        series = st["ret"].to_frame("y").dropna()
        base = baselines.BaseRate()
        champ = tier1.LogitLags()
        cell_refit = 24
    min_train = 2160 if hz == "1h" else 365
    cell = {"cell": cell_id, "target": tgt, "horizon_bars": 1,
            "strong_baseline": base.name, "loss": loss_name, "mase_m": mase_m,
            "min_train": min_train, "step": 1, "refit_every": cell_refit,
            "embargo": 0, "eval_start": HOLDOUT[0], "allow_holdout": True}
    out = runner.run_cell(cell, series, [base, champ], gates_key=RUN_KEY,
                          tier="holdout", dry=False)
    r = out[out.model == champ.name].iloc[0]
    rb = out[out.model == base.name].iloc[0]
    res = {"champ_loss": float(r["loss_mean"]), "base_loss": float(rb["loss_mean"]),
           "dm_p": float(r["dm_p"]), "cw_p": float(r["cw_p"]),
           "n": int(r["n_origins"]),
           "effect_pct": float(100 * (rb["loss_mean"] - r["loss_mean"])
                               / rb["loss_mean"])}
    if tgt == "T2_dir":
        fdir = DATA_ROOT / "predlab" / "forecasts" / RUN_KEY / cell_id.replace("|", "_")
        fc = pd.read_parquet(fdir / f"{champ.name}.parquet")
        y_up = fc["y_true"].to_numpy() > 0
        acc = float(((fc["pred"].to_numpy() > 0.5) == y_up).mean())
        base_rate = float(max(y_up.mean(), 1 - y_up.mean()))
        res["acc"] = acc
        res["holdout_base_rate"] = base_rate
        res["edge_pp"] = 100 * (acc - base_rate)
    return res


def run_t7(dev_ic: float) -> dict:
    from predlab_t7 import build_panels, monthly_universe

    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    lo = pd.Timestamp(HOLDOUT[0], tz="UTC")
    hi = pd.Timestamp(HOLDOUT[1], tz="UTC")
    close = close[close.index <= hi]
    qv, park = qv.loc[close.index], park.loc[close.index]
    ret = np.log(close).diff()
    uni = monthly_universe(qv, top_n=200)
    sig = park.rolling(5).mean().shift(1)
    y = ret[ret.index >= lo].where(uni)
    s = sig[sig.index >= lo].where(uni)
    ics = xsec.daily_ic(s, y, min_breadth=50)
    summ = xsec.ic_summary(ics, nw_lag=5)
    summ["dev_ic"] = dev_ic
    return summ


def main() -> None:
    if VERDICTS.exists():
        print(f"HOLDOUT ALREADY SPENT — refusing to run again ({VERDICTS})")
        sys.exit(1)
    champs = json.loads((DATA_ROOT / "predlab" / "p5_champions.json").read_text())
    verdicts = {}
    for cell_id, info in champs.items():
        if cell_id.startswith("T7"):
            dev_ic = info["ics"]["park_5"]
            s = run_t7(dev_ic)
            passed = (abs(s["mean_ic"]) >= 0.02 and abs(s["nw_t"]) >= 2
                      and np.sign(s["mean_ic"]) == np.sign(dev_ic))
            verdicts[cell_id] = {"champion": "park_5", **s,
                                 "criteria": "|IC|>=0.02 & |NW-t|>=2 & dev sign",
                                 "verdict": "PASS" if passed else "FAIL"}
            registry.log_trial("predlab_p5", cell_id, "park_5",
                               {"cell": cell_id, "champion": "park_5",
                                "phase": "holdout_oneshot"},
                               HOLDOUT, verdicts[cell_id])
            print(f"{cell_id}: IC={s['mean_ic']:+.4f} t={s['nw_t']:+.2f} "
                  f"n={s['n_days']} -> {verdicts[cell_id]['verdict']}", flush=True)
            continue
        champ = info["champion"]
        loss_name = {"T3": "qlike", "T4": "mase", "T2": "brier"}[cell_id.split("|")[2][:2]]
        dev_eff = float(100 * (info["baseline_loss"] - info["dev_loss"])
                        / info["baseline_loss"])
        res = _cell_run(cell_id, champ, loss_name)
        crit = (res["dm_p"] < 0.05 and res["effect_pct"] > 0
                and res["effect_pct"] >= 0.5 * dev_eff)
        if "edge_pp" in res:
            crit = crit and res["edge_pp"] >= 1.0
        verdicts[cell_id] = {"champion": champ, "dev_effect_pct": dev_eff,
                             **res, "verdict": "PASS" if crit else "FAIL"}
        registry.log_trial("predlab_p5", cell_id, champ,
                           {"cell": cell_id, "champion": champ,
                            "phase": "holdout_oneshot"},
                           HOLDOUT, verdicts[cell_id])
        print(f"{cell_id} [{champ}]: holdout eff {res['effect_pct']:+.1f}% "
              f"(dev {dev_eff:+.1f}%, need >={0.5*dev_eff:.1f}%) dm_p={res['dm_p']:.3g}"
              + (f" edge={res['edge_pp']:.2f}pp" if "edge_pp" in res else "")
              + f" n={res['n']} -> {verdicts[cell_id]['verdict']}", flush=True)
    VERDICTS.write_text(json.dumps(verdicts, indent=1, default=float))
    n_pass = sum(1 for v in verdicts.values() if v["verdict"] == "PASS")
    print(f"\nHOLDOUT SPENT: {n_pass}/{len(verdicts)} PASS -> {VERDICTS}", flush=True)


if __name__ == "__main__":
    main()
