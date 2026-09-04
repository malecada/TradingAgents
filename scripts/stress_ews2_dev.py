#!/usr/bin/env python
"""stress_ews2: probes P0-P2 then the 9-config dev grid on 2020-08-01..2025-03-31.

  python scripts/stress_ews2_dev.py probes   # P0 funding parity, P1 parent parity, P2 target-regime coverage
  python scripts/stress_ews2_dev.py grid     # refuses unless probes.json passes; 9 ledger rows

Grid, gates, episode and warn rules are transcribed from gates.json["stress_ews2"]
(identical to the parent stress_ews); the only stated change is the funding
source (settlement store, daily mean) and the overlay base (simple returns).
"""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.stress.detection import detection_metrics, placebo_pvalue  # noqa: E402
from tradingagents.stress.episodes import build_episodes  # noqa: E402
from tradingagents.stress.index import build_components, build_components_store, composite_warn  # noqa: E402
from tradingagents.stress.overlay import overlay_metrics  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEV = ("2020-08-01", "2025-03-31")
PARENT_DEV = ("2021-11-01", "2025-03-31")
GRID_SETS = [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]]
GRID_K = [1.0, 1.5, 2.0]
GATE = {"hit_rate_min": 0.5, "false_alarms_per_year_max": 6, "placebo_p_max": 0.05,
        "overlay_delta_maxdd_max": 0.0, "overlay_delta_sr_min": -0.10}
WINDOW = 20
OUT = ROOT / "data/rebuild/stress_ews2"
DERIV = ROOT / "data/derivatives"
FUND = ROOT / "data/xsect/funding"
FNG = ROOT / "data/sentiment/fng/fng.parquet"
COINS, SYMS = ["bitcoin", "ethereum"], ["BTCUSDT", "ETHUSDT"]


def load_ew_close(start: str) -> pd.Series:
    from scripts.factor_baselines import _load_windowed
    logrets = {}
    for coin in COINS:
        df = _load_windowed(coin, start, "2026-07-01")
        idx = pd.to_datetime(df["Date"]).dt.tz_localize("UTC")
        close = pd.Series(df["Close"].to_numpy(), index=idx)
        logrets[coin] = np.log(close).diff()
    combined = pd.concat(logrets, axis=1, join="inner").dropna()
    return np.exp(combined.mean(axis=1).cumsum())


def detectable(episodes: pd.DataFrame, composite: pd.Series) -> tuple[pd.DataFrame, list]:
    """Honest denominator: composite non-NaN on every day of the 20-day pre-window."""
    keep, dropped = [], []
    for _, ep in episodes.iterrows():
        lo, hi = ep["start"] - pd.Timedelta(days=WINDOW), ep["start"] - pd.Timedelta(days=1)
        win = composite.reindex(pd.date_range(lo, hi, freq="D"))
        (keep if win.notna().all() else dropped).append(ep)
    return pd.DataFrame(keep, columns=episodes.columns), [str(e["start"].date()) for e in dropped]


