"""llm_c2_veto_ovl P2 — classifier dev (frozen prompt, gpt-5.4-mini, temp 0).

Daily market-severity call over dev D (2021-01-01 -> 2025-03-31): digest of
deduplicated headlines with event_ts <= end of day t-1 UTC, 48h window,
max 60 headlines. Severity {0,1,2} -> multiplier {1.0, 0.5, 0.0}, budget
<=10 veto-days per calendar year in calendar order.

Two registered runs: named and anonymized (entity/date placeholders).
Gates (charter §5 P2):
  (a) recall >= 0.5 of oracle veto days receiving m<1 (before budget cut)
  (b) budget respected by construction
  (c) anonymization kill-probe: anon recall >= 0.7 x named recall, else STOP

All calls disk-cached (idempotent; no double spend). No prompt iteration
after evaluation output exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from llm_veto_engine import DEV_D  # noqa: E402

ALPACA_ROOT = HERE.parent.parent / "TradingAgents" / "data" / "sentiment" / "alpaca"
GDELT_ROOT = HERE.parent.parent / "TradingAgents" / "data" / "sentiment" / "gdelt"
CORPUS_ROOTS = [ALPACA_ROOT, GDELT_ROOT]
OUTDIR = Path("data/predlab/llm_veto")
CACHE_DB = OUTDIR / "p2_call_cache.json"
OUT = OUTDIR / "p2_classifier.json"
LEDGER = Path("data/predlab/trial_ledger.jsonl")
MODEL = "gpt-5.4-mini"
BUDGET = 10

PROMPT = """You are a crypto market risk auditor. You are given a digest of news
headlines from the last 48 hours (crypto and macro). Classify the
CURRENT market-level stress severity for a systematic crypto portfolio.

Severity definitions:
- 2 (severe): ongoing or imminent systemic event — major exchange
  insolvency or withdrawal halt, top-20 protocol/stablecoin collapse or
  depeg in progress, exchange hack > $100M at a top-10 venue, forced
  liquidation cascade across venues, or an acute macro shock hitting all
  risk assets.
- 1 (elevated): credible, specific signs that such an event may be
  developing (proof-of-reserves panic, large fund insolvency rumors from
  multiple sources, regulatory emergency action against a systemically
  important venue).
- 0 (normal): everything else, including ordinary bad news, price drops,
  lawsuits, and single-project failures outside the top tier.

Rules: judge only from the given headlines; do not use knowledge of
later events; prefer 0 when uncertain; output exactly:
SEVERITY: <0|1|2>
REASON: <one line>

