import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.fetch_xsect_fundamentals import (
    ASSET_TO_SYMBOL, CM_ASSETS, STABLE_EXCLUDE, write_vintage,
)

ROOT = Path(__file__).resolve().parents[2]


def test_candidate_count_matches_registration():
    gates = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    assert len(CM_ASSETS) == gates["value_xs_t1"]["universe"]["n_candidates"]


def test_no_stablecoin_or_pegged_names():
    for bad in STABLE_EXCLUDE:
        assert bad not in CM_ASSETS


def test_every_asset_maps_to_a_perp_symbol():
    for a in CM_ASSETS:
        assert a in ASSET_TO_SYMBOL
        assert ASSET_TO_SYMBOL[a].endswith("USDT")


def test_mapped_symbols_exist_in_the_perp_store():
    kdir = ROOT / "data" / "xsect" / "klines"
    missing = [s for s in ASSET_TO_SYMBOL.values() if not (kdir / f"{s}.parquet").exists()]
    assert missing == [], f"unmapped perp symbols: {missing}"


def test_write_vintage_records_date_and_source(tmp_path):
    p = tmp_path / "v.json"
    write_vintage(p, "https://example.test/x")
    d = json.loads(p.read_text())
    assert d["source_url"] == "https://example.test/x"
    assert len(d["fetched_utc"]) >= 10
