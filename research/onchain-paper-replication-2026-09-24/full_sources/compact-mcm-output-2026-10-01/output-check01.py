"""Stream a completed compact MCM into a verified, read-only float32 artifact.

No numerical matching is repeated and no full matrix copy is allocated. The
caller supplies externally trusted stage/scope identities, an exclusive output
namespace, a logical output reservation and a live lease. Native selection,
sample/dictionary admission, physical quotas and representation closure remain
the outer producer's responsibility. This primitive cannot admit execution.

The raw little-endian matrix has an explicit shape/order/dtype manifest. Readers
join every output byte to the retained float64 scores and completed matching
receipt. Boundary verification is sampled, not an atomic filesystem snapshot.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import stat

import numpy as np

from . import compact_stage as stages, score_batches as io
from .cache import cache_key

require = io._require


def _arguments(stage_root, stage_sha256, contract, expected_scope, max_output_bytes):
    root = Path(stage_root)
    require(root.is_absolute() and root.resolve() == root, 'canonical stage root required')
    io._identity(stage_sha256)
    require(isinstance(contract, dict) and contract.get('kind') == 'mcm', 'completed MCM contract required')
    require(type(max_output_bytes) is int and 0 < max_output_bytes < 2**63,
            'positive bounded output reservation required')
    return dict(stage_root=root, stage_sha256=stage_sha256, contract=copy.deepcopy(contract),
        expected_scope=io._scope(expected_scope), max_output_bytes=max_output_bytes)


def _source(args):
    root = args['stage_root']; contract = args['contract']
    receipt = stages.verify(root, expected_sha256=args['stage_sha256'],
        lease=lambda: None, **contract)
    start, _ = stages.read(root / 'stream', 'start.json', receipt['stream_start_sha256'])
    require(start['scope'] == args['expected_scope'], 'MCM output scientific scope differs')
    count = io._shape(start['rows'], start['motifs'], start['chunk_cells'])
    require(count == contract['pairs'] and 4 * count + io.META_LIMIT <= args['max_output_bytes'],
            'MCM output reservation insufficient')
    return start


def _chunks(args, start):
    root, fd = io._open(args['stage_root'] / 'stream/batches')
    try:
        count = start['rows'] * start['motifs']; chunk = start['chunk_cells']
        for index, offset in enumerate(range(0, count, chunk)):
            size = min(chunk, count - offset)
            raw = io._read(fd, f'chunk-{index:012d}.bin', size * 8)
            header, _ = stages.read(root, f'chunk-{index:012d}.json')
            require(len(raw) == size * 8 and io._hash(raw) == header['payload_sha256'],
                    'MCM source score bytes differ')
            # At most one score chunk plus its float32 conversion is live.
            with np.errstate(over='raise', invalid='raise'):
                values = np.frombuffer(raw, dtype='<f8').astype('<f4')
            require(np.isfinite(values).all(), 'nonfinite MCM output')
            io._root(root, fd)
            yield values.tobytes()
    finally: os.close(fd)


def _manifest(args, start, digest):
    return {'schema_version': 1, 'kind': 'compact-mcm-output',
        'stage_sha256': args['stage_sha256'], 'contract_sha256': cache_key(args['contract']),
        'stage_directory': str(args['stage_root']), 'scope': args['expected_scope'],
        'owner': args['contract']['owner'], 'rows': start['rows'], 'motifs': start['motifs'],
        'dtype': '<f4', 'order': 'row-major', 'array_bytes': 4 * start['rows'] * start['motifs'],
        'array_sha256': digest, 'execution_admitted': False}


def _file(fd, size):
    child = os.open('matrix.f32', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        info = os.fstat(child)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == size,
                'MCM output regular extent differs')
        return child, io._signature(info)
    except BaseException:
        os.close(child); raise


def _inspect(directory, expected_sha256, args):
    start = _source(args)
    root, fd = io._open(directory)
    try:
        raw = io._read(fd, 'manifest.json', io.META_LIMIT)
        require(io._hash(raw) == expected_sha256, 'MCM output manifest hash differs')
        value = json.loads(raw); digest = hashlib.sha256()
        stages.inventory(root, {'matrix.f32', 'manifest.json'})
        child, signature = _file(fd, 4 * start['rows'] * start['motifs'])
        try:
            for expected in _chunks(args, start):
                # Regular-file reads can be short; consume exactly this chunk.
                remaining = len(expected); pieces = []
                while remaining:
                    part = os.read(child, remaining)
                    require(bool(part), 'MCM output truncated')
                    pieces.append(part); remaining -= len(part)
                actual = b''.join(pieces)
                require(actual == expected, 'MCM output differs from completed matching scores')
                digest.update(actual)
            require(signature == io._signature(os.fstat(child)) == io._signature(
                os.stat('matrix.f32', dir_fd=fd, follow_symlinks=False)), 'MCM output identity changed')
        finally: os.close(child)
        require(value == _manifest(args, start, digest.hexdigest())
            and raw == io._json(value), 'MCM output metadata binding differs')
        require(_source(args) == start, 'MCM stage changed during output verification')
        require(io._read(fd, 'manifest.json', io.META_LIMIT) == raw, 'MCM output manifest changed')
        stages.inventory(root, {'matrix.f32', 'manifest.json'}); io._root(root, fd)
        return value, signature
    finally: os.close(fd)


def _verified(directory, expected_sha256, args, lease):
    require(callable(lease), 'live MCM output lease required'); io._identity(expected_sha256)
    lease(); first = _inspect(directory, expected_sha256, args)
    lease(); last = _inspect(directory, expected_sha256, args)
    require(first == last, 'MCM output changed across owner lease')
    return last


def publish(directory, *, stage_root, stage_sha256, contract, expected_scope, max_output_bytes, lease):
    """Create once from completed saved scores; failed partial namespaces persist."""
    args = _arguments(stage_root, stage_sha256, contract, expected_scope, max_output_bytes)
    require(callable(lease), 'live MCM output lease required')
    lease(); start = _source(args)
    root = Path(directory)
    require(root.is_absolute() and root.resolve() == root, 'canonical output root required')
    # Scope/reservation failure occurs before consuming the output identity.
    lease(); root.mkdir()
    parent, parent_fd = io._open(root.parent)
    try: os.fsync(parent_fd); io._root(parent, parent_fd)
    finally: os.close(parent_fd)
    root, fd = io._open(root)
    try:
        child = os.open('matrix.f32', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600, dir_fd=fd)
        digest = hashlib.sha256()
        with os.fdopen(child, 'wb', buffering=0) as output:
            for raw in _chunks(args, start):
                lease(); io._root(root, fd)
                view = memoryview(raw)
                while view:
                    written = output.write(view)
                    require(written is not None and written > 0, 'MCM output short write')
                    view = view[written:]
                digest.update(raw)
            os.fsync(output.fileno())
        os.fsync(fd); lease()
        require(_source(args) == start, 'MCM stage changed during output publication')
        ref = io._write(fd, 'manifest.json', io._json(_manifest(args, start, digest.hexdigest())))
        _verified(root, ref, args, lease); io._root(root, fd)
        return ref
    finally: os.close(fd)


def verify(directory, *, expected_sha256, stage_root, stage_sha256, contract,
           expected_scope, max_output_bytes, lease):
    args = _arguments(stage_root, stage_sha256, contract, expected_scope, max_output_bytes)
    return _verified(directory, expected_sha256, args, lease)[0]


@contextmanager
def open_verified(directory, *, expected_sha256, stage_root, stage_sha256, contract,
                  expected_scope, max_output_bytes, lease):
    """Read-only mapping valid only inside the context; reverify before acceptance.

    Consumers must not retain array views or acknowledge downstream output until
    successful context exit. Mapping/page-cache RSS needs an outer process guard.
    """
    args = _arguments(stage_root, stage_sha256, contract, expected_scope, max_output_bytes)
    value, signature = _verified(directory, expected_sha256, args, lease)
    root, fd = io._open(directory)
    try:
        child, current = _file(fd, value['array_bytes'])
        with os.fdopen(child, 'rb') as source:
            require(current == signature, 'MCM mapped file changed since verification')
            mapped = np.memmap(source, dtype='<f4', mode='r', shape=(value['rows'], value['motifs']))
            try:
                io._root(root, fd)
                yield mapped
            finally: mapped._mmap.close()
        _verified(directory, expected_sha256, args, lease); io._root(root, fd)
    finally: os.close(fd)
