"""smw_xs pure functions: swap decoders, mapping rule."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_smw_fetch import SWAP2, SWAP3, decode_swap  # noqa: E402
from predlab_smw_map import base_symbol, map_symbols  # noqa: E402


def _w(v: int) -> str:
    return (v % (1 << 256)).to_bytes(32, "big").hex()


def _log(topic, words, recipient="0x" + "ab" * 20, block=100, idx=3):
    return {"topics": [topic, "0x" + "00" * 32, "0x" + "00" * 12 + recipient[2:]],
            "data": "0x" + "".join(words), "blockNumber": hex(block), "logIndex": hex(idx),
            "address": "0xpool"}


META2 = {"pool": "0xpool", "version": 2, "token_is_0": True, "token_dec": 18, "quote_dec": 18}
META3 = {"pool": "0xpool", "version": 3, "token_is_0": False, "token_dec": 6, "quote_dec": 18}


def test_v2_buy_token0_with_quote1():
    # wallet pays 2 WETH (token1 in), receives 1000 TOKEN (token0 out)
    lg = _log(SWAP2, [_w(0), _w(2 * 10**18), _w(1000 * 10**18), _w(0)])
    r = decode_swap(lg, META2)
    assert r["token_amt"] == 1000 and r["quote_amt"] == 2 and r["block"] == 100 and r["log_index"] == 3
    assert r["recipient"] == "0x" + "ab" * 20


def test_v2_sell_token0():
    lg = _log(SWAP2, [_w(500 * 10**18), _w(0), _w(0), _w(1 * 10**18)])
    r = decode_swap(lg, META2)
    assert r["token_amt"] == -500 and r["quote_amt"] == -1


def test_v3_buy_token1_signed_amounts():
    # token is token1 (6 dec), quote WETH is token0: pool receives +3 WETH, sends -2000 TOKEN
    lg = _log(SWAP3, [_w(3 * 10**18), _w(-2000 * 10**6), _w(0), _w(0), _w(0)])
    r = decode_swap(lg, META3)
    assert r["token_amt"] == 2000 and r["quote_amt"] == 3 and r["version"] == 3


def test_v3_sell_token1():
    lg = _log(SWAP3, [_w(-1 * 10**18), _w(700 * 10**6), _w(0), _w(0), _w(0)])
    r = decode_swap(lg, META3)
    assert r["token_amt"] == -700 and r["quote_amt"] == -1


def test_foreign_topic_ignored():
    assert decode_swap(_log(SWAP3, [_w(1)] * 5), META2) is None
    assert decode_swap(_log(SWAP2, [_w(1)] * 4), META3) is None


def test_base_symbol_strips_multiplier_and_quote():
    assert base_symbol("1000PEPEUSDT") == "PEPE"
    assert base_symbol("1000000MOGUSDT") == "MOG"
    assert base_symbol("LINKUSDT") == "LINK"
    assert base_symbol("1INCHUSDT") == "1INCH"


def test_map_prefers_ranked_then_single_unranked():
    coins = [{"id": "a-token", "symbol": "abc", "name": "A", "platforms": {"ethereum": "0x" + "1" * 40}},
             {"id": "b-token", "symbol": "abc", "name": "B", "platforms": {"ethereum": "0x" + "2" * 40}},
             {"id": "lone", "symbol": "xyz", "name": "X", "platforms": {"ethereum": "0x" + "3" * 40}},
             {"id": "sol-only", "symbol": "qqq", "name": "Q", "platforms": {"solana": "abc"}},
             {"id": "d1", "symbol": "dup", "name": "D1", "platforms": {"ethereum": "0x" + "4" * 40}},
             {"id": "d2", "symbol": "dup", "name": "D2", "platforms": {"ethereum": "0x" + "5" * 40}}]
    m = map_symbols(["ABCUSDT", "XYZUSDT", "QQQUSDT", "DUPUSDT"], coins, {"b-token": 50, "a-token": 900})
    assert m["ABCUSDT"]["cg_id"] == "b-token" and m["ABCUSDT"]["how"] == "fallback_ranked"
    assert m["XYZUSDT"]["cg_id"] == "lone" and m["XYZUSDT"]["how"] == "fallback_single_unranked"
    assert m["QQQUSDT"]["how"] == "fallback_no_candidate" and "address" not in m["QQQUSDT"]
    assert m["DUPUSDT"]["how"] == "fallback_ambiguous"
    m2 = map_symbols(["ABCUSDT"], coins, {"b-token": 812, "a-token": 900})
    assert m2["ABCUSDT"]["how"] == "fallback_ambiguous" and "address" not in m2["ABCUSDT"]


def test_binance_spot_rule_overrides_symbol_collision():
    coins = [{"id": "real-ton", "symbol": "ton", "name": "Toncoin", "platforms": {"ton": "x"}},
             {"id": "tokamak", "symbol": "ton", "name": "Tokamak", "platforms": {"ethereum": "0x" + "6" * 40}},
             {"id": "link", "symbol": "link", "name": "Chainlink", "platforms": {"ethereum": "0x" + "7" * 40}}]
    spot = {"ton": "real-ton", "link": "link"}
    m = map_symbols(["TONUSDT", "LINKUSDT"], coins, {"tokamak": 800, "link": 16}, spot)
    assert m["TONUSDT"]["how"] == "binance_spot_no_eth" and "address" not in m["TONUSDT"]
    assert m["LINKUSDT"]["how"] == "binance_spot" and m["LINKUSDT"]["cg_id"] == "link"


import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from predlab_smw_features import day_features, f4_acceleration, smart_sets  # noqa: E402


def test_smart_sets_are_strictly_pit_and_quintile():
    # wallet 0: 5 episodes completing day 10 (ret +1); wallet 1: 5 episodes completing day 10 (ret -1)
    # wallet 2: 4 episodes only (never qualified)
    ep = pd.DataFrame({"wallet": [0] * 5 + [1] * 5 + [2] * 4,
                       "complete_day": [10] * 10 + [5] * 4,
                       "ret": [1.0] * 5 + [-1.0] * 5 + [9.0] * 4})
    out = list(smart_sets(ep, np.array([10, 11]), n_wallets=3))
    d10, m10, nq10, _ = out[0]
    assert nq10 == 0 and not m10.any()          # completion day 10 is NOT < 10
    d11, m11, nq11, cut = out[1]
    assert nq11 == 2 and m11.tolist() == [True, False, False] and np.isclose(cut, 0.6)


def test_day_features_shares_use_total_denominator():
    sym = np.array(["A", "A", "A", "B"])
    wallet = np.array([0, 1, 2, 0])
    net = np.array([10.0, -4.0, 6.0, 3.0])
    smart = np.array([True, True, False])
    f = day_features(sym, wallet, net, smart, {"A": 40.0, "B": 0.0})
    assert f["A"] == (10.0 / 40.0, 1.0, 4.0 / 40.0)
    assert np.isnan(f["B"][0]) and f["B"][1] == 1.0


def test_f4_log_ratio_and_nan_on_zero_baseline():
    s = pd.Series([0, 0, 0, 0, 0, 0, 0, 5, 2, 2, 2, 2, 2, 2, 4], dtype=float)
    f4 = f4_acceleration(s)
    assert np.isnan(f4.iloc[7])                  # baseline 0
    assert np.isclose(f4.iloc[14], np.log(4 / np.mean([5, 2, 2, 2, 2, 2, 2])))


from predlab_smw_p0 import bh_qvalues, composite, residualize, universe_mask  # noqa: E402


def test_bh_qvalues_monotone_and_bounded():
    q = bh_qvalues(np.array([0.01, 0.04, 0.03, 0.5]))
    assert q.max() <= 1.0 and np.isclose(q[0], 0.04) and np.isclose(q[3], 0.5)
    assert q[1] >= q[2] or np.isclose(q[1], q[2])


def test_composite_requires_three_features_and_signs_f3():
    idx = pd.date_range("2024-01-01", periods=2, tz="UTC")
    cols = ["A", "B", "C"]
    base = pd.DataFrame([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]], index=idx, columns=cols)
    panels = {"f1": base, "f2": base, "f3": base, "f4": base * np.nan}
    c = composite(panels)
    # f1,f2 rank A<B<C (+), f3 signed negative -> z sum = (z + z - z)/3 = z/3
    assert c.loc[idx[0], "C"] > c.loc[idx[0], "A"]
    panels2 = {"f1": base, "f2": base * np.nan, "f3": base * np.nan, "f4": base * np.nan}
    assert composite(panels2).isna().all().all()


def test_universe_mask_months():
    idx = pd.date_range("2024-01-30", "2024-02-02", tz="UTC")
    m = universe_mask({"2024-01-01": ["A"], "2024-02-01": ["B"]}, idx, ["A", "B"])
    assert m.loc["2024-01-31", "A"] and not m.loc["2024-01-31", "B"]
    assert m.loc["2024-02-01", "B"] and not m.loc["2024-02-01", "A"]


def test_residualize_removes_linear_control():
    idx = pd.date_range("2024-01-01", periods=1, tz="UTC")
    cols = [f"s{i}" for i in range(25)]
    x = np.arange(25, dtype=float)
    ctrl = pd.DataFrame([x], index=idx, columns=cols)
    sig = pd.DataFrame([2 * x + 1], index=idx, columns=cols)
    r = residualize(sig, [ctrl])
    assert np.allclose(r.iloc[0].to_numpy(), 0.0, atol=1e-9)
