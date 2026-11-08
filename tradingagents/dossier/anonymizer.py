"""Anonymizer v2 (plan §5): role tokens for every identity channel, relative dates, masked
price levels, and a verification pass that rejects any residual dictionary term or year.

Aliases are stable within one dossier (one ``Masker`` instance) and re-drawn per dossier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random
import re

import pandas as pd

from tradingagents.dossier.entities import DATE_RE, PRICE_LEVEL_RE, Dictionary, _pattern

_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_ROLE_PREFIX = {"asset": "Asset", "exchange": "Exchange", "person": "Person", "regulator": "Regulator",
                "network": "Network"}
_YEAR_RE = re.compile(r"(?<![\d.])(?:19|20)\d{2}(?!\.?\d)")


@dataclass
class Masker:
    dictionary: Dictionary
    decision_ts: pd.Timestamp
    seed: int
    focus_asset: str | None = None
    _aliases: dict[tuple[str, str], str] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)
    _order: list[str] = field(default_factory=list)

    def __post_init__(self):
        rng = random.Random(self.seed)
        self._order = list(_ALPHA)
        rng.shuffle(self._order)
        if self.focus_asset:
            self.alias("asset", self.focus_asset)  # the dossier's own asset gets the first letter

    def alias(self, role: str, key: str) -> str:
        k = (role, key)
        if k not in self._aliases:
            n = self._counters.get(role, 0)
            self._counters[role] = n + 1
            if role == "asset":
                suffix = self._order[n % len(self._order)] + (str(n // len(self._order)) if n >= len(self._order) else "")
            else:
                suffix = str(n + 1)
            self._aliases[k] = f"{_ROLE_PREFIX[role]}_{suffix}"
        return self._aliases[k]

    def mapping(self) -> dict[str, str]:
        return {alias: f"{role}:{key}" for (role, key), alias in self._aliases.items()}

    def relative_date(self, match: re.Match) -> str:
        text = match.group(0)
        has_year = re.search(r"(?:19|20)\d{2}", text) is not None
        has_day = re.search(r"\d", text.replace(re.search(r"(?:19|20)\d{2}", text).group(0), "") if has_year else text) is not None
        if re.match(r"(?i)^(?:Q[1-4]|H[12]|FY)", text):
            return "[period]"
        try:
            if has_year:
                when = pd.Timestamp(text)
            elif has_day:
                # month-day without a year: the occurrence nearest the decision date
                y = self.decision_ts.year
                cands = [pd.Timestamp(f"{text} {yy}") for yy in (y - 1, y, y + 1)]
                when = min(cands, key=lambda c: abs((c.tz_localize("UTC") - self.decision_ts).days))
            else:
                return "[month]"
            when = when.tz_localize("UTC") if when.tzinfo is None else when
        except (ValueError, TypeError):
            return "[date]"
        days = (self.decision_ts.normalize() - when.normalize()).days
        if abs(days) <= 1:
            return "yesterday" if days == 1 else ("today" if days == 0 else "tomorrow")
        if abs(days) < 60:
            return f"{days} days ago" if days > 0 else f"in {-days} days"
        months = round(days / 30.4)
        if abs(months) < 24:
            return f"about {months} months ago" if months > 0 else f"in about {-months} months"
        years = round(days / 365.25, 1)
        return f"about {years} years ago" if years > 0 else f"in about {-years} years"

    def mask_text(self, text: str) -> str:
        out = text
        for term, role, key in self.dictionary.all_terms():
            pat = _pattern(term)
            if pat.search(out):
                out = pat.sub(self.alias(role, key), out)
        out = DATE_RE.sub(self.relative_date, out)
        out = _YEAR_RE.sub("[year]", out)
        out = PRICE_LEVEL_RE.sub("[price level]", out)
        return out

    def verify(self, text: str) -> list[str]:
        """Residual identity leaks: dictionary terms or four-digit years left in ``text``."""
        leaks = []
        for term, role, key in self.dictionary.all_terms():
            if _pattern(term).search(text):
                leaks.append(f"{role}:{term}")
        if _YEAR_RE.search(text):
            leaks.append("year")
        return leaks
