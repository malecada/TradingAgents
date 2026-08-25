"""xfam_amx — Amihud illiquidity XS premium (charter 2026-08-25).

P0: monthly Spearman IC of amihud_21d (shift 1) vs next-21-traded-day return,
top-200 PIT universe + $1M ADV floor. Gate: NW-lag-1 t-test p<0.05 AND same
IC sign in >=3 of 4 years 2021-2024. P1 (only if P0 passes): run_ls, one
config, direction = P0 sign.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predlab_xfam_lib import (  # noqa: E402
    DEV,
    ann_sr,
    clip_dev,
    ledger_append,
    load_daily_panels,
    nw_tstat,
    write_result,
)

ADV_FLOOR = 1e6
FWD_TD = 21


def monthly_ic_series(sig, close, uni):
    ret_fwd = close.shift(-FWD_TD) / close - 1.0
    month_starts = []
    for m, sub in sig.groupby(sig.index.to_period("M")):
        month_starts.append(sub.index[0])
    rows = {}
    last_ok = pd.Timestamp(DEV[1], tz="UTC")
    for t in month_starts:
        # forward window must complete inside dev
        future = close.index[close.index.get_loc(t):]
        if len(future) <= FWD_TD or future[FWD_TD] > last_ok:
            continue
        members = uni.columns[uni.loc[t]] if t in uni.index else []
        s = sig.loc[t, members].dropna()
        f = ret_fwd.loc[t, members].dropna()
        common = s.index.intersection(f.index)
        if len(common) < 50:
            continue
        rho, _ = spearmanr(s[common], f[common])
        rows[t] = float(rho)
    return pd.Series(rows)


def main():
    from tradingagents.predlab.opt import apply_adv_floor, monthly_universe

    panels = load_daily_panels()
    close = clip_dev(panels["close"])
    qv = panels["qv"].loc[close.index]
    ret = close.pct_change(fill_method=None)
    uni = apply_adv_floor(monthly_universe(qv, top_n=200), qv, ADV_FLOOR)
    amihud = (ret.abs() / qv).rolling(21).mean().shift(1)
    amihud = amihud[amihud.index >= pd.Timestamp(DEV[0], tz="UTC")]

    ics = monthly_ic_series(amihud, close, uni)
    mean_ic, t, p = nw_tstat(ics.to_numpy(), lag=1)
    per_year = {str(y): float(ics[ics.index.year == y].mean())
                for y in (2021, 2022, 2023, 2024)}
    overall = np.sign(mean_ic)
    agree = sum(1 for v in per_year.values()
                if not np.isnan(v) and np.sign(v) == overall)
    p0_pass = bool(p < 0.05 and agree >= 3)

    payload = {"family": "xfam_amx", "P0": {
        "n_months": int(len(ics)), "mean_ic": mean_ic, "nw_t": t, "p": p,
        "per_year_ic": per_year, "n_year_agree": agree, "pass": p0_pass,
        "monthly_ics": {str(k.date()): v for k, v in ics.items()}}}
    ledger_append("predlab_xfam_amx", "top200_adv1m|21d", "amihud_ic",
                  {"fwd_td": FWD_TD, "adv_floor": ADV_FLOOR},
                  {"mean_ic": mean_ic, "nw_t": t, "p": p, "n_months": len(ics)})
    print(f"P0: mean IC={mean_ic:+.4f} t={t:+.2f} p={p:.4f} years-agree={agree}/4"
          f" -> {'PASS' if p0_pass else 'FAIL'}")
    print(f"per-year: {per_year}")

    if p0_pass:
        from tradingagents.predlab.opt import OptConfig, run_ls

        sign = float(overall)
        sig = -sign * amihud  # leg_weights longs the BOTTOM quantile
        cache = Path("data/predlab/pp_funding_daily.parquet")
        fund = pd.read_parquet(cache).reindex(ret.index) if cache.exists() else None
        cfg = OptConfig(signal="amihud21", q_frac=0.2, weighting="eq",
                        cadence=21, smooth=1, taker_bp=5.0)
        res = run_ls(sig, ret, uni, fund, cfg, DEV[0], DEV[1])
        payload["P1"] = {"sr_net": res["sr_net"], "sr_gross": res["sr_gross"],
                         "maxdd": res["maxdd"], "avg_turnover": res["avg_turnover"],
                         "n_days": res["n_days"], "direction": "long_illiquid" if sign > 0 else "long_liquid"}
        ledger_append("predlab_xfam_amx", "top200_adv1m|21d", "amihud_ls",
                      {"cfg": "eq_q20_c21", "direction": float(sign)},
                      {k: payload["P1"][k] for k in ("sr_net", "sr_gross", "maxdd")})
        print(f"P1: net SR={res['sr_net']:+.2f} gross={res['sr_gross']:+.2f} "
              f"maxdd={res['maxdd']:.1%} turn={res['avg_turnover']:.3f}")

    path = write_result("amx", payload)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
