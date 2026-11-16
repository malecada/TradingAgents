"""Pairwise comparison of assets on their text dossiers (Charter 5): schedule, prompts, calls, consensus, score.

Three roles answer one comparison, as in the reader stage. Analyst A sees the two dossiers in a drawn order;
reviewer B sees them in the opposite order and starts from ``no_basis``; where the two do not name the same
asset, adjudicator J sees both dossiers and both answers and decides. The consensus is applied by code. The
decided comparisons of a week give one score per asset (Bradley-Terry strength, ``pair_xs.bt_scores``).
Every call is cached under the model, the system prompt and the user prompt (``reader.extract.CallCache``),
so the comparisons can be rebuilt from the cache alone. No outcome is read.
"""
from __future__ import annotations

import hashlib
import json
import random
import threading

import pandas as pd

from tradingagents.compare.dossier import week_seed
from tradingagents.dossier.or_client import ORError, SpendCapError
from tradingagents.reader.extract import CallCache, CallFailed, call_key
from tradingagents.xsect.pair_xs import BT_ALPHA, bt_scores

K_ROUNDS = 10
MAX_TOKENS = 200
ROLES = ("A", "B", "J")
NO_BASIS = "no_basis"
CHOICES = ("first", "second", NO_BASIS)
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["choice", "reason"],
          "properties": {"choice": {"type": "string", "enum": list(CHOICES)}, "reason": {"type": "string"}}}

INSTRUCTION = """You compare two crypto assets on the reports of the last seven days. Assets and all other entities are replaced by role tokens such as Asset_K, Exchange_1, Person_2, and dates are relative. Never guess which asset a token stands for and never use knowledge about real assets, prices or dates. Judge from the reports shown and from nothing else.

For each asset you see the reports in which it is the subject: the age of the report, the kind of source, the number of similar reports where there are several, and a summary. Both lists were selected by the same rule. A longer list alone is no argument, and a price move that already happened is no argument by itself.

Question: given only these reports, which of the two assets has the better outlook for its price over the next seven days relative to the other?

Answer with a JSON object:
- choice: first, second or no_basis. Answer no_basis when the reports give no concrete ground to prefer one asset, for example when both lists hold only routine items or opinions without a new fact.
- reason: at most 25 words that name the reports which decide. Refer to an asset by its token, never as first or second."""

REVIEWER = """You are the reviewer. Start from no_basis. Leave that default only where the reports state a concrete fact that clearly favours one asset over the other."""

ADJUDICATOR = """You are the adjudicator. Two analysts compared the two assets below and did not name the same asset. Both answers are shown with their reasons. Issue the final answer from the reports alone. An analyst may be right, or neither."""


def system_prompt(role: str) -> str:
    if role == "A":
        return INSTRUCTION
    if role == "B":
        return INSTRUCTION + "\n\n" + REVIEWER
    if role == "J":
        return INSTRUCTION + "\n\n" + ADJUDICATOR
    raise ValueError(f"unknown role {role!r}")


