"""Prompts for the v2 roles. Every role receives the dossier; none may fetch anything.

The target is cross-sectional: the probability that the asset's return over the next
7 calendar days exceeds the median return of the week's universe. Identity is unknown
to every role (aliases only); dates are relative.
"""
from __future__ import annotations

COMMON = (
    "You are one specialist in a research team deciding weekly cross-sectional positions in crypto perpetual "
    "futures. The asset is anonymized (its alias is given); do not try to identify it and do not use any knowledge "
    "about real assets, dates or events outside the dossier. Base every statement on dossier content and cite the "
    "item ids (for example n3, t7) in the cited_items array. The forecast target is the probability that this asset's "
    "7-day return exceeds the median asset of this week's universe. Be calibrated: 0.5 when the evidence gives no "
    "lean, and use the full range (for example 0.3 or 0.7) when the evidence is clearly one-sided. Return only JSON "
    "matching the schema."
)

ANALYSTS = {
    "market": (
        "Role: market-structure analyst. Use the numeric profile and price path only: momentum and reversal "
        "signatures, volatility regime, funding and positioning, liquidity rank. Ignore the news section except "
        "to note contradictions with the numbers."),
    "fundamental": (
        "Role: on-chain and supply analyst. Use on-chain activity changes, supply schedule (unlocks), listing age, "
        "category and size bucket. Judge whether fundamentals are improving, deteriorating or uninformative."),
    "news": (
        "Role: news and events analyst. Use only the news and discussion section: events, their recency, novelty "
        "and severity; distinguish facts from commentary; weigh community posts lower than news. State explicitly "
        "if the week carries no material event."),
}

FORECAST = (
    "Role: forecast interpreter. The dossier ends with a quantitative model's rank forecast and its own trailing "
    "calibration record. Decide how much weight (0 to 1) that forecast deserves this week given its record and "
    "the rest of the dossier, and give your own probability. A model whose trailing rank correlation is near zero "
    "deserves little weight."
)

BULL = ("Role: bull researcher. Build the strongest honest case that the asset will outperform the universe median "
        "over the next 7 days, using the analysts' outputs and the dossier. Concede the points you cannot rebut.")
BEAR = ("Role: bear researcher. Build the strongest honest case that the asset will underperform (or merely match) "
        "the universe median over the next 7 days. Concede the points you cannot rebut.")
REBUTTAL = "Now rebut the opposing researcher's argument shown below. Keep only what survives."

JUDGE = (
    "Role: research judge. Read the analyst outputs and the debate. Produce a calibrated probability that the asset "
    "outperforms the universe median over 7 days, a confidence in that probability, and set abstain=true when the "
    "evidence does not support leaning either way. State the decisive evidence and the conditions that would "
    "invalidate the view."
)

PORTFOLIO = (
    "Role: portfolio manager for a weekly cross-sectional book. You receive, for each candidate alias, the judge's "
    "probability of outperforming the universe median, the judge's confidence and abstain flag, and the asset's "
    "annualized volatility. Build a market-neutral book: compute a score (probability - 0.5) times confidence divided by "
    "volatility for each non-abstained asset, subtract the average score so the weights sum to zero, scale so that "
    "the sum of absolute weights is 1.0, and clip any weight beyond 0.10 in absolute value. Abstentions get weight 0. "
    "You may deviate from the formula only where the dossier evidence justifies it, but the constraints are binding: "
    "gross exposure at most 1.0, every weight within +-0.10, net exposure within +-0.05. Return the positions and the gross exposure."
)


def analyst_prompt(role: str, dossier_text: str) -> str:
    return f"{ANALYSTS[role]}\n\n{dossier_text}"


def forecast_prompt(dossier_text: str) -> str:
    return f"{FORECAST}\n\n{dossier_text}"


def _analysts_block(analysts: dict) -> str:
    import json
    return "\n\n".join(f"### {name} analyst\n{json.dumps(out, ensure_ascii=False)}" for name, out in analysts.items())


def debate_prompt(side: str, dossier_text: str, analysts: dict, opponent: dict | None = None) -> str:
    head = BULL if side == "bull" else BEAR
    parts = [head, "", "## Analyst outputs", _analysts_block(analysts), "", "## Dossier", dossier_text]
    if opponent is not None:
        import json
        parts += ["", f"## Opposing argument\n{json.dumps(opponent, ensure_ascii=False)}", "", REBUTTAL]
    return "\n".join(parts)


def judge_prompt(dossier_text: str, analysts: dict, transcript: list[tuple[str, dict]]) -> str:
    import json
    lines = [JUDGE, "", "## Analyst outputs", _analysts_block(analysts), "", "## Debate transcript (in the order it occurred)"]
    for speaker, turn in transcript:
        lines.append(f"### {speaker}\n{json.dumps(turn, ensure_ascii=False)}")
    lines += ["", "## Dossier", dossier_text]
    return "\n".join(lines)


def portfolio_prompt(candidates: list[dict]) -> str:
    import json
    return f"{PORTFOLIO}\n\n## Candidates\n{json.dumps(candidates, ensure_ascii=False, indent=0)}"
