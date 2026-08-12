"""The band universe is the independence axis of the whole replication. If it
overlaps liq_fade_i1's top-50 in any (symbol, month) cell, the samples are not
disjoint and the experiment is not a replication."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def _synthetic_daily(n_symbols=200, n_days=400, seed=3):
    """Daily panel with strictly ordered volumes so ranks are unambiguous:
    SYM000 has the highest quote_volume, SYM199 the lowest."""
    idx = pd.date_range("2020-06-01", periods=n_days, freq="D", tz="UTC")
    rng = np.random.default_rng(seed)
    out = {}
    for i in range(n_symbols):
        out[f"SYM{i:03d}"] = pd.DataFrame(
            {"close": 100.0 + rng.normal(0, 1, n_days).cumsum(),
             "quote_volume": float(n_symbols - i) * 1e6},
            index=idx)
    return out


def test_band_excludes_top50_every_month():
    from liq_fade_r1_universe import band_universe
    from tradingagents.xsect.liq_fade import monthly_top_n
    daily = _synthetic_daily()
    top50 = monthly_top_n(daily, "2021-01-01", "2021-06-01", n=50)
    band = band_universe(daily, "2021-01-01", "2021-06-01")
    assert set(band.keys()) == set(top50.keys())
    for m in band:
        assert not (set(band[m]) & set(top50[m])), (
            f"{m}: band overlaps top-50 -- samples not disjoint")


def test_band_is_ranks_51_to_150():
    from liq_fade_r1_universe import band_universe
    daily = _synthetic_daily()
    band = band_universe(daily, "2021-01-01", "2021-03-01")
    for m, syms in band.items():
        assert len(syms) == 100, f"{m}: expected 100 band symbols, got {len(syms)}"
        # volumes are strictly decreasing in the numeric suffix, so band must
        # be exactly SYM050..SYM149 in rank order
        assert syms == [f"SYM{i:03d}" for i in range(50, 150)]


def test_band_shorter_when_universe_smaller_than_150():
    from liq_fade_r1_universe import band_universe
    daily = _synthetic_daily(n_symbols=80)
    band = band_universe(daily, "2021-01-01", "2021-03-01")
    for m, syms in band.items():
        assert len(syms) == 30, f"{m}: expected 30 (80 listed - 50), got {len(syms)}"


def test_frozen_files_are_consistent():
    """Once generated, the three registration files must agree with each other."""
    uni_p = ROOT / "data" / "xsect" / "liq_fade_r1_universe.json"
    sym_p = ROOT / "data" / "xsect" / "liq_fade_r1_symbols.txt"
    miss_p = ROOT / "data" / "xsect" / "liq_fade_r1_symbols_missing.txt"
    if not uni_p.exists():
        pytest.skip("universe not yet generated")
    universe = json.loads(uni_p.read_text())
    union = {s for v in universe.values() for s in v}
    listed = {s.strip() for s in sym_p.read_text().splitlines() if s.strip()}
    assert listed == union, "symbols.txt does not match the universe union"
    missing = {s.strip() for s in miss_p.read_text().splitlines() if s.strip()}
    # missing.txt is a GENERATION-TIME snapshot of union minus what was on disk.
    # After Task 4's fetch it is no longer equal to (union - on_disk), so the
    # only durable invariant is containment.
    assert missing <= union, "missing.txt contains symbols outside the band union"


def test_frozen_universe_disjoint_from_liq_fade_i1():
    """The real registration files, not synthetic: no (symbol, month) cell may
    appear in both liq_fade_i1's top-50 and liq_fade_r1's band."""
    i1_p = ROOT / "data" / "xsect" / "liq_fade_universe.json"
    r1_p = ROOT / "data" / "xsect" / "liq_fade_r1_universe.json"
    if not r1_p.exists():
        pytest.skip("universe not yet generated")
    i1 = json.loads(i1_p.read_text())
    r1 = json.loads(r1_p.read_text())
    assert set(i1.keys()) == set(r1.keys()), "month keys must match liq_fade_i1"
    for m in r1:
        overlap = set(r1[m]) & set(i1[m])
        assert not overlap, f"{m}: {sorted(overlap)} in BOTH top-50 and band"
