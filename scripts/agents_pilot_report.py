"""Pilot validity report (Charter 1 §4): schema/call failures, order-swap consistency, repeat agreement,
measured cost per asset-week. Reads data/agents_v2/runs (and an optional repeat directory).
Usage: agents_pilot_report.py [--runs data/agents_v2/runs] [--repeat data/agents_v2/runs_repeat]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load(runs: Path) -> pd.DataFrame:
    rows = []
    for day in sorted(p for p in runs.iterdir() if p.is_dir()):
        for f in day.glob("*.json"):
            if f.name.startswith("_"):
                continue
            r = json.loads(f.read_text())
            d = r.get("debates") or {}
            rows.append({"friday": day.name, "symbol": f.stem, "p": r.get("p_outperform"), "conf": r.get("confidence"),
                         "abstain": r.get("abstain"), "debated": r.get("debated", False),
                         "failed": bool(r.get("failed") or r.get("debate_failed")),
                         "p_bull_first": (d.get("bull_first") or {}).get("judge", {}).get("p_outperform_7d"),
                         "p_bear_first": (d.get("bear_first") or {}).get("judge", {}).get("p_outperform_7d"),
                         "cost": sum(m.get("cost", 0.0) for m in r.get("meta", [])),
                         "calls": len(r.get("meta", []))})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="data/agents_v2/runs")
    ap.add_argument("--repeat", default=None)
    args = ap.parse_args()
    df = load(Path(args.runs))
    if df.empty:
        print("no runs")
        return 1
    deb = df.dropna(subset=["p_bull_first", "p_bear_first"])
    report = {
        "asset_weeks": int(len(df)), "weeks": int(df["friday"].nunique()),
        "failed_share": float(df["failed"].mean()),
        "debated": int(df["debated"].sum()),
        "order_swap_spearman": float(deb["p_bull_first"].corr(deb["p_bear_first"], method="spearman")) if len(deb) > 3 else None,
        "order_swap_mean_abs_gap": float((deb["p_bull_first"] - deb["p_bear_first"]).abs().mean()) if len(deb) else None,
        "abstain_share": float(df["abstain"].fillna(False).mean()),
        "p_mean": float(df["p"].dropna().mean()) if df["p"].notna().any() else None,
        "p_std": float(df["p"].dropna().std()) if df["p"].notna().any() else None,
        "cost_per_asset_week_usd": float(df["cost"].sum() / max(1, len(df))),
        "cost_per_debated_asset_usd": float(df[df["debated"]]["cost"].mean()) if df["debated"].any() else None,
        "calls_per_asset_week": float(df["calls"].mean()),
        "total_cost_usd": float(df["cost"].sum()),
    }
    if args.repeat and Path(args.repeat).exists():
        rep = load(Path(args.repeat))
        m = df.merge(rep, on=["friday", "symbol"], suffixes=("", "_rep")).dropna(subset=["p", "p_rep"])
        report["repeat_n"] = int(len(m))
        report["repeat_spearman"] = float(m["p"].corr(m["p_rep"], method="spearman")) if len(m) > 3 else None
        report["repeat_mean_abs_gap"] = float((m["p"] - m["p_rep"]).abs().mean()) if len(m) else None
    Path("data/agents_v2/pilot_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
