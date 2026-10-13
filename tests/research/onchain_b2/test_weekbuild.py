import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import admitted_events, aggregate_pairs
from tradingagents.research.onchain_b2 import weekbuild as WB

A, B, C, D, E1, E2 = ('0x' + c * 40 for c in 'abcdef')
EX = pa.array(sorted([E1, E2]))
ROWS = [(A, E1, 9.0, 1), (A, C, 1.0, 1), (B, E1, 8.9, 1), (B, C, 1.1, 1), (C, A, 5.0, 1),
        (E1, D, 4.0, 1), (E1, E2, 100.0, 1), (D, D, 2.0, 1), (A, B, 3.0, 0), (B, A, 0.0, 1)]


def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [r[3] for r in rows]})


def _week():
    ev, c = admitted_events(_day(ROWS))
    pairs = aggregate_pairs([ev])
    return ev, pairs, WB.address_table(pairs), [c]


def test_f1_activity():
    ev, pairs, addr, counters = _week()
    f = WB.f1_features(ev, pairs, addr, counters, top_n=2)
    assert f['f1_transfers'] == 8 and f['f1_failed_share'] == pytest.approx(0.1) and f['f1_zero_share'] == pytest.approx(0.1)
    assert f['f1_null_share'] == 0 and f['f1_active'] == 6 and f['f1_senders'] == 5 and f['f1_receivers'] == 5
    assert f['f1_eth_moved'] == pytest.approx(131.0) and f['f1_median_size'] == pytest.approx(4.5)
    assert f['f1_p90_size'] == pytest.approx(36.3) and f['f1_self_share'] == pytest.approx(1 / 8)
    assert f['f1_top_share'] == pytest.approx(221.9 / 262) and f['f1_edges'] == 8 and f['f1_mean_degree'] == pytest.approx(8 / 6)


def test_role_flows_deposit_boundary_and_whales():
    ev, pairs, addr, _ = _week()
    f, whales = WB.role_flows(pairs, addr, EX, deposit_share=0.9, n_whales=2)
    assert f['f3a_ex_in_value'] == pytest.approx(17.9) and f['f3a_ex_in_count'] == 2
    assert f['f3a_ex_out_value'] == pytest.approx(4.0) and f['f3a_ex_out_count'] == 1
    assert f['f3a_ex_net_value'] == pytest.approx(13.9)
    assert f['f3a_dep_count'] == 1                          # A sends exactly 90 % to E (inclusive); B sends 89 %
    assert f['f3a_dep_received_value'] == pytest.approx(5.0)  # C -> A
    assert f['f3a_ex_senders'] == 2                         # B -> E1, C -> A (A itself is deposit-like)
    assert whales == [A, B]
    assert f['f3a_whale_net_to_ex'] == pytest.approx(17.9) and f['f3a_whale_share'] == pytest.approx(25 / 262)


def test_receive_only_address_has_zero_out():
    _, _, addr, _ = _week()
    row = {r['address']: r for r in addr.to_pylist()}[E2]
    assert row['out_value'] == 0 and row['out_count'] == 0 and row['in_value'] == pytest.approx(100.0)


def test_role_flows_without_exchanges_are_zero():
    ev, pairs, addr, _ = _week()
    f, whales = WB.role_flows(pairs, addr, pa.array([], pa.string()), deposit_share=0.9, n_whales=2)
    assert all(isinstance(v, (int, float)) and v == v for v in f.values())
    assert f['f3a_ex_in_value'] == 0.0 and f['f3a_dep_count'] == 0 and f['f3a_whale_net_to_ex'] == 0.0
    assert whales == [E1, E2]                                # with no labels, every address is non-exchange


def test_whale_ties_break_by_address():
    rows = [(B, C, 5.0, 1), (A, C, 5.0, 1)]
    ev, _ = admitted_events(_day(rows))
    pairs = aggregate_pairs([ev])
    _, whales = WB.role_flows(pairs, WB.address_table(pairs), EX, 0.9, 2)
    assert whales == [C, A]                                  # C 10; A and B tie at 5 → A first


def test_build_week_summary_and_graph():
    summary, g = WB.build_week('2019-06-03', [_day(ROWS)], EX, {'k': 3, 'roles': {'deposit_share': 0.9, 'whales': 2, 'top_share_n': 2}})
    assert summary['week'] == '2019-06-03' and summary['f1']['f1_transfers'] == 8 and summary['whales'] == [A, B]
    assert g.n == 3 and summary['graph']['k_effective'] == 3 and summary['counters'][0]['rows'] == 10