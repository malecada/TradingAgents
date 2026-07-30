import json
from pathlib import Path

import pandas as pd
import pytest

import scripts.fetch_xsect_fundamentals as fx
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


def test_empty_fetch_asset_round_trips_datetimeindex(tmp_path, monkeypatch):
    """fetch_asset's empty-result branch must honor its own UTC-indexed
    contract, or downstream loaders that check df.index.tz break on it."""
    class _FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [], "next_page_url": None}

    monkeypatch.setattr(fx.requests, "get", lambda *a, **k: _FakeResp())
    df = fx.fetch_asset("zzz_nonexistent", "2020-01-01", "2020-01-02")
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None

    p = tmp_path / "empty.parquet"
    df.to_parquet(p)
    df2 = pd.read_parquet(p)
    assert isinstance(df2.index, pd.DatetimeIndex)
    assert df2.index.tz is not None


def test_end_past_holdout_margin_is_rejected():
    with pytest.raises(SystemExit):
        fx._enforce_holdout_margin("2025-06-01")
    fx._enforce_holdout_margin("2025-04-15")  # exactly the margin: allowed
    fx._enforce_holdout_margin("2020-06-01")  # well inside: allowed


def test_universe_cache_used_without_network_call(tmp_path, monkeypatch):
    """Once resolved, _resolve_universe must read the pinned cache file and
    must not touch the network -- so import-time resolution (test
    collection, Task 4/5 imports) never depends on live API availability."""
    cache = tmp_path / "fundamentals_universe.json"
    cache.write_text(json.dumps({
        "resolved_utc": "2026-01-01T00:00:00+00:00",
        "source_url": "https://example.test/catalog-v2/asset-metrics",
        "assets": ["btc", "eth"],
        "mapping": {"btc": "BTCUSDT", "eth": "ETHUSDT"},
    }))
    monkeypatch.setattr(fx, "UNIVERSE_FILE", cache)

    def _boom(*a, **k):
        raise AssertionError("network must not be called when cache exists")

    monkeypatch.setattr(fx.requests, "get", _boom)
    assets, mapping = fx._resolve_universe()
    assert assets == ["btc", "eth"]
    assert mapping == {"btc": "BTCUSDT", "eth": "ETHUSDT"}


UNIV = ROOT / "data" / "xsect" / "value_xs_universe.json"


def test_universe_file_shape():
    u = json.loads(UNIV.read_text())
    assert len(u) >= 48                       # >= 4 years of months
    k = sorted(u)[0]
    assert k == "2021-01-01"
    assert all(s.endswith("USDT") for s in u[k])


def test_universe_is_subset_of_value_candidates():
    from scripts.fetch_xsect_fundamentals import ASSET_TO_SYMBOL
    allowed = set(ASSET_TO_SYMBOL.values())
    u = json.loads(UNIV.read_text())
    for month, syms in u.items():
        assert set(syms) <= allowed, f"{month} leaks non-candidate symbols"


def test_universe_never_reaches_into_holdout():
    u = json.loads(UNIV.read_text())
    assert max(u) < "2025-04-01"


def test_median_breadth_meets_registered_floor():
    u = json.loads(UNIV.read_text())
    import statistics
    med = statistics.median(len(v) for v in u.values())
    assert med >= 20, f"breadth STOP: median {med} < 20"
