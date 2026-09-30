"""Real lifecycle admission over tiny synthetic saved graphs only."""
import importlib
import importlib.util
import json
from types import SimpleNamespace
import numpy as np
import pytest
from tests.research.test_lifecycle import registered,start,commit
from tests.research.onchain_replication.test_bounded_graph_hash import fixture
from tests.research.onchain_replication.test_job import policy
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication import job


def api():
    assert importlib.util.find_spec('tradingagents.research.onchain_replication.census_production'),'registered census producer missing'
    return importlib.import_module('tradingagents.research.onchain_replication.census_production')


def prepare(registered,change=None):
    root,spec,_=registered;exp=spec['experiments']['example-a']
    manifest=save_graph(root/'graph',fixture());data=json.loads(manifest.read_text())
    def put(name,value):
        path=root/(name+'.json');path.write_text(json.dumps(value))
        exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
    exp['inputs']['graph_manifest']={'path':str(manifest.relative_to(root)),'sha256':file_hash(manifest),'dataset':'sample'}
    plan={'schema_version':1,'graph_input':'graph_manifest','graph_hash':data['graph_hash'],'graph_config_hash':data['metadata']['graph_config_hash'],
          'node_order_sha256':data['arrays']['node_ids']['sha256'],'expected_nodes':7,'expected_edges':12,
          'edge_chunk':2,'max_output_bytes':1024**2,'max_mapped_bytes':sum(x['bytes'] for x in data['arrays'].values()),'cell_id':'census-2024-01-01'}
    if change:plan.update(change)
    put('census_plan',plan)
    exp['cells']=['census-2024-01-01'];exp['outputs']=['cell-ledger.json','source-summary.json','artifact-index.json']
    exp['windows'][0].update(start='2024-01-01T00:00:00Z',end='2024-01-08T00:00:00Z')
    spec['datasets']['sample']['exposures']=[{'start':'2024-01-01T00:00:00Z','end':'2024-01-08T00:00:00Z','state':'spent'}]
    return root,spec,commit(root,spec)


def test_registered_census_dispatch_and_full_array_identity(registered):
    api();case=prepare(registered)
    with start(case) as run:
        cells=job.execute_source_job(run,'neighborhood_census',{'plan_input':'census_plan'})
        terminal=run.finish(cells)
        assert terminal['cell_count']==1 and terminal['unavailable_count']==0
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
        assert summary['financial_run_admitted'] is False
        assert summary['graph_hash']==json.loads((case[0]/'census_plan.json').read_text())['graph_hash']
        assert summary['prepublication_storage']['allocated_output_bytes']<=1024**2
        np.testing.assert_array_equal(np.load(case[0]/summary['cardinalities_path']),[7,5,3,3,3,2,2])
        index=json.loads((run.directory/'outputs/artifact-index.json').read_text())
        assert summary['cardinalities_path'] in index
        for name,info in index.items():assert file_hash(case[0]/name)==info['sha256']


@pytest.mark.parametrize('change',[{'schema_version':True},{'edge_chunk':True},{'expected_nodes':0},{'expected_edges':-1},{'max_output_bytes':True},{'max_mapped_bytes':0},{'graph_input':''},{'graph_hash':'bad'},{'node_order_sha256':'bad'},{'extra':1}])
def test_bad_plan_refused_before_mapping_or_output(registered,monkeypatch,change):
    module=api();case=prepare(registered,change)
    monkeypatch.setattr(module,'open_mapped_graph',lambda *a,**k:pytest.fail('invalid plan opened graph'))
    with start(case) as run:
        with pytest.raises(ValueError):module.produce_registered_census(run,'census_plan')
        assert not (case[0]/module.PREFIX/'example-a').exists()


@pytest.mark.parametrize('field',['graph_hash','graph_config_hash','node_order_sha256'])
def test_bound_identity_mismatch_refused_before_mapping(registered,monkeypatch,field):
    module=api();case=prepare(registered,{field:'0'*64})
    monkeypatch.setattr(module,'open_mapped_graph',lambda *a,**k:pytest.fail('wrong identity opened graph'))
    with start(case) as run:
        with pytest.raises(ValueError):module.produce_registered_census(run,'census_plan')


