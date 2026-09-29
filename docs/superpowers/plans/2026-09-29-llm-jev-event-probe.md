# Jev P0 Extraction Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, register and run a one-shot probe testing whether TypeSafe's Jev, via OpenRouter, meets the C1 P0 extraction floors on the 400 adjudicated C1 articles.

**Architecture:** Small single-purpose modules under `scripts/`: truth rebuild from committed C1 artifacts; frozen Jev questions and candidates; OpenRouter client; two-call labeling; blind review sheet; scoring. Two lifecycle runs follow. E1 labels the articles and emits a blind sheet, then a human reviews it. E2 applies the review and computes the gates. Both runs use `tradingagents.research.ResearchRun` with committed registrations.

**Tech Stack:** Python 3.13.13 (pinned `.venv`), pandas/pyarrow, `requests`, `python-dotenv`, pytest, `tradingagents.research` lifecycle.

**Spec:** `docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md`

## Global Constraints

- Work only in `/home/malecada/master_thesis/TradingAgents-jev-probe`, branch `research/llm-jev-event-2026-09-29`. Never touch the `TradingAgents-audit-fixes` worktree (another session owns its uncommitted work).
- Interpreter: this worktree's `.venv` built with `uv sync --locked --all-extras --python 3.13.13`. No dependency or `uv.lock` change.
- HTTP only through `requests` against `POST https://openrouter.ai/api/alpha/decisions`; body carries `provider = {"only": ["typesafe"], "allow_fallbacks": false}`.
- Never read, print or log `.env` or the key. Code loads it with `python-dotenv` from `<root>/.env`, accepting `OPENROUTER_API_KEY` or `OPENROUTER_API`.
- Spend caps: USD 5 for E1, USD 0.05 for the smoke test, summed from each response's `usage.cost`.
- Class event rule: mean of two Noul probabilities `>= 0.5`. Review seed `20260929`, 20 agreement spot-checks.
- C1 artifacts (`data/llm_event_xs/*`, `scripts/llm_event_xs_*.py`) are read-only.
- No Jev call on sample/corpus text before the design commit is pushed. Smoke test uses invented headlines only.
- Documentation prose is impersonal (no "we/our").
- Every commit message ends with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Test command form: `.venv/bin/python -m pytest <file> --import-mode=importlib -q` (run from the worktree root).
- `$SCRATCH` in commands means `/tmp/claude-1000/-home-malecada-master-thesis/42982101-1028-4d98-a0e8-4d3846e0149c/scratchpad`; export it in each shell that uses it.

## Review Focus

- OpenRouter's alpha endpoint returns a shape differing from its docs (missing answer, incomplete choice probabilities, alias model string). Expected behavior: the run fails loudly and never defaults a value. Pinned in Task 3 (`test_missing_answer_fails`, `test_incomplete_choice_probabilities_fail`, `test_model_drift_fails`).
- An article yields no candidate entity (lowercase/number-only headline). Expected behavior: the asset question is omitted and the asset is `None`, with no crash. Pinned in Task 2 (`test_candidates_none_found`, `test_build_questions_shape`) and Task 4 (`test_no_asset_question`).
- The human fills the sheet sloppily (lowercase, `yes`/`no`, blank, `NEITHER` without a colon). Expected behavior: case and space are normalized, and anything else is rejected with every problem row listed. Pinned in Task 5 (`test_parse_normalizes_case_and_yes_no`, `test_parse_reports_all_problems`).
- A mean probability lands exactly on 0.5. Expected behavior: it counts as an event. Pinned in Task 4 (`test_threshold_is_inclusive`).
- An article has non-ASCII text, NaN fields or content longer than 4,000 chars. Expected behavior: text is preserved, NaN is omitted, and content is truncated before anonymization. Pinned in Task 2 (`test_build_state_fields`).

---

### Task 1: Environment and C1 truth rebuild

**Files:**
- Create: `scripts/llm_event_xs_truth.py`
- Test: `tests/research/test_llm_jev_truth.py`

**Interfaces:**
- Consumes: committed files in `data/llm_event_xs/`.
- Produces:
  - `ROUNDS = ("v1", "v2")`, `ROUND_FILES: dict[str, dict[str, str]]` (kinds `sample, extractor, sheet, key, anon, result`), `C1_DIR = "data/llm_event_xs"`
  - `RoundData(name, sample: DataFrame indexed by int sample_idx, extractor: dict[int, list[dict]], truth: dict[int, list[dict]], audited: frozenset[int], anon_ids: tuple[int, ...], published: dict)`
  - `parse_labels(text: str) -> list[dict]`, `parse_sheet(text: str) -> dict[int, tuple[list, list, str]]`
  - `load_round(name, *, sample, extractor, sheet, key, anon, result: bytes) -> RoundData`
  - `load_rounds(read: Callable[[str], bytes]) -> dict[str, RoundData]` (input names `<kind>_<round>`)
  - `dir_reader(root: Path) -> Callable[[str], bytes]`
  - `match_events(truth: list[dict], pred: list[dict]) -> (pairs[(pred, truth)], false_pos, false_neg)`
  - `class_counts(truth: dict, pred: dict) -> dict[str, {"tp","fp","fn"}]`
  - `published_counts(data) -> dict`, `check_reproduction(rounds) -> None` (raises `ValueError` naming the round)

- [ ] **Step 1: Build the worktree environment**

Run: `cd /home/malecada/master_thesis/TradingAgents-jev-probe && uv sync --locked --all-extras --python 3.13.13`
Then: `.venv/bin/python -c "import tradingagents.research, pandas, requests, dotenv; print(tradingagents.research.__file__)"`
Expected: path under `/home/malecada/master_thesis/TradingAgents-jev-probe/tradingagents/research/`. If it points elsewhere, stop and report.

- [ ] **Step 2: Write the failing tests**

```python
# tests/research/test_llm_jev_truth.py
"""C1 truth rebuild from committed artifacts (read-only; no network)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import (  # noqa: E402
    check_reproduction, class_counts, dir_reader, load_rounds, match_events,
    parse_labels, parse_sheet, published_counts,
)


def test_parse_labels_single_multi_and_empty():
    assert parse_labels("regulatory/Republic/sev1") == [
        {"class": "regulatory", "asset": "Republic", "severity": 1}]
    assert parse_labels("regulatory/Binance/sev3; regulatory/Coinbase/sev3") == [
        {"class": "regulatory", "asset": "Binance", "severity": 3},
        {"class": "regulatory", "asset": "Coinbase", "severity": 3}]
    assert parse_labels("NO EVENTS") == []
    assert parse_labels("\\NO EVENTS") == []
    assert parse_labels("hack/Poly Network") == [{"class": "hack", "asset": "Poly Network"}]
    assert parse_labels("hack/A/B/sev2") == [{"class": "hack", "asset": "A/B", "severity": 2}]


def test_parse_labels_rejects_garbage():
    with pytest.raises(ValueError):
        parse_labels("just words")


def test_parse_sheet_reads_blocks():
    text = ("### row 4 (gdelt, 2024-12-19, disagreement)\n\n**H**\n\n"
            "- A: regulatory/Republic/sev1\n- B: NO EVENTS\n- VERDICT: \\_\\_\\_\\_B\n\n"
            "### row 9 (gdelt, 2022-08-08, agreement-check)\n\n"
            "- A: hack/X/sev2\n- B: hack/X/sev2\n- VERDICT: BOTH\n")
    rows = parse_sheet(text)
    assert rows[4] == ([{"class": "regulatory", "asset": "Republic", "severity": 1}], [], "B")
    assert rows[9][2] == "BOTH"


def test_match_and_counts_hand_example():
    truth = {1: [{"class": "hack", "asset": "X"}, {"class": "regulatory", "asset": "Y"}],
             2: [],
             3: [{"class": "listing_delisting", "asset": "Z"}]}
    pred = {1: [{"class": "hack", "asset": "X2"}],
            2: [{"class": "hack", "asset": "Q"}],
            3: [{"class": "listing_delisting", "asset": "Z"},
                {"class": "listing_delisting", "asset": "Z"}]}
    assert class_counts(truth, pred) == {
        "hack": {"tp": 1, "fp": 1, "fn": 0},
        "regulatory": {"tp": 0, "fp": 0, "fn": 1},
        "listing_delisting": {"tp": 1, "fp": 1, "fn": 0}}
    pairs, false_pos, false_neg = match_events(truth[1], pred[1])
    assert pairs == [({"class": "hack", "asset": "X2"}, {"class": "hack", "asset": "X"})]
    assert false_pos == [] and false_neg == [{"class": "regulatory", "asset": "Y"}]


def test_rebuild_reproduces_published_c1_counts():
    rounds = load_rounds(dir_reader(ROOT))
    for name, data in rounds.items():
        assert class_counts(data.truth, data.extractor) == published_counts(data), name
    check_reproduction(rounds)


def test_round_shapes():
    rounds = load_rounds(dir_reader(ROOT))
    v1, v2 = rounds["v1"], rounds["v2"]
    assert len(v1.sample) == 300 and len(v2.sample) == 100
    assert len(v1.audited) == 115 and len(v2.audited) == 39
    assert len(v1.anon_ids) == 50 and len(v2.anon_ids) == 50
    assert not set(v1.truth) & set(v2.truth)


def test_reproduction_guard_detects_tampering():
    v1 = load_rounds(dir_reader(ROOT))["v1"]
    idx = next(i for i, events in v1.truth.items() if events)
    tampered = dict(v1.truth)
    tampered[idx] = []
    with pytest.raises(ValueError, match="v1"):
        check_reproduction({"v1": replace(v1, truth=tampered)})
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_truth.py --import-mode=importlib -q`
Expected: collection error `ModuleNotFoundError: No module named 'llm_event_xs_truth'`.

- [ ] **Step 4: Write the implementation**

```python
# scripts/llm_event_xs_truth.py
"""Rebuild llm_c1_event_xs P0 ground truth from committed artifacts only.

The C1 scorer read claude-haiku pre-labels from a session scratchpad that no
longer exists. The blind adjudication sheets carry both label sets as
``class/asset/sevN`` lines, so ground truth is rebuilt from committed files:
adjudicated rows follow the human verdict, unaudited rows keep the
gpt-5.4-mini labels (C1 correct-by-agreement convention).
"""
from __future__ import annotations

from dataclasses import dataclass
import io
import json
from pathlib import Path
import re
from typing import Callable

import pandas as pd

ROUNDS = ("v1", "v2")
C1_DIR = "data/llm_event_xs"
ROUND_FILES = {
    "v1": {"sample": "p0_sample.parquet", "extractor": "p0_extractor_labels.json",
           "sheet": "p0_adjudication.md", "key": "p0_adjudication_key.json",
           "anon": "p0_extractor_labels_anon.json", "result": "p0_result.json"},
    "v2": {"sample": "p0_sample_v2.parquet", "extractor": "p0v2_extractor_labels.json",
           "sheet": "p0v2_adjudication.md", "key": "p0v2_adjudication_key.json",
           "anon": "p0v2_extractor_labels_anon.json", "result": "p0v2_result.json"},
}
_LABEL = re.compile(r"(\w+)/(.*?)(?:/sev(\d))?")


@dataclass(frozen=True)
class RoundData:
    name: str
    sample: pd.DataFrame
    extractor: dict
    truth: dict
    audited: frozenset
    anon_ids: tuple
    published: dict


def parse_labels(text: str) -> list[dict]:
    """Parse ``class/asset[/sevN]; ...`` or ``NO EVENTS`` into event dicts."""
    text = text.strip()
    if not text or text.upper().lstrip("\\").startswith("NO EVENTS"):
        return []
    events = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        match = _LABEL.fullmatch(part)
        if match is None:
            raise ValueError(f"unparseable label: {part!r}")
        event = {"class": match.group(1), "asset": match.group(2).strip()}
        if match.group(3):
            event["severity"] = int(match.group(3))
        events.append(event)
    return events


def parse_sheet(text: str) -> dict[int, tuple[list[dict], list[dict], str]]:
    """Adjudication rows: sample_idx -> (A labels, B labels, raw verdict)."""
    text = text.replace("\\_", "_")
    rows = {}
    for block in re.split(r"(?m)^(?=### row )", text):
        head = re.match(r"### row (\d+)", block)
        if head is None:
            continue
        a = re.search(r"(?m)^- A: (.*)$", block)
        b = re.search(r"(?m)^- B: (.*)$", block)
        verdict = re.search(r"VERDICT: *_*([^\n]*)", block)
        if not (a and b and verdict):
            raise ValueError(f"incomplete adjudication row {head.group(1)}")
        rows[int(head.group(1))] = (parse_labels(a.group(1)), parse_labels(b.group(1)),
                                    verdict.group(1).strip())
    return rows


def _truth_row(idx, verdict, a, b, key_row, extractor):
    v = verdict.upper().lstrip("\\").strip()
    if v.startswith("BOTH"):
        return extractor[idx]
    if v.startswith("NO EVENTS") or v.startswith("NEITHER"):
        return []  # every C1 NEITHER row resolved to no events
    if v[:1] in ("A", "B"):
        if key_row[v[0]] == "extractor":
            return extractor[idx]
        return a if v[0] == "A" else b
    raise ValueError(f"unparseable verdict for row {idx}: {verdict!r}")


def load_round(name: str, *, sample: bytes, extractor: bytes, sheet: bytes, key: bytes,
               anon: bytes, result: bytes) -> RoundData:
    frame = pd.read_parquet(io.BytesIO(sample))
    frame.index = frame["sample_idx"].astype(int).to_numpy()
    labels = {int(k): v["events"] for k, v in json.loads(extractor).items()}
    keys = json.loads(key)
    rows = parse_sheet(sheet.decode("utf-8"))
    truth = {}
    for idx in frame.index:
        idx = int(idx)
        if idx in rows:
            a, b, verdict = rows[idx]
            truth[idx] = _truth_row(idx, verdict, a, b, keys[str(idx)], labels)
        else:
            truth[idx] = labels[idx]
    anon_ids = tuple(sorted(int(k) for k in json.loads(anon)))
    return RoundData(name, frame, labels, truth, frozenset(rows), anon_ids,
                     json.loads(result)["per_class"])


def load_rounds(read: Callable[[str], bytes]) -> dict[str, RoundData]:
    """``read(name)`` returns the bytes of registered input ``<kind>_<round>``."""
    return {r: load_round(r, **{kind: read(f"{kind}_{r}") for kind in ROUND_FILES[r]})
            for r in ROUNDS}


def dir_reader(root: Path) -> Callable[[str], bytes]:
    """Reader over the committed C1 directory (tests and pre-registration checks)."""
    def read(name: str) -> bytes:
        kind, rnd = name.rsplit("_", 1)
        return (Path(root) / C1_DIR / ROUND_FILES[rnd][kind]).read_bytes()
    return read


def match_events(truth: list[dict], pred: list[dict]):
    """C1 rule: each predicted event greedily takes an unused truth event of its class."""
    used = [False] * len(truth)
    pairs, false_pos = [], []
    for p in pred:
        hit = next((j for j, t in enumerate(truth)
                    if not used[j] and t.get("class") == p.get("class")), None)
        if hit is None:
            false_pos.append(p)
        else:
            used[hit] = True
            pairs.append((p, truth[hit]))
    false_neg = [t for j, t in enumerate(truth) if not used[j]]
    return pairs, false_pos, false_neg


def class_counts(truth: dict, pred: dict) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}

    def bump(cls, kind):
        counts.setdefault(cls, {"tp": 0, "fp": 0, "fn": 0})[kind] += 1

    for idx in truth:
        pairs, false_pos, false_neg = match_events(truth[idx], pred[idx])
        for p, _ in pairs:
            bump(p.get("class", "?"), "tp")
        for p in false_pos:
            bump(p.get("class", "?"), "fp")
        for t in false_neg:
            bump(t.get("class", "?"), "fn")
    return counts


def published_counts(data: RoundData) -> dict[str, dict[str, int]]:
    return {c: {k: row[k] for k in ("tp", "fp", "fn")} for c, row in data.published.items()}


def check_reproduction(rounds: dict[str, RoundData]) -> None:
    """Blocking: the rebuilt truth must reproduce C1's published counts exactly."""
    for name, data in rounds.items():
        if class_counts(data.truth, data.extractor) != published_counts(data):
            raise ValueError(f"truth rebuild does not reproduce C1 {name} counts")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_truth.py --import-mode=importlib -q`
