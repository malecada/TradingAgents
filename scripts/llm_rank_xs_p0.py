"""llm_c3_rank_xs P0 — determinism/stability probe (charter §5).

8 seeded dev weeks; three runs each with the SAME partition and tags:
  base      anonymous
  rerun     identical inputs, cache-bypassed (fresh API calls)
  shuffled  same batches, shuffled in-batch presentation order
Gates: per-week Spearman(base, rerun) >= 0.9; Spearman(base, shuffled)
>= 0.8. STOP if the ranking is a sampling or presentation artifact.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_rank_xs_rank import CACHE, DEV_END, OUT, rank_week, week_seed  # noqa: E402

RESULT = OUT / "p0_stability.json"
LEDGER = OUT / "trial_ledger.jsonl"
N_WEEKS = 8


def main() -> int:
    if RESULT.exists():
        print(f"{RESULT} exists — refusing to overwrite (stop rule)")
        return 1
    from dotenv import load_dotenv
    load_dotenv(".env")
    from openai import OpenAI
    client = OpenAI()

    cards = pd.read_parquet(OUT / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]
    rng = np.random.default_rng(20260814)
    dates = sorted(cards["date"].unique())
    weeks = sorted(rng.choice(dates, size=N_WEEKS, replace=False))

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    per_week = []
    for d in weeks:
        wk = cards[cards["date"] == d]
        seed = week_seed(pd.Timestamp(d), "base")
        base = rank_week(client, wk, cache, seed, tag_prefix="anon")
        rerun = rank_week(client, wk, cache, seed, tag_prefix="anon-rr")
        shuf = rank_week(client, wk, cache, seed, shuffle=True,
                         tag_prefix="anon-shuf")
        CACHE.write_text(json.dumps(cache))
        common = base.dropna().index.intersection(rerun.dropna().index)
        r_rr = float(spearmanr(base[common], rerun[common]).statistic)
        common2 = base.dropna().index.intersection(shuf.dropna().index)
        r_sh = float(spearmanr(base[common2], shuf[common2]).statistic)
        per_week.append({"week": str(pd.Timestamp(d).date()),
                         "n": int(len(base)), "rerun_rho": r_rr,
                         "shuffle_rho": r_sh})
        print(per_week[-1], flush=True)

    min_rr = min(w["rerun_rho"] for w in per_week)
    min_sh = min(w["shuffle_rho"] for w in per_week)
    verdict = "PASS" if (min_rr >= 0.9 and min_sh >= 0.8) else "STOP"
    res = {"experiment": "llm_c3_rank_xs", "probe": "P0_stability",
           "weeks": per_week, "min_rerun_rho": min_rr,
           "min_shuffle_rho": min_sh,
           "criteria": {"rerun_min": 0.9, "shuffle_min": 0.8},
           "verdict": verdict}
    RESULT.write_text(json.dumps(res, indent=1))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
           "experiment": "llm_c3_rank_xs", "cell": "P0_stability",
           "model": "gpt-5.4-mini",
           "config": {"weeks": N_WEEKS, "batch": 25, "rounds": 2},
           "config_hash": "p0-stability", "git_commit": commit,
           "window": ["2021-01-01", "2025-03-31"],
           "metrics": {"min_rerun_rho": min_rr, "min_shuffle_rho": min_sh,
                       "verdict": verdict}}
    with LEDGER.open("a") as f:
        f.write(json.dumps(row) + "\n")
    print(f"P0 verdict: {verdict} (min rerun {min_rr:.3f}, min shuffle {min_sh:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
