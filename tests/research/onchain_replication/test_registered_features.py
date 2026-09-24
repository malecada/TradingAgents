import copy,json
import pytest
from tests.research.test_lifecycle import registered,start,commit
from tests.research.onchain_replication.test_feature_pipeline import population,configs
from tradingagents.research.onchain_replication.registered_features import representation_descriptor,prepare_registered_features,reuse_registered_features
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash
from tradingagents.research.onchain_replication.neighborhoods import graph_hash


def prepared_registration(registered):
    root,spec,_=registered;graphs,fold,examples=population();config=configs()
    descriptor=representation_descriptor(graphs,examples,fold,'gin',11,config)
    refs={}
    def add(name,path):spec['experiments']['example-a']['inputs'][name]={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
    for i,g in enumerate(graphs):
        name='graph-'+str(i);path=root/(name+'.json');path.write_bytes(canonical_bytes({'graph_hash':graph_hash(g)}));add(name,path);refs[graph_hash(g)]={'input':name}
    plan={'schema_version':1,'producers':{'gin11':{'descriptor':descriptor,'graphs':refs,'binding_output':'features.json','journal_output':'journal.json','max_entries':100000,'max_array_bytes':1024**2}}}
    path=root/'feature-plan.json';path.write_bytes(canonical_bytes(plan));add('feature-plan',path)
    spec['experiments']['example-a']['outputs'].extend(['features.json','journal.json'])
    return (root,spec,commit(root,spec)),(graphs,examples,fold,'gin',11,config),descriptor


def produce(run,args,**kwargs):
    return prepare_registered_features(run,'gin11',*args,plan_input='feature-plan',max_entries=100000,max_array_bytes=1024**2,**kwargs)


def test_registered_representation_exclusive_ownership_and_completed_reuse(registered,monkeypatch):
    import tradingagents.research.onchain_replication.registered_features as module
    fixture,args,descriptor=prepared_registration(registered);root,spec,source=fixture
    with start(fixture) as run:
        result,path=produce(run,args)
        assert json.loads((run.directory/'outputs/features.json').read_bytes())==result.binding
        reused=reuse_registered_features(run,None,descriptor,max_array_bytes=1024**2,journal_output='journal.json')
        assert reused.binding==result.binding
        with pytest.raises(FileExistsError):produce(run,args)
    child=copy.deepcopy(spec['experiments']['example-a']);child['parent']='example-a'
    child['inputs']['completed-features']={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
    spec['experiments']['example-b']=child;source=commit(root,spec)
    monkeypatch.setattr(module,'prepare_features',lambda *a,**k:pytest.fail('completed representation refitted'))
    with start((root,spec,source),experiment='example-b') as run:
        recovered=reuse_registered_features(run,'completed-features',descriptor,max_array_bytes=1024**2)
        assert recovered.binding==result.binding
        with pytest.raises(ValueError,match='identity'):
            reuse_registered_features(run,'completed-features',{**descriptor,'seed':12},max_array_bytes=1024**2)


def test_registered_failed_representation_continues_without_repeating_completed_graph(registered,monkeypatch):
    import tradingagents.research.onchain_replication.registered_features as module
    fixture,args,descriptor=prepared_registration(registered);root,spec,source=fixture;original=module.prepare_features
    def interrupted(*args,checkpoint,**kwargs):
        def callback(stage,context,payload):
            checkpoint(stage,context,payload)
            if stage=='graph_complete':raise InterruptedError('synthetic stop')
        return original(*args,checkpoint=callback,**kwargs)
    monkeypatch.setattr(module,'prepare_features',interrupted)
    with start(fixture) as run:
        with pytest.raises(InterruptedError):produce(run,args)
    failed=list((root/'research_artifacts/onchain_representations').glob('*/example-a/failed.json'));assert len(failed)==1
    child=copy.deepcopy(spec['experiments']['example-a']);child['parent']='example-a'
    child['inputs']['prior-features']={'path':str(failed[0].relative_to(root)),'sha256':file_hash(failed[0]),'dataset':'sample'}
    spec['experiments']['example-b']=child;source=commit(root,spec)
    monkeypatch.setattr(module,'prepare_features',original)
    with start((root,spec,source),experiment='example-b') as run:
        result,path=produce(run,args,continuation_input='prior-features')
        events=json.loads(path.read_bytes())['events']
        assert sum(e['stage']=='graph_complete' for e in events)==len(result.features)-1


def test_motif_control_descriptors_are_one_scientific_representation():
    graphs,fold,examples=population();config=configs()
    descriptors=[representation_descriptor(graphs,examples,fold,arm,11,config) for arm in ('proposed','mcm_without_gat','training_label_permutation')]
    assert descriptors[0]==descriptors[1]==descriptors[2]


def test_graph_output_hash_checks_the_exact_parsed_buffer(registered,monkeypatch):
    from pathlib import Path
    fixture,args,descriptor=prepared_registration(registered);root,spec,_=fixture
    plan_path=root/'feature-plan.json';plan=json.loads(plan_path.read_bytes())
    graph=descriptor['graph_population'][0];plan['producers']['gin11']['graphs'][graph]={'output':'graph-runtime.json'}
    plan_path.write_bytes(canonical_bytes(plan));spec['experiments']['example-a']['inputs']['feature-plan']['sha256']=file_hash(plan_path)
    spec['experiments']['example-a']['outputs'].append('graph-runtime.json');source=commit(root,spec)
    with start((root,spec,source)) as run:
        run.write_json('graph-runtime.json',{'graph_hash':'f'*64})
        target=run.directory/'outputs/graph-runtime.json';original=Path.read_bytes
        def changed(p):return canonical_bytes({'graph_hash':graph}) if p==target else original(p)
        monkeypatch.setattr(Path,'read_bytes',changed)
        with pytest.raises(ValueError,match='graph output not published'):produce(run,args)
