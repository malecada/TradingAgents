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
    policy={'memory_max_bytes':6*1024**3,'memory_high_bytes':5*1024**3,'reserve_bytes':3*1024**3,
            'start_reserve_bytes':9*1024**3,'disk_floor_bytes':10*1024**3,'disk_paths':[str(tmp_path)],'wall_seconds':600}
    execution={'schema_version':1,'kind':'neural_resource','resources':policy,'environment_input':'env','payload':{'plan_input':'plan'}}
    path=tmp_path/'execution.json';path.write_text(json.dumps(execution));add('execution_job',path)
    path=tmp_path/'env.json';path.write_text('{"torch":true}');add('env',path)
    from tradingagents.research.onchain_replication import environment,resources
    monkeypatch.setattr(environment,'inventory',lambda root,include_torch:{'torch':include_torch})
    owner={'experiment':'synthetic-neural','source_commit':'a'*40}
    ownerdir=tmp_path/job.PREFIX/'runs'/'synthetic-neural';ownerdir.mkdir(parents=True)
    (ownerdir/'owner.json').write_text(json.dumps(owner))
    monkeypatch.setattr(resources,'assert_guarded_worker',lambda *a,**kw:{**policy,'owner_identity':owner})
    monkeypatch.setattr(module(),'__file__',str(tmp_path/'tradingagents/research/onchain_replication/neural_resource.py'))
    admission=SimpleNamespace(root=tmp_path,registration='synthetic-registration',experiment_id='synthetic-neural',source='a'*40,inputs=inputs,
        experiment={'source_files':dict.fromkeys(job.required_sources(),'a'*64),'cells':[c['cell_id'] for c in cells],'outputs':['cell-ledger.json','resource-summary.json','artifact-index.json'],
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


def test_saved_state_matches_independent_original_one_step(tmp_path):
    import numpy as np
    from tradingagents.research.onchain_replication.checkpoints import seed_all,capture_rng
    from tradingagents.research.onchain_replication.model import ReplicationModel
    n=module();torch.set_num_threads(2)
    edges=np.array([[0,1],[1,2]],dtype=np.int64)
    n.run_cell(SimpleNamespace(node_ids=('a','b','c'),edge_index=edges),cfg(),tmp_path,{},max_checkpoint_bytes=8*1024**2,cooperative_seconds=60)
    saved=torch.load(tmp_path/'checkpoint.pt',weights_only=True)
    rng=seed_all(11);model=ReplicationModel(cfg(),'classification')
    item={'mcm':torch.from_numpy(rng.random((3,32),dtype=np.float32)),'edge_index':torch.tensor(edges.copy(),dtype=torch.long)}
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    scores=model([[item]*28 for _ in range(16)],torch.linspace(-1,1,448).reshape(16,28,1))
    torch.nn.functional.cross_entropy(scores,torch.arange(16)%2).backward();optimizer.step()
    for name,value in model.state_dict().items():assert torch.equal(saved['model'][name],value)
    for key,state in optimizer.state_dict()['state'].items():
        for name,value in state.items():assert torch.equal(saved['optimizer']['state'][key][name],value)
    assert torch.equal(saved['rng']['torch_cpu'],capture_rng(rng)['torch_cpu'])
    assert saved['rng']['pcg64']==capture_rng(rng)['pcg64']


def test_count_refusal_occurs_before_resident_graph_load(tmp_path,monkeypatch):
    n=module();run,plan=synthetic_run(tmp_path,monkeypatch)
    plan['cells'][0]['expected_nodes']=4000
    path=tmp_path/'plan.json';path.write_text(json.dumps(plan))
    from tradingagents.research.onchain_replication.provenance import file_hash
    run.admission.inputs['plan']['sha256']=file_hash(path)
    from tradingagents.research.onchain_replication import graph_store
    allocations=[]
    def forbidden(*args,**kwargs):
        allocations.append(True);raise RuntimeError('unexpected resident allocation')
    monkeypatch.setattr(graph_store,'load_graph',forbidden)
    rows,_,_=n.produce_registered_neural_resource(run,'plan')
    assert allocations==[]
    assert rows[0]['status']=='failed' and 'count' in rows[0]['reason']


def test_all_nine_synthetic_graphs_complete_and_remain_distinct(tmp_path,monkeypatch):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    rows,summary,directory=n.produce_registered_neural_resource(run,'plan')
    assert len(rows)==9 and all(r['status']=='complete' for r in rows)
    assert summary['complete']==9 and summary['failed']==summary['unavailable']==0
    assert len(list(directory.glob('cell-*/checkpoint.pt')))==9
    identities=[torch.load(p,weights_only=True)['identity']['cell_id'] for p in sorted(directory.glob('cell-*/checkpoint.pt'))]
    assert identities==run.admission.experiment['cells']


def test_worker_requires_torch_inventory_and_resource_output_route(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from tradingagents.research.onchain_replication import environment,resources
    n=module();args=SimpleNamespace(root=tmp_path,experiment='synthetic',source='a'*40,registration='reg')
    base=tmp_path/'guard-owner';base.mkdir();owner={'experiment':'synthetic','source_commit':'a'*40}
    (base/'owner.json').write_text(json.dumps(owner))
    policy={'disk_paths':[str(tmp_path)],'wall_seconds':60,'memory_max_bytes':1024,'memory_high_bytes':512,'disk_floor_bytes':1024}
    specification={'kind':'neural_resource','resources':policy,'payload':{'plan_input':'plan'},'environment_input':'env'}
    monkeypatch.setattr(job,'_admitted',lambda a:(SimpleNamespace(root=tmp_path),specification))
    monkeypatch.setattr(job,'_base',lambda a:base)
    monkeypatch.setattr(resources,'assert_guarded_worker',lambda *a,**kw:{**policy,'owner_identity':owner})
    monkeypatch.setattr(job.signal,'signal',lambda *a:None)
    def inventory(root,*,include_torch):return {'torch_included':include_torch}
    monkeypatch.setattr(environment,'inventory',inventory)
    outputs={};finished=[];directory=tmp_path/'artifacts';directory.mkdir()
    (directory/'receipt').write_text('synthetic')
    run=SimpleNamespace(read_input=lambda name:b'{"torch_included":true}',write_json=lambda name,value:outputs.__setitem__(name,value),finish=lambda cells:finished.extend(cells),fail=lambda reason:pytest.fail(reason))
    @contextmanager
    def start(**kwargs):yield run
    monkeypatch.setattr(job.ResearchRun,'start',start)
    monkeypatch.setattr(n,'produce_registered_neural_resource',lambda r,p:([{'id':'cell','status':'complete'}],{'resource_only':True},directory))
    monkeypatch.setattr(n,'finalize_storage',lambda *a:None)
    job.worker(args)
    assert set(outputs)=={'cell-ledger.json','resource-summary.json','artifact-index.json'}
    assert finished==[{'id':'cell','status':'complete'}]
    assert outputs['artifact-index.json']['artifacts/receipt']['bytes']==9


def test_plan_rejects_wrong_graph_week_end(tmp_path,monkeypatch):
    n=module();run,plan=synthetic_run(tmp_path,monkeypatch)
    from tradingagents.research.onchain_replication.provenance import file_hash
    path=tmp_path/'g0/manifest.json';manifest=json.loads(path.read_bytes())
    manifest['metadata']['end_utc']='2022-01-11T00:00:00Z';path.write_text(json.dumps(manifest));run.admission.inputs['g0']['sha256']=file_hash(path)
    with pytest.raises(ValueError,match='week'):n.registered_plan(run,'plan')


@pytest.mark.parametrize('fatal',[SystemExit('synthetic stop'),MemoryError('synthetic memory exhausted')])
def test_fatal_propagates_after_full_failed_denominator(tmp_path,monkeypatch,fatal):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    def fail(*a,**kw):raise fatal
    monkeypatch.setattr(n,'run_cell',fail)
    with pytest.raises(type(fatal)) as caught:n.produce_registered_neural_resource(run,'plan')
    assert caught.value is fatal
    directory=tmp_path/n.PREFIX/run.admission.experiment_id
    assert len(list(directory.glob('neural_checkpoint-*.json')))==9
    assert not (directory/'cell-01').exists()


def test_failed_publication_cannot_mask_primary_fatal(tmp_path,monkeypatch):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch);primary=SystemExit('primary interruption')
    original=n._immutable;writes=[]
    def write(path,value):
        writes.append(path.name)
        if path.name.startswith('neural_checkpoint-'):raise OSError('secondary publication unavailable')
        return original(path,value)
    monkeypatch.setattr(n,'_immutable',write)
    def fail(*a,**kw):raise primary
    monkeypatch.setattr(n,'run_cell',fail)
    with pytest.raises(SystemExit) as caught:n.produce_registered_neural_resource(run,'plan')
    assert caught.value is primary and len([x for x in writes if x.startswith('neural_checkpoint-')])==9
    assert any('publication' in note for note in primary.__notes__)


def test_checkpoint_close_is_once_and_preserves_original_fatal(tmp_path,monkeypatch):
    n=module();from tradingagents.research.onchain_replication.score_batches import CleanupFailure
    primary=CleanupFailure('primary write cleanup uncertainty');closes=[]
    original=Path.open
    class UncertainClose:
        def __init__(self,stream):self.stream=stream
        def __getattr__(self,name):return getattr(self.stream,name)
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
        def close(self):
            closes.append(True);self.stream.close();raise OSError('secondary close uncertainty')
    def opened(path,*a,**kw):
        stream=original(path,*a,**kw)
        return UncertainClose(stream) if path.name=='checkpoint.pt' and a==('xb',) else stream
    monkeypatch.setattr(Path,'open',opened)
    def fail(*a,**kw):raise primary
    monkeypatch.setattr(torch,'save',fail)
    import numpy as np
    graph=SimpleNamespace(node_ids=('a','b'),edge_index=np.array([[0],[1]],dtype='int64'))
    with pytest.raises(CleanupFailure) as caught:n.run_cell(graph,cfg(),tmp_path,{},max_checkpoint_bytes=1024**2,cooperative_seconds=60)
    assert caught.value is primary and closes==[True]
    assert any('close' in note for note in primary.__notes__)


def test_producer_requires_selected_execution_plan_before_output(tmp_path,monkeypatch):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    # Remove the selected job to make this fixture intentionally unbound.
    del run.admission.inputs['execution_job']
    with pytest.raises((KeyError,ValueError),match='execution|unregistered'):
        n.produce_registered_neural_resource(run,'plan')
    assert not (tmp_path/n.PREFIX/run.admission.experiment_id).exists()


@pytest.mark.parametrize('change',[{'kind':'fit'},{'payload':{'plan_input':'foreign-plan'}}])
def test_producer_rejects_wrong_admitted_job_or_plan(tmp_path,monkeypatch,change):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    path=tmp_path/'execution.json';value=json.loads(path.read_bytes());value.update(change);path.write_text(json.dumps(value))
    from tradingagents.research.onchain_replication.provenance import file_hash
    run.admission.inputs['execution_job']['sha256']=file_hash(path)
    with pytest.raises(ValueError,match='selected'):n.produce_registered_neural_resource(run,'plan')
    assert not (tmp_path/n.PREFIX/run.admission.experiment_id).exists()


def test_producer_rejects_absent_live_guard_before_output(tmp_path,monkeypatch):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    from tradingagents.research.onchain_replication import resources
    def missing(*a,**kw):raise RuntimeError('guard not released')
    monkeypatch.setattr(resources,'assert_guarded_worker',missing)
    with pytest.raises(RuntimeError,match='guard'):n.produce_registered_neural_resource(run,'plan')
    assert not (tmp_path/n.PREFIX/run.admission.experiment_id).exists()


@pytest.mark.parametrize('redirect',['device','symlink'])
def test_foreign_output_ancestor_refused_before_allocation(tmp_path,monkeypatch,redirect):
    n=module();run,_=synthetic_run(tmp_path,monkeypatch)
    ancestor=tmp_path/n.PREFIX;ancestor.parent.mkdir(parents=True,exist_ok=True)
    if redirect=='symlink':
        foreign=tmp_path/'redirect';foreign.mkdir();ancestor.symlink_to(foreign,target_is_directory=True)
    else:
        ancestor.mkdir();original=Path.stat
        def changed(path,*a,**kw):
            result=original(path,*a,**kw)
            return SimpleNamespace(st_dev=result.st_dev+1) if path==ancestor else result
        monkeypatch.setattr(Path,'stat',changed)
    with pytest.raises(ValueError,match='namespace|device'):n.produce_registered_neural_resource(run,'plan')
    assert not (ancestor/run.admission.experiment_id).exists()
