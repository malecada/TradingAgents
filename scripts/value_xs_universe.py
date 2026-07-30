"""Monthly PIT universe for value_xs_t1: value candidates INTERSECT top-150 liquidity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL  # noqa: E402
from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "xsect" / "value_xs_universe.json"
DEV = ("2021-01-01", "2025-03-31")
FLOOR_RANK = 150   # registered in gates.json


def main() -> None:
    daily = load_klines(ROOT / "data" / "xsect" / "klines")
    liquid = monthly_top_n(daily, DEV[0], DEV[1], n=FLOOR_RANK)
    allowed = set(ASSET_TO_SYMBOL.values())
    out = {str(month.date()): sorted(set(syms) & allowed) for month, syms in liquid.items()}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    sizes = [len(v) for v in out.values()]
    print(f"months={len(out)} breadth min/median/max="
          f"{min(sizes)}/{sorted(sizes)[len(sizes)//2]}/{max(sizes)}")


if __name__ == "__main__":
    main()
