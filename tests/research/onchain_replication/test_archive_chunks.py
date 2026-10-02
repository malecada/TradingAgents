"""Synthetic transport tests. No external archive or empirical claim."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Transport:
    identity = digest(b'synthetic-directory-transport')

    def __init__(self, root):
        self.root = root
        root.mkdir()
        self.corrupt = False
        self.fail_put = False

    def mkdir(self, name):
        (self.root / name).mkdir()

    def put(self, source, name):
        with (self.root / name).open('xb') as output:
            output.write(source.read_bytes())
        if self.fail_put:
            raise OSError('synthetic interrupted upload')

    def get(self, name, destination, *, expected_bytes):
        raw = (self.root / name).read_bytes()
        if self.corrupt:
            raw = bytes([raw[0] ^ 1]) + raw[1:]
        if len(raw) > expected_bytes:
            raise ValueError('transport byte cap')
        with destination.open('xb') as output:
            output.write(raw)


def fixture(tmp_path):
    from tradingagents.research.onchain_replication import archive_chunks as archive
    source = tmp_path / 'source.bin'
    source.write_bytes(bytes(range(256)) * 257)
    transport = Transport(tmp_path / 'remote')
    kwargs = dict(source=source, attempt=tmp_path / 'attempt',
        expected_sha256=digest(source.read_bytes()), expected_bytes=source.stat().st_size,
        scope=digest(b'closed-chunk-scope'), remote='object-0001', transport=transport,
        lease=lambda: None, free_floor_bytes=0)
    return archive, source, transport, kwargs


def test_preserve_and_fresh_read_without_original(tmp_path):
    archive, source, transport, kwargs = fixture(tmp_path)
    original = source.read_bytes()
    ref = archive.preserve(**kwargs)
    receipt = json.loads((kwargs['attempt'] / 'complete.json').read_bytes())
    assert receipt['source_sha256'] == digest(original)
    assert receipt['bytes'] == len(original)
    assert receipt['scope'] == kwargs['scope']
    assert source.read_bytes() == original
    # Removal is confined to this disposable synthetic fixture, never implementation.
    source.unlink()
    result = archive.retrieve(kwargs['attempt'], receipt_sha256=ref,
        attempt=tmp_path / 'read01', transport=transport, lease=lambda: None,
        free_floor_bytes=0)
    assert result.read_bytes() == original
    assert (tmp_path / 'read01' / 'complete.json').is_file()
    with pytest.raises(FileExistsError):
        archive.retrieve(kwargs['attempt'], receipt_sha256=ref,
            attempt=tmp_path / 'read01', transport=transport, lease=lambda: None,
            free_floor_bytes=0)


@pytest.mark.parametrize('failure', ['corrupt', 'put', 'source_mutation', 'lease'])
def test_failed_attempt_retains_bytes_and_cannot_replay(tmp_path, failure):
    archive, source, transport, kwargs = fixture(tmp_path)
    if failure == 'corrupt': transport.corrupt = True
    if failure == 'put': transport.fail_put = True
    original_get = transport.get
    def get(*args, **options):
        original_get(*args, **options)
        if failure == 'source_mutation': source.write_bytes(b'changed')
        if failure == 'lease': kwargs['lease'].__dict__['revoked'] = True
    transport.get = get
    def lease():
        if getattr(lease, 'revoked', False): raise RuntimeError('lease revoked')
    kwargs['lease'] = lease
    with pytest.raises((ValueError, OSError, RuntimeError)):
        archive.preserve(**kwargs)
    assert source.exists()
    assert (kwargs['attempt'] / 'snapshot.bin').exists()
    assert (kwargs['attempt'] / 'failed.json').exists()
    assert not (kwargs['attempt'] / 'complete.json').exists()
    assert (transport.root / kwargs['remote'] / 'payload.bin').exists()
    with pytest.raises(FileExistsError): archive.preserve(**kwargs)


@pytest.mark.parametrize('failure', ['hash', 'size', 'oversize', 'symlink', 'hardlink', 'floor', 'remote'])
def test_preflight_refuses_before_claim(tmp_path, failure):
    archive, source, transport, kwargs = fixture(tmp_path)
    if failure == 'hash': kwargs['expected_sha256'] = '0' * 64
    if failure == 'size': kwargs['expected_bytes'] += 1
    if failure == 'oversize': kwargs['expected_bytes'] = 8 * 1024**2 + 1
    if failure == 'symlink':
        linked = source.with_name('link.bin'); linked.symlink_to(source); kwargs['source'] = linked
    if failure == 'hardlink': source.with_name('link.bin').hardlink_to(source)
    if failure == 'floor': kwargs['free_floor_bytes'] = 2**62
    if failure == 'remote': kwargs['remote'] = '../escape'
    with pytest.raises((ValueError, OSError)): archive.preserve(**kwargs)
    assert not kwargs['attempt'].exists()
    assert list(transport.root.iterdir()) == []


@pytest.mark.parametrize('failure', ['receipt', 'transport', 'remote_bytes'])
def test_fresh_read_refuses_changed_evidence(tmp_path, failure):
    archive, source, transport, kwargs = fixture(tmp_path)
    ref = archive.preserve(**kwargs)
    if failure == 'receipt': (kwargs['attempt'] / 'complete.json').write_text('{}')
    if failure == 'transport': transport.identity = '1' * 64
    if failure == 'remote_bytes': transport.corrupt = True
    with pytest.raises(ValueError):
        archive.retrieve(kwargs['attempt'], receipt_sha256=ref,
            attempt=tmp_path / 'read01', transport=transport, lease=lambda: None,
            free_floor_bytes=0)
    assert source.exists()
    assert not (tmp_path / 'read01' / 'complete.json').exists()


def test_existing_remote_never_overwritten(tmp_path):
    archive, source, transport, kwargs = fixture(tmp_path)
    directory = transport.root / kwargs['remote']; directory.mkdir()
    (directory / 'payload.bin').write_bytes(b'previous attempt')
    with pytest.raises(FileExistsError): archive.preserve(**kwargs)
    assert (directory / 'payload.bin').read_bytes() == b'previous attempt'
    assert (kwargs['attempt'] / 'failed.json').exists()


@pytest.mark.parametrize('operation', ['preserve', 'retrieve'])
@pytest.mark.parametrize('failure', ['revoked', 'payload', 'complete'])
def test_publication_callback_cannot_return_false_success(tmp_path, monkeypatch, operation, failure):
    archive, source, transport, kwargs = fixture(tmp_path)
    if operation == 'retrieve': ref = archive.preserve(**kwargs)
    target = kwargs['attempt'] if operation == 'preserve' else tmp_path / 'read01'
    original = archive.io._write
    def lease():
        if getattr(lease, 'revoked', False): raise RuntimeError('lease revoked')
    kwargs['lease'] = lease
    def write(fd, name, body):
        result = original(fd, name, body)
        if name == 'complete.json':
            if failure == 'revoked': lease.revoked = True
            if failure == 'payload':
                (target / ('readback.bin' if operation == 'preserve' else 'payload.bin')).write_bytes(b'corrupt')
            if failure == 'complete': (target / name).write_bytes(b'{}')
        return result
    monkeypatch.setattr(archive.io, '_write', write)
    with pytest.raises((ValueError, RuntimeError)):
        if operation == 'preserve': archive.preserve(**kwargs)
        else: archive.retrieve(kwargs['attempt'], receipt_sha256=ref,
            attempt=target, transport=transport, lease=lease, free_floor_bytes=0)
    assert (target / 'complete.json').exists()
    assert (target / 'failed.json').exists()
    assert source.exists()


@pytest.mark.parametrize('operation', ['preserve', 'retrieve', 'receipt'])
@pytest.mark.parametrize('foreign', ['failed.json', 'foreign.bin', 'dangling-failure'])
def test_exact_inventory_rejects_conflict_and_foreign_bytes(tmp_path, operation, foreign):
    archive, source, transport, kwargs = fixture(tmp_path)
    if operation != 'preserve': ref = archive.preserve(**kwargs)
    target = kwargs['attempt'] if operation in ('preserve', 'receipt') else tmp_path / 'read01'
    def inject():
        if foreign == 'dangling-failure': (target / 'failed.json').symlink_to(target / 'missing')
        else: (target / foreign).write_bytes(b'foreign')
    if operation == 'receipt': inject()
    else:
        original_get = transport.get
        def get(*args, **options):
            original_get(*args, **options); inject()
        transport.get = get
    with pytest.raises(ValueError):
        if operation == 'preserve': archive.preserve(**kwargs)
        else: archive.retrieve(kwargs['attempt'], receipt_sha256=ref,
            attempt=tmp_path / 'read01', transport=transport, lease=lambda: None,
            free_floor_bytes=0)
    assert source.exists()
