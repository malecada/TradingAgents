"""Real finite local receiver behind the new SSH adapter; no network."""
import importlib.util
from pathlib import Path
import sys

import pytest

RUNNER = Path(__file__).resolve().parents[3] / 'research/onchain-paper-replication-2026-09-24/storage/archive-chunk-smoke-2026-10-02-01/run.py'


def load():
    spec = importlib.util.spec_from_file_location('archive_smoke', RUNNER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_fresh_adapter_reads_prebound_extent_and_retains_diagnostic(tmp_path):
    module = load()
    budget = module.Budget(100000)
    adapter = module.Transport(tmp_path / 'diagnostics', budget)
    # A real local child emits known bytes; dd argv are inert script arguments.
    adapter.ssh = [sys.executable, '-c', 'import sys;sys.stdout.buffer.write(b"readback")']
    destination = tmp_path / 'payload.bin'
    adapter.get('object/payload.bin', destination, expected_bytes=8)
    assert destination.read_bytes() == b'readback'
    assert destination.stat().st_nlink == 1
    assert (tmp_path / 'diagnostics/get-0000.bin.transport.json').is_file()
    assert budget.remaining == 100000 - 32768
    with pytest.raises(FileExistsError):
        adapter.get('object/payload.bin', destination, expected_bytes=8)


def test_receiver_excess_bytes_and_budget_are_fatal(tmp_path):
    module = load()
    adapter = module.Transport(tmp_path / 'diagnostics', module.Budget(40000))
    adapter.ssh = [sys.executable, '-c', 'print("too much content")']
    with pytest.raises(ValueError):
        adapter.get('object/payload.bin', tmp_path / 'payload.bin', expected_bytes=2)
    assert not (tmp_path / 'payload.bin').exists()
    assert (tmp_path / 'diagnostics/get-0000.bin.transport.json').is_file()
    with pytest.raises(RuntimeError):
        adapter.get('object/payload.bin', tmp_path / 'next.bin', expected_bytes=20)


def test_upload_does_not_accept_unsafe_names(tmp_path):
    module = load()
    adapter = module.Transport(tmp_path / 'diagnostics', module.Budget(20))
    for name in ('../escape', '/absolute', 'object/payload.bin;bad', 'object//payload.bin'):
        with pytest.raises(ValueError): adapter.remote_path(name)


def test_revoked_after_mkdir_prevents_upload_process(tmp_path):
    module = load()
    def live():
        if getattr(live, 'revoked', False): raise RuntimeError('guard revoked')
    adapter = module.Transport(tmp_path / 'diagnostics', module.Budget(100000), lease_callback=live)
    adapter.ssh = [sys.executable, '-c', 'pass']
    adapter.mkdir('fresh-object')
    live.revoked = True
    sentinel = tmp_path / 'upload-started'
    adapter.scp = [sys.executable, '-c', 'from pathlib import Path;Path(' + repr(str(sentinel)) + ').touch()']
    source = tmp_path / 'source'; source.write_bytes(b'payload')
    with pytest.raises(RuntimeError, match='guard revoked'):
        adapter.put(source, 'fresh-object/payload.bin')
    assert not sentinel.exists()
    assert len(list((tmp_path / 'diagnostics').glob('command-*.bin'))) == 1
