"""Real registered source dispatch over tiny synthetic Parquet fixtures."""
from datetime import datetime, timezone, timedelta
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tests.research.test_lifecycle import registered, start, commit
from tests.research.onchain_replication.test_weekly import config
from tests.research.onchain_replication.test_btc_source import row as btc_row
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.job import execute_source_job, job_schema

WEEKS=['2023-12-25T00:00:00Z','2024-01-01T00:00:00Z']
END='2024-01-08T00:00:00Z'


def api():
    assert importlib.util.find_spec('tradingagents.research.onchain_replication.graph_production'), 'registered graph producer missing'


def prepare(fixture, *, asset='ETH', duplicate=False, missing=False):
    root,spec,_=fixture;exp=spec['experiments']['example-a']
    exp['windows'][0].update(start=WEEKS[0],end=END)
    spec['datasets']['sample']['exposures']=[{'start':WEEKS[0],'end':END,'state':'spent'}]
    def put(name,value):
        p=root/(name+'.json');p.write_text(json.dumps(value))
        exp['inputs'][name]={'path':p.name,'sha256':file_hash(p),'dataset':'sample'}
    put('graph_config',config());sources=[]
    days=['2023-12-31','2024-01-01'] if asset=='ETH' else [(datetime(2023,12,25)+timedelta(days=i)).date().isoformat() for i in range(14)]
    for i,day in enumerate(days[:1 if missing else len(days)]):
        at=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        if asset=='ETH':
            table=pa.table({'hash':['0x'+('1' if duplicate else str(i+1))*64],
                'block_timestamp':pa.array([at],type=pa.timestamp('ns')),
                'from_address':['0x'+'a'*40],'to_address':['0x'+'b'*40],
                'value':[float((i+2)*10**18)],'receipt_status':pa.array([1],type=pa.int64())})
        else:
            r=btc_row();r.update(hash=format(i+1,'x')*64,block_hash=format(i+3,'x')*64,block_number=100+i,block_timestamp=at)
            r['inputs'][0]['spent_transaction_hash']=('c' if duplicate else format(i+5,'x'))*64
            table=pa.Table.from_pylist([r])
            if day not in ('2023-12-31','2024-01-01'):table=table.slice(0,0)
            table=table.replace_schema_metadata({'synthetic_partition_day':day})
        path=root/f'raw-{i}.parquet';pq.write_table(table,path)
        if asset=='ETH':
            manifest={'status':'complete','start_utc':WEEKS[i],'end_utc':WEEKS[i+1] if i==0 else END,
                'expected_rows':1,'expected_members':1,'members':[{'path':str(path),'sha256':file_hash(path),'format':'parquet','expected_rows':1}]}
            if i==0:put('schema',{f.name:str(f.type) for f in table.schema})
        else:manifest={'status':'complete','path':str(path),'sha256':file_hash(path),'expected_rows':len(table),'date':day}
        name=f'raw_source_{i}';put(name,manifest);sources.append(name)
    plan={'schema_version':1,'mode':'build','asset':asset,'graph_config_input':'graph_config',
          'coverage':[[WEEKS[0],END]],'expected_weeks':WEEKS,'source_inputs':sources,
          'decoder':{'schema_input':'schema'} if asset=='ETH' else {'precision_policy':'binary64_satoshi_grid_inverse_v1'}}
    put('graph_plan',plan)
    exp['cells']=[*(f'source-{i:06d}' for i in range(len(sources))),*(f'graph-{w[:10]}' for w in WEEKS)]
    exp['outputs']=['cell-ledger.json','source-summary.json','artifact-index.json']
    return root,spec,commit(root,spec)


@pytest.mark.parametrize('asset',['ETH','BTC'])
def test_registered_parquet_graph_production_retains_exact_weeks_counts_and_sidecars(registered,asset):
    api();fixture=prepare(registered,asset=asset)
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        terminal=run.finish(cells)
        assert terminal['cell_count']==(4 if asset=='ETH' else 16) and terminal['unavailable_count']==0
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
        assert summary['asset']==asset and list(summary['graphs'])==WEEKS
        for week,ref in summary['graphs'].items():
            path=fixture[0]/ref['manifest_path']
            proof=json.loads((fixture[0]/ref['coverage_path']).read_text())
            assert file_hash(fixture[0]/ref['coverage_path'])==ref['coverage_sha256']
            assert len(proof['members'])==(1 if asset=='ETH' else 7)
            assert sum(m['expected_rows'] for m in proof['members'])==1
            if asset=='ETH':
                from tradingagents.research.onchain_replication.graph_store import load_graph
                graph=load_graph(path,ref['manifest_sha256'])
                assert graph.edge_aggregates.tolist()==[[1.,2. if week==WEEKS[0] else 3.]]
            else:
                from tradingagents.research.onchain_replication.btc_store import load_btc_graph
                exact=load_btc_graph(path,ref['manifest_sha256']);graph=exact.graph
                assert exact.fee_satoshis==2 and exact.observed_chain_order_checked
                assert tuple(map(str,exact.edge_satoshis))==('7',)
            assert graph.raw_count==graph.admitted_count==1
        assert (fixture[0]/summary['workspace']/'complete.json').exists()


