#!/usr/bin/env python
"""Dev-window evaluation of the 9 pre-registered stress-EWS configs. Ledger: stress_ews.

Grid, gate thresholds, episode rule and warn rule are frozen in
docs/superpowers/specs/2026-07-14-stress-ews-prereg.md /
data/rebuild/gates.json["stress_ews"] — this script transcribes them, it does
not tune them.

Overlay is tested against (a) EW BTC+ETH buy-and-hold returns (mandatory) and
(b) the frozen factor-sleeve return series in data/rebuild/holdout/, if that
series actually covers the dev window. It does not (holdout/ only holds the
2025-04-02..2026-06-30 locked-holdout returns, disjoint from the
2021-11-01..2025-03-31 dev window evaluated here) — so overlay metrics are
reported against EW B&H only, and this is recorded in the output.
"""
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.rebuild.ledger import log_trial
from tradingagents.stress.detection import detection_metrics, placebo_pvalue
from tradingagents.stress.episodes import build_episodes
from tradingagents.stress.index import build_components, composite_warn
from tradingagents.stress.overlay import overlay_metrics

DEV = ("2021-11-01", "2025-03-31")
GRID_SETS = [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]]
GRID_K = [1.0, 1.5, 2.0]
GATE = {"hit_rate_min": 0.5, "false_alarms_per_year_max": 6,
        "placebo_p_max": 0.05, "overlay_delta_maxdd_max": 0.0, "overlay_delta_sr_min": -0.10}
OUT = Path("data/rebuild/stress_ews")
FACTOR_HOLDOUT_RETURNS = Path("data/rebuild/holdout/portfolio_daily_returns.csv")


def load_ew_close() -> pd.Series:
    """Synthetic EW BTC+ETH close path, built from causal log-returns.

    Reuses the rebuild's windowed OHLCV loader (`scripts.factor_baselines
    ._load_windowed`, the loader the factor-sleeve holdout used) rather than
    re-implementing a fetcher. Per coin: log(Close).diff(); the two log-return
    series are aligned on their common dates (inner join) and equal-weighted;
    the EW price path is reconstructed as exp(cumsum) so `build_episodes` can
    run its 10-day-forward-return rule directly on it.
    """
    from scripts.factor_baselines import _load_windowed

    logrets = {}
    for coin in ["bitcoin", "ethereum"]:
        df = _load_windowed(coin, "2021-11-01", "2026-07-01")
        idx = pd.to_datetime(df["Date"]).dt.tz_localize("UTC")
        close = pd.Series(df["Close"].to_numpy(), index=idx)
        logrets[coin] = np.log(close).diff()
    combined = pd.concat(logrets, axis=1, join="inner").dropna()
    ew_logret = combined.mean(axis=1)
    return np.exp(ew_logret.cumsum())


def load_factor_sleeve_dev_returns(lo: pd.Timestamp, hi: pd.Timestamp):
    """Return (series, note) — the frozen factor-sleeve daily return series if
    it actually covers the dev window; else (None, note-of-why-not)."""
    if not FACTOR_HOLDOUT_RETURNS.exists():
        return None, f"{FACTOR_HOLDOUT_RETURNS} not found"
    df = pd.read_csv(FACTOR_HOLDOUT_RETURNS)
    idx = pd.to_datetime(df["date"], utc=True)
    s = pd.Series(df["portfolio"].to_numpy(), index=idx)
    s_dev = s.loc[lo:hi]
    if s_dev.empty:
        return None, (f"{FACTOR_HOLDOUT_RETURNS} covers "
                       f"[{s.index.min().date()}, {s.index.max().date()}], disjoint from dev "
                       f"window [{lo.date()}, {hi.date()}] (it is the locked-holdout series) "
                       f"-- overlay computed against EW B&H only")
    return s_dev, f"{FACTOR_HOLDOUT_RETURNS} covers dev window"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    comps = build_components(["bitcoin", "ethereum"],
                             Path("data/derivatives"), Path("data/sentiment/fng/fng.parquet"))
    close = load_ew_close()
    close_dev = close.loc[lo:hi]
    episodes = build_episodes(close_dev)
    ew_ret = np.log(close_dev / close_dev.shift(1)).dropna()

    factor_ret, factor_note = load_factor_sleeve_dev_returns(lo, hi)
    print(f"factor sleeve dev series: {factor_note}")

    results = []
    for cset, k in product(GRID_SETS, GRID_K):
        cw = composite_warn(comps, cset, k).loc[lo:hi]
        det = detection_metrics(cw["warn"], episodes)
        plc = placebo_pvalue(cw["warn"], episodes, n=500, seed=0)
        ovl = overlay_metrics(ew_ret, cw["warn"])
        cfg = {"components": cset, "k": k, "hysteresis": 0.25, "cooldown": 5,
               "episode": "-15pct/10d/merge10", "window": 20}
        metrics = {**det, "p_hit_rate": plc["p_hit_rate"],
                   **{f"ovl_{m}": v for m, v in ovl.items()}}
        if factor_ret is not None:
            ovl_factor = overlay_metrics(factor_ret, cw["warn"])
            metrics.update({f"ovl_factor_{m}": v for m, v in ovl_factor.items()})
        log_trial("stress_ews", cfg, DEV, metrics)
        passes = (det["hit_rate"] >= GATE["hit_rate_min"]
                  and det["false_alarm_clusters_per_year"] <= GATE["false_alarms_per_year_max"]
                  and plc["p_hit_rate"] <= GATE["placebo_p_max"]
                  and ovl["delta_maxdd"] <= GATE["overlay_delta_maxdd_max"]
                  and ovl["delta_sr"] >= GATE["overlay_delta_sr_min"])
        results.append({"config": cfg, "metrics": metrics, "gate_pass": bool(passes)})
        print(f"{cset} k={k}: hit={det['hit_rate']:.2f} p={plc['p_hit_rate']:.3f} "
              f"FA/yr={det['false_alarm_clusters_per_year']:.1f} "
              f"dMaxDD={ovl['delta_maxdd']:+.3f} dSR={ovl['delta_sr']:+.2f} pass={passes}")

    passing = [r for r in results if r["gate_pass"]]
    selected = (sorted(passing, key=lambda r: (r["metrics"]["p_hit_rate"],
                                               r["metrics"]["ovl_delta_maxdd"]))[0]
                if passing else None)
    json.dump({"n_episodes_dev": len(episodes),
               "episodes": episodes.assign(start=episodes["start"].astype(str),
                                           end=episodes["end"].astype(str)).to_dict("records") if len(episodes) else [],
               "overlay_factor_sleeve_note": factor_note,
               "results": results, "selected": selected},
              open(OUT / "dev_results.json", "w"), indent=1, default=str)
    print("selected:", json.dumps(selected["config"]) if selected else "NONE (all fail gate)")


if __name__ == "__main__":
    main()
