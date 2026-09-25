"""Real synthetic subprocesses catch diagnostic deadlock and lost bounds."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import pytest

SCRIPT = Path(__file__).resolve().parents[3] / 'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-25-05/transfer.py'


def receiver():
    spec = importlib.util.spec_from_file_location('backup05', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.receive_diagnostic


@pytest.mark.parametrize('payload,expected,okay', [('abc', 3, True), ('abcd', 3, False), ('ab', 3, False)])
def test_preserves_exact_size_bound_with_diagnostics(tmp_path, payload, expected, okay):
    receive = receiver(); out = tmp_path/'download'
    cmd = [sys.executable, '-c', f'import sys;sys.stdout.write({payload!r});sys.stderr.write("diagnostic")']
    if okay:
        receive(cmd, out, expected_bytes=expected, max_seconds=5, bytes_per_second=1024**2)
        assert out.read_bytes() == b'abc'
    else:
        with pytest.raises(ValueError, match='size'):
            receive(cmd, out, expected_bytes=expected, max_seconds=5, bytes_per_second=1024**2)
        assert out.stat().st_size <= expected
    receipt = json.loads((tmp_path/'download.transport.json').read_text())
    assert receipt['status'] == ('complete' if okay else 'failed')


def test_large_stderr_does_not_deadlock_and_retains_bounded_error_tail(tmp_path):
    receive = receiver(); out = tmp_path/'download'
    cmd = [sys.executable, '-c', 'import sys;sys.stderr.write("x"*200000+"connection lost");sys.stderr.flush();sys.stdout.write("ab");sys.exit(17)']
    with pytest.raises(RuntimeError, match='download process failed'):
        receive(cmd, out, expected_bytes=3, max_seconds=5, bytes_per_second=1024**2)
    receipt = json.loads((tmp_path/'download.transport.json').read_text())
    assert receipt['returncode'] == 17
    assert receipt['received_bytes'] == 2
    assert receipt['stderr_bytes_seen'] == 200015
    assert receipt['stderr_tail'].endswith('connection lost')
    assert receipt['stderr_truncated'] is True
    assert len(receipt['stderr_tail'].encode()) <= 16384
    assert (tmp_path/'download.transport.json').stat().st_size < 20000


def test_timeout_kills_child_and_records_partial_error(tmp_path):
    receive = receiver(); out = tmp_path/'download'
    cmd = [sys.executable, '-c', 'import sys,time;sys.stderr.write("stalled");sys.stderr.flush();time.sleep(10)']
    with pytest.raises(TimeoutError):
        receive(cmd, out, expected_bytes=1, max_seconds=.3, bytes_per_second=1024**2)
    receipt = json.loads((tmp_path/'download.transport.json').read_text())
    assert receipt['returncode'] is not None
    assert receipt['stderr_tail'] == 'stalled'
    assert receipt['error_type'] == 'TimeoutError'
    assert not Path('/proc/'+str(receipt['pid'])).exists()


def test_rate_bound_and_exclusive_destination_survive(tmp_path):
    receive = receiver(); out = tmp_path/'download'
    cmd = [sys.executable, '-c', 'import sys;sys.stdout.write("x"*32)']
    before = time.monotonic()
    receive(cmd, out, expected_bytes=32, max_seconds=5, bytes_per_second=64)
    assert time.monotonic()-before >= .45
    saved = (tmp_path/'download.transport.json').read_bytes()
    with pytest.raises(FileExistsError):
        receive(cmd, out, expected_bytes=32, max_seconds=5, bytes_per_second=64)
    assert (tmp_path/'download.transport.json').read_bytes() == saved
