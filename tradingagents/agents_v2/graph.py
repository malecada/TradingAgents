"""Deterministic orchestration of the v2 roles for one dossier and for one weekly book (agents v2.4).

Information flow (design review 2026-11-10, findings 2, 5, 10):
- three analysts receive physically different slices of the dossier (market: price/vol/funding lines and the
  calendar; fundamental: profile, on-chain and supply lines plus event-typed items; news: all text items and
  the calendar); none sees the quant forecast;
- the forecast interpreter alone sees the quant section and returns a weight for it;
- debaters and the judge see the dossier without the quant section plus the analysts' outputs, so the judge's
  probability is the LLM-only forecast (``p_judge``);
- the deployed probability is a structural mix on the logit scale,
  logit(p_hybrid) = w * logit(q) + (1 - w) * logit(p_judge), with q the quant rank percentile and w the
  interpreter's weight; q, p_judge and p_hybrid are all recorded as separate panels.
The debate is symmetric (opening, then the opponent's opening-plus-rebuttal) and run in both orders with one
judge per order; the asset's p_judge is the mean of the two judges (order debiasing, the C3-P lesson).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import re

from tradingagents.agents_v2 import roles, schemas
from tradingagents.dossier.or_client import PINS

CONFIG_VERSION = "agents-v2.4"
N_DEBATE = 12
DEBATE_SELECTION = "random"          # seeded per week; the paired judge-no-debate call makes the debate effect a within-asset contrast
ANALYST_ROLES = ("market", "fundamental", "news")
TEMPERATURE = 0
# Reasoning per role. Providers did not honour effort/cap settings for DeepSeek V4-Pro (pilot: ~2,000 reasoning
# tokens and ~45 s per call regardless), so evidence-gathering roles run in non-thinking mode (~9 s, 5x cheaper,
# and they cite dossier items), while the two judgment roles think.
REASONING = {"analyst": {"enabled": False}, "forecast": {"enabled": False}, "debate": {"enabled": False},
             "judge": {"effort": "medium"}, "portfolio": {"effort": "medium"}}
EFFORT = {k: ("none" if v.get("enabled") is False else v.get("effort")) for k, v in REASONING.items()}
MAX_TOKENS = {"analyst": 4000, "forecast": 3000, "debate": 4000, "judge": 16000, "portfolio": 16000}

# physical input partition (dossier numeric line ids are stable: builder render order n1..n8)
ANALYST_LINES = {"market": ("n2", "n3", "n4", "n7", "n8"), "fundamental": ("n1", "n5", "n6")}
QUANT_HEADER = "## Quant forecast"
CALENDAR_HEADER = "## Scheduled events"
NEWS_HEADER = "## News and discussion"
Q_CLIP = (0.02, 0.98)


@dataclass
class AssetRun:
    alias: str
    analysts: dict
    forecast: dict
    debates: dict                      # order -> {"transcript": [...], "judge": {...}}
    p_judge: float                     # LLM-only probability (judge, no quant section)
    p_hybrid: float                    # structural mix with the quant rank percentile
    confidence: float
    abstain: bool
    quant_rank_pct: float | None = None
    weight_on_quant: float | None = None
    citations: dict = field(default_factory=dict)
    meta: list = field(default_factory=list)
    config_sha: str = ""

    @property
    def p_outperform(self) -> float:    # deployed probability
        return self.p_hybrid

    def to_json(self) -> dict:
        return {"config_version": CONFIG_VERSION, "config_sha": self.config_sha, "alias": self.alias,
                "analysts": self.analysts, "forecast": self.forecast, "debates": self.debates,
                "p_judge": self.p_judge, "p_hybrid": self.p_hybrid, "p_outperform": self.p_outperform,
                "confidence": self.confidence, "abstain": self.abstain, "quant_rank_pct": self.quant_rank_pct,
                "weight_on_quant": self.weight_on_quant, "citations": self.citations, "meta": self.meta}


def config_sha() -> str:
    payload = {"version": CONFIG_VERSION, "reasoning": REASONING, "max_tokens": MAX_TOKENS, "pins": PINS,
               "n_debate": N_DEBATE, "debate_selection": DEBATE_SELECTION, "analyst_roles": ANALYST_ROLES,
               "analyst_lines": ANALYST_LINES, "temperature": TEMPERATURE, "q_clip": Q_CLIP,
               "common": roles.COMMON, "analysts": roles.ANALYSTS,
               "forecast": roles.FORECAST, "bull": roles.BULL, "bear": roles.BEAR, "rebuttal": roles.REBUTTAL,
               "judge": roles.JUDGE, "portfolio": roles.PORTFOLIO, "schemas": {
                   "analyst": schemas.ANALYST, "forecast": schemas.FORECAST_INTERPRETER, "turn": schemas.DEBATE_TURN,
                   "judge": schemas.JUDGE, "portfolio": schemas.PORTFOLIO}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


# ---------------------------------------------------------------- dossier slicing
def split_sections(dossier_text: str) -> dict[str, str]:
    """Header line ('# ...' or '## ...') -> body text. The title line is kept under 'title'."""
    out, key, buf = {}, "title", []
    for line in dossier_text.splitlines():
        if line.startswith("#"):
            out[key] = "\n".join(buf).strip("\n")
            key, buf = line.strip(), []
        else:
            buf.append(line)
    out[key] = "\n".join(buf).strip("\n")
    return out


def _section(sections: dict, prefix: str) -> tuple[str, str]:
    for k, v in sections.items():
        if k.startswith(prefix):
            return k, v
    return "", ""


def without_quant(dossier_text: str) -> str:
    """The dossier with the quant-forecast section removed (what debaters and judges see)."""
    i = dossier_text.find(QUANT_HEADER)
    return dossier_text if i < 0 else dossier_text[:i].rstrip("\n") + "\n"


def analyst_view(role: str, dossier_text: str) -> str:
    """The slice of the dossier an analyst role receives (finding 5: physical partition)."""
    s = split_sections(dossier_text)
    title = next((k for k in s if k.startswith("# ")), "# Dossier")
    num_key, numeric = _section(s, "## Numeric profile")
    cal_key, calendar = _section(s, CALENDAR_HEADER)
    news_key, news = _section(s, NEWS_HEADER)
    num_lines = [l for l in numeric.splitlines() if l.strip()]
    parts = [title, ""]
    if role == "market":
        keep = ANALYST_LINES["market"]
        parts += [num_key, "\n".join(l for l in num_lines if re.match(r"\[(%s)\]" % "|".join(keep), l)), "", cal_key, calendar]
    elif role == "fundamental":
        keep = ANALYST_LINES["fundamental"]
        events = [l for l in news.splitlines() if re.match(r"- \[t\d+\] \[[^]]*, event,", l)]
        parts += [num_key, "\n".join(l for l in num_lines if re.match(r"\[(%s)\]" % "|".join(keep), l)), "",
                  "## Event-typed news items (last 30 days)", "\n".join(events) if events else "- No event-typed items."]
    elif role == "news":
        parts += [cal_key, calendar, "", news_key, news]
    else:
        raise ValueError(role)
    return "\n".join(p for p in parts if p is not None) + "\n"


_ITEM_ID = re.compile(r"\[([nt]\d+)\]")
_NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")


def citation_report(output: dict, text_seen: str) -> dict:
    """Mechanical validity checks (finding 11): cited ids exist in the text the role saw; numbers quoted in
    evidence bullets occur in that text. No API cost."""
    ids = set(_ITEM_ID.findall(text_seen))
    cited = [c.strip() for c in output.get("cited_items", []) if isinstance(c, str)]
    norm = [re.sub(r"[^nt\d]", "", c.lower()) for c in cited]
    exist = [c in ids for c in norm]
    nums_in_text = set(_NUM.findall(text_seen))
    bullets = []
    for k in ("key_facts", "bullish_evidence", "bearish_evidence", "risks", "decisive_evidence", "strongest_points"):
        bullets += [b for b in output.get(k, []) if isinstance(b, str)]
    quoted = [n for b in bullets for n in _NUM.findall(b)]
    grounded = [n in nums_in_text or n.rstrip("0").rstrip(".") in nums_in_text for n in quoted]
    return {"n_cited": len(cited), "cite_exist_rate": (sum(exist) / len(exist)) if exist else None,
            "n_numbers": len(quoted), "number_grounded_rate": (sum(grounded) / len(grounded)) if grounded else None}


# ---------------------------------------------------------------- probability mixing
def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def hybrid_probability(p_judge: float, quant_rank_pct: float | None, weight: float | None) -> float:
    """logit(p_hybrid) = w*logit(q) + (1-w)*logit(p_judge); q clipped to Q_CLIP; without a quant value, p_judge."""
    if quant_rank_pct is None or weight is None or (isinstance(quant_rank_pct, float) and math.isnan(quant_rank_pct)):
        return float(p_judge)
    q = min(max(float(quant_rank_pct), Q_CLIP[0]), Q_CLIP[1])
    w = min(max(float(weight), 0.0), 1.0)
    return _sigmoid(w * _logit(q) + (1 - w) * _logit(p_judge))


def _judge_p(judge: dict) -> float:
    """Abstention maps to 0.5 (finding 9: consistent in both arms)."""
    return 0.5 if judge.get("abstain") else float(judge["p_outperform_7d"])


# ---------------------------------------------------------------- per-asset run
def run_asset(dossier_text: str, alias: str, client, *, analyst_roles=ANALYST_ROLES, with_forecast: bool = True,
              debate: bool = True, analysts: dict | None = None, quant_rank_pct: float | None = None,
              forecast: dict | None = None) -> AssetRun:
    """``analysts`` / ``forecast`` may be supplied from a prior pass so they are not re-run.
    ``quant_rank_pct`` is the dossier's quant rank percentile (needed for the hybrid mix)."""
    meta, citations = [], {}

    def ask(prompt, schema, name, effort_key, seen_text):
        parsed, m = client.call(prompt, schema, name, system=roles.COMMON, reasoning=REASONING[effort_key],
                                max_tokens=MAX_TOKENS[effort_key])
        meta.append({"role": name, **m})
        citations[name] = citation_report(parsed, seen_text)
        return parsed

    if analysts is None:
        analysts = {}
        for r in analyst_roles:
            view = analyst_view(r, dossier_text)
            analysts[r] = ask(roles.analyst_prompt(r, view), schemas.ANALYST, f"analyst_{r}", "analyst", view)
    if with_forecast and forecast is None:
        forecast = ask(roles.forecast_prompt(dossier_text), schemas.FORECAST_INTERPRETER, "forecast", "forecast", dossier_text)
    forecast = forecast or {}
    seen = without_quant(dossier_text)             # debaters and judges never see the quant section
    debates = {}
    if debate:
        for order in ("bull_first", "bear_first"):
            first, second = ("bull", "bear") if order == "bull_first" else ("bear", "bull")
            t1 = ask(roles.debate_prompt(first, seen, analysts), schemas.DEBATE_TURN, f"{first}_open", "debate", seen)
            t2 = ask(roles.debate_prompt(second, seen, analysts, opponent=t1), schemas.DEBATE_TURN, f"{second}_reply", "debate", seen)
            transcript = [(first, t1), (second, t2)]
            judge = ask(roles.judge_prompt(seen, analysts, transcript), schemas.JUDGE, f"judge_{order}", "judge", seen)
            debates[order] = {"transcript": [{"speaker": s, **t} for s, t in transcript], "judge": judge}
        p = sum(_judge_p(d["judge"]) for d in debates.values()) / len(debates)
        conf = sum(d["judge"]["confidence"] for d in debates.values()) / len(debates)
        abstain = all(d["judge"]["abstain"] for d in debates.values())
    else:
        judge = ask(roles.judge_prompt(seen, analysts, []), schemas.JUDGE, "judge_no_debate", "judge", seen)
        debates["none"] = {"transcript": [], "judge": judge}
        p, conf, abstain = _judge_p(judge), judge["confidence"], judge["abstain"]
    w = forecast.get("weight_on_quant_forecast") if forecast else None
    p_h = hybrid_probability(p, quant_rank_pct, w)
    return AssetRun(alias, analysts, forecast, debates, float(p), float(p_h), float(conf), bool(abstain),
                    quant_rank_pct, w, citations, meta, config_sha())