Expected: `7 passed`. If `test_rebuild_reproduces_published_c1_counts` fails, STOP: the plan cannot proceed (spec §3.1 blocking check). Report the per-class diff.

- [ ] **Step 6: Commit**

```bash
git add scripts/llm_event_xs_truth.py tests/research/test_llm_jev_truth.py
git commit -m "feat(llm-jev): rebuild C1 P0 truth from committed artifacts

Reproduces published C1 v1/v2 per-class counts exactly (blocking check).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Frozen questions, state and asset candidates

**Files:**
- Create: `scripts/llm_jev_questions.py`
- Test: `tests/research/test_llm_jev_questions.py`

**Interfaces:**
- Consumes: nothing from earlier tasks. The test reads `PROMPT`, `PROMPT_V2` from `scripts/llm_event_xs_extract.py`.
- Produces:
  - `CLASSES: tuple[str, ...]`, `GENERAL_RULES: str`, `CLASS_DEFINITIONS: dict`, `V2_RULES: dict`
  - `NONE_KEY = "none"`, `ASSET_INSTRUCTIONS: str`, `NONE_OPTION: str`, `CONTENT_LIMIT = 4000`, `MAX_CANDIDATES = 30`, `MAX_SPAN = 3`
  - `noul_instruction(cls: str) -> str`
  - `build_state(row: dict, transform: Callable[[str], str] | None = None) -> dict`
  - `candidates(row: dict) -> list[str]`
  - `build_questions(cands: list[str], *, reverse: bool, with_asset: bool = True) -> dict`. Keys are `ev_<class>` (noul) plus `asset` (choice with criteria keys `c00…` and `none`).
  - `questions_sha256() -> str`

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_questions.py
"""Frozen Jev wording, state and candidate generator (no network)."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_questions import (  # noqa: E402
    CLASS_DEFINITIONS, CLASSES, GENERAL_RULES, V2_RULES, build_questions, build_state,
    candidates, noul_instruction,
)


def test_class_definitions_are_verbatim_c1_prompt_text():
    from llm_event_xs_extract import PROMPT, PROMPT_V2
    flat = " ".join(PROMPT.split())
    flat_v2 = " ".join(PROMPT_V2.split())
    for cls, definition in CLASS_DEFINITIONS.items():
        assert f"- {cls}: {definition}" in flat, cls
    for cls, rule in V2_RULES.items():
        assert f"- {cls}: {rule}" in flat_v2, cls
    assert ("Only report events the article itself asserts as fact or formal action "
            "(not speculation, price commentary, or opinion).") in flat
    assert "No knowledge of later events; judge only the given text." in flat
    assert set(CLASS_DEFINITIONS) == set(CLASSES)


def test_noul_instruction_composition():
    text = noul_instruction("regulatory")
    assert text.startswith("The article reports a 'regulatory' event. Definition: government/agency action")
    assert "Additional rule: the target must be a crypto asset" in text
    assert text.endswith(GENERAL_RULES)
    assert "Additional rule" not in noul_instruction("hack")


def test_candidates_title_case_headline():
    row = {"store": "gdelt", "symbols": "BTCUSD", "summary": "",
           "headline": "Bitcoin Miner Greenidge Faces Setback as Regulator Denies Permit Application"}
    assert candidates(row) == [
        "Bitcoin", "Bitcoin Miner Greenidge", "Bitcoin Miner", "Miner Greenidge", "Miner",
        "Greenidge", "Setback", "Regulator", "Permit Application", "Permit", "Application"]


def test_candidates_alpaca_symbols_first():
    row = {"store": "alpaca", "symbols": "AVAXUSD,ETHUSD", "summary": "",
           "headline": "Kraken lists AVAX"}
    assert candidates(row) == ["AVAX", "ETH", "Kraken"]


def test_candidates_none_found():
    assert candidates({"store": "gdelt", "headline": "prices slide 5% as traders wait",
                       "summary": ""}) == []


def test_candidates_capped_at_30():
    headline = " and ".join(f"Name{i}" for i in range(40))
    assert len(candidates({"store": "gdelt", "headline": headline, "summary": ""})) == 30


def test_build_state_fields():
    row = {"headline": "Héadline 한국", "summary": float("nan"), "content": "x" * 5000}
    assert build_state(row) == {"headline": "Héadline 한국", "content": "x" * 4000}
    upper = build_state(row, str.upper)
    assert upper == {"headline": "HÉADLINE 한국", "content": "X" * 4000}
    assert build_state({"headline": None, "summary": "S"}) == {"headline": "", "summary": "S"}


def test_build_questions_shape():
    q = build_questions(["Kraken", "AVAX"], reverse=False)
    assert list(q) == [f"ev_{c}" for c in CLASSES] + ["asset"]
    assert all(q[f"ev_{c}"] == {"type": "noul", "instructions": noul_instruction(c)} for c in CLASSES)
    assert list(q["asset"]["criteria"]) == ["c00", "c01", "none"]
    assert q["asset"]["criteria"]["c01"] == "AVAX"
    assert q["asset"]["type"] == "choice"
    r = build_questions(["Kraken", "AVAX"], reverse=True)
    assert list(r["asset"]["criteria"]) == ["c01", "c00", "none"]
    assert "asset" not in build_questions([], reverse=False)
    assert "asset" not in build_questions(["X"], reverse=False, with_asset=False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_questions.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_questions'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/llm_jev_questions.py
"""Frozen Jev question wording, article state and asset candidates (charter §4).

Class definitions are C1's prompt class list plus its v2 additional rules,
verbatim. Any edit changes ``questions_sha256()`` and must precede registration.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Callable

CLASSES = ("hack", "regulatory", "listing_delisting", "unlock_emission",
           "upgrade_partnership", "insolvency_halt")
GENERAL_RULES = ("Only report events the article itself asserts as fact or formal action "
                 "(not speculation, price commentary, or opinion). No knowledge of later "
                 "events; judge only the given text.")
CLASS_DEFINITIONS = {
    "hack": "exploit, breach, funds stolen or drained from a protocol/venue",
    "regulatory": ("government/agency action — lawsuit, charge, settlement, ban, "
                   "license grant/revocation, emergency order"),
    "listing_delisting": "an exchange lists or delists a specific asset",
    "unlock_emission": ("token unlock, vesting cliff, or emission-schedule news "
                        "for a specific asset"),
    "upgrade_partnership": ("protocol upgrade, mainnet launch, hard fork, or a concrete "
                            "named partnership/acquisition involving the asset"),
    "insolvency_halt": ("insolvency, bankruptcy, withdrawal halt or suspension, depeg, "
                        "collapse of a venue/fund/stablecoin"),
}
V2_RULES = {
    "regulatory": ("the target must be a crypto asset, crypto company, or crypto venue. "
                   "Enforcement against non-crypto firms or people (even by SEC/CFTC) is NOT "
                   "an event. Personnel changes and prospective/planned regulation are NOT "
                   "events. Convictions, sentencing, and extradition of crypto-company "
                   "principals ARE regulatory events for the affected venue/asset."),
    "upgrade_partnership": ("requires a concrete named action that is signed, live, or "
                            "deployed. Exploration, MOUs, and conference statements are NOT "
                            "events."),
    "listing_delisting": ("includes IDO/IEO, exchange debut, \"X lists Y\", \"trading opens\", "
                          "and \"exchange adds support for Y\"."),
}
NONE_KEY = "none"
ASSET_INSTRUCTIONS = ("Which listed entity is primarily affected by the main event the article "
                      "reports? Prefer the affected crypto asset or protocol token; use the venue "
                      "(exchange/fund) when no single asset is affected.")
NONE_OPTION = "The article reports no qualifying event, or no listed entity fits."
CONTENT_LIMIT = 4000
MAX_CANDIDATES = 30
MAX_SPAN = 3
DICTIONARY = (
    "Bitcoin", "BTC", "Ethereum", "Ether", "ETH", "Solana", "SOL", "Ripple", "XRP", "Cardano",
    "ADA", "Dogecoin", "DOGE", "BNB", "Binance", "Coinbase", "Kraken", "FTX", "FTT", "Alameda",
    "Terra", "LUNA", "UST", "Celsius", "Three Arrows", "3AC", "Voyager", "BlockFi", "Genesis",
    "Tether", "USDT", "USDC", "Circle", "Polygon", "MATIC", "Avalanche", "AVAX", "Chainlink",
    "Polkadot", "Litecoin", "LTC", "Tron", "TRX", "Shiba Inu", "SHIB", "Uniswap", "Arbitrum",
    "Optimism", "Aptos", "Cosmos", "Stellar", "XLM", "Monero", "XMR", "Bitfinex", "Huobi", "OKX",
    "OKEx", "Gemini", "Bybit", "KuCoin", "Crypto.com", "Silvergate", "Signature Bank",
    "Silicon Valley Bank", "SVB", "Worldcoin", "EigenLayer", "Lido", "Aave", "MakerDAO", "Curve",
    "Ronin", "Axie Infinity", "Wormhole", "Poly Network", "Mt. Gox", "Grayscale", "MicroStrategy",
    "Sam Bankman-Fried", "SBF", "Do Kwon", "Changpeng Zhao", "CZ",
)
STOPWORDS = frozenset("""
a an the and or but nor of in on at to for from by with without over under after before as
into onto about amid against via vs per than then this that these those it its his her their
our your my we you they he she i is are was were be been being has have had do does did will
would can could may might must shall should not no new says said say reports report update
updates news price prices market markets today week year daily how why what when where who
which here there more most just now also up down out off back first last top big full live
faces face denies deny hits hit falls fall rises rise surges surge plunges plunge jumps jump
drops drop soars soar slides slide tumbles tumble gains gain loses lose wins win gets get adds
add lists list delists delist halts halt suspends suspend receives receive reaches reach
expands expand signs sign buys buy sells sell plans plan seeks seek warns warn calls call
takes take makes make sets set hires hire joins join backs partners partner acquires acquire
settles settle bans ban approves approve rejects reject launches launch files file sues sue
charges charge fines fine opens open closes close announces announce unveils unveil
completes complete
""".split())
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.&'$-]*")


def noul_instruction(cls: str) -> str:
    extra = f" Additional rule: {V2_RULES[cls]}" if cls in V2_RULES else ""
    return (f"The article reports a '{cls}' event. Definition: {CLASS_DEFINITIONS[cls]}."
            f"{extra} {GENERAL_RULES}")


def _text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value)


def build_state(row: dict, transform: Callable[[str], str] | None = None) -> dict:
    """Headline always; summary and content (first 4,000 chars) when non-empty."""
    state = {"headline": _text(row.get("headline"))}
    summary = _text(row.get("summary"))
    content = _text(row.get("content"))[:CONTENT_LIMIT]
    if summary.strip():
        state["summary"] = summary
    if content.strip():
        state["content"] = content
    if transform is not None:
        state = {k: transform(v) for k, v in state.items()}
    return state


def _qualifies(token: str) -> bool:
    if not token or token.lower() in STOPWORDS:
        return False
    has_alpha = any(ch.isalpha() for ch in token)
    return token[0].isupper() or (has_alpha and any(ch.isdigit() for ch in token))


def _flush(run: list[str], out: list[str]) -> None:
    for i in range(len(run)):
        for n in range(min(MAX_SPAN, len(run) - i), 0, -1):
            out.append(" ".join(run[i:i + n]))


def _spans(text: str) -> list[str]:
    out: list[str] = []
    run: list[str] = []
    for raw in _TOKEN.findall(text):
        token = raw.rstrip(".'-&$")
        if _qualifies(token):
            run.append(token)
        else:
            _flush(run, out)
            run = []
    _flush(run, out)
    return out


def candidates(row: dict) -> list[str]:
    """Alpaca symbols, dictionary names, then capitalized spans; dedup; cap 30."""
    text = " ".join(_text(row.get(f)) for f in ("headline", "summary"))
    found: list[str] = []
    if row.get("store") == "alpaca":
        for symbol in _text(row.get("symbols")).split(","):
            symbol = symbol.strip().upper()
            for quote in ("USDT", "USDC", "USD"):
                if symbol.endswith(quote) and len(symbol) > len(quote):
                    symbol = symbol[: -len(quote)]
                    break
            if symbol:
                found.append(symbol)
    for name in DICTIONARY:
        match = re.search(r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])",
                          text, re.IGNORECASE)
        if match:
            found.append(match.group(0))
    found.extend(_spans(text))
    seen: set[str] = set()
    out: list[str] = []
    for cand in found:
        if cand.lower() not in seen:
            seen.add(cand.lower())
            out.append(cand)
    return out[:MAX_CANDIDATES]


def build_questions(cands: list[str], *, reverse: bool, with_asset: bool = True) -> dict:
    questions = {f"ev_{c}": {"type": "noul", "instructions": noul_instruction(c)}
                 for c in CLASSES}
    if with_asset and cands:
        keys = [f"c{i:02d}" for i in range(len(cands))]
        order = list(reversed(keys)) if reverse else keys
        criteria = {k: cands[int(k[1:])] for k in order}
        criteria[NONE_KEY] = NONE_OPTION
        questions["asset"] = {"type": "choice", "instructions": ASSET_INSTRUCTIONS,
                              "criteria": criteria}
    return questions


def questions_sha256() -> str:
    payload = {"classes": CLASSES, "general": GENERAL_RULES, "definitions": CLASS_DEFINITIONS,
               "v2": V2_RULES, "noul": {c: noul_instruction(c) for c in CLASSES},
               "asset": ASSET_INSTRUCTIONS, "none": NONE_OPTION, "dictionary": DICTIONARY,
               "stopwords": sorted(STOPWORDS), "content_limit": CONTENT_LIMIT,
               "max_candidates": MAX_CANDIDATES, "max_span": MAX_SPAN}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_questions.py --import-mode=importlib -q`