def run_grid_on(comps: pd.DataFrame, close: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp,
                n_placebo: int, simple_overlay: bool, ledger_exp: str | None, window_label) -> dict:
    close_dev = close.loc[lo:hi]
    episodes = build_episodes(close_dev)
    ew_simple = close_dev.pct_change().dropna()
    ew_log = np.log(close_dev / close_dev.shift(1)).dropna()
    results = []
    for cset, k in product(GRID_SETS, GRID_K):
        cw = composite_warn(comps, cset, k).loc[lo:hi]
        eps, dropped = detectable(episodes, cw["composite"])
        det = detection_metrics(cw["warn"], eps, WINDOW)
        plc = placebo_pvalue(cw["warn"], eps, n=n_placebo, seed=0, window=WINDOW)
        ovl = overlay_metrics(ew_simple if simple_overlay else ew_log, cw["warn"])
        ovl_swap = overlay_metrics(ew_log if simple_overlay else ew_simple, cw["warn"])
        # max composite in any pre-window (mechanism diagnostic, as parent 42.5)
        pre_max = []
        for _, ep in eps.iterrows():
            w = cw["composite"].loc[ep["start"] - pd.Timedelta(days=WINDOW): ep["start"] - pd.Timedelta(days=1)]
            pre_max.append(float(w.max()) if len(w) else float("nan"))
        cfg = {"components": cset, "k": k, "hysteresis": 0.25, "cooldown": 5,
               "episode": "-15pct/10d/merge10", "window": WINDOW, "funding_source": "settlement_store_daily_mean"}
        metrics = {**det, "n_episodes_raw": int(len(episodes)), "episodes_dropped_no_history": dropped,
                   "p_hit_rate": plc["p_hit_rate"], "pre_window_composite_max": pre_max,
                   **{f"ovl_{m}": v for m, v in ovl.items()}, **{f"ovlswap_{m}": v for m, v in ovl_swap.items()}}
        if ledger_exp:
            log_trial(ledger_exp, cfg, window_label, {k_: v for k_, v in metrics.items() if not isinstance(v, list)})
        passes = (det["hit_rate"] >= GATE["hit_rate_min"]
                  and det["false_alarm_clusters_per_year"] <= GATE["false_alarms_per_year_max"]
                  and plc["p_hit_rate"] <= GATE["placebo_p_max"]
                  and ovl["delta_maxdd"] <= GATE["overlay_delta_maxdd_max"]
                  and ovl["delta_sr"] >= GATE["overlay_delta_sr_min"])
        results.append({"config": cfg, "metrics": metrics, "gate_pass": bool(passes)})
        print(f"{cset} k={k}: hit={det['hit_rate']:.2f} ({det['n_hits']}/{det['n_episodes']}) p={plc['p_hit_rate']:.3f} "
              f"FA/yr={det['false_alarm_clusters_per_year']:.2f} dMaxDD={ovl['delta_maxdd']:+.3f} dSR={ovl['delta_sr']:+.2f} "
              f"premax={np.nanmax(pre_max) if pre_max else float('nan'):+.2f} pass={passes}", flush=True)
    passing = [r for r in results if r["gate_pass"]]
    selected = (sorted(passing, key=lambda r: (r["metrics"]["p_hit_rate"], r["metrics"]["ovl_delta_maxdd"]))[0]
                if passing else None)
    return {"window": [str(lo.date()), str(hi.date())], "n_episodes_raw": int(len(episodes)),
            "episodes": episodes.assign(start=episodes["start"].astype(str), end=episodes["end"].astype(str)).to_dict("records"),
            "results": results, "selected": selected}


