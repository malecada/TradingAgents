"""Registered hub sizing lifecycle over synthetic retained graph/census only."""
import importlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import uuid
from copy import deepcopy
import numpy as np
import pytest
from tests.research.test_lifecycle import registered,start,commit
from tests.research.onchain_replication.test_bounded_graph_hash import fixture
from tests.research.onchain_replication.test_job import policy
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhood_census import census
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication import job


def api():
    assert importlib.util.find_spec('tradingagents.research.onchain_replication.hub_census_production'),'hub producer missing'
    return importlib.import_module('tradingagents.research.onchain_replication.hub_census_production')


def prepare(registered,change=None):
    from tests.research.onchain_replication.test_registered_census import prepare as census_prepare
    case=census_prepare(registered);root,spec,_=case
    spec['experiments']['prior-census']=spec['experiments'].pop('example-a')
    case=root,spec,commit(root,spec)
    with start(case,'prior-census') as parent:
        cells=job.execute_source_job(parent,'neighborhood_census',{'plan_input':'census_plan'})
        parent.finish(cells)
    exp=deepcopy(spec['experiments']['prior-census']);exp['parent']='prior-census'
    spec['experiments']['example-a']=exp
    manifest=root/'graph/manifest.json';meta=json.loads(manifest.read_text())
    def put(name,value):
        p=root/(name+'.json');p.write_text(json.dumps(value));bind(name,p);return p
    def bind(name,p):exp['inputs'][name]={'path':str(p.relative_to(root)),'sha256':file_hash(p),'dataset':'sample'}
    bind('prior_claim',parent.directory/'claim.json');bind('prior_terminal',parent.directory/'complete.json')
    bind('prior_result',parent.directory/'outputs/source-summary.json')
    previous=json.loads((parent.directory/'outputs/source-summary.json').read_text())
    bind('cardinalities',root/previous['cardinalities_path']);bind('graph_manifest',manifest)
    cells=[f'hub-edge-{i:03d}' for i in range(5)]
    plan={'schema_version':1,'graph_input':'graph_manifest','prior_claim_input':'prior_claim','prior_terminal_input':'prior_terminal','prior_result_input':'prior_result','cardinalities_input':'cardinalities',
        'census_experiment':'prior-census','graph_hash':meta['graph_hash'],'graph_config_hash':meta['metadata']['graph_config_hash'],'node_order_sha256':meta['arrays']['node_ids']['sha256'],
        'expected_nodes':7,'expected_edges':12,'expected_centers':5,'threshold':2,'edge_chunk':2,'max_output_bytes':1024**2,'max_buffer_bytes':8*1024**2,
        'max_mapped_bytes':sum(v['bytes'] for v in meta['arrays'].values()),'cell_ids':cells}
    if change:plan.update(change)
    put('hub_plan',plan);exp['cells']=cells;exp['outputs']=['cell-ledger.json','source-summary.json','artifact-index.json']
    exp['windows'][0].update(start='2024-01-01T00:00:00Z',end='2024-01-08T00:00:00Z')
    spec['datasets']['sample']['exposures']=[{'start':'2024-01-01T00:00:00Z','end':'2024-01-08T00:00:00Z','state':'spent'}]
    return root,spec,commit(root,spec)


def test_registered_hub_complete_durable_denominator_and_accounting(registered,capsys):
    api();case=prepare(registered)
    with start(case) as run:
        rows=job.execute_source_job(run,'hub_edge_census',{'plan_input':'hub_plan'})
        assert [r['center'] for r in rows]==[0,1,2,3,4]
        graph=fixture()
        for row in rows:
            members={row['center']}
            for a,b in graph.edge_index.T:
                if a==row['center']:members.add(int(b))
                if b==row['center']:members.add(int(a))
            assert row['nodes']==len(members)
            assert row['directed_edges']==sum(int(a) in members and int(b) in members for a,b in graph.edge_index.T)
            saved=case[0]/api().PREFIX/'example-a'/(row['id']+'.json')
            assert json.loads(saved.read_text())==row
        run.finish(rows)
        account=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert account['within_allowance'] and len(rows)==5


