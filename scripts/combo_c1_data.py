"""combo_c1 holdout data preparation (no result is produced here).

Writes the two PIT universes the holdout sleeves need, using the parents' own
functions on the survivorship-safe daily store:
  data/xsect/liq_fade_universe_h1.json  monthly top-50 (min age 60d), 2025-04 .. 2026-06
  data/xsect/liq_fade_symbols_h1.txt    union of the above
  data/xsect/value_xs_universe_h1.json  monthly top-150 INTERSECT CoinMetrics-mapped names

The CoinMetrics fundamentals vintage for the holdout is pulled separately:
  python scripts/fetch_xsect_fundamentals.py --start 2020-06-01 --end 2026-07-01 \
      --out-dir data/xsect/fundamentals_h1 --allow-past-holdout combo_c1
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.xsect.combo_sleeves import load_cm_mapping  # noqa: E402
from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
H1 = ("2025-04-01", "2026-06-30")   # month starts 2025-04-01 .. 2026-06-01 cover the holdout


def main() -> None:
    daily = load_klines(ROOT / "data/xsect/klines")
    liq = monthly_top_n(daily, H1[0], H1[1], n=50)
    liq_out = {str(k.date()): v for k, v in liq.items()}
    (ROOT / "data/xsect/liq_fade_universe_h1.json").write_text(json.dumps(liq_out, indent=1))
    union = sorted({s for v in liq.values() for s in v})
    (ROOT / "data/xsect/liq_fade_symbols_h1.txt").write_text("\n".join(union) + "\n")
    sizes = [len(v) for v in liq_out.values()]
    print(f"liq_fade_h1: months={len(liq_out)} union={len(union)} "
          f"breadth min/med/max={min(sizes)}/{statistics.median(sizes)}/{max(sizes)}")

    allowed = set(load_cm_mapping(ROOT / "data/xsect/fundamentals_universe.json").values())
    liquid = monthly_top_n(daily, H1[0], H1[1], n=150)
    val_out = {str(m.date()): sorted(set(syms) & allowed) for m, syms in liquid.items()}
    (ROOT / "data/xsect/value_xs_universe_h1.json").write_text(json.dumps(val_out, indent=1, sort_keys=True))
    sizes = [len(v) for v in val_out.values()]
    print(f"value_xs_h1: months={len(val_out)} breadth min/med/max="
          f"{min(sizes)}/{statistics.median(sizes)}/{max(sizes)}")


if __name__ == "__main__":
    main()