def main_probes() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    comps = build_components_store(COINS, SYMS, DERIV, FUND, FNG)
    # P0 funding parity (EW of the two coins' ma7 vs parent ma7 -- both columns EW-averaged by build)
    both_raw = comps[["funding_rate_ma7_store", "funding_rate_ma7_parent"]].dropna()
    corr_raw = float(both_raw.corr().iloc[0, 1])
    # amendment A1 (2026-09-04, pre-grid): the parent store fills funding_rate_ma7 with 0.0 (not NaN)
    # on its first six days (2021-11-01..06, fewer than 7 observations); parity is computed where the
    # parent's own 7-day window is complete. Raw figure reported alongside.
    parent_first = pd.read_parquet(DERIV / "bitcoin.parquet")["funding_rate"].first_valid_index()
    both = both_raw.loc[both_raw.index >= parent_first + pd.Timedelta(days=6)]
    corr = float(both.corr().iloc[0, 1])
    ratio = float((both["funding_rate_ma7_store"] / both["funding_rate_ma7_parent"]).replace([np.inf, -np.inf], np.nan).median())
    maxdiff = float((both["funding_rate_ma7_store"] - both["funding_rate_ma7_parent"]).abs().max())
    p0 = {"n_overlap_raw": int(len(both_raw)), "corr_raw_incl_parent_zero_fill": corr_raw,
          "n_overlap": int(len(both)), "corr": corr, "median_ratio": ratio, "max_abs_diff": maxdiff,
          "excluded_parent_rows": [str(i.date()) for i in both_raw.index if i < parent_first + pd.Timedelta(days=6)],
          "amendment": "A1: parent ma7 zero-filled on its first six days; parity on complete-window rows",
          "pass": bool(corr >= 0.999 and 0.98 <= ratio <= 1.02)}
    print(f"P0 corr {corr:.6f} (raw {corr_raw:.4f}) ratio {ratio:.4f} maxdiff {maxdiff:.2e} pass={p0['pass']}")
    # P1 parent parity: parent pipeline on parent window, no ledger, 50 placebo draws only for speed of the parity
    plo, phi = pd.Timestamp(PARENT_DEV[0], tz="UTC"), pd.Timestamp(PARENT_DEV[1], tz="UTC")
    parent_comps = build_components(COINS, DERIV, FNG)
    close = load_ew_close("2019-04-14")
    rep = run_grid_on(parent_comps, close, plo, phi, n_placebo=20, simple_overlay=False, ledger_exp=None, window_label=None)
    parent = json.loads((ROOT / "data/rebuild/stress_ews/dev_results.json").read_text())
    same_eps = [e["start"][:10] for e in rep["episodes"]] == [e["start"][:10] for e in parent["episodes"]]
    diffs = []
    for a, b in zip(rep["results"], parent["results"]):
        diffs.append({"config": a["config"]["components"] + [a["config"]["k"]],
                      "hit": (a["metrics"]["hit_rate"], b["metrics"]["hit_rate"]),
                      "fa": (a["metrics"]["false_alarm_clusters_per_year"], b["metrics"]["false_alarm_clusters_per_year"])})
    hit_ok = all(abs(d["hit"][0] - d["hit"][1]) < 1e-12 and abs(d["fa"][0] - d["fa"][1]) < 1e-9 for d in diffs)
    p1 = {"same_episode_catalog": same_eps, "n_episodes": (len(rep["episodes"]), len(parent["episodes"])),
          "hit_fa_identical": hit_ok, "diffs": diffs, "pass": bool(same_eps and hit_ok),
          "note": "P1 reruns the parent pipeline with the parent funding source (build_components) on the parent window; honest-denominator rule applied (parent had no exclusions)"}
    print(f"P1 same_episodes={same_eps} hit/fa identical={hit_ok}")
    # P2 target-regime coverage on the extended window
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    eps = build_episodes(close.loc[lo:hi])
    cw = composite_warn(comps, GRID_SETS[0], 1.0).loc[lo:hi]
    det_eps, dropped = detectable(eps, cw["composite"])
    starts = pd.to_datetime(det_eps["start"]) if len(det_eps) else pd.Series([], dtype="datetime64[ns, UTC]")
    may21 = int(((starts >= "2021-04-01") & (starts <= "2021-06-30")).sum())
    nov21 = int(((starts >= "2021-11-01") & (starts <= "2022-01-31")).sum())
    p2 = {"n_episodes_raw": int(len(eps)), "n_detectable_set0": int(len(det_eps)), "dropped_no_history": dropped,
          "episodes_2021_04_06": may21, "episodes_2021_11_2022_01": nov21,
          "first_composite_date_set0": str(cw["composite"].first_valid_index()),
          "episode_starts": [str(s.date()) for s in starts], "pass": bool(may21 >= 1 and nov21 >= 1)}
    print(f"P2 episodes raw {len(eps)} detectable {len(det_eps)} may21={may21} nov21={nov21} first composite {p2['first_composite_date_set0']} pass={p2['pass']}")
    payload = {"generated_utc": pd.Timestamp.utcnow().isoformat(), "p0": p0, "p1": p1, "p2": p2,
               "stop": not (p0["pass"] and p1["pass"] and p2["pass"])}
    (OUT / "probes.json").write_text(json.dumps(payload, indent=1, default=str))
    print("STOP" if payload["stop"] else "PROBES PASS")


def main_grid() -> None:
    probes = json.loads((OUT / "probes.json").read_text())
    if probes["stop"]:
        raise SystemExit("probes STOP -- refusing to run the grid")
    if (OUT / "dev_results.json").exists():
        raise SystemExit("dev_results.json exists -- one-shot dev grid, no second look")
    comps = build_components_store(COINS, SYMS, DERIV, FUND, FNG)
    close = load_ew_close("2019-04-14")
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    res = run_grid_on(comps, close, lo, hi, n_placebo=500, simple_overlay=True, ledger_exp="stress_ews2", window_label=DEV)
    res["generated_utc"] = pd.Timestamp.utcnow().isoformat()
    (OUT / "dev_results.json").write_text(json.dumps(res, indent=1, default=str))
    print("selected:", json.dumps(res["selected"]["config"]) if res["selected"] else "NONE (all fail gate)")


if __name__ == "__main__":
    {"probes": main_probes, "grid": main_grid}[sys.argv[1]]()
