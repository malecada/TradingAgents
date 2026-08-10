"""llm_c2_veto_ovl P1 — news recall audit on oracle veto days.

For each P0 oracle veto day t: pull all admissible-corpus headlines with
event_ts in [t-1 00:00, t 23:59] UTC (charter: same-day-or-earlier, <=24h
lookback), screen with the pinned cheap tier for presence of >=1
market-level crisis-class headline (hack / insolvency / withdrawal-halt /
depeg / regulatory shock / liquidation cascade / macro shock), and write
the per-day audit table for hand check.

STOP if coverage < 60% of oracle veto days.
Corpus: Alpaca PIT store (TradingAgents/data/sentiment/alpaca) incl. the
declared 2021-01..2023-09 backfill. Screening calls are cached on disk
(idempotent reruns, no double spend).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ALPACA_ROOT = HERE.parent.parent / "TradingAgents" / "data" / "sentiment" / "alpaca"
OUTDIR = Path("data/predlab/llm_veto")
OUT = OUTDIR / "p1_news_recall.json"
CACHE = OUTDIR / "p1_screen_cache.json"
LEDGER = Path("data/predlab/trial_ledger.jsonl")
MODEL = "gpt-5.4-mini"
COVERAGE_FLOOR = 0.60

SCREEN_PROMPT = """You are auditing a news corpus. Below are crypto/macro news headlines
from a 48-hour window. Answer whether at least one headline reports a
market-level crisis-class event: exchange hack or exploit, exchange or
fund insolvency, withdrawal halt, stablecoin or major-protocol depeg or
collapse, systemic regulatory emergency action, forced liquidation
cascade, or an acute macro shock hitting all risk assets. Ordinary bad
news, price drops, single small-project failures do NOT count.

Headlines:
{headlines}

Output exactly:
CRISIS: <YES|NO>
EVIDENCE: <the single strongest qualifying headline, verbatim, or NONE>"""


def headlines_for(day: pd.Timestamp) -> list[str]:
    lo = (day - pd.Timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    hi = day.strftime("%Y-%m-%d 23:59:59")
    months = {(day.year, day.month), ((day - pd.Timedelta(days=1)).year,
                                      (day - pd.Timedelta(days=1)).month)}
    frames = []
    for y, m in months:
        p = ALPACA_ROOT / str(y) / f"{m:02d}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=["event_ts", "headline"]))
    if not frames:
        return []
    df = pd.concat(frames)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    mask = (df["event_ts"] >= pd.Timestamp(lo, tz="UTC")) & \
           (df["event_ts"] <= pd.Timestamp(hi, tz="UTC"))
    heads = df.loc[mask].sort_values("event_ts")["headline"].dropna().tolist()
    seen, out = set(), []
    for h in heads:
        k = h.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(h.strip())
    return out[:120]


def screen(day: str, heads: list[str], cache: dict) -> dict:
    if day in cache:
        return cache[day]
    if not heads:
        cache[day] = {"crisis": "NO", "evidence": "NONE", "n_headlines": 0,
                      "note": "empty window"}
        return cache[day]
    from openai import OpenAI
    client = OpenAI()
    msg = SCREEN_PROMPT.format(headlines="\n".join(f"- {h}" for h in heads))
    r = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "user", "content": msg}])
    text = r.choices[0].message.content.strip()
    crisis = "YES" if "CRISIS: YES" in text.upper() else "NO"
    evidence = "NONE"
    for line in text.splitlines():
        if line.upper().startswith("EVIDENCE:"):
            evidence = line.split(":", 1)[1].strip()
    cache[day] = {"crisis": crisis, "evidence": evidence,
                  "n_headlines": len(heads)}
    return cache[day]


def main() -> int:
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    from dotenv import load_dotenv
    load_dotenv(HERE.parent.parent / "TradingAgents" / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY missing")
        return 1

    p0 = json.loads((OUTDIR / "p0_oracle.json").read_text())
    days = [pd.Timestamp(d, tz="UTC") for d in p0["veto_days"]]
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    rows = []
    for day in days:
        key = str(day.date())
        heads = headlines_for(day)
        res = screen(key, heads, cache)
        CACHE.write_text(json.dumps(cache, indent=1))
        rows.append({"day": key, **res})
        print(f"{key}: {res['crisis']:3s} ({res['n_headlines']:3d} heads) {res['evidence'][:80]}")

    n_yes = sum(1 for r in rows if r["crisis"] == "YES")
    coverage = n_yes / len(rows)
    verdict = "PASS" if coverage >= COVERAGE_FLOOR else "STOP"
    res = {"experiment": "llm_c2_veto_ovl", "probe": "P1_news_recall",
           "corpus": "alpaca PIT store incl. declared 2021-01..2023-09 backfill "
                     "(provider event_ts + 60s synthetic ingest lag, store-wide "
                     "convention, disclosed)",
           "screen_model": MODEL, "coverage_floor": COVERAGE_FLOOR,
           "n_days": len(rows), "n_with_crisis_news": n_yes,
           "coverage": coverage, "verdict": verdict, "days": rows}
    OUT.write_text(json.dumps(res, indent=1, default=float))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
           "experiment": "llm_c2_veto_ovl", "cell": "P1_news_recall",
           "model": MODEL,
           "config": {"window_hours": 48, "coverage_floor": COVERAGE_FLOOR},
           "config_hash": "p1-recall-48h", "git_commit": commit,
           "window": p0["window_D"],
           "metrics": {"coverage": coverage, "n_days": len(rows),
                       "n_with_crisis_news": n_yes}}
    with LEDGER.open("a") as f:
        f.write(json.dumps(row, default=float) + "\n")
    print(f"\nP1 coverage {coverage:.0%} ({n_yes}/{len(rows)}) — verdict {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
