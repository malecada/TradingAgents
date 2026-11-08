"""Single-pass DeepSeek labeling per article, anonymized subsets and a repeat set (Charter 0 §4)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import random
from typing import Callable

from llm_event_xs_extract import anonymize, validate_spans
from llm_v2c0_prompt import article_text

REPEAT_SEED = 20261109
N_REPEAT = 50
WORKERS = 4


def label_article(client, row: dict, *, anon: bool) -> dict:
    """One call on the full text; evidence spans not found in the text drop the event (C1 rule)."""
    text = article_text(row, anonymize if anon else None)
    out = client.extract(text)
    events, dropped = validate_spans(out["events"], text)
    return {"events": [{"class": e["class"], "asset": e["asset"], "severity": e["severity"],
                        "evidence": e["evidence"]} for e in events],
            "ambiguous": bool(out["ambiguous"]), "spans_dropped": dropped,
            "raw_events": len(out["events"]), "raw": out["raw"]}


def repeat_ids(rounds: dict, seed: int = REPEAT_SEED, n: int = N_REPEAT) -> tuple[int, ...]:
    """Fixed subset of v1 articles labeled a second time for the stability diagnostic."""
    pool = sorted(int(i) for i in rounds["v1"].sample.index)
    return tuple(sorted(random.Random(seed).sample(pool, min(n, len(pool)))))


def _run(jobs, client, progress: Callable[[str], None], tag: str) -> dict:
    """``jobs`` = [(key, row_dict, anon)]; results keyed by ``key``."""
    out = {}
    def work(job):
        key, row, anon = job
        return key, label_article(client, row, anon=anon)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for n, (key, label) in enumerate(pool.map(work, jobs), 1):
            out[key] = label
            if n % 50 == 0 or n == len(jobs):
                progress(f"{tag} {n}/{len(jobs)} spent={client.spent_usd:.4f}")
    return out


def label_rounds(rounds: dict, client, progress: Callable[[str], None] = print):
    """Return (named, anon, repeat): all 400 named; the C1 50+50 anonymized subsets;
    a second named pass on the fixed repeat subset."""
    named, anon = {}, {}
    for name, data in rounds.items():
        jobs = [(str(int(idx)), row.to_dict(), False) for idx, row in data.sample.iterrows()]
        for key, label in _run(jobs, client, progress, f"{name} named").items():
            named[key] = {"round": name, **label}
        jobs = [(str(idx), data.sample.loc[idx].to_dict(), True) for idx in data.anon_ids]
        for key, label in _run(jobs, client, progress, f"{name} anon").items():
            anon[key] = {"round": name, **label}
    v1 = rounds["v1"]
    jobs = [(str(idx), v1.sample.loc[idx].to_dict(), False) for idx in repeat_ids(rounds)]
    repeat = {key: {"round": "v1", **label}
              for key, label in _run(jobs, client, progress, "v1 repeat").items()}
    return named, anon, repeat
