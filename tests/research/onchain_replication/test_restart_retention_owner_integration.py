"""Actual-owner synthetic retention route. Run only from an immutable source copy."""
import json
from types import SimpleNamespace
import pytest
from tests.research.onchain_replication import test_archive_producer_integration as archive
from tests.research.onchain_replication.test_restart_retention_integration import retention_policy


@pytest.fixture
def admitted(monkeypatch,tmp_path,request):
    native=archive.native
    training=native.upstream.upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    option=getattr(request,'param','valid')
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            policy=retention_policy();t.input('restart_retention',policy)
            envelope=json.loads((t.root/'compact_policy.json').read_bytes())
            envelope['stage_policy']['restart_retention']=policy
            envelope['stage_policy']['schedule']['calls_per_checkpoint']=2
            envelope['stage_policy']['max_retained_logical_bytes']=100000000
            envelope['max_workflow_retained_logical_bytes']=1000000000
            t.input('compact_policy',envelope)
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_restart_retention_input']='restart_retention'
                item['descriptor']['compact_restart_retention_execution']={'backend':policy['format'],
                    'policy_sha256':t.exp['inputs']['restart_retention']['sha256']}
                item['descriptor']['compact_execution']['policy_sha256']=t.exp['inputs']['compact_policy']['sha256']
            if option=='hash':t.item['descriptor']['compact_restart_retention_execution']['policy_sha256']='0'*64
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=archive.admitted.__wrapped__(monkeypatch,tmp_path,SimpleNamespace(param='capacity'))
    values=next(gen)
    try:yield values
    finally:gen.close()


def test_actual_owner_retention_dictionary_mcm_terminal_and_original_pins(admitted,monkeypatch):
    t,job,graphs,examples,transport=admitted
    from tradingagents.research.onchain_replication import compact_matcher,stage_retention
    from tradingagents.research.onchain_replication.provenance import thaw
    original=compact_matcher.engine.advance;calls=0
    def advance(state,a,b,config,*,max_operations):
        nonlocal calls
        # Forced boundary coverage: six reduced-work calls span three
        # two-call checkpoints; this is not production cadence evidence.
        amount=1 if calls<6 else max_operations;calls+=1
        return original(state,a,b,config,max_operations=amount)
    monkeypatch.setattr(compact_matcher.engine,'advance',advance)
    prepared,terminal=archive.native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    owner=terminal._owner;ledger=owner._archive_operations
    assert owner.closed and ledger._closed and not ledger._poisoned
    dictionary=owner.stages['dictionary'];assert dictionary.contract['pairs']==20 and dictionary.pairs==22
    record=json.loads((dictionary.root/'checkpoints/seal.json').read_bytes())
    assert record['progress_events']==3 and record['stores']==1 and record['completed_pairs']==20
    selected=[json.loads(p.read_bytes()) for p in sorted((dictionary.root/'checkpoints').glob('selected-*.json'))]
    assert [p['disposition'] for p in selected]==['first_checkpoint_retained','completed_before_first_scheduled_checkpoint']
    assert len(list((dictionary.root/'checkpoints/stores').rglob('*.npy')))==3
    for name,stage in owner.stages.items():
        assert stage.contract['retention']['seal_sha256']==stage_retention._reference(stage)['seal_sha256']
        assert stage.contract['retention']['spent']['generations']<=10
        if name!='dictionary':
            assert stage.contract['pairs']==6 and stage.pairs==6
            assert stage.contract['retention']['spent']['stores']==0
    spending=thaw(ledger.reserved)
    originals={p:p.read_bytes() for p in ledger.root.rglob('*.json')}
    def forbidden(*args,**kwargs):raise AssertionError('postclose remote transfer')
    transport.mkdir=transport.put=transport.get=forbidden
    terminal.check();archive.native.api().finalize(prepared)
    with pytest.raises(ValueError):archive.native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    assert thaw(ledger.reserved)==spending and all(p.read_bytes()==raw for p,raw in originals.items())
    seal=dictionary.root/'checkpoints/seal.json';original_raw=seal.read_bytes();changed=json.loads(original_raw)
    changed['spent']['control_bytes']-=1;seal.write_text(json.dumps(changed))
    with pytest.raises(ValueError):terminal.check()
    seal.write_bytes(original_raw)
    (dictionary.root/'checkpoints/foreign').mkdir()
    with pytest.raises(ValueError):terminal.check()


@pytest.mark.parametrize('admitted',['hash'],indirect=True)
def test_retention_descriptor_refuses_before_new_owner(admitted):
    t,job,graphs,examples,transport=admitted
    with pytest.raises(ValueError):archive.native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    assert not t.directory.exists()


def test_late_mcm_retirement_failure_retains_prior_reader_writer_and_closed_spending(admitted,monkeypatch):
    t,job,graphs,examples,transport=admitted
    from tradingagents.research.onchain_replication import compact_matcher,stage_retention,restart_retention,archive_owner_stage
    from tradingagents.research.onchain_replication.provenance import thaw
    advance=compact_matcher.engine.advance;begin=stage_retention.Controller.begin
    read=archive_owner_stage._execute_locked;unlink=restart_retention.os.unlink
    state={'calls':0,'armed':False}
    def started(controller,purpose,*args):
        result=begin(controller,purpose,*args)
        if purpose['kind']=='mcm' and not state['armed']:
            state.update(armed=True,controller=controller)
        return result
    def forced(s,a,b,c,*,max_operations):
        if state['armed']:
            amount=1 if state['calls']<6 else max_operations;state['calls']+=1
        else:amount=max_operations
        return advance(s,a,b,c,max_operations=amount)
    def verified(ledger,stage,**kwargs):
        result=read(ledger,stage,**kwargs)
        if stage.kind=='dictionary':
            state.update(ledger=ledger,prior=thaw(ledger.reserved),
                claims={p:p.read_bytes() for op in ledger._operations.values() for p in op.root.glob('*.json')})
        return result
    def refused(path,*args,**kwargs):
        if state['armed'] and str(path).endswith('.npy'):raise OSError('synthetic MCM retirement refusal')
        return unlink(path,*args,**kwargs)
    monkeypatch.setattr(stage_retention.Controller,'begin',started)
    monkeypatch.setattr(compact_matcher.engine,'advance',forced)
    monkeypatch.setattr(archive_owner_stage,'_execute_locked',verified)
    monkeypatch.setattr(restart_retention.os,'unlink',refused)
    try:
        with pytest.raises(archive.native.api().CompactProducerError):
            archive.native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    finally:monkeypatch.setattr(restart_retention.os,'unlink',unlink)
    ledger=state['ledger'];controller=state['controller']
    assert ledger._closed and ledger._poisoned and ledger.owner.poisoned
    assert all(p.read_bytes()==raw for p,raw in state['claims'].items())
    assert all(ledger.reserved[k]>=v for k,v in state['prior'].items())
    closed=json.loads((ledger.root/'closed.json').read_bytes())
    assert closed['poisoned'] and closed['reserved']==thaw(ledger.reserved)
    assert controller.spent['generations']==2 and (controller.root/'failed.json').exists()
    root=next((controller.root/'stores').iterdir())
    assert len(list(root.rglob('*.npy')))==9
    assert (root/'retire-00000000000000000000-intent.json').exists()
    assert not (root/'retire-00000000000000000000-complete.json').exists()
    assert not (ledger.owner.root/'complete.json').exists()
    assert not (ledger.owner.root.parent/'complete.json').exists()
