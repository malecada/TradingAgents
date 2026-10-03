"""Fixed-size ordered matcher events, retaining only one active pair in memory.

Begin precedes numerical allocation; completion records include convergence and
iterations. Progress binds a checkpoint manifest hash at a deterministic event
path. This log does not inspect checkpoint trees, admit owners, execute matching,
resume predecessors or delete files. Those duties remain with the caller.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import stat
import struct

from . import score_batches as io

FRAME = struct.Struct('<QB7xQdQ32s32s32s')
RECORD_BYTES = FRAME.size + 32
FIELDS = {'workflow', 'config', 'policy', 'context', 'numerical_source'}
ZERO = '0' * 64
require = io._require


def _scope(scope):
    require(isinstance(scope, dict) and set(scope) == FIELDS, 'compact log scope schema')
    for value in scope.values(): io._identity(value)
    return dict(scope)


def _limits(limits):
    require(isinstance(limits, dict) and set(limits) == {
        'chunk_events', 'max_events', 'max_pairs', 'max_logical_bytes'}, 'compact log policy schema')
    require(all(type(v) is int and 0 < v < 2**63 for v in limits.values()), 'positive bounded log limits')
    require(limits['chunk_events'] * RECORD_BYTES <= io.MAX_CHUNK_BYTES
        and limits['max_events'] * RECORD_BYTES + 2 * io.META_LIMIT <= limits['max_logical_bytes']
        and (limits['max_events'] + limits['chunk_events'] - 1) // limits['chunk_events'] <= 10**12,
        'compact log chunk/logical allowance')
    return dict(limits)


def _empty():
    return dict(events=0, started_pairs=0, completed_pairs=0, progress_events=0, pending=None)


def _advance(state, frame, limits, max_iterations):
    event, kind, ordinal, score, iterations, purpose, identity, artifact = FRAME.unpack(frame)
    purpose = purpose.hex(); identity = identity.hex(); artifact = artifact.hex()
    require(event == state['events'] and event < limits['max_events'], 'event order/capacity')
    pending = state['pending']; result = dict(state)
    if kind == 0:
        require(pending is None and ordinal == state['started_pairs'] < limits['max_pairs']
                and score == 0 and iterations == 0 and artifact == ZERO, 'begin order/fields/capacity')
        result['pending'] = {'ordinal': ordinal, 'purpose_sha256': purpose, 'identity_sha256': identity}
        result['started_pairs'] += 1
    else:
        require(pending == {'ordinal': ordinal, 'purpose_sha256': purpose, 'identity_sha256': identity},
                'event differs from pending pair')
        if kind in (1, 2):
            require(math.isfinite(score) and 0 <= score <= 1 and iterations <= max_iterations
                    and artifact == ZERO, 'completion values differ')
            result['pending'] = None; result['completed_pairs'] += 1
        else:
            require(kind == 3 and score == 0 and iterations == 0 and artifact != ZERO,
                    'progress fields differ')
            result['progress_events'] += 1
    result['events'] += 1
    return result


def _name(index): return f'events-{index:012d}.bin'


class PairLog:
    def __init__(self, root, *, owner, scope, limits, max_iterations, lease):
        io._identity(owner); scope = _scope(scope); limits = _limits(limits)
        require(type(max_iterations) is int and 0 < max_iterations < 2**63 and callable(lease),
                'iteration bound and live lease required')
        root = Path(root)
        require(root.is_absolute() and root.resolve() == root, 'canonical compact log root')
        self.start = {'schema_version': 1, 'owner': owner, 'scope': scope, 'limits': limits,
            'max_iterations': max_iterations, 'record_bytes': RECORD_BYTES, 'format': '<QB7xQdQ32s32s32s32s'}
        self.state = _empty(); self.chunks = 0; self.chunk_fd = None
        self.closed = self.poisoned = False; self.lease = lease
        lease(); root.mkdir()
        parent, fd = io._open(root.parent)
        try: os.fsync(fd); io._root(parent, fd)
        finally:
            primary = sys.exception()
            if primary is not None: io._close_after_failure(lambda: os.close(fd), primary)
            else: io._cleanup((lambda: os.close(fd),))
        self.root, self.fd = io._open(root)
        try:
            self.head = self.start_sha = io._write(self.fd, 'start.json', io._json(self.start))
            self._check()
            require(io._hash(io._read(self.fd, 'start.json', io.META_LIMIT)) == self.start_sha,
                    'compact log start changed')
        except BaseException as primary:
            io._close_after_failure(self.close, primary)
            raise

    @property
    def events(self): return self.state['events']

    def checkpoint_path(self):
        """A progress event binds this path; creation/verification is external."""
        return self.root.parent / 'checkpoints' / f'event-{self.events:012d}'

    def _check(self, *, failing=False):
        require(not self.closed and (failing or not self.poisoned), 'compact log terminal or poisoned')
        self.lease(); io._root(self.root, self.fd)

    def _append(self, kind, score=0., iterations=0, artifact=ZERO, purpose=None, identity=None):
        self._check()
        pending = self.state['pending']
        if kind == 0:
            ordinal = self.state['started_pairs']
            io._identity(purpose); io._identity(identity)
        else:
            require(pending is not None, 'no pending pair')
            ordinal = pending['ordinal']; purpose = pending['purpose_sha256']; identity = pending['identity_sha256']
        io._identity(artifact)
        require(type(score) in (int, float) and math.isfinite(score)
                and type(iterations) is int and 0 <= iterations < 2**63, 'finite score/integer iterations')
        frame = FRAME.pack(self.events, kind, ordinal, score, iterations, bytes.fromhex(purpose),
                           bytes.fromhex(identity), bytes.fromhex(artifact))
        state = _advance(self.state, frame, self.start['limits'], self.start['max_iterations'])
        head = io._hash(bytes.fromhex(self.head) + frame); raw = frame + bytes.fromhex(head)
        chunk, slot = divmod(self.events, self.start['limits']['chunk_events'])
        try:
            self._check()
            if slot == 0:
                if self.chunk_fd is not None:
                    previous = self.chunk_fd; self.chunk_fd = None
                    io._cleanup((lambda: os.close(previous),))
                self.chunk_fd = os.open(_name(chunk), os.O_RDWR | os.O_CREAT | os.O_EXCL
                    | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=self.fd)
                self.chunks += 1; self.chunk_identity = io._signature(os.fstat(self.chunk_fd))[:2]
                os.fsync(self.fd)
            offset = slot * RECORD_BYTES
            before = os.fstat(self.chunk_fd); entry = os.stat(_name(chunk), dir_fd=self.fd, follow_symlinks=False)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and io._signature(before) == io._signature(entry)
                and io._signature(before)[:2] == self.chunk_identity
                and before.st_size == offset, 'compact chunk identity/extent changed')
            require(os.lseek(self.chunk_fd, 0, os.SEEK_END) == offset, 'compact log append offset')
            sent = 0
            while sent < len(raw):
                count = os.write(self.chunk_fd, raw[sent:])
                require(count > 0, 'compact log zero-byte write'); sent += count
            os.fsync(self.chunk_fd); self._check()
            after = os.fstat(self.chunk_fd); entry = os.stat(_name(chunk), dir_fd=self.fd, follow_symlinks=False)
            require(io._signature(after) == io._signature(entry)
                and io._signature(after)[:2] == self.chunk_identity and after.st_nlink == 1
                and after.st_size == offset + RECORD_BYTES
                and os.pread(self.chunk_fd, RECORD_BYTES, offset) == raw, 'compact log publication differs')
            self.state = state; self.head = head
        except BaseException:
            self.poisoned = True; raise

    def begin(self, purpose_sha256, identity_sha256):
        self._append(0, purpose=purpose_sha256, identity=identity_sha256)

    def progress(self, checkpoint_sha256):
        self._append(3, artifact=checkpoint_sha256)

    def complete(self, score, convergence, iterations):
        require(convergence in ('temperature_complete', 'iteration_cap'), 'convergence value differs')
        pending = self.state['pending']
        self._append(1 if convergence == 'temperature_complete' else 2, score=score, iterations=iterations)
        return {'purpose_sha256': pending['purpose_sha256'], 'score': float(score)}

    def _terminal(self, status, reason):
        self._check(failing=status == 'failed')
        require(status == 'failed' or self.state['pending'] is None, 'pending pair prevents completion')
        require(isinstance(reason, str) and len(reason.encode()) <= 1024, 'bounded log terminal reason')
        digest = hashlib.sha256(); total = 0
        for index in range(self.chunks):
            raw = io._read(self.fd, _name(index), self.start['limits']['chunk_events'] * RECORD_BYTES)
            digest.update(raw); total += len(raw)
        terminal = {'schema_version': 1, 'start_sha256': self.start_sha, 'status': status,
            'reason': reason, 'state': self.state, 'head': self.head, 'chunks': self.chunks,
            'record_bytes': total, 'payload_sha256': digest.hexdigest()}
        try:
            reference = io._write(self.fd, 'terminal.json', io._json(terminal))
            self._check(failing=status == 'failed')
            verify(self.root, owner=self.start['owner'], scope=self.start['scope'],
                   terminal_sha256=reference, lease=lambda: None)
        except BaseException as primary:
            io._close_after_failure(self.close, primary)
            raise
        self.close()
        return reference

    def finish(self): return self._terminal('complete', '')
    def fail(self, reason): return self._terminal('failed', reason)

    def close(self):
        if not self.closed:
            self.closed = True
            chunk = self.chunk_fd; self.chunk_fd = None
            actions = []
            if chunk is not None: actions.append(lambda: os.close(chunk))
            actions.append(lambda: os.close(self.fd))
            io._cleanup(actions)


def verify(root, *, owner, scope, terminal_sha256, lease):
    """Bounded replay with one pending pair. This grants no reuse admission."""
    io._identity(owner); scope = _scope(scope); io._identity(terminal_sha256)
    require(callable(lease), 'mandatory compact log verification lease')
    lease(); root, fd = io._open(root)
    try:
        observations = [0, 0, 0]
        raw = io._read(fd, 'terminal.json', io.META_LIMIT, observations)
        require(io._hash(raw) == terminal_sha256, 'compact terminal hash differs')
        terminal = json.loads(raw)
        require(set(terminal) == {'schema_version', 'start_sha256', 'status', 'reason', 'state',
            'head', 'chunks', 'record_bytes', 'payload_sha256'} and type(terminal['schema_version']) is int
            and terminal['schema_version'] == 1, 'compact terminal schema')
        raw = io._read(fd, 'start.json', io.META_LIMIT, observations); start_sha = io._hash(raw)
        require(start_sha == terminal['start_sha256'], 'compact start hash differs')
        start = json.loads(raw)
        require(set(start) == {'schema_version', 'owner', 'scope', 'limits', 'max_iterations', 'record_bytes', 'format'}
            and type(start['schema_version']) is int and start['schema_version'] == 1 and start['owner'] == owner
            and start['scope'] == scope and type(start['record_bytes']) is int and start['record_bytes'] == RECORD_BYTES
            and start['format'] == '<QB7xQdQ32s32s32s32s', 'compact start scope/format differs')
        limits = _limits(start['limits']); max_iterations = start['max_iterations']
        require(type(max_iterations) is int and 0 < max_iterations < 2**63, 'iteration bound')
        expected = terminal['state']
        require(isinstance(expected, dict) and set(expected) == set(_empty())
                and all(type(expected[k]) is int and expected[k] >= 0 for k in set(expected) - {'pending'}),
                'compact terminal state schema')
        events = expected['events']; chunks = terminal['chunks']; size = terminal['record_bytes']
        required = (events + limits['chunk_events'] - 1) // limits['chunk_events']
        require(events <= limits['max_events'] and type(chunks) is int
            and required <= chunks <= required + (1 if events % limits['chunk_events'] == 0 and events < limits['max_events'] else 0)
            and type(size) is int and events * RECORD_BYTES <= size
            <= min(limits['max_events'], events + 1) * RECORD_BYTES, 'compact terminal extent')
        require(terminal['status'] in ('complete', 'failed') and (terminal['status'] == 'failed'
            or (chunks == required and size == events * RECORD_BYTES and expected['pending'] is None)),
            'compact terminal status')
        require(isinstance(terminal['reason'], str) and len(terminal['reason'].encode()) <= 1024, 'terminal reason bound')
        state = _empty(); head = start_sha; digest = hashlib.sha256(); total = 0
        for index in range(chunks):
            lease(); io._root(root, fd)
            raw = io._read(fd, _name(index), limits['chunk_events'] * RECORD_BYTES, observations)
            expected_size = min(limits['chunk_events'] * RECORD_BYTES, size - total)
            require(len(raw) == expected_size, 'compact chunk extent differs')
            digest.update(raw); total += len(raw)
            count = min(limits['chunk_events'], events - state['events'])
            for offset in range(count):
                record = raw[offset * RECORD_BYTES:(offset + 1) * RECORD_BYTES]
                require(len(record) == RECORD_BYTES, 'truncated acknowledged event')
                checksum = io._hash(bytes.fromhex(head) + record[:-32])
                require(record[-32:] == bytes.fromhex(checksum), 'compact event checksum differs')
                state = _advance(state, record[:-32], limits, max_iterations); head = checksum
        require(state == expected and head == terminal['head'] and total == size
            and digest.hexdigest() == terminal['payload_sha256'], 'compact terminal replay differs')
        lease(); io._root(root, fd)
        final = [0, 0, 0]; count = 0
        with io._closing(os.scandir(fd)) as entries:
            for entry in entries:
                count += 1
                require(count <= chunks + 2, 'unexpected compact log inventory')
                if entry.name in ('start.json', 'terminal.json'): cap = io.META_LIMIT
                else:
                    require(entry.name.startswith('events-') and entry.name.endswith('.bin'), 'foreign compact log file')
                    index = int(entry.name[7:-4])
                    require(0 <= index < chunks and entry.name == _name(index), 'compact chunk filename')
                    cap = limits['chunk_events'] * RECORD_BYTES
                io._read(fd, entry.name, cap, final)
        require(count == chunks + 2 and final == observations, 'compact log changed during verification')
        io._root(root, fd)
        return {**state, 'status': terminal['status'], 'record_bytes': total,
                'chunks': chunks, 'unacknowledged_bytes': size - events * RECORD_BYTES}
    finally: io._release(lambda: os.close(fd))
