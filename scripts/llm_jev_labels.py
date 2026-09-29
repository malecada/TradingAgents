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
