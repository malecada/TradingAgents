"""Executor selection and final acceptance hooks; producers/fits are stubbed."""
import pytest
from tests.research.test_lifecycle import registered, start
from tests.research.onchain_replication.test_run import setup, register_plan
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_feature_pipeline import configs
from tradingagents.research.onchain_replication.job_payload import population_record, execute_fit_payload
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.feature_pipeline import PreparedFeatures
from tradingagents.research.onchain_replication.cache import cache_key


@pytest.mark.parametrize('fault',[None,'producer','final'])
def test_compact_dispatch_uses_resident_loader_and_checks_after_batch(registered,monkeypatch,fault):
    from tradingagents.research.onchain_replication import compact_native_producer as compact
    from tradingagents.research.onchain_replication import native_producer, graph_store, run as batch
    registered,populations,plan=setup(registered);root,spec,_=registered
    graphs,_,fold,_=fixture();examples,scaler=populations['whole']
    required={h for row in (*examples.train,*examples.test) for h in row.graph_hashes}
    graphs=[g for g in graphs if graph_hash(g) in required]
    descriptor=representation_descriptor(graphs,examples,fold,'proposed',11,configs())
    refs={}
    for i,g in enumerate(graphs):
        path=save_graph(root/'graphs'/str(i),g);name='graph_'+str(i)
        spec['experiments']['example-a']['inputs'][name]={'path':str(path.relative_to(root)),
            'sha256':file_hash(path),'dataset':'sample'}
        refs[graph_hash(g)]={'input':name}
    producer={'descriptor':descriptor,'graphs':refs,'binding_output':'compact-binding.json',
        'journal_output':'compact-journal.json'}
    plan['cells'][0]['cell']['arm']='proposed';plan['cells'][0]['representation']='compact'
    plan['representations']['compact']={'output':'compact-binding.json','failure_output':'compact-failed.json'}
    spec['experiments']['example-a']['outputs']+=['compact-binding.json','compact-journal.json','compact-failed.json']
    payload={'population_inputs':{'whole':'population'},'batch_plan_input':'batch_plan',
        'representation_jobs':{'compact':{'operation':'produce','native_backend':compact.BACKEND,
            'descriptor':descriptor,'plan_input':'representation_plan','producer':'compact',
            'population':'whole','max_graph_payload_bytes':1048576}}}
    registered=register_plan((root,spec,None),plan,[('population',population_record(examples,scaler)),
        ('representation_plan',{'schema_version':2,'producers':{'compact':producer}}),
        ('execution_job',{'kind':'fit','payload':payload})])
    events=[];actual_loader=graph_store.load_graph
    def load(path,sha,**kw):
        assert kw=={'resident':True};events.append('load');return actual_loader(path,sha,**kw)
    def produce(run,name,job,loaded,population):
        events.append('produce')
        if fault=='producer':raise compact.CompactProducerError('synthetic fatal producer')
        value=PreparedFeatures({}, {'workflow_identity':cache_key(descriptor)},None)
        run.write_json('compact-binding.json',value.binding);run.write_json('compact-journal.json',{'synthetic':True})
        return value,object()
    def finalize(value):
        events.append('check')
        if fault=='final' and 'batch' in events:raise ValueError('synthetic final evidence changed')
    def execute(*args,**kw):events.append('batch');return 'synthetic completed batch'
    monkeypatch.setattr(compact,'selected',lambda *args:True)
    monkeypatch.setattr(native_producer,'selected',lambda *args:pytest.fail('compact route reached old selector'))
    monkeypatch.setattr(compact,'produce',produce);monkeypatch.setattr(compact,'finalize',finalize)
    monkeypatch.setattr(graph_store,'load_graph',load);monkeypatch.setattr(batch,'execute_batch',execute)
    run=start(registered)
    try:
        if fault=='producer':
            with pytest.raises(compact.CompactProducerError):execute_fit_payload(run,payload)
            assert 'batch' not in events
        elif fault=='final':
            with pytest.raises(ValueError,match='final evidence'):execute_fit_payload(run,payload)
            assert events[-3:]==['check','batch','check']
        else:
            assert execute_fit_payload(run,payload)=='synthetic completed batch'
            assert events[-3:]==['check','batch','check']
        assert 'load' in events and 'produce' in events
    finally:run.fail('synthetic dispatch fixture closed')
