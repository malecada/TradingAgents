"""combo_c1 registration (charter docs/superpowers/specs/2026-09-02-combo-c1-charter.md).

  python scripts/combo_c1_register.py key   # write gates.json["combo_c1"] (refuses if present)
  python scripts/combo_c1_register.py dev   # dev sleeves -> pins, weights, corr, dev-combined SR

`dev` builds the four sleeves on the dev window with the fixed engines,
checks P0 parity against the parents' pins (1e-6), computes the W1/W2
weights, the 4x4 correlation matrix and the dev combined SR, and writes them
under gates.json["combo_c1"]["registered_dev"] plus
data/rebuild/combo_c1/register.json and dev_sleeves.parquet. One ledger row
(experiment combo_c1, window dev) is appended per weight variant. The
holdout is never loaded here: every store read is truncated at 2025-03-31
(hourly panel 2025-03-31 23:00) before any computation.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.rebuild.ledger import log_trial  # noqa: E402
from tradingagents.xsect.combo import (  # noqa: E402
    align_sleeves, combine, equal_weights, inverse_vol_weights, maxdd_simple, sharpe,
    sleeve_contributions,
)
from tradingagents.xsect.combo_sleeves import (  # noqa: E402
    CFG, SLEEVE_IDS, build_carry, build_liq_fade, build_momentum, build_value,
    load_cm_mapping, load_hourly_panel, sleeve_net,
)
from tradingagents.xsect.universe import load_klines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "data/rebuild/gates.json"
OUT = ROOT / "data/rebuild/combo_c1"
KL = ROOT / "data/xsect/klines"
KL1H = ROOT / "data/xsect/klines_1h"
FUND = ROOT / "data/xsect/funding"
CM_FUND = ROOT / "data/xsect/fundamentals"
CM_UNIV = ROOT / "data/xsect/fundamentals_universe.json"
LIQ_UNIV = ROOT / "data/xsect/liq_fade_universe.json"
LIQ_SYMS = ROOT / "data/xsect/liq_fade_symbols.txt"
VAL_UNIV = ROOT / "data/xsect/value_xs_universe.json"
FORENSIC = Path("/home/malecada/master_thesis/data/audit_2026-09-02/convswap_results.json")

DEV = ("2021-01-01", "2025-03-31")
HOLDOUT = ("2025-04-01", "2026-07-01")
WARMUP_1H = "2020-06-01"
WARMUP_VAL = "2020-06-01"
PIN_TOL = 1e-6

KEY = {
    "registered": "2026-09-02",
    "spec": "docs/superpowers/specs/2026-09-02-combo-c1-charter.md",
    "source": "LEADS_SCOPE_2026-09-02.md Lead 1; AUDIT_RESEARCH_PROGRAM_2026-09-02.md section 4.1 / 6 item 1",
    "hypothesis": "four dev-selected placebo-clearing thin-edge sleeves, frozen as their parents selected them and priced under simple returns, combined by a pre-declared inverse-vol capital rule, earn a positive net Sharpe on the sealed window none of them touched",
    "dev_window": list(DEV),
    "holdout_window": list(HOLDOUT),
    "holdout_class": "H1 virgin (none of S1-S4 ever evaluated on it); ONE evaluation; verdict-file lock",
    "sleeves": {
        "liq_fade": {"parent": "liq_fade_i1", "thesis": 49, "config": CFG["liq_fade"],
                     "pin_source": "data/rebuild/liq_fade/dev_results.json (thr 3.5, H 48)"},
        "carry": {"parent": "carry_xs_t1", "thesis": 46, "config": CFG["carry"],
                  "pin_source": "Sep-2 forensic convswap_results.json carry L30 leg0.2 simple"},
        "momentum": {"parent": "xs_mom_p1", "thesis": 43, "config": CFG["momentum"],
                     "pin_source": "Sep-2 forensic convswap_results.json xs_mom L28 s0 K10 simple"},
        "value": {"parent": "value_xs_t1", "thesis": 51, "config": {**CFG["value"], "leg_frac": "1/3"},
                  "pin_source": "data/rebuild/value_xs/grid.json nvt_proxy tercile"},
    },
    "returns": "simple at every PnL step (lead-0 fixed engines); log only for the convention-swap kill-test",
    "costs": "10 bp/side on |dW| inside each sleeve engine; rf 4.5%/yr on full allocated capital inside S1, S2, S4 (S3 fully invested, none); cost-stress 2x reported",
    "weight_rule": {
        "W1_primary": "w_i ~ 1/sd_i, sd_i = dev daily SD (ddof 1) of the ALIGNED (zero-filled) sleeve net return; sum w = 1; no leverage",
        "W2_sensitivity": "0.25 each; reported not gated",
        "book": "constant-mix of fixed capital weights on daily sleeve net returns; no cross-sleeve rebalancing cost (deployment contract)",
    },
    "alignment": "calendar days of the window; a day a sleeve does not cover contributes 0.0; each sleeve series starts the bar after its first decision (parents' convention)",
    "probes": {
        "P0": "engine parity: each dev sleeve series reproduces its parent pin to 1e-6; else STOP (harness)",
        "P1": "coverage: stores span holdout to 2026-07-01; S2/S3 PIT eligibility >= 20 at every rebalance, S1 universe >= 20 monthly, S4 signal-valid weekly breadth median >= 20; fundamentals_h1 vs sealed-store restatement on the overlap reported; else STOP (data)",
        "P2": "leakage canary: W.shift(-1) (today's weights use tomorrow's decision) raises each sleeve's dev SR by >= +1.0; else STOP (harness cannot see leakage)",
        "P3": "dev pairwise |rho| <= 0.6 for all pairs; else disclosed, W1 unchanged",
    },
    "gates_holdout": {
        "sr_ratio_min": 0.5, "sr_abs_min": 0.5, "same_sign": True,
        "placebo": "dual family on WEIGHT PATHS, 500 draws each, costs+rf re-applied by the sleeve engines, p=(1+#{placebo SR >= real})/(N+1), gate on WORSE family; A = per-column independent circular shift within every sleeve (min 30 d / 720 bars, seeds 0..499); B = one shared day offset for every sleeve and column (x24 hourly; seeds 0..499)",
        "placebo_p_max": 0.10,
        "sleeve_contribution_min": 0.0,
        "maxdd_max": 0.25,
        "maxdd_basis": "compounded simple returns",
        "top_name_share_max": 0.5,
        "top_name_share_basis": "pooled gross per-symbol PnL across sleeves; max|pnl| / sum|pnl|",
        "convention_swap": "log returns at every PnL step must not flip gates 1-2",
        "all_required": True,
    },
    "reported_not_gated": ["W2 book on all gates", "2x cost stress", "per-sleeve holdout SR", "two-halves SR",
                            "DSR at n_trials 1 / family 28 / cumulative ledger"],
    "multiplicity": {"n_trials": 1, "rationale": "frozen book, virgin data, one evaluation; family (28) and cumulative denominators reported"},
    "stop_rule": "FAIL on any gate => thin-edge stratum closed as a combination; no re-weighting, no sleeve dropping, no second look; H1 SPENT for S1-S4. PASS => stop-and-decide (paper journal from F window); deployment is the user's decision",
    "data_deviation": "fundamentals store sealed at 2025-04-15; separate vintage data/xsect/fundamentals_h1 (pulled 2026-09-02, own manifest/vintage) serves S4 on the holdout; PIT caveat = vendor restatement only, measured in P1",
    "mechanics": "branch feature/combo-c1 (off feature/llm-event-xs); tradingagents/xsect/combo.py + combo_sleeves.py; scripts/combo_c1_{data,register,probes,holdout}.py; ledger experiment combo_c1; THESIS section 76",
    "thesis_section": "76",
}


def _pins() -> dict:
    liq = json.loads((ROOT / "data/rebuild/liq_fade/dev_results.json").read_text())
    liq_pin = next(r["metrics"]["net_sr"] for r in liq["results"]
                   if r["config"]["thr"] == 3.5 and r["config"]["H"] == 48)
    val = json.loads((ROOT / "data/rebuild/value_xs/grid.json").read_text())
    val_pin = next(r["metrics"]["net_sr"] for r in val["results"]
                   if r["config"]["metric"] == "nvt_proxy" and r["config"]["breadth"] == "tercile")
    f = json.loads(FORENSIC.read_text())
    mom_pin = next(c["simple"]["sr"] for c in f["xs_mom_p1"]["configs"]
                   if (c["L"], c["skip"], c["K"]) == (28, 0, 10))
    car_pin = next(c["simple"]["sr"] for c in f["carry_xs_t1"]["configs"]
                   if (c["L"], c["leg_frac"]) == (30, 0.2))
    return {"liq_fade": liq_pin, "carry": car_pin, "momentum": mom_pin, "value": val_pin}


def build_dev_sleeves(t0: float) -> dict:
    lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")
    klines = load_klines(KL)
    klines_dev = {s: d.loc[:hi] for s, d in klines.items()}
    print(f"[{time.time()-t0:6.1f}s] klines {len(klines)} symbols (truncated at {DEV[1]})", flush=True)
    sleeves = {}
    sleeves["momentum"] = build_momentum(klines_dev, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] momentum built", flush=True)
    sleeves["carry"] = build_carry(klines_dev, FUND, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] carry built", flush=True)
    sleeves["value"] = build_value(klines_dev, CM_FUND, load_cm_mapping(CM_UNIV),
                                   json.loads(VAL_UNIV.read_text()), WARMUP_VAL, lo, hi)
    print(f"[{time.time()-t0:6.1f}s] value built", flush=True)
    syms = [s.strip() for s in LIQ_SYMS.read_text().splitlines() if s.strip()]
    close, qvol = load_hourly_panel(KL1H, syms, pd.Timestamp(WARMUP_1H, tz="UTC"),
                                    hi + pd.Timedelta(hours=23))
    sleeves["liq_fade"] = build_liq_fade(close, qvol, json.loads(LIQ_UNIV.read_text()), lo, hi)
    print(f"[{time.time()-t0:6.1f}s] liq_fade built ({sleeves['liq_fade'].meta})", flush=True)
    return sleeves


def main_dev() -> None:
    t0 = time.time()
    gates = json.loads(GATES.read_text())
    assert "combo_c1" in gates, "run `key` first"
    if "registered_dev" in gates["combo_c1"]:
        raise SystemExit("registered_dev already present — registration is one-shot")
    sleeves = build_dev_sleeves(t0)
    pins = _pins()
    series = {sid: sleeve_net(sleeves[sid]) for sid in SLEEVE_IDS}
    parity = {}
    for sid in SLEEVE_IDS:
        got = sharpe(series[sid])
        parity[sid] = {"pin": pins[sid], "got": got, "abs_diff": abs(got - pins[sid]),
                       "ok": bool(abs(got - pins[sid]) <= PIN_TOL), "n_days": int(len(series[sid]))}
        print(f"P0 {sid:9s} pin {pins[sid]:+.6f} got {got:+.6f} {'OK' if parity[sid]['ok'] else 'FAIL'}")
    p0_ok = all(v["ok"] for v in parity.values())

    idx = pd.date_range(DEV[0], DEV[1], freq="D", tz="UTC")
    dev = align_sleeves(series, idx)
    w1 = inverse_vol_weights(dev)
    w2 = equal_weights(dev.columns)
    corr = dev.corr()
    out = {"parity": parity, "p0_pass": p0_ok,
           "dev_sd_daily": {c: float(dev[c].std(ddof=1)) for c in dev.columns},
           "dev_sleeve_sr_aligned": {c: sharpe(dev[c]) for c in dev.columns},
           "weights_W1": w1, "weights_W2": w2,
           "corr_dev": {a: {b: float(corr.loc[a, b]) for b in corr.columns} for a in corr.index},
           "max_abs_offdiag_corr": float(np.max(np.abs(corr.to_numpy() - np.eye(len(corr))))),
           "combined": {}}
    for name, w in (("W1", w1), ("W2", w2)):
        c = combine(dev, w)
        halves = np.array_split(np.arange(len(c)), 2)
        m = {"sr": sharpe(c), "maxdd": maxdd_simple(c), "mean_bp_day": float(c.mean() * 1e4),
             "contrib": sleeve_contributions(dev, w),
             "sr_halves": [sharpe(c.iloc[h]) for h in halves], "n_days": int(len(c))}
        out["combined"][name] = m
        print(f"dev {name}: SR {m['sr']:+.4f} maxdd {m['maxdd']:.3f} halves {m['sr_halves']}")
        log_trial("combo_c1", {"variant": name, "weights": w, "sleeves": {k: CFG[k] for k in SLEEVE_IDS},
                               "window_role": "dev-reference"}, DEV,
                  {"net_sr": m["sr"], "maxdd": m["maxdd"], "n_days": m["n_days"]})
    OUT.mkdir(parents=True, exist_ok=True)
    dev.to_parquet(OUT / "dev_sleeves.parquet")
    for sid in SLEEVE_IDS:
        sleeves[sid].W.to_parquet(OUT / f"dev_W_{sid}.parquet")
    out["runtime_sec"] = time.time() - t0
    (OUT / "register.json").write_text(json.dumps(out, indent=1))
    gates["combo_c1"]["registered_dev"] = {
        "computed": pd.Timestamp.utcnow().isoformat(),
        "p0_pass": p0_ok, "weights_W1": w1, "weights_W2": w2,
        "dev_sd_daily": out["dev_sd_daily"], "corr_dev": out["corr_dev"],
        "dev_sr_W1": out["combined"]["W1"]["sr"], "dev_sr_W2": out["combined"]["W2"]["sr"],
        "holdout_sr_min_W1": max(0.5 * out["combined"]["W1"]["sr"], 0.5),
    }
    GATES.write_text(json.dumps(gates, indent=1))
    print(f"registered_dev written; holdout floor SR_H >= {gates['combo_c1']['registered_dev']['holdout_sr_min_W1']:.4f}")
    if not p0_ok:
        raise SystemExit("P0 parity FAILED — STOP (harness)")


def main_key() -> None:
    gates = json.loads(GATES.read_text())
    if "combo_c1" in gates:
        raise SystemExit("combo_c1 already registered")
    gates["combo_c1"] = KEY
    GATES.write_text(json.dumps(gates, indent=1))
    print("gates.json['combo_c1'] written")


if __name__ == "__main__":
    {"key": main_key, "dev": main_dev}[sys.argv[1]]()
