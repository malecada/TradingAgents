"""Tiny actual matcher/archive integration; no empirical or network admission."""
import hashlib
import json
import struct

import pytest

from tests.research.onchain_replication.test_archive_chunks import Transport
from tests.research.onchain_replication.test_compact_matcher import CONTEXT, POLICY, SCHEDULE
from tests.research.onchain_replication.test_matching_reference import graph, config
from tradingagents.research.onchain_replication import archive_pair_writer, compact_matcher
from tradingagents.research.onchain_replication import compact_pair_log as events, compact_stage
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.matching_reference import match_reference


def fixture(tmp_path, *, checkpoints=False):
    a = graph([[0.], [.3]], [(0, 1, .1)])
    b = graph([[.2], [.7]], [(1, 0, .4)])
    c = config() | {'beta_final': 1.}
    schedule = SCHEDULE if not checkpoints else SCHEDULE | {
        'operations_per_call': 10, 'calls_per_checkpoint': 1, 'max_checkpoints': 32,
        'max_total_checkpoints': 64, 'max_total_checkpoint_bytes': 30000000}
    policy = POLICY | {'total_checkpoint_bytes': 15000000, 'max_publications': 32}
    limits = {'chunk_events': 3, 'max_events': 100, 'max_pairs': 3,
        'max_logical_bytes': 100 * events.RECORD_BYTES + 2 * events.io.META_LIMIT}
    transport = Transport(tmp_path / 'remote')
    archive_policy = {'schema_version': 1, 'remote_prefix': 'fresh-matcher',
        'transport_identity': transport.identity, 'max_chunks': 34,
        'max_metadata_bytes': (7 * 34 + 8) * events.io.META_LIMIT,
        'local_free_floor_bytes': 10 * 1024**3}
    scope = compact_matcher.scope(c, CONTEXT, policy, 'f' * 64, schedule)
    log = archive_pair_writer.ArchivePairLog(tmp_path / 'matching', owner='d' * 64,
        scope=scope, limits=limits, max_iterations=c['max_iterations'], lease=lambda: None,
        transport=transport, archive_policy=archive_policy)
    try:
        matcher = compact_matcher.CompactMatcher(log, config=c, context=CONTEXT, policy=policy,
            workload_sha256='f' * 64, schedule=schedule, lease=lambda: None)
    except BaseException:
        log.close()
        raise
    purpose = {'schema_version': 1, 'kind': 'mcm', 'workload_sha256': 'f' * 64,
        'typed_graphs': [graph_identity(a), graph_identity(b)], 'center_index': 0, 'motif_index': 0}
    return matcher, log, transport, a, b, c, purpose, policy, schedule


@pytest.mark.parametrize('checkpoints', [False, True])
def test_actual_matching_scores_and_checkpoint_trees_survive_archive_rotation(tmp_path, checkpoints):
    matcher, log, transport, a, b, c, purpose, policy, schedule = fixture(tmp_path, checkpoints=checkpoints)
    expected = match_reference(a, b, c)
    scores = hashlib.sha256()
    try:
        for ordinal in range(2):
            current = purpose | {'center_index': ordinal}
            got = matcher(current, a, b)
            assert got == {'purpose_sha256': cache_key(current), 'score': expected.score}
            scores.update(struct.pack('<Qd32s', ordinal, expected.score, bytes.fromhex(cache_key(current))))
        reference = log.finish()
    finally:
        log.close()
    complete = json.loads((log.root / 'archive-complete.json').read_bytes())
    assert complete['terminal_sha256'] == reference
    assert complete['replay']['matching_scores_sha256'] == scores.hexdigest()
    assert complete['replay']['completed_pairs'] == 2
    assert not list(log.root.rglob('*.bin'))
    # Decode retained remote bytes directly, without trusting writer replay output.
    payloads = sorted(transport.root.glob('*/payload.bin'))
    assert len(payloads) >= 2
    if not checkpoints:
        assert [p.stat().st_size for p in payloads] == [3 * events.RECORD_BYTES, events.RECORD_BYTES]
    seen = 0
    references = hashlib.sha256()
    for payload in payloads:
        raw = payload.read_bytes()
        for offset in range(0, len(raw), events.RECORD_BYTES):
            frame = struct.unpack('<QB7xQdQ32s32s32s', raw[offset:offset + 136])
            if frame[1] != 3:
                continue
            seen += 1
            ref, size = compact_stage.checkpoint(tmp_path / 'checkpoints', frame,
                start_sha=log.start_sha, policy={'pair': policy}, ordinal=seen)
            assert size > 0
            references.update(struct.pack('<Q32s', frame[0], bytes.fromhex(ref)))
    assert (seen > 0) == checkpoints
    assert seen == complete['replay']['progress_events']
    assert references.hexdigest() == complete['replay']['checkpoint_references_sha256']
    assert len(list((tmp_path / 'checkpoints').iterdir())) == seen
