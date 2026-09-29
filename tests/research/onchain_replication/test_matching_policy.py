"""Score-only execution admission, exact outputs and preserved failed lineage."""
import copy
import json
import pytest

from tests.research.test_lifecycle import registered, start, commit
from tests.research.onchain_replication.test_registered_features import prepared_registration
from tradingagents.research.onchain_replication.registered_features import representation_descriptor, prepare_registered_features
from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash


def setup(registered, policy=None):
    fixture,args,_=prepared_registration(registered); root,spec,_=fixture
    graphs,examples,fold,_,seed,configs=args
    configs=copy.deepcopy(configs); configs['dictionary'].update(sample_count=2,size=2)
    args=(graphs,examples,fold,'proposed',seed,configs)
    descriptor=representation_descriptor(*args)
    path=root/'feature-plan.json'; plan=json.loads(path.read_bytes())
    item=plan['producers'].pop('gin11'); item.update(descriptor=descriptor,matching_input='matching')
    plan['producers']['proposed11']=item
    path.write_bytes(canonical_bytes(plan)); spec['experiments']['example-a']['inputs']['feature-plan']['sha256']=file_hash(path)
    path=root/'matching-policy.json'; path.write_bytes(canonical_bytes(policy if policy is not None else {'schema_version':1,'mode':'score_only'}))
    spec['experiments']['example-a']['inputs']['matching']={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
    return (root,spec,commit(root,spec)),args


def produce(run,args,**kwargs):
    return prepare_registered_features(run,'proposed11',*args,plan_input='feature-plan',
        max_entries=100000,max_array_bytes=1024**2,matching_input='matching',**kwargs)


def test_admitted_score_only_preserves_binding_and_avoids_diagnostics(registered,monkeypatch):
    import tradingagents.research.onchain_replication.matching as matching
    fixture,args=setup(registered)
    baseline=prepare_features(*args,max_entries=100000,checkpoint=lambda *a:None)
    monkeypatch.setattr(matching,'MatchResult',lambda *a,**k:pytest.fail('score-only retained diagnostics'))
    with start(fixture) as run:
        result,path=produce(run,args)
        assert result.binding==baseline.binding
        assert result.dictionary.identity==baseline.dictionary.identity
        claim=json.loads((path.parent/'claim.json').read_bytes())
        assert claim['matching_input']=='matching'
        assert claim['matching_policy_sha256']==run.admission.inputs['matching']['sha256']


@pytest.mark.parametrize('policy',[{}, {'schema_version':True,'mode':'score_only'},
    {'schema_version':2,'mode':'score_only'}, {'schema_version':1,'mode':'other'},
    {'schema_version':1,'mode':'score_only','max_pair_entries':99999999}])
def test_invalid_policy_rejected_before_claim(registered,policy):
    fixture,args=setup(registered,policy); root,_,_=fixture
    with start(fixture) as run:
        with pytest.raises(ValueError,match='matching'):produce(run,args)
        assert not (root/'research_artifacts/onchain_representations').exists()


def test_planned_policy_cannot_be_omitted(registered):
    fixture,args=setup(registered); root,_,_=fixture
    with start(fixture) as run:
        with pytest.raises(ValueError,match='matching'):
            prepare_registered_features(run,'proposed11',*args,plan_input='feature-plan',max_entries=100000,max_array_bytes=1024**2)
        assert not (root/'research_artifacts/onchain_representations').exists()


def test_policy_hash_drift_rejected_before_claim(registered):
    fixture,args=setup(registered); root,_,_=fixture
    with start(fixture) as run:
        (root/'matching-policy.json').write_bytes(canonical_bytes({'schema_version':1,'mode':'other'}))
        with pytest.raises(ValueError):produce(run,args)
        assert not (root/'research_artifacts/onchain_representations').exists()


@pytest.mark.parametrize('option',[1,'yes',True])
def test_component_rejects_invalid_or_unused_score_option_before_graph_access(option):
    with pytest.raises(ValueError,match='matching'):
        prepare_features(None,None,None,'gin',11,{},max_entries=10,checkpoint=lambda *a:None,score_only=option)


@pytest.mark.parametrize('fault',['invalid','mismatch','omitted','reuse','non_mcm','later_job'])
def test_job_matching_preflight_precedes_population_production(fault,monkeypatch):
    from tradingagents.research.onchain_replication.job_payload import execute_fit_payload
    import tradingagents.research.onchain_replication.population_assembly as assembly
    job={'operation':'reuse' if fault=='reuse' else 'produce','matching_input':'matching',
         'plan_input':'plan','producer':'p','descriptor':{'arm':'gin' if fault=='non_mcm' else 'proposed'}}
    if fault=='omitted':job.pop('matching_input')
    jobs={'p':job}
    if fault=='later_job':jobs={'first':{**job,'matching_input':None,'producer':'first'},'p':job}
    payload={'population_inputs':{'whole':{'producer_input':'population-plan'}},'batch_plan_input':'batch','representation_jobs':jobs}
    values={'execution_job':{'kind':'fit','payload':payload},
        'matching':{'schema_version':1,'mode':'invalid' if fault in {'invalid','later_job'} else 'score_only'},
        'plan':{'producers':{'p':{'matching_input':'other' if fault=='mismatch' else 'matching'},'first':{}}}}
    class Run:
        def read_input(self,name):return canonical_bytes(values[name])
    monkeypatch.setattr(assembly,'produce_registered_population',lambda *a:pytest.fail('population executed before policy preflight'))
    with pytest.raises(ValueError,match='matching'):execute_fit_payload(Run(),payload)


def test_failed_default_checkpoint_continues_score_only_without_resampling(registered,monkeypatch):
    import tradingagents.research.onchain_replication.registered_features as module
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    fixture,args=setup(registered); root,spec,_=fixture
    baseline=prepare_features(*args,max_entries=100000,checkpoint=lambda *a:None)
    plan_path=root/'feature-plan.json'; plan=json.loads(plan_path.read_bytes())
    plan['producers']['proposed11'].pop('matching_input'); plan_path.write_bytes(canonical_bytes(plan))
    spec['experiments']['example-a']['inputs']['feature-plan']['sha256']=file_hash(plan_path)
    source=commit(root,spec); original=module.prepare_features
    def interrupted(*a,checkpoint,**kw):
        def save(stage,context,payload):
            checkpoint(stage,context,payload)
            if stage=='graph_complete':raise InterruptedError('after durable completed graph')
        return original(*a,checkpoint=save,**kw)
    monkeypatch.setattr(module,'prepare_features',interrupted)
    with start((root,spec,source)) as run:
        with pytest.raises(InterruptedError):
            prepare_registered_features(run,'proposed11',*args,plan_input='feature-plan',max_entries=100000,max_array_bytes=1024**2)
    failed,=list((root/'research_artifacts/onchain_representations').glob('*/example-a/failed.json'))
    failed_hash=file_hash(failed)
    child=copy.deepcopy(spec['experiments']['example-a']); child['parent']='example-a'
    child['inputs']['prior']={'path':str(failed.relative_to(root)),'sha256':failed_hash,'dataset':'sample'}
    plan['producers']['proposed11']['matching_input']='matching'
    new_plan=root/'feature-plan-b.json';new_plan.write_bytes(canonical_bytes(plan))
    child['inputs']['feature-plan']={'path':str(new_plan.relative_to(root)),'sha256':file_hash(new_plan),'dataset':'sample'}
    spec['experiments']['example-b']=child; source=commit(root,spec)
    monkeypatch.setattr(module,'prepare_features',original)
    monkeypatch.setattr(pipeline,'sample_neighborhoods',lambda *a,**k:pytest.fail('resampled'))
    monkeypatch.setattr(pipeline,'fit_dictionary',lambda *a,**k:pytest.fail('dictionary refitted'))
    with start((root,spec,source),experiment='example-b') as run:
        result,path=produce(run,args,continuation_input='prior')
        assert result.binding==baseline.binding and result.dictionary.identity==baseline.dictionary.identity
        events=json.loads(path.read_bytes())['events']
        assert sum(e['stage']=='graph_complete' for e in events)==len(result.features)-1
        assert file_hash(failed)==failed_hash


def test_valid_job_delivers_score_only_features_to_batch(registered,monkeypatch):
    from tests.research.onchain_replication.test_run import setup as batch_setup, register_plan
    from tests.research.onchain_replication.test_dataset import fixture as dataset_fixture
    from tests.research.onchain_replication.test_feature_pipeline import configs
    from tradingagents.research.onchain_replication.job_payload import population_record, execute_fit_payload
    from tradingagents.research.onchain_replication.graph_store import save_graph
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash
    import tradingagents.research.onchain_replication.run as batch
    import tradingagents.research.onchain_replication.matching as matching
    fixture,populations,plan=batch_setup(registered);root,spec,_=fixture
    graphs,_,fold,_=dataset_fixture();examples,scaler=populations['whole']
    needed={h for row in (*examples.train,*examples.test) for h in row.graph_hashes}
    graphs=[g for g in graphs if graph_hash(g) in needed]
    config=configs();config['dictionary'].update(sample_count=2,size=2)
    descriptor=representation_descriptor(graphs,examples,fold,'proposed',11,config)
    expected=prepare_features(graphs,examples,fold,'proposed',11,config,max_entries=100000,checkpoint=lambda *a:None)
    refs={}
    for i,g in enumerate(graphs):
        path=save_graph(root/'graphs'/str(i),g);name='graph_'+str(i)
        spec['experiments']['example-a']['inputs'][name]={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
        refs[graph_hash(g)]={'input':name}
    producer={'descriptor':descriptor,'graphs':refs,'max_entries':100000,'max_array_bytes':1024**2,
              'binding_output':'binding.json','journal_output':'journal.json','matching_input':'matching'}
    plan['cells'][0]['cell']['arm']='proposed';plan['cells'][0]['representation']='p'
    plan['representations']['p']={'output':'binding.json','failure_output':'failure.json'}
    spec['experiments']['example-a']['outputs']+=['binding.json','journal.json','failure.json']
    payload={'population_inputs':{'whole':'population'},'batch_plan_input':'batch_plan',
        'representation_jobs':{'p':{'operation':'produce','descriptor':descriptor,'plan_input':'representation_plan',
            'producer':'p','population':'whole','max_graph_payload_bytes':10*1024**2,'matching_input':'matching'}}}
    fixture=register_plan((root,spec,None),plan,[('population',population_record(examples,scaler)),
        ('representation_plan',{'schema_version':1,'producers':{'p':producer}}),
        ('matching',{'schema_version':1,'mode':'score_only'}),('execution_job',{'kind':'fit','payload':payload})])
    # Stop at the batch boundary; real admission, graph loading, journals and
    # numerical representation remain exercised. This test never fits a model.
    monkeypatch.setattr(batch,'execute_batch',lambda run,populations,prepared,**kw:prepared)
    monkeypatch.setattr(matching,'MatchResult',lambda *a,**k:pytest.fail('job retained diagnostic matrices'))
    with start(fixture) as run:
        prepared=execute_fit_payload(run,payload)
        assert prepared['p'].binding==expected.binding
        assert json.loads((run.directory/'outputs/failure.json').read_bytes())['status']=='complete'
        claim,=list((root/'research_artifacts/onchain_representations').glob('*/example-a/claim.json'))
        assert json.loads(claim.read_bytes())['matching_policy_sha256']==run.admission.inputs['matching']['sha256']