@pytest.mark.parametrize('asset',['ETH','BTC'])
def test_cross_partition_corruption_accounts_for_all_weeks_without_publishing_graphs(registered,asset):
    api();fixture=prepare(registered,asset=asset,duplicate=True)
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        assert len(cells)==(4 if asset=='ETH' else 16)
        assert all(c['status']=='unavailable' and 'duplicate' in c['reason'] for c in cells if c['id'].startswith('graph-'))
        assert cells[0]['status']=='complete' and cells[1 if asset=='ETH' else 7]['status']=='unavailable'
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
        assert not summary['graphs']
        assert (fixture[0]/summary['workspace']/'failed.json').exists()
        run.finish(cells)
    with pytest.raises(ValueError,match='repeat'):start(fixture)


def test_missing_week_remains_unavailable(registered):
    api();fixture=prepare(registered,missing=True)
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        assert len(cells)==3 and all(c['status']=='unavailable' for c in cells[1:])
        assert all('coverage' in c['reason'] for c in cells[1:])
        run.finish(cells)


def test_graph_dispatch_requires_explicit_registered_plan():
    api()
    job={'schema_version':1,'kind':'graphs','resources':{},'environment_input':'environment','payload':{'plan_input':'graph_plan'}}
    job_schema(job)
    for payload in ({},{'plan_input':''},{'plan_input':'graph_plan','resume':True}):
        with pytest.raises(ValueError):job_schema({**job,'payload':payload})


def test_graph_preparation_imports_no_neural_runtime():
    api()
    result=subprocess.run([sys.executable,'-B','-c',"import sys; import tradingagents.research.onchain_replication.graph_production; assert 'torch' not in sys.modules"],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('asset',['ETH','BTC'])
@pytest.mark.parametrize('coverage_fault',[None,'gap','wrong_graph'])
def test_admitted_graph_reuse_verifies_original_arrays_without_decoding(registered,monkeypatch,asset,coverage_fault):
    fixture=prepare(registered,asset=asset);root,spec,_=fixture
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'});run.finish(cells)
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
    import copy
    exp=copy.deepcopy(spec['experiments']['example-a']);spec['experiments']['example-b']=exp
    exp['parent']='example-a';exp['cells']=['graph-'+w[:10] for w in WEEKS]
    refs={}
    for i,(week,ref) in enumerate(summary['graphs'].items()):
        name=f'graph_{i}'
        exp['inputs'][name]={'path':ref['manifest_path'],'sha256':ref['manifest_sha256'],'dataset':'sample'}
        coverage_name=f'coverage_{i}'
        exp['inputs'][coverage_name]={'path':ref['coverage_path'],'sha256':ref['coverage_sha256'],'dataset':'sample'}
        if coverage_fault and i==0:
            proof=json.loads((root/ref['coverage_path']).read_text())
            if coverage_fault=='gap':proof['members']=proof['members'][1:]
            else:proof['graph_manifest_sha256']='0'*64
            proof_path=root/'bad-coverage.json';proof_path.write_text(json.dumps(proof))
            exp['inputs'][coverage_name]={'path':proof_path.name,'sha256':file_hash(proof_path),'dataset':'sample'}
        refs[week]={'input':name,'source_hashes':ref['source_hashes'],'coverage_input':coverage_name}
    plan={'schema_version':1,'mode':'reuse','asset':asset,'graph_config_input':'graph_config',
          'coverage':[[WEEKS[0],END]],'expected_weeks':WEEKS,'graphs':refs}
    path=root/'reuse.json';path.write_text(json.dumps(plan))
    exp['inputs']['reuse']={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
    # This sentinel detects accidental decoding; every output assertion checks
    # the real graph store and registered producer, not the sentinel itself.
    import tradingagents.research.onchain_replication.eth_source as eth
    import tradingagents.research.onchain_replication.btc_source as btc
    monkeypatch.setattr(eth,'decode_eth',lambda *a,**k:pytest.fail('reused graph decoded again'))
    monkeypatch.setattr(btc,'decode_parquet',lambda *a,**k:pytest.fail('reused graph decoded again'))
    with start((root,spec,commit(root,spec)),experiment='example-b') as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'reuse'})
        assert len(cells)==2
        if coverage_fault:
            assert cells[0]['status']=='unavailable' and 'coverage' in cells[0]['reason']
            assert cells[1]['status']=='complete' and cells[1]['reused']
        else:assert all(c['status']=='complete' and c['reused'] for c in cells)
        reused=json.loads((run.directory/'outputs/source-summary.json').read_text())
        assert reused['workspace'] is None
        for week,ref in reused['graphs'].items():
            assert ref['manifest_sha256']==summary['graphs'][week]['manifest_sha256']
            assert ref['manifest_path']==summary['graphs'][week]['manifest_path']
        run.finish(cells)


