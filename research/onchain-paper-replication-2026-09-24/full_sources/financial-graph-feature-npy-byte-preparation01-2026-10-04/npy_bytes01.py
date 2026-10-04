"""Opaque MCM NPY engineering reader. No numerical decoding or research authority.

Supports the pinned writer's 64-aligned NPY v1/2/3 plain <f4 C-order (N,32)
subset. The local reader retains the current 4 MiB file ceiling; parsing a
larger projected envelope is metadata only. Expected role hashes are caller
assertions, not authenticated Graph/Owner/Run grants. Production always refuses.
"""
import hashlib
import json
import os
import re
import stat
import struct
import time
from dataclasses import dataclass
from pathlib import Path
import owned_io as IO

FILE_LIMIT = 4 * 1024**2
READ_LIMIT = 1024**2
HEADER_LIMIT = 4096
RAW_LIMIT = 2_309_992_448
FLOOR = 10 * 1024**3
SECONDS = 120
ROLES = ('source_sha256', 'component_manifest_sha256', 'context_sha256',
         'ordered_nodes_sha256', 'dictionary_sha256', 'sample_sha256',
         'feature_receipt_sha256', 'graph_sha256')
HEX = re.compile(r'[0-9a-f]{64}\Z')
FIELD = re.compile(r" *(['\"])(descr|fortran_order|shape)\1 *: *(?:('<f4>'|\"<f4>\")|(.+))")


def require(ok, message):
    if not ok: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Envelope:
    version: tuple
    literal_header: bytes  # complete magic/version/length/dict/padding/newline
    rows: int
    payload_offset: int
    payload_bytes: int
    dtype: str = '<f4'
    columns: int = 32
    order: str = 'C'


def parse_header(raw):
    """Parse a complete bounded header, never a payload or arbitrary expression."""
    require(type(raw) is bytes and 10 <= len(raw) <= HEADER_LIMIT, 'header byte bound/type')
    require(raw[:6] == b'\x93NUMPY', 'NPY magic')
    version = tuple(raw[6:8])
    require(version in ((1, 0), (2, 0), (3, 0)), 'NPY version')
    prefix = 10 if version == (1, 0) else 12
    require(len(raw) >= prefix, 'length prefix truncated')
    count = int.from_bytes(raw[8:prefix], 'little')
    require(prefix + count == len(raw) and len(raw) % 64 == 0, 'header extent/alignment')
    header = raw[prefix:]
    require(header.endswith(b'\n') and b'\n' not in header[:-1] and b'\r' not in header, 'header newline')
    # This plain dtype/shape subset needs only ASCII even for UTF-8 version 3.
    text = header[:-1].decode('ascii')
    require(text.startswith('{'), 'dictionary start')
    end = text.find('}')
    require(end > 0 and text[end + 1:] and set(text[end + 1:]) == {' '}, 'space-only padding')
    body = text[1:end]
    # A deliberately small grammar, not eval/literal_eval. Whitespace inside the
    # literal is ASCII space only. Key order is arbitrary; duplicates forbidden.
    token = re.compile(r" *(['\"])(descr|fortran_order|shape)\1 *: *(('[^']*'|\"[^\"]*\")|False|True|\([0-9]+ *, *[0-9]+ *,? *\)) *(,|$)")
    fields = {}; pos = 0
    while pos < len(body):
        if body[pos:].strip(' ') == '': break
        match = token.match(body, pos)
        require(match is not None and match.end() > pos, 'restricted header grammar')
        key, value = match.group(2), match.group(3)
        require(key not in fields, 'duplicate header key')
        fields[key] = value; pos = match.end()
    require(set(fields) == {'descr', 'fortran_order', 'shape'}, 'exact header keys')
    require(fields['descr'] in ("'<f4'", '"<f4"') and fields['fortran_order'] == 'False', 'little float32/C-order required')
    shape = re.fullmatch(r'\(([0-9]+) *, *([0-9]+) *,? *\)', fields['shape'])
    require(shape is not None, 'two-dimensional shape')
    require(all(len(x) <= 10 and (x == '0' or not x.startswith('0')) for x in shape.groups()), 'canonical bounded dimensions')
    n, width = map(int, shape.groups())
    require(n > 0 and width == 32 and n * 128 <= RAW_LIMIT, 'MCM shape/payload bound')
    return Envelope(version, raw, n, len(raw), n * 128)


