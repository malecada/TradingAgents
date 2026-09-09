"""Phase roll-up: champions per cell, BH-FDR across cells, verdict lines.

Prospective v2 accounting for contender selection is exposed through the
primary_test/selection_p fields; dm_p retains a compatibility alias. Archived
reports must retain their registered policy and dated qualifications.

Verdict semantics (charter §2 + reports):
  SKILL-CANDIDATE          — champion beats the registered strong baseline with
                             FDR-surviving significance, clears the effect
                             floor, and is sub-period stable (dev-only; U4/U5
                             holdout/MCS confirmation happens in Phase 5)
  BASELINE-WINS            — no model improves on the registered baseline
  NO-SKILL                 — improvements exist but fail FDR or the floor
  PREDICTABLE-VS-WEAK-ONLY — manual override for cells where forensics showed
                             the registered-baseline margin is baseline
                             fragility (override carries a reason and the
                             forensics pointer; applied explicitly, never
                             silently)
  DEGENERATE               — no scoreable comparison
"""

from __future__ import annotations

import numpy as np


def bh_fdr(pvalues: "dict[str, float]", q: float = 0.10) -> "dict[str, bool]":
    """Benjamini-Hochberg: returns per-key pass flags; nan p never passes."""
    if not 0 < q < 1:
        raise ValueError("q must lie between zero and one")
    if any(np.isfinite(p) and not 0 <= p <= 1 for p in pvalues.values()):
        raise ValueError("p-values must lie between zero and one")
    items = [(k, p if np.isfinite(p) else 1.0) for k, p in pvalues.items()]
    out = {k: False for k in pvalues}
    if not items:
        return out
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    cutoff_idx = -1
    for i, (_, p) in enumerate(items, start=1):
        if p <= q * i / m:
            cutoff_idx = i
    for i, (k, _) in enumerate(items, start=1):
        out[k] = i <= cutoff_idx
    return out


def champion(card: dict) -> dict:
    """Best non-degenerate model by loss; falls back to the baseline row."""
    base_name = card["strong_baseline"]
    per = card["per_model"]
    base_loss = per[base_name]["loss_mean"]
    contenders = {n: r for n, r in per.items() if n != base_name}
    best_name, best = None, None
    for n, r in contenders.items():
        if not np.isfinite(r["loss_mean"]):
            continue
        if best is None or r["loss_mean"] < best["loss_mean"]:
            best_name, best = n, r
    if best is None or best["loss_mean"] >= base_loss:
        return {"model": base_name, "loss_mean": base_loss, "dm_p": float("nan"),
                "improvement_pct": 0.0, "baseline_wins": True,
                "subperiod_stable": False}
    sub = best.get("sub_periods", {}) or {}
    n_pos = sum(1 for v in sub.values() if v > 0)
    stable = len(sub) >= 3 and n_pos >= 2
    primary_test = best.get("primary_test", "cw" if best.get("nested", False) and card.get("loss") == "se" else "dm")
    eligible = bool(best.get("inference_eligible", not best.get("nested", False) or card.get("loss") == "se"))
    p_key = {"clark_west": "cw_p", "dm_hac": "dm_p", "cw": "cw_p", "dm": "dm_p"}.get(primary_test)
    raw_p = float(best.get(p_key, float("nan"))) if eligible and p_key else float("nan")
    adjusted = min(1.0, raw_p * len(contenders)) if np.isfinite(raw_p) else float("nan")
    return {
        "inference_policy": "hac-selection-v2",
        "inference_eligible": eligible,
        "primary_test": primary_test,
        "n_contenders": len(contenders),
        "raw_dm_p": float(best.get("dm_p", float("nan"))),
        "raw_primary_p": raw_p,
        "selection_p": adjusted,
        "model": best_name,
        "loss_mean": best["loss_mean"],
        "dm_p": adjusted,
        "improvement_pct": 100.0 * (base_loss - best["loss_mean"]) / abs(base_loss) if base_loss else float("nan"),
        "baseline_wins": False,
        "subperiod_stable": bool(stable),
    }


def verdict(fdr_pass: bool, floor_pass: bool, stable: bool,
            baseline_wins: bool, override: "str | None",
            inference_eligible: bool = True) -> str:
    if not inference_eligible:
        return "DEGENERATE (inference unavailable)"
    if override:
        return override
    if baseline_wins:
        return "BASELINE-WINS"
    if fdr_pass and floor_pass and stable:
        return "SKILL-CANDIDATE"
    return "NO-SKILL"


def by_fdr(pvalues: dict[str, float], q: float = .10) -> dict[str, bool]:
    """Prospective family control allowing arbitrary dependence across cells.

    Includes unscoreable preregistered hypotheses as non-rejections. BH remains
    available to reproduce archived registered arithmetic under its assumptions.
    """
    m = len(pvalues)
    harmonic = sum(1 / i for i in range(1, m + 1)) if m else 1
    return bh_fdr(pvalues, q=q / harmonic)
