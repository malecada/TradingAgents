"""T7 cross-sectional IC battery (registered: predlab_p2_t7).

Raw-signal ICs over the monthly PIT top-200 universe. Panels cached
canonically at data/predlab/t7_panel.parquet (rebuild with --rebuild).
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

from tradingagents.predlab import registry, xsec  # noqa: E402
from tradingagents.predlab.meanstats import nw_tstat  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
KLINES = DATA_ROOT / "xsect" / "klines"
CACHE = DATA_ROOT / "predlab" / "t7_panels"

SUBPERIODS = [("2021-2022", "2021-01-01", "2022-12-31"),
              ("2023-2024", "2023-01-01", "2024-12-31"),
              ("2025Q1", "2025-01-01", "2025-03-31")]


def build_panels(rebuild: bool = False) -> "dict[str, pd.DataFrame]":
    CACHE.mkdir(parents=True, exist_ok=True)
    names = ["close", "qv", "park"]
    if not rebuild and all((CACHE / f"{n}.parquet").exists() for n in names):
        return {n: pd.read_parquet(CACHE / f"{n}.parquet") for n in names}
    closes, qvs, parks = {}, {}, {}
    for path in sorted(KLINES.glob("*.parquet")):
        sym = path.stem
        df = pd.read_parquet(path)
        closes[sym] = df["close"]
        qvs[sym] = df["quote_volume"]
        parks[sym] = (np.log(df["high"] / df["low"]) ** 2) / (4 * np.log(2))
    panels = {"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs),
              "park": pd.DataFrame(parks)}
    for n, p in panels.items():
        p.to_parquet(CACHE / f"{n}.parquet")
    return panels


def monthly_universe(qv: pd.DataFrame, top_n: int = 200) -> pd.DataFrame:
    """Mask (days x syms): month m membership from month m-1 median qv (PIT)."""
    med = qv.resample("MS").median()  # median within calendar month, labeled at start
    mask_rows = {}
    months = med.index
    for i in range(1, len(months)):
        prior = med.iloc[i - 1].dropna()
        members = set(prior.nlargest(top_n).index)
        mask_rows[months[i]] = members
    mask = pd.DataFrame(False, index=qv.index, columns=qv.columns)
    for month_start, members in mask_rows.items():
        in_month = (qv.index >= month_start) & (qv.index < month_start + pd.offsets.MonthBegin(1))
        mask.loc[in_month, list(members & set(qv.columns))] = True
    return mask


def _zscore_rows(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean(axis=1)
    sd = df.std(axis=1, ddof=1).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0)


def run_combos(signals: dict, ret: pd.DataFrame, uni: pd.DataFrame,
               dev_start: str, dev_end: str) -> None:
    """Registered ridge/lgb combos: trailing-252d pooled train, monthly refit."""
    from sklearn.linear_model import Ridge
    import lightgbm as lgb_mod

    y_rank_z = _zscore_rows(ret.where(uni).rank(axis=1))
    feats_z = {k: _zscore_rows(v.where(uni)) for k, v in signals.items()}
    keys = list(feats_z)
    months = pd.date_range(dev_start, dev_end, freq="MS", tz="UTC")
    preds = {"ridge_combo": pd.DataFrame(np.nan, index=ret.index, columns=ret.columns),
             "lgb_combo": pd.DataFrame(np.nan, index=ret.index, columns=ret.columns)}
    for m in months:
        tr_lo, tr_hi = m - pd.Timedelta(days=252), m - pd.Timedelta(days=1)
        Xtr, ytr = [], []
        for k in keys:
            Xtr.append(feats_z[k].loc[tr_lo:tr_hi].to_numpy().ravel())
        ytr = y_rank_z.loc[tr_lo:tr_hi].to_numpy().ravel()
        Xtr = np.column_stack(Xtr)
        ok = ~(np.isnan(Xtr).any(axis=1) | np.isnan(ytr))
        if ok.sum() < 2000:
            continue
        m_end = m + pd.offsets.MonthBegin(1) - pd.Timedelta(days=1)
        Xte_frames = [feats_z[k].loc[m:m_end] for k in keys]
        idx, cols = Xte_frames[0].index, Xte_frames[0].columns
        Xte = np.column_stack([f.to_numpy().ravel() for f in Xte_frames])
        te_ok = ~np.isnan(Xte).any(axis=1)
        for name, model in (("ridge_combo", Ridge(alpha=1.0)),
                            ("lgb_combo", lgb_mod.LGBMRegressor(
                                n_estimators=300, learning_rate=0.05, num_leaves=31,
                                min_child_samples=50, subsample=0.9, subsample_freq=1,
                                colsample_bytree=0.9, random_state=0,
                                deterministic=True, force_row_wise=True,
                                verbosity=-1, n_jobs=4))):
            model.fit(Xtr[ok], ytr[ok])
            p = np.full(len(Xte), np.nan)
            p[te_ok] = model.predict(Xte[te_ok])
            preds[name].loc[idx, cols] = p.reshape(len(idx), len(cols))
    for name, pred in preds.items():
        p_dev = pred[(pred.index >= dev_start)].where(uni)
        y_dev = ret[(ret.index >= dev_start)].where(uni)
        ics = xsec.daily_ic(p_dev, y_dev, min_breadth=50)
        s = xsec.ic_summary(ics, nw_lag=5)
        subs = {lab: float(ics[(ics.index >= lo) & (ics.index <= hi)].dropna().mean())
                for lab, lo, hi in SUBPERIODS}
        registry.log_trial("predlab_p2_t7", f"ret_24h|{name}", name,
                           {"target": "ret_24h", "model": name}, (dev_start, dev_end),
                           {k: v for k, v in s.items()})
        print(f"ret_24h|{name}: mean_ic={s['mean_ic']:+.4f} nw_t={s['nw_t']:+.2f} "
              f"subs={ {k: round(v,4) for k,v in subs.items()} }", flush=True)


def run_slice(signals: dict, ret: pd.DataFrame, qv: pd.DataFrame,
              dev_start: str) -> None:
    """Forensic: park_5 + rev_1 ICs on top-50 vs ranks 51-200 (microstructure)."""
    uni50 = monthly_universe(qv, top_n=50)
    uni200 = monthly_universe(qv, top_n=200)
    band = uni200 & ~uni50
    for label, mask in (("top50", uni50), ("rank51_200", band)):
        for sname in ("park_5", "rev_1"):
            s_dev = signals[sname][signals[sname].index >= dev_start].where(mask)
            y_dev = ret[ret.index >= dev_start].where(mask)
            ics = xsec.daily_ic(s_dev, y_dev, min_breadth=20)
            s = xsec.ic_summary(ics, nw_lag=5)
            print(f"slice {label} ret_24h|{sname}: mean_ic={s['mean_ic']:+.4f} "
                  f"nw_t={s['nw_t']:+.2f} n={s['n_days']}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--mode", default="raw", choices=["raw", "combos", "slice"])
    args = ap.parse_args()

    entry = registry.get_experiment("predlab_p2_t7")
    dev_end = entry["dev_window"][1]

    panels = build_panels(args.rebuild)
    close, qv, park = panels["close"], panels["qv"], panels["park"]
    # clip at dev end (holdout sealed)
    close = close[close.index <= dev_end]
    qv = qv.loc[close.index]
    park = park.loc[close.index]

    ret = np.log(close).diff()
    uni = monthly_universe(qv, top_n=200)

    signals = {
        "mom_21": ret.rolling(21).sum().shift(1),
        "mom_5": ret.rolling(5).sum().shift(1),
        "rev_1": -ret.shift(1),
        "volchg_5": np.log(qv.shift(1)) - np.log(qv.shift(2).rolling(5).mean()),
        "park_5": park.rolling(5).mean().shift(1),
    }
    targets = {
        "ret_24h": (ret, 5),
        "ret_7d": (ret.rolling(7).sum().shift(-6), 10),
        "park_24h": (park, 5),
    }

    dev_start = entry["dev_window"][0]
    if args.mode == "combos":
        run_combos(signals, ret, uni, dev_start, dev_end)
        return
    if args.mode == "slice":
        run_slice(signals, ret, qv, dev_start)
        return
    results = {}
    for tname, (y, lag) in targets.items():
        y_dev = y[y.index >= dev_start].where(uni)
        for sname, sig in signals.items():
            s_dev = sig[sig.index >= dev_start].where(uni)
            ics = xsec.daily_ic(s_dev, y_dev, min_breadth=int(entry["universe"]["min_breadth"]))
            s = xsec.ic_summary(ics, nw_lag=lag)
            subs = {}
            for label, lo, hi in SUBPERIODS:
                sub = ics[(ics.index >= lo) & (ics.index <= hi)].dropna()
                subs[label] = float(sub.mean()) if len(sub) > 20 else float("nan")
            s["sub_periods"] = subs
            key = f"{tname}|{sname}"
            results[key] = s
            registry.log_trial("predlab_p2_t7", key, sname,
                               {"target": tname, "signal": sname, "universe": "top200"},
                               (dev_start, dev_end),
                               {k: v for k, v in s.items() if k != "sub_periods"})
            print(f"{key}: mean_ic={s['mean_ic']:+.4f} nw_t={s['nw_t']:+.2f} "
                  f"n={s['n_days']} subs={ {k: round(v,4) for k,v in subs.items()} }",
                  flush=True)
    out = DATA_ROOT / "predlab" / "t7_raw_ics.json"
    out.write_text(json.dumps(results, indent=1, default=float))
    print(f"written {out}")


if __name__ == "__main__":
    main()
