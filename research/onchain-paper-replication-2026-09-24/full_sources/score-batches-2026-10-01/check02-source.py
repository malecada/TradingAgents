"""Bounded immutable completed-score chunks, independent of numerical execution.

Row-major float64 cells bind to externally admitted graph/node/motif order and
matching/workflow hashes. The caller owns numerical correctness and the lease.
No historical journal migration, successor admission, scratch disposal, fitting
or resource admission is performed here. Failed/incomplete files stay in place.
The logical bound excludes filesystem overhead, guard logs and matching scratch.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

import numpy as np

META_LIMIT = 8192
MAX_CHUNK_BYTES = 8 * 1024**2
SCOPE_FIELDS = {'graph', 'node_order', 'dictionary', 'ordered_motifs', 'matching', 'workflow'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _identity(value):
    _require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'hash identity')


def _scope(value):
    _require(isinstance(value, dict) and set(value) == SCOPE_FIELDS, 'score scope schema')
    for entry in value.values():
        _identity(entry)
    return dict(value)


def _shape(rows, motifs, chunk_cells):
    _require(all(type(x) is int and 0 < x < 2**63 for x in (rows, motifs, chunk_cells)),
             'positive bounded dimensions required')
    _require(rows * motifs < 2**63 and chunk_cells * 8 <= MAX_CHUNK_BYTES,
             'score chunk/dimension bound')
    _require((rows * motifs + chunk_cells - 1) // chunk_cells <= 10**12,
             'chunk filename capacity exceeded')
    return rows * motifs


def logical_bound(*, rows, motifs, chunk_cells):
    cells = _shape(rows, motifs, chunk_cells)
    chunks = (cells + chunk_cells - 1) // chunk_cells
    return cells * 8 + (chunks + 2) * META_LIMIT


def _json(value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    _require(len(raw) <= META_LIMIT, 'compact metadata bound')
    return raw


def _write(fd, name, body):
    # Exclusive publication. A failure leaves bytes for forensics; no overwrite,
    # retry under this identity, or cleanup that could erase interrupted work.
    child = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    with os.fdopen(child, 'wb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(fd)
    return _hash(body)


def _signature(info):
    # Reads can update atime. Modification/change clocks detect content writes.
    return tuple(getattr(info, key) for key in ('st_dev', 'st_ino', 'st_mode',
        'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_blocks'))


def _stamp(name, info):
    return int(_hash(_json([name, _signature(info)])), 16)


def _read(fd, name, limit, observations=None):
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(child, 'rb') as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_size <= limit, 'score file type/size')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=fd, follow_symlinks=False)
    _require(len(raw) == before.st_size and _signature(before) == _signature(after)
             and _signature(current) == _signature(after),
             'score file changed during read')
    if observations is not None:
        observations[0] += 1
        observations[1] = (observations[1] + _stamp(name, after)) % 2**256
    return raw


def _open(root):
    root = Path(root)
    _require(root.is_absolute() and root.resolve() == root, 'canonical score root required')
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    return root, fd


def _root(root, fd):
    current = root.lstat()
    pinned = os.fstat(fd)
    _require(root.resolve() == root and stat.S_ISDIR(current.st_mode)
             and (current.st_dev, current.st_ino) == (pinned.st_dev, pinned.st_ino),
             'score root identity changed')


class ScoreBatches:
    """One active writer; creation is exclusive and reopening is unsupported."""

    def __init__(self, root, *, scope, owner, rows, motifs, chunk_cells, lease):
        self.total = _shape(rows, motifs, chunk_cells)
        scope = _scope(scope); _identity(owner)
        _require(callable(lease), 'mandatory score lease')
        root = Path(root)
        _require(root.is_absolute() and root.resolve() == root, 'canonical score root required')
        self.start = {'schema_version': 1, 'scope': scope, 'owner': owner,
                      'rows': rows, 'motifs': motifs, 'chunk_cells': chunk_cells,
                      'dtype': '<f8', 'order': 'row-major'}
        raw = _json(self.start)
        lease(); root.mkdir()
        parent, parent_fd = _open(root.parent)
        try:
            os.fsync(parent_fd); _root(parent, parent_fd)
        finally:
            os.close(parent_fd)
        self.root, self.fd = _open(root)
        self.lease = lease; self.chunk_cells = chunk_cells
        self.cells = self.chunks = 0
        self.closed = self.poisoned = False
        try:
            self.start_sha = self.head = _write(self.fd, 'start.json', raw)
            self._check()
            _require(_hash(_read(self.fd, 'start.json', META_LIMIT)) == self.start_sha,
                     'score start publication changed')
        except BaseException:
            os.close(self.fd); self.closed = True
            raise

    def _check(self, *, failing=False):
        _require(not self.closed and (failing or not self.poisoned), 'score writer terminal or interrupted')
        self.lease(); _root(self.root, self.fd)

    def append(self, start_cell, values):
        self._check()
        count = min(self.chunk_cells, self.total - self.cells)
        _require(type(start_cell) is int and start_cell == self.cells and count > 0,
                 'score cell sequence differs')
        _require(isinstance(values, np.ndarray) and values.dtype.str == '<f8'
                 and values.shape == (count,) and values.flags.c_contiguous,
                 'bounded contiguous float64 score chunk required')
        raw = values.tobytes()  # bounded private snapshot before hashing/writing
        _require(np.isfinite(np.frombuffer(raw, dtype='<f8')).all(), 'nonfinite scores')
        header = {'schema_version': 1, 'start_sha256': self.start_sha,
                  'previous': self.head, 'index': self.chunks, 'start_cell': self.cells,
                  'cells': count, 'payload_sha256': _hash(raw)}
        name = f'chunk-{self.chunks:012d}'
        try:
            self._check()
            _write(self.fd, name + '.bin', raw)
            head = _write(self.fd, name + '.json', _json(header))
            self._check()
            _require(_hash(_read(self.fd, name + '.bin', len(raw))) == header['payload_sha256']
                     and _hash(_read(self.fd, name + '.json', META_LIMIT)) == head,
                     'score chunk publication changed')
            self.head = head; self.chunks += 1; self.cells += count
        except BaseException:
            self.poisoned = True
            raise
        return head

    def _terminal(self, status, reason):
        self._check(failing=status == 'failed')
        _require(status == 'failed' or self.cells == self.total, 'incomplete scores')
        _require(isinstance(reason, str) and len(reason.encode()) <= 1024, 'bounded terminal reason')
        pending = []
        if self.poisoned:
            for suffix, limit in (('.bin', MAX_CHUNK_BYTES), ('.json', META_LIMIT)):
                name = f'chunk-{self.chunks:012d}' + suffix
                try:
                    raw = _read(self.fd, name, limit)
                except FileNotFoundError:
                    continue
                pending.append({'name': name, 'bytes': len(raw), 'sha256': _hash(raw)})
        terminal = {'schema_version': 1, 'start_sha256': self.start_sha,
                    'head': self.head, 'status': status, 'cells': self.cells,
                    'chunks': self.chunks, 'reason': reason, 'pending': pending}
        try:
            result = _write(self.fd, 'terminal.json', _json(terminal))
            self._check(failing=status == 'failed')
            _require(_hash(_read(self.fd, 'terminal.json', META_LIMIT)) == result,
                     'score terminal publication changed')
            return result
        finally:
            self.closed = True; os.close(self.fd)

    def finish(self):
        return self._terminal('complete', '')

    def fail(self, reason):
        return self._terminal('failed', reason)

    def close(self):
        """Release only the descriptor; incomplete bytes are never deleted."""
        if not self.closed:
            self.closed = True; os.close(self.fd)


def verify(root, *, scope, owner, terminal_sha256, lease):
    """Verify a terminal store with O(chunk_bytes) memory; return compact counts.

    This is a sampled, non-atomic check under a sole-writer/source-freeze contract.
    Per-read signatures are aggregated in constant space and rechecked by a
    final inventory scan; concurrent mutation after that scan is not prevented.
    This does not admit reuse or publish numerical outputs. The terminal hash
    must come from an independently admitted receipt, not from observed files.
    """
    scope = _scope(scope); _identity(owner); _identity(terminal_sha256)
    _require(callable(lease), 'mandatory verification lease')
    lease(); root, fd = _open(root)
    try:
        observations = [0, 0]
        raw = _read(fd, 'terminal.json', META_LIMIT, observations)
        _require(_hash(raw) == terminal_sha256, 'terminal hash differs')
        terminal = json.loads(raw)
        _require(set(terminal) == {'schema_version', 'start_sha256', 'head', 'status',
                                  'cells', 'chunks', 'reason', 'pending'}
                 and type(terminal['schema_version']) is int and terminal['schema_version'] == 1,
                 'terminal schema')
        start_raw = _read(fd, 'start.json', META_LIMIT, observations); start = json.loads(start_raw)
        head = start_sha = _hash(start_raw)
        _require(head == terminal['start_sha256'] and set(start) == {
            'schema_version', 'scope', 'owner', 'rows', 'motifs', 'chunk_cells', 'dtype', 'order'},
            'score start differs')
        _require(type(start['schema_version']) is int and start['schema_version'] == 1
                 and start['scope'] == scope and start['owner'] == owner
                 and start['dtype'] == '<f8' and start['order'] == 'row-major', 'score binding differs')
        total = _shape(start['rows'], start['motifs'], start['chunk_cells'])
        chunks = terminal['chunks']; cells = terminal['cells']
        _require(type(chunks) is int and 0 <= chunks <= (total + start['chunk_cells'] - 1) // start['chunk_cells']
                 and type(cells) is int and cells == min(chunks * start['chunk_cells'], total),
                 'score denominator differs')
        _require(terminal['status'] in ('complete', 'failed')
                 and (terminal['status'] != 'complete' or cells == total), 'score status differs')
        _require(isinstance(terminal['reason'], str) and len(terminal['reason'].encode()) <= 1024,
                 'terminal reason bound')
        for index in range(chunks):
            lease(); _root(root, fd)
            name = f'chunk-{index:012d}'; offset = index * start['chunk_cells']
            count = min(start['chunk_cells'], total - offset)
            raw = _read(fd, name + '.json', META_LIMIT, observations); header = json.loads(raw)
            payload = _read(fd, name + '.bin', count * 8, observations)
            _require(header == {'schema_version': 1, 'start_sha256': start_sha,
                'previous': head, 'index': index, 'start_cell': offset, 'cells': count,
                'payload_sha256': _hash(payload)}, 'score chunk binding/hash differs')
            _require(len(payload) == count * 8 and np.isfinite(np.frombuffer(payload, dtype='<f8')).all(),
                     'score payload differs')
            head = _hash(raw)
        _require(head == terminal['head'], 'score chain head differs')
        pending = terminal['pending']
        _require(isinstance(pending, list) and len(pending) <= 2
                 and (not pending or terminal['status'] == 'failed'), 'pending files schema')
        names = set()
        for entry in pending:
            _require(isinstance(entry, dict) and set(entry) == {'name', 'bytes', 'sha256'}, 'pending entry schema')
            name = entry['name']
            _require(isinstance(name, str) and name in {f'chunk-{chunks:012d}.bin', f'chunk-{chunks:012d}.json'}
                     and name not in names and chunks * start['chunk_cells'] < total, 'pending file sequence')
            raw = _read(fd, name, MAX_CHUNK_BYTES if name.endswith('.bin') else META_LIMIT, observations)
            _require(type(entry['bytes']) is int and len(raw) == entry['bytes']
                     and _hash(raw) == entry['sha256'], 'pending file hash/size differs')
            names.add(name)
        # No list of all cell/chunk identities is retained in memory.
        lease(); _root(root, fd)
        count = stamp = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                count += 1
                _require(count <= 2 + 2 * chunks + len(names), 'unexpected score files')
                match = re.fullmatch(r'chunk-([0-9]{12})\.(bin|json)', entry.name)
                _require(entry.name in {'start.json', 'terminal.json'} | names
                         or (match is not None and int(match[1]) < chunks), 'unexpected score file')
                stamp = (stamp + _stamp(entry.name, entry.stat(follow_symlinks=False))) % 2**256
        _require(count == 2 + 2 * chunks + len(names), 'score inventory differs')
        _require([count, stamp] == observations, 'score files changed after verification reads')
        _root(root, fd)
        return {'status': terminal['status'], 'cells': cells, 'chunks': chunks,
                'payload_bytes': cells * 8, 'pending_files': sorted(names)}
    finally:
        os.close(fd)
