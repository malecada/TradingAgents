"""Freeze the order-flow P0 registration (predlab_oflow). Refuses if present."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

ENTRY = {
    "registered_utc": "2026-09-04",
    "charter": "docs/superpowers/specs/2026-09-04-oflow-charter.md",
    "purpose": "lagged signed taker flow -> next-bar return (TS BTC/ETH 1h, 24h, 5m->1h) and XS flow rank -> next-day/7d return rank; direct predictive regressions (xfam P0 protocol)",
    "decisions_afk_grant": "8 cells as listed; hourly survivors priced at taker (primary) + exec_pf passive overlay reported",
    "windows": {"dev": ["2021-01-01", "2025-03-31"], "holdout": ["2025-04-01", "2026-07-01"],
                "holdout_status": "H2 contamination-disclosed, one-shot after stop-and-decide", "F": "2026-07-02+ untouched"},
    "data": "1h store klines_1h (393 syms, taker_buy_quote_volume), 5m store BTC/ETH, daily 799 store closes + monthly top-200 PIT universe; no new fetch",
    "signal": "imb = (2*taker_buy_qv - qv)/qv per bar; z over 30-day rolling window (720 bars 1h / 30 daily / 8640 bars 5m, min_periods = half), bars <= t only; daily imb from 1h sums; 5m variant = last 5-minute bar of hour t; XS = within-universe rank of daily z",
    "cells": ["TS_1h_BTC", "TS_1h_ETH", "TS_24h_BTC", "TS_24h_ETH", "TS_5m1h_BTC", "TS_5m1h_ETH", "XS_24h_IC", "XS_7d_IC"],
    "tests": {"TS": "OLS r_{t+1} ~ z_t, HAC lag 24 (1h, 5m->1h) / lag 5 (24h); two-sided p < 0.01 AND same slope sign in 3/4 years 2021-2024",
              "XS": "daily Spearman IC (xsec.daily_ic, min_breadth 25) vs next-day / next-7-day return rank; NW-t lag 5 / 10; |IC| >= 0.02 AND NW-t >= 3 AND right sign in 2/3 sub-periods",
              "family": "BH-FDR q < 0.10 across the 8 cells; survivor = floor AND FDR"},
    "sign": "not pre-fixed (continuation or reversal); dev sign is a declared one-bit fit carried into P1 (n_trials x2)",
    "cost_prestatement": "hourly sign(z) book ~12 flips/day => ~60 bp/day at 5 bp => needs >= 5 bp mean |effect| per traded hour; TS-1h survivor below that = real but arithmetic-dead, no P1 run",
    "P1": "one frozen config per survivor: TS sign(z) hold one bar 5 bp taker (+ funding for 24h); XS quintile L/S opt.run_ls q0.2 eq 5 bp + funding; gates net SR >= 1.0, circular-shift placebo 500 draws min shift 30 p < 0.10, 2x cost sign, name share <= 50%, convention swap no flip; hourly survivors also through exec_pf LTM overlay (reported)",
    "returns": "simple returns everywhere (PnL and regressions)",
    "stop_rule": "0/8 => family CLOSED; no lag/window/threshold changes; P0 script refuses to run twice (verdicts present)",
    "mechanics": "scripts/predlab_register_oflow.py, scripts/predlab_oflow_p0.py; cache data/predlab/oflow/cache_1h; result data/predlab/oflow/p0_result.json; ledger predlab_oflow; THESIS section 80",
}


def main() -> None:
    gates = registry.load_gates()
    if "predlab_oflow" in gates:
        raise SystemExit("predlab_oflow already registered")
    gates["predlab_oflow"] = ENTRY
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print("gates.json['predlab_oflow'] written")


if __name__ == "__main__":
    main()