def test_cell_denominator_and_window_checked_before_mapping(registered,monkeypatch):
    module=api();case=prepare(registered);root,spec,_=case
    spec['experiments']['example-a']['cells'].append('unplanned')
    case=root,spec,commit(root,spec)
    monkeypatch.setattr(module,'open_mapped_graph',lambda *a,**k:pytest.fail('wrong denominator opened graph'))
    with start(case) as run:
        with pytest.raises(ValueError):module.produce_registered_census(run,'census_plan')


def test_census_shape_mismatch_fails_and_closes_graph(registered,monkeypatch):
    from contextlib import contextmanager
    module=api();case=prepare(registered,{'expected_nodes':8});original=module.open_mapped_graph;closed=[]
    @contextmanager
    def tracked(*a,**k):
        with original(*a,**k) as graph:
            try:yield graph
            finally:closed.extend([graph.node_features._mmap,graph.edge_index._mmap])
    monkeypatch.setattr(module,'open_mapped_graph',tracked)
    with start(case) as run:
        cells,summary,directory=module.produce_registered_census(run,'census_plan')
        assert cells[0]['status']=='failed' and 'shape' in cells[0]['reason']
        assert summary['status']=='failed' and not (directory/'census/summary.json').exists()
        assert all(x.closed for x in closed)


def test_census_job_schema_and_strict_wall_bound(tmp_path):
    resources={**policy(tmp_path),'disk_floor_bytes':10*1024**3,'wall_seconds':540}
    value={'schema_version':1,'kind':'neighborhood_census','resources':resources,'environment_input':'environment','payload':{'plan_input':'census_plan'}}
    job.job_schema(value);assert job.resource_policy(resources,tmp_path)==resources
    for payload in ({},{'plan_input':''},{'plan_input':'census_plan','extra':1}):
        with pytest.raises(ValueError):job.job_schema({**value,'payload':payload})
    with pytest.raises(ValueError):job.job_schema({**value,'resources':{**resources,'wall_seconds':541}})


def test_worker_forwards_exact_registered_disk_floor(tmp_path,monkeypatch):
    resources={**policy(tmp_path),'disk_floor_bytes':10*1024**3}
    args=SimpleNamespace(root=tmp_path,experiment='example-a',source='a'*40,registration='registration.json')
    monkeypatch.setattr(job,'_admitted',lambda args:(SimpleNamespace(root=tmp_path),{'resources':resources}))
    class Reached(Exception):pass
    def guard(*a,**kwargs):
        assert kwargs['disk_floor_bytes']==resources['disk_floor_bytes'];raise Reached
    monkeypatch.setattr(job.resources,'assert_guarded_worker',guard)
    with pytest.raises(Reached):job.worker(args)


def test_output_symlink_escape_refused_before_any_outside_write(registered):
    module=api();case=prepare(registered);root=case[0]
    outside=root.parent/(root.name+'-outside');outside.mkdir()
    owner=root/module.PREFIX;owner.parent.mkdir(parents=True);owner.symlink_to(outside,target_is_directory=True)
    with start(case) as run:
        with pytest.raises(ValueError,match='guarded|volume|root'):module.produce_registered_census(run,'census_plan')
        assert list(outside.iterdir())==[]


def test_final_accounting_includes_published_producer_and_lifecycle_files(registered,capsys):
    module=api();case=prepare(registered)
    with start(case) as run:
        cells=job.execute_source_job(run,'neighborhood_census',{'plan_input':'census_plan'})
        row=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert row['kind']=='census_final_storage_accounting'
        roots=[case[0]/module.PREFIX/'example-a',run.directory/'outputs']
        paths=[p for root in roots for p in [root,*root.rglob('*')]]
        assert row['logical_bytes']==sum(p.stat().st_size for p in paths if p.is_file())
        assert row['allocated_bytes']==sum(p.stat().st_blocks*512 for p in paths)
        assert row['within_allowance']
        assert any(p.endswith('/result.json') for p in row['files'])
        assert any(p.endswith('/source-summary.json') for p in row['files'])
        run.finish(cells)


