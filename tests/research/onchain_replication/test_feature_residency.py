"""Verified fixed features stay on disk until one unique-graph batch needs them."""
import importlib.util
import json
from types import SimpleNamespace
import weakref
import numpy as np
import pytest
import torch

from tradingagents.research.onchain_replication.component_store import save_component,load_component
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.evaluation import feature_hash,batch_factory


def api():
    assert importlib.util.find_spec('tradingagents.research.onchain_replication.feature_residency'), 'bounded feature residency missing'
    from tradingagents.research.onchain_replication.feature_residency import FixedFeatureMap
    return FixedFeatureMap


def saved(tmp_path,name,value):
    context={'synthetic':name}
    path=save_component(tmp_path/name,{'feature':value,'aligned_vectors':None},context)
    return path,context


@pytest.mark.parametrize('fortran',[False,True])
def test_component_references_verify_and_hash_without_copying_numeric_payload(tmp_path,monkeypatch,fortran):
    api()
    import tradingagents.research.onchain_replication.component_store as store
    values=np.arange(90.,dtype=np.float64).reshape(30,3)
    if fortran:values=np.asfortranarray(values)
    path,context=saved(tmp_path,'component',values)
    expected=feature_hash(values)
    original=store.np.array
    def no_copy(*a,**kw):
        if kw.get('copy'):pytest.fail('numeric payload materialized during reference verification')
        return original(*a,**kw)
    monkeypatch.setattr(store.np,'array',no_copy)
    reference=load_component(path,file_hash(path),context,max_array_bytes=10000,materialize_arrays=False)
    assert feature_hash(reference['feature'])==expected


@pytest.mark.parametrize('value',[np.array(1.,dtype=np.float64),torch.tensor(1.)])
def test_scalar_reference_retains_eager_feature_identity(tmp_path,value):
    path,context=saved(tmp_path,'scalar',value)
    reference=load_component(path,file_hash(path),context,max_array_bytes=4096,materialize_arrays=False)
    assert feature_hash(reference['feature'])==feature_hash(value)


def test_lazy_batch_deduplicates_graphs_releases_arrays_and_rechecks_corruption(tmp_path):
    Map=api()
    features={'a'*64:{'mcm':torch.arange(12,dtype=torch.float32).reshape(3,4),'edge_index':torch.tensor([[0,1],[1,2]])},
              'b'*64:{'mcm':torch.ones(3,4),'edge_index':torch.tensor([[2],[0]])}}
    refs={};paths={}
    for i,(h,value) in enumerate(features.items()):
        path,context=saved(tmp_path,str(i),value);paths[h]=path
        refs[h]=load_component(path,file_hash(path),context,max_array_bytes=4096,materialize_arrays=False)['feature']
    hashes={h:feature_hash(v) for h,v in features.items()}
    lazy=Map(refs,hashes,max_unique_feature_bytes=4096)
    assert lazy.verified_hashes()==hashes
    examples=[SimpleNamespace(input_prices=(1.,2.),up=1,target_price=3.,graph_hashes=('a'*64,'a'*64)),
              SimpleNamespace(input_prices=(2.,3.),up=0,target_price=2.,graph_hashes=('b'*64,'a'*64))]
    scaler=SimpleNamespace(transform=lambda x:np.asarray(x))
    factory=batch_factory('gin','direction',examples,scaler,lazy)
    inputs,labels=factory([0,1]);rows=inputs['graph_sequences']
    assert rows[0][0] is rows[0][1] is rows[1][1]
    assert labels.tolist()==[1,0]
    held=weakref.ref(rows[0][0]['mcm'])
    del rows,inputs
    assert held() is None, 'feature map retained a completed batch tensor'
    # Changing a sealed member after initial verification is still refused.
    member=paths['a'*64].parent/'array-000000.npy'
    body=bytearray(member.read_bytes());body[-1]^=1;member.write_bytes(body)
    with pytest.raises(ValueError,match='hash|changed'):factory([0])


def test_batch_numeric_limit_is_enforced_before_any_materialization(tmp_path,monkeypatch):
    Map=api()
    from tradingagents.research.onchain_replication.component_store import ArrayReference
    value=torch.ones(10,4)
    refs={}
    for i,h in enumerate(('a'*64,'b'*64)):
        path,context=saved(tmp_path,str(i),value)
        refs[h]=load_component(path,file_hash(path),context,max_array_bytes=4096,materialize_arrays=False)['feature']
    lazy=Map(refs,{h:feature_hash(value) for h in refs},max_unique_feature_bytes=200)
    monkeypatch.setattr(ArrayReference,'load',lambda *a,**k:pytest.fail('over-limit batch began numeric loading'))
    with pytest.raises(ValueError,match='batch.*bound|batch.*capacity'):lazy.load_batch(list(refs))


def test_streamed_producer_does_not_keep_previous_graph_tensors(tmp_path):
    api()
    from tests.research.onchain_replication.test_feature_pipeline import population,configs
    from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
    from tradingagents.research.onchain_replication.feature_journal import FeatureJournal,read_feature_journal
    graphs,fold,examples=population();required={h for row in (*examples.train,*examples.test) for h in row.graph_hashes}
    owner={'synthetic':'residency'};journal=FeatureJournal(tmp_path/'journal',owner,required_graphs=required)
    retained=[]
    def checkpoint(stage,context,payload):
        if stage=='graph_complete':
            assert all(ref() is None for ref in retained), 'producer kept an earlier graph tensor'
            retained.append(weakref.ref(payload['feature']['mcm']))
        journal(stage,context,payload)
    result=prepare_features(graphs,examples,fold,'gin',11,configs(),max_entries=100000,
        checkpoint=checkpoint,retain_features=False,max_array_bytes=1024**2)
    assert not result.features and len(retained)==len(required)
    assert all(ref() is None for ref in retained)
    path=journal.seal('complete')
    state,binding=read_feature_journal(path,file_hash(path),owner,required_graphs=required,max_array_bytes=1024**2,lazy_features=True)
    assert binding==result.binding
    Map=api();lazy=Map({h:state['completed_graphs'][h]['feature'] for h in required},binding['feature_hashes'],max_unique_feature_bytes=1024**2)
    assert lazy.verified_hashes()==binding['feature_hashes']
