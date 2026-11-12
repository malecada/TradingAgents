"""Fact record, JSON schema and agent instructions of the reader configuration (Charter 2).

Three roles read the same de-identified summary: reader A (event analyst), reader B (reviewer who starts from
neutral and materiality 1) and an adjudicator who sees both readings where they disagree. No role states a
probability, a return or a rank. The instructions are fixed at the freeze; ``prompt_sha256`` identifies them.
"""
from __future__ import annotations

import hashlib
import json

RELEVANCE = ("subject", "side_mention", "not_about")
EVENT_CLASSES = ("security_incident", "legal_regulatory", "exchange_listing", "exchange_delisting",
                 "token_supply_increase", "token_supply_reduction", "protocol_upgrade_or_launch",
                 "partnership_or_integration", "adoption_or_product", "distress_or_outage", "governance_or_team",
                 "funding_or_treasury", "market_wide_or_macro", "opinion_or_forecast", "other")
STATUSES = ("occurred", "scheduled", "proposed_or_rumoured")
DIRECTIONS = ("favourable", "unfavourable", "mixed", "neutral")
MATERIALITY = (1, 2, 3)
FIELDS = ("relevance", "event_class", "status", "direction", "materiality", "evidence")
ROLES = ("A", "B", "J")
FILED_ALIAS = "Filed_asset"   # the asset an item is filed under when its summary names no asset token
NOT_ABOUT = {"relevance": "not_about", "event_class": "other", "status": "occurred", "direction": "neutral",
             "materiality": 1, "evidence": ""}

RECORD_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["records"],
    "properties": {"records": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["asset", *FIELDS],
        "properties": {"asset": {"type": "string"},
                       "relevance": {"type": "string", "enum": list(RELEVANCE)},
                       "event_class": {"type": "string", "enum": list(EVENT_CLASSES)},
                       "status": {"type": "string", "enum": list(STATUSES)},
                       "direction": {"type": "string", "enum": list(DIRECTIONS)},
                       "materiality": {"type": "integer", "enum": list(MATERIALITY)},
                       "evidence": {"type": "string"}}}}},
}

INSTRUCTION = """You read one de-identified summary of a crypto-market news item or community post and record what it states.
Names are replaced by role tokens (Asset_K, Exchange_1, Person_2, Regulator_1, Network_3) or by [entity], and dates are relative. Never guess a real name. Never predict a price. Record only what the text states.

Return exactly one record for every asset listed under "Assets", with "asset" set to the listed token:
- relevance: subject (the item is mainly about this asset), side_mention (the asset appears, the item is mainly about something else), or not_about (the item states nothing about this asset).
- event_class: the one class that fits best.
  security_incident: hack, exploit, theft, vulnerability.
  legal_regulatory: lawsuit, enforcement, ruling, licence, regulation.
  exchange_listing: a venue lists the asset or adds a market for it.
  exchange_delisting: a venue delists the asset or suspends its trading.
  token_supply_increase: unlock, emission, mint, sale by insiders or by a treasury.
  token_supply_reduction: burn, buyback, lock-up.
  protocol_upgrade_or_launch: upgrade, fork, mainnet or product release by the project itself.
  partnership_or_integration: a named cooperation or a technical integration.
  adoption_or_product: usage, users, institutional adoption, a product of others built on the asset.
  distress_or_outage: insolvency, halt, outage, loss of a peg, withdrawal freeze.
  governance_or_team: vote, proposal, change of leadership or team.
  funding_or_treasury: fund raise, grant, treasury decision.
  market_wide_or_macro: a fact about the whole market or the economy, not about this asset in particular.
  opinion_or_forecast: a view, outlook or price forecast without a new fact.
  other: none of the above.
- status: occurred, scheduled (announced with a date or a firm plan), or proposed_or_rumoured.
- direction: what the stated fact means for a holder of this asset: favourable, unfavourable, mixed or neutral. For an opinion item: the stance of the author on the asset. A reported price move alone is neutral.
- materiality: 1 routine; 2 notable, the text states a magnitude that matters for this asset; 3 major, the text states a loss of a large share of funds, an enforcement action against the issuer, a listing or delisting on a leading venue, or a supply change above one tenth.
- evidence: at most 12 consecutive words copied exactly from the summary that support class and direction.

When relevance is not_about, set event_class other, status occurred, direction neutral, materiality 1 and an empty evidence."""

REVIEWER = """You are the reviewer. Start from direction neutral and materiality 1. Leave that default only where the text states a concrete fact that requires it."""

ADJUDICATOR = """You are the adjudicator. Two readers recorded the assets below and their records differ. Both records are shown. Issue the final record for every listed asset from the text alone. A reader may be right, or neither."""

RETRY_LINE = "The evidence of the earlier answer was not found in the summary. Copy the evidence word for word from the summary."

TYPE_LABEL = {"event": "event", "analysis_opinion": "opinion or analysis"}
SOURCE_LABEL = {"reddit": "community post"}


def system_prompt(role: str) -> str:
    if role == "A":
        return INSTRUCTION
    if role == "B":
        return INSTRUCTION + "\n\n" + REVIEWER
    if role == "J":
        return INSTRUCTION + "\n\n" + ADJUDICATOR
    raise ValueError(f"unknown role {role!r}")


def _asset_line(alias: str) -> str:
    if alias == FILED_ALIAS:
        return f"- {alias} (the item is filed under this asset; the summary describes it without a token)"
    return f"- {alias}"


def _head(unit) -> str:
    return (f"Item type: {TYPE_LABEL[unit.type]}\nSource: {SOURCE_LABEL.get(unit.source, 'news')}\n"
            f"Summary: {unit.summary}\n")


def _shown(record: dict | None) -> str:
    if record is None:
        return "no valid record"
    return json.dumps({f: record[f] for f in FIELDS}, ensure_ascii=False)


def unit_prompt(unit, aliases: list[str], retry: bool = False) -> str:
    text = _head(unit) + "Assets:\n" + "\n".join(_asset_line(a) for a in aliases)
    return text + ("\n\n" + RETRY_LINE if retry else "")


def adjudication_prompt(unit, aliases: list[str], first: dict, second: dict, retry: bool = False) -> str:
    """``first`` and ``second`` map alias -> record (or None); the caller fixes which reader is shown first."""
    lines = []
    for a in aliases:
        lines += [_asset_line(a), f"  reader 1: {_shown(first.get(a))}", f"  reader 2: {_shown(second.get(a))}"]
    text = _head(unit) + "Assets and the two records:\n" + "\n".join(lines)
    return text + ("\n\n" + RETRY_LINE if retry else "")


def prompt_sha256() -> str:
    """Identity of everything an agent is told apart from the unit itself."""
    blob = json.dumps({"instruction": INSTRUCTION, "reviewer": REVIEWER, "adjudicator": ADJUDICATOR, "retry": RETRY_LINE,
                       "schema": RECORD_SCHEMA, "type_label": TYPE_LABEL, "source_label": SOURCE_LABEL,
                       "filed_alias": FILED_ALIAS, "asset_line": _asset_line(FILED_ALIAS)}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
