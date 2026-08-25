"""xfam_cal — 11 pre-named calendar-effect tests (charter 2026-08-25).

H1 weekend (BTC/ETH/XSM), H2 turn-of-month (BTC/ETH/XSM),
H3 Deribit expiry week (BTC/ETH/XSM), H4 funding-window hours (BTC/ETH 1h).
Effect = OLS slope of return on bucket indicator, HAC/NW t (lag 5 daily,
24 hourly). Gate: BH-FDR q<0.10 across the 11. Dev window only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predlab_xfam_lib import (  # noqa: E402
    DEV,
    bh_fdr,
    clip_dev,
    ledger_append,
    load_1h_panels,
    load_daily_panels,
    write_result,
)

DEV_LO = pd.Timestamp(DEV[0], tz="UTC")


def hac_slope(ret: pd.Series, indicator: pd.Series, lag: int):
    """OLS ret ~ const + I, HAC(Bartlett, lag) t and p for the slope."""
    import statsmodels.api as sm

    df = pd.concat({"r": ret, "i": indicator.astype(float)}, axis=1).dropna()
    if len(df) < 100 or df["i"].nunique() < 2:
        return {"effect": np.nan, "t": np.nan, "p": np.nan, "n": len(df)}
    X = sm.add_constant(df["i"])
    res = sm.OLS(df["r"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return {"effect": float(res.params["i"]), "t": float(res.tvalues["i"]),
            "p": float(res.pvalues["i"]), "n": int(len(df))}


def last_friday(year: int, month: int) -> pd.Timestamp:
    end = pd.Timestamp(year=year, month=month, day=1, tz="UTC") + pd.offsets.MonthEnd(0)
    off = (end.weekday() - 4) % 7
    return end - pd.Timedelta(days=off)


def expiry_indicator(index: pd.DatetimeIndex) -> pd.Series:
    """+1 for the 4 trading days ending at expiry Friday (incl.), 0 for the 4
    days after, NaN elsewhere (excluded from the regression)."""
    ind = pd.Series(np.nan, index=index)
    months = sorted({(d.year, d.month) for d in index})
    days = index.sort_values()
    for y, m in months:
        exp = last_friday(y, m)
        upto = days[days <= exp]
        after = days[days > exp]
        if len(upto) >= 4:
            ind.loc[upto[-4:]] = 1.0
        ind.loc[after[:4]] = 0.0
    return ind


def yearly_effect(ret: pd.Series, indicator: pd.Series) -> dict:
    df = pd.concat({"r": ret, "i": indicator.astype(float)}, axis=1).dropna()
    out = {}
    for y, sub in df.groupby(df.index.year):
        a, b = sub[sub["i"] == 1]["r"], sub[sub["i"] == 0]["r"]
        if len(a) > 5 and len(b) > 5:
            out[str(y)] = float(a.mean() - b.mean())
    return out


def main():
    from tradingagents.predlab.opt import monthly_universe

    panels = load_daily_panels()
    close = clip_dev(panels["close"])
    qv = panels["qv"].loc[close.index]
    ret = close.pct_change(fill_method=None)
    uni100 = monthly_universe(qv, top_n=100)
    xsm = ret.where(uni100).mean(axis=1)
    series_daily = {
        "BTC": ret["BTCUSDT"],
        "ETH": ret["ETHUSDT"],
        "XSM": xsm,
    }
    for k in series_daily:
        series_daily[k] = series_daily[k][series_daily[k].index >= DEV_LO]

    h1 = load_1h_panels()
    close1h = clip_dev(h1["close"])
    tests, details = {}, {}

    for cell, r in series_daily.items():
        idx = r.index
        # H1 weekend
        wk = pd.Series((idx.weekday >= 5).astype(float), index=idx)
        res = hac_slope(r, wk, lag=5)
        tests[f"H1_weekend_{cell}"] = res["p"]
        details[f"H1_weekend_{cell}"] = {**res, "yearly": yearly_effect(r, wk)}
        # H2 turn-of-month
        dim = idx.days_in_month
        tom = pd.Series(((idx.day <= 2) | (idx.day >= dim - 1)).astype(float), index=idx)
        res = hac_slope(r, tom, lag=5)
        tests[f"H2_tom_{cell}"] = res["p"]
        details[f"H2_tom_{cell}"] = {**res, "yearly": yearly_effect(r, tom)}
        # H3 expiry week
        exp = expiry_indicator(idx)
        res = hac_slope(r, exp, lag=5)
        tests[f"H3_expiry_{cell}"] = res["p"]
        details[f"H3_expiry_{cell}"] = {**res, "yearly": yearly_effect(r, exp)}

    for cell, sym in [("BTC", "BTCUSDT"), ("ETH", "ETHUSDT")]:
        rh = close1h[sym].pct_change(fill_method=None)
        rh = rh[rh.index >= DEV_LO]
        fh = pd.Series(np.isin(rh.index.hour, [7, 15, 23]).astype(float), index=rh.index)
        res = hac_slope(rh, fh, lag=24)
        tests[f"H4_fundhour_{cell}"] = res["p"]
        details[f"H4_fundhour_{cell}"] = {**res, "yearly": yearly_effect(rh, fh)}

    assert len(tests) == 11, f"charter pins 11 tests, got {len(tests)}"
    survivors = sorted(bh_fdr(tests, q=0.10))
    payload = {"family": "xfam_cal", "n_tests": 11, "pvals": tests,
               "bh_fdr_q010_survivors": survivors, "details": details,
               "dev_window": list(DEV)}
    for name, det in details.items():
        ledger_append("predlab_xfam_cal", name, "hac_bucket_ols",
                      {"test": name, "lag": 24 if name.startswith("H4") else 5},
                      {k: det[k] for k in ("effect", "t", "p", "n")})
    path = write_result("cal", payload)
    print(f"survivors (BH-FDR q<0.10): {survivors or 'NONE'}")
    for name in sorted(tests):
        d = details[name]
        print(f"  {name:22s} effect={d['effect']:+.5f} t={d['t']:+.2f} p={d['p']:.4f}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
