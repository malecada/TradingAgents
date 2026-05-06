#!/usr/bin/env python
"""Generate per-coin hybrid quant+LLM signals over a date range.

Drop-in cousin of ``scripts/generate_agent_signals.py`` for the
asset-agnostic hybrid graph. Captures the Layer 2 ``ModulatedPosition``
emitted by the new Modulator node:

  date, coin, regime, regime_confidence, hurst, quant_direction,
  quant_magnitude, llm_multiplier, llm_confidence, llm_uncertainty,
  effective_weight, position, unlock_flag, rolling_llm_edge, narrative

Usage:
    python scripts/generate_hybrid_signals.py \\
        --coins bitcoin ethereum \\
        --start 2026-01-16 --end 2026-04-15 \\
        --analysts market onchain crypto_sentiment prediction \\
        --output-dir data/hybrid_signals_p1
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--coins", nargs="+", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument(
        "--analysts",
        nargs="+",
        default=["market", "onchain", "crypto_sentiment", "prediction"],
    )
    p.add_argument("--llm-provider", default="openai")
    p.add_argument("--deep-think", default="gpt-4o-mini")
    p.add_argument("--quick-think", default="gpt-4o-mini")
    p.add_argument("--output-dir", default="data/hybrid_signals_p1")
    p.add_argument("--anonymize", action="store_true",
                   help="Enable asset-name anonymization (Tier A4)")
    p.add_argument("--force", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    log = logging.getLogger(__name__)
    t0 = time.time()

    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    cfg = DEFAULT_CONFIG.copy()
    cfg["llm_provider"] = args.llm_provider
    cfg["deep_think_llm"] = args.deep_think
    cfg["quick_think_llm"] = args.quick_think
    cfg["asset_class"] = "crypto"
    cfg["replay_cache"] = True
    cfg["anonymize_assets"] = bool(args.anonymize)

    print(f"\n{'=' * 60}")
    print(f"  Hybrid Signal Generation (Layer 1 + Modulator)")
    print(f"{'=' * 60}")
    print(f"  Coins      : {', '.join(args.coins)}")
    print(f"  Period     : {args.start} -> {args.end}")
    print(f"  Analysts   : {', '.join(args.analysts)}")
    print(f"  LLM        : {args.deep_think} / {args.quick_think}")
    print(f"  Anonymize  : {args.anonymize}")
    print(f"  Output     : {args.output_dir}")
    print()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ta = TradingAgentsGraph(
        selected_analysts=args.analysts, debug=False, config=cfg,
    )

    dates = pd.date_range(start=args.start, end=args.end, freq="D")

    for coin in args.coins:
        csv_path = out_dir / f"{coin}_{args.start}_{args.end}.csv"
        cached: list[dict] = []
        have: set[str] = set()
        if csv_path.exists() and not args.force:
            df_old = pd.read_csv(csv_path, parse_dates=["date"])
            cached = df_old.to_dict(orient="records")
            have = {pd.Timestamp(d).strftime("%Y-%m-%d") for d in df_old["date"]}
            log.info(f"{coin}: resuming with {len(cached)} cached rows")

        rows = list(cached)
        for i, dt in enumerate(dates):
            ds = dt.strftime("%Y-%m-%d")
            if ds in have:
                continue
            try:
                final_state, mp, qs, narrative = ta.propagate_with_modulator(coin, ds)
            except Exception as exc:
                log.error(f"{coin} @ {ds}: {exc}")
                rows.append({"date": dt, "coin": coin, "error": str(exc)[:200]})
                continue
            row = {
                "date": dt,
                "coin": coin,
                "regime": (qs or {}).get("regime"),
                "regime_confidence": (qs or {}).get("regime_confidence"),
                "hurst": (qs or {}).get("hurst"),
                "quant_direction": (qs or {}).get("direction"),
                "quant_magnitude": (qs or {}).get("magnitude"),
                "llm_multiplier": (mp or {}).get("llm_multiplier"),
                "llm_confidence": (mp or {}).get("llm_confidence"),
                "llm_uncertainty": (mp or {}).get("llm_uncertainty"),
                "effective_weight": (mp or {}).get("effective_weight"),
                "position": (mp or {}).get("position"),
                "unlock_flag": (mp or {}).get("unlock_flag"),
                "rolling_llm_edge": (mp or {}).get("rolling_llm_edge"),
                "narrative": (narrative or "")[:500],
            }
            rows.append(row)
            tmp = csv_path.with_suffix(".csv.tmp")
            pd.DataFrame(rows).to_csv(tmp, index=False)
            tmp.replace(csv_path)
            if (i + 1) % 5 == 0:
                log.info(f"{coin}: {i+1}/{len(dates)} -> {csv_path}")

        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        df.to_csv(csv_path, index=False)
        log.info(f"{coin}: saved {len(df)} rows to {csv_path}")

    print(f"\n  Runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
