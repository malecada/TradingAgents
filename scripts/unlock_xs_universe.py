"""Monthly PIT universe for unlock_xs_t1: emissions-mapped perps INTERSECT top-150 liquidity.

Mirrors scripts/value_xs_universe.py. Candidates come from the snapshotted
DefiLlama emissions store (see scripts/fetch_emissions.py) mapped to perp
symbols; the registered recipe is the intersection itself, and the realized
candidate count is written next to the universe for disclosure (the gate
recorded 129 on 2026-07-30; the protocol list has since grown).
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402
from tradingagents.xsect.unlock_xs import map_slugs_to_perps  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EMISSIONS_DIR = ROOT / "data" / "xsect" / "emissions"
GECKO_LIST = ROOT / "data" / "xsect" / "coingecko_coins_list.json"
OUT = ROOT / "data" / "xsect" / "unlock_xs_universe.json"
MAP_OUT = ROOT / "data" / "xsect" / "unlock_xs_slug_map.json"
DEV = ("2021-01-01", "2025-03-31")
FLOOR_RANK = 150   # registered in gates.json


def main() -> None:
    daily = load_klines(ROOT / "data" / "xsect" / "klines")
    slug_map = map_slugs_to_perps(EMISSIONS_DIR, GECKO_LIST, set(daily))
    MAP_OUT.write_text(json.dumps(slug_map, indent=1, sort_keys=True))
    allowed = set(slug_map.values())
    liquid = monthly_top_n(daily, DEV[0], DEV[1], n=FLOOR_RANK)
    out = {str(month.date()): sorted(set(syms) & allowed)
           for month, syms in liquid.items()}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    sizes = [len(v) for v in out.values()]
    print(f"candidates={len(slug_map)} months={len(out)} "
          f"breadth min/median/max="
          f"{min(sizes)}/{statistics.median(sizes)}/{max(sizes)}")


if __name__ == "__main__":
    main()
