"""Tiny numerical adapter tests; coordinator release required before execution."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from tests.research.onchain_replication.test_model import cfg
from tests.research.onchain_replication.test_neural_resource import synthetic_run
from tradingagents.research.onchain_replication import model,neural_resource as resource
from tradingagents.research.onchain_replication.gat import GraphAttention as Eager
from tradingagents.research.onchain_replication.streamed_gat import GraphAttention as Streamed
POLICY={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
SOURCE='tradingagents/research/onchain_replication/streamed_gat.py'
PACKAGE=Path(__file__).resolve().parents[3]/'tradingagents/research/onchain_replication'


def test_real_constructor_default_selected_initial_rng_and_detachment():
    torch.manual_seed(11);eager=model.ReplicationModel(cfg(),'classification');rng=torch.get_rng_state().clone()
    torch.manual_seed(11);selected=dict(POLICY);streamed=model.ReplicationModel(cfg(),'classification',execution=selected)
    assert torch.equal(rng,torch.get_rng_state())
    assert all(type(layer) is Eager for layer in eager.graph.gat)
    assert all(type(layer) is Streamed and layer.block_edges==65536 for layer in streamed.graph.gat)
    assert eager.state_dict().keys()==streamed.state_dict().keys()
    assert all(torch.equal(v,streamed.state_dict()[k]) for k,v in eager.state_dict().items())
    selected['block_edges']=1
    assert streamed.execution['block_edges']==65536
    with pytest.raises(TypeError):streamed.execution['block_edges']=1


def selected_run(tmp_path,monkeypatch):
    run,plan=synthetic_run(tmp_path,monkeypatch)
    path=tmp_path/SOURCE;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((PACKAGE/'streamed_gat.py').read_bytes())
    run.admission.experiment['source_files'][SOURCE]=hashlib.sha256(path.read_bytes()).hexdigest()
    plan={**plan,'schema_version':2,'model_execution':dict(POLICY)}
    target=tmp_path/'plan.json';target.write_text(json.dumps(plan))
    run.admission.inputs['plan']['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    return run,plan


def test_schema2_real_admission_source_and_original_model(tmp_path,monkeypatch):
    run,plan=selected_run(tmp_path,monkeypatch)
    actual,config,_=resource.registered_plan(run,'plan')
    assert actual==plan and config=={**cfg(),'graph_activation_checkpointing':False}
    identity=resource._execution_identity(run,plan)
    assert identity['source_sha256']==identity['candidate_sha256']==run.admission.experiment['source_files'][SOURCE]
    run.admission.experiment['source_files'][SOURCE]='a'*64
    with pytest.raises(ValueError,match='source'):resource.registered_plan(run,'plan')


def test_schema2_refuses_checkpoint_block_and_source_body(tmp_path,monkeypatch):
    run,plan=selected_run(tmp_path,monkeypatch)
    for changed in ({**plan,'graph_activation_checkpointing':True},
                    {**plan,'model_execution':{**POLICY,'block_edges':7}}):
        with pytest.raises(ValueError):resource._execution_identity(run,changed)
    (tmp_path/SOURCE).write_text('changed')
    with pytest.raises(ValueError,match='source'):resource._execution_identity(run,plan)


def test_actual_selected_tiny_resource_checkpoint_identity(tmp_path,monkeypatch):
    run,plan=selected_run(tmp_path,monkeypatch);torch.set_num_threads(2)
    evidence=resource._execution_identity(run,plan)
    identity={'cell_id':'synthetic','model_execution':evidence}
    graph=SimpleNamespace(node_ids=('a','b','c'),edge_index=__import__('numpy').array([[0,1],[1,2]],dtype='int64'))
    target=tmp_path/'cell';target.mkdir()
    result=resource.run_cell(graph,cfg(),target,identity,max_checkpoint_bytes=8*1024**2,cooperative_seconds=60,execution=POLICY)
    assert result['checkpoint_roundtrip_exact'] and result['optimizer_steps']==1
    saved=torch.load(target/'checkpoint.pt',map_location='cpu',weights_only=True)
    assert saved['identity']==identity
    target=tmp_path/'refused';target.mkdir()
    with pytest.raises(ValueError,match='identity'):
        resource.run_cell(graph,cfg(),target,{},max_checkpoint_bytes=8*1024**2,cooperative_seconds=60,execution=POLICY)
    assert not (target/'checkpoint.pt').exists()
