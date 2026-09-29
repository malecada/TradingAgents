"""Actual admitted synthetic representation production/reuse with batch loading."""
import copy
import json
import weakref
import numpy as np
import pytest
import torch

from tests.research.test_lifecycle import registered,start,commit
from tests.research.onchain_replication.test_registered_features import prepared_registration,produce
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash
from tradingagents.research.onchain_replication.registered_features import reuse_registered_features


def setup(registered,policy=None,arm='gin'):
    fixture,args,descriptor=prepared_registration(registered);root,spec,_=fixture
    if arm!='gin':
        from tradingagents.research.onchain_replication.registered_features import representation_descriptor
        graphs,examples,fold,_,seed,config=args
        # Bounded synthetic fixture settings; frozen empirical settings unchanged.
        config['dictionary']['sample_count']=32
        config['baselines']['graph']['watchyourstep']['epochs']=2
        descriptor=representation_descriptor(graphs,examples,fold,arm,seed,config)
        args=graphs,examples,fold,arm,seed,config
    value=policy if policy is not None else {'schema_version':1,'mode':'batch','max_unique_feature_bytes':1024**2}
    p=root/'feature-residency.json';p.write_bytes(canonical_bytes(value))
    spec['experiments']['example-a']['inputs']['residency']={'path':str(p.relative_to(root)),'sha256':file_hash(p),'dataset':'sample'}
    p=root/'feature-plan.json';plan=json.loads(p.read_bytes());plan['producers']['gin11']['residency_input']='residency'
    plan['producers']['gin11']['descriptor']=descriptor
    p.write_bytes(canonical_bytes(plan));spec['experiments']['example-a']['inputs']['feature-plan']['sha256']=file_hash(p)
    return (root,spec,commit(root,spec)),args,descriptor


@pytest.mark.parametrize('arm',['gin','proposed'])
def test_registered_streaming_production_reuse_and_joint_updates_match_eager(registered,arm):
    from tradingagents.research.onchain_replication.feature_residency import FixedFeatureMap
    from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
    from tradingagents.research.onchain_replication.model_registry import build_model
    from tests.research.onchain_replication.test_model import cfg
    fixture,args,descriptor=setup(registered,arm=arm)
    expected=prepare_features(*args,max_entries=100000,checkpoint=lambda *a:None)
    with start(fixture) as run:
        result,path=produce(run,args,residency_input='residency')
        assert isinstance(result.features,FixedFeatureMap) and result.binding==expected.binding
        reused=reuse_registered_features(run,None,descriptor,max_array_bytes=1024**2,journal_output='journal.json',residency_input='residency')
        assert reused.binding==expected.binding
        keys=list(expected.features)[:2]
        def update(features):
            torch.manual_seed(11);model=build_model(arm,'direction',{**cfg(),'graph_activation_checkpointing':True})
            optimizer=torch.optim.Adam(model.parameters(),lr=.001)
            selected=features.load_batch(keys) if isinstance(features,FixedFeatureMap) else features
            inputs=[[selected[keys[0]],selected[keys[1]],selected[keys[0]]]]
            output=model(inputs,torch.zeros(1,3,1))
            torch.nn.functional.cross_entropy(output,torch.tensor([1])).backward()
            grads={k:v.grad.clone() for k,v in model.named_parameters()};optimizer.step()
            return output.detach(),grads,model.state_dict()
        eager=update(expected.features);lazy=update(reused.features)
        torch.testing.assert_close(eager[0],lazy[0],rtol=0,atol=0)
        for section in (1,2):
            for name in eager[section]:torch.testing.assert_close(eager[section][name],lazy[section][name],rtol=0,atol=0)


@pytest.mark.parametrize('fault',['undeclared','negative_bound','wrong_mode'])
def test_bad_residency_policy_fails_before_representation_claim(registered,fault):
    policy={'schema_version':1,'mode':'batch','max_unique_feature_bytes':-1 if fault=='negative_bound' else 1024**2}
    if fault=='wrong_mode':policy['mode']='anything'
    fixture,args,_=setup(registered,policy);root,_,_=fixture
    with start(fixture) as run:
        with pytest.raises(ValueError,match='residency|batch|policy'):
            produce(run,args,residency_input=None if fault=='undeclared' else 'residency')
        assert not (root/'research_artifacts/onchain_representations').exists()


