"""Finite SSH archive adapter, independent of historical launch scripts.

Configuration contains endpoint and authentication *paths*, never credentials.
Construction does not open those paths or start a process. Callers must supply
their current admission/guard lease; this adapter grants no run authority.
Payload reservations exclude SSH framing, diagnostics and filesystem overhead.
No retry, remote overwrite recovery, deletion or capacity admission is provided.
Linux sealed memfd and /proc are required for immutable upload snapshots.
"""
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

from tradingagents.research.lifecycle import _immutable, _encode
from . import archive_chunks as archive
from .provenance import sync_directory

BLOCK_BYTES = 32768
STDERR_TAIL_BYTES = 16384


def _positive_finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


class Budget:
    """Shared conservative payload allowance; failed operations are not refunded."""

    def __init__(self, maximum):
        if type(maximum) is not int or maximum < 0:
            raise ValueError('nonnegative integer archive payload budget required')
        self.remaining = maximum

    def reserve(self, size):
        if type(size) is not int or size < 0 or size > self.remaining:
            raise RuntimeError('archive network payload budget exhausted')
        self.remaining -= size


def receive_diagnostic(command, destination, *, expected_bytes, max_seconds,
                       bytes_per_second, lease_callback, receipt_sink=None):
    """Receive exact bytes, retaining a partial file and bounded diagnostic tail.

    Deadline covers child execution and throttling; forced cleanup gets a
    separate ten-second wait. Each child owns a process group so pipe-holding
    descendants receive a kill request during cleanup. Only the direct child
    wait is confirmed here; the outer guard owns descendant cleanup verification.
    A live lease is checked before spawn and during polling.
    """
    if (type(expected_bytes) is not int or not 0 <= expected_bytes <= archive.MAX_BYTES
            or not _positive_finite(max_seconds) or not _positive_finite(bytes_per_second)
            or not callable(lease_callback)):
        raise ValueError('invalid receive bounds or live lease')
    destination = Path(destination)
    receipt = Path(str(destination) + '.transport.json')
    if os.path.lexists(receipt):
        raise FileExistsError(receipt)
    began = time.monotonic(); received = 0; seen = 0; tail = b''
    proc = None; primary = None; cleanup_error = None
    output = destination.open('xb')
    try:
        lease_callback()
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        stdout = proc.stdout.fileno(); stderr = proc.stderr.fileno()
        streams = {stdout, stderr}
        for fd in streams:
            os.set_blocking(fd, False)
        while streams:
            lease_callback()
            elapsed = time.monotonic() - began
            remaining = max_seconds - elapsed
            if remaining <= 0:
                raise TimeoutError('bounded download deadline')
            # Continue draining stderr while stdout is rate-limited.
            delay = max(0., received / bytes_per_second - elapsed)
            watched = streams - {stdout} if delay else streams
            ready, _, _ = select.select(list(watched), [], [],
                                        min(0.1, remaining, delay or 0.1))
            for fd in ready:
                chunk = os.read(fd, 65536 if fd == stderr else
                                min(65536, expected_bytes - received + 1))
                if not chunk:
                    streams.remove(fd)
                    continue
                if fd == stderr:
                    seen += len(chunk); tail = (tail + chunk)[-STDERR_TAIL_BYTES:]
                else:
                    received += len(chunk)
                    if received > expected_bytes:
                        raise ValueError('download size exceeds expected bytes')
                    output.write(chunk)
        remaining = max_seconds - (time.monotonic() - began)
        if remaining <= 0:
            raise TimeoutError('bounded download deadline')
        if proc.wait(timeout=remaining):
            raise RuntimeError('bounded download process failed; see transport receipt')
        if received != expected_bytes:
            raise ValueError('download size shorter than expected bytes')
        lease_callback()
        output.flush(); os.fsync(output.fileno())
    except BaseException as error:
        primary = error

    def kill_group():
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass

    def drain_tail():
        nonlocal seen, tail
        # Preserve one bounded queued tail even after the data/deadline failure.
        # Initial nonblocking setup may itself have been the primary failure.
        os.set_blocking(proc.stderr.fileno(), False)
        try:
            chunk = os.read(proc.stderr.fileno(), 65536)
            seen += len(chunk); tail = (tail + chunk)[-STDERR_TAIL_BYTES:]
        except BlockingIOError:
            pass

    actions = []
    if proc is not None:
        actions.extend((kill_group, lambda: proc.wait(timeout=10), drain_tail,
                        proc.stdout.close, proc.stderr.close))
    actions.append(output.close)
    try:
        archive.io._cleanup(actions)
    except BaseException as error:
        cleanup_error = error
    failure = cleanup_error if cleanup_error is not None else primary
    # Completion is publishable only after every owned cleanup has succeeded.
    try:
        record = {'status': 'failed' if failure is not None else 'complete',
            'error_type': type(failure).__name__ if failure is not None else None,
            'primary_error_type': type(primary).__name__ if primary is not None else None,
            'pid': proc.pid if proc else None,
            'returncode': proc.returncode if proc else None,
            'received_bytes': received, 'expected_bytes': expected_bytes,
            'elapsed_seconds': time.monotonic() - began,
            'stderr_bytes_seen': seen, 'stderr_truncated': seen > len(tail),
            'stderr_tail': tail.decode('utf-8', errors='replace')}
        if receipt_sink is None:_immutable(receipt, record)
        else:receipt_sink(receipt, _encode(record), failure is None)
    except BaseException as error:
        if failure is None:
            raise
        failure.add_note('transport receipt publication failed: ' + repr(error))
    if cleanup_error is not None:
        if primary is not None:
            raise cleanup_error from primary
        raise cleanup_error
    if primary is not None:
        raise primary


