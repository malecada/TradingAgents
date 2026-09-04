"""predlab_oflow P0 floor correction (2026-09-04) — harness defect, disclosed.

The registered XS floor is "|IC| >= 0.02 AND NW-t >= 3 AND right sign in 2/3
sub-periods" under a charter that fixes NO sign ("continuation or reversal
both admissible"; the TS test is two-sided). predlab_oflow_p0.py compared the
SIGNED NW-t with +3, so a reversal cell with NW-t = -7.57 was marked floor-fail.
This script re-derives floor_pass/survive from the UNCHANGED statistics in
p0_result.json using |NW-t|, keeps the original verdict verbatim under
"original_verdict_signbug", and records the corrected verdict in gates.json.
No statistic is recomputed; no data is re-read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.predlab import registry  # noqa: E402

OUT = ROOT / "data" / "predlab" / "oflow"
KEY = "predlab_oflow"
FLOOR = {"ts_p": 0.01, "ts_years": 3, "xs_abs_ic": 0.02, "xs_nw_t": 3.0, "xs_subperiods": 2}


def main() -> None:
    p = OUT / "p0_result.json"
    res = json.loads(p.read_text())
    if "original_verdict_signbug" in res:
        raise SystemExit("already corrected")
    res["original_verdict_signbug"] = res["verdict"]
    fdr = set(res["fdr_rejected"])
    survivors = []
    for k, r in res["cells"].items():
        if k.startswith("TS"):
            floor_ok = r["p"] < FLOOR["ts_p"] and r["n_year_agree"] >= FLOOR["ts_years"]
        else:
            floor_ok = (abs(r["mean_ic"]) >= FLOOR["xs_abs_ic"] and abs(r["nw_t"]) >= FLOOR["xs_nw_t"]
                        and r["n_sub_right_sign"] >= FLOOR["xs_subperiods"])
        r["floor_pass_original_signed"] = r["floor_pass"]
        r["floor_pass"] = bool(floor_ok)
        r["survive"] = bool(floor_ok and k in fdr)
        if r["survive"]:
            survivors.append(k)
    res["survivors"] = survivors
    res["verdict"] = (f"P0 {len(survivors)}/8 survive BH-FDR q<0.10 + floors (|NW-t| per charter, corrected): {survivors}"
                      if survivors else "FAIL at P0 — 0/8 (corrected floors); family CLOSED")
    res["correction"] = {"utc": "2026-09-04", "what": "XS floor used signed NW-t >= 3; charter fixes no sign; corrected to |NW-t| >= 3",
                         "statistics_recomputed": False}
    p.write_text(json.dumps(res, indent=1, default=str))
    gates = registry.load_gates()
    gates[KEY]["verdicts"]["P0_original_signbug"] = gates[KEY]["verdicts"]["P0"]
    gates[KEY]["verdicts"]["P0"] = res["verdict"]
    gates[KEY]["verdicts"]["P0_correction_note"] = res["correction"]["what"]
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(res["verdict"])
    for k in survivors:
        r = res["cells"][k]
        print(f"  {k}: IC {r['mean_ic']:+.4f} NW-t {r['nw_t']:+.2f} subs {r['n_sub_right_sign']}/3")


if __name__ == "__main__":
    main()
