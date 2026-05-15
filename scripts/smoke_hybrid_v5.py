#!/usr/bin/env python
"""Lightweight smoke: verify V5 pool_map routing produces different ETH signal
than V2 default routing.

No LLM call — only exercises tradingagents.strategies.quant_engine.get_quant_signal
with and without pool_map, comparing the magnitudes that the V2 vs V4-B LGB CSVs
produce for the same (ethereum, date). This is enough to catch a routing bug
before the multi-hour VPS run.

Run: python scripts/smoke_hybrid_v5.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.strategies.quant_engine import get_quant_signal
from tradingagents.strategies.quant_signal_provider import (
    V5QuantSignalProvider,
    build_provider,
)

DATE = "2025-06-02"

POOL_MAP = {
    "bitcoin": "data/multi_2coins_v2",
    "ethereum": "data/multi_2coins_pit_wf",
}


def main() -> int:
    print(f"V5 pool_map smoke @ {DATE}")
    print("=" * 60)

    btc_v2 = get_quant_signal("bitcoin", DATE, base_dir="data/multi_2coins_v2")
    btc_v5 = get_quant_signal("bitcoin", DATE, pool_map=POOL_MAP)
    eth_v2 = get_quant_signal("ethereum", DATE, base_dir="data/multi_2coins_v2")
    eth_v5 = get_quant_signal("ethereum", DATE, pool_map=POOL_MAP)

    for label, sig in [
        ("BTC v2-only", btc_v2),
        ("BTC v5     ", btc_v5),
        ("ETH v2-only", eth_v2),
        ("ETH v5     ", eth_v5),
    ]:
        print(f"  {label}: dir={sig.direction:5s} "
              f"mag={sig.magnitude:+.4f} regime={sig.regime}")

    assert btc_v2.direction == btc_v5.direction, "BTC v2 vs v5 should match (same pool)"
    assert abs(btc_v2.magnitude - btc_v5.magnitude) < 1e-9, (
        f"BTC magnitudes differ: {btc_v2.magnitude} vs {btc_v5.magnitude}"
    )
    print("[OK] BTC v2 and v5 produce identical signals (same pool).")

    if (eth_v2.direction == eth_v5.direction
            and abs(eth_v2.magnitude - eth_v5.magnitude) < 1e-9):
        print(
            "[WARN] ETH v2 and v5 magnitudes identical at this date. Possible but "
            "unlikely; pick another date if ETH 193f pool is supposed to differ."
        )
    else:
        print(
            f"[OK] ETH v2 ({eth_v2.magnitude:+.4f}) differs from "
            f"ETH v5 ({eth_v5.magnitude:+.4f}) — pool_map routing works."
        )

    provider = build_provider("v5", pool_map=POOL_MAP)
    assert isinstance(provider, V5QuantSignalProvider)
    import pandas as pd
    sig = provider.signal("ethereum", pd.Timestamp(DATE))
    assert abs(sig.magnitude - eth_v5.magnitude) < 1e-9
    print("[OK] V5QuantSignalProvider.signal() forwards pool_map correctly.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