Expected: `8 passed`.

- [ ] **Step 5: Pin the wording hash**

Run: `.venv/bin/python -c "import sys; sys.path.insert(0, 'scripts'); import llm_jev_questions as q; print(q.questions_sha256())"`
Append to `tests/research/test_llm_jev_questions.py`, with `<HASH>` replaced by the printed 64-hex value:

```python
QUESTIONS_SHA256 = "<HASH>"


def test_questions_hash_pinned():
    from llm_jev_questions import questions_sha256
    assert questions_sha256() == QUESTIONS_SHA256
```

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_questions.py --import-mode=importlib -q`
Expected: `9 passed`.

- [ ] **Step 6: Commit**

```bash
git add scripts/llm_jev_questions.py tests/research/test_llm_jev_questions.py
git commit -m "feat(llm-jev): frozen question wording, state and asset candidates

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: OpenRouter Decisions client

**Files:**
- Create: `scripts/llm_jev_client.py`
- Test: `tests/research/test_llm_jev_client.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `ENDPOINT`, `PROVIDER_SLUG = "typesafe"`, `PROVIDER_NAME = "TypeSafe"`, `KEY_NAMES`, `RETRY_STATUS`
  - `class JevError(RuntimeError)`
  - `load_api_key(env_file: Path) -> str`
  - `@dataclass JevClient(api_key, model, cost_cap_usd=5.0, max_attempts=5, expected_model=None, expected_provider=PROVIDER_NAME, session=None, sleep=time.sleep)` with counters `spent_usd`, `calls`, `max_call_usd`
  - `JevClient.decide(state, questions: dict) -> dict`. Returns the response JSON plus `_latency_s`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_client.py
"""OpenRouter Decisions client with a fake session (no network)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_client import ENDPOINT, JevClient, JevError, load_api_key  # noqa: E402

QUESTIONS = {"ev_hack": {"type": "noul", "instructions": "x"},
             "asset": {"type": "choice", "instructions": "y",
                       "criteria": {"c00": "A", "none": "n"}}}


def ok_payload(model="typesafe/jev-1.13-20260917", provider="TypeSafe", cost=0.0004, answers=None):
    return {"id": "gen-dec-1", "model": model, "provider": provider,
            "answers": answers if answers is not None else {
                "ev_hack": {"type": "noul", "noul": 0.9},
                "asset": {"type": "choice", "choice": "c00", "confidence": 0.8,
                          "probabilities": {"c00": 0.8, "none": 0.2}}},
            "usage": {"input_tokens": 400, "output_tokens": 20, "cost": cost}}


class FakeResponse:
    def __init__(self, status, payload=None, headers=None, text=""):
        self.status_code, self._payload = status, payload
        self.headers, self.text = headers or {}, text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses, self.bodies, self.headers = list(responses), [], []

    def post(self, url, json=None, timeout=None, headers=None):
        assert url == ENDPOINT
        self.bodies.append(json)
        self.headers.append(headers)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(responses, **kw):
    sleeps = []
    c = JevClient(api_key="sk-test", model="typesafe/jev-1.13-20260917",
                  expected_model="typesafe/jev-1.13-20260917",
                  session=FakeSession(responses), sleep=sleeps.append, **kw)
    return c, sleeps


def test_success_body_and_cost_tracking():
    c, _ = client([FakeResponse(200, ok_payload())])
    data = c.decide({"headline": "h"}, QUESTIONS)
    body = c.session.bodies[0]
    assert body["model"] == "typesafe/jev-1.13-20260917"
    assert body["provider"] == {"only": ["typesafe"], "allow_fallbacks": False}
    assert body["questions"] == QUESTIONS and body["state"] == {"headline": "h"}
    assert c.session.headers[0]["Authorization"] == "Bearer sk-test"
    assert c.calls == 1 and c.spent_usd == pytest.approx(0.0004)
    assert data["_latency_s"] >= 0


def test_retry_after_honoured_then_success():
    c, sleeps = client([FakeResponse(429, headers={"retry-after": "2"}),
                        FakeResponse(200, ok_payload())])
    c.decide({}, QUESTIONS)
    assert sleeps == [2.0] and c.calls == 1


def test_network_error_retried_then_exhausted():
    c, sleeps = client([requests.ConnectionError("boom")] * 5)
    with pytest.raises(JevError, match="network failure"):
        c.decide({}, QUESTIONS)
    assert len(sleeps) == 4


def test_retry_status_exhausted():
    c, _ = client([FakeResponse(503)] * 5)
    with pytest.raises(JevError, match="HTTP 503"):
        c.decide({}, QUESTIONS)


def test_insufficient_credits_fails_immediately():
    c, sleeps = client([FakeResponse(402)])
    with pytest.raises(JevError, match="402"):
        c.decide({}, QUESTIONS)
    assert sleeps == []


def test_model_drift_fails():
    c, _ = client([FakeResponse(200, ok_payload(model="typesafe/jev-1.14-20261001"))])
    with pytest.raises(JevError, match="model drift"):
        c.decide({}, QUESTIONS)


def test_provider_drift_fails():
    c, _ = client([FakeResponse(200, ok_payload(provider="Other"))])
    with pytest.raises(JevError, match="provider drift"):
        c.decide({}, QUESTIONS)


def test_missing_answer_fails():
    answers = {"ev_hack": {"type": "noul", "noul": 0.9}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="answers"):
        c.decide({}, QUESTIONS)


def test_incomplete_choice_probabilities_fail():
    answers = {"ev_hack": {"type": "noul", "noul": 0.9},
               "asset": {"type": "choice", "choice": "c00", "probabilities": {"c00": 1.0}}}
    c, _ = client([FakeResponse(200, ok_payload(answers=answers))])
    with pytest.raises(JevError, match="probabilities"):
        c.decide({}, QUESTIONS)


def test_cost_cap_blocks_before_posting():
    c, _ = client([FakeResponse(200, ok_payload(cost=0.0008)),
                   FakeResponse(200, ok_payload(cost=0.0008))], cost_cap_usd=0.001)
    c.decide({}, QUESTIONS)
    with pytest.raises(JevError, match="spend cap"):
        c.decide({}, QUESTIONS)
    assert len(c.session.bodies) == 1


def test_key_loading_and_repr(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTHER=1\nOPENROUTER_API=sk-abc\n")
    assert load_api_key(env) == "sk-abc"
    env.write_text("OPENROUTER_API_KEY=sk-def\n")
    assert load_api_key(env) == "sk-def"
    env.write_text("NOTHING=1\n")
    with pytest.raises(JevError, match="no OpenRouter key"):
        load_api_key(env)
    assert "sk-test" not in repr(client([])[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_client.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_client'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/llm_jev_client.py
"""Minimal OpenRouter Decisions API client for Jev (charter §4.1).

Never logs or returns the API key. Fails loudly on model/provider drift,
malformed answers, exhausted retries, missing credits or the spend cap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

import requests

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
PROVIDER_SLUG = "typesafe"
PROVIDER_NAME = "TypeSafe"
KEY_NAMES = ("OPENROUTER_API_KEY", "OPENROUTER_API")
RETRY_STATUS = frozenset({429, 500, 502, 503, 524, 529})


class JevError(RuntimeError):
    """Any condition that must stop a registered run."""


def load_api_key(env_file: Path) -> str:
    from dotenv import dotenv_values
    values = dotenv_values(env_file)
    for name in KEY_NAMES:
        if values.get(name):
            return values[name].strip()
    raise JevError(f"no OpenRouter key in {env_file} (expected one of {KEY_NAMES})")


@dataclass
class JevClient:
    api_key: str = field(repr=False)
    model: str
    cost_cap_usd: float = 5.0
    max_attempts: int = 5
    expected_model: str | None = None
    expected_provider: str | None = PROVIDER_NAME
    session: object = None
    sleep: object = time.sleep
    spent_usd: float = 0.0
    calls: int = 0
    max_call_usd: float = 0.0

    def decide(self, state, questions: dict) -> dict:
        if self.spent_usd + self.max_call_usd > self.cost_cap_usd:
            raise JevError(f"spend cap reached: {self.spent_usd:.6f} USD of {self.cost_cap_usd}")
        body = {"model": self.model, "state": state, "questions": questions,
                "provider": {"only": [PROVIDER_SLUG], "allow_fallbacks": False}}
        session = self.session or requests
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                response = session.post(ENDPOINT, json=body, timeout=60,
                                        headers={"Authorization": f"Bearer {self.api_key}"})
            except requests.RequestException as exc:
                if attempt == self.max_attempts:
                    raise JevError(f"network failure after {attempt} attempts: "
                                   f"{type(exc).__name__}") from None
                self.sleep(min(2 ** attempt, 30))
                continue
            if response.status_code == 200:
                data = response.json()
                self._check(data, questions)
                cost = float(data["usage"]["cost"])
                self.spent_usd += cost
                self.calls += 1
                self.max_call_usd = max(self.max_call_usd, cost)
                data["_latency_s"] = time.monotonic() - started
                return data
            if response.status_code == 402:
                raise JevError("OpenRouter reports insufficient credits (HTTP 402)")
            if response.status_code in RETRY_STATUS and attempt < self.max_attempts:
                retry_after = str(response.headers.get("retry-after") or "")
                is_number = retry_after.replace(".", "", 1).isdigit()
                self.sleep(float(retry_after) if is_number else min(2 ** attempt, 30))
                continue
            raise JevError(f"HTTP {response.status_code}: {str(response.text)[:300]}")
        raise JevError("retry loop exited without a response")

    def _check(self, data: dict, questions: dict) -> None:
        if self.expected_model is not None and data.get("model") != self.expected_model:
            raise JevError(f"model drift: got {data.get('model')!r}, "
                           f"pinned {self.expected_model!r}")
        if self.expected_provider is not None and data.get("provider") != self.expected_provider:
            raise JevError(f"provider drift: got {data.get('provider')!r}")
        answers = data.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise JevError("answers do not cover exactly the asked questions")
        for name, question in questions.items():
            answer = answers[name]
            if answer.get("type") != question["type"]:
                raise JevError(f"answer type mismatch for {name}")
            if question["type"] == "noul" and not isinstance(answer.get("noul"), (int, float)):
                raise JevError(f"noul probability missing for {name}")
            if question["type"] == "choice":
                probs = answer.get("probabilities")
                if not isinstance(probs, dict) or set(probs) != set(question["criteria"]):
                    raise JevError(f"choice probabilities incomplete for {name}")
        if "cost" not in (data.get("usage") or {}):
            raise JevError("usage.cost missing from response")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_client.py --import-mode=importlib -q`
