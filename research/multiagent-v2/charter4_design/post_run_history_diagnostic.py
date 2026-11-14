"""Post-run diagnostic of Charter 4 (not a registered output, no gate, no re-estimation).

Daily Spearman correlation of every single price-history feature with the next-day return on the 722 test
days. The outcome column is the one already written by the registered run into ``forecasts.json``; the
features come from the decision-time panel (``scripts/reader_charter4_null_gate.py panel <path>``). The
question is why the history forecast ``v_hist`` reaches a rank IC of about 0.11 for the next-day return rank.

Usage: python post_run_history_diagnostic.py <forecasts.json> <panel.parquet> <out.json>
"""
import json
import sys

import numpy as np
import pandas as pd

HIST = ["ret_1d", "ret_7d", "ret_30d", "rv_1d", "rv_7d", "rv_30d", "vsurge_1d", "dvol_30d", "beta_60d", "age_weeks", "funding_3d"]


def main(forecasts_path: str, panel_path: str, out_path: str) -> None:
    raw = json.load(open(forecasts_path))
    out = pd.DataFrame(raw["rows"], columns=raw["columns"])[["date", "symbol", "fwd_ret_1d", "v_hist"]]
    out["date"] = pd.to_datetime(out["date"], utc=True)
    panel = pd.read_parquet(panel_path)[["date", "symbol", *HIST]]
    panel["date"] = pd.to_datetime(panel["date"], utc=True)
    frame = out.merge(panel, on=["date", "symbol"], how="left", validate="one_to_one").dropna(subset=["fwd_ret_1d"])
    result = {"rows": int(len(frame)), "days": int(frame["date"].nunique()), "features": {}}
    for name in [*HIST, "v_hist"]:
        daily = frame.groupby("date").apply(lambda day: day[name].corr(day["fwd_ret_1d"], method="spearman"), include_groups=False).dropna()
        year = daily.index.year
        result["features"][name] = {
            "mean": float(daily.mean()),
            "t_iid": float(daily.mean() / daily.std(ddof=1) * np.sqrt(len(daily))),
            "days": int(len(daily)),
            "2023": float(daily[year == 2023].mean()),
            "2024": float(daily[year == 2024].mean()),
        }
    json.dump(result, open(out_path, "w"), indent=1, sort_keys=True)
    for name, row in result["features"].items():
        print(f"{name:12s} mean {row['mean']:+.4f}  t {row['t_iid']:+.2f}  2023 {row['2023']:+.4f}  2024 {row['2024']:+.4f}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
