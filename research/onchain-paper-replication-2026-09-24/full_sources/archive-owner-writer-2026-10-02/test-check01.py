"""Reserved current-owner archive execution with actual tiny matching engines."""
import json
import pytest
from tests.research.onchain_replication.test_archive_owner_policy import admitted, select
from tests.research.onchain_replication.test_matching_reference import graph
from tradingagents.research.onchain_replication import archive_owner_operations, compact_matcher
from tradingagents.research.onchain_replication.provenance import thaw
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.cache import cache_key

pytestmark = pytest.mark.parametrize('admitted',['writer_matching'],indirect=True)


def setup(admitted,pairs):
    from tradingagents.research.onchain_replication import archive_owner_writer
    ledger = archive_owner_operations.attach(select(admitted))
    stage = admitted[1].begin('dictionary',workload_sha256='d'*64,pairs=pairs)
    return archive_owner_writer,ledger,stage


def test_actual_matching_rotates_archive_under_reserved_writer(admitted):
    module,ledger,stage = setup(admitted,9);owner = admitted[1]
    a = graph([[0.],[.3]],[(0,1,.1)]);b = graph([[.2],[.7]],[(1,0,.4)])
    expected = match_reference(a,b,thaw(owner.matching)).score
    def produce(log,lease):
        p = thaw(owner.policy)
        matcher = compact_matcher.CompactMatcher(log,config=thaw(owner.matching),
            context=thaw(owner.bound.context),policy=p['pair'],workload_sha256='d'*64,
            schedule=p['schedule'],lease=lease)
        results = []
        for i in range(9):
            purpose = {'schema_version':1,'kind':'dictionary','workload_sha256':'d'*64,
                'typed_graphs':[graph_identity(a),graph_identity(b)],'fixture_pair':i}
            got = matcher(purpose,a,b)
            assert got == {'purpose_sha256':cache_key(purpose),'score':expected}
            results.append(got['score'])
        return results
    values,receipt = module.run(ledger,stage,produce)
    assert values == [expected]*9 and receipt['completed_pairs'] == 9
    assert receipt['execution_admitted'] is False
    assert sorted(p.stat().st_size for p in admitted[2].root.rglob('payload.bin')) == [336,2688]
    assert not list((stage.root/'matching').rglob('*.bin'))
    claim = ledger._writers['dictionary']
    completed = json.loads((claim.root/'complete.json').read_bytes())
    assert completed['reference_sha256'] == receipt['archive_complete_sha256']
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    before = {str(p):p.read_bytes() for p in ledger.root.rglob('*.json')}
    with pytest.raises(ValueError):module.run(ledger,stage,produce)
    assert before == {str(p):p.read_bytes() for p in ledger.root.rglob('*.json')}
    ledger.close()


def test_callback_failure_preserves_actual_log_and_claim(admitted):
    module,ledger,stage = setup(admitted,1)
    primary = RuntimeError('numerical callback interrupted')
    def produce(log,lease):
        log.begin('a'*64,'b'*64)
        raise primary
    with pytest.raises(RuntimeError) as caught:module.run(ledger,stage,produce)
    assert caught.value is primary
    assert (stage.root/'matching/failed.json').is_file()
    assert (ledger._writers['dictionary'].root/'failed.json').is_file()
    assert list((stage.root/'matching').glob('*.bin'))
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    ledger.close()


def test_final_reservation_callback_cannot_invalidate_writer_evidence(admitted,monkeypatch):
    module,ledger,stage = setup(admitted,0);owner=admitted[1];original=owner.lease
    def lease():
        original()
        claim = ledger._writers.get('dictionary')
        if claim is not None and (claim.root/'complete.json').exists():
            (stage.root/'matching/terminal.json').write_bytes(b'{}')
    monkeypatch.setattr(owner,'lease',lease)
    with pytest.raises(ValueError):module.run(ledger,stage,lambda log,lease:None)
    assert (ledger._writers['dictionary'].root/'failed.json').exists()
    assert owner.poisoned
    ledger.close()


def test_callback_cannot_reenter_transition_or_reuse_expired_lease(admitted):
    module,ledger,stage = setup(admitted,0);saved=[]
    def produce(log,lease):
        saved.append(lease);lease()
        with pytest.raises(ValueError):module.run(ledger,stage,lambda *_:None)
        return 'caller-value'
    value,receipt = module.run(ledger,stage,produce)
    assert value == 'caller-value' and receipt['completed_pairs'] == 0
    with pytest.raises(ValueError):saved[0]()
    ledger.close()
