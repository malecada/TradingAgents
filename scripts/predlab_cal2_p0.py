"""predlab_cal2 — session/macro-day effects at 1h, 12 pre-named tests (charter 2026-09-04).

  python scripts/predlab_cal2_p0.py register   # gates key (refuses if present)
  python scripts/predlab_cal2_p0.py run        # one-shot P0

FOMC statement days: Federal Reserve FOMC calendars (8 scheduled meetings/yr).
CPI release days: BLS CPI news-release archive. Both lists frozen below.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_xfam_cal import hac_slope, yearly_effect  # noqa: E402
from predlab_xfam_lib import DEV, bh_fdr, clip_dev, ledger_append, load_1h_panels, load_daily_panels, write_result  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402
from tradingagents.predlab.opt import monthly_universe  # noqa: E402

KEY = "predlab_cal2"
DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
FOMC = ["2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
        "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19"]
CPI = ["2021-01-13", "2021-02-10", "2021-03-10", "2021-04-13", "2021-05-12", "2021-06-10", "2021-07-13", "2021-08-11",
       "2021-09-14", "2021-10-13", "2021-11-10", "2021-12-10", "2022-01-12", "2022-02-10", "2022-03-10", "2022-04-12",
       "2022-05-11", "2022-06-10", "2022-07-13", "2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13",
       "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10",
       "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12", "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10",
       "2024-05-15", "2024-06-12", "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
       "2025-01-15", "2025-02-12", "2025-03-12"]
WINDOWS = {"H1_us": list(range(13, 20)), "H2_asia": list(range(0, 8)), "H3_usopen": [13], "H4_fomc": [18, 19], "H5_cpi": [12, 13]}

ENTRY = {
    "registered_utc": "2026-09-04", "charter": "docs/superpowers/specs/2026-09-04-cal2-charter.md",
    "purpose": "12 pre-named session / macro-day tests at 1h the xfam calendar sweep did not include",
    "windows": {"dev": list(DEV), "holdout": ["2025-04-01", "2026-07-01"], "holdout_status": "H2, stop-and-decide"},
    "tests": {"H1_us_{BTC,ETH,XSM}": "bars 13-19 vs other", "H2_asia_{BTC,ETH,XSM}": "bars 0-7 vs other",
              "H3_usopen_{BTC,ETH}": "bar 13 vs other", "H4_fomc_{BTC,ETH}": "bars 18-19 on FOMC statement days vs same bars other days",
              "H5_cpi_{BTC,ETH}": "bars 12-13 on CPI release days vs same bars other days"},
    "dates": {"FOMC": FOMC, "CPI": CPI, "sources": "federalreserve.gov FOMC calendars; bls.gov CPI news-release archive"},
    "statistic": "OLS hourly simple return ~ indicator, HAC lag 24, two-sided p; BH-FDR q<0.10 across 12; survivor also needs same sign in >=3/4 years 2021-2024",
    "P1": "one survivor => session-holding config by dev sign (declared 1-bit fit), 5 bp taker (10 bp/day floor pre-stated), exec_pf LTM overlay reported; house gates",
    "stop_rule": "0/12 => family CLOSED; no window/hour/date changes; one-shot", "thesis_section": "86",
}


def main_register() -> None:
    gates = registry.load_gates()
    if KEY in gates:
        raise SystemExit(f"{KEY} already registered")
    gates[KEY] = ENTRY
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"gates.json['{KEY}'] written")


def main_run() -> None:
    gates = registry.load_gates()
    if gates[KEY].get("verdicts"):
        raise SystemExit("REFUSED: verdicts already recorded (one-shot)")
    h1 = load_1h_panels()
    close1h = clip_dev(h1["close"])
    ret1h = close1h.pct_change(fill_method=None)
    ret1h = ret1h[ret1h.index >= DEV_LO]
    daily = load_daily_panels()
    qv_d = clip_dev(daily["qv"])
    uni100 = monthly_universe(qv_d, top_n=100)
    uni_h = uni100.reindex(ret1h.index.normalize()).to_numpy()
    uni_h = pd.DataFrame(uni_h, index=ret1h.index, columns=uni100.columns).reindex(columns=ret1h.columns).fillna(False)
    xsm = ret1h.where(uni_h.astype(bool)).mean(axis=1)
    series = {"BTC": ret1h["BTCUSDT"], "ETH": ret1h["ETHUSDT"], "XSM": xsm}
    fomc = set(pd.to_datetime(FOMC).date)
    cpi = set(pd.to_datetime(CPI).date)
    tests, details = {}, {}

    def add(name, r, ind, restrict=None):
        rr, ii = (r, ind) if restrict is None else (r[restrict], ind[restrict])
        res = hac_slope(rr, ii, lag=24)
        tests[name] = res["p"]
        details[name] = {**res, "yearly": yearly_effect(rr, ii), "n_event_bars": int(ii.sum())}

    for cell, r in series.items():
        hrs = r.index.hour
        add(f"H1_us_{cell}", r, pd.Series(np.isin(hrs, WINDOWS["H1_us"]).astype(float), index=r.index))
        add(f"H2_asia_{cell}", r, pd.Series(np.isin(hrs, WINDOWS["H2_asia"]).astype(float), index=r.index))
    for cell in ("BTC", "ETH"):
        r = series[cell]
        hrs = r.index.hour
        add(f"H3_usopen_{cell}", r, pd.Series(np.isin(hrs, WINDOWS["H3_usopen"]).astype(float), index=r.index))
        days = pd.Series(r.index.date, index=r.index)
        in_w4 = pd.Series(np.isin(hrs, WINDOWS["H4_fomc"]), index=r.index)
        add(f"H4_fomc_{cell}", r, pd.Series(days.isin(fomc).astype(float).to_numpy(), index=r.index), restrict=in_w4)
        in_w5 = pd.Series(np.isin(hrs, WINDOWS["H5_cpi"]), index=r.index)
        add(f"H5_cpi_{cell}", r, pd.Series(days.isin(cpi).astype(float).to_numpy(), index=r.index), restrict=in_w5)
    assert len(tests) == 12, len(tests)
    fdr = sorted(bh_fdr(tests, q=0.10))
    survivors = []
    for name in fdr:
        y = details[name]["yearly"]
        vals = [v for k, v in y.items() if k in ("2021", "2022", "2023", "2024")] if isinstance(y, dict) else []
        sgn = np.sign(details[name]["effect"])
        agree = sum(1 for v in vals if isinstance(v, (int, float)) and not np.isnan(v) and np.sign(v) == sgn)
        details[name]["n_year_agree"] = agree
        if agree >= 3:
            survivors.append(name)
    for name, det in details.items():
        ledger_append(KEY, name, "hac_bucket_ols", {"test": name, "lag": 24},
                      {k: det[k] for k in ("effect", "t", "p", "n")})
    verdict = (f"P0 {len(survivors)}/12 survive: {survivors}" if survivors
               else f"FAIL at P0 — 0/12 survive BH-FDR q<0.10 + year rule (min raw p {min(tests.values()):.4f}); family CLOSED")
    payload = {"family": "cal2", "n_tests": 12, "pvals": tests, "bh_fdr_q010": fdr, "survivors": survivors,
               "details": details, "dev_window": list(DEV), "verdict": verdict}
    path = write_result("cal2", payload)
    gates = registry.load_gates()
    gates[KEY]["verdicts"] = {"P0": verdict}
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    for name in sorted(tests):
        d = details[name]
        print(f"  {name:16s} effect={d['effect']*1e4:+.2f}bp t={d['t']:+.2f} p={d['p']:.4f} n_ev={d['n_event_bars']}")
    print(verdict, "->", path)


if __name__ == "__main__":
    {"register": main_register, "run": main_run}[sys.argv[1]]()
