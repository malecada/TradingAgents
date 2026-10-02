"""Actual archived stage publication and current-owner local evidence checks."""
import json
import pytest
from tests.research.onchain_replication.test_archive_owner_policy import admitted
from tests.research.onchain_replication.test_archive_owner_stage import written
from tradingagents.research.onchain_replication.provenance import thaw

pytestmark=pytest.mark.parametrize('admitted',['writer_matching'],indirect=True)


def test_actual_seal_then_local_check_and_duplicate_preserves_history(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_owner_seal as module
    ledger,stage=written(admitted);calls=[];original=admitted[2].get
    def get(*args,**kwargs):calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(admitted[2],'get',get)
    ref=module.seal(ledger,stage)
    assert len(calls)==1 and stage.closed and not stage.closing and ledger.owner.active is None
    raw=(stage.root/'stage-complete.json').read_bytes()
    assert ref==stage.reference==module.io._hash(raw)
    record=json.loads(raw);assert record['format']=='archived-owner-stage-v1'
    assert record['contract']==thaw(stage.contract)
    before={str(p):p.read_bytes() for p in ledger.root.parent.rglob('*') if p.is_file()}
    with pytest.raises(ValueError):module.seal(ledger,stage)
    assert ledger._reads=={'dictionary':1} and not ledger.owner.poisoned
    def forbidden(*args,**kwargs):raise AssertionError('sealed local check must not transfer')
    for name in ('get','put','mkdir'):monkeypatch.setattr(admitted[2],name,forbidden)
    result=module.check(ledger,stage)
    assert result['completed_pairs']==1 and result['execution_admitted'] is False
    assert before=={str(p):p.read_bytes() for p in ledger.root.parent.rglob('*') if p.is_file()}
    # A completed dictionary must remain checkable while a later stage is active.
    next_stage=ledger.owner.begin(ledger.owner.required[1],workload_sha256='e'*64,pairs=1)
    assert module.check(ledger,stage)['completed_pairs']==1 and ledger.owner.active is next_stage
    ledger.close()


def test_caller_completed_read_cannot_shortcut_fresh_seal_replay(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_owner_seal as module
    ledger,stage=written(admitted)
    bogus=ledger.reader(stage);bogus.complete('0'*64)
    original=admitted[2].get;calls=[]
    def get(*args,**kwargs):calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(admitted[2],'get',get)
    module.seal(ledger,stage)
    assert len(calls)==1 and ledger._reads=={'dictionary':2}
    assert stage.contract['archive']['reader_claim']=='reader-dictionary-0001'
    assert json.loads(bogus._terminal['complete.json'])['reference_sha256']=='0'*64
    ledger.close()


@pytest.mark.parametrize('failure',['callback','close'])
def test_seal_failure_keeps_marker_and_read_spent_before_stage_ack(admitted,monkeypatch,failure):
    from tradingagents.research.onchain_replication import archive_owner_seal as module
    ledger,stage=written(admitted);owner=ledger.owner;original=owner.lease;close=module.os.close;injected=[]
    def lease():
        original()
        if failure=='callback' and (stage.root/'stage-complete.json').exists():
            (stage.root/'stage-complete.json').write_bytes(b'{}')
    def uncertain(fd):
        path=module.os.readlink('/proc/self/fd/'+str(fd));close(fd)
        if failure=='close' and not injected and path==str(stage.root) and (stage.root/'stage-complete.json').exists():
            injected.append(1);raise OSError('synthetic stage close uncertainty')
    monkeypatch.setattr(owner,'lease',lease);monkeypatch.setattr(module.os,'close',uncertain)
    with pytest.raises(ValueError if failure=='callback' else module.io.CleanupFailure):module.seal(ledger,stage)
    assert (stage.root/'stage-complete.json').exists() and not stage.closed and owner.poisoned
    assert stage.reference is None and stage.contract is None and owner.active is stage
    assert set(ledger._operations['reader-dictionary-0000']._terminal)=={'complete.json','failed.json'}
    monkeypatch.setattr(owner,'lease',original);monkeypatch.setattr(module.os,'close',close);ledger.close()


def test_sealed_check_detects_last_callback_mutation_without_rewriting_claim(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_owner_seal as module
    ledger,stage=written(admitted);module.seal(ledger,stage)
    claim=ledger._operations['reader-dictionary-0000'];before=dict(claim._terminal)
    original=ledger.owner.lease;calls=[]
    def lease():
        original();calls.append(1)
        if len(calls)==2:(stage.root/'stage-complete.json').write_bytes(b'{}')
    monkeypatch.setattr(ledger.owner,'lease',lease)
    with pytest.raises(ValueError):module.check(ledger,stage)
    assert claim._terminal==before and ledger.owner.poisoned and ledger._poisoned
    assert (ledger.root/'failed-stage-check.json').is_file()
    monkeypatch.setattr(ledger.owner,'lease',original);ledger.close()


def test_seal_final_callback_cannot_replace_original_matching_namespace(admitted,monkeypatch):
    import shutil
    from tradingagents.research.onchain_replication import archive_owner_seal as module
    ledger,stage=written(admitted);original=ledger.owner.lease;replaced=[]
    def lease():
        original()
        if not replaced and (stage.root/'stage-complete.json').exists():
            previous=ledger.root.parent/'preserved-original-matching'
            (stage.root/'matching').rename(previous)
            shutil.copytree(previous,stage.root/'matching');replaced.append(previous)
    monkeypatch.setattr(ledger.owner,'lease',lease)
    with pytest.raises(ValueError):module.seal(ledger,stage)
    assert replaced and replaced[0].is_dir() and not stage.closed and ledger.owner.poisoned
    assert set(ledger._operations['reader-dictionary-0000']._terminal)=={'complete.json','failed.json'}
    monkeypatch.setattr(ledger.owner,'lease',original);ledger.close()