@pytest.mark.parametrize('change',[{'expected_centers':0},{'expected_centers':65},{'threshold':True},{'max_buffer_bytes':True},{'edge_chunk':65537},{'graph_hash':'0'*64},{'cell_ids':['wrong']},{'extra':1}])
def test_invalid_hub_plan_refused_before_mapping(registered,monkeypatch,change):
    mod=api();case=prepare(registered,change)
    monkeypatch.setattr(mod,'open_mapped_graph',lambda *a,**k:pytest.fail('bad plan mapped graph'))
    with start(case) as run:
        with pytest.raises(ValueError):mod.produce_registered_hub_census(run,'hub_plan')


def test_wrong_selected_denominator_fails_before_measurement(registered,monkeypatch):
    mod=api();case=prepare(registered,{'threshold':3})
    monkeypatch.setattr(mod,'measure',lambda *a,**k:pytest.fail('wrong selection measured graph'))
    with start(case) as run:
        rows,summary,_=mod.produce_registered_hub_census(run,'hub_plan')
        assert summary['status']=='failed' and len(rows)==5
        assert [r['status'] for r in rows]==['failed']+['unavailable']*4


def test_partial_failure_retains_rows_and_observer_recovers(registered,monkeypatch):
    mod=api();case=prepare(registered);original=mod.measure
    def partial(*args,checkpoint,**kwargs):
        seen=0
        def publish(row):
            nonlocal seen
            if seen==2:raise RuntimeError('synthetic third center failure')
            checkpoint(row);seen+=1
        return original(*args,checkpoint=publish,**kwargs)
    monkeypatch.setattr(mod,'measure',partial)
    with start(case) as run:
        rows,summary,directory=mod.produce_registered_hub_census(run,'hub_plan')
        assert [r['status'] for r in rows]==['complete','complete','failed','unavailable','unavailable']
    args=SimpleNamespace(root=case[0],registration='registration.json',experiment='example-a',source=case[2])
    base=job._base(args);(base/'guard').mkdir(parents=True)
    owner={'experiment':args.experiment,'source_commit':args.source,'nonce':'synthetic','monitor_pid':2000000000,'monitor_start_ticks':'0'}
    (base/'owner.json').write_text(json.dumps(owner));unit='onchain-replication-'+uuid.uuid4().hex+'.service'
    (base/'guard/live.json').write_text(json.dumps({'owner_identity':owner,'monitor_pid':owner['monitor_pid'],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'cgroup':'/sys/fs/cgroup/'+unit,'unit':unit,'command':job._command(args,'worker')}))
    result=job.reconcile(args);assert result['status']=='failed'
    assert json.loads((base/'postmortem-cells.json').read_text())==rows
    assert job.reconcile(args)==result


def test_hub_guard_schema_whole_job_bound(tmp_path):
    value={'schema_version':1,'kind':'hub_edge_census','resources':{**policy(tmp_path),'wall_seconds':540,'disk_floor_bytes':10*1024**3},'environment_input':'environment','payload':{'plan_input':'hub_plan'}}
    job.job_schema(value)
    with pytest.raises(ValueError):job.job_schema({**value,'resources':{**value['resources'],'wall_seconds':541}})


def test_numeric_policy_refused_before_any_counts_mapping(registered,monkeypatch):
    mod=api();case=prepare(registered,{'max_buffer_bytes':1})
    monkeypatch.setattr(mod,'_open_counts',lambda *a,**k:pytest.fail('numeric refusal came after mapping'))
    with start(case) as run:
        with pytest.raises(ValueError,match='numeric'):mod.produce_registered_hub_census(run,'hub_plan')


def test_closed_census_must_be_actual_admitted_parent(registered,monkeypatch):
    mod=api();root,spec,_=prepare(registered)
    spec['experiments']['example-a']['parent']=None;case=root,spec,commit(root,spec)
    monkeypatch.setattr(mod,'_open_counts',lambda *a,**k:pytest.fail('unrelated census mapped'))
    with start(case) as run:
        with pytest.raises(ValueError,match='parent'):mod.produce_registered_hub_census(run,'hub_plan')


