"""Weekly orchestration over dossiers: analysts on every universe member, full debate on the
most-contested candidates, judge probabilities for all, one portfolio call per week.

Results are cached per (dossier sha, config sha) so ablations and re-runs reuse calls.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pandas as pd

from tradingagents.agents_v2 import roles, schemas
from tradingagents.agents_v2.graph import MAX_TOKENS, REASONING, config_sha, run_asset, run_portfolio
from tradingagents.dossier.or_client import ORError

RUNS = Path("data/agents_v2/runs")
N_DEBATE = 12
WORKERS = 12


def select_debate_candidates(analyst_runs: dict[str, dict], n: int = N_DEBATE) -> list[str]:
    """Aliases whose analysts' mean probability is farthest from 0.5 (conviction) or most
    dispersed (disagreement); union ranked by max of the two normalized scores."""
    scores = {}
    for alias, analysts in analyst_runs.items():
        ps = [a["p_outperform_7d"] for a in analysts.values()]
        mean = sum(ps) / len(ps)
        spread = max(ps) - min(ps)
        scores[alias] = max(abs(mean - 0.5) * 2, spread)
    return sorted(scores, key=lambda a: -scores[a])[:n]


def analysts_only(dossier_text: str, client, analyst_roles=("market", "fundamental", "news")) -> tuple[dict, list]:
    out, meta = {}, []
    for r in analyst_roles:
        parsed, m = client.call(roles.analyst_prompt(r, dossier_text), schemas.ANALYST, f"analyst_{r}", system=roles.COMMON,
                                reasoning=REASONING["analyst"], max_tokens=MAX_TOKENS["analyst"])
        out[r] = parsed
        meta.append({"role": f"analyst_{r}", **m})
    return out, meta


def run_week(friday: pd.Timestamp, dossiers: dict[str, dict], client, *, n_debate: int = N_DEBATE,
             runs_dir: Path = RUNS, debate: bool = True) -> dict:
    """``dossiers``: symbol -> dossier json. Returns per-symbol results and the portfolio."""
    day_dir = Path(runs_dir) / pd.Timestamp(friday).strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    cfg = config_sha()
    results = {}
    analyst_runs = {}
    pending = []
    for sym, d in dossiers.items():
        target = day_dir / f"{sym}.json"
        if target.exists():
            cached = json.loads(target.read_text())
            if cached.get("config_sha") == cfg and cached.get("dossier_sha") == d["sha256"]:
                results[sym] = cached
                analyst_runs[d["alias"]] = cached["analysts"]
                continue
        pending.append(sym)

    def analyze(sym):
        d = dossiers[sym]
        try:
            analysts, meta = analysts_only(d["text"], client)
        except ORError as exc:                       # counted, never silently defaulted
            return sym, {"symbol": sym, "alias": d["alias"], "dossier_sha": d["sha256"], "config_sha": cfg,
                         "failed": str(exc), "analysts": {}, "meta": [], "debated": False,
                         "p_outperform": None, "confidence": None, "abstain": True}
        return sym, {"symbol": sym, "alias": d["alias"], "dossier_sha": d["sha256"], "config_sha": cfg,
                     "analysts": analysts, "meta": meta, "debated": False,
                     "p_outperform": sum(a["p_outperform_7d"] for a in analysts.values()) / len(analysts),
                     "confidence": sum(a["confidence"] for a in analysts.values()) / len(analysts), "abstain": False}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for sym, res in pool.map(analyze, pending):
            results[sym] = res
            if not res.get("failed"):
                analyst_runs[dossiers[sym]["alias"]] = res["analysts"]
    alias_to_sym = {d["alias"]: s for s, d in dossiers.items()}
    if debate:
        todo = [alias_to_sym[a] for a in select_debate_candidates(analyst_runs, n_debate)
                if not results[alias_to_sym[a]].get("debated") and not results[alias_to_sym[a]].get("failed")]

        def debate_one(sym):
            try:
                return sym, run_asset(dossiers[sym]["text"], dossiers[sym]["alias"], client,
                                      analysts=results[sym]["analysts"]), None
            except ORError as exc:
                return sym, None, str(exc)

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for sym, run, err in pool.map(debate_one, todo):
                if run is None:
                    results[sym]["debate_failed"] = err
                    continue
                results[sym].update({"debated": True, "forecast": run.forecast, "debates": run.debates,
                                     "p_outperform": run.p_outperform, "confidence": run.confidence,
                                     "abstain": run.abstain, "meta": results[sym]["meta"] + run.meta})
    for sym, r in results.items():
        (day_dir / f"{sym}.json").write_text(json.dumps(r, indent=1, default=str))
    candidates = [{"alias": r["alias"], "p_outperform_7d": r["p_outperform"], "confidence": r["confidence"],
                   "abstain": r["abstain"],
                   "vol_ann": (dossiers[s]["numeric"].get("vol_ewma20_ann_pct") or 80.0) / 100.0}
                  for s, r in results.items() if not r.get("failed")]
    pm_path = day_dir / "_portfolio.json"
    if pm_path.exists() and json.loads(pm_path.read_text()).get("config_sha") == cfg:
        portfolio = json.loads(pm_path.read_text())
    else:
        try:
            portfolio = run_portfolio(candidates, client)
        except ORError as exc:
            from tradingagents.agents_v2.graph import rule_weights
            portfolio = {"pm_output": None, "problems": [f"pm call failed: {exc}"], "weights": rule_weights(candidates),
                         "rule_weights": rule_weights(candidates), "meta": {}, "config_sha": cfg}
        portfolio["weights_by_symbol"] = {alias_to_sym[a]: w for a, w in portfolio["weights"].items() if a in alias_to_sym}
        pm_path.write_text(json.dumps(portfolio, indent=1, default=str))
    return {"results": results, "portfolio": portfolio}
