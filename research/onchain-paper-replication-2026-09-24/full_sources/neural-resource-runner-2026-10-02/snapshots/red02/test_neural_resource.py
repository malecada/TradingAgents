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


def synthetic_run(tmp_path,monkeypatch):
    from dataclasses import replace
    from datetime import date,timedelta
    from tests.research.onchain_replication.test_subsets import fixture
    from tradingagents.research.onchain_replication.graph_store import save_graph
    from tradingagents.research.onchain_replication.provenance import file_hash
    from tradingagents.research.lifecycle import ResearchRun
    weeks=['2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23']
    inputs={};cells=[]
    def add(name,path):inputs[name]={'path':str(path.relative_to(tmp_path)),'sha256':file_hash(path),'dataset':'graphs'}
    for i,w in enumerate(weeks):
        end=(date.fromisoformat(w)+timedelta(days=7)).isoformat()+'T00:00:00Z'
        g=replace(fixture(),start_utc=w+'T00:00:00Z',end_utc=end,available_at=end)
        path=save_graph(tmp_path/f'g{i}',g);m=json.loads(path.read_bytes());add(f'g{i}',path)
        cells.append({'cell_id':'neural_checkpoint-'+w,'week':w,'graph_input':f'g{i}','graph_hash':m['graph_hash'],'graph_config_hash':m['metadata']['graph_config_hash'],'node_order_sha256':m['arrays']['node_ids']['sha256'],'expected_nodes':4,'expected_edges':2})
    model=tmp_path/'model.json';model.write_text(json.dumps(cfg()));add('model',model)
    plan={'schema_version':1,'model_input':'model','graph_activation_checkpointing':False,'cells':cells,
          'limits':{'max_graph_bytes':1024**2,'max_checkpoint_bytes':8*1024**2,'max_output_bytes':128*1024**2,'cooperative_cell_seconds':60}}
    p=tmp_path/'plan.json';p.write_text(json.dumps(plan));add('plan',p)
    admission=SimpleNamespace(root=tmp_path,experiment_id='synthetic-neural',source='a'*40,inputs=inputs,
        experiment={'cells':[c['cell_id'] for c in cells],'outputs':['cell-ledger.json','resource-summary.json','artifact-index.json'],
                    'windows':[{'dataset':'graphs','start':'2022-01-01T00:00:00Z','end':'2025-01-01T00:00:00Z'}]})
    run=ResearchRun(admission);run._claim_sha256='b'*64
    monkeypatch.setattr(run,'_active',lambda:None);monkeypatch.setattr(run,'_check_source',lambda:None)
    # Source/admission is not exercised against the shared checkout. Reads retain actual input hashing.
    return run,plan


def test_exact_denominator_and_manifest_extent_precede_graph_allocation(tmp_path,monkeypatch):
    n=module();run,plan=synthetic_run(tmp_path,monkeypatch)
    n.registered_plan(run,'plan')
    run.admission.experiment['cells'].pop()
    with pytest.raises(ValueError,match='denominator'):n.registered_plan(run,'plan')


def test_failure_stops_next_graph_and_retains_full_ledger(tmp_path,monkeypatch):
    n=module();run,plan=synthetic_run(tmp_path,monkeypatch)
    # Inject an actual model-step failure at first cell; production ledger remains real.
    def failure(*args,**kwargs):raise RuntimeError('synthetic step failure')
    monkeypatch.setattr(n,'run_cell',failure)
    rows,summary,directory=n.produce_registered_neural_resource(run,'plan')
    assert [r['status'] for r in rows]==['failed']+['unavailable']*8
    assert summary['financial_run_admitted'] is False
    assert len(list(directory.glob('neural_checkpoint-*.json')))==9
    assert not (directory/'cell-01').exists()
    with pytest.raises(FileExistsError):n.produce_registered_neural_resource(run,'plan')
