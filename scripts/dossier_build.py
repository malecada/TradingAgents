"""Build dossiers for the weekly top-N universe over a date range (plan §6.2).

Usage: dossier_build.py --start 2022-01-01 --end 2024-12-31 [--top 50] [--seed 20261109] [--cost-cap 30]
Idempotent: existing dossier files are skipped. Quant forecasts are computed walk-forward once.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.anonymizer import Masker  # noqa: E402
from tradingagents.dossier.builder import OUT, build  # noqa: E402
from tradingagents.dossier.entities import Linker, build_dictionary  # noqa: E402
from tradingagents.dossier.llm_text import TextLLM  # noqa: E402
from tradingagents.dossier.quant_forecast import calibration, fit_predict, forward_returns, render_forecast  # noqa: E402
from tradingagents.dossier.universe import base_symbol, load_cards, weekly_top  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_v2c0_client import load_api_key  # noqa: E402

FORECASTS = Path("data/dossier/quant_forecasts.parquet")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--cost-cap", type=float, default=30.0)
    args = ap.parse_args()
    cards = load_cards()
    top = weekly_top(cards, args.top, args.start, args.end)
    fridays = sorted(top["date"].unique())
    bases = sorted({base_symbol(s) for s in cards["symbol"].unique()})
    dictionary = build_dictionary(bases)
    linker = Linker(dictionary)
    llm = TextLLM(api_key=load_api_key(), cost_cap_usd=args.cost_cap)
    # walk-forward quant forecasts for every Friday in range (all card symbols)
    if FORECASTS.exists():
        preds = pd.read_parquet(FORECASTS)
    else:
        preds = pd.DataFrame(columns=["date", "symbol", "pred_rank_pct"])
    fwd = forward_returns(sorted(cards["symbol"].unique()), sorted(cards["date"].unique()))
    new = []
    for f in fridays:
        if not ((preds["date"] == f).any() if len(preds) else False):
            p = fit_predict(cards, fwd, f)
            if len(p):
                new.append(p.assign(date=f))
    if new:
        preds = pd.concat([preds, *new], ignore_index=True)
        FORECASTS.parent.mkdir(parents=True, exist_ok=True)
        preds.to_parquet(FORECASTS, index=False)
    started, n = time.monotonic(), 0
    for f in fridays:
        calib = calibration(preds, fwd, f)
        week = top[top["date"] == f]
        for sym in week["symbol"]:
            target = OUT / pd.Timestamp(f).strftime("%Y-%m-%d") / f"{sym}.json"
            if target.exists():
                continue
            seed = args.seed + int(pd.Timestamp(f).timestamp() // 86400) * 7 + hash(sym) % 1000
            d = build(sym, f, cards, dictionary, linker, llm, seed=seed)
            row = preds[(preds["date"] == f) & (preds["symbol"] == sym)]
            pr = float(row["pred_rank_pct"].iloc[0]) if len(row) else None
            payload = json.loads(target.read_text())
            payload["quant_forecast"] = {"pred_rank_pct": pr, "calibration": calib,
                                         "text": render_forecast(pr, calib)}
            payload["text"] = payload["text"] + "\n## Quant forecast\n" + payload["quant_forecast"]["text"] + "\n"
            target.write_text(json.dumps(payload, indent=1, default=str))
            n += 1
            if n % 25 == 0:
                print(f"{n} dossiers; {pd.Timestamp(f).date()}; llm calls {llm.calls} cache {llm.cache_hits} spent ${llm.spent_usd:.3f}; "
                      f"{n / (time.monotonic() - started) * 3600:.0f}/h", flush=True)
    print(f"done: {n} new dossiers; llm spent ${llm.spent_usd:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
