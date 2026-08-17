"""llm_c3p_pair_xs P2 (part 1) — full anonymous dev run (charter §5).

All 222 dev Fridays, anonymous tags, base construction (both orders of
every pair). Writes weekly BT scores to data/llm_pair_xs/scores_dev.parquet.
Idempotent: every LLM call is disk-cached, so a killed run resumes for
free; the scores file itself is refuse-overwrite (stop rule).

Scoring, residual IC, and the GBDT twin live in llm_pair_xs_p2_score.py.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_pair_xs_p0 as p0  # noqa: E402
from llm_pair_xs_p0 import CACHE, DEV_END, OUT, run_week, usage  # noqa: E402

SCORES = OUT / "scores_dev.parquet"


def main() -> int:
    if SCORES.exists():
        print(f"{SCORES} exists — refusing to overwrite (stop rule)")
        return 1
    p0.WORKERS = int(os.environ.get("PAIR_XS_WORKERS", "16"))
    from dotenv import load_dotenv
    load_dotenv(".env")
    from openai import OpenAI
    client = OpenAI()

    cards = pd.read_parquet(Path("data/llm_rank_xs") / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]  # dev clip: holdout never scored here

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    dates = sorted(pd.Timestamp(d) for d in cards["date"].unique())
    rows = []
    for i, d in enumerate(dates):
        wk = cards[cards["date"] == d]
        bt, _res, rr = run_week(client, wk, d, cache, "anon")
        CACHE.write_text(json.dumps(cache))
        for sym, v in bt.items():
            rows.append({"date": d, "symbol": sym, "score": float(v)})
        print(f"{d.date()} ({i + 1}/{len(dates)}): n={wk['symbol'].nunique()} "
              f"resolution={rr:.4f} fresh_calls={usage['fresh_calls']}",
              flush=True)
    pd.DataFrame(rows).to_parquet(SCORES, index=False)
    print(f"written {SCORES} | fresh_calls {usage['fresh_calls']} "
          f"prompt_tok {usage['prompt_tokens']} compl_tok {usage['completion_tokens']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
