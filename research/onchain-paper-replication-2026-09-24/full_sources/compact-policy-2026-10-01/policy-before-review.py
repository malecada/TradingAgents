"""Prospective compact persistence contract; validation is NOT run admission.

The old native producer does not select this backend. A compact owner, publication
reader and terminal seal must bind this policy before empirical execution. Bounds
here cover retained logical evidence only, excluding filesystem allocation,
graphs, numerical matrices, scratch, guard logs and preceding attempts.
"""
from .cache import cache_key
from . import matching_pair as pair, score_batches as io, compact_pair_log as log

BACKEND = 'resident-native-compact-current-owner-v1'
require = io._require
SCHEDULE_FIELDS = {'operations_per_call', 'calls_per_checkpoint', 'max_checkpoints',
                   'max_total_checkpoints', 'max_total_checkpoint_bytes'}


def positive(values):
    require(all(type(v) is int and 0 < v < 2**63 for v in values), 'positive bounded integer required')


def dictionary_capacity(*, sample_count, size, partition_threshold, partition_size):
    """Conservative directional pair/matrix counts; identical matrix reuse may reduce them."""
    positive((sample_count, size, partition_threshold, partition_size))
    require(sample_count >= size and partition_threshold >= size and partition_size > size,
            'dictionary partition must reduce samples')
    n = sample_count; pairs = entries = levels = 0
    while n > partition_threshold:
        count, remainder = divmod(n, partition_size)
        pairs += count * partition_size * (partition_size - 1) + remainder * (remainder - 1)
        entries += count * partition_size**2 + remainder**2
        reduced = count * size + min(size, remainder)
        require(reduced < n, 'dictionary partition fails to reduce samples')
        n = reduced; levels += 1
    pairs += n * (n - 1); entries += n * n; levels += 1
    require(pairs < 2**63 and entries < 2**63, 'dictionary capacity overflow')
    return {'max_pairs': pairs, 'max_matrix_entries': entries, 'levels': levels}


def validate(value, *, kind, pairs):
    """Validate one fresh dictionary/MCM stage, never silently supply defaults.

    A stage can still exhaust its checkpoint schedule and stop. Global checkpoint
    byte reservations cover every permitted snapshot, with two bounded metadata
    records each. No progress budget is inferred from optimistic convergence.
    """
    require(type(value) is dict and set(value) == {'schema_version', 'backend', 'pair',
        'schedule', 'log', 'score_chunk_cells', 'max_retained_logical_bytes'}, 'compact policy schema')
    require(type(value['schema_version']) is int and value['schema_version'] == 1
        and value['backend'] == BACKEND, 'explicit compact persistence backend required')
    require(kind in ('dictionary', 'mcm'), 'compact workload kind')
    require(type(pairs) is int and 0 <= pairs < 2**63 and (kind == 'dictionary' or pairs > 0),
            'bounded pair occurrence count')
    p = value['pair']; s = value['schedule']
    require(type(p) is dict and set(p) == pair.POLICY_FIELDS, 'compact pair policy schema')
    require(type(s) is dict and set(s) == SCHEDULE_FIELDS, 'compact schedule schema')
    positive(p.values()); positive(s.values())
    positive((value['score_chunk_cells'], value['max_retained_logical_bytes']))
    limits = log._limits(value['log'])
    require(p['chunk_edges'] <= 65536, 'bounded scoring edge chunk required')
    require(s['max_checkpoints'] <= p['max_publications']
        and pair.LIMIT + s['max_checkpoints'] * (p['max_checkpoint_bytes'] + pair.LIMIT)
            <= p['total_checkpoint_bytes'], 'per-pair checkpoint reservation insufficient')
    require(s['max_total_checkpoints'] >= s['max_checkpoints']
        and s['max_total_checkpoint_bytes'] >= s['max_total_checkpoints']
            * (p['max_checkpoint_bytes'] + 2 * io.META_LIMIT), 'global checkpoint reservation insufficient')
    require(limits['max_pairs'] >= pairs and limits['max_events'] >= 2 * pairs + s['max_total_checkpoints'],
            'compact occurrence/event reservation insufficient')
    # Both the float64 batch and the larger retained purpose-bearing tail must fit.
    require(value['score_chunk_cells'] * 80 <= io.MAX_CHUNK_BYTES, 'bounded retained score chunk required')
    chunks = (pairs + value['score_chunk_cells'] - 1) // value['score_chunk_cells'] if kind == 'mcm' else 0
    score_bytes = 88 * pairs + (4 * chunks + 4) * io.META_LIMIT if kind == 'mcm' else 0
    total = limits['max_logical_bytes'] + s['max_total_checkpoint_bytes'] + score_bytes
    require(total <= value['max_retained_logical_bytes'] < 2**63, 'retained logical evidence reservation insufficient')
    return {'backend': BACKEND, 'policy_sha256': cache_key(value), 'kind': kind,
        'pair_occurrences': pairs, 'score_chunks': chunks, 'score_bytes': score_bytes,
        'logical_reservation_bytes': total, 'execution_admitted': False}
