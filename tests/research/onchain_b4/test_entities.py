# tests/research/onchain_b4/test_entities.py
import numpy as np

from tradingagents.research.onchain_b4.entities import Entities, member

u = lambda *x: np.array(x, np.uint64)
L = 100


def _ent():
    return Entities(u(L), 16, 5, 0.9)


def test_first_send_to_label_becomes_deposit_next_day():
    e = _ent()
    # X=1 first sends to L; Y=2 first sends to 3, later (block 9) to L; L itself sends to 4
    e.update(u(1, 2, 2, L), u(L, 3, L, 4), np.array([5, 5, 9, 5]), '2017-01-01')
    assert e.deposits.tolist() == [1] and e.c_keys.tolist() == [1]
    assert e.is_exchange(u(1, 2, L, 4)).tolist() == [True, False, True, False]
    assert e.is_labelled(u(1, L)).tolist() == [False, True]


def test_seen_sender_never_joins_and_share_drop_leaves():
    e = _ent()
    e.update(u(1, 4), u(L, 3), np.array([1, 1]), '2017-01-01')      # 4 seen as a sender
    e.update(u(4, 1, 1), u(L, 3, 3), np.array([2, 2, 3]), '2017-01-02')
    assert 4 not in e.c_keys.tolist()                                 # previously seen sender
    assert e.c_out.tolist() == [3] and e.c_lab.tolist() == [1] and e.deposits.tolist() == []


def test_update_with_no_transfers():
    e = _ent()
    e.update(u(), u(), np.array([], np.int64), '2017-01-01')
    assert e.deposits.size == 0 and e.last_day == '2017-01-01'


def test_snapshot_round_trip(tmp_path):
    e = _ent()
    e.update(u(1, 5), u(L, L), np.array([1, 1]), '2017-01-01')
    e.save(tmp_path / 'state' / 'entities.npz')
    f = Entities.load(tmp_path / 'state' / 'entities.npz')
    assert f.last_day == '2017-01-01' and f.deposits.tolist() == [1, 5] and np.array_equal(f.bloom.bits, e.bloom.bits)
    for x in (e, f):
        x.update(u(6, 1), u(L, 7), np.array([1, 1]), '2017-01-02')
    assert np.array_equal(e.c_keys, f.c_keys) and np.array_equal(e.deposits, f.deposits)
    assert member(u(1, 6, 9), u(9)).tolist() == [True]