def prompt_sha256() -> str:
    """Identity of everything an agent is told apart from the two dossiers."""
    blob = json.dumps({"instruction": INSTRUCTION, "reviewer": REVIEWER, "adjudicator": ADJUDICATOR, "schema": SCHEMA,
                       "layout": duel_prompt(("Asset_A", "x"), ("Asset_B", "y"))}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- schedule
def schedule(syms: list[str], seed: int, k: int = K_ROUNDS) -> list[tuple[str, str]]:
    """The first ``k`` rounds of a round-robin (circle method) on a seeded order of ``syms``: every asset meets
    ``min(k, n - 1)`` distinct opponents (one fewer in a round where it rests, when the number is odd) and no
    pair occurs twice. Pairs are returned in ticker order."""
    order = sorted(syms)
    random.Random(seed).shuffle(order)
    ring: list[str | None] = order + ([None] if len(order) % 2 else [])
    m = len(ring)
    pairs = []
    for _ in range(min(k, m - 1)):
        for i in range(m // 2):
            a, b = ring[i], ring[m - 1 - i]
            if a is not None and b is not None:
                pairs.append(tuple(sorted((a, b))))
        ring = [ring[0], ring[-1], *ring[1:-1]]
    return pairs


def _parity(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:8], 16) % 2


def week_duels(friday, dossiers: pd.DataFrame, k: int = K_ROUNDS) -> list[dict]:
    """The comparisons of one week. ``dossiers`` holds the week's rows (base, alias, text). ``shown`` is the
    order analyst A sees; ``judge`` the order the adjudicator sees."""
    day = pd.Timestamp(friday).strftime("%Y-%m-%d")
    by_base = {r.base: (r.alias, r.text) for r in dossiers.itertuples(index=False)}
    out = []
    for a, b in schedule(list(by_base), week_seed(friday), k):
        shown = (a, b) if _parity("shown", day, a, b) == 0 else (b, a)
        judge = (a, b) if _parity("judge", day, a, b) == 0 else (b, a)
        out.append({"friday": friday, "a": a, "b": b, "shown": shown, "judge": judge,
                    "dossier": {a: by_base[a], b: by_base[b]}})
    return out


# ---------------------------------------------------------------- prompts
def duel_prompt(first: tuple[str, str], second: tuple[str, str]) -> str:
    """``first`` and ``second`` are (alias, dossier text)."""
    return (f"FIRST asset: {first[0]}\nReports of the last seven days:\n{first[1]}\n\n"
            f"SECOND asset: {second[0]}\nReports of the last seven days:\n{second[1]}")


def adjudication_prompt(first: tuple[str, str], second: tuple[str, str], one: str, two: str) -> str:
    """``one`` and ``two`` are the analysts' answers as shown to the adjudicator (``said``)."""
    return duel_prompt(first, second) + f"\n\nAnalyst 1 answered: {one}\nAnalyst 2 answered: {two}"


def valid(parsed) -> dict | None:
    """The answer when it has the registered form (reason cut to 60 words), else None."""
    if not isinstance(parsed, dict) or parsed.get("choice") not in CHOICES or not isinstance(parsed.get("reason"), str):
        return None
    return {"choice": parsed["choice"], "reason": " ".join(parsed["reason"].split()[:60])}


def _asset(answer: dict | None, order: tuple[str, str]) -> str | None:
    """The asset an answer names under the order it was given in: a base, ``no_basis`` or None (invalid)."""
    if answer is None:
        return None
    return {"first": order[0], "second": order[1], NO_BASIS: NO_BASIS}[answer["choice"]]


def said(answer: dict | None, order: tuple[str, str], alias: dict[str, str]) -> str:
    """An analyst's answer as the adjudicator reads it: the token of the named asset and the reason."""
    named = _asset(answer, order)
    if named is None:
        return "no valid answer"
    return f"{alias.get(named, NO_BASIS)}. Reason: {answer['reason']}"


# ---------------------------------------------------------------- calls and consensus
class Judge:
    """Cached calls of the three roles. ``client`` is a ``StructuredClient`` (or a stand-in with ``call`` and
    ``model``); with ``client=None`` only cached calls can be answered."""

    def __init__(self, client, cache: CallCache, model: str | None = None, max_tokens: int = MAX_TOKENS):
        self.client, self.cache, self.max_tokens = client, cache, max_tokens
        self.model = model or client.model
        self._lock = threading.Lock()
        self.used: set[str] = set()
        self.stats = {"calls": 0, "cached": 0, "cost": 0.0, "providers": {}, "prompt_tokens": 0, "completion_tokens": 0,
                      "invalid": {r: 0 for r in ROLES}}

    def ask(self, role: str, prompt: str) -> dict | None:
        """The valid answer of one role to one prompt, or None when the stored answer has not the registered form."""
        system = system_prompt(role)
        key = call_key(self.model, system, prompt)
        hit = self.cache.get(key)
        if hit is None:
            if self.client is None:
                raise CallFailed("not in the cache and no client")
            try:
                parsed, meta = self.client.call(prompt, SCHEMA, schema_name="comparison", system=system,
                                                max_tokens=self.max_tokens)
            except SpendCapError:
                raise
            except ORError as exc:
                raise CallFailed(str(exc)) from None
            keep = {k: meta.get(k) for k in ("provider", "cost", "prompt_tokens", "completion_tokens", "latency_s")}
            hit = {"parsed": parsed, "meta": keep, "role": role}
            self.cache.put(key, hit)
            with self._lock:
                self.stats["calls"] += 1
                self.stats["cost"] += float(meta.get("cost") or 0.0)
                self.stats["prompt_tokens"] += int(meta.get("prompt_tokens") or 0)
                self.stats["completion_tokens"] += int(meta.get("completion_tokens") or 0)
                prov = meta.get("provider")
                self.stats["providers"][prov] = self.stats["providers"].get(prov, 0) + 1
        else:
            with self._lock:
                self.stats["cached"] += 1
        answer = valid(hit["parsed"])
        with self._lock:
            self.used.add(key)
            if answer is None:
                self.stats["invalid"][role] += 1
        return answer


RESULT_COLUMNS = ["friday", "a", "b", "shown_first", "a_named", "b_named", "j_named", "winner", "resolution",
                  "a_reason", "b_reason", "j_reason"]


def resolve(judge: Judge, duel: dict) -> dict:
    """One comparison under the consensus rule. Both analysts name the same asset: that asset wins. Both
    answer ``no_basis``: no result. Otherwise the adjudicator decides; ``no_basis`` from the adjudicator is no
    result. An answer without the registered form leaves the comparison unresolved."""
    a, b = duel["a"], duel["b"]
    shown, swapped = duel["shown"], (duel["shown"][1], duel["shown"][0])
    dos = duel["dossier"]
    alias = {a: dos[a][0], b: dos[b][0]}
    ans_a = judge.ask("A", duel_prompt(dos[shown[0]], dos[shown[1]]))
    ans_b = judge.ask("B", duel_prompt(dos[swapped[0]], dos[swapped[1]]))
    named_a, named_b = _asset(ans_a, shown), _asset(ans_b, swapped)
    row = {"friday": duel["friday"], "a": a, "b": b, "shown_first": shown[0], "a_named": named_a, "b_named": named_b,
           "j_named": None, "winner": None, "resolution": "unresolved",
           "a_reason": ans_a["reason"] if ans_a else None, "b_reason": ans_b["reason"] if ans_b else None, "j_reason": None}
    if named_a is None or named_b is None:
        return row
    if named_a == named_b:
        row["resolution"] = "agreed"
        row["winner"] = None if named_a == NO_BASIS else named_a
        return row
    order = duel["judge"]
    texts = [said(ans_a, shown, alias), said(ans_b, swapped, alias)]
    if _parity("analyst", pd.Timestamp(duel["friday"]).strftime("%Y-%m-%d"), a, b):
        texts.reverse()
    ans_j = judge.ask("J", adjudication_prompt(dos[order[0]], dos[order[1]], texts[0], texts[1]))
    named_j = _asset(ans_j, order)
    row["j_named"], row["j_reason"] = named_j, ans_j["reason"] if ans_j else None
    if named_j is not None:
        row["resolution"] = "adjudicated"
        row["winner"] = None if named_j == NO_BASIS else named_j
    return row


def rebuild(duels: list[dict], cache: CallCache, model: str) -> tuple[pd.DataFrame, Judge, int]:
    """Results of every comparison from the cache alone. Returns (results, judge with the used keys, number of
    comparisons with a call missing from the cache)."""
    judge = Judge(None, cache, model=model)
    rows, missing = [], 0
    for duel in duels:
        try:
            rows.append(resolve(judge, duel))
        except CallFailed:
            missing += 1
    return pd.DataFrame(rows, columns=RESULT_COLUMNS), judge, missing


# ---------------------------------------------------------------- score and quality
def scores(results: pd.DataFrame, dossiers: pd.DataFrame, alpha: float = BT_ALPHA) -> pd.DataFrame:
    """One row per asset with a dossier: the week's Bradley-Terry log strength from the decided comparisons
    (``cmp_score``), the number of comparisons and of decided ones. An asset without a decided comparison
    sits at the prior."""
    out = []
    for friday, week in dossiers.groupby("friday"):
        syms = sorted(week["base"])
        res = results[results["friday"] == friday]
        won = res[res["winner"].notna()]
        wins = [(w, b if w == a else a) for a, b, w in zip(won["a"], won["b"], won["winner"])]
        strength = bt_scores(syms, wins, alpha=alpha)
        games = pd.concat([res["a"], res["b"]]).value_counts()
        decided = pd.concat([won["a"], won["b"]]).value_counts()
        for s in syms:
            out.append((friday, s, float(strength[s]), int(games.get(s, 0)), int(decided.get(s, 0))))
    return pd.DataFrame(out, columns=["friday", "base", "cmp_score", "n_duels", "n_decided"])


def quality(results: pd.DataFrame) -> dict:
    """Descriptive shares of the comparison stage. ``first_shown`` is the share of analyst A's asset answers
    that name the asset A saw first, ``b_first_shown`` the same for the reviewer (who saw the opposite order).
    ``same_asset`` is the share of the comparisons in which both analysts name an asset where they name the
    same one."""
    n = len(results)
    if n == 0:
        return {"comparisons": 0}
    a_named = results[results["a_named"].notna() & (results["a_named"] != NO_BASIS)]
    b_named = results[results["b_named"].notna() & (results["b_named"] != NO_BASIS)]
    both = a_named[a_named["b_named"].notna() & (a_named["b_named"] != NO_BASIS)]
    return {"comparisons": n,
            "resolution": {k: int(v) for k, v in results["resolution"].value_counts().items()},
            "decided": float(results["winner"].notna().mean()),
            "adjudicated": float((results["resolution"] == "adjudicated").mean()),
            "a_no_basis": float((results["a_named"] == NO_BASIS).mean()),
            "b_no_basis": float((results["b_named"] == NO_BASIS).mean()),
            "first_shown": float((a_named["a_named"] == a_named["shown_first"]).mean()) if len(a_named) else None,
            "b_first_shown": float((b_named["b_named"] != b_named["shown_first"]).mean()) if len(b_named) else None,
            "both_named": int(len(both)),
            "same_asset": float((both["a_named"] == both["b_named"]).mean()) if len(both) else None}
