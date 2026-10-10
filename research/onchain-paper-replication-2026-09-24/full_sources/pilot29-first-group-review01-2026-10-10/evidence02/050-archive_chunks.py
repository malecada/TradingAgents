"""Copy/readback prototype for bounded immutable archive members.

Transport is caller-owned: identity, exclusive mkdir, bounded finite put/get.
No source disposal, existing-reader substitution, empirical admission or remote
immutability is granted. The caller supplies a trusted frozen-member reference
and real source/runtime/guard lease. Failed attempts and all bytes are retained.
"""
import json
import os
from pathlib import Path
import re
import shutil

from . import score_batches as io

require = io._require
MAX_BYTES = io.MAX_CHUNK_BYTES


def _path(value):
    path = Path(value)
    require(path.is_absolute() and path.resolve() == path, 'canonical archive path required')
    return path


def _fresh(value):
    path = _path(value)
    if os.path.lexists(path): raise FileExistsError(path)
    require(path.parent.is_dir(), 'archive parent must exist')
    return path


def _extent(size, digest):
    io._identity(digest)
    require(type(size) is int and 0 < size <= MAX_BYTES, 'bounded positive archive extent')


def _transport(transport):
    io._identity(transport.identity)
    require(all(callable(getattr(transport, name, None)) for name in ('mkdir', 'put', 'get')),
            'archive transport contract required')
    return transport.identity


def _remote(name):
    require(isinstance(name, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}', name),
            'single bounded remote object name required')
    return name + '/payload.bin'


def _capacity(path, floor, copies, size):
    require(type(floor) is int and floor >= 0, 'archive free-space floor')
    # Admission check, not a reservation or a filesystem physical upper bound.
    require(shutil.disk_usage(path).free >= floor + copies * size + 4 * io.META_LIMIT,
            'archive local floor plus scratch unavailable')


def _read(path, size, digest):
    root, fd = io._open(path.parent)
    try:
        raw = io._read(fd, path.name, size)
        info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
        require(info.st_blocks * 512 >= info.st_size, 'sparse archive source unsupported')
        require(len(raw) == size and io._hash(raw) == digest, 'archive content extent/hash differs')
        io._root(root, fd)
        return raw
    finally: os.close(fd)


def _claim(path):
    path.mkdir()
    parent, fd = io._open(path.parent)
    try:
        os.fsync(fd); io._root(parent, fd)
    finally: os.close(fd)
    return io._open(path)[1]


def _check(path, fd, lease, transport, identity):
    lease(); io._root(path, fd)
    require(_transport(transport) == identity, 'archive transport identity changed')


def _inventory(fd, names):
    # Count before accumulating names; foreign files cannot create an unbounded scan.
    seen = set()
    with os.scandir(fd) as entries:
        for entry in entries:
            require(entry.name in names and entry.name not in seen, 'archive inventory conflict/foreign member')
            seen.add(entry.name)
    require(seen == names, 'archive inventory incomplete')


def _failed(fd, error):
    io._write(fd, 'failed.json', io._json({'schema_version': 1, 'error_type': type(error).__name__}))


