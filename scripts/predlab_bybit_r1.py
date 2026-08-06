"""predlab_bybit_r1 — champion venue replication on Bybit (pre-registered).

Hypothesis: the frozen Phase-O final champion (gates
predlab_opt.final_champion) transfers to an independent venue's perpetual
universe with NO re-tuning. Configuration is copied verbatim; exactly one
strategy evaluation is authorized (n_trials=1).

Frozen config (chain seq 2): ewma_20 Parkinson low-vol signal (span 20,
lag 1), monthly PIT top-200 universe by prior-month median quote turnover,
eq-weight quintile long-short (gross 2), daily rebalance, 5bp/side +
realized funding, vt15_naive20 overlay (target 0.15, cap 2.0, breadth-100
guard, O4 cost formula).

Window rule (pre-declared): 2021-01-01 -> 2026-07-01; the engine's
MIN_NAMES=25 rule governs early thin days; no post-hoc window or universe
edits.

Sequencing: `register` freezes this file's criteria into gates.json;
`probes` runs DATA-QUALITY probes only (P1 coverage / P2 panel sanity) and
may declare INFEASIBLE without spending the trial; `run` executes the
single authorized strategy evaluation and refuses to run twice.

Verdict criteria (frozen):
  feasibility (P1): >= 1000 trading days with breadth >= 100 signal-bearing
      universe names, else INFEASIBLE (trial unspent).
  PASS iff  ovl net SR >= 0.946  (0.5 x Binance full-window +1.892 — same
      halving convention as the registered forward one-shot)
        AND same sign
        AND circular time-shift placebo p < 0.10 (200 draws, shift >= 30d).
  Anything else: NEGATIVE. Single-name concentration and per-year folds are
  reported as disclosure; they cannot rescue or overturn the verdict
  (stop rule: no post-hoc exclusions — the FTT lesson, THESIS S50).

Survivorship caveat (disclosed at registration): Bybit enumerates only
live contracts; delisted history is recovered by probing all Binance-store
symbol names against Bybit's kline API (FTT/SRM-class recovered,
LUNA-class not servable). Bybit-only delistings are unrecoverable. The P1
probe quantifies recovered-delisted coverage; the caveat is reported with
the verdict either way.
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

from tradingagents.predlab import opt  # noqa: E402
from tradingagents.predlab.pp import (  # noqa: E402
    ANN_DAYS, TAKER_BP, ann_sr, max_drawdown, placebo_pvalue)

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
STORE = DATA_ROOT / "predlab" / "bybit"
GATES = DATA_ROOT / "predlab" / "gates.json"
OUT_PROBES = DATA_ROOT / "predlab" / "bybit_r1_probes.json"
OUT = DATA_ROOT / "predlab" / "bybit_r1_result.json"
FULL = ("2021-01-01", "2026-07-01")
SR_FLOOR = 0.946          # 0.5 x Binance ovl +1.892
PLACEBO_ALPHA = 0.10
PLACEBO_DRAWS = 200
FEAS_MIN_DAYS, FEAS_BREADTH = 1000, 100


def register() -> None:
    gates = json.loads(GATES.read_text())
    if "predlab_bybit_r1" in gates:
        print("predlab_bybit_r1 already frozen — refusing")
        sys.exit(1)
    gates["predlab_bybit_r1"] = {
        "frozen_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "hypothesis": "Phase-O final champion transfers to Bybit verbatim",
        "config": "ewma_20 eq-quintile top-200 monthly-PIT daily + "
                  "vt15_naive20_b100; 5bp + realized funding; NO re-tuning",
        "window": list(FULL),
        "n_trials": 1,
        "feasibility": f">= {FEAS_MIN_DAYS} trading days with breadth >= "
                       f"{FEAS_BREADTH}, else INFEASIBLE (trial unspent)",
        "criteria": {"ovl_sr_floor": SR_FLOOR, "same_sign": True,
                     "placebo_shift_p_lt": PLACEBO_ALPHA,
                     "placebo_draws": PLACEBO_DRAWS},
        "stop_rule": "one run; no post-hoc universe/window edits; "
                     "single-name checks disclosed, never acted on",
        "survivorship_caveat": "Bybit enumerates live contracts only; "
                               "delisted recovered via Binance-name probes "
                               "(partial); Bybit-only delistings missing",
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print("frozen predlab_bybit_r1")


def build_panels() -> dict:
    hi = pd.Timestamp(FULL[1], tz="UTC")
    closes, qvs, parks = {}, {}, {}
    for p in sorted((STORE / "klines").glob("*.parquet")):
        df = pd.read_parquet(p)
        df = df[df.index <= hi]
        if len(df) < 40:
            continue
        closes[p.stem] = df["close"]
        qvs[p.stem] = df["turnover"]
        parks[p.stem] = (np.log(df["high"] / df["low"]) ** 2) / (4 * np.log(2))
    close = pd.DataFrame(closes)
    return {"close": close, "qv": pd.DataFrame(qvs),
            "park": pd.DataFrame(parks)}


def build_funding(index: pd.DatetimeIndex, symbols) -> pd.DataFrame:
    cols = {}
    for sym in symbols:
        p = STORE / "funding" / f"{sym}.parquet"
        if not p.exists():
            continue
        r = pd.read_parquet(p)["fundingRate"].astype(float)
        cols[sym] = r.groupby(r.index.floor("D")).sum()
    return pd.DataFrame(cols).reindex(index)


def probes() -> None:
    gates = json.loads(GATES.read_text())
    if "predlab_bybit_r1" not in gates:
        print("not registered — run `register` first")
        sys.exit(1)
    manifest = json.loads((STORE / "manifest.json").read_text())
    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    sig = opt.build_signal(park, close, "ewma_20")
    uni = opt.monthly_universe(qv, top_n=200)
    breadth = (~sig.where(uni).isna()).sum(axis=1)
    lo = pd.Timestamp(FULL[0], tz="UTC")
    breadth = breadth[(breadth.index >= lo)]
    feas_days = int((breadth >= FEAS_BREADTH).sum())
    recovered = sum(1 for k, v in manifest["symbols"].items()
                    if v.get("status") == "probe-delisted" and v.get("kline_days"))
    ret = np.log(close).diff()
    daily_abs = float(ret.abs().stack().median())
    fund_med = float(build_funding(ret.index, list(close.columns)[:50])
                     .stack().abs().median())
    res = {
        "n_symbols_with_klines": int(close.shape[1]),
        "recovered_delisted": recovered,
        "panel_days": int(len(close)),
        "days_breadth_ge_100": feas_days,
        "breadth_min_median_max": [int(breadth.min()), int(breadth.median()),
                                   int(breadth.max())],
        "median_abs_daily_logret": daily_abs,
        "median_abs_daily_funding": fund_med,
        "feasible": bool(feas_days >= FEAS_MIN_DAYS),
    }
    OUT_PROBES.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print("FEASIBLE — `run` is authorized" if res["feasible"]
          else "INFEASIBLE — trial unspent")


def run() -> None:
    gates = json.loads(GATES.read_text())
    if "predlab_bybit_r1" not in gates:
        print("not registered — refusing")
        sys.exit(1)
    if OUT.exists():
        print(f"result exists ({OUT}) — single-shot spent, refusing")
        sys.exit(1)
    pr = json.loads(OUT_PROBES.read_text())
    if not pr["feasible"]:
        print("probes said INFEASIBLE — refusing")
        sys.exit(1)

    panels = build_panels()
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    ret = np.log(close).diff()
    uni = opt.monthly_universe(qv, top_n=200)
    fund = build_funding(ret.index, sorted(uni.columns[uni.any(axis=0)]))
    sig = opt.build_signal(park, close, "ewma_20")

    raw = opt.run_ls(sig, ret, uni, fund, opt.OptConfig(), *FULL)
    base = raw["rets"]
    breadth = (~sig.where(uni).isna()).sum(axis=1).reindex(base.index)
    net = base["net"]
    sh = net.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    scale = (0.15 / sh).clip(0.0, 2.0).fillna(0.0).where(breadth >= 100, 0.0)
    cost = TAKER_BP / 1e4 * (scale * base["turnover"]
                             + scale.diff().abs().fillna(0.0) * 2.0)
    ovl = scale * net - cost
    ovl_sr = ann_sr(ovl.to_numpy())

    def shifted_sr(shifted_sig) -> float:
        r = opt.run_ls(shifted_sig, ret, uni, fund, opt.OptConfig(), *FULL)
        return r["sr_net"]

    rng = np.random.default_rng(0)
    n = len(sig)
    null = []
    for _ in range(PLACEBO_DRAWS):
        k = int(rng.integers(30, n - 30))
        vals = np.roll(sig.to_numpy(), k, axis=0)
        null.append(shifted_sr(pd.DataFrame(vals, index=sig.index,
                                            columns=sig.columns)))
    p_shift = placebo_pvalue(raw["sr_net"], null)

    pnl = raw["name_pnl"].abs()
    yearly = {}
    for y in sorted(set(ovl.index.year)):
        seg = ovl[(ovl.index.year == y)].dropna()
        if len(seg) >= 30:
            yearly[str(y)] = {"sr": ann_sr(seg.to_numpy()),
                              "maxdd": max_drawdown(seg.to_numpy())}

    verdict = bool(ovl_sr >= SR_FLOOR and ovl_sr > 0
                   and p_shift < PLACEBO_ALPHA)
    res = {
        "raw_sr": raw["sr_net"], "raw_maxdd": raw["maxdd"],
        "ovl_sr": ovl_sr,
        "ovl_maxdd": max_drawdown(ovl.dropna().to_numpy()),
        "avg_scale": float(scale.mean()),
        "avg_turnover": raw["avg_turnover"], "n_days": raw["n_days"],
        "placebo_p_shift": p_shift, "placebo_draws": PLACEBO_DRAWS,
        "yearly_ovl": yearly,
        "max_name_share": float(pnl.max() / pnl.sum()) if pnl.sum() > 0 else 0,
        "max_name": str(pnl.idxmax()) if pnl.sum() > 0 else "",
        "criteria": {"floor": SR_FLOOR, "alpha": PLACEBO_ALPHA},
        "verdict": "PASS" if verdict else "NEGATIVE",
    }
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "yearly_ovl"},
                     indent=1, default=float))
    print(f"\nVERDICT: {res['verdict']}")


if __name__ == "__main__":
    {"register": register, "probes": probes, "run": run}[sys.argv[1]]()
