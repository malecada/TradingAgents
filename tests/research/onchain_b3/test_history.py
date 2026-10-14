import math

import numpy as np
import pytest

from tradingagents.research.onchain_b3 import history as H


def test_keys_from_addresses():
    a = np.array([b'0x0123456789abcdef0000000000000000000000ff', b'0xffffffffffffffff000000000000000000000000',
                  b'0x0123456789abcdef1111111111111111111111ff'], dtype='S42')
    k = H.keys_from_addresses(a)
    assert k.dtype == np.uint64 and k.tolist() == [0x0123456789ABCDEF, 0xFFFFFFFFFFFFFFFF]


def test_bloom_no_false_negatives_and_low_false_positive_rate():
    rng = np.random.default_rng(0)
    seen = np.unique(rng.integers(0, 2**63, 10000, dtype=np.uint64))
    other = np.setdiff1d(np.unique(rng.integers(0, 2**63, 10000, dtype=np.uint64)), seen)
    b = H.Bloom(20, 5)
    b.add(seen)
    assert b.contains(seen).all()
    assert b.contains(other).mean() < 0.01


def _seq(**weeks):
    return {w: np.array(sorted(v), dtype=np.uint64) if v is not None else None for w, v in weeks.items()}


def test_history_shares():
    keys = _seq(w0=[1, 2, 3], w1=[2, 3, 4, 5], w2=[1, 6], w3=[6], w4=[7], w5=[8], w6=[1, 9])
    out = H.history_pass(list(keys), keys.get, 20, 5)
    assert out['w0']['f4_new_share'] == 1.0 and out['w0']['f4_prev1_share'] == 0.0
    assert out['w1'] == {'f4_new_share': 0.5, 'f4_prev1_share': 0.5, 'f4_prev4_share': 0.5, 'f4_return_share': 0.0}
    assert out['w2']['f4_new_share'] == 0.5 and out['w2']['f4_prev1_share'] == 0.0 and out['w2']['f4_prev4_share'] == 0.5
    # w6 = {1, 9}; previous four weeks w2..w5 = {1, 6, 7, 8}: 1 is in the window (not returning), 9 is new
    assert out['w6'] == {'f4_new_share': 0.5, 'f4_prev1_share': 0.0, 'f4_prev4_share': 0.5, 'f4_return_share': 0.0}


def test_missing_week_poisons_window_not_bloom():
    keys = _seq(w0=[1, 2], w1=None, w2=[1, 3], w3=[3], w4=[3], w5=[3], w6=[2])
    out = H.history_pass(list(keys), keys.get, 20, 5)
    assert out['w1'] is None
    assert math.isnan(out['w2']['f4_prev1_share']) and math.isnan(out['w2']['f4_prev4_share'])
    assert math.isnan(out['w5']['f4_prev4_share']) and not math.isnan(out['w6']['f4_prev4_share'])
    assert out['w2']['f4_new_share'] == 0.5 and out['w6']['f4_new_share'] == 0.0     # 2 was seen in w0
    assert out['w6']['f4_return_share'] == 1.0