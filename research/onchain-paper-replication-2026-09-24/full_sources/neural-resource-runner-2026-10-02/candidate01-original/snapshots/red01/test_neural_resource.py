"""Invented graphs only; registered boundary and one-update resource semantics."""
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from tests.research.onchain_replication.test_model import cfg
from tradingagents.research.onchain_replication import job


def module():
    try:return importlib.import_module('tradingagents.research.onchain_replication.neural_resource')
    except ModuleNotFoundError:pytest.fail('maintained neural resource runner missing')


def test_explicit_job_kind_and_no_payload_overrides():
    value={'schema_version':1,'kind':'neural_resource','resources':{},'environment_input':'env','payload':{'plan_input':'plan'}}
    job.job_schema(value)
    for payload in ({},{'plan_input':'plan','mcm_input':'elsewhere'},{'plan_input':''}):
        with pytest.raises(ValueError):job.job_schema({**value,'payload':payload})


def test_original_population_has_one_update_and_real_checkpoint(tmp_path):
    n=module();torch.set_num_threads(2)
    graph=SimpleNamespace(node_ids=('a','b','c'),edge_index=__import__('numpy').array([[0,1],[1,2]],dtype='int64'))
    result=n.run_cell(graph,cfg(),tmp_path,{'cell_id':'synthetic','plan_sha256':'a'*64},
        max_checkpoint_bytes=8*1024**2,cooperative_seconds=60)
    state=torch.load(tmp_path/'checkpoint.pt',weights_only=True)
    assert result['batch']==16 and result['lookback']==28 and result['unique_graphs']==1
    assert result['optimizer_steps']==1 and result['checkpoint_roundtrip_exact'] is True
    assert state['epoch']==1 and state['batch']==0
    assert all(float(v['step'])==1 for v in state['optimizer']['state'].values())
    assert state['rng']['pcg64']['bit_generator']=='PCG64'
    assert result['checkpoint_bytes']==(tmp_path/'checkpoint.pt').stat().st_size


def test_checkpoint_limit_preserves_partial_bytes_and_stops(tmp_path):
    n=module();torch.set_num_threads(2)
    graph=SimpleNamespace(node_ids=('a','b'),edge_index=__import__('numpy').array([[0],[1]],dtype='int64'))
    with pytest.raises((ValueError,RuntimeError),match='checkpoint|write|position'):
        n.run_cell(graph,cfg(),tmp_path,{},max_checkpoint_bytes=1024,cooperative_seconds=60)
    assert (tmp_path/'checkpoint.pt').exists()
    assert (tmp_path/'checkpoint.pt').stat().st_size<=1024


def test_no_silent_architecture_shrinking():
    n=module()
    assert n.validate_model(cfg(),False)=={**cfg(),'graph_activation_checkpointing':False}
    with pytest.raises(ValueError):n.validate_model({**cfg(),'gat_widths':[8,32]},False)
    with pytest.raises(ValueError):n.validate_model({**cfg(),'graph_activation_checkpointing':True},False)
