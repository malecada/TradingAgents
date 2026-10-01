"""Prospective compact route policy checks; no registered run or outcomes."""
import copy
import subprocess
import sys
import pytest
from tests.research.onchain_replication.test_compact_matcher import POLICY, SCHEDULE


def candidate():
    return {'schema_version': 1, 'backend': 'resident-native-compact-current-owner-v1',
        'pair': dict(POLICY), 'schedule': dict(SCHEDULE),
        'log': {'chunk_events': 16, 'max_events': 200, 'max_pairs': 64, 'max_logical_bytes': 60000},
        'score_chunk_cells': 4, 'max_retained_logical_bytes': 10000000}


def test_directional_hierarchy_capacity_includes_every_partition_and_final_matrix():
    from tradingagents.research.onchain_replication.compact_policy import dictionary_capacity
    # Seven samples => partitions of 4 and 3 => four representatives => final4x4.
    assert dictionary_capacity(sample_count=7, size=2, partition_threshold=4, partition_size=4) == {
        'max_pairs': 30, 'max_matrix_entries': 41, 'levels': 2}
    assert dictionary_capacity(sample_count=2, size=2, partition_threshold=4, partition_size=4) == {
        'max_pairs': 2, 'max_matrix_entries': 4, 'levels': 1}
    with pytest.raises(ValueError):
        dictionary_capacity(sample_count=7, size=2, partition_threshold=2, partition_size=2)


def test_policy_binds_full_log_checkpoint_and_retained_tail_batch_allowances():
    from tradingagents.research.onchain_replication.compact_policy import validate
    p = candidate(); original = copy.deepcopy(p)
    d = validate(p, kind='dictionary', pairs=30)
    assert d['logical_reservation_bytes'] == 60000 + 6000000
    assert d['pair_occurrences'] == 30 and d['score_bytes'] == 0
    m = validate(p, kind='mcm', pairs=14)
    assert m['score_bytes'] == 88 * 14 + (4 * 4 + 4) * 8192
    assert m['logical_reservation_bytes'] == 6060000 + m['score_bytes']
    assert p == original
    assert d['policy_sha256'] == m['policy_sha256']


@pytest.mark.parametrize('change', ['backend', 'boolean', 'events', 'pairs', 'checkpoint', 'logical', 'chunk', 'unknown'])
def test_invalid_or_underreserved_policy_refused(change):
    from tradingagents.research.onchain_replication.compact_policy import validate
    p = candidate()
    if change == 'backend': p['backend'] = 'resident-native-current-owner-v1'
    if change == 'boolean': p['schedule']['calls_per_checkpoint'] = True
    if change == 'events': p['log']['max_events'] = 69  # Need2*30+10.
    if change == 'pairs': p['log']['max_pairs'] = 29
    if change == 'checkpoint': p['schedule']['max_total_checkpoint_bytes'] = 1
    if change == 'logical': p['max_retained_logical_bytes'] = 6059999
    if change == 'chunk': p['score_chunk_cells'] = 200000
    if change == 'unknown': p['silently_allow_resume'] = True
    with pytest.raises(ValueError): validate(p, kind='dictionary', pairs=30)


def test_pathological_hierarchy_is_refused_with_bounded_accounting_work():
    source = '''from tradingagents.research.onchain_replication.compact_policy import dictionary_capacity
for size in (2**40 - 1, 10**6):
    try:
        dictionary_capacity(sample_count=2*size+1, size=size, partition_threshold=size, partition_size=size+1)
    except ValueError:
        pass
    else:
        raise AssertionError('pathological accounting accepted')
'''
    # Timeout kills and waits for this fresh metadata-only child; no lingering worker.
    result = subprocess.run([sys.executable, '-B', '-c', source], capture_output=True, timeout=3)
    assert result.returncode == 0, result.stderr.decode()


def test_mcm_chunk_filename_capacity_refused_even_with_sufficient_logical_budget():
    from tradingagents.research.onchain_replication.compact_policy import validate
    p = candidate(); pairs = 10**12 + 1
    p['score_chunk_cells'] = 1
    p['log'].update(chunk_events=10000, max_pairs=pairs, max_events=2*pairs+10,
        max_logical_bytes=(2*pairs+10)*168+16384)
    p['max_retained_logical_bytes'] = 10**18
    with pytest.raises(ValueError, match='chunk'): validate(p, kind='mcm', pairs=pairs)


def test_single_sample_dictionary_has_zero_pairs_but_retains_explicit_stage_reservations():
    from tradingagents.research.onchain_replication.compact_policy import dictionary_capacity, validate
    assert dictionary_capacity(sample_count=1, size=1, partition_threshold=1, partition_size=2) == {
        'max_pairs': 0, 'max_matrix_entries': 1, 'levels': 1}
    assert validate(candidate(), kind='dictionary', pairs=0)['pair_occurrences'] == 0
    with pytest.raises(ValueError): validate(candidate(), kind='mcm', pairs=0)
