"""Maintained archive adapter: temporary files and local Python children only."""
import importlib
import hashlib
import json
from pathlib import Path
import sys
import time

import pytest


@pytest.fixture
def module():
    return importlib.import_module('tradingagents.research.onchain_replication.archive_transport')


def connection():
    return dict(host='archive.invalid', user='synthetic', port=23,
                identity_file='/nonexistent/synthetic-key',
                known_hosts_file='/nonexistent/synthetic-known-hosts')


def adapter(module, tmp_path, **kwargs):
    return module.Transport(connection(), tmp_path / 'diagnostics',
                            kwargs.pop('budget', module.Budget(100000)),
                            lease_callback=kwargs.pop('lease_callback', lambda: None), **kwargs)


def child(code):
    return [sys.executable, '-B', '-c', code]


def test_exact_read_is_exclusive_and_reserves_remote_block(module, tmp_path):
    transport = adapter(module, tmp_path)
    transport.ssh = child('import sys;sys.stdout.buffer.write(b"readback")')
    destination = tmp_path / 'result'
    transport.get('object/payload.bin', destination, expected_bytes=8)
    assert destination.read_bytes() == b'readback'
    assert destination.stat().st_nlink == 1
    assert transport.budget.remaining == 67232
    receipt = json.loads((tmp_path / 'diagnostics/get-0000.bin.transport.json').read_text())
    assert receipt['status'] == 'complete' and receipt['received_bytes'] == 8
    with pytest.raises(FileExistsError):
        transport.get('object/payload.bin', destination, expected_bytes=8)


@pytest.mark.parametrize('code,expected,error', [
    ('print("too much content")', 2, ValueError),
    ('print("x",end="")', 8, ValueError),
    ('import sys;sys.exit(7)', 8, RuntimeError),
])
def test_failed_read_retains_diagnostic_and_charge(module, tmp_path, code, expected, error):
    transport = adapter(module, tmp_path)
    transport.ssh = child(code)
    with pytest.raises(error):
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=expected)
    assert not (tmp_path / 'result').exists()
    assert transport.budget.remaining == 67232
    receipt = json.loads((tmp_path / 'diagnostics/get-0000.bin.transport.json').read_text())
    assert receipt['status'] == 'failed'
    assert receipt['received_bytes'] <= expected + 1


def test_upload_snapshot_cannot_grow_or_be_written(module, tmp_path):
    source = tmp_path / 'source'; source.write_bytes(b'original')
    uploaded = tmp_path / 'uploaded'
    sealed = tmp_path / 'sealed'
    class GrowingBudget(module.Budget):
        def reserve(self, size):
            super().reserve(size)
            source.write_bytes(b'replacement larger than reserved extent')
    transport = adapter(module, tmp_path, budget=GrowingBudget(100000))
    transport.scp = child(
        'from pathlib import Path;import sys;'
        f'Path({str(uploaded)!r}).write_bytes(Path(sys.argv[-2]).read_bytes());'
        '\ntry:\n open(sys.argv[-2],"wb").write(b"bad")'
        f'\nexcept PermissionError:\n Path({str(sealed)!r}).touch()')
    transport.put(source, 'object/payload.bin')
    assert uploaded.read_bytes() == b'original'
    assert sealed.exists()
    assert transport.budget.remaining == 99992


def test_revoked_lease_prevents_upload_after_mkdir(module, tmp_path):
    revoked = False
    def live():
        if revoked: raise RuntimeError('lease revoked')
    transport = adapter(module, tmp_path, lease_callback=live)
    transport.ssh = child('pass')
    transport.mkdir('object')
    revoked = True
    sentinel = tmp_path / 'started'
    transport.scp = child(f'from pathlib import Path;Path({str(sentinel)!r}).touch()')
    source = tmp_path / 'source'; source.write_bytes(b'payload')
    with pytest.raises(RuntimeError, match='lease revoked'):
        transport.put(source, 'object/payload.bin')
    assert not sentinel.exists()


def test_deadline_stops_child_and_preserves_receipt(module, tmp_path):
    transport = adapter(module, tmp_path, max_seconds=0.2)
    transport.ssh = child('import time;time.sleep(10)')
    began = time.monotonic()
    with pytest.raises(TimeoutError):
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=8)
    assert time.monotonic() - began < 3
    receipt = json.loads((tmp_path / 'diagnostics/get-0000.bin.transport.json').read_text())
    assert receipt['returncode'] is not None and receipt['error_type'] == 'TimeoutError'


def test_stderr_is_drained_and_tail_bounded(module, tmp_path):
    transport = adapter(module, tmp_path)
    transport.ssh = child('import sys;sys.stderr.buffer.write(b"x"*200000+b"END");sys.stdout.buffer.write(b"ok")')
    transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=2)
    receipt = json.loads((tmp_path / 'diagnostics/get-0000.bin.transport.json').read_text())
    assert receipt['stderr_bytes_seen'] == 200003
    assert receipt['stderr_truncated'] is True
    assert len(receipt['stderr_tail']) == 16384
    assert receipt['stderr_tail'].endswith('END')


