"""Reader calls of the reader configuration (Charter 2): cache, evidence check, one re-read.

Every call is keyed by the model, the system prompt and the user prompt, and stored in an append-only JSONL
file, so an interrupted extraction resumes without paying twice and the records can be rebuilt from the
cache alone. A record is valid when its asset was requested and its evidence phrase occurs in the summary
(whitespace and case normalised); a record with relevance ``not_about`` needs no evidence. Assets without a
valid record are re-read once with one added line; a second failure leaves the reading missing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading

from tradingagents.dossier.or_client import ORError, SpendCapError
from tradingagents.reader import schema
from tradingagents.reader.reading import Unit

MAX_TOKENS = 1500


class CallCache:
    """Append-only JSONL of calls: key -> {"parsed", "meta"}. Thread-safe; a later line replaces an earlier one.
    ``paid_usd`` is the cost of every line ever written, replaced lines included, so a spend limit holds across
    resumed processes."""

    def __init__(self, path: Path | None):
        self.path = Path(path) if path else None
        self._lock = threading.Lock()
        self._data: dict[str, dict] = {}
        self.paid_usd = 0.0
        if self.path and self.path.exists():
            with open(self.path, encoding="utf-8") as fh:
                self._load(fh)

    @classmethod
    def from_bytes(cls, data: bytes) -> "CallCache":
        """A read-only cache from the bytes of a cache file (nothing is written back)."""
        cache = cls(None)
        cache._load(data.decode("utf-8").splitlines())
        return cache

    def _load(self, lines) -> None:
        for line in lines:
            if line.strip():
                rec = json.loads(line)
                self._data[rec["key"]] = rec["value"]
                self.paid_usd += _cost(rec["value"])

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str):
        return self._data.get(key)

    def values(self) -> list[dict]:
        return list(self._data.values())

    def put(self, key: str, value: dict) -> None:
        with self._lock:
            self._data[key] = value
            self.paid_usd += _cost(value)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")


def _cost(value: dict) -> float:
    return float((value.get("meta") or {}).get("cost") or 0.0)


def call_key(model: str, system: str, prompt: str) -> str:
    return hashlib.sha256("\x1f".join((model, system, prompt)).encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def evidence_ok(record: dict, summary: str) -> bool:
    phrase = normalize(record.get("evidence", ""))
    if not phrase:
        return record.get("relevance") == "not_about"
    return phrase in normalize(summary)


def clean(record: dict) -> dict:
    """The record without its asset token; a ``not_about`` record carries the fixed neutral fields."""
    if record["relevance"] == "not_about":
        return dict(schema.NOT_ABOUT)
    return {f: record[f] for f in schema.FIELDS}


def well_formed(record) -> bool:
    return (isinstance(record, dict) and record.get("relevance") in schema.RELEVANCE
            and record.get("event_class") in schema.EVENT_CLASSES and record.get("status") in schema.STATUSES
            and record.get("direction") in schema.DIRECTIONS and record.get("materiality") in schema.MATERIALITY
            and not isinstance(record.get("materiality"), bool) and isinstance(record.get("evidence"), str))


def validate(parsed, aliases: list[str], summary: str) -> tuple[dict[str, dict | None], dict[str, str]]:
    """(alias -> valid record or None, alias -> ok | absent | malformed | evidence). The first record of an
    asset counts; unrequested assets are ignored."""
    out: dict[str, dict | None] = {a: None for a in aliases}
    why = {a: "absent" for a in aliases}
    seen = set()
    for rec in (parsed.get("records") if isinstance(parsed, dict) else None) or []:
        alias = rec.get("asset") if isinstance(rec, dict) else None
        if alias not in out or alias in seen:
            continue
        seen.add(alias)
        if not well_formed(rec):
            why[alias] = "malformed"
        elif not evidence_ok(rec, summary):
            why[alias] = "evidence"
        else:
            out[alias], why[alias] = clean(rec), "ok"
    return out, why


class CallFailed(RuntimeError):
    """A call failed at the transport or format level after the client's retries; nothing was cached."""


