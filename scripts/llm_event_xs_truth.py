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
