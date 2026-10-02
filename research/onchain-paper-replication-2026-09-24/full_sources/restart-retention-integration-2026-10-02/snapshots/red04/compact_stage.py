"""Join completed compact matching, retained checkpoints and MCM score evidence.

This publishes an exclusive stage receipt, not ResearchRun or representation
admission. Trusted owner/scope/terminal references and an exclusive frozen stage
come from the caller. Full content reads occur at sealing/verification boundaries,
with bounded chunks and one checkpoint at a time, never per numerical pair.
Checks are sampled, not an atomic filesystem snapshot. Failures retain all bytes.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct

from . import compact_pair_log as events, compact_matcher as matcher, compact_policy
from . import score_batches as io, score_tail as tail
from .cache import cache_key

require = io._require
SCORE = struct.Struct('<Qd32s')


def read(root, name, expected=None):
    path, fd = io._open(root)
    try:
        raw = io._read(fd, name, io.META_LIMIT); io._root(path, fd)
        if expected is not None: require(io._hash(raw) == expected, 'stage metadata hash differs')
        return json.loads(raw), io._hash(raw)
    finally: io._release(lambda: os.close(fd))


def inventory(root, fixed, pattern=None, count=0):
    path, fd = io._open(root)
    try:
        seen = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                seen += 1
                match = re.fullmatch(pattern, entry.name) if pattern else None
                require(seen <= len(fixed) + count and (entry.name in fixed
                    or (match is not None and int(match[1]) < count)), 'unexpected stage inventory')
        require(seen == len(fixed) + count, 'incomplete stage inventory')
        io._root(path, fd)
    finally: io._release(lambda: os.close(fd))


def checkpoint(root, frame, *, start_sha, policy, ordinal):
    event, _, pair_index, _, _, purpose_sha, identity_sha, artifact = frame
    directory = root / f'event-{event:012d}'
    meta, ref = read(directory, 'manifest.json', artifact.hex())
    require(set(meta) == {'schema_version', 'intent_sha256', 'state_sha256',
        'state_logical_bytes', 'reserved_bytes'} and type(meta['schema_version']) is int
        and meta['schema_version'] == 1, 'checkpoint wrapper schema')
    intent, _ = read(directory, 'intent.json', meta['intent_sha256'])
    reserved = policy['pair']['max_checkpoint_bytes'] + 2 * io.META_LIMIT
    require(set(intent) == {'schema_version', 'log_start_sha256', 'event', 'pair', 'identity',
        'purpose', 'policy', 'reserved_bytes', 'cumulative_reserved_bytes', 'cumulative_checkpoints'}
        and type(intent['schema_version']) is int and intent['schema_version'] == 1
        and intent['log_start_sha256'] == start_sha and intent['event'] == event
        and intent['pair'] == {'ordinal': pair_index, 'purpose_sha256': purpose_sha.hex(),
            'identity_sha256': identity_sha.hex()}
        and matcher.pair.digest(intent['identity']) == identity_sha.hex()
        and cache_key(intent['purpose']) == purpose_sha.hex() and intent['policy'] == policy['pair']
        and intent['reserved_bytes'] == meta['reserved_bytes'] == reserved
        and intent['cumulative_reserved_bytes'] == ordinal * reserved
        and intent['cumulative_checkpoints'] == ordinal, 'checkpoint intent binding differs')
    logical = matcher._snapshot(directory / 'state', meta['state_sha256'], intent['identity'], policy['pair'])
    require(type(meta['state_logical_bytes']) is int and logical == meta['state_logical_bytes'],
            'checkpoint state byte count differs')
    inventory(directory, {'intent.json', 'manifest.json', 'state'})
    return ref, logical


def matching(root, *, owner, scope, terminal, policy, pairs):
    record = events.verify(root / 'matching', owner=owner, scope=scope,
        terminal_sha256=terminal, lease=lambda: None)
    require(record['status'] == 'complete' and record['pending'] is None
        and record['completed_pairs'] == record['started_pairs'] == pairs
        and record['unacknowledged_bytes'] == 0, 'stage matching denominator/status differs')
    start, start_sha = read(root / 'matching', 'start.json')
    require(start['limits'] == policy['log'] and scope['policy'] == cache_key({
        'pair': policy['pair'], 'schedule': policy['schedule']}), 'stage matching policy differs')
    scores = hashlib.sha256(); checkpoints = hashlib.sha256(); seen = logical = 0
    path, fd = io._open(root / 'matching')
    try:
        head = start_sha; state = events._empty(); per_pair = 0
        for index in range(record['chunks']):
            raw = io._read(fd, events._name(index), policy['log']['chunk_events'] * events.RECORD_BYTES)
            for offset in range(0, len(raw), events.RECORD_BYTES):
                body = raw[offset:offset + events.FRAME.size]
                head = io._hash(bytes.fromhex(head) + body)
                require(raw[offset + events.FRAME.size:offset + events.RECORD_BYTES] == bytes.fromhex(head),
                        'stage event changed during join')
                state = events._advance(state, body, policy['log'], start['max_iterations'])
                frame = events.FRAME.unpack(body)
                if frame[1] == 0: per_pair = 0
                elif frame[1] in (1, 2): scores.update(SCORE.pack(frame[2], frame[3], frame[5]))
                else:
                    seen += 1; per_pair += 1
                    require(per_pair <= policy['schedule']['max_checkpoints']
                        and seen <= policy['schedule']['max_total_checkpoints'], 'checkpoint count exceeds policy')
                    ref, size = checkpoint(root / 'checkpoints', frame, start_sha=start_sha,
                        policy=policy, ordinal=seen)
                    checkpoints.update(struct.pack('<Q', frame[0]) + bytes.fromhex(ref)); logical += size
        terminal_record, _ = read(root / 'matching', 'terminal.json', terminal)
        require(state == terminal_record['state'] and head == terminal_record['head']
            and seen == record['progress_events'], 'matching join terminal differs')
        io._root(path, fd)
    finally: os.close(fd)
    # Event numbers are sparse; every actual directory must refer to one seen
    # progress event. Count plus exact verification above rejects extra entries.
    path, fd = io._open(root / 'checkpoints')
    try:
        count = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                count += 1
                require(count <= seen and re.fullmatch(r'event-[0-9]{12}', entry.name), 'extra checkpoint inventory')
        require(count == seen, 'checkpoint inventory denominator differs'); io._root(path, fd)
    finally: os.close(fd)
    return dict(log_start_sha256=start_sha, matching_scores_sha256=scores.hexdigest(),
        checkpoints=seen, checkpoint_logical_bytes=logical, checkpoints_sha256=checkpoints.hexdigest())


def stream(root, *, owner, scope, terminal, policy, pairs):
    complete, _ = read(root, 'complete.json', terminal)
    require(set(complete) == {'schema_version', 'start_sha256', 'head', 'cells', 'chunks',
        'batch_terminal_sha256'} and type(complete['schema_version']) is int
        and complete['schema_version'] == 1, 'stream terminal schema')
    start, start_sha = read(root, 'start.json', complete['start_sha256'])
    require(set(start) == {'schema_version', 'kind', 'scope', 'owner', 'rows', 'motifs',
        'batch_start_sha256', 'chunk_cells'} and type(start['schema_version']) is int
        and start['schema_version'] == 1 and start['kind'] == 'mcm-score-stream'
        and start['owner'] == owner and start['scope']['workflow'] == scope['workflow']
        and start['chunk_cells'] == policy['score_chunk_cells'], 'stream binding differs')
    stream_scope = io._scope(start['scope'])
    require(io._shape(start['rows'], start['motifs'], start['chunk_cells']) == pairs
        and complete['cells'] == pairs, 'stream cell denominator differs')
    chunks = (pairs + start['chunk_cells'] - 1) // start['chunk_cells']
    require(type(complete['chunks']) is int and complete['chunks'] == chunks, 'stream chunk denominator differs')
    batch_start, _ = read(root / 'batches', 'start.json', start['batch_start_sha256'])
    require(batch_start == {'schema_version': 1, 'scope': stream_scope, 'owner': owner,
        'rows': start['rows'], 'motifs': start['motifs'], 'chunk_cells': start['chunk_cells'],
        'dtype': '<f8', 'order': 'row-major'}, 'stream batch start differs')
    result = io.verify(root / 'batches', scope=stream_scope, owner=owner,
        terminal_sha256=complete['batch_terminal_sha256'], lease=lambda: None)
    require(result['status'] == 'complete' and result['cells'] == pairs and result['chunks'] == chunks,
            'stream batch completion differs')
    previous = start_sha; scores = hashlib.sha256()
    for index in range(chunks):
        link, ref = read(root, f'seal-{index:012d}.json')
        offset = index * start['chunk_cells']; count = min(start['chunk_cells'], pairs - offset)
        require(set(link) == {'schema_version', 'start_sha256', 'previous', 'index', 'start_cell',
            'cells', 'tail_terminal_sha256', 'batch_header_sha256'} and type(link['schema_version']) is int
            and link['schema_version'] == 1 and link['start_sha256'] == start_sha
            and link['previous'] == previous and link['index'] == index
            and link['start_cell'] == offset and link['cells'] == count, 'stream seal link differs')
        saved = tail.verify(root / 'tails' / f'tail-{index:012d}', scope=stream_scope,
            owner=owner, terminal_sha256=link['tail_terminal_sha256'], lease=lambda: None)
        destination = io._hash(io._json({'directory': str(root / 'batches'),
            'start_sha256': start['batch_start_sha256'], 'index': index, 'start_cell': offset, 'cells': count}))
        require(saved['status'] == 'complete' and saved['start_cell'] == offset and saved['cells'] == count
            and saved['acknowledged_cells'] == count and saved['pending_bytes'] == 0
            and saved['destination'] == destination, 'retained tail destination/denominator differs')
        read(root / 'batches', f'chunk-{index:012d}.json', link['batch_header_sha256'])
        path, fd = io._open(root / 'batches')
        try:
            require(io._read(fd, f'chunk-{index:012d}.bin', count * 8) == saved['values'].tobytes(),
                    'retained tail and score batch differ'); io._root(path, fd)
        finally: io._release(lambda: os.close(fd))
        for cell in range(count):
            scores.update(SCORE.pack(offset + cell, float(saved['values'][cell]), bytes(saved['purpose_hashes'][cell])))
        previous = ref
    require(previous == complete['head'], 'stream terminal chain differs')
    inventory(root, {'start.json', 'complete.json', 'batches', 'tails'}, r'seal-([0-9]{12})\.json', chunks)
    inventory(root / 'tails', set(), r'tail-([0-9]{12})', chunks)
    return scores.hexdigest(), start_sha


def inspect(root, *, owner, scope, policy, kind, pairs, log_terminal_sha256, stream_terminal_sha256):
    """Callback-free content join; caller must supply externally trusted identities."""
    root = Path(root); io._identity(owner); scope = events._scope(scope)
    capacity = compact_policy.validate(policy, kind=kind, pairs=pairs)
    require((kind == 'mcm') == (stream_terminal_sha256 is not None), 'stage stream kind differs')
    joined = matching(root, owner=owner, scope=scope, terminal=log_terminal_sha256, policy=policy, pairs=pairs)
    stream_start = None
    if kind == 'mcm':
        scores, stream_start = stream(root / 'stream', owner=owner, scope=scope,
            terminal=stream_terminal_sha256, policy=policy, pairs=pairs)
        require(scores == joined['matching_scores_sha256'], 'matching and retained score purposes/values differ')
    return {'schema_version': 1, 'kind': kind, 'owner': owner, 'scope': scope,
        'policy_sha256': capacity['policy_sha256'], 'completed_pairs': pairs,
        'log_terminal_sha256': log_terminal_sha256, 'stream_terminal_sha256': stream_terminal_sha256,
        'stream_start_sha256': stream_start, **joined, 'execution_admitted': False}


def seal(root, *, lease, **contract):
    """Exclusive receipt; existing/failed seal bytes must never be overwritten."""
    require(callable(lease), 'live stage owner lease required'); lease()
    root, fd = io._open(root)
    try:
        require(not (root / 'stage-complete.json').exists(), 'stage seal already claimed')
        value = inspect(root, **contract); raw = io._json(value)
        lease(); require(inspect(root, **contract) == value, 'stage changed before seal')
        io._root(root, fd); ref = io._write(fd, 'stage-complete.json', raw)
        lease(); require(inspect(root, **contract) == value, 'stage changed during seal')
        require(io._read(fd, 'stage-complete.json', io.META_LIMIT) == raw, 'stage seal bytes changed')
        io._root(root, fd); return ref
    finally: os.close(fd)


def verify(root, *, expected_sha256, lease, **contract):
    require(callable(lease), 'live stage verification lease required'); io._identity(expected_sha256)
    lease(); root, fd = io._open(root)
    try:
        raw = io._read(fd, 'stage-complete.json', io.META_LIMIT)
        require(io._hash(raw) == expected_sha256, 'stage receipt hash differs')
        value = inspect(root, **contract); require(io._json(value) == raw, 'stage receipt content differs')
        lease(); require(inspect(root, **contract) == value, 'stage changed during verification')
        require(io._read(fd, 'stage-complete.json', io.META_LIMIT) == raw, 'stage receipt changed')
        io._root(root, fd); return value
    finally: os.close(fd)
