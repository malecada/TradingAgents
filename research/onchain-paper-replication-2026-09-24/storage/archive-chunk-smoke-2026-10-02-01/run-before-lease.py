"""One exclusive guarded synthetic external archive check; never a retry runner."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tradingagents.research.onchain_replication import archive_chunks as archive
from tradingagents.research.onchain_replication.resources import guarded_run, assert_guarded_worker
from tradingagents.research.lifecycle import _immutable

BASE = ROOT / 'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-28-09/transfer.py'
spec = importlib.util.spec_from_file_location('retained_archive_transport', BASE)
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
GIB = 1024**3
CONNECTION = dict(host='u676273.your-storagebox.de', user='u676273', port=23,
    public_key_path='/home/malecada/.ssh/id_ed25519_storagebox_u676273.pub')
REMOTE = 'paper-replication-chunk-smoke-20261002-01'


class Budget:
    def __init__(self, maximum): self.remaining = maximum
    def reserve(self, size):
        if type(size) is not int or size < 0 or size > self.remaining:
            raise RuntimeError('archive network payload budget exhausted')
        self.remaining -= size


class Transport(base.Transport):
    def __init__(self, diagnostics, budget):
        super().__init__(CONNECTION, rate=32768, maximum_payload_bytes=0)
        self.identity = hashlib.sha256(json.dumps(CONNECTION, sort_keys=True).encode()).hexdigest()
        self.diagnostics = Path(diagnostics); self.diagnostics.mkdir()
        self.budget = budget; self.counter = 0
    def reserve(self, size): self.budget.reserve(size)
    def remote_path(self, path):
        if not isinstance(path, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}(?:/payload\.bin)?', path):
            raise ValueError('unsafe archive remote member')
        return path
    def next(self, kind):
        path = self.diagnostics / f'{kind}-{self.counter:04d}.bin'
        self.counter += 1
        return path
    def run(self, args):
        # Commands must be silent; stderr is continuously drained to a bounded tail.
        base.receive_diagnostic(args, self.next('command'), expected_bytes=0,
            max_seconds=30, bytes_per_second=self.rate_bytes)
    def get(self, path, destination, *, expected_bytes):
        path = self.remote_path(path); destination = Path(destination)
        if os.path.lexists(destination): raise FileExistsError(destination)
        if type(expected_bytes) is not int or not 0 < expected_bytes <= archive.MAX_BYTES:
            raise ValueError('archive download extent')
        count = expected_bytes // 32768 + 1
        self.reserve(count * 32768)
        staging = self.next('get')
        base.receive_diagnostic([*self.ssh, 'dd', 'if=' + path, 'bs=32768', 'count=' + str(count)],
            staging, expected_bytes=expected_bytes, max_seconds=30, bytes_per_second=self.rate_bytes)
        os.link(staging, destination)  # Exclusive destination; interrupted dual links fail closed.
        staging.unlink()
        for directory in (self.diagnostics, destination.parent): base.sync_directory(directory)


def lease():
    raw = (HERE / 'bindings.json').read_bytes()
    if len(sys.argv) != 3 or hashlib.sha256(raw).hexdigest() != sys.argv[2]:
        raise ValueError('archive binding inventory changed')
    bindings = json.loads(raw)
    for name, expected in bindings.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('archive source/contract binding changed: ' + name)
    assert_guarded_worker(HERE / 'guard01', sys.orig_argv, required_paths=[ROOT],
        wall_seconds=180, memory_max_bytes=512*1024**2, memory_high_bytes=384*1024**2,
        disk_floor_bytes=10*GIB)


def worker():
    lease()
    payload = bytes(range(256)) * 4096
    expected = hashlib.sha256(payload).hexdigest()
    scope = hashlib.sha256((HERE / 'CONTRACT.md').read_bytes()).hexdigest()
    _immutable(HERE / 'intent.json', {'remote': REMOTE, 'bytes': len(payload), 'sha256': expected,
        'scope': scope, 'no_financial_computation': True, 'retry': False})
    try:
        source = HERE / 'synthetic.bin'
        with source.open('xb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        budget = Budget(4*1024**2)
        transport = Transport(HERE / 'transport01', budget)
        reference = archive.preserve(source=source, attempt=HERE / 'copy01', expected_sha256=expected,
            expected_bytes=len(payload), scope=scope, remote=REMOTE, transport=transport,
            lease=lease, free_floor_bytes=10*GIB)
        fresh = Transport(HERE / 'transport02', budget)
        recovered = archive.retrieve(HERE / 'copy01', receipt_sha256=reference, attempt=HERE / 'read01',
            transport=fresh, lease=lease, free_floor_bytes=10*GIB)
        lease()
        if source.read_bytes() != payload or recovered.read_bytes() != payload:
            raise ValueError('external synthetic recovery differs')
        _immutable(HERE / 'complete.json', {'status': 'complete', 'bytes': len(payload),
            'sha256': expected, 'archive_receipt_sha256': reference, 'remote': REMOTE,
            'reserved_payload_bytes': 4*1024**2-budget.remaining, 'sources_preserved': True,
            'fresh_transport_recovery': True, 'no_eviction_or_empirical_admission': True})
    except BaseException as error:
        _immutable(HERE / 'failed.json', {'error_type': type(error).__name__, 'retry': False})
        raise


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker': worker()
    elif sys.argv[1:]: raise ValueError('unexpected arguments')
    else:
        binding_path = HERE / 'bindings.json'
        raw = binding_path.read_bytes()
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + str(binding_path.relative_to(ROOT))], cwd=ROOT)
        if raw != committed: raise ValueError('archive bindings are not the committed gate')
        for name, expected in json.loads(raw).items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise ValueError('prelaunch archive binding changed: ' + name)
        binding_hash = hashlib.sha256(raw).hexdigest()
        result = guarded_run([str(ROOT / '.venv/bin/python'), '-B', str(Path(__file__).resolve()), '--worker', binding_hash],
            cwd=ROOT, receipt_dir=HERE / 'guard01', memory_max_bytes=512*1024**2,
            memory_high_bytes=384*1024**2, memory_swap_max_bytes=0,
            reserve_bytes=3*GIB, start_reserve_bytes=int(3.5*GIB), disk_paths=[ROOT],
            disk_floor_bytes=10*GIB, wall_seconds=180)
        print(json.dumps({k: result.get(k) for k in ('phase', 'child_exit_code', 'cleanup_verified', 'limit_reason')}))
        sys.exit(0 if result['phase'] == 'complete' and result['cleanup_verified'] and result['child_exit_code'] == 0 else 1)
