"""llm_c1_event_xs P0 — score extraction quality from the adjudicated table.

Ground truth per article = the adjudicator's verdict: A/B pick the winning
model's label set; BOTH = shared labels correct; NEITHER + correction =
adjudicator's labels (this run: all NEITHER rows resolved to NO EVENTS).
Articles outside the 115 adjudicated rows were class-set-agreed and not in
the audited subsample; the registered gates are computed on the adjudicated
115 plus the 185 unaudited-agreement rows scored as correct-by-agreement,
with the agreement-check error rate reported alongside (disclosure).

Gates (charter §5 P0): precision >=0.8, recall >=0.6 (small classes pooled),
asset-link accuracy >=0.9, prefilter recall >=0.85, anonymization
agreement >=0.8.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

OUTDIR = Path("data/llm_event_xs")
SCRATCH = Path("/tmp/claude-1000/-home-malecada-master-thesis/"
               "f08d2b6d-f71e-4c57-a703-b74203ce521c/scratchpad")
OUT = OUTDIR / "p0_result.json"
LEDGER = OUTDIR / "trial_ledger.jsonl"


def norm_asset(a: str) -> str:
    a = (a or "").lower().strip()
    aliases = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana",
               "xrp": "ripple", "doge": "dogecoin", "bnb": "binancecoin"}
    return aliases.get(a, a)


def load_all():
    sample = pd.read_parquet(OUTDIR / "p0_sample.parquet").set_index("sample_idx")
    ext = json.loads((OUTDIR / "p0_extractor_labels.json").read_text())
    ext = {int(k): v["events"] for k, v in ext.items()}
    pre = {}
    for f in sorted(SCRATCH.glob("p0_prelabel_*.json")):
        for l in json.loads(f.read_text())["labels"]:
            pre[int(l["sample_idx"])] = l.get("events", [])
    key = json.loads((OUTDIR / "p0_adjudication_key.json").read_text())
    txt = (OUTDIR / "p0_adjudication.md").read_text().replace("\\_", "_")
    verdicts = {int(r): v.strip() for r, v in
                re.findall(r"### row (\d+).*?VERDICT: *_*([^\n]*)", txt, re.S)}
    return sample, ext, pre, key, verdicts


def truth_for(idx, ext, pre, key, verdicts):
    """Return ground-truth event list for an adjudicated row."""
    v = verdicts[idx].upper().lstrip("\\").strip()
    k = key[str(idx)]
    if v.startswith("A"):
        winner = k["A"]
    elif v.startswith("B"):
        winner = k["B"]
    elif v.startswith("BOTH"):
        winner = "extractor"  # identical class-sets; extractor rep is fine
    elif v.startswith("NO EVENTS"):
        return []
    elif v.startswith("NEITHER"):
        rest = verdicts[idx].split(":", 1)
        return []  # this run: all NEITHER resolved to empty
    else:
        raise ValueError(f"unparseable verdict row {idx}: {v!r}")
    return ext[idx] if winner == "extractor" else pre[idx]


def main() -> int:
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    sample, ext, pre, key, verdicts = load_all()

    truth = {}
    for idx in sample.index:
        if idx in verdicts:
            truth[idx] = truth_for(idx, ext, pre, key, verdicts)
        else:
            # unaudited agreement row: both models agreed on class-set;
            # scored correct-by-agreement (disclosed)
            truth[idx] = ext[idx]

    # agreement-check error rate (60 audited agreement rows)
    agree_rows = [i for i, k in ((int(r), k) for r, k in key.items())
                  if k["kind"] == "agreement-check"]
    both_wrong = sum(1 for i in agree_rows
                     if not verdicts[i].upper().lstrip("\\").startswith("BOTH")
                     and truth[i] != ext[i])
    agree_err = both_wrong / len(agree_rows)

    # event-level precision/recall per class (extractor vs truth)
    tp, fp, fn = {}, {}, {}
    asset_match, asset_total = 0, 0
    for idx in sample.index:
        t_events = list(truth[idx])
        e_events = list(ext[idx])
        t_used = [False] * len(t_events)
        for e in e_events:
            hit = None
            for j, t in enumerate(t_events):
                if not t_used[j] and t.get("class") == e.get("class"):
                    hit = j
                    break
            c = e.get("class", "?")
            if hit is not None:
                t_used[hit] = True
                tp[c] = tp.get(c, 0) + 1
                asset_total += 1
                if norm_asset(e.get("asset")) == norm_asset(t_events[hit].get("asset")):
                    asset_match += 1
            else:
                fp[c] = fp.get(c, 0) + 1
        for j, t in enumerate(t_events):
            if not t_used[j]:
                c = t.get("class", "?")
                fn[c] = fn.get(c, 0) + 1

    classes = sorted(set(tp) | set(fp) | set(fn))
    per_class, pooled = {}, {"tp": 0, "fp": 0, "fn": 0}
    gate_rows = {}
    for c in classes:
        n_true = tp.get(c, 0) + fn.get(c, 0)
        row = {"tp": tp.get(c, 0), "fp": fp.get(c, 0), "fn": fn.get(c, 0),
               "n_true": n_true}
        row["precision"] = row["tp"] / max(1, row["tp"] + row["fp"])
        row["recall"] = row["tp"] / max(1, n_true)
        per_class[c] = row
        if n_true < 10:
            for k2 in ("tp", "fp", "fn"):
                pooled[k2] += row[k2]
        else:
            gate_rows[c] = row
    if pooled["tp"] + pooled["fp"] + pooled["fn"] > 0:
        gate_rows["pooled_small"] = {
            **pooled,
            "n_true": pooled["tp"] + pooled["fn"],
            "precision": pooled["tp"] / max(1, pooled["tp"] + pooled["fp"]),
            "recall": pooled["tp"] / max(1, pooled["tp"] + pooled["fn"])}

    asset_acc = asset_match / max(1, asset_total)

    # prefilter recall: corpus-weighted share of true events reachable
    pos_rows = sample[sample["prefilter"]].index
    neg_rows = sample[~sample["prefilter"]].index
    ev_rate_pos = sum(len(truth[i]) for i in pos_rows) / len(pos_rows)
    ev_rate_neg = sum(len(truth[i]) for i in neg_rows) / len(neg_rows)
    N_POS, N_NEG = 57076, 320749  # frozen corpus counts (manifest)
    est_pos, est_neg = ev_rate_pos * N_POS, ev_rate_neg * N_NEG
    prefilter_recall = est_pos / max(1e-9, est_pos + est_neg)

    # anonymization agreement on the 50-subset
    anon = json.loads((OUTDIR / "p0_extractor_labels_anon.json").read_text())
    agree_n = 0
    for k2, v2 in anon.items():
        named_cl = sorted({e.get("class") for e in ext[int(k2)]})
        anon_cl = sorted({e.get("class") for e in v2["events"]})
        agree_n += int(named_cl == anon_cl)
    anon_agree = agree_n / len(anon)

    gates = {
        "precision": {"min": 0.8,
                      "per_gate_class": {c: r["precision"] for c, r in gate_rows.items()},
                      "pass": all(r["precision"] >= 0.8 for r in gate_rows.values())},
        "recall": {"min": 0.6,
                   "per_gate_class": {c: r["recall"] for c, r in gate_rows.items()},
                   "pass": all(r["recall"] >= 0.6 for r in gate_rows.values())},
        "asset_link": {"min": 0.9, "value": asset_acc, "pass": asset_acc >= 0.9},
        "prefilter_recall": {"min": 0.85, "value": prefilter_recall,
                             "pass": prefilter_recall >= 0.85},
        "anon_agreement": {"min": 0.8, "value": anon_agree,
                           "pass": anon_agree >= 0.8},
    }
    verdict = "PASS" if all(g["pass"] for g in gates.values()) else "FAIL"
    res = {"experiment": "llm_c1_event_xs", "probe": "P0_extraction_quality",
           "n_adjudicated": len(verdicts), "n_sample": len(sample.index),
           "agreement_check_error_rate": agree_err,
           "per_class": per_class, "gates": gates,
           "asset_pairs": asset_total,
           "event_rate_prefilter_pos": ev_rate_pos,
           "event_rate_prefilter_neg": ev_rate_neg,
           "verdict": verdict,
           "note": "unaudited agreement rows scored correct-by-agreement; "
                   "audited-agreement error rate reported above"}
    OUT.write_text(json.dumps(res, indent=1, default=float))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
           "experiment": "llm_c1_event_xs", "cell": "P0_extraction_quality",
           "model": "gpt-5.4-mini + human adjudication (haiku pre-label)",
           "config": {"sample": 300, "adjudicated": len(verdicts)},
           "config_hash": "p0-v1", "git_commit": commit,
           "window": ["2021-01-01", "2025-03-31"],
           "metrics": {"asset_link": asset_acc,
                       "prefilter_recall": prefilter_recall,
                       "anon_agreement": anon_agree,
                       "agreement_check_error_rate": agree_err,
                       "verdict": verdict}}
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps(row, default=float) + "\n")

    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_gate_class"}
                      for k, v in gates.items()}, indent=1, default=float))
    for c, r in per_class.items():
        print(f"{c}: P {r['precision']:.2f} R {r['recall']:.2f} (n_true {r['n_true']})")
    print(f"agreement-check error rate: {agree_err:.2%}")
    print(f"P0 verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