@pytest.mark.parametrize('arm',['gin','watchyourstep'])
def test_failed_streamed_parent_reuses_completed_graph_without_republication(registered,monkeypatch,arm):
    import tradingagents.research.onchain_replication.registered_features as module
    fixture,args,descriptor=setup(registered,arm=arm);root,spec,_=fixture;original=module.prepare_features
    expected=original(*args,max_entries=100000,checkpoint=lambda *a:None)
    def interrupted(*args,checkpoint,**kwargs):
        def callback(stage,context,payload):
            checkpoint(stage,context,payload)
            if stage=='graph_complete':raise InterruptedError('synthetic streaming interruption')
        return original(*args,checkpoint=callback,**kwargs)
    monkeypatch.setattr(module,'prepare_features',interrupted)
    with start(fixture) as run:
        with pytest.raises(InterruptedError):produce(run,args,residency_input='residency')
    path=next((root/'research_artifacts/onchain_representations').glob('*/example-a/failed.json'))
    prior=json.loads(path.read_bytes())['events'][0]['context']['graph_hash']
    child=copy.deepcopy(spec['experiments']['example-a']);child['parent']='example-a'
    child['inputs']['prior-features']={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
    spec['experiments']['example-b']=child;source=commit(root,spec)
    monkeypatch.setattr(module,'prepare_features',original)
    with start((root,spec,source),experiment='example-b') as run:
        result,path=produce(run,args,residency_input='residency',continuation_input='prior-features')
        events=json.loads(path.read_bytes())['events']
        written=[e['context']['graph_hash'] for e in events if e['stage']=='graph_complete']
        # Fixture: 104 causal alignment weeks, but only 10 scored GIN weeks.
        assert prior not in written and len(written)==(103 if arm=='watchyourstep' else 9)
        assert result.features.verified_hashes()==result.binding['feature_hashes']
        assert result.binding==expected.binding


@pytest.mark.parametrize('training',[False,True])
def test_engine_releases_previous_input_before_requesting_next_batch(registered,training):
    from tests.research.onchain_replication.test_training import P,CFG
    from tradingagents.research.onchain_replication.training import fit_cell,predict_cell
    refs=[]
    def batch(indices):
        assert all(ref() is None for ref in refs), 'previous batch remains live while next batch loads'
        x=torch.ones(len(indices),2);refs.append(weakref.ref(x))
        return {'input':x},torch.ones(len(indices),1)
    if training:
        with start(registered) as run:
            fit_cell(run,'sum',{**P,'source_commit':run.admission.source},lambda:torch.nn.Linear(2,1),batch,4,'regression',11,{**CFG,'epochs':2})
    else:predict_cell(torch.nn.Linear(2,1),batch,4,2)
    assert all(ref() is None for ref in refs)


@pytest.mark.parametrize('batch_bound',[1,1024**2])
def test_registered_job_uses_policy_and_retains_independent_cell_dispositions(registered,batch_bound):
    from tests.research.onchain_replication.test_run import setup as setup_batch,register_plan
    from tests.research.onchain_replication.test_dataset import fixture as source_fixture
    from tests.research.onchain_replication.test_feature_pipeline import configs
    from tradingagents.research.onchain_replication.graph_store import save_graph
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash
    from tradingagents.research.onchain_replication.registered_features import representation_descriptor
    from tradingagents.research.onchain_replication.job_payload import population_record,execute_fit_payload
    registration,populations,plan=setup_batch(registered);root,spec,_=registration
    graphs,_,fold,_=source_fixture();examples,scaler=populations['whole']
    required={h for row in (*examples.train,*examples.test) for h in row.graph_hashes}
    graphs=[g for g in graphs if graph_hash(g) in required]
    descriptor=representation_descriptor(graphs,examples,fold,'gin',11,configs());refs={}
    for i,g in enumerate(graphs):
        path=save_graph(root/'graphs'/str(i),g);name='graph_'+str(i)
        spec['experiments']['example-a']['inputs'][name]={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
        refs[graph_hash(g)]={'input':name}
    producer={'descriptor':descriptor,'graphs':refs,'max_entries':100000,'max_array_bytes':1024**2,
        'binding_output':'gin-binding.json','journal_output':'gin-journal.json','residency_input':'residency'}
    plan['cells'][0]['cell']['arm']='gin';plan['cells'][0]['representation']='gin-11'
    plan['representations']['gin-11']={'output':'gin-binding.json','failure_output':'gin-failed.json'}
    spec['experiments']['example-a']['outputs']+=['gin-binding.json','gin-journal.json','gin-failed.json']
    payload={'population_inputs':{'whole':'population'},'batch_plan_input':'batch_plan',
        'representation_jobs':{'gin-11':{'operation':'produce','descriptor':descriptor,'plan_input':'representation_plan',
        'producer':'gin-11','population':'whole','max_graph_payload_bytes':10*1024**2,'residency_input':'residency'}}}
    registration=register_plan((root,spec,None),plan,[('population',population_record(examples,scaler)),
        ('representation_plan',{'schema_version':1,'producers':{'gin-11':producer}}),
        ('execution_job',{'kind':'fit','payload':payload}),
        ('residency',{'schema_version':1,'mode':'batch','max_unique_feature_bytes':batch_bound})])
    with start(registration) as run:
        rows,_=execute_fit_payload(run,payload)
        assert [r['status'] for r in rows]==['complete' if batch_bound>1 else 'failed','complete','unavailable']
        if batch_bound==1:assert 'batch feature array bound' in rows[0]['reason']
        assert json.loads((run.directory/'outputs/gin-failed.json').read_bytes())['status']=='complete'
        assert list((root/'research_artifacts/onchain_representations').glob('*/example-a/complete.json'))
