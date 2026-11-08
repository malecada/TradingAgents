"""Frozen extraction contract for Charter 0 (`llm-v2-charter0-2026-11-09`).

The prompt is C1's v2 prompt, imported verbatim from
``scripts/llm_event_xs_extract.py`` so that the only changes against the dead
C1 cycle are the model (DeepSeek V4-Pro via OpenRouter), the absence of the
keyword prefilter, and a single full-text pass instead of C1's two-stage
headline-then-content call. The JSON schema below is the structured-output
contract sent as ``response_format``. Any edit changes ``prompt_sha256()`` and
must precede registration.
"""
from __future__ import annotations

import hashlib
import json

from llm_event_xs_extract import CLASSES, PROMPT_V2
from llm_jev_questions import CONTENT_LIMIT, build_state

SCHEMA_NAME = "typed_crypto_events"
SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "class": {"type": "string", "enum": list(CLASSES)},
                    "severity": {"type": "integer", "enum": [1, 2, 3]},
                    "evidence": {"type": "string"},
                },
                "required": ["asset", "class", "severity", "evidence"],
                "additionalProperties": False,
            },
        },
        "ambiguous": {"type": "boolean"},
    },
    "required": ["events", "ambiguous"],
    "additionalProperties": False,
}
TEXT_FIELDS = ("headline", "summary", "content")


def render_text(state: dict) -> str:
    """C1's article text: headline, then summary and content when present."""
    return "\n".join(state[k] for k in TEXT_FIELDS if k in state)


def article_text(row: dict, transform=None) -> str:
    """Full-text single pass (content capped at ``CONTENT_LIMIT`` by ``build_state``)."""
    return render_text(build_state(row, transform))


def user_prompt(text: str) -> str:
    return PROMPT_V2.format(text=text)


def validate_output(obj) -> dict:
    """Strict structural validation of a parsed model answer; raises ValueError."""
    if not isinstance(obj, dict) or set(obj) != {"events", "ambiguous"}:
        raise ValueError("answer must be an object with exactly events and ambiguous")
    if not isinstance(obj["ambiguous"], bool):
        raise ValueError("ambiguous must be boolean")
    if not isinstance(obj["events"], list):
        raise ValueError("events must be a list")
    for event in obj["events"]:
        if not isinstance(event, dict) or set(event) != {"asset", "class", "severity", "evidence"}:
            raise ValueError("event must have exactly asset, class, severity, evidence")
        if event["class"] not in CLASSES:
            raise ValueError(f"unknown class {event['class']!r}")
        severity = event["severity"]
        if isinstance(severity, bool) or not isinstance(severity, int) or severity not in (1, 2, 3):
            raise ValueError("severity must be 1, 2 or 3")
        if not isinstance(event["asset"], str) or not isinstance(event["evidence"], str):
            raise ValueError("asset and evidence must be strings")
    return obj


def prompt_sha256() -> str:
    payload = {"prompt_v2": PROMPT_V2, "schema": SCHEMA, "schema_name": SCHEMA_NAME,
               "classes": list(CLASSES), "content_limit": CONTENT_LIMIT,
               "text_fields": list(TEXT_FIELDS)}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
