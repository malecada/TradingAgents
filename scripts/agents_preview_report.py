"""Descriptive preview of agent-run weeks (NOT a gate computation): per-week rank IC of every panel against
realized 7-day forward returns, Brier, rule-twin book returns with costs and funding, encompassing coefficients,
interpreter weights, paired debate shift and citation validity. Reads a runs directory written by run_week.
Usage: agents_preview_report.py --runs data/agents_v2/runs/charter1-preview --dossiers data/dossier/dossiers_v26 [--out report.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.agents_v2.evaluate import brier, encompassing, residualize  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import book_returns, realized_funding  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402

PANELS = ["p_quant", "p_judge_nd", "p_hybrid_nd", "p_outperform", "p_analyst_mean"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--dossiers", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    runs = Path(args.runs)
    rows, weights = [], {}
    for day in sorted(p for p in runs.iterdir() if p.is_dir()):
        f = pd.Timestamp(day.name, tz="UTC")
        pf = day / "_portfolio.json"
        if not pf.exists():
            continue
        weights[f] = json.loads(pf.read_text())["rule_weights"]
        for p in day.glob("*.json"):
            if p.name.startswith("_"):
                continue
            r = json.loads(p.read_text())
            if r.get("failed"):
                continue
            d = json.loads((Path(args.dossiers) / day.name / p.name).read_text())
            cites = [rep for st in r.get("stages", {}).values() for rep in (st.get("citations") or {}).values()]
            rows.append({"date": f, "symbol": r["symbol"], "p_quant": r.get("quant_rank_pct"), "p_judge_nd": r.get("p_judge_nd"),
                         "p_hybrid_nd": r.get("p_hybrid_nd"), "p_outperform": r.get("p_outperform"), "p_judge": r.get("p_judge"),
                         "p_analyst_mean": r.get("p_analyst_mean"), "p_judge_debate": r.get("p_judge_debate"),
                         "weight_on_quant": r.get("weight_on_quant"), "debated": bool(r.get("debated")), "abstain": r.get("abstain"),
                         "cite_exist": np.mean([c["cite_exist_rate"] for c in cites if c.get("cite_exist_rate") is not None]) if cites else np.nan,
                         "num_grounded": np.mean([c["number_grounded_rate"] for c in cites if c.get("number_grounded_rate") is not None]) if cites else np.nan,
                         "vol_ewma20": d["numeric"].get("vol_ewma20_ann_pct"), "ret_4w": d["numeric"].get("ret_4w_pct"),
                         "dvol_30d": d["numeric"].get("volume_rank_pct")})
    panel = pd.DataFrame(rows)
    fridays = sorted(panel["date"].unique())
    fwd = forward_returns(sorted(panel["symbol"].unique()), fridays)
    panel = panel.merge(fwd, on=["date", "symbol"], how="left")
    out = {"weeks": [str(pd.Timestamp(f).date()) for f in fridays], "asset_weeks": int(len(panel)),
           "delisted_rows": int(panel["delisted"].fillna(False).sum()), "per_week": {}, "pooled": {}}
    for f, g in panel.groupby("date"):
        g = g.dropna(subset=["fwd_ret"])
        wk = {"n": int(len(g)), "median_fwd_ret_pct": round(float(g["fwd_ret"].median() * 100), 2)}
        for c in PANELS:
            gg = g.dropna(subset=[c])
            wk[f"ic_{c}"] = round(float(residualize(gg, c).corr(residualize(gg, "fwd_ret"), method="spearman")), 3) if len(gg) >= 10 else None
            wk[f"raw_ic_{c}"] = round(float(gg[c].rank(pct=True).corr(gg["fwd_ret"].rank(pct=True), method="spearman")), 3) if len(gg) >= 10 else None
        wk["weight_on_quant_mean"] = round(float(g["weight_on_quant"].mean()), 3)
        wk["p_judge_nd_mean"] = round(float(g["p_judge_nd"].mean()), 3)
        wk["p_judge_nd_sd"] = round(float(g["p_judge_nd"].std()), 3)
        out["per_week"][str(pd.Timestamp(f).date())] = wk
    pooled = {}
    for c in PANELS:
        ics = [v[f"ic_{c}"] for v in out["per_week"].values() if v.get(f"ic_{c}") is not None]
        pooled[c] = {"ic_mean": round(float(np.mean(ics)), 3) if ics else None, "ic_weeks_positive": int(sum(i > 0 for i in ics)),
                     "brier": brier(panel, c)}
    out["pooled"] = pooled
    out["encompassing_llm_vs_quant"] = encompassing(panel, "p_judge", "p_quant")
    out["encompassing_hybrid_vs_quant"] = encompassing(panel, "p_hybrid_nd", "p_quant")
    paired = panel.dropna(subset=["p_judge_debate", "p_judge_nd"])
    out["debate_paired"] = {"n": int(len(paired)), "mean_abs_shift": round(float((paired["p_judge_debate"] - paired["p_judge_nd"]).abs().mean()), 4),
                            "sd_debate": round(float(paired["p_judge_debate"].std()), 4), "sd_nd": round(float(paired["p_judge_nd"].std()), 4)} if len(paired) else {}
    out["citations"] = {"cite_exist_mean": round(float(panel["cite_exist"].mean()), 3), "number_grounded_mean": round(float(panel["num_grounded"].mean()), 3)}
    funding = realized_funding(sorted(panel["symbol"].unique()), fridays)
    r_book = book_returns(weights, fwd, funding=funding)
    r_nocost = book_returns(weights, fwd, cost_per_side=0.0)
    out["book"] = {"weekly_net_return_pct": {str(k.date()): round(float(v * 100), 3) for k, v in r_book.items()},
                   "weekly_gross_return_pct": {str(k.date()): round(float(v * 100), 3) for k, v in r_nocost.items()},
                   "funding_coverage": round(float(panel.merge(funding, on=["date", "symbol"], how="left")["funding_week"].notna().mean()), 3)}
    text = json.dumps(out, indent=1, default=str)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