Expected: `11 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/llm_jev_client.py tests/research/test_llm_jev_client.py
git commit -m "feat(llm-jev): OpenRouter Decisions client with pinning and spend cap

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Two-call labeling and aggregation

**Files:**
- Create: `scripts/llm_jev_labels.py`
- Test: `tests/research/test_llm_jev_labels.py`

**Interfaces:**
- Consumes:
  - `CLASSES`, `NONE_KEY`, `build_questions`, `build_state`, `candidates` (Task 2)
  - `anonymize(text) -> str` from `scripts/llm_event_xs_extract.py`
  - Any object with `decide(state, questions) -> dict` and `spent_usd` (Task 3 `JevClient`)
  - `RoundData` (Task 1)
- Produces:
  - `THRESHOLD = 0.5`
  - `aggregate(first: dict, second: dict, cands: list[str]) -> dict`. Keys: `probs`, `delta`, `events` (`[{"class","asset"}]`), `asset`, `asset_probs`, `flip`, `candidates`, `raw` (2 trimmed responses keeping `id, model, provider, answers, usage, _latency_s`).
  - `label_article(client, row: dict, *, anon: bool) -> dict`
  - `label_rounds(rounds, client, progress=print) -> tuple[dict, dict]`: named/anon labels keyed `str(sample_idx)`, each with `round`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_labels.py
"""Aggregation of two Jev calls and article labeling with a scripted client."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_jev_labels import aggregate, label_article  # noqa: E402
from llm_jev_questions import CLASSES  # noqa: E402


def response(nouls: dict, asset: dict | None = None) -> dict:
    answers = {f"ev_{c}": {"type": "noul", "noul": nouls.get(c, 0.0)} for c in CLASSES}
    if asset is not None:
        answers["asset"] = {"type": "choice", "choice": max(asset, key=asset.get),
                            "confidence": 0.9, "probabilities": asset}
    return {"id": "gen-x", "model": "m", "provider": "TypeSafe", "answers": answers,
            "usage": {"cost": 1e-5}, "_latency_s": 0.2}


class ScriptedClient:
    def __init__(self, responses):
        self.responses, self.calls, self.spent_usd = list(responses), [], 0.0

    def decide(self, state, questions):
        self.calls.append((state, questions))
        return self.responses.pop(0)


def test_threshold_is_inclusive():
    out = aggregate(response({"hack": 0.5, "regulatory": 0.49}),
                    response({"hack": 0.5, "regulatory": 0.49}), [])
    assert [e["class"] for e in out["events"]] == ["hack"]
    assert out["flip"] is False


def test_mean_and_flip():
    out = aggregate(response({"hack": 0.7}), response({"hack": 0.2}), [])
    assert out["probs"]["hack"] == pytest.approx(0.45)
    assert out["delta"]["hack"] == pytest.approx(0.5)
    assert out["events"] == [] and out["flip"] is True


def test_asset_argmax_over_mean():
    first = response({"hack": 0.9}, {"c00": 0.6, "c01": 0.3, "none": 0.1})
    second = response({"hack": 0.9}, {"c00": 0.2, "c01": 0.7, "none": 0.1})
    out = aggregate(first, second, ["Poly", "Ronin"])
    assert out["asset"] == "Ronin"
    assert out["events"] == [{"class": "hack", "asset": "Ronin"}]
    assert out["asset_probs"]["c01"] == pytest.approx(0.5)


def test_none_asset_wins():
    probs = {"c00": 0.1, "none": 0.9}
    out = aggregate(response({"hack": 0.8}, probs), response({"hack": 0.8}, probs), ["X"])
    assert out["asset"] is None and out["events"] == [{"class": "hack", "asset": None}]


def test_no_asset_question():
    out = aggregate(response({"regulatory": 0.9}), response({"regulatory": 0.9}), [])
    assert out["asset"] is None and out["asset_probs"] == {}
    assert out["raw"][0]["_latency_s"] == 0.2 and "answers" in out["raw"][0]


def test_label_article_named_reverses_candidates():
    row = {"store": "alpaca", "symbols": "AVAXUSD", "headline": "Kraken lists AVAX", "summary": ""}
    probs = {"c00": 0.8, "c01": 0.1, "none": 0.1}
    client = ScriptedClient([response({"listing_delisting": 0.9}, probs)] * 2)
    out = label_article(client, row, anon=False)
    first_q, second_q = client.calls[0][1], client.calls[1][1]
    assert list(first_q["asset"]["criteria"]) == ["c00", "c01", "none"]
    assert list(second_q["asset"]["criteria"]) == ["c01", "c00", "none"]
    assert out["candidates"] == ["AVAX", "Kraken"] and out["asset"] == "AVAX"


def test_label_article_anon_masks_and_skips_asset():
    row = {"store": "alpaca", "symbols": "BNBUSD", "headline": "Binance halts withdrawals",
           "summary": ""}
    client = ScriptedClient([response({"insolvency_halt": 0.9})] * 2)
    out = label_article(client, row, anon=True)
    for state, questions in client.calls:
        assert "Binance" not in state["headline"] and "ENTITY_12" in state["headline"]
        assert "asset" not in questions
    assert out["candidates"] == [] and out["asset"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_labels.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_labels'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/llm_jev_labels.py
"""Two-call Jev labeling per article and aggregation (charter §4.5)."""
from __future__ import annotations

from typing import Callable

from llm_event_xs_extract import anonymize
from llm_jev_questions import CLASSES, NONE_KEY, build_questions, build_state, candidates

THRESHOLD = 0.5
_KEEP = ("id", "model", "provider", "answers", "usage", "_latency_s")


def _noul(response: dict, cls: str) -> float:
    return float(response["answers"][f"ev_{cls}"]["noul"])


def aggregate(first: dict, second: dict, cands: list[str]) -> dict:
    probs = {c: (_noul(first, c) + _noul(second, c)) / 2 for c in CLASSES}
    delta = {c: abs(_noul(first, c) - _noul(second, c)) for c in CLASSES}
    set_first = {c for c in CLASSES if _noul(first, c) >= THRESHOLD}
    set_second = {c for c in CLASSES if _noul(second, c) >= THRESHOLD}
    asset, asset_probs = None, {}
    if "asset" in first["answers"]:
        p1 = first["answers"]["asset"]["probabilities"]
        p2 = second["answers"]["asset"]["probabilities"]
        asset_probs = {k: (float(p1[k]) + float(p2[k])) / 2 for k in sorted(p1)}
        best = max(asset_probs, key=asset_probs.get)  # ties: lowest key in sorted order
        asset = None if best == NONE_KEY else cands[int(best[1:])]
    events = [{"class": c, "asset": asset} for c in CLASSES if probs[c] >= THRESHOLD]
    return {"probs": probs, "delta": delta, "events": events, "asset": asset,
            "asset_probs": asset_probs, "flip": set_first != set_second,
            "candidates": list(cands),
            "raw": [{k: r[k] for k in _KEEP if k in r} for r in (first, second)]}


def label_article(client, row: dict, *, anon: bool) -> dict:
    """Two calls: candidates forward then reversed; anonymized rows ask classes only."""
    state = build_state(row, anonymize if anon else None)
    cands = [] if anon else candidates(row)
    responses = [client.decide(state, build_questions(cands, reverse=reverse,
                                                      with_asset=not anon))
                 for reverse in (False, True)]
    return aggregate(responses[0], responses[1], cands)


def label_rounds(rounds: dict, client,
                 progress: Callable[[str], None] = print) -> tuple[dict, dict]:
    """Named labels for all articles; anonymized labels for the C1 50+50 subsets."""
    named, anon = {}, {}
    for name, data in rounds.items():
        for n, (idx, row) in enumerate(data.sample.iterrows(), 1):
            named[str(int(idx))] = {"round": name,
                                    **label_article(client, row.to_dict(), anon=False)}
            if n % 50 == 0:
                progress(f"{name} named {n}/{len(data.sample)} spent={client.spent_usd:.4f}")
        for idx in data.anon_ids:
            anon[str(idx)] = {"round": name,
                              **label_article(client, data.sample.loc[idx].to_dict(), anon=True)}
        progress(f"{name} anon {len(data.anon_ids)} done spent={client.spent_usd:.4f}")
    return named, anon
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_labels.py --import-mode=importlib -q`
Expected: `7 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/llm_jev_labels.py tests/research/test_llm_jev_labels.py
git commit -m "feat(llm-jev): two-call labeling and aggregation

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Blind review sheet (build, render, parse, apply)

**Files:**
- Create: `scripts/llm_jev_review.py`
- Test: `tests/research/test_llm_jev_review.py`

**Interfaces:**
- Consumes:
  - `norm_asset` from `scripts/llm_event_xs_p0_score.py`
  - `match_events`, `parse_labels`, `RoundData` (Task 1)
  - `build_state` (Task 2)
  - Label dicts from Task 4 (`jev[str(idx)]["events"]`)
- Produces:
  - `SEED = 20260929`, `N_CHECKS = 20`
  - `auto_asset_match(a, b) -> bool`, `class_set(events) -> tuple[str, ...]`, `label_string(events) -> str`
  - `build_review(rounds, jev, seed=SEED, n_checks=N_CHECKS) -> (rows: list[dict], key: dict[str, dict])`. Row fields: `row, kind ('class'|'check'|'entity'), sample_idx, store, date, text, entity_class, A, B, same`. Key fields: `kind, sample_idx, entity_class, A, B` with values `'jev'|'stored'`.
  - `render_markdown(rows) -> str`
  - `parse_filled(text, rows) -> dict[int, {"verdict", "labels", "same": {cls: bool}}]` (raises `ValueError` listing all problems)
  - `apply_review(rounds, jev, rows, key, filled) -> (truth: dict[int, list], same: dict["idx|class", bool], stats: dict)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_review.py
"""Blind review sheet: construction, blindness, rendering, parsing, application."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import RoundData  # noqa: E402
from llm_jev_review import (  # noqa: E402
    apply_review, auto_asset_match, build_review, parse_filled, render_markdown,
)


def make_round(truth: dict, audited: set, name: str = "v1") -> RoundData:
    idxs = sorted(truth)
    frame = pd.DataFrame({"sample_idx": idxs, "headline": [f"Headline {i}" for i in idxs],
                          "summary": "", "content": "", "store": "gdelt", "symbols": "BTCUSD",
                          "event_ts": pd.Timestamp("2023-01-02", tz="UTC"), "prefilter": True})
    frame.index = frame["sample_idx"].to_numpy()
    return RoundData(name, frame, dict(truth), dict(truth), frozenset(audited), (), {})


def ev(cls, asset):
    return {"class": cls, "asset": asset}


@pytest.fixture()
def scenario():
    truth = {1: [ev("hack", "Poly Network")], 2: [ev("regulatory", "SEC target")]}
    truth.update({i: [] for i in range(3, 40)})
    rounds = {"v1": make_round(truth, audited={1})}
    jev = {"1": {"events": [ev("hack", "Ronin")]}, "2": {"events": []}}
    jev.update({str(i): {"events": []} for i in range(3, 40)})
    return rounds, jev


def test_auto_asset_match_rules():
    assert auto_asset_match("BTC", "Bitcoin")
    assert auto_asset_match("North Korean", "North Korean computer programmers")
    assert auto_asset_match("Poly Network", "poly network")
    assert not auto_asset_match("Binance", "Coinbase")
    assert not auto_asset_match(None, "X") and not auto_asset_match("X", "")


def test_build_review_kinds_blindness_and_determinism(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    kinds = sorted(r["kind"] for r in rows)
    assert kinds.count("entity") == 1 and kinds.count("class") == 1
    assert kinds.count("check") == 20
    entity = next(r for r in rows if r["kind"] == "entity")
    assert {entity["A"], entity["B"]} == {"Ronin", "Poly Network"}
    k = key[str(entity["row"])]
    assert entity[next(s for s in "AB" if k[s] == "jev")] == "Ronin"
    klass = next(r for r in rows if r["kind"] == "class")
    assert {klass["A"], klass["B"]} == {"NO EVENTS", "regulatory/SEC target"}
    blob = json.dumps(rows)
    assert '"jev"' not in blob and '"stored"' not in blob
    assert build_review(rounds, jev) == (rows, key)


def fill(text: str, rows: list[dict], verdicts: dict[str, str], same: str = "Y") -> str:
    kinds = {r["row"]: r["kind"] for r in rows}
    out = []
    for block in re.split(r"(?m)^(?=### row )", text):
        head = re.match(r"### row (\d+)", block)
        if head:
            kind = kinds[int(head.group(1))]
            if kind in verdicts:
                block = block.replace("- VERDICT: \n", f"- VERDICT: {verdicts[kind]}\n")
            block = re.sub(r"(?m)^(- SAME \([a-z_]+\):) $", rf"\1 {same}", block)
        out.append(block)
    return "".join(out)


def test_render_parse_apply_roundtrip(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": "A", "check": "BOTH"})
    filled = parse_filled(text, rows)
    truth, same, stats = apply_review(rounds, jev, rows, key, filled)
    klass = next(r for r in rows if r["kind"] == "class")
    expected = [] if key[str(klass["row"])]["A"] == "jev" else [ev("regulatory", "SEC target")]
    assert truth[2] == expected
    assert same == {"1|hack": True}
    assert stats["check_rows"] == 20 and stats["check_error_rate"] == 0.0
    assert truth[1] == [ev("hack", "Poly Network")]


def test_neither_and_no_events_on_checks(scenario):
    rounds, jev = scenario
    rows, key = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows,
                {"class": "neither: hack/Poly", "check": "no events"}, same="n")
    filled = parse_filled(text, rows)
    truth, same, stats = apply_review(rounds, jev, rows, key, filled)
    assert truth[2] == [{"class": "hack", "asset": "Poly"}]
    assert same == {"1|hack": False}
    assert stats["check_error_rate"] == 1.0


def test_parse_normalizes_case_and_yes_no(scenario):
    rounds, jev = scenario
    rows, _ = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": " b ", "check": "Both"}, same="yes")
    filled = parse_filled(text, rows)
    assert {f["verdict"] for f in filled.values() if f["verdict"]} <= {"B", "BOTH"}


def test_parse_reports_all_problems(scenario):
    rounds, jev = scenario
    rows, _ = build_review(rounds, jev)
    text = fill(render_markdown(rows), rows, {"class": "NEITHER", "check": "maybe"}, same="")
    with pytest.raises(ValueError) as err:
        parse_filled(text, rows)
    message = str(err.value)
    assert "NEITHER" in message and "maybe" in message and "SAME" in message
    assert message.count("row ") >= 22
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_review.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_review'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/llm_jev_review.py
"""Blind review sheet for Jev disputes (charter §3.2): build, render, parse, apply.

