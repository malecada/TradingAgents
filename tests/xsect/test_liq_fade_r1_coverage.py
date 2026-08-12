"""Gate on data completeness before any band probe or run. A partial fetch
would produce a smoke:false result off an incomplete universe -- exactly the
failure mode liq_fade_dev._assert_data_complete was added to prevent."""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
XSECT = ROOT / "data" / "xsect"
SYMBOLS = XSECT / "liq_fade_r1_symbols.txt"
KLINES_1H = XSECT / "klines_1h"

WARMUP_START = pd.Timestamp("2020-06-01", tz="UTC")
DEV_END = pd.Timestamp("2025-03-31", tz="UTC")


def test_all_band_symbols_present():
    required = {s.strip() for s in SYMBOLS.read_text().splitlines() if s.strip()}
    on_disk = {p.stem for p in KLINES_1H.glob("*.parquet")}
    missing = sorted(required - on_disk)
    assert not missing, (
        f"{len(missing)}/{len(required)} band symbols still missing "
        f"(e.g. {missing[:5]}) -- fetch incomplete")


def test_band_coverage_spans_dev_window():
    """Every band symbol must have SOME data inside the dev window. A symbol
    whose entire history sits outside it contributes nothing and signals a
    universe-selection bug rather than a fetch gap."""
    required = sorted({s.strip() for s in SYMBOLS.read_text().splitlines() if s.strip()})
    empty = []
    for sym in required:
        p = KLINES_1H / f"{sym}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if df.empty or df.index.max() < WARMUP_START or df.index.min() > DEV_END:
            empty.append(sym)
    assert not empty, f"band symbols with no dev-window coverage: {empty}"


def test_manifest_agrees_with_disk():
    manifest = json.loads((XSECT / "klines_1h_manifest.json").read_text())
    required = {s.strip() for s in SYMBOLS.read_text().splitlines() if s.strip()}
    absent = sorted(s for s in required if s not in manifest)
    assert not absent, f"band symbols missing from manifest: {absent[:10]}"
