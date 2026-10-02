"""Bounded replay of the unchanged compact event format through explicit reads.

Caller supplies trusted terminal/owner/scope and bounded archive-aware chunk
reads. This verifies event bytes/order/scores/checkpoint references, not actual
checkpoint trees, score batches, source graphs or current-owner admission.
No old local reader, writer, receipt or disposal policy is changed.
"""
import hashlib
import json
import struct

from . import compact_pair_log as events

io = events.io
require = io._require
SCORE = struct.Struct('<Qd32s')
CHECKPOINT = struct.Struct('<Q32s')


def _metadata(raw):
    require(type(raw) is bytes and len(raw) <= io.META_LIMIT, 'bounded immutable event metadata')
    result = json.loads(raw)
    require(isinstance(result, dict) and io._json(result) == raw, 'canonical event metadata')
    return result


def verify(*, start_bytes, terminal_bytes, terminal_sha256, owner, scope, read_chunk, lease):
    """Stream every full/partial chunk and preserve pair event semantics."""
    io._identity(owner); io._identity(terminal_sha256); scope = events._scope(scope)
    require(callable(read_chunk) and callable(lease), 'bounded archive reader and live lease required')
    lease()
    terminal = _metadata(terminal_bytes)
    require(io._hash(terminal_bytes) == terminal_sha256, 'archive event terminal hash differs')
    require(set(terminal) == {'schema_version', 'start_sha256', 'status', 'reason', 'state',
        'head', 'chunks', 'record_bytes', 'payload_sha256'} and type(terminal['schema_version']) is int
        and terminal['schema_version'] == 1 and terminal['status'] == 'complete',
        'complete archive event terminal required')
    start = _metadata(start_bytes); start_sha = io._hash(start_bytes)
    require(terminal['start_sha256'] == start_sha, 'archive event start hash differs')
    require(set(start) == {'schema_version', 'owner', 'scope', 'limits', 'max_iterations', 'record_bytes', 'format'}
        and type(start['schema_version']) is int and start['schema_version'] == 1
        and start['owner'] == owner and start['scope'] == scope
        and type(start['record_bytes']) is int and start['record_bytes'] == events.RECORD_BYTES
        and start['format'] == '<QB7xQdQ32s32s32s32s', 'archive event scope/format differs')
    limits = events._limits(start['limits']); maximum = start['max_iterations']
    require(type(maximum) is int and 0 < maximum < 2**63, 'archive event iteration bound')
    expected = terminal['state']
    require(isinstance(expected, dict) and set(expected) == set(events._empty())
        and all(type(expected[k]) is int and 0 <= expected[k] < 2**63 for k in set(expected)-{'pending'})
        and expected['pending'] is None, 'archive event terminal state schema')
    count = expected['events']; chunks = terminal['chunks']; size = terminal['record_bytes']
    require(count <= limits['max_events'] and expected['started_pairs'] == expected['completed_pairs']
        <= limits['max_pairs'] and count == 2*expected['completed_pairs'] + expected['progress_events']
        and type(chunks) is int and chunks == (count+limits['chunk_events']-1)//limits['chunk_events']
        and type(size) is int and size == count*events.RECORD_BYTES, 'archive event denominator differs')
    require(isinstance(terminal['reason'], str) and len(terminal['reason'].encode()) <= 1024,
        'bounded archive event terminal reason')
    io._identity(terminal['head']); io._identity(terminal['payload_sha256'])
    state = events._empty(); head = start_sha; total = 0
    digest = hashlib.sha256(); scores = hashlib.sha256(); references = hashlib.sha256()
    for index in range(chunks):
        extent = min(limits['chunk_events']*events.RECORD_BYTES, size-total)
        lease()
        raw = read_chunk(index, extent)
        lease()
        require(type(raw) is bytes and len(raw) == extent, 'archive event chunk extent/type differs')
        digest.update(raw); total += len(raw)
        for offset in range(0, len(raw), events.RECORD_BYTES):
            record = raw[offset:offset+events.RECORD_BYTES]; body = record[:-32]
            head = io._hash(bytes.fromhex(head)+body)
            require(record[-32:] == bytes.fromhex(head), 'archive event checksum differs')
            state = events._advance(state, body, limits, maximum)
            frame = events.FRAME.unpack(body)
            if frame[1] in (1, 2): scores.update(SCORE.pack(frame[2], frame[3], frame[5]))
            elif frame[1] == 3: references.update(CHECKPOINT.pack(frame[0], frame[7]))
        del raw  # Release this full chunk before the next archive read allocates.
    require(state == expected and head == terminal['head'] and total == size
        and digest.hexdigest() == terminal['payload_sha256'], 'archive event terminal replay differs')
    lease()
    return {**state, 'status': 'complete', 'record_bytes': total, 'chunks': chunks,
        'unacknowledged_bytes': 0, 'matching_scores_sha256': scores.hexdigest(),
        'checkpoint_references_sha256': references.hexdigest()}
