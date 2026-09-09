#!/usr/bin/env python
"""Carry audit pass 1: timing convention.

Verifies the sleeve cannot see same-day information it wouldn't have live,
by comparing the as-built daily series vs a funding-lagged (+1d) variant.
For an always-on hedged sleeve the two should differ only marginally
(reordering, not information) — a large SR drop indicates a same-bar credit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.carry_blend_p4 import fetch_spot_close  # noqa: E402
from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.strategies.carry_sleeve import (  # noqa: E402
    compute_price_pnl, fetch_perp_mark, funding_daily_income,
)

ANN = np.sqrt(252)
START, END = "2021-11-08", "2025-03-31"


def sr(x):
    x = x.dropna()
    return float(x.mean() / x.std() * ANN) if x.std() > 0 else 0.0


def main():
    from datetime import date
    start, end = date(2021, 11, 8), date(2025, 3, 31)
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        funding = funding_daily_income(sym, start, end)
        spot = fetch_spot_close(sym, start, end)
        perp = fetch_perp_mark(sym, start, end)
        hedge = compute_price_pnl(spot, perp)
        asbuilt = (funding + hedge.reindex(funding.index)).dropna()
        lagged = (funding.shift(1) + hedge.reindex(funding.index)).dropna()
        out[sym] = {"sr_asbuilt": sr(asbuilt), "sr_funding_lag1": sr(lagged),
                    "delta": sr(asbuilt) - sr(lagged)}
        print(sym, out[sym])
    verdict = "PASS" if all(abs(v["delta"]) < 0.5 for v in out.values()) else "INVESTIGATE"
    out["verdict"] = verdict
    outp = PROJECT_ROOT / "data/rebuild/carry_audit/timing.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2))
    log_trial("carry_audit", {"pass": "timing", "variant": "funding_lag1"},
              (START, END), {k: v for k, v in out.items() if k != "verdict"})
    print("verdict:", verdict)


if __name__ == "__main__":
    main()
