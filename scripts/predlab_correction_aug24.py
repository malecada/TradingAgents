"""engine_correction_2026-08-24 — corrected recomputes of the frozen configs.

Registered in gates.json (engine_correction_2026-08-24) BEFORE this ran.
Recomputes, under simple-return position PnL, the headline numbers the
log-return defect superseded, on the exact frozen configs and windows:

  1. Phase-P S1 (park_5 eq_h1) dev + spent-holdout net SR (raw book)
  2. Phase-O final champion (ewma_20 + vt15_naive20_b100): FULL, D, V
     (+ old champion park_5 + vt10 for the record)
  3. Bybit r1 verbatim replication (raw + ovl)

No selection happens here — one evaluation per frozen config. The holdout
recompute is a corrected recording of the already-spent one-shot, not a
new peek. Placebos are not recomputed: the corrected SRs are negative, so
there is no positive claim to protect. Original verdict/result files are
left untouched; this writes data/predlab/correction_aug24_results.json and
one ledger row per item (experiment=engine_correction_2026-08-24).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, pp, registry  # noqa: E402
from tradingagents.predlab.pp import ANN_DAYS, TAKER_BP, ann_sr, max_drawdown  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT = DATA_ROOT / "predlab" / "correction_aug24_results.json"

DEV = ("2021-01-01", "2025-03-31")
HOLDOUT = ("2025-04-01", "2026-07-01")
FULL = ("2021-01-01", "2026-07-01")
EXP = "engine_correction_2026-08-24"


def overlay_o4(base: pd.DataFrame, breadth: pd.Series, target: float = 0.15,
               cap: float = 2.0, breadth_floor: int = 100) -> pd.Series:
    net = base["net"]
    sh = net.rolling(20).std().shift(1) * np.sqrt(ANN_DAYS)
    s = (target / sh).clip(0.0, cap).fillna(0.0)
    s = s.where(breadth >= breadth_floor, 0.0)
    cost = TAKER_BP / 1e4 * (s * base["turnover"] + s.diff().abs().fillna(0.0) * 2.0)
    return s * net - cost


def metrics(net: pd.Series) -> dict:
    a = net.dropna()
    if not len(a):
        return {"sr": None, "n_days": 0}
    return {"sr": round(ann_sr(a.to_numpy()), 4),
            "maxdd": round(max_drawdown(a.to_numpy()), 4),
            "mean_bp_day": round(float(a.mean()) * 1e4, 2),
            "n_days": int(len(a))}


def main() -> None:
    results: dict = {
        "correction": EXP,
        "ret_convention": "close.pct_change(fill_method=None)",
        "note": "corrected recompute of frozen configs; supersedes "
                "pp_dev_results.json / pp_holdout_verdicts.json / "
                "champion chain dev_metrics / bybit_r1_result.json headline SRs",
    }

    # ---- 1. Phase-P S1 (park_5 eq_h1), Binance ----------------------------
    # pp_holdout.inputs clips at the holdout end (pp_dev clips at dev end,
    # which would leave the holdout window empty); dev metrics are identical
    # on the longer panel because the dev window rows are the same.
    from predlab_pp_holdout import inputs as s1_inputs  # corrected ret inside
    sig, ret, uni, fund = s1_inputs()
    dev = pp.run_s1(sig, ret, uni, fund, "eq", 1, *DEV)
    hold = pp.run_s1(sig, ret, uni, fund, "eq", 1, *HOLDOUT)
    results["pp_s1_eq_h1"] = {
        "original": {"dev_sr_net": 1.483, "holdout_sr_net": 2.198,
                     "verdict": "PASS (VOID)"},
        "corrected": {
            "dev": {"sr_net": round(dev["sr_net"], 4),
                    "sr_gross": round(dev["sr_gross"], 4),
                    "maxdd": round(dev["maxdd"], 4)},
            "holdout": {"sr_net": round(hold["sr_net"], 4),
                        "sr_gross": round(hold["sr_gross"], 4),
                        "maxdd": round(hold["maxdd"], 4),
                        "n_days": hold["n_days"]},
        },
    }
    registry.log_trial(EXP, "S1_t7_lowvol_ls", "s1_eq_h1_corrected",
                       {"weighting": "eq", "smooth": 1, "correction": EXP},
                       DEV, {"sr_net_dev": dev["sr_net"],
                             "sr_net_holdout": hold["sr_net"],
                             "supersedes": "predlab_pp dev+holdout"})
    print(f"S1 eq_h1 corrected: dev {dev['sr_net']:+.3f} "
          f"(was +1.483) | holdout {hold['sr_net']:+.3f} (was +2.198)",
          flush=True)

    # ---- 2. Phase-O champion, Binance --------------------------------------
    from predlab_opt_o1 import inputs  # corrected ret inside
    close, park, ret2, uni2, fund2 = inputs()
    cfg = opt.OptConfig()
    sig_ch = opt.build_signal(park, close, "ewma_20")
    raw = opt.run_ls(sig_ch, ret2, uni2, fund2, cfg, *FULL)
    base = raw["rets"]
    breadth = (~sig_ch.where(uni2).isna()).sum(axis=1).reindex(base.index)
    ovl = overlay_o4(base, breadth)
    results["opt_final_champion"] = {
        "original": {"ovl_sr_full": 1.892, "ovl_maxdd": 0.176,
                     "raw_sr_full": 1.928},
        "corrected": {
            "raw_full": {"sr_net": round(raw["sr_net"], 4),
                         "sr_gross": round(raw["sr_gross"], 4),
                         "maxdd": round(raw["maxdd"], 4)},
            "ovl_full": metrics(ovl),
            "ovl_D": metrics(ovl[(ovl.index >= pd.Timestamp(DEV[0], tz="UTC"))
                                 & (ovl.index <= pd.Timestamp(DEV[1], tz="UTC"))]),
            "ovl_V": metrics(ovl[(ovl.index >= pd.Timestamp(HOLDOUT[0], tz="UTC"))
                                 & (ovl.index <= pd.Timestamp(HOLDOUT[1], tz="UTC"))]),
        },
    }
    registry.log_trial(EXP, "opt_final_champion", "ewma20_vt15b100_corrected",
                       {"signal": "ewma_20", "overlay": "vt15_naive20_b100",
                        "correction": EXP},
                       FULL, {"sr_net_raw": raw["sr_net"],
                              "sr_net_ovl": results["opt_final_champion"]
                              ["corrected"]["ovl_full"]["sr"],
                              "supersedes": "opt_champion_chain seq 1-3"})
    print(f"champion corrected: raw {raw['sr_net']:+.3f} (was +1.928) | "
          f"ovl {results['opt_final_champion']['corrected']['ovl_full']['sr']:+.3f}"
          f" (was +1.892)", flush=True)

    # ---- 3. Bybit r1 verbatim ----------------------------------------------
    from predlab_bybit_r1 import build_panels, build_funding
    panels_b = build_panels()
    close_b, qv_b, park_b = panels_b["close"], panels_b["qv"], panels_b["park"]
    ret_b = close_b.pct_change(fill_method=None)
    uni_b = opt.monthly_universe(qv_b, top_n=200)
    fund_b = build_funding(ret_b.index, sorted(uni_b.columns[uni_b.any(axis=0)]))
    sig_b = opt.build_signal(park_b, close_b, "ewma_20")
    raw_b = opt.run_ls(sig_b, ret_b, uni_b, fund_b, cfg, *FULL)
    base_b = raw_b["rets"]
    breadth_b = (~sig_b.where(uni_b).isna()).sum(axis=1).reindex(base_b.index)
    ovl_b = overlay_o4(base_b, breadth_b)
    results["bybit_r1"] = {
        "original": {"raw_sr": 1.941, "ovl_sr": 1.712, "verdict": "PASS (VOID)"},
        "corrected": {"raw": {"sr_net": round(raw_b["sr_net"], 4),
                              "maxdd": round(raw_b["maxdd"], 4)},
                      "ovl": metrics(ovl_b)},
    }
    registry.log_trial(EXP, "bybit_r1", "ewma20_vt15b100_bybit_corrected",
                       {"venue": "bybit", "correction": EXP},
                       FULL, {"sr_net_raw": raw_b["sr_net"],
                              "sr_net_ovl": results["bybit_r1"]["corrected"]
                              ["ovl"]["sr"],
                              "supersedes": "predlab_bybit_r1 verdict"})
    print(f"bybit corrected: raw {raw_b['sr_net']:+.3f} (was +1.941) | "
          f"ovl {results['bybit_r1']['corrected']['ovl']['sr']:+.3f}"
          f" (was +1.712)", flush=True)

    OUT.write_text(json.dumps(results, indent=1, default=float))
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
