"""xfam_llg — BTC/ETH → alt lead-lag (charter 2026-08-25).

P0 cells: (a) daily BTC ret t → follower index t+1, (b) daily ETH,
(c) hourly BTC h → follower h+1, (d) hourly ETH. Follower = equal-weight
top-200 (daily) / top-100 (1h, by prior-month median qv) universe ex BTC/ETH.
OLS slope, NW lag 5 daily / 24 hourly; gate p<0.01 + >=3/4 year sign
consistency per cell + BH-FDR q<0.10 across 4. P1: sign-follow TS strategy
on the follower basket, one config per surviving cell.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predlab_xfam_lib import (  # noqa: E402
    DEV,
    TAKER_BP,
    ann_sr,
    bh_fdr,
    circular_shift_placebo,
    clip_dev,
    ledger_append,
    load_1h_panels,
    load_daily_panels,
    placebo_pvalue,
    write_result,
)

DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
LEADERS = ["BTCUSDT", "ETHUSDT"]


def hac_predictive(leader_ret: pd.Series, follower_ret: pd.Series, lag: int):
    """OLS follower(t+1) ~ leader(t), HAC t/p on slope + yearly slopes."""
    import statsmodels.api as sm

    df = pd.concat({"y": follower_ret.shift(-1), "x": leader_ret}, axis=1).dropna()
    X = sm.add_constant(df["x"])
    res = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    slope, t, p = float(res.params["x"]), float(res.tvalues["x"]), float(res.pvalues["x"])
    yearly = {}
    for y in (2021, 2022, 2023, 2024):
        sub = df[df.index.year == y]
        if len(sub) > 50:
            yearly[str(y)] = float(np.polyfit(sub["x"], sub["y"], 1)[0])
    agree = sum(1 for v in yearly.values() if np.sign(v) == np.sign(slope))
    return {"slope": slope, "t": t, "p": p, "n": int(len(df)),
            "yearly_slopes": yearly, "n_year_agree": agree}


def follower_index_daily():
    from tradingagents.predlab.opt import monthly_universe

    panels = load_daily_panels()
    close = clip_dev(panels["close"])
    qv = panels["qv"].loc[close.index]
    ret = close.pct_change(fill_method=None)
    uni = monthly_universe(qv, top_n=200)
    uni[["BTCUSDT", "ETHUSDT"]] = False
    fol = ret.where(uni).mean(axis=1)
    return ret, fol[fol.index >= DEV_LO]


def follower_index_hourly():
    panels = load_1h_panels()
    close = clip_dev(panels["close"])
    qv = panels["qv"].loc[close.index]
    ret = close.pct_change(fill_method=None)
    # monthly PIT top-100 by prior-month median hourly qv
    med = qv.resample("MS").median()
    mask = pd.DataFrame(False, index=ret.index, columns=ret.columns)
    months = med.index
    for i in range(1, len(months)):
        members = set(med.iloc[i - 1].dropna().nlargest(100).index) - set(LEADERS)
        in_m = (ret.index >= months[i]) & (ret.index < months[i] + pd.offsets.MonthBegin(1))
        mask.loc[in_m, list(members & set(ret.columns))] = True
    fol = ret.where(mask).mean(axis=1)
    return ret, fol[fol.index >= DEV_LO]


def ts_follow_backtest(leader_ret: pd.Series, follower: pd.Series, slope_sign: float,
                       taker_bp: float = TAKER_BP) -> pd.Series:
    """w(t) = slope_sign * sign(leader ret t-1) on the follower basket; net of
    turnover costs (positions +/-1, turnover = |w_t - w_{t-1}|)."""
    w = (slope_sign * np.sign(leader_ret)).shift(1)
    df = pd.concat({"w": w, "r": follower}, axis=1).dropna()
    gross = df["w"] * df["r"]
    turn = df["w"].diff().abs().fillna(df["w"].abs())
    return gross - taker_bp / 1e4 * turn


def main():
    ret_d, fol_d = follower_index_daily()
    ret_h, fol_h = follower_index_hourly()
    cells, data = {}, {}
    for sym, tag in [("BTCUSDT", "BTC"), ("ETHUSDT", "ETH")]:
        ld = ret_d[sym].loc[fol_d.index]
        res = hac_predictive(ld, fol_d, lag=5)
        cells[f"daily_{tag}"] = res
        data[f"daily_{tag}"] = (ld, fol_d, 365.0)
        lh = ret_h[sym].loc[fol_h.index]
        res_h = hac_predictive(lh, fol_h, lag=24)
        cells[f"hourly_{tag}"] = res_h
        data[f"hourly_{tag}"] = (lh, fol_h, 365.0 * 24)

    pvals = {k: v["p"] for k, v in cells.items()}
    fdr = bh_fdr(pvals, q=0.10)
    survivors = sorted(k for k in fdr
                       if cells[k]["p"] < 0.01 and cells[k]["n_year_agree"] >= 3)
    payload = {"family": "xfam_llg", "P0": cells, "bh_fdr_q010": sorted(fdr),
               "P0_survivors": survivors}
    for k, v in cells.items():
        ledger_append("predlab_xfam_llg", k, "predictive_ols",
                      {"cell": k}, {kk: v[kk] for kk in ("slope", "t", "p", "n")})
    print("P0 cells:")
    for k, v in cells.items():
        print(f"  {k:12s} slope={v['slope']:+.4f} t={v['t']:+.2f} p={v['p']:.4g} "
              f"years={v['n_year_agree']}/4")
    print(f"survivors: {survivors or 'NONE'}")

    payload["P1"] = {}
    for k in survivors:
        leader, follower, ppy = data[k]
        sign = np.sign(cells[k]["slope"])
        net = ts_follow_backtest(leader, follower, sign)
        sr = ann_sr(net.to_numpy(), periods_per_year=ppy)

        def run_fn(shifted_leader, _f=follower, _s=sign, _ppy=ppy):
            return ann_sr(ts_follow_backtest(shifted_leader, _f, _s).to_numpy(),
                          periods_per_year=_ppy)

        nulls = circular_shift_placebo(run_fn, leader, n_draws=200,
                                       min_shift=100)
        pp = placebo_pvalue(sr, nulls)
        gross = ts_follow_backtest(leader, follower, sign, taker_bp=0.0)
        payload["P1"][k] = {"sr_net": sr,
                            "sr_gross": ann_sr(gross.to_numpy(), periods_per_year=ppy),
                            "placebo_p": pp, "n_bars": int(len(net))}
        ledger_append("predlab_xfam_llg", k, "ts_follow",
                      {"cell": k, "sign": float(sign)}, payload["P1"][k])
        print(f"P1 {k}: net SR={sr:+.2f} gross SR={payload['P1'][k]['sr_gross']:+.2f} "
              f"placebo p={pp:.3f}")

    path = write_result("llg", payload)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
