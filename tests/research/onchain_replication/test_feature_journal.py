from dataclasses import replace
import numpy as np
import pytest
from tests.research.onchain_replication.test_feature_pipeline import population,configs
from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
from tradingagents.research.onchain_replication.feature_journal import FeatureJournal,read_feature_journal
from tradingagents.research.onchain_replication.provenance import file_hash


def test_completed_and_interrupted_graph_journal_reuses_numerical_work(tmp_path,monkeypatch):
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    graphs,fold,examples=population();owner={'run':'synthetic','source':'a'*40};calls=[];required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes}
    def engine(edges,n,config,**kwargs):calls.append(n);return np.ones((n,30))*len(calls)
    monkeypatch.setattr(pipeline,'graphwave',engine)
    journal=FeatureJournal(tmp_path/'first',owner,required_graphs=required)
    def interrupted(stage,context,payload):
        journal(stage,context,payload)
        if stage=='graph_complete':raise InterruptedError('synthetic interruption')
    with pytest.raises(InterruptedError):prepare_features(graphs,examples,fold,'graphwave',11,configs(),max_entries=100000,checkpoint=interrupted)
    path=journal.seal('failed',reason='synthetic interruption')
    state,binding=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=1024**2)
    assert binding is None and len(state['completed_graphs'])==1
    second=FeatureJournal(tmp_path/'second',owner,required_graphs=required,parent={'path':str(path.resolve()),'sha256':file_hash(path),'owner':owner})
    result=prepare_features(graphs,examples,fold,'graphwave',11,configs(),max_entries=100000,checkpoint=second,resume_state=state)
    assert len(calls)==len(result.features)
    completed=second.seal('complete')
    remainder,binding=read_feature_journal(completed,file_hash(completed),owner,required_graphs=required,max_array_bytes=1024**2)
    # The successor writes only new work and pins its complete parent closure.
    assert len(remainder['completed_graphs'])==len(result.features)
    assert binding==result.binding
    with pytest.raises(ValueError,match='identity'):
        prepare_features(graphs,examples,fold,'graphwave',12,configs(),max_entries=100000,checkpoint=lambda *a:None,resume_state=state)


def test_dictionary_and_mcm_complete_checkpoint_never_refit_on_resume(tmp_path,monkeypatch):
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    graphs,fold,examples=population();config=configs();config['dictionary']={**config['dictionary'],'sample_count':32,'size':32}
    owner={'run':'synthetic'};required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes};journal=FeatureJournal(tmp_path/'first',owner,required_graphs=required)
    original=prepare_features(graphs,examples,fold,'proposed',11,config,max_entries=100000,checkpoint=journal)
    path=journal.seal('complete');state,binding=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=1024**2)
    for name in ('sample_neighborhoods','fit_dictionary','mcm_features'):
        monkeypatch.setattr(pipeline,name,lambda *a,**kw:pytest.fail('completed component recomputed'))
    for arm in ('proposed','mcm_without_gat','training_label_permutation'):
        replay=prepare_features(graphs,examples,fold,arm,11,config,max_entries=100000,checkpoint=lambda *a:None,resume_state=state)
        assert replay.binding==original.binding and replay.dictionary.identity==original.dictionary.identity


def test_unsealed_or_duplicate_journal_cannot_masquerade_as_completion(tmp_path):
    journal=FeatureJournal(tmp_path/'j',{'run':'synthetic'},required_graphs=['a'*64])
    with pytest.raises(FileExistsError):FeatureJournal(tmp_path/'j',{},required_graphs=['a'*64])
    with pytest.raises(ValueError,match='not reached'):journal.seal('complete')
    path=journal.seal('failed',reason='before first checkpoint')
    state,binding=read_feature_journal(path,file_hash(path),{'run':'synthetic'},required_graphs=['a'*64],max_array_bytes=100)
    assert state['identity'] is None and binding is None
    with pytest.raises(ValueError,match='closure'):journal.seal('failed')