def test_budget_exhaustion_never_starts_receiver(module, tmp_path):
    transport = adapter(module, tmp_path, budget=module.Budget(32767))
    sentinel = tmp_path / 'started'
    transport.ssh = child(f'from pathlib import Path;Path({str(sentinel)!r}).touch()')
    with pytest.raises(RuntimeError):
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=8)
    assert not sentinel.exists()
    assert list((tmp_path / 'diagnostics').iterdir()) == []


def test_unsafe_remote_members_refused_before_process(module, tmp_path):
    transport = adapter(module, tmp_path)
    for name in ('../escape', '/absolute', 'object/payload.bin;bad', 'object//payload.bin'):
        with pytest.raises(ValueError): transport.remote_path(name)


@pytest.mark.parametrize('field,value', [('host','-option'), ('user','x;y'), ('port',True), ('port',0)])
def test_connection_rejects_shell_and_option_injection(module, tmp_path, field, value):
    config = connection(); config[field] = value
    with pytest.raises(ValueError):
        module.Transport(config, tmp_path / 'diagnostics', module.Budget(100000), lease_callback=lambda: None)


@pytest.mark.parametrize('maximum', [-1, True, float('inf')])
def test_budget_requires_nonnegative_integer(module, maximum):
    with pytest.raises(ValueError): module.Budget(maximum)


@pytest.mark.parametrize('bound', [0, float('inf'), float('nan'), True])
def test_receiver_refuses_nonfinite_or_nonpositive_deadline(module, tmp_path, bound):
    with pytest.raises(ValueError): adapter(module, tmp_path, max_seconds=bound)


def test_fresh_instance_identity_is_explicit_and_stable(module, tmp_path):
    first = adapter(module, tmp_path)
    second = module.Transport(connection(), tmp_path / 'fresh', module.Budget(100000), lease_callback=lambda: None)
    assert second.identity == first.identity
    config = connection(); config['host'] = 'different.invalid'
    other = module.Transport(config, tmp_path / 'other', module.Budget(100000), lease_callback=lambda: None)
    assert other.identity != first.identity
    assert '-o' in first.ssh and 'StrictHostKeyChecking=yes' in first.ssh


def test_live_revocation_during_read_kills_child(module, tmp_path):
    started = tmp_path / 'started'
    def live():
        if started.exists(): raise RuntimeError('lease revoked during receive')
    transport = adapter(module, tmp_path, lease_callback=live)
    transport.ssh = child(f'from pathlib import Path;import time;Path({str(started)!r}).touch();time.sleep(10)')
    with pytest.raises(RuntimeError, match='lease revoked during receive'):
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=8)
    receipt = json.loads((tmp_path / 'diagnostics/get-0000.bin.transport.json').read_text())
    assert receipt['returncode'] is not None
    assert receipt['status'] == 'failed'
    assert not (tmp_path / 'result').exists()


def test_real_archive_roundtrip_through_local_children(module, tmp_path):
    from tradingagents.research.onchain_replication import archive_chunks
    remote = tmp_path / 'remote'; remote.mkdir()
    source = tmp_path / 'source'; source.write_bytes(b'immutable archive payload')
    budget = module.Budget(100000)
    def local_transport(name):
        transport = module.Transport(connection(), tmp_path / name, budget, lease_callback=lambda: None)
        transport.ssh = child(
            'from pathlib import Path;import sys;'
            f'root=Path({str(remote)!r});'
            '\nif sys.argv[1]=="mkdir": (root/sys.argv[2]).mkdir()'
            '\nelse: sys.stdout.buffer.write((root/sys.argv[2].removeprefix("if=")).read_bytes())')
        transport.scp = child(
            'from pathlib import Path;import sys;'
            f'root=Path({str(remote)!r});'
            '(root/sys.argv[-1].split(":",1)[1]).write_bytes(Path(sys.argv[-2]).read_bytes())')
        return transport
    transport = local_transport('first')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    reference = archive_chunks.preserve(source=source, attempt=tmp_path / 'copy',
        expected_sha256=digest, expected_bytes=25, scope='0'*64, remote='object',
        transport=transport, lease=lambda: None, free_floor_bytes=0)
    restored = archive_chunks.retrieve(tmp_path / 'copy', receipt_sha256=reference,
        attempt=tmp_path / 'read', transport=local_transport('fresh'),
        lease=lambda: None, free_floor_bytes=0)
    assert restored.read_bytes() == b'immutable archive payload'
    assert source.read_bytes() == b'immutable archive payload'
    assert budget.remaining == 100000 - 25 - 2*32768
    with pytest.raises(RuntimeError): transport.mkdir('object')
    assert (remote / 'object/payload.bin').read_bytes() == b'immutable archive payload'


