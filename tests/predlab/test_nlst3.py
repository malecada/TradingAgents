"""Unit tests for nlst3 smart-money / deployer-history features."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_nlst3_features import (  # noqa: E402
    flow_features, pool_buyers, serial_deployer, smart_money,
)


def E(pair, create, complete, ret7, **kw):
    return {"pair": pair, "create_ts": create, "complete_ts": complete,
            "ret7": ret7, **kw}


W_GOOD, W_BAD, DEP = "0xgood", "0xbad", "0xdep"
D = 86_400.0


def _history_entries():
    """4 completed pools: W_GOOD bought 3 winners, W_BAD bought 3 losers."""
    out = []
    for i in range(3):
        t = i * 10 * D
        out.append(E(f"win{i}", t, t + 8 * D, 2.0,
                     buyers={W_GOOD: 1.0, "0xother%d" % i: 1.0}))
        out.append(E(f"lose{i}", t + D, t + 9 * D, -0.9,
                     buyers={W_BAD: 1.0}))
    return out


def test_smart_money_pit_and_selection():
    entries = _history_entries()
    # target pool after all completions; W_GOOD and W_BAD both buy 1 ETH
    entries.append(E("target", 100 * D, 108 * D, 0.0,
                     buyers={W_GOOD: 1.0, W_BAD: 1.0}))
    g = smart_money(entries)
    # W_GOOD (record +2.0) is top-quintile among {W_GOOD, W_BAD}; W_BAD is not
    assert g.loc["target", "smart_money_volshare"] == pytest.approx(0.5)
    assert g.loc["target", "smart_money_breadth"] == 1.0


def test_smart_money_ignores_incomplete_priors():
    entries = _history_entries()
    # pool created BEFORE any prior completes -> no qualified wallets -> NaN
    entries.append(E("early", 2 * D, 10 * D, 0.0, buyers={W_GOOD: 1.0}))
    g = smart_money(entries)
    assert np.isnan(g.loc["early", "smart_money_volshare"])


def test_serial_deployer_pit_counts():
    entries = [
        E("p1", 0.0, 8 * D, 1.0, deployer=DEP),
        E("p2", 10 * D, 18 * D, -0.5, deployer=DEP),
        E("p3", 12 * D, 20 * D, 0.0, deployer=DEP),  # p2 not yet complete
    ]
    g = serial_deployer(entries)
    assert g.loc["p3", "serial_deployer_count"] == 2.0   # p1, p2 created
    assert g.loc["p3", "serial_deployer_perf"] == pytest.approx(1.0)  # only p1 done
    assert g.loc["p1", "serial_deployer_count"] == 0.0
    assert np.isnan(g.loc["p1", "serial_deployer_perf"])


def test_pool_buyers_sums_weth_in_by_recipient():
    def swap(weth_in, to):
        return {"topics": ["0xs", "0x" + "0" * 64, "0x" + "0" * 24 + to[2:]],
                "data": "0x" + hex(int(weth_in * 1e18))[2:].rjust(64, "0")
                        + "0" * 192}
    logs = [swap(1.0, "0x" + "a" * 40), swap(2.0, "0x" + "a" * 40),
            swap(5.0, "0x" + "b" * 40)]
    b = pool_buyers(logs, weth_is_0=True)
    assert b["0x" + "a" * 40] == pytest.approx(3.0)
    assert b["0x" + "b" * 40] == pytest.approx(5.0)


def test_flow_features_inflow_and_acceleration():
    def swap(block, w_in, w_out):
        return {"kind": "swap", "block": block,
                "a0in": int(w_in * 1e18), "a1in": 0,
                "a0out": int(w_out * 1e18), "a1out": 0}
    logs = [swap(10, 4.0, 0.0), swap(20, 2.0, 0.0),   # early
            swap(60, 0.0, 1.0), swap(70, 1.0, 0.0),
            swap(80, 0.0, 0.5), swap(90, 3.0, 0.0)]   # late
    f = flow_features(logs, weth_is_0=True, first_w=10.0, b12=50, b24=100)
    assert f["early_net_inflow"] == pytest.approx((10.0 - 1.5) / 10.0)
    assert f["buy_acceleration"] == pytest.approx(4 / 2)
