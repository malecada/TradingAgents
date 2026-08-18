"""Register xasset_equity_r1 — Phase-O champion verbatim replication on US equities.

Idempotent: refuses to overwrite an existing xasset_equity_r1 entry.
Charter: docs/predlab/reports/xasset_equity_r1_charter.md
Precedent: predlab_bybit_r1 (zero degrees of freedom on new data -> one-shot
full-window replication, no dev/holdout split; the entire equity window is
virgin because no strategy parameter was ever fitted to equity data).
"""
from __future__ import annotations

import json
from pathlib import Path

GATES = Path("data/predlab/gates.json")

ENTRY = {
    "registered_utc": "2026-08-18",
    "charter": "docs/predlab/reports/xasset_equity_r1_charter.md",
    "hypothesis": (
        "Phase-O final champion (ewma_20 Parkinson low-vol eq-quintile LS, "
        "top-200 monthly-PIT dollar-volume universe, vt15_naive20_b100) "
        "transfers verbatim to US equities — asset-class generalization"
    ),
    "config": (
        "identical to predlab_opt.final_champion; ONLY forced asset-class "
        "adaptations: (1) ANN 365->252; (2) funding carry -> 0, replaced by "
        "short-leg borrow fee 1.0%/yr charged daily on scaled short gross; "
        "(3) taker 5bp/side kept; (4) NO re-tuning of signal/universe/overlay"
    ),
    "data": {
        "source": "Alpaca SIP daily bars, adjustment=all, feed=sip (free tier)",
        "store": "data/xsect_equity/bars/*.parquet + manifest",
        "universe_pool": (
            "Alpaca /v2/assets us_equity, status active+inactive (survivorship-"
            "safe); exchanges NYSE/NASDAQ/AMEX/ARCA/BATS only (no OTC); "
            "exclude 5-char symbols ending W/R/U (warrants/rights/units) and "
            "ETF/fund name-heuristic matches (frozen list in fetch script)"
        ),
        "dollar_volume": "vw * volume (VWAP notional, analogue of quote_volume)",
        "parkinson_note": (
            "ln(high/low) invariant to multiplicative split/div adjustment; "
            "adjusted closes give total returns"
        ),
    },
    "window": ["2017-01-03", "2026-08-14"],
    "window_note": (
        "2016 bars = signal burn-in + first membership month only; entire "
        "window VIRGIN (no equity data touched by any prior selection)"
    ),
    "n_trials": 1,
    "sensitivity_disclosure_only": (
        "borrow {0, 1, 3}%/yr x taker {2.5, 5, 10}bp grid reported, never "
        "used for selection; rf-on-collateral ignored (conservative)"
    ),
    "probes_P0_pre_equity": {
        "parity_pin": (
            "ported runner on crypto store must reproduce final_champion "
            "ovl SR +1.892 within +/-0.001 (proves engine reuse exact)"
        ),
        "planted_alpha": "inject +20bp/day on future book longs -> pipeline must recover it",
        "leaky_canary": "shift(0) signal variant must beat shift(1) materially, else harness cannot see leakage",
    },
    "feasibility_P1": {
        "breadth": ">= 2000 trading days with breadth >= 100, else INFEASIBLE (trial unspent)",
        "deaths": (
            ">= 100 distinct inactive (delisted) symbols must appear in "
            "top-200 membership months with terminal bars, else INFEASIBLE "
            "(store would be survivorship-biased)"
        ),
        "splits": "AAPL & TSLA 2020-08-31 adjusted |daily return| < 20% (adjustment sanity)",
    },
    "criteria": {
        "U1_transfer": {
            "ovl_sr_floor": 0.946,
            "note": "= 0.5 x crypto dev ovl SR, mirrors predlab_bybit_r1 floor",
            "placebo_shift_p_lt": 0.05,
            "placebo_xshuffle_p_lt": 0.05,
            "placebo_draws": 400,
            "subperiods_positive_min": "3/4",
        },
        "U2_yields_returns": {
            "ovl_sr_gt": 0.0,
            "placebo_shift_p_lt": 0.05,
            "placebo_xshuffle_p_lt": 0.05,
            "placebo_draws": 400,
            "borrow_stress_3pct_sr_gt": 0.0,
        },
        "hierarchy": "U1 implies U2; report the strongest level attained; U2 fail = clean negative",
    },
    "stop_rule": (
        "one run; no post-hoc universe/window/cost/signal edits after the "
        "first equity strategy number exists; single-name checks disclosed, "
        "never acted on; failure = negative recorded; revival or any equity "
        "re-tuning requires a NEW registered cycle"
    ),
}


def main() -> int:
    gates = json.loads(GATES.read_text())
    if "xasset_equity_r1" in gates:
        print("xasset_equity_r1 already registered — refusing to overwrite")
        return 1
    gates["xasset_equity_r1"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=1) + "\n")
    print("registered xasset_equity_r1 in", GATES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