def expected(raw):
    """Require immutable canonical bytes. Role hashes remain untrusted assertions."""
    require(type(raw) is bytes and len(raw) <= 8192, 'immutable expected metadata bytes required')
    value = json.loads(raw)
    require(type(value) is dict and canonical(value) == raw, 'canonical expected metadata')
    require(set(value) == set(ROLES) | {'member', 'rows', 'columns', 'dtype', 'order', 'file_bytes', 'file_sha256', 'header_sha256', 'payload_sha256'}, 'expected fields')
    require(value['member'] == 'array-000000.npy' and type(value['member']) is str, 'MCM member')
    require(type(value['rows']) is int and 0 < value['rows'] <= RAW_LIMIT // 128, 'expected rows')
    require(type(value['columns']) is int and value['columns'] == 32, 'expected columns')
    require(value['dtype'] == '<f4' and type(value['dtype']) is str and value['order'] == 'C' and type(value['order']) is str, 'expected dtype/order')
    require(type(value['file_bytes']) is int and 0 < value['file_bytes'] <= RAW_LIMIT + HEADER_LIMIT, 'expected extent')
    for key in ROLES + ('file_sha256', 'header_sha256', 'payload_sha256'):
        require(type(value[key]) is str and HEX.fullmatch(value[key]) is not None, 'expected hash ' + key)
    return value


def fingerprint(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns, s.st_blocks)


class Cursor:
    """Single-use sequential aligned reader of an existing tiny opaque file.

    No sink, allocation, reservation, recycling or publication. Each successful
    finish is a sampled byte proof, not continuous filesystem immunity. Deadline
    and disk floor are sampled and do not interrupt blocking calls.
    """
    def __init__(self, path, metadata):
        self.fd = None; self.state = 'FAILED'; self.position = 0
        self._metadata = metadata; self._pin = sha(metadata) if type(metadata) is bytes else None
        self.path = Path(path); self.deadline = time.monotonic() + SECONDS
        self.spec = expected(metadata)
        require(self.path.is_absolute() and self.path.resolve(strict=True) == self.path, 'canonical absolute path required')
        require(self.path.name == self.spec['member'], 'member path differs')
        self.initial = fingerprint(self.path.lstat())
        s = self.path.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size == self.spec['file_bytes'] <= FILE_LIMIT, 'regular singleton local file limit')
        self._sample()
        try:
            self.fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
            require(fingerprint(os.fstat(self.fd)) == self.initial, 'opened inode differs')
            prefix = self._exact(8)
            require(prefix[:6] == b'\x93NUMPY', 'NPY magic')
            v = tuple(prefix[6:]); require(v in ((1, 0), (2, 0), (3, 0)), 'NPY version')
            count_raw = self._exact(2 if v == (1, 0) else 4)
            count = int.from_bytes(count_raw, 'little')
            require(0 < count <= HEADER_LIMIT - len(prefix) - len(count_raw), 'header allocation bound')
            self.envelope = parse_header(prefix + count_raw + self._exact(count))
            e = self.envelope
            require(e.rows == self.spec['rows'] and e.payload_offset + e.payload_bytes == s.st_size, 'header/body/expected extent')
            require(sha(e.literal_header) == self.spec['header_sha256'], 'literal header hash')
            self._whole = hashlib.sha256(e.literal_header); self._raw = hashlib.sha256()
            self.state = 'OPEN'; self._sample()
        except BaseException as error:
            self._fail(error); raise

    def _exact(self, size):
        data = os.read(self.fd, size)
        require(type(data) is bytes and len(data) == size, 'short read')
        return data

    def _sample(self):
        require(time.monotonic() <= self.deadline, 'sampled deadline')
        require(type(self._metadata) is bytes and sha(self._metadata) == self._pin and canonical(self.spec) == self._metadata, 'expected metadata changed')
        require(self.path.resolve(strict=True) == self.path and fingerprint(self.path.lstat()) == self.initial, 'current canonical file changed')
        if self.fd is not None: require(fingerprint(os.fstat(self.fd)) == self.initial, 'held file changed')
        disk = os.statvfs(self.path.parent)
        require(disk.f_bavail * disk.f_frsize >= FLOOR, 'sampled 10 GiB floor')

    def _close(self, primary=None):
        fd, self.fd = self.fd, None
        if fd is not None: IO._cleanup((lambda: os.close(fd),), primary=primary)

    def _fail(self, error):
        self.state = 'FAILED'; self._close(error)

    def read(self, offset, size):
        try:
            require(self.state == 'OPEN', 'terminal cursor')
            self._sample()
            require(type(offset) is int and offset == self.position and type(size) is int and 0 < size <= READ_LIMIT and size % 4 == 0, 'sequential aligned read')
            require(size <= self.envelope.payload_bytes - self.position, 'payload extent')
            data = self._exact(size)
            self._whole.update(data); self._raw.update(data); self.position += size
            self._sample()
            return data
        except BaseException as error:
            self._fail(error); raise

    def finish(self):
        try:
            require(self.state == 'OPEN', 'terminal cursor')
            self._sample()
            require(self.position == self.envelope.payload_bytes and os.read(self.fd, 1) == b'', 'complete payload/exact EOF')
            whole, raw = self._whole.hexdigest(), self._raw.hexdigest()
            require(whole == self.spec['file_sha256'] and raw == self.spec['payload_sha256'], 'whole/raw hash')
            self._close()
            # No owned descriptor cleanup follows this currentness sample.
            self._sample()
            proof = canonical({'schema_version': 1, 'kind': 'opaque-npy-member-byte-proof',
                'expected_sha256': self._pin, 'header_hex': self.envelope.literal_header.hex(),
                'header_sha256': sha(self.envelope.literal_header), 'payload_offset': self.envelope.payload_offset,
                'payload_bytes': self.position, 'payload_sha256': raw, 'file_sha256': whole,
                'file_bytes': self.spec['file_bytes'], 'production_authority': False})
            self.state = 'FINISHED'
            return proof
        except BaseException as error:
            self._fail(error); raise

    def abort(self):
        self.state = 'FAILED'; self._close()


def production(*args, **kwargs):
    raise PermissionError('No genuine graph ancestry, registered NPY role, shared reservation, typed transport/recovery, retirement or native capacity adapter is installed; Source339 unsupported')
