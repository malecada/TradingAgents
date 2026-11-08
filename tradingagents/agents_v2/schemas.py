"""Strict JSON schemas for every role output (plan §7.1: no free-text parsing)."""
from __future__ import annotations

PROB = {"type": "number", "minimum": 0, "maximum": 1}
CITES = {"type": "array", "items": {"type": "string"}, "description": "dossier item ids such as n3 or t7"}

ANALYST = {
    "type": "object",
    "properties": {
        "p_outperform_7d": PROB,
        "confidence": PROB,
        "key_facts": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "bullish_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "bearish_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "risks": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "cited_items": CITES,
        "data_quality": {"type": "string", "enum": ["adequate", "thin", "contradictory"]},
    },
    "required": ["p_outperform_7d", "confidence", "key_facts", "bullish_evidence", "bearish_evidence", "risks",
                 "cited_items", "data_quality"],
    "additionalProperties": False,
}

FORECAST_INTERPRETER = {
    "type": "object",
    "properties": {
        "weight_on_quant_forecast": PROB,
        "rationale": {"type": "string"},
        "p_outperform_7d": PROB,
    },
    "required": ["weight_on_quant_forecast", "rationale", "p_outperform_7d"],
    "additionalProperties": False,
}

DEBATE_TURN = {
    "type": "object",
    "properties": {
        "argument": {"type": "string"},
        "strongest_points": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "concessions": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "cited_items": CITES,
    },
    "required": ["argument", "strongest_points", "concessions", "cited_items"],
    "additionalProperties": False,
}

JUDGE = {
    "type": "object",
    "properties": {
        "p_outperform_7d": PROB,
        "confidence": PROB,
        "abstain": {"type": "boolean"},
        "decisive_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "invalidation_conditions": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "cited_items": CITES,
    },
    "required": ["p_outperform_7d", "confidence", "abstain", "decisive_evidence", "invalidation_conditions", "cited_items"],
    "additionalProperties": False,
}

PORTFOLIO = {
    "type": "object",
    "properties": {
        "positions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "alias": {"type": "string"},
                    "weight": {"type": "number", "minimum": -1, "maximum": 1},
                    "reason": {"type": "string"},
                },
                "required": ["alias", "weight", "reason"],
                "additionalProperties": False,
            },
        },
        "gross_exposure": {"type": "number", "minimum": 0, "maximum": 1},
        "notes": {"type": "string"},
    },
    "required": ["positions", "gross_exposure", "notes"],
    "additionalProperties": False,
}
