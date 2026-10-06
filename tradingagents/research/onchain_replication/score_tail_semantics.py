"""Streaming COMPLETE score-tail semantics, not provenance or execution authority.

The caller authenticates original metadata, source, scope, owner and transport;
provides an already-open, bounded read(n); and owns its lifetime/deadline. This
single content pass neither opens files nor establishes immutability or leases.
"""
import hashlib
import json
import math
import re
import struct

RECORD_BYTES = 80
FRAME = struct.Struct('<Qd32s')
META_LIMIT = 8192
MAX_CHUNK_BYTES = 8 * 1024**2
SCOPE_FIELDS = {'graph', 'node_order', 'dictionary', 'ordered_motifs', 'matching', 'workflow'}
START_FIELDS = {'schema_version', 'kind', 'scope', 'owner', 'start_cell', 'cells',
                'destination', 'record_format', 'record_bytes'}
TERMINAL_FIELDS = {'schema_version', 'start_sha256', 'status', 'reason',
                   'acknowledged_cells', 'head', 'records_bytes', 'records_sha256'}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _identity(value):
    _require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'hash identity')


def _scope(value):
    _require(isinstance(value, dict) and set(value) == SCOPE_FIELDS, 'score scope schema')
    for entry in value.values():
        _identity(entry)
    return dict(value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate metadata key')
        result[key] = value
    return result


def _metadata(raw, expected):
    _identity(expected)
    _require(type(raw) is bytes and 0 < len(raw) <= META_LIMIT, 'bounded metadata bytes required')
    _require(hashlib.sha256(raw).hexdigest() == expected, 'original metadata hash differs')
    value = json.loads(raw, object_pairs_hook=_pairs)
    _require(type(value) is dict, 'metadata object required')
    return value


def _read_exact(read, size):
    parts = bytearray()
    while len(parts) < size:
        left = size - len(parts)
        part = read(left)
        _require(type(part) is bytes and len(part) <= left, 'reader violated requested byte bound')
        _require(bool(part), 'complete tail truncated')
        parts.extend(part)
    return bytes(parts)


def verify_complete(read, *, start_raw, terminal_raw, start_sha256,
                    terminal_sha256, scope, owner):
    """Validate one entire original COMPLETE tail with O(80 + metadata) memory.

    read(n) must return at most n bytes and b'' only at EOF. It may perform short
    reads; errors propagate. It must start at the records body's first byte.
    An FD adapter is lambda n: os.read(fd, n). Reader calls are bounded to the
    declared body plus one EOF byte, each request <=80 bytes. No rewind/close.
    Pinned source semantics bound a tail to 8MiB, not an entire multi-tail MCM.
    Full history requires the caller's independently authenticated tail roster.
    """
    _require(callable(read), 'bounded binary reader required')
    scope = _scope(scope)
    _identity(owner)
    start = _metadata(start_raw, start_sha256)
    terminal = _metadata(terminal_raw, terminal_sha256)
    _require(set(start) == START_FIELDS and type(start['schema_version']) is int
             and start['schema_version'] == 1, 'tail start schema')
    _require(start['kind'] == 'mcm-score-tail' and start['scope'] == scope
             and start['owner'] == owner and start['record_format'] == '<Qd32s32s'
             and type(start['record_bytes']) is int and start['record_bytes'] == RECORD_BYTES,
             'tail scope/owner/format differs')
    first, count = start['start_cell'], start['cells']
    _require(type(first) is int and 0 <= first < 2**63 and type(count) is int
             and 0 < count <= MAX_CHUNK_BYTES // RECORD_BYTES and first + count < 2**63,
             'tail ordinal/capacity bound')
    _identity(start['destination'])
    _require(set(terminal) == TERMINAL_FIELDS and type(terminal['schema_version']) is int
             and terminal['schema_version'] == 1, 'tail terminal schema')
    _require(terminal['start_sha256'] == start_sha256, 'tail start identity differs')
    _require(terminal['status'] == 'complete', 'only original COMPLETE tail supported')
    _require(type(terminal['acknowledged_cells']) is int
             and terminal['acknowledged_cells'] == count
             and type(terminal['records_bytes']) is int
             and terminal['records_bytes'] == count * RECORD_BYTES, 'complete tail denominator')
    _require(isinstance(terminal['reason'], str) and len(terminal['reason'].encode()) <= 1024,
             'tail terminal reason bound')
    _identity(terminal['head'])
    _identity(terminal['records_sha256'])
    head = bytes.fromhex(start_sha256)
    body_hash = hashlib.sha256()
    for index in range(count):
        record = _read_exact(read, RECORD_BYTES)
        ordinal, value, purpose = FRAME.unpack(record[:48])
        checksum = hashlib.sha256(head + record[:48]).digest()
        _require(ordinal == first + index and math.isfinite(value) and 0 <= value <= 1
                 and record[48:] == checksum, 'tail record order/value/checksum differs')
        # purpose is exactly 32 stored bytes, bound by the original chain.
        # It is intentionally not interpreted as authenticated matcher ancestry.
        head = checksum
        body_hash.update(record)
    trailing = read(1)
    _require(type(trailing) is bytes and len(trailing) <= 1, 'reader violated requested byte bound')
    _require(not trailing, 'complete tail has trailing bytes')
    _require(head.hex() == terminal['head'], 'tail acknowledged chain differs')
    _require(body_hash.hexdigest() == terminal['records_sha256'], 'tail body hash differs')
    return {'schema_version': 1, 'kind': 'engineering-complete-score-tail-semantics',
            'start_sha256': start_sha256, 'terminal_sha256': terminal_sha256,
            'scope': scope, 'owner': owner, 'destination': start['destination'],
            'start_cell': first, 'cells_verified': count, 'bytes_verified': count * RECORD_BYTES,
            'records_sha256': body_hash.hexdigest(), 'head': head.hex(),
            'content_passes': 1, 'purpose_ancestry_verified': False,
            'whole_history_roster_verified': False, 'immutable_storage_verified': False,
            'execution_admission': False, 'scientific_completion': False,
            'capacity_verified': False, 'deletion_authority': False}