def preserve(*, source, attempt, expected_sha256, expected_bytes, scope, remote,
             transport, lease, free_floor_bytes):
    """Copy and round-trip one prebound member. Original is never unlinked."""
    attempt = _fresh(attempt); source = _path(source)
    _extent(expected_bytes, expected_sha256); io._identity(scope)
    identity = _transport(transport); member = _remote(remote)
    require(callable(lease), 'archive live lease required')
    lease()
    raw = _read(source, expected_bytes, expected_sha256)
    _capacity(attempt.parent, free_floor_bytes, 2, expected_bytes)
    receipt = dict(schema_version=1, format='archive-chunk-v1',
        transport_identity=identity, remote=remote, member=member, scope=scope,
        source_sha256=expected_sha256, bytes=expected_bytes)
    fd = _claim(attempt)
    try:
        io._write(fd, 'intent.json', io._json(receipt))
        io._write(fd, 'snapshot.bin', raw)
        del raw
        _check(attempt, fd, lease, transport, identity)
        transport.mkdir(remote)  # Must fail if the remote attempt already exists.
        transport.put(attempt / 'snapshot.bin', member)
        _check(attempt, fd, lease, transport, identity)
        transport.get(member, attempt / 'readback.bin', expected_bytes=expected_bytes)
        _check(attempt, fd, lease, transport, identity)
        def verify(completed):
            # Callbacks have finished before all final inventory/content checks.
            names = {'intent.json', 'snapshot.bin', 'readback.bin'}
            if completed: names.add('complete.json')
            _inventory(fd, names)
            for path in (source, attempt / 'snapshot.bin', attempt / 'readback.bin'):
                _read(path, expected_bytes, expected_sha256)
            for name in ('intent.json', 'complete.json') if completed else ('intent.json',):
                require(io._read(fd, name, io.META_LIMIT) == io._json(receipt), 'archive metadata changed')
            io._root(attempt, fd)
        verify(False)
        reference = io._write(fd, 'complete.json', io._json(receipt))
        _check(attempt, fd, lease, transport, identity)
        verify(True)
        return reference
    except BaseException as error:
        try: _failed(fd, error)
        except BaseException as failure: error.add_note('archive failure marker error: ' + type(failure).__name__)
        raise
    finally: os.close(fd)


def retrieve(receipt_root, *, receipt_sha256, attempt, transport, lease, free_floor_bytes):
    """Fresh download using a trusted receipt hash; never reuses a failed path."""
    attempt = _fresh(attempt); receipt_root = _path(receipt_root)
    io._identity(receipt_sha256); identity = _transport(transport)
    require(callable(lease), 'archive live lease required')
    lease()
    root, rfd = io._open(receipt_root)
    try:
        _inventory(rfd, {'intent.json', 'snapshot.bin', 'readback.bin', 'complete.json'})
        raw = io._read(rfd, 'complete.json', io.META_LIMIT)
        require(io._hash(raw) == receipt_sha256, 'archive receipt hash differs')
        receipt = json.loads(raw)
        require(set(receipt) == {'schema_version', 'format', 'transport_identity', 'remote',
            'member', 'scope', 'source_sha256', 'bytes'} and type(receipt['schema_version']) is int
            and receipt['schema_version'] == 1 and receipt['format'] == 'archive-chunk-v1',
            'archive receipt schema differs')
        io._identity(receipt['scope'])
        _extent(receipt['bytes'], receipt['source_sha256'])
        require(receipt['transport_identity'] == identity and receipt['member'] == _remote(receipt['remote']),
                'archive receipt transport/member differs')
        _capacity(attempt.parent, free_floor_bytes, 1, receipt['bytes'])
        fd = _claim(attempt)
        try:
            intent = io._json({'receipt_sha256': receipt_sha256, **receipt})
            io._write(fd, 'intent.json', intent)
            _check(attempt, fd, lease, transport, identity)
            destination = attempt / 'payload.bin'
            transport.get(receipt['member'], destination, expected_bytes=receipt['bytes'])
            _check(attempt, fd, lease, transport, identity)
            def verify(completed):
                names = {'intent.json', 'payload.bin'}
                if completed: names.add('complete.json')
                _inventory(fd, names)
                _inventory(rfd, {'intent.json', 'snapshot.bin', 'readback.bin', 'complete.json'})
                _read(destination, receipt['bytes'], receipt['source_sha256'])
                for name in ('complete.json', 'intent.json'):
                    require(io._read(rfd, name, io.META_LIMIT) == raw, 'archive receipt changed')
                for name in ('intent.json', 'complete.json') if completed else ('intent.json',):
                    require(io._read(fd, name, io.META_LIMIT) == intent, 'archive retrieval metadata changed')
                io._root(root, rfd); io._root(attempt, fd)
            verify(False)
            io._write(fd, 'complete.json', intent)
            _check(attempt, fd, lease, transport, identity)
            verify(True)
            return destination
        except BaseException as error:
            try: _failed(fd, error)
            except BaseException as failure: error.add_note('archive failure marker error: ' + type(failure).__name__)
            raise
        finally: os.close(fd)
    finally: os.close(rfd)
