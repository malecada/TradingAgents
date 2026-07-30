import json

import numpy as np
import pandas as pd
import pytest

import scripts.value_xs_dev as vxd
from scripts.value_xs_dev import (VintageStampStale, _lag_from_vintage,
                                   decile_spread, measure_lag,
                                   verdict_from_probes)


def test_measure_lag_detects_two_day_publication_delay():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    # metric present only up to day 7 while klines run to day 9 => lag 2
    fund_last = days[7]
    kline_last = days[9]
    assert measure_lag(fund_last, kline_last) == 2


def test_p0_lag_gate_fails_when_vendor_frontier_more_than_two_days_behind_fetch():
    # fix round 2: P0's lag is the vendor's own frontier (vendor_max_time,
    # captured at fetch time from the catalog endpoint) staleness vs the
    # stamp's fetch time -- not a diff against the store's own (truncated)
    # last observation, which was fix round 1's defect.
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00",
               "vendor_max_time": "2026-07-25"}  # 5 days behind the fetch
    result = _lag_from_vintage(vintage)
    assert result["lag"] == 5
    assert result["pass"] is False


def test_p0_lag_gate_passes_at_exactly_the_registered_threshold():
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00",
               "vendor_max_time": "2026-07-28"}  # exactly 2 days behind
    result = _lag_from_vintage(vintage)
    assert result["lag"] == 2
    assert result["pass"] is True


def test_p0_lag_gate_fails_loudly_when_vendor_max_time_missing():
    # An older vintage stamp (pre fix-round-2) has no vendor_max_time. P0
    # must refuse to run rather than silently falling back to a
    # store-endpoint comparison -- that fallback is exactly the defect that
    # produced the superseded 443-day and 471-day measurements.
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00"}
    with pytest.raises(VintageStampStale):
        _lag_from_vintage(vintage)


def test_decile_spread_orders_cheap_minus_expensive():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    # cheap (low signal) names earn +1%/day, expensive earn -1%/day
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    spread = decile_spread(S, R, valid, leg_frac=0.2)
    assert spread > 0


def test_decile_spread_sign_flips_when_signal_inverted():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    assert decile_spread(-S, R, valid, leg_frac=0.2) < 0


def test_verdict_stops_on_any_failed_probe():
    ok = {"pass": True}
    bad = {"pass": False}
    assert verdict_from_probes(ok, ok, ok) == "CONTINUE"
    assert verdict_from_probes(ok, bad, ok) == "NEGATIVE-at-probe"
    assert verdict_from_probes(bad, ok, ok) == "NEGATIVE-at-probe"


def test_main_exits_2_and_writes_probes_json_on_stale_vintage_stamp(tmp_path, monkeypatch):
    # Fix round 3, Finding 1: VintageStampStale must not bypass the STOP
    # contract. Before this fix, main() had no exception boundary around
    # probe_p0_lag(), so a stale stamp died with Python's default exit 1
    # and wrote no probes.json -- the same bug class that cost two rounds:
    # a failure loud in a unit test but not wired into the contract the
    # rest of the pipeline depends on. Uses a synthetic tmp-dir store via
    # monkeypatch; never touches the real fundamentals/klines stores.
    days = pd.date_range(vxd.WARMUP_START, vxd.MAX_LOAD_END, freq="D", tz="UTC")

    fund_dir = tmp_path / "fundamentals"
    fund_dir.mkdir()
    pd.DataFrame(
        {"AdrActCnt": np.linspace(100, 200, len(days)),
         "TxCnt": np.linspace(1000, 2000, len(days)),
         "CapMrktCurUSD": np.linspace(1e9, 2e9, len(days))},
        index=days,
    ).to_parquet(fund_dir / "testcoin.parquet")

    klines_dir = tmp_path / "klines"
    klines_dir.mkdir()
    pd.DataFrame({"close": np.linspace(1.0, 2.0, len(days))}, index=days
                ).to_parquet(klines_dir / "TESTUSDT.parquet")

    univ_file = tmp_path / "universe.json"
    univ_file.write_text(json.dumps({"2021-01-01": ["TESTUSDT"]}))

    # Stale: no vendor_max_time key (predates fix round 2).
    vintage_file = tmp_path / "vintage.json"
    vintage_file.write_text(json.dumps(
        {"fetched_utc": "2026-07-30T00:00:00+00:00", "source_url": "test",
         "note": "test"}))

    out_dir = tmp_path / "out"

    monkeypatch.setattr(vxd, "FUND_DIR", fund_dir)
    monkeypatch.setattr(vxd, "KLINES_DIR", klines_dir)
    monkeypatch.setattr(vxd, "UNIV_FILE", univ_file)
    monkeypatch.setattr(vxd, "FUND_VINTAGE_FILE", vintage_file)
    monkeypatch.setattr(vxd, "OUT_DIR", out_dir)
    monkeypatch.setattr(vxd, "ASSET_TO_SYMBOL", {"testcoin": "TESTUSDT"})

    with pytest.raises(SystemExit) as exc:
        vxd.main()
    assert exc.value.code == 2

    probes = json.loads((out_dir / "probes.json").read_text())
    assert probes["verdict"] == "NEGATIVE-at-probe"
    p0 = probes["probes"][0]
    assert p0["probe"] == "P0_publication_lag"
    assert p0["pass"] is False
    assert p0["error"] == "vintage_stamp_stale"
    assert "vendor_max_time" in p0["note"]


def test_load_all_klines_never_exceed_max_load_end():
    # Fix round 3, Finding 2: data/xsect/klines/ is a shared,
    # continuously-updated store (observed reaching 2026-07-02 -- deep
    # inside the sealed holdout -- before this fix). _load_all must
    # truncate every frame at MAX_LOAD_END; touches the real store.
    _, klines, _, _, _ = vxd._load_all()
    bound = pd.Timestamp(vxd.MAX_LOAD_END, tz="UTC")
    assert len(klines) > 0
    over = {s: str(d.index.max()) for s, d in klines.items()
           if len(d) and d.index.max() > bound}
    assert over == {}, f"klines frames exceeding MAX_LOAD_END: {over}"
