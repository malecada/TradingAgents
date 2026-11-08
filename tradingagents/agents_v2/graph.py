"""Deterministic orchestration of the v2 roles for one dossier and for one weekly book.

Per asset: four analysts (parallel-safe, independent), one debate run in BOTH orders
(bull first, then bear first), each with one rebuttal, each judged separately; the
asset's forecast is the mean of the two judge probabilities (order debiasing by
construction, the C3-P lesson). Every call result is kept for the ablation table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from tradingagents.agents_v2 import roles, schemas

CONFIG_VERSION = "agents-v2.0"


@dataclass
class AssetRun:
    alias: str
    analysts: dict
    forecast: dict
    debates: dict                      # order -> {"transcript": [...], "judge": {...}}
    p_outperform: float
    confidence: float
    abstain: bool
    meta: list = field(default_factory=list)
    config_sha: str = ""

    def to_json(self) -> dict:
        return {"config_version": CONFIG_VERSION, "config_sha": self.config_sha, "alias": self.alias,
                "analysts": self.analysts, "forecast": self.forecast, "debates": self.debates,
                "p_outperform": self.p_outperform, "confidence": self.confidence, "abstain": self.abstain,
                "meta": self.meta}


def config_sha() -> str:
    payload = {"version": CONFIG_VERSION, "common": roles.COMMON, "analysts": roles.ANALYSTS,
               "forecast": roles.FORECAST, "bull": roles.BULL, "bear": roles.BEAR, "rebuttal": roles.REBUTTAL,
               "judge": roles.JUDGE, "portfolio": roles.PORTFOLIO, "schemas": {
                   "analyst": schemas.ANALYST, "forecast": schemas.FORECAST_INTERPRETER, "turn": schemas.DEBATE_TURN,
                   "judge": schemas.JUDGE, "portfolio": schemas.PORTFOLIO}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def run_asset(dossier_text: str, alias: str, client, *, analyst_roles=("market", "fundamental", "news"),
              with_forecast: bool = True, debate: bool = True) -> AssetRun:
    meta = []

    def ask(prompt, schema, name):
        parsed, m = client.call(prompt, schema, name, system=roles.COMMON)
        meta.append({"role": name, **m})
        return parsed

    analysts = {r: ask(roles.analyst_prompt(r, dossier_text), schemas.ANALYST, f"analyst_{r}") for r in analyst_roles}
    forecast = ask(roles.forecast_prompt(dossier_text), schemas.FORECAST_INTERPRETER, "forecast") if with_forecast else {}
    all_analysts = dict(analysts)
    if forecast:
        all_analysts["forecast_interpreter"] = forecast
    debates = {}
    if debate:
        for order in ("bull_first", "bear_first"):
            first, second = ("bull", "bear") if order == "bull_first" else ("bear", "bull")
            t1 = ask(roles.debate_prompt(first, dossier_text, all_analysts), schemas.DEBATE_TURN, f"{first}_open")
            t2 = ask(roles.debate_prompt(second, dossier_text, all_analysts, opponent=t1), schemas.DEBATE_TURN, f"{second}_rebut")
            t3 = ask(roles.debate_prompt(first, dossier_text, all_analysts, opponent=t2), schemas.DEBATE_TURN, f"{first}_rebut")
            transcript = [(first, t1), (second, t2), (first, t3)]
            judge = ask(roles.judge_prompt(dossier_text, all_analysts, transcript), schemas.JUDGE, f"judge_{order}")
            debates[order] = {"transcript": [{"speaker": s, **t} for s, t in transcript], "judge": judge}
        p = sum(d["judge"]["p_outperform_7d"] for d in debates.values()) / len(debates)
        conf = sum(d["judge"]["confidence"] for d in debates.values()) / len(debates)
        abstain = all(d["judge"]["abstain"] for d in debates.values())
    else:
        judge = ask(roles.judge_prompt(dossier_text, all_analysts, []), schemas.JUDGE, "judge_no_debate")
        debates["none"] = {"transcript": [], "judge": judge}
        p, conf, abstain = judge["p_outperform_7d"], judge["confidence"], judge["abstain"]
    return AssetRun(alias, analysts, forecast, debates, float(p), float(conf), bool(abstain), meta, config_sha())


def rule_weights(candidates: list[dict], max_weight: float = 0.10, gross_cap: float = 1.0) -> dict[str, float]:
    """Deterministic twin of the PM prompt: score = (p-0.5)*confidence/vol, scaled to the caps.
    Used as the quant baseline for the PM role and as a fallback when the PM output violates constraints."""
    raw = {c["alias"]: 0.0 if c.get("abstain") else (c["p_outperform_7d"] - 0.5) * c["confidence"] / max(c["vol_ann"], 0.05)
           for c in candidates}
    gross = sum(abs(v) for v in raw.values())
    if gross == 0:
        return {k: 0.0 for k in raw}
    scaled = {k: v / gross * gross_cap for k, v in raw.items()}
    clipped = {k: max(-max_weight, min(max_weight, v)) for k, v in scaled.items()}
    return clipped


def validate_portfolio(out: dict, candidates: list[dict], max_weight: float = 0.10) -> list[str]:
    problems = []
    aliases = {c["alias"] for c in candidates}
    weights = {p["alias"]: p["weight"] for p in out["positions"]}
    if set(weights) - aliases:
        problems.append("unknown alias in positions")
    if any(abs(w) > max_weight + 1e-9 for w in weights.values()):
        problems.append("weight beyond cap")
    gross = sum(abs(w) for w in weights.values())
    if gross > 1.0 + 1e-6:
        problems.append("gross exposure above 1")
    if abs(sum(weights.values())) > 0.2 + 1e-6:
        problems.append("net exposure beyond +-0.2")
    for c in candidates:
        if c.get("abstain") and abs(weights.get(c["alias"], 0.0)) > 1e-9:
            problems.append(f"non-zero weight on abstained {c['alias']}")
    return problems


def run_portfolio(candidates: list[dict], client) -> dict:
    parsed, m = client.call(roles.portfolio_prompt(candidates), schemas.PORTFOLIO, "portfolio", system=roles.COMMON)
    problems = validate_portfolio(parsed, candidates)
    weights = {p["alias"]: p["weight"] for p in parsed["positions"]}
    if problems:
        weights = rule_weights(candidates)
    return {"pm_output": parsed, "problems": problems, "weights": weights, "rule_weights": rule_weights(candidates),
            "meta": m, "config_sha": config_sha()}