Class disputes offer A, B, NO EVENTS or NEITHER (BOTH is not offered because
the class sets differ). Agreement spot-checks offer BOTH, NO EVENTS or
NEITHER. Entity questions ask whether two names denote the same entity. A Jev
asset of ``none`` is never sent for entity review; it counts as a mismatch.
"""
from __future__ import annotations

import random
import re

from llm_event_xs_p0_score import norm_asset
from llm_event_xs_truth import match_events, parse_labels
from llm_jev_questions import build_state

SEED = 20260929
N_CHECKS = 20
CLASS_VERDICTS = frozenset({"A", "B", "NO EVENTS"})
CHECK_VERDICTS = frozenset({"BOTH", "NO EVENTS"})
HEADER = """# Jev P0 blind review — llm-jev-p0-label-20260929

Judge only from the article text shown. Do not open `review_key.json`.
Classes: hack, regulatory, listing_delisting, unlock_emission, upgrade_partnership, insolvency_halt.

- `class` rows: VERDICT is `A`, `B`, `NO EVENTS`, or `NEITHER: class/asset; class/asset`.
- `check` rows: VERDICT is `BOTH` (labels correct), `NO EVENTS`, or `NEITHER: class/asset; ...`.
- `SAME (class)` lines: `Y` if the two names refer to the same affected entity, else `N`.
"""


def _tokens(name: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", norm_asset(name))


def auto_asset_match(a, b) -> bool:
    """Equal after C1 normalization/aliases, or one is a contiguous token run of the other."""
    if not a or not b:
        return False
    x, y = _tokens(a), _tokens(b)
    if not x or not y:
        return False
    short, long_ = (x, y) if len(x) <= len(y) else (y, x)
    return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))


def class_set(events: list[dict]) -> tuple[str, ...]:
    return tuple(sorted({e["class"] for e in events}))


def label_string(events: list[dict]) -> str:
    if not events:
        return "NO EVENTS"
    ordered = sorted(events, key=lambda e: (e["class"], str(e.get("asset"))))
    return "; ".join(f"{e['class']}/{e.get('asset') or 'none'}" for e in ordered)


def _entity_pairs(truth_events: list[dict], jev_events: list[dict]):
    """Same-class pairs whose names fail the automatic rule; one per class."""
    pairs, _, _ = match_events(truth_events, jev_events)
    out, seen = [], set()
    for p, t in pairs:
        if (p.get("asset") and t.get("asset") and p["class"] not in seen
                and not auto_asset_match(p["asset"], t["asset"])):
            seen.add(p["class"])
            out.append((p["class"], p["asset"], t["asset"]))
    return out


def build_review(rounds: dict, jev: dict, seed: int = SEED, n_checks: int = N_CHECKS):
    """Return (rows, key). ``jev`` maps str(sample_idx) -> label dict with ``events``."""
    rng = random.Random(seed)
    items, agree = [], []
    for data in rounds.values():
        for idx in data.sample.index:
            idx = int(idx)
            stored, mine = data.truth[idx], jev[str(idx)]["events"]
            if idx not in data.audited and class_set(stored) != class_set(mine):
                items.append(("class", data, idx, None, None, None))
                continue
            if idx not in data.audited:
                agree.append((data, idx))
            for cls, j_name, t_name in _entity_pairs(stored, mine):
                items.append(("entity", data, idx, cls, j_name, t_name))
    for data, idx in rng.sample(agree, min(n_checks, len(agree))):
        items.append(("check", data, idx, None, None, None))
    rng.shuffle(items)
    rows, key = [], {}
    for number, (kind, data, idx, cls, j_name, t_name) in enumerate(items, 1):
        jev_side = "A" if rng.random() < 0.5 else "B"
        other = "B" if jev_side == "A" else "A"
        stored, mine = data.truth[idx], jev[str(idx)]["events"]
        record = data.sample.loc[idx]
        row = {"row": number, "kind": kind, "sample_idx": idx, "store": str(record["store"]),
               "date": str(record["event_ts"])[:10], "text": build_state(record.to_dict()),
               "entity_class": cls, "same": []}
        if kind == "entity":
            row[jev_side], row[other] = j_name, t_name
            row["same"] = [{"class": cls}]
        else:
            row[jev_side], row[other] = label_string(mine), label_string(stored)
            if kind == "class":
                row["same"] = [{"class": c} for c, _, _ in _entity_pairs(stored, mine)]
        rows.append(row)
        key[str(number)] = {"kind": kind, "sample_idx": idx, "entity_class": cls,
                            jev_side: "jev", other: "stored"}
    return rows, key


def render_markdown(rows: list[dict]) -> str:
    out = [HEADER]
    for row in rows:
        out.append(f"### row {row['row']} ({row['store']}, {row['date']}, {row['kind']})\n")
        text = row["text"]
        out.append(f"**{text.get('headline', '')}**\n")
        for name in ("summary", "content"):
            if text.get(name):
                out.append(text[name].replace("\n", " ") + "\n")
        if row["kind"] == "entity":
            out.append(f"- Event class: {row['entity_class']}")
        out.append(f"- A: {row['A']}")
        out.append(f"- B: {row['B']}")
        if row["kind"] != "entity":
            out.append("- VERDICT: ")
        for pair in row["same"]:
            out.append(f"- SAME ({pair['class']}): ")
        out.append("")
    return "\n".join(out) + "\n"


def parse_filled(text: str, rows: list[dict]) -> dict[int, dict]:
    blocks = {}
    for block in re.split(r"(?m)^(?=### row )", text):
        head = re.match(r"### row (\d+)", block)
        if head:
            blocks[int(head.group(1))] = block
    problems, parsed = [], {}
    for row in rows:
        number = row["row"]
        block = blocks.get(number)
        if block is None:
            problems.append(f"row {number}: missing from sheet")
            continue
        entry = {"verdict": None, "labels": None, "same": {}}
        if row["kind"] != "entity":
            match = re.search(r"(?m)^- VERDICT:[ \t]*(.*)$", block)
            raw = (match.group(1) if match else "").strip()
            upper = raw.upper()
            allowed = CLASS_VERDICTS if row["kind"] == "class" else CHECK_VERDICTS
            if upper in allowed:
                entry["verdict"] = upper
            elif upper.startswith("NEITHER") and ":" in raw:
                try:
                    entry["verdict"], entry["labels"] = "NEITHER", parse_labels(raw.split(":", 1)[1])
                except ValueError as exc:
                    problems.append(f"row {number}: bad NEITHER labels ({exc})")
            else:
                problems.append(f"row {number}: verdict {raw!r} not in {sorted(allowed)} "
                                f"or 'NEITHER: labels'")
        for pair in row["same"]:
            match = re.search(rf"(?m)^- SAME \({re.escape(pair['class'])}\):[ \t]*(.*)$", block)
            answer = (match.group(1) if match else "").strip().upper()
            if answer in ("Y", "YES"):
                entry["same"][pair["class"]] = True
            elif answer in ("N", "NO"):
                entry["same"][pair["class"]] = False
            else:
                problems.append(f"row {number}: SAME ({pair['class']}) must be Y or N")
        parsed[number] = entry
    if problems:
        raise ValueError("review sheet incomplete:\n" + "\n".join(problems))
    return parsed


def apply_review(rounds: dict, jev: dict, rows: list[dict], key: dict, filled: dict):
    truth = {int(i): list(e) for data in rounds.values() for i, e in data.truth.items()}
    stored = dict(truth)
    same, checks, check_errors = {}, 0, 0
    for row in rows:
        info, entry = key[str(row["row"])], filled[row["row"]]
        idx = info["sample_idx"]
        for cls, answer in entry["same"].items():
            same[f"{idx}|{cls}"] = answer
        if row["kind"] == "entity":
            continue
        verdict = entry["verdict"]
        if verdict in ("A", "B"):
            truth[idx] = list(jev[str(idx)]["events"]) if info[verdict] == "jev" else stored[idx]
        elif verdict == "NO EVENTS":
            truth[idx] = []
        elif verdict == "NEITHER":
            truth[idx] = entry["labels"]
        if row["kind"] == "check":
            checks += 1
            check_errors += verdict != "BOTH"
    stats = {"rows": len(rows), "class_rows": sum(r["kind"] == "class" for r in rows),
             "check_rows": checks, "entity_rows": sum(r["kind"] == "entity" for r in rows),
             "check_error_rate": check_errors / checks if checks else None}
    return truth, same, stats
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_review.py --import-mode=importlib -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/llm_jev_review.py tests/research/test_llm_jev_review.py
git commit -m "feat(llm-jev): blind review sheet build/render/parse/apply

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Gates and diagnostics

**Files:**
- Create: `scripts/llm_jev_score.py`
- Test: `tests/research/test_llm_jev_score.py`

**Interfaces:**
- Consumes:
  - `class_counts`, `match_events` (Task 1)
  - `CLASSES` (Task 2)
  - `auto_asset_match`, `class_set` (Task 5)
  - Label dicts (Task 4)
- Produces:
  - `FLOORS`, `POOL_BELOW = 10`, `CORPUS_ARTICLES = 377825`
  - `wilson(k, n) -> list[float] | None`
  - `gate_rows(counts) -> dict`
  - `asset_link(truth, pred, same) -> dict`
  - `anon_agreement(named, anon) -> dict`
  - `evaluate(truth, jev_events, same, named, anon) -> {"verdict", "gate_rows", "gates"}`
  - `diagnostics(rounds, truth, named, meta) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_score.py
"""Gate arithmetic and diagnostics on hand-built cases."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from llm_event_xs_truth import RoundData  # noqa: E402
from llm_jev_questions import CLASSES  # noqa: E402
from llm_jev_score import (  # noqa: E402
    anon_agreement, asset_link, diagnostics, evaluate, gate_rows, wilson,
)


def ev(cls, asset):
    return {"class": cls, "asset": asset}


def lab(events, probs=None, cands=("X",)):
    probs = probs or {c: (0.9 if any(e["class"] == c for e in events) else 0.1) for c in CLASSES}
    raw = {"answers": {f"ev_{c}": {"type": "noul", "noul": probs[c]} for c in CLASSES},
           "usage": {"cost": 0.0002}, "_latency_s": 0.3}
    return {"events": events, "probs": probs, "delta": {c: 0.0 for c in CLASSES},
            "flip": False, "candidates": list(cands),
            "asset": events[0]["asset"] if events else None, "raw": [raw, raw]}


def test_wilson_known_value():
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-3) and hi == pytest.approx(0.9433, abs=1e-3)
    assert wilson(0, 0) is None


def test_gate_rows_pooling():
    rows = gate_rows({"hack": {"tp": 9, "fp": 1, "fn": 1},
                      "regulatory": {"tp": 3, "fp": 2, "fn": 1},
                      "unlock_emission": {"tp": 1, "fp": 0, "fn": 1}})
    assert set(rows) == {"hack", "pooled_small"}
    assert rows["hack"]["precision"] == pytest.approx(0.9)
    assert rows["pooled_small"]["tp"] == 4 and rows["pooled_small"]["fp"] == 2
    assert rows["pooled_small"]["precision"] == pytest.approx(4 / 6)
    assert rows["pooled_small"]["recall"] == pytest.approx(4 / 6)


def test_asset_link_uses_review_and_rejects_none():
    truth = {1: [ev("hack", "Poly Network")], 2: [ev("hack", "Bitcoin")]}
    pred = {1: [ev("hack", "Ronin")], 2: [ev("hack", None)]}
    assert asset_link(truth, pred, {"1|hack": True, "2|hack": True})["value"] == 0.5
    assert asset_link(truth, pred, {})["value"] == 0.0


def test_anon_agreement():
    named = {"1": {"events": [ev("hack", "X")]}, "2": {"events": []}}
    anon = {"1": {"events": [ev("hack", None)]}, "2": {"events": [ev("regulatory", None)]}}
    assert anon_agreement(named, anon) == {"agree": 1, "n": 2, "value": 0.5}


def test_evaluate_pass_and_fail():
    truth = {i: [ev("hack", "Bitcoin")] for i in range(12)}
    named = {str(i): {"events": [ev("hack", "BTC")]} for i in range(12)}
    events = {i: named[str(i)]["events"] for i in range(12)}
    result = evaluate(truth, events, {}, named, dict(named))
    assert result["verdict"] == "PASS"
    assert result["gates"]["prefilter_recall"]["status"] == "not_applicable"
    worse = {i: events[i] + [ev("regulatory", "BTC")] for i in range(12)}
    assert evaluate(truth, worse, {}, named, dict(named))["verdict"] == "FAIL"


def test_diagnostics_shape():
    frame = pd.DataFrame({"sample_idx": [1, 2], "prefilter": [True, False],
                          "store": "gdelt", "headline": "h", "summary": "", "content": ""})
    frame.index = frame["sample_idx"].to_numpy()
    truth = {1: [ev("hack", "X")], 2: []}
    rounds = {"v1": RoundData("v1", frame, dict(truth), dict(truth), frozenset(), (), {})}
    named = {"1": lab([ev("hack", "X")]), "2": lab([])}
    meta = {"spent_usd": 0.0008, "calls": 4}
    out = diagnostics(rounds, truth, named, meta)
    assert out["asset_candidate_coverage"]["value"] == 1.0
    assert out["stability"]["flip_rate"] == 0.0
    assert out["threshold_sweep"]["0.5"]["hack"]["tp"] == 1
    assert out["cost"]["per_article_usd"] == pytest.approx(0.0004)
    assert out["prefilter_negative_recall"]["value"] is None
    assert len(out["reliability"]["hack"]) == 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_score.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_score'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/llm_jev_score.py