# ---------------------------------------------------------------- book
def rule_weights(candidates: list[dict], max_weight: float = 0.10, gross_cap: float = 1.0, key: str = "symbol",
                 use_confidence: bool = False) -> dict[str, float]:
    """Deterministic, market-neutral book keyed by ``key`` (symbol; aliases collide across a week).
    score = (p - 0.5) / vol, demeaned across the week's assets (net 0), scaled to gross 1, clipped per asset.
    A calibrated probability is the complete forecast for a binary target, so self-reported confidence is NOT
    in the primary book (finding 9); ``use_confidence=True`` gives the descriptive variant. Abstentions are flat
    (weight 0, outside the demeaning set); their panel probability is 0.5."""
    rows = [c for c in candidates if c.get("p_outperform_7d") is not None and not c.get("abstain")]
    out = {c[key]: 0.0 for c in candidates}
    if len(rows) < 2:
        return out
    raw = {}
    for c in rows:
        conf = float(c.get("confidence", 1.0)) if use_confidence else 1.0
        raw[c[key]] = (float(c["p_outperform_7d"]) - 0.5) * conf / max(float(c["vol_ann"]), 0.05)
    w = dict(raw)
    for _ in range(100):                             # alternate demeaning and clipping until both hold
        mean = sum(w.values()) / len(w)
        w = {k: v - mean for k, v in w.items()}
        gross = sum(abs(v) for v in w.values())
        if gross == 0:
            return out
        w = {k: max(-max_weight, min(max_weight, v / gross * gross_cap)) for k, v in w.items()}
        if abs(sum(w.values())) < 1e-12:
            break
    mean = sum(w.values()) / len(w)                  # final centering; a shrink keeps caps and neutrality
    w = {k: v - mean for k, v in w.items()}
    scale = min(1.0, gross_cap / max(sum(abs(v) for v in w.values()), 1e-12), max_weight / max(max(abs(v) for v in w.values()), 1e-12))
    out.update({k: v * scale for k, v in w.items()})
    return out


