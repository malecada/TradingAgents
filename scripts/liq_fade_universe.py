import json
from pathlib import Path
from tradingagents.xsect.universe import load_klines
from tradingagents.xsect.liq_fade import monthly_top_n

ROOT = Path(__file__).parents[1]
daily = load_klines(ROOT / "data/xsect/klines")
sel = monthly_top_n(daily, "2021-01-01", "2025-03-31", n=50)
out = {str(k.date()): v for k, v in sel.items()}
(ROOT / "data/xsect/liq_fade_universe.json").write_text(json.dumps(out, indent=1))
union = sorted({s for v in sel.values() for s in v})
(ROOT / "data/xsect/liq_fade_symbols.txt").write_text("\n".join(union) + "\n")
print(f"months={len(out)} union={len(union)}")