"""P0 gates and diagnostics for the Jev probe (charter §5–6). Nothing is selected here."""
from __future__ import annotations

import math

from llm_event_xs_truth import class_counts, match_events
from llm_jev_questions import CLASSES
from llm_jev_review import auto_asset_match, class_set

FLOORS = {"precision": 0.8, "recall": 0.6, "asset_link": 0.9, "anon_agreement": 0.8}
POOL_BELOW = 10
CORPUS_ARTICLES = 57076 + 320749  # C1 frozen corpus counts (llm_event_xs_p0_score)
Z95 = 1.959963984540054


def wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    denom = 1 + Z95 ** 2 / n
    center = (p + Z95 ** 2 / (2 * n)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / denom
    return [center - half, center + half]


def gate_rows(counts: dict) -> dict:
    """Classes with < 10 true events pooled into ``pooled_small`` (C1 rule)."""
    rows, pooled = {}, {"tp": 0, "fp": 0, "fn": 0}
    for cls, c in sorted(counts.items()):
        if c["tp"] + c["fn"] < POOL_BELOW:
            for k in pooled:
                pooled[k] += c[k]
        else:
            rows[cls] = {k: c[k] for k in ("tp", "fp", "fn")}
    if any(pooled.values()):
        rows["pooled_small"] = pooled
    for c in rows.values():
        c["n_true"] = c["tp"] + c["fn"]
        c["precision"] = c["tp"] / max(1, c["tp"] + c["fp"])
        c["recall"] = c["tp"] / max(1, c["n_true"])
        c["precision_ci95"] = wilson(c["tp"], c["tp"] + c["fp"])
        c["recall_ci95"] = wilson(c["tp"], c["n_true"])
    return rows


def asset_link(truth: dict, pred: dict, same: dict) -> dict:
    hits = total = 0
    for idx, events in truth.items():
        pairs, _, _ = match_events(events, pred[idx])
        for p, t in pairs:
            total += 1
            if p.get("asset") and (auto_asset_match(p["asset"], t.get("asset"))
                                   or same.get(f"{idx}|{p['class']}") is True):
                hits += 1
    return {"hits": hits, "pairs": total, "value": hits / total if total else 0.0}


def anon_agreement(named: dict, anon: dict) -> dict:
    agree = sum(class_set(named[k]["events"]) == class_set(v["events"]) for k, v in anon.items())
    return {"agree": agree, "n": len(anon), "value": agree / len(anon) if anon else 0.0}


def evaluate(truth: dict, jev_events: dict, same: dict, named: dict, anon: dict) -> dict:
    rows = gate_rows(class_counts(truth, jev_events))
    link = asset_link(truth, jev_events, same)
    anon_res = anon_agreement(named, anon)
    gates = {
        "precision": {"min": FLOORS["precision"],
                      "per_gate_class": {c: r["precision"] for c, r in rows.items()},
                      "pass": all(r["precision"] >= FLOORS["precision"] for r in rows.values())},
        "recall": {"min": FLOORS["recall"],
                   "per_gate_class": {c: r["recall"] for c, r in rows.items()},
                   "pass": all(r["recall"] >= FLOORS["recall"] for r in rows.values())},
        "asset_link": {"min": FLOORS["asset_link"], **link,
                       "pass": link["value"] >= FLOORS["asset_link"]},
        "anon_agreement": {"min": FLOORS["anon_agreement"], **anon_res,
                           "pass": anon_res["value"] >= FLOORS["anon_agreement"]},
        "prefilter_recall": {"status": "not_applicable", "reason": "no keyword prefilter"},
    }
    passed = all(g["pass"] for g in gates.values() if "pass" in g)
    return {"verdict": "PASS" if passed else "FAIL", "gate_rows": rows, "gates": gates}


def _pr(counts: dict) -> dict:
    return {c: {**v, "precision": v["tp"] / max(1, v["tp"] + v["fp"]),
                "recall": v["tp"] / max(1, v["tp"] + v["fn"])}
            for c, v in sorted(counts.items())}


def _quantile(values: list[float], q: float):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))] if ordered else None


