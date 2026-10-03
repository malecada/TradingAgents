"""Durable bounded MCM score tails; no matcher, ownership admission or restart.

Each 80-byte record binds global ordinal, exact float64 score and purpose hash
to the preceding record and immutable start manifest. All tails are retained,
including those copied to ScoreBatches. This duplicates storage deliberately.
The caller supplies admitted identities, exclusive ownership and a live lease.
"""
import json
import math
import os
from pathlib import Path
import stat
import struct

import numpy as np

from . import score_batches as batch

RECORD_BYTES = 80
FRAME = struct.Struct('<Qd32s')
require = batch._require


def destination(batches):
    require(isinstance(batches, batch.ScoreBatches), 'actual score batch writer required')
    batches._check()
    count = min(batches.chunk_cells, batches.total - batches.cells)
    require(count > 0, 'batch destination already complete')
    return batch._hash(batch._json({'directory': str(batches.root),
        'start_sha256': batches.start_sha, 'index': batches.chunks,
        'start_cell': batches.cells, 'cells': count}))


def _shape(start_cell, cells):
    require(type(start_cell) is int and 0 <= start_cell < 2**63
        and type(cells) is int and 0 < cells <= batch.MAX_CHUNK_BYTES // RECORD_BYTES
        and start_cell + cells < 2**63, 'tail ordinal/capacity bound')


def _decode(raw, start_sha, start_cell, acknowledged):
    values = np.empty(acknowledged, dtype='<f8')
    purposes = np.empty((acknowledged, 32), dtype=np.uint8)
    head = start_sha
    for index in range(acknowledged):
        record = raw[index * RECORD_BYTES:(index + 1) * RECORD_BYTES]
        require(len(record) == RECORD_BYTES, 'acknowledged record truncated')
        ordinal, value, purpose = FRAME.unpack(record[:48])
        checksum = batch._hash(bytes.fromhex(head) + record[:48])
        require(ordinal == start_cell + index and math.isfinite(value) and 0 <= value <= 1
                and record[48:] == bytes.fromhex(checksum), 'tail record order/value/checksum differs')
        values[index] = value; purposes[index] = np.frombuffer(purpose, dtype=np.uint8)
        head = checksum
    return head, values, purposes


