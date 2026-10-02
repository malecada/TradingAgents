"""Only freshly created synthetic fixture cache is disposable here."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

spec = importlib.util.spec_from_file_location('archive_fixture', Path(__file__).with_name('test_archive_chunks.py'))
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)


def fixture(tmp_path):
    from tradingagents.research.onchain_replication import archive_consume as consume
    archive, source, transport, values = base.fixture(tmp_path)
    ref = archive.preserve(**values)
    raw = (values['attempt'] / 'complete.json').read_bytes()
    kwargs = dict(receipt_bytes=raw, receipt_sha256=ref, expected_scope=values['scope'],
        attempt=tmp_path / 'cache', transport=transport, lease=lambda: None, free_floor_bytes=0)
    return consume, archive, source, transport, values, kwargs


def test_returned_bytes_verified_scratch_removed_originals_untouched(tmp_path):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    original = source.read_bytes()
    result = mod.consume(**kwargs)
    assert type(result) is bytes and result == original
    assert source.read_bytes() == original
    assert (values['attempt'] / 'snapshot.bin').read_bytes() == original
    assert (transport.root / values['remote'] / 'payload.bin').read_bytes() == original
    assert {p.name for p in kwargs['attempt'].iterdir()} == {'intent.json','verified.json','complete.json'}
    with pytest.raises(FileExistsError): mod.consume(**kwargs)


def test_sequential_read_without_original_copy_directory_has_no_retained_payload(tmp_path):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    original = source.read_bytes()
    # Disposable synthetic fixture only; the consumer never disposes source evidence.
    shutil.rmtree(values['attempt']); source.unlink()
    cache_root = tmp_path / 'cache-attempts'; cache_root.mkdir()
    for index in range(4):
        kwargs['attempt'] = cache_root / f'chunk-{index}'
        assert mod.consume(**kwargs) == original
        assert list(cache_root.rglob('*.bin')) == []
    assert len(list(cache_root.rglob('*.json'))) == 12


@pytest.mark.parametrize('kind', ['hash', 'scope', 'transport', 'oversize', 'floor'])
def test_preflight_refuses_before_attempt(tmp_path, kind):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    if kind == 'hash': kwargs['receipt_sha256'] = '0'*64
    if kind == 'scope': kwargs['expected_scope'] = '0'*64
    if kind == 'transport': transport.identity = '0'*64
    if kind == 'floor': kwargs['free_floor_bytes'] = 2**62
    if kind == 'oversize':
        raw = json.loads(kwargs['receipt_bytes']);raw['bytes'] = 8*1024**2+1
        kwargs['receipt_bytes'] = archive.io._json(raw)
        kwargs['receipt_sha256'] = base.digest(kwargs['receipt_bytes'])
    with pytest.raises(ValueError): mod.consume(**kwargs)
    assert not kwargs['attempt'].exists()


@pytest.mark.parametrize('kind', ['corrupt','foreign','symlink','revoked'])
def test_download_failure_retains_attempt_and_original(tmp_path, kind):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    original = transport.get
    def get(*args, **options):
        original(*args, **options)
        if kind == 'corrupt': args[1].write_bytes(b'corrupt')
        if kind == 'foreign': (kwargs['attempt'] / 'failed.json').write_bytes(b'foreign')
        if kind == 'symlink':
            args[1].unlink();args[1].symlink_to(source)
        if kind == 'revoked': live.revoked = True
    def live():
        if getattr(live,'revoked',False): raise RuntimeError('revoked')
    transport.get = get;kwargs['lease'] = live
    with pytest.raises((ValueError,RuntimeError)): mod.consume(**kwargs)
    assert source.exists()
    assert (kwargs['attempt'] / 'failed.json').exists()
    assert (kwargs['attempt'] / 'payload.bin').exists()
    assert not (kwargs['attempt'] / 'complete.json').exists()
    with pytest.raises(FileExistsError): mod.consume(**kwargs)


@pytest.mark.parametrize('phase',['verified.json','complete.json'])
@pytest.mark.parametrize('kind',['metadata','payload','revoked'])
def test_final_publication_callback_is_checked(tmp_path,monkeypatch,phase,kind):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    original = archive.io._write
    def live():
        if getattr(live,'revoked',False): raise RuntimeError('revoked')
    kwargs['lease'] = live
    def write(fd,name,body):
        result=original(fd,name,body)
        if name == phase:
            if kind == 'metadata': (kwargs['attempt']/name).write_bytes(b'{}')
            if kind == 'payload': (kwargs['attempt']/'payload.bin').write_bytes(b'changed')
            if kind == 'revoked': live.revoked=True
        return result
    monkeypatch.setattr(archive.io,'_write',write)
    with pytest.raises((ValueError,RuntimeError)): mod.consume(**kwargs)
    assert source.exists()
    assert (kwargs['attempt']/'failed.json').is_file()
    if phase == 'verified.json': assert (kwargs['attempt']/'payload.bin').exists()


def test_cleanup_failure_is_terminal_and_payload_retained(tmp_path,monkeypatch):
    mod, archive, source, transport, values, kwargs = fixture(tmp_path)
    original=mod.os.unlink
    def unlink(name,*args,**options):
        if name == 'payload.bin': raise OSError('cannot release cache')
        return original(name,*args,**options)
    monkeypatch.setattr(mod.os,'unlink',unlink)
    with pytest.raises(OSError,match='cannot release cache'):mod.consume(**kwargs)
    assert (kwargs['attempt']/'payload.bin').read_bytes()==source.read_bytes()
    assert (kwargs['attempt']/'failed.json').is_file()
