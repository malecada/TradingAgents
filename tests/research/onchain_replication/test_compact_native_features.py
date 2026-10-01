"""Current compact terminal to bounded saved MCM/edge batches for training."""
import shutil
import gc
import numpy as np
import pytest
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_terminal as upstream
from tradingagents.research.onchain_replication.provenance import file_hash


def api():
    from tradingagents.research.onchain_replication import compact_native_features
    return compact_native_features


def test_actual_terminal_required():
    with pytest.raises(ValueError,match='actual'):api().prepare(object(),input_name='native')


@pytest.fixture
def admitted(monkeypatch):
    training=upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t);m=api()
            t.input('compact_native_features',{'schema_version':1,'max_live_tensor_bytes':1024,
                'max_numeric_bytes':8192,'chunk_entries':64})
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_native_features_input']='compact_native_features'
            for name in m.required_sources():
                path=t.root/name;path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(m.ROOT/name,path);git(t.root,'add','--',name)
                t.exp['source_files'][name]=file_hash(path)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(monkeypatch);published,t=next(gen)
    try:yield upstream.api().finish(published,input_name='compact_terminal'),published,t
    finally:
        try:next(gen)
        except StopIteration:pass


def test_actual_terminal_loads_equal_independent_training_batches_and_refuses_corruption(admitted):
    terminal,published,t=admitted;m=api()
    prepared=m.prepare(terminal,input_name='compact_native_features');features=prepared.features
    expected={p.record['graph_hash']:p._features.feature for p in published._closure._graphs}
    assert set(features)==set(expected) and features.verified_hashes()==prepared.binding['feature_hashes']
    batch=features.load_batch([*expected,*expected])
    for h,v in batch.items():
        for key in ('mcm','edge_index'):
            np.testing.assert_array_equal(v[key].numpy(),expected[h][key].numpy())
            assert v[key].data_ptr()!=expected[h][key].data_ptr()
    assert features.live_tensor_bytes()>0
    del batch,v;gc.collect();assert features.live_tensor_bytes()==0
    path=published._closure._graphs[0].directory/'artifact/array-000000.npy'
    raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises(ValueError):features.load_batch([published._closure._graphs[0].record['graph_hash']])


def test_last_batch_callback_value_mutation_is_refused_without_retained_tensors(tmp_path):
    from types import SimpleNamespace
    from tradingagents.research.onchain_replication import component_store
    m=api();native=m._api();key='a'*64;context={'synthetic':True}
    payload={'feature':{'mcm':np.ones((2,2),dtype=np.float32),
        'edge_index':np.array([[0],[1]],dtype=np.int64)},'aligned_vectors':None}
    manifest=component_store.save_component(tmp_path/'artifact',payload,context)
    expected=native.boundary.identity(payload['feature']['mcm'],payload['feature']['edge_index'],64)
    refs={key:{'path':str(manifest),'sha256':file_hash(manifest),'context':context,
        'nodes':2,'motifs':2,'edge_shape':[2,1],'feature_hash':expected,
        'max_manifest_bytes':8192,'max_artifact_bytes':16384}}
    holder={};changed=[]
    def mutate():
        if holder and holder['map']._live:
            value=holder['map']._live[0][0]()
            if value is not None:value.fill_(.25);changed.append(True)
    mapping=native._NativeMap(tmp_path,refs,{'schema_version':1,'max_live_tensor_bytes':1024,
        'max_numeric_bytes':8192,'chunk_entries':64},lease=mutate,read_lease=lambda:None)
    holder['map']=mapping
    terminal=SimpleNamespace(_verify=lambda **kw:None)
    features=m._Features(mapping,terminal,{key:expected},native.boundary,64)
    with pytest.raises(ValueError,match='returned feature bytes'):features.load_batch([key])
    assert changed
    gc.collect();assert features.live_tensor_bytes()==0