def test_changed_body_hash_leaves_every_source_and_graph_cell_accounted(registered):
    fixture=prepare(registered);root,_,_=fixture
    (root/'raw-0.parquet').write_bytes(b'changed synthetic body')
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        assert len(cells)==4 and all(c['status']=='unavailable' and 'hash' in c['reason'] for c in cells)
        run.finish(cells)


def test_publication_failure_retains_partial_graph_and_failed_aggregation(registered,monkeypatch):
    fixture=prepare(registered);root,_,_=fixture
    import tradingagents.research.onchain_replication.graph_store as store
    save=store.save_graph
    def interrupted(*args):
        save(*args)
        raise OSError('synthetic publication interruption')
    monkeypatch.setattr(store,'save_graph',interrupted)
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        assert all(c['status']=='unavailable' for c in cells if c['id'].startswith('graph-'))
        directory=root/'research_artifacts/onchain-paper-replication-2026-09-24/sources/example-a'
        assert (directory/'graph-2023-12-25/manifest.json').exists()
        assert (directory/'aggregation/failed.json').exists()
        assert not (directory/'aggregation/complete.json').exists()
        index=json.loads((run.directory/'outputs/artifact-index.json').read_text())
        assert str((directory/'graph-2023-12-25/node_features.npy').relative_to(root)) in index
        run.finish(cells)


def test_sealed_graph_outputs_feed_a_separately_registered_population(registered):
    from copy import deepcopy
    from dataclasses import asdict
    from datetime import timedelta
    from tradingagents.research.onchain_replication.calendar import build_folds
    from tradingagents.research.onchain_replication.contracts import PricePanel
    from tradingagents.research.onchain_replication.provenance import digest,canonical_bytes
    from tradingagents.research.onchain_replication.cache import cache_key
    from tradingagents.research.onchain_replication.population_assembly import produce_registered_population
    fixture=prepare(registered);root,spec,_=fixture
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'});run.finish(cells)
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
    exp=deepcopy(spec['experiments']['example-a']);spec['experiments']['example-b']=exp
    exp['parent']='example-a';exp['cells']=['population'];exp['outputs']=['population.json','binding.json','assembly.json']
    exp['windows'][0]['end']='2024-01-11T00:00:00Z'
    def put(name,value):
        path=root/(name+'.json');path.write_bytes(canonical_bytes(value))
        exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
    cfg={'lookback_days':1,'folds':[{'id':'tiny','train_start':'2024-01-02T00:00:00Z',
        'train_end':'2024-01-07T00:00:00Z','test_start':'2024-01-07T00:00:00Z','test_end':'2024-01-11T00:00:00Z',
        'validation_start':None,'validation_end':None}]}
    fold=build_folds(cfg,summary['graphs'])[0]
    prices=PricePanel('ETH-USD',tuple(f'2024-01-{i:02d}' for i in range(1,11)),tuple(float(9+i) for i in range(1,11)),(),'f'*64,'2024-01-12T00:00:00Z')
    put('prices',asdict(prices));put('calendar',cfg)
    refs={}
    for i,(week,ref) in enumerate(summary['graphs'].items()):
        name=f'produced_{i}';exp['inputs'][name]={'path':ref['manifest_path'],'sha256':ref['manifest_sha256'],'dataset':'sample'}
        refs[week]={'input':name,'status':'complete'}
    admission={'asset':'ETH','graph_config_hash':cache_key(config()),'price_source_hash':prices.source_hash,
        'price_panel_hash':digest(canonical_bytes(asdict(prices))),'calendar_hash':digest(canonical_bytes(cfg)),
        'fold_hash':fold.member_hash,'graph_manifest_hashes':sorted(r['manifest_sha256'] for r in summary['graphs'].values()),
        'source_hashes':sorted({h for r in summary['graphs'].values() for h in r['source_hashes']}),'unavailable_week_hashes':{}}
    put('admission',admission)
    put('population_plan',{'schema_version':1,'graphs':refs,'price_input':'prices','fold':asdict(fold),
        'calendar_input':'calendar','expected_weeks':WEEKS,'admission_input':'admission',
        'outputs':{'population':'population.json','binding':'binding.json','assembly':'assembly.json'}})
    with start((root,spec,commit(root,spec)),experiment='example-b') as run:
        result=produce_registered_population(run,'population_plan')
        examples=result['population']['examples']
        assert (len(examples['train']),len(examples['test']),len(examples['exclusions']))==(4,4,1)
        assert examples['exclusions'][0]['reason']=='purged_training_label'
        assert result['population']['scaler']['mean']==12.
        run.finish([{'id':'population','status':'complete'}])