Headlines:
{headlines}"""

# deterministic anonymization: crypto/finance entities + dates -> placeholders
ENTITY_PATTERNS = [
    r"FTX|Alameda", r"Terra|LUNA|UST\b", r"Celsius", r"Three Arrows|3AC",
    r"Voyager", r"BlockFi", r"Genesis", r"Silvergate", r"Signature Bank",
    r"Silicon Valley Bank|SVB", r"USDC|Circle", r"Tether|USDT",
    r"Binance", r"Coinbase", r"Kraken", r"Bitfinex", r"Huobi", r"OKX|OKEx",
    r"Gemini", r"Mt\.? ?Gox", r"Sam Bankman-Fried|SBF", r"Do Kwon",
    r"Su Zhu", r"Kyle Davies", r"Alex Mashinsky", r"Changpeng Zhao|CZ\b",
    r"Bitcoin|BTC\b", r"Ethereum|ETH\b", r"Dogecoin|DOGE\b", r"Solana|SOL\b",
    r"Cardano|ADA\b", r"XRP|Ripple", r"Elon Musk", r"Tesla", r"MicroStrategy",
    r"Michael Saylor", r"Grayscale", r"Evergrande", r"Fed(?:eral Reserve)?",
    r"Powell", r"SEC\b", r"CFTC\b",
]
DATE_PATTERN = (r"\b(?:January|February|March|April|May|June|July|August|"
                r"September|October|November|December|Jan|Feb|Mar|Apr|Jun|"
                r"Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.? ?\d{0,2},? ?(?:20\d{2})?\b"
                r"|\b20\d{2}\b")


def anonymize(text: str) -> str:
    for i, pat in enumerate(ENTITY_PATTERNS):
        text = re.sub(pat, f"ENTITY_{i}", text, flags=re.IGNORECASE)
    text = re.sub(DATE_PATTERN, "DATE", text)
    return text


def load_headlines() -> pd.DataFrame:
    frames = []
    for root in CORPUS_ROOTS:
        for f in sorted(root.rglob("*.parquet")):
            frames.append(pd.read_parquet(f, columns=["event_ts", "headline"]))
    df = pd.concat(frames, ignore_index=True)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df = df.dropna(subset=["headline"]).sort_values("event_ts")
    return df


def digest_for(df: pd.DataFrame, day: pd.Timestamp) -> list[str]:
    """Headlines with event_ts in [day-2d 00:00, day-1 23:59] (info thru t-1)."""
    lo = (day - pd.Timedelta(days=2)).normalize()
    hi = day.normalize() - pd.Timedelta(seconds=1)
    heads = df.loc[(df["event_ts"] >= lo) & (df["event_ts"] <= hi),
                   "headline"].tolist()
    seen, out = set(), []
    for h in heads:
        k = h.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(h.strip())
    return out[-60:]


def call(client, day: str, variant: str, heads: list[str], cache: dict) -> int:
    key = f"{variant}|{day}|" + hashlib.sha256(
        "\n".join(heads).encode()).hexdigest()[:16]
    if key in cache:
        return cache[key]["severity"]
    if not heads:
        cache[key] = {"severity": 0, "reason": "empty digest"}
        return 0
    text_heads = "\n".join(f"- {h}" for h in heads)
    if variant == "anon":
        text_heads = anonymize(text_heads)
    r = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "user", "content": PROMPT.format(headlines=text_heads)}])
    text = r.choices[0].message.content.strip()
    m = re.search(r"SEVERITY:\s*([012])", text)
    sev = int(m.group(1)) if m else 0
    reason = ""
    rm = re.search(r"REASON:\s*(.+)", text)
    if rm:
        reason = rm.group(1).strip()[:200]
    cache[key] = {"severity": sev, "reason": reason}
    return sev


def run_variant(client, df, days, variant, cache, flush) -> pd.Series:
    sevs = {}
    for i, day in enumerate(days):
        sevs[day] = call(client, str(day.date()), variant,
                         digest_for(df, day), cache)
        if i % 25 == 0:
            flush()
            print(f"[{variant}] {day.date()} sev={sevs[day]} ({i+1}/{len(days)})",
                  flush=True)
    flush()
    return pd.Series(sevs)


def main() -> int:
    if OUT.exists():
        print(f"results exist ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    from dotenv import load_dotenv
    load_dotenv(HERE.parent.parent / "TradingAgents" / ".env")
    from openai import OpenAI
    client = OpenAI()

    p0 = json.loads((OUTDIR / "p0_oracle.json").read_text())
    oracle_days = set(p0["veto_days"])
    df = load_headlines()
    days = pd.date_range(DEV_D[0], DEV_D[1], freq="D", tz="UTC")

    cache = json.loads(CACHE_DB.read_text()) if CACHE_DB.exists() else {}

    def flush() -> None:
        CACHE_DB.write_text(json.dumps(cache, indent=0))

    out = {"experiment": "llm_c2_veto_ovl", "probe": "P2_classifier",
           "model": MODEL, "budget": BUDGET, "variants": {}}
    recalls = {}
    for variant in ("named", "anon"):
        sev = run_variant(client, df, days, variant, cache, flush)
        m_raw = sev.map({0: 1.0, 1: 0.5, 2: 0.0})
        flagged = m_raw[m_raw < 1.0]
        hit = [d for d in oracle_days if pd.Timestamp(d, tz="UTC") in flagged.index]
        recall = len(hit) / len(oracle_days)
        recalls[variant] = recall
        out["variants"][variant] = {
            "n_flagged_days": int((m_raw < 1.0).sum()),
            "flagged_per_year": {str(y): int(n) for y, n in
                                 flagged.groupby(flagged.index.year).size().items()},
            "recall_of_oracle_days": recall,
            "oracle_days_hit": sorted(hit),
            "severity_counts": {str(k): int(v) for k, v in
                                sev.value_counts().items()},
            "m_raw": {str(d.date()): float(v) for d, v in
                      m_raw[m_raw < 1.0].items()},
        }
        print(f"[{variant}] flagged {int((m_raw<1).sum())} days, "
              f"recall {recall:.2f}")

    named_r, anon_r = recalls["named"], recalls["anon"]
    gate_recall = named_r >= 0.5
    gate_anon = anon_r >= 0.7 * named_r
    verdict = "PASS" if (gate_recall and gate_anon) else "STOP"
    out["gates"] = {"recall_min": 0.5, "named_recall": named_r,
                    "anon_recall": anon_r,
                    "anon_floor": 0.7 * named_r,
                    "gate_recall": gate_recall, "gate_anon": gate_anon}
    out["verdict"] = verdict
    OUT.write_text(json.dumps(out, indent=1, default=float))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    for variant in ("named", "anon"):
        row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
               "experiment": "llm_c2_veto_ovl", "cell": f"P2_classifier_{variant}",
               "model": MODEL,
               "config": {"prompt": "charter appendix A frozen", "temp": 0,
                          "digest": "48h, max60, thru t-1", "variant": variant},
               "config_hash": f"p2-{variant}-v1", "git_commit": commit,
               "window": list(DEV_D),
               "metrics": {"recall": recalls[variant],
                           "n_flagged": out["variants"][variant]["n_flagged_days"]}}
        with LEDGER.open("a") as f:
            f.write(json.dumps(row, default=float) + "\n")
    print(f"P2 verdict: {verdict} (named {named_r:.2f}, anon {anon_r:.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
