"""liq_fade_r1 band universe: monthly PIT ranks 51-150, the independence axis
of the replication. Writes three registration files under data/xsect/:

  liq_fade_r1_universe.json        {month_start: [symbols]}, the frozen selection
  liq_fade_r1_symbols.txt          union of the above, one per line
  liq_fade_r1_symbols_missing.txt  union members with no 1h parquet yet (Task 4 input)

Band membership is computed as top-150 minus top-50 using the SAME monthly_top_n
selector as liq_fade_i1, so the two universes are disjoint per month by
construction. Spec: docs/superpowers/specs/2026-07-29-liq-fade-r1-design.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tradingagents.xsect.liq_fade import monthly_top_n  # noqa: E402
from tradingagents.xsect.universe import load_klines  # noqa: E402

DEV = ("2021-01-01", "2025-03-31")
LO_RANK, HI_RANK = 50, 150
XSECT = ROOT / "data" / "xsect"


def band_universe(daily, start, end, lo_rank=LO_RANK, hi_rank=HI_RANK):
    """Monthly PIT selection of ranks (lo_rank, hi_rank] by trailing 30d median
    quote_volume -- i.e. top-`hi_rank` with the top-`lo_rank` removed.

    Returns {month_start Timestamp: [symbols in rank order]}. Months where fewer
    than hi_rank symbols are eligible yield a shorter list; months where fewer
    than lo_rank are eligible yield an empty list.
    """
    inner = monthly_top_n(daily, start, end, n=lo_rank)
    outer = monthly_top_n(daily, start, end, n=hi_rank)
    return {m: [s for s in outer[m] if s not in set(inner[m])] for m in outer}


def main() -> None:
    daily = load_klines(XSECT / "klines")
    sel = band_universe(daily, *DEV)
    out = {str(k.date()): v for k, v in sel.items()}
    (XSECT / "liq_fade_r1_universe.json").write_text(json.dumps(out, indent=1))

    union = sorted({s for v in sel.values() for s in v})
    (XSECT / "liq_fade_r1_symbols.txt").write_text("\n".join(union) + "\n")

    on_disk = {p.stem for p in (XSECT / "klines_1h").glob("*.parquet")}
    missing = [s for s in union if s not in on_disk]
    (XSECT / "liq_fade_r1_symbols_missing.txt").write_text("\n".join(missing) + "\n")

    i1 = json.loads((XSECT / "liq_fade_universe.json").read_text())
    never_top50 = sorted(set(union) - {s for v in i1.values() for s in v})

    print(f"months={len(out)} band_union={len(union)} "
          f"already_on_disk={len(union) - len(missing)} to_fetch={len(missing)}")
    print(f"never_in_i1_top50={len(never_top50)}")
    print(f"avg_band_size_per_month={sum(len(v) for v in sel.values()) / len(sel):.1f}")


if __name__ == "__main__":
    main()