class Reader:
    """Cached calls for the three roles. ``client`` is a ``StructuredClient`` (or a stand-in with ``call`` and
    ``model``); with ``client=None`` only cached calls can be answered."""

    def __init__(self, client, cache: CallCache, model: str | None = None, max_tokens: int = MAX_TOKENS):
        self.client, self.cache, self.max_tokens = client, cache, max_tokens
        self.model = model or client.model
        self._lock = threading.Lock()
        self.used: set[str] = set()      # keys of every call an answer was taken from (cached or new)
        self.stats = {"calls": 0, "cached": 0, "cost": 0.0, "providers": {}, "prompt_tokens": 0, "completion_tokens": 0,
                      "first_read": {r: {"ok": 0, "absent": 0, "malformed": 0, "evidence": 0} for r in schema.ROLES},
                      "reread": {r: {"ok": 0, "absent": 0, "malformed": 0, "evidence": 0} for r in schema.ROLES},
                      "grounding": {r: {"needed": 0, "found": 0} for r in schema.ROLES}}

    def _call(self, role: str, prompt: str) -> dict:
        system = schema.system_prompt(role)
        key = call_key(self.model, system, prompt)
        hit = self.cache.get(key)
        if hit is not None:
            with self._lock:
                self.stats["cached"] += 1
                self.used.add(key)
            return hit["parsed"]
        if self.client is None:
            raise CallFailed("not in the cache and no client")
        try:
            parsed, meta = self.client.call(prompt, schema.RECORD_SCHEMA, schema_name="records", system=system,
                                            max_tokens=self.max_tokens)
        except SpendCapError:
            raise
        except ORError as exc:
            raise CallFailed(str(exc)) from None
        keep = {k: meta.get(k) for k in ("provider", "cost", "prompt_tokens", "completion_tokens", "latency_s")}
        self.cache.put(key, {"parsed": parsed, "meta": keep, "role": role})
        with self._lock:
            self.used.add(key)
            self.stats["calls"] += 1
            self.stats["cost"] += float(meta.get("cost") or 0.0)
            self.stats["prompt_tokens"] += int(meta.get("prompt_tokens") or 0)
            self.stats["completion_tokens"] += int(meta.get("completion_tokens") or 0)
            prov = meta.get("provider")
            self.stats["providers"][prov] = self.stats["providers"].get(prov, 0) + 1
        return parsed

    def read(self, role: str, unit: Unit, aliases: list[str] | None = None, readings: tuple[dict, dict] | None = None) -> dict:
        """alias -> record or None for one role on one unit. ``readings`` (first, second) is given to the adjudicator."""
        aliases = list(aliases if aliases is not None else unit.aliases)

        def prompt(names: list[str], retry: bool) -> str:
            if role == "J":
                return schema.adjudication_prompt(unit, names, readings[0], readings[1], retry=retry)
            return schema.unit_prompt(unit, names, retry=retry)

        out, why = validate(self._call(role, prompt(aliases, False)), aliases, unit.summary)
        self._count("first_read", role, why, out)
        missing = [a for a in aliases if out[a] is None]
        if missing:
            again, why = validate(self._call(role, prompt(missing, True)), missing, unit.summary)
            self._count("reread", role, why, again)
            out.update(again)
        return out

    def _count(self, stage: str, role: str, why: dict[str, str], out: dict[str, dict | None]) -> None:
        """Reasons per stage; evidence grounding of first reads: of the well-formed records that need an evidence
        phrase (every record except a clean ``not_about``), the share whose phrase occurs in the summary."""
        with self._lock:
            for alias, reason in why.items():
                self.stats[stage][role][reason] += 1
                if stage == "first_read":
                    found = reason == "ok" and out[alias]["relevance"] != "not_about"
                    if found or reason == "evidence":
                        self.stats["grounding"][role]["needed"] += 1
                        self.stats["grounding"][role]["found"] += int(found)
