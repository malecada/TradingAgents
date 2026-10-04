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
        raise PermissionError('UNAVAILABLE: ordinary-path inode writer exclusion is not enforced; stat fingerprints and repeated hashes are insufficient')
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
            self._sample()
            # Rejoin actual bounded bytes after the original cursor close; stat
            # timestamps alone can collide within one filesystem clock tick.
            verify_fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
            try:
                require(fingerprint(os.fstat(verify_fd)) == self.initial, 'verification inode changed')
                final_hash = hashlib.sha256()
                remaining = self.spec['file_bytes']
                while remaining:
                    block = os.read(verify_fd, min(READ_LIMIT, remaining))
                    require(type(block) is bytes and len(block) == min(READ_LIMIT, remaining), 'final short read')
                    final_hash.update(block); remaining -= len(block)
                require(os.read(verify_fd, 1) == b'' and final_hash.hexdigest() == whole, 'post-cursor-cleanup bytes changed')
            finally:
                IO._cleanup((lambda: os.close(verify_fd),))
            self._sample()
            # This is a sampled byte proof. A subsequent adversarial mutation
            # within unresolved filesystem timestamp granularity is not excluded.

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

# Explicit separate engineering domain. This does NOT capture an ordinary file,
# implement graph publication, or turn a copy into the current original member.
import fcntl
import threading

# Linux UAPI values authenticated from original local linux/fcntl.h and
# asm-generic/fcntl.h. The pinned Python exposes fcntl(), but omits seal names.
# No seal is installed here. Unsupported kernel/ioctl always refuses.
import sys
F_ADD_SEALS=1033
F_GET_SEALS=1034
F_SEAL_SEAL=1
F_SEAL_SHRINK=2
F_SEAL_GROW=4
F_SEAL_WRITE=8
REQUIRED_SEALS = F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL


def sealed_identity(fd):
    """Kernel exclusion applies to this inode and every fd/mapping alias.

    F_SEAL_WRITE cannot be installed while a writable shared mapping exists;
    once installed, write/pwrite/truncate/shared writable mmap refuse. Require
    SEAL_SEAL too. Named ordinary component files are deliberately unsupported.
    """
    require(sys.platform == 'linux', 'UNAVAILABLE: Linux kernel seal ABI required')
    require(type(fd) is int and fd >= 0, 'actual borrowed descriptor required')
    s = os.fstat(fd)
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 0 and
            s.st_uid == os.getuid() and 0 < s.st_size <= FILE_LIMIT,
            'anonymous owned sealed-inode extent/type required')
    seals = fcntl.fcntl(fd, F_GET_SEALS)
    require((seals & REQUIRED_SEALS) == REQUIRED_SEALS,
            'kernel WRITE/GROW/SHRINK/SEAL exclusion required before reading')
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_nlink, s.st_size)