class Transport:
    """Caller-configured archive_chunks transport with one-use diagnostics.

    ``connection`` has exactly host, user, port, identity_file and
    known_hosts_file. Absolute authentication paths are passed to SSH without
    opening them here. Host aliases/DNS names only; IPv6 literals are excluded.
    Identity hashes this explicit configuration under a new versioned format;
    it does not silently reinterpret historical smoke-job transport receipts.
    """

    def __init__(self, connection, diagnostics, budget, *, lease_callback,
                 rate_kbit=32768, max_seconds=30, receipt_sink=None):
        if (not isinstance(connection, dict) or set(connection) !=
                {'host', 'user', 'port', 'identity_file', 'known_hosts_file'}):
            raise ValueError('explicit archive connection configuration required')
        connection = dict(connection)
        for field in ('host', 'user'):
            value = connection[field]
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}', value):
                raise ValueError('unsafe archive connection ' + field)
        if type(connection['port']) is not int or not 1 <= connection['port'] <= 65535:
            raise ValueError('archive connection port')
        for field in ('identity_file', 'known_hosts_file'):
            value = connection[field]
            if (not isinstance(value, str) or not value.startswith('/') or len(value) > 4096
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise ValueError('absolute archive authentication path required')
        if (type(rate_kbit) is not int or rate_kbit <= 0 or not _positive_finite(max_seconds)
                or not callable(lease_callback) or not callable(getattr(budget, 'reserve', None))):
            raise ValueError('finite transport bounds, budget and mandatory live lease required')
        self.identity = hashlib.sha256(json.dumps(
            {'format': 'archive-ssh-transport-v1', 'connection': connection},
            sort_keys=True).encode()).hexdigest()
        self.host = connection['user'] + '@' + connection['host']
        opts = ['-i', connection['identity_file'], '-o', 'IdentitiesOnly=yes',
                '-o', 'BatchMode=yes', '-o', 'UserKnownHostsFile=' + connection['known_hosts_file'],
                '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
                '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2']
        self.ssh = ['ssh', '-p', str(connection['port']), *opts, self.host]
        self.scp = ['scp', '-q', '-l', str(rate_kbit), '-P', str(connection['port']), *opts]
        self.rate_bytes = rate_kbit * 1024 // 8
        self.max_seconds = max_seconds
        self.live = lease_callback
        self.budget = budget
        self.diagnostics = Path(diagnostics)
        self.diagnostics.mkdir()
        self.counter = 0
        if receipt_sink is not None:
            if not callable(receipt_sink):raise ValueError("actual receipt sink required")
            self._receipt_sink=receipt_sink

    def remote_path(self, path):
        if not isinstance(path, str) or not re.fullmatch(
                r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}(?:/payload\.bin)?', path):
            raise ValueError('unsafe archive remote member')
        return path

    def next(self, kind):
        path = self.diagnostics / f'{kind}-{self.counter:04d}.bin'
        self.counter += 1
        return path

    def reserve(self, size):
        self.budget.reserve(size)

    def run(self, args):
        self.live()
        receive_diagnostic(args, self.next('command'), expected_bytes=0,
            max_seconds=self.max_seconds, bytes_per_second=self.rate_bytes,
            lease_callback=self.live, **({"receipt_sink":self._receipt_sink} if hasattr(self,"_receipt_sink") else {}))

    def mkdir(self, path):
        self.run([*self.ssh, 'mkdir', self.remote_path(path)])

    def put(self, source, path):
        path = self.remote_path(path); source = Path(source)
        self.live()
        root, descriptor = archive.io._open(source.parent)
        try:
            raw = archive.io._read(descriptor, source.name, archive.MAX_BYTES)
            archive.io._root(root, descriptor)
        finally: archive.io._release(lambda: os.close(descriptor))
        if not raw:
            raise ValueError('positive upload extent required')
        # The pinned Python omits memfd/seal constants. Checked Linux ABI.
        create = ctypes.CDLL(None, use_errno=True).memfd_create
        create.argtypes = [ctypes.c_char_p, ctypes.c_uint]; create.restype = ctypes.c_int
        frozen = create(b'archive-upload', 0x0001 | 0x0002)
        if frozen < 0:
            raise OSError(ctypes.get_errno(), 'memfd_create failed')
        try:
            sent = 0
            while sent < len(raw):
                count = os.write(frozen, raw[sent:])
                if count <= 0: raise OSError('zero upload snapshot write')
                sent += count
            seals = 0x0008 | 0x0004 | 0x0002 | 0x0001
            fcntl.fcntl(frozen, 1033, seals)
            if fcntl.fcntl(frozen, 1034) != seals:
                raise RuntimeError('upload seals differ')
            self.reserve(len(raw))
            self.run([*self.scp, f'/proc/{os.getpid()}/fd/{frozen}', self.host + ':' + path])
        finally: archive.io._release(lambda: os.close(frozen))

    def get(self, path, destination, *, expected_bytes):
        path = self.remote_path(path); destination = Path(destination)
        if os.path.lexists(destination):
            raise FileExistsError(destination)
        if type(expected_bytes) is not int or not 0 < expected_bytes <= archive.MAX_BYTES:
            raise ValueError('archive download extent')
        count = expected_bytes // BLOCK_BYTES + 1
        self.reserve(count * BLOCK_BYTES)
        staging = self.next('get')
        self.live()
        receive_diagnostic([*self.ssh, 'dd', 'if=' + path, 'bs=' + str(BLOCK_BYTES), 'count=' + str(count)],
            staging, expected_bytes=expected_bytes, max_seconds=self.max_seconds,
            bytes_per_second=self.rate_bytes, lease_callback=self.live,
            **({"receipt_sink":self._receipt_sink} if hasattr(self,"_receipt_sink") else {}))
        os.link(staging, destination)
        staging.unlink()
        for directory in (self.diagnostics, destination.parent):
            sync_directory(directory)
