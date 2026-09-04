"""Synthetic end-to-end run of predlab_smw_features.main() on a tmp data dir:
checks day assignment from block anchors, USD conversion, contract exclusion,
PIT smart set (episodes complete strictly before the day) and F1/F2/F4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import predlab_smw_features as feat  # noqa: E402

DAY = 86_400
T0 = 1_700_000_000 - (1_700_000_000 % DAY)      # a UTC midnight
BLOCK0 = 18_000_000
ROUTER = "0x" + "ee" * 20


def _setup(tmp_path, monkeypatch):
    smw = tmp_path / "smw"
    raw = smw / "raw" / "2023-11-01"
    raw.mkdir(parents=True)
    panels = tmp_path / "panels"
    panels.mkdir()
    monkeypatch.setattr(feat, "SMW", smw)
    monkeypatch.setattr(feat, "RAW", smw / "raw")
    monkeypatch.setattr(feat, "PANELS", panels)
    monkeypatch.setattr(feat, "DEV_END", "2030-01-01")
    # 12 s blocks: 7,200 blocks per day; anchors every 2,000 blocks
    blocks = np.arange(BLOCK0 - 2000, BLOCK0 + 60 * 7200, 2000)
    pd.DataFrame({"block": blocks, "ts": T0 + (blocks - BLOCK0) * 12}).to_parquet(smw / "anchors.parquet")
    pools = {"AAAUSDT": [{"sym": "AAAUSDT", "pool": "0xpa", "quote": "WETH", "version": 2}],
             "BBBUSDT": [{"sym": "BBBUSDT", "pool": "0xpb", "quote": "USDC", "version": 3}]}
    (smw / "pools.json").write_text(json.dumps({"by_symbol": pools}))
    (smw / "universe.json").write_text(json.dumps({"2023-11-01": ["AAAUSDT", "BBBUSDT"],
                                                   "2023-12-01": ["AAAUSDT", "BBBUSDT"]}))
    idx = pd.to_datetime(T0 + np.arange(-5, 70) * DAY, unit="s", utc=True)
    close = pd.DataFrame({"ETHUSDT": 2000.0,
                          "AAAUSDT": 1.0 + 0.01 * np.arange(len(idx)),      # rising: buyers earn +
                          "BBBUSDT": 1.0 - 0.005 * np.arange(len(idx))}, index=idx)  # falling
    close.to_parquet(panels / "close.parquet")
    return smw, raw


def _swap(pool, day, wallet, quote_amt, idx):
    return {"pool": pool, "block": BLOCK0 + day * 7200 + 100 + idx, "log_index": idx,
            "recipient": wallet, "token_amt": 1.0, "quote_amt": quote_amt, "version": 2}


def test_pipeline_end_to_end(tmp_path, monkeypatch):
    smw, raw = _setup(tmp_path, monkeypatch)
    rows = []
    # wallet good buys AAA (rising) on days 0..9 -> 10 winning episodes complete by day 16
    # wallet bad buys BBB (falling) on days 0..9 -> 10 losing episodes
    # router (contract) buys everything every day with huge size
    for d in range(0, 40):
        if d < 10:
            rows.append(_swap("0xpa", d, "0xgood", 1.0, 1))       # 1 WETH = $2000
            rows.append(_swap("0xpb", d, "0xbad", 500.0, 2))     # $500 USDC
        rows.append(_swap("0xpa", d, ROUTER, 50.0, 3))            # $100k contract flow
        rows.append(_swap("0xpb", d, ROUTER, 50000.0, 4))
        rows.append(_swap("0xpa", d, "0xnoise%02d" % d, 0.1, 5))  # one-off small buyers
    # day 30: good wallet buys AAA again, bad wallet sells AAA
    rows.append(_swap("0xpa", 30, "0xgood", 2.0, 6))
    rows.append(_swap("0xpa", 30, "0xbad", -1.0, 7))
    pd.DataFrame(rows).to_parquet(raw / "main_1.parquet", index=False)

    def fake_batch(method, params_list):
        assert method == "eth_getCode"
        return ["0x6060" if p[0] == ROUTER else "0x" for p in params_list]
    monkeypatch.setattr(feat.rpc_pool, "rpc_batch", fake_batch)

    feat.main()
    F = pd.read_parquet(smw / "features.parquet")
    Q = pd.read_parquet(smw / "qualified_daily.parquet")
    build = json.loads((smw / "feature_build.json").read_text())
    assert build["n_contracts"] == 1
    d0 = T0 // DAY
    # PIT: episodes from days 0..4 complete on days 7..11 -> first qualified (>=5, strictly before) on day 12
    q = Q.set_index("day")["n_qualified"]
    assert q.get(d0 + 11, 0) == 0 and q[d0 + 12] == 2
    # day 30: smart set = good only (top quintile of two records -> cut between)
    row = F[(F["sym"] == "AAAUSDT") & (F["day"] == d0 + 30)].iloc[0]
    gross_total = 2.0 * 2000 + 1.0 * 2000 + 50.0 * 2000 + 0.1 * 2000   # ALL recipients incl. router
    assert np.isclose(row["gross_total"], gross_total)
    assert np.isclose(row["f1"], 2.0 * 2000 / gross_total) and row["f2"] == 1.0 and row["f3"] == 0.0
    # F4: day 30 buyers (good + noise) = 2 non-contract vs prior 7 days of 1 noise buyer each
    assert np.isclose(row["f4"], np.log(2 / 1))
    # day assignment: block BLOCK0 + 30*7200 + 100 -> day 30
    assert row["date"] == pd.Timestamp(T0 + 30 * DAY, unit="s", tz="UTC")
    # contract rows excluded from n_buyers: day 5 buyers = good + noise = 2
    r5 = F[(F["sym"] == "AAAUSDT") & (F["day"] == d0 + 5)].iloc[0]
    assert r5["n_buyers"] == 2
