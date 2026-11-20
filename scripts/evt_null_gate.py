"""Noise pass rate and power of the event-time gate before the freeze. No outcome of the test window is read.

The lead events of the gate set keep their asset and time of day but are moved back by 104 weeks, to a time
at which their news did not exist. Minute bars at these moved times give returns with the real distribution,
clustering and drift. Signs are then drawn at random (a permutation of the real sign vector, so the share of
favourable events is kept). Noise rows: share of draws that pass both gates. Power rows: the same with a
planted effect of b basis points per event in the direction of the sign.
Usage: evt_null_gate.py [--draws 2000]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evt_events_build import KLINES, OUT, load_events

from tradingagents.eventtime import study

SHIFT = pd.Timedelta(weeks=104)
PLANTED_BP = (0, 5, 10, 15, 20, 30)
SEED = 20261120


def moved_panel() -> pd.DataFrame:
    gate = study.gate_set(load_events()).copy()
    gate["year"] = gate["t0"].dt.year                       # the year of the real event keeps the two groups of G2
    gate["t0"] = gate["t0"] - SHIFT
    panel = study.event_returns(gate, KLINES)
    return panel[np.isfinite(panel[study.GATE_COLUMN])].reset_index(drop=True)


def pass_rates(panel: pd.DataFrame, draws: int, seed: int = SEED) -> dict:
    ret = panel[study.GATE_COLUMN].to_numpy(dtype=float)
    sign = panel["sign"].to_numpy()
    day, year = panel["t0"].dt.floor("D").to_numpy(), panel["year"].to_numpy()
    rng = np.random.default_rng(seed)
    out = {}
    for bp in PLANTED_BP:
        passed, ts = 0, []
        for _ in range(draws):
            s = rng.permutation(sign)
            r = ret + s * bp * 1e-4
            total = study.slope(r, s, day, year)
            years = [study.slope(r[year == y], s[year == y], day[year == y], year[year == y])["mean"] for y in study.YEARS]
            ts.append(total["t"])
            passed += int(total["t"] >= study.T_MIN and total["mean"] > 0 and all(m is not None and m > 0 for m in years))
        ts = np.array(ts)
        out[str(bp)] = {"pass_rate": passed / draws, "t_mean": float(ts.mean()), "t_sd": float(ts.std()),
                        "share_t_at_least_2": float((ts >= study.T_MIN).mean())}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=2000)
    args = ap.parse_args(argv)
    panel = moved_panel()
    ret = panel[study.GATE_COLUMN]
    result = {"shift_weeks": 104, "draws": args.draws, "seed": SEED, "moved_events_with_return": len(panel),
              "moved_events_by_year_of_real_event": {str(k): int(v) for k, v in panel["year"].value_counts().sort_index().items()},
              "assets": int(panel["base"].nunique()), "days": int(panel["t0"].dt.floor("D").nunique()),
              "share_favourable": float((panel["sign"] > 0).mean()),
              "return_sd_bp": float(1e4 * ret.std()), "return_mean_bp": float(1e4 * ret.mean()),
              "return_abs_q99_bp": float(1e4 * ret.abs().quantile(0.99)),
              "planted_bp": pass_rates(panel, args.draws)}
    (OUT / "null_gate.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