@pytest.mark.parametrize('nonempty',[False,True])
def test_second_interruption_before_new_event_preserves_parent_identity(tmp_path,nonempty):
    owner={'run':'synthetic'};required=['a'*64]
    first=FeatureJournal(tmp_path/'first',owner,required_graphs=required)
    if nonempty:
        first('graph_complete',{'workflow_identity':'b'*64,'graph_hash':required[0]},
              {'feature':np.ones(32),'aligned_vectors':None})
    path=first.seal('failed')
    previous,_=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=4096)
    second=FeatureJournal(tmp_path/'second',owner,required_graphs=required,
        parent={'path':str(path),'sha256':file_hash(path),'owner':owner})
    successor=second.seal('failed',reason='interrupted before first new event')
    recovered,binding=read_feature_journal(successor,file_hash(successor),owner,required_graphs=required,max_array_bytes=4096)
    assert recovered['identity']==previous['identity'] and binding is None
    assert set(recovered['completed_graphs'])==set(previous['completed_graphs'])
    if nonempty:np.testing.assert_array_equal(recovered['completed_graphs'][required[0]]['feature'],np.ones(32))


def test_retained_arrays_are_bounded_across_events_and_completed_progress_removed(tmp_path):
    owner={'run':'synthetic'};required=['a'*64,'b'*64];journal=FeatureJournal(tmp_path/'j',owner,required_graphs=required)
    context={'workflow_identity':'c'*64,'graph_hash':required[0]}
    journal('mcm_progress',{**context,'next_node':1},np.ones(500))
    journal('graph_complete',context,{'feature':np.ones(500),'aligned_vectors':None})
    path=journal.seal('failed')
    state,_=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=5000)
    assert state['graph_progress']=={}
    successor=FeatureJournal(tmp_path/'next',owner,required_graphs=required,parent={'path':str(path),'sha256':file_hash(path),'owner':owner})
    successor('graph_complete',{**context,'graph_hash':required[1]},{'feature':np.ones(500),'aligned_vectors':None})
    new=successor.seal('failed')
    with pytest.raises(ValueError,match='retained representation array budget'):
        read_feature_journal(new,file_hash(new),owner,required_graphs=required,max_array_bytes=5000)


@pytest.mark.parametrize('failure_point',['before_first_checkpoint','after_representation_complete'])
def test_empty_and_numerically_complete_failed_parents_recover_without_refit(tmp_path,monkeypatch,failure_point):
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    graphs,fold,examples=population();owner={'run':'synthetic'};required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes}
    journal=FeatureJournal(tmp_path/'first',owner,required_graphs=required)
    if failure_point=='after_representation_complete':
        original=prepare_features(graphs,examples,fold,'gin',11,configs(),max_entries=100000,checkpoint=journal)
    path=journal.seal('failed',reason=failure_point)
    state,binding=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=1024**2)
    successor=FeatureJournal(tmp_path/'next',owner,required_graphs=required,parent={'path':str(path),'sha256':file_hash(path),'owner':owner})
    recovered=prepare_features(graphs,examples,fold,'gin',11,configs(),max_entries=100000,checkpoint=successor,resume_state=state)
    completed=successor.seal('complete');_,final=read_feature_journal(completed,file_hash(completed),owner,required_graphs=required,max_array_bytes=1024**2)
    assert final==recovered.binding
    if failure_point=='after_representation_complete':
        assert len(successor.records)==1 and successor.records[0]['stage']=='representation_complete'
        assert final==original.binding


@pytest.mark.parametrize('corruption',['binding_hash','empty_membership'])
def test_final_binding_and_required_population_cannot_be_fabricated(tmp_path,corruption):
    from tradingagents.research.onchain_replication.cache import cache_key
    graphs,fold,examples=population();owner={'run':'synthetic'};required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes}
    journal=FeatureJournal(tmp_path/'j',owner,required_graphs=required)
    def corrupt(stage,context,payload):
        if stage=='representation_complete':
            if corruption=='binding_hash':context={**context,'binding_hash':'0'*64}
            else:payload={**payload,'feature_hashes':{}};context={**context,'binding_hash':cache_key(payload)}
        journal(stage,context,payload)
    prepare_features(graphs,examples,fold,'gin',11,configs(),max_entries=100000,checkpoint=corrupt)
    path=journal.seal('complete')
    with pytest.raises(ValueError,match='binding hash|closure incomplete'):
        read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=1024**2)
