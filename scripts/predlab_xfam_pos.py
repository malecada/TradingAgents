"""xfam_pos — Coinglass positioning extremes, 8-sym panel (charter 2026-08-25).

Signals (shift 1, z-scored rolling 90d min 60):
  S1 retail-contrarian: z(ls_global ratio), hypothesis NEGATIVE next-day ret.
  S2 smart-follow: z(ls_top_position ratio), hypothesis POSITIVE.
P0: hypothesis-signed signal-weighted portfolio return, NW lag 5, one-sided
p<0.05 AND >=3/4 year positive; BH-FDR q<0.10 across 2. P1: thin-panel LS
(long 2 / short 2), one config per surviving signal.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predlab_xfam_lib import (  # noqa: E402
    DEV,
    ann_sr,
    bh_fdr,
    circular_shift_placebo,
    clip_dev,
    ledger_append,
    load_coinglass_ls,
    load_daily_panels,
    nw_tstat,
    placebo_pvalue,
    write_result,
)

DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
HYPOTHESES = {"S1_retail_contrarian": ("ls_global", -1.0),
              "S2_smart_follow": ("ls_top_position", +1.0)}


def zscore(panel: pd.DataFrame, win: int = 90, min_obs: int = 60) -> pd.DataFrame:
    mu = panel.rolling(win, min_periods=min_obs).mean()
    sd = panel.rolling(win, min_periods=min_obs).std()
    return ((panel - mu) / sd).shift(1)


def main():
    ls = load_coinglass_ls()
    syms = sorted(ls["ls_global"].columns)
    panels = load_daily_panels()
    close = clip_dev(panels["close"])[syms]
    ret = close.pct_change(fill_method=None)

    results, pvals, zs = {}, {}, {}
    for name, (kind, sgn) in HYPOTHESES.items():
        z = clip_dev(zscore(ls[kind])).reindex(ret.index)[syms]
        z = z[z.index >= DEV_LO]
        zs[name] = (z, sgn)
        port = (sgn * z * ret.reindex(z.index)).mean(axis=1).dropna()
        m, t, p2 = nw_tstat(port.to_numpy(), lag=5)
        p1 = p2 / 2 if m > 0 else 1 - p2 / 2  # one-sided per hypothesis
        per_year = {str(y): float(port[port.index.year == y].mean())
                    for y in (2021, 2022, 2023, 2024)}
        agree = sum(1 for v in per_year.values() if not np.isnan(v) and v > 0)
        results[name] = {"mean_daily": m, "nw_t": t, "p_one_sided": p1,
                         "per_year": per_year, "n_year_pos": agree,
                         "n_days": int(len(port)),
                         "sym_coverage": int(z.notna().sum(axis=1).median())}
        pvals[name] = p1
        ledger_append("predlab_xfam_pos", "8sym|1d", name,
                      {"z_win": 90, "hypothesis_sign": sgn},
                      {"mean_daily": m, "nw_t": t, "p_one_sided": p1})

    fdr = bh_fdr(pvals, q=0.10)
    survivors = sorted(k for k in fdr
                       if results[k]["p_one_sided"] < 0.05
                       and results[k]["n_year_pos"] >= 3)
    payload = {"family": "xfam_pos", "symbols": syms, "P0": results,
               "P0_survivors": survivors}
    for k, v in results.items():
        print(f"P0 {k:22s} mean={v['mean_daily']:+.5f} t={v['nw_t']:+.2f} "
              f"p1s={v['p_one_sided']:.4f} yrs+={v['n_year_pos']}/4")
    print(f"survivors: {survivors or 'NONE'}")

    payload["P1"] = {}
    if survivors:
        from predlab_xfam_lib import thin_ls_backtest
        from tradingagents.predlab import pp

        fund = pp.build_funding_daily(syms, Path("data/xsect/funding"), ret.index)
        for k in survivors:
            z, sgn = zs[k]
            df = thin_ls_backtest(sgn * z, ret, n_leg=2, fund_daily=fund)
            sr = ann_sr(df["net"].to_numpy())

            def run_fn(shifted_z, _r=ret, _f=fund):
                d = thin_ls_backtest(shifted_z, _r, n_leg=2, fund_daily=_f)
                return ann_sr(d["net"].to_numpy())

            nulls = circular_shift_placebo(run_fn, sgn * z, n_draws=200)
            payload["P1"][k] = {
                "sr_net": sr, "sr_gross": ann_sr(df["gross"].to_numpy()),
                "placebo_p": placebo_pvalue(sr, nulls),
                "avg_turnover": float(df["turnover"].mean()),
                "n_days": int(len(df))}
            ledger_append("predlab_xfam_pos", "8sym|1d", f"{k}_thinls",
                          {"n_leg": 2}, payload["P1"][k])
            print(f"P1 {k}: net SR={sr:+.2f} gross={payload['P1'][k]['sr_gross']:+.2f} "
                  f"placebo p={payload['P1'][k]['placebo_p']:.3f} "
                  f"turn={payload['P1'][k]['avg_turnover']:.2f}")

    path = write_result("pos", payload)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