def test_unicode_error_reason_has_bounded_encoded_bytes(registered,monkeypatch):
    mod=api();case=prepare(registered)
    def fail(*a,**k):raise ValueError('🔥'*100000)
    monkeypatch.setattr(mod,'measure',fail)
    with start(case) as run:
        rows,summary,_=mod.produce_registered_hub_census(run,'hub_plan')
        assert len(json.dumps(rows[0]['reason']).encode())<2304
        assert summary['reason_truncated']


def test_measure_failure_plus_counts_close_failure_is_fatal(registered,monkeypatch):
    mod=api();case=prepare(registered);original=mod._open_counts
    class Proxy:
        def __init__(self,value):self.value=value;self._mmap=self
        def __len__(self):return len(self.value)
        def __getitem__(self,key):return self.value[key]
        def close(self):self.value._mmap.close();raise RuntimeError('synthetic close failure')
    monkeypatch.setattr(mod,'_open_counts',lambda *a:Proxy(original(*a)))
    def fail(*a,**k):raise ValueError('measurement failed')
    monkeypatch.setattr(mod,'measure',fail)
    with start(case) as run:
        with pytest.raises(RuntimeError,match='close failure'):mod.produce_registered_hub_census(run,'hub_plan')


def test_interrupt_preserves_completed_prefix_and_map_cleanup(registered,monkeypatch):
    mod=api();case=prepare(registered);original=mod._open_counts;maps=[]
    def mapped(*a):
        value=original(*a);maps.append(value._mmap);return value
    monkeypatch.setattr(mod,'_open_counts',mapped)
    def interrupt(edges,n,expected,checkpoint,**kwargs):
        center,count=next(iter(expected.items()));checkpoint({'center':center,'nodes':count,'directed_edges':12})
        raise KeyboardInterrupt('synthetic stop')
    monkeypatch.setattr(mod,'measure',interrupt)
    with start(case) as run:
        with pytest.raises(KeyboardInterrupt):mod.produce_registered_hub_census(run,'hub_plan')
        directory=case[0]/mod.PREFIX/'example-a'
        assert (directory/'hub-edge-000.json').exists() and not (directory/'result.json').exists()
        assert all(m.closed for m in maps)


def test_graph_close_failure_after_all_cells_never_publishes_success(registered,monkeypatch):
    from contextlib import contextmanager
    mod=api();case=prepare(registered);original=mod.open_mapped_graph
    @contextmanager
    def closing(*a,**k):
        with original(*a,**k) as graph:yield graph
        raise RuntimeError('synthetic graph close failure')
    monkeypatch.setattr(mod,'open_mapped_graph',closing)
    with start(case) as run:
        with pytest.raises(RuntimeError,match='graph close failure'):mod.produce_registered_hub_census(run,'hub_plan')
        directory=case[0]/mod.PREFIX/'example-a'
        assert len(list(directory.glob('hub-edge-*.json')))==5
        assert (directory/'infrastructure-failure.json').exists() and not (directory/'result.json').exists()


def test_output_containment_before_any_outside_write(registered):
    mod=api();case=prepare(registered);root=case[0]
    # Prior source directory already exists; use the future exclusive child name.
    outside=root.parent/(root.name+'-external');outside.mkdir()
    (root/mod.PREFIX/'example-a').symlink_to(outside,target_is_directory=True)
    with start(case) as run:
        with pytest.raises(ValueError,match='guarded'):mod.produce_registered_hub_census(run,'hub_plan')
    assert list(outside.iterdir())==[]


def test_late_hub_quota_failure_retains_outputs_but_no_complete(registered,capsys):
    mod=api();case=prepare(registered)
    with start(case) as run:
        original=run.write_json
        def write(name,value):
            original(name,value)
            if name=='artifact-index.json':(case[0]/mod.PREFIX/'example-a/padding.bin').write_bytes(b'x'*1024**2)
        run.write_json=write
        with pytest.raises(RuntimeError,match='storage allowance'):job.execute_source_job(run,'hub_edge_census',{'plan_input':'hub_plan'})
    assert (run.directory/'failed.json').exists() and not (run.directory/'complete.json').exists()
    assert len(list((run.directory/'outputs').iterdir()))==3
