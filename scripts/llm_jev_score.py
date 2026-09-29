"""P0 gates and diagnostics for the Jev probe (charter §5–6). Nothing is selected here."""
from __future__ import annotations

import math

from llm_event_xs_p0_score import norm_asset
from llm_event_xs_truth import class_counts, match_events
from llm_jev_questions import CLASSES
from llm_jev_review import auto_asset_match, class_set

FLOORS = {"precision": 0.8, "recall": 0.6, "asset_link": 0.9, "anon_agreement": 0.8}
PRIMARY_GATES = ("precision", "recall", "anon_agreement")
SECONDARY_GATES = ("precision", "recall", "asset_link", "anon_agreement")
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


def asset_link(truth: dict, pred: dict, same: dict, jev_adopted: frozenset = frozenset()) -> dict:
    """For idx in ``jev_adopted``, the pred asset is Jev's own claim copied into truth, so an
    automatic match would be tautological: the class-row SAME verification is required
    instead, and a missing verification is excluded from the gated denominator (counted as
    ``unverified``, with a ``lenient_value`` that credits unverified non-empty pred assets)."""
    hits = total = unverified = lenient_extra = 0
    for idx, events in truth.items():
        pairs, _, _ = match_events(events, pred[idx])
        for p, t in pairs:
            key = f"{idx}|{p['class']}"
            if idx in jev_adopted:
                if key not in same:
                    unverified += 1
                    if p.get("asset"):
                        lenient_extra += 1
                    continue
                total += 1
                if p.get("asset") and same[key] is True:
                    hits += 1
                continue
            total += 1
            if p.get("asset") and (auto_asset_match(p["asset"], t.get("asset"))
                                   or same.get(key) is True):
                hits += 1
    denom = total + unverified
    return {"hits": hits, "pairs": total, "value": hits / total if total else 0.0,
            "unverified": unverified,
            "lenient_value": (hits + lenient_extra) / denom if denom else 0.0}


def anon_agreement(named: dict, anon: dict) -> dict:
    agree = sum(class_set(named[k]["events"]) == class_set(v["events"]) for k, v in anon.items())
    return {"agree": agree, "n": len(anon), "value": agree / len(anon) if anon else 0.0}


def evaluate(truth: dict, jev_events: dict, same: dict, named: dict, anon: dict,
            jev_adopted: frozenset = frozenset()) -> dict:
    rows = gate_rows(class_counts(truth, jev_events))
    link = asset_link(truth, jev_events, same, jev_adopted)
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
    def verdict(names):
        return "PASS" if all(gates[n]["pass"] for n in names) else "FAIL"
    return {"primary": {"name": "class_extraction", "gates": list(PRIMARY_GATES),
                        "verdict": verdict(PRIMARY_GATES)},
            "secondary": {"name": "full_c1_p0", "gates": list(SECONDARY_GATES),
                          "verdict": verdict(SECONDARY_GATES)},
            "gate_rows": rows, "gates": gates}


def _pr(counts: dict) -> dict:
    return {c: {**v, "precision": v["tp"] / max(1, v["tp"] + v["fp"]),
                "recall": v["tp"] / max(1, v["tp"] + v["fn"])}
            for c, v in sorted(counts.items())}


def _quantile(values: list[float], q: float):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))] if ordered else None


def _asset_link_c1_exact(truth: dict, jev_events: dict) -> dict:
    """Share of Jev TP pairs (against final truth) where the C1 normalized pred asset is
    exactly equal to the normalized truth asset (a None pred asset is always a miss)."""
    hits = total = 0
    for idx, events in truth.items():
        pairs, _, _ = match_events(events, jev_events[idx])
        for p, t in pairs:
            total += 1
            pred_asset = p.get("asset")
            if pred_asset and norm_asset(pred_asset) == norm_asset(t.get("asset")):
                hits += 1
    return {"hits": hits, "pairs": total, "value": hits / total if total else 0.0}


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
        "pre_review_per_round": {name: _pr(class_counts({i: stored[i] for i in d.truth},
                                                        jev_events))
                                 for name, d in rounds.items()},
        "asset_link_c1_exact": _asset_link_c1_exact(truth, jev_events),
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