@pytest.mark.parametrize('asset',['ETH','BTC'])
def test_daily_source_gaps_cannot_be_promoted_to_complete_weeks(registered,asset):
    fixture=prepare(registered,asset=asset);root,spec,_=fixture;exp=spec['experiments']['example-a']
    plan_path=root/'graph_plan.json';plan=json.loads(plan_path.read_text())
    if asset=='ETH':
        for i,name in enumerate(plan['source_inputs']):
            path=root/exp['inputs'][name]['path'];source=json.loads(path.read_text())
            day='2023-12-31T00:00:00Z' if i==0 else '2024-01-01T00:00:00Z'
            end='2024-01-01T00:00:00Z' if i==0 else '2024-01-02T00:00:00Z'
            source['members'][0].update(start_utc=day,end_utc=end)
            path.write_text(json.dumps(source));exp['inputs'][name]['sha256']=file_hash(path)
    else:
        plan['source_inputs']=[name for name in plan['source_inputs'] if json.loads((root/exp['inputs'][name]['path']).read_text())['expected_rows']]
        plan_path.write_text(json.dumps(plan));exp['inputs']['graph_plan']['sha256']=file_hash(plan_path)
        exp['cells']=[*(f'source-{i:06d}' for i in range(len(plan['source_inputs']))),*('graph-'+w[:10] for w in WEEKS)]
    with start((root,spec,commit(root,spec))) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'})
        assert all(c['status']=='unavailable' and 'coverage' in c['reason'] for c in cells)
        run.finish(cells)


@pytest.mark.parametrize('clock',['short_week','early_publication'])
def test_reuse_refuses_nonweekly_or_premature_graphs_even_with_valid_hashes(registered,clock):
    from copy import deepcopy
    from dataclasses import replace
    from tradingagents.research.onchain_replication.graph_store import load_graph,save_graph
    fixture=prepare(registered);root,spec,_=fixture
    with start(fixture) as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'graph_plan'});run.finish(cells)
        summary=json.loads((run.directory/'outputs/source-summary.json').read_text())
    exp=deepcopy(spec['experiments']['example-a']);spec['experiments']['example-b']=exp
    exp['parent']='example-a';exp['cells']=['graph-'+w[:10] for w in WEEKS]
    refs={}
    for i,(week,ref) in enumerate(summary['graphs'].items()):
        path=root/ref['manifest_path'];graph=load_graph(path,ref['manifest_sha256'])
        if i==0:
            graph=replace(graph,**({'end_utc':'2023-12-26T00:00:00Z'} if clock=='short_week' else {'available_at':'2024-01-01T00:00:00Z'}))
            path=save_graph(root/'synthetic-invalid-graph',graph)
        name=f'graph_{i}';exp['inputs'][name]={'path':str(path.relative_to(root)),'sha256':file_hash(path),'dataset':'sample'}
        coverage_name=f'coverage_{i}'
        exp['inputs'][coverage_name]={'path':ref['coverage_path'],'sha256':ref['coverage_sha256'],'dataset':'sample'}
        refs[week]={'input':name,'source_hashes':list(graph.source_hashes),'coverage_input':coverage_name}
    plan={'schema_version':1,'mode':'reuse','asset':'ETH','graph_config_input':'graph_config','coverage':[[WEEKS[0],END]],'expected_weeks':WEEKS,'graphs':refs}
    path=root/'reuse.json';path.write_text(json.dumps(plan));exp['inputs']['reuse']={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
    with start((root,spec,commit(root,spec)),experiment='example-b') as run:
        cells=execute_source_job(run,'graphs',{'plan_input':'reuse'})
        assert cells[0]['status']=='unavailable' and 'interval' in cells[0]['reason']
        assert cells[1]['status']=='complete'
        run.finish(cells)