class SealedCursor(Cursor):
    """Opaque bytes of an already kernel-sealed original anonymous inode.

    No file copy/seal installation is performed here. The caller must supply an
    already immutable inode; current ordinary graph files cannot qualify. Only
    the owned duplicate's lifetime supports proof access, from open to release.
    finish does NOT close it. consume runs callbacks while exclusion remains;
    release invalidates proof access BEFORE attempting close, including failure.
    Returned proof bytes are historical evidence after release, never current
    original-path or genuine scientific authority. All role hashes are untrusted.
    """
    def __init__(self, fd, metadata, floor_root):
        self.fd = None; self.state = 'FAILED'; self.position = 0
        self._metadata = metadata; self._pin = sha(metadata) if type(metadata) is bytes else None
        self.spec = expected(metadata); self.deadline = time.monotonic() + SECONDS
        self.thread = threading.get_ident(); self._busy = False; self._offset = 0
        self._proof = None; self._proof_pin = None
        self.floor_root = Path(floor_root)
        require(self.floor_root.is_absolute() and self.floor_root.resolve(strict=True) == self.floor_root,
                'canonical engineering floor root')
        ds = self.floor_root.lstat()
        require(stat.S_ISDIR(ds.st_mode) and ds.st_uid == os.getuid(), 'owned floor directory')
        self._floor_identity = (ds.st_dev, ds.st_ino, ds.st_mode, ds.st_uid)
        self.initial = sealed_identity(fd)  # No owned resource yet, no body read.
        require(self.initial[-1] == self.spec['file_bytes'], 'sealed original expected extent')
        try:
            self.fd = os.dup(fd); os.set_inheritable(self.fd, False)
            require(sealed_identity(self.fd) == self.initial, 'duplicate actual original inode join')
            self.state = 'OPEN'; self._sample()
            prefix = self._exact(8)
            require(prefix[:6] == b'\x93NUMPY', 'NPY magic')
            v = tuple(prefix[6:]); require(v in ((1, 0), (2, 0), (3, 0)), 'NPY version')
            count_raw = self._exact(2 if v == (1, 0) else 4)
            count = int.from_bytes(count_raw, 'little')
            require(0 < count <= HEADER_LIMIT - len(prefix) - len(count_raw), 'header allocation bound')
            self.envelope = parse_header(prefix + count_raw + self._exact(count))
            e = self.envelope
            require(e.rows == self.spec['rows'] and e.payload_offset + e.payload_bytes == self.initial[-1],
                    'sealed header/body/expected extent')
            require(sha(e.literal_header) == self.spec['header_sha256'], 'literal header hash')
            self._whole = hashlib.sha256(e.literal_header); self._raw = hashlib.sha256()
            self._sample()
        except BaseException as error:
            self._fail(error); raise

    def _exact(self, size):
        require(type(size) is int and 0 < size <= READ_LIMIT, 'bounded sealed read')
        data = os.pread(self.fd, size, self._offset)
        require(type(data) is bytes and len(data) == size, 'sealed short read')
        self._offset += size
        return data

    def _sample(self):
        require(self.state in ('OPEN', 'PROVEN') and self.fd is not None and
                threading.get_ident() == self.thread, 'inactive sealed proof lifetime/thread')
        require(time.monotonic() <= self.deadline, 'sampled deadline')
        require(type(self._metadata) is bytes and sha(self._metadata) == self._pin and
                canonical(self.spec) == self._metadata, 'expected metadata changed')
        require(sealed_identity(self.fd) == self.initial, 'sealed original inode identity changed')
        s = self.floor_root.lstat()
        require(self.floor_root.resolve(strict=True) == self.floor_root and
                (s.st_dev, s.st_ino, s.st_mode, s.st_uid) == self._floor_identity, 'floor root changed')
        disk = os.statvfs(self.floor_root)
        require(disk.f_bavail * disk.f_frsize >= FLOOR, 'sampled 10 GiB floor')
        if self.state == 'PROVEN':
            require(type(self._proof) is bytes and sha(self._proof) == self._proof_pin, 'proof changed')

    def finish(self):
        try:
            require(self.state == 'OPEN' and not self._busy, 'terminal/recursive cursor')
            self._sample()
            require(self.position == self.envelope.payload_bytes and
                    os.pread(self.fd, 1, self._offset) == b'', 'complete payload/exact EOF')
            whole, raw = self._whole.hexdigest(), self._raw.hexdigest()
            require(whole == self.spec['file_sha256'] and raw == self.spec['payload_sha256'], 'whole/raw hash')
            self._proof = canonical({'schema_version': 1, 'kind': 'kernel-sealed-anonymous-npy-inode-proof',
                'expected_sha256': self._pin, 'header_hex': self.envelope.literal_header.hex(),
                'header_sha256': sha(self.envelope.literal_header), 'payload_offset': self.envelope.payload_offset,
                'payload_bytes': self.position, 'payload_sha256': raw, 'file_sha256': whole,
                'file_bytes': self.spec['file_bytes'], 'sealed_inode': list(self.initial),
                'required_seals': REQUIRED_SEALS, 'lifetime': 'owned-sealed-descriptor-until-release',
                'original_component_path_current': False, 'production_authority': False})
            self._proof_pin = sha(self._proof); self.state = 'PROVEN'; self._sample()
            # No descriptor cleanup occurs here. Exclusion and the original inode
            # remain owned while the proof is consumed; release is explicit.
            return self._proof
        except BaseException as error:
            self._fail(error); raise

    def consume(self, callback):
        try:
            require(self.state == 'PROVEN' and not self._busy and callable(callback), 'live proof callback')
            self._sample(); self._busy = True
            try:result = callback(self._proof)
            finally:self._busy = False
            self._sample();return result
        except BaseException as error:
            self._fail(error); raise

    def release(self):
        # Revoke before the actual close, so its hook/failure cannot consume proof.
        require(not self._busy, 'cannot release during consumption')
        self.state = 'RELEASED'; self._proof = None; self._proof_pin = None
        self._close(sys.exception())

    def abort(self):
        self.state = 'FAILED'; self._proof = None; self._proof_pin = None
        self._close(sys.exception())


from contextlib import contextmanager


@contextmanager
def sealed_cursor(fd, metadata, floor_root):
    """Mandatory structured lifetime for any future admitted consumer.

    Revocation precedes close even when the body raises. The original active
    exception is passed explicitly to the unchanged first-fatal cleanup helper.
    Escaped proof bytes after context exit are historical sealed-inode evidence.
    """
    cursor = SealedCursor(fd, metadata, floor_root)
    try:
        yield cursor
    finally:
        primary = sys.exception()
        cursor.state = 'RELEASED'; cursor._proof = None; cursor._proof_pin = None
        cursor._close(primary)