def validate_portfolio(out: dict, candidates: list[dict], max_weight: float = 0.10, key: str = "id") -> list[str]:
    problems = []
    ids = {c[key] for c in candidates}
    weights = {p["alias"]: p["weight"] for p in out["positions"]}
    if set(weights) - ids:
        problems.append("unknown id in positions")
    if len(weights) != len(out["positions"]):
        problems.append("duplicate id in positions")
    if any(abs(w) > max_weight + 1e-9 for w in weights.values()):
        problems.append("weight beyond cap")
    gross = sum(abs(w) for w in weights.values())
    if gross > 1.0 + 1e-6:
        problems.append("gross exposure above 1")
    if abs(sum(weights.values())) > 0.05 + 1e-6:
        problems.append("net exposure beyond +-0.05")
    for c in candidates:
        if c.get("abstain") and abs(weights.get(c[key], 0.0)) > 1e-9:
            problems.append(f"non-zero weight on abstained {c[key]}")
    return problems


def run_portfolio(candidates: list[dict], client) -> dict:
    """LLM portfolio manager (ablation only; not part of the main run, finding 12). Candidates are shown under
    week-unique ids C01..C50 so collisions between dossier aliases cannot corrupt the book."""
    shown = [{"id": f"C{i + 1:02d}", "symbol": c["symbol"], "p_outperform_7d": c["p_outperform_7d"],
              "confidence": c["confidence"], "abstain": c["abstain"], "vol_ann": c["vol_ann"]} for i, c in enumerate(candidates)]
    prompt_rows = [{k: v for k, v in s.items() if k != "symbol"} for s in shown]
    parsed, m = client.call(roles.portfolio_prompt(prompt_rows), schemas.PORTFOLIO, "portfolio", system=roles.COMMON,
                            reasoning=REASONING["portfolio"], max_tokens=MAX_TOKENS["portfolio"])
    problems = validate_portfolio(parsed, shown)
    id_to_sym = {s["id"]: s["symbol"] for s in shown}
    weights = {id_to_sym[p["alias"]]: p["weight"] for p in parsed["positions"] if p["alias"] in id_to_sym}
    rule = rule_weights(candidates)
    if problems:
        weights = rule
    return {"pm_output": parsed, "problems": problems, "weights": weights, "rule_weights": rule,
            "meta": m, "config_sha": config_sha()}
