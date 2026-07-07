#!/usr/bin/env python
"""Flip-rate stability metric between two prediction runs (Experiment E2).

Reproduces the vintage/PIT audit's "PURE CONFIG" measurement (see
THESIS_FINDINGS.md / project_backtest_vintage_pit_audit memory): given two
walk-forward prediction directories with the same schema
(`preds_lgb_h{h}.csv` — columns `date`, `coin_id`, `prediction`, `actual`,
`ref_price`, optionally extra diagnostic columns), compute the share of
common (date, coin_id) rows where the trading DIRECTION implied by the
prediction — sign(prediction - ref_price) — differs between run A and run B.

Direction = sign(prediction - ref_price). Ties (prediction == ref_price) yield
direction 0 and count as a flip against any nonzero direction — deliberate:
a tie is a changed signal for the V5 term-structure consumer.

This is used to compare a baseline single-model walk-forward run against a
training-window-staggered ensemble run (`--train-end-offsets`), typically
with the whole evaluation grid shifted by ~21 days between the two runs
(matching the audit's 3-week training-window-shift measurement), to test
whether the ensemble reduces signal flips.

Usage:
    python scripts/exp_flip_rate.py \\
        --dir-a data/multi_2coins_walkforward \\
        --dir-b data/multi_2coins_walkforward_shift21 \\
        --out data/flip_rate_baseline_vs_shift21.json

    # Restrict to specific horizons (default: auto-detect common horizons)
    python scripts/exp_flip_rate.py --dir-a A --dir-b B --horizons 7 14 --out out.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

_PRED_FILE_RE = re.compile(r"^preds_lgb_h(\d+)\.csv$")


def discover_common_horizons(dir_a: Path, dir_b: Path) -> list[int]:
    """Find horizons with a `preds_lgb_h{h}.csv` file present in both dirs."""

    def horizons_in(d: Path) -> set[int]:
        out = set()
        for f in d.glob("preds_lgb_h*.csv"):
            m = _PRED_FILE_RE.match(f.name)
            if m:
                out.add(int(m.group(1)))
        return out

    return sorted(horizons_in(dir_a) & horizons_in(dir_b))


def _pred_direction(df: pd.DataFrame) -> pd.Series:
    """sign(prediction - ref_price) — the trading direction implied by a row.

    Returns 1 for up (prediction > ref_price), -1 for down (prediction < ref_price),
    and 0 for ties (prediction == ref_price). Ties carry direction 0 and will always
    count as flips against any nonzero direction — deliberate: a tie is a changed
    signal for the V5 term-structure consumer.
    """
    return np.sign(df["prediction"] - df["ref_price"])


def flip_rate_for_pair(df_a: pd.DataFrame, df_b: pd.DataFrame) -> tuple[int, int, float]:
    """Compute flip count/rate for two prediction frames (same horizon).

    Both frames must have `date`, `coin_id`, `prediction`, `ref_price` columns.
    Rows are matched on (date, coin_id); rows only present in one side are
    dropped (not "common"). Direction = sign(prediction - ref_price) ∈ {-1, 0, 1};
    a row "flips" when direction differs between A and B.

    Ties (prediction == ref_price) carry direction 0 and count as a flip against
    any nonzero direction — deliberate: a tie is a changed signal for the V5
    term-structure consumer.

    Returns:
        (n_common, n_flips, flip_rate). flip_rate is 0.0 when n_common == 0.
    """
    a = df_a.copy()
    b = df_b.copy()
    a["date"] = pd.to_datetime(a["date"])
    b["date"] = pd.to_datetime(b["date"])

    a["_dir"] = _pred_direction(a)
    b["_dir"] = _pred_direction(b)

    merged = a[["date", "coin_id", "_dir"]].merge(
        b[["date", "coin_id", "_dir"]],
        on=["date", "coin_id"],
        how="inner",
        suffixes=("_a", "_b"),
    )

    n_common = int(len(merged))
    if n_common == 0:
        return 0, 0, 0.0

    flips = merged["_dir_a"] != merged["_dir_b"]
    n_flips = int(flips.sum())
    return n_common, n_flips, n_flips / n_common


def compute_flip_rates(
    dir_a: Path, dir_b: Path, horizons: list[int] | None = None,
) -> dict:
    """Compute per-horizon and overall flip rates between two prediction dirs.

    Returns a dict:
        {
          "horizons": {h: {"n_common": int, "n_flips": int, "flip_rate": float}, ...},
          "overall": {"n_common": int, "n_flips": int, "flip_rate": float},
        }
    """
    if horizons is None:
        horizons = discover_common_horizons(dir_a, dir_b)

    per_horizon = {}
    total_common = 0
    total_flips = 0
    for h in horizons:
        path_a = dir_a / f"preds_lgb_h{h}.csv"
        path_b = dir_b / f"preds_lgb_h{h}.csv"
        if not path_a.exists() or not path_b.exists():
            continue
        df_a = pd.read_csv(path_a)
        df_b = pd.read_csv(path_b)
        n_common, n_flips, flip_rate = flip_rate_for_pair(df_a, df_b)
        per_horizon[h] = {
            "n_common": n_common,
            "n_flips": n_flips,
            "flip_rate": flip_rate,
        }
        total_common += n_common
        total_flips += n_flips

    overall_rate = (total_flips / total_common) if total_common > 0 else 0.0
    return {
        "horizons": per_horizon,
        "overall": {
            "n_common": total_common,
            "n_flips": total_flips,
            "flip_rate": overall_rate,
        },
    }


def print_table(result: dict, dir_a: Path, dir_b: Path) -> None:
    print(f"\n{'='*60}\n  Signal flip-rate: {dir_a} vs {dir_b}\n{'='*60}")
    print(f"{'horizon':>8}  {'n_common':>10}  {'n_flips':>10}  {'flip_rate':>10}")
    for h in sorted(result["horizons"].keys()):
        r = result["horizons"][h]
        print(f"{h:>8}  {r['n_common']:>10}  {r['n_flips']:>10}  {r['flip_rate']:>10.2%}")
    o = result["overall"]
    print(f"{'-'*8}  {'-'*10}  {'-'*10}  {'-'*10}")
    print(f"{'overall':>8}  {o['n_common']:>10}  {o['n_flips']:>10}  {o['flip_rate']:>10.2%}")


def parse_args():
    p = argparse.ArgumentParser(
        description="Signal flip-rate stability metric between two LGB "
                     "walk-forward prediction directories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dir-a", required=True, type=Path,
                   help="First prediction directory (e.g. baseline run).")
    p.add_argument("--dir-b", required=True, type=Path,
                   help="Second prediction directory (e.g. ensemble or "
                        "training-window-shifted run).")
    p.add_argument("--horizons", nargs="+", type=int, default=None,
                   help="Horizons to compare. Default: auto-detect horizons "
                        "with a preds_lgb_h{h}.csv present in both dirs.")
    p.add_argument("--out", required=True, type=Path,
                   help="Output JSON path for the flip-rate result.")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.dir_a.exists():
        print(f"ERROR: --dir-a does not exist: {args.dir_a}")
        sys.exit(1)
    if not args.dir_b.exists():
        print(f"ERROR: --dir-b does not exist: {args.dir_b}")
        sys.exit(1)

    result = compute_flip_rates(args.dir_a, args.dir_b, args.horizons)

    if not result["horizons"]:
        print("ERROR: no common preds_lgb_h{h}.csv horizons found between "
              f"{args.dir_a} and {args.dir_b}")
        sys.exit(1)

    print_table(result, args.dir_a, args.dir_b)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dir_a": str(args.dir_a),
        "dir_b": str(args.dir_b),
        **result,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nJSON -> {args.out}")


if __name__ == "__main__":
    main()
