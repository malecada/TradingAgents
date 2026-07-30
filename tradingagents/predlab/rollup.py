"""Phase roll-up: champions per cell, BH-FDR across cells, verdict lines.

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
    items = [(k, p) for k, p in pvalues.items() if not np.isnan(p)]
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
        if best is None or r["loss_mean"] < best["loss_mean"]:
            best_name, best = n, r
    if best is None or best["loss_mean"] >= base_loss:
        return {"model": base_name, "loss_mean": base_loss, "dm_p": float("nan"),
                "improvement_pct": 0.0, "baseline_wins": True,
                "subperiod_stable": False}
    sub = best.get("sub_periods", {}) or {}
    n_pos = sum(1 for v in sub.values() if v > 0)
    stable = len(sub) >= 3 and n_pos >= 2
    return {
        "model": best_name,
        "loss_mean": best["loss_mean"],
        "dm_p": float(best["dm_p"]),
        "improvement_pct": 100.0 * (base_loss - best["loss_mean"]) / base_loss,
        "baseline_wins": False,
        "subperiod_stable": bool(stable),
    }


def verdict(fdr_pass: bool, floor_pass: bool, stable: bool,
            baseline_wins: bool, override: "str | None") -> str:
    if override:
        return override
    if baseline_wins:
        return "BASELINE-WINS"
    if fdr_pass and floor_pass and stable:
        return "SKILL-CANDIDATE"
    return "NO-SKILL"