class ScoreTail:
    """Single-use append-only tail. A failed append poisons further appends."""

    def __init__(self, root, *, scope, owner, start_cell, cells, destination, lease):
        _shape(start_cell, cells); scope = batch._scope(scope)
        batch._identity(owner); batch._identity(destination)
        require(callable(lease), 'mandatory tail lease')
        root = Path(root)
        require(root.is_absolute() and root.resolve() == root, 'canonical tail root required')
        self.start = {'schema_version': 1, 'kind': 'mcm-score-tail', 'scope': scope,
            'owner': owner, 'start_cell': start_cell, 'cells': cells,
            'destination': destination, 'record_format': '<Qd32s32s', 'record_bytes': RECORD_BYTES}
        self.lease = lease; self.closed = self.poisoned = False
        self.acknowledged = 0; self.record_fd = None
        lease(); root.mkdir()
        parent, parent_fd = batch._open(root.parent)
        try:
            os.fsync(parent_fd); batch._root(parent, parent_fd)
        finally: batch._release(lambda: os.close(parent_fd))
        self.root, self.fd = batch._open(root)
        try:
            self.head = self.start_sha = batch._write(self.fd, 'start.json', batch._json(self.start))
            self.record_fd = os.open('records.bin', os.O_RDWR | os.O_CREAT | os.O_EXCL
                | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=self.fd)
            self.record_identity = batch._signature(os.fstat(self.record_fd))[:2]
            os.fsync(self.record_fd); os.fsync(self.fd)
            self._check()
            require(batch._hash(batch._read(self.fd, 'start.json', batch.META_LIMIT)) == self.start_sha,
                    'tail start changed during publication')
        except BaseException as primary:
            batch._close_after_failure(self.close, primary)
            raise

    def _check(self, *, pending=False, expected_size=None):
        require(not self.closed and (pending or not self.poisoned), 'tail terminal or interrupted')
        self.lease(); batch._root(self.root, self.fd)
        live = os.fstat(self.record_fd)
        entry = os.stat('records.bin', dir_fd=self.fd, follow_symlinks=False)
        require(stat.S_ISREG(live.st_mode) and live.st_nlink == 1
                and batch._signature(live) == batch._signature(entry)
                and batch._signature(live)[:2] == self.record_identity, 'tail file identity differs')
        if expected_size is not None:
            require(live.st_size == expected_size, 'tail publication extent differs')
        else:
            low = self.acknowledged * RECORD_BYTES
            high = min(self.start['cells'], self.acknowledged + (1 if pending else 0)) * RECORD_BYTES
            require(low <= live.st_size <= high, 'tail extent differs from acknowledged prefix')

    def append(self, ordinal, purpose_sha256, score):
        self._check(); batch._identity(purpose_sha256)
        require(type(ordinal) is int and ordinal == self.start['start_cell'] + self.acknowledged
                and self.acknowledged < self.start['cells'], 'tail score order/capacity differs')
        require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1,
                'finite scalar similarity in [0,1] required')
        value = float(score); frame = FRAME.pack(ordinal, value, bytes.fromhex(purpose_sha256))
        head = batch._hash(bytes.fromhex(self.head) + frame); raw = frame + bytes.fromhex(head)
        offset = self.acknowledged * RECORD_BYTES
        try:
            self._check()
            require(os.lseek(self.record_fd, 0, os.SEEK_END) == offset, 'tail append position differs')
            sent = 0
            while sent < len(raw):
                count = os.write(self.record_fd, raw[sent:])
                require(count > 0, 'tail short write made no progress'); sent += count
            os.fsync(self.record_fd)
            self._check(expected_size=offset + RECORD_BYTES)
            require(os.pread(self.record_fd, RECORD_BYTES, offset) == raw, 'tail record readback differs')
            self.head = head; self.acknowledged += 1
        except BaseException:
            self.poisoned = True
            raise
        return {'purpose_sha256': purpose_sha256, 'score': value}

    def _terminal(self, status, reason):
        self._check(pending=status == 'failed')
        require(status == 'failed' or self.acknowledged == self.start['cells'], 'incomplete tail')
        require(isinstance(reason, str) and len(reason.encode()) <= 1024, 'bounded failure reason')
        raw = batch._read(self.fd, 'records.bin', self.start['cells'] * RECORD_BYTES)
        head, _, _ = _decode(raw, self.start_sha, self.start['start_cell'], self.acknowledged)
        require(head == self.head, 'tail acknowledged prefix changed')
        record = {'schema_version': 1, 'start_sha256': self.start_sha, 'status': status,
            'reason': reason, 'acknowledged_cells': self.acknowledged, 'head': self.head,
            'records_bytes': len(raw), 'records_sha256': batch._hash(raw)}
        try:
            result = batch._write(self.fd, 'terminal.json', batch._json(record))
            self._check(pending=status == 'failed')
            require(batch._hash(batch._read(self.fd, 'terminal.json', batch.META_LIMIT)) == result
                    and batch._read(self.fd, 'records.bin', self.start['cells'] * RECORD_BYTES) == raw,
                    'tail terminal publication changed')
        except BaseException as primary:
            batch._close_after_failure(self.close, primary)
            raise
        self.close()
        return result

    def finish(self):
        return self._terminal('complete', '')

    def fail(self, reason):
        return self._terminal('failed', reason)

    def close(self):
        if not self.closed:
            self.closed = True
            actions = []
            if self.record_fd is not None: actions.append(lambda: os.close(self.record_fd))
            actions.append(lambda: os.close(self.fd))
            batch._cleanup(actions)


