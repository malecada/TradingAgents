"""value_rev registration: python scripts/value_rev_register.py (refuses if present)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "data/rebuild/gates.json"

KEY = {
    "registered": "2026-09-04",
    "spec": "docs/superpowers/specs/2026-09-04-value-rev-charter.md",
    "source": "LEADS_SCOPE_2026-09-02.md Lead 6; parent value_xs_t1 (thesis 51, dev 0/4)",
    "decisions_afk_grant": "revenue as second metric (4 cells); 90-day trailing window",
    "dev_window": ["2021-01-01", "2025-03-31"],
    "holdout_window": ["2025-04-01", "2026-07-01"],
    "holdout_class": "H1 virgin for this signal; one-shot only on dev PASS",
    "data": {"fees": "DefiLlama overview/fees + /protocols mapping + summary/fees/{slug} dailyFees|dailyRevenue; protocols summed per perp base; stables/wrapped excluded",
             "snapshot_1": "vintage 2026-09-04 (data/xsect/fees/2026-09-04, raw + sha256 in data/xsect/fees_raw/2026-09-04)",
             "mcap": "CoinMetrics community CapMrktCurUSD (data/xsect/fundamentals); names without it dropped, breadth reported",
             "prices": "799-symbol daily store, simple returns"},
    "probes": {"P0": "restatement: second snapshot >= 14 days after the first (>= 2026-09-18); on common protocol-days ending >= 30 d before snapshot 1, <= 5% change by > 10%; else STOP; nothing after P0 runs before it exists",
               "P1": "breadth: median weekly signal-valid names >= 20 on dev; else STOP",
               "P2": "publication lag <= 2 days at snapshot; registered feature lag 2 d, widened pre-grid if measured longer (logged)"},
    "grid": [{"metric": "mcap_over_fees_90d", "breadth": "tercile"}, {"metric": "mcap_over_fees_90d", "breadth": "decile"},
             {"metric": "mcap_over_revenue_90d", "breadth": "tercile"}, {"metric": "mcap_over_revenue_90d", "breadth": "decile"}],
    "signal": "log(mcap / trailing-90d sum of fees or revenue), cross-sectional z per weekly Monday rebalance, low = cheap = long; feature lag 2 d",
    "book": "weekly Monday dollar-neutral L/S, 10 bp/side, realized funding, rf 4.5%/yr full capital once; simple returns",
    "controls": {"C1": "30-day realized vol sort, identical pipeline", "C2": "reversal (-30d return) sort, identical pipeline", "gating": "value must beat both (delta SR > 0)"},
    "dev_select": {"net_sr_min": 1.0, "placebo": "dual-family (A per-symbol circular shift; B count-matched random rank re-assignment), 500 draws each, worse p <= 0.05",
                   "placebo_p_max": 0.05, "delta_sr_vs_controls_min": 0.0, "dsr_min": 0.9, "n_trials": 4},
    "stop_rule": "0/4 => family closed; no metric/window/breadth changes; grid refuses to run without a passing P0 file",
    "mechanics": "scripts/fetch_defillama_fees.py, scripts/value_rev_register.py, scripts/value_rev_dev.py; data/rebuild/value_rev/; ledger value_rev; THESIS section 81",
    "thesis_section": "81",
}

if __name__ == "__main__":
    gates = json.loads(GATES.read_text())
    if "value_rev" in gates:
        raise SystemExit("value_rev already registered")
    gates["value_rev"] = KEY
    GATES.write_text(json.dumps(gates, indent=1))
    print("gates.json['value_rev'] written")
