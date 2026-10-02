"""Read-only local joins retain a trusted earlier full remote observation."""
import json
import pytest
from tests.research.onchain_replication.test_archived_stage import fixture


def verified(tmp_path,monkeypatch,kind='mcm'):
    module,root,contract=fixture(tmp_path,monkeypatch,kind)
    result=module.verify(root,**contract)
    expected=module.io._hash((contract['attempt']/'complete.json').read_bytes())
    return module,root,contract,result,expected


def tree(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('kind',['dictionary','mcm'])
def test_local_check_never_fetches_or_publishes(tmp_path,monkeypatch,kind):
    module,root,c,result,expected=verified(tmp_path,monkeypatch,kind)
    before=tree(tmp_path)
    def forbidden(*args,**kwargs):raise AssertionError('local check must not transfer or publish')
    for name in ('get','put','mkdir'):monkeypatch.setattr(c['transport'],name,forbidden)
    monkeypatch.setattr(module.io,'_write',forbidden)
    got=module.check(root,attempt=c['attempt'],expected_sha256=expected,
        transport=c['transport'],lease=lambda:None)
    assert got==result and got['schema_version']==2
    assert tree(tmp_path)==before


@pytest.mark.parametrize('target',['intent','event_intent','event_complete','checkpoint','score','reference','source','extra','failed'])
def test_final_lease_mutation_rejects_without_rewriting_proof(tmp_path,monkeypatch,target):
    module,root,c,result,expected=verified(tmp_path,monkeypatch)
    calls=[];mutated=[]
    def lease():
        calls.append(1)
        if len(calls)!=2:return
        paths={'intent':c['attempt']/'intent.json','event_intent':c['attempt']/'events/intent.json',
            'event_complete':c['attempt']/'events/complete.json',
            'checkpoint':next((root/'checkpoints').glob('*/state/annealing/M.npy')),
            'score':root/'stream/batches/chunk-000000000000.bin',
            'reference':c['attempt']/'checkpoint-references.bin','source':root/'matching/terminal.json',
            'extra':c['attempt']/'unexpected','failed':c['attempt']/'failed.json'}
        paths[target].write_bytes(b'{}');mutated.append(tree(tmp_path))
    with pytest.raises((ValueError,UnicodeError)):
        module.check(root,attempt=c['attempt'],expected_sha256=expected,transport=c['transport'],lease=lease)
    assert len(mutated)==1 and tree(tmp_path)==mutated[0]


@pytest.mark.parametrize('target',['v1','unknown','policy','replay'])
def test_even_caller_rehashed_invalid_proof_is_refused(tmp_path,monkeypatch,target):
    module,root,c,result,expected=verified(tmp_path,monkeypatch)
    path=c['attempt']/'complete.json'
    if target=='v1':result['schema_version']=1;result['format']='archived-compact-stage-v1'
    if target=='unknown':result['unrecognized']=True
    if target=='policy':
        intent=json.loads((c['attempt']/'intent.json').read_bytes());intent['max_stage_bytes']=1
        raw=module.io._json(intent);(c['attempt']/'intent.json').write_bytes(raw)
        result['stage_read_intent_sha256']=module.io._hash(raw)
    if target=='replay':
        item=c['attempt']/'events/complete.json';record=json.loads(item.read_bytes())
        record['replay']['completed_pairs']+=1;raw=module.io._json(record);item.write_bytes(raw)
        result['event_read_complete_sha256']=module.io._hash(raw)
    raw=module.io._json(result);path.write_bytes(raw);before=tree(tmp_path)
    with pytest.raises(ValueError):
        module.check(root,attempt=c['attempt'],expected_sha256=module.io._hash(raw),
            transport=c['transport'],lease=lambda:None)
    assert tree(tmp_path)==before
