"""Charter 1 lifecycle runner (one registered experiment): run the v2 agent system over every manifested
dev dossier (resumable through the per-asset cache), then compute the forecast-quality and rule-twin
portfolio gates. All inputs are registered by hash; outputs are written through ResearchRun.
Usage: llm_v2c1_run.py --registration research/llm-v2-charter1-<date>/gates.json --experiment <id>
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
from tradingagents.agents_v2.evaluate import evaluate_panel  # noqa: E402
from tradingagents.agents_v2.graph import config_sha, rule_weights  # noqa: E402
from tradingagents.agents_v2.portfolio_eval import summarize_book  # noqa: E402
from tradingagents.agents_v2.runner import run_week  # noqa: E402
from tradingagents.dossier.or_client import StructuredClient  # noqa: E402
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
        # verify and load dossiers
        by_day: dict[str, dict] = {}
        for path, digest in manifest["files"].items():
            p = ROOT / path
            if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                raise SystemExit(f"dossier changed since freeze: {path}")
            by_day.setdefault(p.parent.name, {})[p.stem] = json.loads(p.read_text())
        # agent run (cached per asset-week under data/agents_v2/runs)
        rows, weights = [], {}
        for day in sorted(by_day):
            out = run_week(pd.Timestamp(day, tz="UTC"), by_day[day], client)
            cands = [{"alias": r["alias"], "p_outperform_7d": r["p_outperform"], "confidence": r["confidence"], "abstain": r["abstain"],
                      "vol_ann": (by_day[day][s]["numeric"].get("vol_ewma20_ann_pct") or 80.0) / 100.0}
                     for s, r in out["results"].items() if not r.get("failed")]
            alias_to_sym = {by_day[day][s]["alias"]: s for s in by_day[day]}
            weights[pd.Timestamp(day, tz="UTC")] = {alias_to_sym[a]: w for a, w in rule_weights(cands).items()}
            for s, r in out["results"].items():
                rows.append({"date": day, "symbol": s, "p_outperform": r.get("p_outperform"), "confidence": r.get("confidence"),
                             "abstain": r.get("abstain"), "debated": r.get("debated", False), "failed": bool(r.get("failed")),
                             "pm_problems": len(out["portfolio"].get("problems", []))})
            print(f"{day}: calls {client.calls} spent ${client.spent_usd:.2f}", flush=True)
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
        evaluation = {"system": evaluate_panel(panel, "p_outperform"), "quant_twin": evaluate_panel(panel.dropna(subset=["p_quant"]), "p_quant"),
                      "by_year": {str(y): evaluate_panel(g, "p_outperform") for y, g in panel.groupby(panel["date"].dt.year)}}
        subsets = {}
        if flags is not None:
            flags["date"] = pd.to_datetime(flags["friday"], utc=True)
            panel = panel.merge(flags[["date", "symbol", "identified"]], on=["date", "symbol"], how="left")
            for name, g in (("identified", panel[panel["identified"] == True]), ("not_identified", panel[panel["identified"] == False])):
                subsets[name] = {"n": int(len(g)), **evaluate_panel(g, "p_outperform")}
        evaluation["identified_subsets"] = subsets
        portfolio = {"rule_twin": summarize_book(weights, fwd)}
        run.write_json("forecasts.json", {"rows": json.loads(panel.to_json(orient="records", date_format="iso"))})
        run.write_json("evaluation.json", evaluation)
        run.write_json("portfolio.json", portfolio)
        run.write_json("cost.json", {"calls": client.calls, "spent_usd": client.spent_usd, "config_sha": config_sha()})
        run.finish([{"id": c, "status": "complete" if (c != "identified-subsets" or subsets) else "unavailable",
                     **({} if (c != "identified-subsets" or subsets) else {"reason": "no reid flags registered"})} for c in CELLS])
        print(json.dumps({"system": evaluation["system"], "quant_twin": evaluation["quant_twin"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
