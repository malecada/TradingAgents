"""Weekly orchestration over dossiers (agents v2.4): analysts, forecast interpreter and a judge-without-debate
for EVERY universe member (uniform panel), a seeded-random debate subset with its own judges (paired
within-asset contrast), and a deterministic market-neutral book keyed by symbol.

Results are cached per (symbol, dossier sha, config sha) in stages so interrupted runs resume and ablations
reuse calls. The LLM portfolio manager is not part of the main run (ablation only).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random

import pandas as pd

from tradingagents.agents_v2.graph import (DEBATE_SELECTION, N_DEBATE, config_sha, rule_weights, run_asset,
                                           run_portfolio)
from tradingagents.dossier.or_client import ORError, SpendCapError

RUNS = Path("data/agents_v2/runs")
WORKERS = 12
SELECTION_SEED = 20261110


def select_debate_candidates(analyst_runs: dict[str, dict], n: int = N_DEBATE) -> list[str]:
    """Contested-selection rule (kept for the ablation table): keys whose analysts' mean probability is
    farthest from 0.5 or most dispersed."""
    scores = {}
    for key, analysts in analyst_runs.items():
        ps = [a["p_outperform_7d"] for a in analysts.values()]
        mean = sum(ps) / len(ps)
        scores[key] = max(abs(mean - 0.5) * 2, max(ps) - min(ps))
    return sorted(scores, key=lambda a: -scores[a])[:n]


def random_debate_candidates(symbols: list[str], friday: pd.Timestamp, n: int = N_DEBATE, seed: int = SELECTION_SEED) -> list[str]:
    """Seeded random subset per week (finding 4): the debated/not-debated contrast is then not a selection artifact."""
    rng = random.Random(f"{pd.Timestamp(friday).date()}:{seed}")
    pool = sorted(symbols)
    return sorted(rng.sample(pool, min(n, len(pool))))


def _quant_rank(dossier: dict):
    q = (dossier.get("quant_forecast") or {}).get("pred_rank_pct")
    return None if q is None or (isinstance(q, float) and q != q) else float(q)


def run_week(friday: pd.Timestamp, dossiers: dict[str, dict], client, *, n_debate: int = N_DEBATE,
             runs_dir: Path = RUNS, debate: bool = True, pm: bool = False, selection: str = DEBATE_SELECTION) -> dict:
    """``dossiers``: symbol -> dossier json. Returns per-symbol results, the book and the candidate rows."""
    friday = pd.Timestamp(friday)
    day_dir = Path(runs_dir) / friday.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    cfg = config_sha()
    results: dict[str, dict] = {}
    for sym, d in dossiers.items():
        target = day_dir / f"{sym}.json"
        cached = None
        if target.exists():
            c = json.loads(target.read_text())
            if c.get("config_sha") == cfg and c.get("dossier_sha") == d["sha256"] and not c.get("failed"):
                cached = c
        results[sym] = cached or {"symbol": sym, "alias": d["alias"], "dossier_sha": d["sha256"], "config_sha": cfg,
                                  "quant_rank_pct": _quant_rank(d), "meta": [], "stages": {}}

    def _save(sym):
        (day_dir / f"{sym}.json").write_text(json.dumps(results[sym], indent=1, default=str))

    # ---- stage 1: analysts + interpreter + judge without debate, every asset
    def stage1(sym):
        d = dossiers[sym]
        try:
            run = run_asset(d["text"], d["alias"], client, debate=False, quant_rank_pct=_quant_rank(d))
        except SpendCapError:
            raise
        except ORError as exc:                       # counted, never silently defaulted
            return sym, None, str(exc)
        return sym, run, None

    todo = [s for s, r in results.items() if "nd" not in r.get("stages", {})]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for sym, run, err in pool.map(stage1, todo):
            r = results[sym]
            if run is None:
                r["failed"] = err
                r["debated"] = False
                r.update({"p_outperform": None, "p_judge": None, "p_hybrid": None, "confidence": None, "abstain": True})
                _save(sym)
                continue
            r["analysts"], r["forecast"] = run.analysts, run.forecast
            r["weight_on_quant"] = run.weight_on_quant
            r["p_analyst_mean"] = sum(a["p_outperform_7d"] for a in run.analysts.values()) / len(run.analysts)
            r["stages"]["nd"] = {"judge": run.debates["none"]["judge"], "p_judge": run.p_judge, "p_hybrid": run.p_hybrid,
                                 "confidence": run.confidence, "abstain": run.abstain, "citations": run.citations}
            r["meta"] = r.get("meta", []) + run.meta
            r["debated"] = False
            _save(sym)

    # ---- stage 2: debate on a seeded random subset (or the contested subset for the ablation)
    ok = [s for s, r in results.items() if not r.get("failed")]
    if debate and ok:
        if selection == "random":
            chosen = random_debate_candidates(ok, friday, n_debate)
        else:
            chosen = select_debate_candidates({s: results[s]["analysts"] for s in ok}, n_debate)
        todo = [s for s in chosen if "debate" not in results[s]["stages"]]

        def stage2(sym):
            d = dossiers[sym]
            r = results[sym]
            try:
                run = run_asset(d["text"], d["alias"], client, debate=True, analysts=r["analysts"], forecast=r["forecast"],
                                quant_rank_pct=_quant_rank(d))
            except SpendCapError:
                raise
            except ORError as exc:
                return sym, None, str(exc)
            return sym, run, None

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for sym, run, err in pool.map(stage2, todo):
                r = results[sym]
                if run is None:
                    r["debate_failed"] = err             # asset keeps its no-debate forecast; disclosed
                    _save(sym)
                    continue
                r["stages"]["debate"] = {"debates": run.debates, "p_judge": run.p_judge, "p_hybrid": run.p_hybrid,
                                         "confidence": run.confidence, "abstain": run.abstain, "citations": run.citations}
                r["meta"] = r.get("meta", []) + run.meta
                _save(sym)
        for sym in chosen:
            results[sym]["debate_selected"] = True

    # ---- deployed probabilities (debate where available, else judge without debate) and uniform panels
    for sym, r in results.items():
        if r.get("failed"):
            continue
        nd, db = r["stages"]["nd"], r["stages"].get("debate")
        src = db if db else nd
        r["debated"] = bool(db)
        r.update({"p_judge": src["p_judge"], "p_hybrid": src["p_hybrid"], "p_outperform": src["p_hybrid"],
                  "confidence": src["confidence"], "abstain": src["abstain"],
                  "p_judge_nd": nd["p_judge"], "p_hybrid_nd": nd["p_hybrid"],
                  "p_judge_debate": db["p_judge"] if db else None, "p_hybrid_debate": db["p_hybrid"] if db else None})
        _save(sym)

    # ---- book keyed by symbol (finding 1); vol fallback = the week's median
    vols = [dossiers[s]["numeric"].get("vol_ewma20_ann_pct") for s in dossiers]
    vols = [v for v in vols if v]
    median_vol = (sorted(vols)[len(vols) // 2] if vols else 80.0) / 100.0
    candidates = [{"symbol": s, "p_outperform_7d": r["p_outperform"], "confidence": r["confidence"], "abstain": r["abstain"],
                   "vol_ann": (dossiers[s]["numeric"].get("vol_ewma20_ann_pct") or median_vol * 100) / 100.0}
                  for s, r in results.items() if not r.get("failed")]
    assert len({c["symbol"] for c in candidates}) == len(candidates)
    portfolio = {"config_sha": cfg, "rule_weights": rule_weights(candidates),
                 "rule_weights_confidence": rule_weights(candidates, use_confidence=True),
                 "rule_weights_judge_nd": rule_weights([{**c, "p_outperform_7d": results[c["symbol"]]["p_judge_nd"]} for c in candidates]),
                 "rule_weights_llm_only": rule_weights([{**c, "p_outperform_7d": results[c["symbol"]]["p_judge"]} for c in candidates])}
    portfolio["weights"] = portfolio["rule_weights"]
    pm_path = day_dir / "_portfolio.json"
    if pm:                                           # ablation: LLM portfolio manager with week-unique ids
        if pm_path.exists() and json.loads(pm_path.read_text()).get("config_sha") == cfg and "pm_output" in json.loads(pm_path.read_text()):
            portfolio["pm"] = json.loads(pm_path.read_text())["pm"]
        else:
            try:
                portfolio["pm"] = run_portfolio(candidates, client)
            except SpendCapError:
                raise
            except ORError as exc:
                portfolio["pm"] = {"pm_output": None, "problems": [f"pm call failed: {exc}"], "weights": portfolio["rule_weights"]}
    pm_path.write_text(json.dumps(portfolio, indent=1, default=str))
    return {"results": results, "portfolio": portfolio, "candidates": candidates}