@pytest.mark.parametrize('target', ['kill', 'wait', 'stdout', 'stderr', 'output'])
@pytest.mark.parametrize('primary', [False, True])
def test_receiver_cleanup_is_fatal_one_shot_and_preserves_primary(
        module, tmp_path, monkeypatch, target, primary):
    transport = adapter(module, tmp_path)
    transport.ssh = child('import sys;sys.stdout.buffer.write(b"excess" if sys.argv[-1]=="count=1" else b"ok")'
                          if primary else 'import sys;sys.stdout.buffer.write(b"ok")')
    calls = []
    original_popen = module.subprocess.Popen
    original_kill = module.os.killpg
    original_open = Path.open
    stage = tmp_path / 'diagnostics/get-0000.bin'
    class Stream:
        def __init__(self, stream, name): self.stream = stream; self.name = name
        def __getattr__(self, name): return getattr(self.stream, name)
        def __enter__(self): return self
        def __exit__(self, *args): self.close()
        def close(self):
            calls.append(self.name)
            self.stream.close()
            if self.name == target: raise OSError('uncertain ' + self.name)
    def popen(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        proc.stdout = Stream(proc.stdout, 'stdout')
        proc.stderr = Stream(proc.stderr, 'stderr')
        wait = proc.wait
        def waiting(*args, **kwargs):
            result = wait(*args, **kwargs)
            if kwargs.get('timeout') == 10:
                calls.append('wait')
                if target == 'wait': raise OSError('uncertain wait')
            return result
        proc.wait = waiting
        return proc
    def kill(*args):
        calls.append('kill')
        try: original_kill(*args)
        except ProcessLookupError: pass
        if target == 'kill': raise OSError('uncertain kill')
    def opened(path, *args, **kwargs):
        stream = original_open(path, *args, **kwargs)
        return Stream(stream, 'output') if path == stage else stream
    monkeypatch.setattr(module.subprocess, 'Popen', popen)
    monkeypatch.setattr(module.os, 'killpg', kill)
    monkeypatch.setattr(Path, 'open', opened)
    with pytest.raises(module.archive.io.CleanupFailure) as caught:
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=2)
    assert sorted(calls) == sorted(['kill', 'wait', 'stdout', 'stderr', 'output'])
    if primary: assert isinstance(caught.value.__cause__, ValueError)
    receipt = json.loads(Path(str(stage) + '.transport.json').read_text())
    assert receipt['status'] == 'failed'
    assert receipt['error_type'] == 'CleanupFailure'
    assert not (tmp_path / 'result').exists()


@pytest.mark.parametrize('target', ['directory', 'memfd'])
@pytest.mark.parametrize('primary', [False, True])
def test_upload_close_uncertainty_is_fatal_and_primary_aware(
        module, tmp_path, monkeypatch, target, primary):
    transport = adapter(module, tmp_path)
    transport.scp = child('pass')
    source = tmp_path / 'source'; source.write_bytes(b'payload')
    original_close = module.os.close
    original_read = module.archive.io._read
    injected = []
    def close(fd):
        name = module.os.readlink('/proc/self/fd/' + str(fd))
        original_close(fd)
        selected = name == str(tmp_path) if target == 'directory' else name.startswith('/memfd:archive-upload')
        if selected:
            injected.append(fd)
            raise OSError('uncertain ' + target)
    def read(*args):
        if primary and target == 'directory': raise ValueError('primary source failure')
        return original_read(*args)
    def run(*args):
        if primary and target == 'memfd': raise ValueError('primary upload failure')
    monkeypatch.setattr(module.os, 'close', close)
    monkeypatch.setattr(module.archive.io, '_read', read)
    monkeypatch.setattr(transport, 'run', run)
    with pytest.raises(module.archive.io.CleanupFailure) as caught:
        transport.put(source, 'object/payload.bin')
    assert len(injected) == 1
    if primary: assert isinstance(caught.value.__cause__, ValueError)
    assert transport.budget.remaining == (100000 if target == 'directory' else 99993)


def test_failed_diagnostic_publication_preserves_primary(module, tmp_path, monkeypatch):
    transport = adapter(module, tmp_path)
    transport.ssh = child('print("excess")')
    def failed(*args, **kwargs): raise OSError('receipt publication failed')
    monkeypatch.setattr(module, '_immutable', failed)
    with pytest.raises(ValueError, match='exceeds expected bytes') as caught:
        transport.get('object/payload.bin', tmp_path / 'result', expected_bytes=2)
    assert any('receipt' in note for note in caught.value.__notes__)
    assert not (tmp_path / 'result').exists()
    assert transport.budget.remaining == 67232
