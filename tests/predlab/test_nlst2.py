"""Unit tests for nlst2 feature construction — required before first use."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from predlab_nlst2_features import (  # noqa: E402
    DEAD, SIGNS, ZERO, buyer_breadth, composite, deployer_of, lp_secured,
    sell_tax_proxy,
)
from predlab_nlst_lib import v2_sell  # noqa: E402


def T(frm, to, value, block=1):
    return {"block": block, "from": frm, "to": to, "value": value}


DEP = "0x" + "a" * 40
LOCKER = "0x663a5c229c09b049e36dcc11a9b0d4a8eb9db214"


def test_deployer_is_first_lp_mint_recipient_skipping_dust():
    transfers = [T(ZERO, DEAD, 1000), T(ZERO, DEP, 10**18), T(DEP, LOCKER, 5)]
    assert deployer_of(transfers) == DEP


def test_lp_secured_counts_burns_and_lockers_only():
    transfers = [
        T(ZERO, DEP, 100),          # mint
        T(DEP, LOCKER, 40),         # locked
        T(DEP, DEAD, 10),           # burned
        T(DEP, "0x" + "b" * 40, 20),  # sold/moved -> NOT secured
    ]
    assert lp_secured(transfers) == pytest.approx(0.5)


def test_lp_secured_nan_without_mint():
    assert np.isnan(lp_secured([T(DEP, DEAD, 10)]))


def test_sell_tax_proxy_zero_for_honest_token():
    rw, rt = 10 * 10**18, 1000 * 10**18
    tok_in = 50 * 10**18
    honest_out = v2_sell(tok_in, rw, rt)
    logs = [
        {"kind": "sync", "block": 1, "r0": rw, "r1": rt},
        {"kind": "swap", "block": 2, "a0in": 0, "a1in": tok_in,
         "a0out": int(honest_out), "a1out": 0},
    ]
    assert sell_tax_proxy(logs, weth_is_0=True) == pytest.approx(0.0, abs=1e-9)


def test_sell_tax_proxy_detects_20pct_tax():
    rw, rt = 10 * 10**18, 1000 * 10**18
    tok_in = 50 * 10**18
    taxed_out = 0.8 * v2_sell(tok_in, rw, rt)
    logs = [
        {"kind": "sync", "block": 1, "r0": rw, "r1": rt},
        {"kind": "swap", "block": 2, "a0in": 0, "a1in": tok_in,
         "a0out": int(taxed_out), "a1out": 0},
    ]
    assert sell_tax_proxy(logs, weth_is_0=True) == pytest.approx(0.2, abs=1e-6)


def test_buyer_breadth_counts_unique_buy_recipients():
    def swap(weth_in, to):
        return {"topics": ["0xswap", "0x" + "0" * 64, "0x" + "0" * 24 + to[2:]],
                "data": "0x" + hex(weth_in)[2:].rjust(64, "0")
                        + "0" * 64 + "0" * 64 + hex(10**18)[2:].rjust(64, "0")}
    logs = [swap(10**18, "0x" + "c" * 40), swap(10**18, "0x" + "c" * 40),
            swap(10**18, "0x" + "d" * 40), swap(0, "0x" + "e" * 40)]  # last = sell
    assert buyer_breadth(logs, weth_is_0=True) == 2.0


def test_composite_signs_and_min_features():
    n = 40
    rng = np.random.default_rng(1)
    df = pd.DataFrame({c: rng.normal(0, 1, n) for c in SIGNS})
    df["quarter"] = ["2021Q1"] * 20 + ["2021Q2"] * 20
    # pool 0: strongly legit on a + feature; pool 1: same value on a - feature
    df.loc[0, "lp_secured"] = 5.0
    df.loc[1, "deployer_supply_share"] = 5.0
    score = composite(df)
    assert score.loc[0] > score.drop([0, 1]).mean()
    assert score.loc[1] < score.drop([0, 1]).mean()
    # sparse row excluded
    df2 = df.copy()
    df2.loc[2, list(SIGNS)] = np.nan
    df2.loc[2, "lp_secured"] = 1.0
    assert np.isnan(composite(df2).loc[2])
