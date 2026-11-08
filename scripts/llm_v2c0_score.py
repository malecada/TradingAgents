"""Charter 0 gates (reused from the Jev scorer) and DeepSeek-specific diagnostics (§5–6)."""
from __future__ import annotations

from llm_event_xs_truth import class_counts, match_events
from llm_jev_questions import CLASSES
from llm_jev_review import class_set
from llm_jev_score import CORPUS_ARTICLES, _asset_link_c1_exact, _pr, _quantile, evaluate  # noqa: F401


def _events(labels: dict) -> dict:
    return {int(k): v["events"] for k, v in labels.items()}


def diagnostics(rounds: dict, truth: dict, named: dict, anon: dict, repeat: dict,
                meta: dict) -> dict:
    pred = _events(named)
    stored = {i: e for d in rounds.values() for i, e in d.truth.items()}
    gpt = {i: e for d in rounds.values() for i, e in d.extractor.items()}
    severity = {c: {"1": 0, "2": 0, "3": 0} for c in CLASSES}
    for label in named.values():
        for e in label["events"]:
            severity[e["class"]][str(e["severity"])] += 1
    flips = asset_flips = compared = 0
    for key, second in repeat.items():
        first = named[key]
        compared += 1
        flips += class_set(first["events"]) != class_set(second["events"])
        a = {e["class"]: e["asset"] for e in first["events"]}
        b = {e["class"]: e["asset"] for e in second["events"]}
        asset_flips += any(a.get(c) != b.get(c) for c in set(a) & set(b))
    anon_per_class = {}
    for c in CLASSES:
        agree = sum((any(e["class"] == c for e in named[k]["events"])
                     == any(e["class"] == c for e in v["events"])) for k, v in anon.items())
        anon_per_class[c] = agree / len(anon) if anon else None
    negative = {int(i) for d in rounds.values()
                for i in d.sample.index[~d.sample["prefilter"].astype(bool)]}
    neg = class_counts({i: truth[i] for i in negative}, pred)
    neg_tp, neg_fn = sum(c["tp"] for c in neg.values()), sum(c["fn"] for c in neg.values())
    latencies = [label["raw"]["_latency_s"] for label in named.values()]
    reasoning = [label["raw"]["usage"].get("reasoning_tokens") or 0 for label in named.values()]
    named_cost = sum(label["raw"]["usage"]["cost"] for label in named.values())
    per_article = named_cost / len(named)
    return {
        "head_to_head_gpt_5_4_mini": _pr(class_counts(truth, gpt)),
        "pre_review_vs_stored_labels": _pr(class_counts(stored, pred)),
        "per_round": {name: _pr(class_counts({i: truth[i] for i in d.truth}, pred))
                      for name, d in rounds.items()},
        "asset_link_c1_exact": _asset_link_c1_exact(truth, pred),
        "severity_distribution": severity,
        "spans": {"dropped": sum(l["spans_dropped"] for l in named.values()),
                  "raw_events": sum(l["raw_events"] for l in named.values()),
                  "kept_events": sum(len(l["events"]) for l in named.values())},
        "ambiguous_rate": sum(l["ambiguous"] for l in named.values()) / len(named),
        "stability": {"repeat_n": compared,
                      "class_set_flip_rate": flips / compared if compared else None,
                      "asset_flip_rate": asset_flips / compared if compared else None},
        "anon_agreement_per_class": anon_per_class,
        "prefilter_negative_recall": {"tp": neg_tp, "fn": neg_fn,
                                      "value": neg_tp / (neg_tp + neg_fn) if neg_tp + neg_fn else None},
        "cost": {"spent_usd": meta["spent_usd"], "calls": meta["calls"],
                 "latency_p50_s": _quantile(latencies, 0.5),
                 "latency_p90_s": _quantile(latencies, 0.9),
                 "reasoning_tokens_mean": sum(reasoning) / len(reasoning),
                 "per_article_usd": per_article,
                 "projected_corpus_usd": per_article * CORPUS_ARTICLES},
    }
