"""llm_c3p_pair_xs P1 — anonymization kill-probe (charter §5).

26-week seeded dev subset run twice with IDENTICAL pairs/orders:
anonymous tags (primary) and named tags (probe only). Weekly Spearman IC
of the BT score vs 5d forward log returns.

Gate (frozen in data/llm_pair_xs/gates.json): named IC exceeding anonymous
IC by > 50% relative => memorization STOP. Implementation, written before
any P1 result exists: STOP iff
    mean_named_ic - mean_anon_ic > max(0.5 * abs(mean_anon_ic), 0.01)
(the difference form covers a zero/negative anonymous IC; the 0.01
absolute floor stops noise-level anon IC from making the probe a
hair-trigger). Primary evaluation is ALWAYS anonymous.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_pair_xs_p0 import (  # noqa: E402
    CACHE, DEV_END, LEDGER, MODEL, OUT, SEED, run_week, usage)
from llm_rank_xs_cards import load_panels  # noqa: E402

RESULT = OUT / "p1_anonymization.json"
N_WEEKS = 26
FWD_DAYS = 5


def weekly_ic(bt: pd.Series, fwd: pd.Series) -> float:
    common = bt.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 20:
        return float("nan")
    return float(spearmanr(bt[common], fwd[common]).statistic)


def main() -> int:
    if RESULT.exists():
        print(f"{RESULT} exists — refusing to overwrite (stop rule)")
        return 1
    from dotenv import load_dotenv
    load_dotenv(".env")
    from openai import OpenAI
    client = OpenAI()

    cards = pd.read_parquet(Path("data/llm_rank_xs") / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]
    rng = np.random.default_rng(SEED + 1)
    dates = sorted(cards["date"].unique())
    weeks = sorted(pd.Timestamp(w) for w in
                   rng.choice(dates, size=N_WEEKS, replace=False))

    close, _opens, _dvol = load_panels()
    close.index = pd.to_datetime(close.index, utc=True)
    fwd_all = np.log(close.shift(-FWD_DAYS) / close)

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    per_week = []
    for d in weeks:
        wk = cards[cards["date"] == d]
        fwd = fwd_all.loc[d] if d in fwd_all.index else pd.Series(dtype=float)
        anon_bt, _, rr_a = run_week(client, wk, d, cache, "anon")
        named_bt, _, rr_n = run_week(client, wk, d, cache, "named", named=True)
        CACHE.write_text(json.dumps(cache))
        row = {"week": str(d.date()), "n": int(wk["symbol"].nunique()),
               "anon_ic": weekly_ic(anon_bt, fwd),
               "named_ic": weekly_ic(named_bt, fwd),
               "anon_named_rho": float(spearmanr(anon_bt, named_bt).statistic),
               "resolution_anon": rr_a, "resolution_named": rr_n}
        per_week.append(row)
        print(row, flush=True)

    anon_ics = [w["anon_ic"] for w in per_week if np.isfinite(w["anon_ic"])]
    named_ics = [w["named_ic"] for w in per_week if np.isfinite(w["named_ic"])]
    mean_anon, mean_named = float(np.mean(anon_ics)), float(np.mean(named_ics))
    excess = mean_named - mean_anon
    threshold = max(0.5 * abs(mean_anon), 0.01)
    verdict = "STOP" if excess > threshold else "PASS"

    res = {"experiment": "llm_c3p_pair_xs", "probe": "P1_anonymization",
           "weeks": per_week, "n_weeks_ic": len(anon_ics),
           "mean_anon_ic": mean_anon, "mean_named_ic": mean_named,
           "named_excess": excess, "stop_threshold": threshold,
           "criteria": "STOP iff named-anon > max(0.5*|anon|, 0.01)",
           "verdict": verdict,
           "fresh_calls": int(usage["fresh_calls"]),
           "prompt_tokens": int(usage["prompt_tokens"]),
           "completion_tokens": int(usage["completion_tokens"])}
    RESULT.write_text(json.dumps(res, indent=1))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    for cell, ic in (("P1_anon_26wk", mean_anon), ("P1_named_26wk", mean_named)):
        row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "experiment": "llm_c3p_pair_xs", "cell": cell, "model": MODEL,
               "config": {"weeks": N_WEEKS, "fwd_days": FWD_DAYS,
                          "seed": SEED + 1},
               "config_hash": cell, "git_commit": commit + ("-dirty" if dirty else ""),
               "window": ["2021-01-01", "2025-03-31"],
               "metrics": {"mean_weekly_ic": ic, "verdict": verdict}}
        with LEDGER.open("a") as f:
            f.write(json.dumps(row) + "\n")
    print(f"P1 verdict: {verdict} | anon IC {mean_anon:.4f} vs named {mean_named:.4f}"
          f" (excess {excess:+.4f}, stop > {threshold:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
