"""Charter 1 lifecycle runner (one registered experiment): run the v2 agent system over every manifested
dev dossier (resumable through the per-asset cache), then compute the forecast-quality and rule-twin
portfolio gates. Weeks are processed newest first; when the registered spend cap is reached the run stops,
the incomplete week is excluded, and the set of completed weeks is recorded (charter §6a). All inputs are
registered by hash; outputs are written through ResearchRun.
Usage: llm_v2c1_run.py --registration research/llm-v2-charter1-<date>/gates.json --experiment <id> --cost-cap 400
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tradingagents.agents_v2.evaluate import encompassing, evaluate_panel, newey_west_t  # noqa: E402
from tradingagents.agents_v2.graph import config_sha  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import realized_funding, summarize_book  # noqa: E402
from tradingagents.agents_v2.runner import run_week  # noqa: E402
from tradingagents.dossier.or_client import SpendCapError, StructuredClient  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402
from llm_v2c0_client import load_api_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("forecasts.json", "evaluation.json", "portfolio.json", "cost.json")
CELLS = ("agent-run", "forecast-gates", "portfolio-gates", "identified-subsets")


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--cost-cap", type=float, required=True)
    args = ap.parse_args()
    from tradingagents.research import ResearchRun
    client = StructuredClient.pinned("pro", load_api_key(), cost_cap_usd=args.cost_cap)
    with ResearchRun.start(root=ROOT, registration=args.registration, experiment=args.experiment, source=_head()) as run:
        manifest = json.loads(run.read_input("dossier_manifest"))
        cfg = json.loads(run.read_input("agent_config"))
        if cfg["config_sha"] != config_sha():
            raise SystemExit("agent config differs from the registered freeze")
        flags = pd.read_parquet(Path(ROOT) / json.loads(run.read_input("reid_flags_path"))["path"]) if "reid_flags_path" in run.admission.inputs else None
        cards = pd.read_parquet(ROOT / "data/llm_rank_xs/cards.parquet")
        # the kline store (forward-return source) must be the registered one
        klines = json.loads(run.read_input("klines_digest"))
        for path, digest in klines.items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
                raise SystemExit(f"kline store changed since freeze: {path}")
        # verify and load dossiers
        by_day: dict[str, dict] = {}
        for path, digest in manifest["files"].items():
            p = ROOT / path
            if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                raise SystemExit(f"dossier changed since freeze: {path}")
            by_day.setdefault(p.parent.name, {})[p.stem] = json.loads(p.read_text())
        # agent run, newest week first, cached per asset-week under a runs directory scoped to this experiment
        runs_dir = ROOT / "data/agents_v2/runs" / args.experiment
        rows, weights, completed, truncated_at = [], {}, [], None
        weights_llm, weights_nd, weights_conf = {}, {}, {}
        for day in sorted(by_day, reverse=True):
            try:
                out = run_week(pd.Timestamp(day, tz="UTC"), by_day[day], client, runs_dir=runs_dir)
            except SpendCapError as exc:
                truncated_at = {"week": day, "reason": str(exc)}
                print(f"{day}: spend cap reached, week excluded; stopping", flush=True)
                break
            weights[pd.Timestamp(day, tz="UTC")] = out["portfolio"]["rule_weights"]      # keyed by symbol
            for s, r in out["results"].items():
                cites = {}
                for stage in ("nd", "debate"):
                    for role, rep in (r.get("stages", {}).get(stage, {}).get("citations") or {}).items():
                        cites[role] = rep
                rows.append({"date": day, "symbol": s, "p_outperform": r.get("p_outperform"), "p_judge": r.get("p_judge"),
                             "p_hybrid": r.get("p_hybrid"), "p_judge_nd": r.get("p_judge_nd"), "p_hybrid_nd": r.get("p_hybrid_nd"),
                             "p_judge_debate": r.get("p_judge_debate"), "p_analyst_mean": r.get("p_analyst_mean"),
                             "weight_on_quant": r.get("weight_on_quant"), "quant_rank_pct": r.get("quant_rank_pct"),
                             "confidence": r.get("confidence"), "abstain": r.get("abstain"),
                             "debated": r.get("debated", False), "debate_selected": r.get("debate_selected", False),
                             "failed": bool(r.get("failed")),
                             "cite_exist_mean": (sum(v["cite_exist_rate"] for v in cites.values() if v.get("cite_exist_rate") is not None)
                                                 / max(sum(1 for v in cites.values() if v.get("cite_exist_rate") is not None), 1)) if cites else None,
                             "number_grounded_mean": (sum(v["number_grounded_rate"] for v in cites.values() if v.get("number_grounded_rate") is not None)
                                                      / max(sum(1 for v in cites.values() if v.get("number_grounded_rate") is not None), 1)) if cites else None})
            weights_llm[pd.Timestamp(day, tz="UTC")] = out["portfolio"]["rule_weights_llm_only"]
            weights_nd[pd.Timestamp(day, tz="UTC")] = out["portfolio"]["rule_weights_judge_nd"]
            weights_conf[pd.Timestamp(day, tz="UTC")] = out["portfolio"]["rule_weights_confidence"]
            completed.append(day)
            print(f"{day}: calls {client.calls} spent ${client.spent_usd:.2f}", flush=True)
        if not completed:
            raise SystemExit("no complete week within the spend cap")
        panel = pd.DataFrame(rows)
        panel["date"] = pd.to_datetime(panel["date"], utc=True)
        fridays = sorted(panel["date"].unique())
        fwd = forward_returns(sorted(panel["symbol"].unique()), fridays)
        panel = panel.merge(fwd, on=["date", "symbol"], how="left")
        ctrl = cards[["date", "symbol", "vol_ewma20", "ret_4w", "size_rank", "dvol_30d"]]
        panel = panel.merge(ctrl, on=["date", "symbol"], how="left")
        # quant-only twin: the ridge forecast rank as probability stand-in
        qf = pd.read_parquet(ROOT / "data/dossier/quant_forecasts.parquet")
        qf["date"] = pd.to_datetime(qf["date"], utc=True)
        panel = panel.merge(qf.rename(columns={"pred_rank_pct": "p_quant"}), on=["date", "symbol"], how="left")
        paired = panel.dropna(subset=["p_judge_debate", "p_judge_nd"])
        contrast = {}
        if len(paired) >= 30:                           # paired within-asset-week debate effect (finding 4)
            def _wk_ic(col):
                return pd.Series({d: g[col].rank(pct=True).corr(g["fwd_ret"].rank(pct=True), method="spearman")
                                  for d, g in paired.dropna(subset=["fwd_ret"]).groupby("date") if len(g) >= 8})
            diff = (_wk_ic("p_judge_debate") - _wk_ic("p_judge_nd")).dropna()
            contrast = {"n_pairs": int(len(paired)), "weeks": int(len(diff)), "delta_ic_mean": float(diff.mean()) if len(diff) else None,
                        "delta_ic_nw_t": newey_west_t(diff) if len(diff) >= 3 else None,
                        "mean_abs_shift": float((paired["p_judge_debate"] - paired["p_judge_nd"]).abs().mean()),
                        "sd_debate": float(paired["p_judge_debate"].std()), "sd_nd": float(paired["p_judge_nd"].std())}
        evaluation = {"system": evaluate_panel(panel, "p_outperform"),            # deployed hybrid (debate where available)
                      "llm_only": evaluate_panel(panel.dropna(subset=["p_judge"]), "p_judge"),
                      "hybrid_uniform": evaluate_panel(panel.dropna(subset=["p_hybrid_nd"]), "p_hybrid_nd"),
                      "llm_only_uniform": evaluate_panel(panel.dropna(subset=["p_judge_nd"]), "p_judge_nd"),
                      "analyst_mean": evaluate_panel(panel.dropna(subset=["p_analyst_mean"]), "p_analyst_mean"),
                      "quant_twin": evaluate_panel(panel.dropna(subset=["p_quant"]), "p_quant"),
                      "encompassing_llm_vs_quant": encompassing(panel, "p_judge", "p_quant"),
                      "encompassing_hybrid_vs_quant": encompassing(panel, "p_hybrid", "p_quant"),
                      "debate_paired_contrast": contrast,
                      "weight_on_quant": {"mean": float(panel["weight_on_quant"].mean()) if panel["weight_on_quant"].notna().any() else None,
                                          "sd": float(panel["weight_on_quant"].std()) if panel["weight_on_quant"].notna().any() else None},
                      "citations": {"cite_exist_mean": float(panel["cite_exist_mean"].mean()) if panel["cite_exist_mean"].notna().any() else None,
                                    "number_grounded_mean": float(panel["number_grounded_mean"].mean()) if panel["number_grounded_mean"].notna().any() else None},
                      "by_year": {str(y): evaluate_panel(g, "p_outperform") for y, g in panel.groupby(panel["date"].dt.year)},
                      "weeks": {"completed": sorted(completed), "n_completed": len(completed), "n_manifested": len(by_day),
                                "truncated_at": truncated_at},
                      "delisted_rows": int(panel["delisted"].fillna(False).sum()) if "delisted" in panel else 0}
        subsets = {}
        if flags is not None:
            flags["date"] = pd.to_datetime(flags["friday"], utc=True)
            panel = panel.merge(flags[["date", "symbol", "identified"]], on=["date", "symbol"], how="left")
            for name, g in (("identified", panel[panel["identified"] == True]), ("not_identified", panel[panel["identified"] == False])):
                subsets[name] = {"n": int(len(g)), **evaluate_panel(g, "p_outperform")}
        evaluation["identified_subsets"] = subsets
        funding = realized_funding(sorted(panel["symbol"].unique()), fridays)
        portfolio = {"rule_twin": summarize_book(weights, fwd, funding=funding),
                     "rule_twin_no_funding": summarize_book(weights, fwd),
                     "rule_twin_llm_only": summarize_book(weights_llm, fwd, funding=funding),
                     "rule_twin_judge_nd": summarize_book(weights_nd, fwd, funding=funding),
                     "rule_twin_confidence": summarize_book(weights_conf, fwd, funding=funding),
                     "funding_coverage": float(funding.groupby("date").size().reindex(fridays).fillna(0).mean() / max(panel.groupby("date").size().mean(), 1))}
        run.write_json("forecasts.json", {"rows": json.loads(panel.to_json(orient="records", date_format="iso"))})
        run.write_json("evaluation.json", evaluation)
        run.write_json("portfolio.json", portfolio)
        run.write_json("cost.json", {"calls": client.calls, "spent_usd": client.spent_usd, "cost_cap_usd": args.cost_cap,
                                     "config_sha": config_sha(), "weeks_completed": len(completed), "truncated_at": truncated_at})
        run.finish([{"id": c, "status": "complete" if (c != "identified-subsets" or subsets) else "unavailable",
                     **({} if (c != "identified-subsets" or subsets) else {"reason": "no reid flags registered"})} for c in CELLS])
        print(json.dumps({"system": evaluation["system"], "quant_twin": evaluation["quant_twin"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