def verify(root, *, scope, owner, terminal_sha256, lease):
    """Read-only terminal validation, not successor/replay permission.

    Pending bytes on a failed tail remain uninterpreted, even when record-sized.
    Two bounded content passes detect drift; concurrent changes after the last
    read remain outside this sampled check's sole-writer contract.
    """
    scope = batch._scope(scope); batch._identity(owner); batch._identity(terminal_sha256)
    require(callable(lease), 'mandatory tail verification lease')
    lease(); root, fd = batch._open(root)
    try:
        observations = [0, 0, 0]
        raw = batch._read(fd, 'terminal.json', batch.META_LIMIT, observations)
        require(batch._hash(raw) == terminal_sha256, 'tail terminal hash differs')
        terminal = json.loads(raw)
        require(set(terminal) == {'schema_version', 'start_sha256', 'status', 'reason',
            'acknowledged_cells', 'head', 'records_bytes', 'records_sha256'}
            and type(terminal['schema_version']) is int and terminal['schema_version'] == 1,
            'tail terminal schema')
        start_raw = batch._read(fd, 'start.json', batch.META_LIMIT, observations)
        start = json.loads(start_raw); start_sha = batch._hash(start_raw)
        require(start_sha == terminal['start_sha256'] and set(start) == {'schema_version',
            'kind', 'scope', 'owner', 'start_cell', 'cells', 'destination', 'record_format', 'record_bytes'},
            'tail start identity/schema differs')
        require(type(start['schema_version']) is int and start['schema_version'] == 1
            and start['kind'] == 'mcm-score-tail' and start['scope'] == scope and start['owner'] == owner
            and start['record_format'] == '<Qd32s32s' and type(start['record_bytes']) is int
            and start['record_bytes'] == RECORD_BYTES, 'tail scope/owner/format differs')
        _shape(start['start_cell'], start['cells']); batch._identity(start['destination'])
        acknowledged = terminal['acknowledged_cells']; size = terminal['records_bytes']
        require(type(acknowledged) is int and 0 <= acknowledged <= start['cells']
            and type(size) is int and acknowledged * RECORD_BYTES <= size
            <= min(start['cells'], acknowledged + 1) * RECORD_BYTES, 'tail terminal denominator')
        require(terminal['status'] in ('complete', 'failed')
            and (terminal['status'] == 'failed' or acknowledged == start['cells']), 'tail status differs')
        require(isinstance(terminal['reason'], str) and len(terminal['reason'].encode()) <= 1024,
                'tail terminal reason bound')
        lease(); batch._root(root, fd)
        raw = batch._read(fd, 'records.bin', start['cells'] * RECORD_BYTES, observations)
        require(len(raw) == size and batch._hash(raw) == terminal['records_sha256'], 'tail bytes/hash differs')
        head, values, purposes = _decode(raw, start_sha, start['start_cell'], acknowledged)
        require(head == terminal['head'], 'tail acknowledged chain differs')
        lease(); batch._root(root, fd)
        final = [0, 0, 0]; count = 0
        with batch._closing(os.scandir(fd)) as entries:
            for entry in entries:
                count += 1
                require(count <= 3 and entry.name in ('start.json', 'records.bin', 'terminal.json'),
                        'unexpected tail entry')
                batch._read(fd, entry.name, start['cells'] * RECORD_BYTES if entry.name == 'records.bin'
                    else batch.META_LIMIT, final)
        require(final == observations, 'tail changed after verification reads')
        batch._root(root, fd)
        return {'status': terminal['status'], 'start_cell': start['start_cell'],
            'cells': start['cells'], 'destination': start['destination'],
            'acknowledged_cells': acknowledged, 'pending_bytes': size - acknowledged * RECORD_BYTES,
            'values': values, 'purpose_hashes': purposes}
    finally:
        batch._release(lambda: os.close(fd))


def seal(root, *, terminal_sha256, batches, lease):
    """Copy one verified complete tail to its exact next chunk; retain the tail.

    This validates the stored purpose chain, not whether supplied purposes were
    derived from admitted graph inputs. Numerical/owner admission is external.
    No retry/reconciliation of a previously published chunk is inferred.
    """
    expected = destination(batches)
    result = verify(root, scope=batches.start['scope'], owner=batches.start['owner'],
                    terminal_sha256=terminal_sha256, lease=lease)
    require(result['status'] == 'complete' and result['destination'] == expected
        and result['start_cell'] == batches.cells
        and result['cells'] == min(batches.chunk_cells, batches.total - batches.cells),
        'tail is not the complete exact next batch destination')
    lease()
    require(destination(batches) == expected, 'batch destination changed before seal')
    index = batches.chunks; start_sha = batches.start_sha
    expected_payload = result['values'].tobytes()
    head = batches.append(result['start_cell'], result['values'])
    # Tail and batch leases can be different. A late failure retains the
    # published chunk but cannot acknowledge a successful combined seal.
    lease(); batches._check()
    # All externally supplied callbacks precede the final content checks on
    # BOTH stores. The no-op below performs no additional owner callback.
    verify(root, scope=batches.start['scope'], owner=batches.start['owner'],
           terminal_sha256=terminal_sha256, lease=lambda: None)
    batch._root(batches.root, batches.fd)
    require(batch._hash(batch._read(batches.fd, 'start.json', batch.META_LIMIT)) == start_sha
        and batch._hash(batch._read(batches.fd, f'chunk-{index:012d}.json', batch.META_LIMIT)) == head
        and batch._read(batches.fd, f'chunk-{index:012d}.bin', len(expected_payload)) == expected_payload,
        'sealed destination changed after tail verification')
    return head
