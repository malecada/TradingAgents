"""Actual owner writer followed by a finite reserved scientific archive read."""
import json
import pytest
from tests.research.onchain_replication.test_archive_owner_policy import admitted
from tests.research.onchain_replication.test_archive_owner_writer import setup
from tests.research.onchain_replication.test_matching_reference import graph
from tradingagents.research.onchain_replication import compact_matcher
from tradingagents.research.onchain_replication.provenance import thaw
from tradingagents.research.onchain_replication.matching_identity import graph_identity

pytestmark=pytest.mark.parametrize('admitted',['writer_matching'],indirect=True)


def written(admitted):
    module,ledger,stage=setup(admitted,1);owner=admitted[1]
    a=graph([[0.],[.3]],[(0,1,.1)]);b=graph([[.2],[.7]],[(1,0,.4)])
    def produce(log,lease):
        p=thaw(owner.policy)
        matcher=compact_matcher.CompactMatcher(log,config=thaw(owner.matching),
            context=thaw(owner.bound.context),policy=p['pair'],workload_sha256='d'*64,
            schedule=p['schedule'],lease=lease)
        return matcher({'schema_version':1,'kind':'dictionary','workload_sha256':'d'*64,
            'typed_graphs':[graph_identity(a),graph_identity(b)]},a,b)
    module.run(ledger,stage,produce)
    return ledger,stage


def test_actual_reserved_stage_read_joins_writer_once(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_owner_stage as module
    ledger,stage=written(admitted);calls=[];transport=admitted[2];original=transport.get
    def get(*args,**kwargs):calls.append(args[0]);return original(*args,**kwargs)
    monkeypatch.setattr(transport,'get',get)
    result=module.verify(ledger,stage)
    assert result['completed_pairs']==1 and result['execution_admitted'] is False
    assert len(calls)==1 and ledger._reads=={'dictionary':1}
    claim=ledger._operations['reader-dictionary-0000']
    attempt=module.attempt_path(ledger,claim)
    assert attempt.parent==ledger.root.parent and not attempt.is_relative_to(stage.root)
    raw=(attempt/'complete.json').read_bytes()
    assert json.loads(raw)==thaw(result)
    assert json.loads(claim._terminal['complete.json'])['reference_sha256']==module.io._hash(raw)
    assert ledger.reserved['decoded_transfer_bytes']==4*200*168
    ledger.close()


def test_corrupt_archive_spends_read_and_preserves_writer(admitted):
    from tradingagents.research.onchain_replication import archive_owner_stage as module
    ledger,stage=written(admitted);writer=ledger._writers['dictionary']
    before={p.name:p.read_bytes() for p in writer.root.iterdir()};admitted[2].corrupt=True
    with pytest.raises(ValueError):module.verify(ledger,stage)
    claim=ledger._operations['reader-dictionary-0000']
    assert (claim.root/'failed.json').is_file() and ledger.owner.poisoned
    assert before=={p.name:p.read_bytes() for p in writer.root.iterdir()}
    assert ledger.reserved['decoded_transfer_bytes']==4*200*168
    ledger.close()


@pytest.mark.parametrize('target',['terminal','outer'])
def test_completion_callback_mutation_retains_both_terminals(admitted,monkeypatch,target):
    from tradingagents.research.onchain_replication import archive_owner_stage as module
    ledger,stage=written(admitted);owner=ledger.owner;original=owner.lease
    def lease():
        original()
        claim=ledger._operations.get('reader-dictionary-0000')
        if claim is not None and (claim.root/'complete.json').exists():
            (stage.root/('matching/terminal.json' if target=='terminal' else 'foreign.bin')).write_bytes(b'{}')
    monkeypatch.setattr(owner,'lease',lease)
    with pytest.raises(ValueError):module.verify(ledger,stage)
    claim=ledger._operations['reader-dictionary-0000']
    assert set(claim._terminal)=={'complete.json','failed.json'} and owner.poisoned
    assert ledger.reserved['decoded_transfer_bytes']==4*200*168
    monkeypatch.setattr(owner,'lease',original);ledger.close()
