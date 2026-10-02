"""Read a trusted archived member; dispose only this call's fresh cache copy.

Old source/receipt directories are neither opened nor disposed. Caller owns
scientific eligibility, transport/guard budgets, cumulative metadata, parallel
calls and retained returned bytes. Completion is a verified read observation,
not a promise of remote availability or admission to an old local-only owner.
"""
import json
import os

from . import archive_chunks as archive

io = archive.io
require = io._require


def consume(*, receipt_bytes, receipt_sha256, expected_scope, attempt, transport,
            lease, free_floor_bytes):
    """Return immutable verified bytes, retaining metadata but no success payload."""
    attempt = archive._fresh(attempt)
    io._identity(receipt_sha256); io._identity(expected_scope)
    require(type(receipt_bytes) is bytes and len(receipt_bytes) <= io.META_LIMIT
        and io._hash(receipt_bytes) == receipt_sha256, 'trusted bounded receipt bytes required')
    receipt = json.loads(receipt_bytes)
    require(isinstance(receipt, dict) and set(receipt) == {'schema_version', 'format',
        'transport_identity', 'remote', 'member', 'scope', 'source_sha256', 'bytes'}
        and type(receipt['schema_version']) is int and receipt['schema_version'] == 1
        and receipt['format'] == 'archive-chunk-v1' and io._json(receipt) == receipt_bytes,
        'canonical archive receipt schema required')
    identity = archive._transport(transport)
    require(receipt['scope'] == expected_scope and receipt['transport_identity'] == identity
        and receipt['member'] == archive._remote(receipt['remote']), 'archive scope/endpoint/member differs')
    archive._extent(receipt['bytes'], receipt['source_sha256'])
    require(callable(lease), 'mandatory archive consumption lease')
    lease(); archive._capacity(attempt.parent, free_floor_bytes, 1, receipt['bytes'])
    intent = io._json({'schema_version': 1, 'format': 'archive-consume-v1',
        'receipt_sha256': receipt_sha256, 'receipt': receipt})
    verified = io._json({'schema_version': 1, 'intent_sha256': io._hash(intent),
        'bytes': receipt['bytes'], 'payload_sha256': receipt['source_sha256']})
    complete = io._json({'schema_version': 1, 'verified_sha256': io._hash(verified),
        'owned_cache_disposed': True})
    fd = archive._claim(attempt)
    try:
        io._write(fd, 'intent.json', intent)
        archive._check(attempt, fd, lease, transport, identity)
        transport.get(receipt['member'], attempt / 'payload.bin', expected_bytes=receipt['bytes'])
        archive._check(attempt, fd, lease, transport, identity)

        def evidence(bodies, payload):
            names = set(bodies) | ({'payload.bin'} if payload else set())
            archive._inventory(fd, names)
            for name, body in bodies.items():
                require(io._read(fd, name, io.META_LIMIT) == body, 'archive consumption metadata changed')
            io._root(attempt, fd)

        evidence({'intent.json': intent}, True)
        # Validate before publishing a verified receipt; final callback checks repeat it.
        archive._read(attempt / 'payload.bin', receipt['bytes'], receipt['source_sha256'])
        io._write(fd, 'verified.json', verified)
        archive._check(attempt, fd, lease, transport, identity)
        evidence({'intent.json': intent, 'verified.json': verified}, True)
        before = os.stat('payload.bin', dir_fd=fd, follow_symlinks=False)
        result = archive._read(attempt / 'payload.bin', receipt['bytes'], receipt['source_sha256'])
        require(io._signature(before) == io._signature(os.stat('payload.bin', dir_fd=fd,
            follow_symlinks=False)), 'cache identity changed before disposal')
        # No callback between the last content/identity check and owned cache disposal.
        os.unlink('payload.bin', dir_fd=fd)
        os.fsync(fd)
        io._write(fd, 'complete.json', complete)
        archive._check(attempt, fd, lease, transport, identity)
        evidence({'intent.json': intent, 'verified.json': verified, 'complete.json': complete}, False)
        require(type(result) is bytes and len(result) == receipt['bytes']
            and io._hash(result) == receipt['source_sha256'], 'returned archive bytes differ')
        return result
    except BaseException as error:
        try: archive._failed(fd, error)
        except BaseException as failure:
            error.add_note('archive consumption failure marker error: ' + type(failure).__name__)
        raise
    finally: os.close(fd)
