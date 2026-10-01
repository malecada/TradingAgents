"""Actual compact MCM to registered fixed graph tensor inputs."""
import json
import shutil
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_mcm as upstream
from tradingagents.research.onchain_replication.provenance import file_hash

BOUNDARY='research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-boundary-2026-10-01/boundary.py'

@pytest.fixture
def admitted(request,monkeypatch):
    training=upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture;option=getattr(request,'param','valid')
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            policy={'schema_version':1,'chunk_entries':4,'max_numeric_bytes':65536}
            if option=='budget':policy['max_numeric_bytes']=1
            t.input('compact_features',policy)
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_feature_input']='compact_features'
            if option=='route':t.item['compact_feature_input']='sample'
            target=t.root/BOUNDARY;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(upstream.ROOT/BOUNDARY,target);git(t.root,'add','--',BOUNDARY)
            if option!='source':t.exp['source_files'][BOUNDARY]=file_hash(target)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(SimpleNamespace(param='valid'),monkeypatch)
    dictionary,t=next(gen);key,graph=upstream.target(dictionary)
    try:
        result=upstream.api().produce(dictionary,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
        yield result,t
    finally:
        try:next(gen)
        except StopIteration:pass


def api():
    from tradingagents.research.onchain_replication import compact_features
    return compact_features


def test_actual_mcm_tensor_values_and_independent_storage(admitted):
    mcm,t=admitted;m=api();result=m.prepare(mcm,input_name='compact_features')
    result.check();f=result.feature
    np.testing.assert_array_equal(f['mcm'].numpy(),mcm.matrix)
    np.testing.assert_array_equal(f['edge_index'].numpy(),mcm._graph.edge_index)
    assert not np.shares_memory(f['mcm'].numpy(),mcm.matrix)
    assert not np.shares_memory(f['edge_index'].numpy(),mcm._graph.edge_index)
    assert f['mcm'].dtype==torch.float32 and f['edge_index'].dtype==torch.int64
    assert not f['mcm'].requires_grad
    assert result.record['mcm_receipt_sha256']==mcm.receipt_sha256
    assert result.record['representation_admitted'] is False
    f['mcm'][0,0] += .125
    with pytest.raises(ValueError,match='feature'):result.check()


@pytest.mark.parametrize('admitted',['budget','route','source'],indirect=True)
def test_registered_limits_refuse_before_tensor_allocation(admitted,monkeypatch):
    mcm,t=admitted;m=api();calls=[]
    def refuse(*args,**kwargs):calls.append(1);raise AssertionError('unexpected allocation')
    monkeypatch.setattr(torch,'empty',refuse)
    with pytest.raises(ValueError):m.prepare(mcm,input_name='compact_features')
    assert not calls and not mcm._dictionary._proof.owner.poisoned


def test_last_live_callback_cannot_hide_graph_mutation(admitted,monkeypatch):
    mcm,t=admitted;m=api();lease=mcm.lease;seen=[]
    boundary=m._boundary();materialize=boundary.materialize
    def copy(*args,**kwargs):
        result=materialize(*args,**kwargs);seen.append(result);return result
    def changed():
        lease()
        if seen:mcm._graph.edge_index[0,0]=1-int(mcm._graph.edge_index[0,0])
    monkeypatch.setattr(m,'_boundary',lambda:boundary)
    monkeypatch.setattr(boundary,'materialize',copy);monkeypatch.setattr(mcm,'lease',changed)
    with pytest.raises(ValueError):m.prepare(mcm,input_name='compact_features')


def test_concurrent_conversion_refused_before_allocation(admitted):
    mcm,t=admitted;m=api();owner=mcm._dictionary._proof.owner
    owner._transition.acquire()
    try:
        with pytest.raises(ValueError,match='concurrent'):m.prepare(mcm,input_name='compact_features')
    finally:owner._transition.release()
