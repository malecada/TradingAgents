"""exec_pf registration (charter docs/superpowers/specs/2026-09-03-exec-pf-charter.md).

  python scripts/exec_pf_register.py symbols  # freeze data/xsect/exec_pf_symbols.txt + event table
  python scripts/exec_pf_register.py key      # write gates.json["exec_pf"] (refuses if present)
  python scripts/exec_pf_register.py inputs   # copy predlab forecast/rv stores with sha256 stamps

`symbols` re-runs the PARENT detector (thr 3.5, membership-masked, dev window
only) on the parent 1h store and writes the symbols that carry at least one
dev trigger, plus BTCUSDT/ETHUSDT for R1, and the dev event table used by the
P0 sampler. Nothing here reads past 2025-03-31 23:00 (parent loader cap).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "data/rebuild/gates.json"
OUT = ROOT / "data/rebuild/exec_pf"
SYMS_FILE = ROOT / "data/xsect/exec_pf_symbols.txt"
EVENTS_FILE = OUT / "dev_events_thr35.json"
PREDLAB = Path("/home/malecada/master_thesis/TradingAgents-predlab/data/predlab")

DEV = ("2021-01-01", "2025-03-31")
R2_CFG = {"thr": 3.5, "H": 48, "w_per": 0.1, "cap": 1.0, "cost_bps": 10.0, "rf_annual": 0.045}
R1_CFG = {"thresh": 0.50, "smooth": 24, "model": "logit_lags5", "cell": "predlab_p2_ml/{SYM}_1h_T2_dir"}

KEY = {
    "registered": "2026-09-03",
    "spec": "docs/superpowers/specs/2026-09-03-exec-pf-charter.md",
    "source": "LEADS_SCOPE_2026-09-02.md Lead 2; AUDIT_RESEARCH_PROGRAM_2026-09-02.md section 6 item 2",
    "hypothesis": "two closed hourly signals whose only binding kill was taker cost clear the house net-SR floor under a conservative pre-frozen maker-fill model with a realistic fill rate",
    "holdout_class": "H3 dev-only: no holdout claim; loaders clip at 2025-03-31 23:00; liq_fade H1 already SPENT by combo_c1",
    "dev_window": list(DEV),
    "signals": {
        "R1_BTC": {"parent": "predlab_pp S3 (thesis 58, exploratory)", "config": R1_CFG,
                   "parent_pin": "pp_dev_results.json S3 s3_t0.5_h24 sr_net -0.0804 (hourly SR, LOG-return engine, 5 bp) -- harness check only; taker reference re-derived under simple returns",
                   "forecast_window": ["2021-01-01", "2025-03-31"]},
        "R1_ETH": {"parent": "config transfer from R1_BTC (never run by parent)", "config": R1_CFG,
                   "forecast_window": ["2021-12-01", "2025-03-31"]},
        "R2": {"parent": "liq_fade_i1 (thesis 49)", "config": R2_CFG,
               "parent_pin": "data/rebuild/liq_fade/dev_results.json thr3.5 H48 net_sr 1.3047 (daily SR, simple returns, 10 bp)"},
        "R0": {"parent": "xfam_llg (thesis 72)", "rule": "arithmetic pre-check only: |slope 0.0340| x E[|r_BTC_1h| | top decile] must exceed 2 x maker round trip (8.0 bp) else closed without a run; q95/q99 reported",
               "registration_estimate": {"q90_abs_r": 0.00955, "top_decile_mean_abs_r": 0.01636, "expected_gross_bp": 5.6, "bar_bp": 8.0}},
    },
    "data": {
        "klines_1m": "Vision futures/um/monthly/klines/{SYM}/1m, symbols = data/xsect/exec_pf_symbols.txt (88 dev-trigger symbols + BTC/ETH), months 2020-12..2025-03 within each symbol's 1h coverage; store data/xsect/klines_1m/, manifest + confirmed-404 list",
        "aggtrades": "Vision futures/um/daily/aggTrades, ONLY the P0 sample (40 liq_fade entry symbol-days + 10 BTC + 10 ETH dev days, seed 20260903)",
        "bookDepth": "PROBED 2026-09-03: starts 2023-01-01, only +/-1..5% notional bands, no touch quote -- NOT USED (deviation from scoping charter); bookTicker 404 on Vision UM",
        "tick": "inferred per symbol-month from 1m OHLC (min positive gap of sorted distinct prices), cross-checked vs fapi exchangeInfo on the last month",
        "inputs_copied": "predlab forecasts predlab_p2_ml/{BTC,ETH}USDT_1h_T2_dir/logit_lags5.parquet + rv_1h/{BTC,ETH}USDT.parquet -> data/rebuild/exec_pf/inputs/ with sha256",
    },
    "fill_model": {
        "placement": "every parent dW != 0 at boundary b|b+1 -> limit at close_b; buy L = close_b - spread/2 rounded DOWN to tick; sell L = close_b + spread/2 rounded UP",
        "spread": "spread_b = max(1 tick, s_rel(sym) x close_b); s_rel per symbol = median over sampled days of median over minutes of (median ask-side print - median bid-side print)/mid from aggTrades is_buyer_maker; unsampled symbols = pooled median over sampled non-BTC/ETH symbol-days; numbers frozen in data/rebuild/exec_pf/spread_model.json by P0, never edited",
        "latency": "order live from minute 1 of bar b+1 (minute 0 excluded)",
        "fill_rule": "trade-through: buy fills iff any 1m low in minutes 1..59 <= L - 1 tick; sell iff any 1m high >= L + 1 tick; touch does not fill; fill price = L; single pre-declared tightening to 2 ticks if P0 fails once",
        "booking": "simple returns, exact segment accounting: bar b+1 contribution = w_old x (L/close_b - 1) + w_new x (close_{b+1}/L - 1); unfilled LTM: w_old x (close_{b+1}/close_b - 1) then market at close_{b+1} charged spread/2 + taker on |dw|, w_new from bar b+2; adverse selection lives inside the PnL",
        "policies": {"LTM": "primary, gated: limit then market at bar end", "LOC": "reported: entries/increases limit-or-cancel re-placed each boundary while parent wants more; reductions/exits limit-then-market", "taker": "parity mode: fill at close_b at parent cost"},
        "fees": {"maker_bp": 2.0, "taker_bp": 5.0, "parent_cost_bp": {"R2": 10.0, "R1": 5.0}, "rf": "R2 4.5%/yr full capital daily (parent); R1 none (parent)"},
        "sr": "daily UTC aggregation, mean/sd(ddof 1) x sqrt(365) for both signals; R1 parent hourly SR reported for parity",
        "missing_minutes": "no fill; LTM market at close_{b+1} from the 1h store; parent fillna(0) return convention kept",
    },
    "probes": {
        "P0": "tick-vs-1m calibration on the seeded sample: 1m-rule fill rate <= tick-level fill rate + 5 pp (tick truth: last bid/ask-side print at placement, print strictly beyond limit >= 60 s after placement); FAIL -> tighten to 2 ticks once; second FAIL -> STOP (model)",
        "P1": "unconditional adverse selection: 2000 seeded random (symbol, hour, side) placements in dev; mean signed 5-min post-fill drift <= 0; else STOP (model broken); R2-event drift reported not gated",
        "P2": "parity: taker mode reproduces R2 parent daily series to 1e-9 and SR 1.3047 to 1e-6; R1-BTC parent hourly SR -0.0804 to 1e-6 on the parent's log series at 5 bp (harness check); FAIL -> STOP (harness)",
        "P3": "data integrity: 1m-rebuilt hourly close == 1h store close (|d|/close <= 1e-6) on >= 99.5% of overlapping dev bars per symbol; every ordered bar of the real paths has >= 55/60 minutes; tick consistency across months; FAIL -> STOP (data)",
    },
    "gates_dev_LTM": {
        "net_sr_min": 1.0,
        "fill_rate_min": 0.60,
        "fill_rate_basis": "limit-filled |dw| notional / total ordered |dw| notional (LTM market remainders = unfilled)",
        "placebo": "parent families through the passive overlay, 500 draws each, worse p <= 0.05; R2: A per-symbol circular trigger shift >= 24 bars, B count-matched uniform redraw within membership, seed 48; R1: A circular shift of P(up) min 30 bars, B 24h-block permutation of P(up)",
        "placebo_p_max": 0.05,
        "cost_stress": "maker 3.0 bp keeps sign of net SR",
        "convention_swap": "log booking at every PnL step keeps sign of net SR; both reported (rail 15)",
        "all_required": True,
    },
    "reported_not_gated": ["LOC policy on every metric", "taker reference under simple returns", "fill rate by side/year",
                            "mean adverse-selection cost per fill (L vs bar-end close)", "per-year SR", "DSR at n_trials 3 and cumulative",
                            "maxDD", "top-name share of pooled gross PnL (R2)", "R2-event 5-min post-fill drift"],
    "multiplicity": {"gated_rows": 3, "n_trials_family": 3, "non_selectable_rows": "3 LOC + 3 taker-reference", "rationale": "fill model fixed pre-result, one frozen config per signal; cumulative ledger denominator reported"},
    "stop_rule": "per signal any gate FAIL -> closed at the execution layer ('real, uneconomic even passive' / 'no edge to price'); no re-tuning of threshold, spread, latency, fee; PASS -> stop-and-decide with the user (F-window confirmatory >= 2027-01, registered then)",
    "decisions": "LTM primary; maker 2.0 bp; R0 pre-check included; worktree TradingAgents feature/exec-pf; bookDepth dropped (probed unusable)",
    "mechanics": "tradingagents/xsect/fills.py + tests/test_xsect_fills.py; scripts/fetch_vision_{1m,aggtrades}.py; scripts/exec_pf_{register,probes,run}.py; data/rebuild/exec_pf/; ledger experiment exec_pf; THESIS section 77",
    "thesis_section": "77",
}


def main_symbols() -> None:
    from liq_fade_dev import (DEV as PDEV, UNIVERSE_FILE, load_hourly_panel, load_symbols,
                              membership_mask_hourly)
    from tradingagents.xsect.liq_fade import cascade_triggers, event_weights_hourly

    syms = load_symbols(False)
    close, qvol = load_hourly_panel(syms)
    uni = json.loads(UNIVERSE_FILE.read_text())
    mask = membership_mask_hourly(uni, close.columns.tolist(), close.index)
    lo = pd.Timestamp(PDEV[0], tz="UTC")
    hi = pd.Timestamp(PDEV[1], tz="UTC") + pd.Timedelta(hours=23)
    trig = (cascade_triggers(close, qvol, R2_CFG["thr"]) & mask).loc[lo:hi]
    W = event_weights_hourly(trig, R2_CFG["H"], w_per=R2_CFG["w_per"], cap=R2_CFG["cap"])
    ev = trig.stack()
    ev = ev[ev]
    active = sorted(set(trig.columns[trig.to_numpy().any(axis=0)]) | {"BTCUSDT", "ETHUSDT"})
    SYMS_FILE.write_text("\n".join(active) + "\n")
    OUT.mkdir(parents=True, exist_ok=True)
    events = [{"ts": str(t), "symbol": s} for t, s in ev.index]
    days = sorted({(s, str(t.normalize().date())) for t, s in ev.index})
    EVENTS_FILE.write_text(json.dumps({
        "config": R2_CFG, "dev_window": list(PDEV), "n_events": len(events),
        "n_symbols": len(active) , "n_event_symbol_days": len(days),
        "n_bars_with_position": int((W.sum(axis=1) > 0).sum()),
        "events": events, "event_symbol_days": [list(d) for d in days]}, indent=1))
    print(f"{len(active)} symbols -> {SYMS_FILE}; {len(events)} events, {len(days)} symbol-days -> {EVENTS_FILE}")


def main_key() -> None:
    gates = json.loads(GATES.read_text())
    if "exec_pf" in gates:
        raise SystemExit("exec_pf already registered")
    gates["exec_pf"] = KEY
    GATES.write_text(json.dumps(gates, indent=1))
    print("gates.json['exec_pf'] written")


def main_inputs() -> None:
    dst = OUT / "inputs"
    dst.mkdir(parents=True, exist_ok=True)
    stamps = {}
    for rel in ("forecasts/predlab_p2_ml/BTCUSDT_1h_T2_dir/logit_lags5.parquet",
                "forecasts/predlab_p2_ml/ETHUSDT_1h_T2_dir/logit_lags5.parquet",
                "rv_1h/BTCUSDT.parquet", "rv_1h/ETHUSDT.parquet", "pp_dev_results.json"):
        src = PREDLAB / rel
        name = rel.replace("/", "__")
        shutil.copyfile(src, dst / name)
        stamps[name] = {"source": str(src), "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                        "bytes": src.stat().st_size}
    (dst / "manifest.json").write_text(json.dumps(stamps, indent=1))
    print(json.dumps(stamps, indent=1))


if __name__ == "__main__":
    {"symbols": main_symbols, "key": main_key, "inputs": main_inputs}[sys.argv[1]]()
