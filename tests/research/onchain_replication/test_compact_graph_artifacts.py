"""Actual compact Features through exclusive saved graph artifact admission."""
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import torch
import pytest
from tests.research.onchain_replication import test_compact_features as upstream


@pytest.fixture
def admitted(request,monkeypatch):
    training=upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture;option=getattr(request,'param','valid')
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            policy={'schema_version':1,'max_manifest_bytes':32768,'max_artifact_bytes':65536,
                'max_resident_array_bytes':65536,'max_workflow_output_bytes':1000000}
            if option=='budget':policy['max_workflow_output_bytes']=1
            t.input('compact_graph_output',policy)
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_graph_output_input']='compact_graph_output'
            if option=='route':t.item['compact_graph_output_input']='sample'
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(SimpleNamespace(param='valid'),monkeypatch)
    mcm,t=next(gen)
    try:yield upstream.api().prepare(mcm,input_name='compact_features'),t
    finally:
        try:next(gen)
        except StopIteration:pass


def api():
    from tradingagents.research.onchain_replication import compact_graph_artifacts
    return compact_graph_artifacts


def test_actual_saved_tensors_exact_lineage_and_corruption_before_allocation(admitted,monkeypatch):
    features,t=admitted;m=api();p=m.publish(features,input_name='compact_graph_output')
    saved=p.load();saved.check()
    for key in ('mcm','edge_index'):
        np.testing.assert_array_equal(saved.feature[key].numpy(),features.feature[key].numpy())
        assert saved.feature[key].data_ptr()!=features.feature[key].data_ptr()
    assert p.record['feature_receipt_sha256']==m.cache_key(dict(features.record))
    assert p.record['representation_admitted'] is False
    assert saved.record['graph_receipt_sha256']==p.receipt_sha256
    with pytest.raises(ValueError):m.publish(features,input_name='compact_graph_output')
    member=p.directory/'artifact/array-000000.npy';raw=member.read_bytes();member.write_bytes(raw[:-1])
    calls=[]
    def refuse(*args,**kwargs):calls.append(1);raise AssertionError('bad saved graph allocated')
    real=p._reader.np
    class Trap:
        def __getattr__(self,name):return refuse if name=='empty' else getattr(real,name)
    monkeypatch.setattr(p._reader,'np',Trap())
    with pytest.raises(ValueError):p.load()
    assert not calls


@pytest.mark.parametrize('admitted',['budget','route'],indirect=True)
def test_registered_output_refusal_precedes_namespace(admitted):
    features,t=admitted;m=api()
    with pytest.raises(ValueError):m.publish(features,input_name='compact_graph_output')
    assert not m.directory(features).exists() and not features._mcm._dictionary._proof.owner.poisoned


def test_partial_writer_failure_is_retained_and_owner_poisoned(admitted,monkeypatch):
    features,t=admitted;m=api()
    def fail(path,payload,context):
        path.mkdir();(path/'partial').write_bytes(b'partial');raise RuntimeError('synthetic writer failure')
    monkeypatch.setattr(m.component_store,'save_component',fail)
    with pytest.raises(RuntimeError,match='writer failure'):m.publish(features,input_name='compact_graph_output')
    root=m.directory(features);assert (root/'artifact/partial').read_bytes()==b'partial'
    assert (root/'failed.json').exists() and features._mcm._dictionary._proof.owner.poisoned
    assert not (root/'complete.json').exists()


def test_last_callback_cannot_hide_changed_saved_inventory(admitted,monkeypatch):
    features,t=admitted;m=api();original=type(features).lease;injected=[]
    def changed(self):
        original(self)
        root=m.directory(self)
        if (root/'complete.json').exists():
            (root/'artifact/orphan').write_bytes(b'retained');injected.append(True)
    monkeypatch.setattr(type(features),'lease',changed)
    with pytest.raises(ValueError):m.publish(features,input_name='compact_graph_output')
    assert injected and features._mcm._dictionary._proof.owner.poisoned


def test_post_sizing_tensor_growth_refused_before_writer(admitted,monkeypatch):
    features,t=admitted;m=api();original=type(features).lease;calls=[]
    def changed(self):
        original(self)
        if (m.directory(self)/'start.json').exists():self.feature['mcm'].set_(torch.zeros((100,100),dtype=torch.float32))
    def refuse(*args,**kwargs):calls.append(1);raise AssertionError('grown tensor reached writer')
    monkeypatch.setattr(type(features),'lease',changed);monkeypatch.setattr(m.component_store,'save_component',refuse)
    with pytest.raises(ValueError):m.publish(features,input_name='compact_graph_output')
    assert not calls and features._mcm._dictionary._proof.owner.poisoned
    assert tuple(features.feature['mcm'].shape)==(100,100)


def test_valid_rehashed_wrong_saved_value_refused(admitted,monkeypatch):
    features,t=admitted;m=api();write=m.component_store.save_component;altered=[]
    def wrong(path,payload,context):
        values=payload['feature']['mcm'].copy()
        values[0,0]=.25 if float(values[0,0])!=.25 else .75
        changed={'feature':payload['feature']|{'mcm':values},'aligned_vectors':None}
        altered.append(True);return write(path,changed,context)
    monkeypatch.setattr(m.component_store,'save_component',wrong)
    with pytest.raises(ValueError,match='numeric bytes differ'):m.publish(features,input_name='compact_graph_output')
    assert altered and (m.directory(features)/'failed.json').exists()


def test_final_loaded_callback_cannot_revoke_owner(admitted,monkeypatch):
    features,t=admitted;m=api();original=m.Loaded.lease;changed=[]
    def revoke(self):
        original(self);features._mcm._dictionary._proof.owner.poisoned=True;changed.append(True)
    monkeypatch.setattr(m.Loaded,'lease',revoke)
    with pytest.raises(ValueError,match='owner'):m.publish(features,input_name='compact_graph_output')
    assert changed and (m.directory(features)/'failed.json').exists()


def test_empty_edge_header_and_strict_readback(tmp_path):
    m=api();payload={'feature':{'mcm':np.ones((2,2),dtype=np.float32),
        'edge_index':np.empty((2,0),dtype=np.int64)},'aligned_vectors':None};context={'synthetic':True}
    expected=m._template(payload,context);path=m.component_store.save_component(tmp_path/'artifact',payload,context)
    raw=path.read_bytes();assert len(raw)==len(m.canonical_bytes(expected))
    assert sum(x['bytes'] for x in expected['arrays'].values())==sum(p.stat().st_size for p in path.parent.glob('*.npy'))
    reader=m.compact_samples._reader()
    loaded=reader.read_component(path,m.file_hash(path),context,root=tmp_path,
        max_manifest_bytes=8192,max_artifact_bytes=16384,max_array_bytes=16,lease=lambda:None)
    m.compact_samples._equal_numeric(loaded,payload)