def test_large_error_is_bounded_and_hash_preserved(registered,monkeypatch):
    import hashlib
    module=api();case=prepare(registered)
    text='unexpected'*100_000
    def fail(*a,**k):raise RuntimeError(text)
    monkeypatch.setattr(module,'census',fail)
    with start(case) as run:
        cells,summary,directory=module.produce_registered_census(run,'census_plan')
        assert cells[0]['status']=='failed'
        assert summary['reason_truncated'] and summary['reason_sha256']==hashlib.sha256(text.encode()).hexdigest()
        assert len(summary['reason'])<2200
        assert sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())<1024**2


def test_disjoint_registered_window_rejected_before_graph_mapping(registered,monkeypatch):
    module=api();case=prepare(registered);root,spec,_=case
    exp=spec['experiments']['example-a'];exp['windows'][0].update(start='2024-02-01T00:00:00Z',end='2024-02-08T00:00:00Z')
    spec['datasets']['sample']['exposures']=[{'start':'2024-01-01T00:00:00Z','end':'2024-03-01T00:00:00Z','state':'spent'}]
    case=root,spec,commit(root,spec)
    monkeypatch.setattr(module,'open_mapped_graph',lambda *a,**k:pytest.fail('disjoint window opened graph'))
    with start(case) as run:
        with pytest.raises(ValueError,match='window'):module.produce_registered_census(run,'census_plan')


@pytest.mark.parametrize('nodes,status',[(7,'complete'),(8,'failed')])
def test_observer_recovers_durable_census_disposition_after_interruption(registered,nodes,status):
    from pathlib import Path
    import uuid
    module=api();case=prepare(registered,{'expected_nodes':nodes})
    with start(case) as run:
        rows,_,directory=module.produce_registered_census(run,'census_plan')
        assert rows[0]['status']==status
    args=SimpleNamespace(root=case[0],registration='registration.json',experiment='example-a',source=case[2])
    base=job._base(args);(base/'guard').mkdir(parents=True)
    owner={'experiment':args.experiment,'source_commit':args.source,'nonce':'synthetic','monitor_pid':2000000000,'monitor_start_ticks':'0'}
    (base/'owner.json').write_text(json.dumps(owner))
    unit='onchain-replication-'+uuid.uuid4().hex+'.service'
    live={'owner_identity':owner,'monitor_pid':owner['monitor_pid'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
          'cgroup':'/sys/fs/cgroup/'+unit,'unit':unit,'command':job._command(args,'worker')}
    (base/'guard/live.json').write_text(json.dumps(live))
    outcome=job.reconcile(args)
    assert outcome['status']=='failed'
    assert json.loads((base/'postmortem-cells.json').read_text())==rows
    assert job.reconcile(args)==outcome


def test_late_quota_failure_prevents_lifecycle_completion_and_retains_outputs(registered,capsys):
    module=api();case=prepare(registered)
    with start(case) as run:
        original=run.write_json
        def write(name,value):
            original(name,value)
            if name=='artifact-index.json':
                (case[0]/module.PREFIX/'example-a/unexpected-synthetic-padding.bin').write_bytes(b'0'*1024**2)
        run.write_json=write
        with pytest.raises(RuntimeError,match='storage allowance'):
            job.execute_source_job(run,'neighborhood_census',{'plan_input':'census_plan'})
        accounting=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert not accounting['within_allowance']
        assert accounting['allocated_bytes']>accounting['maximum_bytes']
    assert (run.directory/'failed.json').exists() and not (run.directory/'complete.json').exists()
    assert len(list((run.directory/'outputs').iterdir()))==3
