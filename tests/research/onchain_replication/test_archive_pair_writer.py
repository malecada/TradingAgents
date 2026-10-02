import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from tradingagents.research.onchain_replication import compact_pair_log as events

spec=importlib.util.spec_from_file_location('archive_fixture',Path(__file__).with_name('test_archive_chunks.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
sha=base.digest


def fixture(tmp_path):
    from tradingagents.research.onchain_replication import archive_pair_writer as writer
    transport=base.Transport(tmp_path/'remote')
    limits={'chunk_events':3,'max_events':12,'max_pairs':4,
        'max_logical_bytes':12*events.RECORD_BYTES+2*events.io.META_LIMIT}
    policy={'schema_version':1,'remote_prefix':'fresh-log','transport_identity':transport.identity,
        'max_chunks':4,'max_metadata_bytes':(7*4+8)*events.io.META_LIMIT,
        'local_free_floor_bytes':10*1024**3}
    kwargs=dict(root=tmp_path/'log',owner=sha(b'owner'),scope={k:sha(k.encode()) for k in events.FIELDS},
        limits=limits,max_iterations=10,lease=lambda:None,transport=transport,archive_policy=policy)
    return writer,transport,kwargs


def first(log):
    log.begin(sha(b'purpose0'),sha(b'pair0'));log.progress(sha(b'checkpoint'))
    log.complete(.25,'temperature_complete',1)


def test_rollover_disposes_only_sealed_owned_chunks_and_finish_replays(tmp_path):
    module,transport,kwargs=fixture(tmp_path)
    log=module.ArchivePairLog(**kwargs)
    first(log)
    assert (log.root/events._name(0)).stat().st_size==3*events.RECORD_BYTES
    assert not list(transport.root.iterdir())  # latest acknowledged event remains local
    log.begin(sha(b'purpose1'),sha(b'pair1'))
    assert not (log.root/events._name(0)).exists()
    assert (log.root/events._name(1)).stat().st_size==events.RECORD_BYTES
    assert list((log.root/'copies').rglob('*.bin'))==[]
    log.complete(.75,'iteration_cap',2)
    reference=log.finish()
    assert sha((log.root/'terminal.json').read_bytes())==reference
    assert list(log.root.rglob('*.bin'))==[]
    assert sorted(p.stat().st_size for p in transport.root.rglob('payload.bin'))==[2*events.RECORD_BYTES,3*events.RECORD_BYTES]
    complete=json.loads((log.root/'archive-complete.json').read_bytes())
    assert complete['terminal_sha256']==reference and complete['chunks']==2
    assert complete['replay']['completed_pairs']==2 and complete['replay']['progress_events']==1
    assert complete['replay']['record_bytes']==5*events.RECORD_BYTES
    with pytest.raises(ValueError):log.begin(sha(b'again'),sha(b'again'))
    with pytest.raises(FileExistsError):module.ArchivePairLog(**kwargs)


@pytest.mark.parametrize('failure',['corrupt','put','changed_chunk'])
def test_rollover_failure_preserves_chunk_and_poisoned_attempt(tmp_path,failure):
    module,transport,kwargs=fixture(tmp_path);log=module.ArchivePairLog(**kwargs);first(log)
    if failure=='corrupt':transport.corrupt=True
    if failure=='put':transport.fail_put=True
    if failure=='changed_chunk':(log.root/events._name(0)).write_bytes(b'changed')
    with pytest.raises((ValueError,OSError)):log.begin(sha(b'p1'),sha(b'i1'))
    assert (log.root/events._name(0)).exists()
    assert (log.root/'failed.json').exists()
    assert not (log.root/'archive-complete.json').exists()
    with pytest.raises(ValueError):log.finish()


@pytest.mark.parametrize('failure',['metadata','foreign','revoked'])
def test_manifest_final_callback_prevents_source_disposal(tmp_path,monkeypatch,failure):
    module,transport,kwargs=fixture(tmp_path)
    def live():
        if getattr(live,'revoked',False):raise RuntimeError('revoked')
    kwargs['lease']=live;log=module.ArchivePairLog(**kwargs);first(log)
    original=events.io._write
    def write(fd,name,raw):
        result=original(fd,name,raw)
        if name=='chunk-000000000000.json':
            if failure=='metadata':(log.root/name).write_bytes(b'{}')
            if failure=='foreign':(log.root/'copies/chunk-000000000000/failed.json').write_bytes(b'conflict')
            if failure=='revoked':live.revoked=True
        return result
    monkeypatch.setattr(events.io,'_write',write)
    with pytest.raises((ValueError,RuntimeError)):log.begin(sha(b'p1'),sha(b'i1'))
    assert (log.root/events._name(0)).exists()
    assert (log.root/'failed.json').exists()


@pytest.mark.parametrize('failure',['remote_corrupt','mapping','final_revoke'])
def test_terminal_replay_and_final_publication_refuse_changed_evidence(tmp_path,monkeypatch,failure):
    module,transport,kwargs=fixture(tmp_path)
    def live():
        if getattr(live,'revoked',False):raise RuntimeError('revoked')
    kwargs['lease']=live;log=module.ArchivePairLog(**kwargs);first(log)
    log.begin(sha(b'p1'),sha(b'i1'));log.complete(.5,'iteration_cap',1)
    if failure=='remote_corrupt':next(transport.root.rglob('payload.bin')).write_bytes(b'corrupt')
    if failure=='mapping':(log.root/'chunk-000000000000.json').write_bytes(b'{}')
    if failure=='final_revoke':
        original=events.io._write
        def write(fd,name,raw):
            result=original(fd,name,raw)
            if name=='archive-complete.json':live.revoked=True
            return result
        monkeypatch.setattr(events.io,'_write',write)
    with pytest.raises((ValueError,OSError,RuntimeError)):log.finish()
    assert (log.root/'failed.json').exists()
    assert log.closed


@pytest.mark.parametrize('failure',['floor','metadata','chunks','prefix','transport'])
def test_bad_policy_refused_before_local_claim(tmp_path,failure):
    module,transport,kwargs=fixture(tmp_path);policy=kwargs['archive_policy']
    if failure=='floor':policy['local_free_floor_bytes']=0
    if failure=='metadata':policy['max_metadata_bytes']=1
    if failure=='chunks':policy['max_chunks']=3
    if failure=='prefix':policy['remote_prefix']='../bad'
    if failure=='transport':policy['transport_identity']='0'*64
    with pytest.raises(ValueError):module.ArchivePairLog(**kwargs)
    assert not kwargs['root'].exists()


@pytest.mark.parametrize('operation',['finish','fail'])
def test_terminal_call_never_mutates_closed_success(tmp_path,operation):
    module,transport,kwargs=fixture(tmp_path);log=module.ArchivePairLog(**kwargs);first(log);log.finish()
    before={str(p.relative_to(log.root)):sha(p.read_bytes()) for p in log.root.rglob('*') if p.is_file()}
    with pytest.raises(ValueError):
        if operation=='finish':log.finish()
        else:log.fail('duplicate')
    after={str(p.relative_to(log.root)):sha(p.read_bytes()) for p in log.root.rglob('*') if p.is_file()}
    assert after==before


def test_post_append_lease_cannot_corrupt_acknowledged_event(tmp_path):
    module,transport,kwargs=fixture(tmp_path);box={}
    def lease():
        log=box.get('log')
        if log is not None and log.events==1:
            (log.root/events._name(0)).write_bytes(b'corrupt')
    kwargs['lease']=lease;log=module.ArchivePairLog(**kwargs);box['log']=log
    with pytest.raises(ValueError):log.begin(sha(b'p'),sha(b'i'))
    assert (log.root/'failed.json').exists()


@pytest.mark.parametrize('phase',['start_write','post_start_lease'])
def test_constructor_failure_closes_owned_root_without_missing_identity(tmp_path,monkeypatch,phase):
    module,transport,kwargs=fixture(tmp_path);opened=[];original_open=events.io._open;original_write=events.io._write
    def opening(path):
        result=original_open(path)
        if Path(path)==kwargs['root']:opened.append(result[1])
        return result
    def write(fd,name,raw):
        result=original_write(fd,name,raw)
        if phase=='start_write' and name=='start.json':raise RuntimeError('fixture start publication')
        return result
    def lease():
        if phase=='post_start_lease' and (kwargs['root']/'start.json').exists():raise RuntimeError('fixture start publication')
    monkeypatch.setattr(events.io,'_open',opening);monkeypatch.setattr(events.io,'_write',write);kwargs['lease']=lease
    try:
        with pytest.raises(RuntimeError,match='fixture start publication'):module.ArchivePairLog(**kwargs)
        for fd in opened:
            with pytest.raises(OSError):module.os.fstat(fd)
    finally:
        # Preserve an old implementation's leaked test descriptors without leaving them active.
        for fd in opened:
            try:module.os.close(fd)
            except OSError:pass


def test_equal_byte_replacement_is_not_owned_sealed_chunk(tmp_path):
    module,transport,kwargs=fixture(tmp_path);log=module.ArchivePairLog(**kwargs);first(log)
    path=log.root/events._name(0);raw=path.read_bytes();replacement=tmp_path/'replacement'
    replacement.write_bytes(raw);replacement.replace(path)
    with pytest.raises(ValueError):log.begin(sha(b'p1'),sha(b'i1'))
    assert path.read_bytes()==raw
    assert (log.root/'failed.json').is_file()


@pytest.mark.parametrize('name',['failed.json','cleanup-failed.json'])
def test_conflicting_root_failure_blocks_disposition(tmp_path,monkeypatch,name):
    module,transport,kwargs=fixture(tmp_path);log=module.ArchivePairLog(**kwargs);first(log)
    original=events.io._write
    def write(fd,member,raw):
        result=original(fd,member,raw)
        if member=='chunk-000000000000.json':(log.root/name).symlink_to(log.root/'missing')
        return result
    monkeypatch.setattr(events.io,'_write',write)
    with pytest.raises(ValueError):log.begin(sha(b'p1'),sha(b'i1'))
    assert (log.root/events._name(0)).exists()


def test_owned_child_close_uncertainty_is_fatal(tmp_path,monkeypatch):
    module,transport,kwargs=fixture(tmp_path);log=module.ArchivePairLog(**kwargs);first(log)
    original_open=events.io._open;original_close=module.os.close;target={}
    def opening(path):
        result=original_open(path)
        if Path(path)==log.root/'copies' and not target.get('done'):target['fd']=result[1]
        return result
    def close(fd):
        if fd==target.get('fd') and not target.get('done'):
            target['done']=True;original_close(fd);raise OSError('uncertain child close')
        return original_close(fd)
    monkeypatch.setattr(events.io,'_open',opening);monkeypatch.setattr(module.os,'close',close)
    with pytest.raises(events.io.CleanupFailure):log.begin(sha(b'p1'),sha(b'i1'))
    assert (log.root/'failed.json').exists()