def diagnostics(rounds: dict, truth: dict, named: dict, meta: dict) -> dict:
    jev_events = {int(k): v["events"] for k, v in named.items()}
    stored = {i: e for d in rounds.values() for i, e in d.truth.items()}
    gpt = {i: e for d in rounds.values() for i, e in d.extractor.items()}
    covered = pairs_n = 0
    for idx, events in truth.items():
        pairs, _, _ = match_events(events, jev_events[idx])
        for _, t in pairs:
            pairs_n += 1
            covered += any(auto_asset_match(c, t.get("asset"))
                           for c in named[str(idx)]["candidates"])
    reliability = {}
    for cls in CLASSES:
        bins = [[0, 0] for _ in range(10)]
        for k, label in named.items():
            b = min(9, int(label["probs"][cls] * 10))
            bins[b][0] += 1
            bins[b][1] += any(e["class"] == cls for e in truth[int(k)])
        reliability[cls] = [{"bin": f"{b / 10:.1f}-{(b + 1) / 10:.1f}", "n": n,
                             "positive_rate": pos / n if n else None}
                            for b, (n, pos) in enumerate(bins)]
    sweep = {}
    for thr in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        pred = {int(k): [{"class": c, "asset": label["asset"]} for c in CLASSES
                         if label["probs"][c] >= thr] for k, label in named.items()}
        sweep[f"{thr:.1f}"] = _pr(class_counts(truth, pred))
    deltas = [d for label in named.values() for d in label["delta"].values()]
    nouls = [float(r["answers"][f"ev_{c}"]["noul"])
             for label in named.values() for r in label["raw"] for c in CLASSES]
    latencies = [r["_latency_s"] for label in named.values() for r in label["raw"]]
    negative = {int(i) for d in rounds.values()
                for i in d.sample.index[~d.sample["prefilter"].astype(bool)]}
    neg = class_counts({i: truth[i] for i in negative}, jev_events)
    neg_tp, neg_fn = sum(c["tp"] for c in neg.values()), sum(c["fn"] for c in neg.values())
    named_cost = sum(float(r["usage"]["cost"]) for label in named.values() for r in label["raw"])
    per_article = named_cost / len(named)
    return {
        "head_to_head_gpt_5_4_mini": _pr(class_counts(truth, gpt)),
        "pre_review_vs_stored_labels": _pr(class_counts(stored, jev_events)),
        "per_round": {name: _pr(class_counts({i: truth[i] for i in d.truth}, jev_events))
                      for name, d in rounds.items()},
        "asset_candidate_coverage": {"covered": covered, "pairs": pairs_n,
                                     "value": covered / pairs_n if pairs_n else None},
        "reliability": reliability,
        "threshold_sweep": sweep,
        "stability": {"flip_rate": sum(label["flip"] for label in named.values()) / len(named),
                      "delta_p50": _quantile(deltas, 0.5), "delta_p90": _quantile(deltas, 0.9),
                      "delta_p99": _quantile(deltas, 0.99), "delta_max": max(deltas),
                      "exact_zero": sum(v == 0.0 for v in nouls),
                      "exact_one": sum(v == 1.0 for v in nouls), "noul_values": len(nouls)},
        "prefilter_negative_recall": {"tp": neg_tp, "fn": neg_fn,
                                      "value": neg_tp / (neg_tp + neg_fn)
                                      if neg_tp + neg_fn else None},
        "cost": {"spent_usd": meta["spent_usd"], "calls": meta["calls"],
                 "latency_p50_s": _quantile(latencies, 0.5),
                 "latency_p90_s": _quantile(latencies, 0.9),
                 "per_article_usd": per_article,
                 "projected_corpus_usd": per_article * CORPUS_ARTICLES},
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_score.py --import-mode=importlib -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/llm_jev_score.py tests/research/test_llm_jev_score.py
git commit -m "feat(llm-jev): P0 gates and diagnostics

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Runners, registration builder and smoke script

**Files:**
- Create: `scripts/llm_jev_event_p0.py`, `scripts/llm_jev_register.py`, `scripts/llm_jev_smoke.py`
- Test: `tests/research/test_llm_jev_runner.py`

**Interfaces:**
- Consumes: everything from Tasks 1–6, plus `tradingagents.research.ResearchRun` and `tradingagents.research.admission.runtime_hashes`.
- Produces:
  - In `llm_jev_event_p0`:
    - Constants `PROGRAM_DIR, E1, E2, PINNED_MODEL (None until Task 8), COST_CAP_USD, E1_OUTPUTS, E1_CELLS, E2_OUTPUTS, E2_CELLS, SHEET_PATH`
    - Functions `run_label(root, registration, source)`, `run_render(root)`, `run_score(root, registration, source)`, CLI `label|render|score`
  - In `llm_jev_register`: `build_e1(root)`, `build_e2(root)`, `write(root, name, spec)`, CLI `e1|e2`
  - In `llm_jev_smoke`: CLI `--model`, `--expect-model`

- [ ] **Step 1: Write the failing tests**

```python
# tests/research/test_llm_jev_runner.py
"""Runner guards and registration structure (no network, no run claims)."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import llm_jev_event_p0 as p0  # noqa: E402
import llm_jev_register as reg  # noqa: E402


def test_label_refuses_without_pinned_model(monkeypatch, tmp_path):
    monkeypatch.setattr(p0, "PINNED_MODEL", None)
    with pytest.raises(SystemExit, match="PINNED_MODEL"):
        p0.run_label(tmp_path, "gates.json", "0" * 40)


def test_render_refuses_overwrite(tmp_path):
    outputs = tmp_path / "research_runs" / p0.E1 / "outputs"
    outputs.mkdir(parents=True)
    (outputs / "review_sheet.json").write_text(json.dumps({"rows": []}))
    first = p0.run_render(tmp_path)
    assert first.read_text().startswith("# Jev P0 blind review")
    with pytest.raises(SystemExit, match="refusing"):
        p0.run_render(tmp_path)


def test_build_e1_structure(monkeypatch):
    monkeypatch.setattr(reg, "CHARTER",
                        "docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md")
    spec = reg.build_e1(ROOT)
    assert spec["schema_version"] == 1 and spec["program_id"] == "llm-jev-event-2026-09-29"
    family = spec["families"][reg.FAMILY_KEY]
    assert family["attempt_budget"] == 12 and family["prior_attempts"] == 2
    exp = spec["experiments"][p0.E1]
    assert exp["parent"] is None and exp["stage"] == "development"
    assert exp["reuse"] == "exploratory" and exp["selection"] is None
    assert exp["outputs"] == list(p0.E1_OUTPUTS) and exp["cells"] == list(p0.E1_CELLS)
    assert set(exp["source_files"]) == set(reg.SOURCE_FILES)
    assert len(exp["inputs"]) == 12
    for item in exp["inputs"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) and item["dataset"] == reg.DATASET
        assert item["path"].startswith("data/llm_event_xs/")
    assert exp["windows"] == [reg.WINDOW]
    assert all(e.endswith(".json") for e in exp["outputs"])


def test_write_refuses_overwrite(tmp_path):
    reg.write(tmp_path, "gates.json", {"a": 1})
    with pytest.raises(SystemExit, match="never overwritten"):
        reg.write(tmp_path, "gates.json", {"a": 2})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_runner.py --import-mode=importlib -q`
Expected: `ModuleNotFoundError: No module named 'llm_jev_event_p0'`.

- [ ] **Step 3: Write `scripts/llm_jev_event_p0.py`**

```python
# scripts/llm_jev_event_p0.py
"""Runners for the registered Jev P0 probe (charter §7.3).

  label   E1: Jev labels + blind review sheet data (no metrics)
  render  write the markdown sheet from E1 outputs for the human reviewer
  score   E2: apply the filled sheet, compute gates and diagnostics
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_truth import check_reproduction, load_rounds  # noqa: E402
from llm_jev_client import PROVIDER_NAME, JevClient, load_api_key  # noqa: E402
from llm_jev_labels import THRESHOLD, label_rounds  # noqa: E402
from llm_jev_questions import questions_sha256  # noqa: E402
from llm_jev_review import apply_review, build_review, parse_filled, render_markdown  # noqa: E402
from llm_jev_score import diagnostics, evaluate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_DIR = "research/llm-jev-event-2026-09-29"
E1 = "llm-jev-p0-label-20260929"
E2 = "llm-jev-p0-score-20260929"
PINNED_MODEL: str | None = None  # set from the smoke-test response before registration
COST_CAP_USD = 5.0
E1_OUTPUTS = ("jev_labels.json", "jev_labels_anon.json", "review_sheet.json",
              "review_key.json", "run_meta.json")
E1_CELLS = ("label-v1", "label-v2", "anon-v1", "anon-v2", "review-sheet")
E2_OUTPUTS = ("p0_verdict.json", "p0_diagnostics.json")
E2_CELLS = ("gates", "diagnostics")
SHEET_PATH = f"{PROGRAM_DIR}/review/jev-review-sheet.md"


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def run_label(root: Path, registration: str, source: str) -> dict:
    if PINNED_MODEL is None:
        raise SystemExit("PINNED_MODEL is unset; finish the smoke test and registration first")
    from tradingagents.research import ResearchRun
    client = JevClient(api_key=load_api_key(root / ".env"), model=PINNED_MODEL,
                       expected_model=PINNED_MODEL, cost_cap_usd=COST_CAP_USD)
    with ResearchRun.start(root=root, registration=registration, experiment=E1,
                           source=source) as run:
        rounds = load_rounds(run.read_input)
        check_reproduction(rounds)
        named, anon = label_rounds(rounds, client)
        rows, key = build_review(rounds, named)
        latencies = [r["_latency_s"] for label in [*named.values(), *anon.values()]
                     for r in label["raw"]]
        meta = {"model": PINNED_MODEL, "provider": PROVIDER_NAME, "calls": client.calls,
                "spent_usd": client.spent_usd, "questions_sha256": questions_sha256(),
                "threshold": THRESHOLD, "latency_median_s": statistics.median(latencies),
                "review_rows": len(rows)}
        run.write_json("jev_labels.json", named)
        run.write_json("jev_labels_anon.json", anon)
        run.write_json("review_sheet.json", {"rows": rows})
        run.write_json("review_key.json", key)
        run.write_json("run_meta.json", meta)
        return run.finish([{"id": cell, "status": "complete"} for cell in E1_CELLS])


def run_render(root: Path) -> Path:
    sheet = json.loads((root / "research_runs" / E1 / "outputs" / "review_sheet.json").read_text())
    target = root / SHEET_PATH
    if target.exists():
        raise SystemExit(f"{target} exists; refusing to overwrite a review sheet")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(sheet["rows"]))
    return target


def run_score(root: Path, registration: str, source: str) -> dict:
    from tradingagents.research import ResearchRun
    with ResearchRun.start(root=root, registration=registration, experiment=E2,
                           source=source) as run:
        rounds = load_rounds(run.read_input)
        check_reproduction(rounds)
        named = json.loads(run.read_input("jev_labels"))
        anon = json.loads(run.read_input("jev_labels_anon"))
        rows = json.loads(run.read_input("review_sheet"))["rows"]
        key = json.loads(run.read_input("review_key"))
        meta = json.loads(run.read_input("run_meta"))
        filled = parse_filled(run.read_input("review_filled").decode("utf-8"), rows)
        truth, same, stats = apply_review(rounds, named, rows, key, filled)
        jev_events = {int(k): v["events"] for k, v in named.items()}
        verdict = {**evaluate(truth, jev_events, same, named, anon), "review": stats,
                   "model": meta["model"], "questions_sha256": meta["questions_sha256"]}
        run.write_json("p0_verdict.json", verdict)
        run.write_json("p0_diagnostics.json", diagnostics(rounds, truth, named, meta))
        run.finish([{"id": cell, "status": "complete"} for cell in E2_CELLS])
        return verdict


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("label", "render", "score"))
    parser.add_argument("--registration")
    parser.add_argument("--source")
    args = parser.parse_args(argv)
    if args.command == "render":
        print(run_render(ROOT))
        return 0
    default = "gates.json" if args.command == "label" else "gates_e2.json"
    registration = args.registration or f"{PROGRAM_DIR}/{default}"
    source = args.source or _head(ROOT)
    runner = run_label if args.command == "label" else run_score
    print(json.dumps(runner(ROOT, registration, source), indent=1)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write `scripts/llm_jev_register.py`**

```python
# scripts/llm_jev_register.py
"""Build the lifecycle registrations for the Jev P0 probe from committed files.

  e1  research/llm-jev-event-2026-09-29/gates.json      (E1 only)
  e2  research/llm-jev-event-2026-09-29/gates_e2.json   (E1 unchanged + E2)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_truth import C1_DIR, ROUND_FILES, ROUNDS  # noqa: E402
from llm_jev_event_p0 import (  # noqa: E402
    E1, E1_CELLS, E1_OUTPUTS, E2, E2_CELLS, E2_OUTPUTS, PROGRAM_DIR, SHEET_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ID = "llm-jev-event-2026-09-29"
CHARTER = "docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md"
SOURCE_FILES = (
    "scripts/llm_event_xs_truth.py", "scripts/llm_jev_questions.py", "scripts/llm_jev_client.py",
    "scripts/llm_jev_labels.py", "scripts/llm_jev_review.py", "scripts/llm_jev_score.py",
    "scripts/llm_jev_event_p0.py", "scripts/llm_event_xs_extract.py",
    "scripts/llm_event_xs_p0_score.py", "uv.lock",
)
FAMILY_KEY = "llm-news-event-extraction"
FAMILY = {
    "mechanism_id": "llm-typed-news-event-extraction",
    "attempt_budget": 12,
    "prior_attempts": 2,
    "history_reference": (
        "docs/superpowers/specs/2026-08-11-llm-c1-event-xs-charter.md and "
        "data/llm_event_xs/trial_ledger.jsonl: llm_c1_event_xs declared <=12 ledgered configs; "
        "P0 v1 (FAIL) and P0 v2 (STOP) consumed 2 on 2026-08-14 with gpt-5.4-mini; C1 dead "
        "that cycle (THESIS_FINDINGS section 63)."),
}
DATASET = "c1-p0-samples"
WINDOW = {"dataset": DATASET, "start": "2021-01-01T00:00:00Z",
          "end": "2025-04-01T00:00:00Z", "availability": "existing"}
DATASETS = {DATASET: {
    "identity": "llm-c1-event-xs-p0-samples-20260813",
    "history_reference": (
        "data/llm_event_xs/corpus_manifest.json frozen 2026-08-13; P0 v1 (300) and v2 (100) "
        "articles inspected 2026-08-14 with gpt-5.4-mini labels, claude-haiku-4-5 pre-labels "
        "and blind human adjudication."),
    "exposures": [{"start": "2021-01-01T00:00:00Z", "end": "2025-04-01T00:00:00Z",
                   "state": "exposed"}],
}}
E1_QUESTION = ("Label the 400 adjudicated C1 P0 articles with Jev (sole class extractor, no "
               "keyword prefilter) and emit the blind review sheet, without computing metrics.")
E2_QUESTION = ("Does Jev meet the C1 P0 extraction floors (per-class precision >= 0.8, recall "
               ">= 0.6, asset link >= 0.9, anonymization agreement >= 0.8) on the 400 "
               "adjudicated C1 P0 articles after blind human review of its disputes?")


def _sha(root: Path, path: str) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def c1_inputs(root: Path) -> dict:
    return {f"{kind}_{rnd}": {"path": f"{C1_DIR}/{name}", "sha256": _sha(root, f"{C1_DIR}/{name}"),
                              "dataset": DATASET}
            for rnd in ROUNDS for kind, name in ROUND_FILES[rnd].items()}


def experiment(root: Path, *, parent, question, inputs, cells, outputs) -> dict:
    from tradingagents.research.admission import runtime_hashes
    return {"family": FAMILY_KEY, "parent": parent, "question": question,
            "charter": {"path": CHARTER, "sha256": _sha(root, CHARTER)},
            "stage": "development", "reuse": "exploratory", "selection": None,
            "source_files": {p: _sha(root, p) for p in SOURCE_FILES},
            "runtime_hashes": runtime_hashes(), "windows": [dict(WINDOW)],
            "inputs": inputs, "cells": list(cells), "outputs": list(outputs)}


def build_e1(root: Path) -> dict:
    return {"schema_version": 1, "program_id": PROGRAM_ID,
            "families": {FAMILY_KEY: dict(FAMILY)}, "datasets": copy.deepcopy(DATASETS),
            "experiments": {E1: experiment(root, parent=None, question=E1_QUESTION,
                                           inputs=c1_inputs(root), cells=E1_CELLS,
                                           outputs=E1_OUTPUTS)}}


def build_e2(root: Path) -> dict:
    """E1 entry is copied from the committed gates.json so it stays byte-for-byte equal."""
    spec = json.loads((root / PROGRAM_DIR / "gates.json").read_text())
    inputs = c1_inputs(root)
    for name in ("jev_labels", "jev_labels_anon", "review_sheet", "review_key", "run_meta"):
        path = f"research_runs/{E1}/outputs/{name}.json"
        inputs[name] = {"path": path, "sha256": _sha(root, path), "dataset": DATASET}
    inputs["review_filled"] = {"path": SHEET_PATH, "sha256": _sha(root, SHEET_PATH),
                               "dataset": DATASET}
    spec["experiments"][E2] = experiment(root, parent=E1, question=E2_QUESTION, inputs=inputs,
                                         cells=E2_CELLS, outputs=E2_OUTPUTS)
    return spec


def write(root: Path, name: str, spec: dict) -> Path:
    target = root / PROGRAM_DIR / name
    if target.exists():
        raise SystemExit(f"{target} exists; registrations are never overwritten")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("which", choices=("e1", "e2"))
    args = parser.parse_args(argv)
    if args.which == "e1":
        print(write(ROOT, "gates.json", build_e1(ROOT)))
    else:
        print(write(ROOT, "gates_e2.json", build_e2(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Write `scripts/llm_jev_smoke.py`**

```python
# scripts/llm_jev_smoke.py
"""Pre-registration smoke test on invented headlines (never corpus text).

Prints resolved model ID, provider and answer shapes; writes nothing into the
repository. Spend capped at USD 0.05.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_jev_client import JevClient, load_api_key  # noqa: E402
from llm_jev_questions import build_questions, build_state, candidates  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INVENTED = (
    {"store": "gdelt", "summary": "",
     "headline": "Fictional exchange Zetrix halts withdrawals after $40 million exploit"},
    {"store": "gdelt", "summary": "",
     "headline": "Regulator fines imaginary token issuer Quarkcoin Labs over unregistered sale"},
    {"store": "alpaca", "summary": "", "symbols": "NMBUSD",
     "headline": "Invented protocol Nimbus Chain completes mainnet launch"},
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="typesafe/jev-1.13")
    parser.add_argument("--expect-model", default=None)
    args = parser.parse_args(argv)
    client = JevClient(api_key=load_api_key(ROOT / ".env"), model=args.model,
                       expected_model=args.expect_model, expected_provider=None,
                       cost_cap_usd=0.05)
    for reverse in (False, True):
        for row in INVENTED:
            cands = candidates(row)
            resp = client.decide(build_state(row), build_questions(cands, reverse=reverse))
            print(json.dumps({"reverse": reverse, "headline": row["headline"],
                              "candidates": cands, "id": resp.get("id"),
                              "model": resp.get("model"), "provider": resp.get("provider"),
                              "usage": resp.get("usage"),
                              "latency_s": round(resp["_latency_s"], 3),
                              "answers": resp["answers"]}, indent=1))
    print(f"calls={client.calls} spent_usd={client.spent_usd:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_runner.py --import-mode=importlib -q`
Expected: `4 passed`.
Then run all probe tests: `.venv/bin/python -m pytest tests/research/test_llm_jev_*.py --import-mode=importlib -q`
Expected: `50 passed`.

- [ ] **Step 7: Commit**

```bash
git add scripts/llm_jev_event_p0.py scripts/llm_jev_register.py scripts/llm_jev_smoke.py tests/research/test_llm_jev_runner.py
git commit -m "feat(llm-jev): E1/E2 runners, registration builder, smoke script

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Live smoke test and model pin (main session; uses the user's key)

**Files:**
- Modify: `scripts/llm_jev_event_p0.py` (the `PINNED_MODEL` line)
- Modify, only if the smoke output requires it: `scripts/llm_jev_client.py` (`PROVIDER_SLUG`/`PROVIDER_NAME`), plus the matching test expectations

**Interfaces:**
- Consumes: Task 7 smoke script.
- Produces: `PINNED_MODEL = "<dated ID>"`, and provider constants confirmed against live responses.

- [ ] **Step 1: Alias smoke run (invented headlines only)**

Run: `.venv/bin/python scripts/llm_jev_smoke.py > "$SCRATCH/jev-smoke-1.txt" 2>&1; tail -3 "$SCRATCH/jev-smoke-1.txt"`, with `SCRATCH=/tmp/claude-1000/-home-malecada-master-thesis/42982101-1028-4d98-a0e8-4d3846e0149c/scratchpad`.
Expected: `calls=6 spent_usd=` below 0.01.
- **If it prints `HTTP 400` naming the provider:** the slug differs. Retry once with `PROVIDER_SLUG` set to the slug named in the error, update `test_success_body_and_cost_tracking`, and re-run Task 3 tests.
- **If it prints `HTTP 401`/`402`:** stop and ask the user to check the key or credits.

- [ ] **Step 2: Read the resolved identifiers**

Run: `grep -E '"(model|provider)"' "$SCRATCH/jev-smoke-1.txt" | sort | uniq -c`
Expected: one dated model string (form `typesafe/jev-1.13-YYYYMMDD`) and one provider string.
- If the provider string is not `TypeSafe`, set `PROVIDER_NAME` to the observed value, update `ok_payload`'s default in `tests/research/test_llm_jev_client.py`, and re-run that test file.

- [ ] **Step 3: Pinned smoke run**

Run: `.venv/bin/python scripts/llm_jev_smoke.py --model <DATED> --expect-model <DATED> > "$SCRATCH/jev-smoke-2.txt" 2>&1; tail -1 "$SCRATCH/jev-smoke-2.txt"`, with `<DATED>` the string from Step 2.
Expected: `calls=6` with no `JevError`. That confirms the dated ID is accepted and echoed.

- [ ] **Step 4: Pin the model**

Edit `scripts/llm_jev_event_p0.py`, replacing `PINNED_MODEL: str | None = None  # set from the smoke-test response before registration` with `PINNED_MODEL: str | None = "<DATED>"  # smoke test 2026-09-29, invented headlines`.
Run: `.venv/bin/python -m pytest tests/research/test_llm_jev_*.py --import-mode=importlib -q`
Expected: `50 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/llm_jev_event_p0.py scripts/llm_jev_client.py tests/research/test_llm_jev_client.py
git commit -m "chore(llm-jev): pin Jev model from invented-headline smoke test

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Charter, registration, admission check, review, push (main session)

**Files:**
- Create: `docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md`, `research/llm-jev-event-2026-09-29/STATE.md`, `research/llm-jev-event-2026-09-29/gates.json` (generated)

**Interfaces:**
- Consumes: pinned code from Tasks 1–8. `questions_sha256()` value from Task 2 Step 5. `PINNED_MODEL` from Task 8.
- Produces: the pushed design commit, which the E1 run executes against.

- [ ] **Step 1: Write the charter**

Create `docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md`. Replace `{{PINNED_MODEL}}` with the Task 8 value and `{{QUESTIONS_SHA256}}` with the Task 2 Step 5 value:

```markdown
# Charter — Jev P0 extraction-quality probe (`llm-jev-event-2026-09-29`)

**Frozen:** 2026-09-29, before any Jev call on sample text. **Design:**
`docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md`.
**Parent mechanism:** `llm_c1_event_xs` (charter 2026-08-11; P0 v1 FAIL, v2 STOP).
**Authority:** user instruction of 2026-09-29 (probe only; OpenRouter key supplied;
paid spend capped at USD 5). No production, order or account action follows.

## 1. Question
Does Jev (`{{PINNED_MODEL}}`, OpenRouter Decisions API, provider locked to
TypeSafe, alpha endpoint), as sole class extractor with no keyword prefilter,
meet the C1 P0 extraction floors on the 400 adjudicated C1 P0 articles?

## 2. Inputs and exposure
The 12 committed C1 P0 artifacts are registered by hash in `gates.json`:
- samples, gpt-5.4-mini labels, adjudication sheets and keys;
- anonymization subsets and published results, for v1 and v2.

All 400 articles were inspected in August 2026. The stage is development and
reuse is exploratory; no fresh-data claim is made.

## 3. Ground truth
Ground truth is rebuilt from committed files by `scripts/llm_event_xs_truth.py`:
- adjudicated rows (154) follow the human verdict;
- unaudited rows (246) keep the gpt-5.4-mini labels.

The runner refuses to call Jev unless the rebuild reproduces C1's published
per-class tp/fp/fn exactly. After E1, a blind sheet (seed 20260929) presents:
- class disputes on unaudited rows (A/B/NO EVENTS/NEITHER);
- 20 agreement spot-checks (BOTH/NO EVENTS/NEITHER);
- same-entity questions on correctly classified events whose names fail the
  automatic rule.

The human verdict is final. A Jev asset of `none` counts as an asset mismatch
and is not reviewed.

## 4. Protocol (frozen code; hashes in `gates.json`)
- Question wording SHA-256 `{{QUESTIONS_SHA256}}` (`scripts/llm_jev_questions.py`).
- Each call asks six Noul class questions plus an asset Choice over up to 30
  deterministic candidates and `none`.
- Two calls are made per article, with candidates forward then reversed. A
  class is an event when the mean probability is at least 0.5. The asset is
  the argmax of the mean.
- The anonymization subsets (50 + 50, C1's) ask the class questions only, on
  text masked by C1's `anonymize()`.
- Retries: at most 5 per call. Any drift, malformed answer, exhausted retry
  or spend over the cap fails the run.

## 5. Gates (all required; union of 400 articles)
| Gate | Floor |
|---|---|
| Per-class precision (classes with < 10 final true events pooled) | >= 0.8 |
| Per-class recall (same pooling) | >= 0.6 |
| Asset-link accuracy on TP pairs | >= 0.9 |
| Anonymization class-set agreement (100 rows) | >= 0.8 |
C1's prefilter-recall gate is not applicable.

## 6. Diagnostics (never gated or used for selection)
- Wilson 95% intervals.
- gpt-5.4-mini head-to-head on the same final truth. Unaudited truth rows
  originate from gpt-5.4-mini, so this comparison is biased toward it.
- Pre-review metrics, and v1/v2 separately.
- Asset candidate coverage.
- Reliability bins and threshold sweep 0.3–0.9.
- Stability: flip rate, |Δp|, exact 0/1 counts.
- Recall on prefilter-negative rows.
- Cost, latency and projected full-corpus cost.

## 7. Stop rules and attribution
- One shot. No amendment, wording, threshold, candidate or model change after
  the first sample call, and no resampling.
- FAIL ends this design for this cycle.
- An E1 infrastructure failure consumes an attempt; any retry requires a
  recorded review decision and a new experiment ID.
- An asset-link failure with candidate coverage below 0.9 is recorded as a
  candidate-generator (measurement) defect. It is still FAIL.
- PASS authorizes nothing further. Any P1–P3 work requires a new charter
  using data after 2026-09-15 only.

## 8. Budget and lifecycle
- Family `llm-news-event-extraction`: budget 12, with 2 prior attempts.
- E1 `llm-jev-p0-label-20260929` and E2 `llm-jev-p0-score-20260929` (child)
  consume 2 attempts.
- E2 is registered in `gates_e2.json` after the filled sheet is committed;
  its rules are those of this charter.

## 9. Limitations
- There is no evidence span. Anonymization agreement is the only memorization
  check.
- Jev's training cutoff, determinism and retention are undisclosed.
- Label strings shown to the reviewer omit severity, so both sides look alike.
- Per-class counts are small (about 10–35).
- Jev was trained on synthetic data, and its calibration claims are
  unverified.
```

- [ ] **Step 2: Write the program state file**

Create `research/llm-jev-event-2026-09-29/STATE.md`:

```markdown
# llm-jev-event-2026-09-29 — state

- Charter: `docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md`
- Design: `docs/superpowers/specs/2026-09-29-llm-jev-event-probe-design.md`
- Plan: `docs/superpowers/plans/2026-09-29-llm-jev-event-probe.md`
- Branch: `research/llm-jev-event-2026-09-29` (worktree `TradingAgents-jev-probe`)
- Status: E1 registered, not started.
- Next action: run `.venv/bin/python scripts/llm_jev_event_p0.py label` at the pushed
  registration commit; then `render` and hand the sheet to the reviewer.
- Do not open `research_runs/llm-jev-p0-label-20260929/outputs/review_key.json`
  before the review is committed.
```

- [ ] **Step 3: Commit the charter and state, then generate the registration**

```bash
git add docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md research/llm-jev-event-2026-09-29/STATE.md
git commit -m "docs(llm-jev): freeze Jev P0 probe charter

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
.venv/bin/python scripts/llm_jev_register.py e1
git add research/llm-jev-event-2026-09-29/gates.json
git commit -m "research(llm-jev): register E1 label run

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Admission check and offline suite**

Run: `.venv/bin/python -m tradingagents.research check --root . --registration research/llm-jev-event-2026-09-29/gates.json --experiment llm-jev-p0-label-20260929 --source $(git rev-parse HEAD)`
Expected: the admission report succeeds with `ready` true and no exception.
- If it fails, fix the cause, delete the uncommitted/last registration commit only if it was never pushed (`git reset --soft HEAD~1`), rebuild with the register script, then recommit and recheck.

Run: `.venv/bin/python -B scripts/verify_offline.py`
Expected: pass, with the 50 new probe tests included under `tests/research`.

- [ ] **Step 5: Independent review**

Dispatch a fresh reviewer subagent (most capable model). Its prompt: review the charter, `gates.json` and `scripts/llm_jev_*.py` / `scripts/llm_event_xs_truth.py` against the design spec and the raw C1 artifacts in `data/llm_event_xs/`. Checks:
- (a) The truth rebuild matches C1 semantics.
- (b) No path lets Jev see sample text before the claim.
- (c) Blindness of the sheet.
- (d) The gate arithmetic equals C1's `scripts/llm_event_xs_p0_score.py` rules.
- (e) Registration family/dataset/exposure fields are honest.
- (f) No secret is read or logged.

The reviewer must not reuse implementation outputs as expected answers. Fix confirmed findings before Step 6. Changing a registered source file requires rebuilding the registration: remove the unpushed registration commit, rebuild, recommit and recheck.

- [ ] **Step 6: Push the design commit**

Run: `git push -u origin research/llm-jev-event-2026-09-29`
Expected: branch published. Record the pushed HEAD in `STATE.md` only after E1 (Task 10), not now, so the registered sources stay unchanged.

---

### Task 10: Execute E1 and produce the review sheet (main session)

**Files:**
- Generated: `research_runs/llm-jev-p0-label-20260929/**`, `research/llm-jev-event-2026-09-29/review/jev-review-sheet.md`
- Modify: `research/llm-jev-event-2026-09-29/STATE.md`

- [ ] **Step 1: Confirm a clean source state**

Run: `git status --short scripts tests docs research` and `git log -1 --format=%H`
Expected: no modified tracked files, and HEAD equal to the pushed commit.

- [ ] **Step 2: Run E1 in the background**

Run with Bash `run_in_background: true`: `cd /home/malecada/master_thesis/TradingAgents-jev-probe && .venv/bin/python scripts/llm_jev_event_p0.py label > "$SCRATCH/jev-e1.log" 2>&1`
Expected on completion: `research_runs/llm-jev-p0-label-20260929/complete.json` exists, and the log shows progress lines with `spent=` below 5.
- **If `failed.json` appears:** do not retry. Record the reason in `STATE.md`, commit the failed receipt and report to the user. A retry needs a recorded decision and a new experiment ID (charter §7).

- [ ] **Step 3: Verify the run**

Run: `.venv/bin/python -m tradingagents.research verify --run research_runs/llm-jev-p0-label-20260929`
Expected: verification passes.
Run: `.venv/bin/python -c "import json; m=json.load(open('research_runs/llm-jev-p0-label-20260929/outputs/run_meta.json')); print(m['calls'], round(m['spent_usd'],4), m['review_rows'], m['model'])"`
Expected: `1000` calls, spend below 5, a positive row count and the pinned model.

- [ ] **Step 4: Render the sheet and commit**

Run: `.venv/bin/python scripts/llm_jev_event_p0.py render`
Update `STATE.md`:
- Status becomes "E1 complete (receipt hash from `complete.json`); review sheet awaiting the human reviewer".
- Record the pushed design commit.
- Record the E1 spend.

```bash
git add research_runs/llm-jev-p0-label-20260929 research/llm-jev-event-2026-09-29
git commit -m "research(llm-jev): E1 labels and blank blind review sheet

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push
```

- [ ] **Step 5: Hand off to the reviewer**

Tell the user the sheet path, the row count, the verdict formats (from the sheet header), and not to open `review_key.json`. Stop until the user reports the sheet filled.

---

### Task 11: Execute E2, forensics and records (main session, after the review)

**Files:**
- Modify: `research/llm-jev-event-2026-09-29/review/jev-review-sheet.md` (the user's filled version)
- Generated: `research/llm-jev-event-2026-09-29/gates_e2.json`, `research_runs/llm-jev-p0-score-20260929/**`
- Create: `research/llm-jev-event-2026-09-29/RESULT.md`
- Modify: `research/llm-jev-event-2026-09-29/STATE.md`, `THESIS_FINDINGS.md` (append section 122, noting renumbering may be needed at merge)

- [ ] **Step 1: Validate the filled sheet before committing**

Run: `.venv/bin/python -c "import json,sys; sys.path.insert(0,'scripts'); from llm_jev_review import parse_filled; rows=json.load(open('research_runs/llm-jev-p0-label-20260929/outputs/review_sheet.json'))['rows']; parse_filled(open('research/llm-jev-event-2026-09-29/review/jev-review-sheet.md').read(), rows); print('sheet complete')"`
Expected: `sheet complete`. On `ValueError`, show the user the listed rows to fix. Do not edit their verdicts.

- [ ] **Step 2: Commit the sheet and register E2**

```bash
git add research/llm-jev-event-2026-09-29/review/jev-review-sheet.md
git commit -m "research(llm-jev): filled blind review sheet

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
.venv/bin/python scripts/llm_jev_register.py e2
git add research/llm-jev-event-2026-09-29/gates_e2.json
git commit -m "research(llm-jev): register E2 score run

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
.venv/bin/python -m tradingagents.research check --root . --registration research/llm-jev-event-2026-09-29/gates_e2.json --experiment llm-jev-p0-score-20260929 --source $(git rev-parse HEAD)
git push
```
Expected: the check succeeds.

- [ ] **Step 3: Run E2**

Run: `.venv/bin/python scripts/llm_jev_event_p0.py score > "$SCRATCH/jev-e2.log" 2>&1; tail -40 "$SCRATCH/jev-e2.log"`
Expected: the verdict JSON is printed and `research_runs/llm-jev-p0-score-20260929/complete.json` exists.
Run: `.venv/bin/python -m tradingagents.research verify --run research_runs/llm-jev-p0-score-20260929`
Expected: verification passes.

- [ ] **Step 4: Independent forensic review**

Dispatch a fresh reviewer subagent. Its tasks:
- Recompute the per-class counts, asset link and anonymization agreement independently from the raw E1 outputs, the filled sheet and `review_key.json`, with its own short script. It must not import `scripts/llm_jev_score.py`.
- Confirm they equal `p0_verdict.json`.
- Classify any FAIL per charter §7: Jev failure, candidate-generator defect, or label-quality concern bounded by the spot-check error rate.
- Report discrepancies.

- [ ] **Step 5: Record the result**

Write `research/llm-jev-event-2026-09-29/RESULT.md` in impersonal prose, with:
- the verdict;
- the gate table with Wilson intervals;
- the review statistics (rows, spot-check error rate);
- the gpt-5.4-mini head-to-head, with its bias disclosure;
- the key diagnostics (coverage, stability, cost, projected corpus cost);
- the forensic review outcome;
- the explicit statement that no further stage is authorized.

Update `STATE.md` to terminal status. Append `## 122. Jev System One extractor on the C1 P0 sample (September 2026)` to `THESIS_FINDINGS.md`, summarizing the same facts with file references.

```bash
git add research_runs/llm-jev-p0-score-20260929 research/llm-jev-event-2026-09-29 THESIS_FINDINGS.md
git commit -m "research(llm-jev): E2 verdict, forensics and findings

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push
```
